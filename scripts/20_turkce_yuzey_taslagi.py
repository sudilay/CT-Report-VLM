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

BOLUNME DISIPLINI (tr-0.3 ile eklendi):
  RadTr KENDI yayimlanmis bolunmesini tasiyor (train 327 / dev 46 / test 56) ve
  16_extract_radtr_thorax.py bunu `kaynak_bolum` alaninda korudu. Turkce yuzeyler
  YALNIZCA train+dev uzerinde gelistirilir; test 56 belge DOKUNULMAZDIR.

  Neden bu kadar onemli: kirlenmenin YONU tehlikeli. Desenler test'e uydurulursa
  Turkce taraf haksiz yere iyi cikar ve dil ablasyonundan yanlislikla "Turkce veri
  onemliymis" sonucu cikar - yani kirlenme tam da varmak istedigimiz sonucu bozar.

  MARUZIYET KAYDI: tr-0.1 sayimlari bolunmeden ONCE 429 belgenin tamaminda bir kez
  yapildi. Sinirli ve olculmus bir maruziyettir: hicbir belge okunmadi, hicbir skor
  hesaplanmadi, ve sonuc train+dev uzerinde BIREBIR yeniden uretildi (72/82 = %88,
  test dahil ve haric ayni). Test bolumu o sonuca hicbir sey katmadi.

Kullanim:
    .venv/Scripts/python.exe scripts/20_turkce_yuzey_taslagi.py
    .venv/Scripts/python.exe scripts/20_turkce_yuzey_taslagi.py --bolum test  # KILITLI
"""
import argparse
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
    # BETIMLEYICI KALIP (tr-0.3): "kardiyomegali" train+dev'de 0 anma verdi ama
    # "kalp boyutlari" 313 kez geciyor. Turkce raporlar Latince adlastirma yerine
    # TAM CUMLE kuruyor. Kesinligi tasiyan kelime kalibin ICINDE ("artmistir" =
    # present, "normal sinirlarda" = absent) - ipucu sozlugunde ele alinacak.
    "cardiomegaly": "kardiyomegali|kalp boyut|kardiyak boyut", "aneurysm": "anevrizma",
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

    # ---------------- tr-0.3: kalan 62 kavram ----------------
    # Radyoloji Turkcesi buyuk olcude Latin kokenli translitasyondur; bu yuzden
    # cogu yuzey Ingilizce terimin Turkce yazimidir (nodul, plevra, efuzyon).
    # Ozturkce karsiligi yaygin olanlarda IKISI de yazilir ("dif[uü]z|yayg[ıi]n").
    # --- gozlem ---
    "tumor": "t[uü]m[oö]r|neoplaz|kitlesel",
    "effusion_thickening": "ef[uü]zyon.{0,3}kal[ıi]nla[şs]|kal[ıi]nla[şs]ma.{0,3}ef[uü]zyon",
    "atheroma_plaque": "aterom|ateroskler",
    "lytic_destructive_lesion": "litik|destr[uü]ktif",
    "mosaic_attenuation": "mozaik",
    "dilatation": "dilate|dilatasyon|ektazi",
    "nodular_lesion": "nod[uü]ler lezyon|nod[uü]ler dansite",
    "small_airway_disease": "k[uü][çc][uü]k hava yolu",
    "small_vessel_disease": "k[uü][çc][uü]k damar",
    "soft_tissue_density": "yumu[şs]ak doku dansite",
    "adiposity": "adipozite|ya[gğ]lanma",
    "infective_pathology": "enfekt[iı]f|enfeksiy[oö]n",
    # --- niteleyici ---
    "spiculated": "spik[uü]l", "irregular": "d[uü]zensiz|irreg[uü]ler",
    "lobulated": "lob[uü]le|lob[uü]lasyon", "smooth": "d[uü]zg[uü]n",
    "well_defined": "iyi s[ıi]n[ıi]rl|d[uü]zg[uü]n s[ıi]n[ıi]rl|keskin s[ıi]n[ıi]rl"
                    "|d[uü]zg[uü]n kont|keskin kont",
    "indistinct": "belirsiz s[ıi]n[ıi]r|s[ıi]n[ıi]rlar[ıi] se[çc]ilemeyen",
    "halo": "halo", "calcific": "kalsifiye|kalsifik",
    "ground_glass": "buzlu cam", "hypodense": "hipodens",
    "hyperdense": "hiperdens", "isodense": "izodens", "solid": "solid",
    "part_solid": "yar[ıi] solid|k[ıi]smen solid|par[çc]a solid",
    "fat_containing": "ya[gğ] i[çc]er|lipomat[oö]z|ya[gğ]l[ıi]",
    "cystic": "kistik", "necrotic": "nekro", "diffuse": "dif[uü]z|yayg[ıi]n",
    "subpleural": "subplevral|plevra alt", "apical": "apikal",
    "peripheral": "perifer", "basal": "bazal", "central": "santral|merkezi",
    "sequela": "sekel", "granulomatous": "gran[uü]lomat", "punctate": "punktat|noktasal",
    # --- cihaz ---
    # "port" tek basina "portal hilus" yakaliyordu (yanlis pozitif, D34) - daraltildi
    "catheter": "kateter|port kateter|port hazne", "stent": "stent",
    "pacemaker": "kalp pili|pacemaker|pil elektrod",
    "surgical_clip": "klips|cerrahi klip|s[uü]t[uü]r",
    "prosthesis": "protez|greft",
    "drainage_tube": "dren|g[oö][gğ][uü]s t[uü]p|toraks t[uü]p",
    # --- anatomi ---
    "parenchyma": "parankim", "lumen": "l[uü]men", "airway": "hava yolu",
    "station_prevascular": "prevask[uü]ler",
    "station_paratracheal": "paratrakeal|pretrakeal",
    "station_subcarinal": "subkarinal",
    "station_hilar_axillary": "hiler.{0,2}aksiller",
    "station_axillary": "aksiller|koltuk alt",
    "station_supraclavicular": "supraklavik[uü]ler",
    "station_aortopulmonary": "aortopulmoner|aortikopulmoner",
    "thymus": "timus|timik", "vena_cava": "vena ka?va",
    "pancreas": "pankreas",
    "intervertebral_disc": "intervertebral disk|disk mesafe",
    "neural_foramen": "n[oö]ral foramen|foramen",
    "rib": "kosta|kaburga", "sternum": "sternum|sternal",
    "diaphragm": "diyafra",
}


GELISTIRME_BOLUMLERI = ("train", "dev")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", default="gelistirme",
                    help="gelistirme (train+dev) | test")
    a = ap.parse_args()

    # KILIT: test bolumu yuzey gelistirmede KULLANILAMAZ.
    # Bu betik desen yazmaya hizmet eder; test'i acmak olcumu gecersiz kilar.
    if a.bolum != "gelistirme":
        sys.exit(
            "DURDU: bu betik yalnizca train+dev uzerinde calisir.\n"
            "  test bolumu (56 belge) dil ablasyonu icin dokunulmazdir ve BIR KEZ\n"
            "  acilir - desen gelistirirken degil, olcum yapilirken.\n"
            "  Kilit gerekcesi: reports/turkce_bolunme_dondurma.md")

    yol = PROC / "radtr_toraks.jsonl"
    if not yol.exists():
        sys.exit("once scripts/16_extract_radtr_thorax.py calistirilmali")
    belgeler = [json.loads(l) for l in yol.open(encoding="utf-8")]
    secili = [b for b in belgeler if b["kaynak_bolum"] in GELISTIRME_BOLUMLERI]
    metin = " ".join(b["metin"] for b in secili)
    print(f"olcum tabani: {len(secili)}/{len(belgeler)} belge "
          f"({'+'.join(GELISTIRME_BOLUMLERI)}) · {len(metin.split())} kelime")
    print(f"DISARIDA BIRAKILAN: "
          f"{len(belgeler)-len(secili)} test belgesi - dokunulmaz\n")
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
        f.write("# TURKCE YUZEY TASLAGI - surum: tr-0.3 (TASLAK)\n"
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
        yaml.safe_dump({"surum": "tr-0.3", "durum": "taslak",
                        "kaynak": "RadTr toraks train+dev (373 belge) - test HARIC",
                        "yuzeyler": kayit},
                       f, allow_unicode=True, sort_keys=False)

    print(f"yazildi: {cikti.name}")
    print(f"  {len(YUZEY)} kavram · RadTr'de var {var} (%{100*var/len(YUZEY):.0f}) · yok {len(yok)}")
    print("\nRADTR'DE GECMEYENLER (CT-RATE sikligiyla):")
    for k, c in sorted(yok, key=lambda x: -x[1]):
        print(f"  {k:<24}{c:>8,}")


if __name__ == "__main__":
    main()
