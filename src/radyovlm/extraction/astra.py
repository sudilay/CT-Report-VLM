"""Astra VLM rapor adaptoru — bolum cozumlemesi ve kapsam sozlesmesi.

Sozlesme: `docs/39_astra_veri_sozlesmesi.md` (v4, bagimsiz olcumle revize).

TASARIM KARARI — bolum basligini AD belirler, madde isareti DEGIL.
Olculdu: organ baslikari da madde isaretiyle geliyor (`lung` 174 duz /
1.780 madde), `normal` ise yalniz madde (0 / 5.975). "Madde = deger" kurali
yazilsaydi her organdan ~1.780 baslik kaybedilirdi. Bu nedenle:

  * Taninan bolum adi        -> YENI BOLUM acar
  * Taninmayan kalin etiket  -> bolum ACMAZ; satir mevcut bolumde kalir
    (`**Normal:** No masses...` boyle ebeveyn organda kalir)
  * Markdown `#` basligi     -> her zaman bolum siniri

Bu, sozlesmenin "en yakin baslik" kuralini karsilar ve `normal` tuzagina
dusmez.
"""
from __future__ import annotations

import re
import unicodedata

# 1.0 -> 1.1 · uyum denetimi K5.1: teknik olcu tanimi tekillestirildi
# (`olcu_teknik_mi`). Bolum eslemesi degismedi.
SOZLESME_SURUMU = "astra-sozlesme-1.1"

# --- Bolum kovalari (docs/39 §3) -------------------------------------------

TORAKS = frozenset({
    "lung", "lungs", "left lung", "right lung", "both lungs",
    "lung parenchyma", "pulmonary parenchyma",
    "pleura", "left pleura", "right pleura", "pleural effusion",
    "pleural thickening", "pleural space",
    "trachea", "trachea and bronchie", "trachea and bronchi", "bronchie",
    "bronchi", "bronchus", "bronchial tree", "bronchioles",
    "bronchial wall thickening", "airways",
    "emphysema", "severe emphysema", "atelectasis", "bronchiectasis",
    "air trapping", "air-trapping", "airspace consolidation",
    "airspace opacities",
})

# Mediastinum toraktir; katkisi ayrica izlenebilsin diye ayri kume.
MEDIASTEN = frozenset({
    "mediastinum", "mediastinal lymph nodes", "mediastinal structures",
    "hilum", "hila",
})

# Rapor duzeyi ozet bolumleri — icerigi organ-bagimsizdir.
OZET = frozenset({
    "findings", "description of findings", "abnormalities", "abnormal",
    "abnormality", "abnormal findings", "additional findings",
    "significant findings", "conclusion", "conclusions", "diagnosis",
    "final diagnosis", "impression", "impressions", "summary",
    "summary of findings", "general observations", "overall impression",
})

# Akciger disi organlar — kapsam DISI (docs/39 §3.3.1, karar 2026-09-08).
DIS_ORGAN = frozenset({
    "breast", "breasts", "breast parenchyma",
    "thyroid", "thyroid gland",
    "abdomen", "upper abdomen", "liver", "spleen", "kidneys", "kidney",
    "pancreas", "bowel", "bladder", "gallbladder",
    "adrenal glands", "adrenals", "adrenal",
    "bone", "bones", "ribs", "vertebrae", "skeletal structures",
    "esophagus", "oesophagus",
    "heart", "cardiac", "pericardium",
    "aorta", "aortic aneurysm", "aortopulmonary window", "great vessels",
    "chest wall", "soft tissues", "axilla",
})

# Meta / sablon — hicbir klinik bulgu tasimaz.
META = frozenset({
    "patient information", "prepared by", "report prepared by", "reviewed by",
    "date", "date of examination", "clinical history", "clinical context",
    "imaging details", "imaging modality", "imaging technique", "image type",
    "image quality", "note", "important note", "notes", "additional notes",
    "disclaimer", "limitations",
    "chest ct report", "chest ct image analysis report",
    "chest ct image analysis", "chest ct scan report",
    "comprehensive chest ct diagnosis report", "comprehensive chest ct report",
    "comprehensive chest ct diagnosis", "report",
    # S1 karari: oneri metni bulgu degildir.
    "recommendations", "recommendation", "further evaluation",
    "clinical correlation", "biopsy consideration", "follow-up",
    "reporting physician", "clinical indication", "indication",
})

BASSIZ = "__bassiz__"

_KOVALAR: dict[str, tuple[str, bool]] = {}
for _ad in TORAKS:
    _KOVALAR[_ad] = ("toraks", True)
for _ad in MEDIASTEN:
    _KOVALAR[_ad] = ("mediasten", True)
for _ad in OZET:
    _KOVALAR[_ad] = ("ozet", True)
for _ad in DIS_ORGAN:
    _KOVALAR[_ad] = ("dis_organ", False)
for _ad in META:
    _KOVALAR[_ad] = ("meta", False)

BOLUM_ADLARI = frozenset(_KOVALAR)

# --- Desenler ---------------------------------------------------------------

# Markdown basligi: satir basinda 1-6 '#'
_MD_BASLIK = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")

# Satir basinda (istege bagli madde isaretiyle) kalin etiket.
_KALIN_ETIKET = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?\*\*\s*([^*\n]{1,60}?)\s*\*\*\s*:?\s*(.*)$")

# Teknik parametre — BAGLAM ZORUNLU, `mAs`/`kVp` HARF DUYARLI.
# ⚠ Ciplak `mas` KULLANILMAZ: harf duyarsizken `mass`/`masses` ile eslesir ve
# olculu 222 raporun 221'ini teknik sayar (docs/39 §7.1). Gercek `mAs` tokeni
# bu korpusta 0 kez gecer.
_TEKNIK = re.compile(
    r"(?i:slice\s+thickness|section\s+thickness"
    r"|reconstruction\s+(?:interval|thickness)|slice\s+interval"
    r"|scan\s+interval|collimation|kernel)"
    r"|\bkVp\b|\bmAs\b")

_YER_TUTUCU = re.compile(r"\[[^\]]{2,60}\]|not visible|not given|placeholder",
                         re.I)

# Olcunun cevresinde teknik baglam aranan pencere (scripts/07 ile ayni).
TEKNIK_PENCERE = 60


def normalize_baslik(ham: str) -> str:
    """Baslik adini karsilastirilabilir hale getirir (kovalama icin)."""
    s = unicodedata.normalize("NFKC", ham)
    s = s.replace("*", " ").replace("#", " ")
    s = re.sub(r"^\s*\d+[.)]\s*", "", s)          # "1. Lung" -> "Lung"
    s = s.strip().strip(":").strip()
    s = re.sub(r"\s+", " ", s).lower()
    # "Chest CT Abdomen" gibi onekli varyantlar: onek atilinca taninan bir
    # bolum adi kaliyorsa o ada indirgenir. Olculdu: 11 farkli baslik.
    ek = re.sub(r"^chest\s+ct\s+", "", s)
    if ek != s and ek in _KOVALAR:
        return ek
    return s


def bolum_esle(ham_baslik: str) -> tuple[str, bool, bool]:
    """(bolum_eslenmis, kapsam_ici, bilinmeyen_baslik)."""
    ad = normalize_baslik(ham_baslik)
    if ad in _KOVALAR:
        kova, kapsam = _KOVALAR[ad]
        return kova, kapsam, False
    # Fail-closed (docs/39 §4): bilinmeyen baslik kapsam DISI ve isaretli.
    return "bilinmeyen", False, True


def teknik_satir_mi(satir: str) -> bool:
    """Satir bir teknik cekim parametresi mi bildiriyor."""
    return bool(_TEKNIK.search(satir))


def olcu_teknik_mi(metin: str, bas: int, son: int) -> bool:
    """Bir OLCUNUN teknik parametre olup olmadigi - TEK KAYNAK.

    ⚠ Denetim bulgusu (K5.1): once iki ayri teknik tanimi vardi - adaptorun
    `teknik_satir_mi` deseni ile `scripts/07`nin dar penceresi. Sentetik
    sozlesme vakasi `"Tube current 100 mAs; reconstructed at 5 mm."` ikisini
    ayristirdi: adaptor teknik der, olcu filtresi demezdi ve olcu
    `measured_by` iliskisine girebilirdi.

    Tanim burada TEKILLESTIRILDI. Iki kosuldan biri yeterlidir:
      * olcunun cevresindeki pencerede teknik baglam var, ya da
      * satirin tamami teknik parametre bildiriyor
    """
    pencere = metin[max(0, bas - TEKNIK_PENCERE): son + TEKNIK_PENCERE]
    return bool(_TEKNIK.search(pencere)) or teknik_satir_mi(metin)


def yer_tutucu_var_mi(metin: str) -> bool:
    return bool(_YER_TUTUCU.search(metin))


def bolumlere_ayir(rapor: str) -> list[tuple[str, str]]:
    """Raporu (ham_baslik, icerik) ciftlerine ayirir.

    Baslik olusturan iki sozdizimi (docs/39 §2.0):
      1. Markdown `#` basligi — her zaman bolum siniri
      2. Satir basindaki kalin etiket — YALNIZ adi BOLUM_ADLARI'nda ise

    Taninmayan kalin etiket bolum acmaz; satiri mevcut bolumde birakir.
    Ilk basliktan onceki metin `__bassiz__` kovasina duser.
    """
    bolumler: list[tuple[str, list[str]]] = []
    aktif_baslik = BASSIZ
    aktif_satirlar: list[str] = []

    def kapat() -> None:
        if aktif_satirlar and any(s.strip() for s in aktif_satirlar):
            bolumler.append((aktif_baslik, "\n".join(aktif_satirlar).strip()))

    for satir in rapor.splitlines():
        yeni: str | None = None

        m = _MD_BASLIK.match(satir)
        if m:
            yeni = m.group(2).strip()
            kalan = ""
        else:
            m = _KALIN_ETIKET.match(satir)
            if m and normalize_baslik(m.group(1)) in BOLUM_ADLARI:
                yeni = m.group(1).strip()
                kalan = m.group(2)

        if yeni is None:
            aktif_satirlar.append(satir)
            continue

        kapat()
        aktif_baslik = yeni
        aktif_satirlar = [kalan] if kalan.strip() else []

    kapat()
    return bolumler
