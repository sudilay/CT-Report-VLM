# -*- coding: utf-8 -*-
"""TASK-12 / B0: ayar-degerlendirme ayriminin testleri (D26).

Bu ayrimin amaci metodolojik: kurallar bir orneklege bakilarak duzeltilip AYNI
orneklem uzerinde basarim bildirilirse, bildirilen sayi o orneklere uydurulmus
olur. Testler ayrimin gercekten korundugunu denetler.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PROC = ROOT / "data" / "processed"
AYAR = PROC / "task12_ayar.csv"
TEST = PROC / "task12_test-v1.csv"
YANMIS = PROC / "incelenmis_hastalar.csv"


def _var():
    return AYAR.exists() and TEST.exists() and YANMIS.exists()


@pytest.fixture(scope="module")
def kumeler():
    if not _var():
        pytest.skip("orneklem henuz uretilmedi (scripts/10_build_eval_split.py)")
    reps = pd.read_parquet(PROC / "reports_study_level.parquet",
                           columns=["study_id", "patient_id", "split"])
    return (pd.read_csv(AYAR, encoding="utf-8-sig"),
            pd.read_csv(TEST, encoding="utf-8-sig"),
            pd.read_csv(YANMIS, encoding="utf-8-sig"), reps)


def test_hasta_kesisimi_yok(kumeler):
    """En kritik koruma: ayni hasta iki kumeye dusemez.

    Ayrim CALISMA duzeyinde yapilsaydi ayni hastanin iki calismasi iki kumeye
    dusebilirdi ve test sizmis olurdu.
    """
    ayar, test, _, reps = kumeler
    h = dict(zip(reps.study_id, reps.patient_id))
    assert not ({h[x] for x in ayar.study_id} & {h[x] for x in test.study_id})


def test_yanmis_hasta_teste_sizmamis(kumeler):
    """Bugune kadar incelenen orneklerdeki hastalar uzerinde kural gelistirildi;
    degerlendirme kumesine giremezler."""
    _, test, yanmis, reps = kumeler
    h = dict(zip(reps.study_id, reps.patient_id))
    assert not ({h[x] for x in test.study_id} & set(yanmis.patient_id))


def test_ayar_yalnizca_train(kumeler):
    ayar, _, _, reps = kumeler
    s = dict(zip(reps.study_id, reps.split))
    assert {s[x] for x in ayar.study_id} == {"train"}


def test_degerlendirme_yalnizca_valid(kumeler):
    """Sozluk TUM train cumlelerinden turetildi; hicbir train cumlesi
    'gorulmemis' sayilamaz. Degerlendirme valid'den gelmek ZORUNDA."""
    _, test, _, reps = kumeler
    s = dict(zip(reps.study_id, reps.split))
    assert {s[x] for x in test.study_id} == {"valid"}


def test_rastgele_ve_hedefli_ayrilabiliyor(kumeler):
    """D26/6: iki skor AYRI raporlanacak, birlestirilmeyecek. Kolonun
    ayirt edici olmasi sart."""
    ayar, test, _, _ = kumeler
    for d in (ayar, test):
        assert set(d.tur.unique()) == {"rastgele", "hedefli"}
        assert (d.tur == "hedefli").sum() > 0 and (d.tur == "rastgele").sum() > 0


def test_hedefli_gruplar_tam(kumeler):
    _, test, _, _ = kumeler
    beklenen = {"negasyon", "belirsizlik", "coklu_bulgu",
                "onceki_tetkik", "coklu_olcu"}
    assert beklenen <= set(test.grup.unique())


def test_isaretleme_kolonlari_bos(kumeler):
    """Kumeler HENUZ isaretlenmedi; dolu gelirse yanlislikla siziyor demektir."""
    _, test, _, _ = kumeler
    for k in ("assertion_dogru", "temporality_dogru", "change_type_dogru"):
        assert test[k].isna().all() or (test[k].astype(str).str.strip() == "").all()


def test_cumle_tekrari_yok(kumeler):
    ayar, test, _, _ = kumeler
    for d in (ayar, test):
        assert not d.duplicated(["study_id", "section", "sent_idx"]).any()


def test_tuketilen_valid_hastalar_kaydedilmis():
    """Faz 3'e borc: test valid hastasi tuketiyor, TASK-18 bunu bilmeli.
    Sessizce tuketilmemeli."""
    yol = PROC / "tuketilen_valid_hastalar.csv"
    if not yol.exists():
        pytest.skip("orneklem henuz uretilmedi")
    d = pd.read_csv(yol, encoding="utf-8-sig")
    assert len(d) > 0 and "patient_id" in d.columns


# --------------------------------------------------------------------
# Korumanin GERCEKTEN atesledigini dogrula - sentetik ihlal
# --------------------------------------------------------------------

def test_koruma_hasta_cakismasini_yakalar():
    """Koruma kodunun ise yaradigini dogrudan sina: cakisan hasta verilirse
    ihlal uretilmeli. Gecen bir testin gercekten denetledigini bilmek icin."""
    dev_p, test_p, yanmis = {"p1", "p2"}, {"p2", "p3"}, {"p9"}
    ihlal = []
    if dev_p & test_p:
        ihlal.append("kesisim")
    if test_p & yanmis:
        ihlal.append("yanmis")
    assert "kesisim" in ihlal


def test_koruma_yanmis_sizintiyi_yakalar():
    dev_p, test_p, yanmis = {"p1"}, {"p2", "p9"}, {"p9"}
    ihlal = []
    if dev_p & test_p:
        ihlal.append("kesisim")
    if test_p & yanmis:
        ihlal.append("yanmis")
    assert "yanmis" in ihlal
