# -*- coding: utf-8 -*-
"""A3 / TASK-08 sablon kolonlari testleri.

Kararlar: D3 (maskeleme kapsami), D4 (K=10), D9/D12 (Faz 1 negasyon yapmaz),
D11 (katalog yalnizca train'den).
"""
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SENT = ROOT / "data" / "processed" / "sentences.parquet"
REPS = ROOT / "data" / "processed" / "reports_study_level.parquet"


@pytest.fixture(scope="module")
def sent():
    df = pd.read_parquet(SENT)
    if "is_stock_phrasing" not in df.columns:
        pytest.skip("sablon kolonlari yok - once 06_apply_templates.py")
    return df


@pytest.fixture(scope="module")
def tmpl():
    return import_module("06_apply_templates")


@pytest.fixture(scope="module")
def split_map():
    r = pd.read_parquet(REPS, columns=["study_id", "patient_id", "split"])
    return r


# --- Kolon butunlugu ------------------------------------------------------

def test_beklenen_kolonlar_var(sent):
    for c in ["template_id_exact", "template_id_norm", "n_patients_train",
              "is_stock_phrasing", "has_technical_caveat", "pipeline_version"]:
        assert c in sent.columns, f"{c} kolonu yok"


def test_faz1_negasyon_siniflandirmasi_yapmiyor(sent):
    """D9/D12: negasyon ve normal/pozitif ayrimi Faz 2'ye tasindi.
    Faz 1 ciktisinda boyle bir kolon BULUNMAMALI."""
    yasak = [c for c in sent.columns if c in ("template_type", "is_negated", "negation")]
    assert not yasak, f"Faz 1'e ait olmayan kolon(lar) uretilmis: {yasak}"


def test_esik_tutarli(sent, tmpl):
    """D4: is_stock_phrasing tam olarak n_patients_train >= K olmali."""
    beklenen = sent.n_patients_train >= tmpl.K_ESIK
    assert (sent.is_stock_phrasing == beklenen).all()


def test_teknik_cekince_bool(sent):
    assert sent.has_technical_caveat.dtype == bool


def test_pipeline_surumu_tek(sent):
    assert sent.pipeline_version.nunique() == 1


# --- Normalizasyon ve kimlik ---------------------------------------------

def test_ayni_normalize_ayni_kimlik(sent):
    g = sent.groupby("template_id_norm")["n_patients_train"].nunique()
    assert (g == 1).all(), "Ayni sablon kimligi farkli hasta sayilari tasiyor"


def test_maskeleme_sayilari_kapsiyor(tmpl):
    """D3: sayilar maskelenir, anatomi ve taraf KORUNUR."""
    a = tmpl.normalize("There is a 5 mm nodule in the right upper lobe.")
    b = tmpl.normalize("There is a 12 mm nodule in the right upper lobe.")
    assert a == b, "Sayi maskeleme calismiyor"
    c = tmpl.normalize("There is a 5 mm nodule in the left upper lobe.")
    assert a != c, "Taraf bilgisi maskelenmis - D3'e aykiri"


def test_maskeleme_cok_eksenli_olcu(tmpl):
    assert tmpl.normalize("A 5x3 mm lesion.") == tmpl.normalize("A 12x8 mm lesion.")


# --- D11: katalog yalnizca train'den -------------------------------------

def test_valid_katalogu_kirletmiyor(sent, split_map, tmpl):
    """Yalnizca valid'de gecen bir kalip, n_patients_train=0 almali."""
    m = sent.merge(split_map, on="study_id", how="left")
    tr_kaliplar = set(m.loc[m.split == "train", "template_id_norm"])
    yalniz_valid = m[(m.split == "valid") & (~m.template_id_norm.isin(tr_kaliplar))]
    assert len(yalniz_valid) > 0, "test anlamsiz: yalnizca valid'de gecen kalip yok"
    assert (yalniz_valid.n_patients_train == 0).all()
    assert (~yalniz_valid.is_stock_phrasing).all(), "eslesmeyen valid cumlesi sablon isaretlenmis"


def test_hasta_bazinda_sayim_ust_sinir(sent, split_map):
    """n_patients_train, train hasta sayisini (20.000) asamaz."""
    n = split_map[split_map.split == "train"].patient_id.nunique()
    assert sent.n_patients_train.max() <= n


# --- Teknik cekince: negasyondan bagimsiz --------------------------------

def test_teknik_cekince_negasyondan_bagimsiz(tmpl):
    """Bir cumle hem teknik cekince hem klinik icerik tasiyabilir."""
    assert tmpl.teknik_cekince("The mediastinum could not be evaluated optimally "
                               "in the non-contrast examination.")
    assert tmpl.teknik_cekince("As far as can be seen; heart contour is normal.")
    # negasyon iceren ama teknik olmayan cumle isaretlenmemeli
    assert not tmpl.teknik_cekince("No enlarged lymph nodes were detected.")
    assert not tmpl.teknik_cekince("Trachea, both main bronchi are open.")


# --- Kabul olcutu ---------------------------------------------------------

def test_kapsama_olcutu_saglandi(sent, split_map, tmpl):
    """Onceden yazilan olcut: elle dogrulanacak ilk N sablon, train
    cumlelerinin >= %50'sini kapsamali."""
    m = sent.merge(split_map, on="study_id", how="left")
    tr = m[m.split == "train"]
    ust = (tr[tr.is_stock_phrasing].groupby("template_id_norm").size()
           .sort_values(ascending=False).head(tmpl.ELLE_ETIKET_N))
    kapsama = ust.sum() / len(tr)
    assert kapsama >= 0.50, f"kapsama %{100*kapsama:.1f} - olcut saglanmadi"
