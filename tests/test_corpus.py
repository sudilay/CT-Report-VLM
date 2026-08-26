# -*- coding: utf-8 -*-
"""TASK-06 korpus dogrulama testleri.

Calistirma:  .venv/Scripts/python.exe -m pytest tests/ -v
"""
import csv
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ct_rate"
PARQ = ROOT / "data" / "processed" / "reports_study_level.parquet"

LABELS = ['Medical material', 'Arterial wall calcification', 'Cardiomegaly', 'Pericardial effusion',
          'Coronary artery wall calcification', 'Hiatal hernia', 'Lymphadenopathy', 'Emphysema',
          'Atelectasis', 'Lung nodule', 'Lung opacity', 'Pulmonary fibrotic sequela', 'Pleural effusion',
          'Mosaic attenuation pattern', 'Peribronchial thickening', 'Consolidation', 'Bronchiectasis',
          'Interlobular septal thickening']


@pytest.fixture(scope="module")
def df():
    return pd.read_parquet(PARQ)


@pytest.fixture(scope="module")
def nochest():
    out = set()
    for f in ["no_chest_train.txt", "no_chest_valid.txt"]:
        for ln in (RAW / f).read_text().splitlines():
            if ln.strip():
                out.add(ln.strip().split("/")[-1])
    return out


# --- Buyukluk ve kimlik -------------------------------------------------

def test_yayinlanan_sayilarla_ortusuyor(df):
    """CT-RATE yayini 25.692 calisma / 21.304 hasta bildiriyor."""
    assert len(df) == 25_692
    assert df["patient_id"].nunique() == 21_304


def test_study_id_benzersiz(df):
    assert df["study_id"].is_unique, "Ayni calisma birden fazla satirda"


def test_volume_name_benzersiz(df):
    assert df["VolumeName"].is_unique


def test_kimlik_alanlari_volumename_ile_tutarli(df):
    """patient_id / study_id gercekten VolumeName'den mi tureniyor."""
    stem = df["VolumeName"].str.replace(".nii.gz", "", regex=False)
    p = stem.str.split("_", expand=True)
    assert (df["patient_id"] == p[0] + "_" + p[1]).all()
    assert (df["study_id"] == p[0] + "_" + p[1] + "_" + p[2]).all()
    assert (df["recon_id"] == p[3]).all()


# --- Sizinti -------------------------------------------------------------

def test_hasta_sizintisi_yok(df):
    """Hicbir hasta hem train hem valid kumesinde olmamali."""
    tr = set(df.loc[df["split"] == "train", "patient_id"])
    va = set(df.loc[df["split"] == "valid", "patient_id"])
    assert not (tr & va), f"{len(tr & va)} hasta iki kumede birden"


def test_kumeler_arasi_metin_tekrari_bilinen_sinirda(df):
    """CT-RATE'in kendi split'inde, farkli hastalara ait 46 rapor metni birebir ayni.

    Bu bir isleme hatasi degil, verinin ozelligi: tamamen normal toraks BT'ler
    kelimesi kelimesine ayni sablon raporu uretiyor (bkz. sablon cumle orani %75).
    Hasta duzeyinde sizinti YOKTUR - test_hasta_sizintisi_yok ayrica dogruluyor.
    Olculen sinir asilirsa isleme mantiginda bir sey degismis demektir.
    """
    tr = set(df.loc[df["split"] == "train", "report_text"])
    va = set(df.loc[df["split"] == "valid", "report_text"])
    ortak = tr & va
    assert len(ortak) == 46, f"beklenen 46 ortak metin, bulunan {len(ortak)}"

    etkilenen = df[(df["split"] == "valid") & (df["report_text"].isin(ortak))]
    assert len(etkilenen) == 93
    assert len(etkilenen) / (df["split"] == "valid").sum() < 0.07


def test_kumeler_arasi_tekrar_eden_raporlar_negatif(df):
    """Tekrar eden metinler 'tamamen normal' raporlar olmali.

    Bunlarin buyuk cogunlugunun pozitif etiketi bulunmamasi, tekrarin
    malignite metriklerini sismesine yol acmadigini gosterir. Oran duserse
    tekrar eden raporlar artik zararsiz sayilamaz.
    """
    tr = set(df.loc[df["split"] == "train", "report_text"])
    va = set(df.loc[df["split"] == "valid", "report_text"])
    etkilenen = df[(df["split"] == "valid") & (df["report_text"].isin(tr & va))]
    etiketsiz_oran = (etkilenen[LABELS].sum(axis=1) == 0).mean()
    assert etiketsiz_oran > 0.85, f"tekrar eden raporlarin yalnizca %{100*etiketsiz_oran:.0f}'i etiketsiz"


# --- Gogus disi taramalar ------------------------------------------------

def test_gogus_disi_taramalar_korpusta_yok(df, nochest):
    kalan = set(df["VolumeName"]) & nochest
    assert not kalan, f"{len(kalan)} gogus disi tarama korpusta kalmis"


def test_tamamen_gogus_disi_calisma_kalmadi(nochest, df):
    """Tum rekonstruksiyonlari beyin taramasi olan calisma korpusta olmamali."""
    csv.field_size_limit(10 ** 7)
    ham = pd.read_csv(RAW / "train_reports.csv", usecols=["VolumeName"])
    ham["study_id"] = ham["VolumeName"].str.replace(".nii.gz", "", regex=False).str.split("_").str[:3].str.join("_")
    ham["nc"] = ham["VolumeName"].isin(nochest)
    tam_nc = ham.groupby("study_id")["nc"].all()
    tamamen = set(tam_nc[tam_nc].index)
    kalan = tamamen & set(df["study_id"])
    assert not kalan, f"{len(kalan)} tamamen beyin taramasi olan calisma korpusta"


# --- Tekillestirmenin dogrulugu -----------------------------------------

def test_tekillestirme_bilgi_kaybetmiyor(df):
    """Ayni calismanin tum rekonstruksiyonlari ayni raporu tasiyor olmali;
    aksi halde tekillestirme bilgi kaybina yol acardi."""
    csv.field_size_limit(10 ** 7)
    ham = pd.read_csv(RAW / "train_reports.csv", usecols=["VolumeName", "Findings_EN", "Impressions_EN"])
    ham["study_id"] = ham["VolumeName"].str.replace(".nii.gz", "", regex=False).str.split("_").str[:3].str.join("_")
    farkli = ham.groupby("study_id")[["Findings_EN", "Impressions_EN"]].nunique().max(axis=1)
    assert (farkli <= 1).all(), f"{(farkli > 1).sum()} calismada rekonstruksiyonlar farkli rapor tasiyor"


def test_korunan_rapor_ham_veriyle_ayni(df):
    """Parquet'teki Findings, ham CSV'deki ayni VolumeName kaydiyla birebir ayni olmali."""
    ham = pd.read_csv(RAW / "validation_reports.csv", usecols=["VolumeName", "Findings_EN"])
    m = df[df["split"] == "valid"].merge(ham, on="VolumeName", suffixes=("_p", "_h"))
    assert len(m) == (df["split"] == "valid").sum()
    assert (m["Findings_EN_p"].str.strip() == m["Findings_EN_h"].fillna("").str.strip()).all()


# --- Birlestirme butunlugu ----------------------------------------------

def test_etiketler_eksiksiz_birlesti(df):
    eksik = df[LABELS].isna().sum().sum()
    assert eksik == 0, f"{eksik} etiket hucresi bos"


def test_etiketler_ikili_deger(df):
    for c in LABELS:
        assert set(df[c].unique()) <= {0, 1}, f"{c} 0/1 disi deger iceriyor"


def test_metadata_birlesti(df):
    for c in ["Manufacturer", "NumberofSlices", "ZSpacing"]:
        assert df[c].notna().all(), f"{c} icinde bos deger var"


# --- Metin butunlugu -----------------------------------------------------

def test_report_text_bilesenlerden_olusuyor(df):
    yeniden = (df["Findings_EN"] + "\n\n" + df["Impressions_EN"]).str.strip()
    assert (df["report_text"] == yeniden).all()


def test_bos_rapor_sayisi_beklenen(df):
    assert (df["Findings_EN"] == "").sum() <= 1
    assert (df["Impressions_EN"] == "").sum() <= 14


def test_hicbir_rapor_tamamen_bos_degil(df):
    assert (df["report_text"].str.len() > 0).all()


# --- Impression'i olmayan calismalar -------------------------------------

def test_impression_is_null_kolonu_var(df):
    assert "impression_is_null" in df.columns
    assert df["impression_is_null"].dtype == bool


def test_impression_is_null_dogru_sayida(df):
    """811 calisma "Not given." yaziyor, 14 tanesi tamamen bos -> 825."""
    assert df["impression_is_null"].sum() == 825
    assert (df["Impressions_EN"] == "").sum() == 14


def test_impression_is_null_report_text_degistirmedi(df):
    """D10: isaretleme yapildi ama report_text'e DOKUNULMADI."""
    yeniden = (df["Findings_EN"] + "\n\n" + df["Impressions_EN"]).str.strip()
    assert (df["report_text"] == yeniden).all()
    bos = df[df["impression_is_null"] & (df["Impressions_EN"] != "")]
    assert (bos["Impressions_EN"].str.strip().str.lower() == "not given.").all()
