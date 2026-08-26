# Standartlaştırma Planı — TASK-08 ve TASK-09

Veri hazırlığının kalan kısmının ayrıntılı planı. Kaynak görev listesindeki **T-01**'in ikinci yarısı.

**Sürüm 2** — bağımsız bir inceleme sonrası güncellendi. Değişenler bölüm 11'de özetli.

Belgede üç işaret var:

- **`[KARAR]`** — birlikte verilen karar
- **`[SEN BAK]`** — insan gözüyle bakılacak yer
- **`[ÖLÇ]`** — sayıyla doğrulanacak yer

---

## 1. Nerede duruyoruz

Elimizde çalışma düzeyinde bir tablo var: `data/processed/reports_study_level.parquet`, 25.692 satır. Her satır bir hastanın bir BT çekimi ve o çekimin raporu.

Ama rapor hâlâ **tek bir metin bloğu**. Bu hâliyle üzerinde ölçüm yapamayız: kelimenin geçmesi ile bulgunun var olması aynı şey değil — `tumoral` kelimesinin %100'ü olumsuz cümlelerde geçiyor.

**Amaç:** metin bloğunu, üzerinde güvenle sayı üretilebilen bir yapıya çevirmek.

---

## 2. Üç kavram — birbirine karıştırılmamalı

Bu ayrım planın en kritik noktası. Üçü **bağımsız** eksenlerdir:

| Kavram | Sorusu | Nerede belirlenir |
|---|---|---|
| **Negasyon** | Bulgu var mı, yok mu deniyor? | Faz 2 — dilbilimsel |
| **Şablon** | Cümle kalıp mı, serbest mi? | Faz 1 — istatistiksel |
| **Malignite ilgisi** | Bu bulgu malignite ile ilgili mi? | **Faz 3** — klinik sözlükler |

### Neden bu ayrım önemli

*"Pericardial effusion-thickening was not observed."* cümlesi:
- **Negatif** ✓ (bulgu yok deniyor)
- **Şablon** ✓ (9.787 raporda birebir aynı)
- **Malignite ile ilgili mi?** **Hayır.** Perikardiyal efüzyonun yokluğu malignite hakkında hiçbir şey söylemez.

Buna karşılık *"No enlarged lymph nodes were detected"* de negatif ve şablon, ama **malignite ile ilgili** — lenfadenopati bir malignite göstergesidir.

> **Yani "negatif bulgu" otomatik olarak "malignite aleyhine kanıt" değildir.** Bu iki şeyi eşitlemek, malignite kararını sistematik olarak çarpıtır.

### `[KARAR] D9` — Faz 1 malignite ilgisi atamaz

`malignancy_relevance` diye bir kolonu **Faz 1'de üretmeyeceğiz**. O bilgi Faz 3'teki gösterge sözlüklerine (TASK-15, TASK-16) bağlı; şimdi atamak tahmin yürütmek olur.

**Faz 1 yalnızca yapısal bilgi kaydeder:** cümle sınırları, ofsetler, şablon kimliği. Negasyon Faz 2'de, malignite ilgisi Faz 3'te eklenir.

---

## 3. Klinik çerçeve — Lung-RADS mı, Fleischner mı?

Bu ayrım kolayca gözden kaçıyor ama kohortumuz için belirleyici:

| Çerçeve | Kimin için tasarlandı |
|---|---|
| **Lung-RADS** | Akciğer kanseri **taraması** — tanımlı tarama popülasyonu, düşük doz BT |
| **Fleischner** | **İnsidental** nodüller — başka bir sebeple çekilmiş BT'de rastlanan nodül |

**CT-RATE bir tarama kohortu değil.** Genel hastane popülasyonu, yaş medyanı 46, raporların %50,5'inde klinik endikasyon bile yok. Yani **insidental bağlam**.

**Sonuç:**
- Boyut ve morfoloji eşiklerini **gösterge referansı** olarak kullanabiliriz
- **Lung-RADS kategorisi üretmeyeceğiz** — `Lung-RADS 4B` gibi bir etiket basmak bu kohortta yanlış olur
- Klinik bağlam (tarama mı, takip mi, semptomatik mi) bilinmediğinde **otomatik kategori üretmeyeceğiz**

## 3.1 Adlandırma disiplini

CT-RATE'te **patoloji veya malignite ground truth'u yoktur.** (`biopsy` ifadesi 47.149 raporun 16'sında geçiyor.) Rapordan çıkardığımız hiçbir sınıf, hastanın gerçek sonucu değildir.

Bu yüzden kolon adları karıştırılamayacak biçimde olacak:

| Yanlış | Doğru |
|---|---|
| `malignancy` | `report_derived_malignancy_label` |
| `diagnosis` | `report_derived_class` |

Ground truth adı yalnızca **Faz 7'de**, patoloji verisiyle üretilen etiketler için kullanılacak.

---

## 4. Veri modeli

**Üç tablo — Faz 1 için. Bu nihai veri modeli değildir.**

```
reports_study_level.parquet        1 satır = 1 çalışma        [VAR]
        │
        ├─ sentences.parquet       1 satır = 1 cümle          [YENİ]
        │
        └─ measurements.parquet    1 satır = 1 ölçü ifadesi   [YENİ]
```

Faz 2'de bulgu (entity) tablosu eklenecek ve **ölçüler bulgulara bağlanacak**. Şu an ölçü yalnızca cümleye bağlı; hangi lezyonun ölçüsü olduğu Faz 2'de belirlenecek. Model buna göre genişleyecek.

**Neden ayrı tablolar?** Bir cümlede sıfır, bir veya üç ölçü olabilir. Tek tabloda tutmanın iki yolu var, ikisi de kötü: satır çoğaltmak (cümle sayımları bozulur) ya da liste kolonu (filtreleme zorlaşır).

*(Etiket ve metadata'yı birleştirmiştik çünkü ilişki 1:1'di. Burada 1:n, o yüzden ayrı.)*

### `sentences.parquet`

| Kolon | Açıklama |
|---|---|
| `study_id` | Hangi çalışma |
| `section` | `findings` / `impression` |
| `sent_idx` | Bölüm içinde sıra |
| `text` | Cümle |
| `char_start`, `char_end` | Konum — bkz. D10 |
| `n_char` | Uzunluk |
| `template_id_exact` | Birebir aynı cümlelerin kimliği |
| `template_id_norm` | Sayılar maskelendikten sonraki kimlik |
| `n_patients_train` | Kalıbın kaç farklı **train** hastasında geçtiği (sürekli değer) |
| `is_stock_phrasing` | `n_patients_train >= 10` (D4) — **"standart kalıp", "önemsiz" değil** |
| `has_technical_caveat` | Cümle tetkik sınırlılığı bildiriyor mu (D12) |
| `pipeline_version` | Üreten kural setinin sürümü |

> Bu kolonlar **yapısal**dır, klinik değil. Negasyon ve normal/pozitif ayrımı **Faz 2'de** medspaCy ConText ile üretilir (D12); Faz 1 bu işi yapmaz.

### `measurements.parquet`

| Kolon | Açıklama |
|---|---|
| `study_id`, `section`, `sent_idx` | Hangi cümleden |
| `meas_idx` | Cümle içinde sıra |
| `raw_text` | Ham hâli (`5x3 mm`) — **her zaman korunur** |
| `unit_raw` | Ham birim (`mm` / `cm`) |
| `axes_mm` | Tüm eksenler, mm (`[5.0, 3.0]`) |
| `min_mm`, `max_mm` | Alt ve üst sınır — bkz. D6 |
| `is_range` | Aralık mı (`2-3 mm`) |
| `is_technical` | Teknik parametre mi — bkz. D3 |
| `char_start`, `char_end` | Konum |

### `[KARAR] D1` — Bu tablo yapısı, Faz 1 için onaylandı.

### `[KARAR] D10` — Ofsetlerin referansı

- Ofsetler **`report_text` alanına göredir** (`Findings_EN` + `\n\n` + `Impressions_EN`)
- **`report_text` bir daha değiştirilmez.** Değiştirilirse tüm ofsetler sessizce bozulur
- Her satır `pipeline_version` taşır; kural setini değiştirdiğimizde eski çıktı ayırt edilebilir
- Doğrulama testi: her satır için `text == report_text[char_start:char_end]`

**Neden gerekli:** Faz 4'te (TASK-21) "model bu bulguyu uydurdu mu?" sorusunu soracağız. Cevap ancak her bulguyu metindeki tam yerine geri bağlayabilirsek verilebilir. Şimdi bedava, sonra pahalı.

---

## 5. Adım 1 — Cümle bölütleme

### Findings

**Araç:** medspaCy `PyRuSH` — klinik metin için geliştirilmiş bölütleyici. Noktadan körü körüne bölmez (`1.5 mm` parçalanmaz).

### Impression farklı yazılmış

Rapor #7'nin Impression'ı şöyle:

> `"...consistent with viral pneumonia. Its prevalence has decreased partially.  Areas of subsegmental atelectasis...  Stable, calcific parenchymal metastases..."`

Maddeler çift boşlukla ayrılmış, bazıları noktayla bitmiyor — yani bir cümle dizisi değil, **madde listesi**.

### `[KARAR] D2` — Hibrit bölütleme, ölçerek seçim

Tek bir rapora bakıp "çift boşluktan böleriz" demek zayıf kanıt olurdu. Bunun yerine **üç aday kuralı korpusun tamamında karşılaştıracağız**:

| Aday | Kural |
|---|---|
| A | Yalnızca PyRuSH |
| B | Çift boşluk / satır sonu → sonra PyRuSH |
| C | B + madde işareti desenleri (`-`, `•`, numaralandırma) |

**Seçim ölçütü:** hangi kural, elle etiketlenmiş bir örneklemde doğru madde sınırlarını en iyi yakalıyor. Sayıyla seçeceğiz, sezgiyle değil.

### `[SEN BAK]` — Impression yapısını gör

```bash
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --report 7
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --report 25
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --report 100
```

`--- Impressions_EN ---` bölümüne bak.

**Aradığın şey:** Maddeler hep çift boşlukla mı ayrılmış? Bazılarında tek boşluk, satır sonu veya madde işareti (`-`) var mı? Farklı bir yapı görürsen söyle — aday kural listesine ekleriz.

### `[ÖLÇ]` Kabul ölçütleri *(önceden yazıldı)*

1. Ondalık içeren cümlelerde bölünme **yok** — `1.5 mm` tek parça
2. Ofset doğruluğu: `text == report_text[char_start:char_end]` **%100**
3. Toplam cümle sayısı 450–600 bin aralığında
4. Elle etiketli örneklemde madde sınırı doğruluğu **≥ %95**

---

## 6. Adım 2 — Şablon karakterizasyonu

### Tanım

Şablon = *sayılar maskelendikten sonra* en az **K farklı hastada** geçen cümle.

### `[KARAR] D11` — Sadece train verisinde hesapla

Şablon istatistiği **yalnızca train hastalarından** hesaplanır, sonra valid'e **uygulanır**.

**Neden:** Valid verisini de sayarsak test kümesinden ön işlemeye bilgi sızar. İnce ama gerçek bir sızıntı.

**Eşleşmeyen cümleler için kural:** Valid'deki bazı cümleler train kataloğunda karşılık bulamayacak. Bunlar **`is_stock_phrasing = False`** olarak işaretlenir — boş bırakılmaz.

**Hasta bazında sayım:** Bir hastanın üç çekimi varsa aynı cümle üç kez sayılıp şablon gibi görünür. Hasta üzerinden saymak bunu engeller.

### `[KARAR] D3` — Maskeleme kapsamı

**Maskelenecek:**

| Maskele | Maskeleme |
|---|---|
| `2 mm` → `<NUM> mm` | `right upper lobe` |
| `12x8 mm` → `<NUM>x<NUM> mm` | `left lower lobe` |

Anatomi ve taraf **klinik olarak anlamlı** — maskelersek "sağ üst lobda nodül" ile "sol alt lobda nodül" aynı şablon sayılır ve lokalizasyon kaybolur.

**Tarih ayrımı yapılmayacak.** Ölçtük: raporların **%99,6'sında tarih yok** (`gg.aa.yyyy` %0,16, 4 haneli yıl %0,42, ay adı 1 rapor). Binde 2'lik bir durum için tarih tespiti mantığı eklemek karşılıksız karmaşıklık. Zamansal ifadeler (`stabil`, `6 ay sonra`) önemli ama yerleri **TASK-12**, Faz 1 maskelemesi değil.

**Teknik sayı ayrımı ölçü tablosunda yapılacak** (`is_technical`), maskelemede değil. Bkz. Adım 3.

İki seviye birden tutulur (`template_id_exact`, `template_id_norm`) — karşılaştırılabilsin.

### `[KARAR] D4` — Eşik **K = 10** (verildi)

Train frekans dağılımı çizildi (`reports/figures/sablon_dagilimi.png`). **Beklenen kırılma noktası çıkmadı** — düzgün bir güç yasası eğrisi var. Tek keskin kırılma `n=1` ile `n≥2` arasında: benzersiz kalıpların %89,8'i tek hastada geçiyor.

Veri hazır eşik vermediği için seçim niteliksel yapıldı. Her seviyeden örnek cümlelere bakıldı:

| Hasta sayısı | Örnek | Değerlendirme |
|---|---|---|
| 2–4 | *"Nodular thickening in left adrenal gland corpus"* | Gerçek özgün bulgu, şablon değil |
| 10–20 | *"Calibration of other vascular structures is natural"* | **Kalıp ifade burada başlıyor** |
| 20+ | *"Pericardial, pleural effusion or thickness increase is not observed"* | Net şablon |

**K = 10** seçildi: 2.188 şablon ailesi, cümlelerin %61,8'i.

Ayrıca **`n_patients_train` sürekli değer olarak saklanıyor.** Bayrak bir kısayol; sonraki fazlar kendi eşiğini seçebilir. Kalıcı olan sayı.

**Ve kritik:** sık geçen her cümle şablon değildir. *"No mass, nodule-infiltration was detected in both lung parenchyma"* hem sık hem **gerçek klinik bilgi** taşıyor. Bu yüzden eşik seçildikten sonra **manuel örneklemle doğrulanacak**: eşiğin üstünde kalan cümlelerden rastgele seçilenler gerçekten kalıp mı?

### `[KARAR] D13` — `is_boilerplate` → `is_stock_phrasing`

Elle doğrulama sırasında ortaya çıktı: 1–2 kelimelik **69 şablon ailesinin neredeyse tamamı tek başına tanı**:

```
761 hasta | hepatosteatosis.       413 hasta | Cholelithiasis.
751 hasta | Hiatal hernia.         315 hasta | Cardiomegaly.
219 hasta | Thoracic spondylosis.  162 hasta | Left nephrolithiasis.
```

Bunlar `is_boilerplate=True` işaretli ama **bilgi yoğunluğu en yüksek cümleler**. Sebep sistematik: bir tanının adı ne kadar kısa ve standartsa, o kadar kesin "kalıp" çıkar — çünkü `Cholelithiasis` yazmanın tek bir yolu var.

Bu düzeltilecek bir hata değil; ölçtüğümüz şey gerçekten "bu ifade standart mı". Sorun **adlandırmada**: `boilerplate` kulağa "işe yaramaz" geliyor ve Faz 6'da biri bunu filtre olarak kullanırsa `Cholelithiasis`, `Cardiomegaly`, `Millimetric nodule` gibi gerçek bulguları siler.

**Karar:** kolon adı **`is_stock_phrasing`**. Anlamı: "bu ifade standart kalıptır" — bilgi değeri hakkında hiçbir iddia yok.

> **Bu bayrak asla filtreleme için kullanılmaz.** "Bu cümle bilgi taşıyor mu" sorusunun cevabı **Faz 2'den**, bulgu (entity) çıkarımından gelir; frekanstan değil.

### `[KARAR] D14` — Impression'ı olmayan çalışmalar

Ölçüldü: **811 çalışmanın Impression'ı yalnızca `"Not given."`**, 14 tanesi tamamen boş → **825 çalışmada radyolog kanaati yok** (önceki "14 boş" ölçümü eksikti).

Çalışma düzeyinde `impression_is_null` ile işaretlenir. **`report_text` değiştirilmez** — D10 gereği ofsetler ona bağlı. Faz 2'de "bu rapordan kanaat çıkarılamaz" demek için kullanılacak.

### `[KARAR] D12` — Dörtlü tip sınıflandırması Faz 2'ye taşındı

Planın ilk hâlinde şablonlar dört tipe ayrılacaktı: `negatif_ifade` / `normal_beyan` / `teknik` / `serbest`. Uygulamada iki sorun çıktı:

1. **Kural çakışması.** 120 teknik ailenin 62'si aynı zamanda negasyon içeriyordu. *"In the upper abdominal sections within the image, no solid mass was detected as far as can be observed"* hem teknik çekince hem negatif bulgu taşıyor; tek etiket vermek bilgi kaybı.
2. **D9 ihlali.** Dört tipin üçü negasyon analizi gerektiriyor. D9 negasyonun **Faz 2'de** yapılacağını söylüyordu; Faz 1'de basit regex ile yapmak hem karara aykırı hem de Faz 2'de medspaCy ConText ile üretilecek doğru analizin kötü bir kopyası olurdu.

**Karar:** dörtlü sınıflandırma Faz 2'ye taşındı. Faz 1'de kalan tek yapısal özellik:

| Kolon | İçerik |
|---|---|
| `has_technical_caveat` | Cümle tetkik sınırlılığı bildiriyor mu — *"as far as can be seen"*, *"could not be evaluated"*, *"unenhanced"* |

Bu **bağımsız bir boolean**, tip değil. Bir cümle hem klinik içerik hem teknik çekince taşıyabilir; çakışma böylece ortadan kalkar.

Faz 2'de ConText ile negasyon üretildiğinde `is_stock_phrasing` + `negated` birleştirilerek "rutin negatif" ile "kasıtlı negatif" ayrımı zaten elde edilecek. Üç eksen bağımsız kalır.

### `[SEN BAK]` — Şablon bayrağını birlikte doğrulayacağız

D4 manuel doğrulama istiyordu. `reports/sablon_dogrulama.csv` içinde en sık **350 şablon** var (train cümlelerinin %51,1'i). Bunların gerçekten kalıp olup olmadığını birlikte geçeceğiz. **Radyoloji metnini gerçekten tanıyacağın adım burası.**

Şimdiden fikir edinmek için:

```bash
.venv/Scripts/python.exe scripts/02_inspect_corpus.py
```

En sondaki **"SABLON CUMLE SORUNU"** başlığına bak.

**Aradığın şey:** Bu cümlelerin kaçı "bir şey yok" diyor, kaçı "normal" diyor? Ve şunu da düşün: hangileri malignite ile *ilgili* bir şey söylüyor, hangileri tamamen ilgisiz? (Bu ayrımı Faz 3'te kullanacağız.)

### `[ÖLÇ]` Kabul ölçütleri *(önceden yazıldı)*

1. ~~En sık 200 şablonun kapsama oranı ≥ %50~~ → **ölçüldü: %46,2, ölçüt tutmadı.** Kurala uyularak sayı **350**'ye çıkarıldı → %51,1 ✓
2. Manuel doğrulama örnekleminde **yanlış şablon oranı ≤ %5**
3. Valid'de eşleşmeyen cümle oranı raporlanır

---

## 7. Adım 3 — Ölçü normalizasyonu

### Desenler tahmin değil, ölçüm

25.692 raporda gerçek dağılım:

| Biçim | Kapsam | Örnek |
|---|---|---|
| `N mm` / `N cm` | %51,1 | `12 mm` |
| **`millimetric` (sayısız)** | **%39,9** | *"A few **millimetric** nodules"* |
| `NxN` | %12,5 | `5x3 mm` |
| Ondalık nokta | %10,3 | `1.5 mm` |
| `7mm` (bitişik) | %1,1 | *"measuring **7mm** on the short axis"* |
| Aralık `2-3 mm` | %0,5 | *"calcific **2-3 mm** nodules"* |
| `NxNxN` | %0,3 | `26x18x40 mm` |
| Ondalık virgül | %0 | yok |

Birim: **mm baskın** (5.193 / 823). Değer aralığı 0,8–181 mm.

### `[KARAR] D5` — `millimetric` ayrı niteliksel kategori

Raporların **%40'ında boyut sayısız** veriliyor. Fleischner/boyut eşikleri sayı ister; sayısı olmayan bulguyu eşikle karşılaştıramayız.

| Seçenek | Sonuç |
|---|---|
| Yok say | %40'ta boyut bilgisi kaybolur |
| Sayı ata (örn. 5 mm) | Uydurma veri |
| **Ayrı kategori: `size_qualitative = "millimetric"`** | **Bilgi korunur, uydurma yok** |

Milimetrik olması zaten "küçük lezyon" bilgisi taşır; Faz 6'da kendi başına kullanılabilir.

### `[KARAR] D6` — Alt ve üst sınırı birlikte tut

`2-3 mm` için `min_mm = 2.0`, `max_mm = 3.0`, `is_range = True`.

Önceki taslakta "üst sınırı al" demiştim. Yanlıştı: bu bir **karar kuralı** ve karar kuralları Faz 6'ya ait. **Veri hazırlığı korur, karar vermez.** Bir kolon maliyetine bilgi kaybı sıfırlanıyor.

`raw_text` her zaman korunur — hiçbir dönüşüm geri dönülemez olmayacak.

### `[KARAR] D7` — cm → mm

Tek birimde tutulur (`2 cm` → `20.0`). Ham birim `unit_raw` içinde saklanır.

### `[KARAR] D3-b` — Teknik ölçüleri ayır

Findings/Impression içinde teknik parametre geçebiliyor. Ölçtük — **gerçek ama küçük**:

| Desen | Kapsam |
|---|---|
| `N mm thick/slice/section` | 153 rapor (%0,60) |
| `sections ... N mm` | 291 rapor (%1,13) |
| reconstruction / collimation / kernel | **0** |

Bunlar `is_technical = True` ile işaretlenip lezyon ölçülerinden ayrılacak (silinmeyecek).

> **Uygulama tuzağı:** `thickness` kelimesi 7.822 raporda (%30) geçiyor ve neredeyse tamamı **klinik**: *"pericardial effusion or **thickness** increase"*, *"wall **thickness** increase in the esophagus"*, *"septal **thickness** increase"*.
>
> "thickness geçiyorsa teknik" kuralı yazarsak raporların %30'unda gerçek bulguyu ıskalarız. Yalnızca dar desenlerle işaretlenecek (`N mm thick sections` gibi), kelime bazlı değil.

### `[SEN BAK]` — Ölçüleri gör

```bash
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --search millimetric
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --search "in diameter"
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --search "thick sections"
```

**Aradığın şey:** `millimetric` geçen cümlelerde gerçekten hiç sayı yok mu? Bazılarında hem "millimetric" hem sayı varsa söyle — kural değişir.

### `[ÖLÇ]` Kabul ölçütleri *(önceden yazıldı)*

1. Zor vaka takımının tamamı doğru (bkz. bölüm 8)
2. Rastgele 100 eşleşmede hata **≤ %2**
3. Yakalama oranı: `mm|cm` geçen cümlelerin **≥ %95**'inde ölçü çıkarılmış
4. 200 mm üstü her değer tek tek incelenmiş
5. `is_technical` işaretlilerin tamamı elle doğrulanmış (az sayıda: ~450 rapor)

---

## 8. Doğrulama — rastgele örnek yetmez

Rastgele 100 örnek, nadir ama zararlı vakaları kaçırır. Bu yüzden **iki katmanlı** doğrulama:

**Katman 1 — Rastgele örneklem.** Genel doğruluk için.

**Katman 2 — Zor vaka takımı.** Elle seçilmiş, bilinçli olarak zor örnekler. Sabit bir dosyada tutulur ve her değişiklikten sonra çalıştırılır:

| Zorluk | Örnek |
|---|---|
| Ondalık | `1.5 mm thick sections` |
| Aralık | `calcific 2-3 mm diameter nodules` |
| Çoklu ölçü | `34mm and 31mm respectively` |
| Üç eksen | `26x18x40 mm` |
| Bitişik birim | `measuring 7mm on the short axis` |
| Sayısız boyut | `A few millimetric nonspecific nodules` |
| Negasyon | `No mass lesion ... was detected` |
| Belirsizlik | `hypodense lesion ... is stable (cyst?)` |
| Teknik/klinik ayrımı | `1.5 mm thick sections` vs `wall thickness increase` |
| Bozuk noktalama | `...hilar regions.3.2021. There is an area...` |

**Kabul ölçütleri sonuç görülmeden yazılır.** Sonucu görüp eşiği ayarlamak kendini kandırmaktır.

---

## 9. Faz 2'ye taşınanlar

### `[KARAR] D8` — Findings→Impression önem sinyali Faz 2'ye taşındı

Impression medyan uzunluğu Findings'in %15'i; radyolog önemli bulduğunu Impression'a taşıyor. Bu değerli bir sinyal — **ama Faz 1'de yapılacak iş değil.**

Kelime düzeyinde eşleştirme zayıf kalır (*"hypodense nodules in the right lobe of the thyroid gland"* ↔ *"nodules in the right thyroid lobe"*). Faz 2'de bulgular yapılandırılmış olacak ve eşleştirme **kavram düzeyinde** yapılabilecek.

Zorunlu standartlaştırma adımı değil, denenebilecek **yardımcı özellik**. Faz 1'in kapsamı bu kadar küçüldü.

---

## 10. Karar listesi

| # | Karar | Durum |
|---|---|---|
| D1 | Üç tablo — Faz 1 için, nihai değil | Onaylandı |
| D2 | Hibrit bölütleme, üç aday kural, ölçerek seçim | Onaylandı |
| D3 | Sayıları maskele · anatomiyi koru · **tarih ayrımı yok** | Onaylandı |
| D3-b | Teknik ölçüler `is_technical` ile ayrılır (dar desenle) | **Uygulandı** · gerçek etki 6 kayıt |
| D4 | Eşik **K = 10** · `n_patients_train` sürekli saklanır | **Verildi** |
| D5 | `millimetric` → ayrı niteliksel kategori | **Uygulandı** · 16.726 kayıt |
| D6 | Alt ve üst sınır birlikte | **Uygulandı** · 166 aralık |
| D7 | cm → mm, ham birim korunur | **Uygulandı** |
| D8 | Önem sinyali → Faz 2 | Onaylandı |
| D9 | Negasyon / şablon / malignite ilgisi ayrı; ilgi Faz 3'te | Onaylandı |
| D10 | Ofsetler `report_text`'e göre; kaynak değişmez; sürüm kaydedilir | Onaylandı |
| D11 | Şablonlar train'de hesaplanır; eşleşmeyen = şablon değil | Onaylandı |
| D12 | Dörtlü tip sınıflandırması Faz 2'ye taşındı; Faz 1'de `has_technical_caveat` kalır | **Verildi** |
| D13 | Kolon adı `is_boilerplate` → **`is_stock_phrasing`**; asla filtreleme için kullanılmaz | **Verildi** |
| D14 | Impression'ı olmayan 825 çalışma `impression_is_null` ile işaretlenir; `report_text` değişmez | **Verildi** |

---

## 11. Sürüm 1'den farklar

Bağımsız inceleme sonrası düzeltilenler:

1. **`negatif_bulgu → malignite aleyhine kanıt` eşitlemesi kaldırıldı** — üç kavram ayrıldı (D9)
2. **Lung-RADS/Fleischner ayrımı eklendi** — kohort insidental, tarama değil
3. **Aralıklarda "üst sınırı al" → alt+üst birlikte** (D6)
4. **Teknik ölçü ayrımı eklendi** (D3-b), `thickness` tuzağıyla birlikte
5. **Ofset referansı ve `pipeline_version` tanımlandı** (D10)
6. **Şablonlar train-only** — sızıntı düzeltmesi (D11)
7. **Impression bölütleme: varsayım → üç aday kuralın ölçülmesi** (D2)
8. **Önem sinyali Faz 2'ye taşındı** (D8)
9. **Zor vaka takımı ve önceden yazılmış kabul ölçütleri eklendi**
10. **Adlandırma disiplini eklendi** (`report_derived_*`)
11. **Tarih ayrımı önerisi reddedildi** — %99,6'sında tarih yok

---

## 12. Kendi gözünle bakma rehberi

Komutlar proje klasöründe (`c:\Users\PC_7820\Desktop\radyo-vlm`) çalıştırılır.

```bash
# Korpusun genel tablosu
.venv/Scripts/python.exe scripts/02_inspect_corpus.py

# Tek rapor
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --report 7

# Kelime arama
.venv/Scripts/python.exe scripts/02_inspect_corpus.py --search spicul

# Doğrulama testleri
.venv/Scripts/python.exe -m pytest tests/ -v
```

### Jupyter

Not defterleri `notebooks/` altında tutulmalı (`data/processed/` veri için, git'e girmiyor).

```bash
.venv/Scripts/python.exe -m jupyter lab
```

```python
import pandas as pd
d = pd.read_parquet(r"C:\Users\PC_7820\Desktop\radyo-vlm\data\processed\reports_study_level.parquet")
print(d.iloc[7]["report_text"])
d[d.report_text.str.contains("spicul", case=False)][["study_id", "report_text"]]
```

### Ham dosyalar — salt okunur

`data/raw/ct_rate/` içindekiler orijinal CT-RATE verisidir, değiştirilmez:

| Dosya | İçerik |
|---|---|
| `train_reports.csv` | 47.149 hacim için rapor metni |
| `README.md` | Resmi dokümantasyon — isimlendirme kuralı 183. satır |
| `data_correction_note.md` | Veri düzeltme talimatları |
| `no_chest_train.txt` | Göğüs BT'si olmayan hacimlerin listesi |
