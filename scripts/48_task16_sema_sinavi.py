"""TASK-16 Adim 6 - SEMA KILITLI TAKIMA KARSI SINANIYOR.

Plan: docs/29 §8.1, §8.3 · Motor: src/radyovlm/evaluation/sema.py

Kabul olcutleri (sonuc gorulmeden yazilmisti):
  - kilitli hedef siniflarla %100 uyum (docs/29 §8.1)
  - negatif kontrol takiminda TOLERANSSIZ: hicbir vaka malignite uretmemeli
    (docs/29 §8.3)

BU BETIK SONUCU DUZELTMEZ. Uymayan vaka varsa KURAL degisir (eger genel bir
duzeltmeyse) ya da "motor sinirlamasi" olarak ISARETLENIR (eger cikarim
katmaninin bilinen bir eksikliginden geliyorsa - bkz. sema.py modul basi).
Ikisi ayri raporlanir; hicbiri sessizce gecistirilmez.

Kullanim:
    python scripts/48_task16_sema_sinavi.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from radyovlm.evaluation import envanter as env  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation import sema  # noqa: E402

VARLIKLAR = KOK / "data/processed/entities.parquet"
CUMLELER = KOK / "data/processed/sentences.parquet"
ILISKILER = KOK / "data/processed/relations.parquet"
SINIR = KOK / "data/processed/sema_sinir_vakalari.csv"
KONTROL = KOK / "data/processed/sema_negatif_kontrol.csv"
RAPOR = KOK / "data/processed/sema_rapor_vakalari.csv"
CIKTI = KOK / "reports/task16_sema_sinavi.json"

# Motorun bu surumde OTOMATIK URETEMEDIGI duzey (sema.py modul basi).
# `high` ARTIK URETILEBILIYOR (cumleden derece okunuyor) - listeden cikti.
MOTOR_SINIRLAMASI_DUZEYLER = {"known_malignancy"}

# Hedef atama yordaminin (scripts/45) kullandigi malignite terim deseni.
# Burada SEBEP siniflamasi icin kullaniliyor: cumlede terim var ama varlik
# yoksa sorun sozlukte, semada degil.
# TASK-17 madde 3 (D79): tek kaynak `envanter.py`.
M_DESENI = re.compile(env.MALIGNITE_METIN_DESENI, re.I)


def _cumle_varliklari(varliklar: pd.DataFrame, cumleler: pd.DataFrame,
                      study_id: str, cumle_metni: str) -> pd.DataFrame:
    """Tek bir kilitli cumleye ait entities.parquet satirlarini bulur.

    `cumle_metni` kolonu EKLENIR - semanin cumle duzeyi kurallari (ayirici
    tani, olumsuzlanmis suphe, derece) bunu ister (sema.py "GIRDI SOZLESMESI").
    """
    aday = cumleler[(cumleler["study_id"] == study_id) & (cumleler["text"] == cumle_metni)]
    if aday.empty:
        return varliklar.iloc[0:0]
    # ⚠ BOLUM ANAHTARI ZORUNLU (D96): `sent_idx` her bolumde sifirdan baslar
    sent_idx = aday.iloc[0]["sent_idx"]
    section = aday.iloc[0]["section"] if "section" in aday.columns else None
    m = (varliklar["study_id"] == study_id) & (varliklar["sent_idx"] == sent_idx)
    if section is not None and "section" in varliklar.columns:
        m &= varliklar["section"] == section
    v = varliklar[m].copy()
    v["cumle_metni"] = cumle_metni
    return v


def _rapor_varliklari(varliklar: pd.DataFrame, cumleler: pd.DataFrame,
                      study_id: str) -> pd.DataFrame:
    """Bir calismanin TUM varliklari, her biri kendi cumle metniyle."""
    v = varliklar[varliklar["study_id"] == study_id].copy()
    if v.empty:
        return v
    # ⚠ BOLUM ANAHTARI ZORUNLU (D96)
    ah = [k for k in ("section", "sent_idx") if k in v.columns and k in cumleler.columns]
    c = cumleler[cumleler["study_id"] == study_id][ah + ["text"]].drop_duplicates(subset=ah)
    v = v.merge(c, on=ah, how="left").rename(columns={"text": "cumle_metni"})
    return v


def _sebep(varliklar: pd.DataFrame, cumle: str, olcek_hedef: str,
           bulgular: list) -> str:
    """Uyumsuzlugun SEBEBINI siniflar.

    ⚠ Bu siniflandirma uyumsuzluk SAYISINI DUSURMEZ - her uyumsuzluk
    uyumsuzdur; sebep yalniz "ne yapilmasi gerektigini" soyler.

    sozluk_boslugu       : cumlede malignite terimi VAR ama hicbir malignite
                           varligi cikmamis -> `bulgu_sozlugu.yaml` (TASK-17)
    kavram_listesi_eksik : varlik cikmis ama semanin MALIGNITE_KAVRAMLARI
                           listesinde degil -> sema tarafi, sozluk degil
    girdi_filtresi       : malignite varligi var ama F1/F2 susturmus ->
                           girdi katmani (K7 F1 %36,4 / D29)
    known_malignancy     : docs/33 §4.1 esigi, TASK-17'ye birakildi
    kural                : yukaridakilerin hicbiri - KURAL sorgulanir
    """
    if varliklar.empty:
        return "sozluk_boslugu"
    mal = varliklar[varliklar["normalized_concept"].isin(sema.MALIGNITE_KAVRAMLARI)]
    if mal.empty:
        return "sozluk_boslugu" if M_DESENI.search(cumle) else "kavram_listesi_eksik"
    if bulgular and all(not b.suphe_yukseltebilir for b in bulgular
                        if b.normalized_concept in sema.MALIGNITE_KAVRAMLARI):
        return "girdi_filtresi"
    if olcek_hedef in MOTOR_SINIRLAMASI_DUZEYLER:
        return "known_malignancy"
    return "kural"


def _sina(vaka_id: str, olcek_hedef: str, motor_ciktisi: sema.RaporSonucu,
          varliklar: pd.DataFrame, cumle: str, bulgular: list) -> dict:
    uyum = motor_ciktisi.olcek_duzeyi == olcek_hedef
    sebep = "-" if uyum else _sebep(varliklar, cumle, olcek_hedef, bulgular)
    return {
        "vaka_id": vaka_id,
        "hedef": olcek_hedef,
        "motor_ciktisi": motor_ciktisi.olcek_duzeyi,
        "uyum": uyum,
        "sebep": sebep,
        "cikarilan_varlik": len(varliklar),
        "belirleyici_entity": motor_ciktisi.belirleyici_entity_id,
        "belirleyici_kaynak": motor_ciktisi.belirleyici_kaynak,
    }


def main() -> int:
    for y in (VARLIKLAR, CUMLELER, SINIR, KONTROL, RAPOR):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    varliklar = pd.read_parquet(
        VARLIKLAR,
        columns=["entity_id", "study_id", "section", "sent_idx", "raw_text", "normalized_concept",
                 "assertion", "assertion_rule", "assertion_cue", "temporality"],
    )
    cumleler = pd.read_parquet(
        CUMLELER, columns=["study_id", "section", "sent_idx", "text", "is_stock_phrasing"])
    iliskiler = pd.read_parquet(
        ILISKILER, columns=["head_id", "tail_id", "relation_type"])
    # C#nodul-kalip girdi sozlesmesi (TASK-17 madde 4, D81): iki kolon
    # EKLENIR. TUM varlik cercevesi uzerinde cagrilir - niteleyici kavram
    # haritasi eksik kalmasin diye (filtreleme SONRA yapilir).
    varliklar = sema.kalip_nodul_kolonlarini_ekle(varliklar, cumleler, iliskiler)

    sonuclar: dict[str, list[dict]] = {"sinir": [], "kontrol": [], "rapor": []}

    # --- SINIR + KONTROL: tek cumle duzeyi -----------------------------
    for ad, dosya in (("sinir", SINIR), ("kontrol", KONTROL)):
        d = pd.read_csv(dosya, keep_default_na=False)
        for _, r in d.iterrows():
            v = _cumle_varliklari(varliklar, cumleler, r["study_id"], r["cumle"])
            bulgular = sema.bulgulari_hesapla(v) if not v.empty else []
            sonuc = sema.rapora_topla(r["study_id"], bulgular)
            sonuclar[ad].append(
                _sina(r["vaka_id"], r["hedef_sinif"], sonuc, v, r["cumle"], bulgular))

    # --- RAPOR: cok cumleli, calismanin TUM findings varliklari --------
    dr = pd.read_csv(RAPOR, keep_default_na=False)
    for _, r in dr.iterrows():
        v = _rapor_varliklari(varliklar, cumleler, r["study_id"])
        bulgular = sema.bulgulari_hesapla(v) if not v.empty else []
        sonuc = sema.rapora_topla(r["study_id"], bulgular)
        tam_metin = " ".join(v["cumle_metni"].fillna("").astype(str)) if not v.empty else ""
        sonuclar["rapor"].append(
            _sina(r["vaka_id"], r["hedef_sinif"], sonuc, v, tam_metin, bulgular))

    # --- Raporla ---------------------------------------------------------
    ozet = {}
    for ad, liste in sonuclar.items():
        n = len(liste)
        uyan = sum(1 for x in liste if x["uyum"])
        sebepler = {}
        for x in liste:
            if not x["uyum"]:
                sebepler[x["sebep"]] = sebepler.get(x["sebep"], 0) + 1
        print(f"\n=== {ad.upper()} ({n} vaka) ===")
        print(f"  UYUM     : {uyan}/{n}")
        print(f"  UYUMSUZ  : {n - uyan}/{n}   sebep dagilimi: "
              f"{sebepler if sebepler else '-'}")
        for x in liste:
            if not x["uyum"]:
                print(f"    [{x['sebep']:20}] {x['vaka_id']:28} hedef={x['hedef']:16} "
                      f"motor={x['motor_ciktisi']:16} varlik={x['cikarilan_varlik']:3} "
                      f"kaynak={x['belirleyici_kaynak']}")
        ozet[ad] = {"toplam": n, "uyum": uyan, "uyumsuz": n - uyan,
                    "sebep_dagilimi": sebepler, "detay": liste}

    # --- KORUMA KAPISI: kontrol takiminda GERCEK ihlal var mi -----------
    # Asil koruma kapisi denetimi: motor kontrol takiminda YONLU SUPHE
    # uretti mi? Hedefle uyumsuzluk degil, MALIGNITE URETIMI olculur.
    # TASK-17 madde 3 (D79) + docs/34 v2 §4.2 (Karar 2): kapi kumesinden
    # `low` CIKARILDI. K-A = toleranssiz; `low` ayri olarak K-C ile
    # raporlanir (esik <= 1, turetilmis - bkz. envanter.py).
    kapi_ciktisi_ihlali = [x for x in sonuclar["kontrol"]
                           if x["motor_ciktisi"] in env.KAPI_MALIGNITE_SINIFLARI]
    kapi_low = [x for x in sonuclar["kontrol"] if x["motor_ciktisi"] == "low"]

    print(f"\n{'='*70}")
    print("KORUMA KAPISI DENETIMI (docs/29 §8.3, toleranssiz)")
    print(f"  motor, kontrol takiminda YONLU SUPHE uretti mi: "
          f"{len(kapi_ciktisi_ihlali)} vaka")
    for x in kapi_ciktisi_ihlali:
        print(f"    [KAPI IHLALI] {x['vaka_id']:28} motor={x['motor_ciktisi']}")

    print(f"  K-C · kontrol takiminda `low` ureten vaka: {len(kapi_low)} "
          f"(tolerans <= {env.KAPI_LOW_TOLERANSI})")
    for x in kapi_low:
        print(f"    [K-C] {x['vaka_id']:28} motor=low")

    ozet["koruma_kapisi"] = {
        "K_A_toleranssiz_ihlal_sayisi": len(kapi_ciktisi_ihlali),
        "K_A_gecti": len(kapi_ciktisi_ihlali) == 0,
        "K_A_kume": sorted(env.KAPI_MALIGNITE_SINIFLARI),
        "ihlaller": kapi_ciktisi_ihlali,
        "K_C_low_sayisi": len(kapi_low),
        "K_C_toleransi": env.KAPI_LOW_TOLERANSI,
        "K_C_gecti": len(kapi_low) <= env.KAPI_LOW_TOLERANSI,
        "K_C_vakalar": kapi_low,
    }
    ozet["sema_surumu"] = sema.SEMA_SURUMU

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(ozet, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
