"""Kör TASK-15 pilot yargılarını kaynak satırlarla birleştirip kilitler.

Yargı dosyası yalnız ``span_id -> karar`` taşır. Kaynak metin bu dosyadan
alınmaz; kilit sırasında dondurulmuş kör paketle yeniden bağlanır ve tam kapsam,
kapalı kavram envanteri, değişmez kaynak alanları ve üzerine-yazmama denetlenir.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation.task15 import lock_annotation_output


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blind", type=Path, required=True)
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--annotator-id", required=True)
    args = parser.parse_args()

    blind = read_jsonl(args.blind)
    decisions = json.loads(args.judgments.read_text(encoding="utf-8"))
    if type(decisions) is not dict:
        sys.exit("DURDU: judgments kokte JSON nesnesi olmali")
    catalog = yaml.safe_load(args.catalog.read_text(encoding="utf-8"))
    inventory = frozenset(catalog["kavramlar"])

    blind_by_span = {row["span_id"]: row for row in blind}
    if len(blind_by_span) != len(blind):
        sys.exit("DURDU: kor pakette span_id tekil degil")
    if set(decisions) != set(blind_by_span):
        missing = set(blind_by_span) - set(decisions)
        extra = set(decisions) - set(blind_by_span)
        sys.exit(f"DURDU: yargi kapsam farki eksik={len(missing)} fazla={len(extra)}")

    rows = []
    for source in blind:
        decision = decisions[source["span_id"]]
        if set(decision) != {"concept_ids", "mapping_status", "note"}:
            sys.exit(f"DURDU: yargi alanlari gecersiz: {source['span_id']}")
        rows.append(
            {
                "document_id": source["document_id"],
                "span_id": source["span_id"],
                "sentence_text": source["sentence_text"],
                "span_text": source["span_text"],
                "radtr_label": source["radtr_label"],
                "concept_ids": decision["concept_ids"],
                "mapping_status": decision["mapping_status"],
                "annotator_id": args.annotator_id,
                "note": decision["note"],
            }
        )

    manifest = lock_annotation_output(
        rows, blind, args.output, inventory, args.annotator_id
    )
    print(
        f"kilitlendi: {manifest['records']} kayit · {manifest['sha256']} · "
        f"annotator={manifest['annotator_id']}"
    )


if __name__ == "__main__":
    main()
