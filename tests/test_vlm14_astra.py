"""SUDE-VLM-14 · Adim 1 gerileme testleri.

Sozlesme: docs/39_astra_veri_sozlesmesi.md §11
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.extraction import astra as A  # noqa: E402
CIKTI = KOK / "data/processed/astra_sentences.parquet"
KILIT = KOK / "configs/splits_astra.json"

YASAK_KOLONLAR = {
    "Kanser_Etiketi_y", "Censor_Time", "Pillar_Ensemble_Skoru",
    "Kanser_Yil_1", "Kanser_Yil_2", "Y_Seq", "Y_Mask",
}


@pytest.fixture(scope="module")
def cumleler() -> pd.DataFrame:
    if not CIKTI.exists():
        pytest.skip("astra_sentences.parquet yok - scripts/60 kosulmali")
    return pd.read_parquet(CIKTI)


@pytest.fixture(scope="module")
def kilit() -> dict:
    return json.loads(KILIT.read_text(encoding="utf-8"))


# --- 1 · `normal` baslik degil, degerdir (§2.2) -----------------------------

def test_normal_baslik_sayilmaz():
    rapor = (
        "**Lung:**\n"
        "- **Normal:** No masses, calcifications, or asymmetries observed.\n"
        "- **Emphysema:** Mild centrilobular emphysema is present.\n"
    )
    bolumler = A.bolumlere_ayir(rapor)
    adlar = [A.normalize_baslik(b) for b, _ in bolumler]
    assert "normal" not in adlar, "`normal` bolum basligi olarak acilmamali"
    # Icerigi ebeveyn bolumde kalmali
    birlesik = " ".join(i for _, i in bolumler)
    assert "No masses" in birlesik


def test_taninmayan_kalin_etiket_bolum_acmaz():
    rapor = "**Lung:**\n- **Findings of note:** a nodule is seen.\n"
    bolumler = A.bolumlere_ayir(rapor)
    assert len(bolumler) == 1
    assert A.normalize_baslik(bolumler[0][0]) == "lung"


# --- 2 · Tanimsiz baslik kapsam ici olamaz (§4, fail-closed) ---------------

def test_bilinmeyen_baslik_kapsam_disi():
    kova, kapsam_ici, bilinmeyen = A.bolum_esle("Quantum Flux Analysis")
    assert bilinmeyen is True
    assert kapsam_ici is False
    assert kova == "bilinmeyen"


def test_uretilen_veride_tanimsiz_baslik_kapsam_ici_degil(cumleler):
    ihlal = cumleler[cumleler["bilinmeyen_baslik"] & cumleler["kapsam_ici"]]
    assert len(ihlal) == 0, f"{len(ihlal)} satir hem bilinmeyen hem kapsam ici"


# --- 3 · Cumle anahtari benzersiz (§8, D96) --------------------------------

def test_cumle_anahtari_benzersiz(cumleler):
    anahtar = cumleler[["seri_anahtari", "bolum_ham", "cumle_idx"]]
    assert len(anahtar) == len(anahtar.drop_duplicates()), (
        "(seri_anahtari, bolum_ham, cumle_idx) benzersiz olmali - D96")


# --- 4 · Kayipsiz islem ----------------------------------------------------

def test_tum_seriler_islendi(cumleler, kilit):
    assert cumleler["seri_anahtari"].nunique() == kilit["kaynak"]["ham_seri"]


def test_split_sayilari_kilide_uyar(cumleler, kilit):
    dahil = cumleler[cumleler["included_in_evaluation"]]
    for ad in ("train", "dev", "held_out"):
        uretilen = dahil.loc[dahil["split"] == ad, "seri_anahtari"].nunique()
        assert uretilen == kilit["bolunme"][ad]["seri"], (
            f"{ad}: {uretilen} != kilit {kilit['bolunme'][ad]['seri']}")


def test_dislanan_seriler_isaretli(cumleler, kilit):
    haric = cumleler.loc[~cumleler["included_in_evaluation"], "seri_anahtari"]
    assert haric.nunique() == kilit["filtre"]["dislanan_seri"]


# --- 5 · Teknik satir deseni `mass` ile ESLESMEZ (§7.3) --------------------

def test_mass_teknik_sayilmaz():
    assert not A.teknik_satir_mi(
        "a mass measuring 12 mm in the right upper lobe")
    assert not A.teknik_satir_mi("multiple masses are seen")


def test_gercek_teknik_satir_yakalanir():
    assert A.teknik_satir_mi("Slice thickness: 5 mm")
    assert A.teknik_satir_mi("Reconstruction interval: 5 mm")


def test_uretilen_veride_mass_cumleleri_teknik_degil(cumleler):
    mass = cumleler[cumleler["cumle_metni"].str.contains(r"(?i)\bmass")]
    assert len(mass) > 0, "kontrol anlamsiz olurdu"
    assert mass["is_technical_param"].sum() == 0, (
        "`mass` gecen cumle teknik parametre sayilamaz - docs/39 §7.1")


def test_ciplak_interval_teknik_degil():
    assert not A.teknik_satir_mi("There is no interval growth of the nodule.")


# --- 6 · Etiket kolonu sizmasi (§6) ---------------------------------------

def test_etiket_kolonu_sizmadi(cumleler):
    sizan = YASAK_KOLONLAR & set(cumleler.columns)
    assert not sizan, f"etiket kolonu sizdi: {sorted(sizan)}"


def test_betik_yalniz_izinli_kolonlari_okur():
    kaynak = (KOK / "scripts/60_vlm14_astra_metin_katmani.py").read_text(
        encoding="utf-8")
    assert 'IZINLI_KOLONLAR = ["PID", "Seri_Anahtari", "Radyoloji_Raporu"]' in kaynak
    assert "usecols=IZINLI_KOLONLAR" in kaynak


# --- 7 · Kapsam kovalari (§3) ---------------------------------------------

def test_dis_organ_kapsam_disi():
    for ad in ("breast", "thyroid", "liver", "bone", "heart", "esophagus"):
        _, kapsam_ici, _ = A.bolum_esle(ad)
        assert kapsam_ici is False, f"{ad} kapsam disi olmali"


def test_toraks_ve_mediasten_kapsam_ici():
    for ad in ("lung", "pleura", "trachea and bronchie", "mediastinum"):
        _, kapsam_ici, _ = A.bolum_esle(ad)
        assert kapsam_ici is True, f"{ad} kapsam ici olmali"


def test_chest_ct_oneki_normalize_edilir():
    assert A.normalize_baslik("Chest CT Abdomen") == "abdomen"
    kova, kapsam_ici, bilinmeyen = A.bolum_esle("**Chest CT Lung:**")
    assert bilinmeyen is False and kapsam_ici is True and kova == "toraks"


# --- 8 · Baslıksiz metin (§5) ---------------------------------------------

def test_basliksiz_metin_ayri_kovaya_duser():
    bolumler = A.bolumlere_ayir("Some preamble text.\n\n**Lung:**\nClear.")
    assert bolumler[0][0] == A.BASSIZ
    assert "preamble" in bolumler[0][1]


# --- 9 · Markdown `#` sozdizimi de taninir (§2.0) --------------------------

def test_markdown_basligi_taninir():
    bolumler = A.bolumlere_ayir("# Lung\nNo nodules.\n## Pleura\nNormal.")
    adlar = [A.normalize_baslik(b) for b, _ in bolumler]
    assert "lung" in adlar and "pleura" in adlar


# --- 10 · Kolon sozlesmesi (Adim 4, astra-adaptor-1.0) ---------------------

def test_lob_cozumleme():
    from radyovlm.evaluation import vlm14 as V
    assert V.lob_coz("a nodule in the right upper lobe") == "RUL"
    assert V.lob_coz("lower lobe of the left lung") == "LLL"
    assert V.lob_coz("no lobar information here") is None


def test_sablon_istatistigi_yalniz_trainden():
    """AGENTS §4: sablon istatistigi valid/test'ten hesaplanamaz."""
    from radyovlm.evaluation import vlm14 as V
    import inspect
    kaynak = inspect.getsource(V.sablon_kolonu_ekle)
    assert 'c["split"].eq("train")' in kaynak, (
        "sablon istatistigi YALNIZ train'den hesaplanmali - D4/AGENTS §4")


def test_kilit_baglayici_kisitlari_tasir():
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    assert kilit["surum"] == "astra-adaptor-1.2"
    metin = " ".join(kilit["baglayici_kisitlar"])
    assert "Surekli olasilik URETILMEZ" in metin
    assert "teknik parametre satirindan ASLA alinmaz" in metin
    assert "SAYILIR" in metin          # sessiz kayip yasagi


def test_surekli_olasilik_kolonu_uretilmez():
    """VLM-20 hedef sizintisi korumasi: kural motoru olasilik uretmez."""
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    kolonlar = set(kilit["A_tablosu_kolonlari"]) | set(kilit["B_tablosu_kolonlari"])
    yasak = {"suphe_olasiligi", "olasilik", "probability", "risk_skoru", "score"}
    assert not (kolonlar & yasak), f"olasilik kolonu uretilemez: {kolonlar & yasak}"


def test_lung_rads_kolonu_uretilmez():
    """Karar 2026-09-08: Lung-RADS gercek hekim raporu kohortuna tasindi."""
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    kolonlar = set(kilit["A_tablosu_kolonlari"]) | set(kilit["B_tablosu_kolonlari"])
    assert not [k for k in kolonlar if "lung_rads" in k.lower()]


def test_nodul_var_mi_uc_degerli():
    """`not_assessable` != `false` - kanit yoklugu, yokluk kaniti degildir."""
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    d = kilit["train_dogrulamasi"]["nodul_var_mi"]
    assert "not_assessable" in d and "false" in d and "true" in d


def test_ekstratorasik_eleme_sayiliyor():
    """Sessiz kayip yasak: elenen malignite kaniti sayilmis olmali."""
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    assert kilit["train_dogrulamasi"]["ekstratorasik_elenen_seri"] > 0


def test_sema_surumu_dondurulmus():
    from radyovlm.evaluation import sema
    assert sema.SEMA_SURUMU == "sema-1.0", "Faz A'da donduruldu"


# --- 11 · Iliski katmanindan turetilen kolonlar (Ç4, Ç5) -------------------

ILISKI = KOK / "data/processed/astra_relations_train.parquet"
VARLIK = KOK / "data/processed/astra_entities_train.parquet"


def test_supheli_niteleyici_sabit_false_degil():
    """`False` sabitlemek C#nodul-kalip'in bir dalini SESSIZCE oldurur."""
    if not ILISKI.exists():
        pytest.skip("iliski katmani yok - scripts/61 kosulmali")
    from radyovlm.evaluation import vlm14 as V
    v = pd.read_parquet(VARLIK)
    r = pd.read_parquet(ILISKI)
    v2 = V.supheli_niteleyici_ekle(v, r)
    assert v2["supheli_niteleyici"].sum() > 0, (
        "modify iliskilerinden en az bir supheli niteleyici cikmali")


def test_boyut_yalniz_L1_kaynagindan():
    if not ILISKI.exists():
        pytest.skip("iliski katmani yok")
    from radyovlm.evaluation import vlm14 as V
    v = pd.read_parquet(VARLIK)
    r = pd.read_parquet(ILISKI)
    b = V.boyut_ekle(V.kanit_tablosu(v), r)
    dolu = b[b["boyut_mm"].notna()]
    assert len(dolu) > 0
    assert set(dolu["boyut_bag_duzeyi"]) == {"L1"}, (
        "boyut_mm YALNIZ L1'den gelir - L2/L3/L4 girmez")


def test_teknik_olcu_boyuta_sizmaz():
    """Teknik parametre olculeri iliski katmanina HIC girmez (scripts/61)."""
    for betik in ("scripts/61_vlm14_train_aktarim_denetimi.py",
                  "scripts/62_vlm14_olculebilirlik_envanteri.py",
                  "scripts/63_vlm14_tam_kosum.py"):
        kaynak = (KOK / betik).read_text(encoding="utf-8")
        assert "A.olcu_teknik_mi(metin, m.start(), m.end())" in kaynak, betik
        assert "olcu07.teknik_mi" not in kaynak, (
            f"{betik}: iki teknik tanimi olmamali - K5.1")


def test_varlik_kimligi_benzersiz():
    if not VARLIK.exists():
        pytest.skip("varlik tablosu yok")
    v = pd.read_parquet(VARLIK)
    assert v["entity_id"].nunique() == len(v)


def test_iliski_kimlikleri_cozulur():
    if not ILISKI.exists():
        pytest.skip("iliski katmani yok")
    v = pd.read_parquet(VARLIK)
    r = pd.read_parquet(ILISKI)
    assert r["head_id"].isin(set(v["entity_id"])).all(), (
        "her iliski head_id'si varlik tablosunda cozulmeli")


# --- 12 · Sozlesme uyum denetimi duzeltmeleri (astra-adaptor-1.1) ----------

def test_K1_eksik_zenginlestirme_hata_verir():
    """Alan yoklugu normal deger sayilmaz - iki kez sessiz olume yol acti."""
    from radyovlm.evaluation import vlm14 as V
    v = pd.DataFrame({"entity_id": ["a"], "seri_anahtari": ["s"],
                      "bolum_ham": ["lung"], "cumle_idx": [0],
                      "kapsam_ici": [True], "normalized_concept": ["nodule"],
                      "assertion": ["present"], "sablon_cumle": [False]})
    with pytest.raises(ValueError, match="zenginlestirme alani eksik"):
        V._sema_girdisi(v)


def test_K5_1_teknik_tanimi_tekil():
    """Denetimin sentetik vakasi: iki tanim ayrisiyordu."""
    import re
    c = "Tube current 100 mAs; reconstructed at 5 mm."
    m = re.search(r"\d+\s*(mm|cm)", c)
    assert A.olcu_teknik_mi(c, m.start(), m.end()) is True
    # Klinik olcu teknik sayilmamali
    c2 = "a mass measuring 12 mm in the right upper lobe"
    m2 = re.search(r"\d+\s*(mm|cm)", c2)
    assert A.olcu_teknik_mi(c2, m2.start(), m2.end()) is False


def test_K5_2_anatomi_duzeyi_eleme():
    """Ozet bolumunde karaciger metastazi elenmeli, toraks kaniti kalmali."""
    if not ILISKI.exists():
        pytest.skip("iliski katmani yok")
    from radyovlm.evaluation import vlm14 as V
    v = pd.read_parquet(VARLIK)
    r = pd.read_parquet(ILISKI)
    ekst = V.ekstratorasik_varliklar(v, r)
    assert len(ekst) > 0, "located_at ile akciger disi organ bulunmali"
    # Elenenlerin hicbiri akciger anatomisine bagli olmamali
    kavram = dict(zip(v["entity_id"], v["normalized_concept"]))
    la = r[r["relation_type"].eq("located_at")]
    for eid in list(ekst)[:200]:
        hedefler = set(la.loc[la["head_id"].eq(eid), "tail_id"].map(kavram))
        assert hedefler & V.EKSTRATORASIK_ANATOMI, eid


def test_K5_2_bayraklar_ayristirildi():
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    kolonlar = set(kilit["A_tablosu_kolonlari"])
    assert "qf_ekstratorasik_malignite_elendi" in kolonlar
    assert "qf_bilinmeyen_bolum_malignite" in kolonlar, (
        "organ kaynakli eleme ile bilinmeyen/meta kaybi ayri sayilmali")


def test_K5_3_mediastinum_bayragi_uretiliyor():
    """Sozlesme vaat etmisti; 1.0'da uretilmiyordu."""
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    assert "qf_mediastinum_kaynakli" in set(kilit["A_tablosu_kolonlari"])
    assert kilit["train_dogrulamasi"]["mediastinum_kaynakli_seri"] > 0


def test_K5_5_seri_ozeti_zorunlu_parametreler():
    """Sessiz varsayilan `measurement_available`i her seride False yapiyordu."""
    import inspect
    from radyovlm.evaluation import vlm14 as V
    imza = inspect.signature(V.seri_ozeti)
    for ad in ("boyutlu_seriler", "iliskiler"):
        assert imza.parameters[ad].default is inspect.Parameter.empty, (
            f"`{ad}` zorunlu olmali - K5.5")


def test_kemik_yapilar_anatomi_filtresinde_degil():
    """C5-03 (`vertebrae` metastazi) hedefi known_malignancy - sema sayar."""
    from radyovlm.evaluation import vlm14 as V
    for ad in ("bone", "rib", "vertebra", "sternum"):
        assert ad not in V.EKSTRATORASIK_ANATOMI


def test_kilit_kod_surumleriyle_tutarli():
    """Bayat kilit sinifi: kod surumu ile kilit surumu ayrisamaz."""
    from radyovlm.evaluation import sema, vlm14 as V
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    assert kilit["surum"] == V.VLM14_SURUMU
    assert kilit["sozlesme"]["astra_adaptoru"] == A.SOZLESME_SURUMU
    assert kilit["sozlesme"]["sema"] == sema.SEMA_SURUMU


# --- 13 · Anatomi filtresi asiri eleme yapmaz (R3, astra-adaptor-1.2) ------

R3_VAKALARI = [
    # (cumlede aranan metin, elenmemesi gereken kavram)
    ("biopsy of the liver lesions and pulmonary nodules", "nodule"),
    ("suggesting metastatic disease", "nodule"),
    ("No acute pathology such as infection", "malignancy"),
]


def test_R3_karisik_organli_cumlede_toraks_kaniti_korunur():
    """Yeniden denetimin buldugu uc gercek vaka.

    `located_at` her gozlem icin EN FAZLA BIR bag kurar; `pulmonary nodules`
    en yakin anatomi olarak `liver`a baglanip eleniyordu. Bu test, elemenin
    acik toraks kanitini yutmadigini dogrular.
    """
    if not ILISKI.exists():
        pytest.skip("iliski katmani yok")
    from radyovlm.evaluation import vlm14 as V
    v = pd.read_parquet(VARLIK)
    r = pd.read_parquet(ILISKI)
    elenen = V.ekstratorasik_varliklar(v, r)

    for parca, kavram in R3_VAKALARI:
        alt = v[v["cumle_metni"].str.contains(parca, regex=False, na=False)]
        if alt.empty:
            pytest.skip(f"korpusta yok: {parca[:40]}")
        hedef = alt[alt["normalized_concept"].eq(kavram)]
        assert len(hedef) > 0, parca
        yutulan = [e for e in hedef["entity_id"] if e in elenen]
        assert not yutulan, (
            f"toraks kaniti elendi: {parca[:60]} ({kavram})")


def test_R3_toraks_oneki_koruyor():
    from radyovlm.evaluation import vlm14 as V
    assert V.TORAKS_ISARETI.search("and pulmonary nodules")
    assert V.TORAKS_ISARETI.search("bilateral lung nodules")
    assert not V.TORAKS_ISARETI.search("the liver lesions")


def test_R1_iliskiler_none_hata_verir():
    """`None` sessizce bos iliski sayilirsa uc girdi birden susar."""
    from radyovlm.evaluation import vlm14 as V
    v = pd.DataFrame({"entity_id": ["a"], "normalized_concept": ["nodule"],
                      "raw_text": ["nodule"], "seri_anahtari": ["s"],
                      "bolum_ham": ["lung"], "cumle_idx": [0],
                      "char_start": [0], "char_end": [6],
                      "cumle_metni": ["a nodule"]})
    for fn in (V.supheli_niteleyici_ekle, V.ekstratorasik_varliklar):
        with pytest.raises(ValueError, match="iliskiler"):
            fn(v, None)


def test_R5_kilit_evreni_ilan_eder():
    kilit = json.loads((KOK / "configs/astra_adaptor_kilidi.json")
                       .read_text(encoding="utf-8"))
    assert kilit["surum"] == "astra-adaptor-1.2"
    assert "evren" in kilit, "kilit hangi evreni kullandigini ilan etmeli (R5.1)"
    assert "train_dogrulamasi_evreni" in kilit["evren"]


def test_R5_split_filtresi_okuma_aninda():
    """Kapsam disi satirlar bellege alinmamali (R5.4)."""
    for betik in ("scripts/61_vlm14_train_aktarim_denetimi.py",
                  "scripts/62_vlm14_olculebilirlik_envanteri.py",
                  "scripts/63_vlm14_tam_kosum.py"):
        kaynak = (KOK / betik).read_text(encoding="utf-8")
        assert "filters=[(" in kaynak, f"{betik}: okuma aninda filtre yok"


def test_kosum_betigi_ofset_uretir():
    """Anatomi filtresi span oncesi pencereyi tarar; ofsetler zorunlu."""
    kaynak = (KOK / "scripts/63_vlm14_tam_kosum.py").read_text(encoding="utf-8")
    assert '"char_start": v["bas"]' in kaynak
    assert '"char_end": v["son"]' in kaynak
