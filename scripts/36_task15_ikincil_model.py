# -*- coding: utf-8 -*-
"""TASK-15 · IKINCIL MODEL kosusu - UZAK GPU makinesinde calisir.

NE YAPAR: Bir kolun (TR / EN-genel / EN-ucuz) 46 `dev` belgesini secilen modele
tek tek verir, kapali JSON sozlesmesine gore dogrular, ham yaniti saklar ve
kapi olcumlerini yazar.

NE YAPMAZ:
  * Gecersiz ciktiyi ONARMAZ (docs/19 §4.2 - "sonradan icerik onarimi yapilmaz")
  * Icerige gore istem DEGISTIRMEZ, elle duzeltme YAPMAZ
  * Altin etiket GORMEZ - bu pakette altin YOKTUR
  * `test` bolumune DOKUNMAZ

KAPILAR (docs/19, testten once donduruldu):
  1. Calisabilirlik : butun belgeler OOM/kesilme/kalici hata olmadan tamamlanir
  2. Yapisal gecerlilik : ciktilarin %100'u dogrudan ayristirilabilir olmali
  3. Kapali envanter : envanter disi concept_id / gecersiz assertion orani SIFIR
  4. Dogruluk : ALTIN GEREKTIRIR - bu betikte HESAPLANMAZ, yerel adimda yapilir
  5. Dil dengesi : uc kol kosulduktan sonra YEREL karsilastirmada olculur
  6. Esitlik : tepe VRAM ve sure bu betikte olculur, secimde kullanilir

Kullanim (her model x her kol icin bir kez):
  python scripts/36_task15_ikincil_model.py \
      --model Qwen/Qwen3.5-4B --kol tr \
      --girdi girdi/tr_dev.jsonl --cikti cikti/qwen_tr_dev.jsonl

Butun kollar icin: bkz. OKU_BENI.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation.ikincil_model import (  # noqa: E402
    ISTEM_SURUMU,
    IkincilModelAdapter,
    envanter_blogu,
    istemi_yukle,
)
from radyovlm.evaluation.task15 import (  # noqa: E402
    ContractError,
    load_inventory,
    parse_model_output,
    require_development_split,
)

MODELLER = {
    "Qwen/Qwen3.5-4B": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "CohereLabs/aya-expanse-8b": "5062468bf9bc0c6035fd64e06274333ec127d980",
}
KOLLAR = ("tr", "en-genel", "en-ucuz")
MANIFEST_KOLLARI = {"tr": "tr", "en-genel": "en_genel", "en-ucuz": "en_ucuz"}
ERKEN_PENCERE = 8      # ilk kac belgeye bakilir
ERKEN_ESIK = 0.60      # bu oranda ihlal olursa durulur (D59 dersi)


def sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with yol.open("rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def jsonl_oku(yol: Path) -> list[dict]:
    with yol.open(encoding="utf-8") as f:
        return [json.loads(s) for s in f if s.strip()]


def girdiyi_dogrula(kayitlar: list[dict]) -> None:
    """Girdi paketini sozlesmeye gore sinar - bozuk girdi sessizce gecmez."""
    if not kayitlar:
        raise ContractError("Girdi bos")
    gorulen = set()
    for beklenen_sira, k in enumerate(kayitlar):
        if set(k) != {"document_id", "order", "text"}:
            raise ContractError(
                f"Girdi alanlari sozlesmeye uymuyor (satir {beklenen_sira}): {sorted(k)}"
            )
        if type(k["order"]) is not int or k["order"] != beklenen_sira:
            raise ContractError(f"Girdi sirasi kesintisiz degil: {k['order']}")
        if type(k["document_id"]) is not str or not k["document_id"].strip():
            raise ContractError(f"Gecersiz document_id: satir {beklenen_sira}")
        if k["document_id"] in gorulen:
            raise ContractError(f"Tekrarli document_id: {k['document_id']}")
        gorulen.add(k["document_id"])
        if not isinstance(k["text"], str) or not k["text"].strip():
            raise ContractError(f"Bos metin: {k['document_id']}")


def paket_butunlugunu_dogrula() -> dict:
    """Manifestte dondurulan her girdiyi/kodu kosudan once hash ile dogrula."""
    yol = KOK / "paket_manifest.json"
    if not yol.exists():
        raise ContractError("paket_manifest.json yok")
    manifest = json.loads(yol.read_text(encoding="utf-8"))
    if manifest.get("model_revizyonlari") != MODELLER:
        raise ContractError("Manifest model revizyonlari kosucu ile uyusmuyor")
    beklenen = dict(manifest["dosya_sha256"])
    for bilgi in manifest["girdi"].values():
        beklenen[f"girdi/{bilgi['dosya']}"] = bilgi["sha256"]
    beklenen[f"envanter/{manifest['envanter']['dosya']}"] = manifest["envanter"][
        "sha256"
    ]
    for goreli, beklenen_hash in beklenen.items():
        dosya = KOK / goreli
        if not dosya.is_file() or sha256(dosya) != beklenen_hash:
            raise ContractError(f"Paket butunluk hatasi: {goreli}")
    return manifest


def kol_girdisini_dogrula(yol: Path, kol: str, manifest: dict) -> None:
    """Komuttaki girdi secilen kolun dondurulmus dosyasi olmali."""
    bilgi = manifest["girdi"][MANIFEST_KOLLARI[kol]]
    if not yol.is_file() or sha256(yol) != bilgi["sha256"]:
        raise ContractError(f"--girdi secilen {kol} koluyla eslesmiyor")


def devam_kayitlarini_dogrula(
    onceki: list[dict], kayitlar: list[dict], adapter: str, kol: str
) -> None:
    """Devam dosyasi ayni kosunun kesintisiz on eki olmali."""
    if len(onceki) > len(kayitlar):
        raise ContractError("Devam dosyasi girdiden uzun")
    for sira, satir in enumerate(onceki):
        if (
            satir.get("order") != sira
            or satir.get("document_id") != kayitlar[sira]["document_id"]
            or satir.get("adapter") != adapter
            or satir.get("kol") != kol
        ):
            raise ContractError(f"Devam dosyasi farkli/kesintili kosu tasiyor: satir {sira}")


def tepe_vram_mib() -> float | None:
    try:
        import torch

        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / (1024**2)
    except Exception:  # noqa: BLE001 - olcum yoksa kosu durmaz
        pass
    return None


def ortam_bilgisi() -> dict:
    bilgi = {"python": platform.python_version(), "platform": platform.platform()}
    try:
        import torch

        bilgi["torch"] = torch.__version__
        bilgi["cuda_var"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            bilgi["gpu"] = torch.cuda.get_device_name(0)
            bilgi["gpu_toplam_mib"] = (
                torch.cuda.get_device_properties(0).total_memory / (1024**2)
            )
    except Exception as exc:  # noqa: BLE001
        bilgi["torch"] = f"okunamadi: {exc}"
    try:
        import transformers

        bilgi["transformers"] = transformers.__version__
    except Exception as exc:  # noqa: BLE001
        bilgi["transformers"] = f"okunamadi: {exc}"
    return bilgi


def main() -> int:
    ap = argparse.ArgumentParser(description="TASK-15 ikincil model kosusu")
    ap.add_argument("--model", required=True, choices=tuple(MODELLER))
    ap.add_argument("--kol", required=True, choices=KOLLAR)
    ap.add_argument("--girdi", required=True, type=Path)
    ap.add_argument("--cikti", required=True, type=Path)
    ap.add_argument(
        "--dort-bit",
        action="store_true",
        help="4-bit nicemleme (yalniz bellek yetmezse; provenance'a yazilir)",
    )
    ap.add_argument("--devam", action="store_true", help="yarim kalan kosuyu surdur")
    a = ap.parse_args()

    # ---- KAPI 0: test bolumu dokunulmazdir -------------------------------
    require_development_split("dev")
    manifest = paket_butunlugunu_dogrula()

    envanter_yolu = KOK / "envanter" / "envanter_144.yaml"
    istem_yolu = KOK / "istem" / "ikincil_model_v2.txt"
    envanter = load_inventory(envanter_yolu)       # 144 olmali, yoksa durur
    sablon = istemi_yukle(istem_yolu)
    kol_girdisini_dogrula(a.girdi, a.kol, manifest)
    kayitlar = jsonl_oku(a.girdi)
    girdiyi_dogrula(kayitlar)

    revizyon = MODELLER[a.model]
    adapter = IkincilModelAdapter(
        model_id=a.model,
        istem_sablonu=sablon,
        envanter_metni=envanter_blogu(envanter),
        revision=revizyon,
        dort_bit=a.dort_bit,
        max_new_tokens=2048,
        dusunme_kapali=True,
    )

    a.cikti.parent.mkdir(parents=True, exist_ok=True)
    tamamlanan: dict[str, dict] = {}
    if a.devam and a.cikti.exists():
        onceki = jsonl_oku(a.cikti)
        devam_kayitlarini_dogrula(onceki, kayitlar, adapter.name, a.kol)
        tamamlanan = {r["document_id"]: r for r in onceki}
        print(f"DEVAM: {len(tamamlanan)} belge zaten var, atlanacak")
    elif a.cikti.exists():
        return _dur(
            f"{a.cikti} zaten var. Uzerine yazmak veri kaybidir.\n"
            "  Surdurmek icin --devam, bastan kosmak icin dosyayi elle tasi."
        )
    if len(tamamlanan) == len(kayitlar):
        return _dur("Kosunun 46 belgesi zaten tamamlanmis; yeniden kosma")

    print(f"model    : {a.model}@{revizyon}")
    print(f"kol      : {a.kol}   bolum: dev")
    print(f"girdi    : {a.girdi}  ({len(kayitlar)} belge, sha256 {sha256(a.girdi)[:16]}...)")
    print(f"envanter : {len(envanter)} kavram · istem {ISTEM_SURUMU}")
    print(f"nicemleme: {'4-bit' if a.dort_bit else 'YOK (tam bfloat16)'}\n")

    try:
        adapter.hazirla()
    except Exception as exc:  # noqa: BLE001 - calisabilirlik kapisi
        return _dur(
            f"MODEL YUKLEME HATASI: {type(exc).__name__}: {exc}\n"
            "  Cikti yaratilmadi; ortam/erisim duzeltildikten sonra ayni komutu kullan."
        )

    baslangic = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    ihlal_turleri: Counter = Counter()
    gecerli = gecersiz = 0
    sureler: list[float] = []
    vramlar: list[float] = []
    pencere: list[bool] = [
        not satir["gecerli"]
        for satir in sorted(tamamlanan.values(), key=lambda x: x["order"])[
            :ERKEN_PENCERE
        ]
    ]
    erken_durdu = False
    if len(pencere) == ERKEN_PENCERE and sum(pencere) / ERKEN_PENCERE >= ERKEN_ESIK:
        return _dur("Bu kosu erken durdurma kapisina zaten ulasmis; --devam kullanma")

    with a.cikti.open("a", encoding="utf-8") as f:
        for kayit in kayitlar:
            if kayit["document_id"] in tamamlanan:
                onceki = tamamlanan[kayit["document_id"]]
                sureler.append(float(onceki["sure_sn"]))
                if onceki.get("tepe_vram_mib") is not None:
                    vramlar.append(float(onceki["tepe_vram_mib"]))
                if onceki["gecerli"]:
                    gecerli += 1
                else:
                    gecersiz += 1
                    tur = str(onceki.get("ihlal", "bilinmiyor")).split(":")[0]
                    ihlal_turleri[tur] += 1
                continue

            tb = time.perf_counter()
            try:
                ham = adapter.generate(kayit["text"])
            except Exception as exc:  # noqa: BLE001
                # Calisabilirlik kapisi (KAPI 1) - OOM/kesilme burada gorunur.
                hata = {
                    "model": a.model,
                    "revizyon": revizyon,
                    "kol": a.kol,
                    "document_id": kayit["document_id"],
                    "order": kayit["order"],
                    "hata_turu": type(exc).__name__,
                    "hata": str(exc),
                    "zaman_utc": datetime.now(timezone.utc).isoformat(),
                    "ortam": ortam_bilgisi(),
                }
                a.cikti.with_suffix(".hata.json").write_text(
                    json.dumps(hata, ensure_ascii=False, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
                return _dur(
                    f"CALISABILIRLIK HATASI ({kayit['document_id']}): "
                    f"{type(exc).__name__}: {exc}\n"
                    "  KAPI 1 gecilemedi. Bu model bu ortamda kosmuyor; "
                    "docs/19'a gore yedek adaya gecilir."
                )
            gecen = time.perf_counter() - tb
            sureler.append(gecen)
            belge_tepe_vram = tepe_vram_mib()
            if belge_tepe_vram is not None:
                vramlar.append(belge_tepe_vram)

            try:
                findings = parse_model_output(ham, envanter)
                ihlal = None
            except ContractError as exc:
                findings, ihlal = None, str(exc)

            satir = {
                "document_id": kayit["document_id"],
                "order": kayit["order"],
                "kol": a.kol,
                "adapter": adapter.name,
                "gecerli": ihlal is None,
                "findings": findings,       # gecersizse None - UYDURULMAZ
                "ihlal": ihlal,
                "raw_response": ham,        # HER ZAMAN saklanir (D53/D59)
                "sure_sn": round(gecen, 3),
                "tepe_vram_mib": belge_tepe_vram,
            }
            f.write(json.dumps(satir, ensure_ascii=False) + "\n")
            f.flush()

            if ihlal is None:
                gecerli += 1
            else:
                gecersiz += 1
                ihlal_turleri[ihlal.split(":")[0]] += 1
            pencere.append(ihlal is not None)

            durum = "OK " if ihlal is None else "IHLAL"
            adet = len(findings) if findings is not None else 0
            print(
                f"  [{kayit['order']+1:>3}/{len(kayitlar)}] {durum} "
                f"{adet:>3} bulgu  {gecen:>5.1f}sn  {kayit['document_id'][:22]}"
                + ("" if ihlal is None else f"\n        -> {ihlal[:100]}")
            )

            # ---- ERKEN DURDURMA (D59 dersi: oransal, "hepsi" degil) --------
            if (
                len(pencere) == ERKEN_PENCERE
                and sum(pencere) / ERKEN_PENCERE >= ERKEN_ESIK
            ):
                erken_durdu = True
                print(
                    f"\nERKEN DURDURMA: ilk {ERKEN_PENCERE} belgenin "
                    f"{sum(pencere)}'i sozlesmeyi bozdu. Kalan "
                    f"{len(kayitlar)-len(pencere)} belgeyi kosmak zaman kaybi."
                )
                break

    toplam = time.perf_counter() - t0
    islenen = gecerli + gecersiz
    ozet = {
        "model": a.model,
        "revizyon": revizyon,
        "kol": a.kol,
        "bolum": "dev",
        "belge_sayisi": len(kayitlar),
        "islenen": islenen,
        "erken_durdu": erken_durdu,
        # KAPI 2 · yapisal gecerlilik
        "yapisal_gecerli": gecerli,
        "yapisal_gecersiz": gecersiz,
        "gecerlilik_orani": round(gecerli / islenen, 4) if islenen else 0.0,
        "ihlal_turleri": dict(ihlal_turleri),
        # KAPI 6 · maliyet
        "oturum_duvar_sure_sn": round(toplam, 1),
        "toplam_uretim_sure_sn": round(sum(sureler), 1),
        "belge_basina_ortalama_sn": round(sum(sureler) / len(sureler), 2)
        if sureler
        else None,
        "tepe_vram_mib": max(vramlar) if vramlar else tepe_vram_mib(),
    }
    (a.cikti.with_suffix(".ozet.json")).write_text(
        json.dumps(ozet, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )

    provenance = {
        "adapter": adapter.name,
        "model_id": a.model,
        "revizyon": revizyon,
        "kol": a.kol,
        "bolum": "dev",
        "baslangic_utc": baslangic.isoformat(),
        "bitis_utc": datetime.now(timezone.utc).isoformat(),
        "girdi_dosya": str(a.girdi),
        "girdi_sha256": sha256(a.girdi),
        "cikti_dosya": str(a.cikti),
        "cikti_sha256": sha256(a.cikti) if a.cikti.exists() else None,
        "istem_dosya": str(istem_yolu),
        "istem_sha256": sha256(istem_yolu),
        "istem_surumu": ISTEM_SURUMU,
        "envanter_dosya": str(envanter_yolu),
        "envanter_sha256": sha256(envanter_yolu),
        "envanter_boyutu": len(envanter),
        "uretim": adapter.uretim_parametreleri(),
        "ortam": ortam_bilgisi(),
        "ozet": ozet,
    }
    (a.cikti.with_suffix(".provenance.json")).write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"\n{'='*64}")
    print(f"islenen {islenen}/{len(kayitlar)} · gecerli {gecerli} · gecersiz {gecersiz}")
    print(f"KAPI 2 (yapisal gecerlilik) : %{100*ozet['gecerlilik_orani']:.1f}"
          f"  {'GECTI' if ozet['gecerlilik_orani'] == 1.0 else 'GECEMEDI'}")
    if ihlal_turleri:
        print("  ihlal turleri:")
        for tur, n in ihlal_turleri.most_common():
            print(f"    {n:>3}  {tur[:70]}")
    print(f"sure {toplam/60:.1f} dk · tepe VRAM {ozet['tepe_vram_mib']} MiB")
    print(f"cikti      : {a.cikti}")
    print(f"ozet       : {a.cikti.with_suffix('.ozet.json')}")
    print(f"provenance : {a.cikti.with_suffix('.provenance.json')}")
    print("="*64)
    return 1 if erken_durdu else 0


def _dur(mesaj: str) -> int:
    print(f"\nDURDU: {mesaj}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
