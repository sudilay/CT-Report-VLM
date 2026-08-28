# -*- coding: utf-8 -*-
"""Kavramlarimizin TURKCE yuzeylerini yazar ve RadTr'de OLCER.

NEDEN:
  Sistemin dili Turkce olacak. Once cevrilmesi gereken sey MIMARI degil
  SOZLUKTUR - ama once "kavram envanterimiz Turkceye tasiniyor mu" sorusu
  cevaplanmali. RadTr (429 uzman-yazimi Turkce toraks belgesi) bunu olcmenin
  tek yolu.

⚠ BU BIR TASLAKTIR - UZMAN DOGRULAMASI GEREKIR.
  Radyoloji Turkcesi buyuk olcude Latin kokenli translitasyondur (nodul,
  plevra, efuzyon) ve bu yuzeyler makul gorunuyor. Ama "makul gorunmek"
  dogrulama degildir. Yuzeyler radyolog onayindan gecmeden sisteme girmez.

DESEN KURALI - TURKCEYE OZGU:
  Turkce sondan eklemeli: "akcigerde", "akcigerin", "nodulleri". Bu yuzden
  desenler BASTA sinirlidir, SONDA DEGIL.  \bakci[gğ]er  degil  \bakcigers?\b
  Ilk olcumde bu unutuldu ve 'b[uü]l' deseni "bulgu"/"bulunmaktadir"
  yakalayarak bulla'yi RadTr'de CT-RATE'ten daha sik gosterdi. Bu, tools/
  README'deki kelime siniri tuzaginin Turkce hali.

Kullanim: .venv/Scripts/python.exe scripts/20_turkce_yuzey_taslagi.py
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
BS = chr(92)

# kavram -> Turkce yuzey deseni (BAS sinirli)
YUZEY = {
    # --- gozlem ---
    "nodule": "nod[uü]l", "mass": "kitle", "lesion": "lezyon",
    "effusion": "ef[uü]zyon", "thickening": "kal[ıi]nla[şs]",
    "consolidation": "konsolidasyon", "infiltration": "infiltrasyon",
    "pneumonia": "pn[oö]moni", "emphysema": "amfizem",
    "bronchiectasis": "bron[şs]ektazi", "cyst": "kist",
    "calcification": "kalsifi|kire[çc]len", "atelectasis": "atelektazi",
    "fibrosis": "fibro", "metastasis": "metastaz", "granuloma": "gran[uü]lom",
    "cavitation": "kavit", "pneumothorax": "pn[oö]motoraks",
    "cardiomegaly": "kardiyomegali", "aneurysm": "anevrizma",
    "hernia": "herni|f[ıi]t[ıi]k", "fracture": "frakt[uü]r|k[ıi]r[ıi]k",
    "bulla": "b[uü]l(?:l|[oö]z)", "reticulation": "retik[uü]l",
    "density": "dansite", "density_increase": "dansite art",
    "enlarged_lymph_node": "lenfadenopati|patolojik.{0,20}lenf",
    "lymphadenomegaly": "lenfadenomegali", "covid": "covid|kovid",
    "edema": "[oö]dem", "hepatosteatosis": "hepatosteatoz|karaci[gğ]er.{0,15}ya[gğ]lan",
    "nephrolithiasis": "b[oö]brek ta[şs]", "cholelithiasis": "safra ta[şs]|kolelit",
    "sequela_change": "sekel", "spondylosis": "spondiloz",
    "degenerative_change": "dejeneratif", "septal_thickening": "septal kal[ıi]nla",
    "air_bronchogram": "hava bronkogram", "goiter": "guatr", "lymphoma": "lenfoma",
    "occlusive_pathology": "t[ıi]kay[ıi]c[ıi]|okl[uü]z",
    "cardiothoracic_ratio": "kardiyotorasik|KTO",
    "space_occupying_lesion": "yer kaplayan lezyon",
    "fluid_collection": "s[ıi]v[ıi] koleksiyon",
    # --- anatomi ---
    "lung": "akci[gğ]er", "lung_parenchyma": "parankim", "pleura": "plevra",
    "mediastinum": "mediasten", "heart": "kalp|kardiyak", "aorta": "aort",
    "trachea": "trakea", "bronchus": "bron[şs]", "esophagus": "[oö]zofagus",
    "liver": "karaci[gğ]er", "kidney": "b[oö]brek", "lymph_node": "lenf",
    "upper_lobe": "[uü]st lob", "lower_lobe": "alt lob", "middle_lobe": "orta lob",
    "lingula": "lingul", "hilum": "hilus|hiler", "pericardium": "perikard",
    "pulmonary_artery": "pulmoner arter", "vertebra": "vertebra", "bone": "kemik",
    "chest_wall": "g[oö][gğ][uü]s duvar|toraks duvar", "thyroid": "tiroid",
    "spleen": "dalak", "adrenal_gland": "s[uü]rrenal|adrenal",
    "gallbladder": "safra kesesi", "fissure": "fiss[uü]r",
    "hemithorax": "hemitoraks", "lung_apex": "apeks|apikal",
    "soft_tissue": "yumu[şs]ak doku", "vascular_structure": "vask[uü]ler",
    "coronary_artery": "koroner", "abdomen": "abdomen|bat[ıi]n", "breast": "meme",
    "pleuroparenchymal": "plevroparankimal", "aortic_valve": "aort kapa",
    "pulmonary_conus": "pulmoner konus", "anatomic_segment": "segment",
}


def main() -> None:
    yol = PROC / "radtr_toraks.jsonl"
    if not yol.exists():
        sys.exit("once scripts/16_extract_radtr_thorax.py calistirilmali")
    metin = " ".join(json.loads(l)["metin"] for l in yol.open(encoding="utf-8"))
    ing = pd.read_parquet(PROC / "entities.parquet").normalized_concept.value_counts()

    kayit, var, yok = {}, 0, []
    for k, d in YUZEY.items():
        n = len(re.findall(BS + "b(?:" + d + ")", metin, re.I))
        kayit[k] = {"desen": d, "radtr": n, "ct_rate_ingilizce": int(ing.get(k, 0)),
                    "uzman_onayi": False}
        if n:
            var += 1
        else:
            yok.append((k, int(ing.get(k, 0))))

    cikti = ROOT / "configs" / "turkce_yuzeyler_taslak.yaml"
    with cikti.open("w", encoding="utf-8") as f:
        f.write("# TURKCE YUZEY TASLAGI - surum: tr-0.1 (TASLAK)\n"
                "#\n"
                "# ⚠ HICBIR YUZEY UZMAN ONAYINDAN GECMEDI. 'uzman_onayi: false'\n"
                "#   olan hicbir girdi sisteme alinmaz.\n"
                "#\n"
                "# 'radtr' sayilari RadTr'nin 429 uzman-yazimi Turkce toraks\n"
                "# belgesinde OLCULDU (59.041 kelime). 'ct_rate_ingilizce'\n"
                "# karsilastirma icindir; iki korpus farkli buyuklukte oldugu\n"
                "# icin sayilar dogrudan kiyaslanamaz, VARLIK/YOKLUK anlamlidir.\n"
                "#\n"
                "# Desenler BASTA sinirlidir - Turkce sondan eklemelidir.\n\n")
        yaml.safe_dump({"surum": "tr-0.1", "durum": "taslak",
                        "kaynak": "RadTr toraks alt kumesi (429 belge)",
                        "yuzeyler": kayit},
                       f, allow_unicode=True, sort_keys=False)

    print(f"yazildi: {cikti.name}")
    print(f"  {len(YUZEY)} kavram · RadTr'de var {var} (%{100*var/len(YUZEY):.0f}) · yok {len(yok)}")
    print("\nRADTR'DE GECMEYENLER (CT-RATE sikligiyla):")
    for k, c in sorted(yok, key=lambda x: -x[1]):
        print(f"  {k:<24}{c:>8,}")


if __name__ == "__main__":
    main()
