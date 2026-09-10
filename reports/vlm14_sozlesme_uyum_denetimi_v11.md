# Astra Adaptörü 1.1 Sözleşme Yeniden Denetimi

**Tarih:** 2026-09-08  
**Kapsam:** `astra-adaptor-1.1`, Adım 5 öncesi R1-R5 kapısı  
**İncelenen veri:** yalnız `train`  
**Hüküm:** **KALDI. `dev` açılmamalıdır.**

## 1. Kapsam ve yöntem

Yeniden denetim yalnız `train` satırlarıyla yürütüldü. Cümle tablosu Parquet
filtresiyle `split == "train"` ve ölçüm evreni için
`included_in_evaluation == true` koşulları uygulanarak okundu. Train varlık ve
ilişki artefaktları kullanıldı. `dev` ve `held_out` satırları açılmadı;
`Kanser_Etiketi_y`, `Censor_Time` ve `Pillar_Ensemble_Skoru` kolonları okunmadı.

İş emrinin dar kapsamı gereği K2, K3 ve K4 baştan tekrarlanmadı. R3 için
anatomi filtresinin etkilediği kapsam içi cümlelerin tamamı incelendi. R4 ve R5
sayıları mevcut koddan bellekte yeniden üretildi; çıktı artefaktlarının üzerine
yazılmadı.

## 2. R1: Zenginleştirme kapısı

| Kontrol | Bulgular | Sonuç |
|---|---|---|
| `_sema_girdisi` zorunlu kolonları | `sablon_cumle` veya `supheli_niteleyici` kolonu yoksa `ValueError` veriyor | Geçti |
| Gerçek üretim sırası | `scripts/63_vlm14_tam_kosum.py`, şablon kolonunu ve ilişki tabanlı şüpheli niteleyiciyi `seri_ozeti` öncesinde üretiyor | Geçti |
| Şemadaki eski `else: sablon_cumle = False` dalı | `sema.kalip_nodul_kolonlarini_ekle` yalnız CT-RATE betiklerinden çağrılıyor; Astra akışı bu yardımcıdan geçmiyor | Astra için ulaşılamıyor |
| Girdi filtresi | `normalized_concept`, `assertion`, `temporality` veya `assertion_rule` eksikse `ValueError` veriyor | Geçti |
| İlişki girdisinin zorunluluğu | `supheli_niteleyici_ekle`, `boyut_ekle` ve `ekstratorasik_varliklar`, `iliskiler=None` değerini boş ilişki gibi kabul ediyor | **Kaldı, (b) tipi kusur** |

Zorunlu parametreyi yalnız imzada varsayılansız bırakmak yeterli değildir.
Çağıran taraf `None` verdiğinde şüpheli niteleyicilerin tamamı `False`, anatomik
eleme kümesi boş ve bütün ölçüler eksik kabul edilebilmektedir. Bu yol hata
vermeden sonuç üretir ve ilişki tabanlı üç girdiyi aynı anda susturur. Mevcut
üretim betiği gerçek bir ilişki tablosu verdiği için bugünkü train çıktısı bu
kusurdan etkilenmemiştir; yine de sözleşme kapısı tam olarak kapanmamıştır.

Mevcut train zenginleştirmesinde iki zorunlu kolonda null yoktur ve
`supheli_niteleyici=True` olan 574 varlık vardır.

## 3. R2: Teknik ölçü tanımının tekilliği

VLM-14 üretim yolundaki üç betik (`scripts/61`, `scripts/62`, `scripts/63`)
teknik ölçü kararını yalnız `astra.olcu_teknik_mi` ile veriyor.
`scripts/07_extract_measurements.py` içindeki eski `TEKNIK` deseni dosyanın
kendi ölçüm görevi için duruyor; VLM-14 betikleri bu modülden yalnız `OLCU`
desenini kullanıyor ve `teknik_mi` fonksiyonunu çağırmıyor. `scripts/06` içindeki
teknik çekince deseni de başka bir iş akışına aittir.

Sentetik sözleşme vakası `Tube current 100 mAs; reconstructed at 5 mm.` teknik,
`a mass measuring 12 mm in the right upper lobe` ise klinik ölçü olarak doğru
ayrıldı. R2'de (b) tipi kusur bulunmadı.

## 4. R3: Anatomi filtresinin kapsamı ve doğruluğu

### 4.1 Sayısal ayrım

| Ölçüm | Sayı |
|---|---:|
| Anatomi ilişkisiyle elenen varlık | 6.093 |
| Zaten kapsam dışı bölümde olan | 6.057 (%99,41) |
| Kapsam içi bölümden yeni elenen | 36 (%0,59) |
| Kapsam içi etkilenen cümle | 22 |
| Kapsam içi etkilenen seri | 14 |

6.057 varlık için anatomi filtresi bölüm filtresini tekrar etmektedir. Yeni
karar yalnız kapsam içindeki 36 varlığa etki eder. Bu 36 varlığın 25'i
`absent`, 11'i `present` durumundadır. Hedef anatomi dağılımı bütün 6.093
varlıkta breast 2.137, esophagus 1.790, thyroid 1.630, abdomen 452, liver 38,
spleen 26, kidney 13 ve pancreas 7'dir.

### 4.2 Kapsam içi cümlelerin tam incelemesi

22 cümlenin 19'unda 32 varlık açık biçimde akciğer dışı organa aittir ve eleme
doğrudur. Üç cümlede dört varlık yalnız en yakın anatomiye bağlandığı için
toraks kanıtı yanlış veya eksik temsil edilmektedir:

1. `No acute pathology such as infection, malignancy ... in the abdomen,
   bone, breast, esophagus, heart, mediastinum, pleura, thyroid, trachea, or
   bronchie regions.` cümlesindeki `infection` ve `malignancy`, yalnız
   `abdomen`a bağlanıp eleniyor. İfade hem akciğer dışı hem torasik yapıları
   kapsayan çok organlı bir negasyondur.
2. `... lesions in the liver, suggesting metastatic disease, and bilateral
   pulmonary nodules ... early-stage lung cancer ...` cümlesindeki
   `pulmonary nodules`, `liver`a bağlanıp eleniyor. Aynı cümledeki `density`
   ve `cancer` akciğere bağlı kaldığından toraks kanıtı ancak kısmen korunuyor.
3. `... biopsy of the liver lesions and pulmonary nodules ...` cümlesindeki
   `pulmonary nodules` yine `liver`a bağlanıp eleniyor; bu cümlede nodül
   kanıtı tamamen kayboluyor.

İlişki katmanı her gözlem için en fazla bir `located_at` bağı kuruyor.
Train'deki 31.278 `located_at` ilişkisinde birden fazla hedefi olan gözlem
yoktur. Bu nedenle filtre, yanlış tekil bağı doğru kabul edip karışık organlı
cümlede geri dönüşsüz eleme yapmaktadır. **Anatomi filtresi aşırı eleme
yapıyor; R3 kabul ölçütünü geçmemiştir.**

### 4.3 Kemik yapılar

`bone`, `rib`, `vertebra` ve `sternum`un anatomi filtresinin dışında bırakılması
kilitli C5-03 sınır vakasıyla uyumludur. Bölüm düzeyinde kemik başlığı kapsam
dışı, özet içindeki vertebra metastazı ise şema hedefi gereği kapsam içidir.
Bu klinik olarak organ-simetrik bir politika değildir, ancak sözleşmede açıkça
ilan edildiği ve dondurulmuş sınır takımına dayandığı için bu denetimde ayrı
bir (b) tipi kusur sayılmamıştır.

## 5. R4: Sınıf dağılımı ve gerileme

Değerlendirmeye dahil 2.050 train serisinde sınıf dağılımı bağımsız olarak
yeniden üretildi:

| Sınıf | Kilit | Yeniden ölçüm |
|---|---:|---:|
| `None` | 1.669 | 1.669 |
| `not_mentioned` | 209 | 209 |
| `intermediate` | 89 | 89 |
| `indeterminate` | 82 | 82 |
| `known_malignancy` | 1 | 1 |

Anatomi filtresi kapatılarak yapılan karşılaştırmada seri sınıfı değişen vaka
yoktur. Filtre 14 serinin `evidence_count` değerini düşürmüş ve böbrek kitlesi
bulunan bir seride `nodul_var_mi` değerini `true`dan `false`a çevirmiştir. Bu
değişiklik akciğer dışı böbrek kitlesinin çıkarılmasıyla açıklanır.

Sınıf dağılımının sabit kalması, R3'teki yanlış elemenin zararsız olduğunu
göstermez. Hata bu train kümesinde nihai sınıfı değiştirmemiş, fakat kanıt
satırlarını değiştirmiştir. R4 sınıf dağılımı açısından geçti.

## 6. R5: Kilit, kod ve üretilmiş artefaktların tutarlılığı

### 6.1 Yeniden üretilebilen kalemler

Değerlendirme evreni 2.050 seriyle sınırlandığında A tablosunun 20 kolonu ve B
tablosunun 15 kolonu kilitle aynıdır. Aşağıdaki değerler de yeniden üretildi:

| Kalem | Sonuç |
|---|---:|
| Kanıt satırı | 84.763 |
| İlişki satırı | 33.676 |
| Nodül dağılımı (`false/true/not_assessable`) | 1.394 / 519 / 137 |
| Ekstratorasik malignite bayraklı seri | 85 |
| Bilinmeyen/meta bölüm malignite bayraklı seri | 46 |
| Mediastinum kaynaklı seri | 1.921 |
| Kapsam içi bölümü olmayan seri | 53 |
| Şüpheli niteleyicili varlık | 574 |
| L1 boyutlu kanıt / seri | 77 / 64 |
| `measurement_available` seri | 64 |
| Anatomiyle elenen varlık | 6.093 |

Şablon oranı, değerlendirme dışı 12 seriyi de içeren 48.144 train cümlesinde
%38,256'dır ve kilitle aynıdır. Yalnız değerlendirmeye dahil 47.873 cümledeki
oran %38,276'dır. Kilit farklı kalemlerde iki ayrı train paydası kullandığı
için bu paydaların adlandırılması gerekir.

### 6.2 Tutarsızlıklar

1. `scripts/63_vlm14_tam_kosum.py --kapsam train`, yalnız `split` filtresi
   uyguluyor; `included_in_evaluation` filtresi uygulamıyor. Bu nedenle üretim
   girişi 2.062 seri, 48.144 cümle, 85.331 varlık ve 33.919 ilişki üretirken
   kilit 2.050 seri, 84.763 varlık ve 33.676 ilişkiyi ilan ediyor.
2. Diskteki `astra_seri_duzeyi_train.parquet` 2.062, B tablosu 85.331 satırdır.
   A tablosu `adaptor_surumu=astra-adaptor-1.1` taşımasına rağmen
   `sozlesme_surumu=astra-sozlesme-1.0` taşımaktadır. Güncel kod ve kilit
   `astra-sozlesme-1.1` ilan etmektedir.
3. `reports/vlm14_kosum_gunlugu_train.json` hâlâ adaptör ve sözleşme sürümünü
   `1.0` olarak kaydetmektedir.
4. Train koşum betiği cümle Parquet'inin tamamını okuduktan sonra split filtresi
   uyguluyor. Bu yeniden denetimde betik çalıştırılmadı; ancak mevcut kodla
   `--kapsam train` çalıştırılması `dev` ve `held_out` satırlarını belleğe alır.
   İş emrindeki sıkı "yalnız train satırlarına dokunulur" sınırı için split
   filtresi okuma anında uygulanmalıdır.

Kilit dosyasının sürüm alanı ve revizyon defteri günceldir, fakat kilit, üretim
girişi ve diskteki A/B artefaktları aynı evreni ve sürümü temsil etmemektedir.
R5 bu nedenle geçmemiştir.

## 7. Test sonucu

1.1 düzeltmeleri için seçilen yedi hedefli test geçti. Bu testler kolonların
varlığını ve elenen gözlemin tanımlı ekstratorasik anatomiye bağlı olmasını
kontrol ediyor; `located_at` bağının semantik olarak doğru olup olmadığını veya
karışık organlı cümlede pulmoner gözlemin korunduğunu sınamıyor. R3'te bulunan
iki `pulmonary nodules` vakasının mevcut testlerden geçebilmesinin nedeni budur.

Tam test koleksiyonu çalıştırılmadı. Mevcut modül fixture'ı
`astra_sentences.parquet` dosyasının tamamını filtresiz okuduğu için denetimin
`dev` ve `held_out` sınırını ihlal eder.

## 8. Hüküm ve gerekli düzeltmeler

R2 ve R4 geçti. R1'de ilişki yokluğunu sessizce boş ilişki sayan yol, R3'te
karışık organlı cümlelerde aşırı eleme ve R5'te üretim/kilit/artefakt
tutarsızlıkları bulundu. Kabul ölçütü gereği **`dev` açılmaz.**

Bir sonraki adaptör sürümü `astra-adaptor-1.2` olmalıdır. Açılmadan önce:

1. `iliskiler=None` tüm ilişki tabanlı girişlerde açık hata üretmelidir.
2. Anatomi filtresi, tek başına en yakın `located_at` bağına dayanarak
   `pulmonary nodules` gibi açık toraks kanıtını elemeyecek biçimde
   daraltılmalıdır. Yukarıdaki iki karışık organ cümlesi gerileme testine
   eklenmelidir.
3. Üretim girişi train evrenini okuma anında sınırlandırmalı ve
   `included_in_evaluation` politikasını kilitle aynı uygulamalıdır.
4. A/B tabloları, koşum günlüğü ve adaptör kilidi aynı sürüm ve aynı payda ile
   yeniden üretilmelidir.
5. R1, R3, R4 ve R5 düzeltme sonrasında yalnız train üzerinde yeniden
   çalıştırılmalıdır.

Bu denetim klinik doğruluğu veya duyarlılığı ölçmez. Hüküm yalnız kod, veri
sözleşmesi ve dondurulmuş train artefaktlarının tutarlılığı içindir.
