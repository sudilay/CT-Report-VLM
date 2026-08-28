# -*- coding: utf-8 -*-
"""TASK-13 puanlama motoru testleri.

Eslestirme kurallari OLCUMDEN ONCE sabitlendi; bu testler onlarin gercekten
uygulandigini denetler. Sonucu gorup kurali gevsetmek, esigi gevsetmekle aynidir.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation import score as S  # noqa: E402


def sp(b, s, k, **ek):
    return S.Span(b, s, k, ek)


# ----------------------------------------------------------- eslestirme

def test_kati_esitlik_ister():
    a = [sp(0, 6, "nodule")]
    tam = [sp(0, 6, "nodule")]
    kaymis = [sp(0, 7, "nodule")]
    assert len(S.esle(a, tam, kati=True)[0]) == 1
    assert len(S.esle(a, kaymis, kati=True)[0]) == 0


def test_gevsek_kesisme_yeter():
    """Kural tabanlı cikarimda sinir bir kelime kayar; gevsek olcut bunu
    yakalar, kati olcut cezalandirir. Ikisi de raporlanir."""
    a = [sp(0, 6, "nodule")]
    kaymis = [sp(3, 12, "nodule")]
    assert len(S.esle(a, kaymis, kati=False)[0]) == 1


def test_kavram_farkliysa_eslesmez():
    a = [sp(0, 6, "nodule")]
    y = [sp(0, 6, "mass")]
    ciftler, kac, faz = S.esle(a, y, kati=False)
    assert not ciftler and len(kac) == 1 and len(faz) == 1


def test_ayni_kavramin_iki_anmasi_konumsal_eslesir():
    """Kume temelli eslestirme birini kacirmayi gizlerdi."""
    a = [sp(0, 6, "nodule"), sp(40, 46, "nodule")]
    y = [sp(0, 6, "nodule")]
    ciftler, kac, faz = S.esle(a, y, kati=True)
    assert len(ciftler) == 1 and len(kac) == 1 and not faz


def test_bir_sistem_span_iki_altina_eslesmez():
    a = [sp(0, 6, "nodule"), sp(2, 8, "nodule")]
    y = [sp(0, 6, "nodule")]
    ciftler, kac, _ = S.esle(a, y, kati=False)
    assert len(ciftler) == 1 and len(kac) == 1


# ----------------------------------------------------------- kesinlik/duyarlilik

def test_kesinlik_ve_duyarlilik_ayri():
    """Tek F1 sozluk cikariminin asimetrisini gizler - ayri olculur."""
    altin = [[sp(0, 6, "nodule"), sp(10, 18, "effusion")]]
    sistem = [[sp(0, 6, "nodule"), sp(30, 36, "mass")]]
    r = S.kesinlik_duyarlilik(altin, sistem, kati=True)
    assert r["tp"] == 1 and r["fn"] == 1 and r["fp"] == 1
    assert r["kesinlik"] == 0.5 and r["duyarlilik"] == 0.5


def test_bos_cumle_paydaya_girmez():
    """Ikisi de bos = dogru, ama kesinligi sisirmemeli."""
    r = S.kesinlik_duyarlilik([[]], [[]], kati=True)
    assert r["bos_dogru"] == 1
    assert r["tp"] == 0 and r["fp"] == 0 and r["fn"] == 0


def test_fazladan_varlik_duyarliligi_etkilemez():
    altin = [[sp(0, 6, "nodule")]]
    sistem = [[sp(0, 6, "nodule"), sp(20, 26, "cyst")]]
    r = S.kesinlik_duyarlilik(altin, sistem, kati=True)
    assert r["duyarlilik"] == 1.0
    assert r["kesinlik"] == 0.5


# ----------------------------------------------------------- makro F1

def test_makro_f1_yalnizca_eslesenlerde():
    """Kacirilan varlik negasyon hatasi gibi gorunmemeli."""
    ciftler = [(sp(0, 6, "nodule", assertion="absent"),
                sp(0, 6, "nodule", assertion="absent")),
               (sp(9, 17, "effusion", assertion="present"),
                sp(9, 17, "effusion", assertion="absent"))]
    r = S.makro_f1(ciftler, "assertion", ["present", "absent", "uncertain"])
    assert r["n"] == 2
    assert r["dogruluk"] == 0.5
    assert r["sinif"]["absent"]["tp"] == 1
    assert r["sinif"]["present"]["fn"] == 1


def test_makro_f1_bos_sinifi_atlar():
    ciftler = [(sp(0, 6, "n", assertion="present"), sp(0, 6, "n", assertion="present"))]
    r = S.makro_f1(ciftler, "assertion", ["present", "absent", "uncertain"])
    assert r["makro_f1"] == 1.0     # bos siniflar ortalamaya girmez


# ----------------------------------------------------------- celdirici

def test_celdirici_denetimi_dikkatsiz_isaretlemeyi_yakalar():
    """Her seye 'E' diyen isaretleyici celdiricileri de kabul eder."""
    hepsine_evet = [{"sahte": True, "dogru_varlik_mi": "E"} for _ in range(10)]
    r = S.celdirici_denetimi(hepsine_evet)
    assert r["ret_orani"] == 0.0

    dikkatli = [{"sahte": True, "dogru_varlik_mi": "H"} for _ in range(10)]
    assert S.celdirici_denetimi(dikkatli)["ret_orani"] == 100.0


def test_celdirici_yoksa_olculemez():
    assert S.celdirici_denetimi([{"sahte": False}])["n"] == 0


# ----------------------------------------------------------- esik

def test_olculemeyen_olcut_gecti_sayilmaz():
    """Payda sifirsa 'gecti' demek yanlis guven verir."""
    assert S.olcut_durumu(float("nan"), 90.0) == "olculemedi"
    assert S.olcut_durumu(95.0, 90.0) == "gecti"
    assert S.olcut_durumu(85.0, 90.0) == "KALDI"


def test_celdirici_kavram_reddini_de_sayar():
    """PILOT SONRASI DUZELTME: celdirici uretici cumleden rastgele kelime secip
    rastgele kavram atiyor. O kelimelerin cogu ('pleura', 'lungs') GERCEKTEN
    varliktir; yanlis olan KAVRAMDIR. Dogru cevap "varlik=E, kavram=H" ve bu
    YAKALANMIS sayilmali. Ilk surum yalnizca varlik sorusuna bakiyordu ve
    gercek %100'luk ret oranini %54 gosteriyordu."""
    kavram_reddi = [{"sahte": True, "dogru_varlik_mi": "E", "dogru_kavram_mi": "H"}]
    assert S.celdirici_denetimi(kavram_reddi)["ret_orani"] == 100.0

    varlik_reddi = [{"sahte": True, "dogru_varlik_mi": "H", "dogru_kavram_mi": ""}]
    assert S.celdirici_denetimi(varlik_reddi)["ret_orani"] == 100.0

    tam_kabul = [{"sahte": True, "dogru_varlik_mi": "E", "dogru_kavram_mi": "E"}]
    assert S.celdirici_denetimi(tam_kabul)["ret_orani"] == 0.0
