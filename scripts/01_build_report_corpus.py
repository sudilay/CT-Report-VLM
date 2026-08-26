"""T-01: CT-RATE raporlarindan analize hazir, tekillestirilmis calisma duzeyi korpus uretir.

Yaptiklari:
  1. train/validation raporlarini yukler
  2. VolumeName -> (hasta, calisma, rekonstruksiyon) olarak ayristirir
  3. Ayni calismanin tekrarlanan rekonstruksiyonlarini tekillestirir (rapor metni ayni)
  4. Gogus disi (beyin) taramalari no_chest listeleriyle atar
  5. 18 anormallik etiketini ve secili metadatayi birlestirir
  6. data/processed/reports_study_level.parquet olarak yazar

Kullanim:  .venv/Scripts/python.exe scripts/01_build_report_corpus.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ct_rate"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

META_KEEP = ["VolumeName", "PatientSex", "PatientAge", "StudyDate",
             "Manufacturer", "SliceLocation", "NumberofSlices", "ZSpacing"]


def parse_volume_name(s: pd.Series) -> pd.DataFrame:
    """'train_1267_a_4.nii.gz' -> split/patient/study/recon."""
    stem = s.str.replace(".nii.gz", "", regex=False)
    parts = stem.str.split("_", expand=True)
    return pd.DataFrame({
        "split_tag": parts[0],
        "patient_id": parts[0] + "_" + parts[1],
        "study_id": parts[0] + "_" + parts[1] + "_" + parts[2],
        "recon_id": parts[3],
    }, index=s.index)


def load_split(split: str) -> pd.DataFrame:
    rep_f = "train_reports.csv" if split == "train" else "validation_reports.csv"
    lab_f = "train_predicted_labels.csv" if split == "train" else "valid_predicted_labels.csv"
    met_f = "train_metadata.csv" if split == "train" else "validation_metadata.csv"
    nochest_f = "no_chest_train.txt" if split == "train" else "no_chest_valid.txt"

    rep = pd.read_csv(RAW / rep_f)
    rep = pd.concat([rep, parse_volume_name(rep["VolumeName"])], axis=1)
    rep["split"] = split
    n0 = len(rep)

    # 1) gogus disi taramalari at
    nochest = {ln.strip().split("/")[-1] for ln in (RAW / nochest_f).read_text().splitlines() if ln.strip()}
    rep = rep[~rep["VolumeName"].isin(nochest)]
    n_nochest = n0 - len(rep)

    # 2) calisma duzeyinde tekillestir (ayni calismanin raporu ayni)
    rep = rep.sort_values("recon_id").drop_duplicates(subset="study_id", keep="first")

    # 3) etiket + metadata birlestir (volume duzeyinde -> temsilci volume uzerinden)
    lab = pd.read_csv(RAW / lab_f)
    met = pd.read_csv(RAW / met_f, usecols=lambda c: c in META_KEEP, low_memory=False)
    rep = rep.merge(lab, on="VolumeName", how="left").merge(met, on="VolumeName", how="left")

    print(f"[{split}] hacim={n0} -> gogus-disi atilan={n_nochest} -> calisma={len(rep)} "
          f"| hasta={rep['patient_id'].nunique()}")
    return rep


def main() -> None:
    df = pd.concat([load_split("train"), load_split("valid")], ignore_index=True)

    for col in ["Findings_EN", "Impressions_EN", "ClinicalInformation_EN", "Technique_EN"]:
        df[col] = df[col].fillna("").str.strip()
    df["report_text"] = (df["Findings_EN"] + "\n\n" + df["Impressions_EN"]).str.strip()
    df["n_char"] = df["report_text"].str.len()

    out = OUT / "reports_study_level.parquet"
    df.to_parquet(out, index=False)
    print(f"\nyazildi: {out}  ({len(df)} calisma, {df['patient_id'].nunique()} hasta)")
    print(f"bos Findings: {(df['Findings_EN'] == '').sum()} | bos Impressions: {(df['Impressions_EN'] == '').sum()}")
    print(f"rapor uzunlugu (karakter) medyan={df['n_char'].median():.0f} p95={df['n_char'].quantile(.95):.0f}")


if __name__ == "__main__":
    main()
