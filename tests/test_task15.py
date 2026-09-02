"""TASK-15 altyapisini sinar; RadTr `test.json` HICBIR testte acilmaz."""

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation.task15 import (
    ContractError,
    build_package_records,
    build_stratified_pilot,
    lock_annotation_output,
    paired_bootstrap_difference,
    parse_model_output,
    reconcile_annotations,
    run_secondary_model,
    run_translation,
    score_assertions,
    score_concepts,
    sha256_file,
    validate_annotation_rows,
    write_package_pair,
)

INVENTORY = frozenset({"nodule", "pleura", "effusion"})


def _document(split="dev"):
    return {
        "belge_id": "dev-1",
        "kaynak_bolum": split,
        "metin": "Plevral efüzyon izlenmedi. Nodül mevcuttur.",
        "varliklar": [
            {
                "metin": "Plevral efüzyon",
                "radtr_etiket": "Obs_Absent",
                "tok_bas": 0,
                "tok_son": 1,
            },
            {
                "metin": "Nodül",
                "radtr_etiket": "Obs_Present",
                "tok_bas": 3,
                "tok_son": 3,
            },
        ],
    }


def _annotation(annotator, concepts=("effusion",), status="mapped"):
    return {
        "document_id": "dev-1",
        "span_id": "dev-1:s0000",
        "sentence_text": "Plevral efüzyon izlenmedi.",
        "span_text": "Plevral efüzyon",
        "radtr_label": "Obs_Absent",
        "concept_ids": list(concepts),
        "mapping_status": status,
        "annotator_id": annotator,
        "note": "",
    }


def _blind():
    return [
        {
            "document_id": "dev-1",
            "span_id": "dev-1:s0000",
            "document_order": 0,
            "span_order": 0,
            "sentence_text": "Plevral efüzyon izlenmedi.",
            "span_text": "Plevral efüzyon",
            "radtr_label": "Obs_Absent",
        }
    ]


def test_split_kilidi_testi_paketlemeden_durdurur():
    with pytest.raises(ContractError, match="tek kullanimlik"):
        build_package_records([_document("test")], "test")


def test_iki_kor_paket_ayni_geciste_uretilir(tmp_path):
    translation, normalization = build_package_records([_document()], "dev")
    assert translation == [
        {
            "document_id": "dev-1",
            "order": 0,
            "text_tr": "Plevral efüzyon izlenmedi. Nodül mevcuttur.",
        }
    ]
    assert len(normalization) == 2
    assert normalization[0]["sentence_text"] == "Plevral efüzyon izlenmedi."
    assert not ({"radtr_label", "span_text", "concept_ids"} & set(translation[0]))
    assert not ({"translation", "prediction", "concept_ids"} & set(normalization[0]))

    manifest = write_package_pair(translation, normalization, "dev", tmp_path)
    assert manifest["translation"]["sha256"] == sha256_file(
        tmp_path / "translation_dev.jsonl"
    )
    assert manifest["normalization"]["sha256"] == sha256_file(
        tmp_path / "normalization_blind_dev.jsonl"
    )
    assert (tmp_path / manifest["ledger"]).read_text().count("\n") == 3


@pytest.mark.parametrize(
    "raw",
    [
        '```json\n{"findings": []}\n```',
        '{"findings": [], "explanation": "normal"}',
        '{"findings": [{"concept_id": "free_diagnosis", "assertion": "present"}]}',
        '{"findings": [{"concept_id": "nodule", "assertion": "likely"}]}',
    ],
)
def test_model_cikisi_kapali_json_olmali(raw):
    with pytest.raises(ContractError):
        parse_model_output(raw, INVENTORY)


def test_model_cikisi_gecerli_json():
    raw = '{"findings":[{"concept_id":"nodule","assertion":"present"}]}'
    assert parse_model_output(raw, INVENTORY) == [
        {"concept_id": "nodule", "assertion": "present"}
    ]


def test_adapterler_kimlik_ve_sirayi_korur():
    class Translator:
        name = "fake-nmt"

        def translate(self, text, source_language, target_language):
            assert (source_language, target_language) == ("tr", "en")
            return "No pleural effusion."

    class Model:
        name = "fake-model"

        def generate(self, text, prompt):
            assert prompt == "frozen"
            return '{"findings":[{"concept_id":"effusion","assertion":"absent"}]}'

    translated = run_translation(
        [{"document_id": "dev-1", "order": 0, "text_tr": "Efüzyon yok."}],
        Translator(),
    )
    model_input = [
        {"document_id": x["document_id"], "order": x["order"], "text": x["text"]}
        for x in translated
    ]
    output = run_secondary_model(model_input, Model(), "frozen", INVENTORY)
    assert output[0]["document_id"] == "dev-1"
    assert output[0]["findings"][0] == {"concept_id": "effusion", "assertion": "absent"}


def test_annotation_kilidi_ve_tam_liste_uzlastirmasi(tmp_path):
    a = [_annotation("opus")]
    b = [_annotation("codex", ("pleura",))]
    a_manifest = lock_annotation_output(
        a, _blind(), tmp_path / "a.jsonl", INVENTORY, "opus"
    )
    b_manifest = lock_annotation_output(
        b, _blind(), tmp_path / "b.jsonl", INVENTORY, "codex"
    )
    assert a_manifest["sha256"] != b_manifest["sha256"]
    assert a_manifest["blind_package_sha256"] == b_manifest["blind_package_sha256"]

    merged = reconcile_annotations(a, b, _blind(), INVENTORY)
    assert len(merged) == 1
    assert merged[0]["agreement"] == "disagreement"
    assert merged[0]["radiologist_mapping_status"] == "pending"


def test_annotation_durum_kavram_tutarliligi():
    invalid = [_annotation("codex", (), "mapped")]
    with pytest.raises(ContractError, match="mapped kaydi"):
        validate_annotation_rows(invalid, INVENTORY)


def test_annotation_notu_yalniz_eslesmeyen_ve_uzlastirilacak_kayitta():
    mapped_with_note = _annotation("codex")
    mapped_with_note["note"] = "gereksiz aciklama"
    with pytest.raises(ContractError, match="note alani bos"):
        validate_annotation_rows([mapped_with_note], INVENTORY)

    unmapped_without_reason = _annotation("codex", (), "unmapped")
    with pytest.raises(ContractError, match="gerekce icermeli"):
        validate_annotation_rows([unmapped_without_reason], INVENTORY)


def test_annotation_kor_paketten_satir_atlayamaz(tmp_path):
    with pytest.raises(ContractError, match="tam kapsamiyor"):
        lock_annotation_output([], _blind(), tmp_path / "a.jsonl", INVENTORY, "opus")


def test_kilitli_artefaktin_uzerine_yazilmaz(tmp_path):
    path = tmp_path / "a.jsonl"
    lock_annotation_output([_annotation("opus")], _blind(), path, INVENTORY, "opus")
    with pytest.raises(FileExistsError, match="uzerine yazilmaz"):
        lock_annotation_output([_annotation("opus")], _blind(), path, INVENTORY, "opus")


def test_ceviri_paketine_gizli_altin_alani_sizdirilamaz(tmp_path):
    translation, normalization = build_package_records([_document()], "dev")
    translation[0]["radtr_label"] = "Obs_Absent"
    with pytest.raises(ContractError, match="kapali sozlesmeye"):
        write_package_pair(translation, normalization, "dev", tmp_path)


def test_belge_duzeyi_a1_a2_a3():
    gold_concepts = {"d1": {"nodule", "effusion"}, "d2": {"pleura"}}
    predicted_concepts = {"d1": {"nodule", "pleura"}, "d2": {"pleura"}}
    a1 = score_concepts(gold_concepts, predicted_concepts)
    assert (a1["tp"], a1["fp"], a1["fn"]) == (2, 1, 1)
    assert a1["f1"] == pytest.approx(2 / 3)

    gold_assertions = {
        "d1": {("nodule", "present"), ("effusion", "absent")},
        "d2": {("nodule", "uncertain")},
    }
    predicted_assertions = {
        "d1": {("nodule", "present"), ("effusion", "present")},
        "d2": {("nodule", "uncertain")},
    }
    a2 = score_assertions(gold_assertions, predicted_assertions)
    assert a2["classes"]["present"]["f1"] == pytest.approx(2 / 3)
    assert a2["classes"]["absent"]["f1"] == 0
    assert a2["classes"]["uncertain"]["f1"] == 1
    assert a2["macro_f1"] == pytest.approx(5 / 9)


def test_bootstrap_eslestirilmis_ve_yonu_en_eksi_tr():
    ids = ["d1", "d2", "d3"]
    values_tr = {"d1": 0.2, "d2": 0.4, "d3": 0.6}
    values_en = {"d1": 0.3, "d2": 0.5, "d3": 0.7}

    def metric(values):
        return lambda sample: sum(values[x] for x in sample) / len(sample)

    result = paired_bootstrap_difference(
        ids, metric(values_tr), metric(values_en), iterations=10_000, seed=7
    )
    assert result["direction"] == "EN-TR"
    assert result["iterations"] == 10_000
    assert result["observed_difference"] == pytest.approx(0.1)
    assert result["ci95"] == pytest.approx([0.1, 0.1])


def test_iki_dilli_katalog_dondurulmus_envanterle_birebir():
    def load(name):
        return yaml.safe_load((ROOT / "configs" / name).read_text(encoding="utf-8"))

    inventory = load("turkce_yuzeyler_taslak.yaml")["yuzeyler"]
    catalog = load("task15_kavram_katalogu.yaml")
    anatomy = load("anatomi_sozlugu.yaml")["kavramlar"]
    findings = load("bulgu_sozlugu.yaml")["kavramlar"]

    assert catalog["envanter_surum"] == "tr-1.0"
    assert catalog["uzman_onayi"] is False
    assert len(catalog["kavramlar"]) == 144
    assert set(catalog["kavramlar"]) == set(inventory)
    for concept_id, entry in catalog["kavramlar"].items():
        expected_type = (
            "anatomy" if concept_id in anatomy else findings[concept_id]["tip"]
        )
        assert set(entry) == {"tip", "tr", "en"}
        assert entry["tip"] == expected_type
        assert entry["tr"].strip() and entry["en"].strip()


def test_tabakali_pilot_kota_belge_siniri_ve_tekrarlanabilirlik():
    rows = []
    for document_order in range(4):
        for span_order, label in enumerate(("A", "B")):
            rows.append(
                {
                    "document_id": f"d{document_order}",
                    "span_id": f"d{document_order}:s{span_order}",
                    "document_order": document_order,
                    "span_order": span_order,
                    "sentence_text": f"cümle {document_order}",
                    "span_text": f"span {span_order}",
                    "radtr_label": label,
                }
            )

    first = build_stratified_pilot(rows, {"A": 3, "B": 3}, 2, 20260901)
    second = build_stratified_pilot(rows, {"A": 3, "B": 3}, 2, 20260901)
    assert first == second
    assert len(first) == 6
    assert {
        label: sum(x["radtr_label"] == label for x in first) for label in ("A", "B")
    } == {"A": 3, "B": 3}
    assert (
        max(
            sum(x["document_id"] == document_id for x in first)
            for document_id in {x["document_id"] for x in first}
        )
        <= 2
    )


# --------------------------------------------------------------------------
# RadTr kaynak gercekleri - sentetik degil, gercek veriye karsi kosar.
# Veri yoksa atlanir; test.json HICBIR kosulda okunmaz (D49/D50).
# --------------------------------------------------------------------------

RADTR = ROOT / "data" / "external" / "radtr"
# Yon-tarafsiz semantik capa: bir `Obs_Absent` spani negasyon ipucu ICERMELI.
# Bu olcut spani sola kaydirmakla iyilesmez; noktalama sayimindan farki budur.
NEGASYON = re.compile(
    r"izlenme|saptanma|görülme|mevcut değil|yoktur|yok\b|bulunma|rastlan"
    r"|seçilme|tespit edilme|değildir",
    re.IGNORECASE,
)
ANCAK_ESIK = 0.70


def _absent_capa_orani(kayma: int) -> float:
    """Verilen ofset kaymasinda negasyon ipucu tasiyan Obs_Absent span orani."""
    isabet = toplam = 0
    for bolum in ("train", "dev"):
        with (RADTR / f"{bolum}.json").open(encoding="utf-8") as f:
            for satir in f:
                d = json.loads(satir)
                kel = [w for c in d["sentences"] for w in c]
                for b, e, etiket in [x for c in d["ner"] for x in c]:
                    if etiket != "Obs_Absent":
                        continue
                    bas, son = b + kayma, e + kayma
                    if bas < 0 or son >= len(kel) or bas > son:
                        continue
                    toplam += 1
                    isabet += bool(NEGASYON.search(" ".join(kel[bas : son + 1])))
    return isabet / toplam if toplam else 0.0


@pytest.mark.skipif(
    not (RADTR / "train.json").exists(), reason="RadTr kaynagi yok"
)
def test_radtr_ofseti_semantik_capayi_gecer():
    """Ofset 0-tabanli kapsayici olmali; `-1` kaymasi bu kapiyi GECEMEZ.

    Bu satir iki kez yanlis 'duzeltildi'. Nesnel ama yon-yanli bir olcut
    (ic noktalama sayimi) yanlis yone goturdugu icin capa semantik secildi.
    """
    dogru = _absent_capa_orani(0)
    assert dogru >= ANCAK_ESIK, (
        f"0-tabanli okumada absent/negasyon orani {dogru:.1%} < {ANCAK_ESIK:.0%}. "
        "Ya kaynak veri degisti ya cikarim semantigi bozuldu."
    )
    # Kapinin disi var mi - eski `-1` hatasi geri gelirse yakalanmali.
    assert _absent_capa_orani(-1) < ANCAK_ESIK
    assert _absent_capa_orani(1) < dogru


@pytest.mark.skipif(
    not (RADTR / "train.json").exists(), reason="RadTr kaynagi yok"
)
def test_radtr_bolunmesi_dosya_adindan_alinamaz():
    """train.json dev ve test belgelerini icerir (D49); kapi bunu gormeli."""
    hashler = {}
    for bolum in ("train", "dev"):
        with (RADTR / f"{bolum}.json").open(encoding="utf-8") as f:
            hashler[bolum] = {
                hashlib.sha256(
                    " ".join(
                        w for c in json.loads(s)["sentences"] for w in c
                    ).encode("utf-8")
                ).hexdigest()
                for s in f
            }
    # Bu cakisma RadTr'nin bilinen bir olgusudur; kaybolursa varsayim degismistir.
    assert hashler["dev"] <= hashler["train"], (
        "dev artik train'in alt kumesi degil - bolunme haritasi yeniden uretilmeli"
    )


@pytest.mark.skipif(
    not (ROOT / "data" / "processed" / "radtr_bolunme_haritasi.json").exists(),
    reason="bolunme haritasi uretilmedi",
)
def test_bolunme_haritasi_uc_bolumu_de_kapsar():
    veri = json.loads(
        (ROOT / "data" / "processed" / "radtr_bolunme_haritasi.json").read_text(
            encoding="utf-8"
        )
    )
    harita = veri["harita"]
    assert set(harita.values()) == {"train", "dev", "test"}
    assert len(harita) == veri["belge_sayisi"]
    # Harita metin TASIMAMALI - yalniz hash ve etiket.
    assert all(re.fullmatch(r"[0-9a-f]{64}", k) for k in harita)


# --------------------------------------------------------------------------
# Sozlesme kenarlari (docs/24 §6) - her biri sessiz basarisizligi gorunur yapar
# --------------------------------------------------------------------------


def test_model_ciktisi_tekrarli_cifti_reddeder():
    """Puanlayici kume kullaniyor; tekrar sessizce yutulursa yapisal hata gizlenir."""
    ham = (
        '{"findings": [{"concept_id": "nodule", "assertion": "present"},'
        ' {"concept_id": "nodule", "assertion": "present"}]}'
    )
    with pytest.raises(ContractError, match="tekrarli"):
        parse_model_output(ham, INVENTORY)
    # Ayni kavram FARKLI kesinlikle gecebilir - bu mesrudur, katlanmaz.
    ikili = (
        '{"findings": [{"concept_id": "nodule", "assertion": "present"},'
        ' {"concept_id": "nodule", "assertion": "uncertain"}]}'
    )
    assert len(parse_model_output(ikili, INVENTORY)) == 2


def test_puanlayici_kapali_assertion_disini_reddeder():
    """Gecersiz assertion hicbir sinifa girmeyip sessizce kaybolmamali."""
    altin = {"d1": {("nodule", "present")}}
    bozuk = {"d1": {("nodule", "probably")}}
    with pytest.raises(ContractError, match="assertion"):
        score_assertions(altin, bozuk, ["d1"])
    with pytest.raises(ContractError, match="assertion"):
        score_assertions(bozuk, altin, ["d1"])


def test_bootstrap_taban_listesinde_tekrar_kabul_etmez():
    """Tabanda tekrar orneklem agirligini bozar; orneklem ICINDE tekrar normaldir."""
    with pytest.raises(ContractError, match="tekrarli"):
        paired_bootstrap_difference(
            ["d1", "d1", "d2"], lambda s: 0.5, lambda s: 0.6, iterations=10
        )


def test_bootstrap_tanimsiz_iterasyon_politikasi():
    """`nan` = tanimsiz iterasyon: atlanir ve sayilir; asiri olursa durur."""
    ids = [f"d{i}" for i in range(20)]
    sayac = {"n": 0}

    def bazen_tanimsiz(_sample):
        sayac["n"] += 1
        return float("nan") if sayac["n"] % 50 == 0 else 0.5

    sonuc = paired_bootstrap_difference(
        ids, lambda s: 0.5, bazen_tanimsiz, iterations=500
    )
    assert sonuc["undefined_iterations"] > 0
    assert sonuc["direction"] == "EN-TR"

    with pytest.raises(ContractError, match="tanimsiz"):
        paired_bootstrap_difference(
            ids, lambda s: 0.5, lambda s: float("nan"), iterations=100
        )
