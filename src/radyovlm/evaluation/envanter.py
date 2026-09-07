"""TASK-17 Madde 3 - PAYLASILAN ENVANTERLER, TEK KAYNAK.

Plan: docs/34_task17_calisma_plani.md v2 §3.2 · Karar: D79

NEDEN VAR
---------
D75 sunu bulmustu: hedef atama yordami ile degerlendirilen motor AYNI kavram
tanimini kullanmiyordu, ve fark KILITTEN SONRA ortaya cikti. Dersi yazildi
("ayni tanimi kullanmali") ama duzeltme TASK-19'a birakilmisti. Sozluk
genisletmesi (TASK-17) bu farki BUYUTECEGI icin duzeltme buraya cekildi.

Madde 3'te tarandi ve drift D75'in bildirdiginden GENISTI:

  "malignite terimi" METIN deseni : 4 kopya, 2 farkli icerik
  koruma kapisi siniflari         : 4 kopya, ayni deger AMA IKI FARKLI IS

Bu modul o tanimlarin TEK kaynagidir. Tuketiciler buradan okur; kopya tutmaz.
Bildirimsel karsiligi `configs/degerlendirme_semasi.json` -> `envanterler`
icindedir ve `tests/test_task16_sema.py` ikisini birbirine baglar: belge kodun
gerisinde kalirsa test kirilir.

⚠ IKI AYRI KUME, AYNI ISIMLE KARISTIRILMASIN
--------------------------------------------
Madde 3'un en onemli bulgusu: `MALIGN_URETIR` adi dort yerde ayni degeri
tasiyordu ama IKI FARKLI KURALI ifade ediyordu. Korlemesine tek kaynaga
baglamak, kilidin kendi degismezini SESSIZCE zayiflatirdi.

  HEDEF_MALIGNITE_SINIFLARI -> kilitli takimin KENDI gecerliligi.
      "Kontrol takimindaki hicbir vakanin HEDEFI malignite ureten bir
       duzey olamaz."  (scripts/45, scripts/46, tests/test_task16_takim.py)
      Bir kontrol vakasina `low` HEDEFI yazmak, ne olursa olsun bir hedef
      yazim hatasidir. Bu kume DEGISMEZ.

  KAPI_MALIGNITE_SINIFLARI  -> motorun CIKTISINI sinayan koruma kapisi.
      "Sema kontrol takiminda malignite URETMEYECEK."  (scripts/48)
      docs/34 v2 §4.2 (Karar 2, kullanici onayli) bu kumeden `low`u
      CIKARDI; gerekce ve uc argumani orada.

  tests/test_task16_takim.py'nin docstring'i bu ayrimi ZATEN yaziyordu
  ("Semanin bu vakalarda ne urettigi adim 6'da sinanir; bu test takimin
  kendisinin gecerliligini korur") - ama iki kural ayni sabit adini
  paylastigi icin ayrim koda yansimamisti.
"""

from __future__ import annotations

ENVANTER_SURUMU = "envanter-1.0"

# ═══════════════════════════════════════════════════════════════════════
# 1 · MALIGNITE KAVRAMLARI - VARLIK duzeyi (`normalized_concept`)
# ═══════════════════════════════════════════════════════════════════════
# TASK-16'da `girdi_filtresi.py` icinde tanimliydi ve zaten TEK kaynakti
# (sema.py oradan aliyordu, test JSON'a bagliyordu). Buraya TASINDI ki
# butun paylasilan envanterler ayni yerde dursun; `girdi_filtresi` yeniden
# disa aktarir, boylece `gf.MALIGNITE_KAVRAMLARI` cagiranlar kirilmaz.
#
# ⚠ TASK-17 Tier A bu kumeyi GENISLETECEK (madde 7): `carcinomatosis`
#   eklenecek. `malignancy`, `carcinoma`, `neoplasm` listede YAZILI ama
#   cikarim sozlugunde (`bulgu-1.1`) karsiligi olmadigi icin bugun OLU
#   satirlardir - madde 7-8 onlari canlandiracak.
MALIGNITE_KAVRAMLARI: frozenset[str] = frozenset({
    "metastasis", "malignancy", "carcinoma", "tumor", "neoplasm", "mass",
    "nodule", "lytic_destructive_lesion", "space_occupying_lesion", "spiculated",
    # TASK-17 madde 6 (D84): `lymphoma` cikarim sozlugunde ZATEN VARDI
    # (`lymphomas?`, korpus 112) ve varlik uretiyordu - ama bu envanterde
    # olmadigi icin SEMA ONU GORMUYORDU. D73'un "atifli ama olu kural"
    # kategorisinin TERS YONDEKI karsiligi: uretilen ama sayilmayan kavram.
    # ⚠ Bu ekleme sozluge DOKUNMAZ -> `ent-1.0` KIRILMAZ, yeniden uretim
    # GEREKMEZ. Yalniz semanin neyi sayacagi degisir.
    "lymphoma",
    # TASK-17 madde 8-oncesi ARTIK TARAMASI (D86): sozluk boslugu %18,8 -> %1,1
    # dustukten sonra kalan 106 cumle UC eksige isaret etti.
    "cancer",              # 21 cumle - en yalin terim, sozlukte HIC yoktu
    "malignant_character", # 141 cumle (49'u tek kanit) - NITELEYICI, bkz. D24
    # Tier A/B genisletmesi (D85) - `bulgu-1.2`
    "carcinomatosis", "sarcoma", "mesothelioma", "thymoma",
    "small_cell_carcinoma", "adenocarcinoma", "squamous_cell_carcinoma",
    "large_cell_carcinoma", "carcinoid",
})

# ═══════════════════════════════════════════════════════════════════════
# 2 · MALIGNITE METIN DESENI - CUMLE duzeyi (ham metin)
# ═══════════════════════════════════════════════════════════════════════
# ⚠ Bu, (1)'in metin karsiligi DEGILDIR ve olmasi da beklenmez: (1) cikarim
#   katmaninin urettigi kavramlar uzerinde, bu ise HAM METIN uzerinde
#   calisir. `mass`/`nodule` bilerek burada YOKTUR - metin taramasinda
#   onlar "malignite terimi" sayilmaz (sablon "nonspecific nodules"
#   cumleleri butun taramayi bogardi).
#
# MADDE 3'TE BULUNAN DRIFT ve ONARIMI:
#
#   scripts/42, scripts/44 : `...|tumoral|...`   -> 9.862 cumle   (DAR)
#   scripts/48, scripts/49 : `...|tumor|...`     -> 9.930 cumle   (GENIS)
#
#   Olculdu (gelistirme havuzu, 2026-09-07): genis desen darin UST KUMESI;
#   fark **68 cumle / 56 calisma**, ters yonde fark YOK (0).
#   Kacirilanlar onemsiz degil - tam tersi: "lung tumor", "primary tumor",
#   "followed up due to lung tumor", "Operated right renal tumor on
#   follow-up" gibi cumleler, yani `known_malignancy` adaylari.
#
# SECILEN: GENIS desen (`tumor`). Gerekce: `tumoral` bir sifattir ve `tumor`
# onu zaten kapsar; dar desen bilgi kaybettiriyordu, kazandirmiyordu.
MALIGNITE_METIN_DESENI: str = r"malignan|carcinom|neoplas|metasta|tumor|spicul"

# ⚠⚠ KILIT KAYDI - DOKUNULMAZ TARIHSEL GERCEK
# `configs/sema_takim_kilidi.json` (takim-1.1) ornekleme yapilirken
# scripts/44 DAR deseni kullandi. Yani yukaridaki 68 cumle / 56 calisma
# orneklemeye HIC GORUNMEDI. Kilit kurali geregi (docs/33 §7) kilit
# ACILMAZ ve yeniden orneklenmez; fark ILAN EDILIR (D75 emsali).
# scripts/44 bu yuzden bu modulden OKUMAZ - kendi tarihsel desenini korur,
# yoksa dondurulmus bir artefakti yeniden uretemez hale gelir.
MALIGNITE_METIN_DESENI_KILIT_ONCESI: str = (
    r"malignan|metasta|carcinom|tumoral|neoplas|spicul"
)

# ═══════════════════════════════════════════════════════════════════════
# 3 · KORUMA KAPISI KUMELERI - IKISI FARKLI, bkz. modul basi
# ═══════════════════════════════════════════════════════════════════════

OLCEK_SIRA: tuple[str, ...] = (
    "None", "low", "indeterminate", "intermediate", "high", "known_malignancy",
)

# (a) Kilitli takimin kendi gecerliligi - HEDEF siniflari uzerinde.
#     DEGISMEDI. Bir kontrol vakasina `low` HEDEFI yazmak hedef hatasidir.
HEDEF_MALIGNITE_SINIFLARI: frozenset[str] = frozenset({
    "low", "intermediate", "high", "known_malignancy",
})

# (b) Motorun CIKTISINI sinayan asil kapi (docs/29 §8.3, K-A).
#     docs/34 v2 §4.2 (Karar 2, kullanici onayli) `low`u CIKARDI.
#     Gerekce ozeti: dondurulmus olcut metni hangi duzeylerin sayildigini
#     SAYMIYOR; scripts/48'in kendi yorum satiri "YONLU SUPHE" diyor ama
#     `low`un dondurulmus tanimi "kanit zayif/dolayli" - yon icermez;
#     ve kosumdan once yazilmis dort-sinif eslemesi `low` ile
#     `indeterminate`i AYNI sinifa koyar (`indeterminate` bu gerekceyle
#     kumeden zaten cikarilmisti, docs/33 bulgu 3.1).
KAPI_MALIGNITE_SINIFLARI: frozenset[str] = frozenset({
    "intermediate", "high", "known_malignancy",
})

# K-C (docs/34 v2 §4.2): kontrol takiminda `low` ureten vaka sayisi
# raporlanir ve **<= 1** olmalidir. Esik seciilmedi, TURETILDI: muafiyet
# genisletilmiyor (Karar 3) ve kavram envanteri daraltiliyor, dolayisiyla
# bu tasarimin ONGORUSU 0'dir. 1 bir birim paydir; 2 ve ustu ongorunun
# YANLISLANDIGI anlamina gelir ve kapi KALIR - gevsetilmez.
KAPI_LOW_TOLERANSI: int = 1

__all__ = [
    "ENVANTER_SURUMU",
    "MALIGNITE_KAVRAMLARI",
    "MALIGNITE_METIN_DESENI",
    "MALIGNITE_METIN_DESENI_KILIT_ONCESI",
    "OLCEK_SIRA",
    "HEDEF_MALIGNITE_SINIFLARI",
    "KAPI_MALIGNITE_SINIFLARI",
    "KAPI_LOW_TOLERANSI",
]
