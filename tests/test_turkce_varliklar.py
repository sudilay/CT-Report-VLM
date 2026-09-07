# -*- coding: utf-8 -*-
"""TASK-15 Turkce birlesik kavram matcher'i testleri (D60/D61)."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction import entities as E
from radyovlm.extraction import turkce_varliklar as T


@pytest.fixture(scope="module")
def matcher():
    return T.tr_matcher_kur(T.turkce_sozlugu_yukle())


def kavramlar(metin: str, matcher) -> set[str]:
    return T.kavramlari_bul(metin, *matcher)


@pytest.mark.parametrize(
    ("metin", "beklenen", "beklenmeyen"),
    [
        ("akciğer parankiminde", "lung_parenchyma", {"parenchyma", "lung"}),
        ("nodüler lezyon", "nodular_lesion", {"nodule", "lesion"}),
        ("sekel değişiklikler", "sequela_change", {"sequela"}),
        ("aort kapağında", "aortic_valve", {"aorta"}),
        ("alt lob", "lower_lobe", {"anatomic_segment"}),
    ],
)
def test_en_uzun_eslesme_kazanir(metin, beklenen, beklenmeyen, matcher):
    bulunan = kavramlar(metin, matcher)
    assert beklenen in bulunan
    assert not (bulunan & beklenmeyen)


def test_ektazi_atelektazinin_icine_dusmez(matcher):
    bulunan = kavramlar("bilateral atelektaziler mevcuttur", matcher)
    assert "dilatation" not in bulunan
    assert "atelectasis" in bulunan


def test_lobule_interlobulerin_icine_dusmez(matcher):
    assert "lobulated" not in kavramlar("interlobüler septal kalınlaşmalar", matcher)


@pytest.mark.parametrize(
    "metin", ["nodül", "nodülde", "nodüller", "nodüllerin", "nodüler görünüm"]
)
def test_turkce_ekler_yakalanir(metin, matcher):
    assert "nodule" in kavramlar(metin, matcher)


def test_kalsifikasyon_ve_kalsifik_ayri(matcher):
    bulunan = kavramlar("kalsifiye plaklar", matcher)
    assert "calcific" in bulunan
    assert "calcification" not in bulunan
    assert "calcification" in kavramlar("kalsifikasyonlar izlendi", matcher)


def test_karaciger_parankimi_akciger_sayilmaz(matcher):
    assert "lung_parenchyma" not in kavramlar("karaciğer parankiminde", matcher)


def test_yakalayan_grup_reddedilir():
    with pytest.raises(ValueError, match="yakalayan grup"):
        T.tr_matcher_kur({"bozuk": "(nodul)"})


def test_ham_parantez_deseni_solda_sinirlanmaz():
    matcher = T.tr_matcher_kur({"ham": r"\(nodül\?\)"})
    assert T.kavramlari_bul("olası (nodül?)", *matcher) == {"ham"}


# TASK-15'in dondurdugu 144 kavram (tr-1.0). TASK-17 madde 10 (D91) 16 yeni
# yuzey EKLEDI ama BU 144'UN HICBIRINI DEGISTIRMEDI. Asil degismez budur:
# eski kavramlar duruyor mu, ve her yuzey derleniyor mu.
TASK15_KAVRAM_SAYISI = 144


def test_tr15_kavramlari_KORUNDU_ve_hepsi_derlenir(matcher):
    """tr-1.0'in 144 kavraminin hicbiri kaybolmadi; tum yuzeyler derleniyor.

    ⚠ Eski hali `== 144` diyordu ve TASK-17'nin genisletmesiyle kirildi.
    Test SILINMEDI: korudugu GERCEK degismez "eski kavramlar duruyor mu"dur,
    "sayi tam 144 mu" degil. Sayi sabiti bir dondurma kaydidir, bir kural
    degil - ve dondurma kaydi surum yukseltilerek guncellenir (D88'in dersi).
    """
    sozluk = T.turkce_sozlugu_yukle()
    _, indeks = matcher
    # her yuzey derlendi mi
    assert len(sozluk) == len(indeks)
    # TASK-15'in dondurdugu kavram sayisindan AZ olamaz
    assert len(sozluk) >= TASK15_KAVRAM_SAYISI, (
        f"tr-1.0'in {TASK15_KAVRAM_SAYISI} kavramindan geriye gidilmis: {len(sozluk)}")


def test_tr11_eklemeleri_kunye_tasiyor():
    """D87/B7 kurali: kaynagi olmayan Turkce yuzey sozluge GIRMEZ.

    tr-1.1 ile eklenen her girdi `kaynak` ve `mezuniyet` alani tasimalidir
    (`kunye` = literaturde belgelenmis, `olcum` = RadTr'de gecti).
    """
    sozluk = T.turkce_sozlugu_yukle()
    import yaml
    ham = yaml.safe_load(
        (ROOT / "configs/turkce_yuzeyler_taslak.yaml").read_text(encoding="utf-8"))
    yeni = [a for a, k in ham["yuzeyler"].items() if "mezuniyet" in k]
    assert yeni, "tr-1.1 eklemeleri bulunamadi"
    for a in yeni:
        k = ham["yuzeyler"][a]
        assert k.get("kaynak"), f"{a}: `kaynak` yok"
        assert k["mezuniyet"] in ("kunye", "olcum"), f"{a}: gecersiz mezuniyet"


def test_complete_calcification_kunyesiz_oldugu_icin_GIRMEDI():
    """⛔ Kuralin gercekten isledigini kanitlar.

    Terminoloji arastirmasi bu kavrami YANLIS esleyerek dogrulamisti
    ("diffuz kalsifikasyon"); esleme D83'te olculup curutuldu (491 cumle,
    tamami damar ateromu). Dogru kavram icin TR kunyesi YOK, RadTr'de 0.
    Tahminle eklenmedi - bu test o disiplini korur.
    """
    assert "complete_calcification" not in T.turkce_sozlugu_yukle()


def test_bos_metin_bos_kume(matcher):
    assert kavramlar("", matcher) == set()


def test_determinizm(matcher):
    metin = "Her iki akciğerde nodüler lezyon izlenmiştir."
    assert kavramlar(metin, matcher) == kavramlar(metin, matcher)


def test_uretim_mimarisi_iki_tarafta_ayni():
    tr = T.tr_matcher_kur({"kisa": "nod[uü]l", "uzun": "nod[uü]ler lezyon"})
    en_kavramlar = [
        E.Kavram("kisa", "observation", ["nodules?"]),
        E.Kavram("uzun", "observation", ["nodular lesions?"]),
    ]
    en_matcher, en_nesne_indeks = E.matcher_kur(en_kavramlar)
    en_indeks = {grup: kavram.ad for grup, kavram in en_nesne_indeks.items()}

    assert T.kavramlari_bul("nodüler lezyon", *tr) == {"uzun"}
    assert T.kavramlari_bul("nodular lesion", en_matcher, en_indeks) == {"uzun"}
    assert not tr[0].pattern.endswith(r"\b")
    assert en_matcher.pattern.endswith(r"\b")
