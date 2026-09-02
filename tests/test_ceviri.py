"""TASK-15 ceviri/post-edit sozlesmeleri - sahte adaptorlerle, model indirmeden."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation.task15 import ContractError, run_translation
from radyovlm.evaluation.translation import (
    CumleDuzeyiAdapter,
    CumleDuzeyiPostEdit,
    OpusMtAdapter,
    cumlelere_bol,
    run_post_edit,
    sayi_korunumu_ihlalleri,
    yapisal_ihlaller,
)

TR_PAKET = [
    {"document_id": "a#1111", "order": 0, "text_tr": "Sağ akciğerde 12 mm nodül."},
    {"document_id": "b#2222", "order": 1, "text_tr": "Plevral sıvı saptanmadı."},
]


class SahteCevirmen:
    name = "sahte-mt"

    def translate(self, text, source_language, target_language):
        return f"[{source_language}->{target_language}] {text}"


class SahtePostEdit:
    name = "sahte-postedit"

    def __init__(self, donusum=lambda t: t + " (edited)"):
        self.donusum = donusum

    def post_edit(self, text):
        return self.donusum(text)


# --------------------------------------------------------------------------
# Sayi/birim korunumu - docs/24 §7'nin istedigi otomatik denetim
# --------------------------------------------------------------------------


def test_sayi_korunumu_temiz_metni_gecirir():
    assert sayi_korunumu_ihlalleri("12x8 mm nodül", "a 12 x 8 mm nodule") == []


def test_sayi_korunumu_ondalik_ayiriciyi_normalize_eder():
    """'1,5 cm' ile '1.5 cm' ayni olcumdur; yanlis alarm uretmemeli."""
    assert sayi_korunumu_ihlalleri("1,5 cm lezyon", "a 1.5 cm lesion") == []


@pytest.mark.parametrize(
    ("kaynak", "hedef"),
    [
        ("12x8 mm nodül", "a 12 x 9 mm nodule"),  # sayi degisti
        ("1,5 cm lezyon", "a 1.5 mm lesion"),  # birim degisti
        ("12 mm nodül", "a nodule"),  # olcum dustu
        ("nodül", "a 12 mm nodule"),  # olcum uyduruldu
    ],
)
def test_sayi_korunumu_ihlalleri_yakalar(kaynak, hedef):
    assert sayi_korunumu_ihlalleri(kaynak, hedef)


# --------------------------------------------------------------------------
# Kosucu sozlesmeleri
# --------------------------------------------------------------------------


def test_ceviri_kimlik_ve_sirayi_korur():
    cikti = run_translation(TR_PAKET, SahteCevirmen())
    assert [r["document_id"] for r in cikti] == ["a#1111", "b#2222"]
    assert [r["order"] for r in cikti] == [0, 1]
    assert all(r["adapter"] == "sahte-mt" for r in cikti)


def test_post_edit_en_genel_ciktisini_girdi_alir():
    """EN-tibbi'nin girdisi Turkce paket DEGIL, EN-genel ciktisidir."""
    en_genel = run_translation(TR_PAKET, SahteCevirmen())
    cikti = run_post_edit(en_genel, SahtePostEdit())
    assert [r["document_id"] for r in cikti] == ["a#1111", "b#2222"]
    assert all(r["base_adapter"] == "sahte-mt" for r in cikti)
    assert all(r["number_violations"] == [] for r in cikti)
    # Turkce paketi dogrudan vermek kapali alan sozlesmesini bozmali.
    with pytest.raises(ContractError):
        run_post_edit(TR_PAKET, SahtePostEdit())


def test_post_edit_sayi_bozarsa_durur():
    bozan = SahtePostEdit(lambda t: t.replace("12", "13"))
    en_genel = run_translation(TR_PAKET, SahteCevirmen())
    with pytest.raises(ContractError, match="sayi"):
        run_post_edit(en_genel, bozan)


def test_post_edit_gevsek_modda_olcer_ama_durmaz():
    """`dev`de ihlal profili olculebilir; `test`te bu mod kullanilmaz."""
    bozan = SahtePostEdit(lambda t: t.replace("12", "13"))
    en_genel = run_translation(TR_PAKET, SahteCevirmen())
    cikti = run_post_edit(en_genel, bozan, strict_numbers=False)
    ihlalli = [r for r in cikti if r["number_violations"]]
    assert len(ihlalli) == 1
    assert "sayi" in ihlalli[0]["number_violations"][0]


def test_post_edit_bos_cikti_reddedilir():
    en_genel = run_translation(TR_PAKET, SahteCevirmen())
    with pytest.raises(ContractError, match="Bos post-edit"):
        run_post_edit(en_genel, SahtePostEdit(lambda t: "   "))


def test_opus_adapteri_yalniz_tr_en_cevirir():
    """Kol sozlesmesi disinda bir dil cifti sessizce kabul edilmemeli."""
    with pytest.raises(ContractError, match="tr->en"):
        OpusMtAdapter().translate("metin", "en", "tr")


def test_adapter_adi_revizyonu_tasir():
    """Provenance adaptor adindan okunuyor; revizyon gorunur olmali."""
    assert OpusMtAdapter(revision="abc123").name.endswith("@abc123")


def test_birim_kontrolu_diller_arasi_kapatilabilir():
    """Turkce eki birime yapistirir (`1 cmyi`); diller arasi kiyasta yanlis alarm
    uretir. Sayi kontrolu her iki durumda da calisir."""
    tr, en = "kısa aksı 1 cmyi geçmeyen lenf nodu", "lymph node not exceeding 1 cm"
    assert sayi_korunumu_ihlalleri(tr, en)  # birim kontrolu acikken yanlis alarm
    assert sayi_korunumu_ihlalleri(tr, en, birim_kontrolu=False) == []
    # Sayi degisimi birim kontrolu kapaliyken de yakalanmali.
    assert sayi_korunumu_ihlalleri(tr, "lymph node not exceeding 2 cm", birim_kontrolu=False)


# --------------------------------------------------------------------------
# Cumle duzeyi sarmalayici (D54) - yalniz ucuz kol icin
# --------------------------------------------------------------------------


def test_cumle_bolmesi_kayipsizdir():
    """Bolme yalnizca boler, ATMAZ. Kayipli bolme olcmek istedigimiz ceviri
    kaybini taklit eder ve sonucu yanlis yone ceker."""
    metin = "Sağda 4 ve 5. kotlarda kırık var. Plevral sıvı yok.  Yeni cümle."
    parcalar = cumlelere_bol(metin)
    assert "".join(c + a for c, a in parcalar) == metin


def test_cumle_bolmesi_sira_sayisini_bolmez():
    """'5. kotlarda' bir cumle sonu DEGIL - kucuk harf devam ediyor."""
    parcalar = cumlelere_bol("Sağda 4 ve 5. kotlarda kırık var. Sol taraf normal.")
    assert len(parcalar) == 2
    assert "5. kotlarda" in parcalar[0][0]


def test_cumle_bolmesi_ondaligi_bolmez():
    assert len(cumlelere_bol("Lezyon 1.5 cm çapındadır.")) == 1


def test_cumle_duzeyi_adapteri_her_cumleyi_ayri_cevirir():
    cagrilar = []

    class Sayan:
        name = "sayan"

        def translate(self, text, s, t):
            cagrilar.append(text)
            return f"<{len(cagrilar)}>"

    sarmal = CumleDuzeyiAdapter(Sayan())
    sonuc = sarmal.translate("Bir cümle. İki cümle.", "tr", "en")
    assert len(cagrilar) == 2
    assert sonuc == "<1> <2>"  # ayirici korunmus
    assert sarmal.name == "cumle-duzeyi(sayan)"


def test_cumle_duzeyi_bos_ceviriyi_reddeder():
    class Bos:
        name = "bos"

        def translate(self, text, s, t):
            return "  "

    with pytest.raises(ContractError, match="Bos cumle cevirisi"):
        CumleDuzeyiAdapter(Bos()).translate("Bir cümle.", "tr", "en")


# --------------------------------------------------------------------------
# Yapisal denetim - sayi korunumunun GORMEDIGI yeniden-yazma ihlalleri
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bozuk",
    [
        "**Findings:** a 12 mm nodule is seen.",           # Markdown kalin
        "*   a 12 mm nodule is seen.",                      # madde imi
        "IMPRESSION:\na 12 mm nodule is seen.",             # ozet basligi
        "Here is the corrected text: a 12 mm nodule.",      # sohbet onsozu
    ],
)
def test_yapisal_denetim_yeniden_yazmayi_yakalar(bozuk):
    """Sayilar korunsa bile bicim degistirmek docs/19 §4/4 ihlalidir."""
    kaynak = "a 12 mm nodule is seen in the right upper lobe of the lung today."
    assert yapisal_ihlaller(kaynak, bozuk)


def test_yapisal_denetim_temiz_metni_gecirir():
    kaynak = "A 12 mm nodule is seen in the right upper lobe."
    assert yapisal_ihlaller(kaynak, "A 12 mm nodule is observed in the right upper lobe.") == []


def test_yapisal_denetim_ozetlemeyi_uzunluktan_yakalar():
    """Asil vaka: 46 belgeden biri asil uzunlugunun %13'une inmisti."""
    kaynak = "A" * 400
    assert any("kisalmis" in x for x in yapisal_ihlaller(kaynak, "A" * 50))
    assert any("uzamis" in x for x in yapisal_ihlaller(kaynak, "A" * 900))


def test_post_edit_markdown_uretirse_durur():
    """Sayilar bozulmasa bile yapisal ihlal kosuyu durdurmali."""

    class Markdownci:
        name = "md"

        def post_edit(self, text):
            return f"**Findings:**\n*   {text}"

    en_genel = run_translation(TR_PAKET, SahteCevirmen())
    with pytest.raises(ContractError, match="korunum sozlesmesini"):
        run_post_edit(en_genel, Markdownci())


def test_erken_durdurma_bozuk_kosuyu_bastan_keser():
    """Istem v1 kosusunda ilk 5 belgenin 5'i de ihlalliydi ve 22 dakika surdu.
    Kalan belgeleri kosmak zaman kaybi."""
    paket = [
        {"document_id": f"d{i}", "order": i, "text": f"nodule {i} mm seen.", "adapter": "x"}
        for i in range(20)
    ]
    bozan = SahtePostEdit(lambda t: "**Findings:**\n*   " + t)
    with pytest.raises(ContractError, match="ERKEN DURDURMA"):
        run_post_edit(paket, bozan, strict_numbers=False, erken_dur=5)
    # Duzgun cikti erken durdurmayi TETIKLEMEZ.
    assert len(run_post_edit(paket, SahtePostEdit(lambda t: t), strict_numbers=False)) == 20


def test_istem_sizintisi_yakalanir():
    """Model istemi ciktiya kopyalarsa sayilar korunur ve diger denetimleri gecerdi."""
    assert any("sizinti" in x for x in yapisal_ihlaller("a" * 100, "a" * 90 + " Absolute rules"))


def test_cumle_duzeyi_postedit_her_cumleyi_ayri_verir():
    """Belge duzeyinde model raporu yeniden yaziyordu; cumle duzeyi bunu
    yapisal olarak engeller (kosu 2: 20/46 Markdown, 8/46 dusunme izi)."""
    gorulen = []

    class Sayan:
        name = "sayan"
        model_id = "m"
        revision = "r"

        def post_edit(self, text):
            gorulen.append(text)
            return text.upper()

    s = CumleDuzeyiPostEdit(Sayan())
    # Turkce buyuk harf tuzagina girmemek icin duz ASCII metin.
    sonuc = s.post_edit("First sentence. Second sentence.")
    assert gorulen == ["First sentence.", "Second sentence."]
    assert sonuc == "FIRST SENTENCE. SECOND SENTENCE."
    assert s.model_id == "m" and s.revision == "r"


def test_cumle_duzeyi_postedit_bos_cikti_reddeder():
    class Bos:
        name = "bos"

        def post_edit(self, text):
            return "   "

    with pytest.raises(ContractError, match="Bos cumle post-editi"):
        CumleDuzeyiPostEdit(Bos()).post_edit("Bir cümle.")
