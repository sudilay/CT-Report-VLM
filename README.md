# CT-Report-VLM

CT-RATE toraks BT kohortu üzerinde, radyoloji raporu ve BT görüntüsünden yapılandırılmış bulgu çıkarımı; farklı VLM/LLM modellerinin karşılaştırılması; patoloji doğrulamalı malignite değerlendirme pipeline'ı.

Projenin ayırt edici vurgusu yalnızca malignite yakalamak değil, **yanlış pozitifleri azaltmak**: negasyon, belirsizlik, stabilite ve benign niteleyicilerin doğru yorumlanması.

---

## Kapsam

| Aşama | İçerik |
|---|---|
| **Veri hazırlığı** | Rapor korpusunun kurulması, cümle bölütleme, şablon karakterizasyonu, ölçü normalizasyonu |
| **Yapılandırılmış çıkarım** | Bulgu, anatomik bölge, niteleyici, negasyon ve belirsizlik çıkarımı |
| **Değerlendirme şeması** | Malignite sınıflandırma şeması ve uyum ölçümlü altın standart |
| **VLM/LLM çıkarımı** | Standart prompt protokolüyle metin tabanlı gösterge çıkarımı |
| **VLM benchmark** | 3B BT üzerinde lezyon tespiti, lokalizasyon ve morfoloji karşılaştırması |
| **Malignite değerlendirme** | Kanıt birleştirme, karar katmanı, yanlış pozitif azaltma |
| **Patoloji doğrulama** | Patoloji raporlarının yapılandırılması ve uyum analizi |
| **Değerlendirme** | Ayrım gücü, kalibrasyon, alt grup ve ablasyon analizleri |

---

## Veri

**Veri bu depoda tutulmaz.** CT-RATE `CC-BY-NC-SA-4.0` lisanslıdır (ticari kullanım yok) ve HuggingFace üzerinde erişim onayı gerektirir.

Kohort: kontrastsız toraks BT, 25.692 çalışma / 21.304 hasta, eşleşen radyoloji raporları ve 18 anormallik etiketi.

1. [huggingface.co/datasets/ibrahimhamamci/CT-RATE](https://huggingface.co/datasets/ibrahimhamamci/CT-RATE) üzerinden erişim al
2. Şu dosyaları `data/raw/ct_rate/` altına indir:
   - `dataset/radiology_text_reports/{train,validation}_reports.csv`
   - `dataset/multi_abnormality_labels/{train,valid}_predicted_labels.csv`
   - `dataset/metadata/{train,validation}_metadata.csv`
   - `dataset/metadata/no_chest_{train,valid}.txt`

---

## Kurulum ve çalıştırma

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

```bash
# Ham CSV -> çalışma düzeyi korpus
.venv/Scripts/python.exe scripts/01_build_report_corpus.py

# Cümlelere bölme (karakter ofsetleriyle)
.venv/Scripts/python.exe scripts/04_segment_sentences.py

# Doğrulama
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
  test_corpus.py               korpus bütünlüğü
  test_sentences.py            bölütleme ve zor vaka takımı

docs/
  01_veri_notlari.md           ölçülmüş veri bulguları ve tuzaklar
  03_standartlastirma_plani.md tasarım kararları ve gerekçeleri

data/                          veri (depoya dahil değil)
```

---

## Yöntem ilkeleri

Tasarım kararları veriden **ölçülerek** verilir, varsayımla değil. Projeye yön veren kurallar:

- **Bölme hasta düzeyinde yapılır.** Aynı çalışmanın farklı rekonstrüksiyonları birebir aynı raporu taşır; hacim düzeyinde bölmek aynı raporu hem eğitime hem teste düşürür.
- **Her cümle ve ölçü, kaynak metindeki karakter ofsetini taşır.** Bu izlenebilirlik, sonraki fazlarda model çıktısının rapora dayanıp dayanmadığını denetlemek için gereklidir.
- **Veri hazırlığı korur, karar vermez.** Eşik ve ağırlık kuralları değerlendirme katmanına aittir.
- **Negasyon, şablon ve malignite ilgisi üç ayrı eksendir.** Olumsuzlanmış bir bulgu otomatik olarak malignite aleyhine kanıt değildir.
- **Şablon istatistiği yalnızca eğitim kümesinde hesaplanır**, doğrulama kümesinden ön işlemeye bilgi sızmaması için.
- **Kabul ölçütleri sonuç görülmeden yazılır.**

Ayrıntılı gerekçeler: [docs/01_veri_notlari.md](docs/01_veri_notlari.md) ve [docs/03_standartlastirma_plani.md](docs/03_standartlastirma_plani.md)

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

## Kaynaklar

- Hamamci et al., *Developing Generalist Foundation Models from a Multimodal Dataset for 3D Computed Tomography*, arXiv:2403.17834 — CT-RATE veri seti
- Eyre et al., *Launching into clinical space with medspaCy*, AMIA 2021
- Chapman et al., *A simple algorithm for identifying negated findings and diseases in discharge summaries*, J Biomed Inform 2001 — NegEx
