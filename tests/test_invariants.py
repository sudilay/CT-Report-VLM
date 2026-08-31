# -*- coding: utf-8 -*-
"""K16 gerileme testleri — kapsam karari kilavuza yazilmadan sozluge girmesin.

NEDEN BU TEST VAR:
  Kilavuza yazilmayan kapsam karari olcumu IKI KEZ bozdu ve iki seferde de
  ayrisma TEK YONLUYDU (ayar: D28, 99 ayrisma · test-v2: anatomic_segment +
  abdomen, 37 ayrisma). Her ikisinde de kural SISTEMDE VARDI ve DOGRUYDU;
  yalnizca isaretleyiciye sorulmamisti.

  K16'nin kendisi ilk kosusunda 7 karardan 3'unu ihlal olarak buldu - yani
  olcut, kendisini dogurmus olan hatayi bagimsiz olarak yeniden buldu.
"""
import importlib
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

INV = importlib.import_module("13_check_invariants")

SOZLUKLER = ("configs/anatomi_sozlugu.yaml", "configs/bulgu_sozlugu.yaml")


def _kapsam_kararlari() -> list[str]:
    out = []
    for dosya in SOZLUKLER:
        ham = yaml.safe_load((ROOT / dosya).read_text(encoding="utf-8"))
        kavramlar = ham.get("kavramlar", ham)
        out += [ad for ad, t in kavramlar.items()
                if isinstance(t, dict) and t.get("kilavuz_karari")]
    return out


def test_k16_gecer():
    """Her kapsam kararinin kilavuzda karsiligi var."""
    r = INV.k16_olc()
    assert r["ihlal"] == 0, r["ornek"]
    assert r["deger"] == pytest.approx(100.0)


def test_k16_bos_paydayla_calismiyor():
    """Olcut anlamli olsun diye en az birkac kapsam karari isaretli olmali.

    Payda sifira duserse K16 sessizce 'gecti' gorunur ve hicbir sey denetlemez.
    """
    assert INV.k16_olc()["payda"] >= 5


def test_testv2yi_bozan_kavramlar_isaretli():
    """test-v2'de fiilen ayrisan iki kavram denetim kapsaminda kalmali.

    Bunlarin isareti kaldirilirsa K16 yesil yanar ama koruma kaybolur.
    """
    kararlar = _kapsam_kararlari()
    for ad in ("anatomic_segment", "abdomen"):
        assert ad in kararlar, f"{ad} kapsam karari isareti dusmus"


def test_k16_eksik_kilavuzu_yakalar(monkeypatch):
    """Kilavuz bulunamazsa olcut SESSIZ GECMEZ, ihlal verir.

    Bu, olcutun kendisinin kor noktasi olurdu: bos kilavuz metniyle hicbir
    kavram bulunamaz ve hepsi ihlal sayilmalidir.
    """
    monkeypatch.setattr(INV, "KILAVUZLAR", ("docs/olmayan_dosya.md",))
    r = INV.k16_olc()
    assert r["ihlal"] == r["payda"] > 0
