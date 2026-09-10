"""BTB3D degerlendirmesi · CT-RATE 18 anormallik sinifi cikarimi.

Uc etiket kaynagi uretir ve tek parquet'e yazar:

    A · resmi CT-RATE `valid_predicted_labels.csv`      (referans capa)
    B · kendi cikarimimiz, GT hekim raporlari uzerinde  (cikarici kalibrasyonu)
    C · kendi cikarimimiz, BTB3D uretilmis raporlarda   (olculen sey)

B↔A uyumu olmadan C↔A hatasinin ne kadari modelin ne kadari cikaricinin
oldugu ayrilamaz; bu yuzden ucu birden uretilir.

⛔ DUVAR (kullanici karari 2026-09-10): bu betigin girdisi CT-RATE `valid`
   havuzudur ve `configs/splits_holdout.json` → `degerlendirme_kilidi.
   a_ctrate_valid` altinda muhurludur. Buradan gorulen icerik YALNIZ BTB3D
   degerlendirmesinde kullanilir; sema, sozluk veya esik gelistirmesine
   YANSITILMAZ.

Kullanim:
    python scripts/74_btb3d_ctrate_18sinif.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import medspacy  # noqa: F401  - spaCy fabrikalarini kaydeder
import pandas as pd
import spacy

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.extraction import context as C  # noqa: E402
from radyovlm.extraction import entities as E  # noqa: E402

URETILEN = KOK / "data/raw/btb3d-ctrate-500-reports/generated_reports_500.csv"
RESMI_ETIKET = KOK / "data/raw/ct_rate/valid_predicted_labels.csv"
KARANTINA = KOK / "outputs/btb3d_ctrate_muhurlu"
CIKTI = KARANTINA / "ctrate500_18sinif.parquet"
OZET = KARANTINA / "ctrate500_cikarim_ozeti.json"

SURUM = "btb3d-ctrate-18sinif-1.0"

# ---------------------------------------------------------------- 18 sinif
# Her sinif: gozlem kavramlari + (istege bagli) anatomi kosulu.
# `anatomi` verilmisse varligin anatomi baglaminin O KUMEDE olmasi gerekir;
# `anatomi_disla` verilmisse o kumede OLMAMASI gerekir.

SINIFLAR: dict[str, dict] = {
    "Medical material": {
        "kavram": {"catheter", "stent", "pacemaker", "surgical_clip",
                   "prosthesis", "drainage_tube"},
    },
    "Arterial wall calcification": {
        "kavram": {"calcification", "calcific", "atheroma_plaque"},
        "anatomi": {"aorta", "vascular_structure", "pulmonary_artery",
                    "vena_cava", "aortic_valve"},
    },
    "Cardiomegaly": {
        "kavram": {"cardiomegaly"},
    },
    "Pericardial effusion": {
        "kavram": {"effusion", "effusion_thickening", "fluid_collection"},
        "anatomi": {"pericardium"},
    },
    "Coronary artery wall calcification": {
        "kavram": {"calcification", "calcific", "atheroma_plaque"},
        "anatomi": {"coronary_artery"},
    },
    "Hiatal hernia": {
        "kavram": {"hernia"},
    },
    "Lymphadenopathy": {
        "kavram": {"enlarged_lymph_node", "lymphadenomegaly"},
    },
    "Emphysema": {
        "kavram": {"emphysema", "bulla"},
    },
    "Atelectasis": {
        "kavram": {"atelectasis"},
    },
    "Lung nodule": {
        "kavram": {"nodule", "nodular_lesion"},
        "anatomi_disla": {"liver", "adrenal_gland", "kidney", "spleen",
                          "gallbladder", "pancreas", "thyroid", "breast",
                          "abdomen", "lymph_node"},
    },
    "Lung opacity": {
        "kavram": {"density_increase", "consolidation", "infiltration",
                   "ground_glass", "density"},
        "anatomi_disla": {"liver", "adrenal_gland", "kidney", "spleen",
                          "gallbladder", "pancreas", "thyroid", "breast",
                          "abdomen", "bone", "vertebra"},
    },
    "Pulmonary fibrotic sequela": {
        "kavram": {"fibrosis", "sequela_change", "sequela", "reticulation"},
    },
    "Pleural effusion": {
        "kavram": {"effusion", "effusion_thickening", "fluid_collection"},
        "anatomi_disla": {"pericardium"},
    },
    "Mosaic attenuation pattern": {
        "kavram": {"mosaic_attenuation"},
    },
    "Peribronchial thickening": {
        "kavram": {"thickening"},
        "anatomi": {"bronchus", "airway"},
    },
    "Consolidation": {
        "kavram": {"consolidation"},
    },
    "Bronchiectasis": {
        "kavram": {"bronchiectasis"},
    },
    "Interlobular septal thickening": {
        "kavram": {"septal_thickening"},
    },
}

ETIKET_SIRASI = list(SINIFLAR)

# ------------------------------------------------------- yerel yuzey yamasi
# ⛔ Bunlar YEREL'dir: `configs/bulgu_sozlugu.yaml` DONDURULMUS kalir.
#    Gerekce - uc sinifta dondurulmus sozluk CT-RATE etiket tanimiyla
#    ortusmuyor; teshis sozlugun KENDISINDEN yapildi, muhurlu metinden degil:
#
#    Lymphadenopathy  `enlarged lymph nodes?` bitisiklik istiyor, araya sifat
#                     girince ('enlarged mediastinal lymph nodes') kaciyor.
#    Peribronchial    `bronchus` anatomisi 'peribronchial' / 'bronchial wall'
#      thickening     yuzeylerini tanimiyor, anatomi kosulu hic tetiklenmiyor.
#    Cardiomegaly     `cardiomegaly` kavrami notr 'heart size' / 'heart
#                     dimensions' yuzeylerini de kapsiyor; bunlar 'normaldir'
#                     cumlelerinde de gectigi icin yanlis pozitif uretiyor.
#                     Yerel desen ARTIS sarti koyar.
#
#    Bu yama sozluk hatasini duzeltmez, YALNIZ bu degerlendirmenin esleme
#    katmanini CT-RATE etiket tanimina hizalar. Sozluk onarimi ayri bir istir
#    ve muhurlu kumeden BAGIMSIZ kanitla yapilmalidir.

import re  # noqa: E402

YEREL_DESEN: dict[str, re.Pattern] = {
    "Lymphadenopathy": re.compile(
        r"lymphadenopath(?:y|ies)|lymphadenomegal(?:y|ies)|"
        r"\benlarged\b[^.;]{0,40}?\blymph(?:atic)? nodes?\b|"
        r"\blymph(?:atic)? nodes?\b[^.;]{0,40}?\b\d+(?:[.,]\d+)?\s*mm\b|"
        r"\b(?:pathological|significant|prominent|conglomerate)\b[^.;]{0,30}?"
        r"\blymph(?:atic)? nodes?\b", re.I),
    "Peribronchial thickening": re.compile(
        r"peri-?bronchial\s+(?:wall\s+)?thicken|"
        r"bronchial\s+wall\s+thicken|"
        r"thickening\s+of\s+the\s+bronchial\s+wall", re.I),
    "Cardiomegaly": re.compile(
        r"\bcardiomegaly\b|"
        r"heart\s+(?:size|dimensions?)\s+(?:is\s+|are\s+|was\s+|were\s+)?"
        r"(?:mildly\s+|markedly\s+|moderately\s+)?increas|"
        r"(?:CTO(?: ratio)?|cardiothoracic\s+(?:ratio|index))"
        r"[^.;]{0,25}?increas", re.I),
}

# Yerel desenle degistirilen siniflarda DONDURULMUS kavram eslemesi kapatilir,
# yoksa iki yol birbirini gecersiz kilar.
YEREL_DESEN_TEKEL = set(YEREL_DESEN)


class _YerelKavram:
    """kesinlik_ata'nin bekledigi asgari kavram arayuzu."""

    __slots__ = ("ad", "tip")

    def __init__(self, ad: str) -> None:
        self.ad = ad
        self.tip = "observation"


# ------------------------------------------------------------------ cikarim

def _anatomi_baglami(varlik: dict, iliskiler: list[dict],
                     cumle_anatomileri: set[str]) -> set[str]:
    """Varligin anatomi baglami: once `located_at`, yoksa cumledeki anatomi.

    `located_at` tekil ve en-yakin-komsu kuraliyla kuruldugu icin tek basina
    guvenilmez (olculdu: 'right upper lobe' yerine 'hemithorax' secilebiliyor).
    Bu yuzden iliski hedefi VE cumle anatomileri birlikte dondurulur; sinif
    kosullari kume kesisimi ile calisir.
    """
    baglam = set(cumle_anatomileri)
    for r in iliskiler:
        if r["tip"] != "located_at":
            continue
        bas = r["head"]
        if not isinstance(bas, dict):
            continue
        if bas["bas"] != varlik["bas"] or bas["son"] != varlik["son"]:
            continue
        kuy = r["tail"]
        if isinstance(kuy, dict) and kuy.get("kavram") is not None:
            baglam.add(kuy["kavram"].ad)
    return baglam


def rapor_etiketle(metin: str, nlp, matcher, indeks, ipuclari,
                   sonlandirici, siniflar: dict | None = None,
                   yerel_desen: dict | None = None
                   ) -> tuple[dict[str, int], list[dict]]:
    """Bir rapor metnini ikili siniflara cevirir. Kanit satirlari da doner.

    `siniflar`/`yerel_desen` verilmezse bu betigin CT-RATE 18 sinifi kullanilir;
    betik 76 (NLST) ayni motoru kendi sinif kumesiyle cagirir.
    """
    siniflar = SINIFLAR if siniflar is None else siniflar
    yerel_desen = YEREL_DESEN if yerel_desen is None else yerel_desen
    tekel = set(yerel_desen)
    varsa = {ad: 0 for ad in siniflar}
    kanit: list[dict] = []

    for sent in nlp(metin).sents:
        cumle = sent.text.strip()
        if not cumle or not any(c.isalpha() for c in cumle):
            continue
        varliklar = E.cumleden_varliklar(cumle, matcher, indeks)

        # Yerel yuzey yamasi: sozde-varlik olarak AYNI negasyon cozumlemesinden
        # gecer, boylece 'no ... lymph nodes' hala absent olur.
        yerel: list[dict] = []
        for sinif, desen in yerel_desen.items():
            for mm in desen.finditer(cumle):
                yerel.append({"bas": mm.start(), "son": mm.end(),
                              "metin": mm.group(0),
                              "kavram": _YerelKavram(f"yerel::{sinif}")})
        if not varliklar and not yerel:
            continue

        iliskiler, _ = E.iliskileri_kur(varliklar, [], cumle)
        varliklar = C.kesinlik_ata(cumle, varliklar + yerel, ipuclari,
                                   sonlandirici)

        cumle_anatomileri = {v["kavram"].ad for v in varliklar
                             if v["kavram"].tip == "anatomy"}

        for v in varliklar:
            if v["assertion"] != "present":
                continue          # absent/uncertain POZITIF SAYILMAZ
            ad = v["kavram"].ad

            if ad.startswith("yerel::"):
                sinif = ad.split("::", 1)[1]
                varsa[sinif] = 1
                kanit.append({"sinif": sinif, "kavram": ad,
                              "metin": v["metin"], "cumle": cumle,
                              "kural": v["assertion_rule"]})
                continue

            baglam = None
            for sinif, kural in siniflar.items():
                if sinif in tekel:
                    continue      # bu sinifi YALNIZ yerel desen belirler
                if ad not in kural["kavram"]:
                    continue
                if baglam is None:
                    baglam = _anatomi_baglami(v, iliskiler, cumle_anatomileri)
                if "anatomi" in kural and not (baglam & kural["anatomi"]):
                    continue
                if "anatomi_disla" in kural and (baglam & kural["anatomi_disla"]):
                    continue
                varsa[sinif] = 1
                kanit.append({"sinif": sinif, "kavram": ad,
                              "metin": v["metin"], "cumle": cumle,
                              "kural": v["assertion_rule"]})
    return varsa, kanit


# -------------------------------------------------------------------- excel

def excel_yaz(gen: pd.DataFrame, etiketler: pd.DataFrame,
              kanit: pd.DataFrame) -> None:
    """Yan yana inceleme calisma kitabi (karantina dizinine yazilir).

    Sayfalar:
      Karsilastirma · her satir bir seri: BTB3D raporu | orijinal bulgu |
                      orijinal sonuc, ardindan 18 sinif icin A/B/C sutunlari
      Etiketler     · yalniz ikili etiket matrisi (metinsiz, pivot icin)
      Kanit         · hangi cumle hangi sinifi tetikledi
      Prevalans     · sinif basina A/B/C pozitif sayilari
      OKUBENI       · muhur ve surum beyani
    """
    yol = KARANTINA / "btb3d_ctrate500_karsilastirma.xlsx"

    k = gen[["VolumeName", "Generated_Report", "Ground_Truth_Findings",
             "Ground_Truth_Impressions"]].merge(etiketler.drop(
                 columns=["surum", "varlik_surumu", "baglam_surumu"]),
                 on="VolumeName", how="left")
    k = k.rename(columns={
        "Generated_Report": "BTB3D_Raporu",
        "Ground_Truth_Findings": "Orijinal_Bulgular",
        "Ground_Truth_Impressions": "Orijinal_Sonuc"})

    # A/B/C uclusunu sinif basina yan yana getir; okunurluk icin isaret sutunu
    for ad in ETIKET_SIRASI:
        a, b, c = k[f"A::{ad}"], k[f"B::{ad}"], k[f"C::{ad}"]
        k[f"± {ad}"] = [
            "TP" if (ai and ci) else "FN" if (ai and not ci)
            else "FP" if (not ai and ci) else "TN"
            for ai, ci in zip(a, c)]

    prevalans = pd.DataFrame([
        {"Sinif": ad,
         "A resmi": int(etiketler[f"A::{ad}"].sum()),
         "B kendi cikarim (GT)": int(etiketler[f"B::{ad}"].sum()),
         "C kendi cikarim (BTB3D)": int(etiketler[f"C::{ad}"].sum())}
        for ad in ETIKET_SIRASI])

    okubeni = pd.DataFrame({"Alan": [
        "Surum", "Varlik surumu", "Baglam surumu", "Rapor sayisi",
        "A kaynagi", "B kaynagi", "C kaynagi", "Pozitif kurali", "MUHUR"],
        "Deger": [
        SURUM, E.ENTITY_VERSION, C.CONTEXT_VERSION, len(etiketler),
        "CT-RATE valid_predicted_labels.csv (RadBERT, GT raporlardan)",
        "kendi negasyon-farkindali cikarimimiz, GT hekim raporunda",
        "kendi negasyon-farkindali cikarimimiz, BTB3D uretilmis raporunda",
        "assertion == 'present' olan en az bir varlik; absent/uncertain sayilmaz",
        "CT-RATE valid muhurlu havuz - icerik yalniz BTB3D degerlendirmesinde "
        "kullanilir, sema/sozluk gelistirmesine yansitilmaz"]})

    with pd.ExcelWriter(yol, engine="openpyxl") as w:
        okubeni.to_excel(w, sheet_name="OKUBENI", index=False)
        k.to_excel(w, sheet_name="Karsilastirma", index=False)
        etiketler.to_excel(w, sheet_name="Etiketler", index=False)
        prevalans.to_excel(w, sheet_name="Prevalans", index=False)
        kanit.to_excel(w, sheet_name="Kanit", index=False)

        ws = w.sheets["Karsilastirma"]
        ws.freeze_panes = "B2"
        for kol, en in (("A", 22), ("B", 70), ("C", 70), ("D", 45)):
            ws.column_dimensions[kol].width = en
    print(f"excel  : {yol}")


def main() -> None:
    gen = pd.read_csv(URETILEN)
    resmi = pd.read_csv(RESMI_ETIKET)

    eksik = set(ETIKET_SIRASI) - set(resmi.columns)
    if eksik:
        raise ValueError(f"resmi etiket tablosunda eksik sinif: {sorted(eksik)}")

    resmi = resmi[resmi.VolumeName.isin(gen.VolumeName)].set_index("VolumeName")
    if len(resmi) != len(gen):
        raise ValueError(f"resmi etiket ortusmesi eksik: {len(resmi)}/{len(gen)}")

    nlp = spacy.blank("en")
    nlp.add_pipe("medspacy_pyrush")

    kavramlar, _ = E.sozlukleri_yukle()
    matcher, indeks = E.matcher_kur(kavramlar)
    ipuclari, sonlandirici = C.ipuclarini_kur()

    satirlar: list[dict] = []
    kanitlar: list[dict] = []

    for i, r in enumerate(gen.itertuples(index=False), 1):
        gt_metin = f"{r.Ground_Truth_Findings} {r.Ground_Truth_Impressions}"
        b, kb = rapor_etiketle(gt_metin, nlp, matcher, indeks, ipuclari,
                              sonlandirici)
        c, kc = rapor_etiketle(str(r.Generated_Report), nlp, matcher, indeks,
                              ipuclari, sonlandirici)
        a = resmi.loc[r.VolumeName]

        satir = {"VolumeName": r.VolumeName}
        for ad in ETIKET_SIRASI:
            satir[f"A::{ad}"] = int(a[ad])
            satir[f"B::{ad}"] = b[ad]
            satir[f"C::{ad}"] = c[ad]
        satirlar.append(satir)

        for kaynak, kk in (("B", kb), ("C", kc)):
            for x in kk:
                kanitlar.append({"VolumeName": r.VolumeName, "kaynak": kaynak,
                                 **x})
        if i % 100 == 0:
            print(f"  {i}/{len(gen)} rapor")

    out = pd.DataFrame(satirlar)
    out["surum"] = SURUM
    out["varlik_surumu"] = E.ENTITY_VERSION
    out["baglam_surumu"] = C.CONTEXT_VERSION

    KARANTINA.mkdir(parents=True, exist_ok=True)
    out.to_parquet(CIKTI, index=False)
    kanit_df = pd.DataFrame(kanitlar)
    kanit_df.to_parquet(CIKTI.with_name("ctrate500_kanit.parquet"), index=False)
    excel_yaz(gen, out, kanit_df)

    ozet = {
        "surum": SURUM,
        "baglam_surumu": C.CONTEXT_VERSION,
        "rapor": int(len(out)),
        "sinif": len(ETIKET_SIRASI),
        "prevalans": {
            ad: {k: int(out[f"{k}::{ad}"].sum()) for k in "ABC"}
            for ad in ETIKET_SIRASI
        },
        "kanit_satiri": int(len(kanitlar)),
        "duvar": ("CT-RATE valid muhuru · icerik yalniz BTB3D "
                  "degerlendirmesinde kullanilir"),
    }
    OZET.write_text(json.dumps(ozet, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"\nyazildi: {CIKTI}")
    print(f"ozet   : {OZET}")


if __name__ == "__main__":
    main()
