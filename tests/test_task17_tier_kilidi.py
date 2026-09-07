"""TASK-17 madde 7 - Tier A/B sozluk genisletmesinin degismezleri.

Plan: docs/34_task17_calisma_plani.md v2 §4.1 · Karar: D85

Bu testler kilidin (`configs/task17_tier_kilidi.json`) yazildiktan SONRA
degistirilmedigini otomatik denetler. Kilidin butun anlami sudur:

    Liste `test-v2` etki olcumunden ONCE dondurulur; boylece sonraki
    adimlarin SONUCU listeyi degistiremez.

Kilit yoksa testler ATLANIR (henuz madde 7 kosulmamis olabilir).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

KILIT = KOK / "configs/task17_tier_kilidi.json"
SOZLUK = KOK / "configs/bulgu_sozlugu.yaml"
SEMA_KAPISI = KOK / "configs/extraction_schema.json"

pytestmark = pytest.mark.skipif(not KILIT.exists(), reason="tier kilidi yok")


@pytest.fixture(scope="module")
def kilit() -> dict:
    return json.loads(KILIT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sozluk() -> dict:
    return yaml.safe_load(SOZLUK.read_text(encoding="utf-8"))


def test_sozluk_kilitten_sonra_degismedi(kilit):
    """⚠ EN ONEMLI TEST. Kilit sonrasi sozluk degistiyse, 'once kilitle sonra
    olc' protokolu kirilmis demektir ve `test-v2` etki olcumu GECERSIZDIR.
    """
    simdiki = hashlib.sha256(SOZLUK.read_bytes()).hexdigest()
    assert simdiki == kilit["sozluk_sha256"], (
        "bulgu_sozlugu.yaml KILITTEN SONRA DEGISTI. Protokol geregi (docs/34 "
        "§4.1) liste dondurulduktan sonra degistirilemez; degistiyse `test-v2` "
        "etki olcumu gecersizdir ve kilit yeniden yazilip gerekcesi kayda "
        "gecirilmelidir."
    )


def test_sema_kapisi_kilitten_sonra_degismedi(kilit):
    simdiki = hashlib.sha256(SEMA_KAPISI.read_bytes()).hexdigest()
    assert simdiki == kilit["sema_kapisi_sha256"], (
        "extraction_schema.json kilitten sonra degisti - niteleyici gruplari "
        "sozlukle birlikte kilitlenmisti."
    )


def test_surum_yukseltildi(kilit, sozluk):
    assert kilit["onceki_surum"] == "bulgu-1.1"
    assert sozluk["surum"] == kilit["yeni_surum"] == "bulgu-1.2"


def test_her_yeni_girdi_uc_alani_tasir(kilit, sozluk):
    """D74'un kosullu gevsettigi kuralin sarti: kaynak + korpus_destegi + amac.

    Bu alanlar olmadan 'sifir destekli girdi' kabul edilmez; kapsam iddiasi
    sisirilmesin diye ("N'si olculmus destekli, M'si transfer amacli").
    """
    for ad in kilit["girdiler"]:
        k = sozluk["kavramlar"][ad]
        assert k.get("kaynak"), f"{ad}: `kaynak` yok"
        assert "korpus_destegi" in k, f"{ad}: `korpus_destegi` yok"
        assert k.get("amac") in ("olculmus", "transfer"), f"{ad}: `amac` gecersiz"


def test_kunye_ELDE_OLAN_bir_belgeyi_adlandiriyor(kilit, sozluk):
    """⚠ Bagimsiz denetim (Codex, D87) bu boslugu buldu.

    Eski test yalniz `kaynak` alaninin BOS OLMADIGINI denetliyordu. Bu, bir
    girdiyi "kaynakli" saymaya yetmez: 7 girdi elimizde OLMAYAN bir belgeye
    (WHO 2021) atif veriyordu. Kunye artik DOGRULANABILIR bir belge
    adlandirmalidir - ya depoda duran bir dosya, ya `KORPUS` (kendi olcumumuz).

    ⚠ SINIR (ilan edilmistir): belgenin ADLANDIRILMASI, o belgenin ilgili
    terimi GERCEKTEN destekledigini KANITLAMAZ. Bunu ancak insan dogrulamasi
    yapabilir. Test "dogrulanabilir bir belge gosteriliyor mu" der, o kadar.
    """
    eldeki = kilit["kunye_disiplini"]["eldeki_belgeler"]
    for ad in kilit["girdiler"]:
        kaynak = sozluk["kavramlar"][ad]["kaynak"]
        assert "| belge:" in kaynak, f"{ad}: kunye belge adlandirmiyor -> {kaynak}"
        belge = kaynak.split("| belge:")[1].strip()
        if belge == "KORPUS":
            continue
        assert belge in eldeki, f"{ad}: `{belge}` elimizdeki belgeler arasinda yok"
        assert (KOK / eldeki[belge]).exists(), f"{ad}: belge dosyasi yok -> {eldeki[belge]}"


def test_tier_ayrimi_korpus_destegiyle_tutarli(kilit, sozluk):
    """Tier B = korpus_destegi 0, Tier A = > 0. Karismasi kapsam iddiasini bozar."""
    for ad in kilit["tier_b_sifir_destek_transfer"]:
        assert sozluk["kavramlar"][ad]["korpus_destegi"] == 0, f"{ad} Tier B ama destegi var"
        assert sozluk["kavramlar"][ad]["amac"] == "transfer"
    for ad in kilit["tier_a_olculmus_destek"]:
        assert sozluk["kavramlar"][ad]["korpus_destegi"] > 0, f"{ad} Tier A ama destegi 0"
        assert sozluk["kavramlar"][ad]["amac"] == "olculmus"


def test_reddedilen_desen_parcalari_sozlukte_YOK(sozluk):
    """⛔ Olculup reddedilen parcalar geri sizmamali.

    `concentric`      -> 16 cumle, damar/duvar kalinlasmasi
    `diffuse calcifi` -> 491 cumle, damar ateromu (Lung-RADS 'complete' DEGIL)
    Bu test onlarin sessizce geri eklenmesini engeller.
    """
    tum = " ".join(
        d for k in sozluk["kavramlar"].values() for d in k["desenler"])
    assert "concentric" not in tum, "`concentric` reddedilmisti (16 cumle, damar/duvar)"
    assert "diffuse" not in tum or "calcifi" not in tum.split("diffuse")[1][:20], (
        "`diffuse calcifi` reddedilmisti (491 cumle, damar ateromu)")


def test_carcinomatosis_carcinoma_tarafindan_yutulmuyor():
    """⚠ Tier A'nin ILK maddesi bu cakismaya baglidir.

    `carcinomas?\\b` deseni `carcinomatosis` icinde eslesirse `carcinomatosis`
    HIC uretilmez ve D74'un birinci maddesi olu dogar.
    """
    from radyovlm.extraction import entities as ent

    kavramlar, _ = ent.sozlukleri_yukle()
    matcher, indeks = ent.matcher_kur(kavramlar)
    v = ent.cumleden_varliklar(
        "Lymphangitic carcinomatosis is observed in both lungs.", matcher, indeks)
    bulunan = {x["kavram"].ad for x in v}
    assert "carcinomatosis" in bulunan
    assert "carcinoma" not in bulunan


@pytest.mark.parametrize("cumle,beklenen", [
    ("Squamous cell carcinoma of the left upper lobe.", "squamous_cell_carcinoma"),
    ("Adenocarcinoma was reported in the biopsy.", "adenocarcinoma"),
    ("A nodule with central calcification is observed.", "central_calcification"),
    ("A completely calcified nodule measuring 15 mm.", "complete_calcification"),
    ("Popcorn calcification in the nodule.", "popcorn_calcification"),
    ("Small cell lung carcinoma on follow-up.", "small_cell_carcinoma"),
])
def test_en_uzun_eslesme_yeni_girdilerde_calisiyor(cumle, beklenen):
    """Bilesik kavramlar, iclerindeki daha kisa kavrami yenmeli."""
    from radyovlm.extraction import entities as ent

    kavramlar, _ = ent.sozlukleri_yukle()
    matcher, indeks = ent.matcher_kur(kavramlar)
    v = ent.cumleden_varliklar(cumle, matcher, indeks)
    assert beklenen in {x["kavram"].ad for x in v}


def test_reddedilen_diffuse_kalsifikasyon_hala_yakalanmiyor():
    """⛔ 491 damar ateromu cumlesi benign kalsifikasyon paterni SAYILMAMALI."""
    from radyovlm.extraction import entities as ent

    kavramlar, _ = ent.sozlukleri_yukle()
    matcher, indeks = ent.matcher_kur(kavramlar)
    v = ent.cumleden_varliklar(
        "Diffuse calcific atheroma plaques in the aorta.", matcher, indeks)
    bulunan = {x["kavram"].ad for x in v}
    assert "complete_calcification" not in bulunan
    assert "calcific" in bulunan


def test_sema_kapisi_yeni_niteleyicileri_taniyor(kilit):
    """Niteleyici sozlukte olup sema kapisinda YOKSA cikarim reddeder."""
    sema = json.loads(SEMA_KAPISI.read_text(encoding="utf-8"))
    izinli = set(sema["niteleyici_gruplari"]["calcification_pattern"]["degerler"])
    for ad, g in kilit["girdiler"].items():
        if g["grup"] == "calcification_pattern":
            assert ad in izinli, f"{ad} sema kapisinda tanimli degil"


def test_desenlerde_yakalayan_grup_yok(kilit, sozluk):
    """Yakalayan grup birlesik regex'te grup numaralarini kaydirir ve
    eslesmeyi SESSIZCE bozar (entities.py `_yakalayan_grup_var_mi`)."""
    for ad in kilit["girdiler"]:
        for d in sozluk["kavramlar"][ad]["desenler"]:
            assert not re.search(r"\((?!\?)", d), f"{ad}: yakalayan grup var -> {d}"
