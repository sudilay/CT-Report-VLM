"""TASK-15 icin onaylanan 150-span kor `dev` pilotunu uretir.

Secim yalniz RadTr etiketi, sabit tohum ve belge basina ust sinir kullanir.
Span metni, sozluk/model eslesmesi veya skor secime girmez. RadTr test'e erisim
yoktur; kaynak yalniz daha once kilitlenmis `dev` kor paketidir.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation.task15 import (
    SCHEMA_VERSION,
    build_stratified_pilot,
    sha256_file,
    write_jsonl,
)

SOURCE = ROOT / "outputs" / "task15" / "dev_packages" / "normalization_blind_dev.jsonl"
CATALOG = ROOT / "configs" / "task15_kavram_katalogu.yaml"
GUIDE = ROOT / "docs" / "22_task15_kavram_normalizasyon_kilavuzu_taslak.md"
SEED = 20260901
MAX_PER_DOCUMENT = 5
QUOTAS = {
    "Obs_Anatomy": 40,
    "Obs_Present": 40,
    "Obs_Absent": 20,
    "Obs_Uncertain": 20,
    "Differential Diagnosis": 10,
    "Obs_Technical": 8,
    "Obs_Advice": 5,
    "Symptom_P": 7,
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def write_new_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not all(path.exists() for path in (SOURCE, CATALOG, GUIDE)):
        sys.exit("DURDU: dev kor paket/katalog/kilavuz eksik")

    source_rows = read_jsonl(SOURCE)
    pilot = build_stratified_pilot(source_rows, QUOTAS, MAX_PER_DOCUMENT, SEED)
    output_path = args.output_dir / "normalization_pilot_dev.jsonl"
    manifest_path = args.output_dir / "pilot_manifest_dev.json"
    checksums_path = args.output_dir / "pilot_checksums_dev.sha256"
    if any(path.exists() for path in (output_path, manifest_path, checksums_path)):
        sys.exit("DURDU: var olan pilot artefaktinin uzerine yazilmaz")

    write_jsonl(output_path, pilot)
    label_counts = Counter(row["radtr_label"] for row in pilot)
    document_counts = Counter(row["document_id"] for row in pilot)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "split": "dev",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection": "radtr_label_stratified_only",
        "seed": SEED,
        "max_per_document": MAX_PER_DOCUMENT,
        "quotas": QUOTAS,
        "records": len(pilot),
        "documents": len(document_counts),
        "min_spans_per_document": min(document_counts.values()),
        "max_spans_per_document": max(document_counts.values()),
        "label_counts": dict(sorted(label_counts.items())),
        "source": {
            "file": str(SOURCE.relative_to(ROOT)),
            "sha256": sha256_file(SOURCE),
        },
        "catalog": {
            "file": str(CATALOG.relative_to(ROOT)),
            "sha256": sha256_file(CATALOG),
        },
        "guide": {"file": str(GUIDE.relative_to(ROOT)), "sha256": sha256_file(GUIDE)},
        "pilot": {"file": output_path.name, "sha256": sha256_file(output_path)},
    }
    write_new_text(
        manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    write_new_text(
        checksums_path,
        f"{manifest['pilot']['sha256']}  {output_path.name}\n"
        f"{sha256_file(manifest_path)}  {manifest_path.name}\n",
    )

    print(f"pilot: {len(pilot)} span · {len(document_counts)} belge")
    print(
        f"belge basi: {min(document_counts.values())}-{max(document_counts.values())}"
    )
    for label, count in label_counts.most_common():
        print(f"  {label:<24} {count:>3}")
    print(f"pilot SHA-256: {manifest['pilot']['sha256']}")
    print(f"manifest SHA-256: {sha256_file(manifest_path)}")


if __name__ == "__main__":
    main()
