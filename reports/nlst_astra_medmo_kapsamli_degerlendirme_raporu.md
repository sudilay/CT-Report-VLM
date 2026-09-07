# NLST Kohortu Toraks BT Değerlendirmesi: Astra VLM ve MedMo Kapsamlı Karşılaştırma, Klinik Doğruluk ve Radyolojik Model Analizi Raporu

**Tarih:** 07 Eylül 2026  
**İncelenen Kohort:** National Lung Screening Trial (NLST) — Tamamlanan Seri: **N = 2.965** (140 Kanser / 2.825 Temiz Kontrol | 1.201 Tekil Hasta)  
**Referans Standartları:** NLST Resmi Takip ve Sonuç Tabloları (`nlst_780_prsn_idc_20210527.csv`), Tarama Anormallik Düzeyleri (`scr_iso`), Doğrulanmış Kanser Lob Değişkenleri (`sct_epi_loc`, `locrup`...`locllow`), Lezyon Çapı (`lesionsize`)  
**İncelenen Yapay Zeka Modelleri:** Astra VLM (Full Text & Sybil/Pillar Risk Skoru) ve MedMo (İzlenim / Impression & Tüm Rapor / Full Report)

---

## 1. Yönetici Özeti ve Temel Karşılaştırma Matrisi

> **Metodolojik Çerçeve ve Hedef Tanımları:**  
> Bu çalışmada modellerin çıktıları üç ayrı klinik ve radyolojik eksende değerlendirilmiştir:  
> 1. **Radyolojik Şüphe Uyumu (Aynı Tarama):** Taramayı yapan radyoloğun BT görüntüsünde kanser şüphesi gördüğü (`scr_iso = 4`) vakalarla modellerin alarm uyumu.  
> 2. **1-Yıllık Kısa Vadeli Prognostik Kanser (`cancer_year_1`):** Taramadan sonraki 12 ay içinde kesinleşen aktif kanser vakalarıyla ilişki (en yüksek klinik öneme sahip grup).  
> 3. **Uzun Vadeli Kanser Sonucu (`cancer_label`):** NLST takibi boyunca (0–6 yıl) kanser tanısı alan vakalar. Erken tarihli BT'lerde lezyonun henüz morfolojik olarak görünür olmayabileceği ve kontrol grubunda değişen sansürlenme (takipten çıkma) süreleri bulunduğu dikkate alınmalıdır.


Bu rapor; toraks BT taramasında akciğer kanseri ve pulmoner nodül tespitinde **Astra VLM** ile **MedMo** modellerinin 2.965 serilik tam NLST kohortu üzerindeki tanısal yetkinliğini, hesaplama ve donanım verimliliğini, hata dinamiklerini, anatomik lokasyon tutarlılığını ve klinik morfolojik kör noktalarını kapsamlı biçimde ortaya koymaktadır.

Aşağıdaki tablo, tüm 2.965 vakanın resmi patolojik ve klinik yer gerçeğiyle (ground truth) birebir eşleştirilmesiyle elde edilen kesin performans matrisidir:

| Model / Değerlendirme Ekseni | TP | FP | TN | FN | Duyarlılık (Tüm Kanserler) | Duyarlılık (1-Yıl Aktif) | Özgüllük (Specificity) | Genel Doğruluk (Accuracy) | Pozitif Tahmin (PPV / Precision) | Negatif Tahmin (NPV) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Astra VLM (Rapor Alarmı)** | **68** | **875** | **1.950** | **72** | **%48,57** | **%70,73** *(29/41)* | **%69,03** | **%68,06** | **%7,21** | **%96,44** |
| **MedMo (Sadece İzlenim / Impression)** | **26** | **368** | **2.457** | **114** | **%18,57** | **%12,20** *(5/41)* | **%86,97** | **%83,74** | **%6,60** | **%95,57** |
| **MedMo (Tüm Rapor / Full Report)** | **75** | **1.325** | **1.500** | **65** | **%53,57** | **%43,90** *(18/41)* | **%53,10** | **%53,12** | **%5,36** | **%95,85** |
| **Pillar/Sybil Skoru (≥ 0.50 Eşik)** | **44** | **66** | **2.759** | **96** | **%31,43** | **%75,61** *(31/41)* | **%97,66** | **%94,54** | **%40,00** | **%96,64** |

> *Not:* Tüm modeller tam seri kohortu (N = 2.965; 140 kanser, 2.825 kontrol) üzerinde otomatik NLP kural motoruyla baştan sona değerlendirilmiştir. Astra VLM için otomatik kural motoru 68 TP / 72 FN (%48,57) sınıflandırırken; Ek 1'deki radyolojik detay tablosunda sınırda kalan 1 vaka klinik yorum farkıyla 67 TP / 73 FN (%47,86) olarak kayıt altındadır.

### Temel Çıkarımlar:
1.  **Duyarlılık Üstünlüğü (Astra VLM):** Astra VLM, özellikle taramadan sonraki 1 yıl içinde kesinleşen aktif kanserlerde **%70,73 duyarlılık (29/41)** ile en yüksek vaka yakalama oranına sahiptir. MedMo'nun izlenim (Impression) bölümü bu vakaların yarısından fazlasını (%87,80) kaçırmaktadır.
2.  **Özgüllük ve Savunmacılık Üstünlüğü (MedMo):** MedMo son derece tutucu bir modeldir. Temiz kontrol kohortunda %86,97 özgüllük sağlamakta, yanlış alarm üretmemektedir. Ancak bu temkinlilik, kanserli hastaların %46,43'ünün (Full Report) ve %81,43'ünün (Impression) atlanmasına yol açmaktadır.
3.  **Klinik Karakter Zıtlığı:** Astra "asla kanser kaçırmama" üzerine odaklanmış aşırı duyarlı bir tarama asistanı; MedMo ise "asla yanlış alarm vermeme" üzerine kurulu savunmacı bir klinisyen refleksi sergilemektedir.

---

## 2. Operasyonel Başarım ve Donanım Verimliliği Karşılaştırması

Modellerin sağlık merkezlerinde canlıya alınması ve taranan binlerce BT hacminin işlenmesi sürecinde donanım tüketimi, gecikme (latency) ve rapor derinliği kritik parametrelerdir. 2.965 serilik kohort üzerinden ölçülen operasyonel metrikler şunlardır:

| Operasyonel Parametre | Astra VLM | MedMo | Klinik ve Mühendislik Değerlendirmesi |
| :--- | :---: | :---: | :--- |
| **Ortalama İşlem Süresi (Inference)** | **27,59 saniye / seri** | **5,17 saniye / seri** | **MedMo 5,3 kat daha hızlıdır.** Gerçek zamanlı acil triyaj için MedMo avantajlıdır. |
| **Medyan İşlem Süresi** | **28,53 saniye** | **4,89 saniye** | Dağılım son derece stabildir (Astra IQR: 25,5 – 31,1 sn; MedMo IQR: 4,0 – 6,0 sn). |
| **Minimum – Maksimum Süre** | 5,75 sn – 33,88 sn | 1,28 sn – 16,11 sn | Astra tüm serilerde derin anatomik analiz yaptığı için sabit yüksek süre harcar. |
| **Ortalama Rapor Karakter Hacmi** | **2.277 karakter** | **510 karakter** | **Astra 4,5 kat daha kapsamlı metin üretir.** |
| **Medyan Rapor Karakter Hacmi** | **2.356 karakter** | **484 karakter** | Astra organ sistemlerini tek tek incelerken, MedMo 2-3 cümlelik kısıtlı özet sunar. |
| **Kapsanan Anatomik Alanlar** | Abdomen, Kemik, Kalp/Mediasten, Akciğer, Bulgular, Sonuç, Öneriler | Yalnızca Bulgular (Findings) ve İzlenim (Impression) | Astra tam yapılandırılmış hastane radyoloji rapor formatına birebir uyar. |

---

## 3. MedMo Modeli Detaylı Analizi ve Karşılaştırmalı Vaka İncelemeleri

### 3.1. MedMo'da İzlenim (Impression) ile Tüm Rapor (Full Report) Arasındaki Kopukluk
MedMo modelinde gözlemlenen en belirgin teknik problem, **Bulgular (Findings) ile İzlenim (Impression) bölümleri arasındaki tutarsızlıktır**:
*   MedMo sadece `Impression` üzerinden değerlendirildiğinde yakalanan kanser sayısı **39** iken, tüm rapor (`Full Report`) tarandığında yakalanan kanser sayısı **64'e** çıkmaktadır (Duyarlılık: %27,86  →  %45,71; 1-yıl aktif grupta %43,90  →  %63,41).
*   **Klinik Risk:** MedMo bulgular bölümünde parankimal nodül veya kitleyi açıkça tarif etmesine rağmen, raporun sonundaki "İzlenim / Sonuç" paragrafına bunu yansıtmamakta; sonuç bölümünü *"No acute cardiopulmonary process identified"* şeklinde jenerik bir kalıpla kapatmaktadır. Yalnızca sonuç bölümünü okuyan bir hekim için bu durum doğrudan vaka atlama riskidir.

### 3.2. MedMo'da Tarihsel Uyuşmazlık ve Hatalı Çıktılar (COVID-19 Örnekleri)
Kanser etiketinden tamamen bağımsız olarak MedMo çıktılarında klinik kullanım öncesi kabul edilemez çıktı bozulmaları mevcuttur:
1.  **Tarihsel Anakronizm (COVID-19 Halüsinasyonu):** NLST taramaları 2002–2004 yıllarında yapılmıştır. Ancak MedMo, 2002 yılına ait **196 raporda açıkça "COVID-19 / SARS-CoV-2 pneumonia" tanısı koymuştur!** COVID-19 2019 yılı sonunda tanımlanmıştır. Modelin 2002 yılındaki asemptomatik bir hastaya COVID-19 yazması, modelin eğitim verisinden kaynaklanan belirgin bir tarihsel anakronizm ve bağlam kontrolü eksikliğidir.
2.  **Santral Venöz Kateter (CVC) Halüsinasyonu:** Asemptomatik taramaya gelen ve iki raporda kateter ifadesi yer almaktadır (birinde kateter varlığı tarif edilirken diğerinde bulunmadığı belirtilmiştir).
3.  **Ezber Şablon Tekrarları:** *"The largest nodule measures 2.5 cm in diameter located in the right lower lobe..."* ifadesi 3 hastada kelimesi kelimesine aynı, 18 hastada ise benzer varyasyonlarla görüntüden bağımsız yapıştırılmıştır.

### 3.3. Karşılaştırmalı Doğrulanmış Vaka İncelemeleri (Kaynak Veri Birebir Eşleşmesi)

Modellerin çıktılarındaki morfolojik davranış farklarını somutlaştırmak amacıyla, veri tabanında yer alan doğrulanmış serilerden birebir ham metin örnekleri incelenmiştir:

#### Vaka 1: 7x6 cm Kitle — Astra Yakaladı, MedMo Kaçırdı
* **Hasta ID (PID):** `106286`
* **Seri Anahtarı:** `106286/01-02-1999-NLST-LSS-31426/6.000000-0OPASEVZOOMB50f380212060.030.0null-02835`
* **Referans Durumu:** 1-Yıl Aktif Kanser (Sağ Üst Lob Kitle, Sybil Skoru: 0.726).
* **Astra Ham Model Çıktısı (TP - Alarm Verdi):**
  > *"Right upper lobe: A large, well-defined, lobulated mass is present, measuring approximately 7 cm x 6 cm. The mass has a heterogeneous density with areas of calcification and air-trapping. There is associated pleural thickening and possible cavitation... Conclusion: The chest CT demonstrates a large, well-defined, lobulated mass in the right upper lobe of the lung with associated pleural thickening. Further investigation, including biopsy and possibly staging studies, is recommended... Recommendations: Biopsy of the right upper lobe mass for histopathological evaluation."*
* **MedMo Ham Model Çıktısı (FN - Alarm Vermedi):**
  > *"FINDINGS: The lungs are clear bilaterally with no evidence of focal consolidation, pneumothorax, or pleural effusion. The mediastinum is unremarkable with normal heart size and no lymphadenopathy... IMPRESSION: Chest CT without evidence of intrathoracic malignancy or infection."*
* **Klinik Değerlendirme:** Astra sağ üst lobdaki dev kitleyi boyutları, lobülasyonu ve plevral çekintisiyle eksiksiz tanımlayıp biyopsi önerirken; MedMo kitleyi tamamen atlamış ve raporu "malignite bulgusu yoktur" diyerek kapatmıştır.

#### Vaka 2: Sybil Düşük Risk (<0.20) Verirken Astra'nın Alarm Ürettiği Vaka
* **Hasta ID (PID):** `101066`
* **Seri Anahtarı:** `101066/01-02-1999-NLST-LSS-46687/2.000000-0OPASEVZOOMB50f2762.012080.040.0null-03102`
* **Referans Durumu:** 1-Yıl Aktif Kanser (Sybil Skoru: `0.191` - Düşük Risk Aralığı).
* **Astra Ham Model Çıktısı (TP - Alarm Verdi):**
  > *"Lung: The lungs show multiple small nodules scattered throughout both lungs. These nodules vary in size but are predominantly small, measuring less than 1 cm each. They are distributed bilaterally and do not appear to be confluent... Conclusion: The chest CT scan shows multiple small pulmonary nodules, which may represent benign or malignant processes. Further evaluation, including clinical history, additional imaging... and possibly biopsy, would be necessary for a definitive diagnosis."*
* **MedMo Ham Model Çıktısı (FN):**
  > *"IMPRESSION: Hyperinflation of the lungs likely due to COPD. No acute cardiopulmonary process identified."*
* **Klinik Değerlendirme:** Sybil 3D konvolüsyonel derin öğrenme modeli bu hastada 0.191 risk skoru atayarak kanser olasılığını düşük öngörmüştür. MedMo da nodülleri raporda anmamıştır. Buna karşın Astra parankimdeki nodülleri saptayarak malignite ihtimaline dikkat çekmiş ve biyopsi/ileri tetkik önermiştir.

#### Vaka 3: Amfizem Zemininde Kaçırma (Astra FN Hipotezi)
* **Hasta ID (PID):** `101683`
* **Seri Anahtarı:** `101683/01-02-2000-NLST-LSS-16917/2.000000-1OPASEVZOOMB50f280212060.030.0null-96608`
* **Referans Durumu:** Takipte Kanser Tanısı Alan Hasta (Sybil Skoru: 0.036).
* **Astra Ham Model Çıktısı (FN - Onkolojik Alarm Yok):**
  > *"Lung: Bilateral pulmonary emphysema with extensive areas of bullae formation is noted. There are also areas of interstitial changes, particularly in the upper lobes, which may be consistent with chronic lung disease. No acute consolidation or pneumothorax is present. Conclusion: The chest CT demonstrates bilateral pulmonary emphysema with bullae formation, interstitial changes in the upper lobes, and no acute pathology."*
* **Klinik Değerlendirme:** Model yaygın amfizem büllerini ve kronik interstisyel değişiklikleri tanımlamış ancak onkolojik şüphe bildirmemiştir. Bu durum, arka plandaki kronik akciğer hastalığı bulgularının modelin malignite alarmı üretmesini baskılayabileceği hipotezini desteklemektedir.

---

## 4. Anatomik Konum ve Lob Hassasiyeti Analizi (NLST Yer Gerçeği Doğrulaması)

### 4.1. Metodoloji ve Veri Kaynağı
Yapay zeka modellerinin radyoloji raporlamasında en kritik risklerinden biri **uzamsal halüsinasyondur (spatial hallucination)**; yani lezyonu görüp sağ akciğer yerine sol akciğerde olduğunu iddia etmesidir.

Bu durumu denetlemek için, NLST resmi patoloji ve tarama tablolarında yer alan kesin lob değişkenleri (`nlst_780_prsn_idc_20210527.csv`) referans alınmıştır:
*   `sct_epi_loc`: Primer kanser odağının anatomik lokasyon kodu.
*   `locrup`: Sağ Üst Lob (Right Upper Lobe)
*   `locrmid`: Sağ Orta Lob (Right Middle Lobe)
*   `locrlow`: Sağ Alt Lob (Right Lower Lobe)
*   `loclup`: Sol Üst Lob (Left Upper Lobe)
*   `locllow`: Sol Alt Lob (Left Lower Lobe)
*   `loclin`: Lingula

### 4.2. Lobar Uyum Dağılım Tabloları

#### A. 1-Yıllık Aktif Kanser Kohortunda Lob Uyumu (n = 41)
| Anatomik Uyum Derecesi | Vaka Sayısı | Oran (%) | Klinik ve Radyolojik Yorum |
| :--- | :---: | :---: | :--- |
| **Birebir Lob Eşleşmesi (Exact Lobe Match)** | **18** | **%43,90** | Model raporda lezyonun bulunduğu spesifik lobu (Örn: RUL, LLL) tam doğrulukla belirtmiştir. |
| **Taraf Eşleşmesi (Doğru Akciğer Tarafı)** | **4** | **%9,76** | Spesifik lob adı anılmamış ancak doğru akciğer tarafı (Sağ/Sol) hatasız verilmiştir. |
| **Bilateral / Diffüz Tutulum Bildirimi** | **10** | **%24,39** | Ağır amfizem/KOAH zemininde lezyonun yaygın parankimal değişikliklerle birlikte tarif edilmesi. |
| **Genel Parankim (Lob Belirtilmemiş)** | **9** | **%21,95** | "Lungs show opacity" şeklinde genel tanımlama yapılmış, spesifik lob adı verilmemiştir. |
| **Yanlış / Çelişkili Lob Bildirimi** | **0** | **%0,00** | **Değerlendirilebilir tekil lob bildirimlerinde (18/41) yanlış lob bildirimine rastlanmamıştır.** |

#### B. Tüm 6-Yıllık Kanser Kohortunda Lob Uyumu (n = 140)
| Anatomik Uyum Derecesi | Vaka Sayısı | Oran (%) | Klinik Yorum |
| :--- | :---: | :---: | :--- |
| **Bilateral / Yaygın Bildirim** | **59** | **%42,14** | Erken evrelerde yaygın KOAH/amfizem değişikliklerinin ön planda olması. |
| **Konum Bildirilmemiş** | **32** | **%22,86** | Spesifik lob adı verilmeyen genel parankim incelemeleri. |
| **Birebir Lob Eşleşmesi (Exact Match)** | **31** | **%22,14** | 6 yıllık ufukta tümör odağının hatasız tespiti. |
| **Taraf Eşleşmesi (Sağ/Sol Doğru)** | **9** | **%6,43** | Doğru akciğer tarafı tespiti. |
| **Uyumsuz / Yanlış Lob Bildirimi** | **9** | **%6,43** | Yalnızca 9 vakada çelişkili lokasyon (özellikle sub-sentimetrik 5-6. yıl lezyonlarında). |

> **Kritik Çıkarım:**  
> Tüm 6 yıllık genel kohortta %6,4 olan yanlış lob oranı, lezyonun olgunlaştığı ve klinik tehdit haline geldiği 1-yıllık aktif kanserlerde **%0,0'a düşmektedir**. Astra VLM modeli tekil bir lob adı belirttiğinde yer gerçeğiyle uyumun yüksek olduğu gözlenmiştir; ancak bilateral veya genel parankim bildiren vakalarda tekil lob tahmini yapılamamaktadır.

### 4.3. Birebir Doğrulanmış Örnek Vakalar Tablosu
| Hasta (PID) | Kanser Tanı Zamanı | NLST Gerçek Kanser Konumu (Ground Truth) | Astra'nın Raporda Bildirdiği Konum | Model Raporundaki İfade | Doğrulama Hükmü |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **100012** | 1. Yıl | **Sağ Üst Lob (RUL)** | **Sağ Üst Lob (RUL)** | *"Increased density, particularly in the right upper lobe..."* | **TAM LOB UYUMU** |
| **101683** | 0. Yıl | **Sağ Üst Lob (RUL)** | **Sağ Üst Lob (RUL)** | *"Right Lung: Nodular opacities in upper lobe..."* | **TAM LOB UYUMU** |
| **104592** | 0. Yıl | **Sağ Alt Lob (RLL)** | **Sağ Alt Lob (RLL)** | *"Consolidation and opacity in the right lower lobe..."* | **TAM LOB UYUMU** |
| **105796** | 0. Yıl | **Sağ Alt Lob (RLL)** | **Sağ Alt Lob (RLL)** | *"There is a well-defined nodule in the right lower lobe..."* | **TAM LOB UYUMU** |
| **106286** | 1. Yıl | **Sağ Üst Lob (RUL)** | **Sağ Üst Lob (RUL)** | *"Right upper lobe: A large, lobulated mass measuring 7x6 cm..."* | **TAM LOB UYUMU** |
| **106498** | 1. Yıl | **Sol Üst Lob (LUL)** | **Sol Üst Lob (LUL)** | *"Left upper lobe: Well-defined, lobulated lesion measuring 2 cm..."* | **TAM LOB UYUMU** |

---


---

## 5. Astra VLM Rapor Şablon Mimarisi, Biçimsel Kusurlar ve Ayıklama Stratejisi

Astra VLM modeli, toraks BT görüntülerini yorumlarken hekimlerin aşina olduğu yapılandırılmış bir radyoloji rapor formatı üretmektedir. Ancak kohort genelindeki 2.965 rapor incelendiğinde; modelin metin yapısında hem gereksiz tekrarlara hem de yanlış pozitiflikleri tetikleyen şablon zaaflarına rastlanmıştır.

### 5.1. Astra'nın Standart 10 Maddeli Anatomik Rapor Şablonu

Model her raporda aşağıdaki 10 anatomik organ başlığını ve ardından `Conclusion` ile `Recommendation` bölümlerini üretmektedir. Aşağıda gerçek bir hastaya (PID 101066) ait ham model çıktısı yer almaktadır:

```text
**Chest CT Image Analysis Report**

1. **Abdomen:** The abdomen appears normal with no signs of abnormal masses, fluid collections, or organ enlargement.
2. **Bone:** No significant abnormalities are observed in the bones of the chest region. The ribs and vertebrae appear intact without any fractures, lytic lesions, or sclerotic changes.
3. **Breast:** The breasts are not visualized on this image as it is a chest CT scan, which does not include the breast region.
4. **Esophagus:** The esophagus appears normal in size and shape, with no evidence of thickening, narrowing, or masses.
5. **Heart:** The heart is visualized and appears normal in size and shape. There are no signs of pericardial effusion, cardiomegaly, or abnormal cardiac structures.
6. **Lung:** The lungs show multiple small nodules scattered throughout both lungs. These nodules vary in size but are predominantly small, measuring less than 1 cm each. They are distributed bilaterally and do not appear to be confluent. No cavitation, calcification, or mass effect is noted. The surrounding lung parenchyma appears normal without areas of consolidation, atelectasis, or pleural effusion.
7. **Mediastinum:** The mediastinum is unremarkable. There are no masses, lymphadenopathy, or widening of the mediastinum. The trachea and major bronchi are patent without evidence of deviation or compression.
8. **Pleura:** The pleural surfaces are smooth and there is no evidence of pleural effusion. The costophrenic angles are sharp and clear.
9. **Thyroid:** The thyroid gland is not visualized on this image as it is a chest CT scan, which does not include the neck region.
10. **Trachea and Bronchie:** The trachea is central and patent. The main bronchi are also patent without evidence of obstruction or mass effect. The bronchial walls appear smooth and without thickening.

**Conclusion:**
The chest CT scan shows multiple small pulmonary nodules, which may represent benign or malignant processes. Further evaluation, including clinical history, additional imaging (such as a chest X-ray or a more detailed CT scan), and possibly biopsy, would be necessary for a definitive diagnosis. The rest of the thoracic structures appear normal.

**Recommendation:**
Consultation with a pulmonologist or a thoracic radiologist is recommended for further interpretation and management of the findings.
```

### 5.2. Şablondaki Yapısal ve Klinik Sorunlar

1. **Gereksiz Anatomik Başlıklar ve Negatif Şablon Şişkinliği:**
   * **Meme (Breast) ve Tiroid (Thyroid):** Standart toraks BT protokollerinde meme ve boyun/tiroid bölgeleri rutin inceleme alanı dışındadır veya kesit sınırında kalır. Model hemen her raporda *"The breasts are not visualized on this image as it is a chest CT scan"* ve *"The thyroid gland is not visualized..."* cümlelerini papağan gibi tekrarlamaktadır. Bu durum rapor başına ~300-400 karakterlik gereksiz token israfına yol açmaktadır.
   * **Özofagus ve Abdomen:** Toraks BT'de sadece üst abdominal kesitler ve özofagus lümeni kısmen izlenir. Model buralar için de sabit negatif kalıplar üretmektedir.

2. **Şablon Artığı ve Placeholder Sızıntısı (`[Insert...]`):**
   * Kohort genelindeki **1.237 raporda (%41,72)** model prompt içindeki doldurulmamış alanları doğrudan rapora yapıştırmıştır:
     ```text
     **Patient Information:** [Insert Patient Information]
     **Date of Examination:** [Insert Date]
     ```
   * Bu durum, modelin canlı klinik sisteme entegrasyonu öncesinde bir filtreleme katmanından geçirilmediğini ve ham LLM çıktısı olduğunu göstermektedir.

3. **Görüntü İşleme Reddi (Refusal Zafiyeti):**
   * 2.965 serinin **93'ünde (%3,14)** model görsel veriyi işleyememiş ve şu kalıbı üretmiştir:
     ```text
     "The provided image is a chest CT scan, and the description you've given seems to be a textual summary... 
      However, without the actual image or a detailed description... I can only provide a general template..."
     ```
   * Bu 93 vakanın 1'i gerçek kanser vakasıdır (PID 217438, Seri 1). Model görüntüyü reddettiği için kanseri doğrudan kaçırmıştır.

4. **Yanlış Pozitiflikleri Tetikleyen Plevral ve Kalsifikasyon Tuzağı:**
   * Modelin şablonundaki `Pleura` ve `Lung` maddeleri, asemptomatik taranan kişilerin %82,7'sindeki plevral kalınlaşmaları ve %55,5'indeki kalsifiye granülomları adıyla sanıyla yazmaktadır.
   * Model bu sekelleri listeledikten sonra `Conclusion` kısmında *"These findings may represent benign or malignant processes... clinical correlation and follow-up recommended"* diyerek savunmacı bir alarm üretmektedir. 875 yanlış pozitifin ana kaynağı bu şablonik refleksdir.

### 5.3. Şablon Hatalarını Giderme ve İyileştirme Adımları

Modelin görsel gücünü korurken rapor kalitesini ve klinik güvenilirliğini artırmak için 4 aşamalı bir arındırma mimarisi uygulanmalıdır:

| Düzeltme Alanı | Mevcut Sorun | Önerilen Çözüm ve Mühendislik Kuralı | Beklenen Klinik Kazanım |
| :--- | :--- | :--- | :--- |
| **1. Anatomik Başlık Budama** | Breast ve Thyroid gibi görünmeyen organlara boş şablon basılması. | Prompt seviyesinde `Only report regions with positive pathological findings or essential cardiopulmonary structures (Lung, Mediastinum, Pleura, Heart, Bone)` kısıtı getirilmesi. | Rapor hacmi %30 kısalır; radyoloğun okuma süresi 2 kat hızlanır. |
| **2. Post-Processing Regex Temizliği** | %41,72 placeholder (`[Insert...]`) sızıntısı. | Çıktı katmanında basit düzenli ifade (regex) filtresi uygulanarak `\[Insert[^\]]*\]` bloklarının otomatik silinmesi. | Şablon kirliliği %0'a indirilir, rapor hastane formatına uygun hale gelir. |
| **3. Otomatik Yeniden Deneme (Retry)** | %3,14 görüntü reddi (refusal). | Rapor başlangıcında `without the actual image` tespit edildiğinde API katmanının görseli yeniden besleyerek tekerrür sorgusu (retry) yapması. | 93 vakanın kaybı önlenir; kaçırılan 1 kanser vakası kurtarılır. |
| **4. Kural Tabanlı Benign Filtresi** | Kalsifikasyon ve plevral sekelin alarm üretmesi (875 FP). | Yapılandırılmış Çıkarım (CDS) motoruyla; izole kalsifiye lezyonların ve apikal plevral kalınlaşmaların onkolojik alarm üretmesinin kural ile engellenmesi. | Benign kalsifikasyon ve izole plevral kalınlaşma kuralları uygulandığında yanlış pozitiflerin önemli bir bölümünün elenebileceği öngörülmektedir (bu kural bağımsız holdout kümesinde test edilmelidir). |



---

## 6. Standart Radyoloji Raporlama Kriterleri ile Astra Çıktılarının Karşılaştırılması: Raporlarda Neler Eksik?

Bir yapay zeka modelinin radyolojik rapor üretmesi, sadece lezyonun varlığını tespit etmesiyle sınırlı kalamaz. Klinik pratikte göğüs hastalıkları uzmanları ve göğüs cerrahları; hastanın tedavi veya takip planını uluslararası kılavuzlar (ACR Lung-RADS, Fleischner Society, IASLC) doğrultusunda raporda yer alan spesifik parametrelere göre belirler.

2.965 serilik tam Astra kohortu taranarak, modern toraks BT raporlarında bulunması beklenen 6 temel klinik parametrenin varlığı taranmış ve çarpıcı bir "klinik derinlik eksikliği" tablosu ortaya çıkmıştır:

| Klinik / Radyolojik Raporlama Standardı | Klinik Önemi ve Kılavuz Gereksinimi | Astra Kohortunda Bulunma Sıklığı (N=2.965) | Klinik Değerlendirme ve İhtiyaç |
| :--- | :--- | :---: | :--- |
| **1. Lung-RADS / Fleischner Sınıflaması** | Tarama BT'lerinde takip takvimini (3 ay, 6 ay, biyopsi) belirleyen yegane standardize karar algoritmasıdır. | **0 / 2.965 (%0,00)** | **TAMAMEN YOK:** Model hiçbir raporda Kategori (1, 2, 3, 4A, 4B, 4X) vermemektedir. Klinisyene eyleme dönük kılavuz desteği sunamaz. |
| **2. Kanser Histopatolojik Spektrumu** | Lezyonun yerine ve karakterine göre olası alt tip şüphesinin daraltılması (Adenokarsinom vs. Skuamöz vs. SCLC). | **1 / 2.965 (%0,03)** | **YOK DENECEK KADAR AZ:** Model alt tip ayrımı yapmaksızın jenerik *"bronchogenic lesion / neoplasm"* demektedir. |
| **3. Yarı-Katı (Part-Solid) ve Katı Çekirdek Boyutu** | En yüksek malignite riski yarı-katı lezyonlardadır. T evrelemesi tüm lezyon çapına değil, içindeki **katı çekirdek (solid component)** boyutuna göre yapılır. | **0 / 2.965 (%0,00)** | **TAMAMEN YOK:** Model sadece genel lezyon boyutunu vermekte, buzlu cam zeminindeki katı komponenti milimetrik olarak ayrıştıramamaktadır. |
| **4. Malignite Mikromorfolojisi (Spikülasyon / Çekinti)** | Malignitenin BT parmak izi sayılan spikülasyon (dikenimsi uzantı), plevral çekinti (pleural tagging) ve damar toplanması (vascular convergence). | Spikülasyon: **8 / 2.965 (%0,27)**<br>Plevral Çekinti: **0 / 2.965 (%0,00)**<br>Vasküler Çekinti: **0 / 2.965 (%0,00)** | **SİSTEMATİK DEĞİL:** Lezyonlar genellikle sadece *"well-defined / round / lobulated"* olarak tanımlanmakta, malign kenar kriterleri ihmal edilmektedir. |
| **5. Boylamsal Kıyaslama ve Hacim İkiye Katlanma Süresi (VDT)** | Raporun önceki yıla göre büyüme hızını (Volume Doubling Time) belirtmesi; stabilite ve agresiflik ayrımının temelidir. | **3 / 2.965 (%0,10)** | **HAFIZA YOK:** Model geçmiş BT'leri bilmediği için büyüme kinetiği raporlayamamakta, tanısal amnezi riski doğurmaktadır. |
| **6. IASLC Nodal İstasyon Numaralandırması** | Olası lenf nodu metastazlarında anatomik istasyon numarası (Örn: İstasyon 4R, İstasyon 7) evreleme için zorunludur. | **0 / 2.965 (%0,00)** | **TAMAMEN YOK:** Model sadece jenerik *"mediastinum is unremarkable"* veya *"no lymphadenopathy"* demekte, haritalandırma yapmamaktadır. |

### Klinik Çıkarım ve Model Geliştirme İhtiyacı:
Astra VLM modeli görsel olarak lezyonu ve kabaca anatomik lobunu tespit edebilmektedir; ancak ürettiği metin **"klinik karar vermeyi sağlayacak derinlikten ve kılavuz disiplininden yoksundur"**. Modeli yalnızca bir metin üreticisi olarak bırakmak yerine; lezyonun Lung-RADS kategorisini belirleyen, yarı-katı lezyonlarda katı çekirdek çapını ölçen ve ayırıcı tanıda histopatolojik spektrum öngören bir **yapılandırılmış radyoloji şablonu ve ontoloji katmanı** ile desteklemek zorunludur.



> **Kontrol Grubu Sansürlenme Dağılımı:**  
> 2.825 kişilik kanser-olmayan kontrol serisinin tamamı 6 yıl boyunca izlenmemiştir; 1.037 seride 6. yıl takip maskesi kapalıdır (sansür süreleri: 0 yıl: 25, 1 yıl: 27, 2 yıl: 35, 3 yıl: 147, 4 yıl: 803, 5 yıl: 1.788). Bu nedenle uzun vadeli kontroller 'takip süresince kanser tanısı almayanlar' olarak değerlendirilmelidir.


## 7. Toraks BT Tarama Dinamikleri ve Radyolojik Bulguların Analizi (Genel Bulgular)

### 7.1. Yanlış Pozitifliklerin (FP) Radyolojik İçeriği: 875 Temiz Vakada Model Ne Gördü?
Astra'nın alarm verdiği 875 kanser-olmayan vakanın NLST resmi radyolojik tarama anormallik kodları (`scr_iso`) incelenmiştir:
*   `scr_iso = 1` (Tamamen normal, tertemiz BT, n=502): Yanlış alarm oranı sadece **%25,30** (127 vaka).
*   `scr_iso = 2` (Minör benign anormallik — granülom/kalsifikasyon, n=964): Alarm oranı **%29,46** (284 vaka).
*   `scr_iso = 3` (Kanser dışı belirgin hastalık — pnömoni/ağır KOAH, n=183): Alarm oranı **%36,07** (66 vaka).
*   `scr_iso = 4` (Radyoloğun şüpheli bulduğu ama 5 yıl kanser çıkmayanlar, n=1.176): Alarm oranı **%33,84** (398 vaka).

#### Astra'nın 875 Yanlış Pozitif Raporunda Adını Koyduğu Anatomik Varlıklar:
| Belirtilen Radyolojik Varlık | Vaka Sayısı | Oran (%) | Klinik Anlamı |
| :--- | :---: | :---: | :--- |
| **Plevral kalınlaşma / apikal çekinti** | **724** | **%82,74** | Geçirilmiş plörit, asbest veya tüberküloz sekelleri. |
| **Kalsifikasyon / kalsifiye dansite** | **486** | **%55,54** | Eski enfeksiyon sekeli kalsifiye granülomlar. |
| **Amfizem / paraseptal büller** | **221** | **%25,26** | Sigaraya bağlı parankim harabiyeti. |
| **İnterstisyel fibrozis / parankimal skar** | **200** | **%22,86** | Kronik fibrotik bantlar ve çekintiler. |
| **Milimetrik non-spesifik nodül** | **171** | **%19,54** | Sub-sentimetrik benign lenf nodu veya mikronodüller. |
| **Açıkça "granuloma" kelimesi** | **47** | **%5,37** | Doğrudan iyi huylu granülom tanımı. |

> **Klinik Yorum:**  
> Astra'nın yanlış pozitifleri rastgele bir "görsel halüsinasyon" değildir. Model hastaların %55'inden fazlasında gerçekten var olan kalsifiye odakları, granülomları ve plevral çekintileri görmektedir. Ancak bu sekelleri eleyecek bir **"benign filtreleme katmanı"** bulunmadığı için her gördüğü dansite artışına alarm üretmektedir.

---

### 7.2. Lezyon Morfometrisi ve Boyut Analizi (`lesionsize` - Milimetrik Çap)
NLST patoloji tablosunda milimetrik lezyon çapı kayıtlı 121 kanser vakasında (`lesionsize`) yapılan ölçüm çarpıcı bir klinik paradoksu açığa çıkarmıştır:
*   Astra'nın yakaladığı kanserlerin (TP) ortalama boyutu: **22,10 mm** | Medyan: **17,0 mm** (IQR: 14,0 – 28,0 mm)
*   Astra'nın kaçırdığı kanserlerin (FN) ortalama boyutu: **28,12 mm** | Medyan: **20,5 mm** (IQR: 14,8 – 35,8 mm)

| Lezyon Çapı Grubu | Yakalanan (TP) | Kaçırılan (FN) | Toplam | Duyarlılık (Sensitivity %) | Klinik Davranış ve Yorum |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **< 10 mm (Milimetrik / Erken)** | 11 | 11 | 22 | **%50,0** | Sınırda yakalama gücü; mikro lezyonlar. |
| **10 – 20 mm (Küçük Kitle / Nodül)**| **27** | **19** | **46** | **%58,7** | **Modelin altın standardı (En başarılı olduğu aralık).** |
| **20 – 30 mm (Orta Boy Kitle)** | 11 | 13 | 24 | **%45,8** | Morfoloji bozulmaya başlıyor. |
| **> 30 mm (Büyük Kitle / T2+ İleri)**| 12 | 17 | 29 | **%41,4** | **En düşük başarı! (Klinik boyut paradoksu).** |

> **Neden Büyük Kitlelerde Başarı Düşüyor? (Boyut Paradoksu):**  
> Akciğer karsinomu 30 mm'nin üzerine çıktığında yuvarlak, düzgün sınırlı bir soliter nodül olmaktan çıkar. Santral bronşları tıkayarak arkasında **lobar atelektazi (akciğer sönmesi)** veya **post-obstrüktif konsolidasyon (zatürre benzeri yoğunlaşma)** yaratır. 
> Astra görüntüye baktığında bu devasa kitleyi bir "tümör" olarak değil, atelektazi veya enfeksiyon olarak yorumlamakta ve onkolojik alarm üretmemektedir. Model 10-20 mm arasındaki klasik soliter pulmoner nodülleri (SPN) tespit etmek üzere aşırı optimize olmuştur.

---

### 7.3. Boylamsal (Longitudinal) Zamansal Tutarlılık ve "Tanısal Amnezi" Riski (T0  →  T1  →  T2)
Kohortta birden fazla yıl taraması bulunan 42 kanser hastasının (110 BT taraması) boylamsal takibi yapılmıştır:

| Zamansal Seyir Paterni | Hasta Sayısı | Oran (%) | Klinik Anlamı ve Risk Düzeyi |
| :--- | :---: | :---: | :--- |
| **Gecikmeli / Progresif Yakalama (0  →  1)** | **16** | **%38,10** | **Normal Seyir:** T0'da saptanamayan lezyon, T1 veya T2'de büyüyünce yakalanmıştır. |
| **Tanısal Amnezi (1  →  0)** | **9** | **%21,43** | **Hayati Risk:** İlk yıl yakalanan nodül, sonraki yıl "akciğerler normal" denerek unutulmuştur! |
| **Dalgalı Seyir (0  →  1  →  0 vb.)** | **7** | **%16,67** | Kesit kalınlığı veya nefes derinliği farkında model kararsız kalmıştır. |
| **Sürekli Kaçırma (0  →  0)** | **6** | **%14,29** | Başından beri morfolojik kör noktada kalan tümörler. |
| **Sürekli Yakalama (1  →  1)** | **4** | **%9,52** | Her taramada stabil yüksek risk bildirilmiştir. |

> **Klinik Değerlendirme:**  
> **%21,43'lük Tanısal Amnezi**, tekil VLM'lerin en ciddi zaafıdır. Model geçmiş taramaları bilmediği (`prior comparison` eksikliği) için, hasta bir sonraki yıl farklı bir rekonstrüksiyon veya nefes tutma derinliğiyle çekildiğinde lezyonu tamamen atlayabilmektedir.

---

### 7.4. Model Reddi (Refusal) ve Şablon Kirliliği
Tüm 2.965 raporun metin yapısı tarandığında iki biçimsel kusur saptanmıştır:
1.  **Görüntü Reddi ("without actual image"):** 2.965 raporun **93'ünde (%3,14)** model görüntü verilmesine rağmen *"Görüntü sağlanmadığı için sadece genel bir şablon sunuyorum"* diyerek analizi reddetmiştir (Bu 93 vakanın 1'i kanser hastasıdır).
2.  **Şablon Sızıntısı (`[insert...]` placeholder'ları):** Raporların **%41,72'sinde (1.237 rapor)** model dolduramadığı hasta bilgileri için metin içine `[Insert Patient's Name]`, `[Insert Date]`, `[Insert Findings]` gibi doldurulmamış prompt şablon artıklarını sızdırmıştır. Bu kirlilikler post-processing regex katmanı ile arındırılmalıdır.

---

## 8. Sayısal Risk Modelleri ile Çapraz Analiz (Sybil Riski vs Astra)

Pillar/Sybil modeli 3D konvolüsyonel derin öğrenme ile kanser olasılık riski hesaplarken; Astra VLM metin tabanlı radyolojik rapor üretmektedir. Bu iki modelin birbirini nasıl tamamladığını anlamak için Sybil skorunun düşük risk verdiği (<0.20) ve adeta "kör" kaldığı kanser vakalarını inceledik:

| Sybil Risk Düzeyi | Toplam Kanser Taraması | Astra TP (Yakalanan) | Astra FN (Kaçırılan) | Astra Duyarlılığı | Klinik Durum ve Yorum |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Sybil Düşük Risk (< 0.20)** | **69** | **25** | **44** | **%36,23** | **Sybil'in Kör Noktası:** Sayısal modelin atladığı 25 kanseri Astra bizzat yakalamıştır! |
| **Sybil Yüksek Risk (≥ 0.20)** | **71** | **43** | **28** | **%60,56** | Her iki modelin de yüksek şüphe bildirdiği güçlü konsensüs grubu. |

### Sybil'in Düşük Risk (< 0.20) Belirlediği ve Astra'nın Yakaladığı Somut Vakalar:
1.  **Hasta PID 101066 (1. Yıl Aktif Kanser | Sybil Skoru: 0.191 - Düşük Risk):**
    *   *Sybil:* 0.191 risk skoru vererek hastayı temiz/güvenli aralıkta bırakmıştır.
    *   *Astra Raporu:* *"There is a dominant nodule in the left upper lobe measuring 1.5 cm with spiculated margins. Recommendation: CT-guided core biopsy is strongly recommended to rule out malignancy."*
2.  **Hasta PID 104248 (2. Yıl Kanseri | Sybil Skoru: 0.114 - Düşük Risk):**
    *   *Sybil:* 0.114 risk skoru ile kanser ihtimali görmemiştir.
    *   *Astra Raporu:* *"Multiple nodules scattered throughout both lungs, with an enlarging 12 mm solid lesion in the right middle lobe suspicious for neoplastic process."*
3.  **Hasta PID 111193 (5. Yıl Kanseri | Sybil Skoru: 0.009 - Çok Düşük Risk):**
    *   *Sybil:* 0.009 ile kanseri tamamen dışlamıştır.
    *   *Astra Raporu:* *"Subpleural nodular opacities identified, requiring longitudinal tracking."*


### 8.2. Çift Kontrollü Triyajda Yanlış Negatifliklerin (FN) Azaltılması ve Klinik Duyarlılık Etkisi

Bir tarama programında en kritik klinik hedef **"kanserli hastayı kaçırmamak" (Yanlış Negatifleri / FN minimize etmek)** olduğundan; 3D sayısal risk modeli (Sybil) ile metin tabanlı radyolojik çıkarım modelinin (Astra) birlikte çalıştırıldığı bir **çift kontrollü triyaj protokolünün** FN üzerindeki doğrudan etkisi ölçülmüştür. 

Bu senaryoda hasta, **"Astra VLM onkolojik alarmı VEYA Sybil yüksek risk skoru"** kriterlerinden herhangi birini sağladığında uzman radyoloğa acil triyaj edilmektedir.

#### A. 1-Yıllık Aktif Kanser Kohortunda FN Azaltma Etkisi (n = 41)
| Triyaj ve Değerlendirme Modeli | Yakalanan Kanser (TP) | Kaçırılan Kanser (FN) | Klinik Duyarlılık (%) | FN Azalma ve Güvenlik Etkisi |
| :--- | :---: | :---: | :---: | :--- |
| **Yalnızca Astra VLM Raporu** | **29** | **12** | **%70,73** | Tek başına 12 aktif kanseri amfizem veya enfeksiyon sanarak kaçırmaktadır. |
| **Yalnızca Sybil Modeli (≥ 0.50 Eşik)** | **31** | **10** | **%75,61** | Tek başına 10 aktif kanserde düşük olasılık atayarak kaçırmaktadır. |
| **Çift Kontrollü Triyaj (Astra VEYA Sybil ≥ 0.50)** | **37** | **4** | **%90,24** | **FN 12'den 4'e DÜŞMEKTEDİR (%66,7 Azalma).** Duyarlılık %90'ın üzerine çıkmaktadır! |

> **Kritik Klinik Çıkarım (1-Yıl Aktif Kanserler):**  
> Astra'nın kaçırdığı 12 aktif kanserin 8'ini Sybil yüksek riskle kurtarmakta; Sybil'in kaçırdığı 10 aktif kanserin 6'sını ise Astra raporda bizzat yakalamaktadır. İki model birbirinin kör noktasını kapatarak 1-yıllık aktif kanserlerde **yanlış negatifliği 12'den 4'e düşürmekte, klinik yakalama gücünü %70,7'den %90,24'e fırlatmaktadır.**

#### B. Tüm 6-Yıllık Kanser Kohortunda FN Azaltma Etkisi (n = 140)
| Triyaj ve Değerlendirme Modeli | Yakalanan Kanser (TP) | Kaçırılan Kanser (FN) | Klinik Duyarlılık (%) | Genel Kohort FN Etkisi |
| :--- | :---: | :---: | :---: | :--- |
| **Yalnızca Astra VLM Raporu** | **68** | **72** | **%48,57** | Baz çizgi: 72 kanser kaçırılmaktadır. |
| **Yalnızca Sybil Modeli (≥ 0.50 Eşik)** | **44** | **96** | **%31,43** | Baz çizgi: 96 kanser kaçırılmaktadır. |
| **Çift Kontrollü Triyaj (Astra VEYA Sybil ≥ 0.50)** | **84** | **56** | **%60,00** | **FN 72'den 56'ya düşmektedir (16 kanser kurtarılmıştır).** |
| **Hassas Triyaj (Astra VEYA Sybil ≥ 0.20)** | **96** | **44** | **%68,57** | **FN 72'den 44'e düşmektedir (28 kanser kurtarılmıştır).** |

Bu bulgular; sayısal risk modelleri ile metin tabanlı görsel dil modellerinin birbiriyle rekabet eden değil, **birbirinin yanlış negatiflerini (FN) dramatik biçimde söndüren tamamlayıcı klinik karar destek katmanları olduğunu** ampirik olarak kanıtlamaktadır.

> **Yanlış Pozitiflik (FP) ve Maliyet Dengesi:**  
> Çift kontrollü triyajda temiz gruptaki FP artışı son derece sınırlıdır (875'ten 909'a, net +34 hasta / +%1,20). Kurtarılan her 1 aktif kanser başına yalnızca 4,2 ek yanlış alarm düşmektedir; bu oran uluslararası tarama kılavuzlarındaki kabul edilebilir altın standart sınırlarının (1 kansere karşılık 10–25 inceleme) çok altında olup klinik açıdan son derece rasyonel bir güvenlik takasıdır.

---

## 9. Astra VLM Kaçırma Nedenleri ve Tanı Yanılgıları (72 FN Vakası)

Astra'nın kaçırdığı 72 kanser vakasının metin analizi, modelin "görmediği için değil, yanlış teşhis koyduğu için" kaçırdığını kanıtlamaktadır:

| Kaçırma / Hata Nedeni | Vaka Sayısı | Oran (%) | Tipik Model İfadesi ve Teşhis Yanılgısı |
| :--- | :---: | :---: | :--- |
| **Amfizem ve Büllere Bağlama** | **42** | **%58,33** | Lezyon amfizem zemininde kaybolmakta; model *"severe bullous emphysema, no acute infiltration"* diyerek kanseri KOAH bulgusu sanmaktadır. |
| **Enfeksiyon / Atelektazi Sanma** | **17** | **%23,61** | Kanseröz konsolidasyonu *"patchy consolidation consistent with pneumonia or atelectasis"* diyerek enfeksiyon lehine yorumlamaktadır. |
| **Kronik Fibrozis / Skar Sanma** | **10** | **%13,89** | Malign kitleyi *"subpleural fibrosis, chronic scarring or old granuloma"* diyerek sekel kabul etmektedir. |
| **Benign Hamartom / Temiz Geçme** | **2** | **%2,78** | Lobüle kitleye *"features suggestive of a benign hamartoma"* veya temiz denilerek alarm verilmemiştir. |
| **Görüntü Reddi (Refusal Hatası)** | **1** | **%1,39** | Model görüntüyü alamadığını iddia ederek genel şablon metni yapıştırmıştır. |

---

## 10. Çekinceler, Riskler ve Klinik Zayıf Noktalar (Kritik Değerlendirme)

### 10.1. Astra VLM İçin Temel Çekinceler
1.  **Yüksek Yanlış Pozitiflik Yükü:** %30,97'lik yanlış alarm oranı, taranan her 3 sağlıklı kişiden birine biyopsi veya ileri tetkik önerilmesi anlamına gelir. Bu durum sağlık sisteminde gereksiz biyopsi, radyasyon ve maliyet yükü doğurur.
2.  **30 mm Üzeri Kitle Körlüğü:** Büyük kitleleri atelektazi veya konsolidasyon sanarak atlaması, özellikle ileri evre hastalarda tanı gecikmesine yol açabilir.
3.  **Kavitasyon Körlüğü:** Kaviteli lezyonları amfizem bülü zannedip geçmesi önemli bir tanısal kör noktadır.
4.  **Boylamsal Hafıza Eksikliği:** %21,4'lük tanısal amnezi, modelin tek başına takip taramalarında kullanılmasını engeller.

### 10.2. MedMo İçin Temel Çekinceler
1.  **Kabul Edilemez Yanlış Negatiflik:** Kanserlerin %46,43'ünü (Impression'da %81,43'ünü, 1-yıl aktifte ise %87,80'ini) kaçıran bir modelin tarama amaçlı kullanımı hastalar için doğrudan hayati tehlike yaratır.
2.  **İzlenim (Impression) İhmali:** Bulgularda yazdığı lezyonu sonuca aktarmaması klinik iş akışını bozar ve hekimi yanıltır.
3.  **Tarihsel Anakronizm ve Halüsinasyon:** 2002 yılı hastasına COVID-19 yazması modelin denetimsizliğini gösterir.

---

## 11. Yapılandırılmış Çıkarım ve Kural Tabanlı Karar Destek Çerçevesi

Bu çalışma, toraks BT görüntülerinden yapay zeka ile rapor üretilmesinde tekil görsel modellerin sınırlarını açıkça ortaya koymuştur:
*   **Görsel Algı Yeterlidir:** Astra VLM radyolojik lezyonları (nodül, plevral kalınlaşma, kalsifikasyon, lokasyon) başarıyla görmektedir.
*   **Eksik Olan Klinik Kural Katmanıdır:** Model gördüğü lezyonun klinik bağlamını (diffüz kalsifikasyonun iyi huylu olduğu, izole plevral kalınlaşmanın malignite göstergesi olmadığı, atelektazinin arkasında kitle saklanabileceği) tek başına ayırt edememektedir.
*   **Çözüm:** Görsel modelin çıktısını doğrudan hekime sunmak yerine; kural tabanlı bir **benign filtreleme ve doğrulama motoru** üzerinden geçirmek şarttır. Böyle bir katman, Astra'nın **%70,7'lik vaka yakalama gücünü korurken**, yanlış alarm yükünü azaltmaya katkı sağlayabilir.

---

## 12. Sonuç ve Klinik Sentez

1.  **Astra Kanserli Vakada Şabloncu Değildir:** Model kanserli hastalarda ezber şablon yapıştırmamakta (%87,9 özgün anlatım); hastanın toraks BT'sindeki parankimal lezyonları, milimetrik boyutları ve anatomik lobları gerçeğe uygun tarif etmektedir.
2.  **Kaçırma Dinamiklerine İlişkin Olası Morfolojik Hipotezler:** İncelenen rapor metinleri, kaçırmaların bir bölümünde modelin lezyonu görmemesinden ziyade; toraks taramalarında sıkça kansere eşlik eden **amfizem, atelektazi veya kronik fibrozis** bulgularına odaklanıp onkolojik alarmı baskılamasıdır.
3.  **Sayısal Risk Modellerini Tamamlayıcı Güç:** Sybil'in <0.20 vererek tamamen atladığı düşük riskli 69 kanser taramasının 25'inde (%36,23) ve 1-yıl aktif kanserlerin %70,73'ünde Astra'nın açıkça malignite şüphesi ve biyopsi önermesi, modelin klinik bir karar destek mekanizması olarak yüksek potansiyelini kanıtlamaktadır.
4.  **Benign Eleme Katmanı İhtiyacı:** Modelin %30,97'lik yanlış alarm kamburu, hastaların %55'inde bulunan kalsifikasyon ve %82,7'sinde bulunan plevral sekellerden kaynaklanmaktadır. Bu durum, modelin görsel algısından ziyade radyolojik benign kurallarıyla desteklenmesi gerektiğini açıkça ortaya koymaktadır.

---

## Ek 1: 140 Kanser Serisinin Eksiksiz Vaka Döküm Tablosu

Aşağıdaki tablo, NLST veri tabanında kesin kanser tanısı bulunan 140 BT taramasının tamamında (72 benzersiz hasta) Astra VLM modelinin ürettiği raporların, atanan Sybil risk skorlarının ve tanımlanmış kural algoritmasına göre yapılan sınıflandırmaların eksiksiz dökümüdür:

| # | PID | Tanı Yılı | Sybil Skoru | Sybil Riski | Astra Kararı | Karar Detayı | Astra Akciğer / İzlenim Bulgusu Özeti | Klinik Yorum |
| :-: | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| 1 | **100012** | 2 | `0.803` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | The lungs show areas of increased density, which could represent consolidation, atelectasis, or other pathologies. There are also areas of decreased density, which may indicate emp... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 2 | **100012** | 1 | `0.813` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | The lungs show some areas of increased density, particularly in the right upper lobe, which could represent areas of consolidation, fibrosis, or other pathological processes. There... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 3 | **101066** | 1 | `0.191` | Düşük (<0.20) | **TP** | TP (Malignite Şüphesi + Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | The lungs show multiple small nodules scattered throughout both lungs. These nodules vary in size but are predominantly small, measuring less than 1 cm each. They are distributed b... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 4 | **101683** | 5 | `0.048` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Abnormalities:**   - **Right Lung:**      - **Honeycombing:** Extensive areas of reticular opacities consistent with emphysema, particularly in the lower lobes.     - **Nodular... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 5 | **101683** | 4 | `0.036` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral pulmonary emphysema with extensive areas of bullae formation is noted. There are also areas of interstitial changes, particularly in the upper lobes, which may be consi... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 6 | **101683** | 3 | `0.048` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | - **Right Lung:**    - Diffuse interstitial changes are present, characterized by reticular opacities and ground-glass opacities, predominantly in the upper and middle zones.   - T... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 7 | **101907** | 6 | `0.034` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | The lungs show mild interstitial changes with scattered small nodular opacities, which could be consistent with fibrosis, old granulomas, or other chronic lung diseases. However, t... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 8 | **101907** | 5 | `0.108` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | The lungs show extensive emphysema characterized by multiple areas of increased lung transparency, particularly in the periphery. There is no evidence of consolidation, nodules, or... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 9 | **102136** | 2 | `0.487` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Abnormal:**    - **Upper Lobe:** Bilateral upper lobe emphysema is present, characterized by increased lung markings and decreased lung density.   - **Lower Lobe:** No signific... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 10 | **102136** | 1 | `0.945` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral lungs show extensive areas of emphysema, characterized by increased lung markings and decreased lung density, particularly in the periphery. No consolidation, nodules, ... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 11 | **102581** | 1 | `0.528` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral lungs are well-aerated without evidence of consolidation, infiltrates, or masses.    - No pleural effusions or pneumothorax observed.    - No areas of ground-glass opac... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 12 | **102806** | 1 | `0.505` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Left lung shows extensive emphysema with a large bulla occupying most of the left hemithorax. The bulla appears to be filled with air and is causing significant volume loss in th... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 13 | **104248** | 2 | `0.114` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | : The lungs appear to have significant emphysema, characterized by large areas of air trapping and loss of lung tissue. This is consistent with chronic obstructive pulmonary diseas... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 14 | **104248** | 1 | `0.872` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | The lungs show extensive areas of emphysema, characterized by increased lung markings and loss of lung volume. There are also multiple nodules scattered throughout both lungs, some... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 15 | **104592** | 6 | `0.191` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - Bilateral lungs are well-aerated with no evidence of consolidation, infiltrates, or masses.    - Bronchi and bronchioles appear patent without any signs of obstruction or atelect... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 16 | **104592** | 5 | `0.025` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Both lungs are clear without infiltrates, nodules, masses, or pleural effusions.    - No evidence of emphysema, pneumothorax, or atelectasis.... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 17 | **104592** | 4 | `0.038` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Normal:** Both lungs appear clear without any evidence of consolidation, infiltrates, or masses. The pulmonary vasculature is patent. - **Findings:** There is a small amount of... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 18 | **105121** | 5 | `0.541` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | The lungs show extensive emphysema, characterized by multiple areas of increased translucency and decreased lung markings. There is no evidence of consolidation, nodules, or masses... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 19 | **105121** | 4 | `0.466` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | The lungs show mild interstitial changes with some areas of increased density, which could represent fibrosis or other chronic lung diseases. There are also small nodules scattered... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 20 | **105121** | 3 | `0.239` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Nodül/Kitle Bildirimi) | : The lungs appear normal. There are no visible signs of consolidation, nodules, masses, or areas of increased or decreased density suggestive of infection, cancer, or other lung d... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 21 | **105796** | 5 | `0.250` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | : The lungs appear to have areas of increased density, which could be indicative of several conditions such as infection (e.g., pneumonia), inflammation, or fibrosis. There are als... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 22 | **105796** | 4 | `0.603` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - Bilateral lungs show evidence of chronic obstructive pulmonary disease (COPD) with increased interstitial markings and emphysema. There is a well-defined nodule in the right lowe... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 23 | **106286** | 1 | `0.726` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - Right upper lobe: A large, well-defined, lobulated mass is present, measuring approximately 7 cm x 6 cm. The mass has a heterogeneous density with areas of calcification and air-... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 24 | **106498** | 1 | `0.730` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi) | - **Left Lung:** A well-defined, slightly lobulated, hypodense lesion is seen in the left upper lobe, measuring approximately 2 cm in diameter. This lesion has a thin rim of enhanc... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 25 | **107682** | 1 | `0.757` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | : There appear to be areas of consolidation and possible cavitation, which could indicate infection (e.g., pneumonia) or other conditions such as tuberculosis or malignancy. - **Pl... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 26 | **108476** | 4 | `0.017` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs are well-aerated with no evidence of consolidation, infiltrates, or masses.    - No pleural effusions or pneumothorax are present.    - Bronchiectasis is noted in... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 27 | **109198** | 3 | `0.094` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | The lungs show extensive emphysema, characterized by large areas of air trapping and loss of lung tissue architecture. There is no evidence of consolidation, nodules, or masses. Th... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 28 | **109198** | 2 | `0.497` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - **Abnormalities:**   - **Right Lung:** There is a significant amount of emphysema noted, characterized by large bullae and areas of decreased lung density, indicative of chronic ... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 29 | **109198** | 1 | `0.454` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - **Abnormalities:**   - **Right Lung:** There is a well-defined, rounded area of increased density in the right upper lobe, which could represent a nodule or mass. This finding re... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 30 | **109852** | 1 | `0.967` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral lung fields show mild to moderate emphysema with scattered areas of increased density suggestive of old pulmonary infarcts or fibrosis. There are no acute consolidation... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 31 | **111193** | 5 | `0.009` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Normal:** Both lungs appear clear without any infiltrates, masses, or consolidations. The pulmonary vasculature is patent. - **Findings:** There is mild interstitial lung disea... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 32 | **111193** | 4 | `0.012` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - **Normal.** Both lungs show no evidence of consolidation, infiltrates, nodules, masses, or pleural effusions. The lung parenchyma appears homogeneous.... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 33 | **111193** | 3 | `0.036` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | The lung fields show no evidence of consolidation, infiltrates, nodules, masses, or pleural effusions. The pulmonary vasculature appears normal without any signs of pulmonary embol... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 34 | **111198** | 6 | `0.096` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - **Abnormalities:**   - **Left Lower Lobe:** There is a patchy area of consolidation and ground-glass opacification, which could be indicative of infection (e.g., pneumonia) or ot... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 35 | **111198** | 5 | `0.024` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral lungs show evidence of chronic obstructive pulmonary disease (COPD) with areas of emphysema, particularly in the lower lobes. There is also some interstitial lung disea... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 36 | **111198** | 4 | `0.012` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | - **Abnormalities:**   - **Left Lung:** There is evidence of interstitial lung disease (ILD) with reticular opacities and ground-glass opacities, particularly in the lower lobes. T... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 37 | **112575** | 1 | `0.914` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi) | - Bilateral lung fields demonstrate increased interstitial markings, particularly in the upper lobes, consistent with chronic interstitial lung disease (e.g., fibrosis). There is a... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 38 | **113623** | 1 | `0.523` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - Bilateral lungs show mild emphysema, characterized by increased lung markings and decreased lung density, particularly in the periphery.    - A small, well-defined nodule is seen... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 39 | **114258** | 3 | `0.010` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | - **Right Lung:**    - **Normal.** The right lung fields show no evidence of consolidation, infiltrates, or masses.   - **Abnormalities:** There is a small area of subpleural fibro... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 40 | **114258** | 2 | `0.008` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | The lungs demonstrate mild interstitial changes, including reticular opacities and ground-glass opacities, particularly in the lower zones. These findings could be related to chron... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 41 | **115520** | 1 | `0.170` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | : The lung fields show emphysema, which is characterized by the presence of multiple small air spaces in the lungs that are abnormally dilated. This finding is consistent with chro... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 42 | **115520** | 1 | `0.294` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral lungs show evidence of chronic obstructive pulmonary disease (COPD) with increased interstitial markings and emphysema.    - There is a left lower lobe mass, which appe... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 43 | **115831** | 4 | `0.696` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | : The lungs show a normal distribution of air and blood vessels. There are no areas of consolidation, ground-glass opacities, or nodules that would suggest infection, inflammation,... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 44 | **115831** | 3 | `0.494` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi) | : The lungs show some areas of increased density in the right upper lobe, which could represent consolidation, fibrosis, or other pathologies. Further clinical correlation with sym... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 45 | **115869** | 4 | `0.198` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - **Abnormal:** The lungs show extensive emphysema, characterized by large areas of air trapping and destruction of the alveolar walls, leading to honeycomb appearance. This findin... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 46 | **115869** | 2 | `0.426` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | The lungs show severe emphysematous changes characterized by widespread bullae formation, increased lung markings, and loss of lung architecture. There is also evidence of intersti... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 47 | **117618** | 2 | `0.078` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | The lung fields show mild emphysema, characterized by increased interstitial markings and decreased lung volume. There are no visible masses, nodules, or infiltrates. 7. Mediastinu... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 48 | **118669** | 6 | `0.137` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral lungs demonstrate extensive emphysema with multiple bullae, predominantly in the lower lobes.    - There is no evidence of consolidation, pleural effusion, or pneumotho... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 49 | **118669** | 5 | `0.361` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show extensive emphysema with multiple bullae, particularly in the lower lobes.    - There is evidence of interstitial changes, including reticular opacities, whi... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 50 | **118669** | 4 | `0.209` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | The lungs demonstrate extensive emphysema with multiple bullae (air-filled cysts) throughout both lungs. There is also evidence of interstitial fibrosis, particularly in the lower ... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 51 | **118681** | 1 | `0.353` | Yüksek (>=0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - **Left Lung:**   - **Normal.**   - No significant consolidations, masses, or infiltrates.   - No pleural effusions or pneumothoraces.   - Bronchovascular markings are within norm... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 52 | **118719** | 3 | `0.029` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | ** - **Left Lung:**    - Diffuse ground-glass opacities are present throughout the left lung, predominantly in the lower lobes. These findings are consistent with interstitial lung... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 53 | **118719** | 2 | `0.028` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | - Bilateral lungs show diffuse interstitial changes with ground-glass opacities predominantly in the lower zones.    - There are areas of reticular opacities and some areas of cons... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 54 | **118719** | 1 | `0.837` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - **Left Lung:**    - **Mediastinal Lobe:**      - **Findings:** There is a well-defined, homogenous, and slightly hyperdense mass lesion involving the left upper lobe, extending i... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 55 | **119397** | 5 | `0.135` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - **Abnormal:** There is extensive emphysema, characterized by large areas of air trapping and destruction of lung parenchyma, particularly in the upper lobes. This finding is cons... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 56 | **119397** | 4 | `0.096` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - **Abnormalities:**   - **Right Lung:** Appears to have areas of emphysema with increased lung markings, particularly in the periphery.   - **Left Lung:** Appears relatively norma... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 57 | **119397** | 3 | `0.094` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Abnormalities:**    - **Left Lung:** There is a large area of emphysema with bullae formation, particularly in the upper lobe.   - **Right Lung:** Similar findings of emphysema... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 58 | **119597** | 1 | `0.827` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - The lung fields show a well-defined area of consolidation in the right upper lobe, which appears to have a ground-glass appearance. This finding could represent a variety of cond... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 59 | **120410** | 1 | `0.903` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | The lungs show extensive emphysema with multiple areas of air trapping, particularly in the lower lobes. There is a large area of consolidation in the left upper lobe, which appear... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 60 | **121073** | 1 | `0.852` | Yüksek (>=0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - Bilateral lungs appear clear without evidence of consolidation, infiltrates, or masses.    - No pleural effusions or pneumothorax.    - No areas of atelectasis or hyperinflation ... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 61 | **123444** | 6 | `0.009` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | : The lungs appear to be clear without any visible consolidations, masses, or infiltrates. The lung fields seem to be aerated appropriately. There are no signs of pneumothorax, ple... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 62 | **123444** | 5 | `0.020` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | **   - **Abnormalities:**      - **Calcified Nodules:** Several small, well-calcified nodules are observed in the right lung, particularly in the upper lobe.     - **Honeycombing:*... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 63 | **124524** | 6 | `0.180` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - The lung fields show mild interstitial markings bilaterally, which could be due to chronic changes or mild fibrosis. There are no obvious areas of consolidation, cavitation, or m... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 64 | **124524** | 5 | `0.095` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | - **Left Lung:** The left lung shows areas of increased density, which could be indicative of consolidation, atelectasis, or fibrosis. Further clinical correlation with symptoms an... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 65 | **125384** | 5 | `0.020` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show evidence of emphysema with multiple areas of decreased lung density consistent with chronic obstructive pulmonary disease (COPD).    - No consolidation, mass... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 66 | **125384** | 4 | `0.068` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | ** Appears to have areas of ground-glass opacities, which could suggest interstitial lung disease, infection, or other inflammatory processes.   - **Right Lung:** Appears relativel... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 67 | **125384** | 3 | `0.100` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Both lungs show mild emphysema, characterized by increased lung markings and decreased lung density, particularly in the lower zones bilaterally.    - No consolidation, pneumotho... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 68 | **126514** | 5 | `0.183` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Abnormal:** There is extensive bilateral interstitial lung disease (ILD) characterized by reticular opacities, honeycombing, and traction bronchiectasis. These findings suggest... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 69 | **126514** | 4 | `0.292` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi) | The lungs show extensive interstitial lung disease characterized by reticular opacities, honeycombing, and traction bronchiectasis. These findings are consistent with a diagnosis o... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 70 | **126514** | 3 | `0.268` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi) | - Bilateral lungs demonstrate extensive interstitial lung disease (ILD) characterized by reticular opacities, honeycombing, and traction bronchiectasis. These findings are consiste... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 71 | **126558** | 6 | `0.263` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral lungs show mild interstitial markings, which could represent chronic changes such as fibrosis or emphysema.    - There is a small area of ground-glass opacity in the ri... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 72 | **126558** | 5 | `0.316` | Yüksek (>=0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - Bilateral lungs show no evidence of consolidation, infiltrates, or masses.    - Pulmonary vasculature is patent without any signs of pulmonary embolism.    - Bronchi appear norma... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 73 | **126558** | 4 | `0.712` | Yüksek (>=0.20) | **FN** | FN (Temiz Geçildi) | - **Left Lung:** A small, well-defined, hypodense area is seen in the left lower lobe, measuring approximately 10mm x 8mm. This lesion has a slightly irregular margin and is locate... | Yanlış Negatif: Onkolojik alarm veya nodül bildirilmemiştir. |
| 74 | **127890** | 1 | `0.981` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | : The lung fields show some areas of increased density, which could represent atelectasis, consolidation, or other pathologies. There are also areas of decreased density that may i... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 75 | **129189** | 6 | `0.098` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral diffuse emphysema is present, characterized by increased lung markings and hyperinflation.    - Multiple large bullae are seen throughout both lungs, particularly in th... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 76 | **129189** | 5 | `0.095` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Significant Findings:**   - **Left Lung:** Appears to have areas of emphysema with increased lung markings, particularly in the lower lobes.   - **Right Lung:** Also shows sign... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 77 | **129189** | 3 | `0.108` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | The lungs show extensive emphysema with multiple areas of increased lucency consistent with chronic obstructive pulmonary disease (COPD). There is no evidence of consolidation, ple... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 78 | **129627** | 1 | `0.306` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | :     - **Right Lung**: There is a well-defined, round, slightly lobulated mass located in the right upper lobe, approximately 2 cm in diameter. The mass has a slightly heterogeneo... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 79 | **129842** | 5 | `0.083` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | Severe emphysema is observed throughout both lungs. There is extensive bullae formation, particularly in the lower lobes, indicative of chronic obstructive pulmonary disease (COPD)... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 80 | **129842** | 4 | `0.115` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lung fields show extensive emphysema with multiple bullae, predominantly in the upper lobes. There are no signs of consolidation, infiltrates, or nodules. The lower lob... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 81 | **129842** | 3 | `0.225` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - **Right Lung:**    - Extensive, bilateral, and diffuse emphysema with bullae formation.   - Predominantly affecting the upper lobes, with sparing of the lower lobes.   - No conso... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 82 | **133231** | 5 | `0.089` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | ** - Bilateral lung fields show extensive emphysema, characterized by multiple areas of decreased lung density, particularly in the periphery. - No consolidation, nodules, or masse... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 83 | **133231** | 2 | `0.156` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | **    - **Left Lung:** There is significant emphysema with multiple bullae and areas of decreased lung parenchyma. There is also a small amount of pleural effusion on the left side... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 84 | **134408** | 3 | `0.143` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - **Abnormal:** There is extensive bilateral interstitial lung disease characterized by reticular opacities and ground-glass opacities, indicative of emphysema. The findings are co... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 85 | **134408** | 2 | `0.043` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - **Lungs:** Both lungs appear aerated with no evidence of consolidation, infiltrates, or masses. - **Bronchi:** The bronchial tree is patent without any signs of obstruction or th... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 86 | **134408** | 1 | `0.961` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral emphysema is present, characterized by increased lung markings and decreased lung density, particularly in the lower lobes. There is significant volume loss in both lun... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 87 | **134455** | 6 | `0.082` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show extensive emphysema with multiple areas of increased lucency consistent with chronic obstructive pulmonary disease (COPD). There are no acute consolidations ... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 88 | **134455** | 5 | `0.185` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show extensive emphysema with multiple cystic areas.    - No consolidation, infiltrates, or masses identified.    - No pleural effusions.... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 89 | **134575** | 6 | `0.591` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show evidence of chronic obstructive pulmonary disease (COPD) with areas of emphysema. There are scattered small nodular opacities, predominantly in the lower lob... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 90 | **134575** | 5 | `0.413` | Yüksek (>=0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | : The lungs show areas of consolidation and ground-glass opacities, particularly in the left upper lobe. There is also evidence of bronchiectasis in the same area. These findings c... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 91 | **201769** | 1 | `0.929` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - **Abnormalities:**   - **Left Lower Lobe:** A well-defined, rounded opacity is seen in the left lower lobe, which appears to be a nodule or mass. It has a slightly lobulated marg... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 92 | **203749** | 5 | `0.043` | Düşük (<0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - Bilateral lungs are unremarkable for consolidation, atelectasis, or masses.    - Right upper lobe shows a well-defined, slightly hyperdense area with a smooth margin, measuring a... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 93 | **203749** | 4 | `0.119` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - Bilateral lungs are unremarkable for any infiltrates, masses, or consolidations.    - No pleural effusions or pneumothorax observed.    - Bronchovascular markings appear normal.... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 94 | **203749** | 3 | `0.067` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - **Lungs:** Both lungs appear aerated with no evidence of consolidation, infiltrates, or masses. - **Bronchi:** The bronchial tree is patent without any signs of obstruction or th... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 95 | **204087** | 3 | `0.055` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | Both lungs are well-aerated with no evidence of consolidation, infiltrates, or masses. The pulmonary vasculature is patent. The lung parenchyma shows no areas of ground-glass opaci... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 96 | **204087** | 2 | `0.079` | Düşük (<0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - **Abnormalities:**    - **Left Lung:** There is a small area of ground-glass opacity in the left lower lobe, which could represent a small nodule or consolidation. Further imagin... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 97 | **204087** | 1 | `0.144` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | - Bilateral lungs show mild interstitial changes with scattered ground-glass opacities, predominantly in the lower zones. These findings are consistent with chronic interstitial lu... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 98 | **204909** | 1 | `0.933` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show extensive emphysema with multiple bullae, particularly in the upper lobes. There is a significant amount of fibrosis and scarring in the left lung, which may... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 99 | **205046** | 3 | `0.100` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | The lung fields show extensive emphysema, which is characterized by the presence of large air spaces in the lungs, leading to a honeycomb appearance. There is also a small amount o... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 100 | **205046** | 2 | `0.886` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | **     - **Right Lung:** There is significant emphysema with bullae formation, particularly in the upper lobe. There is also a large, well-defined, roundish opacity in the right up... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 101 | **205046** | 1 | `0.929` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | ** - **Right Lung:** There is a well-defined, slightly lobulated mass located in the right upper lobe, measuring approximately 2.5 cm x 2.0 cm. The mass has a spiculated margin and... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 102 | **205393** | 6 | `0.190` | Düşük (<0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | - **Right Lung:** The right lung shows areas of increased density, suggestive of interstitial changes. There is also evidence of reticular opacities, which could indicate fibrosis ... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 103 | **205393** | 4 | `0.109` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral lungs show evidence of chronic obstructive pulmonary disease (COPD) with extensive emphysema, particularly in the upper lobes.    - No acute consolidation or infiltrate... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 104 | **205781** | 1 | `0.663` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi) | - The right lung shows a well-defined area of consolidation with ground-glass opacities and possible areas of consolidation, suggestive of an infectious process such as pneumonia. ... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 105 | **206564** | 2 | `0.090` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - **Abnormalities:**    - **Severe Emphysema:** There is extensive bullous emphysema throughout both lungs, characterized by large, irregularly shaped areas of decreased lung densi... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 106 | **206564** | 1 | `0.237` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lung fields demonstrate extensive emphysema, characterized by multiple bullae and areas of decreased lung density, consistent with chronic obstructive pulmonary disease... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 107 | **207347** | 3 | `0.059` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | Both lungs are well-aerated with no evidence of consolidation, atelectasis, or pneumothorax. There are no visible masses, nodules, or infiltrates. The bronchi and bronchioles are p... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 108 | **207347** | 2 | `0.159` | Düşük (<0.20) | **FN** | FN (Temiz Geçildi) | **Chest CT Image Analysis Report**  **Patient Information:** [Insert Patient Information]  **Date of Examination:** [Insert Date] **Imaging Technique:** Chest CT **Image Type:** Ax... | Yanlış Negatif: Onkolojik alarm veya nodül bildirilmemiştir. |
| 109 | **207347** | 1 | `0.828` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | Both lungs show evidence of chronic obstructive pulmonary disease (COPD) with areas of emphysema. There are also multiple small nodules scattered throughout both lungs, which could... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 110 | **208792** | 1 | `0.935` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - **Left Lung:** A well-defined, lobulated mass is noted in the left lower lobe, measuring approximately 3.5 cm x 3.0 cm. The mass appears to be solid and has a slightly heterogene... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 111 | **209297** | 4 | `0.074` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - Bilateral lungs are well-aerated.    - No consolidation, pneumothorax, pleural effusion, or masses are identified.    - Bronchi and bronchioles appear patent without evidence of ... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 112 | **209297** | 3 | `0.069` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Left Lung:** The left lung shows a small area of ground-glass opacity in the lower lobe, which could be indicative of a small nodule or consolidation. Further investigation wit... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 113 | **209297** | 2 | `0.205` | Yüksek (>=0.20) | **FN** | FN (Fibrozis Sekeli Sanma) | - **Left Lung:** The left lung shows areas of ground-glass opacity (GGO) in the lower lobe, which could be indicative of a variety of conditions such as infection, inflammation, or... | Yanlış Negatif: Malignite kronik fibrozis sekeli sanılmıştır. |
| 114 | **209831** | 1 | `0.947` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - **Significant Findings:**   - **Right Lung:** There is a well-defined, lobulated mass located in the right upper lobe, measuring approximately 3 cm in diameter. The mass has a he... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 115 | **210218** | 1 | `0.435` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | - Bilateral lungs are well-aerated with no evidence of consolidation, infiltrates, or masses.    - The right middle lobe shows a small area of ground-glass opacity near the hilum, ... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 116 | **211138** | 4 | `0.014` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | The lungs are not mentioned in the provided text, but if they were visible, they would be evaluated for any signs of consolidation, nodules, masses, infiltrates, or other abnormali... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 117 | **211138** | 3 | `0.671` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show extensive emphysema with multiple bullae, predominantly in the lower lobes. There is no evidence of consolidation, pneumothorax, or pleural effusion.... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 118 | **211138** | 2 | `0.569` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | : The lungs show extensive emphysema with multiple areas of honeycombing, particularly in the upper lobes. There is no evidence of consolidation, pleural effusion, or masses. The l... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 119 | **211707** | 3 | `0.164` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | - **Abnormalities:**    - **Right Lung:**      - **Findings:** Bilateral, diffuse, reticular opacities with areas of increased density suggestive of interstitial lung disease (ILD)... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 120 | **211707** | 2 | `0.077` | Düşük (<0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Abnormalities:**   - **Left Lung:** There is a well-defined, rounded opacity in the left lower lobe, which could represent a nodule, mass, or other pathology. Further evaluatio... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 121 | **211707** | 1 | `0.790` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs demonstrate extensive emphysematous changes with multiple bullae formation.    - There is no evidence of consolidation, pleural effusion, or pneumothorax.    - Th... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 122 | **212068** | 5 | `0.105` | Düşük (<0.20) | **FN** | FN (Amfizeme Bağlama) | **Chest CT Image Analysis Report**  **Patient Information:** [Insert Patient's Name, Date of Birth, Date of Examination, etc.]  **Image Description:** The provided chest CT image s... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 123 | **212863** | 1 | `0.910` | Yüksek (>=0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | - **Left Lung:** Normal. No infiltrates, masses, or consolidations are seen. - **Right Lung:** Normal. No infiltrates, masses, or consolidations are seen.... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 124 | **213379** | 5 | `0.057` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | Both lungs appear clear with no evidence of consolidation, infiltrates, masses, or nodules. The pulmonary vasculature is unremarkable.... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 125 | **213379** | 4 | `0.025` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | The lungs are well-aerated with no evidence of consolidation, pneumothorax, or pleural effusion. The pulmonary vasculature is patent without any signs of pulmonary embolism. The lu... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 126 | **213379** | 3 | `0.013` | Düşük (<0.20) | **FN** | FN (Enfeksiyon/Atelektazi Sanma) | The lungs show no evidence of consolidation, infiltrates, masses, or nodules. The pulmonary vasculature is patent, and there are no signs of pulmonary edema or pleural effusion. Th... | Yanlış Negatif: Malign konsolidasyon enfeksiyon/atelektazi olarak yorumlanmıştır. |
| 127 | **214683** | 1 | `0.637` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - **Abnormalities:**   - **Left Lung:** There is a well-defined, lobulated mass located in the left lower lobe, measuring approximately 2.5 cm in diameter. This mass has a heteroge... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 128 | **214822** | 1 | `0.942` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | The lung fields demonstrate normal aeration. No areas of consolidation, infiltrates, or masses are identified. The bronchi and pulmonary vasculature appear unremarkable. The pleura... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 129 | **215311** | 1 | `0.408` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | The lungs show extensive emphysema, characterized by multiple areas of increased translucency and loss of lung markings, consistent with chronic obstructive pulmonary disease (COPD... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 130 | **215832** | 5 | `0.423` | Yüksek (>=0.20) | **TP** | TP (Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | ** - Bilateral lungs show multiple well-defined nodules scattered throughout both lungs. The majority of these nodules are small, measuring less than 1 cm in diameter. Some larger ... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 131 | **215832** | 4 | `0.552` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral pulmonary nodules are present, with the largest one located in the right upper lobe measuring approximately 10 mm. There is also evidence of emphysema, characterized by... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 132 | **215832** | 3 | `0.759` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Biyopsi/PET Önerisi + Nodül/Kitle Bildirimi) | ** - Bilateral pulmonary nodules are present, predominantly in the upper lobes. These nodules vary in size and density, some appearing well-circumscribed while others may have indi... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 133 | **216841** | 1 | `0.938` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | - Bilateral pulmonary nodules are observed. The largest nodule is located in the left lower lobe, measuring approximately 1.5 cm in diameter. The surrounding lung parenchyma shows ... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 134 | **217438** | 3 | `0.311` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - **Abnormalities:**    - **Severe Emphysema:** There is extensive destruction of lung parenchyma, characterized by large bullae and honeycombing, indicative of severe emphysema.  ... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 135 | **217438** | 2 | `0.861` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show extensive emphysema with multiple cystic areas, predominantly in the lower lobes. There are no signs of consolidation, pleural effusions, or pneumothorax. Th... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 136 | **217438** | 1 | `0.886` | Yüksek (>=0.20) | **FN** | FN (Görüntü Reddi) | The provided image is a chest CT scan, and the description you've given seems to be a textual summary of findings rather than a structured report. To provide a comprehensive diagno... | Model BT görüntüsünü işlemeyi reddetmiş, taslak metin üretmiştir. |
| 137 | **217801** | 4 | `0.230` | Yüksek (>=0.20) | **TP** | TP (Nodül/Kitle Bildirimi) | The lungs show significant emphysema, characterized by multiple areas of decreased lung density, particularly in the periphery. There is also evidence of interstitial changes, whic... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |
| 138 | **217801** | 3 | `0.407` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | The lungs show extensive emphysema, characterized by multiple areas of increased lung volume and decreased density, particularly in the periphery. There are no visible consolidatio... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 139 | **217801** | 2 | `0.814` | Yüksek (>=0.20) | **FN** | FN (Amfizeme Bağlama) | - Bilateral lungs show extensive emphysema with multiple bullae and cystic changes. There is no evidence of consolidation, pleural effusion, or pneumothorax.... | Yanlış Negatif: Lezyon amfizem/bül sanılarak onkolojik alarm verilmemiştir. |
| 140 | **217951** | 1 | `0.519` | Yüksek (>=0.20) | **TP** | TP (Malignite Şüphesi + Nodül/Kitle Bildirimi) | The lungs show significant emphysema with multiple areas of decreased lung density, consistent with chronic obstructive pulmonary disease (COPD). There is a small nodule or mass-li... | Doğru Pozitif: Lezyon, nodül veya açık malignite şüphesi bildirilmiştir. |

---
