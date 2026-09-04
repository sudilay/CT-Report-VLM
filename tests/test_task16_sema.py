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
    assert set(env["benign_kavramlari"]) == set(sema.BENIGN_KAVRAMLARI)
    assert set(env["f2_muaf_kavramlar"]["liste"]) == set(sema.F2_MUAF_KAVRAMLAR)
    assert set(env["kesin_hukum_kurallari"]["liste"]) == set(sema.KESIN_HUKUM_KURALLARI)


def test_json_kaydinda_her_kural_dayanak_tasir():
    """D27: atifsiz kural yok. `kapsam-disi` teknik dal, dayanak beklemez."""
    j = json.loads(SEMA_JSON.read_text(encoding="utf-8"))
    for k in j["kurallar_sirali"]:
        if k["kod"] in {"kapsam-disi", "C#4(varsayilan)"}:
            continue
        assert k.get("dayanak"), f"dayanaksiz kural: {k['kod']}"
