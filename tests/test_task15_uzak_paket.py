"""TASK-15 uzak GPU paketinin sessiz deney bozulmalarina karsı kapilari."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation.ikincil_model import IkincilModelAdapter
from radyovlm.evaluation.task15 import ContractError


def _kosucu():
    yol = ROOT / "scripts" / "36_task15_ikincil_model.py"
    spec = importlib.util.spec_from_file_location("task15_uzak_kosucu", yol)
    modul = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modul)
    return modul


def test_kol_ile_girdi_hashi_eslesmek_zorunda(tmp_path):
    kosucu = _kosucu()
    tr = tmp_path / "tr.jsonl"
    en = tmp_path / "en.jsonl"
    tr.write_text("turkce", encoding="utf-8")
    en.write_text("english", encoding="utf-8")
    manifest = {
        "girdi": {
            "tr": {"sha256": kosucu.sha256(tr)},
            "en_genel": {"sha256": kosucu.sha256(en)},
            "en_ucuz": {"sha256": "0" * 64},
        }
    }

    kosucu.kol_girdisini_dogrula(tr, "tr", manifest)
    with pytest.raises(ContractError, match="eslesmiyor"):
        kosucu.kol_girdisini_dogrula(en, "tr", manifest)


def test_girdi_order_bool_ve_bos_kimlik_kabul_etmez():
    kosucu = _kosucu()
    with pytest.raises(ContractError, match="sirasi"):
        kosucu.girdiyi_dogrula(
            [
                {"document_id": "d0", "order": 0, "text": "a"},
                {"document_id": "d1", "order": True, "text": "b"},
            ]
        )
    with pytest.raises(ContractError, match="document_id"):
        kosucu.girdiyi_dogrula([{"document_id": " ", "order": 0, "text": "a"}])


@pytest.mark.parametrize(
    ("model_type", "beklenen"),
    [("qwen3_5", "multimodal"), ("cohere2", "causal")],
)
def test_model_turu_dogru_huggingface_yukleyicisine_gider(
    monkeypatch, model_type, beklenen
):
    cagrilar = []

    class Yukleyici:
        @classmethod
        def from_pretrained(cls, *_args, **_kwargs):
            cagrilar.append(cls.__name__)
            if cls.__name__.startswith("Model"):
                return SimpleNamespace(
                    eval=lambda: SimpleNamespace(
                        hf_device_map={"": 0}, device=SimpleNamespace(type="cuda")
                    )
                )
            return object()

    siniflar = {
        "AutoProcessor": type("Processor", (Yukleyici,), {}),
        "AutoTokenizer": type("Tokenizer", (Yukleyici,), {}),
        "AutoModelForMultimodalLM": type("ModelMultimodal", (Yukleyici,), {}),
        "AutoModelForCausalLM": type("ModelCausal", (Yukleyici,), {}),
        "AutoConfig": SimpleNamespace(
            from_pretrained=lambda *_args, **_kwargs: SimpleNamespace(
                model_type=model_type
            )
        ),
    }
    sahte_transformers = SimpleNamespace(**siniflar)
    sahte_torch = SimpleNamespace(
        bfloat16="bf16",
        cuda=SimpleNamespace(
            is_available=lambda: True,
            is_bf16_supported=lambda: True,
            reset_peak_memory_stats=lambda: None,
        ),
    )
    monkeypatch.setitem(sys.modules, "transformers", sahte_transformers)
    monkeypatch.setitem(sys.modules, "torch", sahte_torch)

    adapter = IkincilModelAdapter("model", "{envanter}{text}", "x", revision="sha")
    adapter.hazirla()
    assert ("ModelMultimodal" in cagrilar) is (beklenen == "multimodal")
    assert ("ModelCausal" in cagrilar) is (beklenen == "causal")


def test_kosucu_yardimi_calismali():
    sonuc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "36_task15_ikincil_model.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert sonuc.returncode == 0
    assert "--dort-bit" in sonuc.stdout


def test_istem_d29_kesinlik_kuralina_uyar():
    istem = (ROOT / "configs" / "istem_ikincil_model_v2.txt").read_text(
        encoding="utf-8"
    )
    present = istem.split("present", 1)[1].split("absent", 1)[0]
    uncertain = istem.split("uncertain", 1)[1].split("Rules:", 1)[0]
    assert '"suspicious for"' in present and '"may represent"' in present
    assert '"suspicious for"' not in uncertain and '"may represent"' not in uncertain
