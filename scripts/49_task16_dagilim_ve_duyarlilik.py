"""TASK-16 adim 6 - DAGILIM KAPISI (docs/29 §8.4) + DUYARLILIK ANALIZI (§7/3).

KAPSAM: yalniz gelistirme havuzu. Degerlendirme kilidi OKUNMAZ.

--------------------------------------------------------------------------
⚠ SIRA KRITIK - KABUL ARALIGI KOSUMDAN ONCE DONDURULMUSTUR.

docs/29 §8.4'un kurali: *"Kabul araligi sayisal olarak, kosumdan ONCE
dondurulur. Dagilim araligin disina cikarsa KURAL revize edilir - aralik
degil."* Asagidaki DONDURULMUS_ARALIK sabiti bu betik ilk kez kosulmadan
once yazilmistir ve tureyisi yanindadir.

v1'in kusuru (denetim #1, KRITIK) *"beklenen prevalansin dis kaynagi yoktu"*
idi. v2'nin capasi KOR bir metin olcumudur: derece kelimesi sayimi
(reports/task16_b_olcumleri.json, adim 3'te semadan BAGIMSIZ olculdu).

⚠ YALNIZ `malignite_pozitif` KAPIYA BAGLANMISTIR. Diger siniflar icin
turetilebilir bir dis capa YOKTUR; onlar OLCULUR ve RAPORLANIR ama kapi
degildir. Capasiz bir araliga kapi demek, v1'in reddedilen hatasini
tekrarlamak olurdu.
--------------------------------------------------------------------------

Kullanim:
    python scripts/49_task16_dagilim_ve_duyarlilik.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation import sema  # noqa: E402

VARLIKLAR = KOK / "data/processed/entities.parquet"
CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/task16_dagilim.json"

# =========================================================================
# DONDURULMUS KABUL ARALIGI - kosumdan ONCE yazildi
# =========================================================================
DONDURULMUS_ARALIK = {
    "malignite_pozitif": {
        "alt_yuzde": 0.5,
        "ust_yuzde": 3.0,
        "tureyis": (
            "Motor `known_malignancy` URETMEZ (docs/33 §4.1, ilan edilmis sinir), "
            "yani `malignite_pozitif` pratikte YALNIZ `high`tir. `high` iki sart "
            "ister: ipuclu present + cumlede derece kelimesi. Derece kelimesinin "
            "korpustaki hacmi adim 3'te SEMADAN BAGIMSIZ olculdu: 392 cumle / "
            "230 calisma = %1,12 (reports/task16_b_olcumleri.json, '#4 · suphe "
            "derece kelimeleri' / 'high suspicion'). "
            "UST SINIR %3,0: derece cumlesi olan her calisma malignite-ekseninde "
            "bir kavram da tasimayabilir (dusurur), ama rapor duzeyi toplama cok "
            "cumleli raporlarda birden fazla yoldan `high` uretebilir (yukseltir). "
            "%1,12'nin ~2,7 kati tavan olarak birakildi. "
            "ALT SINIR %0,5: derece cumlelerinin yarisindan azi malignite "
            "kavramiyla eslesiyorsa motor derece kuralini pratikte kullanamiyor "
            "demektir - bu da bir basarisizliktir, sessizce gecmemeli."
        ),
    },
}
M_DESENI = re.compile(r"malignan|carcinom|neoplas|metasta|tumor|spicul", re.I)

KAPIYA_BAGLI_OLMAYAN = (
    "malignite_negatif, belirsiz_yetersiz_kanit, benign_bulgu ve not_mentioned "
    "icin turetilebilir bir DIS capa yoktur; olculur ve raporlanir, kapi degildir."
)

# =========================================================================
# DUYARLILIK SENARYOLARI (docs/29 §7/3)
# Cikarim katmaninin OLCULMUS hata oranlari girdiye enjekte edilir; semanin
# kendisi DEGISTIRILMEZ - yalniz girdi bozulur ve kayma olculur.
# =========================================================================
SENARYOLAR = {
    "S1_zaman_ekseni_guvenilmez": {
        "aciklama": "K7 `prior` F1 %36,4 (D39). Zaman ekseni esigi gecemedi; "
                    "TUM `prior` etiketleri `current` sayilirsa (F1 hic "
                    "susturmazsa) dagilim ne kadar kayiyor?",
        "yon": "F1 devre disi - ust sinir tahmini",
    },
    "S2_kanitsiz_present_gercek": {
        "aciklama": "`present`in %80,33'u varsayilan (ipucusuz). Bunlarin hepsi "
                    "GERCEK ipuclu bulgu olsaydi (F2 hic susturmazsa) dagilim "
                    "ne kadar kayiyor?",
        "yon": "F2 devre disi - ust sinir tahmini",
    },
    "S3_hedge_aslinda_uncertain": {
        "aciklama": "`uncertain` duyarliligi %71/%46 (D29 belirsizlik ipuclarini "
                    "`present` yapmisti). Ipuclu present'ler aslinda `uncertain` "
                    "olsaydi dagilim ne kadar kayiyor?",
        "yon": "suphe ASAGI - alt sinir tahmini",
    },
}


def _kapi_teshisi(v: pd.DataFrame, cumleler: pd.DataFrame) -> dict:
    """Kapi kalirsa: derece kuralinin populasyonu NEREDE eriyor?

    Bu olcum kapi sonucundan BAGIMSIZ olarak anlamlidir ve tekrar
    uretilebilir olmasi icin betige yazilmistir (prose'da sayi birakmak
    bu projede bir kez hataya yol acti).
    """
    d = cumleler[cumleler["text"].str.contains(sema.DERECE_DESENI, na=False)].copy()
    d["kanser_terimi"] = d["text"].str.contains(M_DESENI, na=False)
    mal = (v[v["normalized_concept"].isin(sema.MALIGNITE_KAVRAMLARI)]
           [["study_id", "sent_idx"]].drop_duplicates())
    mal["mal_varlik"] = True
    d = d.merge(mal, on=["study_id", "sent_idx"], how="left")
    d["mal_varlik"] = d["mal_varlik"].fillna(False).astype(bool)
    kanser = d[d["kanser_terimi"]]
    return {
        "derece_cumlesi": {"cumle": int(len(d)), "calisma": int(d["study_id"].nunique())},
        "kanser_terimi_iceren": int(d["kanser_terimi"].sum()),
        "kanser_terimi_ICERMEYEN": int((~d["kanser_terimi"]).sum()),
        "kanser_terimli_ve_malignite_varligi_cikan": int(kanser["mal_varlik"].sum()),
        "kanser_terimli_ama_varlik_cikmayan": int((~kanser["mal_varlik"]).sum()),
        "yorum": (
            "Derece kelimesi bu korpusta AGIRLIKLA MALIGNITE HAKKINDA DEGILDIR: "
            "'highly suspicious' cumlelerinin buyuk cogunlugu enfeksiyon/COVID "
            "suphesidir (korpusun %21'i COVID, docs/08). Kapi capasi bu yuzden "
            "yanlis turetilmisti - 'suphe derecesi dili' ile 'MALIGNITE suphe "
            "derecesi dili' esitlenmisti."
        ),
    }


def _gelistirme_havuzu() -> set:
    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])
    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    return set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])


def _ilgili_varliklar(v: pd.DataFrame) -> pd.DataFrame:
    """Sonuca etki EDEBILECEK satirlar. Digerleri `duzey=None, kaynak='-'`
    dondurur ve toplama kuralina hic girmez - elenmeleri sonucu degistirmez."""
    ilgili = (
        v["normalized_concept"].isin(sema.MALIGNITE_KAVRAMLARI)
        | v["normalized_concept"].isin(sema.BENIGN_KAVRAMLARI)
        | v["cumle_metni"].fillna("").str.contains(sema.BENIGN_HUKUM_DESENI, na=False)
    )
    return v[ilgili]


def _kosul(v: pd.DataFrame) -> pd.DataFrame:
    """Semayi calisma calisma kosar, rapor duzeyi sonuclari dondurur."""
    kayit = []
    for sid, grup in v.groupby("study_id", sort=False):
        bulgular = sema.bulgulari_hesapla(grup)
        s = sema.rapora_topla(sid, bulgular)
        kayit.append({"study_id": sid, "olcek": s.olcek_duzeyi, "dort_sinif": s.dort_sinif})
    return pd.DataFrame(kayit)


def _dagilim(sonuc: pd.DataFrame, n_calisma: int) -> dict:
    """Rapor duzeyi dagilimi. Payda TUM gelistirme havuzudur - malignite
    ekseninde hic varligi olmayan calismalar `not_mentioned` sayilir."""
    olcek = sonuc["olcek"].value_counts().to_dict()
    dort = sonuc["dort_sinif"].value_counts().to_dict()
    kapsanmayan = n_calisma - len(sonuc)
    olcek["not_mentioned"] = olcek.get("not_mentioned", 0) + kapsanmayan
    dort["belirsiz_yetersiz_kanit"] = dort.get("belirsiz_yetersiz_kanit", 0)
    return {
        "olcek": {k: {"calisma": int(c), "yuzde": round(c / n_calisma * 100, 3)}
                  for k, c in sorted(olcek.items())},
        "dort_sinif": {k: {"calisma": int(c), "yuzde": round(c / n_calisma * 100, 3)}
                       for k, c in sorted(dort.items())},
        "kapsanmayan_calisma": int(kapsanmayan),
    }


def main() -> int:
    for y in (VARLIKLAR, CUMLELER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    gel = _gelistirme_havuzu()
    print(f"kapsam: gelistirme havuzu · {len(gel):,} calisma\n")

    v = pd.read_parquet(VARLIKLAR, columns=[
        "entity_id", "study_id", "sent_idx", "raw_text", "normalized_concept",
        "assertion", "assertion_rule", "assertion_cue", "temporality"])
    v = v[v["study_id"].isin(gel)]
    c = pd.read_parquet(CUMLELER, columns=["study_id", "sent_idx", "text"])
    v = v.merge(c, on=["study_id", "sent_idx"], how="left").rename(
        columns={"text": "cumle_metni"})
    v = _ilgili_varliklar(v)
    print(f"ilgili varlik: {len(v):,}\n")

    n = len(gel)
    cikti = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sema_surumu": sema.SEMA_SURUMU,
        "kapsam": {"gelistirme_havuzu_calisma": n, "ilgili_varlik": int(len(v))},
        "dondurulmus_aralik": DONDURULMUS_ARALIK,
        "kapiya_bagli_olmayan": KAPIYA_BAGLI_OLMAYAN,
    }

    # --- TABAN KOSUM ---------------------------------------------------
    print("### TABAN KOSUM")
    taban = _dagilim(_kosul(v), n)
    cikti["taban"] = taban
    for k, d in taban["dort_sinif"].items():
        print(f"  {k:28} {d['calisma']:>7,}  (%{d['yuzde']:6.3f})")
    print()
    for k, d in taban["olcek"].items():
        print(f"    olcek/{k:22} {d['calisma']:>7,}  (%{d['yuzde']:6.3f})")

    # --- KAPI ----------------------------------------------------------
    print(f"\n### DAGILIM KAPISI (docs/29 §8.4)")
    kapi = {}
    for sinif, ar in DONDURULMUS_ARALIK.items():
        gercek = taban["dort_sinif"].get(sinif, {"yuzde": 0.0})["yuzde"]
        gecti = ar["alt_yuzde"] <= gercek <= ar["ust_yuzde"]
        kapi[sinif] = {"gercek_yuzde": gercek, "alt": ar["alt_yuzde"],
                       "ust": ar["ust_yuzde"], "gecti": gecti}
        print(f"  {sinif}: %{gercek:.3f}  aralik [%{ar['alt_yuzde']}, "
              f"%{ar['ust_yuzde']}]  ->  {'GECTI' if gecti else 'KALDI'}")
    cikti["kapi"] = kapi

    if not all(x["gecti"] for x in kapi.values()):
        print("\n### KAPI TESHISI - populasyon nerede eriyor")
        t = _kapi_teshisi(v, c[c["study_id"].isin(gel)])
        cikti["kapi_teshisi"] = t
        print(f"  derece cumlesi                    : {t['derece_cumlesi']['cumle']:>6,}"
              f"  / {t['derece_cumlesi']['calisma']:,} calisma")
        print(f"    kanser terimi ICEREN            : {t['kanser_terimi_iceren']:>6,}")
        print(f"    kanser terimi ICERMEYEN         : {t['kanser_terimi_ICERMEYEN']:>6,}"
              f"  <- enfeksiyon/COVID suphesi")
        print(f"    kanser terimli + varlik cikan   : "
              f"{t['kanser_terimli_ve_malignite_varligi_cikan']:>6,}")
        print(f"    kanser terimli + varlik cikmayan: "
              f"{t['kanser_terimli_ama_varlik_cikmayan']:>6,}  <- sozluk boslugu")

    # --- DUYARLILIK ----------------------------------------------------
    print("\n### DUYARLILIK ANALIZI (docs/29 §7/3)")
    cikti["duyarlilik"] = {}
    for ad, meta in SENARYOLAR.items():
        b = v.copy()
        if ad == "S1_zaman_ekseni_guvenilmez":
            b["temporality"] = "current"
        elif ad == "S2_kanitsiz_present_gercek":
            m = b["assertion_rule"].eq("varsayilan_present")
            b.loc[m, "assertion_rule"] = "cikarim:uyumlu"
            b.loc[m, "assertion_cue"] = "[enjekte]"
        elif ad == "S3_hedge_aslinda_uncertain":
            m = b["assertion"].eq("present") & b["assertion_rule"].isin(sema.HEDGE_KURALLARI)
            b.loc[m, "assertion"] = "uncertain"
        d = _dagilim(_kosul(b), n)
        poz = d["dort_sinif"].get("malignite_pozitif", {"yuzde": 0.0})["yuzde"]
        taban_poz = taban["dort_sinif"].get("malignite_pozitif", {"yuzde": 0.0})["yuzde"]
        cikti["duyarlilik"][ad] = {**meta, "dagilim": d,
                                   "malignite_pozitif_yuzde": poz,
                                   "tabandan_kayma_puan": round(poz - taban_poz, 3)}
        print(f"  {ad:32} malignite_pozitif %{poz:6.3f}  "
              f"(taban %{taban_poz:.3f}, kayma {poz - taban_poz:+.3f} puan)")

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(cikti, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
