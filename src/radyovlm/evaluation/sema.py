"""TASK-16 Adim 6 - MALIGNITE DEGERLENDIRME SEMASI (sema-0.9-taslak).

Plan: docs/29 §8.5 adim 6 · Kararlar: docs/31 · Aktarim: docs/30

Bu modul KAYITTAN yazilmistir: her kural docs/31'deki bir C# maddesine ya da
docs/30'daki bir A# kuraline atif tasir. Atifsiz kural yoktur (D27 disiplini).

SURUM: "taslak" - klinik uzman onayi ALINMAYACAKTIR (D71). Bu sema
`sema-1.0` olarak DONDURULMEDEN once kilitli sinir/kontrol/rapor takimina
karsi sinanir (adim 6'nin geri kalani) ve sonuc GORULMEDEN once yazilmis
kabul olcutleriyle (docs/29 §8.1, §8.3) degerlendirilir.

--------------------------------------------------------------------------
GIRDI SOZLESMESI - CUMLE METNI GEREKIR:

Varlik satiri iki farkli metin tasir ve IKISI FARKLI ISE KULLANILIR:
  - `raw_text`     : varligin KENDI span'i (ort. 11 karakter, "ground glass")
  - `cumle_metni`  : varligin gectigi TAM CUMLE (cagiran taraf ekler)

Cumle DUZEYINDE kapsam kuran kurallar (ayirici tani, olumsuzlanmis suphe,
suphe derecesi) `cumle_metni` uzerinde calisir; span uzerinde calisamaz.
`cumle_metni` verilmezse bu kurallar SESSIZCE ATLANIR - `raw_text`e geri
dusulmez (11 karakterlik span'de cumle deseni aramak alet hatasidir; bu
surumden once tam olarak bu hata vardi ve C#16/C#negbelirsiz kurallari hic
tetiklenmiyordu).

--------------------------------------------------------------------------
⚠ ENGINE'IN BILINEN SINIRI (gercek veriyle olculdu, gizlenmiyor):

`assertion_cue` alani (cikarim/belirsizlik tetikleyen HAM ifade) DERECE
KELIMESINI (ornegin "highly") KORUMUYOR - "highly suspicious" ile
"suspicious" ayni cue'ya dusuyor. Bu surumde derece, cue'dan degil
`cumle_metni`nden okunur (DERECE_DESENI, olcum: reports/task16_b_olcumleri
"#4 · suphe derece kelimeleri" - 392 cumle / 230 calisma). Karar yine
`entity_id`ye baglidir: metinden YENI VARLIK URETILMEZ, yalnizca ZATEN
CIKARILMIS bir varligin DERECESI okunur.

KALAN SINIR - `known_malignancy` OTOMATIK URETILMEZ. docs/33 §4.1'in C
karari bu duzey icin raporda YAZILI bilinen/belgelenmis kanser sarti
koyuyor ("known primary", "bladder ca in the follow-up"); bunun tespiti
ayri bir tetikleyici gerektirir ve TASK-17'ye birakilmistir. Hedefi
`known_malignancy` olan vakalar "motor sinirlamasi" olarak isaretlenir,
"kural hatasi" olarak degil.

IKINCI SINIR - derece kapsami CUMLE duzeyidir, varlik duzeyi degil: ayni
cumlede hem dereceli hem deregesiz suphe varsa ikisi de yukselir. Olculmedi,
ilan ediliyor.
--------------------------------------------------------------------------
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

from radyovlm.evaluation import girdi_filtresi as gf

SEMA_SURUMU = "sema-0.9-taslak"

# --- Envanterler -------------------------------------------------------

MALIGNITE_KAVRAMLARI = gf.MALIGNITE_KAVRAMLARI  # ayni envanter, tek kaynak
BENIGN_KAVRAMLARI = frozenset({"sequela", "sequela_change", "granuloma", "granulomatous"})

# 6+1 olcek - sirali. Docs/29 §5.1: belgeden okunan 6 duzey + not_mentioned
# (olcek DISI - veri yoklugu isareti, siraya girmez).
OLCEK_SIRA = ("None", "low", "indeterminate", "intermediate", "high", "known_malignancy")
_SIRA_DEGERI = {d: i for i, d in enumerate(OLCEK_SIRA)}

# C#8: 6+1 -> 4 sinif esleme (docs/29 §5.1)
DORT_SINIF_ESLEME = {
    "None": "malignite_negatif",
    "low": "belirsiz_yetersiz_kanit",
    "indeterminate": "belirsiz_yetersiz_kanit",
    "intermediate": "belirsiz_yetersiz_kanit",
    "high": "malignite_pozitif",
    "known_malignancy": "malignite_pozitif",
}

# Motorun OTOMATIK URETEBILECEGI tavan - bkz. modul basi uyarisi.
MOTOR_TAVANI = "intermediate"

# Ipuclu (hedge) present kurallari - hepsi "intermediate"ye gider (derece
# ayrimi yapilamiyor, bkz. modul basi). C#4'un ust siniri budur.
HEDGE_KURALLARI = frozenset({
    "cikarim:lehine", "cikarim:uyumlu", "cikarim:dusunuldu", "cikarim:onerir",
    "cikarim:degerlendirildi_kalip", "cikarim:supheli", "cikarim:olasilik",
    "cikarim:oncelikle", "cikarim:ikincil",
})

# C#16: ayirici tani / "X ya da Y" kaliplari -> indeterminate (kazanan aranmaz)
#
# ⚠ DARALTILDI: onceki surumde `may (?:also )?(?:be|belong)` de bu desendeydi.
# Yanlisti - docs/33 §3.4 ikisini TERS yonde ayiriyor: YONLU hipotez
# ("may be compatible with metastasis") -> intermediate, AYIRT EDILEMEZ
# ayirici tani ("infection or metastasis") -> indeterminate. Desen olu kod
# oldugu icin (bkz. GIRDI SOZLESMESI) bu hata bugune kadar gorunmedi.
AYIRICI_TANI_DESENI = re.compile(
    r"\bor\b.{0,20}(?:metasta|malignan|carcinom|neoplas)"
    r"|differential diagnosis",
    re.I,
)

# A18 / Kritik kural 1: "dislanamaz" supheyi ORTADAN KALDIRAMAZ -> indeterminate.
# Cumle duzeyinde uygulanir: cikarim katmani ayni cumlede varligi `present`
# isaretlemis olsa bile (ornek: "may belong to infection, metastasis could not
# be excluded" - "may belong" cue'su kazaniyor) A18 yazili kural olarak onceliklidir.
DISLANAMAZ_DESENI = re.compile(r"(?:can|could)\s*not\s+be\s+excluded|cannot be excluded", re.I)

# docs/33 §4.3 (yeni C karari): LEZYON VAR ama karakterize edilemiyor ->
# indeterminate. Hicbir bulgu tarif edilmeden yalnizca inceleme kisitliysa
# ("could not be optimally evaluated") bu desen ESLESMEZ -> not_mentioned kalir.
AYIRT_EDILEMEZ_DESENI = re.compile(
    r"(?:can|could)\s*not\s+be\s+(?:clearly\s+)?distinguished"
    r"|not possible to comment",
    re.I,
)

# docs/33 §4.2 + A26 + C#12: radyologun KESIN BENIGN HUKMU. Iki yoldan tespit:
#   (a) varlik yolu  - ayni cumlede BENIGN kavram `cikarim:` kuraliyla
#       ("evaluated in favor of sequela") - entity_id'ye bagli, tercih edilen yol
#   (b) metin yolu   - kavram uretmeyen benign hukum ifadeleri
# ⚠ Bu karar BILGI KAYBI tasir ve ilan edilmistir: A34 (Fleischner) spikule
# kenarin malignite olasiligini artirdigini yaziyor; kesin benign hukum onu ezer.
BENIGN_HUKUM_DESENI = re.compile(
    r"(?:possibly|probably|likely) benign|in favor of benign|benign in (?:appearance|nature)"
    r"|hilar fat|fat.contain|fatty hilum",
    re.I,
)

# A34: spikulasyon GOZLENEN MORFOLOJIDIR, cikarilmis tani degil. Radyolog
# "spikule kontur" yazdiysa bu bir gozlemdir; F2'nin (kanitsiz present)
# gerekcesi - present'in %80,33'u varsayilan, D29 - CIKARIM tipi kavramlar
# icindi. Morfoloji niteleyicisinden ipucu beklemek aleti yanlis kullanmaktir.
#
# ⚠⚠ SUPHELI TASARIM BORCU - D77. Muafiyetin KENDISI dogru sayiliyor, ama
# vardigi DUZEY sorgulaniyor: muafiyetten sonra `spiculated` hedge disi
# present olarak MOTOR_TAVANI'na (intermediate) gidiyor. Adim 7'de IKI
# BAGIMSIZ YARGIC (Codex, Gemini) bunun fazla agresif oldugunu soyledi -
# olcegin tanimina gore `intermediate` YONLU suphe ister, spikulasyon tek
# basina hicbir yon ifade etmez; ikisi de `low` dedi.
#
# Cozulmemis iki soru (TASK-17 sonrasi):
#   1. Ilke `spiculated`da DURMUYOR - `nodule`/`mass` de gozlenen morfolojidir.
#      Kontrol takiminin 6/23'u present malignite kavrami tasiyor ve onlari
#      sessiz tutan TEK sey F2; muafiyet genislerse hedefi `not_mentioned`
#      olan 5 vaka `low`a cikar.
#   2. `low` koruma kapisinin POZITIF kumesinde (MALIGN_URETIR). Morfolojiyi
#      `low`a indirmek toleranssiz kapiya carpiyor - denendi, kapi kirildi.
#      docs/33 bulgu 3.1 `indeterminate`i ayni gerekcyle kumeden cikarmisti.
F2_MUAF_KAVRAMLAR = frozenset({"spiculated"})

# docs/33 §4.2 "KESIN benign hukum" der. Hedge'li cikarim hukum degildir:
# "possible sequelae" (cikarim:olasilik) radyologun karar verdigi anlamina
# gelmez. Yalniz HUKUM grade kurallar sayilir.
KESIN_HUKUM_KURALLARI = frozenset({
    "cikarim:lehine", "cikarim:uyumlu", "cikarim:degerlendirildi_kalip",
})

# Yeni C karari (docs/31 §5-B): "no suspicious X" -> None (supheyi DISLAR,
# "cannot be excluded" gibi ORTADAN KALDIRAMAYAN belirsizlikten farkli).
NEGATIF_SUPHE_DESENI = re.compile(r"\bno\s+suspicio", re.I)

# C#4 derece esigi: adverb CUE'YA BAGLI yakalanir ("highly suspicious"),
# ciplak "suspicious" tetiklemez. Desen scripts/43'ten aynen alindi (olcum:
# reports/task16_b_olcumleri.json "#4 · suphe derece kelimeleri").
DERECE_DESENI = re.compile(r"high(?:ly)? suspic|strongly suspic|highly suggestive", re.I)


@dataclass
class BulguSonucu:
    entity_id: str
    normalized_concept: str
    duzey: str | None          # None ise bu varlik eksene katkida bulunmuyor
    kaynak: str                # A# / C# atifi
    suphe_yukseltebilir: bool
    not_: str = ""


@dataclass
class RaporSonucu:
    study_id: str
    olcek_duzeyi: str          # OLCEK_SIRA + "not_mentioned"
    dort_sinif: str
    belirleyici_entity_id: str | None
    belirleyici_kaynak: str | None
    motor_tavanina_takildi: bool
    bulgular: list[BulguSonucu] = field(default_factory=list)


def _bulgu_duzeyi(satir: pd.Series, benign_hukum: bool = False) -> BulguSonucu:
    """Tek bir malignite/benign-eksenindeki varligi bulgu duzeyine cevirir.

    Her dal docs/30 (A#) ya da docs/31 (C#)'e atif tasir.

    `benign_hukum`: bu varligin CUMLESINDE radyologun kesin benign hukmu var
    (docs/33 §4.2). Cagiran taraf cumle duzeyinde hesaplar.
    """
    kavram = satir["normalized_concept"]
    eid = satir.get("entity_id", "")
    # Cumle duzeyi kurallar icin; yoksa bos - `raw_text`e GERI DUSULMEZ
    # (bkz. modul basi "GIRDI SOZLESMESI").
    cumle = str(satir.get("cumle_metni", "") or "")

    if kavram in BENIGN_KAVRAMLARI:
        # Benign nitelik ekseni ayri tutulur; malignite duzeyine katilmaz.
        return BulguSonucu(eid, kavram, None, "benign-eksen", True)

    # --- docs/33 §4.2 + A26 + C#12: radyologun KESIN benign hukmu, ayni
    # cumledeki malignite adayini EZER (spikulasyon dahil - A34 karsi kanidi
    # kayitli). Malignite kavrami olmasa bile hukum RAPOR duzeyinde aktif
    # negatiftir (`None`), "ifade yok" (`not_mentioned`) degildir. ---
    if benign_hukum:
        return BulguSonucu(eid, kavram, "None", "A26+C#12+§4.2", True,
                           "radyologun kesin benign hukmu")

    if kavram not in MALIGNITE_KAVRAMLARI:
        return BulguSonucu(eid, kavram, None, "-", True)

    assertion = satir["assertion"]
    cue = str(satir.get("assertion_cue", "") or "")

    # --- C#1: negasyon KAPSAMI, ctx-1.1 tarafindan varlik duzeyinde
    # cozulmustur (assertion=="absent" == dogru kapsamli negasyon). ---
    if assertion == "absent":
        return BulguSonucu(eid, kavram, "None", "A1+C#1", True,
                           "negasyon kapsami icinde (ctx-1.1)")

    # --- Yeni C karari (docs/31 §5-B): "no suspicious X" -> None. ---
    if NEGATIF_SUPHE_DESENI.search(cumle):
        return BulguSonucu(eid, kavram, "None", "A1+C#negbelirsiz", True,
                           "suphe acikca dislanmis")

    # --- Asagidaki UC kural ASSERTION'DAN BAGIMSIZ uygulanir. Sebebi olculdu:
    # cikarim katmani ayni cumlede varligi `present` isaretleyebiliyor
    # (ornek: "may belong to infection, metastasis could not be excluded" ->
    # cue "may be" kazaniyor), o yuzden `uncertain` dalina hapsedilirlerse
    # yazili kural sessizce atlaniyor. ---
    if AYIRICI_TANI_DESENI.search(cumle):
        return BulguSonucu(eid, kavram, "indeterminate", "C#16", True,
                           "ayirici tani / kazanan aranmaz")

    if DISLANAMAZ_DESENI.search(cumle):
        return BulguSonucu(eid, kavram, "indeterminate", "A18", True,
                           "suphe ortadan kaldirilamiyor")

    if AYIRT_EDILEMEZ_DESENI.search(cumle):
        return BulguSonucu(eid, kavram, "indeterminate", "§4.3", True,
                           "lezyon var, karakterize edilemiyor")

    if assertion == "uncertain":
        # --- docs/33 §3.4: parantez ici soru ("(metastasis?)") YONLU
        # hipotezdir, ayirt edilemezlik degil -> bir ust basamak. ---
        if satir.get("assertion_rule", "") == "belirsizlik:parantez_soru":
            return BulguSonucu(eid, kavram, "intermediate", "§3.4", True,
                               "yonlu hipotez (parantez ici soru)")
        # --- A18/Kritik kural 1: uncertain != present -> indeterminate ---
        return BulguSonucu(eid, kavram, "indeterminate", "A18+C#10", True,
                           f"cue: {cue}")

    if assertion == "present":
        # Filtre normalde TUM cerceve icin bir kez hesaplanir
        # (`bulgulari_hesapla`); tek satir dogrudan verilmisse burada uretilir.
        if "dusuk_guven" in satir:
            dusuk_guven, kod = bool(satir["dusuk_guven"]), satir["dusuk_guven_kodu"]
        else:
            dg = gf.uygula(pd.DataFrame([satir]).reset_index(drop=True))
            dusuk_guven, kod = bool(dg.at[0, "dusuk_guven"]), dg.at[0, "dusuk_guven_kodu"]
        assertion_rule = satir.get("assertion_rule", "")

        # A34: gozlenen morfoloji F2'den (kanitsiz present) muaftir; F1
        # (gecmis bulgu) uygulanmaya devam eder.
        if dusuk_guven and kavram in F2_MUAF_KAVRAMLAR and kod == "F2_kanitsiz_present":
            dusuk_guven = False

        if dusuk_guven:
            # F1/F2: ipucusuz veya gecmis - suphe YUKSELTEMEZ (docs/29 §7).
            return BulguSonucu(eid, kavram, "low", "girdi-filtresi:dusuk-guven",
                               False, f"kodu: {kod}")

        if assertion_rule in HEDGE_KURALLARI:
            # C#4 uc-yollu derece ayriminin UST basamagi: derece cue'da
            # korunmuyor, CUMLEDEN okunuyor (modul basi). `known_malignancy`
            # bu yolla URETILMEZ - docs/33 §4.1 yazili bilinen kanser sarti.
            if DERECE_DESENI.search(cumle):
                return BulguSonucu(eid, kavram, "high", "C#4(derece)+A5/A7/A8",
                                   True, f"cue: {cue} - cumlede yuksek derece")
            return BulguSonucu(eid, kavram, MOTOR_TAVANI, "C#4(kismi)+A5/A7/A8",
                               True, f"cue: {cue} - derece kelimesi yok")

        # Beklenmeyen bir assertion_rule - guvenli tarafta kal.
        return BulguSonucu(eid, kavram, MOTOR_TAVANI, "C#4(varsayilan)", True,
                           f"taninmayan kural: {assertion_rule}")

    # Beklenmeyen assertion degeri.
    return BulguSonucu(eid, kavram, None, "-", True, f"islenmeyen assertion: {assertion}")


def _benign_hukum_cumleler(varliklar: pd.DataFrame) -> set:
    """docs/33 §4.2: kesin benign hukum tasiyan cumlelerin `sent_idx` kumesi.

    Iki yol (bkz. BENIGN_HUKUM_DESENI):
      (a) VARLIK yolu - benign kavram `cikarim:` kuraliyla asserted; bu yol
          `entity_id`ye bagli oldugu icin tercih edilir
      (b) METIN yolu  - kavram uretmeyen hukum ifadeleri ("possibly benign")
    """
    if "sent_idx" not in varliklar.columns:
        return set()
    varlik_yolu = varliklar[
        varliklar["normalized_concept"].isin(BENIGN_KAVRAMLARI)
        & varliklar["assertion"].eq("present")
        & varliklar["assertion_rule"].isin(KESIN_HUKUM_KURALLARI)
    ]["sent_idx"]
    metin_yolu = varliklar[
        varliklar.get("cumle_metni", pd.Series(dtype=str))
        .fillna("").str.contains(BENIGN_HUKUM_DESENI, na=False)
    ]["sent_idx"]
    return set(varlik_yolu) | set(metin_yolu)


def bulgulari_hesapla(varliklar: pd.DataFrame) -> list[BulguSonucu]:
    """Bir calismanin varlik satirlarini bulgu sonuclarina cevirir."""
    gerekli = {"entity_id", "normalized_concept", "assertion", "assertion_rule",
               "assertion_cue", "temporality"}
    eksik = gerekli - set(varliklar.columns)
    if eksik:
        raise ValueError(f"sema icin eksik kolon: {sorted(eksik)}")
    benign = _benign_hukum_cumleler(varliklar)
    # Girdi filtresi TUM cerceve icin BIR KEZ - satir basina cagrilirsa
    # her varlik icin ayri DataFrame kurulur ve korpus olceginde kosulamaz.
    if "dusuk_guven" not in varliklar.columns:
        varliklar = gf.uygula(varliklar.reset_index(drop=True))
    return [_bulgu_duzeyi(r, benign_hukum=r.get("sent_idx") in benign)
            for _, r in varliklar.iterrows()]


def rapora_topla(study_id: str, bulgular: list[BulguSonucu]) -> RaporSonucu:
    """C#9/A25/A33: bulgu duzeylerinden RAPOR duzeyi sinifi uretir.

    Kural: suphe_yukseltebilir=True olan bulgular arasinda EN YUKSEK duzey
    kazanir (docs/29 §7, A25, A33). Duzeyi None olan (kapsam disi/benign)
    bulgular sayilmaz.
    """
    malignite_adaylar = [b for b in bulgular if b.duzey is not None and b.kaynak != "benign-eksen"]
    yukseltebilen = [b for b in malignite_adaylar if b.suphe_yukseltebilir]

    motor_tavanina_takildi = False

    if yukseltebilen:
        en_yuksek = max(yukseltebilen, key=lambda b: _SIRA_DEGERI.get(b.duzey, -1))
        olcek = en_yuksek.duzey
        belirleyici, belirleyici_kaynak = en_yuksek.entity_id, en_yuksek.kaynak
        if olcek == MOTOR_TAVANI and any(
            b.kaynak.startswith("C#4") for b in yukseltebilen if b.duzey == MOTOR_TAVANI
        ):
            motor_tavanina_takildi = True
    elif malignite_adaylar:
        # Yalniz dusuk-guvenli aday var: suphe YUKSELTILMEZ (docs/29 §7).
        olcek = "not_mentioned"
        belirleyici = belirleyici_kaynak = None
    else:
        # --- C#8-ek (YENI, bu adimda eklendi - asagida gerekceli) ---
        benign_var = any(b.kaynak == "benign-eksen" for b in bulgular)
        olcek = "not_mentioned"
        belirleyici = belirleyici_kaynak = None
        if benign_var:
            return RaporSonucu(study_id, "not_mentioned", "benign_bulgu",
                               None, "C#8-ek(benign)", False, bulgular)

    dort = DORT_SINIF_ESLEME.get(olcek, "belirsiz_yetersiz_kanit")
    return RaporSonucu(study_id, olcek, dort, belirleyici, belirleyici_kaynak,
                       motor_tavanina_takildi, bulgular)
