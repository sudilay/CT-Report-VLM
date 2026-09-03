"""TASK-16 Adim 0 - bolunme kilidinin degismezleri.

Plan: docs/29_task16_calisma_plani.md §4.3

Bu testler, sema/sozluk gelistirmesinin degerlendirme havuzunu KIRLETMEDIGINI
otomatik olarak denetler. TASK-14'teki K16 degismezinin muadilidir.

Kilit dosyasi yoksa testler ATLANIR (skip) - boylece kilit uretilmemis bir
calisma agacinda test takimi kirmiz olmaz.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

KOK = Path(__file__).resolve().parent.parent
KILIT_YOLU = KOK / "configs/splits_holdout.json"
KORPUS_YOLU = KOK / "data/processed/reports_study_level.parquet"

BEKLENEN_TOHUM = 20260903
BEKLENEN_ORAN = 0.15


def _sha(metinler) -> str:
    h = hashlib.sha256()
    for m in sorted(metinler):
        h.update(m.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


@pytest.fixture(scope="module")
def kilit() -> dict:
    if not KILIT_YOLU.exists():
        pytest.skip("bolunme kilidi uretilmemis (scripts/40)")
    return json.loads(KILIT_YOLU.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def korpus() -> pd.DataFrame:
    if not KORPUS_YOLU.exists():
        pytest.skip("korpus yok")
    return pd.read_parquet(KORPUS_YOLU, columns=["patient_id", "study_id", "split"])


@pytest.fixture(scope="module")
def kilitli_hastalar(kilit) -> set:
    dk = kilit["degerlendirme_kilidi"]
    return set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])


# --- K17: sizinti yok -------------------------------------------------------

def test_k17_kilit_parcalari_ayrik(kilit):
    """(a) ve (b) hicbir hastayi paylasmaz."""
    dk = kilit["degerlendirme_kilidi"]
    a = set(dk["a_ctrate_valid"]["hasta_listesi"])
    b = set(dk["b_train_kilit"]["hasta_listesi"])
    assert not (a & b), f"iki kilit parcasinda ortak hasta: {sorted(a & b)[:5]}"


def test_k17_gelistirme_ve_kilit_ayrik(kilit, korpus, kilitli_hastalar):
    """Gelistirme havuzundaki hicbir hasta kilitte olamaz."""
    tum = set(korpus["patient_id"].unique())
    gelistirme = tum - kilitli_hastalar
    assert not (gelistirme & kilitli_hastalar)
    assert len(gelistirme) == kilit["gelistirme_havuzu"]["hasta"]


def test_k17_kapsama_tam(kilit, korpus, kilitli_hastalar):
    """Kilit + gelistirme = butun hastalar. Kaybolan hasta yok."""
    tum = set(korpus["patient_id"].unique())
    assert kilitli_hastalar <= tum, "kilitte korpusta olmayan hasta var"
    gelistirme = tum - kilitli_hastalar
    assert len(kilitli_hastalar) + len(gelistirme) == len(tum)
    assert len(tum) == kilit["kaynak"]["hasta"]


def test_k17_calisma_duzeyinde_sizinti_yok(korpus, kilitli_hastalar):
    """Hicbir CALISMA hem kilitte hem gelistirmede olamaz.

    Hasta duzeyinde ayirmanin calisma duzeyine dogru tasindigini dogrular:
    ayni hastanin butun calismalari ayni tarafta olmali.
    """
    korpus = korpus.copy()
    korpus["kilitte"] = korpus["patient_id"].isin(kilitli_hastalar)
    taraf_sayisi = korpus.groupby("study_id")["kilitte"].nunique()
    bozuk = taraf_sayisi[taraf_sayisi > 1]
    assert bozuk.empty, f"iki tarafa birden dusen calisma: {bozuk.index[:5].tolist()}"


# --- K18: kilit bildirdigi seyi tasiyor -------------------------------------

def test_k18_ctrate_valid_tam_alindi(kilit, korpus):
    """(a) CT-RATE'in resmi valid bolunmesinin TAMAMI kilitte olmali."""
    valid = set(korpus.loc[korpus["split"] == "valid", "patient_id"].unique())
    a = set(kilit["degerlendirme_kilidi"]["a_ctrate_valid"]["hasta_listesi"])
    assert a == valid, "resmi valid bolunmesi birebir alinmamis"


def test_k18_train_orani_ilan_edilen(kilit, korpus):
    """(b) train'den alinan pay ilan edilen %15 olmali."""
    train = korpus.loc[korpus["split"] == "train", "patient_id"].nunique()
    b = kilit["degerlendirme_kilidi"]["b_train_kilit"]["hasta"]
    assert b == round(train * BEKLENEN_ORAN)
    assert kilit["train_kilit_orani"] == BEKLENEN_ORAN


def test_k18_tohum_ilan_edilen(kilit):
    assert kilit["tohum"] == BEKLENEN_TOHUM, "tohum docs/29 §4.3'te ilan edilenden farkli"


def test_k18_hashler_listelerle_tutarli(kilit):
    """Dosyadaki sha256'lar, dosyadaki listelerin kendisinden uretilmis olmali."""
    dk = kilit["degerlendirme_kilidi"]
    for ad in ("a_ctrate_valid", "b_train_kilit"):
        assert _sha(dk[ad]["hasta_listesi"]) == dk[ad]["sha256"], f"{ad} hash tutmuyor"
        assert len(dk[ad]["hasta_listesi"]) == dk[ad]["hasta"]


def test_k18_gelistirme_hash_tutarli(kilit, korpus, kilitli_hastalar):
    """Gelistirme havuzunun hash'i korpustan yeniden uretilebilmeli."""
    tum = set(korpus["patient_id"].unique())
    gelistirme = tum - kilitli_hastalar
    assert _sha(gelistirme) == kilit["gelistirme_havuzu"]["sha256"]
