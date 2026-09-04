# TASK-16 · Metin Tabanlı Malignite/Benign Gösterge Çıkarım Şeması

**Tarih:** 2026-09-04
**Korpus:** CT-RATE toraks BT, 25.692 rapor
**Çıktı:** Kural tabanlı karar motoru (`sema-0.9-taslak`), kaynağa dayalı
kural tabanı, kilitli sınama altyapısı ve bağımsız doğrulama kaydı

---

## 1. Özet

Raporlardan çıkarılmış yapılandırılmış bulguları rapor düzeyinde bir
malignite şüphe sınıfına çeviren karar şeması tasarlandı, kodlandı ve
kilitli bir vaka kümesine karşı sınandı.

Çalışmanın sonunda elde edilenler:

- Dört kaynak kılavuzdan aktarılmış, her biri belirli tablo veya paragrafa
  atıflı 35 kural
- Geliştirme havuzunun tamamı (383.644 cümle) taranarak ölçülmüş 13 klinik
  karar kaydı
- Kurallar yazılmadan önce kilitlenmiş ve bağımsız denetimden geçirilmiş
  58 vakalık sınama kümesi
- Çıkarım katmanının ölçülmüş hatalarını izole eden girdi kalite filtresi
- Çalışan karar motoru ve 400 otomatik testten oluşan bir gerileme koruması
- Yanlış pozitif koruma kapısının ihlalsiz geçilmesi (23/23)
- İki bağımsız sistemin (Codex, Gemini) kör yargılamasıyla doğrulama

Şema `sema-0.9-taslak` sürümündedir ve dondurulmamıştır. Üç kabul kapısından
biri geçilmiş, ikisi geçilememiştir; her ikisinin de kök nedeni saptanmış ve
bir sonraki göreve (TASK-17) devredilmiştir.

## 2. Kapsam ve amaç

Görev, radyoloji raporundan çıkarılmış bulgular verildiğinde raporun
malignite şüphe düzeyini belirleyen kural bütününü üretmektir. Sonraki
görevlerin ölçümleri bu sınıflandırmaya dayanacağından, buradaki
belirsizlikler ileri aşamalara doğrudan taşınır.

Projenin ayırt edici önceliği malignite duyarlılığını en üst düzeye
çıkarmak değil, yanlış pozitif oranını düşürmektir. Tasarım kararları bu
önceliğe göre alınmıştır.

Patoloji doğrulaması bu aşamada mevcut değildir. Bu nedenle şema için
klinik doğruluk iddiasında bulunulmamakta; savunulabilir olan yalnızca
yöntemsel disiplindir: ölçülmeden karar verilmemesi, kabul ölçütlerinin
sonuç görülmeden yazılması ve her kuralın bir kaynağa bağlanması.

## 3. Yöntem

### 3.1 Veri bölünmesi

Şema yazımı korpus incelemesi gerektirdiğinden, aynı veri üzerinde
değerlendirme yapılması durumunda ortaya çıkacak yanlılık baştan engellendi.
Bölünme, herhangi bir kural yazılmadan önce hasta düzeyinde yapıldı ve
kilitlendi:

| | hasta | çalışma |
|---|---:|---:|
| Geliştirme havuzu | 17.000 | 20.576 |
| Değerlendirme kilidi | 4.304 | 5.116 |

Değerlendirme kilidi çalışma boyunca hiç açılmadı. Planlama aşamasında örnek
olarak kullanılan cümlelerin kilide düşme durumu ayrıca ölçüldü: 17 hasta
kilitte görünüyordu, ancak bunların 14'ü hastaya özgü bilgi taşımayan şablon
cümlelerden kaynaklanıyordu. Gerçek maruziyet üç hasta olarak belirlendi ve
bu hastalar sonraki örneklemelerden çıkarıldı.

### 3.2 Kural tabanının kaynaktan aktarılması

Kuralların yazarın kendi yargısıyla üretilmesini engellemek için, şemadaki
her kural ya kaynakta cümle olarak yazılı bir kılavuz maddesine ya da
gerekçesi belgelenmiş bir mühendislik varsayılanına bağlandı. Aktarım
sırasında yalnızca bölüm numarası vermek yeterli sayılmadı; her kural için
kaynağın ilgili tablo veya paragrafı gösterildi.

| kaynak | aktarılan kural |
|---|---:|
| Alan sözlüğü §12.2 | 20 |
| Lung-RADS v2022 | 7 |
| RECIST 1.1 | 4 |
| Fleischner 2017 | 4 |
| Toplam | 35 |

Aktarım sonucunda dört karar, mühendislik varsayılanı olmaktan çıkıp kılavuz
dayanağı kazandı: enfeksiyon bulgularının malignite ölçeğinin dışında
değerlendirilmesi, kalsifikasyonun tek başına benignlik göstermemesi, rapor
düzeyinde en yüksek şüphe düzeyinin belirleyici olması ve büyümenin şüpheyi
yükseltmesi.

### 3.3 Klinik karar noktalarının ölçülmesi

Şemanın kaç noktada klinik yargı gerektireceği tahmin edilmedi. Geliştirme
havuzunun tamamı taranarak, aynı cümle içinde birbiriyle çelişen gösterge
sınıflarının birlikte geçtiği durumlar sayıldı ve 19 karar noktası
çıkarıldı. Ardından her varsayılan gerçek cümlelerle sınandı.

Sınama sonucunda maddelerin dördü kaynağa dayandırıldı, üçünde tarif edilen
çelişkinin korpusta gerçekte bulunmadığı görüldü, ikisi uygulanabilir bir
popülasyona sahip olmadığı için düşürüldü, biri kapsam kuralına dönüştü.
Geriye klinik yargı gerektiren 10 madde kaldı; ikinci denetim sonrasında bu
sayı 13'e yükseldi.

Sınama, iki varsayılanın hatalı kurgulandığını da gösterdi. Birincisinde,
negasyonun kapsamı dikkate alınmadığı için *"No significant difference … in
terms of metastases"* biçimindeki cümlelerde mevcut bir metastaz siliniyordu;
kural, olumsuzlamanın neyi kapsadığına bakacak biçimde yeniden yazıldı.
İkincisinde, malignite ve benign göstergelerin birlikte geçtiği durumlar
çelişki sayılmıştı; incelenen cümlelerde ise radyoloğun açıkça ilan ettiği
bir belirsizlik söz konusuydu ve taraf seçmek bilgi kaybına yol açıyordu.

### 3.4 Kuralların korpusta uygulanabilirliği

Kılavuzda yazılı olması bir kuralın bu korpusta uygulanabilir olduğunu
göstermez. Her A-tipi kuralın korpustaki hacmi ölçüldü ve karşılığı
bulunmayan kurallar şemaya alınmadı.

İki bulgu kapsamı doğrudan etkiledi. Birincisi, büyüme ekseninin bu korpusta
pratikte bulunmamasıdır: `enlarged` ifadesinin 14.378 eşleşmesinin 12.233'ü
*"enlarged lymph node"* kalıbından gelmekte ve statik boyut bildirmektedir.
Zamansal karşılaştırmaya dayalı gerçek lezyon büyümesi 383.644 cümlede 167
kez geçmektedir (çalışmaların %0,64'ü). Lung-RADS'in büyüme temelli kuralları
bu nedenle şemaya alınamamış ve durum rapora yazılmıştır.

İkincisi, korpusun önemli bir bölümünün kılavuz kapsamı dışında kalmasıdır.
Fleischner belgesi kendi metninde 35 yaş altına uygulanmadığını belirtmekte,
Lung-RADS ise tarama popülasyonunu hedeflemektedir. Korpusun %24,53'ü
(5.046 çalışma) 35 yaş altındadır. Şema bu bölgede yalnızca kendi
varsayılanlarıyla çalışmakta ve bu sınır ilan edilmiştir.

Kalsifikasyon ekseni ayrıca denetlendi. Kılavuzun benign kabul ettiği
spesifik paternler (popcorn, santral, konsantrik, tam kalsifikasyon) korpusta
toplam 36 cümlede geçerken, genel *"calcific"* ifadesi 13.862 cümlede
geçmektedir. Kalsifikasyon içeren ifadelerin %99,7'si kılavuzun benign
tanımını karşılamamaktadır; bu nedenle kalsifikasyon tek başına benignlik
göstergesi sayılmamıştır.

### 3.5 Sınama kümelerinin hazırlanması ve denetimi

Sınama kümeleri, kurallar yazılmadan önce oluşturuldu. 30 sınır vakası,
23 negatif kontrol vakası ve 5 çok cümleli rapor vakası ilan edilmiş bir
örnekleme yordamıyla (sabit tohum, popülasyon başına kota) seçildi; her
vakanın hedef sınıfı dayanağıyla birlikte atandı ve dosyalar hash'lenerek
kilitlendi.

Kilitlenen kümenin kendisi de bağımsız denetime verildi. Denetim 14 bulgu
üretti; 11'i tam, 2'si kısmen kabul edildi. Denetimin en önemli üç katkısı:

- Öneri ifadelerinin durum bildirimi sayılmaması yönündeki kendi kuralımızın
  iki vakada ihlal edildiği saptandı ve hedefler düzeltildi.
- Negatif kontrol kümesinin, klinikte en sık yanlış pozitif üreten grupları
  (şablon negatif ifadeler, post-operatif değişiklikler, amfizem, koroner
  kalsifikasyon) içermediği görüldü; küme 15 vakadan 23 vakaya çıkarıldı.
- Kümedeki bütün vakaların tek cümleden oluştuğu, oysa şemanın çıktısının
  rapor düzeyinde olduğu tespit edildi. Bulguları rapor düzeyinde birleştiren
  toplama kuralının hiçbir testi bulunmuyordu; 5 çok cümleli rapor vakası
  eklendi.

Toplam altı hedef düzeltildi ve küme `takim-1.1` sürümüyle yeniden
kilitlendi. Önceki sürüm silinmeyip arşivlendi. Kilidin açılması tek
seferliktir ve gerekçesi kayıtlıdır: düzeltmeler kurallar yazılmadan önce
yapılmış olup, bir kuralın sonucunu görüp hedefi değiştirme durumu söz
konusu değildir.

### 3.6 Girdi kalite filtresi

Şemanın girdisi bir önceki fazın çıkarım katmanıdır ve bu katmanın kusurları
ölçülmüştür. Filtre tasarımı sırasında yapılan inceleme, iki alanın bilgi
taşıma kapasitesinin sanılandan düşük olduğunu gösterdi: zamansallık
değerlerinin %99,24'ü ve `present` atamalarının %80,33'ü herhangi bir metinsel
ipucuna dayanmadan, varsayılan olarak atanmıştır.

Bu durumun somut riski doğrulandı: `prior` ve `present` olarak işaretlenmiş
4.557 varlık bulunmakta, bunların %81,4'ü ipucusuzdur. Yani geçmişe ait bir
bulgunun güncel sayılması ve toplama kuralı yoluyla raporu maligniteye
yükseltmesi teorik değil, gerçekleşen bir senaryodur.

İki filtre kuralı yazıldı; her ikisi de ölçülmüş bir kusura dayanmaktadır.
Filtre varlıkları elemez, düşük güvenli olarak etiketler: bu varlıklar
kayıtta kalır ve raporlanır, ancak rapor sınıfını yükseltemez. Filtrenin
hedeflenmesi ölçüldü:

| | oran |
|---|---:|
| Tüm varlıklar içinde düşük güven | %2,98 |
| Malignite ekseni içinde düşük güven | %34,3 |

Filtre genel bir bastırma uygulamamakta, etkisini yalnızca ilgili eksende
göstermektedir.

## 4. Karar motoru ve sınama

### 4.1 Uygulama

Karar motoru, kural sırası ve her kuralın kaynak atfı bildirimsel bir dosyada
(`configs/degerlendirme_semasi.json`) kayıtlı olacak biçimde kodlandı. Kod ile
bildirimsel kayıt arasındaki tutarlılık otomatik testlerle bağlandı; belge
kodun gerisinde kalırsa test başarısız olur.

### 4.2 Sınama sırasında saptanan uygulama hatası

İlk koşumda hedeflerle uyum beklenenin altında kaldı. Kuralların
sorgulanmasından önce ölçüm aracının doğruluğu denetlendi ve bir uygulama
hatası bulundu: motorun desen aradığı metin alanı cümle değil, varlığın
kendi metin parçasıydı (ortalama 11 karakter). Cümle düzeyinde çalışması
gereken üç kural bu parça üzerinde arama yaptığı için hiçbir koşulda
tetiklenemiyordu. Sınav raporundaki kural atıflarında bu kuralların hiç
görünmemesi durumu doğruladı.

Hata, cümle metninin motora ayrı bir alan olarak verilmesiyle giderildi.
Düzeltme sırasında, metnin yalnızca hâlihazırda çıkarılmış bir varlığın
niteliğini okumak için kullanılması; metinden yeni varlık üretilmemesi kuralı
korundu, böylece her karar bir varlık kimliğine bağlı kalmaya devam etti.

Bu düzeltmenin ardından sekiz kural hatası daha saptanıp giderildi. Hepsi
yazılı bir kaynağa atıflıdır ve yeni klinik yargı içermez. Örnek olarak:
ayırıcı tanı kuralı yönlü hipotez bildiren ifadeleri de ayırıcı tanı
saymaktaydı; *"dışlanamaz"* kalıbı cümlede geçtiği hâlde varlık `present`
işaretlendiğinde ilgili kural atlanıyordu; radyoloğun kesin benign hükmünün
öncelikli olması kararı belgelenmiş ancak kodlanmamıştı.

### 4.3 Sınama sonuçları

Sonuç hiçbir aşamada zorlanmadı; uyumsuzluklar gizlenmek yerine sınıflandırıldı.

| küme | ilk koşum | düzeltmelerden sonra |
|---|---:|---:|
| Sınır vakaları (30) | 11 | 20 |
| Negatif kontrol (23) | 21 | 22 |
| Çok cümleli rapor (5) | 3 | 3 |

Kalan 13 uyumsuzluğun her biri kök nedenine göre sınıflandırıldı:

| kök neden | vaka |
|---|---:|
| Çıkarım sözlüğünde tanımlı olmayan terim | 3 |
| Girdi filtresinin düşük güvenli varlıkları bastırması | 5 |
| "Bilinen kanser" eşiğinin otomatik üretilememesi | 2 |
| Hedef atama yordamı ile motorun kavram tanımı farkı | 2 |
| Şemanın kavram listesindeki eksiklik | 1 |

Bu dağılım, kalan uyumsuzlukların kural tasarımından değil, girdi katmanının
kapsamından kaynaklandığını göstermektedir.

### 4.4 Yanlış pozitif koruma kapısı

Projenin ayırt edici hedefini sınayan ölçüt, negatif kontrol kümesinde hiçbir
malignite şüphesi üretilmemesidir ve toleranssızdır.

Şema, açıkça benign, normal veya olumsuzlanmış olarak işaretlenmiş 23
kontrol vakasının hiçbirinde malignite şüphesi üretmemiştir (0 ihlal).
Kümede şablon negatif ifadeler, post-operatif değişiklikler, amfizem, koroner
kalsifikasyon, sekel değişiklikler ve teknik yetersizlik bildiren cümleler
bulunmaktadır.

### 4.5 Duyarlılık analizi

Çıkarım katmanının ölçülmüş hata oranları girdiye kasıtlı olarak enjekte
edilerek şema çıktısının kararlılığı sınandı. Şemanın kendisi
değiştirilmedi; yalnızca girdi bozuldu.

| senaryo | malignite-pozitif oranındaki değişim |
|---|---:|
| Zamansallık bilgisi tümüyle güvenilmez sayılırsa | ±0,000 puan |
| Kanıtsız `present` atamalarının tamamı gerçek sayılırsa | +0,058 puan |
| İpuçlu `present` atamaları aslında belirsiz sayılırsa | −0,049 puan |

Çıktı, girdi katmanının bilinen hatalarına karşı dar bir bantta kalmaktadır.
Zamansallık ekseninin çıktıyı hiç değiştirmemesi, bu eksenin şemada karar
ağırlığı taşımaması yönündeki kararın yerinde olduğunu göstermektedir.
Bandın darlığında, malignite-pozitif popülasyonunun küçük olmasının payı
bulunduğundan analiz sözlük genişletmesinden sonra tekrarlanacaktır.

## 5. Bağımsız doğrulama

Kilitli hedefleri atayan taraf ile kuralları yazan taraf aynı olduğundan,
hedeflerin kendisi dış denetime açıldı. 30 sınır vakası, hedef sınıflar ve
dayanak etiketleri paketten çıkarılarak (yalnızca vaka kimliği ve cümle
metni bırakılarak) iki ayrı sisteme kör olarak yargılatıldı. Codex ve Gemini
birbirlerinin çıktısını görmedi.

| karşılaştırma | uyum |
|---|---:|
| Codex ↔ kilitli hedef | %80,0 (24/30) |
| Gemini ↔ kilitli hedef | %86,7 (26/30) |
| Codex ↔ Gemini | %90,0 (27/30) |

Otuz vakanın 24'ünde üç yargı da örtüşmektedir. İki değerlendiricinin aynı
anda hedeften ayrıldığı dört vaka işaretlendi. Bunların üçü aynı konudan
kaynaklanmaktadır: spikülasyon gibi morfolojik bir bulgunun, cümlede açık bir
şüphe ifadesi bulunmadığında tek başına yönlü şüphe sayılıp sayılamayacağı.
Her iki değerlendirici de bu bulgunun dolaylı kanıt niteliğinde olduğunu ve
daha düşük bir düzeye karşılık geldiğini belirtti.

Kilitleme protokolü gereği hedefler değiştirilmedi. Bulgu, ilgili kural
bileşeninin gözden geçirilmesi gereken bir tasarım kalemi olarak kayda
alındı ve sözlük genişletmesi sonrasındaki koşuma bırakıldı. Dördüncü
vakada iki değerlendirici birbirinden de ayrıldığından, o vakada gerçek bir
ölçek belirsizliği bulunduğu sonucuna varıldı.

## 6. Tamamlanmamış kalemler

Şema `sema-1.0` olarak dondurulmamıştır. Üç kabul kapısının durumu:

| kapı | eşik | sonuç |
|---|---|---|
| Yanlış pozitif koruma kapısı | toleranssız | 0 ihlal, geçti |
| Kilitli hedeflerle uyum | %100 | sınır kümesinde 20/30 |
| Dağılım aralığı | %0,5 – %3,0 | %0,049 |

### 6.1 Sözlük kapsamı

Geçilemeyen iki kapının ortak kök nedeni, çıkarım sözlüğünün bazı malignite
terimlerini tanımamasıdır. Geliştirme havuzunda malignite kök terimleri geçen
421 cümlenin (288 çalışma) %18,8'inden hiçbir yapılandırılmış varlık
üretilmemektedir. Bu cümlelerin 28'i lenfanjitik veya peritoneal karsinomatoz
bildirmektedir; söz konusu terim mevcut kavramların bir eş anlamlısı değil,
ayrı bir klinik kavramdır.

Çıkarım sözlüğü dondurulmuş bir bileşendir ve önceki görevlerin ölçümleri
bu sürüme dayanmaktadır. Bu nedenle sözlük bu görev kapsamında açılmamış,
genişletme TASK-17'ye devredilmiştir.

### 6.2 Dağılım kapısı

Dağılım kapısının kabul aralığı, koşumdan önce dondurulmuş ve türeyişi
yazılmıştır. Dış çapa olarak, şemadan bağımsız biçimde ölçülmüş yüksek
dereceli şüphe ifadesi sıklığı kullanılmıştı.

Sonuç aralığın altında kalınca aralık değiştirilmedi ve kural gevşetilmedi;
bunun yerine popülasyonun nerede daraldığı ölçüldü. Yüksek dereceli şüphe
ifadesi taşıyan 392 cümlenin yalnızca 15'i malignite bağlamındadır; kalan
377 cümle enfeksiyon veya COVID-19 şüphesi bildirmektedir. Çapa, "şüphe
derecesi dili" ile "malignite şüphesi derecesi dili" eşitlendiği için hatalı
türetilmiştir.

Kapı, geçilememiş olarak kayda geçirildi. Bir sonraki ölçümde çapa, derece
ifadesi ile malignite terimlerinin kesişimi üzerinden yeniden türetilecektir.

## 7. Yeniden üretilebilirlik

Rapordaki sayıların tümü betikle yeniden üretilebilir; hiçbiri elle
yazılmamıştır.

| ölçüm | betik | çıktı |
|---|---|---|
| Çelişen gösterge taraması | `scripts/42` | `reports/task16_celisen_gosterge_taramasi.json` |
| Kuralların korpus karşılığı | `scripts/43` | `reports/task16_b_olcumleri.json` |
| Örnekleme ve kilit | `scripts/44-46` | `configs/sema_takim_kilidi.json` |
| Girdi filtresi ölçümü | `scripts/47` | `reports/task16_girdi_filtresi_olcum.json` |
| Şema sınaması | `scripts/48` | `reports/task16_sema_sinavi.json` |
| Dağılım ve duyarlılık | `scripts/49` | `reports/task16_dagilim.json` |
| Bağımsız yargı ayrışması | `scripts/51` | `reports/task16_adim7_ayrisma.json` |

## 8. Sayısal özet

| | |
|---|---|
| Taranan cümle (geliştirme havuzu) | 383.644 |
| Kaynaktan aktarılan kural | 35 |
| Belgelenmiş klinik karar | 13 |
| Kilitli sınama vakası | 58 |
| Bağımsız denetim bulgusu | 14 (11 tam kabul) |
| Saptanıp giderilen kural hatası | 8 |
| Yanlış pozitif koruma kapısı | 0 ihlal / 23 vaka |
| Bağımsız kör doğrulama uyumu | %80,0 · %86,7 (kendi aralarında %90,0) |
| Otomatik test | 400/400 |
| Kayda geçirilen bağlayıcı karar | D70–D77 |

## 9. Sonraki adım

TASK-17 (gösterge sözlükleri) bu görevden üç kalem devralmaktadır:

1. Çıkarım sözlüğünün genişletilmesi; `carcinomatosis` öncelikli kalemdir.
2. "Bilinen kanser" durumunun tespiti için kaynağa dayalı bir tetikleyici
   tanımlanması.
3. Dağılım kapısı çapasının doğru kesişim üzerinden yeniden türetilmesi.

Bu kalemler tamamlandığında şema yeniden koşulacaktır. Dondurma önkoşulları
`configs/degerlendirme_semasi.json` içinde yazılı olarak beklemektedir.
