"""TASK-15 dil ablasyonu icin kapali veri sozlesmeleri ve puanlama.

Bu modul saglayici SDK'si bilmez. Google/MedGemma ve ikincil model kosuculari
yalnizca asagidaki kucuk Protocol'leri uygular. Boylece paketleme, dogrulama ve
puanlama sentetik veriyle ve test bolumune dokunmadan sinanabilir.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import tempfile
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import yaml

ASSERTIONS = ("present", "absent", "uncertain")
MAPPING_STATUSES = ("mapped", "unmapped", "needs_adjudication")
DEVELOPMENT_SPLITS = ("train", "dev")
SCHEMA_VERSION = "task15-1.0"


class ContractError(ValueError):
    """Girdi veya cikti dondurulmus TASK-15 sozlesmesine uymuyor."""


class TranslationAdapter(Protocol):
    name: str

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        """Tek tam belgeyi cevir; bos veya aciklamali cikti verme."""


class SecondaryModelAdapter(Protocol):
    name: str

    def generate(self, text: str, prompt: str) -> str:
        """Kapali JSON sozlesmesinde ham model yaniti uret."""


def load_inventory(path: Path, expected_count: int = 144) -> frozenset[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    try:
        concepts = data["yuzeyler"]
    except (KeyError, TypeError) as exc:
        raise ContractError("Envanterde 'yuzeyler' nesnesi yok") from exc
    if not isinstance(concepts, dict) or not concepts:
        raise ContractError("Envanter bos veya gecersiz")
    if len(concepts) != expected_count:
        raise ContractError(
            f"Dondurulmus envanter {expected_count} kavram olmali; bulunan={len(concepts)}"
        )
    return frozenset(concepts)


def require_development_split(split: str) -> None:
    if split not in DEVELOPMENT_SPLITS:
        raise ContractError(
            f"DURDU: {split!r} gelistirme bolumu degil; TASK-15 test paketi "
            "ayri ve tek kullanimlik komutla acilacak"
        )


def _exact_keys(value: object, expected: set[str], label: str) -> dict:
    if type(value) is not dict:
        raise ContractError(f"{label} JSON nesnesi olmali")
    keys = set(value)
    if keys != expected:
        raise ContractError(
            f"{label} alanlari kapali sozlesmeye uymuyor: "
            f"eksik={sorted(expected - keys)}, fazla={sorted(keys - expected)}"
        )
    return value


def parse_model_output(raw: str, inventory: frozenset[str]) -> list[dict[str, str]]:
    """Markdown/onarim kabul etmeden ikincil model JSON'unu dogrula."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractError(f"Model cikisi dogrudan JSON degil: {exc.msg}") from exc
    payload = _exact_keys(payload, {"findings"}, "model cikisi")
    if type(payload["findings"]) is not list:
        raise ContractError("findings liste olmali")

    findings, gorulen = [], set()
    for index, finding in enumerate(payload["findings"]):
        finding = _exact_keys(
            finding, {"concept_id", "assertion"}, f"findings[{index}]"
        )
        concept_id, assertion = finding["concept_id"], finding["assertion"]
        if type(concept_id) is not str or concept_id not in inventory:
            raise ContractError(f"findings[{index}] envanter disi concept_id")
        if type(assertion) is not str or assertion not in ASSERTIONS:
            raise ContractError(f"findings[{index}] gecersiz assertion")
        # Tekrarli ciftler REDDEDILIR. Puanlayici kume kullandigi icin sessizce
        # tekillestirilirse modelin yapisal hatasi gizlenir (docs/24 §6.3).
        if (concept_id, assertion) in gorulen:
            raise ContractError(
                f"findings[{index}] tekrarli (concept_id, assertion): "
                f"{concept_id}/{assertion}"
            )
        gorulen.add((concept_id, assertion))
        findings.append({"concept_id": concept_id, "assertion": assertion})
    return findings


def run_translation(
    documents: Sequence[Mapping],
    adapter: TranslationAdapter,
    source_language: str = "tr",
    target_language: str = "en",
) -> list[dict]:
    """Kimlik ve sirayi koruyarak tam belge cevirisi yap."""
    output, seen = [], set()
    for expected_order, document in enumerate(documents):
        _exact_keys(
            dict(document), {"document_id", "order", "text_tr"}, "ceviri girdisi"
        )
        if document["order"] != expected_order:
            raise ContractError("Ceviri girdisi sirasi kesintisiz degil")
        if document["document_id"] in seen:
            raise ContractError("Ceviri girdisinde tekrarli document_id")
        seen.add(document["document_id"])
        if type(document["text_tr"]) is not str or not document["text_tr"].strip():
            raise ContractError("Ceviri girdisinde bos metin")
        translated = adapter.translate(
            document["text_tr"], source_language, target_language
        )
        if type(translated) is not str or not translated.strip():
            raise ContractError(f"Bos ceviri: {document['document_id']}")
        output.append(
            {
                "document_id": document["document_id"],
                "order": expected_order,
                "text": translated,
                "adapter": adapter.name,
            }
        )
    return output


def run_secondary_model(
    documents: Sequence[Mapping],
    adapter: SecondaryModelAdapter,
    prompt: str,
    inventory: frozenset[str],
) -> list[dict]:
    """Ham yaniti onarmadan dogrula; tek hata tum kosuyu gorunur bicimde durdurur."""
    output, seen = [], set()
    for expected_order, document in enumerate(documents):
        document = _exact_keys(
            dict(document), {"document_id", "order", "text"}, "model girdisi"
        )
        if document["order"] != expected_order:
            raise ContractError("Model girdisi sirasi kesintisiz degil")
        if document["document_id"] in seen:
            raise ContractError("Model girdisinde tekrarli document_id")
        seen.add(document["document_id"])
        if type(document["text"]) is not str or not document["text"].strip():
            raise ContractError("Model girdisinde bos metin")
        raw = adapter.generate(document["text"], prompt)
        output.append(
            {
                "document_id": document["document_id"],
                "order": expected_order,
                "findings": parse_model_output(raw, inventory),
                "adapter": adapter.name,
                "raw_response": raw,
            }
        )
    return output


def _sentence_for_span(text: str, token_start: int, token_end: int) -> str:
    tokens = text.split()
    if not (0 <= token_start <= token_end < len(tokens)):
        raise ContractError("Span token ofseti belge siniri disinda")
    starts, position = [], 0
    for token in tokens:
        starts.append(position)
        position += len(token) + 1
    char_start = starts[token_start]
    char_end = starts[token_end] + len(tokens[token_end])
    left = max(text.rfind(".", 0, char_start), text.rfind(";", 0, char_start)) + 1
    rights = [x for x in (text.find(".", char_end), text.find(";", char_end)) if x >= 0]
    right = min(rights) + 1 if rights else len(text)
    return text[left:right].strip()


def build_package_records(
    documents: Sequence[Mapping],
    split: str,
) -> tuple[list[dict], list[dict]]:
    """Ayni kaynak gecisinden altinsiz ceviri ve tahminsiz kor paketleri kur."""
    require_development_split(split)
    translation, normalization, seen = [], [], set()
    for order, document in enumerate(documents):
        required = {"belge_id", "kaynak_bolum", "metin", "varliklar"}
        missing = required - set(document)
        if missing:
            raise ContractError(f"RadTr kaydinda eksik alan: {sorted(missing)}")
        if document["kaynak_bolum"] != split:
            raise ContractError("Paket girdisinde bolum karisimi var")
        document_id = document["belge_id"]
        if type(document_id) is not str or not document_id or document_id in seen:
            raise ContractError("Belge kimligi bos veya tekrarli")
        seen.add(document_id)
        text = document["metin"]
        if type(text) is not str or not text.strip():
            raise ContractError(f"Bos belge metni: {document_id}")
        if type(document["varliklar"]) is not list:
            raise ContractError(f"varliklar liste degil: {document_id}")
        translation.append(
            {"document_id": document_id, "order": order, "text_tr": text}
        )

        for span_order, span in enumerate(document["varliklar"]):
            for field in ("metin", "radtr_etiket", "tok_bas", "tok_son"):
                if field not in span:
                    raise ContractError(f"RadTr span'inda eksik alan: {field}")
            if any(type(span[field]) is not int for field in ("tok_bas", "tok_son")):
                raise ContractError("RadTr span token ofsetleri tam sayi olmali")
            normalization.append(
                {
                    "document_id": document_id,
                    "span_id": f"{document_id}:s{span_order:04d}",
                    "document_order": order,
                    "span_order": span_order,
                    "sentence_text": _sentence_for_span(
                        text, span["tok_bas"], span["tok_son"]
                    ),
                    "span_text": span["metin"],
                    "radtr_label": span["radtr_etiket"],
                }
            )
    return translation, normalization


def _atomic_text(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"Kilitli artefaktin uzerine yazilmaz: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def write_jsonl(path: Path, records: Iterable[Mapping]) -> None:
    text = "".join(
        json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    _atomic_text(path, text)


def _canonical_records_hash(records: Sequence[Mapping]) -> str:
    payload = "".join(
        json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_translation_package(records: Sequence[Mapping]) -> list[dict]:
    output, seen = [], set()
    for order, original in enumerate(records):
        row = _exact_keys(
            dict(original),
            {"document_id", "order", "text_tr"},
            f"translation[{order}]",
        )
        if (
            type(row["document_id"]) is not str
            or not row["document_id"]
            or row["document_id"] in seen
        ):
            raise ContractError("Ceviri paketinde bos/tekrarli document_id")
        if row["order"] != order:
            raise ContractError("Ceviri paketi sirasi kesintisiz degil")
        if type(row["text_tr"]) is not str or not row["text_tr"].strip():
            raise ContractError("Ceviri paketinde bos metin")
        seen.add(row["document_id"])
        output.append(row)
    return output


def _validate_blind_package(records: Sequence[Mapping]) -> list[dict]:
    expected = {
        "document_id",
        "span_id",
        "document_order",
        "span_order",
        "sentence_text",
        "span_text",
        "radtr_label",
    }
    output, seen = [], set()
    previous_document_order = previous_span_order = -1
    for index, original in enumerate(records):
        row = _exact_keys(dict(original), expected, f"normalization_blind[{index}]")
        key = (row["document_id"], row["span_id"])
        if key in seen:
            raise ContractError("Kor pakette tekrarli span anahtari")
        seen.add(key)
        for field in (
            "document_id",
            "span_id",
            "sentence_text",
            "span_text",
            "radtr_label",
        ):
            if type(row[field]) is not str or not row[field].strip():
                raise ContractError(f"Kor pakette bos/gecersiz alan: {field}")
        document_order, span_order = row["document_order"], row["span_order"]
        if any(type(x) is not int or x < 0 for x in (document_order, span_order)):
            raise ContractError("Kor paket sirasi negatif veya tam sayi degil")
        if document_order == previous_document_order:
            if span_order != previous_span_order + 1:
                raise ContractError("Kor pakette span sirasi kesintisiz degil")
        elif document_order > previous_document_order:
            if span_order != 0:
                raise ContractError("Kor pakette yeni belge span_order=0 ile baslamali")
        else:
            raise ContractError("Kor paket belge sirasi artan degil")
        previous_document_order, previous_span_order = document_order, span_order
        output.append(row)
    return output


def build_stratified_pilot(
    blind_rows: Sequence[Mapping],
    quotas: Mapping[str, int],
    max_per_document: int,
    seed: int,
) -> list[dict]:
    """Etiket tabakali, belge yukunu sinirlayan deterministik kor pilot sec."""
    rows = _validate_blind_package(blind_rows)
    if not quotas or any(type(n) is not int or n < 1 for n in quotas.values()):
        raise ContractError("Pilot kotalari pozitif tam sayi olmali")
    if type(max_per_document) is not int or max_per_document < 1:
        raise ContractError("Belge basina pilot siniri pozitif tam sayi olmali")

    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["radtr_label"], []).append(row)
    missing = {
        label: quota
        for label, quota in quotas.items()
        if len(groups.get(label, [])) < quota
    }
    if missing:
        raise ContractError(f"Pilot kotasi icin aday yetersiz: {missing}")

    selected, document_counts = [], Counter()
    # Nadir tabakalar once: yaygin bir etiket belge kotasini tuketip nadir
    # etiketleri disarida birakmasin. Esitlikte etiket adi sirayi sabitler.
    label_order = sorted(quotas, key=lambda label: (len(groups[label]), label))
    for label in label_order:
        candidates = list(groups[label])
        random.Random(f"{seed}:{label}").shuffle(candidates)
        ranks = {
            (row["document_id"], row["span_id"]): rank
            for rank, row in enumerate(candidates)
        }
        chosen_keys = set()
        for _ in range(quotas[label]):
            eligible = [
                row
                for row in candidates
                if (row["document_id"], row["span_id"]) not in chosen_keys
                and document_counts[row["document_id"]] < max_per_document
            ]
            if not eligible:
                raise ContractError(f"Belge siniri altinda kota tamamlanamadi: {label}")
            chosen = min(
                eligible,
                key=lambda row: (
                    document_counts[row["document_id"]],
                    ranks[(row["document_id"], row["span_id"])],
                ),
            )
            chosen_keys.add((chosen["document_id"], chosen["span_id"]))
            document_counts[chosen["document_id"]] += 1
            selected.append(chosen)

    selected.sort(key=lambda row: (row["document_order"], row["span_order"]))
    document_order, span_counts, output = {}, Counter(), []
    for row in selected:
        document_id = row["document_id"]
        if document_id not in document_order:
            document_order[document_id] = len(document_order)
        copied = dict(row)
        copied["document_order"] = document_order[document_id]
        copied["span_order"] = span_counts[document_id]
        span_counts[document_id] += 1
        output.append(copied)
    return _validate_blind_package(output)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_package_pair(
    translation: Sequence[Mapping],
    normalization: Sequence[Mapping],
    split: str,
    output_dir: Path,
) -> dict:
    """Iki paketi, manifesti ve manifest hash'ini tek cagrida atomik dosyalarla yaz."""
    require_development_split(split)
    translation = _validate_translation_package(translation)
    normalization = _validate_blind_package(normalization)
    translation_ids = {x["document_id"] for x in translation}
    normalization_ids = {x["document_id"] for x in normalization}
    if not normalization_ids <= translation_ids:
        raise ContractError("Kor pakette ceviri paketinde olmayan belge var")
    order_by_id = {x["document_id"]: x["order"] for x in translation}
    if any(order_by_id[x["document_id"]] != x["document_order"] for x in normalization):
        raise ContractError("Iki paketin belge kimligi/sirasi uyusmuyor")
    translation_path = output_dir / f"translation_{split}.jsonl"
    normalization_path = output_dir / f"normalization_blind_{split}.jsonl"
    manifest_path = output_dir / f"package_manifest_{split}.json"
    ledger_path = output_dir / f"package_checksums_{split}.sha256"
    for path in (translation_path, normalization_path, manifest_path, ledger_path):
        if path.exists():
            raise FileExistsError(f"Kilitli artefaktin uzerine yazilmaz: {path}")
    write_jsonl(translation_path, translation)
    write_jsonl(normalization_path, normalization)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "split": split,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "translation": {
            "file": translation_path.name,
            "records": len(translation),
            "sha256": sha256_file(translation_path),
        },
        "normalization": {
            "file": normalization_path.name,
            "records": len(normalization),
            "sha256": sha256_file(normalization_path),
        },
    }
    _atomic_text(
        manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    manifest_hash = sha256_file(manifest_path)
    _atomic_text(
        ledger_path,
        f"{manifest['translation']['sha256']}  {translation_path.name}\n"
        f"{manifest['normalization']['sha256']}  {normalization_path.name}\n"
        f"{manifest_hash}  {manifest_path.name}\n",
    )
    return {**manifest, "manifest_sha256": manifest_hash, "ledger": ledger_path.name}


def validate_annotation_rows(
    rows: Sequence[Mapping],
    inventory: frozenset[str],
    annotator_id: str | None = None,
) -> list[dict]:
    expected = {
        "document_id",
        "span_id",
        "sentence_text",
        "span_text",
        "radtr_label",
        "concept_ids",
        "mapping_status",
        "annotator_id",
        "note",
    }
    output, seen = [], set()
    for index, original in enumerate(rows):
        row = _exact_keys(dict(original), expected, f"annotation[{index}]")
        key = (row["document_id"], row["span_id"])
        if key in seen:
            raise ContractError(f"Tekrarli annotation anahtari: {key}")
        seen.add(key)
        for field in (
            "document_id",
            "span_id",
            "sentence_text",
            "span_text",
            "radtr_label",
            "annotator_id",
            "note",
        ):
            if type(row[field]) is not str:
                raise ContractError(f"Annotation metin alani gecersiz: {field}")
        if any(
            not row[field].strip()
            for field in (
                "document_id",
                "span_id",
                "sentence_text",
                "span_text",
                "radtr_label",
                "annotator_id",
            )
        ):
            raise ContractError("Annotation kimlik/kaynak alani bos olamaz")
        if annotator_id is not None and row["annotator_id"] != annotator_id:
            raise ContractError("Annotator kimligi dosya kilidiyle uyusmuyor")
        concepts = row["concept_ids"]
        if type(concepts) is not list or any(type(c) is not str for c in concepts):
            raise ContractError("concept_ids metinlerden olusan bir liste olmali")
        if len(concepts) != len(set(concepts)):
            raise ContractError("concept_ids benzersiz olmali")
        if any(c not in inventory for c in concepts):
            raise ContractError("Annotation envanter disi concept_id iceriyor")
        status = row["mapping_status"]
        if status not in MAPPING_STATUSES:
            raise ContractError("Gecersiz mapping_status")
        if status == "mapped" and not concepts:
            raise ContractError("mapped kaydi concept_ids icermeli")
        if status == "unmapped" and concepts:
            raise ContractError("unmapped kaydi concept_ids iceremez")
        if status == "mapped" and row["note"]:
            raise ContractError("mapped kaydinin note alani bos olmali")
        if status != "mapped" and not row["note"].strip():
            raise ContractError("unmapped/needs_adjudication kaydi gerekce icermeli")
        row["concept_ids"] = sorted(concepts)
        output.append(row)
    return output


def _validate_annotations_against_blind(
    annotations: Sequence[Mapping],
    blind_rows: Sequence[Mapping],
    inventory: frozenset[str],
    annotator_id: str | None = None,
) -> tuple[list[dict], list[dict]]:
    checked = validate_annotation_rows(annotations, inventory, annotator_id)
    blind = _validate_blind_package(blind_rows)
    checked_by_key = {(x["document_id"], x["span_id"]): x for x in checked}
    blind_by_key = {(x["document_id"], x["span_id"]): x for x in blind}
    if set(checked_by_key) != set(blind_by_key):
        missing = set(blind_by_key) - set(checked_by_key)
        extra = set(checked_by_key) - set(blind_by_key)
        raise ContractError(
            f"Annotation kor paketi tam kapsamiyor: eksik={len(missing)}, fazla={len(extra)}"
        )
    for key, annotation in checked_by_key.items():
        source = blind_by_key[key]
        for annotation_field, blind_field in (
            ("sentence_text", "sentence_text"),
            ("span_text", "span_text"),
            ("radtr_label", "radtr_label"),
        ):
            if annotation[annotation_field] != source[blind_field]:
                raise ContractError(f"Annotation kor kaynak metnini degistirmis: {key}")
    return checked, blind


def lock_annotation_output(
    rows: Sequence[Mapping],
    blind_rows: Sequence[Mapping],
    path: Path,
    inventory: frozenset[str],
    annotator_id: str,
) -> dict:
    checked, blind = _validate_annotations_against_blind(
        rows, blind_rows, inventory, annotator_id
    )
    manifest_path = path.with_suffix(path.suffix + ".manifest.json")
    for target in (path, manifest_path):
        if target.exists():
            raise FileExistsError(f"Kilitli artefaktin uzerine yazilmaz: {target}")
    write_jsonl(path, checked)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "annotator_id": annotator_id,
        "records": len(checked),
        "file": path.name,
        "sha256": sha256_file(path),
        "blind_package_sha256": _canonical_records_hash(blind),
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_text(
        manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return manifest


def reconcile_annotations(
    a_rows: Sequence[Mapping],
    b_rows: Sequence[Mapping],
    blind_rows: Sequence[Mapping],
    inventory: frozenset[str],
) -> list[dict]:
    """A/B'nin tamamini radyolog kontrol listesine birlestir; hicbir satiri dusurme."""
    a, blind_a = _validate_annotations_against_blind(a_rows, blind_rows, inventory)
    b, blind_b = _validate_annotations_against_blind(b_rows, blind_rows, inventory)
    if _canonical_records_hash(blind_a) != _canonical_records_hash(blind_b):
        raise ContractError("A/B farkli kor paketlere bagli")
    a_annotators = {x["annotator_id"] for x in a}
    b_annotators = {x["annotator_id"] for x in b}
    if len(a_annotators) != 1 or len(b_annotators) != 1 or a_annotators == b_annotators:
        raise ContractError(
            "A/B dosyalari tek ve birbirinden farkli annotator tasimali"
        )
    a_by_key = {(x["document_id"], x["span_id"]): x for x in a}
    b_by_key = {(x["document_id"], x["span_id"]): x for x in b}
    if set(a_by_key) != set(b_by_key):
        raise ContractError(
            "A/B annotation paketleri ayni span anahtarlarini tasimiyor"
        )

    output = []
    immutable = ("sentence_text", "span_text", "radtr_label")
    for key, left in a_by_key.items():
        right = b_by_key[key]
        if any(left[field] != right[field] for field in immutable):
            raise ContractError(f"A/B kor kaynak alani farkli: {key}")
        agreement = (
            left["mapping_status"] == right["mapping_status"]
            and left["concept_ids"] == right["concept_ids"]
        )
        output.append(
            {
                "document_id": key[0],
                "span_id": key[1],
                "sentence_text": left["sentence_text"],
                "span_text": left["span_text"],
                "radtr_label": left["radtr_label"],
                "a_mapping_status": left["mapping_status"],
                "a_concept_ids": left["concept_ids"],
                "a_note": left["note"],
                "b_mapping_status": right["mapping_status"],
                "b_concept_ids": right["concept_ids"],
                "b_note": right["note"],
                "agreement": "exact" if agreement else "disagreement",
                "radiologist_mapping_status": "pending",
                "radiologist_concept_ids": [],
                "radiologist_note": "",
            }
        )
    return output


def _prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def score_concepts(
    gold: Mapping[str, set[str]],
    prediction: Mapping[str, set[str]],
    document_ids: Sequence[str] | None = None,
) -> dict:
    ids = (
        list(document_ids)
        if document_ids is not None
        else sorted(set(gold) | set(prediction))
    )
    tp = fp = fn = empty_both = 0
    per_document = []
    for document_id in ids:
        expected, actual = (
            gold.get(document_id, set()),
            prediction.get(document_id, set()),
        )
        counts = (
            len(expected & actual),
            len(actual - expected),
            len(expected - actual),
        )
        tp += counts[0]
        fp += counts[1]
        fn += counts[2]
        if not expected and not actual:
            empty_both += 1
            per_document.append(None)
        else:
            per_document.append(_prf(*counts)["f1"])
    return {
        **_prf(tp, fp, fn),
        "documents": len(ids),
        "empty_both": empty_both,
        "document_f1": per_document,
    }


def score_assertions(
    gold: Mapping[str, set[tuple[str, str]]],
    prediction: Mapping[str, set[tuple[str, str]]],
    document_ids: Sequence[str] | None = None,
) -> dict:
    ids = (
        list(document_ids)
        if document_ids is not None
        else sorted(set(gold) | set(prediction))
    )
    # Kapali assertion dogrulamasi ZORUNLU. Aksi halde gecersiz bir assertion
    # hicbir sinifa girmez ve sessizce kaybolur (docs/24 §6.1).
    for kaynak, ad in ((gold, "altin"), (prediction, "tahmin")):
        for document_id, ciftler in kaynak.items():
            for concept_id, assertion in ciftler:
                if assertion not in ASSERTIONS:
                    raise ContractError(
                        f"{ad} kaydinda kapali envanter disi assertion: "
                        f"{document_id}/{concept_id}/{assertion!r}"
                    )
    per_class = {}
    for assertion in ASSERTIONS:
        tp = fp = fn = 0
        for document_id in ids:
            expected = {c for c, a in gold.get(document_id, set()) if a == assertion}
            actual = {
                c for c, a in prediction.get(document_id, set()) if a == assertion
            }
            tp += len(expected & actual)
            fp += len(actual - expected)
            fn += len(expected - actual)
        per_class[assertion] = {**_prf(tp, fp, fn), "support": tp + fn}
    included = [v["f1"] for v in per_class.values() if v["support"] + v["fp"] > 0]
    return {
        "classes": per_class,
        "macro_f1": sum(included) / len(included) if included else 0.0,
        "documents": len(ids),
    }


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    return sorted_values[lower] + (position - lower) * (
        sorted_values[upper] - sorted_values[lower]
    )


def paired_bootstrap_difference(
    document_ids: Sequence[str],
    tr_metric: Callable[[Sequence[str]], float],
    en_metric: Callable[[Sequence[str]], float],
    iterations: int = 10_000,
    seed: int = 20260901,
    max_undefined_ratio: float = 0.05,
) -> dict:
    """Ayni belge orneklemini iki kola ver; fark daima EN - TR'dir.

    TANIMSIZ ITERASYON POLITIKASI (docs/24 §6.7 · testten once donduruldu):
    bir bootstrap orneklemi bir sinif icin ne altin ne tahmin uretirse o
    sinifin F1'i TANIMSIZDIR. Sessizce 0 yazmak farki yapay olarak sifira
    ceker ve GA'yi dar gosterir. Metrik `nan` dondurerek iterasyonu tanimsiz
    ilan eder; iterasyon ATLANIR ve sayisi raporlanir. Atlanan oran
    `max_undefined_ratio`'yu asarsa metrik guvenilmez sayilir ve durulur.
    """
    if not document_ids:
        raise ContractError("Bootstrap icin belge yok")
    if iterations < 1:
        raise ContractError("Bootstrap tekrar sayisi pozitif olmali")
    # Taban listede tekrar OLMAMALI: tekrarli belge orneklem agirligini bozar.
    # (Orneklem ICINDE tekrar normaldir - bootstrap'in kendisi odur.)
    if len(set(document_ids)) != len(document_ids):
        raise ContractError("Bootstrap taban listesinde tekrarli document_id")
    rng, ids = random.Random(seed), list(document_ids)
    observed = en_metric(ids) - tr_metric(ids)
    if not math.isfinite(observed):
        raise ContractError("Bootstrap gozlenen metrigi tanimsiz; tam kume bos")
    differences, tanimsiz = [], 0
    for _ in range(iterations):
        sample = [rng.choice(ids) for _ in ids]
        difference = en_metric(sample) - tr_metric(sample)
        if not math.isfinite(difference):
            tanimsiz += 1
            continue
        differences.append(difference)
    if tanimsiz / iterations > max_undefined_ratio:
        raise ContractError(
            f"Bootstrap iterasyonlarinin %{100 * tanimsiz / iterations:.1f}'i "
            f"tanimsiz (sinir %{100 * max_undefined_ratio:.0f}); bu eksende "
            "destek guven araligi hesaplamak icin yetersiz"
        )
    differences.sort()
    return {
        "direction": "EN-TR",
        "iterations": iterations,
        "undefined_iterations": tanimsiz,
        "seed": seed,
        "observed_difference": observed,
        "ci95": [_percentile(differences, 0.025), _percentile(differences, 0.975)],
    }
