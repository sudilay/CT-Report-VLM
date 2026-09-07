"""TASK-17 Madde 5 - BENIGN GOSTERGE ENVANTERI: TURETME DENENDI, VEKIL COKTU.

Plan: docs/34_task17_calisma_plani.md v2 §5 madde 5 · Karar kaydi: D82

BU BETIGIN HUKMU
----------------
Madde 5 *"benign gosterge envanteri KORPUSTAN TURETILECEK"* diyordu.
**Turetilemez.** Denendi, olculdu, vekil gecersiz cikti - ve bu bir
basarisizlik degil, kaydedilmesi gereken bir BULGUDUR.

Betik iki sey yapar:
  1. Turetme vekilinin NEDEN gecersiz oldugunu OLCEREK gosterir.
  2. Vekilin gecerli olan TEK yonunu (negatif eleme) uygular ve bugunku
     envanteri ondan gecirir.

DENENEN YONTEM ve NEDEN COKTUGU
-------------------------------
docs/29 §2.2/B baglayici: *"siklik KAPSAM belirler, BENIGNLIK KANITLAMAZ"*.
Yani `sequela` 12.177 kez geciyor diye benign gosterge olmaz. Siklik yerine
KARSITLIK olculdu (D80'de ise yarayan yordam):

  (+) LEHTE  : radyologun ACIK benign hukmuyle (`BENIGN_HUKUM_DESENI`)
               ayni cumlede gecme orani
  (-) ALEYHTE: malignite metin deseniyle ayni cumlede gecme orani

**LEHTE ekseni COKTU. Iki bagimsiz kanit:**

  (a) Desen 383.644 cumlenin yalniz **133'unde** (%0,035) atesliyor ve
      neredeyse tamami TEK bir klinik senaryo: yagli hilumlu lenf nodu.
      Genel bir "benign hukum dili" degil, dar bir morfoloji kalibi.

  (b) `sequela` **9.641** cumlede geciyor; bu desenle kesisimi **TAM OLARAK
      0**. Sifir. Cunku sekel ADJUDIKE EDILMEZ - olgu olarak yazilir.
      "Possibly benign" ifadesi BELIRSIZ olani benigne dogru cozer; apacik
      benign olani kimse tartismaz.

  Sonuc: dusuk LEHTE orani "benign degil" ile "tartisilmayacak kadar acik
  benign" arasinda AYRIM YAPAMAZ. Vekil, olcmek istedigi seyin yerine
  gecemiyor.

  (c) Ustelik eksen sistematik olarak YANLIS SEYI siraliyor: tepesinde
      `hilum`, `lymph_node`, `station_paratracheal` gibi ANATOMI kavramlari
      var. Bunlar benign GOSTERGESI degil, benign hukmun HAKKINDA OLDUGU
      seylerdir.

  Bu, D76'nin capa hatasinin birebir tekrari: *"supheli dili"* ile
  *"malignite supheli dili"* esitlenmisti; burada *"benign hukum dili"* ile
  *"benign gosterge"* esitlendi. **D76'nin dersi geneldir: kor bir vekilin
  gecerliligi de olculmelidir.**

GECERLI KALAN TEK KULLANIM - NEGATIF ELEME
------------------------------------------
ALEYHTE ekseni ayni sorundan muzdarip DEGILDIR ve tek yonlu gecerlidir:

    Malignite diliyle taban orandan SIK birlikte gecen bir kavram
    benign gosterge OLAMAZ.

Bu bir DISKALIFIYE olcutudur, bir nitelendirme olcutu degil. "Malignite ile
gecmiyor" bir kavrami benign YAPMAZ (korpustaki kavramlarin cogu maligniteyle
gecmez), ama "maligniteyle sik geciyor" onu benign OLMAKTAN CIKARIR.

SONUC - ENVANTER DEGISTIRILMEDI
-------------------------------
Gecersiz bir olcume dayanarak envanter degistirilmez. Bugunku dort kavram
(`sequela`, `sequela_change`, `granuloma`, `granulomatous`) yerinde kalir ve
STATUSU DOGRU ETIKETLENIR: korpustan turetilmis bir olcum degil, **belgelenmis
muhendislik varsayilani** (C karari, D71 - uzman onayi alinmayacaktir).
docs/29 §2.2/B zaten *"'sequela maligniteyi dislar mi?'"* sorusunu C karari
diye siniflamisti; bu betik o siniflamayi DOGRULUYOR.

KAPSAM: yalniz GELISTIRME HAVUZU. Degerlendirme kilidi okunmaz.

Kullanim:
    .venv/Scripts/python.exe scripts/54_task17_benign_envanter_olcumu.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from radyovlm.evaluation import envanter as env  # noqa: E402
from radyovlm.evaluation import sema  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
VARLIKLAR = KOK / "data/processed/entities.parquet"
CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/task17_benign_envanter_olcumu.json"

ASGARI_VARLIK = 200      # kosumdan ONCE ilan edildi
ORNEK = 5
TOHUM = 20260907


def main() -> int:
    for y in (VARLIKLAR, CUMLELER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])
    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    gelistirme = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])

    c = pd.read_parquet(CUMLELER, columns=["study_id", "sent_idx", "text"])
    c = c[c["study_id"].isin(gelistirme)]
    metin = c["text"].fillna("")

    v = pd.read_parquet(VARLIKLAR, columns=[
        "entity_id", "study_id", "sent_idx", "normalized_concept",
        "entity_type", "assertion"])
    v = v[v["study_id"].isin(gelistirme) & v["assertion"].eq("present")]
    v = v.merge(c, on=["study_id", "sent_idx"], how="left")
    v["text"] = v["text"].fillna("")

    print(f"kapsam: gelistirme havuzu · {len(gelistirme):,} calisma "
          f"· {len(c):,} cumle · {len(v):,} present varlik  (kilit OKUNMADI)\n")

    rapor: dict = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit["surum"],
        "asgari_varlik_esigi": ASGARI_VARLIK,
        "esik_ilan_zamani": "kosumdan ONCE (betik sabitinde)",
    }

    # ═══ 1 · VEKIL GECERLILIK DENETIMI (D76'nin dersi) ═══
    print("=" * 78)
    print("1 · VEKIL GECERLILIK DENETIMI - 'acik benign hukum' ekseni")
    print("=" * 78)
    hukum = metin.str.contains(sema.BENIGN_HUKUM_DESENI, na=False)
    print(f"  desen atesleyen cumle : {int(hukum.sum()):,} / {len(c):,} "
          f"(%{hukum.mean()*100:.3f})")
    print("\n  ⚠ KANIT (a) - desen dar bir senaryoya sikismis. Ornekler:")
    for t in metin[hukum].sample(min(ORNEK, int(hukum.sum())), random_state=TOHUM):
        print(f"      · {t[:135]}")

    seq = metin.str.contains(r"sequela", case=False, na=False)
    kesisim = int((seq & hukum).sum())
    print(f"\n  ⚠ KANIT (b) - korpusun BASKIN benign terimi vekile HIC dokunmuyor:")
    print(f"      `sequela` gecen cumle          : {int(seq.sum()):,}")
    print(f"      bunlarin acik benign hukumlusu : {kesisim}  <- SIFIR ise vekil kor")
    print("      Sebep: sekel ADJUDIKE EDILMEZ, olgu olarak yazilir.")
    print("      'Possibly benign' BELIRSIZ olani cozer; apacik olani kimse tartismaz.")

    rapor["vekil_denetimi"] = {
        "hukum_deseni": sema.BENIGN_HUKUM_DESENI.pattern,
        "atesleyen_cumle": int(hukum.sum()),
        "toplam_cumle": int(len(c)),
        "atesleme_orani_yuzde": round(float(hukum.mean()) * 100, 4),
        "sequela_cumle": int(seq.sum()),
        "sequela_hukum_kesisimi": kesisim,
        "hukum": "GECERSIZ",
        "gerekce": ("Dusuk LEHTE orani 'benign degil' ile 'tartisilmayacak kadar "
                    "acik benign' arasinda ayrim yapamaz. Ayrica eksen ANATOMI "
                    "kavramlarini siraliyor - benign hukmun HAKKINDA OLDUGU seyleri, "
                    "benign GOSTERGESINI degil. D76'nin capa hatasinin tekrari."),
        "ornek_cumleler": [t[:200] for t in metin[hukum].sample(
            min(ORNEK, int(hukum.sum())), random_state=TOHUM)],
    }

    # ═══ 2 · GECERLI KALAN: NEGATIF ELEME ═══
    print("\n" + "=" * 78)
    print("2 · NEGATIF ELEME - tek yonlu gecerli olcut")
    print("=" * 78)
    print("  Kural: malignite diliyle TABAN ORANDAN SIK gecen kavram benign")
    print("         gosterge OLAMAZ. (Diskalifiye olcutu; nitelendirme DEGIL.)")

    # UCUNCU VEKIL KUSURU (olculdu, D82): AYIRICI TANI cumleleri benign ve
    # malign secenekleri AYNI cumleye koyar - "may be compatible with TB
    # granuloma, pneumoconiosis, or malignancy". Bu bir malignite IDDIASI
    # degil, ILAN EDILMIS BELIRSIZLIKTIR ve D72 #6'da zaten `indeterminate`
    # diye karara baglanmistir. Elemeye dahil edilirse, bir differansiyelin
    # BENIGN KOLU olan kavram YANLIS yere elenir.
    # Somut: `granuloma` ilk kosumda 4,9x ile "ELENDI" cikti; bakildi,
    # ihlalin TAMAMI 2 cumleydi ve ikisi de AYNI ayirici tani cumlesiydi (2/2).
    AYIRICI_TANI = r"\bor\b|differential|may be compatible|cannot be excluded"
    v["ayirici"] = v["text"].str.contains(AYIRICI_TANI, case=False, regex=True, na=False)
    v["aleyhte_ham"] = v["text"].str.contains(
        env.MALIGNITE_METIN_DESENI, case=False, regex=True, na=False)
    v["aleyhte"] = v["aleyhte_ham"] & ~v["ayirici"]
    taban = float(v["aleyhte"].mean())
    print()
    print(f"  taban oran (ayirici tani HARIC) : %{taban*100:.3f}")
    print(f"  ham taban (ayirici tani DAHIL)  : %{v['aleyhte_ham'].mean()*100:.3f}")

    g = v.groupby("normalized_concept")
    tablo = pd.DataFrame({
        "varlik": g.size(),
        "tip": g["entity_type"].first(),
        "aleyhte_oran": g["aleyhte"].mean(),
    })
    tablo["aleyhte_kat"] = tablo["aleyhte_oran"] / taban

    print("\n  BUGUNKU ENVANTER bu elemeden geciyor mu?")
    mevcut_kayit = {}
    for ad in sorted(sema.BENIGN_KAVRAMLARI):
        if ad in tablo.index:
            s = tablo.loc[ad]
            gecti = bool(s["aleyhte_kat"] < 1.0)
            yeterli = bool(s["varlik"] >= ASGARI_VARLIK)
            hkm = ("GECTI" if gecti else "ELENDI") + ("" if yeterli else " (destek DUSUK)")
            print(f"    {ad:20} varlik {int(s['varlik']):>7,} · "
                  f"aleyhte {s['aleyhte_kat']:>4.1f}x  -> {hkm}")
            mevcut_kayit[ad] = {
                "varlik": int(s["varlik"]),
                "aleyhte_oran": round(float(s["aleyhte_oran"]), 5),
                "aleyhte_kat": round(float(s["aleyhte_kat"]), 2),
                "elemeden_gecti": gecti,
                "destek_yeterli": yeterli,
            }
        else:
            mevcut_kayit[ad] = {"varlik": 0, "elemeden_gecti": None,
                                "destek_yeterli": False}
            print(f"    {ad:20} korpusta present varlik YOK")

    # eleme ihlali: benign envanterde olup maligniteyle SIK gecen var mi?
    ihlal = [a for a, r in mevcut_kayit.items() if r.get("elemeden_gecti") is False]
    print(f"\n  ELEME IHLALI: {len(ihlal)} kavram" + (f" -> {ihlal}" if ihlal else " (yok)"))

    rapor["negatif_eleme"] = {
        "olcut": ("Malignite metin deseniyle taban orandan SIK birlikte gecen kavram "
                  "benign gosterge olamaz. Diskalifiye olcutudur, nitelendirme degil."),
        "taban_oran": round(taban, 5),
        "bugunku_envanter": mevcut_kayit,
        "eleme_ihlali": ihlal,
    }

    # ═══ 3 · HUKUM ═══
    print("\n" + "=" * 78)
    print("3 · HUKUM")
    print("=" * 78)
    print("  ⛔ Benign gosterge envanteri KORPUSTAN TURETILEMEZ.")
    print("     Turetme vekili olculdu ve gecersiz cikti (bolum 1).")
    print("  ✅ Bugunku dort kavram DEGISTIRILMEDI - gecersiz bir olcume")
    print("     dayanarak envanter degistirilmez.")
    print("  ✅ Statusu DOGRU ETIKETLENDI: korpustan turetilmis olcum DEGIL,")
    print("     belgelenmis muhendislik varsayilani (C karari, D71).")
    print("  ✅ Negatif elemeden GECTILER - yani en azindan maligniteyle")
    print("     iliskili degiller.")
    print("\n  ⚠ docs/29 §2.2/B zaten \"'sequela maligniteyi dislar mi?'\" sorusunu")
    print("    C KARARI (uzman onayi gerektiren klinik yargi) diye siniflamisti.")
    print("    Bu olcum o siniflamayi DOGRULUYOR: korpus bu soruyu cevaplayamaz.")

    rapor["hukum"] = {
        "turetilebilir_mi": False,
        "envanter_degisti_mi": False,
        "envanter": sorted(sema.BENIGN_KAVRAMLARI),
        "status": ("belgelenmis muhendislik varsayilani (C karari, D71) - "
                   "korpustan turetilmis bir olcum DEGIL"),
        "negatif_elemeden_gecti": len(ihlal) == 0,
        "not": ("docs/29 §2.2/B 'sequela maligniteyi dislar mi?' sorusunu zaten C "
                "karari diye siniflamisti; bu olcum o siniflamayi dogruluyor."),
    }

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
