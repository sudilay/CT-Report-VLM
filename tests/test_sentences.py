# -*- coding: utf-8 -*-
"""A1 / TASK-08 cumle bolutleme testleri.

Iki katman:
  1. Korpus butunlugu  - uretilen sentences.parquet uzerinde
  2. Zor vaka takimi   - elle secilmis zorlayici ornekler (sabit, her degisiklikte kosar)
"""
import re
import sys
import warnings
from importlib import import_module
from pathlib import Path

import pandas as pd
import pytest

warnings.filterwarnings("ignore")
from loguru import logger  # noqa: E402

logger.remove()

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

PARQ = ROOT / "data" / "processed" / "sentences.parquet"
REPORTS = ROOT / "data" / "processed" / "reports_study_level.parquet"


@pytest.fixture(scope="module")
def sent():
    if not PARQ.exists():
        pytest.skip("sentences.parquet henuz uretilmedi")
    return pd.read_parquet(PARQ)


@pytest.fixture(scope="module")
def rep():
    return pd.read_parquet(REPORTS)


@pytest.fixture(scope="module")
def bolut():
    """Bolutleyiciyi tek cagrilik bir fonksiyon olarak dondurur."""
    import medspacy  # noqa: F401
    import spacy
    seg = import_module("04_segment_sentences")
    nlp = spacy.blank("en")
    nlp.add_pipe("medspacy_pyrush")

    def _b(metin: str) -> list[str]:
        out = []
        for blok, _ in seg.bloklar(metin, 0):
            out += [s.text.strip() for s in nlp(blok).sents if s.text.strip()]
        return out

    return _b


# =====================================================================
# 1. KORPUS BUTUNLUGU
# =====================================================================

def test_ofsetler_metne_birebir_oturuyor(sent, rep):
    """D10: text == report_text[char_start:char_end] - istisnasiz."""
    metin = dict(zip(rep.study_id, rep.report_text))
    hatali = [r.study_id for r in sent.itertuples(index=False)
              if metin[r.study_id][r.char_start:r.char_end] != r.text]
    assert not hatali, f"{len(hatali)} cumlede ofset uyusmuyor"


def test_her_calisma_temsil_edilmis(sent, rep):
    """Bos raporlar disinda her calismadan en az bir cumle cikmali."""
    bos = set(rep.loc[rep.report_text.str.strip() == "", "study_id"])
    beklenen = set(rep.study_id) - bos
    assert beklenen - set(sent.study_id) == set()


def test_sent_idx_bolum_icinde_sirali(sent):
    g = sent.sort_values("char_start").groupby(["study_id", "section"])["sent_idx"]
    assert (g.apply(lambda s: list(s) == list(range(len(s))))).all()


def test_cumleler_bosluk_ile_baslamaz_bitmez(sent):
    assert not sent.text.str.match(r"^\s").any()
    assert not sent.text.str.contains(r"\s$", regex=True).any()


def test_bos_cumle_yok(sent):
    assert (sent.n_char > 0).all()
    assert (sent.text.str.strip() != "").all()


def test_ofset_araliklari_tutarli(sent):
    assert (sent.char_end > sent.char_start).all()
    assert (sent.char_end - sent.char_start == sent.n_char).all()


def test_bolumler_beklenen_degerler(sent):
    assert set(sent.section.unique()) <= {"findings", "impression"}


def test_bolutleme_surumu_kayitli(sent):
    """D10: her satir hangi bolutleme kural setinden geldigini tasir."""
    assert sent.segmentation_version.notna().all()
    assert sent.segmentation_version.nunique() == 1


def test_cumle_sayisi_beklenen_aralikta(sent):
    """Kabul olcutu (onceden yazildi): 450-600 bin."""
    assert 450_000 <= len(sent) <= 600_000, f"beklenmeyen cumle sayisi: {len(sent):,}"


def test_ayni_cumle_ikiye_bolunmemis(sent):
    """Bir cumle bir sonrakiyle cakismamali."""
    s = sent.sort_values(["study_id", "char_start"])
    onceki_son = s.groupby("study_id")["char_end"].shift()
    cakisan = (s.char_start < onceki_son).sum()
    assert cakisan == 0, f"{cakisan} cumle bir oncekiyle cakisiyor"


# =====================================================================
# 2. ZOR VAKA TAKIMI  (sabit - her degisiklikte kosar)
# =====================================================================

def test_zor_noktalamasiz_cift_bosluk(bolut):
    """Aday B'nin varlik sebebi: noktalama olmadan cift boslukla ayrilmis maddeler.
    Korpusta 3.939 kez geciyor; PyRuSH tek basina bunlari birlestiriyordu."""
    r = bolut("Metastatic breast Ca  Findings compatible with Covid pneumonia  "
              "Bilateral supraclavicular lymph nodes")
    assert len(r) == 3
    assert r[0] == "Metastatic breast Ca"


def test_zor_ondalik_olcu_bolunmez(bolut):
    r = bolut("1.5 mm thick sections were taken in the axial plane. Trachea is open.")
    assert len(r) == 2
    assert r[0].startswith("1.5 mm")


def test_zor_belirsizlik_parantezi(bolut):
    r = bolut("A 13 mm hypodense lesion in liver segment 8 is stable (cyst?). "
              "No lytic lesion was seen.")
    assert len(r) == 2
    assert "(cyst?)" in r[0]


def test_zor_coklu_olcu(bolut):
    r = bolut("It measured 34mm and 31mm respectively. Aortic valve is normal.")
    assert len(r) == 2
    assert "34mm" in r[0] and "31mm" in r[0]


def test_zor_uc_eksen_olcu(bolut):
    r = bolut("A lesion with a size of 52x55x34 mm with slightly lobulated contours "
              "was observed.")
    assert len(r) == 1


def test_zor_aralik_olcusu(bolut):
    r = bolut("There are calcific 2-3 mm diameter nonspecific nodules superposed "
              "in both lungs.")
    assert len(r) == 1


def test_zor_bozuk_noktalama(bolut):
    """Bitisik tarih (regions.3.2021.) asiri bolmeye yol acmamali."""
    r = bolut("No enlarged lymph nodes were detected in the mediastinum and hilar "
              "regions.3.2021. There is an area of atelectasis.")
    assert len(r) == 2
    assert r[1].startswith("There is an area")


def test_zor_noktalamali_cift_bosluk(bolut):
    r = bolut("Emphysematous changes in both lungs.  Cholelithiasis.  "
              "Minimal degenerative changes.")
    assert len(r) == 3


def test_zor_negasyon_cumlesi_butun_kalir(bolut):
    r = bolut("No mass lesion-active infiltration with distinguishable borders "
              "was detected in both lungs.")
    assert len(r) == 1


def test_zor_tek_madde_noktasiz(bolut):
    """Noktayla bitmeyen tek madde - %28,8'i boyle."""
    r = bolut("Thoracic CT examination within normal limits")
    assert len(r) == 1


# =====================================================================
# 3. KORPUS UZERINDE ZOR DESEN TARAMASI
# =====================================================================

def test_korpusta_ondalik_bolunmesi_yok(sent, rep):
    """Hicbir cumle siniri bir ondalik sayinin ORTASINA dusmemeli.

    Dolayli belirtiler bu testte ise yaramadi, ikisi de yanlis alarm verdi:
      1) 'rakam + nokta ile biten cumle'  -> 637 eslesme, hepsi mesru
         ('in liver segment 8.', 'covid 19.', 'dated 2022.')
      2) '+ ardindan rakam gelmesi'       -> 1 eslesme, o da mesru
         ('...old CT dated 7.12.2021.' + '1-2 millimetric nodule...')

    Dogru olcut dogrudan olculur: metindeki her '\\d.\\d' oruntusu icin,
    hicbir cumlenin bitis ofseti o oruntunun icine dusmemeli.
    """
    metin = dict(zip(rep.study_id, rep.report_text))
    bitisler: dict[str, set] = {}
    for r in sent.itertuples(index=False):
        bitisler.setdefault(r.study_id, set()).add(r.char_end)

    kotu = []
    for sid, t in metin.items():
        son = bitisler.get(sid, set())
        for m in re.finditer(r"\d\.\d", t):
            # sinir, nokta ile sonraki rakam arasina dusuyorsa ondalik bolunmus
            if m.start() + 2 in son:
                kotu.append((sid, t[max(0, m.start() - 30):m.end() + 10]))
    assert not kotu, f"{len(kotu)} ondalik bolunmesi: {kotu[:3]}"


def test_korpusta_artik_cift_bosluk_yok(sent):
    """Blok bolme sonrasi hicbir cumlede 2+ bosluk kalmamali."""
    kotu = sent[sent.text.str.contains(r" {2,}", regex=True)]
    assert len(kotu) == 0, f"{len(kotu)} cumlede artik cift bosluk var"


def test_noktalamadan_ibaret_cumle_yok(sent):
    """Elle inceleme sirasinda bulundu: ',' '.' '?' ';' gibi tek karakterlik
    'cumle'ler uretiliyordu (238 adet). Artik filtreleniyor."""
    kotu = sent[~sent.text.str.contains(r"\w", regex=True)]
    assert len(kotu) == 0, f"{len(kotu)} cumle hic harf/rakam icermiyor: {kotu.text.head(5).tolist()}"


def test_orta_nokta_madde_isareti_bolunmus(sent):
    """Orta nokta (U+00B7) ilk taramada kacirildi - 238 raporda, yalnizca
    Impression'da madde isareti olarak kullaniliyor. Artik blok siniri."""
    kalan = sent[sent.text.str.contains("[·•]", regex=True)]
    assert len(kalan) == 0, f"{len(kalan)} cumlede madde isareti kalmis"


def test_zor_orta_nokta_maddeleri(bolut):
    """Regresyon: orta noktali maddeler ayrilmali."""
    t = ("· In follow-up, operated breast Ca, multiple bone metastases. "
         "· Stable calcific parenchymal nodules in both lungs. "
         "· Left pleural effusion is new")
    r = [x for x in bolut(t) if re.search(r"\w", x)]
    assert len(r) == 3
    assert r[0].startswith("In follow-up")


def test_asiri_uzun_cumle_orani_dusuk(sent):
    """Cok uzun cumleler bolunememis maddelere isaret eder."""
    oran = (sent.n_char > 400).mean()
    assert oran < 0.01, f"400 karakterden uzun cumle orani %{100*oran:.2f}"
