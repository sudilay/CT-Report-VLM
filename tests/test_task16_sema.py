"""TASK-16 adim 6 - malignite degerlendirme semasinin birim testleri.

Sinav betigi (`scripts/48`) semayi KILITLI TAKIMA karsi olcer; bu dosya
kurallari TEK TEK sinar. Ikisi farkli seyi korur:
  - sinav: sema dogru KARARI veriyor mu (hedefe karsi)
  - birim: her kural KENDI kosulunda tetikleniyor mu, komsusunu ezmiyor mu

Ayrica bildirimsel kayit (`configs/degerlendirme_semasi.json`) ile kodun
ayrisip ayrismadigi sinanir - belge kodun gerisinde kalirsa test duser.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation import sema  # noqa: E402

SEMA_JSON = KOK / "configs/degerlendirme_semasi.json"


def varlik(**kw) -> pd.DataFrame:
    """Tek varlikli cerceve; sema `bulgulari_hesapla` girdisi seklinde."""
    temel = {
        "entity_id": "e1", "study_id": "s1", "sent_idx": 0,
        "normalized_concept": "nodule", "assertion": "present",
        "assertion_rule": "cikarim:lehine", "assertion_cue": "in favor of",
        "temporality": "current", "raw_text": "nodule", "cumle_metni": "",
    }
    temel.update(kw)
    return pd.DataFrame([temel])


def duzey(**kw) -> str | None:
    """Tek varligin bulgu duzeyi."""
    return sema.bulgulari_hesapla(varlik(**kw))[0].duzey


def rapor_duzeyi(cerceve: pd.DataFrame) -> str:
    return sema.rapora_topla("s1", sema.bulgulari_hesapla(cerceve)).olcek_duzeyi


# --- C#nodul-kalip (TASK-17 madde 4, D81) -----------------------------
# docs/34 v2 §0 "Istisna 2" ile ilan edilmis kapsam. Olcum: D80.

def _kalip(**kw):
    """Sozlesme alanlari DOLU bir kalip-nodul satiri."""
    temel = {"cumle_metni": "Millimetric nonspecific nodules in both lungs.",
             "sablon_cumle": True, "supheli_niteleyici": False}
    temel.update(kw)
    return varlik(**temel)


def test_D87_kalip_kurali_VARSAYILAN_OLARAK_ETKISIZ():
    """⛔ D87: D81 kurali GERI ALINDI - bagimsiz denetim (Codex) haklıydi.

    Bu test kuralin YENIDEN SESSIZCE ACILMASINI engeller. Acilmasi ancak
    altin/patoloji dogrulamasi ya da kor uzman yargisi geldiginde, ayri bir
    kararla olabilir.
    """
    assert sema.KALIP_NODUL_KURALI_ETKIN is False
    b = sema.bulgulari_hesapla(_kalip())[0]
    assert b.kaynak != "C#nodul-kalip", "kural etkisiz olmali"


def test_D87_kural_acilirsa_eski_davranis_geri_gelir(monkeypatch):
    """Altyapi KORUNDU (D80 olcumu gecerli bir bulgudur) - madde 13'te
    alternatif senaryo olarak kosulabilsin diye. Bayrak acilirsa calisir."""
    monkeypatch.setattr(sema, "KALIP_NODUL_KURALI_ETKIN", True)
    b = sema.bulgulari_hesapla(_kalip())[0]
    assert b.duzey is None
    assert b.kaynak == "C#nodul-kalip"


def test_nodul_kalip_supheli_niteleyici_varsa_BASTIRILMAZ(monkeypatch, ):
    """Olculdu (D80): kalip icinde 94 varlik gercek supheli niteleyici tasiyor.

    Duz "kalip" kurali onlari susturur - bu yuzden kural
    "KALIP **VE** supheli niteleyici YOK" ister.
    """
    monkeypatch.setattr(sema, "KALIP_NODUL_KURALI_ETKIN", True)
    b = sema.bulgulari_hesapla(_kalip(supheli_niteleyici=True))[0]
    assert b.kaynak != "C#nodul-kalip"


def test_nodul_kalip_yalniz_present_uzerinde_calisir(monkeypatch, ):
    """`absent` nodul AKTIF NEGATIF (`None`) uretmeye devam eder.

    Kural negasyon semantigine dokunmaz: "no nonspecific nodules observed"
    bir bulgu YOKLUGU degil, aktif bir olumsuz hukumdur.
    """
    monkeypatch.setattr(sema, "KALIP_NODUL_KURALI_ETKIN", True)
    b = sema.bulgulari_hesapla(_kalip(assertion="absent"))[0]
    assert b.kaynak != "C#nodul-kalip"
    assert b.duzey == "None"


def test_nodul_kalip_sozlesme_yoksa_SESSIZCE_ATLANIR():
    """D73 emsali: alan yoksa kural atlanir, varsayilana GERI DUSULMEZ.

    Alan yoklugu "kalip degil" DEMEK DEGILDIR, "olculmedi" demektir;
    olculmemis bir seye dayanarak bastirma yapilmaz.
    """
    v = varlik(cumle_metni="Millimetric nonspecific nodules in both lungs.")
    assert "sablon_cumle" not in v.columns
    assert sema.bulgulari_hesapla(v)[0].kaynak != "C#nodul-kalip"


def test_nodul_kalip_baska_kavrama_bulasmaz(monkeypatch, ):
    """Ayni cumlede gecen `mass` etkilenmez - kural kavrama ozgudur."""
    monkeypatch.setattr(sema, "KALIP_NODUL_KURALI_ETKIN", True)
    b = sema.bulgulari_hesapla(_kalip(normalized_concept="mass"))[0]
    assert b.kaynak != "C#nodul-kalip"


def test_nodul_kalip_sablon_olmayan_nonspecific_de_yakalanir(monkeypatch, ):
    """KALIP = sablon VEYA `nonspecific` - ikisi de tek basina yeter."""
    monkeypatch.setattr(sema, "KALIP_NODUL_KURALI_ETKIN", True)
    b = sema.bulgulari_hesapla(_kalip(sablon_cumle=False))[0]
    assert b.kaynak == "C#nodul-kalip"


def test_nodul_kalip_duz_nodul_cumlesini_yakalamaz(monkeypatch, ):
    """Niteleyicisiz ama KALIP da olmayan nodul gosterge olmaya devam eder."""
    monkeypatch.setattr(sema, "KALIP_NODUL_KURALI_ETKIN", True)
    b = sema.bulgulari_hesapla(_kalip(
        cumle_metni="A 12 mm nodule in the right upper lobe.",
        sablon_cumle=False))[0]
    assert b.kaynak != "C#nodul-kalip"


# --- C#bilinen-kanser (TASK-17 madde 11, D92) -------------------------
# docs/34 v2 §0 "Istisna 1": kural TASK-16'da (docs/33 §4.1) KARARA
# BAGLANMIS ama KODLANMAMISTI. Bu testler onu ve SINIRLARINI korur.

def _km(cumle, **kw):
    t = {"cumle_metni": cumle}
    t.update(kw)
    return varlik(**t)


def test_bilinen_kanser_olcegin_en_ustunu_uretir():
    b = sema.bulgulari_hesapla(_km(
        "In the follow-up, breast Ca, bone lesion compatible with metastasis.",
        normalized_concept="metastasis"))[0]
    assert b.duzey == "known_malignancy"
    assert b.kaynak == "C#bilinen-kanser"


@pytest.mark.parametrize("cumle", [
    "In the case with known primary, evaluated in favor of metastasis.",
    "It was learned that the patient had been operated for lung Ca.",
    "It was learned that bilateral lobectomy was performed due to pulmonary Ca.",
    "In the patient with a history of rectal ca, new nodular lesions.",
])
def test_bilinen_kanser_olculmus_cipalar(cumle):
    """Cipalar korpusta OLCULDU (D92): in the follow-up 104, followed up 64,
    known 53, operated 29, history of 24, diagnosed 3."""
    assert sema._bilinen_kanser(
        _km(cumle, normalized_concept="metastasis").iloc[0])


def test_bilinen_kanser_ONCEKI_RAPOR_OKUMASINI_tetiklemez():
    """⛔ docs/33 §4.1: 'YALNIZ RADYOLOJIK HUKUM en fazla `high` uretir.'

    'it was learned that these lesions were metastases' onceki raporu
    okumaktir - belgelenmis kanser oykusu DEGIL. Olculdu (D92): baska
    cipasi olmayan 22 cumlenin yarisi bu turdendi; `it was learned` bu
    yuzden TEK BASINA cipa sayilmadi.
    """
    assert not sema._bilinen_kanser(
        _km("It was learned that these lesions were metastases.",
            normalized_concept="metastasis").iloc[0])


def test_bilinen_kanser_absent_varligi_tetiklemez():
    """'no metastasis' bir bilinen kanser IDDIASI degildir."""
    assert not sema._bilinen_kanser(
        _km("In the follow-up, breast Ca, no metastasis was observed.",
            normalized_concept="metastasis", assertion="absent").iloc[0])


def test_bilinen_kanser_sozlesme_yoksa_SESSIZCE_ATLANIR():
    """D73 emsali: `cumle_metni` yoksa kural atlanir, `raw_text`e DUSULMEZ."""
    v = varlik(normalized_concept="metastasis")
    assert v.iloc[0]["cumle_metni"] == ""
    assert sema.bulgulari_hesapla(v)[0].kaynak != "C#bilinen-kanser"


@pytest.mark.parametrize("cumle", [
    "In the upper lobes, icy ca density increases were observed.",
    "Calcific atheroma plaques in the vascular structures.",
    "Apical pleural thickening in both lungs.",
])
def test_ca_KELIME_SINIRLI_olmak_zorunda(cumle):
    """⚠ GERCEK BIR TEHLIKE - yazim sirasinda OLUSTU ve test yakaladi.

    `ca` kelime siniri olmadan yazilirsa `calcification`, `vascular`,
    `apical` gibi YUZLERCE kelimenin icinde eslesir ve tetikleyici pratik
    olarak HER cumlede atesler. Bu test o kaymanin geri gelmesini engeller.
    Ayrica 'icy ca density' korpusta gercek bir ceviri artefaktidir ve
    kanser DEGILDIR.
    """
    assert not sema._bilinen_kanser(
        _km(cumle, normalized_concept="metastasis").iloc[0])


def test_bilinen_kanser_kanser_terimi_OLMADAN_tetiklemez():
    """Cipa TEK BASINA yetmez - cumlede kanser terimi de olmali."""
    assert not sema._bilinen_kanser(
        _km("In the follow-up, no significant change was observed.",
            normalized_concept="metastasis").iloc[0])


@pytest.mark.parametrize("cumle", [
    "Consolidation due to malignant infiltration in the right lung.",
    "The appearance may be due to malignancies.",
    "Pleural thickening due to malignant process.",
    "Findings may be due to malignancy or infection.",
])
def test_D97_radyolojik_nedensellik_kanser_oykusu_SAYILMAZ(cumle):
    """⛔ Kor yargida cikan DORT yanlis pozitifin DORDU de bu daldandi.

    `(?:due to|because of) + malignan*` RADYOLOJIK NEDENSELLIK bildiriyordu,
    BELGELENMIS kanser oykusu degil. Dal daraltildi (`malignan\w*` cikarildi);
    `cancer`/`carcinom`/`ca` kaldi cunku onlar klinik ENDIKASYON bildiriyor.
    Bu test daralmanin geri alinmasini engeller.
    """
    v = _km(cumle, normalized_concept="metastasis")
    assert not sema._bilinen_kanser(v.iloc[0])


@pytest.mark.parametrize("cumle", [
    "It was learned that bilateral lobectomy was performed due to pulmonary Ca.",
    "It was learned that the patient underwent lobectomy due to lung ca.",
])
def test_D97_klinik_endikasyon_KORUNDU(cumle):
    """Daraltma DOGRU pozitifleri kaybetmemeli - olculdu: hicbiri kaybolmadi."""
    v = _km(cumle, normalized_concept="metastasis")
    assert sema._bilinen_kanser(v.iloc[0])


# --- BOLUM ANAHTARI (D96) ---------------------------------------------
# ⚠ Bagimsiz denetim (Codex) buldu: `sent_idx` HER BOLUMDE SIFIRDAN BASLAR.
# Yalniz `sent_idx` ile birlestirmek Findings ve Impression cumlelerini
# birbirine karistirir. Kusur TASK-16'dan mirastir.

def test_D96_sent_idx_TEK_BASINA_benzersiz_DEGIL():
    """Hatanin KOKUNU belgeler: anahtarin benzersiz olmadigini olcer.

    Bu test veri yoksa atlanir; varsa (study_id, sent_idx) ikilisinin
    korpusta benzersiz OLMADIGINI ve (study_id, section, sent_idx)
    uclusunun benzersiz OLDUGUNU dogrular.
    """
    import pandas as pd
    yol = KOK / "data/processed/sentences.parquet"
    if not yol.exists():
        pytest.skip("korpus yok")
    c = pd.read_parquet(yol, columns=["study_id", "section", "sent_idx"])
    uclu = len(c.drop_duplicates(["study_id", "section", "sent_idx"]))
    ikili = len(c.drop_duplicates(["study_id", "sent_idx"]))
    assert uclu == len(c), "(study_id, section, sent_idx) benzersiz OLMALI"
    assert ikili < len(c), (
        "(study_id, sent_idx) benzersiz CIKTI - bu testin varsayimi degisti, "
        "gozden gecir")


def test_D96_benign_hukum_BOLUMLER_ARASI_TASMIYOR():
    """Findings'teki benign hukum, Impression'daki ayni sent_idx'i ETKILEMEMELI.

    Hatali surumde `_benign_hukum_cumleler` ciplak `sent_idx` kumesi
    donduruyordu; Findings cumle 0'daki "possibly benign" ifadesi
    Impression cumle 0'daki malignite bulgusunu da EZIYORDU.
    """
    import pandas as pd
    cerceve = pd.DataFrame([
        # Findings/0: benign hukum tasiyan cumle
        {"entity_id": "e1", "study_id": "s1", "section": "findings", "sent_idx": 0,
         "normalized_concept": "nodule", "assertion": "present",
         "assertion_rule": "cikarim:lehine", "assertion_cue": "in favor of",
         "temporality": "current", "raw_text": "nodule",
         "cumle_metni": "The nodule is possibly benign."},
        # Impression/0: AYNI sent_idx, ama benign hukum YOK
        {"entity_id": "e2", "study_id": "s1", "section": "impression", "sent_idx": 0,
         "normalized_concept": "metastasis", "assertion": "present",
         "assertion_rule": "cikarim:lehine", "assertion_cue": "in favor of",
         "temporality": "current", "raw_text": "metastasis",
         "cumle_metni": "Findings are in favor of metastasis."},
    ])
    sonuc = {b.entity_id: b for b in sema.bulgulari_hesapla(cerceve)}
    assert sonuc["e1"].kaynak.startswith("A26"), "findings/0 benign hukum almali"
    assert not sonuc["e2"].kaynak.startswith("A26"), (
        "⚠ BOLUM TASMASI: impression/0, findings/0'in benign hukmunu aldi")


# --- Olcek ve esleme ---------------------------------------------------

def test_olcek_sirali_ve_not_mentioned_olcek_disi():
    assert sema.OLCEK_SIRA[0] == "None"
    assert sema.OLCEK_SIRA[-1] == "known_malignancy"
    assert "not_mentioned" not in sema.OLCEK_SIRA


def test_dort_sinif_esleme_olcegin_tamamini_kapsar():
    assert set(sema.DORT_SINIF_ESLEME) == set(sema.OLCEK_SIRA)


def test_yalniz_high_ve_known_malignancy_pozitif():
    pozitif = {d for d, s in sema.DORT_SINIF_ESLEME.items() if s == "malignite_pozitif"}
    assert pozitif == {"high", "known_malignancy"}


# --- Kapsam ------------------------------------------------------------

def test_malignite_disi_kavram_eksene_katilmaz():
    assert duzey(normalized_concept="lung") is None


def test_benign_kavram_ayri_eksende():
    b = sema.bulgulari_hesapla(varlik(normalized_concept="granuloma"))[0]
    assert b.duzey is None and b.kaynak == "benign-eksen"


# --- Negasyon ve olumsuzlanmis suphe -----------------------------------

def test_absent_none_verir():
    assert duzey(assertion="absent") == "None"


def test_no_suspicious_none_verir():
    assert duzey(cumle_metni="No suspicious mass was observed.") == "None"


def test_cannot_be_excluded_no_suspicious_ile_karistirilmaz():
    """'dislanamaz' supheyi ORTADAN KALDIRAMAZ; 'no suspicious' DISLAR."""
    assert duzey(cumle_metni="However, metastasis cannot be excluded.") == "indeterminate"


# --- Ayirici tani · yonlu hipotez ayrimi (docs/33 §3.4) ----------------

def test_ayirici_tani_indeterminate():
    assert duzey(cumle_metni="may be of fungal infection or metastasis") == "indeterminate"


def test_yonlu_hipotez_ayirici_tani_SAYILMAZ():
    """'may be' tek basina ayirici tani DEGILDIR - ilk surumdeki hata buydu."""
    assert duzey(cumle_metni="may be compatible with capsular metastasis") == "intermediate"


def test_parantez_soru_yonlu_hipotezdir():
    assert duzey(assertion="uncertain", assertion_rule="belirsizlik:parantez_soru",
                 cumle_metni="(metastasis?)") == "intermediate"


# --- Teknik ayrim (docs/33 §4.3) ---------------------------------------

def test_lezyon_var_karakterize_edilemiyor():
    assert duzey(cumle_metni="cannot be clearly distinguished from artifact") == "indeterminate"


def test_yalniz_inceleme_kisitliligi_indeterminate_URETMEZ():
    """K-teknik-01 ile K-teknik-02'yi ayiran sinir."""
    assert duzey(cumle_metni="Lung parenchyma could not be optimally evaluated.") \
        == "intermediate"


# --- Derece (C#4 · D73) ------------------------------------------------

def test_yuksek_derece_high_verir():
    assert duzey(cumle_metni="A highly suspicious mass lesion in favor of malignancy") \
        == "high"


def test_ciplak_suspicious_high_VERMEZ():
    assert duzey(cumle_metni="suspicious nodular lesion in favor of metastasis") \
        == "intermediate"


def test_derece_cue_alanindan_DEGIL_cumleden_okunur():
    """`assertion_cue` derece kelimesini korumuyor - D73'un olcumu."""
    assert duzey(assertion_cue="suspicious", cumle_metni="highly suspicious") == "high"


def test_cumle_metni_yoksa_cumle_kurallari_sessizce_atlanir():
    """`raw_text`e GERI DUSULMEZ - span'de cumle deseni aramak alet hatasidir."""
    assert duzey(cumle_metni="", raw_text="highly suspicious mass") == "intermediate"


# --- Girdi filtresi ----------------------------------------------------

def test_gecmis_bulgu_supheyi_yukseltemez():
    b = sema.bulgulari_hesapla(varlik(temporality="prior"))[0]
    assert b.duzey == "low" and b.suphe_yukseltebilir is False


def test_kanitsiz_present_supheyi_yukseltemez():
    b = sema.bulgulari_hesapla(varlik(assertion_rule="varsayilan_present"))[0]
    assert b.duzey == "low" and b.suphe_yukseltebilir is False


def test_spikulasyon_F2den_muaf_ama_F1den_degil():
    """A34: gozlenen morfoloji ipucu gerektirmez; gecmis bulgu yine susturulur."""
    muaf = sema.bulgulari_hesapla(
        varlik(normalized_concept="spiculated", assertion_rule="varsayilan_present"))[0]
    assert muaf.suphe_yukseltebilir is True

    gecmis = sema.bulgulari_hesapla(
        varlik(normalized_concept="spiculated", assertion_rule="varsayilan_present",
               temporality="prior"))[0]
    assert gecmis.suphe_yukseltebilir is False


# --- Benign hukum (docs/33 §4.2) ---------------------------------------

def test_kesin_benign_hukum_malignite_adayini_ezer():
    c = pd.concat([
        varlik(entity_id="e1", normalized_concept="nodule"),
        varlik(entity_id="e2", normalized_concept="sequela",
               assertion_rule="cikarim:lehine"),
    ], ignore_index=True)
    assert rapor_duzeyi(c) == "None"


def test_hedgeli_benign_hukum_SAYILMAZ():
    """'possible sequelae' karar degildir - daraltma bu testle korunuyor."""
    c = pd.concat([
        varlik(entity_id="e1", normalized_concept="nodule",
               assertion_rule="varsayilan_present"),
        varlik(entity_id="e2", normalized_concept="sequela",
               assertion_rule="cikarim:olasilik"),
    ], ignore_index=True)
    assert rapor_duzeyi(c) == "not_mentioned"


def test_metin_yolu_benign_hukum():
    assert duzey(normalized_concept="lymph_node",
                 cumle_metni="hilar fat contents selected, possibly benign") == "None"


# --- Toplama kurali (C#9) ----------------------------------------------

def test_en_yuksek_suphe_kazanir():
    c = pd.concat([
        varlik(entity_id="e1", assertion="absent"),
        varlik(entity_id="e2", cumle_metni="highly suspicious in favor of metastasis"),
    ], ignore_index=True)
    assert rapor_duzeyi(c) == "high"


def test_yalniz_dusuk_guvenli_aday_supheyi_yukseltmez():
    assert rapor_duzeyi(varlik(temporality="prior")) == "not_mentioned"


def test_malignite_ekseni_bos_ise_not_mentioned():
    assert rapor_duzeyi(varlik(normalized_concept="lung")) == "not_mentioned"


def test_bos_cerceve_not_mentioned():
    assert sema.rapora_topla("s1", []).olcek_duzeyi == "not_mentioned"


# --- Sozlesme ve eksik kolon -------------------------------------------

def test_eksik_kolon_hata_verir():
    with pytest.raises(ValueError, match="eksik kolon"):
        sema.bulgulari_hesapla(pd.DataFrame([{"entity_id": "e1"}]))


# --- Bildirimsel kayit kodla ayrismasin --------------------------------

def test_json_kaydi_kodla_ayni_olcegi_tanimlar():
    j = json.loads(SEMA_JSON.read_text(encoding="utf-8"))
    assert tuple(j["olcek"]["sirali_duzeyler"]) == sema.OLCEK_SIRA
    assert j["sema_version"] == sema.SEMA_SURUMU


def test_json_kaydi_kodla_ayni_envanterleri_tanimlar():
    j = json.loads(SEMA_JSON.read_text(encoding="utf-8"))
    env = j["envanterler"]
    assert set(env["malignite_kavramlari"]["liste"]) == set(sema.MALIGNITE_KAVRAMLARI)
    # D82: benign envanter duz listeden STATUS tasiyan sozluge cevrildi
    # (korpustan turetilmis DEGIL, C karari oldugu kayda gecti).
    assert set(env["benign_kavramlari"]["liste"]) == set(sema.BENIGN_KAVRAMLARI)
    assert env["benign_kavramlari"]["turetme_sonucu"].startswith("BASARISIZ")
    assert set(env["f2_muaf_kavramlar"]["liste"]) == set(sema.F2_MUAF_KAVRAMLAR)
    assert set(env["kesin_hukum_kurallari"]["liste"]) == set(sema.KESIN_HUKUM_KURALLARI)


def test_d79_tek_kaynak_envanteri_belgeyle_ayni():
    """TASK-17 madde 3 (D79): tek kaynak `envanter.py` <-> bildirimsel kayit.

    Belge kodun gerisinde kalirsa bu test kirilir. Drift'in kendisi bu
    gorevin bulgusuydu; ayni drift'in geri gelmesini test engeller.
    """
    from radyovlm.evaluation import envanter as inv

    j = json.loads(SEMA_JSON.read_text(encoding="utf-8"))
    e = j["envanterler"]

    assert e["malignite_metin_deseni"]["desen"] == inv.MALIGNITE_METIN_DESENI
    kk = e["koruma_kapisi_kumeleri"]
    assert set(kk["hedef_malignite_siniflari"]["liste"]) == set(inv.HEDEF_MALIGNITE_SINIFLARI)
    assert set(kk["kapi_malignite_siniflari"]["liste"]) == set(inv.KAPI_MALIGNITE_SINIFLARI)
    assert kk["kapi_malignite_siniflari"]["K_C"]["tolerans"] == inv.KAPI_LOW_TOLERANSI


def test_d79_iki_kapi_kumesi_ayri_kalir():
    """Karar 2 YALNIZ motor kapisina uygulandi, kilit gecerliligine DEGIL.

    Ikisi ayni degere donerse biri sessizce degistirilmis demektir:
      - HEDEF kumesi `low` ICERMELI (kontrol vakasina low HEDEFI yazilamaz)
      - KAPI kumesi `low` ICERMEMELI (docs/34 v2 §4.2, Karar 2)
    """
    from radyovlm.evaluation import envanter as inv

    assert "low" in inv.HEDEF_MALIGNITE_SINIFLARI
    assert "low" not in inv.KAPI_MALIGNITE_SINIFLARI
    assert inv.KAPI_MALIGNITE_SINIFLARI < inv.HEDEF_MALIGNITE_SINIFLARI


def test_d79_kilit_oncesi_desen_gercek_desenin_alt_kumesi():
    """Kilit DAR desenle orneklendi; genis desen onun UST kumesi olmali.

    Ust kume degilse "kilit yalniz bilgi KACIRDI" ifadesi yanlis olur -
    kilit ayrica YANLIS cumle de almis olurdu ve bu daha agir bir bulgudur.
    """
    import re

    from radyovlm.evaluation import envanter as inv

    ornekler = [
        "lung tumor followed up", "tumoral lesion", "malignancy suspected",
        "carcinoma of the lung", "metastasis in the liver", "spiculated nodule",
        "neoplasm", "no pathology",
    ]
    genis = re.compile(inv.MALIGNITE_METIN_DESENI, re.I)
    dar = re.compile(inv.MALIGNITE_METIN_DESENI_KILIT_ONCESI, re.I)
    for c in ornekler:
        if dar.search(c):
            assert genis.search(c), f"dar desen yakaladi ama genis kacirdi: {c!r}"


def test_json_kaydinda_her_kural_dayanak_tasir():
    """D27: atifsiz kural yok. `kapsam-disi` teknik dal, dayanak beklemez."""
    j = json.loads(SEMA_JSON.read_text(encoding="utf-8"))
    for k in j["kurallar_sirali"]:
        if k["kod"] in {"kapsam-disi", "C#4(varsayilan)"}:
            continue
        assert k.get("dayanak"), f"dayanaksiz kural: {k['kod']}"
