# -*- coding: utf-8 -*-
"""SUDE-VLM-33: SPECTRE-Large embeddinglerini dogru yeniden ornekleme ile cikarir.

Uzak GPU sunucusunda (/home/bt/TMP/benchmarks_500) calisir; yollar o sunucuya gore yazildi.

Kok neden (2026-09-15, gorsel tani ve yerel yeniden uretim):
  spectre-fm 0.2.1 io.resample() affine'i monai Spacing'e "affine=" argumani ile veriyor. MONAI
  0.9'dan beri bu argumani yok sayiyor ("Argument affine has been deprecated" uyarisi) ve
  hacmi 1 mm izotrop kabul ederek ornekliyor. Cikti SEKLI dogru, ICERIGI yanlis olcekli ve
  kaymis; kalan bolum dolgu. Bilinen konumdaki bir kup 0.2.1 yolunda ~10-30 mm kayik, MetaTensor
  yolunda dogru yerde cikti. v4'teki SPECTRE CT-RATE ve BIMCV embeddinglerinin hepsi bu yolla
  uretildi. BIMCV'de RAS olmayan/egik baslikli serilerde hacim tamamen dolguya dustu ve 49 seri
  ayni vektore coktu. spectre-fm ust akista bu hata 0.2.1'den hemen sonra duzeltildi
  ("Fix resampling bug": affine MetaTensor uzerinde tasiniyor).

Asamalar:
  hazirla  : BIMCV ham -> bozuk voksel boyutu duzeltmesi -> RAS -> 3B float32 -> kosegen affine.
             CT-RATE icin v4 hazir girdileri kullanilir (yonelimleri SPECTRE'nin kendi CT-RATE
             on islemesiyle ayni; yalniz yeniden ornekleme hataliydi).
  test     : sentetik kup konum testi + 5 gercek seride geri-korelasyon + gorsel panel
  onizleme : BIMCV 317 girdinin aksiyel/koronal kucuk resimleri (yonelim kontrolu)
  cikar    : seri basina CLS + SigLIP goruntu projeksiyonu, her seri ayri dosya, devam edebilir
  rapor    : birlestir ve kabul kapilarini uygula

Seri basina kapilar: RAS, yeniden ornekleme sekli (<%3 hata), geri-korelasyon >= 0,90
(yeniden orneklenmis hacim girdi izgarasina geri indirilip girdiyle Pearson r; hatali yol ~0,
dogru yol ~0,99), bos kirpim orani <= 0,90 (0,50 ustu uyari). Toplu: birebir/yakin kopya yok, NaN yok.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path("/home/bt/TMP/benchmarks_500")
V4 = KOK / "v4"
V5 = KOK / "v5"
CIKTI = V5 / "v2"
HAM_BIMCV = Path("/home/bt/TMP/bimcv_500_scans")
GIRDI = V5 / "inputs" / "bimcv"
CT_GIRDI = V4 / "work" / "spectre_inputs" / "ctrate"

CROP = (128, 128, 64)
SPACING = (0.5, 0.5, 1.0)
HU = (-1000.0, 1000.0)
KOHORT_SHA = "dbca93d4e7e427b70968332acb014334b114c20e42a8638ca3fa6172dccf426f"
V4_BIMCV_NPZ_SHA = "53020ea826ad1d09e3e2bfd9a377c8108a40e461a3aa14d736baa1f81db776ba"
V4_CTRATE_NPZ_SHA = "b63e2b7677ea9748ede6fc187e3346edc39756151913d86006c33873c167a070"
BOS_STD = 0.01
BOS_UYARI = 0.5
BOS_SERT = 0.9
GERI_R_MIN = 0.90
SEKIL_HATA_MAX = 0.03
YAKIN_KOPYA_COS = 0.9999


# --------------------------------------------------------------------------- ortak

def sha256_dosya(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def sha_kontrol(yol, beklenen):
    sha = sha256_dosya(yol)
    if sha != beklenen:
        sys.exit(f"DUR: {yol} sha farkli {sha}")


def kohort_317(manifest_yolu):
    m = pd.read_csv(manifest_yolu)
    b = m[(m.dataset == "bimcv") & (m.in_primary == True)].copy()  # noqa: E712
    adlar = sorted(b.volume_name)
    sha = hashlib.sha256("\n".join(adlar).encode("utf-8")).hexdigest()
    if len(adlar) != 317 or b.patient_id.nunique() != 315 or sha != KOHORT_SHA:
        sys.exit(f"DUR: kohort dogrulanamadi n={len(adlar)} hasta={b.patient_id.nunique()} sha={sha}")
    return b.set_index("volume_name").loc[adlar].reset_index()


def ctrate_500(manifest_yolu, v4_ctrate_npz):
    """v4 CT-RATE npz sirasiyla 500 seri; kimlikler oradan."""
    d = np.load(v4_ctrate_npz, allow_pickle=True)
    adlar = [str(v) for v in d["volume_names"]]
    m = pd.read_csv(manifest_yolu)
    if len(adlar) != 500 or set(adlar) != set(m[m.dataset == "ctrate"].volume_name):
        sys.exit("DUR: CT-RATE 500 seri listesi manifestle uyusmuyor")
    return pd.DataFrame({"volume_name": adlar, "patient_id": [str(p) for p in d["patient_ids"]],
                         "study_id": [str(s) for s in d["study_ids"]]})


def cokmus_seriler(npz_yolu):
    d = np.load(npz_yolu, allow_pickle=True)
    E = d["cls_embeds"]
    adlar = np.array([str(v) for v in d["volume_names"]])
    _, ters, sayi = np.unique(E, axis=0, return_inverse=True, return_counts=True)
    return set(adlar[sayi[ters.ravel()] > 1])


def spectre_yukle():
    """v4 kosusundaki import yamalarini aktif et."""
    sys.path.insert(0, str(V4 / "code"))
    import run_spectre_extraction as rse  # modul duzeyi yamalar (spectre.data stub vb.)
    from spectre.io import load_ct, resample as resample_021
    from spectre.windowing import scale_intensity_range, window_scan
    return rse, load_ct, resample_021, scale_intensity_range, window_scan


def ornekle(yol, yontem="meta"):
    """RAS -> HU olcek -> yeniden ornekle. Donus: (olceklenmis girdi, yeniden orneklenmis, meta)."""
    import torch
    from monai.data import MetaTensor
    from monai.transforms import Spacing
    _, load_ct, resample_021, scale_intensity_range, _ = spectre_yukle()
    hacim, meta = load_ct(yol, orientation="RAS")
    girdi = scale_intensity_range(hacim, a_min=HU[0], a_max=HU[1])
    if yontem == "021":
        cikti, _ = resample_021(girdi, meta, SPACING)  # hatali yol, yalniz tani
    else:
        mt = MetaTensor(girdi, affine=torch.as_tensor(meta.affine, dtype=torch.float64))
        cikti = Spacing(pixdim=SPACING, mode="bilinear")(mt)
        cikti = cikti.as_tensor() if hasattr(cikti, "as_tensor") else torch.as_tensor(cikti)
    return girdi, cikti.float(), meta


def geri_korelasyon(girdi, cikti):
    import torch
    import torch.nn.functional as F
    geri = F.interpolate(cikti[None], size=tuple(girdi.shape[1:]), mode="trilinear", align_corners=False)[0, 0]
    a, b = geri.flatten()[::7], girdi[0].flatten()[::7].float()
    if float(a.std()) == 0 or float(b.std()) == 0:
        return 0.0
    return float(torch.corrcoef(torch.stack([a, b]))[0, 1])


def kirpimlar(yol, yontem="meta"):
    *_, window_scan = spectre_yukle()
    girdi, cikti, meta = ornekle(yol, yontem)
    girdi_sekli = tuple(int(s) for s in girdi.shape[1:])
    ornek_sekli = tuple(int(s) for s in cikti.shape[1:])
    r = geri_korelasyon(girdi, cikti)
    hacim_std = float(cikti.std())
    crops, grid = window_scan(cikti, CROP, scale_intensity=False, pad_short_axes=True)
    beklenen = [g * z / t for g, z, t in zip(girdi_sekli, meta.spacing, SPACING)]
    sekil_hata = max(abs(o - b) / b for o, b in zip(ornek_sekli, beklenen))
    bos = float((crops.flatten(1).std(dim=1) < BOS_STD).float().mean())
    nedenler = []
    if meta.orientation != "RAS":
        nedenler.append(f"orientation={meta.orientation}")
    if sekil_hata > SEKIL_HATA_MAX:
        nedenler.append(f"sekil_hata={sekil_hata:.3f}")
    if r < GERI_R_MIN:
        nedenler.append(f"geri_korelasyon={r:.3f}")
    if bos > BOS_SERT:
        nedenler.append(f"bos_kirpim={bos:.2f}")
    bilgi = {
        "yontem": yontem, "girdi_sekli": girdi_sekli,
        "spacing_mm": tuple(round(float(s), 4) for s in meta.spacing), "orientation": meta.orientation,
        "ornek_sekli": ornek_sekli, "sekil_hata": round(sekil_hata, 4), "geri_korelasyon": round(r, 4),
        "grid": tuple(int(g) for g in grid), "n_crops": int(crops.shape[0]),
        "bos_kirpim_orani": round(bos, 4), "hacim_std": round(hacim_std, 4),
        "k1_gecti": not nedenler, "k1_nedenler": ";".join(nedenler), "bos_uyari": bos > BOS_UYARI,
    }
    return crops, grid, bilgi


# --------------------------------------------------------------------------- hazirla (BIMCV)

def affine_duzelt(img):
    """v4 kuraliyla ayni affine secimi; her eksende FOV olarak yazilmis boyutu duzeltir."""
    sform, qform = img.get_sform(), img.get_qform()
    sekil = img.shape[:3]
    normlar = lambda a: [float(np.linalg.norm(a[:3, j])) for j in range(3)]  # noqa: E731
    makul = lambda a: all(0.2 <= n <= 10.0 for n in normlar(a))  # noqa: E731
    if makul(sform):
        return sform.copy(), "sform", []
    if makul(qform):
        return qform.copy(), "qform", []
    aff = (qform if int(img.header["qform_code"]) != 0 else sform).copy()
    notlar = []
    for j, n in enumerate(normlar(aff)):
        if n > 10.0 and 0.2 <= n / sekil[j] <= 10.0:
            aff[:3, j] = aff[:3, j] / sekil[j]
            notlar.append(f"eksen{j}:{n:.2f}->{n / sekil[j]:.4f}")
    if not makul(aff):
        return None, "duzeltilemedi", notlar
    return aff, "fov_duzeltildi", notlar


def hazirla_tek(ad):
    import nibabel as nib
    hedef = GIRDI / ad
    if hedef.exists():
        return {"volume_name": ad, "durum": "vardi"}
    img = nib.load(str(HAM_BIMCV / ad))
    veri = np.asarray(img.get_fdata(dtype=np.float32))
    if veri.ndim == 4:
        veri = veri[..., 0]
    if veri.ndim != 3:
        return {"volume_name": ad, "durum": f"HATA ndim={veri.ndim}"}
    aff, kaynak, notlar = affine_duzelt(img)
    if aff is None:
        return {"volume_name": ad, "durum": "HATA affine", "notlar": ";".join(notlar)}
    ras = nib.as_closest_canonical(nib.Nifti1Image(veri, aff))
    dizi = np.ascontiguousarray(np.asarray(ras.dataobj), dtype=np.float32)
    zoom = [float(np.linalg.norm(ras.affine[:3, j])) for j in range(3)]
    out = nib.Nifti1Image(dizi, np.diag(zoom + [1.0]))
    out.header.set_xyzt_units("mm")
    gecici = GIRDI / f".{os.getpid()}_{ad}"
    nib.save(out, str(gecici))
    os.replace(gecici, hedef)
    kontrol = nib.load(str(hedef))
    return {
        "volume_name": ad, "durum": "yazildi", "affine_kaynak": kaynak, "notlar": ";".join(notlar),
        "ham_axcodes": "".join(nib.aff2axcodes(img.affine)),
        "yeni_axcodes": "".join(nib.aff2axcodes(kontrol.affine)),
        "yeni_sekil": "x".join(map(str, kontrol.shape)),
        "yeni_zoom": "x".join(f"{z:.4f}" for z in kontrol.header.get_zooms()[:3]),
    }


def asama_hazirla(args):
    b = kohort_317(args.manifest)
    GIRDI.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with Pool(args.isci) as havuz:
        satirlar = list(havuz.imap_unordered(hazirla_tek, b.volume_name.tolist()))
    df = pd.DataFrame(satirlar)
    eski = V5 / "hazirla_manifest.csv"
    if eski.exists():
        df = pd.concat([pd.read_csv(eski), df[df.durum != "vardi"]]).drop_duplicates("volume_name", keep="last")
    df.to_csv(eski, index=False)
    hata = df[df.durum.astype(str).str.startswith("HATA")]
    mevcut = sum((GIRDI / a).exists() for a in b.volume_name)
    print(f"hazirla: {time.time() - t0:.0f} sn, mevcut temiz girdi {mevcut}/317")
    if len(hata) or mevcut != 317:
        print(hata.to_string())
        sys.exit("DUR: hazirla kapisi KALDI")
    print("K-HAZIRLA GECTI")


# --------------------------------------------------------------------------- test

def sentetik_test():
    import nibabel as nib
    import torch
    tmp = CIKTI / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    zoom = (0.8, 0.7, 2.5)
    veri = np.full((100, 120, 40), -1000.0, dtype=np.float32)
    veri[40:60, 50:70, 15:25] = 1000.0
    beklenen_mm = [(40 + 59) / 2 * zoom[0], (50 + 69) / 2 * zoom[1], (15 + 24) / 2 * zoom[2]]
    beklenen_voksel = 20 * zoom[0] / SPACING[0] * 20 * zoom[1] / SPACING[1] * 10 * zoom[2] / SPACING[2]
    gecti = True
    p = tmp / "sentetik_kup.nii.gz"
    nib.save(nib.Nifti1Image(veri, np.diag(list(zoom) + [1.0])), str(p))
    for yontem in ("021", "meta"):
        _, cikti, _ = ornekle(p, yontem)
        dolu = torch.nonzero(cikti[0] > 0.5).double()
        merkez = [float(dolu[:, i].mean()) * SPACING[i] for i in range(3)]
        hata_mm = max(abs(a - b) for a, b in zip(merkez, beklenen_mm))
        oran = len(dolu) / beklenen_voksel
        tamam = hata_mm <= 1.5 and 0.9 <= oran <= 1.1
        print(f"sentetik {yontem}: kup merkezi mm={[round(m, 1) for m in merkez]} "
              f"beklenen={[round(m, 1) for m in beklenen_mm]} hata_mm={hata_mm:.1f} "
              f"hacim_orani={oran:.2f} {'TAMAM' if tamam else 'HATALI'}")
        if yontem == "meta" and not tamam:
            gecti = False
    p.unlink()
    return gecti


def panel_ciz(yol, baslik, hedef):
    """Orta kesitleri npz olarak kaydeder (sunucuda cizim kutuphanesi yok; PNG yerelde cizilir)."""
    girdi, cikti, meta = ornekle(yol, "meta")
    kesitler = {"baslik": baslik}
    for et, vol, sp in [("girdi", girdi[0].numpy(), meta.spacing), ("model", cikti[0].numpy(), SPACING)]:
        X, Y, Z = vol.shape
        kesitler[f"{et}_aksiyel"] = vol[:, :, Z // 2].astype(np.float16)
        kesitler[f"{et}_koronal"] = vol[:, Y // 2, :].astype(np.float16)
        kesitler[f"{et}_sagittal"] = vol[X // 2, :, :].astype(np.float16)
        kesitler[f"{et}_spacing"] = np.array(sp, dtype=np.float32)
    np.savez_compressed(hedef, **kesitler)


def cihaz_sec(istek):
    import torch
    try:
        x = torch.ones(4, device=istek) * 2
        torch.cuda.synchronize()
        assert float(x.sum()) == 8.0
        print(f"cihaz: {istek} {torch.cuda.get_device_name(istek)}", flush=True)
        return istek
    except Exception as e:  # noqa: BLE001
        sys.exit(f"DUR: {istek} kullanilamiyor ({str(e).splitlines()[0]}). Surucuye DOKUNMA.")


def model_yukle(cihaz):
    rse, *_ = spectre_yukle()
    from spectre.model import SpectreImageFeatureExtractor
    model = SpectreImageFeatureExtractor.from_pretrained(
        "spectre-large", include_feature_combiner=True, device=cihaz, verbose=True, strict=True)
    bas_yolu = Path(rse.SPECTRE_REPO_SNAPSHOT) / "SigLIP_projection_head_image.pt"
    if not bas_yolu.exists():
        from huggingface_hub import hf_hub_download
        bas_yolu = Path(hf_hub_download("cclaess/SPECTRE", "SigLIP_projection_head_image.pt"))
    bas, log = rse.load_siglip_head(str(bas_yolu), input_dim=2160, device=cihaz)
    print(f"SigLIP goruntu basi: {bas_yolu} missing={len(log['missing'])} "
          f"unexpected={len(log['unexpected'])}", flush=True)
    return model, bas


def gomme(model, bas, crops, grid, cihaz, max_crops):
    """v4 run_spectre_extraction.encode_image ile ayni: cls ve SigLIP projeksiyonu."""
    import torch
    with torch.inference_mode():
        f = model.extract([crops.to(cihaz)], grid_size=[grid], max_crops_per_forward=max_crops)[0]
        cls = f[0]
        proj = bas(torch.cat([cls, f[1:].mean(dim=0)], dim=0)[None])[0]
    return cls.float().cpu().numpy(), proj.float().cpu().numpy()


def asama_test(args):
    import torch
    torch.set_num_threads(args.threads)
    sha_kontrol(args.v4_ctrate_npz, V4_CTRATE_NPZ_SHA)
    if not sentetik_test():
        sys.exit("DUR: sentetik kup testi KALDI")
    cihaz = cihaz_sec(args.device)
    model, bas = model_yukle(cihaz)
    ct = ctrate_500(args.manifest, args.v4_ctrate_npz).volume_name.tolist()
    d = np.load(args.v4_ctrate_npz, allow_pickle=True)
    v4 = dict(zip([str(v) for v in d["volume_names"]], d["cls_embeds"]))
    ornekler = [("ctrate", ct[0]), ("ctrate", ct[1]),
                ("bimcv", "sub-S03825_ses-E07697_run-2_bp-chest_ct.nii.gz"),
                ("bimcv", "sub-S312107_ses-E64331_acq-1_run-1_bp-chest_ct.nii.gz"),
                ("bimcv", "sub-S03806_ses-E08207_run-2_bp-chest_ct.nii.gz")]
    panel = CIKTI / "test_panelleri"
    panel.mkdir(parents=True, exist_ok=True)
    gecti = True
    for veri, ad in ornekler:
        yol = girdi_yolu(veri, ad)
        g021, c021, _ = ornekle(yol, "021")
        r021 = geri_korelasyon(g021, c021)
        del g021, c021
        crops, grid, bilgi = kirpimlar(yol, "meta")
        cls, _ = gomme(model, bas, crops, grid, cihaz, args.max_crops)
        ek = ""
        if veri == "ctrate":
            ek = f" cos_v4={float(cls @ v4[ad] / (np.linalg.norm(cls) * np.linalg.norm(v4[ad]))):.4f}"
        print(f"{veri} {ad}: grid={grid} bos={bilgi['bos_kirpim_orani']} "
              f"geri_r_meta={bilgi['geri_korelasyon']} geri_r_021={r021:.4f} "
              f"k1={'OK' if bilgi['k1_gecti'] else bilgi['k1_nedenler']}{ek}", flush=True)
        panel_ciz(yol, f"{veri} {ad} grid={grid} bos={bilgi['bos_kirpim_orani']} geri_r={bilgi['geri_korelasyon']}",
                  panel / f"{veri}_{ad.replace('.nii.gz', '')}.npz")
        gecti = gecti and bilgi["k1_gecti"]
    if not gecti:
        sys.exit("DUR: K-TEST KALDI (gercek seride geri-korelasyon veya diger K1 kontrolu)")
    print("K-TEST GECTI")


# --------------------------------------------------------------------------- onizleme

def kucuk_resim(ad):
    import nibabel as nib
    import torch
    import torch.nn.functional as F
    img = nib.load(str(GIRDI / ad))
    v = img.get_fdata(dtype=np.float32)
    z = img.header.get_zooms()[:3]
    X, Y, Z = v.shape
    parcalar = []
    for kes, en_mm, boy_mm in [(v[:, :, Z // 2].T[::-1], X * z[0], Y * z[1]),
                               (v[:, Y // 2, :].T[::-1], X * z[0], Z * z[2])]:
        s = 120 / max(en_mm, boy_mm)
        h, w = max(1, min(120, int(boy_mm * s))), max(1, min(120, int(en_mm * s)))
        t = F.interpolate(torch.from_numpy(np.ascontiguousarray(kes))[None, None], size=(h, w),
                          mode="bilinear", align_corners=False)[0, 0]
        kutu = np.zeros((120, 120), dtype=np.float32)
        y0, x0 = (120 - h) // 2, (120 - w) // 2
        kutu[y0:y0 + h, x0:x0 + w] = np.clip((t.numpy() + 1000) / 1400, 0, 1)
        parcalar.append(kutu)
    return ad, np.concatenate(parcalar, axis=1)


def asama_onizleme(args):
    """Kucuk resimleri tek npz'ye yazar (sayfalar yerelde cizilir)."""
    b = kohort_317(args.manifest)
    hedef = CIKTI / "onizleme"
    hedef.mkdir(parents=True, exist_ok=True)
    adlar = b.volume_name.tolist()
    with Pool(args.isci) as havuz:
        sonuc = dict(havuz.map(kucuk_resim, adlar))
    np.savez_compressed(hedef / "bimcv317_kucuk_resimler.npz", adlar=np.array(adlar),
                        resimler=np.stack([sonuc[a] for a in adlar]).astype(np.float16))
    print(f"ONIZLEME YAZILDI: {hedef / 'bimcv317_kucuk_resimler.npz'} ({len(adlar)} seri; sol aksiyel, sag koronal)")


# --------------------------------------------------------------------------- cikar / rapor

def liste_al(args):
    if args.veri == "ctrate":
        return ctrate_500(args.manifest, args.v4_ctrate_npz)
    b = kohort_317(args.manifest)
    if args.liste == "pilot":
        cokmus = cokmus_seriler(args.v4_bimcv_npz)
        c = [a for a in b.volume_name if a in cokmus]
        n = [a for a in b.volume_name if a not in cokmus][:10]
        return b.set_index("volume_name").loc[c + n].reset_index()
    return b


def girdi_yolu(veri, ad):
    return (CT_GIRDI if veri == "ctrate" else GIRDI) / ad


def asama_cikar(args):
    import torch
    torch.set_num_threads(args.threads)
    liste = liste_al(args).volume_name.tolist()[args.shard::args.nshard]
    dizin = CIKTI / "seriler" / args.veri
    dizin.mkdir(parents=True, exist_ok=True)
    cihaz = cihaz_sec(args.device)
    model, bas = model_yukle(cihaz)
    t0 = time.time()
    for i, ad in enumerate(liste):
        hedef = dizin / f"{ad}.npz"
        if hedef.exists():
            continue
        t = time.time()
        crops, grid, bilgi = kirpimlar(girdi_yolu(args.veri, ad), "meta")
        cls, proj = gomme(model, bas, crops, grid, cihaz, args.max_crops)
        bilgi.update({"sure_sn": round(time.time() - t, 1), "cihaz": cihaz})
        gecici = dizin / f".{os.getpid()}_{ad}.npz"
        np.savez(gecici, cls=cls, proj=proj, bilgi=json.dumps(bilgi))
        os.replace(gecici, hedef)
        print(f"[{args.veri} {args.shard}/{args.nshard}] {i + 1}/{len(liste)} {ad} grid={grid} "
              f"geri_r={bilgi['geri_korelasyon']} bos={bilgi['bos_kirpim_orani']} "
              f"k1={'OK' if bilgi['k1_gecti'] else bilgi['k1_nedenler']} {bilgi['sure_sn']}sn "
              f"toplam={time.time() - t0:.0f}sn", flush=True)


def katilim_orani(E):
    s = np.linalg.svd(E - E.mean(0), compute_uv=False)
    return float((s ** 2).sum() ** 2 / (s ** 4).sum())


def kapilar(E):
    hata = []
    if not np.isfinite(E).all():
        hata.append("NaN/inf embedding")
    _, ters, sayi = np.unique(E, axis=0, return_inverse=True, return_counts=True)
    kopya = int((sayi[ters.ravel()] > 1).sum())
    En = E / np.linalg.norm(E, axis=1, keepdims=True)
    S = En @ En.T
    np.fill_diagonal(S, -1)
    yakin = int((np.triu(S, 1) > YAKIN_KOPYA_COS).sum())
    Xc = E - E.mean(0)
    Xc = Xc / np.linalg.norm(Xc, axis=1, keepdims=True)
    Sc = Xc @ Xc.T
    np.fill_diagonal(Sc, -1)
    bilgi = {"n": len(E), "birebir_kopya_seri": kopya, "yakin_kopya_cift": yakin,
             "katilim_orani": round(katilim_orani(E), 2),
             "merkezli_en_yakin_cos_medyan": round(float(np.median(Sc.max(1))), 4)}
    if kopya:
        hata.append(f"birebir kopya {kopya} seri")
    if yakin:
        hata.append(f"cos>{YAKIN_KOPYA_COS} {yakin} cift")
    return hata, bilgi


def asama_rapor(args):
    tablo = liste_al(args)
    liste = tablo.volume_name.tolist()
    dizin = CIKTI / "seriler" / args.veri
    eksik = [a for a in liste if not (dizin / f"{a}.npz").exists()]
    if eksik:
        sys.exit(f"DUR: {len(eksik)} seri eksik, ornek {eksik[:3]}")
    cls, proj, satirlar = [], [], []
    for a in liste:
        z = np.load(dizin / f"{a}.npz")
        cls.append(z["cls"])
        proj.append(z["proj"])
        satirlar.append({"volume_name": a, **json.loads(str(z["bilgi"]))})
    E = np.stack(cls).astype(np.float32)
    P = np.stack(proj).astype(np.float32)
    man = pd.DataFrame(satirlar)
    hata, bilgi = kapilar(E)
    k1 = man[~man.k1_gecti]
    if len(k1):
        hata.append(f"K1 kalan {len(k1)} seri")
    if not np.isfinite(P).all():
        hata.append("proj NaN/inf")

    v4_yol = args.v4_ctrate_npz if args.veri == "ctrate" else args.v4_bimcv_npz
    d = np.load(v4_yol, allow_pickle=True)
    v4_adlar = [str(v) for v in d["volume_names"]]
    v4_cls = dict(zip(v4_adlar, d["cls_embeds"]))
    v4_txt = dict(zip(v4_adlar, d["text_embeds"]))
    man["cos_v4"] = [float(e @ v4_cls[a] / (np.linalg.norm(e) * np.linalg.norm(v4_cls[a])))
                     for e, a in zip(E, liste)]

    pilot = args.veri == "bimcv" and args.liste == "pilot"
    ek = f"{args.veri}_{'pilot' if pilot else len(liste)}"
    man.to_csv(CIKTI / f"spectre_{ek}_v5_manifest.csv", index=False)
    uyari = man[man.bos_uyari]
    rapor = [f"# SPECTRE v5 (duzeltilmis yeniden ornekleme) kapi raporu: {ek}", "",
             f"Seri: {len(liste)}", f"Kapilar: {json.dumps(bilgi, ensure_ascii=False)}",
             f"K1 kalan seri: {len(k1)}",
             f"Geri-korelasyon min/medyan: {man.geri_korelasyon.min():.4f} / {man.geri_korelasyon.median():.4f}",
             f"Bos kirpim orani medyan/maks: {man.bos_kirpim_orani.median():.3f} / {man.bos_kirpim_orani.max():.3f}",
             f"Bos kirpim > {BOS_UYARI} (uyari, sert hata degil): {len(uyari)} seri",
             f"Sekil hatasi maks: {man.sekil_hata.max():.4f}",
             f"n_crops min/medyan/maks: {man.n_crops.min()} / {man.n_crops.median():.0f} / {man.n_crops.max()}",
             f"v4 ile cos medyan (v4 hatali yoldan uretildi, fark beklenir): {man.cos_v4.median():.4f}",
             "", "SERT HATALAR: " + ("YOK" if not hata else "; ".join(hata))]
    if len(k1):
        rapor += ["", k1[["volume_name", "k1_nedenler", "geri_korelasyon", "bos_kirpim_orani", "grid"]].to_string()]
    if len(uyari):
        rapor += ["", "Uyari listesi:",
                  uyari[["volume_name", "bos_kirpim_orani", "geri_korelasyon", "grid"]].to_string()]
    (CIKTI / f"kapi_raporu_{ek}.md").write_text("\n".join(rapor), encoding="utf-8")
    print("\n".join(rapor))
    if hata:
        sys.exit(f"DUR: {ek} kapisi KALDI")
    if not pilot:
        yol = CIKTI / f"spectre_{ek}_v5_embeddings.npz"
        np.savez_compressed(
            yol, cls_embeds=E, proj_embeds=P,
            text_embeds=np.stack([v4_txt[a] for a in liste]).astype(np.float32),
            volume_names=np.array(liste), patient_ids=tablo.patient_id.astype(str).values,
            study_ids=tablo.study_id.astype(str).values, num_crops=man.n_crops.values.astype(np.int32))
        print("YAZILDI:", yol, sha256_dosya(yol))
    print(f"{ek.upper()} KAPISI GECTI")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asama", choices=["hazirla", "test", "onizleme", "cikar", "rapor"])
    ap.add_argument("--veri", choices=["bimcv", "ctrate"], default="bimcv")
    ap.add_argument("--liste", choices=["pilot", "tum"], default="tum")
    ap.add_argument("--manifest", default=str(V4 / "cohort_manifest.csv"))
    ap.add_argument("--v4-bimcv-npz", default=str(V4 / "spectre_bimcv_embeddings.npz"))
    ap.add_argument("--v4-ctrate-npz", default=str(V4 / "spectre_ctrate_embeddings.npz"))
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--isci", type=int, default=16)
    ap.add_argument("--max-crops", type=int, default=32)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshard", type=int, default=1)
    args = ap.parse_args()
    CIKTI.mkdir(parents=True, exist_ok=True)
    if args.asama in ("cikar", "rapor"):
        if args.veri == "ctrate":
            sha_kontrol(args.v4_ctrate_npz, V4_CTRATE_NPZ_SHA)
        else:
            sha_kontrol(args.v4_bimcv_npz, V4_BIMCV_NPZ_SHA)
    {"hazirla": asama_hazirla, "test": asama_test, "onizleme": asama_onizleme,
     "cikar": asama_cikar, "rapor": asama_rapor}[args.asama](args)


if __name__ == "__main__":
    main()
