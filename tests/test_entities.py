# -*- coding: utf-8 -*-
"""TASK-11 varlik ve iliski cikarimi testleri.

Uc katman:
  1. Sozluk saglıgı      - desenler gecerli mi, sema ile tutarli mi
  2. Zor vaka takimi     - en uzun eslesme, taraf, ceviri artefaktlari (sabit)
  3. Korpus butunlugu    - uretilen tablolar uzerinde (varsa)
"""
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction import entities as E   # noqa: E402
from radyovlm.extraction import schema as S     # noqa: E402

ENT = ROOT / "data" / "processed" / "entities.parquet"
REL = ROOT / "data" / "processed" / "relations.parquet"
SENT = ROOT / "data" / "processed" / "sentences.parquet"
MEAS = ROOT / "data" / "processed" / "measurements.parquet"


@pytest.fixture(scope="module")
def sozluk():
    return E.sozlukleri_yukle()


@pytest.fixture(scope="module")
def cikar(sozluk):
    kavramlar, taraf = sozluk
    matcher, indeks = E.matcher_kur(kavramlar)
    td, ti = E.taraf_matcher(taraf)

    def _c(metin: str):
        vs = E.cumleden_varliklar(metin, matcher, indeks)
        tl = E.taraf_bul(metin, td, ti)
        for v in vs:
            v["taraf"] = (E.taraf_ata(tl, v["bas"], v["son"])
                          if v["kavram"].taraf_alir else None)
        return vs

    return _c


def _kavramlar(vs):
    return [v["kavram"].ad for v in vs]


# =====================================================================
# 1. SOZLUK SAGLIGI
# =====================================================================

def test_tum_desenler_derlenebilir(sozluk):
    kavramlar, taraf = sozluk
    for k in kavramlar:
        for d in k.desenler:
            re.compile(d, re.I)
    for kelimeler in taraf.values():
        for w in kelimeler:
            re.compile(w, re.I)


def test_desenlerde_yakalayan_grup_yok(sozluk):
    """Yakalayan grup birlesik regex'te grup numaralarini kaydirir ve
    eslesmeyi SESSIZCE bozar - matcher_kur bunu reddetmeli."""
    kavramlar, _ = sozluk
    for k in kavramlar:
        for d in k.desenler:
            assert not E._yakalayan_grup_var_mi(d), f"{k.ad}: {d}"


def test_kavram_adlari_tekil(sozluk):
    kavramlar, _ = sozluk
    adlar = [k.ad for k in kavramlar]
    assert len(adlar) == len(set(adlar)), "cakisan kavram adi var"


def test_varlik_tipleri_semaya_uyar(sozluk):
    kavramlar, _ = sozluk
    sema = S.yukle()
    izinli = set(sema["varlik_tipleri"])
    assert {k.tip for k in kavramlar} <= izinli


def test_niteleyici_gruplari_semaya_uyar(sozluk):
    """Sozlukteki her niteleyici grubu semada tanimli olmali."""
    kavramlar, _ = sozluk
    sema = S.yukle()
    izinli = {g for g in sema["niteleyici_gruplari"] if not g.startswith("_")}
    gruplar = {k.grup for k in kavramlar if k.tip == "qualifier"}
    assert gruplar <= izinli, f"semada olmayan grup: {gruplar - izinli}"


def test_niteleyiciler_semanin_reddettiklerini_icermez(sozluk):
    """Semada 'olculup_alinmayan' diye reddedilen degerler sozluge sizmamali.

    Karsilastirma GRUP DUYARLI olmali: ayni ad iki grupta farkli yargi tasiyabilir.
    Ilk hali gruptan bagimsizdi ve 'central' icin yanlis alarm verdi - distribution
    grubunda KABUL (3.240) ama kalsifikasyon paterninde RET (26). Bunun uzerine
    semadaki belirsiz ad 'central_calcification' olarak netlestirildi; test de
    dogru olcute cevrildi.
    """
    kavramlar, _ = sozluk
    sema = S.yukle()
    for grup, t in sema["niteleyici_gruplari"].items():
        if grup.startswith("_"):
            continue
        atilan = set(t.get("olculup_alinmayan", {}))
        sozlukte = {k.ad for k in kavramlar if k.tip == "qualifier" and k.grup == grup}
        sizan = sozlukte & atilan
        assert not sizan, f"{grup}: reddedilen deger sozlukte -> {sizan}"


def test_her_kavram_korpus_destegi_tasir(sozluk):
    """Sifir destekli kavram sozlukte durmamali - olculmemis terim demektir."""
    kavramlar, _ = sozluk
    sifir = [k.ad for k in kavramlar if k.korpus == 0]
    assert not sifir, f"korpus destegi sifir: {sifir}"


def test_taraf_sozlugu_both_iceriyor(sozluk):
    """OLCULDU: 'both' 95.616 cumle, 'bilateral' 32.789. Turkce 'her iki'nin
    cevirisi. Standart sozluk yalnizca 'bilateral' arar ve cogunu kacirir."""
    _, taraf = sozluk
    assert "both" in taraf["bilateral"]


# =====================================================================
# 2. ZOR VAKA TAKIMI  (sabit - her degisiklikte kosar)
# =====================================================================

def test_en_uzun_eslesme_upper_lobe(cikar):
    ad = _kavramlar(cikar("A nodule in the upper lobe of the right lung."))
    assert "upper_lobe" in ad
    assert "lung" in ad


def test_en_uzun_eslesme_hilar_axillary(cikar):
    """'hilar-axillary' bir lenf istasyonudur; 'hilar'a bolunmemeli."""
    ad = _kavramlar(cikar("No enlarged nodes in hilar-axillary areas."))
    assert "station_hilar_axillary" in ad
    assert "hilum" not in ad


def test_ceviri_artefakti_space_occupying(cikar):
    """Turkce 'yer kaplayici lezyon' -> tek bir gozlem, 'lesion' degil."""
    vs = cikar("Space-occupying lesion was not observed in the liver.")
    assert "space_occupying_lesion" in _kavramlar(vs)
    assert "lesion" not in _kavramlar(vs)


def test_ceviri_artefakti_effusion_thickening(cikar):
    """'effusion-thickening' tek bilesiktir; ikiye bolunmemeli."""
    vs = cikar("Pericardial effusion-thickening was not observed.")
    ad = _kavramlar(vs)
    assert "effusion_thickening" in ad
    assert "effusion" not in ad and "thickening" not in ad


def test_ceviri_artefakti_sequela(cikar):
    """'Sequela changes' gozlemdir; ciplak 'sequela' niteleyicidir."""
    assert "sequela_change" in _kavramlar(cikar("Sequela changes in the left lung."))
    assert "sequela" in _kavramlar(cikar("A sequela nodule is observed."))


def test_taraf_both_bilateral_olur(cikar):
    vs = cikar("Emphysematous changes are observed in both lungs.")
    lung = next(v for v in vs if v["kavram"].ad == "lung")
    assert lung["taraf"] == "bilateral"


def test_taraf_sag_atanir(cikar):
    vs = cikar("A nodule in the right lung.")
    assert next(v for v in vs if v["kavram"].ad == "lung")["taraf"] == "right"


def test_taraf_uzaktaki_ipucunu_almaz(cikar):
    """Taraf ipucu TARAF_PENCERE'den uzaksa atanmaz - o baska varliga aittir."""
    uzak = "The right lung is normal. " + "x" * 90 + " A cyst is observed in the liver."
    vs = cikar(uzak)
    liver = next(v for v in vs if v["kavram"].ad == "liver")
    assert liver["taraf"] is None


def test_niteleyici_ve_gozlem_ayrilir(cikar):
    vs = cikar("A spiculated nodule is observed.")
    tipler = {v["kavram"].ad: v["kavram"].tip for v in vs}
    assert tipler["spiculated"] == "qualifier"
    assert tipler["nodule"] == "observation"


def test_lenf_istasyonlari_ayri_ayri_cikar(cikar):
    ad = _kavramlar(cikar(
        "No pathologically enlarged lymph nodes were detected in prevascular, "
        "pre-paratracheal, subcarinal, hilar-axillary areas."))
    for st in ("station_prevascular", "station_paratracheal",
               "station_subcarinal", "station_hilar_axillary"):
        assert st in ad, f"{st} cikarilmadi"


def test_organ_segmenti_akcigere_atanmaz(cikar):
    """'liver segment 8' akciger segmenti DEGILDIR. Desen ayirt edemez;
    bu yuzden kavram genel tutuldu, yanlis ust kavram iddia edilmiyor."""
    ad = _kavramlar(cikar("A lesion in liver segment 8."))
    assert "anatomic_segment" in ad
    assert "lung_segment" not in ad


def test_cihaz_gozlemden_ayrilir(cikar):
    """'port kateter ucu' bir bulgu degil, cihazdir - karistirilirsa
    yanlis pozitif uretir."""
    vs = cikar("The tip of the port catheter is in the right atrium.")
    assert any(v["kavram"].tip == "device" for v in vs)


# --------------------------- iliski kurallari ---------------------------

def test_tek_aday_kurali(cikar):
    vs = cikar("A nodule is observed in the liver.")
    rel, _ = E.iliskileri_kur(vs, [], "A nodule is observed in the liver.")
    la = [r for r in rel if r["tip"] == "located_at"]
    assert la and la[0]["kural"] == "tek_aday"


def test_en_yakin_anatomi_secilir(cikar):
    t = "A nodule in the upper lobe of the right lung."
    rel, _ = E.iliskileri_kur(cikar(t), [], t)
    la = next(r for r in rel if r["tip"] == "located_at")
    assert la["tail"]["kavram"].ad == "upper_lobe"


def test_esit_uzaklikta_bag_kurulmaz():
    """D18: tahmine dayali bag SESSIZCE kurulmaz."""
    sahte = lambda ad, tip, b, s: {  # noqa: E731
        "kavram": E.Kavram(ad, tip, []), "bas": b, "son": s, "metin": ad}
    varliklar = [sahte("lung", "anatomy", 0, 4),
                 sahte("nodule", "observation", 6, 12),
                 sahte("liver", "anatomy", 14, 19)]
    rel, coz = E.iliskileri_kur(varliklar, [], "lung  nodule  liver")
    assert not [r for r in rel if r["tip"] == "located_at"]


def test_olcu_en_yakin_gozleme_baglanir(cikar):
    t = "A 13 mm hypodense lesion in the liver."
    vs = cikar(t)
    olcu = [{"id": "m1", "bas": t.index("13 mm"), "son": t.index("13 mm") + 5}]
    rel, _ = E.iliskileri_kur(vs, olcu, t)
    mb = next(r for r in rel if r["tip"] == "measured_by")
    assert mb["head"]["kavram"].ad == "lesion"


def test_organ_olcusu_anatomiye_baglanir(cikar):
    """10.627 cumlede olcu var ama lezyon adi yok - aort capi gibi."""
    t = "Thoracic aorta diameter is 34 mm."
    vs = cikar(t)
    olcu = [{"id": "m1", "bas": t.index("34 mm"), "son": t.index("34 mm") + 5}]
    rel, _ = E.iliskileri_kur(vs, olcu, t)
    mb = next(r for r in rel if r["tip"] == "measured_by")
    assert mb["head"]["kavram"].tip == "anatomy"
    assert mb["head"]["kavram"].ad == "aorta"


def test_en_buyugu_kalibinda_dogru_hedef(cikar):
    """'the largest of which is N mm' kalibi.

    Ilk hali kural ADININ 'en_buyugu_ifadesi' olmasini sinaviordu. Konum eleyicisi
    eklenince etiket 'konum_edati_atlandi' oldu - cunku hedefi BELIRLEYEN kural
    oydu; 'in the mediastinum' ve 'in the prevascular area' elendi, geriye tek
    aday kaldi. Etiket degisti ama SONUC duzeldi. Test asil iddiaya cevrildi:
    olculen sey lenf nodudur, mediasten veya istasyon degil.
    """
    t = ("Several lymph nodes were seen in the mediastinum, the largest of "
         "which is 9 mm in the prevascular area.")
    vs = cikar(t)
    olcu = [{"id": "m1", "bas": t.index("9 mm"), "son": t.index("9 mm") + 4}]
    rel, _ = E.iliskileri_kur(vs, olcu, t)
    mb = next(r for r in rel if r["tip"] == "measured_by")
    assert mb["head"]["kavram"].ad == "lymph_node"


def test_niteleyici_gozleme_baglanir(cikar):
    t = "A spiculated nodule in the lung."
    rel, _ = E.iliskileri_kur(cikar(t), [], t)
    mod = next(r for r in rel if r["tip"] == "modify")
    assert mod["head"]["kavram"].ad == "spiculated"
    assert mod["tail"]["kavram"].tip == "observation"


# =====================================================================
# 3. KORPUS BUTUNLUGU  (uretilen tablolar varsa)
# =====================================================================

@pytest.fixture(scope="module")
def ent():
    if not ENT.exists():
        pytest.skip("entities.parquet henuz uretilmedi")
    return pd.read_parquet(ENT)


@pytest.fixture(scope="module")
def rel():
    if not REL.exists():
        pytest.skip("relations.parquet henuz uretilmedi")
    return pd.read_parquet(REL)


def test_korpus_sema_dogrulamasindan_gecer(ent, rel):
    sema = S.yukle()
    sent = pd.read_parquet(SENT)
    reps = pd.read_parquet(ROOT / "data/processed/reports_study_level.parquet",
                           columns=["study_id", "report_text"])
    meas = pd.read_parquet(MEAS)
    ihl = S.dogrula_entities(ent, sema, sentences=sent, reports=reps)
    ihl += S.dogrula_relations(rel, sema, entities=ent, measurements=meas)
    assert not ihl, "\n".join(str(i) for i in ihl)


def test_korpus_ofsetleri_metne_oturuyor(ent):
    reps = pd.read_parquet(ROOT / "data/processed/reports_study_level.parquet",
                           columns=["study_id", "report_text"])
    metin = dict(zip(reps.study_id, reps.report_text))
    kotu = [r.entity_id for r in ent.itertuples(index=False)
            if metin[r.study_id][r.char_start:r.char_end] != r.raw_text]
    assert not kotu, f"{len(kotu)} varligin ofseti oturmuyor"


def test_korpus_varliklar_cakismiyor(ent):
    """Ayni cumlede iki varlik ayni karakteri paylasmamali - en uzun eslesme
    kurali bunu garanti etmeli."""
    s = ent.sort_values(["study_id", "section", "sent_idx", "char_start"])
    onceki_son = s.groupby(["study_id", "section", "sent_idx"])["char_end"].shift()
    cakisan = (s.char_start < onceki_son).sum()
    assert cakisan == 0, f"{cakisan} varlik cakisiyor"


def test_korpus_measurement_id_uretilmis():
    meas = pd.read_parquet(MEAS)
    if "measurement_id" not in meas.columns:
        pytest.skip("meas-1.1 henuz uretilmedi")
    assert meas.measurement_id.is_unique
    assert meas.measurement_version.iloc[0] in ("meas-1.1", "meas-1.2")


def test_korpus_surum_zinciri_tam(ent, rel):
    for kol in ("segmentation_version", "template_version", "entity_version"):
        assert ent[kol].nunique() == 1, f"{kol} tekil degil"
    assert rel.entity_version.nunique() == 1
    assert rel.relation_version.nunique() == 1


def test_korpus_iliski_tip_uyumu(ent, rel):
    """located_at'in hedefi her zaman anatomi olmali."""
    tip = dict(zip(ent.entity_id, ent.entity_type))
    la = rel[(rel.relation_type == "located_at") & (rel.tail_kind == "entity")]
    kotu = [t for t in la.tail_id if tip.get(t) != "anatomy"]
    assert not kotu, f"{len(kotu)} located_at anatomi disina bagli"


def test_korpus_belirsiz_bag_yazilmamis(rel):
    """D18: 'belirsiz' bir bag KURULMAMASI demektir; tabloda gorunmemeli."""
    assert (rel.attachment_rule == "belirsiz").sum() == 0


def test_korpus_impression_bos_calismalar_dislanmis(ent):
    """D14/D19 tuzagi: 'Not given.' yazan 825 calisma Impression'a sahipmis
    gibi gorunur; onem sinyalinden dislanmali."""
    reps = pd.read_parquet(ROOT / "data/processed/reports_study_level.parquet",
                           columns=["study_id", "impression_is_null"])
    bos = set(reps.loc[reps.impression_is_null, "study_id"])
    sizan = ent[ent.study_id.isin(bos) & ent.promoted_to_impression]
    assert len(sizan) == 0, f"{len(sizan)} varlik bos Impression'dan sinyal almis"


# =====================================================================
# 4. INCELEME DUZELTMELERI  (her biri bulunan gercek bir kusurun regresyonu)
# =====================================================================

def test_azami_eslesme_uzunlugu_desen_uzunlugundan_bagimsiz():
    """KOK KUSUR: siralama DESEN metninin uzunluguna gore yapiliyordu.
    'athero(?:sclerosis|sclerotic|matous)' 36 karakterlik desen ama en fazla
    15 karakter esler; 'atheromatous plaques?' 21 karakterlik desen 20 karakter
    esler. Uzun desen once denendigi icin kisa desen daha COK metin esledigi
    hâlde kaybediyordu."""
    uzun_desen = r"athero(?:sclerosis|sclerotic|matous)"
    kisa_desen = r"atheromatous plaques?"
    assert len(uzun_desen) > len(kisa_desen)                      # desen uzunlugu
    assert E.azami_eslesme_uzunlugu(uzun_desen) < \
           E.azami_eslesme_uzunlugu(kisa_desen)                   # eslesme uzunlugu


def test_atheromatous_plaques_tek_anma(cikar):
    """2.021 vakada 'atheromatous plaques' IKI ayri atheroma_plaque anmasi
    uretiyordu."""
    vs = [v for v in cikar("Atheromatous plaques are observed in the aorta.")
          if v["kavram"].ad == "atheroma_plaque"]
    assert len(vs) == 1, [v["metin"] for v in vs]
    assert vs[0]["metin"].lower() == "atheromatous plaques"


def test_bitisik_ayni_kavram_birlesir_virgullu_ayri_kalir(cikar):
    """Birlestirme yalnizca TEK bosluk/tire araligi icin; virgulle ayrilmis
    iki anma AYRI kalmali."""
    vs = [v for v in cikar("Calcific plaques, plaques are seen.")
          if v["kavram"].ad == "atheroma_plaque"]
    assert len(vs) == 2


def test_liver_parenchyma_akciger_olmaz(cikar):
    """'liver parenchyma' 2.191 cumlede geciyordu ve AKCIGER parankimi
    sayiliyordu. Ciplak bicim artik organsiz 'parenchyma'."""
    ad = _kavramlar(cikar("Liver parenchyma is heterogeneous."))
    assert "parenchyma" in ad
    assert "lung_parenchyma" not in ad


def test_lung_parenchyma_hala_calisiyor(cikar):
    ad = _kavramlar(cikar("Lung parenchyma is normal."))
    assert "lung_parenchyma" in ad


def test_centriacinar_nodul_amfizem_olmaz(cikar):
    """OLCULDU: 'centriacinar' gecen 1.413 cumlenin 757'si NODUL, 257'si
    amfizem. Ciplak bicim amfizem sayilamaz."""
    ad = _kavramlar(cikar("Centriacinar nodules in both lungs."))
    assert "nodule" in ad
    assert "emphysema" not in ad


def test_centriacinar_amfizem_hala_calisiyor(cikar):
    assert "emphysema" in _kavramlar(cikar("Centriacinar emphysema in both lungs."))


def test_ciplak_density_artis_iddia_etmez(cikar):
    """'decrease in density' ARTIS olarak isaretleniyordu (1.389 cumle).
    Kavram adi metnin soylemedigi bir seyi iddia ediyordu."""
    ad = _kavramlar(cikar("There is a decrease in density in the left lower lobe."))
    assert "density" in ad
    assert "density_increase" not in ad


def test_gercek_density_increase_hala_calisiyor(cikar):
    assert "density_increase" in _kavramlar(cikar("Density increases are observed."))


def test_olcu_organa_degil_bulguya_baglanir(cikar):
    """'The pleural effusion in the right lung reaches 10 cm' -> olculen sey
    EFUZYON, akciger degil. Duz 'en yakin' kurali sistematik olarak yaniliyordu."""
    t = "The pleural effusion in the right lung reaches approximately 10 cm."
    vs = cikar(t)
    olcu = [{"id": "m1", "bas": t.index("10 cm"), "son": t.index("10 cm") + 5}]
    rel, _ = E.iliskileri_kur(vs, olcu, t)
    mb = next(r for r in rel if r["tip"] == "measured_by")
    assert mb["head"]["kavram"].ad == "effusion"
    assert mb["kural"] == "gozlem_onceligi"


def test_konum_edati_ardindaki_anatomi_atlanir(cikar):
    """'in the mediastinal area' bulgunun YERIDIR, olculen sey degil."""
    t = "Lymph nodes with a short axis smaller than 7 mm were observed in the mediastinal area."
    vs = cikar(t)
    olcu = [{"id": "m1", "bas": t.index("7 mm"), "son": t.index("7 mm") + 4}]
    rel, _ = E.iliskileri_kur(vs, olcu, t)
    mb = next(r for r in rel if r["tip"] == "measured_by")
    assert mb["head"]["kavram"].ad == "lymph_node"


def test_gozlem_onceligi_organ_olcusunu_bozmaz(cikar):
    """GERILEME TESTI: gozlem onceligi ilk denemede KOSULSUZDU ve
    'The ascending aorta is 39 mm and ectatic' cumlesinde olcuyu aort yerine
    'ectatic'e bagladi. Kural daraltildi; bu test onu koruyor."""
    t = "The ascending aorta is 39 mm and ectatic."
    vs = cikar(t)
    olcu = [{"id": "m1", "bas": t.index("39 mm"), "son": t.index("39 mm") + 5}]
    rel, _ = E.iliskileri_kur(vs, olcu, t)
    mb = next(r for r in rel if r["tip"] == "measured_by")
    assert mb["head"]["kavram"].ad == "aorta"


def test_cozulemeyen_baglar_dusurulmez():
    """D18 'belirsiz bag sessizce kurulmaz' diyor; sema-1.0'da bu baglar
    tamamen DUSURULUYORDU, yani sessizce yok oluyorlardi. K9 olcutu
    onlardan uretilecek."""
    sahte = lambda ad, tip, b, s: {  # noqa: E731
        "kavram": E.Kavram(ad, tip, []), "bas": b, "son": s, "metin": ad}
    varliklar = [sahte("lung", "anatomy", 0, 4),
                 sahte("nodule", "observation", 6, 12),
                 sahte("liver", "anatomy", 14, 19)]
    rel, coz = E.iliskileri_kur(varliklar, [], "lung  nodule  liver")
    assert not [r for r in rel if r["tip"] == "located_at"]
    assert any(c["sebep"] == "belirsiz" for c in coz)


def test_aday_yok_kaydedilir():
    """Cumlede hic varlik yoksa olcu 'aday_yok' olarak kaydedilmeli."""
    rel, coz = E.iliskileri_kur([], [{"id": "m1", "bas": 0, "son": 4}], "5 mm")
    assert not rel
    assert coz and coz[0]["sebep"] == "aday_yok"


def test_sema_surumu_guncel(sozluk):
    sema = S.yukle()
    assert sema["schema_version"] == "sema-1.3"


def test_assertion_varsayilani_islenmemis():
    """TASK-12 kosmadan 'present' yazmak sessizce yanlis veriydi:
    negasyon ipuclu cumlelerdeki 426.099 anma da 'mevcut' gorunuyordu."""
    sema = S.yukle()
    a = sema["kontrollu_degerler"]["assertion"]
    assert a["varsayilan"] == "not_processed"
    assert "not_processed" in a["degerler"]
    assert sema["kontrollu_degerler"]["temporality"]["varsayilan"] == "unknown"


def test_niteleyici_kavramlari_semanin_degerleriyle_ortusur(sozluk):
    """K3e'nin sozluk tarafi: sozlukteki her niteleyici, semada o grubun
    KABUL EDILEN degerleri arasinda olmali. Onceki surumde yalnizca grup ADI
    denetleniyordu ve sema ile sozluk sessizce ayrisabiliyordu."""
    kavramlar, _ = sozluk
    sema = S.yukle()
    for k in kavramlar:
        if k.tip != "qualifier":
            continue
        izinli = set(sema["niteleyici_gruplari"][k.grup]["degerler"])
        assert k.ad in izinli, f"{k.ad} semada {k.grup} grubunda tanimli degil"


def test_sema_niteleyici_degerleri_sozlukte_var(sozluk):
    """Ters yon: semada tanimli her niteleyici degerinin sozlukte karsiligi
    olmali. Yoksa sema hicbir zaman uretilemeyecek bir deger vaat ediyor."""
    kavramlar, _ = sozluk
    sema = S.yukle()
    sozlukte = {k.ad for k in kavramlar if k.tip == "qualifier"}
    for grup, t in sema["niteleyici_gruplari"].items():
        if grup.startswith("_"):
            continue
        eksik = set(t["degerler"]) - sozlukte
        assert not eksik, f"{grup}: semada var, sozlukte yok -> {sorted(eksik)}"


def test_hicbir_olcu_sessizce_dusmez():
    """BUTUNLUK: her olcu ya baglanir ya cozulemeyen olarak kaydedilir.
    Ilk surumde varlik CIKMAYAN cumleler tamamen atlaniyordu ve icindeki
    805 olcu ne baglaniyor ne kaydediliyordu - sessizce yok oluyorlardi."""
    P = ROOT / "data" / "processed"
    if not (P / "unresolved_attachments.parquet").exists():
        pytest.skip("cozulemeyen bag tablosu henuz uretilmedi")
    meas = pd.read_parquet(P / "measurements.parquet")
    rel = pd.read_parquet(P / "relations.parquet")
    coz = pd.read_parquet(P / "unresolved_attachments.parquet")
    bagli = set(rel.loc[rel.relation_type == "measured_by", "tail_id"])
    kayitli = set(coz.loc[coz.source_kind == "measurement", "source_id"])
    kayip = set(meas.measurement_id) - bagli - kayitli
    assert not kayip, f"{len(kayip)} olcu ne baglandi ne kaydedildi"
