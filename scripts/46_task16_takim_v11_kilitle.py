"""TASK-16 Adim 4 - v1.1 REVIZYONUNUN KILITLENMESI.

Plan: docs/33_task16_denetim2_ve_duzeltme_plani.md §7

v1.0 kilidi ikinci bagimsiz denetimden gecirildi (docs/33). Bulunanlar KURAL
IHLALI (A20) ve IC CELISKI (docs/31 #12 ile CSV arasi) idi - sonuc gorulerek
degil. Bu, kilit acmayi mesru kilan TEK sebeptir (kurallar HENUZ yazilmadi).

Bu betik v1.0'in ACILDIGINI ve v1.1'in kilitlendigini dogrular; v1.0 manifesti
configs/arsiv/ altinda SUPERSEDED olarak saklanir, SILINMEZ.

⚠ BU IKINCI BIR KILIT ACMA ICIN EMSAL DEGILDIR. Kurallar yazildiktan sonra
gelen HER hedef degisikligi talebi reddedilecektir.

Kullanim:
    python scripts/46_task16_takim_v11_kilitle.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from radyovlm.evaluation import envanter as env  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
SINIR = KOK / "data/processed/sema_sinir_vakalari.csv"
KONTROL = KOK / "data/processed/sema_negatif_kontrol.csv"
RAPOR = KOK / "data/processed/sema_rapor_vakalari.csv"
MANIFEST = KOK / "configs/sema_takim_kilidi.json"
ARSIV_V1 = KOK / "configs/arsiv/sema_takim_kilidi_v1.0_superseded.json"

# TASK-17 madde 3 (D79): kilitli takimin KENDI gecerliligi - kontrol
# vakasina malignite HEDEFI yazilamaz. Motorun CIKTISINI sinayan kapi
# AYRI bir kumedir (env.KAPI_MALIGNITE_SINIFLARI) ve Karar 2 yalniz
# ONA uygulandi. Bu kume DEGISMEDI.
MALIGN_URETIR = env.HEDEF_MALIGNITE_SINIFLARI
GECERLI_SINIF = MALIGN_URETIR | {"indeterminate", "None", "not_mentioned"}

REVIZYON_DEFTERI = [
    {"vaka_id": "C16-malignite-enf-03", "eski_hedef": "low", "yeni_hedef": "not_mentioned",
     "sebep": "A20 ihlali: oneri status degildir; enfeksiyon A27 ile olcek disi"},
    {"vaka_id": "C6-malignite-benign-02", "eski_hedef": "low", "yeni_hedef": "None",
     "sebep": "A8 + #12: radyologun kesin benign hukmu kazanir (karsi kanit A34 kayitli)"},
    {"vaka_id": "C4-derece-yuksek-01", "eski_hedef": "known_malignancy", "yeni_hedef": "high",
     "sebep": "Yeni C karari: known_malignancy esigi yazili bilinen kanser gerektirir"},
    {"vaka_id": "C13-ekstratorasik-02", "eski_hedef": "indeterminate", "yeni_hedef": "intermediate",
     "sebep": "'(metastasis?)' yonlu hipotez, ayirt edilemezlik degil"},
    {"vaka_id": "C12-benign-belirsiz-01", "eski_hedef": "low", "yeni_hedef": "None",
     "sebep": "docs/31 #12 ile ic celiski duzeltildi (A26 fat-containing benign patern)"},
    {"vaka_id": "C12-benign-belirsiz-02", "eski_hedef": "low (VAKA CIKARILDI)", "yeni_hedef": "-",
     "sebep": "C12-01 ile neredeyse ayni cumle (mukerrer); yerine A26-kalsifiegranulom-01 eklendi"},
    {"vaka_id": "K-teknik-02", "eski_hedef": "not_mentioned", "yeni_hedef": "indeterminate",
     "sebep": "Yeni C karari: tarif edilen lezyon (tiroid hipodansitesi) var, karakterize edilemiyor"},
    {"vaka_id": "C16-malignite-enf-01", "eski_hedef": "-", "yeni_hedef": "- (dayanak etiketi duzeltildi)",
     "sebep": "Klerikal: dayanak C#13 -> C#5+C#16"},
    {"vaka_id": "MALIGN_URETIR (kod)", "eski_hedef": "indeterminate DAHIL", "yeni_hedef": "indeterminate HARIC",
     "sebep": "indeterminate yonlu suphe degil epistemik belirsizliktir (docs/31 #8 ile uyum)"},
]

EKLENEN_KONTROL = ["K-sablonnegatif-01", "K-sablonnegatif-02", "K-postop-01", "K-postop-02",
                   "K-amfizem-01", "K-amfizem-02", "K-koroner-01", "K-koroner-02"]


def sha(y: Path) -> str:
    return hashlib.sha256(y.read_bytes()).hexdigest()


def main() -> int:
    if MANIFEST.exists():
        print(f"HATA: v1.1 zaten kilitli: {MANIFEST}")
        return 1
    if not ARSIV_V1.exists():
        print(f"HATA: v1.0 arsivi yok, once kilit acilmali: {ARSIV_V1}")
        return 1
    for y in (SINIR, KONTROL, RAPOR):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    ds = pd.read_csv(SINIR, keep_default_na=False)
    dk = pd.read_csv(KONTROL, keep_default_na=False)
    dr = pd.read_csv(RAPOR, keep_default_na=False)

    # --- degismezler ---
    for ad, d, kolon in [("sinir", ds, "hedef_sinif"), ("kontrol", dk, "hedef_sinif"),
                          ("rapor", dr, "hedef_sinif")]:
        bos = d[d[kolon].astype(str).str.strip() == ""]
        assert bos.empty, f"{ad}: hedefsiz vaka {bos['vaka_id'].tolist()}"
        gecersiz = set(d[kolon]) - GECERLI_SINIF
        assert not gecersiz, f"{ad}: olcek disi hedef {gecersiz}"
        assert d["vaka_id"].is_unique, f"{ad}: tekrarli vaka_id"

    ihlal = dk[dk["hedef_sinif"].isin(MALIGN_URETIR)]
    assert ihlal.empty, f"KORUMA KAPISI: kontrol takiminda malignite ureten hedef: {ihlal['vaka_id'].tolist()}"
    assert len(dk) >= 10, f"kontrol takimi {len(dk)} vaka, en az 10 olmali"
    assert set(EKLENEN_KONTROL) <= set(dk["vaka_id"]), "eklenen kontrol vakalari eksik"

    print(f"SINIR   : {len(ds)} vaka")
    print(f"KONTROL : {len(dk)} vaka  ({dk['populasyon_kodu'].nunique()} kategori)")
    print(f"RAPOR   : {len(dr)} cok cumleli vaka")
    print()
    print("SINIR TAKIMI hedef dagilimi:")
    for k, v in ds["hedef_sinif"].value_counts().items():
        print(f"  {k:20} {v:>3}")
    print("\nRAPOR VAKALARI hedef dagilimi:")
    for k, v in dr["hedef_sinif"].value_counts().items():
        print(f"  {k:20} {v:>3}")

    manifest = {
        "surum": "takim-1.1",
        "onceki_surum": "takim-1.0 (SUPERSEDED)",
        "onceki_surum_arsiv": "configs/arsiv/sema_takim_kilidi_v1.0_superseded.json",
        "onceki_surum_sha256": sha(ARSIV_V1),
        "kilit_utc": datetime.now(timezone.utc).isoformat(),
        "revizyon_gerekcesi": (
            "Ikinci bagimsiz denetim (docs/33): kilitli hedeflerde KURAL IHLALI "
            "(A20) ve IC CELISKI (docs/31 #12 vs CSV) bulundu - sonuc gorulerek "
            "degil. Bu, kilit acmayi mesru kilan TEK sebeptir: kurallar HENUZ "
            "yazilmamisti. Bu ikinci bir kilit acma icin EMSAL DEGILDIR."
        ),
        "revizyon_defteri": REVIZYON_DEFTERI,
        "artik_sinir": (
            "Hedefleri atayan taraf ile kurallari yazacak taraf ayni. Hedefi A "
            "kuraline dayanan vakalar 'KILAVUZ ATIFLI YAZAR ATAMASI'dir, gercek "
            "dis denetim DEGILDIR (2. denetimin bulgu 3.4'u, C16-03 ornegiyle "
            "kanitlandi). Gercek bagimsiz denetim ancak adim 7'de (Codex kor "
            "yargilamasi) gelir."
        ),
        "sinir_takimi": {
            "dosya": "data/processed/sema_sinir_vakalari.csv",
            "vaka": len(ds), "sha256": sha(SINIR),
            "hedef_dagilimi": ds["hedef_sinif"].value_counts().to_dict(),
        },
        "kontrol_takimi": {
            "dosya": "data/processed/sema_negatif_kontrol.csv",
            "vaka": len(dk), "sha256": sha(KONTROL),
            "kategori": dk["populasyon_kodu"].value_counts().to_dict(),
            "kapi": "Sema bu vakalarin HICBIRINDE malignite uretmeyecek. MALIGN_URETIR = "
                    "{low, intermediate, high, known_malignancy}; indeterminate HARIC "
                    "(epistemik/teknik belirsizlik, yonlu suphe degil).",
        },
        "rapor_vakalari": {
            "dosya": "data/processed/sema_rapor_vakalari.csv",
            "vaka": len(dr), "sha256": sha(RAPOR),
            "amac": "Cumle duzeyi hedeflerden RAPOR duzeyi sinifa toplama kuralinin "
                    "(#9, en yuksek supheli bulgu kazanir) tek testi.",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nKILITLENDI: {MANIFEST.relative_to(KOK)}  (surum takim-1.1)")
    print(f"  sinir   sha256 {manifest['sinir_takimi']['sha256'][:16]}")
    print(f"  kontrol sha256 {manifest['kontrol_takimi']['sha256'][:16]}")
    print(f"  rapor   sha256 {manifest['rapor_vakalari']['sha256'][:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
