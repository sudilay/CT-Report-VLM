# Astra Hattı Sözleşme Uyum Denetimi

**Tarih:** 2026-09-08  
**Kapsam:** SUDE-VLM-14, Adım 5 öncesi kapı  
**İncelenen veri:** yalnız `train`, 2.050 seri ve 47.873 cümle  
**Hüküm:** **KALDI. `dev` açılamaz.**

## 1. Kapsam ve veri güvenliği

Kod, sözleşme ve kilit dosyaları açık olarak incelendi. Veri ölçümlerinde
`astra_sentences.parquet` yalnız `split == "train"` ve
`included_in_evaluation == true` filtresiyle okundu.
`astra_entities_train.parquet` ve `astra_relations_train.parquet` train
artefaktlarıdır. `dev` ve `held_out` satırları incelenmedi.

`Kanser_Etiketi_y`, `Censor_Time` ve `Pillar_Ensemble_Skoru` okunmadı.
Etiket okuyan `scripts/62_vlm14_olculebilirlik_envanteri.py` kaynak kodu
incelendi, fakat betik çalıştırılmadı. Mevcut VLM-14 test takımının veri
fixture'ı bütün `astra_sentences.parquet` dosyasını filtresiz okuduğu için bu
denetim sırasında test takımı da çalıştırılmadı.

Şema girdisi olarak yalnız kapsam içindeki **51.443 varlık / 1.997 seri**
kullanıldı. Kapsam içi varlığı olmayan 53 train serisi toplama aşamasında
ayrıca hesaba katıldı.

## 2. K1: Girdi sözleşmesi

Şema kodundan çıkarılan alan listesinde iş emrindeki taslağa ek olarak
`temporality` alanı bulundu. `raw_text` açıklama metninde anılıyor ancak karar
kodunda okunmuyor. `suphe_yukseltebilir`, girdi tablosundan değil
`BulguSonucu` nesnesinden okunuyor.

| alan | Astra kaynağı | null | farklı değer | durum |
|---|---|---:|---:|---|
| `normalized_concept` | varlık tablosu | %0,0 | 117 | Sağlanıyor |
| `cumle_metni` | varlık tablosu | %0,0 | 9.866 | Sağlanıyor |
| `assertion` | varlık tablosu | %0,0 | 2 | `present/absent`; kapsam içinde `uncertain` yok |
| `sent_idx` | `cumle_idx` yeniden adlandırılıyor | %0,0 | 24 | Sağlanıyor |
| `sablon_cumle` | train cümlelerinden sonradan hesaplanıyor | %0,0 | 2 | Değeri üretilebilir, çağrı zinciri zorunlu kılmıyor |
| `entity_id` | varlık tablosu | %0,0 | 51.443 | Sağlanıyor ve benzersiz |
| `assertion_rule` | varlık tablosu | %0,0 | 12 | Sağlanıyor |
| `supheli_niteleyici` | `modify` ilişkilerinden sonradan hesaplanıyor | %0,0 | 2 | Değeri üretilebilir, çağrı zinciri zorunlu kılmıyor |
| `section` | `bolum_ham` yeniden adlandırılıyor | %0,0 | 83 | Sağlanıyor |
| `dusuk_guven_kodu` | `girdi_filtresi.uygula` üretiyor | %0,0 | 4 | Şema içinde güvenli biçimde üretiliyor |
| `dusuk_guven` | `girdi_filtresi.uygula` üretiyor | %0,0 | 2 | Şema içinde güvenli biçimde üretiliyor |
| `assertion_cue` | varlık tablosu | %64,9 | 30 | Null, varsayılan atamalarda beklenen; dolu değerler kullanılıyor |
| `temporality` | varlık tablosu | %0,0 | 2 | Sağlanıyor; iş emri taslak listesinde eksikti |

`sablon_cumle=True` 9.491, `supheli_niteleyici=True` 539 ve
`dusuk_guven=True` 1.598 kapsam içi varlıkta görüldü. Alanlar tek değerli
değildir.

### K1 kusuru

Değerler bağımsız denetimde açıkça zenginleştirildiğinde üretilebiliyor;
ancak üretim hattında bu sırayı zorunlu kılan bir çağrı yoktur.
`seri_ozeti`, `sablon_kolonu_ekle` ve `supheli_niteleyici_ekle`
fonksiyonlarını çağırmaz. `_sema_girdisi`, `supheli_niteleyici` eksikse hata
vermek yerine sessizce `False` atar. `sablon_cumle` eksikliği de şemada
sessiz atlanır. Kod tabanı taramasında bu hazırlık adımlarını birleştirip
`seri_ozeti` çağıran üretim girişi bulunmadı.

Bu, iş emrinde tanımlanan **(b) tipi kusurdur**. `C#nodul-kalip` bugün açıkça
devre dışı olduğu için mevcut sınıf dağılımını değiştirmiyor; ancak dal tekrar
açılırsa aynı sessiz ölüm yeniden oluşur. Girdi sözleşmesi alan yokluğunu
normal değer gibi kabul etmemelidir.

## 3. K2: Kural dallarının ateşlenmesi

Sayım, yalnız şemaya gerçekten verilen `kapsam_ici=True` train varlıklarında
yapıldı. `kurallar_sirali` adlı bir sembol güncel `sema.py` içinde yoktur;
mevcut `_bulgu_duzeyi` ve `rapora_topla` dalları doğrudan denetlendi.

| dal / kaynak | varlık | durum | sıfırsa açıklama |
|---|---:|---|---|
| `benign-eksen` | 83 | Ateşliyor | |
| `A26+C#12+§4.2` kesin benign hüküm | 58 | Ateşliyor | |
| `C#nodul-kalip` | 0 | (a) Meşru | Kural D87 ile açıkça kapalı; açılsa 4 seride 6 aday var |
| Malignite dışı geçiş `-` | 45.055 | Ateşliyor | |
| `C#bilinen-kanser` | 2 | Ateşliyor | 1 seri sonucunu belirledi |
| `A1+C#1` negasyon | 4.837 | Ateşliyor | |
| `A1+C#negbelirsiz` | 0 | (a) Meşru | Train kapsam içi metinde önkoşul deseni yok |
| `C#16` ayırıcı tanı | 186 | Ateşliyor | |
| `A18` dışlanamazlık | 0 | (a) Meşru | Train kapsam içi metinde önkoşul deseni yok |
| `§4.3` ayırt edilemezlik | 0 | (a) Meşru | Train kapsam içi metinde önkoşul deseni yok |
| `§3.4` parantez içi soru | 0 | (a) Meşru | Kapsam içinde `uncertain` malignite varlığı yok |
| `A18+C#10` diğer uncertain | 0 | (a) Meşru | Kapsam içinde `uncertain` malignite varlığı yok |
| `girdi-filtresi:dusuk-guven` | 1.097 | Ateşliyor | |
| `C#4(derece)` | 0 | (a) Meşru | 9 ham adayın tamamında daha öncelikli `C#16` kazandı |
| `C#4(kismi)` | 117 | Ateşliyor | |
| `C#4(varsayilan)` | 8 | Ateşliyor | F2 muaf spikülasyon yolu çalışıyor |
| İşlenmeyen assertion | 0 | (a) Beklenen | Geçersiz assertion değeri yok |

Sıfır ateşlenen dalların her biri ya açık politika ile kapalıdır, ya ham
önkoşulu train verisinde yoktur ya da daha öncelikli bir dal tarafından
bilinçli olarak karşılanmıştır. Zenginleştirilmiş doğru girdi verildiğinde
K2 içinde ayrıca bir (b) tipi ölü dal bulunmadı. CT-RATE karşılaştırmasına
gerek duyulmadı; sıfırların nedeni Astra train üzerindeki ham önkoşul
sayımlarıyla doğrudan ayrıştırılabildi.

## 4. K3: Yirmi train raporunun manuel bölüm incelemesi

Örnek sabit `20260908` tohumu ile sıralı train seri anahtarlarından rastgele
seçildi. Etiket veya skor kullanılmadı.

| # | seri anahtarı | sonuç |
|---:|---|---|
| 1 | `125071/01-02-2001-NLST-LSS-94146/4.000000-2OPASEVZOOMB50f320212060.030.0null-23976` | Uyumlu; akciğer önerileri doğru biçimde meta |
| 2 | `119620/01-02-2001-NLST-LSS-35723/3.000000-2OPASEVZOOMB50f376212060.030.0null-09792` | Uyumlu; rapor başlığındaki organ listesi meta |
| 3 | `203921/01-02-2001-NA-NLST-ACRIN-53095/3.000000-2OPASESEN4B30f320212080402-37914` | Uyumlu; başlıksız giriş fail-closed, akciğer bulgusu `abnormalities/right lung` içinde |
| 4 | `113899/01-02-1999-NLST-LSS-96189/2.000000-0OPASEVZOOMB50f3702120120.060.0null-06887` | Uyumlu |
| 5 | `119522/01-02-2001-NLST-LSS-50253/2.000000-2OPASEVZOOMB30f388212075.040.0null-75164` | Uyumlu; başlıksız giriş klinik bulgu taşımıyor |
| 6 | `214957/01-02-2000-NA-NLST-ACRIN-38952/4.000000-1OPASESEN64B30f330212037.5251.5-30622` | Uyumlu; başlıksız giriş klinik bulgu taşımıyor |
| 7 | `203879/01-02-1999-NA-NLST-ACRIN-63257/2.000000-0OPAGELSULTBONE3511.21204029.61.4-86572` | Uyumlu |
| 8 | `125587/01-02-2000-NLST-LSS-46768/4.000000-1OPATOAQUL4FC51306.22-80529` | Uyumlu |
| 9 | `101717/01-02-2001-NLST-LSS-66819/3.000000-2OPATOAQUL4FC51340.62-89387` | Uyumlu |
| 10 | `119050/01-02-1999-NLST-LSS-71364/4.000000-0OPATOAQUL4FC51318.82-87776` | Uyumlu; pulmonoloji ifadesi öneri, bulgu değil |
| 11 | `216905/01-02-1999-NA-NLST-ACRIN-16222/2.000000-0OPAGELSULTSTANDARD3601.21206044.41.4-82969` | Uyumlu |
| 12 | `112516/01-02-2000-NLST-LSS-43908/3.000000-1OPASEVZOOMB50f288212060.030.0null-31966` | Uyumlu |
| 13 | `122078/01-02-2001-NLST-LSS-59915/3.000000-2OPASEVZOOMB50f310212060.030.0null-75557` | Uyumlu |
| 14 | `209690/01-02-2000-NA-NLST-ACRIN-76029/3.000000-1OPATOAQUL4FC10429.7212075nana-19667` | Uyumlu |
| 15 | `211787/01-02-2001-NA-NLST-ACRIN-78060/2.000000-2OPAGELS16STANDARD3601.21204029.11.4-62997` | Uyumlu; teknik bilgi doğru biçimde meta |
| 16 | `120160/01-02-2000-NLST-LSS-59923/5.000000-1OPASESEN16B30f356212045.030.0null-79974` | Uyumlu; akciğer tavsiyeleri doğru biçimde öneri/meta |
| 17 | `123079/01-02-2000-NLST-LSS-45613/2.000000-1OPASEVZOOMB30f306212075.040.0null-06493` | Uyumlu |
| 18 | `209203/01-02-2001-NA-NLST-ACRIN-25553/2.000000-2OPAGELSPR16BONE3661.21204029.11.4-57250` | Uyumlu |
| 19 | `210232/01-02-2000-NA-NLST-ACRIN-23408/2.000000-1OPASESEN16B30f382212052.5351.5-39125` | Uyumlu; başlıksız giriş klinik bulgu taşımıyor |
| 20 | `127708/01-02-1999-NLST-LSS-57061/6.000000-0OPASESEN16B50f358212045.030.0null-76580` | Uyumlu; başlıksız giriş ve öneriler klinik bulgu taşımıyor |

Özet:

- Akciğer bulgusunun yanlışlıkla `dis_organ`, `meta` veya `bilinmeyen`
  kovasına düşmesi: **0/20**.
- `Normal` değerinin bölüm açması: **0/20**.
- Kapsam dışı bölümde gerçek akciğer bulgusu kalması: **0/20**.
- Beş raporda kapsam dışı metin akciğer sözcüğü taşıyordu; tamamı öneri,
  yöntem açıklaması veya organ listesiydi, klinik bulgu değildi.
- Beş raporda `__bassiz__` girişi vardı; tamamı açıklama/çekince metniydi ve
  fail-closed davranış uygundu.

K3 örnekleminde (b) tipi kusur görülmedi.

## 5. K4: Kilidin yeniden üretimi

Kilit train verisiyle, çıktılar diske yeniden yazılmadan bellekte üretildi.

| kilit kalemi | kilit | yeniden ölçüm | durum |
|---|---:|---:|---|
| A tablosu kolonları | 18 kolon | aynı 18 kolon | Geçti |
| B tablosu kolonları | 15 kolon | aynı 15 kolon | Geçti |
| Seri | 2.050 | 2.050 | Geçti |
| Kanıt satırı | 84.763 | 84.763 | Geçti |
| Şablon cümle oranı | %38,0 | 18.288/47.873 = %38,201 | Geçti; tam yüzdeye yuvarlanınca %38 |
| Sınıf dağılımı | 1.669 / 209 / 89 / 82 / 1 | aynı | Geçti |
| Nodül dağılımı | 1.393 / 520 / 137 | aynı | Geçti |
| Ekstratorasik elenen seri | 131 | 131 | Geçti |
| Kapsam içi bölümü olmayan seri | 53 | 53 | Geçti |
| İlişki satırı | 33.676 | 33.676 | Geçti |
| Şüpheli niteleyicili varlık | 574 | 574 | Geçti |
| L1 boyutlu kanıt / seri | 77 / 64 | 77 / 64 | Geçti |
| `measurement_available` seri | 64 | 64 | Geçti |

Kilit sayıları ve kolon listeleri yeniden üretildi. Şablon oranının kilitte
hangi basamakta yuvarlandığı yazılmamıştır; ham oran %38,201 olup tam yüzdeye
yuvarlandığında kilitteki %38,0 değerini verir. Bu belge açıklığı sorunudur,
kilidi bayat yapan sayısal bir uyuşmazlık değildir.

## 6. K5: Bağlayıcı kısıtların kod karşılığı

| kısıt | kod karşılığı ve train kanıtı | sonuç |
|---|---|---|
| Sürekli olasılık üretilmez | A tablosu yalnız ayrık `report_derived_malignancy_label` üretir; A/B şemasında skor yok | Geçti |
| `boyut_mm` yalnız L1 | `boyut_ekle`, yalnız `relation_type == "measured_by"` ilişkisini kullanıyor; 77 kanıt / 64 seri | Geçti |
| Teknik ölçü asla bağlanmaz | Mevcut train'de 144 teknik cümledeki 119 ölçünün tamamı elendi ve teknik cümlede `measured_by` sayısı 0 | **Kod garantisi kusurlu** |
| Ekstratorasik eleme sayılır | Kapsam dışındaki present malignite varlıkları 131 seri için bayrağı kaldırıyor | **Kısmi; özet bölümü kusuru var** |
| Şema kuralı değiştirilmez | Astra kapsam filtresi şemadan önce uygulanıyor; `sema.py` içinde Astra'ya özgü dal yok | Geçti |
| Şablon yalnız train'den | `sablon_kolonu_ekle`, frekansları yalnız `split == "train"` üzerinde hesaplıyor | Geçti |

### K5.1 Teknik satır garantisi

Metin katmanı teknik cümleyi `astra.teknik_satir_mi` ile doğru işaretliyor;
ancak `scripts/61_vlm14_train_aktarim_denetimi.py` bu alanı kullanmıyor.
Ölçüyü, daha dar ve farklı bir `scripts/07.teknik_mi` deseniyle yeniden
değerlendiriyor. Mevcut train satırlarının tamamı bu dar desenle de yakalandığı
için bugünkü çıktı doğru görünmektedir.

Kod garantisi aynı değildir. Sentetik sözleşme vakası
`Tube current 100 mAs; reconstructed at 5 mm.` için Astra adaptörü satırı
teknik kabul ederken üretim ölçü filtresi teknik kabul etmez. Böyle bir satır
gelecekte `measured_by` ilişkisine girebilir. Bu **(b) tipi kusurdur**.

### K5.2 Özet bölümündeki ekstratorasik kanıt

Sözleşme, `conclusion/findings/abnormalities` içinde anatomik olarak akciğer
dışı olan malignite kanıtlarının elenmesini ve sayılmasını ister. Kod yalnız
başlık kovasına bakıyor; `ozet` kovasının tamamını kapsam içine alıyor ve
özet içeriğinde organ düzeyi eleme yapmıyor.

Train'de gerçek malignite terimi ve akciğer dışı organı aynı cümlede taşıyan
iki özet cümlesi bulundu. Biri bütünüyle olumsuzdu. Diğerinde karaciğer
metastazı ile pulmoner nodül/akciğer kanseri aynı cümledeydi; üç present
malignite varlığı şemaya girdi. `located_at` ilişkisi karaciğer metastazını
ayırabilecek bilgi taşısa da adaptör bu bilgiyi kapsam kararında kullanmıyor.

Bu **(b) tipi kusurdur**. Ayrıca bilinmeyen başlıklardaki 8 present malignite
varlığına sahip 4 seri de aynı `qf_ekstratorasik_malignite_elendi` bayrağına
dahil edilmekte; bayrak ekstratorasik organ ile bilinmeyen/meta kaybını
birbirinden ayırmamaktadır.

### K5.3 Mediastinum kaynak bayrağı

Sözleşme mediastinal kanıtların `qf_mediastinum_kaynakli=true` taşımasını
ister. Bu alan `vlm14.py`, A/B kolonları ve adaptör kilidinde yoktur.
Mediastinum kapsam içinde tutuluyor fakat katkısı vaat edildiği biçimde
ayrıştırılamıyor. Bu da **(b) tipi sözleşme uyumsuzluğudur**.

## 7. K6: Sınıf dağılımının açıklaması

Train A tablosu dağılımı yeniden üretildi:

| sınıf | seri |
|---|---:|
| `None` | 1.669 |
| `not_mentioned` | 209 |
| `intermediate` | 89 |
| `indeterminate` | 82 |
| `known_malignancy` | 1 |

`None` ile `not_mentioned` ayrımı kodda ve veride tutarlıdır:

- `None` üreten 1.669 serinin 1.663'ünde belirleyici kaynak kapsamlı
  negasyon (`A1+C#1`), 6'sında kesin benign hükümdür (`A26+C#12+§4.2`).
- `not_mentioned` üreten 209 serinin 90'ında yalnız raporu yükseltemeyen
  düşük güvenli aday vardır; 63'ünde kapsam içi malignite kavramı yoktur;
  53'ünde kapsam içi varlık yoktur; 3'ünde yalnız benign eksen vardır.

Astra raporları organ başına tekrarlanan `No masses/nodules` cümleleri
taşıdığı için aktif negatif sınıfın yüksek olması beklenir. Dağılımın
`not_mentioned` ile karıştığını veya açıklanamayan bir dal kaybını gösteren
kanıt bulunmadı. K6 tek başına blokaj oluşturmaz.

## 8. Hüküm ve gerekli düzeltmeler

K3, K4 ve K6 geçti. Doğru biçimde hazırlanmış girdi üzerinde K2'de kusur
bulunmadı. Ancak K1 ve K5'te en az bir (b) tipi kusur bulunduğu için kabul
ölçütü gereği **Adım 5 durur ve `dev` açılamaz**.

Adaptör sürümü yükseltilmeden önce şu düzeltmeler gerekir:

1. `sablon_cumle` ve `supheli_niteleyici` hazırlığını tek üretim girişinde
   zorunlu kılmak; eksik alanlarda sessiz `False` yerine hata vermek.
2. Ölçü aktarımında metin katmanının `is_technical_param` kararını kullanmak
   veya iki teknik tanımını tek ortak fonksiyona indirmek.
3. Özet bölümlerindeki ekstratorasik kanıtı ilişki/anatomi düzeyinde elemek ve
   ayrı kalite bayrağıyla saymak; karışık organlı cümlelerde toraks kanıtını
   korumak.
4. Sözleşmedeki mediastinum kaynak bayrağını A/B çıktısına eklemek veya bu
   vaadi sözleşmeden açık bir sürüm kararıyla kaldırmak.
5. `measurement_available` için isteğe bağlı sessiz `False` varsayımını
   kaldırmak; L1 ilişkileri verilmediyse açık hata veya kalite durumu üretmek.
6. Düzeltmelerden sonra adaptör sürümünü yükseltmek, train artefaktlarını ve
   kilidi yeniden üretmek ve bu kapıyı tekrar çalıştırmak.

Bu denetim şemanın klinik doğruluğunu, Astra raporlarının doğruluğunu veya
kaçırılan malignite bulgularına ilişkin duyarlılığı ölçmez.
