# -*- coding: utf-8 -*-
"""Astra tarafindan uretilen raporlarin orijinal Ispanyolca raporlarla
bulgu duzeyinde karsilastirilmasi (BIMCV-R 317 seri).

Iki tarafa da ayni bulgu ontolojisi ve olumsuzlama mantigi uygulanir.
Karsilastirma toraksla sinirlidir; Astra yalniz gogus BT'si gorur, orijinal
raporlarin cogu ise torako-abdomino-pelviktir.

Cikti:
  reports/astra_bulgu_matrisi.csv       seri x bulgu, her iki taraf
  reports/astra_uyum_tablosu.csv        bulgu duzeyi uyum
  reports/astra_lezyon_karsilastirma.csv  odak lezyon taraf/boyut karsilastirmasi
  reports/astra_karsilastirma_ciktisi.txt
"""
import csv
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
XLSX = KOK / "bimcv-analysis" / "BIMCV_Sybil_Pillar_Astra_317_Clean_Results.xlsx"
CIKTI = KOK / "reports"

# =========================================================================
# Bulgu ontolojisi: her iki dilde ayni kavram
# =========================================================================
BULGULAR = {
    "nodul": {
        "es": r"\bnodulo\b|\bnodulos\b|\bnodulillo\w*|\bmicronodulo\w*|\bnodulacion\w*",
        "en": r"\bnodule\b|\bnodules\b|\bnodular opacit\w*|\bmicronodule\w*",
    },
    "kitle": {
        # "mass effect" bir kitle lezyonu degil, bası etkisidir; disarida tutulur.
        "es": r"\bmasa\b|\bmasas\b|tumoracion\w*",
        "en": r"\bmass\b(?!\s+effect)|\bmasses\b|\bmass-like\b",
    },
    "konsolidasyon": {
        "es": r"consolidacion\w*|condensacion\w*|consolidativ\w*",
        "en": r"consolidation\w*|consolidativ\w*",
    },
    "buzlu_cam": {
        "es": r"vidrio deslustrado|vidrio esmerilado",
        "en": r"ground[- ]glass",
    },
    "plevral_efuzyon": {
        "es": r"derrame pleural",
        "en": r"pleural effusion|effusion in the pleural",
    },
    "amfizem": {
        "es": r"enfisema\w*",
        "en": r"emphysema\w*",
    },
    "adenopati": {
        "es": r"adenopat\w*|adenomegal\w*|ganglios? (mediastinic|hiliar|patologic)\w*",
        "en": r"lymphadenopathy|adenopathy|enlarged lymph node\w*|lymph node enlargement",
    },
    "atelektazi": {
        "es": r"atelectasi\w*",
        "en": r"atelectasis|atelectatic|collapse of the (lung|lobe)",
    },
    "bronsektazi": {
        "es": r"bronquiectasi\w*",
        "en": r"bronchiectasis|bronchiectatic",
    },
    "fibrozis": {
        "es": r"fibrosis|fibrotic\w*|tractos fibrosos|panalizacion",
        "en": r"fibrosis|fibrotic|honeycomb\w*|reticulation",
    },
    "kardiyomegali": {
        "es": r"cardiomegalia",
        "en": r"cardiomegaly|enlarged (cardiac|heart)|cardiac enlargement",
    },
    "plevral_kalinlasma": {
        "es": r"engrosamiento pleural|engrosamientos? pleural\w*",
        "en": r"pleural thickening",
    },
    "pnomotoraks": {
        "es": r"neumotorax",
        "en": r"pneumothorax",
    },
}

# ---- Ispanyolca olumsuzlama (66 numarali betikle ayni mantik) ----
ES_NEGASYON = re.compile(
    r"no se (observ|aprecia|identific|objetiv|visualiz|evidenci|defin|detect|reconoc)\w*"
    r"|no (hay|existe|existen|presenta|presentan|se ve|se ven|muestra|muestran"
    r"|aprecio|observo|identifico|visualizo|veo)"
    r"|no evidenciando|no identificando|no mostrando|no apreciando|no observando"
    r"|no visualizando|no objetivando"
    r"|\bsin\b|ausencia de|libre de|negativo para|excluye"
    r"|descarta\b|descartan\b|descartando\b|descartada\w*"
    r"|\bni\b|\bno\b"
)
ES_NEG_KIRICI = re.compile(
    r"\bpero\b|\bsalvo\b|\bexcepto\b|\bsi bien\b|\baunque\b|\bdestac\w+"
    r"|\bcambio\b|\bcambios\b|\bvariacion\w*|\bmodificacion\w*|\bdiferencias?\b"
    r"|\bnuev[ao]s?\b|\baumento\b|\bcrecimiento\b|\bdisminucion\b"
    r"|\bresolucion\b|\bregresion\b|\bprogresion\b"
)

# ---- Ingilizce olumsuzlama ----
EN_NEGASYON = re.compile(
    r"\bno\b|\bnot\b|\bwithout\b|\bnegative for\b|\babsence of\b|\babsent\b"
    r"|\bfree of\b|\bunremarkable\b|\bnormal\b|\bclear\b|\bdenies\b"
    r"|\black of\b|\bdevoid of\b|\bwithout evidence of\b|\bno evidence of\b"
    r"|\bnone\b|\bnor\b|\bexcluded\b|\bruled out\b|\bresolved\b",
    re.I,
)
# Yapilandirilmis raporda olumsuzlama terimden SONRA da gelebilir:
# "Pneumothorax: None." / "Pleural effusion: absent."
EN_ARDIL_NEGASYON = re.compile(
    # terimden hemen sonra: "Pneumothorax: None." / "Effusion: absent"
    r"^\W{0,4}(?:is|are|was|were)?\s*(?:none|absent|not present|not identified"
    r"|not seen|not observed|negative|unremarkable|normal|nil)\b"
    # ya da liste devam ettikten sonra:
    # "Pulmonary nodules or masses are not identified."
    r"|^(?:[,;]?\s*(?:or|and|nor)?\s*[\w()\-/]+){0,6}\s*"
    r"(?:is|are|was|were)?\s*(?:not\s+(?:identified|seen|observed|present|noted"
    r"|visualized|visualised|appreciated|demonstrated|detected|evident)"
    r"|none|absent|negative)\b",
    re.I)

EN_NEG_KIRICI = re.compile(
    r"\bhowever\b|\bbut\b|\bexcept\b|\balthough\b|\bthough\b|\baside from\b"
    r"|\bother than\b|\bapart from\b|\bwhereas\b|\bnotable for\b|\bpositive for\b"
    r"|\bchange\b|\bchanges\b|\bunchanged\b|\bincrease\w*|\bdecrease\w*|\bnew\b",
    re.I,
)

# ---- Astra bolum basliklari ----
TORASIK_BOLUM = re.compile(
    r"lung|pleura|mediastin|trachea|bronchi|heart|cardiac|thora|chest|conclusion"
    r"|summary|impression|findings", re.I)
TORAKS_DISI_BOLUM = re.compile(
    r"abdomen|abdominal|breast|thyroid|liver|hepatic|kidney|renal|adrenal|spleen"
    r"|splenic|gallbladder|pancrea|bowel|colon|stomach|gastric|pelvis|pelvic"
    r"|prostate|uterus|ovar|bladder|neck|cervical|brain|extremit", re.I)

# Astra bolum basliklari satir basinda markdown basligi olarak gelir ve iki
# nokta ISTEMEZ:  "#### Abdomen" / "**Lung:**" / "6. **Lung:**"
# Iki nokta zorunlu tutulunca "**Liver**:" gibi ALT etiketler baslik sanilip
# abdomen icerigi torasik metne siziyordu.
# Iki bicim birlikte kullaniliyor:
#   satir basligi   "#### Abdomen"
#   satir ici etiket "- **Liver**: Appears enlarged"
# Ikisi de yakalanir; etiketten sonraki metin o bolume ait sayilir.
# Baslik ya markdown basligi ya da KALIN etiket olmali. Desen gevsetilirse
# "No pneumothorax is observed." gibi cumleler de baslik sanilip metin
# "No" sonrasindan bolunuyor ve olumsuzlama kopuyor.
BOLUM_BASI = re.compile(
    r"^[ \t]*(?:"
    r"#{1,6}[ \t]*([A-Za-z][A-Za-z /&()\-]{1,30}?)[ \t]*:?[ \t]*$"
    r"|(?:[-*][ \t]*|\d+[.)][ \t]*)?\*\*([A-Za-z][A-Za-z /&()\-]{1,30}?)[ \t]*:?\*\*[ \t]*:?"
    r"|(?:[-*][ \t]*|\d+[.)][ \t]*)?\*\*([A-Za-z][A-Za-z /&()\-]{1,30}?)\*\*[ \t]*:"
    r")", re.M)


def bolum_adi(m):
    return next((g.strip() for g in m.groups() if g), "")

# ---- Ispanyolca toraks baglami ----
ES_TORAKS = re.compile(
    r"pulmon\w*|\blsd\b|\blsi\b|\blid\b|\blii\b|\blm\b|lobulo (superior|inferior|medio)"
    r"|mediastin\w*|pleur\w*|hiliar\w*|\bhilio\w*|bronq\w*|torac\w*|\btorax\b"
    r"|subpleural|cisura|parenquima pulmonar|vertice\w*|lingula|campo\w* pulmonar\w*"
    r"|espacio aereo|traquea|cardiomegalia|pericard\w*"
)


def cumleler_es(metin):
    metin = re.sub(r"\s+", " ", str(metin).strip())
    return [c.strip() for c in re.split(r"\s\.\s|\.$|;", metin) if c and c.strip()]


def cumleler_en(metin):
    """Ingilizce metni cumlelere boler.

    Uc sinir turu kullanilir:
      - noktalama + bosluk
      - satir sonu ("- Patient ID: [Insert ...]" gibi noktasiz baslik bloklari)
      - noktalama + bosluksuz buyuk harf

    Ucuncusu makine cevirisi sutunu icin zorunlu: cevirmen noktadan sonra
    bosluk birakmiyor ("disease.There are no ..."), bu yuzden butun rapor tek
    cumle haline geliyor ve bastaki bir olumsuzlama sonraki butun bulgulari
    kapsiyordu.
    """
    metin = re.sub(r"[^\S\r\n]+", " ", str(metin).strip())
    parcalar = re.split(
        r"(?<=[.!?])\s+|[;\r\n]+|(?<=[a-z0-9])\.(?=[A-Z])|(?=- \*\*)", metin)
    return [c.strip() for c in parcalar if c and c.strip()]


def olumsuz_mu(cumle, konum, negasyon, kirici, kapsam=110, terim_sonu=None, ardil=None):
    """Terim olumsuzlama kapsaminda mi?

    Once terimden SONRA gelen olumsuzlamaya bakilir ("Pneumothorax: None."),
    sonra geriye dogru taranir.
    """
    if ardil is not None and terim_sonu is not None:
        if ardil.match(cumle[terim_sonu:terim_sonu + 40]):
            return True
    onceki = cumle[:konum]
    son_neg = None
    for m in negasyon.finditer(onceki):
        son_neg = m
    if son_neg is None:
        return False
    aradaki = onceki[son_neg.end():]
    if kirici.search(aradaki):
        return False
    return len(aradaki) <= kapsam


def astra_torasik_metin(rapor):
    """Astra raporundan yalniz torasik bolumleri dondurur."""
    metin = str(rapor)
    basliklar = [(m.start(), m.end(), bolum_adi(m)) for m in BOLUM_BASI.finditer(metin)]
    if not basliklar:
        return metin
    parcalar = []
    for i, (bas, son, ad) in enumerate(basliklar):
        bitis = basliklar[i + 1][0] if i + 1 < len(basliklar) else len(metin)
        govde = metin[son:bitis]
        if TORAKS_DISI_BOLUM.search(ad):
            continue
        if TORASIK_BOLUM.search(ad) or not TORAKS_DISI_BOLUM.search(ad):
            parcalar.append(govde)
    return " ".join(parcalar) if parcalar else metin


# Astra cumlesi toraks disi bir organdan soz edip hicbir torasik yapiya
# deginmiyorsa sayilmaz. Bolum filtresi tek basina yetmiyor: ozet ve sonuc
# bolumlerinde meme, tiroid ve batin cumleleri de yer aliyor.
EN_TORAKS = re.compile(
    r"\blung\w*|\bpulmonary\b|\bpleura\w*|\bmediastin\w*|\bhilar\b|\bhilum\b"
    # "lobe" tek basina kullanilamaz: "left lobe of the liver" de eslesiyordu.
    r"|\bbronch\w*|\btrachea\w*|\bthora\w*|\bchest\b"
    r"|\b(?:upper|lower|middle)\s+lobe\w*|\blingula\w*"
    r"|\brul\b|\brml\b|\brll\b|\blul\b|\blll\b|\bcardiac\b|\bheart\b"
    r"|\bpericard\w*|\bairspace\b|\bair space\b|\bfissure\b|\bapex\b|\bapices\b", re.I)
EN_TORAKS_DISI = re.compile(
    r"\bbreast\w*|\bthyroid\w*|\bliver\b|\bhepatic\b|\bspleen\b|\bsplen\w*"
    r"|\bkidney\w*|\brenal\b|\badrenal\w*|\bgallbladder\b|\bpancrea\w*"
    r"|\babdom\w*|\bpelvi\w*|\bbowel\b|\bcolon\b|\bstomach\b|\bgastric\b"
    r"|\bprostate\b|\buterus\b|\bovar\w*|\bbladder\b", re.I)


def astra_cumlesi_torasik(cumle):
    if EN_TORAKS_DISI.search(cumle) and not EN_TORAKS.search(cumle):
        return False
    return True


def bulgu_var_mi(metin, desen, negasyon, kirici, cumle_bol,
                 toraks_filtre=None, ardil=None):
    """Olumsuzlanmamis en az bir gecis var mi?"""
    rx = re.compile(desen, re.I)
    for c in cumle_bol(metin):
        if toraks_filtre is not None:
            uygun = toraks_filtre(c) if callable(toraks_filtre) else toraks_filtre.search(c)
            if not uygun:
                continue
        for m in rx.finditer(c):
            if not olumsuz_mu(c, m.start(), negasyon, kirici,
                              terim_sonu=m.end(), ardil=ardil):
                return True
    return False


# =========================================================================
# Odak lezyon: taraf ve boyut
# =========================================================================
ES_TARAF = [
    ("sag", r"\blsd\b|\blid\b|\blm\b|lobulo (superior|inferior|medio) derecho"
            r"|pulmon derecho|hemitorax derecho|derech[oa]"),
    ("sol", r"\blsi\b|\blii\b|lobulo (superior|inferior) izquierdo"
            r"|pulmon izquierdo|hemitorax izquierdo|izquierd[oa]"),
    ("bilateral", r"bilateral\w*|ambos (pulmones|lobulos|campos)|ambas"),
]
EN_TARAF = [
    ("sag", r"\bright\b|\brul\b|\brll\b|\brml\b"),
    ("sol", r"\bleft\b|\blul\b|\blll\b"),
    ("bilateral", r"\bbilateral\w*|\bboth (lungs|lobes)\b"),
]
ES_LOB = [
    ("ust", r"\blsd\b|\blsi\b|lobulo superior|vertice\w*|apical"),
    ("orta", r"\blm\b|lobulo medio|lingula"),
    ("alt", r"\blid\b|\blii\b|lobulo inferior|basal"),
]
EN_LOB = [
    ("ust", r"upper lobe|\brul\b|\blul\b|apical|apex"),
    ("orta", r"middle lobe|\brml\b|lingula"),
    ("alt", r"lower lobe|\brll\b|\blll\b|basal|base"),
]
OLCU = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mm|cm)\b", re.I)


def en_bilgili_cumle(cumleler):
    """Lezyonu en iyi tarif eden tek cumle: olcu verilen, yoksa en uzun olan."""
    if not cumleler:
        return ""
    olculu = [c for c in cumleler if OLCU.search(c)]
    havuz = olculu or cumleler
    return max(havuz, key=len)


def etiket_bul(metin, tanimlar):
    bulunan = set()
    for ad, desen in tanimlar:
        if re.search(desen, metin, re.I):
            bulunan.add(ad)
    if "bilateral" in bulunan:
        return "bilateral"
    if bulunan == {"sag"}:
        return "sag"
    if bulunan == {"sol"}:
        return "sol"
    if len(bulunan) > 1:
        return "coklu"
    return "belirtilmemis"


def en_buyuk_olcu_mm(metin):
    en = None
    for m in OLCU.finditer(metin):
        deger = float(m.group(1).replace(",", "."))
        mm = deger * 10 if m.group(2).lower() == "cm" else deger
        if en is None or mm > en:
            en = mm
    return en


def lezyon_cumleleri(metin, desen, negasyon, kirici, cumle_bol,
                     toraks_filtre=None, ardil=None):
    rx = re.compile(desen, re.I)
    secilen = []
    for c in cumle_bol(metin):
        if toraks_filtre is not None:
            uygun = toraks_filtre(c) if callable(toraks_filtre) else toraks_filtre.search(c)
            if not uygun:
                continue
        for m in rx.finditer(c):
            if not olumsuz_mu(c, m.start(), negasyon, kirici,
                              terim_sonu=m.end(), ardil=ardil):
                secilen.append(c)
                break
    return secilen


# =========================================================================
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    satirlar = []

    def yaz(*p):
        s = " ".join(str(x) for x in p)
        print(s)
        satirlar.append(s)

    df = pd.read_excel(XLSX, "Skorlar ve Raporlar")
    df.columns = ["no", "hasta", "rapor", "seri", "hekim_ozet",
                  "s1", "s2", "s3", "s4", "s5", "s6",
                  "p1", "p2", "p3", "p4", "p5", "p6",
                  "es", "en", "astra", "ts", "tp", "ta"]

    kayitlar = []
    for _, r in df.iterrows():
        es_metin = str(r["es"])
        astra_tor = astra_torasik_metin(r["astra"])
        kayit = {"no": int(r["no"]), "hasta": r["hasta"], "seri": r["seri"]}
        for ad, d in BULGULAR.items():
            kayit["es_" + ad] = bulgu_var_mi(es_metin, d["es"], ES_NEGASYON,
                                             ES_NEG_KIRICI, cumleler_es, ES_TORAKS)
            kayit["astra_" + ad] = bulgu_var_mi(astra_tor, d["en"], EN_NEGASYON,
                                                EN_NEG_KIRICI, cumleler_en,
                                                toraks_filtre=astra_cumlesi_torasik,
                                                ardil=EN_ARDIL_NEGASYON)
        kayit["astra_tor_metin"] = astra_tor
        kayit["es_metin"] = es_metin
        kayitlar.append(kayit)

    o = pd.DataFrame(kayitlar)

    yaz("BIMCV-R 317 seri: Astra raporu ile Ispanyolca rapor bulgu uyumu")
    yaz("")
    yaz("=== Bulgu sikligi ve uyum ===")
    yaz("%-20s %6s %6s %6s %6s %6s %6s %7s %7s"
        % ("bulgu", "ES+", "AST+", "ikisi", "yalnES", "yalnAS", "ikisi-", "PPA%", "NPA%"))
    uyum = []
    for ad in BULGULAR:
        e = o["es_" + ad].values
        a = o["astra_" + ad].values
        ikisi = int((e & a).sum())
        yaln_e = int((e & ~a).sum())
        yaln_a = int((~e & a).sum())
        ikisi_yok = int((~e & ~a).sum())
        ppa = 100 * ikisi / max(1, e.sum())          # ES pozitiflerinde Astra da pozitif
        npa = 100 * ikisi_yok / max(1, (~e).sum())   # ES negatiflerinde Astra da negatif
        yaz("%-20s %6d %6d %6d %6d %6d %6d %7.1f %7.1f"
            % (ad, e.sum(), a.sum(), ikisi, yaln_e, yaln_a, ikisi_yok, ppa, npa))
        uyum.append(dict(bulgu=ad, es_poz=int(e.sum()), astra_poz=int(a.sum()),
                         ikisi_poz=ikisi, yalniz_es=yaln_e, yalniz_astra=yaln_a,
                         ikisi_neg=ikisi_yok, ppa=round(ppa, 1), npa=round(npa, 1)))
    pd.DataFrame(uyum).to_csv(CIKTI / "astra_uyum_tablosu.csv", index=False,
                              encoding="utf-8-sig")

    # ---- odak lezyon karsilastirmasi ----
    yaz("")
    yaz("=== Odak lezyon (nodul veya kitle) taraf / lob / boyut ===")
    lezyon_satir = []
    odak_es = r"|".join([BULGULAR["nodul"]["es"], BULGULAR["kitle"]["es"]])
    odak_en = r"|".join([BULGULAR["nodul"]["en"], BULGULAR["kitle"]["en"]])
    for _, r in o.iterrows():
        es_c = lezyon_cumleleri(r.es_metin, odak_es, ES_NEGASYON, ES_NEG_KIRICI,
                                cumleler_es, ES_TORAKS)
        as_c = lezyon_cumleleri(r.astra_tor_metin, odak_en, EN_NEGASYON,
                                EN_NEG_KIRICI, cumleler_en,
                                toraks_filtre=astra_cumlesi_torasik,
                                ardil=EN_ARDIL_NEGASYON)
        if not es_c or not as_c:
            continue
        # Taraf ve lob, lezyonun gectigi TEK cumleden okunur. Birden fazla
        # cumle birlestirilince etiket kirleniyor: baska bir bulgunun tarafi
        # lezyonun tarafi gibi gorunuyordu.
        es_ana = en_bilgili_cumle(es_c)
        as_ana = en_bilgili_cumle(as_c)
        lezyon_satir.append(dict(
            no=r.no, hasta=r.hasta,
            es_taraf=etiket_bul(es_ana, ES_TARAF), astra_taraf=etiket_bul(as_ana, EN_TARAF),
            es_lob=etiket_bul(es_ana, ES_LOB), astra_lob=etiket_bul(as_ana, EN_LOB),
            es_mm=en_buyuk_olcu_mm(es_ana), astra_mm=en_buyuk_olcu_mm(as_ana),
            es_cumle=es_ana[:400], astra_cumle=as_ana[:400]))
    lz = pd.DataFrame(lezyon_satir)
    lz.to_csv(CIKTI / "astra_lezyon_karsilastirma.csv", index=False,
              encoding="utf-8-sig")
    yaz("iki tarafta da odak lezyon tarif edilen seri: %d" % len(lz))
    if len(lz):
        kars = lz[(lz.es_taraf != "belirtilmemis") & (lz.astra_taraf != "belirtilmemis")]
        yaz("taraf ikisinde de belirtilen: %d" % len(kars))
        if len(kars):
            ayni = int((kars.es_taraf == kars.astra_taraf).sum())
            yaz("  taraf uyusan: %d  uyusmayan: %d" % (ayni, len(kars) - ayni))
            yaz(pd.crosstab(kars.es_taraf, kars.astra_taraf).to_string())
        kl = lz[(lz.es_lob != "belirtilmemis") & (lz.astra_lob != "belirtilmemis")]
        if len(kl):
            yaz("lob ikisinde de belirtilen: %d  uyusan: %d"
                % (len(kl), int((kl.es_lob == kl.astra_lob).sum())))
        ol = lz.dropna(subset=["es_mm", "astra_mm"])
        if len(ol):
            fark = (ol.astra_mm - ol.es_mm).abs()
            yaz("olcu ikisinde de verilen: %d  medyan mutlak fark: %.1f mm"
                % (len(ol), float(fark.median())))

    # ---- Astra kapsam ve sablon sizintisi ----
    yaz("")
    yaz("=== Astra cikti kalitesi ===")
    ham = df["astra"].astype(str)
    for ad, desen in [("gogus BT'sinde abdomen bolumu", r"abdomen"),
                      ("gogus BT'sinde meme bolumu", r"breast"),
                      ("gogus BT'sinde tiroid bolumu", r"thyroid"),
                      ("sablon yer tutucusu [Insert", r"\[Insert"),
                      ("imza yer tutucusu [Your Name]", r"\[Your Name\]"),
                      ("'Prepared by' satiri", r"Prepared by"),
                      ("'informational purposes' feragati", r"informational purposes")]:
        n = int(ham.str.contains(desen, case=False, regex=True).sum())
        yaz("  %-34s %3d/317  (%%%.1f)" % (ad, n, 100 * n / len(ham)))

    o.drop(columns=["astra_tor_metin", "es_metin"]).to_csv(
        CIKTI / "astra_bulgu_matrisi.csv", index=False, encoding="utf-8-sig")
    (CIKTI / "astra_karsilastirma_ciktisi.txt").write_text(
        "\n".join(satirlar), encoding="utf-8")
    yaz("")
    yaz("Ciktilar reports/ altina yazildi.")


if __name__ == "__main__":
    main()
