# CT-Report-VLM

CT-RATE toraks BT kohortu üzerinde, radyoloji raporu ve BT görüntüsünden yapılandırılmış bulgu çıkarımı; farklı VLM/LLM modellerinin karşılaştırılması; patoloji doğrulamalı malignite değerlendirme pipeline'ı.

Projenin ayırt edici vurgusu yalnızca malignite yakalamak değil, **yanlış pozitifleri azaltmak**: negasyon, belirsizlik, stabilite ve benign niteleyicilerin doğru yorumlanması.

---

## Durum

| | |
|---|---|
| Aktif faz | **Faz 1 — Veri Hazırlığı** |
| Aktif iş | Cümle bölütleme tamamlandı, şablon karakterizasyonu sırada |
| Testler | **43 / 43 geçiyor** |

---

## Şu ana kadar üretilenler

**Rapor korpusu** — 50.188 rekonstrüksiyon çalışma düzeyinde tekilleştirilerek **25.692 çalışma / 21.304 hasta**. Bu üç sayı da CT-RATE yayınında bildirilenlerle birebir örtüşüyor.

**Cümle tablosu** — **479.051 cümle**, her biri orijinal metindeki karakter ofsetiyle. Ofset doğrulaması %100: her cümle `report_text[char_start:char_end]` ile birebir eşleşiyor. Bu izlenebilirlik, sonraki fazlarda "model bu bulguyu gerçekten raporda gördü mü?" sorusunu yanıtlamak için gerekli.

**Doğrulama takımı** — 43 test: korpus bütünlüğü, hasta düzeyinde sızıntı kontrolü, tekilleştirmenin bilgi kaybetmediğinin doğrulanması ve elle seçilmiş zor vakalar (ondalık ölçüler, aralıklar, çoklu ölçü, negasyon, madde işaretleri, bozuk noktalama).

---

## Kurulum

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### Veri

**Veri bu depoda yoktur.** CT-RATE `CC-BY-NC-SA-4.0` lisanslıdır (ticari kullanım yok) ve HuggingFace üzerinde erişim onayı gerektirir.

1. [huggingface.co/datasets/ibrahimhamamci/CT-RATE](https://huggingface.co/datasets/ibrahimhamamci/CT-RATE) üzerinden erişim al
2. Şu dosyaları `data/raw/ct_rate/` altına indir:
   - `dataset/radiology_text_reports/{train,validation}_reports.csv`
   - `dataset/multi_abnormality_labels/{train,valid}_predicted_labels.csv`
   - `dataset/metadata/{train,validation}_metadata.csv`
   - `dataset/metadata/no_chest_{train,valid}.txt`
3. Korpusu üret ve doğrula:

```bash
.venv/Scripts/python.exe scripts/01_build_report_corpus.py
.venv/Scripts/python.exe scripts/04_segment_sentences.py
.venv/Scripts/python.exe -m pytest tests/ -q
```

Cümle bölütleme tam korpusta yaklaşık 11 dakika sürer.

---

## Depo yapısı

```
scripts/
  01_build_report_corpus.py    ham CSV -> çalışma düzeyi korpus
  02_inspect_corpus.py         inceleme aracı
  04_segment_sentences.py      cümle bölütleme (karakter ofsetli)
  05_template_stats.py         şablon istatistiği ve eşik adayları

tests/
  test_corpus.py               korpus bütünlüğü (17 test)
  test_sentences.py            bölütleme + zor vaka takımı (26 test)

docs/
  01_veri_notlari.md           ölçülmüş veri bulguları ve tuzaklar
  03_standartlastirma_plani.md tasarım kararları ve gerekçeleri

data/                          veri (depoya dahil değil)
```

---

## Tasarım gerekçeleri

Koddaki kararların çoğu veriden ölçülerek verildi, varsayımla değil. İki belge bunları taşıyor:

- **[docs/01_veri_notlari.md](docs/01_veri_notlari.md)** — Neden çalışma düzeyinde tekilleştirme yapıldığı, cümlelerin %75'inin neden şablon olduğu, `tumoral` kelimesinin neden %100 olumsuz cümlelerde geçtiği, CT-RATE'te neden malignite ground truth'u bulunmadığı.
- **[docs/03_standartlastirma_plani.md](docs/03_standartlastirma_plani.md)** — D1–D11 kararları: veri modeli, bölütleme kuralının nasıl seçildiği, ofset referansı, şablon istatistiğinin neden yalnızca eğitim kümesinde hesaplandığı, ölçü normalizasyonu.

Örnek: `04_segment_sentences.py` blok bölme kuralı kullanır. Sebebi ölçüldü — Impression'daki 27.985 çift boşluk sınırının **%14,1'inde öncesinde noktalama yok**, dolayısıyla yalnızca cümle bölütleyici kullanmak bu maddeleri birleştirip kaybediyordu.

---

## İnceleme komutları

```bash
# Korpusun genel tablosu: demografi, etiket prevalansı, şablon yükü
.venv/Scripts/python.exe scripts/02_inspect_corpus.py

# Tek raporu oku / cümlelere bölünmüşünü ofsetleriyle gör
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --report 7
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --sents 7

# En uzun / en kısa cümleler ve uzunluk dağılımı
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --uc

# Kelime arama
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --search spicul
```

---

## Atıf

CT-RATE veri seti kullanıldığında atıf zorunludur:

> Hamamci et al., *Developing Generalist Foundation Models from a Multimodal Dataset for 3D Computed Tomography*, arXiv:2403.17834

Negasyon ve belirsizlik çözümlemesi için kullanılan araçlar:

> Eyre et al., *Launching into clinical space with medspaCy*, AMIA 2021
> Chapman et al., *A simple algorithm for identifying negated findings and diseases in discharge summaries*, J Biomed Inform 2001 (NegEx)
