"""TASK-16 Adim 5 - girdi kalite filtresinin degismezleri.

Plan: docs/29 §7 · Modul: src/radyovlm/evaluation/girdi_filtresi.py

Filtrenin isi TEK: olculmus cikarim kusurlarinin (K7 prior F1 %36,4,
`uncertain` duyarliligi %71/%46) rapor sinifini haksiz yere YUKSELTMESINI
engellemek. Bu testler o davranisi sabitler.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation import girdi_filtresi as gf  # noqa: E402


def _varlik(**k) -> dict:
    """Varsayilan olarak GUVENLI bir varlik; testler tek alan degistirir."""
    temel = {
        "normalized_concept": "nodule",
        "assertion": "present",
        "temporality": "current",
        "assertion_rule": "cikarim:uyumlu",   # ipucu VAR
    }
    temel.update(k)
    return temel


def _uygula(*kayitlar) -> pd.DataFrame:
    return gf.uygula(pd.DataFrame(list(kayitlar)))


# --- K25: filtre dogru varliklari isaretliyor -------------------------------

def test_k25_ipuclu_present_guvenli():
    """Ipucuyla atanmis `present` dusuk guvenli DEGILDIR."""
    d = _uygula(_varlik())
    assert not d.at[0, "dusuk_guven"]
    assert d.at[0, "suphe_yukseltebilir"]


def test_k25_prior_her_zaman_dusuk_guven():
    """F1: temporality='prior' olan varlik, ipucusu olsa bile dusuk guvenli."""
    d = _uygula(_varlik(temporality="prior"))
    assert d.at[0, "dusuk_guven"]
    assert "F1_gecmis_bulgu" in d.at[0, "dusuk_guven_kodu"]
    assert not d.at[0, "suphe_yukseltebilir"], "gecmis bulgu suphe YUKSELTEMEZ"


def test_k25_kanitsiz_present_dusuk_guven():
    """F2: malignite kavrami + varsayilan_present -> dusuk guven."""
    d = _uygula(_varlik(assertion_rule="varsayilan_present"))
    assert d.at[0, "dusuk_guven"]
    assert "F2_kanitsiz_present" in d.at[0, "dusuk_guven_kodu"]


def test_k25_malignite_disi_kavram_f2den_etkilenmez():
    """F2 YALNIZ malignite eksenindeki kavramlara uygulanir."""
    d = _uygula(_varlik(normalized_concept="chest_wall", assertion_rule="varsayilan_present"))
    assert not d.at[0, "dusuk_guven"], "anatomi kavrami F2'ye girmemeli"


def test_k25_absent_f2den_etkilenmez():
    """F2 yalniz `present` icin; `absent` olumsuzlama ipucuyla gelir."""
    d = _uygula(_varlik(assertion="absent", assertion_rule="negasyon_ileri:no_oncul"))
    assert not d.at[0, "dusuk_guven"]


def test_k25_iki_kural_birden_tetiklenebilir():
    d = _uygula(_varlik(temporality="prior", assertion_rule="varsayilan_present"))
    kod = d.at[0, "dusuk_guven_kodu"]
    assert "F1_gecmis_bulgu" in kod and "F2_kanitsiz_present" in kod


# --- K26: sozlesme ----------------------------------------------------------

def test_k26_eksik_kolon_hata_verir():
    with pytest.raises(ValueError, match="eksik kolon"):
        gf.uygula(pd.DataFrame([{"assertion": "present"}]))


def test_k26_varlik_silinmiyor():
    """Filtre ELEMEZ, ETIKETLER - satir sayisi degismemeli."""
    girdi = pd.DataFrame([_varlik(), _varlik(temporality="prior"),
                          _varlik(assertion_rule="varsayilan_present")])
    assert len(gf.uygula(girdi)) == len(girdi)


def test_k26_surum_damgasi_var():
    d = _uygula(_varlik())
    assert d.at[0, "girdi_filtresi_surumu"] == gf.FILTRE_SURUMU


def test_k26_ozet_tutarli():
    d = _uygula(_varlik(), _varlik(temporality="prior"))
    o = gf.ozet(d)
    assert o["toplam_varlik"] == 2
    assert o["dusuk_guven"] == 1
    assert o["suphe_yukseltebilir"] == 1
    assert o["kural_basina"]["F1_gecmis_bulgu"] == 1


# --- K27: hata butcesi ilan edilmis olmali ---------------------------------

def test_k27_hata_butcesi_baglayici_karari_tasiyor():
    hb = gf.hata_butcesi()
    assert hb["K7_prior_F1_yuzde"] == 36.4
    assert "KARAR AGIRLIGI TASIMAZ" in hb["baglayici_karar"]
    assert "kalan_olculemez_risk" in hb, "olculemeyen risk acikca ilan edilmeli"


def test_k27_her_kural_dayanak_tasiyor():
    """Hicbir filtre kurali gerekcesiz olamaz (D27 disiplini)."""
    assert gf.KURALLAR, "kural listesi bos olamaz"
    for r in gf.KURALLAR:
        assert r.dayanak.strip(), f"{r.kod}: dayanak yok"
        assert "%" in r.dayanak, f"{r.kod}: dayanak olculmus bir sayiya atif yapmali"
