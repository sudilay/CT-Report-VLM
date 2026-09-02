"""TASK-15 ceviri ve tibbi post-edit adaptorleri.

KOLLAR (D52 · docs/19 §2):
  EN-genel  Google Cloud Translation `general/nmt`
  EN-tibbi  Google NMT ciktisina MedGemma 1.5 4B tibbi post-edit
  EN-ucuz   Helsinki-NLP `opus-mt-tc-big-tr-en` (CC-BY-4.0, ~0,2B parametre)

NEDEN GOOGLE: CT-RATE'in Ingilizcesi Google Translate ile uretildi ve Ingilizce
sozluklerimiz o metnin uzerinde gelistirildi. Baska bir cevirmen, sozlugun hic
gormedigi bir kelime dagilimi uretir ve EN kolunu HAKSIZ YERE kotu gosterir.
Ayrinti ve cheat siniri: docs/19 "Neden Google" bolumu.

BAGLAYICI KURALLAR (docs/19 §4):
  1. Ceviri birimi belgenin TAMAMIDIR - parcalama ve sonradan birlestirme yok.
     Model penceresi yetmiyorsa GORUNUR hata verilir, sessizce kirpilmaz.
  2. Belge kimligi ve sira korunur; altin etiketler pakete girmez.
  3. Google kolunda glossary, ozel model ve insan duzeltmesi yoktur.
  4. MedGemma yalniz tibbi post-edit uretir: bulgu ekleyemez, silemez,
     kesinligi veya SAYISAL DEGERI degistiremez, ozetleyemez.
  5. Uretken modellerde ornekleme KAPALI; sabit, tekrarlanabilir decoding.

Agir bagimliliklar (torch/transformers/google-cloud-translate) TEMBEL yuklenir;
bu modul onlar kurulu olmadan da import edilebilir ve test edilebilir.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from radyovlm.evaluation.task15 import ContractError, _exact_keys

# Sayi + opsiyonel birim. Radyoloji raporu olcum doludur ("12x8 mm", "1,5 cm");
# post-edit bunlarin HICBIRINI degistiremez.
SAYI = re.compile(r"\d+(?:[.,]\d+)?")
BIRIM = re.compile(
    r"\b(mm|cm|m|ml|cc|mg|g|kg|hu|mm2|cm2|mm3|cm3|mSv|kVp|mAs|%)\b", re.IGNORECASE
)


def sayi_imzasi(text: str) -> Counter:
    """Metindeki sayilarin coklu kumesi. Ondalik ayirici normalize edilir."""
    return Counter(s.replace(",", ".") for s in SAYI.findall(text))


def birim_imzasi(text: str) -> Counter:
    return Counter(b.lower() for b in BIRIM.findall(text))


# Post-edit ciktisinda GORULMEMESI gerekenler. Olculdu (2026-09-01, MedGemma
# belge duzeyi, 46 dev belgesi): ciktilarin %80'i Markdown tasiyordu ve bir
# belge tam bir "IMPRESSION" ozetine donusmustu. Istem bunlari yasaklamiyordu.
YAPISAL_YASAK = (
    (re.compile(r"\*\*|^\s*[*\-•]\s|^#{1,6}\s", re.MULTILINE), "Markdown bicimleme"),
    (re.compile(r"^\s*(IMPRESSION|CONCLUSION|SUMMARY)\s*:?\s*$", re.MULTILINE | re.IGNORECASE),
     "ozet/impression basligi"),
    (re.compile(r"^(here is|here's|sure,|certainly|i have)\b", re.IGNORECASE), "sohbet onsozu"),
    # Model istemi ciktiya kopyalarsa sayilar korunur ve digerleri de gecerdi.
    (re.compile(r"Absolute rules|Task: correct medical|Output the corrected text"),
     "istem sizintisi"),
    # Gemma ailesi dusunme izini `<unused94>thought` ile yayabiliyor. Olculdu
    # (kosu 2, istem v2): 46 belgenin 8'i bu izi tasiyordu ve iz icindeki
    # madde numaralari sayi denetimini de tetikledi. IZ SILINMEZ - silmek
    # cevabin nerede basladigini TAHMIN etmek olur ve sessizce veri bozar.
    (re.compile(r"<unused\d+>|<\|?thought|^\s*thought\b|The user wants me to",
                re.IGNORECASE | re.MULTILINE), "dusunme izi"),
)
UZUNLUK_ALT, UZUNLUK_UST = 0.70, 1.40


def yapisal_ihlaller(kaynak: str, hedef: str) -> list[str]:
    """Post-edit metni YENIDEN YAZMIS mi? Sayi denetiminin gormedigi ihlaller.

    Sayi korunumu tek basina yetmiyor: model olcumleri koruyup metni yine de
    Markdown listesine veya impression ozetine cevirebilir. Bunlar
    `docs/19` §4/4'un ozetleme ve aciklama yasaklarini ihlal eder.
    """
    ihlal = [ad for desen, ad in YAPISAL_YASAK if desen.search(hedef)]
    oran = len(hedef) / max(len(kaynak), 1)
    if oran < UZUNLUK_ALT:
        ihlal.append(f"metin kisalmis (oran {oran:.2f} < {UZUNLUK_ALT})")
    elif oran > UZUNLUK_UST:
        ihlal.append(f"metin uzamis (oran {oran:.2f} > {UZUNLUK_UST})")
    return ihlal


def sayi_korunumu_ihlalleri(
    kaynak: str, hedef: str, birim_kontrolu: bool = True
) -> list[str]:
    """Post-edit sayi/birim degistirdiyse ihlalleri dondur (bos = temiz).

    Bu, docs/24 §7'nin istedigi OTOMATIK denetimdir. Negasyon ve belirsizlik
    korunumu mekanik olarak dogrulanamaz; onlar kor insan kontrolune kalir.

    ⚠ `birim_kontrolu` yalniz AYNI DILDE anlamlidir - yani MedGemma post-editi
    (EN -> EN) icin. Turkce eklemeli bir dildir ve eki birime yapistirir:
    kaynakta `1 cmyi`, `5 mmlik`, `2 cmden` gecer; `\\bcm\\b` bunlari gormez ama
    hedefteki `1 cm`'i gorur ve YANLIS ALARM uretir. Olculdu (2026-09-01,
    `dev` 46 belge, TR->EN): 6 "ihlal"in 5'i bu artefaktti, gercek ihlal yoktu.
    Diller arasi kiyasta `birim_kontrolu=False` kullan - sayilar eklenme almaz.
    """
    imzalar = [("sayi", sayi_imzasi)]
    if birim_kontrolu:
        imzalar.append(("birim", birim_imzasi))
    ihlal = []
    for ad, imza in imzalar:
        k, h = imza(kaynak), imza(hedef)
        if k == h:
            continue
        dusen = sorted((k - h).elements())
        eklenen = sorted((h - k).elements())
        if dusen:
            ihlal.append(f"{ad} dustu: {dusen}")
        if eklenen:
            ihlal.append(f"{ad} eklendi: {eklenen}")
    return ihlal


# --------------------------------------------------------------------------
# Adaptorler - hepsi TranslationAdapter sozlesmesine uyar: .name + .translate()
# --------------------------------------------------------------------------


@dataclass
class OpusMtAdapter:
    """Helsinki-NLP Marian, CC-BY-4.0 (atif zorunlu, ticari kullanim serbest).

    Ucuz cevirmen kolu (D52). ~0,2B parametre; CPU'da kosar.

    Revizyon SABITLENIR; boylece kol bir tekrar-uretilebilirlik capasidir.
    """

    model_id: str = "Helsinki-NLP/opus-mt-tc-big-tr-en"
    revision: str = "main"
    num_beams: int = 4
    _paket: dict = field(default_factory=dict, repr=False)

    @property
    def name(self) -> str:
        return f"opus-mt:{self.model_id}@{self.revision}"

    def _yukle(self):
        if not self._paket:
            from transformers import MarianMTModel, MarianTokenizer

            tok = MarianTokenizer.from_pretrained(self.model_id, revision=self.revision)
            model = MarianMTModel.from_pretrained(
                self.model_id, revision=self.revision
            ).eval()
            self._paket = {"tok": tok, "model": model}
        return self._paket["tok"], self._paket["model"]

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        if (source_language, target_language) != ("tr", "en"):
            raise ContractError(f"{self.name} yalniz tr->en cevirir")
        tok, model = self._yukle()
        girdi = tok(text, return_tensors="pt")
        uzunluk = girdi["input_ids"].shape[1]
        sinir = getattr(tok, "model_max_length", 512)
        # Kural 1: parcalama yok. Sigmazsa sessizce kirpmak yerine DUR.
        if uzunluk >= sinir:
            raise ContractError(
                f"{self.name}: belge {uzunluk} token, model siniri {sinir}. "
                "Parcalama yasak (docs/19 §4/1); bu belge gorunur hata olarak kaydedilir."
            )
        cikti = model.generate(
            **girdi, num_beams=self.num_beams, do_sample=False, max_new_tokens=sinir
        )
        return tok.decode(cikti[0], skip_special_tokens=True)


# Cumle siniri: nokta/soru/unlem + BOSLUK + BUYUK HARF.
# Buyuk harf sarti kritik - Turkce radyolojide sira sayisi var:
#   "Sagda 4 ve 5. kotlarda"  -> "5." sonrasi kucuk harf, BOLUNMEZ
#   "1.5 cm"                  -> bosluk yok, BOLUNMEZ
# Ayirici gruplu yakalanir ki birlestirme KAYIPSIZ olsun.
CUMLE_SINIRI = re.compile(r"(?<=[.!?])(\s+)(?=[A-ZÇĞİÖŞÜ])")


def cumlelere_bol(metin: str) -> list[tuple[str, str]]:
    """(cumle, ayirici) ciftleri. Birlestirince ASIL METNI verir - kayipsiz."""
    parcalar, son = [], 0
    for m in CUMLE_SINIRI.finditer(metin):
        parcalar.append((metin[son : m.start()], m.group(1)))
        son = m.end()
    parcalar.append((metin[son:], ""))
    return parcalar


@dataclass
class CumleDuzeyiAdapter:
    """Cumle duzeyinde calisan bir cevirmeni belge duzeyi sozlesmeye sarar.

    NEDEN VAR (D54): Marian/OPUS bir CUMLE cevirmenidir. Tum belge verilince
    dagiliyor - olculdu, `dev` 46 belgede ciktinin ortalama uzunlugu 478 karakter
    (Google 1278), yani icerigin %62'si dusuyor ve uydurma uretiyor.

    docs/19 §4/1'in parcalama yasagi ANA kollar icindir; oradaki amac TR ile EN
    arasinda tek degisken birakmak. Bu sarmalayici yalniz UCUZ KOL icin
    kullanilir ve deneyin kaydinda sapma olarak yazilir.

    KAYIPSIZLIK ZORUNLU: bolme yalnizca boler, atmaz. Parcalarin asil metni
    yeniden uretmedigi durumda DURUR - sessizce cumle dusurmek, olcmek istedigimiz
    ceviri kaybini taklit eder ve sonucu yanlis yone cekerdi.
    """

    ic_adapter: object
    _atlanan: int = 0

    @property
    def name(self) -> str:
        return f"cumle-duzeyi({self.ic_adapter.name})"

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        parcalar = cumlelere_bol(text)
        if "".join(c + a for c, a in parcalar) != text:
            raise ContractError("Cumle bolmesi kayipli; asil metin yeniden uretilemedi")
        cevrilen = []
        for cumle, ayirici in parcalar:
            if not cumle.strip():
                cevrilen.append(cumle + ayirici)
                continue
            cikti = self.ic_adapter.translate(cumle, source_language, target_language)
            if type(cikti) is not str or not cikti.strip():
                raise ContractError(f"Bos cumle cevirisi: {cumle[:60]!r}")
            cevrilen.append(cikti + ayirici)
        return "".join(cevrilen)


@dataclass
class GoogleNmtAdapter:
    """Google Cloud Translation v3, `general/nmt`. Glossary ve ozellestirme YOK.

    Yonetilen model sonradan degisebilir; bu yuzden HAM yanit degismez deney
    artefakti olarak saklanir (docs/19 §2 "Kesin surum dondurmasi").
    """

    project_id: str
    location: str = "global"
    model: str = "general/nmt"
    _istemci: object | None = field(default=None, repr=False)
    son_yanit: dict = field(default_factory=dict, repr=False)

    @property
    def name(self) -> str:
        return f"google-nmt:{self.model}"

    def _client(self):
        if self._istemci is None:
            from google.cloud import translate

            self._istemci = translate.TranslationServiceClient()
        return self._istemci

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        istemci = self._client()
        ana = f"projects/{self.project_id}/locations/{self.location}"
        yanit = istemci.translate_text(
            request={
                "parent": ana,
                "contents": [text],
                "mime_type": "text/plain",
                "source_language_code": source_language,
                "target_language_code": target_language,
                # glossary_config ve model bilerek VERILMEZ: ozellestirme yok.
            }
        )
        if len(yanit.translations) != 1:
            raise ContractError("Google tek belge icin tek ceviri dondurmedi")
        self.son_yanit = {"raw": str(yanit)}
        return yanit.translations[0].translated_text


@dataclass
class MedGemmaPostEditAdapter:
    """Google NMT ciktisina anlam-koruyucu TIBBI post-edit (EN-tibbi kolu).

    Cevirmen DEGILDIR ve degerlendirici DE degildir (docs/19 §2): kendi
    duzenledigi metni puanlamaz. Ornekleme kapali, decoding sabittir.
    """

    model_id: str = "google/medgemma-1.5-4b-it"
    revision: str = "main"
    dort_bit: bool = True
    max_new_tokens: int = 1024
    _paket: dict = field(default_factory=dict, repr=False)

    # ISTEM v2 (2026-09-01). v1 "Rewrite the ... report" diyordu; model bunu bir
    # YENIDEN YAZMA daveti sayip Markdown listesi ve IMPRESSION ozeti uretti.
    # Olculdu: 46 dev belgesinin 0'i hem sayilari koruyup hem Markdown'suz cikti;
    # bir belge asil uzunlugunun %13'une inip impression ozetine dondu.
    # v2 gorevi "rapor yaz"dan "metin ici terim duzelt"e daraltir ve bicim
    # degistirmeyi ACIKCA yasaklar. Kanit: KARANTINA_medgemma_belge_duzeyi/
    ISTEM = (
        "Task: correct medical terminology inside the text below. This is NOT "
        "summarisation, NOT reformatting, NOT report writing.\n"
        "\n"
        "Answer immediately. Do NOT think step by step, do NOT explain your "
        "reasoning, do NOT write any analysis or plan before the answer.\n"
        "\n"
        "Absolute rules:\n"
        "- Keep EVERY sentence. Same order, same count. Nothing may be dropped, "
        "merged, or reordered.\n"
        "- Keep ALL section headings exactly as written (TECHNIQUE, FINDINGS, "
        "CLINICAL INFORMATION, ...).\n"
        "- Keep EVERY number, measurement and unit character-for-character.\n"
        "- Keep negation, uncertainty and hedging exactly as they are.\n"
        "- Do NOT produce an IMPRESSION, CONCLUSION or SUMMARY.\n"
        "- Do NOT use Markdown: no bold, no bullet lists, no headings.\n"
        "- Do NOT add commentary, preamble or explanation.\n"
        "- Change ONLY awkward or non-idiomatic medical wording.\n"
        "- If nothing needs changing, output the text unchanged.\n"
        "\n"
        "Output the corrected text and nothing else.\n"
        "\n"
        "Text:\n{text}"
    )

    @property
    def name(self) -> str:
        return f"medgemma-postedit:{self.model_id}@{self.revision}"

    def _yukle(self):
        # MedGemma COK KIPLI bir modeldir (goruntu+metin). `AutoModelForCausalLM`
        # ile yuklenmez; model karti `AutoProcessor` + `AutoModelForImageTextToText`
        # kullanir. Biz yalniz metin kipini kullaniyoruz.
        if not self._paket:
            import torch
            from transformers import AutoModelForImageTextToText, AutoProcessor

            kwargs = {"revision": self.revision, "dtype": torch.bfloat16}
            if self.dort_bit:
                from transformers import BitsAndBytesConfig

                kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16
                )
                kwargs["device_map"] = "auto"
            self._paket = {
                "islemci": AutoProcessor.from_pretrained(
                    self.model_id, revision=self.revision
                ),
                "model": AutoModelForImageTextToText.from_pretrained(
                    self.model_id, **kwargs
                ).eval(),
            }
        return self._paket["islemci"], self._paket["model"]

    def post_edit(self, text: str) -> str:
        islemci, model = self._yukle()
        mesaj = [
            {
                "role": "user",
                "content": [{"type": "text", "text": self.ISTEM.format(text=text)}],
            }
        ]
        girdi = islemci.apply_chat_template(
            mesaj,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)
        istem_uzunlugu = girdi["input_ids"].shape[-1]
        cikti = model.generate(
            **girdi,
            do_sample=False,  # kural 5: ornekleme KAPALI
            num_beams=1,
            max_new_tokens=self.max_new_tokens,
        )
        return islemci.decode(
            cikti[0][istem_uzunlugu:], skip_special_tokens=True
        ).strip()


# --------------------------------------------------------------------------
# Kosucu - kimlik/sira/sayi korunumunu zorlar
# --------------------------------------------------------------------------


@dataclass
class CumleDuzeyiPostEdit:
    """Post-editi CUMLE CUMLE yaptirir - belge duzeyi yeniden yazmayi engeller.

    NEDEN (kosu 2 olcumu): belge duzeyinde model 46 belgenin 20'sinde Markdown
    basligi/liste uretti ve 8'inde dusunme izini ciktiya yazdi. Tek cumle
    verilince ikisi de YAPISAL OLARAK zorlasir: bir cumleyi rapor bicimine
    sokamazsin, "sentence by sentence inceleyelim" diye plan da yapamazsin.

    Ayni ilac Opus-MT'de ise yaradi (D55): belge duzeyinde %62 icerik kaybi,
    cumle duzeyinde sorun kalmadi.

    KAYIPSIZLIK ZORUNLU - parcalar asil metni yeniden uretmezse DURUR.
    """

    ic_adapter: object

    @property
    def name(self) -> str:
        return f"cumle-duzeyi({self.ic_adapter.name})"

    @property
    def model_id(self):
        return getattr(self.ic_adapter, "model_id", None)

    @property
    def revision(self):
        return getattr(self.ic_adapter, "revision", None)

    def post_edit(self, text: str) -> str:
        parcalar = cumlelere_bol(text)
        if "".join(c + a for c, a in parcalar) != text:
            raise ContractError("Cumle bolmesi kayipli; asil metin yeniden uretilemedi")
        cikti = []
        for cumle, ayirici in parcalar:
            if not cumle.strip():
                cikti.append(cumle + ayirici)
                continue
            duzeltilmis = self.ic_adapter.post_edit(cumle)
            if type(duzeltilmis) is not str or not duzeltilmis.strip():
                raise ContractError(f"Bos cumle post-editi: {cumle[:60]!r}")
            cikti.append(duzeltilmis.strip() + ayirici)
        return "".join(cikti)


def run_post_edit(
    documents: Sequence[Mapping],
    adapter,
    strict_numbers: bool = True,
    erken_dur: int = 8,
    erken_dur_orani: float = 0.6,
) -> list[dict]:
    """Cevrilmis belgelere tibbi post-edit uygula; sayi/birim korunumunu denetle.

    `strict_numbers=True` ihlalde DURUR. `dev` uzerinde False ile kosulup
    ihlal profili olculebilir; `test`te daima True olmalidir.

    ERKEN DURDURMA: gevsek modda ilk `erken_dur` belgenin HEPSI ihlalliyse kosu
    durur. Olculdu - istem v1'in bozuk kosusunda ilk 5 belgenin 5'i de ihlalliydi
    ve kosu 22 dakika surdu; sonuc bastan belliydi. Modelin davranisi ilk birkac
    belgede belli olur. `erken_dur=0` kapatir.
    """
    output, seen = [], set()
    for expected_order, document in enumerate(documents):
        row = _exact_keys(
            dict(document),
            {"document_id", "order", "text", "adapter"},
            "post-edit girdisi",
        )
        if row["order"] != expected_order:
            raise ContractError("Post-edit girdisi sirasi kesintisiz degil")
        if row["document_id"] in seen:
            raise ContractError("Post-edit girdisinde tekrarli document_id")
        seen.add(row["document_id"])
        if type(row["text"]) is not str or not row["text"].strip():
            raise ContractError("Post-edit girdisinde bos metin")

        edited = adapter.post_edit(row["text"])
        if type(edited) is not str or not edited.strip():
            raise ContractError(f"Bos post-edit: {row['document_id']}")
        ihlaller = sayi_korunumu_ihlalleri(row["text"], edited)
        ihlaller += yapisal_ihlaller(row["text"], edited)
        if ihlaller and strict_numbers:
            raise ContractError(
                f"Post-edit korunum sozlesmesini bozdu ({row['document_id']}): "
                + "; ".join(ihlaller)
            )
        output.append(
            {
                "document_id": row["document_id"],
                "order": expected_order,
                "text": edited,
                "adapter": adapter.name,
                "base_adapter": row["adapter"],
                "number_violations": ihlaller,
            }
        )
        # Oransal esik: ilk surumde "hepsi ihlalli" sarti vardi ve kosu 2'de
        # ilk 5'in 4'u ihlalliyken TETIKLENMEDI. Artik cogunluk yeter.
        if (
            erken_dur
            and len(output) == erken_dur
            and sum(1 for r in output if r["number_violations"]) / erken_dur
            >= erken_dur_orani
        ):
            raise ContractError(
                f"ERKEN DURDURMA: ilk {erken_dur} belgenin "
                f"{sum(1 for r in output if r['number_violations'])}'i korunum "
                "sozlesmesini bozdu. Model bu istemle gorevi yapmiyor; kalan "
                f"{len(documents) - erken_dur} belgeyi kosmak zaman kaybi. "
                "Ornek: " + "; ".join(output[0]["number_violations"][:3])
            )
    return output
