"""TASK-16 Adim 4 - kilitli takimlarin degismezleri.

Plan: docs/29 §8.1 ve §8.3

Bu testler, sinir vakasi ve negatif kontrol takimlarinin kilitlendikten SONRA
degistirilmedigini otomatik denetler. Sema yazilirken vaka eklenip cikarilirsa
kabul olcutu anlamini yitirir (docs/32 bulgu #3).

Kilit yoksa testler ATLANIR.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

KOK = Path(__file__).resolve().parent.parent
MANIFEST = KOK / "configs/sema_takim_kilidi.json"
KILIT_BOLUNME = KOK / "configs/splits_holdout.json"
MARUZIYET = KOK / "reports/task16_maruziyet_kaydi.json"
KORPUS = KOK / "data/processed/reports_study_level.parquet"

MALIGN_URETIR = {"low", "indeterminate", "intermediate", "high", "known_malignancy"}
GECERLI_SINIF = MALIGN_URETIR | {"None", "not_mentioned"}

# UYARI: olcegin "None" degeri pandas'in varsayilan NA listesindedir. Bu
# dosyalar HER ZAMAN keep_default_na=False ile okunmalidir, yoksa "None" hedefi
# bos hucre sanilir. (Adim 4'te bulundu.)


@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST.exists():
        pytest.skip("takim kilidi uretilmemis (scripts/45)")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sinir(manifest) -> pd.DataFrame:
    return pd.read_csv(KOK / manifest["sinir_takimi"]["dosya"], keep_default_na=False)


@pytest.fixture(scope="module")
def kontrol(manifest) -> pd.DataFrame:
    return pd.read_csv(KOK / manifest["kontrol_takimi"]["dosya"], keep_default_na=False)


# --- K19: takim kilitten sonra degismedi ------------------------------------

@pytest.mark.parametrize("ad", ["sinir_takimi", "kontrol_takimi"])
def test_k19_takim_hash_tutuyor(manifest, ad):
    """Dosyanin sha256'si manifestteki degerle ayni olmali."""
    yol = KOK / manifest[ad]["dosya"]
    assert yol.exists(), f"{ad} dosyasi yok"
    su = hashlib.sha256(yol.read_bytes()).hexdigest()
    assert su == manifest[ad]["sha256"], (
        f"{ad} KILITLENDIKTEN SONRA DEGISMIS. Kilitli takim degistirilemez; "
        "kural takimi gecemezse KURAL degisir (docs/29 §8.1/4)."
    )


@pytest.mark.parametrize("ad", ["sinir_takimi", "kontrol_takimi"])
def test_k19_vaka_sayisi_sabit(manifest, ad):
    yol = KOK / manifest[ad]["dosya"]
    assert len(pd.read_csv(yol, keep_default_na=False)) == manifest[ad]["vaka"]


# --- K20: takim ic tutarliligi ----------------------------------------------

def test_k20_her_vakanin_hedefi_var(sinir, kontrol):
    for ad, d in (("sinir", sinir), ("kontrol", kontrol)):
        bos = d[d["hedef_sinif"].isna() | (d["hedef_sinif"].astype(str).str.strip() == "")]
        assert bos.empty, f"{ad}: hedefsiz vaka {bos['vaka_id'].tolist()}"
        assert d["hedef_kaynagi"].notna().all(), f"{ad}: dayanaksiz hedef var"
        assert d["hedef_gerekcesi"].notna().all(), f"{ad}: gerekcesiz hedef var"


def test_k20_hedefler_gecerli_sinif(sinir, kontrol):
    for ad, d in (("sinir", sinir), ("kontrol", kontrol)):
        gecersiz = set(d["hedef_sinif"]) - GECERLI_SINIF
        assert not gecersiz, f"{ad}: olcek disi hedef {gecersiz}"


def test_k20_vaka_id_benzersiz(sinir, kontrol):
    for ad, d in (("sinir", sinir), ("kontrol", kontrol)):
        assert d["vaka_id"].is_unique, f"{ad}: tekrarli vaka_id"


# --- K21: KORUMA KAPISI - kontrol takimi malignite uretmemeli ---------------

def test_k21_kontrol_takimi_malignite_uretmiyor(kontrol):
    """docs/29 §8.3 · toleranssiz kapi.

    Kontrol takimindaki hicbir vakanin HEDEFI malignite ureten bir duzey
    olamaz. (Semanin bu vakalarda ne urettigi adim 6'da sinanir; bu test
    takimin kendisinin gecerliligini korur.)
    """
    ihlal = kontrol[kontrol["hedef_sinif"].isin(MALIGN_URETIR)]
    assert ihlal.empty, (
        "KORUMA KAPISI BOZULDU: kontrol takiminda malignite ureten hedef var: "
        f"{ihlal['vaka_id'].tolist()}"
    )


def test_k21_kontrol_takimi_yeterli_buyuklukte(kontrol):
    """Plan en az 10 kontrol vakasi sart kosuyor (docs/29 §8.3)."""
    assert len(kontrol) >= 10, f"kontrol takimi {len(kontrol)} vaka, en az 10 olmali"


# --- K22: kapsam - takimlar gelistirme havuzundan ---------------------------

def test_k22_takimlar_kilit_disindan(sinir, kontrol):
    """Hicbir vaka degerlendirme kilidinden veya maruz hastalardan gelmemeli."""
    if not (KILIT_BOLUNME.exists() and MARUZIYET.exists() and KORPUS.exists()):
        pytest.skip("bolunme kilidi / maruziyet kaydi / korpus yok")
    kb = json.loads(KILIT_BOLUNME.read_text(encoding="utf-8"))["degerlendirme_kilidi"]
    yasak = set(kb["a_ctrate_valid"]["hasta_listesi"]) | set(kb["b_train_kilit"]["hasta_listesi"])
    mar = json.loads(MARUZIYET.read_text(encoding="utf-8"))
    yasak |= {h for r in mar["kayitlar"] for h in r["kilitteki_hasta_listesi"]}

    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    esleme = dict(zip(k["study_id"], k["patient_id"]))
    for ad, d in (("sinir", sinir), ("kontrol", kontrol)):
        hastalar = {esleme.get(c) for c in d["study_id"]} - {None}
        sizan = hastalar & yasak
        assert not sizan, f"{ad}: kilitli/maruz hastadan vaka alinmis: {sorted(sizan)}"
