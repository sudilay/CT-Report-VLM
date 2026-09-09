# -*- coding: utf-8 -*-
"""BIMCV-R 317 serisi: Sybil / Pillar risk skorlarinin Ispanyolca rapordan
turetilen torasik bulgularla betimleyici iliskisi.

Bu betik raporda gecen BUTUN tablolari, AUC degerlerini, hasta-kumeli bootstrap
guven araliklarini ve etiket kesif analizini uretir.

Onemli: dosya duz metin olarak yazilmalidir. Kabuk heredoc'u uzerinden yapilan
duzenlemelerde \\b kelime siniri kacislari U+0008 backspace karakterine
donusmustu; desenler bu yuzden sessizce eslesmez hale gelmisti.

Cikti:
  reports/bimcv_317_siniflama.json     vaka duzeyi iki eksenli siniflama
  reports/bimcv_317_adjudikasyon.csv   elle inceleme / uzlastirma tablosu
  reports/bimcv_317_etiket_kesif.csv   95 hekim etiketi kesif analizi (FDR)
  reports/bimcv_317_tablolar.txt       rapordaki tablolarin ham ciktisi
"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
XLSX = KOK / "bimcv-analysis" / "BIMCV_Sybil_Pillar_Astra_317_Clean_Results.xlsx"
CIKTI = KOK / "reports"
ESIK = 0.20          # analiz oncesinde sabitlenen arastirma esigi
BOOTSTRAP = 4000
TOHUM = 20260909

# =========================================================================
# 1. Sozlukler
# =========================================================================

# Malignitenin acikca ifade edildigi dil
MALIGNITE = re.compile(
    r"neoplas\w*|carcinom\w*|adenocarcinom\w*|\bcancer\w*|metastas\w*|metastat\w*"
    r"|carcinomatosis|malign\w*|linfom\w*|mielom\w*|sarcom\w*|timom\w*"
    r"|mesotelio\w*|tumoracion\w*|tumoral\w*|\btumor\w*|recidiva\w*"
    r"|lesion(es)? secundaria(s)?"
)
# Malignite dili sayilmayacak kaliplar
MALIGNITE_HARIC = re.compile(r"pseudotumor\w*|seudotumor\w*")
BENIGN = re.compile(
    r"benign\w*|no maligno|sin criterios de malignidad|de aspecto benigno"
    r"|granulom\w*|calcificad\w*|quist\w*|lipom\w*|hamartom\w*"
    r"|calcio en su interior|con calcio|contenido calcico"
)
# Cekinceli malignite dili. "puede corresponder a una neoplasia" kesin
# malignite beyani degildir; bu ifadeler duzeyi high yerine intermediate
# yapar.
CEKINCE = re.compile(
    r"pued[eo]n? corresponder|podria\w* corresponder|puede tratarse|sugestiv\w*"
    r"|sospechos\w*|compatible con|probable\w*|posible\w*|dudos\w*"
    r"|a valorar|no se puede descartar|en relacion con|orienta\w* a"
    r"|en el espectro de|no descartable"
)

# Nodul / kitle (malignite dili olmadan)
NODUL = re.compile(
    r"\bnodulo\b|\bnodulos\b|\bnodulillo\w*|\bmicronodulo\w*|\bnodulacion\w*"
    r"|\bmasa\b|\bmasas\b"
)
# "imagen pseudonodular": gercek belirsiz lezyon; suphe nitelemesiyle
# yukseltilmez cunku radyolog "pseudo" diyerek suphesini zaten dusurmustur.
PSEUDONODUL = re.compile(r"pseudonodul\w*|seudonodul\w*")

# Malignite suphesi yukselten nitelemeler
SUPHE = re.compile(
    r"sospechos\w*|espiculad\w*|de aspecto agresivo|caracter agresivo"
    r"|ocupante de espacio|bordes irregulares|contornos irregulares"
    r"|sugestiv\w+ de (malignidad|neoplasia|metastasis|proceso neoplasico)"
    r"|compatible con (malignidad|neoplasia|metastasis)"
)

# Olumsuzlama ipuclari (terimden ONCE gelir)
NEGASYON = re.compile(
    r"no se (observ|aprecia|identific|objetiv|visualiz|evidenci|defin|detect|reconoc)\w*"
    r"|no (hay|existe|existen|presenta|presentan|se ve|se ven|muestra|muestran"
    r"|aprecio|observo|identifico|visualizo|veo)"
    r"|no evidenciando|no identificando|no mostrando|no apreciando|no observando"
    r"|no visualizando|no objetivando"
    r"|\bsin\b|ausencia de|libre de|negativo para|excluye"
    r"|descarta\b|descartan\b|descartando\b|descartada\w*"
    r"|\bni\b|\bno\b"
)
# Olumsuzlamayi kiran ifadeler.
# "no hay cambios en los nodulos" -> nodul VAR, sadece degismemis: olumsuzlama
# varligi degil degisimi hedefliyorsa bulgu ayakta kalir.
NEG_KIRICI = re.compile(
    r"\bpero\b|\bsalvo\b|\bexcepto\b|\bsi bien\b|\baunque\b|\bdestac\w+"
    r"|\bcambio\b|\bcambios\b|\bvariacion\w*|\bmodificacion\w*|\bdiferencias?\b"
    r"|\bnuev[ao]s?\b|\baumento\b|\bcrecimiento\b|\bdisminucion\b"
    r"|\bresolucion\b|\bregresion\b|\bprogresion\b"
)

# ---- Anatomik baglam ----
AKCIGER = re.compile(
    r"pulmon\w*|\blsd\b|\blsi\b|\blid\b|\blii\b|\blm\b"
    r"|lobulo (superior|inferior|medio)|parenquima pulmonar|subpleural|cisura|lingula"
    r"|campo\w* pulmonar\w*|vertice\w*|espacio aereo|segmento (apical|basal|lateral)"
)
MEDIASTEN_PLEVRA = re.compile(
    r"mediastin\w*|pleur\w*|hiliar\w*|\bhilio\w*|\bhilios\b|subcarinal|carina"
    r"|prevascular|paratraqueal|infracarinal|timo\w*|esofag\w*|pericard\w*"
)
TORAKS_KEMIK = re.compile(
    r"\bd[1-9]\b|\bd1[0-2]\b|\bt[1-9]\b|\bt1[0-2]\b|vertebra\w* dorsal\w*"
    r"|\bdorsal\w*|esternal|esternon|manubrio|arco\w* costal\w*|costilla\w*"
    r"|parrilla costal|clavicula\w*|escapula\w*|omoplato|esqueleto toracico"
    r"|pared toracica|costiforme"
)
TORAKS_DISI = re.compile(
    r"hepatic\w*|\bhigado\b|renal\w*|\brinon\w*|\brinones\b|suprarrenal\w*"
    r"|prostat\w*|vejiga|vesical|urotelial\w*|colon|\brecto\b|rectal|peritone\w*|\bovario\w*|\banejo\w*"
    r"|uterin\w*|\butero\b|endometri\w*|pancrea\w*|\bbazo\b|abdomen|abdominal"
    r"|pelvi\w*|\bmama\b|mamari\w*|tiroid\w*|craneal|cerebral|encefal\w*"
    r"|gastric\w*|intestin\w*|\bileo\b|sigma|vesicula|biliar|paladar|laring\w*"
    r"|amigdal\w*|cuello|cervical|inguinal|obturador|iliac\w*|\bl[1-5]\b|\bs1\b"
    r"|femoral|humeral|submandibular|submaxil\w*"
)

# ---- Zamansallik ----
ENDIKASYON = re.compile(
    r"datos clinicos|\bmotivo\b|\bdatos\b|juicio clinico|historia clinica"
    r"|anamnesis|informacion clinica|\binformacion\b|indicacion|se solicita"
)
OYKU = re.compile(
    r"antecedent\w*|\bconocid[ao]s?\b|intervenid\w*|lobectomia|neumonectomia"
    r"|\breseccion\b|postquirurgic\w*|post quirurgic\w*|tratad\w* (de|por)"
    r"|\bqt\b|\brt\b|quimioterapia|radioterapia|mastectomia|post radica"
    r"|en seguimiento|previamente"
)
TAKIP = re.compile(
    r"se compara|respecto a (estudio|control|tc|previo)|estudio previo|control evolutivo"
    r"|\bpersiste\w*|sin cambios|previo de|comparativamente"
)

# Metastaz / primer ayrimi
METASTAZ = re.compile(r"metastas\w*|metastat\w*|lesion(es)? secundaria(s)?|carcinomatosis")


def derle_cumleler(metin):
    metin = re.sub(r"\s+", " ", str(metin).strip())
    return [c.strip() for c in re.split(r"\s\.\s|\.$|;", metin) if c and c.strip()]


def olumsuz_mu(cumle, konum):
    """Terimden geriye tarayarak olumsuzlama kapsaminda mi bak."""
    onceki = cumle[:konum]
    son_neg = None
    for m in NEGASYON.finditer(onceki):
        son_neg = m
    if son_neg is None:
        return False
    aradaki = onceki[son_neg.end():]
    if NEG_KIRICI.search(aradaki):
        return False
    return len(aradaki) <= 120


def yakin_suphe(cumle, eslesme):
    bas = max(0, eslesme.start() - 40)
    son = min(len(cumle), eslesme.end() + 80)
    for m in SUPHE.finditer(cumle, bas, son):
        if not olumsuz_mu(cumle, m.start()):
            return True
    return False


ANATOMI_DESENLERI = [
    ("akciger", AKCIGER),
    ("mediasten_plevra", MEDIASTEN_PLEVRA),
    ("toraks_kemik", TORAKS_KEMIK),
    ("toraks_disi", TORAKS_DISI),
]


def anatomi(cumle, konum=None):
    """Bolgeyi terime EN YAKIN anatomik sozcukten atar.

    Sabit oncelik sirasi kullanmak yaniltiyordu: "hallazgos pulmonares muy
    probable covid, tumoracion urotelial izquierda de 6 cm" cumlesinde mesane
    tumoru, sirf cumlede "pulmonares" gectigi icin akcigere yaziliyordu.
    """
    isaretler = []
    for ad, desen in ANATOMI_DESENLERI:
        for m in desen.finditer(cumle):
            isaretler.append((ad, m.start(), m.end()))
    if not isaretler:
        return "belirsiz"
    if konum is None:
        return isaretler[0][0]
    en_yakin, en_mesafe = None, None
    for ad, bas, son in isaretler:
        mesafe = 0 if bas <= konum <= son else min(abs(konum - bas), abs(konum - son))
        if en_mesafe is None or mesafe < en_mesafe:
            en_yakin, en_mesafe = ad, mesafe
    return en_yakin


def zamansallik(cumle):
    if ENDIKASYON.search(cumle):
        return "klinik_endikasyon"
    if OYKU.search(cumle):
        return "oyku"
    if TAKIP.search(cumle):
        return "takip"
    return "guncel_bulgu"


def kanit_topla(metin):
    """Her cumleden malignite / nodul kanitlarini cikarir."""
    kanitlar = []
    for c in derle_cumleler(metin):
        temiz = MALIGNITE_HARIC.sub(" ", c)
        zaman = zamansallik(c)

        for m in MALIGNITE.finditer(temiz):
            anat = anatomi(c, m.start())
            if olumsuz_mu(temiz, m.start()):
                kanitlar.append(dict(tur="malignite_olumsuz", terim=m.group(),
                                     cumle=c, anatomi=anat, zaman=zaman))
                continue
            # Benign niteleme penceresi genis tutulur: "nodulo calcificado ...
            # de caracteristicas benignas" gibi ifadelerde niteleme uzakta kalir.
            if BENIGN.search(temiz[max(0, m.start() - 120):m.end() + 120]):
                continue
            # metastaz nitelemesi terime yakin olmali
            yakin = temiz[max(0, m.start() - 60):m.end() + 60]
            kanitlar.append(dict(
                tur="malignite", terim=m.group(), cumle=c,
                anatomi=anat, zaman=zaman,
                metastaz=bool(METASTAZ.search(yakin)),
                cekinceli=bool(CEKINCE.search(temiz[max(0, m.start() - 70):m.end() + 30]))))

        for m in NODUL.finditer(temiz):
            anat = anatomi(c, m.start())
            if olumsuz_mu(temiz, m.start()):
                kanitlar.append(dict(tur="nodul_olumsuz", terim=m.group(),
                                     cumle=c, anatomi=anat, zaman=zaman))
                continue
            benign = bool(BENIGN.search(temiz[max(0, m.start() - 120):m.end() + 120]))
            kanitlar.append(dict(tur="nodul", terim=m.group(), cumle=c,
                                 anatomi=anat, zaman=zaman,
                                 supheli=yakin_suphe(temiz, m), benign=benign))

        for m in PSEUDONODUL.finditer(c):
            if olumsuz_mu(c, m.start()):
                continue
            kanitlar.append(dict(tur="nodul", terim=m.group(), cumle=c,
                                 anatomi=anatomi(c, m.start()), zaman=zaman,
                                 supheli=False, benign=False))
    return kanitlar


# =========================================================================
# 2. Iki eksenli siniflama
# =========================================================================

TORASIK = ("akciger", "mediasten_plevra", "toraks_kemik")


def eksen_a(kanitlar, ham):
    """Rapordan turetilmis malignite duzeyi."""
    if not MALIGNITE.search(ham) and not NODUL.search(ham) and not PSEUDONODUL.search(ham):
        return "not_mentioned"

    mal = [k for k in kanitlar if k["tur"] == "malignite" and k["anatomi"] in TORASIK]
    nod = [k for k in kanitlar if k["tur"] == "nodul" and k["anatomi"] in TORASIK]

    guncel_mal = [k for k in mal if k["zaman"] in ("guncel_bulgu", "takip")]
    kesin = [k for k in guncel_mal if not k.get("cekinceli")]
    if kesin:
        return "high"
    if guncel_mal:                            # hepsi cekinceli ifade
        return "intermediate"
    if mal:                                   # yalnizca oyku / endikasyon cumlesinde
        return "known_malignancy"
    if any(k["supheli"] for k in nod):
        return "intermediate"
    if any(not k["benign"] for k in nod):
        return "indeterminate"
    if nod:                                   # hepsi benign nitelenmis
        return "low"
    if any(k["tur"] in ("malignite_olumsuz", "nodul_olumsuz") for k in kanitlar):
        return "none"
    return "not_mentioned"


# Kemik lezyonu sozcukleri: bilesik anatomi ("esqueleto toracoabdominopelvico")
# en yakin anatomi kuralini yaniltabiliyor. Cumlede dorsal vertebra veya kosta
# kodu geciyorsa toraks iskeleti etiketi ayrica eklenir.
KEMIK_LEZYON = re.compile(
    r"lesion\w* (focal\w* )?(escleros\w*|litic\w*|osteolitic\w*|osteoblastic\w*|osea\w*)"
    r"|lesiones oseas|cuerpos vertebrales|afectacion osea|metastasis osea\w*")


def eksen_b(kanitlar):
    """Bulgusal / model-hedefi baglami. Birden fazla etiket alabilir."""
    etiketler = set()
    for k in kanitlar:
        if k["tur"] == "malignite":
            guncel = k["zaman"] in ("guncel_bulgu", "takip")
            if k["anatomi"] == "akciger":
                if k.get("metastaz"):
                    etiketler.add("pulmoner_metastaz")
                elif guncel:
                    etiketler.add("guncel_primer_akciger")
                else:
                    etiketler.add("yalniz_oyku_endikasyon")
            elif k["anatomi"] == "mediasten_plevra":
                etiketler.add("mediastinal_plevral_malignite")
            elif k["anatomi"] == "toraks_kemik":
                etiketler.add("toraks_kemik_metastaz")
            elif k["anatomi"] == "toraks_disi":
                etiketler.add("toraks_disi_malignite")
            else:
                if not guncel:
                    etiketler.add("yalniz_oyku_endikasyon")
        elif k["tur"] == "nodul" and k["anatomi"] == "akciger" and not k["benign"]:
            if k["supheli"]:
                etiketler.add("supheli_primer_pulmoner")
    # bilesik anatomi duzeltmesi
    for k in kanitlar:
        if k["tur"] != "malignite":
            continue
        if KEMIK_LEZYON.search(k["cumle"]) and TORAKS_KEMIK.search(k["cumle"]):
            etiketler.add("toraks_kemik_metastaz")
    if not etiketler:
        etiketler.add("kanit_yok")
    return sorted(etiketler)


# =========================================================================
# 3. Istatistik: hasta-kumeli bootstrap
# =========================================================================

def auc_hesapla(y, skor):
    y = np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = pd.Series(np.asarray(skor, float)).rank().values
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def kumeli_bootstrap_auc(y, skor, hasta, B=BOOTSTRAP, tohum=TOHUM):
    """Hastalari (serileri degil) yeniden orneklyerek %95 GA."""
    rng = np.random.default_rng(tohum)
    y = np.asarray(y, bool)
    skor = np.asarray(skor, float)
    hasta = np.asarray(hasta)
    tekil = np.unique(hasta)
    indeks = {h: np.where(hasta == h)[0] for h in tekil}
    degerler = []
    for _ in range(B):
        secim = rng.choice(tekil, len(tekil), replace=True)
        idx = np.concatenate([indeks[h] for h in secim])
        if y[idx].sum() < 3 or (~y[idx]).sum() < 3:
            continue
        a = auc_hesapla(y[idx], skor[idx])
        if not np.isnan(a):
            degerler.append(a)
    if not degerler:
        return float("nan"), float("nan")
    return tuple(np.percentile(degerler, [2.5, 97.5]))


def bh_fdr(p):
    """Benjamini-Hochberg duzeltilmis q degerleri."""
    p = np.asarray(p, float)
    n = len(p)
    sira = np.argsort(p)
    q = np.empty(n, float)
    onceki = 1.0
    for rank, i in enumerate(sira[::-1]):
        k = n - rank
        onceki = min(onceki, p[i] * n / k)
        q[i] = onceki
    return q


def auc_p_degeri(y, skor):
    """AUC = 0.5 icin normal yaklasimli Mann-Whitney p degeri."""
    from math import erfc, sqrt
    y = np.asarray(y, bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 < 3 or n0 < 3:
        return float("nan")
    a = auc_hesapla(y, skor)
    u = a * n1 * n0
    ort = n1 * n0 / 2
    sd = sqrt(n1 * n0 * (n1 + n0 + 1) / 12)
    return erfc(abs(u - ort) / sd / sqrt(2))


# =========================================================================
# 4. Ana akis
# =========================================================================

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cikti_metni = []

    def yaz(*parcalar):
        satir = " ".join(str(p) for p in parcalar)
        print(satir)
        cikti_metni.append(satir)

    df = pd.read_excel(XLSX, "Skorlar ve Raporlar")
    df.columns = ["no", "hasta", "rapor", "seri", "hekim_ozet",
                  "s1", "s2", "s3", "s4", "s5", "s6",
                  "p1", "p2", "p3", "p4", "p5", "p6",
                  "es", "en", "astra", "ts", "tp", "ta"]

    kayitlar = []
    for _, r in df.iterrows():
        kanitlar = kanit_topla(r["es"])
        a = eksen_a(kanitlar, str(r["es"]))
        b = eksen_b(kanitlar)
        torasik_kanit = [k for k in kanitlar
                         if k["tur"] in ("malignite", "nodul") and k["anatomi"] in TORASIK]
        kayitlar.append({
            "no": int(r["no"]), "hasta": r["hasta"], "rapor": r["rapor"], "seri": r["seri"],
            "sybil1": float(r["s1"]), "sybil6": float(r["s6"]),
            "pillar1": float(r["p1"]), "pillar6": float(r["p6"]),
            "malignite_duzeyi": a,
            "baglam": b,
            "zamansallik": sorted({k["zaman"] for k in torasik_kanit}) or ["yok"],
            "kanit_cumleleri": [k["cumle"] for k in torasik_kanit][:4],
            "hekim_ozet": r["hekim_ozet"],
        })

    o = pd.DataFrame(kayitlar)
    o["sybil_ust"] = o.sybil1 >= ESIK
    o["pillar_ust"] = o.pillar1 >= ESIK

    # ---- model hedefine gore katmanlar ----
    o["dar_hedef"] = o.baglam.apply(
        lambda b: ("guncel_primer_akciger" in b) or ("supheli_primer_pulmoner" in b))
    o["genis_torasik"] = o.baglam.apply(
        lambda b: any(x in b for x in ("guncel_primer_akciger", "supheli_primer_pulmoner",
                                       "pulmoner_metastaz", "mediastinal_plevral_malignite",
                                       "toraks_kemik_metastaz")))

    yaz("Seri sayisi: %d   Benzersiz hasta: %d   Esik: %.2f"
        % (len(o), o.hasta.nunique(), ESIK))
    yaz("")
    yaz("=== Eksen A: rapordan turetilmis malignite duzeyi ===")
    yaz(o.malignite_duzeyi.value_counts().to_string())
    yaz("")
    yaz("=== Eksen B: bulgusal baglam (vaka birden fazla etiket alabilir) ===")
    sayim = {}
    for b in o.baglam:
        for x in b:
            sayim[x] = sayim.get(x, 0) + 1
    for k, v in sorted(sayim.items(), key=lambda t: -t[1]):
        yaz("  %-32s %d" % (k, v))
    yaz("")
    yaz("=== Zamansallik (torasik kanitlar) ===")
    zs = {}
    for z in o.zamansallik:
        for x in z:
            zs[x] = zs.get(x, 0) + 1
    for k, v in sorted(zs.items(), key=lambda t: -t[1]):
        yaz("  %-20s %d" % (k, v))

    # ---- capraz tablolar ----
    for ad, hedef in [("DAR HEDEF (guncel primer akciger + supheli primer pulmoner)", "dar_hedef"),
                      ("GENIS TORASIK MALIGNITE", "genis_torasik")]:
        yaz("")
        yaz("=== %s ===" % ad)
        for model, kol in [("Sybil", "sybil_ust"), ("Pillar", "pillar_ust")]:
            v = o[hedef]
            e = o[kol]
            yaz("  %s:" % model)
            yaz("    rapor kaniti VAR / skor >=%.2f : %d" % (ESIK, int((v & e).sum())))
            yaz("    rapor kaniti VAR / skor < %.2f : %d" % (ESIK, int((v & ~e).sum())))
            yaz("    rapor kaniti YOK / skor >=%.2f : %d" % (ESIK, int((~v & e).sum())))
            yaz("    rapor kaniti YOK / skor < %.2f : %d" % (ESIK, int((~v & ~e).sum())))

    # ---- AUC + kumeli bootstrap ----
    yaz("")
    yaz("=== Siralama iliskisi (AUC, hasta-kumeli %95 GA) ===")
    auc_satirlari = []
    for hedef_ad, hedef in [("dar hedef", "dar_hedef"), ("genis torasik", "genis_torasik")]:
        for model, kol in [("Sybil 1y", "sybil1"), ("Sybil 6y", "sybil6"),
                           ("Pillar 1y", "pillar1"), ("Pillar 6y", "pillar6")]:
            y = o[hedef].values
            a = auc_hesapla(y, o[kol].values)
            lo, hi = kumeli_bootstrap_auc(y, o[kol].values, o.hasta.values)
            yaz("  %-16s %-10s n+=%-3d AUC=%.3f  GA [%.3f, %.3f]"
                % (hedef_ad, model, int(y.sum()), a, lo, hi))
            auc_satirlari.append((hedef_ad, model, int(y.sum()), a, lo, hi))

    # ---- 95 hekim etiketi: kesif analizi ----
    etk = pd.read_excel(XLSX, "Hekim Etiket Matrisi")
    etiketler = list(etk.columns[4:])
    satirlar = []
    for L in etiketler:
        v = etk[L].fillna(0).astype(float).values > 0
        n = int(v.sum())
        if n < 10 or n > len(o) - 10:
            continue
        for model, kol in [("Sybil", "sybil1"), ("Pillar", "pillar1")]:
            a = auc_hesapla(v, o[kol].values)
            lo, hi = kumeli_bootstrap_auc(v, o[kol].values, o.hasta.values)
            satirlar.append(dict(etiket=L, n=n, model=model, auc=a,
                                 ga_alt=lo, ga_ust=hi, p=auc_p_degeri(v, o[kol].values)))
    kesif = pd.DataFrame(satirlar)
    if len(kesif):
        kesif["q_fdr"] = bh_fdr(kesif.p.values)
        kesif = kesif.sort_values("p")
        kesif.to_csv(CIKTI / "bimcv_317_etiket_kesif.csv", index=False,
                     encoding="utf-8-sig", float_format="%.4f")
        yaz("")
        yaz("=== Hekim etiketi kesif analizi (n>=10, BH-FDR) ===")
        yaz("  sinanan etiket-model cifti: %d | q<0.05 olan: %d"
            % (len(kesif), int((kesif.q_fdr < 0.05).sum())))
        for _, r in kesif.head(12).iterrows():
            yaz("  %-30s n=%-4d %-7s AUC=%.3f GA [%.3f, %.3f] q=%.3f"
                % (r.etiket, r.n, r.model, r.auc, r.ga_alt, r.ga_ust, r.q_fdr))

    # ---- ciktilar ----
    o.to_json(CIKTI / "bimcv_317_siniflama.json", orient="records",
              force_ascii=False, indent=1)

    with open(CIKTI / "bimcv_317_adjudikasyon.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["patient_id", "series_id", "report_id", "ispanyolca_kanit_cumlesi",
                    "anatomi", "zamansallik", "primer_metastaz", "kesinlik",
                    "malignite_duzeyi", "baglam", "sybil_1y", "pillar_1y",
                    "ikinci_degerlendirici", "uzlastirma_durumu"])
        for _, r in o.iterrows():
            kanitlar = kanit_topla(df.loc[df.no == r.no, "es"].iloc[0])
            tor = [k for k in kanitlar
                   if k["tur"] in ("malignite", "nodul") and k["anatomi"] in TORASIK]
            if not tor:
                w.writerow([r.hasta, r.seri, r.rapor, "", "", "", "", "",
                            r.malignite_duzeyi, "|".join(r.baglam),
                            r.sybil1, r.pillar1, "", "beklemede"])
                continue
            for k in tor:
                w.writerow([
                    r.hasta, r.seri, r.rapor, k["cumle"][:300], k["anatomi"], k["zaman"],
                    "metastaz" if k.get("metastaz") else ("nodul" if k["tur"] == "nodul" else "primer"),
                    "supheli" if k.get("supheli") else ("benign" if k.get("benign") else "belirtilmemis"),
                    r.malignite_duzeyi, "|".join(r.baglam), r.sybil1, r.pillar1,
                    "", "beklemede"])

    (CIKTI / "bimcv_317_tablolar.txt").write_text("\n".join(cikti_metni), encoding="utf-8")
    yaz("")
    yaz("Ciktilar reports/ altina yazildi.")


if __name__ == "__main__":
    main()
