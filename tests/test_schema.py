# -*- coding: utf-8 -*-
"""TASK-10 sema testleri.

Iki katman:
  1. Semanin kendi tutarliligi  - JSON ic tutarli mi, alinan/atilan degerler mantikli mi
  2. Dogrulayicinin davranisi   - her ihlal sinifini yakaliyor mu, temiz veriyi geciriyor mu

Sema henuz uretilmis veri uzerinde kosmuyor (o TASK-11); dogrulayici sentetik
cerceveler uzerinde sinaniyor.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction import schema as S  # noqa: E402


@pytest.fixture(scope="module")
def sema():
    return S.yukle()


# =====================================================================
# 1. SEMANIN IC TUTARLILIGI
# =====================================================================

def test_sema_yuklenir_ve_surum_tasir(sema):
    assert sema["schema_version"] == "sema-1.1"
    for k in ("varlik_tipleri", "iliski_tipleri", "kontrollu_degerler",
              "niteleyici_gruplari", "tablolar", "dogrulama_kurallari"):
        assert k in sema, f"sema {k} bolumunu tasimiyor"


def test_iliski_uclari_gecerli_tiplere_bakar(sema):
    """Her iliskinin head/tail listesi ya tanimli bir varlik tipi ya measurement olmali."""
    gecerli = set(sema["varlik_tipleri"]) | {"measurement"}
    for ad, t in sema["iliski_tipleri"].items():
        assert set(t["head"]) <= gecerli, f"{ad}.head tanimsiz tip: {set(t['head']) - gecerli}"
        assert set(t["tail"]) <= gecerli, f"{ad}.tail tanimsiz tip: {set(t['tail']) - gecerli}"


def test_measured_by_anatomiye_baglanabilir(sema):
    """Olculu 10.627 cumlede lezyon adi yok - olcu dogrudan organa ait.
    Sema bunu desteklemezse o olculer oksuz kalir."""
    assert "anatomy" in sema["iliski_tipleri"]["measured_by"]["head"]


def test_her_kume_referansi_cozulur(sema):
    """Kolon tanimindaki her 'kume' yolu gercekten bir deger kumesine cozulmeli."""
    for tablo, t in sema["tablolar"].items():
        for kol, tanim in t["kolonlar"].items():
            if "kume" in tanim:
                assert S._kume_degerleri(sema, tanim["kume"]), f"{tablo}.{kol} bos kume"


def test_niteleyici_gruplari_bos_degil(sema):
    for grup, t in sema["niteleyici_gruplari"].items():
        if grup.startswith("_"):
            continue
        assert t["degerler"], f"{grup} hic deger tasimiyor"


def test_alinan_degerler_atilanlardan_daha_iyi_desteklenir(sema):
    """Bir grupta kabul edilen EN ZAYIF deger, reddedilen EN GUCLU degerden
    daha cok korpus destegi tasimali. Aksi hâlde secim tutarsizdir."""
    for grup, t in sema["niteleyici_gruplari"].items():
        if grup.startswith("_") or not t.get("olculup_alinmayan"):
            continue
        en_zayif_alinan = min(t["degerler"].values())
        en_guclu_atilan = max(t["olculup_alinmayan"].values())
        assert en_zayif_alinan > en_guclu_atilan, (
            f"{grup}: alinan en zayif {en_zayif_alinan}, atilan en guclu {en_guclu_atilan}")


def test_alinan_ve_atilan_degerler_cakismaz(sema):
    for grup, t in sema["niteleyici_gruplari"].items():
        if grup.startswith("_"):
            continue
        cakisan = set(t["degerler"]) & set(t.get("olculup_alinmayan", {}))
        assert not cakisan, f"{grup} hem alinmis hem atilmis: {cakisan}"


def test_korpus_destegi_sayilari_gecerli(sema):
    for grup, t in sema["niteleyici_gruplari"].items():
        if grup.startswith("_"):
            continue
        for kaynak in ("degerler", "olculup_alinmayan"):
            for ad, n in t.get(kaynak, {}).items():
                assert isinstance(n, int) and n >= 0, f"{grup}.{ad} gecersiz destek: {n}"


def test_kalsifikasyon_paterni_bos_oldugu_belgelenmis(sema):
    """OLCULDU: popcorn 0 cumlede. Faz 3'un benign sozlugu buna dayanamaz.
    Sema bu uyariyi tasimali ki sonraki faz varsaymasin."""
    g = sema["niteleyici_gruplari"]["calcification_pattern"]
    assert g["olculup_alinmayan"]["popcorn"] == 0
    assert "uyari" in g


def test_radgraph_eslemesi_tum_kombinasyonlari_kapsar(sema):
    """entity_type x assertion kombinasyonlarinin hepsi RadGraph etiketine cevrilebilmeli;
    sapma 'kayipsiz' iddiasi ancak boyle savunulabilir."""
    esleme = sema["radgraph_eslemesi"]["varlik"]
    for tip in sema["varlik_tipleri"]:
        for kesinlik in sema["kontrollu_degerler"]["assertion"]["degerler"]:
            anahtar = f"{tip}+{kesinlik}"
            assert anahtar in esleme, f"{anahtar} eslemede hic gecmiyor"
            if kesinlik == "not_processed":
                # RadGraph her varliga kesinlik atamak ZORUNDA; islenmemis
                # durum eslenemez. Bunu gizlemek yerine null olarak belgeliyoruz.
                assert esleme[anahtar] is None, f"{anahtar} eslenmemeli"
            else:
                assert esleme[anahtar], f"{anahtar} eslenmemis"


def test_radgraph_iliski_eslemesi_tam(sema):
    esleme = sema["radgraph_eslemesi"]["iliski"]
    assert set(esleme) == set(sema["iliski_tipleri"])


def test_kayipli_sapma_acikca_isaretlenmis(sema):
    """change_of RadGraph-XL'de yok. Bunu 'kayipsiz' diye iddia etmek yanlis olurdu."""
    kayipli = [s for s in sema["sapmalar"] if not s["kayipsiz_mi"]]
    assert kayipli, "kayipli sapma isaretlenmemis"
    assert any("change" in s["ne"] for s in kayipli)


def test_kural_alanlari_zorunlu(sema):
    """D18: bag kuran kural kaydedilmeden iliski yazilamaz."""
    assert sema["tablolar"]["entities"]["kolonlar"]["extraction_rule"]["bos_olabilir"] is False
    assert sema["tablolar"]["relations"]["kolonlar"]["attachment_rule"]["bos_olabilir"] is False
    assert "belirsiz" in sema["baglama_kurallari"]["degerler"]


def test_surum_zinciri_semada_var(sema):
    """Her katman kendi surumunu tasir - Faz 1'de kopan zincir."""
    ent = sema["tablolar"]["entities"]["kolonlar"]
    for kol in ("segmentation_version", "template_version", "entity_version"):
        assert kol in ent and ent[kol]["bos_olabilir"] is False


def test_measurements_eki_yikici_degil(sema):
    """Mevcut olcu tablosuna yalnizca kolon EKLENIR."""
    ek = sema["tablolar"]["measurements_ek"]["kolonlar"]
    assert set(ek) == {"measurement_id", "temporality"}


# =====================================================================
# 2. DOGRULAYICI DAVRANISI
# =====================================================================

def _ent(**degis) -> pd.DataFrame:
    taban = {
        "entity_id": "e1", "study_id": "s1", "section": "findings", "sent_idx": 0,
        "char_start": 10, "char_end": 16, "raw_text": "nodule",
        "entity_type": "observation", "qualifier_group": None,
        "normalized_concept": "nodule", "concept_source": "yerel_sozluk",
        "laterality": "right", "assertion": "present", "temporality": "current",
        "change_type": "none", "mentioned_in_findings": True,
        "mentioned_in_impression": False, "promoted_to_impression": False,
        "extraction_rule": "sozluk_eslesme", "segmentation_version": "seg-1.1",
        "template_version": "tmpl-1.0", "entity_version": "ent-1.0",
    }
    taban.update(degis)
    return pd.DataFrame([taban])


def _rel(**degis) -> pd.DataFrame:
    taban = {
        "relation_id": "r1", "study_id": "s1", "head_id": "e1", "head_kind": "entity",
        "tail_id": "e2", "tail_kind": "entity", "relation_type": "located_at",
        "attachment_rule": "tek_aday", "is_cross_sentence": False,
        "entity_version": "ent-1.0", "relation_version": "rel-1.0",
    }
    taban.update(degis)
    return pd.DataFrame([taban])


def _ikili_ent() -> pd.DataFrame:
    a = _ent(entity_id="e1", entity_type="observation")
    b = _ent(entity_id="e2", entity_type="anatomy", raw_text="lung",
             char_start=20, char_end=24)
    return pd.concat([a, b], ignore_index=True)


def test_temiz_entity_gecer(sema):
    assert S.dogrula_entities(_ent(), sema) == []


def test_temiz_relation_gecer(sema):
    assert S.dogrula_relations(_rel(), sema, entities=_ikili_ent()) == []


def test_bos_cerceve_gecer(sema):
    """Hic varlik uretilmemis olmasi sema ihlali degildir."""
    bos = _ent().iloc[0:0]
    assert S.dogrula_entities(bos, sema) == []


def test_eksik_kolon_yakalanir(sema):
    ihl = S.dogrula_entities(_ent().drop(columns=["assertion"]), sema)
    assert ihl and ihl[0].kod == "K0"


def test_tanimsiz_varlik_tipi_yakalanir(sema):
    ihl = S.dogrula_entities(_ent(entity_type="lezyon"), sema)
    assert any(i.kod == "K3c" for i in ihl)


def test_tanimsiz_assertion_yakalanir(sema):
    ihl = S.dogrula_entities(_ent(assertion="negatif"), sema)
    assert any(i.kod == "K3c" for i in ihl)


def test_bos_extraction_rule_yakalanir(sema):
    """D18: kural kaydedilmeden varlik yazilamaz."""
    ihl = S.dogrula_entities(_ent(extraction_rule=""), sema)
    assert any(i.kod in ("K3", "K3d") for i in ihl)


def test_ters_ofset_yakalanir(sema):
    ihl = S.dogrula_entities(_ent(char_start=20, char_end=10), sema)
    assert any(i.kod == "K1b" for i in ihl)


def test_tekrarli_entity_id_yakalanir(sema):
    df = pd.concat([_ent(), _ent()], ignore_index=True)
    ihl = S.dogrula_entities(df, sema)
    assert any(i.kod == "K3b" for i in ihl)


def test_ofset_ham_metne_karsi_dogrulanir(sema):
    rep = pd.DataFrame([{"study_id": "s1", "report_text": "x" * 10 + "nodule" + "y" * 10}])
    assert S.dogrula_entities(_ent(), sema, reports=rep) == []
    ihl = S.dogrula_entities(_ent(raw_text="mass"), sema, reports=rep)
    assert any(i.kod == "K1" for i in ihl)


def test_varlik_cumle_disina_tasarsa_yakalanir(sema):
    sent = pd.DataFrame([{"study_id": "s1", "section": "findings", "sent_idx": 0,
                          "char_start": 12, "char_end": 30}])
    ihl = S.dogrula_entities(_ent(), sema, sentences=sent)   # varlik 10'da basliyor
    assert any(i.kod == "K1c" for i in ihl)


def test_surum_karisimi_yakalanir(sema):
    df = pd.concat([_ent(entity_id="e1"),
                    _ent(entity_id="e2", entity_version="ent-2.0")], ignore_index=True)
    ihl = S.dogrula_entities(df, sema)
    assert any(i.kod == "K3" and "entity_version" in i.kural for i in ihl)


def test_olmayan_iliski_ucu_yakalanir(sema):
    ihl = S.dogrula_relations(_rel(tail_id="e99"), sema, entities=_ikili_ent())
    assert any(i.kod == "K2" for i in ihl)


def test_iliski_tip_uyumsuzlugu_yakalanir(sema):
    """located_at'in hedefi anatomy olmali; observation kabul edilmemeli."""
    ent = pd.concat([_ent(entity_id="e1"),
                     _ent(entity_id="e2", entity_type="observation")], ignore_index=True)
    ihl = S.dogrula_relations(_rel(), sema, entities=ent)
    assert any(i.kod == "K2b" for i in ihl)


def test_modify_yonu_denetlenir(sema):
    """modify'in kaynagi niteleyici olmali (RadGraph yonu)."""
    ihl = S.dogrula_relations(_rel(relation_type="modify"), sema, entities=_ikili_ent())
    assert any(i.kod == "K2b" for i in ihl)


def test_calismalar_arasi_iliski_yakalanir(sema):
    ent = pd.concat([_ent(entity_id="e1"),
                     _ent(entity_id="e2", entity_type="anatomy", study_id="s2")],
                    ignore_index=True)
    ihl = S.dogrula_relations(_rel(), sema, entities=ent)
    assert any(i.kod == "K2c" for i in ihl)


def test_olcuye_baglanan_iliski_gecer(sema):
    olcu = pd.DataFrame([{"measurement_id": "m1", "study_id": "s1"}])
    rel = _rel(relation_id="r2", relation_type="measured_by",
               head_id="e1", head_kind="entity", tail_id="m1", tail_kind="measurement")
    assert S.dogrula_relations(rel, sema, entities=_ikili_ent(), measurements=olcu) == []


def test_organ_olcusu_iliskisi_gecer(sema):
    """Aort capi gibi olculer anatomiye baglanabilmeli - 10.627 cumle."""
    olcu = pd.DataFrame([{"measurement_id": "m1", "study_id": "s1"}])
    rel = _rel(relation_type="measured_by", head_id="e2", tail_id="m1",
               tail_kind="measurement")
    assert S.dogrula_relations(rel, sema, entities=_ikili_ent(), measurements=olcu) == []


def test_bos_attachment_rule_yakalanir(sema):
    ihl = S.dogrula_relations(_rel(attachment_rule=""), sema, entities=_ikili_ent())
    assert any(i.kod in ("K3", "K3d") for i in ihl)


def test_dogrula_veya_dur_hata_firlatir(sema):
    ihl = S.dogrula_entities(_ent(entity_type="lezyon"), sema)
    with pytest.raises(S.SemaHatasi):
        S.dogrula_veya_dur(ihl, "test")


def test_dogrula_veya_dur_temizde_sessiz(sema):
    S.dogrula_veya_dur(S.dogrula_entities(_ent(), sema))


def test_niteleyici_degerleri_atilanlari_icermez(sema):
    """Reddedilen degerler yanlislikla izinli kumeye sizmamali."""
    assert "ill_defined" not in S.niteleyici_degerleri(sema, "margin")
    assert "popcorn" not in S.niteleyici_degerleri(sema, "calcification_pattern")
