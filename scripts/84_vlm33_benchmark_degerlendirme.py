# -*- coding: utf-8 -*-
"""SUDE-VLM-33: uc 3B BT temel modelinin (SPECTRE-Large, M3D-CLIP, MG-3D Swin-B) benchmark
degerlendirmesi. Paketteki metrik kodu kullanilmaz; iki hatasi var
(bootstrap tekrarlari set() ile siliyor, yalniz seed=0 kullaniliyor).

Protokol:
  - Paketin donmus kat dosyasi (StratifiedGroupKFold, hasta gruplu, seed 0-4).
  - StandardScaler + LogisticRegression(C=1, class_weight=balanced), paketle ayni.
  - Birincil deger: 5 tohumun ortalamasi. Seed 0 paketle karsilastirma icin.
  - %95 GA: hasta-kumeli bootstrap, tekrar secilen hastalar tekrar sayisi kadar.
    Model farklari ayni orneklemle eslestirilir.
  - Sinif bazinda farklar: bootstrap SE ile normal yaklasim p, Holm duzeltmesi.
  - Retrieval: sabit aday havuzu, yalniz sorgu hastalari yeniden orneklenir.
    CT-RATE'te no_chest seriler cikarilip calisma basina ilk seri alinir.
  - Sybil: BIMCV-317, 1. yil skoru, 0,20 esigi; hedef rapor-kokenli nodul.

Girdi:  data/external/model_benchmarks_v4/{spectre,m3d,mg3d}/
        bimcv-analysis/BIMCV_Sybil_Pillar_Astra_317_Clean_Results.xlsx
        data/external/vlm33_spectre/v2/ (SPECTRE, duzeltilmis yeniden ornekleme; scripts/85_vlm33_spectre_embedding_cikarimi.py)
Cikti:  outputs/vlm33/sonuclar.json, outputs/vlm33/ozet.txt
"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, norm, rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

KOK = Path(__file__).resolve().parents[1]
B = KOK / "data" / "external" / "model_benchmarks_v4"
CIKTI = KOK / "outputs" / "vlm33"
V5_SPECTRE = KOK / "data" / "external" / "vlm33_spectre" / "v2"
KALITE = KOK / "outputs" / "vlm33" / "bimcv317_gorsel_kalite.csv"
MODELLER = ["spectre", "mg3d", "m3d"]
TOHUMLAR = range(5)
NB = 2000
RNG_SEED = 20260915

fa = pd.read_csv(B / "spectre" / "fold_assignments.csv")
manifest = pd.read_csv(B / "spectre" / "cohort_manifest.csv")


def embedding_yukle(model, ds):
    if model == "spectre":  # v5: duzeltilmis yeniden ornekleme (scripts/85_vlm33_spectre_embedding_cikarimi.py)
        yol = V5_SPECTRE / f"spectre_{'ctrate_500' if ds == 'ctrate' else 'bimcv_317'}_v5_embeddings.npz"
    else:
        yol = B / model / f"{model}_{ds}_embeddings.npz"
    d = np.load(yol, allow_pickle=True)
    img = d["cls_embeds"] if "cls_embeds" in d else d["img_embeds"]
    out = {"img": img, "vols": [str(v) for v in d["volume_names"]],
           "pids": [str(p) for p in d["patient_ids"]],
           "studies": [str(s) for s in d["study_ids"]]}
    if "text_embeds" in d:
        out["text"] = d["text_embeds"]
        out["proj"] = d["proj_embeds"] if "proj_embeds" in d else d["img_embeds"]
    return out


def oof_hesapla(model, ds, alt=None):
    """{sinif: (y, [p_seed0..p_seed4])}, satir sirasi tum siniflarda ayni."""
    E = embedding_yukle(model, ds)
    vi = {v: i for i, v in enumerate(E["vols"])}
    sonuc, vols, pids = {}, None, None
    for seed in TOHUMLAR:
        s = fa[(fa.dataset == ds) & (fa.seed == seed)]
        if alt is not None:
            s = s[s.volume_name.isin(alt)]
        for c, g in s.groupby("class"):
            if vols is None:
                vols, pids = g.volume_name.values, g.patient_id.values
            assert (g.volume_name.values == vols).all(), "sinif satir sirasi farkli"
            X = E["img"][[vi[v] for v in g.volume_name]]
            y, f = g.label.values.astype(int), g.fold.values
            p = np.zeros(len(y))
            for k in range(5):
                tr = f != k
                if len(np.unique(y[tr])) < 2 or (~tr).sum() == 0:
                    p[~tr] = np.nan
                    continue
                sc = StandardScaler().fit(X[tr])
                clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=5000,
                                         random_state=42)
                clf.fit(sc.transform(X[tr]), y[tr])
                p[~tr] = clf.predict_proba(sc.transform(X[~tr]))[:, 1]
            sonuc.setdefault(c, (y, []))[1].append(p)
    return sonuc, vols, pids


def auc(y, p):
    if np.isnan(p).any():
        return np.nan
    n1 = y.sum()
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(p)
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def ap(y, p):
    if y.sum() == 0 or np.isnan(p).any():
        return np.nan
    o = np.argsort(-p, kind="stable")
    ys = y[o]
    tp = np.cumsum(ys)
    return float((tp[ys == 1] / (np.nonzero(ys)[0] + 1)).mean())


def bootstrap_indeksleri(pids, rng, nb=NB):
    """Hasta-kumeli bootstrap; tekrar secilen hastanin satirlari tekrar eder."""
    up = np.unique(pids)
    satir = {p: np.where(pids == p)[0] for p in up}
    return [np.concatenate([satir[p] for p in rng.choice(up, len(up), replace=True)])
            for _ in range(nb)]


def olcutler(O, siniflar, idx):
    """Model basina: 5 tohum ortalamasi ve seed 0 icin sinif AUC/AP, Macro, Micro."""
    out = {}
    for m, o in O.items():
        auc_s = np.array([[auc(o[c][0][idx], o[c][1][s][idx]) for c in siniflar]
                          for s in TOHUMLAR])
        ap_s = np.array([[ap(o[c][0][idx], o[c][1][s][idx]) for c in siniflar]
                         for s in TOHUMLAR])
        yt = np.concatenate([o[c][0][idx] for c in siniflar])
        micro_s = np.array([auc(yt, np.concatenate([o[c][1][s][idx] for c in siniflar]))
                            for s in TOHUMLAR])
        out[m] = {
            "sinif_auc": np.nanmean(auc_s, axis=0),
            "macro_auc": np.nanmean(np.nanmean(auc_s, axis=1)),
            "macro_auc_seed0": np.nanmean(auc_s[0]),
            "micro_auc": micro_s.mean(),
            "macro_ap": np.nanmean(np.nanmean(ap_s, axis=1)),
            "sinif_auc_seed0": auc_s[0],
        }
    return out


def ga(x):
    x = np.asarray(x, dtype=float)
    return [round(float(np.nanpercentile(x, 2.5)), 4), round(float(np.nanpercentile(x, 97.5)), 4)]


def holm(pler):
    pler = np.asarray(pler)
    o = np.argsort(pler)
    k = len(pler)
    duz = np.empty(k)
    enb = 0.0
    for sira, i in enumerate(o):
        enb = max(enb, min(1.0, (k - sira) * pler[i]))
        duz[i] = enb
    return duz


def siniflama(ds, modeller, rng, alt=None):
    O = {}
    for m in modeller:
        O[m], vols, pids = oof_hesapla(m, ds, alt)
    siniflar = sorted(O[modeller[0]])
    nokta = olcutler(O, siniflar, np.arange(len(pids)))
    boot = [olcutler(O, siniflar, idx) for idx in bootstrap_indeksleri(pids, rng)]

    sonuc = {"n_seri": int(len(vols)), "n_hasta": int(len(np.unique(pids))),
             "siniflar": siniflar, "modeller": {}, "farklar": {}, "sinif_farklari": []}
    for m in modeller:
        sonuc["modeller"][m] = {
            k: {"deger": round(float(nokta[m][k]), 4), "ga": ga([b[m][k] for b in boot])}
            for k in ["macro_auc", "macro_auc_seed0", "micro_auc", "macro_ap"]}
        sonuc["modeller"][m]["sinif"] = {
            c: {"pozitif": int(O[m][c][0].sum()),
                "auc": round(float(nokta[m]["sinif_auc"][j]), 4),
                "auc_seed0": round(float(nokta[m]["sinif_auc_seed0"][j]), 4),
                "ga": ga([b[m]["sinif_auc"][j] for b in boot])}
            for j, c in enumerate(siniflar)}

    ciftler = [(a, b) for i, a in enumerate(modeller) for b in modeller[i + 1:]]
    for a, b in ciftler:
        for k in ["macro_auc", "micro_auc", "macro_ap"]:
            d = np.array([x[a][k] - x[b][k] for x in boot])
            sonuc["farklar"][f"{a}-{b}:{k}"] = {
                "deger": round(float(nokta[a][k] - nokta[b][k]), 4), "ga": ga(d)}

    # sinif bazinda eslestirilmis farklar, Holm
    satirlar = []
    for a, b in ciftler:
        for j, c in enumerate(siniflar):
            d = np.array([x[a]["sinif_auc"][j] - x[b]["sinif_auc"][j] for x in boot])
            fark = float(nokta[a]["sinif_auc"][j] - nokta[b]["sinif_auc"][j])
            se = float(np.nanstd(d, ddof=1))
            satirlar.append({"cift": f"{a}-{b}", "sinif": c, "fark": round(fark, 4),
                             "ga": ga(d), "p": float(2 * norm.sf(abs(fark) / se))})
    for s, ph in zip(satirlar, holm([s["p"] for s in satirlar])):
        s["p_holm"] = float(ph)
        s["p"] = round(s["p"], 5)
    sonuc["sinif_farklari"] = satirlar
    return sonuc, O, vols, pids


def calisma_pozisyonlari(img, txt):
    img = img / np.linalg.norm(img, axis=1, keepdims=True)
    txt = txt / np.linalg.norm(txt, axis=1, keepdims=True)
    S = img @ txt.T
    n = len(S)
    i2t = np.array([np.nonzero(np.argsort(-S[i], kind="stable") == i)[0][0] + 1 for i in range(n)])
    t2i = np.array([np.nonzero(np.argsort(-S[:, j], kind="stable") == j)[0][0] + 1 for j in range(n)])
    return i2t, t2i


def retrieval(ds, modeller, rng):
    ranks, pids_ref = {}, None
    for m in modeller:
        E = embedding_yukle(m, ds)
        meta = pd.DataFrame({"vol": E["vols"], "pid": E["pids"], "study": E["studies"]})
        if ds == "ctrate":
            gogus_disi = set(manifest[(manifest.dataset == "ctrate") & (~manifest.in_primary)].volume_name)
            meta = meta[~meta.vol.isin(gogus_disi)].drop_duplicates("study")
        else:
            birincil = set(manifest[(manifest.dataset == "bimcv") & manifest.in_primary].volume_name)
            meta = meta[meta.vol.isin(birincil)].sort_values("vol")
        idx = meta.index.values
        assert not np.isnan(E["text"][idx]).any()
        if pids_ref is None:
            pids_ref = meta.pid.values
        assert (meta.pid.values == pids_ref).all()
        ranks[m] = calisma_pozisyonlari(E["proj"][idx], E["text"][idx])

    def ozet(r):
        return {"R@1": 100 * np.mean(r <= 1), "R@5": 100 * np.mean(r <= 5),
                "R@10": 100 * np.mean(r <= 10), "R@50": 100 * np.mean(r <= 50),
                "MedR": float(np.median(r))}

    boots = bootstrap_indeksleri(pids_ref, rng)
    n = len(pids_ref)
    sonuc = {"n_aday": int(n), "rastgele": {f"R@{k}": round(100 * k / n, 2) for k in (1, 5, 10, 50)},
             "modeller": {}, "farklar": {}}
    sonuc["rastgele"]["MedR"] = (n + 1) / 2
    for m in modeller:
        sonuc["modeller"][m] = {}
        for yon, r in zip(["I2T", "T2I"], ranks[m]):
            p = ozet(r)
            bb = [ozet(r[i]) for i in boots]
            sonuc["modeller"][m][yon] = {k: {"deger": round(float(v), 2), "ga": [round(x, 2) for x in ga([b[k] for b in bb])]}
                                         for k, v in p.items()}
    if len(modeller) == 2:
        a, b = modeller
        for j, yon in enumerate(["I2T", "T2I"]):
            for k in ["R@10", "R@50"]:
                kk = int(k[2:])
                d = [100 * (np.mean(ranks[a][j][i] <= kk) - np.mean(ranks[b][j][i] <= kk)) for i in boots]
                nokta = 100 * (np.mean(ranks[a][j] <= kk) - np.mean(ranks[b][j] <= kk))
                sonuc["farklar"][f"{a}-{b}:{yon}:{k}"] = {"deger": round(nokta, 2), "ga": [round(x, 2) for x in ga(d)]}
    return sonuc


def calisma_noktalari(O, sinif):
    """Tohum basina ozgulluk %90'da duyarlilik ve duyarlilik %80'de ozgulluk, ortalama."""
    from sklearn.metrics import roc_curve
    out = {}
    for m, o in O.items():
        y = o[sinif][0]
        s90, o80 = [], []
        for p in o[sinif][1]:
            fpr, tpr, _ = roc_curve(y, p)
            s90.append(tpr[fpr <= 0.10].max())
            o80.append(1 - fpr[tpr >= 0.80].min())
        out[m] = {"duyarlilik_ozgulluk90": round(float(np.mean(s90)), 3),
                  "ozgulluk_duyarlilik80": round(float(np.mean(o80)), 3)}
    return out


def sybil(O, vols, pids, rng):
    x = pd.ExcelFile(KOK / "bimcv-analysis" / "BIMCV_Sybil_Pillar_Astra_317_Clean_Results.xlsx")
    sk = x.parse(0)
    skor = dict(zip(sk.iloc[:, 3].astype(str), sk.iloc[:, 5].astype(float)))
    assert set(vols) <= set(skor), "Sybil Excel ile OOF seri kumesi farkli"
    s = np.array([skor[v] for v in vols])
    y = O[next(iter(O))]["nodule"][0]
    for o in O.values():
        assert (o["nodule"][0] == y).all()
    alarm = s >= 0.20
    sonuc = {"karisiklik": {"TP": int((alarm & (y == 1)).sum()), "FN": int((~alarm & (y == 1)).sum()),
                            "FP": int((alarm & (y == 0)).sum()), "TN": int((~alarm & (y == 0)).sum())},
             "sybil_nodul_auc": round(float(auc(y, s)), 4)}
    neg = np.where(~alarm)[0]
    yn, pn = y[neg], pids[neg]
    N, K, k_alarm = len(neg), int(yn.sum()), int(alarm.sum())
    sonuc.update({"negatif_havuz": N, "negatif_havuz_nodul": K,
                  "rastgele_beklenen": round(k_alarm * K / N, 2), "ek_alarm": k_alarm, "modeller": {}})
    boots = bootstrap_indeksleri(pn, rng)
    for m, o in O.items():
        ps = [p[neg] for p in o["nodule"][1]]
        nokta = np.mean([auc(yn, p) for p in ps])
        bb = [np.mean([auc(yn[i], p[i]) for p in ps]) for i in boots]
        ort = np.mean(ps, axis=0)
        ust = np.argsort(-ort, kind="stable")[:k_alarm]
        kurt = int(yn[ust].sum())
        sonuc["modeller"][m] = {"auc": round(float(nokta), 4), "ga": ga(bb),
                                "kurtarilan": kurt, "ek_fp": k_alarm - kurt,
                                "p_rastgele": round(float(hypergeom.sf(kurt - 1, N, K, k_alarm)), 3)}
    return sonuc


def main():
    CIKTI.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    sonuc = {"protokol": {"bootstrap": NB, "tohum": list(TOHUMLAR), "rng": RNG_SEED}}

    ct, O_ct, _, _ = siniflama("ctrate", MODELLER, rng)
    ct["nodul_calisma_noktalari"] = calisma_noktalari(O_ct, "Lung nodule")
    sonuc["ctrate_siniflama"] = ct
    sonuc["ctrate_retrieval"] = retrieval("ctrate", ["spectre", "m3d"], rng)

    bm, O_bm, vols, pids = siniflama("bimcv", MODELLER, rng)
    bm["nodul_calisma_noktalari"] = calisma_noktalari(O_bm, "nodule")
    sonuc["bimcv_siniflama"] = bm
    sonuc["bimcv_retrieval"] = retrieval("bimcv", ["spectre", "m3d"], rng)
    sonuc["sybil_negatif_havuz"] = sybil(O_bm, vols, pids, rng)

    # duyarlilik: gorsel kalite kontrolunde geometrisi temiz 256 seri (probe yeniden egitilir)
    k = pd.read_csv(KALITE)
    temiz = set(k[k.gorsel == "normal"].ad)
    bt, O_bt, vols_t, pids_t = siniflama("bimcv", MODELLER, rng, alt=temiz)
    sonuc["bimcv_temiz_siniflama"] = bt
    sonuc["sybil_negatif_havuz_temiz"] = sybil(O_bt, vols_t, pids_t, rng)

    (CIKTI / "sonuclar.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False), encoding="utf-8")

    satir = []
    for ad in ["ctrate_siniflama", "bimcv_siniflama", "bimcv_temiz_siniflama"]:
        r = sonuc[ad]
        satir.append(f"== {ad} n={r['n_seri']} hasta={r['n_hasta']}")
        for m, v in r["modeller"].items():
            satir.append("  " + m + " " + " | ".join(f"{k} {x['deger']} {x['ga']}" for k, x in v.items() if k != "sinif"))
        for k, v in r["farklar"].items():
            satir.append(f"  {k} {v['deger']:+} {v['ga']}")
        for s in r["sinif_farklari"]:
            if s["p_holm"] < 0.05:
                satir.append(f"  holm<0,05 {s['cift']} {s['sinif']} {s['fark']:+} {s['ga']} p_holm={s['p_holm']:.4f}")
    (CIKTI / "ozet.txt").write_text("\n".join(satir), encoding="utf-8")
    print("\n".join(satir))


if __name__ == "__main__":
    main()
