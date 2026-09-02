# -*- coding: utf-8 -*-
"""TASK-15 · IKINCIL MODEL adaptoru - kapali JSON sozlesmesiyle kavram cikarimi.

ROL (docs/19 §3): Bu model BIRINCIL olcum DEGILDIR. Birincil karar dondurulmus
sozluk/kapsam sisteminden gelir; bu modelin isi o kararin ALETE BAGLI OLMADIGINI
sinamaktir. Bu yuzden model sozlugu, desenleri ve birincil ciktiyi HIC GORMEZ -
yalniz metni ve kapali 144'luk kavram ENVANTERINI gorur.

GUVENLIKLER:
  * Model iki dili AYNI ANDA GORMEZ. Uc kol (TR, EN-genel, EN-ucuz) birbirinden
    bagimsiz kosulur; girdinin dili disinda HICBIR SEY degismez - ayni model
    revizyonu, ayni Ingilizce talimat, ayni envanter, ayni uretim parametreleri.
  * Istem ceviriden, dil karsilastirmasindan ya da deneyin amacindan SOZ ETMEZ.
    Etseydi model kolu tanir ve davranisini degistirebilirdi.
  * Adaylar YALNIZ Qwen3.5-4B ve Aya Expanse 8B'dir (docs/19 §2, secim sirasi).
    MedGemma aday DEGILDIR - kendi post-editini degerlendirmesi donguselllik
    olurdu; ayrica EN-tibbi kolu D63 ile dusuruldu. Bu modulde ve uzak makine
    paketinde MedGemma kodu, istemi veya ciktisi BULUNMAZ.

URETIM AYARLARI (docs/19 §4.5): ornekleme KAPALI, num_beams=1, Qwen'de dusunme
modu KAPALI, sabit ve tekrarlanabilir decoding.

D59 DERSI: Cikti sozlesmesini YAPISAL KAPILARLA zorlamazsan model varsayilan
davranisina doner. Ham yanit HER ZAMAN saklanir; gecersiz cikti SILINMEZ,
ONARILMAZ - isaretlenir ve sayilir (docs/19 §4.2: "sonradan icerik onarimi
yapilmaz").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Istem SURUMU - degistirilirse surum de degisir ve provenance'a yazilir.
ISTEM_SURUMU = "ikincil-v2"


def istemi_yukle(yol: Path) -> str:
    """Dondurulmus istem sablonunu okur. `{envanter}` ve `{text}` yuvalari olmali."""
    metin = yol.read_text(encoding="utf-8")
    for yuva in ("{envanter}", "{text}"):
        if yuva not in metin:
            raise ValueError(f"Istem sablonunda {yuva} yuvasi yok: {yol}")
    return metin


def envanter_blogu(envanter: frozenset[str]) -> str:
    """Envanteri isteme gomulecek deterministik metne cevirir.

    SIRALI olmali - kume sirasi Python calismalari arasinda degisebilir ve
    istem degisirse ayni model farkli cikti verebilir; o zaman kollar arasi
    fark modelin degil istemin farki olur.
    """
    return "\n".join(sorted(envanter))


@dataclass
class IkincilModelAdapter:
    """HuggingFace nedensel dil modeliyle kapali JSON kavram cikarimi.

    VARSAYILAN TAM bfloat16'dir, nicemleme YOKTUR. Sebep: 4-bit nicemleme
    modelin ciktisini degistirebilir; "bu model gorevi yapamadi" hukmu verirken
    nicemlemenin payini ayirt edemeyiz. Bellek yetmezse `--dort-bit` acikca
    istenir ve provenance'a yazilir; o zaman hukum "4-bit nicemlenmis haliyle"
    diye kayitlanir.
    """

    model_id: str
    istem_sablonu: str
    envanter_metni: str
    revision: str
    dort_bit: bool = False
    max_new_tokens: int = 2048
    dusunme_kapali: bool = True
    _paket: dict = field(default_factory=dict, repr=False)

    @property
    def name(self) -> str:
        kip = "4bit" if self.dort_bit else "bf16"
        return (
            f"ikincil:{self.model_id}@{self.revision}:{ISTEM_SURUMU}:"
            f"{kip}:mt{self.max_new_tokens}"
        )

    def istem(self, text: str) -> str:
        """Yuvalari DUZ METIN DEGISIMIYLE doldurur - `str.format` DEGIL.

        Sebep (kuru kosuda yakalandi): istem sablonu cikti semasini gostermek
        icin gercek JSON iceriyor -> `{"findings": ...}`. `str.format` bunu bir
        yuva sanip KeyError atiyordu. Sablonda susluleri kacismak (`{{`) da
        cozum degil: istem dondurulmus bir belgedir ve MODELIN GORECEGI metin
        ile dosyadaki metin BIREBIR AYNI olmalidir.
        """
        return self.istem_sablonu.replace("{envanter}", self.envanter_metni).replace(
            "{text}", text
        )

    def _yukle(self):
        if self._paket:
            return self._paket["isleyici"], self._paket["model"]
        import torch
        from transformers import (
            AutoConfig,
            AutoModelForCausalLM,
            AutoModelForMultimodalLM,
            AutoProcessor,
            AutoTokenizer,
        )

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA GPU bulunamadi; CPU kosusu yasak")
        if not self.dort_bit and not torch.cuda.is_bf16_supported():
            raise RuntimeError("GPU bfloat16 desteklemiyor; tam hassasiyet kosusu baslatilmadi")

        torch.cuda.reset_peak_memory_stats()
        config = AutoConfig.from_pretrained(self.model_id, revision=self.revision)
        qwen_multimodal = config.model_type == "qwen3_5"

        kwargs: dict = {
            "revision": self.revision,
            "dtype": torch.bfloat16,
            "device_map": "auto",
        }
        if self.dort_bit:
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16
            )
        isleyici_sinifi = AutoProcessor if qwen_multimodal else AutoTokenizer
        model_sinifi = AutoModelForMultimodalLM if qwen_multimodal else AutoModelForCausalLM
        self._paket = {
            "isleyici": isleyici_sinifi.from_pretrained(
                self.model_id, revision=self.revision
            ),
            "model": model_sinifi.from_pretrained(self.model_id, **kwargs).eval(),
            "qwen_multimodal": qwen_multimodal,
        }
        cihazlar = {
            str(cihaz)
            for cihaz in getattr(self._paket["model"], "hf_device_map", {}).values()
        }
        if "cpu" in cihazlar or "disk" in cihazlar:
            raise RuntimeError("Model CPU/disk'e tasiyor; kosu tamamen GPU'da olmali")
        if not cihazlar and self._paket["model"].device.type != "cuda":
            raise RuntimeError("Model GPU'ya yuklenemedi")
        return self._paket["isleyici"], self._paket["model"]

    def hazirla(self) -> None:
        """Modeli kosudan once yukle; yukleme hatasi bos deney dosyasi yaratmasin."""
        self._yukle()

    def _sohbet_girdisi(self, isleyici, mesaj):
        """Dusunme modunu KAPATMAYA calisir; desteklemeyen modelde sessizce duser.

        Hangi yolun kullanildigi `sohbet_sablonu_kipi`ye yazilir ve provenance'a
        girer - "dusunme kapaliydi" iddiasi kanitsiz kalmaz.
        """
        if self.dusunme_kapali:
            try:
                girdi = isleyici.apply_chat_template(
                    mesaj,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_dict=True,
                    return_tensors="pt",
                    enable_thinking=False,
                )
                self._paket["sohbet_sablonu_kipi"] = "enable_thinking=False"
                return girdi
            except TypeError:
                pass
        girdi = isleyici.apply_chat_template(
            mesaj,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        self._paket.setdefault("sohbet_sablonu_kipi", "varsayilan")
        return girdi

    @property
    def sohbet_sablonu_kipi(self) -> str:
        return self._paket.get("sohbet_sablonu_kipi", "yuklenmedi")

    def generate(self, text: str, prompt: str = "") -> str:  # noqa: ARG002
        """Tek belgeden ham model yaniti uretir. Dogrulama CAGIRANIN isidir.

        `prompt` argumani `SecondaryModelAdapter` protokolu icin durur; istem
        adaptorde dondurulmustur ve disaridan degistirilemez - boylece kollar
        arasinda istem farki olusamaz.
        """
        import torch

        isleyici, model = self._yukle()
        icerik = self.istem(text)
        if self._paket["qwen_multimodal"]:
            icerik = [{"type": "text", "text": icerik}]
        mesaj = [{"role": "user", "content": icerik}]
        girdi = self._sohbet_girdisi(isleyici, mesaj).to(model.device)
        istem_uzunlugu = girdi["input_ids"].shape[-1]
        tokenizer = getattr(isleyici, "tokenizer", isleyici)
        pad_token_id = tokenizer.pad_token_id
        if pad_token_id is None:
            pad_token_id = tokenizer.eos_token_id
        with torch.no_grad():
            cikti = model.generate(
                **girdi,
                do_sample=False,  # docs/19 §4.5: ornekleme KAPALI
                num_beams=1,
                temperature=None,
                top_p=None,
                top_k=None,
                max_new_tokens=self.max_new_tokens,
                pad_token_id=pad_token_id,
            )
        return isleyici.decode(
            cikti[0][istem_uzunlugu:], skip_special_tokens=True
        ).strip()

    def uretim_parametreleri(self) -> dict:
        return {
            "do_sample": False,
            "num_beams": 1,
            "temperature": None,
            "top_p": None,
            "top_k": None,
            "max_new_tokens": self.max_new_tokens,
            "dort_bit": self.dort_bit,
            "dtype": "bfloat16",
            "dusunme_kapali_istendi": self.dusunme_kapali,
            "sohbet_sablonu_kipi": self.sohbet_sablonu_kipi,
            "istem_surumu": ISTEM_SURUMU,
        }
