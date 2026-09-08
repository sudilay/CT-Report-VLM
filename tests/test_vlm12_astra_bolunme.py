"""SUDE-VLM-12 - Astra kohortu bolunme kilidinin degismezleri.

scripts/59_astra_kohort_bolunmesi.py'nin urettigi kilidi denetler. TASK-16'nin
K17/K18 degismezlerinin (tests/test_task16_bolunme.py) Astra kohortundaki
karsiligidir.

Kilit veya kaynak yoksa testler ATLANIR.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

KOK = Path(__file__).resolve().parent.parent
KILIT_YOLU = KOK / "configs/splits_astra.json"
KAYNAK_YOLU = KOK / "astra_radiology_reports_with_labels_all.xlsx"

BEKLENEN_TOHUM = 20260907
BEKLENEN_ORAN = 0.15
# Onceden ilan edildi (D100) - sonuc gorulmeden yazildi
BEKLENEN_PID = {"train": 838, "dev": 180, "held_out": 180}
BEKLENEN_POZITIF_PID = {"train": 50, "dev": 11, "held_out": 11}
KUMELER = ("train", "dev", "held_out")


def _sha(kimlikler) -> str:
    h = hashlib.sha256()
    for m in sorted(kimlikler):
        h.update(str(m).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


@pytest.fixture(scope="module")
def kilit() -> dict:
    if not KILIT_YOLU.exists():
        pytest.skip("astra bolunme kilidi uretilmemis (scripts/59)")
    return json.loads(KILIT_YOLU.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def kohort() -> pd.DataFrame:
    if not KAYNAK_YOLU.exists():
        pytest.skip("astra kaynak dosyasi yok")
    d = pd.read_excel(KAYNAK_YOLU, usecols=["PID", "Seri_Anahtari", "Kanser_Etiketi_y", "Censor_Time"])
    d["PID"] = d["PID"].astype(str)
    return d


@pytest.fixture(scope="module")
def listeler(kilit) -> dict:
    return {ad: set(kilit["bolunme"][ad]["pid_listesi"]) for ad in KUMELER}


# --- sizinti yok ------------------------------------------------------------

def test_hicbir_pid_iki_kumede_degil(listeler):
    for i, a in enumerate(KUMELER):
        for b in KUMELER[i + 1:]:
            ortak = listeler[a] & listeler[b]
            assert not ortak, f"{a} ve {b} ortak PID tasiyor: {sorted(ortak)[:5]}"


def test_hicbir_seri_iki_kumede_degil(kohort, listeler):
    """PID duzeyi ayirmanin seri duzeyine dogru tasindigini dogrular."""
    d = kohort.copy()
    d["kume"] = d["PID"].map({p: ad for ad in KUMELER for p in listeler[ad]})
    taraf = d.dropna(subset=["kume"]).groupby("Seri_Anahtari")["kume"].nunique()
    bozuk = taraf[taraf > 1]
    assert bozuk.empty, f"iki kumeye birden dusen seri: {bozuk.index[:5].tolist()}"


def test_kapsama_tam(kohort, kilit, listeler):
    """Filtre sonrasi her PID tam olarak bir kumede; kaybolan PID yok."""
    kalan = kohort[~((kohort["Censor_Time"] < 1) & (kohort["Kanser_Etiketi_y"] == 0))]
    tum = set(kalan["PID"])
    birlesim = set().union(*listeler.values())
    assert birlesim == tum
    assert len(tum) == kilit["kaynak"]["filtre_sonrasi_pid"] == 1198


# --- filtre bildirdigini yapmis --------------------------------------------

def test_filtre_dogru_uygulandi(kohort, kilit):
    dis = kohort[(kohort["Censor_Time"] < 1) & (kohort["Kanser_Etiketi_y"] == 0)]
    assert len(dis) == kilit["filtre"]["dislanan_seri"] == 25
    assert sorted(str(s) for s in dis["Seri_Anahtari"]) == kilit["filtre"]["dislanan_seri_anahtarlari"]


def test_kanserli_seriler_filtreden_etkilenmedi(kohort, kilit):
    """Kanserli seri sayisi filtreden once ve sonra ayni olmali."""
    toplam_poz_seri = sum(kilit["bolunme"][ad]["pozitif_seri"] for ad in KUMELER)
    assert toplam_poz_seri == int(kohort["Kanser_Etiketi_y"].sum()) == 140


# --- onceden ilan edilen sayilar tuttu --------------------------------------

def test_kume_boyutlari_ilan_edilen(kilit):
    for ad in KUMELER:
        assert kilit["bolunme"][ad]["pid"] == BEKLENEN_PID[ad], f"{ad} PID sayisi ilan edilenden farkli"


def test_pozitif_pid_sayilari_ilan_edilen(kilit):
    for ad in KUMELER:
        assert kilit["bolunme"][ad]["pozitif_pid"] == BEKLENEN_POZITIF_PID[ad]


def test_held_out_orani_ilan_edilen(kilit):
    toplam = sum(kilit["bolunme"][ad]["pid"] for ad in KUMELER)
    assert kilit["bolunme"]["held_out"]["pid"] == round(toplam * BEKLENEN_ORAN)
    assert kilit["oranlar"]["held_out"] == BEKLENEN_ORAN


def test_tohum_ilan_edilen(kilit):
    assert kilit["tohum"] == BEKLENEN_TOHUM


def test_esik_sinanamaz_ilani_korunuyor(kilit):
    """D100: held-out ile duyarlilik esigi SINANAMAZ - bu ilan degistirilemez."""
    assert kilit["onceden_ilan"]["esik_sinanabilir_mi"] is False
    assert kilit["onceden_ilan"]["beklenen_held_out_pozitif_pid"] == 11


# --- karma PID kurali -------------------------------------------------------

def test_karma_pid_max_kurali(kohort, kilit, listeler):
    """3 karma PID kanserli sayilmis ve tam olarak bir kumede olmali."""
    g = kohort.groupby("PID")["Kanser_Etiketi_y"].nunique()
    karma = set(g[g > 1].index)
    assert karma == set(kilit["karma_pid_kurali"]["etkilenen_pid"])
    for p in karma:
        assert sum(p in listeler[ad] for ad in KUMELER) == 1


# --- kilit kendi icinde tutarli ---------------------------------------------

def test_hashler_listelerle_tutarli(kilit):
    for ad in KUMELER:
        b = kilit["bolunme"][ad]
        assert _sha(b["pid_listesi"]) == b["sha256"], f"{ad} hash tutmuyor"
        assert len(b["pid_listesi"]) == b["pid"]
        assert len(set(b["pid_listesi"])) == b["pid"], f"{ad} listesinde tekrar var"
