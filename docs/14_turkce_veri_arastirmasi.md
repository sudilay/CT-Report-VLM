# Türkçe Radyoloji Verisi Araştırması — 2026-08-28

Sistemin dili Türkçe olacak. Bu belge, **kamuya açık Türkçe radyoloji raporu**
aramasının sonucudur. Her aday indirilip **içeriğine bakılarak** değerlendirildi;
makale özetine güvenilmedi.

---

## Sonuç tablosu

| Kaynak | Ne | Karar |
|---|---|---|
| **RadTr** | 1.364 belge · **292 toraks BT** · radyologlar yazdı, 3 radyolog etiketledi | ✅ **kullanılabilir** |
| PARROT | 48 Türkçe · 28 toraks BT ama **hepsi koroner anjiyo** | ❌ elendi |
| CT-RATE Türkçe aslı | Yayımlanmadı; yalnızca İngilizce çevirisi açık | ⚠ istenebilir |
| Model-SEY (Elazığ) | Türkçe göğüs **röntgeni**; hastane verisi paylaşılmıyor | ❌ |
| `turkish-clinical-ner` | n<1K; depoda **veri dosyası yok** | ❌ |
| `Turkish-Medical-Notes` | blog yazıları, radyoloji raporu değil | ❌ |
| `turkish-medical-deid-eval` | kimliksizleştirme değerlendirmesi | ❌ |
| TurkMedNLI | çeviriyle üretilmiş çıkarım veri seti | ❌ |

---

## RadTr — tek gerçek aday

[Diagnostic and Interventional Radiology, 2025](https://www.dirjournal.org/articles/deep-learning-for-named-entity-recognition-in-turkish-radiology-reports/doi/dir.2025.243100) ·
[github.com/BIGDaTA-Lab-AI/dygiepp-multilingual-radiology](https://github.com/BIGDaTA-Lab-AI/dygiepp-multilingual-radiology)

### Ölçülen içerik (indirilip sayıldı, makaleden alınmadı)

| | |
|---|---|
| Belge | **1.364** (train 1.057 · dev 132 · test 175) |
| Etiketli varlık | **36.520** |
| Ortalama uzunluk | 114 kelime |

**Bölgeye göre** — makale *"toraks"* diyor ama gerçek dağılım geniş:

| bölge | belge |
|---|---|
| abdomen | 449 (%33) |
| **toraks BT** | **292 (%21)** |
| beyin | 234 (%17) |
| anjiyo | 156 (%11) |
| diğer | 233 (%17) |

Toraks alt kümesinin **114'ünde nodül**, 7'sinde malignite geçiyor.

### Etiketler — bizim eksenlerimizle örtüşüyor

| RadTr | sayı | Bizdeki karşılığı |
|---|---|---|
| `Obs_Anatomy` | 16.577 | `entity_type = anatomy` |
| `Obs_Present` | 12.178 | `assertion = present` |
| `Obs_Absent` | 2.828 | `assertion = absent` |
| **`Obs_Technical`** | **1.721** | **D30 — teknik çekince ayrı eksen** |
| `Obs_Uncertain` | 1.160 | `assertion = uncertain` |
| `Differential Diagnosis` | 1.001 | `belirsizlik:ayirici_tani` |
| `Obs_Advice` | 395 | *"öneri kesinliği değiştirmez"* kuralımız |

### D30'un dış doğrulaması

`Obs_Technical` span'larının **%97'si** `Obs_Uncertain` ile **örtüşmüyor**
(1.664 / 1.721). Yani üç Türk radyolog, bağımsız olarak, teknik yetersizliği
belirsizlikten **ayrı** bir kategori saymış.

Bu, D30 kararının dış kaynakla doğrulanmasıdır: *"optimal değerlendirilemedi"*
bulgunun belirsizliği değil, tetkikin kısıtıdır.

### Örnek — tam bizim alanımız

> *"IVKM verilmediğinden kalp boşlukları, mediastinal vasküler yapılar ve lenf
> nodları açısından değerlendirme optimal yapılamamıştır."* → `Obs_Technical`
>
> *"...patolojik boyutta lenf nodları mevcuttur."* → `Obs_Present`
>
> *"...plevral sıvı saptanmadı."* → `Obs_Absent`
>
> *"...8 mm çapa ulaşan solid nodüller izlenmiştir."* → `Obs_Present`

---

## "Sentetik" burada ne demek — ve neye mal oluyor

**Sentetik = makine üretimi değil.** RadTr'de:

- Raporları **radyologlar elle yazdı**, gerçek raporları taklit ederek
- Sebep: gerçek hasta verisi mahremiyet nedeniyle paylaşılamıyor
- **Üç radyolog paralel etiketledi**, bir kişi kalite denetimi yaptı

Yani dil de klinik içerik de uzman ürünü. Bu meşru ve alanda yaygın bir yöntem.

**Ama bedeli var, gizlenmemeli:**

| Sentetik veride | Gerçek raporda |
|---|---|
| Temiz, tutarlı şablon | Yazım hataları, kopyala-yapıştır artığı, çelişki |
| Ders kitabı ifadeleri | Kuruma özgü alışkanlıklar, kısaltmalar |
| Dengeli dağılım | Gerçek sıklıklar (RadTr'de malignite yalnızca %2) |
| Hasta bağlantısı **yok** | Patoloji doğrulaması mümkün |

**Bu ayrım iddia sınırını belirler:**

- ✅ RadTr ile **Türkçe çıkarım kurallarını kurabilir ve doğrulayabiliriz**
- ❌ RadTr ile **gerçek dünya başarımı iddia edemeyiz**

İkisi farklı iddialardır; hangisini yaptığımız raporda açıkça yazılmalı.

---

## PARROT neden elendi

48 Türkçe raporun 28'i toraks BT, ama **28'inin tamamı koroner BT anjiyografi**,
`CV` alt uzmanlığı, **2 katkıcı**, tek şablon. Akciğerden söz eden tek satır her
raporda birebir aynı:

> *"Akciğerler, mediastinum ve üst abdomenin sınırlı görünümlerinde anlamlı ekstra
> kardiyak bulgu yoktur."*

Nodül yok, ölçü yok, malignite yok.

**Yine de bir değeri var:** çeviriler radyologların **kendisi** tarafından
yapılmış (makine değil). Makine çevirisini uzman çevirisine karşı ölçmek için
28 eşli rapor kullanılabilir. Ayrıca diğer diller kalabalık (Lehçe 837,
Fransızca 475) ve veri seti zaten *"çok dilli LLM sınaması"* için tasarlanmış.

Lisans CC BY-NC-SA 4.0; yazarlar **"eğitim için değil, test için"** diyor.

---

## Geriye kalan en değerli yol

**CT-RATE'in Türkçe asılları yayımlanmadı ama yok olmadı.** Veri İstanbul
Medipol'de üretildi; İngilizce sürüm makine çevirisidir. Türkçe asıllara erişim
için tek yol **veri sahiplerine sormaktır**.

Bu istenmeye değer: elimizdeki 25.692 tetkikin **Türkçesi** demek, bugüne kadar
İngilizce üzerinde kurduğumuz her şeyin doğrudan Türkçeye taşınması demek.

---

## Öneri

| sıra | iş | gerekçe |
|---|---|---|
| 1 | **CT-RATE Türkçe asılları istensin** | En yüksek değerli, en düşük maliyetli adım |
| 2 | **RadTr toraks alt kümesi (292) alınsın** | Türkçe kural geliştirmenin zemini |
| 3 | RadTr etiketleri bizim şemamıza eşlensin | Örtüşme yüksek; eşleme tablosu yazılmalı |
| 4 | Gerçek dünya iddiası için kurum verisi | Sentetik veri bunu karşılamaz |

⚠ RadTr deposunun `LICENSE` dosyası **MIT** ama telif *"David Wadden 2021"* —
bu, çatallanılan DyGIE++ **kodunun** lisansı. **Verinin** lisansı ayrıca
doğrulanmalı; yazarlara sorulmadan yayında kullanılmamalı.
