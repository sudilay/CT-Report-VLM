# -*- coding: utf-8 -*-
"""TASK-12 baglam cozumlemesi testleri.

Uc katman:
  1. Ipucu sozlugunun sagligi
  2. Zor vaka takimi - planin 4.x sinir durumlarinin her biri (sabit)
  3. Korpus butunlugu - uretilen tablo uzerinde
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction import context as C     # noqa: E402
from radyovlm.extraction import entities as E    # noqa: E402
from radyovlm.extraction import schema as S      # noqa: E402

ENT = ROOT / "data" / "processed" / "entities.parquet"


@pytest.fixture(scope="module")
def motor():
    kav, _ = E.sozlukleri_yukle()
    M, IX = E.matcher_kur(kav)
    ip, son = C.ipuclarini_kur()

    def _c(metin: str):
        vs = E.cumleden_varliklar(metin, M, IX)
        r = C.kesinlik_ata(metin, vs, ip, son)
        return C.zaman_ata(metin, r, ip, son)

    return _c


def _kes(sonuc, kavram):
    for x in sonuc:
        if x["kavram"].ad == kavram:
            return x
    raise AssertionError(f"{kavram} cikarilmadi: "
                         f"{[x['kavram'].ad for x in sonuc]}")


# =====================================================================
# 1. SOZLUK SAGLIGI
# =====================================================================

def test_sozluk_yuklenir():
    ip, son = C.ipuclarini_kur()
    assert len(ip) >= 30
    assert son.pattern


def test_her_ipucu_korpus_destegi_tasir():
    """Sifir destekli ipucu sozlukte durmamali - olculmemis demektir."""
    sz = C.yukle()
    sifir = []
    for bolum, g in sz.items():
        if not isinstance(g, dict) or bolum.endswith("_olculup_alinmayan"):
            continue
        for ad, t in g.items():
            if isinstance(t, dict) and t.get("korpus") == 0:
                sifir.append(f"{bolum}.{ad}")
    assert not sifir, f"korpus destegi sifir: {sifir}"


def test_ithal_liste_oldugu_gibi_alinmamis():
    """D16: ithal NegEx listesinin %81'i bu korpusta gecmiyor. Reddedilenler
    sayilariyla kayitli olmali ki 'neden yok' sorusunun cevabi belgede olsun."""
    sz = C.yukle()
    red = sz.get("negasyon_olculup_alinmayan", {})
    assert red.get("free_of") == 0
    assert red.get("negative_for") == 0


def test_teknik_cekince_negasyon_bolumunde_degil():
    """Teknik cekince hicbir varliga 'absent' yazdirmamali."""
    sz = C.yukle()
    assert "teknik_cekince" in sz
    assert not set(sz["teknik_cekince"]) & set(sz["negasyon"])


# =====================================================================
# 2. ZOR VAKA TAKIMI - planin 4.x sinir durumlari
# =====================================================================

def test_4_1_cannot_be_excluded_uncertain(motor):
    """TUZAK: icinde 'not' gecer; naif kural 'absent' yazar - anlamin TERSI."""
    r = motor("Underlying pneumonic infiltration cannot be excluded.")
    x = _kes(r, "pneumonia")
    assert x["assertion"] == "uncertain"
    assert "cannot_be_excluded" in x["assertion_rule"]


def test_4_2_nonspecific_bulguyu_yok_etmez(motor):
    """'non' oneki gorup negasyon sayan kural 12.992 cumlede nodulu yok eder."""
    assert _kes(motor("A millimetric nonspecific subpleural nodule was observed."),
                "nodule")["assertion"] == "present"


def test_4_2b_non_calcified_yalnizca_niteleyiciye(motor):
    """Negasyon NITELEYICIYE ait, bulguya degil."""
    r = motor("A non-calcified nodule is seen in the right lung.")
    assert _kes(r, "nodule")["assertion"] == "present"
    assert _kes(r, "calcific")["assertion"] == "absent"


def test_4_3_teknik_cekince_cumleyi_susturmaz(motor):
    """OLCULDU: teknik cekince isaretli cumlelerin %42'sinde BAGIMSIZ gercek
    negasyon var. Cumle duzeyi susturma onlari 'present' yapardi."""
    r = motor("In the upper abdominal sections within the image, no solid mass "
              "was detected as far as can be observed.")
    assert _kes(r, "mass")["assertion"] == "absent"


def test_4_3b_saf_teknik_negasyon_uretmez(motor):
    """'could not be evaluated' = 'kalp yok' demek DEGIL."""
    r = motor("The heart could not be evaluated optimally.")
    assert _kes(r, "heart")["assertion"] == "present"


def test_4_4_negasyon_belirsizligi_yener(motor):
    """'No suspicious lesion' -> absent, uncertain degil."""
    r = motor("No suspicious nodular lesion was detected in the lung parenchyma.")
    assert _kes(r, "nodular_lesion")["assertion"] == "absent"


def test_4_5_koordinasyon_ikisini_de_kapsar(motor):
    """17.291 cumle. Kapsam ilk bulguda kesilirse ikincisi yanlis 'present' kalir."""
    r = motor("No pleural effusion or thickening was observed.")
    assert _kes(r, "effusion")["assertion"] == "absent"
    assert _kes(r, "thickening")["assertion"] == "absent"


def test_4_5b_sonlandirici_kapsami_keser(motor):
    r = motor("No significant consolidation; however, newly developed effusion "
              "is observed.")
    assert _kes(r, "consolidation")["assertion"] == "absent"
    assert _kes(r, "effusion")["assertion"] == "present"


def test_ardil_negasyon_yakalanir(motor):
    """OLCULDU: negatif cumlelerin %19,9'unda ipucu hedeften SONRA. Yalnizca
    ileri yonlu bir NegEx her bes negatif cumleden birini kacirir."""
    x = _kes(motor("Pericardial effusion-thickening was not observed."),
             "effusion_thickening")
    assert x["assertion"] == "absent"
    assert "geri" in x["assertion_rule"]


def test_belirsizlik_parantez_soru(motor):
    """KORPUSA OZGU: soru isaretlerinin %70'i parantez icinde. Hicbir standart
    belirsizlik sozlugunde yoktur."""
    x = _kes(motor("Stable hypodense lesion (cyst?) in the right lobe."), "cyst")
    assert x["assertion"] == "uncertain"


# --------------------------- zamansallik ---------------------------

def test_4_11_increase_zamansal_referanssiz_degisim_degil(motor):
    """OLCULDU: increas* 25.522 cumlede ama yalnizca %3,4'unde zamansal
    referans var. Kalani 'kalinlik artisi' gibi DURAGAN tanimlardir."""
    x = _kes(motor("Peribronchial thickness increases are observed in both lungs."),
             "thickening")
    assert x["change_type"] == "none"


def test_4_11b_increase_zamansal_referansla_degisim(motor):
    x = _kes(motor("The nodule has increased compared to the previous examination."),
             "nodule")
    assert x["change_type"] == "increased"
    assert x["change_cue"]


def test_karsilastirma_referansi_bulguyu_prior_yapmaz(motor):
    """GERILEME TESTI: ilk kurulumda 'cumlede tek zaman ipucu varsa onun
    zamanini al' kurali vardi ve bu cumlede nodulu 'prior' yapiyordu - oysa
    nodul SIMDIKI, 'previous' yalnizca karsilastirma referansi."""
    x = _kes(motor("The nodule has increased compared to the previous examination."),
             "nodule")
    assert x["temporality"] == "current"


def test_prior_kapsaminda_olan_prior_olur(motor):
    r = motor("In the previous CT examination, a nodule was observed in the "
              "right lung.")
    assert _kes(r, "nodule")["temporality"] == "prior"


def test_4_12_stabil_kaydedilir(motor):
    x = _kes(motor("A stable 6x4 mm nodule is observed in the lower lobe."), "nodule")
    assert x["change_type"] == "stable"


def test_4_8_no_significant_change_degisimi_olumsuzlar(motor):
    """'no significant change' bulguyu degil DEGISIMI olumsuzlar."""
    x = _kes(motor("There is no significant change in the nodule."), "nodule")
    assert x["change_type"] == "stable"
    assert x["assertion"] == "present"      # bulgu YOK degil


def test_degisim_ipucu_cift_yonlu(motor):
    """GERILEME TESTI: ilk kurulumda degisim ipuclari ileri yonluydu ve
    'The nodule has increased' cumlesinde OZNEYI kaciriyorlardi - Ingilizcede
    degisim fiili ozneden SONRA gelir."""
    x = _kes(motor("The nodule has regressed compared to the control examination."),
             "nodule")
    assert x["change_type"] == "decreased"


def test_her_varsayilan_disi_atamanin_ipucu_var(motor):
    """K3f: 'absent'/'uncertain' yazan her atamanin bir dayanagi olmali."""
    for t in ["No pleural effusion was observed.",
              "Underlying infiltration cannot be excluded.",
              "Stable hypodense lesion (cyst?) in the liver."]:
        for x in motor(t):
            if x["assertion"] in ("absent", "uncertain"):
                assert x["assertion_cue"], f"{x['metin']} icin ipucu yok"


# =====================================================================
# 3. KORPUS BUTUNLUGU
# =====================================================================

@pytest.fixture(scope="module")
def ent():
    if not ENT.exists():
        pytest.skip("entities.parquet yok")
    d = pd.read_parquet(ENT)
    if "assertion_cue" not in d.columns:
        pytest.skip("TASK-12 henuz uygulanmadi")
    return d


def test_korpus_islenmemis_kalmadi(ent):
    assert (ent.assertion == "not_processed").sum() == 0


def test_korpus_kesinlik_ipucu_tutarli(ent):
    """K3f korpus uzerinde."""
    g = ent[ent.assertion.isin(["absent", "uncertain"])]
    bos = g.assertion_cue.isna() | (g.assertion_cue.astype(str).str.strip() == "")
    assert not bos.any(), f"{int(bos.sum())} atamanin ipucu yok"


def test_korpus_degisim_ipucu_tutarli(ent):
    """K3g: 'increased'/'decreased' ipucusuz yazilamaz."""
    g = ent[ent.change_type.isin(["increased", "decreased"])]
    bos = g.change_cue.isna() | (g.change_cue.astype(str).str.strip() == "")
    assert not bos.any()


def test_korpus_negasyon_gercekten_bulunmus(ent):
    """Negasyon ipuclu cumlelerde artik 'absent' varliklar olmali. TASK-11
    sonunda 1.180.408 varligin TAMAMI 'present' idi - o sessizce yanlisti."""
    assert (ent.assertion == "absent").sum() > 100_000


def test_korpus_sema_dogrulamasindan_gecer(ent):
    sent = pd.read_parquet(ROOT / "data/processed/sentences.parquet")
    reps = pd.read_parquet(ROOT / "data/processed/reports_study_level.parquet",
                           columns=["study_id", "report_text"])
    ihl = S.dogrula_entities(ent, sentences=sent, reports=reps)
    assert not ihl, "\n".join(str(i) for i in ihl)


def test_korpus_surum_kaydedilmis(ent):
    assert ent.context_version.nunique() == 1


# =====================================================================
# 4. ANATOMI KORUMASI — pilot bulgusu (2026-08-28)
# =====================================================================
# Negasyon/belirsizlik ANATOMIYE siciriyordu. Olculdu: 177.922 anatomi 'absent',
# 24.416 'uncertain' = tum varliklarin %17,1'i. Pilot isaretlemede anatomi hata
# orani %43 iken gozlemlerde %6 idi - hata tamamen anatomideydi.

def _t(motor, metin):
    r = motor(metin)
    return {x["kavram"].ad: x["assertion"] for x in r}


def test_anatomi_negasyondan_korunur_gozlem_varken(motor):
    """'No mass was detected in both LUNGS' -> akcigerler DURUYOR, yok olan KITLE."""
    d = _t(motor, "No mass or infiltrative lesion was detected in both lungs.")
    assert d["mass"] == "absent"
    assert d["lung"] == "present"


def test_sifat_anatomi_korunur(motor):
    """'Pleural effusion-thickening was not detected' -> plevra DURUYOR."""
    d = _t(motor, "Pleural effusion-thickening was not detected.")
    assert d["effusion_thickening"] == "absent"
    assert d["pleura"] == "present"


def test_lenf_istasyonlari_korunur(motor):
    d = _t(motor, "No enlarged lymph nodes in prevascular, pre-paratracheal, "
                  "subcarinal areas were detected.")
    assert d["enlarged_lymph_node"] == "absent"
    for st in ("station_prevascular", "station_paratracheal", "station_subcarinal"):
        assert d[st] == "present", f"{st} korunmali"


def test_konum_edati_ardindaki_anatomi_korunur(motor):
    """Kapsamda gozlem YOK ama anatomi konum edatinin ardinda -> korunur."""
    d = _t(motor, "No lymph nodes are observed in the mediastinum.")
    assert d["lymph_node"] == "absent"      # olumsuzlanan bas
    assert d["mediastinum"] == "present"    # bakilan yer


def test_gercekten_yok_olan_anatomi_absent_kalir(motor):
    """Koruma her anatomiyi kurtarmamali - ameliyatla alinmis yapi GERCEKTEN yok.
    Ne kapsamda gozlem var ne de konum edati."""
    d = _t(motor, "The right breast was not observed secondary to the operation.")
    assert d["breast"] == "absent"


def test_belirsizlik_de_anatomiye_sicramaz(motor):
    """'(cyst?)' belirsizligi karacigere gecmez - karaciger KESIN var."""
    d = _t(motor, "Stable hypodense lesion (cyst?) in the right lobe of the liver.")
    assert d["cyst"] == "uncertain"
    assert d["liver"] == "present"


def test_gozlem_hala_dogru_olumsuzlaniyor(motor):
    """Koruma gozlemleri etkilememeli."""
    d = _t(motor, "There is no obstructive pathology in the trachea and both main bronchi.")
    assert d["occlusive_pathology"] == "absent"
    assert d["trachea"] == "present"
    assert d["bronchus"] == "present"


# ===================================================================
# ctx-1.1 - CIKARIM IFADESI 'present' uretir, 'uncertain' degil
# ===================================================================
# PILOT BULGUSU (2026-08-28): 'ile uyumlu' / 'lehine' / 'supheli' ctx-1.0'da
# belirsizlik altindaydi ve 20.587 varligi (belirsizlerin %70'i) yanlislikla
# uncertain yapiyordu. ALAN SOZLUGU BELGESI §12.2 bunlari PRESENT sayar:
# bulgu vardir, yalnizca dayanagi cikarimdir. Ipucu KAYDEDILIR.

def _ck_kes(metin, varliklar):
    ip, son = C.ipuclarini_kur()
    return C.kesinlik_ata(metin, varliklar, ip, son)


def _ck_v(metin, kelime, tip="observation"):
    b = metin.index(kelime)
    return {"bas": b, "son": b + len(kelime), "tip": tip}


@pytest.mark.parametrize("metin,kelime", [
    ("Findings compatible with pneumonia are observed in the right lung.", "pneumonia"),
    ("Appearance consistent with emphysema in both lungs.", "emphysema"),
    ("Evaluated in favor of a benign nodule.", "nodule"),
    ("A suspicious mass is observed in the left upper lobe.", "mass"),
    ("The lesion is probably a hemangioma.", "hemangioma"),
    ("It is thought to be a sequela of infection.", "infection"),
])
def test_cikarim_ifadesi_present_uretir(metin, kelime):
    """Belge §12.2: cikarim ifadeleri bulguyu MEVCUT sayar."""
    r = _ck_kes(metin, [_ck_v(metin, kelime)])[0]
    assert r["assertion"] == "present", (kelime, r["assertion_rule"])


def test_cikarim_ipucusu_kaydedilir():
    """Sonuc present olsa da hangi ifadeden geldigi izlenebilir kalmali -
    ileride 'certainty' alani eklenirse bu kayit olmadan geri uretilemez."""
    m = "Findings compatible with pneumonia are observed."
    r = _ck_kes(m, [_ck_v(m, "pneumonia")])[0]
    assert r["assertion_rule"].startswith("cikarim:")
    assert r["assertion_cue"]


def test_negasyon_cikarimi_yener():
    """'X ile uyumlu bulgu YOK' -> absent. Cikarim negasyonu ezmemeli."""
    m = "No findings compatible with pneumonia were detected in the lungs."
    r = _ck_kes(m, [_ck_v(m, "pneumonia")])[0]
    assert r["assertion"] == "absent", r["assertion_rule"]


def test_gercek_belirsizlik_cikarimdan_etkilenmez():
    """'dislanamaz' ve parantez-soru hâlâ uncertain kalmali."""
    m1 = "Malignancy cannot be excluded for the nodule."
    assert _ck_kes(m1, [_ck_v(m1, "nodule")])[0]["assertion"] == "uncertain"
    m2 = "A hypodense area (cyst?) is seen in the liver."
    assert _ck_kes(m2, [_ck_v(m2, "cyst")])[0]["assertion"] == "uncertain"
