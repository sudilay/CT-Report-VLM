"""Faz A · A1 · `lesion` kavraminin malignite envanterine eklenmesinin olcumu.

SORU: C11-olumsuz-belirsiz-02 uyumsuzlugu `lesion`in MALIGNITE_KAVRAMLARI
envanterinde bulunmamasindan kaynaklaniyor. Kavram eklenirse korpus genelinde
kac calismanin rapor duzeyi sinifi degisir?

NEDEN OLCULUYOR: 23 negatif kontrolde `lesion` hic gecmiyor (kapi kirilmiyor),
ama bu tek basina yeterli kanit degil. `lesion` genel ve taahhutsuz bir
kelimedir; 12.652 varlik satirinda geciyor. Dagilim kaymasi olculmeden envanter
degistirilmez.

KAPSAM: YALNIZ gelistirme havuzu. Degerlendirme kilidi (holdout-1.0) OKUNMAZ.

Kullanim:
    python scripts/64_fazA_lesion_dagilim_olcumu.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation import sema  # noqa: E402

VARLIKLAR = KOK / "data/processed/entities.parquet"
CUMLELER = KOK / "data/processed/sentences.parquet"
ILISKILER = KOK / "data/processed/relations.parquet"
CALISMALAR = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/fazA_lesion_dagilim_olcumu.json"

YENI_KAVRAM = "lesion"


def gelistirme_havuzu() -> set[str]:
    """Degerlendirme kilidinin DISINDA kalan calisma kimlikleri."""
    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli_hasta = (set(dk["a_ctrate_valid"]["hasta_listesi"])
                     | set(dk["b_train_kilit"]["hasta_listesi"]))
    c = pd.read_parquet(CALISMALAR, columns=["study_id", "patient_id"])
    havuz = set(c.loc[~c["patient_id"].isin(kilitli_hasta), "study_id"])
    return havuz, kilit["surum"]


def siniflari_hesapla(varliklar: pd.DataFrame) -> dict[str, str]:
    """study_id -> rapor duzeyi malignite sinifi."""
    out: dict[str, str] = {}
    for sid, v in varliklar.groupby("study_id", sort=False):
        v = v.reset_index(drop=True)
        bulgular = sema.bulgulari_hesapla(v) if not v.empty else []
        out[sid] = sema.rapora_topla(sid, bulgular).olcek_duzeyi
    return out


def main() -> None:
    havuz, kilit_surumu = gelistirme_havuzu()

    varliklar = pd.read_parquet(VARLIKLAR)
    varliklar = varliklar[varliklar["study_id"].isin(havuz)].copy()
    cumleler = pd.read_parquet(CUMLELER)
    cumleler = cumleler[cumleler["study_id"].isin(havuz)]
    iliskiler = pd.read_parquet(ILISKILER)
    iliskiler = iliskiler[iliskiler["study_id"].isin(havuz)]

    varliklar = sema.kalip_nodul_kolonlarini_ekle(varliklar, cumleler, iliskiler)

    # `cumle_metni` girdi sozlesmesi geregi CAGIRAN tarafca eklenir
    # (configs/degerlendirme_semasi.json -> girdi_sozlesmesi.cumle_metni).
    # Eklenmezse semanin METIN yolu kurallari SESSIZCE OLU KALIR.
    # Anahtar UCLUdur: (study_id, section, sent_idx) - D96.
    varliklar = varliklar.merge(
        cumleler[["study_id", "section", "sent_idx", "text"]]
        .rename(columns={"text": "cumle_metni"}),
        on=["study_id", "section", "sent_idx"], how="left", validate="m:1")

    # Girdi filtresi TUM cerceve icin BIR KEZ (sema.py:566 yorumu). Grup basina
    # cagrilirsa korpus olceginde kosulamaz.
    from radyovlm.evaluation import girdi_filtresi as gf
    varliklar = gf.uygula(varliklar.reset_index(drop=True))

    print(f"kapsam: gelistirme havuzu · {len(havuz):,} calisma "
          f"· {len(varliklar):,} varlik  (kilit OKUNMADI)")
    lesion_satir = int((varliklar["normalized_concept"] == YENI_KAVRAM).sum())
    lesion_calisma = int(varliklar.loc[
        varliklar["normalized_concept"] == YENI_KAVRAM, "study_id"].nunique())
    print(f"`{YENI_KAVRAM}` varlik satiri: {lesion_satir:,} "
          f"· gectigi calisma: {lesion_calisma:,}")

    # --- ONCE: mevcut envanter ---
    onceki_envanter = set(sema.MALIGNITE_KAVRAMLARI)
    once = siniflari_hesapla(varliklar)

    # --- SONRA: `lesion` eklenmis envanter ---
    # Envanter frozenset; modul niteligi gecici olarak yeniden baglanir ve
    # `finally` ile mutlaka eski haline dondurulur.
    try:
        sema.MALIGNITE_KAVRAMLARI = frozenset(onceki_envanter | {YENI_KAVRAM})
        sonra = siniflari_hesapla(varliklar)
    finally:
        sema.MALIGNITE_KAVRAMLARI = frozenset(onceki_envanter)
    assert sema.MALIGNITE_KAVRAMLARI == frozenset(onceki_envanter),         "envanter geri yuklenemedi"

    degisen = {s: (once[s], sonra[s]) for s in once if once[s] != sonra[s]}
    gecis = Counter(f"{a} -> {b}" for a, b in degisen.values())

    sonuc = {
        "gorev": "Faz A · A1",
        "soru": f"`{YENI_KAVRAM}` MALIGNITE_KAVRAMLARI'na eklenirse dagilim ne kadar kayar?",
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit_surumu,
        "sema_surumu": sema.SEMA_SURUMU,
        "havuz_calisma": len(havuz),
        "olculen_calisma": len(once),
        "lesion_varlik_satiri": lesion_satir,
        "lesion_gectigi_calisma": lesion_calisma,
        "sinifi_degisen_calisma": len(degisen),
        "sinifi_degisen_oran_yuzde": round(100 * len(degisen) / max(len(once), 1), 3),
        "gecisler": dict(gecis.most_common()),
        "dagilim_once": dict(Counter(once.values()).most_common()),
        "dagilim_sonra": dict(Counter(sonra.values()).most_common()),
        "ornek_degisen": [
            {"study_id": s, "once": a, "sonra": b}
            for s, (a, b) in list(degisen.items())[:15]
        ],
    }

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1),
                     encoding="utf-8")

    print()
    print(f"sinifi degisen calisma: {len(degisen):,} "
          f"(%{sonuc['sinifi_degisen_oran_yuzde']})")
    for k, v in gecis.most_common(10):
        print(f"   {k:42s} {v:6,}")
    print()
    print(f"yazildi: {CIKTI.relative_to(KOK)}")


if __name__ == "__main__":
    main()
