# Yapılandırılmış Çıkarım Motorunun Astra/NLST Rapor Kohortuna Uygulanması

**Sonuç Raporu · 2026-09-08**
Korpus: NLST toraks BT, Astra görsel-dil modeli tarafından üretilmiş 2.965
rapor. Değerlendirmeye uygun 2.940 seri, 1.198 hasta.

---

## 1. Özet

Bu çalışmada, daha önce CT-RATE korpusunda geliştirilen kural tabanlı çıkarım
motoru, Astra modelinin NLST taramalarından ürettiği 2.965 radyoloji raporuna
uygulanmıştır. Amaç, serbest metin raporları makinenin işleyebileceği bir
tabloya çevirmektir: nodül var mı, hangi lobda, kaç milimetre, iyi huylu bir
işaret var mı, malignite şüphesi hangi düzeyde.

**Sorulan soru şuydu: bu raporlardan klinik bir yapılandırılmış tablo
çıkarılabilir mi? Cevap kısmen evettir.**

| İstenen kolon | Durum | Dolu seri |
|---|---|---:|
| Nodül var mı | üretildi | 2.965 / 2.965 |
| Benign bulgu bayrağı | üretildi | 609 (yüzde 20,5) |
| Lob bilgisi | üretildi | 511 (yüzde 17,2) |
| Boyut (mm) | üretildi, **çok seyrek** | **94 (yüzde 3,2)** |
| Lung-RADS skoru | **üretilmedi** | yok |

Nodül alanı bütün seriler için üretilmiştir, ancak 2.965 serinin 208'inde
(yüzde 7,0) karar verilememiş ve `değerlendirilemez` olarak işaretlenmiştir;
geri kalan 2.757 seride nodül var veya yok kararı verilebilmiştir.

Ölçü 94 seride (yüzde 3,2) elde edilebilmiştir. Bu oran, kolonun pratikte
kullanılabilir olması için gereken düzeyin çok altındadır. Lung-RADS
kategorisi hiç üretilmemiştir. Bunun nedeni çıkarım motorunun yetersizliği
değil, kaynak raporların bu bilgiyi taşımamasıdır: 122.758 kanıt satırının
yalnız 113'ünde bir lezyona bağlanabilen ölçü vardır ve `part-solid` ile
`subsolid` ifadeleri kohortta hiç geçmemektedir.

**Bu düşük doluluk çalışmanın başarısızlığı değil bulgusudur.** Görsel-dil
modeli tarafından üretilen radyoloji raporları, klinik kılavuz uygulamaya
yetecek ölçüm ayrıntısını büyük ölçüde içermemektedir.

### Diğer temel sonuçlar

**Malignite bağlamlı cümlelerde sözlük boşluğu bulunmamıştır.** CT-RATE
metninde geliştirilen sözlük, malignite bağlamlı cümlelerin tamamında
yapılandırılmış kavram üretebilmiştir; ölçülen boşluk yüzde 0,0'dır. Bu ölçüm
sözlüğün tümünü değil, önceki çalışmada tanımlanan bu dar evreni kapsar.

Buna karşılık malignite bağlamlı cümlelerin kendisi azdır: bu cümlelerin oranı
Astra'da binde 8,5, CT-RATE'te yüzde 2,59'dur. Sözlük bu dar evrende iyi
çalışmakta, ancak üzerinde çalışacağı malzeme sınırlıdır.

**Değerlendirme şeması donduruldu.** Şema iki önceki çalışmada
dondurulamamıştı. Bu kez `sema-1.0` olarak dondurulmuş, ancak bunun için bir
protokol değişikliği gerekmiştir: hedef uyumu için konan yüzde 100 eşiği
ulaşılamaz bulunmuş ve ölçüt yeniden tanımlanmıştır. Sayısal sonuç 24/30'dur ve
"geçti" olarak yeniden adlandırılmamıştır.

**Modelin "nodül yok" demesi ayırt edici bir bilgi taşımamaktadır.** Nodül
bulunmadığını bildiren hastalarda kanser oranı yüzde 6,58, böyle bir beyan
taşımayanlarda yüzde 5,50'dir. Aradaki fark 1,08 yüzde puanı olup hasta
kümeli önyükleme ile hesaplanan yüzde 95 güven aralığı eksi 2,08 ile artı
4,41 arasındadır. Aralık sıfırı içerdiğinden, negatif beyanın kanser riskini
azalttığı gösterilememiştir.

**Değerlendirme kümesi etiketle açılmamıştır.** Özellikler kör üretilmiş,
hiçbir metrik hesaplanmamıştır.

---

## 2. Kaynak metinlerin niteliği

Kohorttaki raporlar rutin klinik raporlar değildir. Astra modelinin NLST
görüntülerinden ürettiği metinlerdir ve organ başlıklı bir şablon yapısı
taşırlar. Raporların yüzde 57,4'ünde doldurulmamış yer tutucu ifade
bulunmaktadır. Bu özellikler bulguların yorumlanmasında dikkate alınmalıdır.

Şu konular bu çalışmanın kapsamı dışındadır: metrik ve kalibrasyon protokolü,
değerlendirme kümesinin etiketli analizi, Lung-RADS kategorisi ve model
istemlerinin gözden geçirilmesi.

---

## 3. Yöntem

### 3.1 Veri sözleşmesi ve bölüm eşlemesi

Astra raporları organ başlıklı bir şablon kullanmaktadır. Çıkarım motorunun bu
yapıya doğru uygulanabilmesi için, kod yazılmadan önce bir veri sözleşmesi
hazırlanmıştır. Sözleşmenin belirlediği başlıca kurallar şunlardır.

**İki başlık sözdizimi tanınır.** Kalın etiket biçimi 2.869 raporda, Markdown
başlığı biçimi 900 raporda görülmektedir. Hiçbir başlık içermeyen rapor sayısı
79'dur.

**Bölüm başlığını ad belirler, madde işareti belirlemez.** Ölçüm, organ
başlıklarının da madde işaretiyle geldiğini göstermiştir: `lung` başlığı 174
kez düz, 1.780 kez madde işaretli biçimde geçmektedir. Buna karşılık `normal`
etiketi 5.975 kez yalnız değer konumunda kullanılmaktadır. Bu nedenle tanınan
bir bölüm adı yeni bölüm açar; tanınmayan kalın etiket bölüm açmaz ve içeriği
bağlı bulunduğu bölümde kalır. Madde işareti ölçüt alınsaydı her organdan
yaklaşık 1.780 bölüm başlığı kaybedilecekti.

**Bilinmeyen başlık kapsam dışıdır ve işaretlenir.** Sözlük korpusu tam
kapsamaktadır; tanımsız başlık sayısı sıfırdır.

**Teknik parametre satırları bağlamlı desenlerle ayrılır.** Ölçü çıkarımı bu
satırları kaynak almaz.

### 3.2 Girdi kolonu kısıtı

Çıkarım hattı kaynak dosyadan yalnız hasta kimliği, seri anahtarı ve rapor
metni kolonlarını okumaktadır. Kanser etiketi, takip süresi ve model risk
skoru kolonları hattın hiçbir aşamasında açılmamaktadır; bölünme ve uygunluk
bilgisi bölünme kilidinden türetilmektedir. Bu kısıt, değerlendirme kümesi
özelliklerinin kör üretilmesini disipline değil yapıya bağlamakta ve bir
gerileme testiyle korunmaktadır.

### 3.3 Anatomik kapsam kararı

Değerlendirme şeması bölge bağımsızdır: kilitli sınır takımı akciğer dışı
malignite vakalarını bilerek içermekte ve bunların rapor düzeyi sınıfı
yükseltmesini öngörmektedir. Buna karşılık NLST'nin altın standardı akciğer
kanseridir.

Bu farkın maliyeti ölçülmüştür. Eğitim kümesinde, akciğer dışı organ adı ile
olumsuzlanmamış malignite terimi aynı cümlede yalnız 99 kanserli serinin
1'inde (yüzde 1,0) ve 1.963 kanser dışı serinin 4'ünde bulunmaktadır. NLST bir
tarama kohortudur; hastalar çoğunlukla asemptomatik, yakalanan kanserler erken
evredir ve uzak metastaz nadirdir.

Bu ölçüme dayanarak akciğer dışı organ bölümleri girdi kapsamının dışında
bırakılmıştır. Şemanın kuralı değiştirilmemiştir; değişen, şemaya verilen
metnin kapsamıdır.

Eleme iki katmanlıdır. Bölüm düzeyi kapsam, özet bölümleri için tek başına
yetersizdir: sonuç ve bulgu bölümleri kapsam içindedir ve içlerinde akciğer
dışı kanıt geçebilir. Bu nedenle anatomi ilişkisiyle kesin olarak akciğer dışı
bir organa bağlanan gözlemler, kapsam içi bölümde bulunsalar dahi
elenmektedir. Eleme varlık düzeyindedir. Ancak ilişki katmanı her gözlem için en fazla bir
anatomi bağı kurduğundan, bu bağ karışık organlı cümlelerde yanlış olabilir.
Bu nedenle filtre muhafazakâr tutulmuştur: bir cümlede hem toraks hem akciğer
dışı anatomi bulunuyorsa tekil bağ güvenilmez sayılır ve **o cümlede hiçbir
eleme yapılmaz**. Bunun sonucu, toraks kanıtının korunması, ancak aynı
cümledeki akciğer dışı kanıtın da elenmeden kalmasıdır. Bu, bilinçli bir
seçimdir: gerçek toraks kanıtını kaybetme riski, birkaç akciğer dışı kanıtı
tutma riskinden ağır basmaktadır.

Kemik yapılar bu kümeye bilinçli olarak dahil edilmemiştir, çünkü kilitli sınır
takımı vertebra metastazlarını bilinen malignite olarak hedeflemektedir.

Elenen kanıt üç ayrı kalite bayrağıyla sayılmaktadır: organ kaynaklı eleme,
bilinmeyen veya meta bölüm kaybı, ve mediastinum katkısının ayrıştırılması.

---

## 4. Değerlendirme şemasının dondurulması

Şema, önceki iki çalışmada sınanmış ve iki kez dondurulamamıştı. Bu kez
`sema-1.0` olarak dondurulmuştur.

**Hedef uyumu eşiği ulaşılamaz bulunmuş ve ölçüt yeniden tanımlanmıştır.**
Kilitli sınır takımındaki altı uyumsuzluğun altısı da kapatılamaz niteliktedir.

| Uyumsuzluk | Kök neden |
|---|---|
| Düşük şüphe düzeyi vakası | Bu düzey üretilemiyor; üretmek yanlış pozitif koruma kapısını kırıyor |
| Stabil malignite ailesi (üç vaka) | Zaman ekseninin ölçülen başarımı yüzde 36,4; kuralı gevşetmek ölçülmüş bir hatayı sonuca taşır |
| Olumsuz belirsizlik vakası | İlgili kavramı envantere eklemek korpusun yüzde 11,7'sinin sınıfını değiştiriyor |
| Regrese malignite vakası | Çıpa deseni tetiklemiyor; genişletmek ölçüyle daraltılmış bir deseni geri açar |

Birinci satır özellikle önemlidir. Hedef uyumu kapısını geçmek için düşük şüphe
düzeyinin üretilmesi gerekir, ancak bu düzeyi üretmek yanlış pozitif koruma
kapısını kırmaktadır. İki kabul ölçütü bu vaka üzerinde birbirini
dışlamaktadır. Eşiğin sağlanamaması bu nedenle eksik çalışmanın değil, ölçüt
setinin kendi içinde tutarsız olmasının sonucudur.

**Sayısal sonuç 24/30'dur ve "geçti" olarak yeniden adlandırılmamıştır.**
Değişen, sayı değil ölçüttür ve değişiklik kayıt altına alınmıştır.

### 4.1 Üç kapının durumu

| Kapı | Ölçüt | Sonuç |
|---|---|---|
| Yanlış pozitif koruması | 23 kontrol vakasında sıfır malignite | 0 ihlal |
| Bilinen malignite kör metin doğrulaması | Kesinlik en az yüzde 85 | yüzde 88,9 (40 vaka) |
| Dağılım kapısı, yüksek şüphe basamağı | Yüzde 0,0336 ile 0,108 aralığı | yüzde 0,0632 |

Kural sürümü daraltıldığı için kör doğrulama yeni bir örneklemle
yinelenmiştir; bağımsız yargıç yalnız cümle metnini görmüştür. Dağılım kapısı,
bilinen malignite basamağının üretilmeye başlamasıyla geçersizleşmişti.
Kapının kendi türeyiş metni yüksek şüphe basamağını tek başına varsaydığından
değerlendirme bu basamak için ayrıştırılmıştır; aralık ve desenler
değiştirilmemiştir.

### 4.2 İlan edilen dört sınır

Bu şemayı kullanan her çalışmada aşağıdaki sınırlar beyan edilir.

1. Hedef uyumu 24/30'dur. Yüzde 100 eşiği ulaşılamaz bulunmuş ve ölçüt
   yeniden tanımlanmıştır.
2. Düşük şüphe vakası üzerinde hedef uyumu kapısı ile yanlış pozitif koruma
   kapısı birbirini dışlamaktadır. Ölçüt seti bu vaka bakımından kendi içinde
   tutarsızdır.
3. Kör metin doğrulaması güç yetersizdir. Kırk vakalık örneklemde yüzde 88,9
   nokta tahmininin güven aralığı yüzde 73,9 ile 96,9'dur; gerçek kesinliğin
   eşiğin üzerinde olduğu istatistiksel olarak gösterilmemiştir.
4. Dağılım kapısı düşük güçlüdür ve yalnız kaba sapmaları dışlayabilir;
   geçilmesi kalibrasyonun doğruluğunu kanıtlamaz. Klinik uzman onayı yoktur.

---

## 5. Sözlüğün aktarımı

Çıkarım sözlükleri CT-RATE metninde geliştirilmiş ve Astra'nın dağılımını
görmemişti. Önceki bir çalışmada benzer bir durumda kavram farkının yüzde
78'inin çeviri kaybı değil sözlük boşluğu olduğu ortaya çıkmış, ölçüm
yapılmasaydı sonuç yanlış nedene bağlanacaktı. Bu nedenle üretimden önce ölçüm
yapılmıştır.

Eğitim kümesinde (2.050 seri, 47.873 cümle) 84.763 varlık üretilmiştir.

| Ölçüt | Değer |
|---|---:|
| Sözlük boşluğu | yüzde 0,0 |
| Karşılaştırma: CT-RATE geliştirme havuzu | yüzde 0,4 |
| Varlık durumu: mevcut / yok | 55.175 / 29.586 |

Negasyon katmanının şablon metin üzerinde beklendiği gibi çalıştığı, kitle
kavramına ait 8.474 varlığın 7.803'ünün yok olarak işaretlenmesinden
görülmektedir.

Aktarım sorunsuzdur, ancak aktarılacak malzeme azdır. Malignite bağlamlı cümle
oranı Astra eğitim kümesinde binde 8,5, CT-RATE geliştirme havuzunda yüzde
2,59'dur.

---

## 6. Ölçülebilirlik

### 6.1 Lung-RADS kategorisi bu kohortta üretilememektedir

ACR Lung-RADS v2022 kategorisi nodül tipi, ortalama çap ve büyüme
bilgilerinden hesaplanır. Eğitim kümesinde bu eksenlerin kapsamı şöyledir.

| Eksen | Seri | Oran |
|---|---:|---:|
| Nodül ifadesi | 1.607 | yüzde 78,4 |
| Kalsifikasyon | 941 | yüzde 45,9 |
| Büyüme ifadesi | 623 | yüzde 30,4 |
| Lob bilgisi | 579 | yüzde 28,2 |
| Buzlu cam | 266 | yüzde 13,0 |
| Solid | 7 | yüzde 0,34 |
| Spikülasyon | 7 | yüzde 0,34 |
| Part-solid veya subsolid | 0 | yüzde 0,0 |
| Benign kalsifikasyon paterni | 0 | yüzde 0,0 |

Ölçü ile lezyon arasındaki bağ, üretim boyutunun tek meşru kaynağı olan aynı
cümle düzeyinde 2.050 serinin 50'sinde kurulabilmektedir. Aynı bölüm düzeyinde
61, aynı rapor düzeyinde 66 seri ortak bulunma göstermektedir; bu sayılar
denetim kaydı olup ölçü ile lezyon arasında bağ kurulduğu anlamına gelmez.

Zorunlu negatif kontrol sağlanmıştır: 119 teknik parametre ölçüsünün hiçbiri
hiçbir lezyona bağlanmamıştır.

### 6.2 Negatif beyanın ayırt edici değeri

Modelin nodül bulunmadığını açıkça bildirdiği raporlar, böyle bir beyan
taşımayanlarla karşılaştırılmıştır. Aynı hastaya ait birden çok seri bağımsız
gözlem sayılamayacağından karşılaştırma hasta düzeyinde yapılmış ve güven
aralıkları hasta kümeli önyüklemeyle üretilmiştir.

| Grup | Hasta | Kanser oranı |
|---|---:|---:|
| Negatif beyan taşıyan | 365 | yüzde 6,58 |
| Negatif beyan taşımayan | 473 | yüzde 5,50 |
| **Fark** | | **artı 1,08 puan** |

Farkın yüzde 95 güven aralığı eksi 2,08 ile artı 4,41 arasındadır ve sıfırı
içermektedir. Negatif beyanın kanser riskini azalttığı gösterilememiştir.

İki grubun kendi güven aralıklarının örtüşmesi tek başına bir eşitlik testi
sayılmayacağından, karşılaştırma farkın kendi aralığı üzerinden yapılmıştır.

---

## 7. Doğrulama kümesi

Kurallar adaptör kilidiyle sabitlendikten sonra doğrulama kümesi bir kez
açılmıştır. Amaç, dondurulmuş motorun eğitim kümesi dışında da beklendiği gibi
davrandığını doğrulamaktır.

| Ölçüt | Eğitim | Doğrulama |
|---|---:|---:|
| Seri | 2.050 | 450 |
| Sözlük boşluğu | yüzde 0,0 | yüzde 0,0 |
| Bilinmeyen başlıklı cümle | yüzde 4,60 | yüzde 4,33 |
| Kapsam içi cümle | yüzde 43,9 | yüzde 44,1 |
| Malignite göstergesi yok sınıfı | yüzde 81,4 | yüzde 82,0 |
| Belirtilmemiş sınıfı | yüzde 10,2 | yüzde 11,1 |
| Orta şüphe sınıfı | yüzde 4,3 | yüzde 3,3 |
| Belirsiz sınıf | yüzde 4,0 | yüzde 3,6 |

Tablodaki en büyük fark 1,0 yüzde puanıdır (orta şüphe sınıfı). Sözlük boşluğu her iki kümede sıfırdır.

**Doğrulama kümesi sonucuna göre hiçbir kural değiştirilmemiştir.** Bu nedenle
küme, doğrulama niteliğini korumaktadır.

---

## 8. Üretilen tablolar

Tam koşum, dondurulmuş motorla 2.965 serinin tamamı üzerinde yürütülmüştür.

| | Değer |
|---|---:|
| İşlenen seri | 2.965 |
| Değerlendirmeye dahil | 2.940 |
| Uygunluk filtresiyle dışlanan | 25 |
| Cümle | 69.055 |
| Varlık | 122.758 |
| İlişki | 48.842 |

Çıktı iki tablodan oluşmaktadır: seri düzeyi özet tablo (20 kolon) ve kanıt
düzeyi uzun tablo (15 kolon). Tek tablo çoklu nodül durumunu temsil
edemediğinden bu ayrım yapılmıştır.

Sınıf dağılımı bölünme kümeleri arasında tutarlıdır.

| Sınıf | Eğitim | Doğrulama | Değerlendirme |
|---|---:|---:|---:|
| Malignite göstergesi yok | yüzde 81,4 | yüzde 82,0 | yüzde 82,0 |
| Belirtilmemiş | yüzde 10,2 | yüzde 11,1 | yüzde 10,7 |
| Orta şüphe | yüzde 4,3 | yüzde 3,3 | yüzde 3,6 |
| Belirsiz | yüzde 4,0 | yüzde 3,6 | yüzde 3,6 |

### 8.1 Kolon doluluk oranları

| Kolon | Seri | Oran |
|---|---:|---:|
| Nodül var | 741 | yüzde 25,0 |
| Nodül yok | 2.016 | yüzde 68,0 |
| Değerlendirilemez | 208 | yüzde 7,0 |
| Benign bulgu bayrağı | 609 | yüzde 20,5 |
| Lob bilgisi | 511 | yüzde 17,2 |
| Ölçü mevcut | 94 | yüzde 3,2 |
| Nodül tipi mevcut | 399 | yüzde 13,5 |
| Yer tutucu içeren rapor | 1.702 | yüzde 57,4 |

Kanıt düzeyinde ölçü içeren satır sayısı 113'tür ve tamamı aynı cümle
kaynaklıdır.

Nodül alanının üç değerli olması bilinçlidir. Değerlendirilemez, nodül yok ile
aynı anlama gelmez: kanıt yokluğu, yokluk kanıtı değildir.

### 8.2 Değerlendirme kümesinin kör üretimi

Değerlendirme kümesi serileri için özellikler dondurulmuş motorla kör biçimde
üretilmiştir. Çıkarım hattı kaynak dosyadan yalnız hasta kimliği, seri
anahtarı ve rapor metni kolonlarını okumakta; etiket ve skor kolonlarını
hiçbir aşamada açmamaktadır. Bu kısıt bir gerileme testiyle korunmakta ve
çalıştırma günlüğünde kayıt altına alınmaktadır.

Çıktılar etiketle birleştirilmemiş, hiçbir metrik hesaplanmamış ve sonuçlara
göre hiçbir kural değiştirilmemiştir.

### 8.3 Bağlayıcı kısıtlar

1. Sürekli olasılık üretilmez. Kural motoru kategorik kanıt üretir. Etiketlere
   uyarlanmış bir skorun aynı veriye uyarlanacak bir modele öznitelik olarak
   verilmesi hedef sızıntısı oluşturur.
2. Boyut yalnız aynı cümle kaynağından alınır ve teknik parametre satırından
   asla alınmaz.
3. Akciğer dışı bölümden elenen malignite kanıtı sayılır; sessiz kayıp
   yasaktır.
4. Şemanın kuralı değiştirilmez; Astra'ya özgü her düzenleme adaptörde yaşar.
5. Şablon istatistiği yalnız eğitim kümesinden hesaplanır.
6. İlişki katmanı verilmeden çağrı yapılamaz; eksik alan sessizce varsayılan
   değere düşürülmez.

---

## 9. Geçerlilik ve sınırlılıklar

**Değerlendirme kümesi etiketle açılmamıştır.** Özellikler kör üretilmiş,
metrik hesaplanmamış ve sonuçlara göre hiçbir kural değiştirilmemiştir.

**Değerlendirme kümesinde önceki bir maruziyet bulunmaktadır.** Bölünme
dondurulmadan bir gün önce kohortun tamamı etiketlerle birlikte çözümlenmiş,
duyarlılık ve özgüllük tabloları üretilmiş ve bir karar eşiği denenmiştir.
Hasta düzeyinde sızıntı yoktur, ancak sonuç görme ve eşik seçme maruziyeti
vardır. Bu küme, hiç görülmemiş bağımsız test olarak sunulmamalıdır. Temiz dış
geçerlilik iddiası ayrı bir kohorta bırakılmıştır.

**Kaynak metinler model çıktısıdır.** Bulgular, insan yazımı klinik raporlara
doğrudan genellenemez.

**Malignite bağlamlı cümle sayısı düşüktür.** Bu, çıkarım sonuçlarının
istatistiksel gücünü sınırlamaktadır.

**Şemanın dört ilan edilmiş sınırı** bu çalışmanın çıktıları için de
geçerlidir.

---

## 10. Bulunan ve düzeltilen kusurlar

Çalışma sırasında üç bağımsız denetim yürütülmüş, üçü de kusur bulmuş ve ikisi
üretimi durdurmuştur. Bulunan dokuz kusurun tamamı düzeltilmiş ve gerileme
testine bağlanmıştır.

| Kusur | Sonucu olacaktı |
|---|---|
| Teknik parametre deseni, harf duyarsız uygulandığında kitle sözcüğüyle eşleşiyordu | Ölçü içeren 222 raporun 221'i teknik sayılacak, lezyon ölçümleri elenecekti |
| Markdown başlık sözdizimi tanınmıyordu | 900 raporun bölüm yapısı çözümlenemeyecekti |
| Veri sözleşmesine akciğer dışı kanıtı bastıran bir kural yazılmıştı | Şemanın bağlayıcı bir kararı çiğnenecekti |
| Bağlam atama fonksiyonlarının dönüş değeri yok sayılmıştı | Bütün varlık durumları boş kalacak, negasyon hiç uygulanmayacaktı |
| Şablon ve şüpheli niteleyici alanları üretilmiyordu | Bir kuralın iki dalı sessizce ölü kalacaktı |
| Anatomi elemesi tek bir bağa dayanarak açık toraks kanıtını eliyordu | Pulmoner nodül ifadesi karaciğer bağlantısı nedeniyle kaybolacaktı |
| İlişki katmanı boş verildiğinde sessizce varsayılan kullanılıyordu | Üç girdi aynı anda susacaktı |
| Kilit, üretim ve disk çıktıları aynı evreni temsil etmiyordu | Sayılar yeniden üretilemeyecekti |
| Bir uyumsuzluğun kör doğrulamaya bağlı olduğu varsayılmıştı | Ulaşılabilir uyum tavanı yanlış raporlanacaktı |

Bu kusurlardan birinin ayrıca yöntemsel bir dersi vardır. Teknik parametre
deseni kusurluyken üretilen sayı (91 rapor), güvenli desenle üretilen sayıyla
(97 rapor) yüzde 6,6 farkla uyuşmakta ve kabul aralığında görünmekteydi.
Uyuşan sayı, yöntemin doğru olduğunu göstermez.

Bir hata sınıfı üç kez tekrarlanmıştır: eksik bir alan sessizce varsayılan
değere düşürülünce kural dalı hata vermeden ölmektedir. Bu davranış artık açık
hata üretmektedir.

Son denetim turunun bulguları düzeltildikten sonra adaptör `astra-adaptor-1.2`
sürümüne yükseltilmiş, eğitim artefaktları yeniden üretilmiş ve düzeltmelerin
sınıf dağılımını değiştirmediği doğrulanmıştır. Denetimin adını verdiği üç
karışık organlı cümle gerileme testine eklenmiştir.

---

## 11. Sürümler ve yeniden üretilebilirlik

| Bileşen | Sürüm veya dosya |
|---|---|
| Veri sözleşmesi | `astra-sozlesme-1.1` |
| Bölüm adaptörü | `src/radyovlm/extraction/astra.py` |
| Kolon sözleşmesi | `astra-adaptor-1.2` · `configs/astra_adaptor_kilidi.json` |
| Değerlendirme şeması | `sema-1.0` · `configs/degerlendirme_semasi.json` |
| Bölünme kilidi | `astra-split-1.0` · `configs/splits_astra.json` |
| Segmentasyon | `astra-seg-1.0` |
| Şablon eşiği | 10 farklı eğitim hastası |
| Metin katmanı | `scripts/60_vlm14_astra_metin_katmani.py` |
| Aktarım denetimi | `scripts/61_vlm14_train_aktarim_denetimi.py` |
| Ölçülebilirlik envanteri | `scripts/62_vlm14_olculebilirlik_envanteri.py` |
| Koşum | `scripts/63_vlm14_tam_kosum.py` |
| Çıktı tabloları | `outputs/vlm14/astra_seri_duzeyi.parquet` · `astra_kanit_duzeyi.parquet` |
| Çalıştırma günlüğü | `reports/vlm14_kosum_gunlugu_tam.json` |
| Gerileme testleri | `tests/test_vlm14_astra.py` |
| Test sonucu | 508 başarılı |
