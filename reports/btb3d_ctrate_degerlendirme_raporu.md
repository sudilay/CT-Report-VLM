# BTB3D Modelinin Toraks BT Raporu Üretimindeki Klinik Başarısı

### Otomatik ölçüm ve kör ikinci metin değerlendirmesi

**Tarih:** 2026-09-10 · **Model:** BTB3D · **Veri:** CT-RATE doğrulama kümesinden 500 toraks BT serisi

---

## Özet

BTB3D, üç boyutlu bilgisayarlı tomografi görüntülerinden otomatik radyoloji raporu üreten bir görüntü-dil modelidir. Bu çalışmada modelin ürettiği 500 rapor, aynı serilere ait hekim raporlarıyla karşılaştırıldı. Analiz birimi **BT serisidir**: 500 seri 428 benzersiz hastadan ve 463 çalışmadan gelmektedir, dolayısıyla bazı hastalar birden fazla seriyle temsil edilmektedir. Sorulan soru şuydu: **model raporu ile hekim raporu aynı klinik bulguları tarif ediyor mu?** Hekim raporu bağımsız görüntü-temelli altın standart değildir; dolayısıyla bu çalışma tek başına görüntüde gerçekte ne bulunduğunu değil, iki rapor arasındaki hasta-özgü klinik uyumu ölçer.

Sonuç iki yönlüdür.

Modelin ürettiği metinler çoğu zaman **biçim olarak inandırıcıdır**. Bölüm düzeni ve radyoloji üslubu birçok raporda gerçek rapora benzer; ancak sık görülen kesilme, bozuk başlangıç ve biçimlendirme artıkları nedeniyle biçimsel başarı kusursuz değildir. Kaynak ayırt etme deneyi yapılmadığından metinlerin hekim raporlarından ayırt edilemez olduğu iddia edilmemektedir.

Ancak metinlerin **hasta-özgü klinik uyumu çok düşüktür**. Bulgu düzeyinde ölçülen uyum (macro-F1 0,183), aynı sayıda bulguyu rastgele dağıtan bir sistemin alacağı skorun (0,151) yalnızca 0,031 üzerindedir. Bu fark için eşli bootstrap ile hesaplanan %95 güven aralığı [+0,010, +0,052] olup sıfırı içermemektedir: fark küçüktür ama rastlantı değildir. Malignite tespitinde ise kappa güven aralığı sıfırı içermektedir, dolayısıyla sonuç "şans düzeyinden ayırt edilemeyen uyum" olarak yorumlanmıştır.

Otomatik çıkarım, açık metin değerlendirmesi ve kör ikinci metin değerlendirmesi aynı yönde bulgu verdi. Bunlar üç ayrı değerlendirme yoludur; tümü aynı rapor çiftlerine ve aynı 18 sınıflı şemaya dayandığı için bütünüyle bağımsız deneyler olarak değerlendirilmemelidir.

---

## 1. Çalışmanın amacı

Otomatik rapor üreten modeller genellikle metin benzerliği ölçütleriyle değerlendirilir. BLEU ve ROUGE gibi bu ölçütler, üretilen metnin gerçek raporla kaç ortak kelime dizisi paylaştığını sayar.

Radyolojide bu yaklaşımın önemli bir zayıflığı vardır. Radyoloji raporları büyük ölçüde şablonludur ve cümlelerin çoğu olumsuzdur: *"Plevral efüzyon saptanmadı"*, *"Her iki akciğerde nodül izlenmedi"*. Şablonu ezberleyen bir model, görüntüye hiç bakmadan yüksek metin benzerliği elde edebilir. Aynı şekilde, bir raporda "nodül" kelimesinin geçmesi o hastada nodül bulunduğu anlamına gelmez.

Bu nedenle çalışmada metin benzerliği değil, **bulgu düzeyinde klinik uyum** ölçüldü: model raporu ile hekim raporu, aynı hastada aynı patolojileri tarif ediyor mu?

---

## 2. Yöntem

Her iki metin de, olumsuzlamayı ayırt edebilen bir çıkarım hattından geçirilerek on sekiz standart toraks patolojisine indirgendi. Patoloji listesi CT-RATE veri kümesinin kendi resmî etiket şemasından alındı, böylece bağımsız bir referansa bağlanmak mümkün oldu.

Ölçümün güvenilir olması için üç ayrı değerlendirme yolu kullanıldı:

| Yöntem | Kapsam | Nasıl yapıldı |
|---|---:|---|
| Otomatik çıkarım | 500 vaka | Olumsuzlama çözümlemesi yapan yazılım hattı tüm kohorta uygulandı |
| Açık değerlendirme | 30 vaka | Seçilen rapor çiftleri kaynak kimliği açıkken okunup patolojiler işaretlendi |
| Kör ikinci değerlendirme | 40 vaka | OpenAI Codex adlı yapay zekâ değerlendiricisine aynı iş verildi; birinci değerlendiricinin yargıları ile hangi metnin hekime/model çıktısına ait olduğu gizlendi |

Açık ve kör değerlendirmeler **30 ortak vakada** karşılaştırıldı (30 vaka × 2 metin × 18 sınıf = 1.080 karar). Kör pakette ayrıca yalnızca kör değerlendirilen 10 vaka bulunmaktadır; bu nedenle kör değerlendirmenin toplamı 40 vaka ve 1.440 karardır. Vaka seçimi önceden sabitlenmiş ve kaydedilmiştir: otuzu sabit tohumla kohortun tamamından rastgele çekilmiş, ek onu ise hekim raporunda malignite terimi geçen vakalardan ayrı bir havuzdan alınmıştır. İkinci grup kasten zenginleştirildiği için 40 vakalık sonuçlar kohort prevalansını temsil eden bağımsız bir örneklem tahmini olarak değil, otomatik ölçümün sağlamlık kontrolü olarak yorumlanmıştır.

### Kullanılan ölçütler

**Duyarlılık**, hekimin tarif ettiği bulguların ne kadarının yakalandığını gösterir. **Kesinlik**, model bir bulgu bildirdiğinde ne sıklıkla haklı olduğunu gösterir. **F1** bu ikisinin harmonik ortalamasıdır. Macro-F1 her patolojinin F1 değerini eşit ağırlıkla ortalar, böylece nadir patolojiler de hesaba katılır; mikro-F1 tüm kararları tek havuzda toplar.

F1 değerinin mutlak büyüklüğü, o patolojinin kohortta ne sıklıkta görüldüğüne bağlıdır ve tek başına yorumlanamaz. Bu nedenle her ölçümün yanına bir **rastgele tahmin taban çizgisi** hesaplandı: model kadar bulgu bildiren, ancak bunları hastalara rastgele dağıtan varsayımsal bir sistemin alacağı skor. Anlamlı olan, iki değer arasındaki farktır.

Buna ek olarak iki şans düzeltmeli ölçüt kullanıldı. **MCC** (Matthews korelasyon katsayısı) ve **Cohen kappa**, rastgele uyuşmayı düşerek gerçek ilişkiyi verir. Her ikisinde de 0 şans düzeyi, 1 kusursuz uyum, negatif değerler şanstan kötü performans anlamına gelir. Dengesiz sınıflarda F1'den daha güvenilirdirler.

Güven aralıkları 10.000 tekrarlı bootstrap yöntemiyle, seri/rapor düzeyinde yeniden örnekleme yapılarak hesaplandı. Aynı hastaya ait birden fazla seri bulunuyorsa bu yaklaşım hasta-içi bağımlılığı hesaba katmaz; benzersiz hasta kimlikleri erişilebilir olduğunda hasta-kümeli bootstrap tercih edilmelidir.

Rastgele taban çizgisi, modelin her sınıfta bildirdiği pozitif sayısı korunarak bu pozitiflerin serilere rastgele dağıtılması fikrine dayanır. Yeniden üretilebilir bir teknik ekte permütasyon sayısı, rastgele tohum, sınıf başına uygulama ve macro-F1 toplama kuralı ayrıca kaydedilmelidir. Taban çizgisi farkı için eşli bootstrap ile %95 güven aralığı hesaplanmıştır (10.000 tekrar, tohum 20260910): fark +0,0315 [+0,0104, +0,0520]. Aralık sıfırı içermediği için fark rastlantıya bağlanamaz; büyüklüğünün klinik olarak önemsiz kaldığı ayrıca değerlendirilmelidir.

---

## 3. Ölçüm aracı önce sınandı

Bir modelin düşük skor alması iki nedenden kaynaklanabilir: model gerçekten başarısızdır, ya da ölçüm aracı bozuktur. Bu ikisi ayrılmadan hiçbir sonuç savunulamaz.

### 3.1 Gerçek raporlar üzerinde kalibrasyon

Çıkarım hattı önce **hekim raporlarına** uygulandı ve sonuçları CT-RATE'in resmî etiketleriyle karşılaştırıldı. Bu, modelin ölçümü için ulaşılabilir tavanı verir: hattın gerçek raporlardan çıkaramadığı bir patolojiyi, model raporundan da çıkaramaz.

**Macro-F1 0,885** (%95 güven aralığı 0,867 ile 0,900). On sekiz patolojinin on üçünde değer 0,85'in üzerindedir ve bu alt kümede macro-F1 **0,952**'ye çıkar.

Kalan beş patolojide çıkarım hattı ile CT-RATE etiket tanımı tam örtüşmemektedir: lenfadenopati 0,51 · peribronşiyal kalınlaşma 0,71 · interlobüler septal kalınlaşma 0,71 · kardiyomegali 0,79 · akciğer opasitesi 0,81. Bu karşılaştırma çıkarım hattının dış etiketlerle **uyum/kalibrasyon ölçümüdür**, matematiksel bir performans tavanı değildir. Aynı çıkarım hattı hekim ve model metinlerine farklı dilsel örüntüler nedeniyle farklı hata yapabilir; bu nedenle özellikle bu beş sınıfın model sonuçları ikinci değerlendirme sonuçlarıyla birlikte okunmalıdır.

### 3.2 Bağımsız kör ikinci metin değerlendirmesiyle doğrulama

Yazılımın çıktısına tek başına güvenilmemesi için 30 rapor çifti açık olarak değerlendirildi. Ardından OpenAI Codex adlı yapay zekâ değerlendiricisine 30'u açık örneklemle ortak, 10'u ek olmak üzere 40 vakalık **iki katmanlı kör** bir paket verildi: birinci değerlendiricinin etiketleri paylaşılmadı ve her vakada hangi metnin hekime, hangisinin modele ait olduğu gizlendi. İki metin vaka içinde rastgele sırayla sunuldu. Bu tasarım kaynak bilgisine bağlı önyargıyı azaltır; ancak kör değerlendirici insan veya radyolog olmadığı için sonuç, uzmanlar arası klinik güvenilirlik kanıtı değildir.

| Karşılaştırma | Karar sayısı | Uyum | Kappa |
|---|---:|---:|---:|
| Açık değerlendirme ile kör Codex değerlendirmesi | 1.080 | %99,4 | **+0,979** |
| Açık değerlendirme ile resmî CT-RATE etiketi | 540 | %96,9 | +0,901 |
| Açık değerlendirme ile otomatik çıkarım | 1.080 | %97,3 | +0,901 |
| Kör Codex değerlendirmesi ile otomatik çıkarım | 1.440 | %96,9 | +0,886 |

Açık değerlendirme ile kör Codex değerlendirmesi 30 ortak vakada neredeyse tam örtüşmektedir: bin seksen kararın bin yetmiş dördü aynıdır. Bu yüksek uyum, metinden 18 sınıfı çıkarma kararlarının tekrarlanabilirliğini destekler; iki bağımsız insanın veya iki radyoloğun klinik görüş birliği olarak yorumlanamaz.

Buradaki en önemli kontrol şudur: otomatik hattın kör değerlendiriciyle uyumu **her iki metin türünde de aynıdır** (hekim metinlerinde kappa 0,883, model metinlerinde 0,889). Ölçüm aracı bir metin türü lehine yanlı değildir; modelin aldığı düşük skor ölçüm yanlılığından kaynaklanmamaktadır.

Kalan altı ayrışmanın tamamı tek bir belirsizlik bölgesindedir: nodüler karakterli buzlu cam görünümlerinin "nodül" mü yoksa yalnızca "opasite" mi sayılacağı. Bu örüntü sınıf sınırındaki yorum farkıyla uyumludur; ölçüm hatasının bütünüyle dışlandığı anlamına gelmez.

---

## 4. Modelin başarılı olduğu yönler

Sonuçların olumsuz kısmına geçmeden önce, modelin gerçekten iyi yaptığı şeyleri ayırmak gerekir.

**Dil ve biçim çoğu örnekte inandırıcıdır.** Üretilen raporların önemli bir bölümü beklenen bölüm sırasını, radyoloji üslubunu ve bir sonuç paragrafını taklit eder. Bununla birlikte §5.5'te gösterilen kesilme, anlamsız başlangıç ve biçimlendirme sorunları sık olduğu için bu başarı “kusursuza yakın” olarak değerlendirilmemelidir. Kaynağı insan/model diye ayırt etmeyi ölçen ayrı bir deney yapılmamıştır.

**Bazı marjinal metin özelliklerinin sıklığı benzerdir.** Model, ölçü ve Covid sözü oranlarını hekim raporlarına yakın üretmektedir; önceki tetkike atıf ve ileri tetkik önerisi oranları ise daha belirgin ayrışmaktadır. Bu tablo hasta bazında doğruluk değil, yalnızca kohort düzeyindeki yazım sıklıklarını gösterir.

| Rapor özelliği | Hekim raporları | Model raporları |
|---|---:|---:|
| Sayısal ölçü içeriyor | %57,4 | %57,8 |
| Covid'den söz ediyor | %23,4 | %25,2 |
| Önceki tetkike atıf yapıyor | %10,4 | %7,4 |
| İleri tetkik öneriyor | %29,8 | %40,6 |

**Yayımlanmış metin benzerliği ölçümleri yeniden üretilmiştir.** Modelin geliştiricileri hem ürettikleri 500 raporu hem de değerlendirme betiğini paylaşmıştır. Bu betik, paylaşılan raporlar üzerinde yeniden koşuldu ve BLEU-1, BLEU-2, BLEU-3, BLEU-4 ile sonuç bölümüne karşı BLEU-1 değerlerinin beşinde de fark **0,00** çıktı (BLEU-1 0,3318 · BLEU-4 0,1140 · sonuç bölümü BLEU-1 0,0716).

Bu doğrulamanın kapsamı sınırlıdır ve doğru anlaşılması önemlidir: yeniden üretilen şey **metrik hesabıdır**, üretim hattı değildir. Paylaşılan raporların hangi model varyantı ve checkpoint ile üretildiği bağımsız olarak doğrulanmamıştır. Yani "bildirilen sayılar, bildirilen çıktılardan doğru hesaplanmıştır" denebilir; "bu çıktılar şu model tarafından üretilmiştir" denemez. Her durumda bu ölçütler klinik doğruluğu değil metin örtüşmesini ölçer.

---

## 5. Modelin başarısız olduğu yönler

### 5.1 Bulgular hastayla eşleşmiyor

Üç değerlendirme yolu aynı yönde bulgu vermiştir:

| Yöntem | Kapsam | Macro-F1 | Mikro-F1 | Rastgele taban (macro) |
|---|---:|---:|---:|---:|
| Otomatik çıkarım | 500 vaka | 0,183 | 0,265 | 0,151 |
| Açık değerlendirme | 30 vaka | 0,162 | 0,244 | |
| Kör LLM değerlendirmesi | 40 vaka | 0,217 | 0,265 | 0,139 |

Üç yol da aynı tanımlarla hesaplanmıştır. Macro-F1 her patolojiyi eşit ağırlıklar, mikro-F1 sık patolojilerin baskın olduğu toplam görünümü verir; ikisinin arasındaki fark beklenen yöndedir ve tutarlıdır.

Bu üç sayının bağımsız deney sayılmadığını belirtmek gerekir: aynı rapor çiftlerine ve aynı on sekiz sınıflı şemaya dayanmaktadırlar. Değerleri yan yana koymanın amacı, sonucun ölçüm yoluna göre değişip değişmediğini görmektir.

Otomatik ölçümün %95 güven aralığı 0,158 ile 0,205 arasındadır. Ortalama MCC değeri +0,041'dir; on sekiz patolojinin yalnızca ikisinde MCC 0,10'un üzerine çıkmakta, beşinde ise negatif değer almaktadır.

Patoloji bazında tablo (500 vaka, otomatik çıkarım):

| Patoloji | Hekim | Model | Kesinlik | Duyarlılık | F1 | Rastgele | MCC | Tavan |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Akciğer nodülü | 239 | 228 | 0,52 | 0,50 | 0,51 | 0,47 | +0,08 | 0,95 |
| Akciğer opasitesi | 177 | 270 | 0,40 | 0,62 | 0,49 | 0,43 | +0,11 | 0,81 |
| Koroner duvar kalsifikasyonu | 123 | 66 | 0,32 | 0,17 | 0,22 | 0,17 | +0,07 | 0,95 |
| Atelektazi | 105 | 96 | 0,23 | 0,21 | 0,22 | 0,20 | +0,02 | 0,99 |
| Arteryel duvar kalsifikasyonu | 144 | 59 | 0,37 | 0,15 | 0,22 | 0,17 | +0,07 | 0,97 |
| Konsolidasyon | 93 | 113 | 0,19 | 0,23 | 0,20 | 0,20 | 0,00 | 0,94 |
| Pulmoner fibrotik sekel | 136 | 102 | 0,23 | 0,17 | 0,19 | 0,23 | −0,05 | 0,96 |
| Mozaik atenüasyon | 49 | 40 | 0,20 | 0,16 | 0,18 | 0,09 | +0,10 | 1,00 |
| Bronşektazi | 50 | 47 | 0,17 | 0,16 | 0,16 | 0,10 | +0,08 | 0,95 |
| Tıbbi materyal | 49 | 36 | 0,17 | 0,12 | 0,14 | 0,08 | +0,06 | 0,88 |
| Plevral efüzyon | 48 | 66 | 0,12 | 0,17 | 0,14 | 0,11 | +0,03 | 0,91 |
| Perikardiyal efüzyon | 27 | 19 | 0,16 | 0,11 | 0,13 | 0,04 | +0,09 | 0,90 |
| Kardiyomegali | 40 | 68 | 0,07 | 0,13 | 0,09 | 0,10 | −0,01 | 0,79 |
| Hiatal herni | 77 | 11 | 0,36 | 0,05 | 0,09 | 0,04 | +0,09 | 1,00 |
| İnterlobüler septal kalınlaşma | 38 | 29 | 0,10 | 0,08 | 0,09 | 0,07 | +0,03 | 0,71 |
| Lenfadenopati | 131 | 30 | 0,23 | 0,05 | 0,09 | 0,10 | −0,02 | 0,51 |
| Amfizem | 96 | 29 | 0,17 | 0,05 | 0,08 | 0,09 | −0,01 | 0,98 |
| Peribronşiyal kalınlaşma | 44 | 10 | 0,10 | 0,02 | 0,04 | 0,03 | +0,01 | 0,71 |

En sık görülen patoloji olan akciğer nodülünde bile F1 değeri 0,51'dir ve rastgele tahminin (0,47) çok az üzerindedir. Bunun nedeni nodülün bu kohortta zaten vakaların yaklaşık yarısında bulunmasıdır; yazı tura atmak benzer bir sonuç verirdi.

Kırk vakalık kör altkümede tablo şöyledir: vakaların **on sekizinde model, hekimin tarif ettiği bulguların hiçbirini yakalayamamıştır**. Hiçbir vakada on sekiz patolojinin tamamı doğru bildirilmemiştir. Hekimin tarif ettiği 136 bulgunun 31'i yakalanmış, buna karşılık hekim raporunda karşılığı olmayan 67 bulgu bildirilmiştir.

Bu kırk vakanın seçimi önceden sabitlenmiş ve kaydedilmiştir: otuzu sabit tohumla kohortun tamamından rastgele çekilmiş, onu ise hekim raporunda malignite terimi geçen vakalardan ayrı bir havuzdan alınmıştır. İkinci grup kasten zenginleştirilmiş olduğu için **bu kırk vakadaki oranlar kohort prevalansına genellenemez**; yansız tahminler otuz vakalık rastgele gruptan ve 500 serilik otomatik ölçümden gelir.

### 5.2 Model, hastanın durumundan bağımsız olarak yazıyor

Bu bulgu, düşük hasta-özgü uyum için güçlü destek sağlar; tek başına nedensel açıklama değildir.

| Hekimin tarif ettiği patoloji sayısı | Vaka | Modelin vaka başına bildirdiği bulgu |
|---|---:|---:|
| Hiç yok | 63 | 2,62 |
| Üç veya daha fazla | 281 | 2,81 |

Model, hastanın ne kadar hasta olduğundan bağımsız olarak yaklaşık aynı sayıda bulgu üretmektedir. Tamamen normal olan 63 vakada toplam 165 yanlış bulgu bildirilmiş, yalnızca 8 vakada hiç yanlış bulgu üretilmemiştir.

### 5.3 Verilen ölçüler hastaya ait değil

Model, raporlarında sık sık kesin sayısal ölçüler vermektedir: *"4 cm çapında hipodens lezyon"*, *"asendan aort çapı 38 mm"*, *"en kalın yerinde 12 mm perikardiyal efüzyon"*.

Bu ölçülerin hekim raporundaki ölçülerle uyumu bir permütasyon testiyle sınandı. Hem hekimin hem modelin ölçü verdiği 166 vakada, model ölçülerinin hekim ölçülerine 2 mm içinde yaklaşma oranı **%42,8** çıktı. Raporlar rastgele eşleştirildiğinde aynı oran **%42,1** (aralık %35,5 ile %48,8) oldu. İki değer arasındaki fark istatistiksel olarak ayırt edilememiştir (p = 0,446). En büyük ölçüler arasındaki korelasyon +0,12'dir.

Bu sonuç, kullanılan eşleştirme tanımı altında ölçü uyumunun rastgele rapor eşleştirmesinden ayırt edilemediğini gösterir. Ancak bu özet; ölçülerin anatomik yapı/bulgu bazında nasıl eşleştirildiğini, çoklu ölçülerin nasıl ele alındığını, birim dönüşümünü ve 2 mm eşiğinin gerekçesini içermemektedir. Bu ayrıntılar teknik ekte verilmeden sonuç anatomik lezyon ölçüm doğruluğu olarak yorumlanmamalıdır. Ayrıca 123 vakada hekim hiç ölçü vermemişken model ölçü vermiştir.

Klinik açıdan en riskli davranış budur. Kesin bir sayı, belirsiz bir cümleden çok daha ikna edicidir ve raporu okuyan kişide yanlış bir güven oluşturur.

### 5.4 Model, kapsamı doğrulanmamış ek anatomik yapılar hakkında yazıyor

Model, toraks dışındaki anatomik yapılar hakkında hekim raporlarından daha sık yorum yapmaktadır. Bununla birlikte tiroid, böbrek ve sürrenal bezler çekim kapsamına bağlı olarak toraks BT kesitlerinde kısmen görülebilir. Bu nedenle yalnız söz edilme oranı, bu ifadelerin görüntü alanı dışı veya yanlış olduğunu kanıtlamaz.

| Organ | Hekim raporları | Model raporları |
|---|---:|---:|
| Tiroid | %4,2 | %18,2 |
| Meme | %1,8 | %11,4 |
| Böbrek | %63,2 | %77,4 |
| Sürrenal | %55,6 | %66,8 |
| Beyin ve kafa içi yapılar | %0,2 | %1,4 |

Bir vakada üretilen rapor beyin parankiminin ve kafa içi yapıların normal olduğunu bildirmektedir; standart toraks BT kapsamıyla bağdaşmayan bu örnek güçlü bir anatomik kapsam ihlalidir. Böbrek, sürrenal, meme ve tiroid satırları ise ancak ilgili DICOM serisinin gerçek kraniyokaudal kapsamı kontrol edilerek “görüntü dışı halüsinasyon” olarak sınıflandırılabilir. Mevcut tablo bu yapılar için hasta bazında yanlışlık değil, aşırı söz etme/şablon kullanma sinyali verir.

### 5.5 Metin üretiminde teknik bozulmalar

Raporların %22,6'sı üretim uzunluk sınırına çarparak cümle ortasında kesilmektedir. %12,8'i anlamsız bir *"Find the…"* kalıbıyla başlamakta, %5,4'ü metin içinde biçimlendirme başlığı taşımaktadır. Beş yüz raporda 478 benzersiz metin bulunmakta, bir şablon on üç farklı hastaya birden yazılmaktadır.

### 5.6 Örnek vakalar

Toplu sayılar bir örüntüyü gösterir, ancak hatanın niteliğini tek tek vakalar anlatır. Aşağıdaki dört örnek kohorttan seçilmiştir ve sıklık tahmini değildir; hatanın nasıl bir şey olduğunu göstermek içindir.

**Toraks tomografisinde beyin yorumu.** Hekim raporu her iki akciğerde konfluan pnömonik konsolidasyon alanları, endobronşiyal yayılım gösteren tomurcuklanmış ağaç görünümü ve alt loblarda silindirik bronşektazi tarif etmektedir. Modelin raporu şöyle başlamaktadır:

> *"Paraffirmary glands shadow, exophytic brain parenchyma and intracranial structures are normal."*

İlk sözcük hiçbir anatomik karşılığı olmayan uydurma bir terimdir; beyin parankimi ve kafa içi yapılar ise toraks tomografisi kapsamında değildir. Benzer şekilde beyin veya kafa içi yapılardan söz eden beş rapor bulunmaktadır.

**Tümüyle normal bir tetkike meme kanseri değerlendirmesi.** Hekim raporunun sonuç bölümü tek cümledir: *"Examination within normal limits"*. Model aynı seri için sağ memede bir centimetrelik protez ucu, bilateral retroareolar alanda jinekomasti ile uyumlu nodüler oluşum, kayıcı tip hiatal herni ve iki taraflı subsegmental atelektazi bildirmiş, sonuç bölümünü ise şöyle yazmıştır:

> *"There was no finding in favor of breast cancer in both breasts."*

Toraks tomografisi meme kanseri değerlendirmesi için yapılmamıştır ve hekim raporunda memeye dair hiçbir ifade yoktur.

**Ayak hastalıkları ve uydurma anatomi.** Hekim raporu geçirilmiş tüberküloz sekeli, torasik aortada hafif çap artışı ve sol sürrenal adenom tarif etmektedir. Modelin raporu yarım bir sözcükle başlamakta ve şu cümleleri içermektedir:

> *"ple. and are rare in the subcavian region. There is a triangular hypodense selection in the subcavian area. […] It is a benefit in terms of internal podology."*

*"Subcavian"* diye bir anatomik bölge yoktur (subklavyen bozulmuş olmalıdır) ve podoloji ayak hastalıklarıyla ilgilenen bir alandır; toraks tomografisiyle hiçbir ilişkisi bulunmamaktadır.

**Nörolojik muayene yorumu.** Hekim raporu her iki akciğerde nodüller, minimal amfizematöz değişiklikler, aortada ateroskleroz, pulmoner arter çapında artış ve hiatal herni tarif etmektedir. Model raporunda şu cümle geçmektedir:

> *"Brain, behavioral and neurological examination are largely uncorrelated."*

Bu cümle bir görüntüleme bulgusu değildir, bir tomografi raporunda karşılığı yoktur ve hastaya dair hiçbir bilgi taşımamaktadır.

Bu örneklerin ortak özelliği, hatanın **rastgele gürültü gibi görünmemesidir**. Cümleler dilbilgisel olarak düzgün, üslup olarak radyolojiktir ve bir rapor içinde doğal biçimde akmaktadır. Metni dikkatle okumayan biri için bu ifadeler diğer cümlelerden ayırt edilemez.

---

## 6. Malignite tespiti

Çalışmanın en kritik sorusu buydu, çünkü otomatik rapor üretiminin klinik değeri büyük ölçüde kanser şüphesini yakalayabilmesine bağlıdır.

### 6.1 Kohortta malignite ne sıklıkta geçiyor

Beş yüz hekim raporunun **25'inde (%5,0)** akciğerde bir malignite tarif edilmektedir: kitle, tümör, metastaz, karsinom veya eşdeğeri bir ifade, olumsuzlanmamış biçimde ve toraks anatomisine bağlı olarak. Şüpheli morfoloji (spiküle, düzensiz konturlu, lobüle, kaviter) 38 raporda (%7,6) geçmektedir.

Daha geniş tanımlı "nodül veya malignite" ise raporların **%53,2'sinde** bulunmaktadır. Bu iki oran arasındaki fark önemlidir: nodül bu kohortta sık ve çoğunlukla iyi huyludur, malignite ise seyrektir. Seyrek bir olayı yakalamak, sık bir olayı yakalamaktan çok daha zordur ve bu, aşağıdaki sayıların yorumlanmasında belirleyicidir.

### 6.2 Model ne kadarını doğru, ne kadarını yanlış yakalıyor

> **Ölçüt düzeltmesi.** Malignite ölçütü ilk kurulumda bir kara liste kullanıyordu: karaciğer, tiroid gibi bilinen toraks dışı yapılar eleniyordu. Anatomi sözlüğünde hiç bulunmayan yapılar (vokal kord, prostat) ise boş bağlam ürettiği için elenmiyordu. Ölçüt beyaz listeye çevrilmiştir: malignite ifadesinin cümlesinde pulmoner bir anatomi bulunması zorunludur. Aşağıdaki iki malignite satırı bu düzeltilmiş ölçütle yeniden hesaplanmıştır; hüküm değişmemiş, sayılar değişmiştir. Şüpheli morfoloji ve "nodül veya malignite" satırları ilk tanımla hesaplanmış olup aynı çekince onlar için de geçerlidir.

| Ölçülen | Prevalans | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|
| Pulmoner malignite | %5,0 | **2** | 20 | **23** | 455 |
| Torasik malignite | %6,8 | 2 | 27 | 32 | 439 |
| Şüpheli morfoloji | %7,6 | 5 | 46 | 33 | 416 |
| Nodül veya malignite | %53,2 | 139 | 107 | 127 | 127 |

Tablodaki dört hücre şu anlama gelir. **TP**, hekimin de modelin de bulguyu bildirdiği vaka sayısıdır. **FN**, hekimin bildirdiği ama modelin kaçırdığı vakadır: klinik olarak en tehlikeli hata, çünkü hasta gözden kaçar. **FP**, hekimin bildirmediği ama modelin uydurduğu vakadır: gereksiz tetkike ve hasta kaygısına yol açar. **TN**, ikisinin de bulgu bildirmediği vakadır.

Pulmoner malignite satırı okunduğunda tablo şudur: model, hekimin akciğerde malignite tarif ettiği **25 vakanın 23'ünü kaçırmış**, buna karşılık malignite olmayan **20 vakaya malignite yazmıştır**. Modelin ürettiği 22 bildirimin yalnızca 2'si doğrudur.

| Ölçülen | Duyarlılık | Özgüllük | Kappa | Youden J |
|---|---|---|---|---:|
| Pulmoner malignite | 0,080 [0,022–0,250] | 0,958 | +0,040 [−0,050, +0,168] | +0,038 |
| Torasik malignite | 0,059 [0,016–0,191] | 0,942 | +0,001 [−0,069, +0,097] | +0,001 |
| Şüpheli morfoloji | 0,132 [0,058–0,273] | 0,900 [0,870–0,925] | +0,028 [−0,061, +0,128] | +0,032 |
| Nodül veya malignite | 0,523 [0,463–0,582] | 0,543 [0,479–0,605] | +0,065 [−0,023, +0,155] | +0,065 |

Köşeli parantez içindekiler %95 güven aralıklarıdır. Kappa, şans eseri uyuşmayı düşerek gerçek ilişkiyi verir. **Youden J** duyarlılık ile özgüllüğü tek sayıda birleştirir (`duyarlılık + özgüllük − 1`) ve yazı tura atan bir sistemi tam sıfıra sabitler; ayrı ayrı bakıldığında yanıltıcı olabilen bu iki değeri birlikte değerlendirmeyi sağlar.

Dört göstergenin de kappa güven aralığı **sıfırı içermektedir**. Bu nedenle savunulabilir hüküm şudur: gözlenen uyum şans düzeyinden ayırt edilememiştir. "Tam olarak sıfır bilgi" gibi kesin bir eşdeğerlik iddiası bu örneklem büyüklüğüyle kurulamaz, ancak kullanılabilir bir ayırt etme gücü de gösterilememiştir.

Yüksek özgüllük değeri (0,958) yanıltıcıdır ve dikkatle okunmalıdır. Pulmoner malignite bu kohortta yalnızca %5,0 oranında görüldüğü için, "çoğu vakada malignite deme" davranışı kendiliğinden yüksek özgüllük üretir. Nitekim Youden J değeri +0,038'dir: duyarlılık ve özgüllük birlikte değerlendirildiğinde ayırt etme gücü kalmamaktadır.

"Nodül veya malignite" bileşiminde duyarlılık 0,523, özgüllük 0,543'tür. Bu, yazı tura atmakla aynı bilgi düzeyidir; nitekim Youden J yalnızca +0,065'tir ve kappa aralığı sıfırı içermektedir.

Kör değerlendirici, kaynakları bilmeden aynı yönde sonuç vermiştir. Kırk vakanın malignite düzeyi karşılaştırıldığında yalnızca 21'inde iki rapor aynı düzeyi vermiştir. Hekimin açıkça malignite tarif ettiği iki vakanın ikisinde de model raporu malignite içermemiş, buna karşılık hekimin hiçbir şey görmediği yedi vakada model bir lezyondan söz etmiştir. Bu altküme kasten malignite açısından zenginleştirildiği için (§2) sayılar kohort prevalansına genellenemez; tanımlayıcı bir sağlamlık kontrolüdür.

Okunan vakalardan üç örnek durumu açıkça göstermektedir:

> Hekim, opere böbrek kanseri olan bir hastada sağ akciğeri neredeyse tamamen dolduran, mediastene uzanan, sağ ana bronşu tıkayan ve göğüs duvarına yayılan metastatik kitleleri tarif etmiştir. Model aynı görüntü için *"Covid-19 pnömonisi ile uyumlu bulgular"* yazmıştır.

> Over kanseri takibindeki bir hastada hekim, kalp çevresinde boyutu belirgin şekilde artmış metastatik lenf nodlarını bildirmiştir. Model yalnızca dalak hakkında yazmıştır.

> Hekimin üç ayrı akciğer nodülü tarif ettiği bir vakada model *"Toraks BT incelemesi normal sınırlarda"* sonucuna varmıştır.

Bu örnekler önceden oluşturulmuş kör altkümeden seçilmiş açıklayıcı vakalardır; tek başlarına sıklık tahmini değildir. Kohort genelindeki kaçırma örüntüsü, örneklerden değil 500 serilik toplu ölçümlerden değerlendirilmelidir.

---

## 7. Alternatif açıklamalar sınandı

Düşük skorun rapor uzunluğu, metin tekrarı veya rapordaki bulgu yüküyle açıklanıp açıklanmadığı üç katmanlı çözümlemeyle sınandı. Bunlar olası bazı karıştırıcıları ele alır; yanlış görüntü–rapor eşleşmesi, model/checkpoint seçimi veya çıkarım yapılandırması gibi bütün alternatifleri dışlamaz.

| Katman | Vaka | Macro-F1 | Rastgele taban | Fark |
|---|---:|---:|---:|---:|
| Uzunluk sınırında kesilen raporlar | 113 | 0,227 | 0,156 | +0,071 |
| Tam biten raporlar | 387 | 0,167 | 0,148 | +0,020 |
| Benzersiz metin üretilen vakalar | 470 | 0,189 | 0,155 | +0,034 |
| Tekrar eden şablon yazılan vakalar | 30 | 0,034 | 0,044 | −0,010 |
| Hekim bir veya iki patoloji tarif etmiş | 156 | 0,107 | 0,091 | +0,016 |
| Hekim üç veya daha fazla tarif etmiş | 281 | 0,211 | 0,186 | +0,025 |

**Üretim uzunluk sınırı tek başına açıklayıcı görünmemektedir.** Kesilen raporlar, tam biten raporlardan daha yüksek skor almaktadır. Kesilen kuyrukta kaybolan bulguların genel düşük uyumun ana nedeni olduğu varsayımı desteklenmemiştir.

**Şablon tekrarı genel sonucu tek başına açıklamamaktadır.** Aynı metnin birden fazla hastaya yazıldığı vakalarda skor rastgele tahminin altına düşmektedir, ancak bu yalnızca otuz vakayı etkilemektedir.

**Rapor bulgu yükü belirgin bir açıklama sağlamamaktadır.** F1 değeri hekim raporundaki bulgu sayısıyla birlikte yükselmekte, ancak rastgele taban da yükselmektedir. Şansın üzerindeki pay iki katmanda da küçük ve birbirine yakındır. Patoloji sayısı klinik vaka zorluğunun tam bir ölçüsü olmadığı için burada “vaka zorluğu” yerine “rapor bulgu yükü” terimi kullanılmıştır.

---

## 8. Bu sonuçlar nasıl açıklanır

Yüksek metin benzerliği ile şans düzeyinde klinik uyumun bir arada bulunması bir çelişki değildir. İkisi birlikte tek bir açıklamaya işaret eder.

Model, radyoloji raporlarının **istatistiksel yapısını** öğrenmiştir. Hangi cümlelerin hangi sıklıkta, hangi sırayla ve hangi üslupla yazıldığını bilmektedir. Bu bilgiyle, gerçek bir rapordan ayırt edilmesi güç metinler üretebilmektedir.

Ancak bu metinleri üretirken önündeki görüntüden yeterince yararlanamamaktadır. Ürettiği rapor, o hastanın tomografisinden çok, eğitim verisindeki raporların ortalamasına benzemektedir.

Bu yorumu üç ölçüm birlikte desteklemektedir: bildirilen bulgu sayısının hastanın durumundan bağımsız olması, verilen ölçülerin gerçek ölçülerle permütasyon testinde ilişkisiz çıkması, ve cümle dağılımlarının gerçek korpusla neredeyse tam örtüşmesi.

---

## 9. Değerlendirme

BTB3D, radyoloji raporu **yazmayı** öğrenmiş, ancak tomografi **okumayı** öğrenememiş bir sistemdir.

Ürettiği metinlerin dilsel kalitesi yüksektir ve bu, teknik olarak kayda değer bir başarıdır. Ancak bir radyoloji raporunun değeri dilinden değil doğruluğundan gelir. Bu ölçüte göre model, mevcut haliyle klinik kullanıma uygun değildir.

Daha önemlisi, sistemin başarısızlık biçimi risklidir. Model, açıkça hatalı görünen metinler üretmemektedir. Aksine inandırıcı, ayrıntılı, sayısal ölçüler içeren ve profesyonel görünen raporlar üretmektedir. Bu tür bir hata, gözden kaçması en kolay hata türüdür. Kanserli bir hastanın raporunda pnömoni tarif edilmesi, okuyan kişiye yanlış geldiğini gösteren hiçbir sinyal vermez.

Bu nedenle, bu tür modellerin değerlendirilmesinde metin benzerliği ölçütlerinin tek başına kullanılmaması gerektiği sonucuna varılmıştır. Bu ölçütler doğru hesaplanabilir ve yine de klinik geçerlilik konusunda yanıltıcı olabilir. Bulgu düzeyinde çalışan, olumsuzlamayı ayırt eden ve rastgele taban çizgisiyle karşılaştırılan değerlendirmeler zorunludur.

---

## 10. Çalışmanın sınırları

**Referans, görüntü değil rapordur.** Karşılaştırma model raporu ile hekim raporu arasında yapılmıştır. Hekimin yazmadığı bir bulgu burada "yok" sayılmıştır. Ölçülen büyüklük rapor uyumudur, görüntüden tanı doğruluğu değildir.

**Referans etiketler de otomatik türetilmiştir.** CT-RATE'in resmî patoloji etiketleri hekim raporlarından bir dil modeliyle çıkarılmıştır ve altın standart değildir.

**Beş patolojide ölçüm aracının tavanı düşüktür** (0,51 ile 0,81 arasında). Bu sınıfların sonuçları kendi tavanlarıyla birlikte okunmalıdır.

**İnsan okuması kırk vakayla sınırlıdır.** Beş yüz vakalık ölçüm otomatik çıkarıma dayanmaktadır. İnsan okumaları bu ölçümü doğrulamak içindir, yerine geçmez.

**Kör değerlendirici radyolog değildir.** Rapor metninden bulgu çıkarma görevinde iki bağımsız okuyucunun kappa 0,979 düzeyinde uyuşması bu görev için yeterli güvenilirlik göstergesidir. Ancak görüntüden tanı geçerliliğine ilişkin bir yargı için radyolog onayı gereklidir.

**Sonuçlar bu veri kümesine özgüdür.** Farklı bir kohortta, özellikle modelin eğitim verisine daha yakın bir dağılımda, farklı sonuçlar elde edilebilir.
