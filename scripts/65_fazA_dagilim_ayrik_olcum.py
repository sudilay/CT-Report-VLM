"""Faz A · A5 · Dagilim kapisinin AYRISTIRILMIS olcumu.

SORUN: Birlesik dagilim kapisi (`malignite_pozitif` = high ∪ known_malignancy)
estimand uyumsuzlugu nedeniyle KARAR VEREMEZ ilan edildi
(`configs/task17_dagilim_capasi.json` -> denetim_hukmu).

KAYITLI GELECEK PROTOKOL (ayni dosya -> gelecek_protokol):
  * `high`             : radyolojik yuksek suphe - derece dili capasi UYGULANABILIR
  * `known_malignancy` : raporda yazili kanser oykusu - AYRI dogrulama ister

`known_malignancy` dogrulamasi A4'te yapildi (kor metin puanlamasi, %88,9).
Bu betik `high` basamagini AYRI olcer. Ikisi TEK prevalans kapisinda
BIRLESTIRILMEZ.

⛔ KAPSAM: yalniz gelistirme havuzu. Degerlendirme kilidi OKUNMAZ.

Kullanim:
    python scripts/65_fazA_dagilim_ayrik_olcum.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation import girdi_filtresi as gf  # noqa: E402
from radyovlm.evaluation import sema  # noqa: E402

P = KOK / "data/processed"
KILIT = KOK / "configs/splits_holdout.json"
CAPA = KOK / "configs/task17_dagilim_capasi.json"
CIKTI = KOK / "reports/fazA_dagilim_ayrik_olcum.json"


def main() -> None:
    capa = json.loads(CAPA.read_text(encoding="utf-8"))
    aralik = capa["kabul_araligi"]
    alt, ust = aralik["alt_yuzde"], aralik["ust_yuzde"]

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = (set(dk["a_ctrate_valid"]["hasta_listesi"])
               | set(dk["b_train_kilit"]["hasta_listesi"]))
    k = pd.read_parquet(P / "reports_study_level.parquet",
                        columns=["study_id", "patient_id"])
    gelistirme = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])

    v = pd.read_parquet(P / "entities.parquet")
    v = v[v["study_id"].isin(gelistirme)]
    c = pd.read_parquet(P / "sentences.parquet")
    c = c[c["study_id"].isin(gelistirme)]
    il = pd.read_parquet(P / "relations.parquet")
    il = il[il["study_id"].isin(gelistirme)]

    v = sema.kalip_nodul_kolonlarini_ekle(v, c, il)
    # `cumle_metni` girdi sozlesmesi geregi CAGIRAN tarafca eklenir.
    v = v.merge(c[["study_id", "section", "sent_idx", "text"]]
                .rename(columns={"text": "cumle_metni"}),
                on=["study_id", "section", "sent_idx"], how="left",
                validate="m:1")
    v = gf.uygula(v.reset_index(drop=True))

    siniflar: dict[str, str] = {}
    for sid, g in v.groupby("study_id", sort=False):
        g = g.reset_index(drop=True)
        bulgular = sema.bulgulari_hesapla(g) if not g.empty else []
        siniflar[sid] = sema.rapora_topla(sid, bulgular).olcek_duzeyi

    n = len(siniflar)
    dagilim = Counter(siniflar.values())
    n_high = dagilim.get("high", 0)
    n_km = dagilim.get("known_malignancy", 0)
    n_birlesik = n_high + n_km

    def yuzde(x: int) -> float:
        return round(100 * x / max(n, 1), 4)

    sonuc = {
        "gorev": "Faz A · A5",
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit["surum"],
        "capa_surumu": capa["surum"],
        "olculen_calisma": n,
        "sinif_dagilimi": dict(dagilim.most_common()),
        "AYRIK_OLCUM": {
            "high": {"calisma": n_high, "yuzde": yuzde(n_high)},
            "known_malignancy": {"calisma": n_km, "yuzde": yuzde(n_km)},
        },
        "birlesik_ESKI_ESTIMAND": {"calisma": n_birlesik,
                                   "yuzde": yuzde(n_birlesik)},
        "onceden_dondurulmus_aralik_yuzde": [alt, ust],
        "high_aralik_icinde_mi": bool(alt <= yuzde(n_high) <= ust),
        "gerekce": (
            "Kapinin KENDI tureyis metni `high`-only varsayiyordu: "
            "'Motor known_malignancy URETMEZ, yani malignite_pozitif pratikte "
            "YALNIZ high'tir' (scripts/49 satir 59-61). D92 bu varsayimi "
            "kirdi. `high`-only degerlendirme, kapiyi ORIJINAL TASARIMINA "
            "dondurur; sonuca bakip yeni olcut secmek DEGILDIR."),
        "ilan_edilen_sinirlar": [
            capa["guc_ilani"],
            ("POST-HOC: bu olcum, birlesik kapi kosulduktan SONRA yapilmistir. "
             "Aralik ve capa desenleri onceden dondurulmustur, ama olcumun "
             "zamanlamasi ilan edilir."),
            ("Kapinin gecilmesi kalibrasyonun dogrulugunu KANITLAMAZ; yalniz "
             "kaba dejenerasyonu diskalar."),
        ],
    }

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1),
                     encoding="utf-8")

    print(f"olculen calisma: {n:,}")
    print(f"\nAYRIK OLCUM:")
    print(f"  high              : {n_high:>5,}  %{yuzde(n_high)}")
    print(f"  known_malignancy  : {n_km:>5,}  %{yuzde(n_km)}")
    print(f"  (eski birlesik)   : {n_birlesik:>5,}  %{yuzde(n_birlesik)}")
    print(f"\nonceden dondurulmus aralik: [%{alt} - %{ust}]")
    print(f"`high` aralik icinde mi   : "
          f"{'EVET' if sonuc['high_aralik_icinde_mi'] else 'HAYIR'}")
    print(f"\nyazildi: {CIKTI.relative_to(KOK)}")


if __name__ == "__main__":
    main()
