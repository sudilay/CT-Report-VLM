# -*- coding: utf-8 -*-
"""A4 / A5 · TASK-09 olcu cikarimi testleri.

Iki katman:
  1. Zor vaka takimi  - elle secilmis zorlayici ornekler (sabit)
  2. Korpus butunlugu - uretilen measurements.parquet uzerinde

Kararlar: D5 (niteliksel boyut), D6 (alt+ust sinir), D7 (cm->mm),
D3-b (teknik olcu ayrimi), D10 (ofsetler report_text'e gore).
"""
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

MEAS = ROOT / "data" / "processed" / "measurements.parquet"
SENT = ROOT / "data" / "processed" / "sentences.parquet"
REPS = ROOT / "data" / "processed" / "reports_study_level.parquet"

ANAHTAR = ["study_id", "section", "sent_idx"]


@pytest.fixture(scope="module")
def mod():
    return import_module("07_extract_measurements")


@pytest.fixture(scope="module")
def meas():
    if not MEAS.exists():
        pytest.skip("measurements.parquet yok - once 07_extract_measurements.py")
    return pd.read_parquet(MEAS)


@pytest.fixture(scope="module")
def sent():
    return pd.read_parquet(SENT)


def bul(mod, metin):
    """Bir metindeki sayisal olculeri (raw, eksenler, aralik) olarak dondurur."""
    out = []
    for m in mod.OLCU.finditer(metin):
        eksen, aralik = mod.eksenleri_coz(m.group("num"), m.group("unit"))
        out.append((m.group(0), eksen, aralik))
    return out


# =====================================================================
# 1. ZOR VAKA TAKIMI  (sabit - her degisiklikte kosar)
# =====================================================================

def test_zor_tek_olcu(mod):
    assert bul(mod, "A 12 mm nodule was seen.") == [("12 mm", [12.0], False)]


def test_zor_ondalik(mod):
    """'12.5 mm' tek olcudur; '5 mm' diye ikinci bir eslesme URETILMEMELI."""
    r = bul(mod, "A 12.5 mm nodule.")
    assert r == [("12.5 mm", [12.5], False)]


def test_zor_bozuk_noktalama_sonrasi_olcu(mod):
    """Kaynak metinde 'limits.5 mm' gibi bozuk noktalama var (23 vaka).
    Ilk lookbehind bunlari bloke ediyordu."""
    r = bul(mod, "no increase was detected in the examination limits.5 mm in diameter")
    assert r == [("5 mm", [5.0], False)]


def test_zor_cok_eksenli(mod):
    assert bul(mod, "measuring 5x3 mm") == [("5x3 mm", [5.0, 3.0], False)]


def test_zor_uc_eksenli(mod):
    r = bul(mod, "a lesion of 26x18x40 mm")
    assert r == [("26x18x40 mm", [26.0, 18.0, 40.0], False)]


def test_zor_aralik_alt_ust_ayri(mod):
    """D6: 'ust siniri al' bir KARAR KURALIDIR, veri hazirligina ait degil."""
    r = bul(mod, "calcific 2-3 mm diameter nodules")
    assert r == [("2-3 mm", [2.0, 3.0], True)]


def test_zor_bitisik_birim_ve_coklu_olcu(mod):
    r = bul(mod, "It measured 34mm and 31mm respectively.")
    assert [x[0] for x in r] == ["34mm", "31mm"]


def test_zor_cm_mm_cevrimi(mod):
    """D7: cm -> mm."""
    assert bul(mod, "a 2 cm lesion") == [("2 cm", [20.0], False)]
    assert bul(mod, "a 1.5 cm lesion") == [("1.5 cm", [15.0], False)]


def test_zor_tarih_olcu_sanilmaz(mod):
    """'7.12.2021' bir olcu degildir - birim yok."""
    assert bul(mod, "the old CT dated 7.12.2021 was compared") == []


def test_zor_niteliksel_boyut(mod):
    """D5: sayi ATANMAZ, yok da SAYILMAZ."""
    assert mod.NITELIKSEL.search("A few millimetric nonspecific nodules")
    assert mod.NITELIKSEL.search("milimetric nodule")       # yazim varyanti
    assert mod.NITELIKSEL.search("a subcentimetric lesion")
    assert not mod.NITELIKSEL.search("a 5 mm nodule")


def test_zor_teknik_olcu_dar_desenle(mod):
    """D3-b: DAR desen. Genis desen ('thick'/'thickness') 54.031 cumle
    yakaliyor ve neredeyse tamami KLINIK."""
    assert mod.teknik_mi("1 mm thick sections were taken in the axial plane.", 2, 7)
    assert mod.teknik_mi("made with a section thickness of 5 mm.", 33, 38)
    # klinik olculer teknik SAYILMAMALI
    assert not mod.teknik_mi("The pleural effusion measured 50 mm at its thickest point.", 30, 35)
    assert not mod.teknik_mi("an effusion reaching 7 mm in thickness is observed", 21, 25)
    assert not mod.teknik_mi("Thickening of the bronchial wall, 4 mm in diameter.", 34, 39)


# =====================================================================
# 2. KORPUS BUTUNLUGU
# =====================================================================

def test_ofsetler_metne_birebir_oturuyor(meas):
    """D10: raw_text == report_text[char_start:char_end] - istisnasiz."""
    reps = pd.read_parquet(REPS, columns=["study_id", "report_text"])
    metin = dict(zip(reps.study_id, reps.report_text))
    hatali = [(r.study_id, r.raw_text) for r in meas.itertuples(index=False)
              if metin[r.study_id][r.char_start:r.char_end] != r.raw_text]
    assert not hatali, f"{len(hatali)} olcuda ofset uyusmuyor: {hatali[:3]}"


def test_kind_degerleri(meas):
    assert set(meas["kind"].unique()) <= {"numeric", "qualitative"}


def test_sayisal_olculer_tutarli(meas):
    n = meas[meas.kind == "numeric"]
    assert n.min_mm.notna().all() and n.max_mm.notna().all()
    assert (n.min_mm <= n.max_mm).all()
    assert (n.min_mm > 0).all()
    assert n.unit_raw.isin(["mm", "cm"]).all()
    assert (n.n_axes >= 1).all()


def test_niteliksel_olculere_sayi_atanmamis(meas):
    """D5: uydurma deger uretilmedigini garanti eder."""
    q = meas[meas.kind == "qualitative"]
    assert q.min_mm.isna().all()
    assert q.max_mm.isna().all()
    assert q.size_qualitative.notna().all()


def test_cm_cevrimi_dogru(meas):
    """D7: cm kayitlarinin mm degeri 10 katidir."""
    cm = meas[(meas.kind == "numeric") & (meas.unit_raw == "cm") & (~meas.is_range)]
    assert len(cm) > 0
    ornek = cm[cm.n_axes == 1].head(200)
    for r in ornek.itertuples(index=False):
        ham = float(r.raw_text.lower().replace("cm", "").strip())
        assert abs(r.max_mm - ham * 10) < 0.01


def test_aralik_iki_deger_tasiyor(meas):
    """D6: aralik kayitlari alt ve ust siniri birlikte tasir.

    min == max olabilir: "29-29 mm" gibi bir vaka var. Orada tire aralik
    degil, sag-sol iki esit degeri listeliyor ("The diameters of the right-left
    pulmonary arteries increased by 35 mm and 29-29 mm"). 166 aralik kaydinin
    1'i boyle; ayirt etmek karar kurali gerektirirdi, kaydedip geciyoruz.
    """
    a = meas[meas.is_range]
    assert len(a) > 0
    assert (a.n_axes == 2).all()
    assert (a.min_mm <= a.max_mm).all()


def test_raw_text_her_zaman_var(meas):
    """Hicbir donusum geri donulemez olmamali."""
    assert meas.raw_text.notna().all()
    assert (meas.raw_text.str.len() > 0).all()


def test_meas_idx_cumle_icinde_sirali(meas):
    g = meas.sort_values("char_start").groupby(ANAHTAR)["meas_idx"]
    assert g.apply(lambda s: sorted(s) == list(range(len(s)))).all()


def test_surum_zinciri_ucdan_uca(meas):
    """Olcu kaydi, hangi bolutleme ve sablon surumunden turedigini tasimali."""
    for kol in ("segmentation_version", "template_version", "measurement_version"):
        assert kol in meas.columns, f"{kol} kolonu yok - surum zinciri kopuk"
        assert meas[kol].nunique() == 1
    assert "pipeline_version" not in meas.columns, "eski tekil surum kolonu geri gelmis"


# =====================================================================
# 3. KABUL OLCUTLERI  (onceden yazildi)
# =====================================================================

def test_kabul_yakalama_orani(meas, sent):
    """Olcut: mm|cm gecen cumlelerin >= %95'inde olcu cikarilmali."""
    olculu = sent[sent.text.str.contains(r"\d\s*(?:mm|cm)\b", case=False, regex=True)]
    yakalanan = set(map(tuple, meas[meas.kind == "numeric"][ANAHTAR].values))
    var = sum(1 for r in olculu.itertuples(index=False)
              if (r.study_id, r.section, r.sent_idx) in yakalanan)
    oran = var / len(olculu)
    assert oran >= 0.95, f"yakalama %{100*oran:.2f}"


def test_kabul_aykiri_deger_sayisi_sinirli(meas):
    """200 mm ustu degerler kaynak rapor hatasi veya buyuk organ olcusudur;
    sayilari elle incelenebilecek duzeyde kalmali."""
    n = meas[meas.kind == "numeric"]
    aykiri = n[n.max_mm > 200]
    assert len(aykiri) <= 50, f"{len(aykiri)} aykiri deger - elle inceleme zorlasir"


def test_kabul_teknik_isaretliler_az_ve_dogru(meas):
    """Teknik bilgi ayri Technique_EN alaninda; Findings/Impression icinde
    yalnizca birkac vaka olmali. Cok cikarsa dar desen genislemis demektir."""
    t = meas[meas.is_technical]
    assert len(t) <= 30, f"{len(t)} teknik isaretli - desen fazla genis olabilir"


def test_meas_idx_metin_sirasini_yansitiyor(meas):
    """meas_idx, olcunun cumle icindeki KONUM sirasini yansitmali.

    Ilk uygulamada sayisal ve niteliksel ayri dongulerde numaralaniyordu; onde
    gelen 'millimetric' arkadaki '4 mm'den sonra numara aliyordu (562 cumle).
    """
    g = meas.sort_values("char_start").groupby(ANAHTAR)["meas_idx"]
    bozuk = g.apply(lambda s: list(s) != sorted(s))
    assert not bozuk.any(), f"{bozuk.sum()} cumlede meas_idx metin sirasini yansitmiyor"


def test_niteliksel_ve_sayisal_ayni_cumlede_olabilir(meas):
    """Cift kayit degil, iki ayri ANMA. 'millimetric nodule ... 4 mm' cumlesinde
    ikisi de metinde geciyor ve ikisi de kaydediliyor. Ayni lezyona ait
    olduklarini belirlemek Faz 2'nin isi. Sayim yaparken dikkat edilmeli."""
    ikili = meas.groupby(ANAHTAR)["kind"].nunique()
    assert (ikili > 1).sum() > 0, "beklenen ortak durum kaybolmus"
    assert (ikili > 1).sum() < 0.05 * len(ikili), "beklenenden cok fazla"


# =====================================================================
# 4. KAPSAMLI MEKANIK DENETIM  (ornekleme degil - TUM kayitlar)
# =====================================================================
# Elle inceleme 100 satirlik ornekleme yapiyor. Bu testler ayni mekanik
# ozellikleri 50.000+ kaydin TAMAMINDA dogruluyor; ornekleme yerine tam sayim.

def test_tum_cm_kayitlari_dogru_cevrilmis(meas):
    """D7: TUM cm kayitlarinda mm degeri ham sayinin 10 kati olmali."""
    import re
    import numpy as np
    cm = meas[(meas.kind == "numeric") & (meas.unit_raw == "cm")]
    kotu = []
    for r in cm.itertuples(index=False):
        say = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", r.raw_text)]
        if sorted(np.round(r.axes_mm, 2).tolist()) != sorted(round(v * 10, 2) for v in say):
            kotu.append(r.raw_text)
    assert not kotu, f"{len(kotu)} cm kaydi yanlis cevrilmis: {kotu[:3]}"


def test_tum_mm_kayitlari_degismemis(meas):
    """mm kayitlarinda deger olduğu gibi kalmali."""
    import re
    import numpy as np
    mm = meas[(meas.kind == "numeric") & (meas.unit_raw == "mm")]
    kotu = [r.raw_text for r in mm.itertuples(index=False)
            if sorted(np.round(r.axes_mm, 2).tolist())
            != sorted(round(float(v), 2) for v in re.findall(r"\d+(?:\.\d+)?", r.raw_text))]
    assert not kotu, f"{len(kotu)} mm kaydi degismis: {kotu[:3]}"


def test_min_max_eksenlerden_turetilmis(meas):
    """min_mm/max_mm gercekten axes_mm'den geliyor mu - TUM kayitlar."""
    n = meas[meas.kind == "numeric"]
    kotu = sum(1 for r in n.itertuples(index=False)
               if abs(r.min_mm - min(r.axes_mm)) > 1e-6
               or abs(r.max_mm - max(r.axes_mm)) > 1e-6)
    assert kotu == 0, f"{kotu} kayitta min/max eksenlerle tutarsiz"


def test_n_axes_eksen_sayisiyla_uyumlu(meas):
    n = meas[meas.kind == "numeric"]
    kotu = sum(1 for r in n.itertuples(index=False) if r.n_axes != len(r.axes_mm))
    assert kotu == 0


def test_sayisal_raw_text_birim_iceriyor(meas):
    n = meas[meas.kind == "numeric"]
    assert n.raw_text.str.contains(r"(?:mm|cm)", case=False, regex=True).all()


def test_is_range_raw_text_ile_tutarli(meas):
    """is_range bayragi ham metindeki tire ile birebir ortusmeli."""
    n = meas[meas.kind == "numeric"]
    assert (n.is_range == n.raw_text.str.contains(r"\d\s*-\s*\d", regex=True)).all()
