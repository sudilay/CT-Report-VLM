# SPECTRE, M3D-CLIP ve MG-3D modellerinin göğüs BT verilerinde karşılaştırılması

Bu çalışmada üç 3B BT temel modeli, SPECTRE-Large, M3D-CLIP ve MG-3D Swin-B, iki göğüs BT veri kümesinde
karşılaştırıldı: CT-RATE (491 seri) ve BIMCV-R (317 seri). Amaç, Sybil'in kaçırdığı akciğer nodülü ve
kanser vakalarını tamamlamaya en uygun hacim temsilini üreten modeli bulmaktı.

Her modelden BT hacmi için tek bir embedding vektörü alındı. Bu vektörün iki şeyi ne kadar iyi taşıdığı
ölçüldü: raporda geçen bulguları ayırmak ve taramayı kendi raporuyla eşleştirmek. Lezyon tespiti,
lokalizasyon ya da segmentasyon ölçülmedi. Bu nedenle sonuçlar, modellerin anatomiyi ne kadar doğru
temsil ettiğini değil, genel amaçlı bir hacim temsili olarak ne kadar işe yaradıklarını gösterir.

## 1. Temel bulgular

- En iyi genel hacim temsili SPECTRE'de. CT-RATE'te 18 bulgunun ortalamasında Macro-AUC SPECTRE
  `0,787`, MG-3D `0,645`, M3D `0,620`. BIMCV-R'de SPECTRE `0,622`, M3D `0,551`, MG-3D `0,528`. Farklar
  büyük ve görüntüsü sorunlu seriler çıkarıldığında da korunuyor.
- Tarama ile raporu eşleştirmede SPECTRE çok önde. CT-RATE'te bir taramanın doğru raporu SPECTRE'de
  vakaların %37'sinde ilk 10 aday arasında; M3D'de %2,6'sında. Bu güçlü bir araştırma sinyali, ama
  klinik kullanım düzeyinde değil.
- Akciğer nodülünde başarı orta-zayıf. CT-RATE'te SPECTRE'nin nodül AUC'si `0,659`, diğer iki model
  `0,575`; özgüllük %90'da tutulduğunda SPECTRE nodüllerin yalnız %25'ini yakalıyor. BIMCV'de SPECTRE ile
  M3D arasında fark yok (`0,576` ve `0,573`).
- Sybil'e ek katman olarak SPECTRE umut veriyor, ama kanıt henüz zayıf. Sybil'in alarm vermediği
  BIMCV serilerinde SPECTRE'ye Sybil kadar ek alarm hakkı verildiğinde, kaçan 74 rapor-nodülünden 8'ini
  öne çıkardı; rastgele seçimde beklenen 3,9. Bunun bedeli alarm sayısının iki katına çıkması. Üç model
  için yapılan düzeltmeden sonra birincil analizde sonuç anlamlı değil. M3D'ye üstünlüğü de gösterilemedi.
- Kanserin kaçırılması konusunda bu verilerle sonuç çıkarılamaz. Raporunda akciğer parankiminde
  malignite bulgusu olan 13 vakanın 9'unu Sybil kaçırıyor; SPECTRE bunlardan 16 ek alarmla yalnız 1'ini
  yakalıyor. Patoloji ya da yeterli kanser sonlanımı yok.
- BIMCV-R'de ciddi veri sorunları var. Resmî listenin %17,7'sinde görüntü ile rapor eşleşmiyor.
  Kimliği doğru 317 serinin 55'inde görüntü geometrisi bozuk, 6'sı göğüs taraması değil.

## 2. Veri ve yöntem

### 2.1 Kohortlar

| Veri kümesi | Seri | Hasta | Bulgu | Açıklama |
|---|---:|---:|---:|---|
| CT-RATE | 491 | 426 | 18 | 500 serilik örneklemden resmî göğüs dışı listesindeki 9 seri çıkarıldı |
| BIMCV-R | 317 | 315 | 25 | 500 serilik örneklemin görüntü-rapor kimliği doğrulanan kısmı |
| BIMCV-R, temiz alt küme | 256 | 254 | 25 | 317 seriden görüntüsü sorunlu 61 seri çıkarıldı (duyarlılık analizi) |

BIMCV-R'de kimlik şu kuralla doğrulandı: dosya adındaki `sub-S…` ve `ses-E…` değerleri metadata'daki
`PatientID` ve `ReportID` ile aynı olmalı. 500 serinin 317'si bu kurala uyuyor.

### 2.2 Embeddingler

- M3D-CLIP ve MG-3D Swin-B: Hugging Face sonuç paketlerindeki görüntü embeddingleri kullanıldı
  (bölüm 11).
- SPECTRE-Large: Embeddingler bu çalışmada çıkarıldı. Taramalar RAS yönelimine çevrildi, HU değerleri
  [-1000, 1000] aralığından [0, 1]'e ölçeklendi, 0,5×0,5×1,0 mm'ye yeniden örneklendi ve 128×128×64'lük
  parçalara bölündü. Özellik birleştiricinin CLS vektörü sınıflandırmada, SigLIP görüntü projeksiyonu
  eşleştirmede kullanıldı. Yeniden örneklemenin doğruluğu her seride ölçüldü (bölüm 3.1).

### 2.3 Değerlendirme

- Sınıflandırıcı: Her bulgu için dondurulmuş embedding üzerinde lineer sınıflandırıcı
  (`StandardScaler` ve `LogisticRegression(C=1, class_weight="balanced")`).
- Çapraz doğrulama: Beş katlı, hasta gruplu. Üç model aynı donmuş kat dosyasını kullandı; hiçbir
  hasta aynı bulgu ve tohumda iki kata düşmüyor. Beş farklı kat bölünmesi (tohum) yapıldı ve sonuçların
  ortalaması raporlandı.
- Güven aralıkları: %95 güven aralığı (GA), kat dışı tahminler üzerinde 2.000 kez hasta-kümeli
  bootstrap ile hesaplandı. Model farkları aynı bootstrap örneklemiyle eşleştirildi. Sınıflandırıcı her
  bootstrap örnekleminde yeniden eğitilmedi. Bu yüzden GA'lar hasta örnekleme belirsizliğini kapsıyor,
  sınıflandırıcı eğitiminden gelen belirsizliği tam kapsamıyor. Büyük farkları etkilemesi beklenmez;
  sınırdaki p değerleri temkinle okunmalı.
- Çoklu karşılaştırma: Bulgu bazındaki farklara Holm düzeltmesi uygulandı. Akciğer nodülü önceden
  belirlenmiş birincil bulgu olduğu için ayrıca iki karşılaştırmalık Bonferroni düzeltmesiyle
  değerlendirildi.
- Duyarlılık analizi: Sınıflandırıcı temiz 256 seriyle yeniden eğitildi. Bu alt küme aynı kohortun
  parçasıdır, bağımsız bir doğrulama kümesi değildir.

AUC nedir? Rastgele seçilmiş pozitif bir serinin, rastgele seçilmiş negatif bir seriden daha yüksek
skor alma olasılığıdır. `0,50` rastgele sıralama, `1,00` kusursuz sıralamadır; doğruluk ya da duyarlılık
yüzdesi değildir. Macro-AUC her bulgunun AUC'sine eşit ağırlık verir ve bu raporun ana ölçütüdür.
Micro-AUC bütün seri-bulgu çiftlerini tek havuzda toplar.

Tarama-rapor eşleştirmesi (retrieval) nasıl ölçüldü? Model hem taramaları hem raporları aynı vektör
uzayına yerleştiriyor. Bu uzayda iki yönde arama yapıldı:

- Görüntüden rapora (I2T, image-to-text): Bir tarama sorgu olarak verilir ve bütün raporlar
  benzerliğe göre sıralanır. Soru: bu taramanın kendi raporu listenin kaçıncı sırasında?
- Rapordan görüntüye (T2I, text-to-image): Bir rapor sorgu olarak verilir ve bütün taramalar
  sıralanır. Soru: bu raporun ait olduğu tarama kaçıncı sırada?

R@10, doğru eşin ilk 10 aday içinde bulunduğu sorguların oranıdır. MedR, doğru eşin medyan sırasıdır;
düşük olması iyidir. CT-RATE'te her çalışmadan bir seri alındı (460 aday), BIMCV'de 317 aday var. Aday
havuzu sabit tutuldu, GA için yalnız sorgular yeniden örneklendi. MG-3D paketinde görüntüyle aynı uzaya
yerleştirilmiş metin embeddingi olmadığı için MG-3D bu analize alınamadı.

### 2.4 Karşılaştırmanın eşitliği

Karşılaştırma sınıflandırıcı düzeyinde kontrollü: aynı kohort, aynı katlar, aynı sınıflandırıcı ve hasta
sızıntısı yok. CT-RATE'te üç model aynı HU dönüşümünü kullandı. Ancak uçtan uca tam eşdeğer değil:

- SPECTRE embeddingleri bu çalışmada, ön işlemesi doğrulanarak üretildi. M3D ve MG-3D embeddingleri hazır
  paketlerden alındı.
- MG-3D'de başlığı bozuk 33 BIMCV serisi yanlış z aralığıyla işlenmiş; ağırlıklar `strict=False` ile
  yüklenmiş ve yükleme günlüğü yok.
- Ön-eğitim verileri farklı. SPECTRE ve MG-3D CT-RATE'in eğitim kısmını, SPECTRE ayrıca NLST'yi görmüş;
  M3D bu verileri görmemiş. BIMCV üç model için de ön-eğitim dışı.
- MG-3D tarama-rapor eşleştirmesinde karşılaştırılamıyor.

Model sıralaması temiz BIMCV alt kümesinde ve ön-eğitim dışı olan BIMCV'de de korunuyor. Bu yüzden bu
eşitsizlikler SPECTRE'nin genel temsildeki üstünlüğünü açıklamaya yetmiyor.

## 3. Ön işleme ve veri kontrolleri

### 3.1 SPECTRE ön işlemesinin doğrulanması

spectre-fm 0.2.1 kütüphanesinin yeniden örnekleme fonksiyonu voksel boyutunu MONAI'ye `affine=`
argümanıyla veriyor. MONAI 0.9'dan beri bu argüman kullanılmıyor; tarama 1 mm izotrop kabul ediliyor ve
model yanlış ölçekte, kaymış bir görüntü görüyor. Loglarda yalnız "Argument affine has been deprecated"
uyarısı çıkıyor. Bu çalışmada voksel boyutu `MetaTensor` üzerinden verildi. Hata spectre-fm'in sonraki
sürümünde de bu şekilde düzeltilmiş.

Ön işlemenin doğruluğu üç yolla ölçüldü:

- Sentetik küp testi: Bilinen konuma konmuş bir küp yeniden örnekleme sonrası 0,2 mm hatayla doğru
  yerde ve tam hacimde çıktı. Kütüphanenin kendi yolunda 29 mm kaydı.
- Geri-korelasyon: Modelin gördüğü hacim, girdi ızgarasına geri indirilip girdiyle karşılaştırıldı.
  Doğru örneklemede yaklaşık 0,99, hatalı örneklemede 0'a yakın değer çıkıyor.
- Görsel kontrol: Beş seride aksiyel, koronal ve sagittal orta kesitlerde modelin gördüğü görüntü
  taramanın kendisiyle örtüşüyor.

| Kontrol | CT-RATE 500 | BIMCV 317 |
|---|---:|---:|
| Kontrolden kalan seri (RAS, boyut hatası < %3, geri-korelasyon ≥ 0,90, boş parça ≤ %90) | 0 | 0 |
| Geri-korelasyon, en düşük / medyan | 0,973 / 0,998 | 0,937 / 0,997 |
| Boş parça oranı, medyan / en yüksek | 0,048 / 0,450 | 0,087 / 0,522 |
| Birebir aynı embedding | 0 | 0 |
| Kosinüs benzerliği 0,9999'u aşan embedding çifti | 0 | 0 |
| Embedding çeşitliliği (etkin boyut) | 10,3 | 10,2 |

### 3.2 BIMCV-R veri sorunları

BIMCV-R'de sonuçları etkileyen dört ayrı veri sorunu bulundu. Sorunlar veri kümesinin kendisinde; bu
çalışmanın işleme adımlarından kaynaklanmıyor.

| Sorun | Kapsam | Nasıl bulundu | Bu çalışmada ne yapıldı |
|---|---|---|---|
| Görüntü ile rapor eşleşmiyor | Resmî `BIMCV-R.csv`'de 7.518 satırın 1.332'si (%17,7); 500 serilik örneklemde 183 seri | Dosya adındaki `sub-S…`/`ses-E…` ile satırdaki `PatientID`/`ReportID` karşılaştırıldı. Örneklemdeki röntgen raporuna benzeyen 33 raporun 30'u bu seriler arasında | 183 seri analizden çıkarıldı |
| NIfTI başlığı bozuk | 317 serinin 38'i (500 serinin 56'sı) | 33 seride kesit kalınlığı yerine toplam görüş alanı (180-370 mm), 5 seride bozuk sform. Başlık onarılınca voksel boyutu düzeliyor, eksen yönü yanlış kalıyor: aksiyel kesit yerine koronal ya da sagittal görüntü | Birincil analizde tutuldu, duyarlılık analizinde çıkarıldı |
| Görüntü geometrisi tutarsız | 317 serinin 17'si | Başlık normal görünüyor, ama aksiyel kesit boş ve diğer düzlemlerde şerit artefaktı var; 16'sı `acq-2` yeniden yapılandırma serisi | Birincil analizde tutuldu, duyarlılık analizinde çıkarıldı |
| Göğüs dışı seri | 317 serinin 6'sı | `bp-chest` etiketli olduğu hâlde kafa (3), bacak (2) ve el (1) taraması; 3'ünün raporunda nodül geçiyor | Birincil analizde tutuldu, duyarlılık analizinde çıkarıldı |

- Kimliği doğru 317 serinin 55'inde geometri sorunu var, 6'sı yanlış vücut bölgesi. Toplam 61 seri bu
  karşılaştırma için güvenilir değil.
- Başlığı bozuk 38 seri, görsel incelemede saptanan serilerle birebir aynı küme; bu grup başlık
  bilgisiyle doğrulandı. Diğer iki grup yalnız görsel incelemeye dayanıyor. İncelemeyi tek okuyucu
  körleme olmadan yaptı; ikinci okuyucu ya da uyuşmazlık çözümü yok.
- NIfTI başlığını okuyan bütün modeller bu serileri aynı biçimde gördü. Başlığı bozuk serilerin doğru
  eksen yönü ham DICOM olmadan güvenilir biçimde kurulamayacağı için bu seriler düzeltilmedi.
- Seri listesi: `outputs/vlm33/bimcv317_gorsel_kalite.csv`.

## 4. CT-RATE sonuçları

### 4.1 Genel bulgu temsili (491 seri, 18 bulgu)

| Model | Macro-AUC [%95 GA] | Micro-AUC [%95 GA] | Macro-AP |
|---|---:|---:|---:|
| SPECTRE-Large | **0,787 [0,773; 0,801]** | **0,825 [0,813; 0,836]** | **0,458** |
| MG-3D Swin-B | 0,645 [0,624; 0,664] | 0,694 [0,678; 0,710] | 0,287 |
| M3D-CLIP | 0,620 [0,599; 0,643] | 0,680 [0,664; 0,696] | 0,278 |

| Eşleştirilmiş fark | ΔMacro-AUC [%95 GA] | ΔMicro-AUC [%95 GA] |
|---|---:|---:|
| SPECTRE − MG-3D | +0,143 [0,122; 0,163] | +0,131 [0,116; 0,147] |
| SPECTRE − M3D | +0,168 [0,144; 0,191] | +0,145 [0,128; 0,162] |
| MG-3D − M3D | +0,025 [0,003; 0,047] | +0,014 [−0,004; 0,032] |

SPECTRE'nin farkı iki modele karşı da büyük ve kesin. MG-3D ile M3D arasındaki fark küçük ve sınırda.

### 4.2 Bulgu bazında

`*` Holm düzeltmesi sonrası p < 0,05. Satırlar SPECTRE AUC'sine göre sıralı.

| Bulgu | Pozitif | SPECTRE | MG-3D | M3D | SPECTRE − MG-3D [%95 GA] | SPECTRE − M3D [%95 GA] |
|---|---:|---:|---:|---:|---:|---:|
| Plevral efüzyon | 47 | 0,969 | 0,820 | 0,802 | +0,150 [0,083; 0,219]* | +0,167 [0,097; 0,244]* |
| Arter duvarı kalsifikasyonu | 142 | 0,910 | 0,676 | 0,686 | +0,234 [0,185; 0,284]* | +0,224 [0,168; 0,282]* |
| Koroner arter duvarı kalsifikasyonu | 121 | 0,872 | 0,691 | 0,653 | +0,181 [0,127; 0,238]* | +0,220 [0,159; 0,280]* |
| Kardiyomegali | 37 | 0,871 | 0,776 | 0,692 | +0,095 [0,013; 0,184] | +0,179 [0,101; 0,263]* |
| Konsolidasyon | 93 | 0,864 | 0,615 | 0,595 | +0,250 [0,177; 0,327]* | +0,269 [0,197; 0,346]* |
| İnterlobüler septal kalınlaşma | 38 | 0,853 | 0,700 | 0,583 | +0,153 [0,063; 0,246]* | +0,270 [0,164; 0,373]* |
| Perikardiyal efüzyon | 26 | 0,848 | 0,731 | 0,675 | +0,117 [0,005; 0,211] | +0,173 [0,036; 0,292] |
| Akciğer opasitesi | 177 | 0,845 | 0,566 | 0,529 | +0,279 [0,219; 0,339]* | +0,316 [0,255; 0,374]* |
| Tıbbi materyal | 46 | 0,824 | 0,572 | 0,675 | +0,252 [0,143; 0,350]* | +0,149 [0,068; 0,229]* |
| Amfizem | 95 | 0,785 | 0,650 | 0,550 | +0,136 [0,064; 0,204]* | +0,235 [0,157; 0,308]* |
| Mozaik atenüasyon | 47 | 0,775 | 0,794 | 0,782 | −0,020 [−0,104; 0,061] | −0,008 [−0,090; 0,074] |
| Bronşektazi | 50 | 0,740 | 0,593 | 0,555 | +0,147 [0,049; 0,252] | +0,185 [0,083; 0,289]* |
| Peribronşiyal kalınlaşma | 44 | 0,730 | 0,582 | 0,493 | +0,148 [0,057; 0,247] | +0,237 [0,115; 0,351]* |
| Pulmoner fibrotik sekel | 134 | 0,724 | 0,570 | 0,564 | +0,154 [0,084; 0,220]* | +0,160 [0,097; 0,226]* |
| Akciğer nodülü | 235 | 0,659 | 0,575 | 0,574 | +0,085 [0,020; 0,149] | +0,085 [0,017; 0,147] |
| Atelektazi | 103 | 0,653 | 0,515 | 0,611 | +0,138 [0,068; 0,210]* | +0,041 [−0,037; 0,120] |
| Hiatal herni | 77 | 0,635 | 0,607 | 0,564 | +0,028 [−0,052; 0,108] | +0,071 [−0,020; 0,156] |
| Lenfadenopati | 126 | 0,611 | 0,571 | 0,568 | +0,040 [−0,039; 0,118] | +0,042 [−0,024; 0,110] |

- SPECTRE 18 bulgunun 9'unda iki modelden de, 3'ünde yalnız M3D'den, 1'inde yalnız MG-3D'den düzeltme
  sonrası anlamlı olarak iyi. Başka bir modelin SPECTRE'yi geçtiği bulgu yok.
- SPECTRE'nin en güçlü olduğu bulgular hacmin geniş bölümüne yayılan değişiklikler: plevral efüzyon
  0,97, arter kalsifikasyonu 0,91, konsolidasyon 0,86.
- Küçük ve odak bulgularda (nodül, lenfadenopati, hiatal herni) üç model de zayıf. Bütün hacmi tek
  vektöre indiren bir temsilin küçük lezyonları taşımakta zorlanması beklenen bir sınır.

### 4.3 Akciğer nodülü

| Model | AUC [%95 GA] | Duyarlılık, özgüllük %90'da | Özgüllük, duyarlılık %80'de |
|---|---:|---:|---:|
| SPECTRE-Large | **0,659 [0,609; 0,705]** | **%25,4** | **%41,6** |
| MG-3D Swin-B | 0,575 [0,528; 0,620] | %14,4 | %27,7 |
| M3D-CLIP | 0,574 [0,526; 0,624] | %13,5 | %29,8 |

SPECTRE'nin farkı MG-3D'ye karşı `+0,085 [0,020; 0,149]`, M3D'ye karşı `+0,085 [0,017; 0,147]`
(ham p = 0,010; iki karşılaştırmalık Bonferroni sonrası p = 0,020). Nodül önceden belirlenmiş birincil
bulgu olarak ele alındığında SPECTRE'nin üstünlüğü desteklenir. 18 bulgu keşifsel olarak birlikte
düzeltildiğinde fark anlamlılığını kaybeder (Holm p = 0,28).

Çalışma noktaları, bu ayrımın tek başına bir tarama aracı için yetersiz olduğunu gösteriyor: nodüllerin
%80'ini yakalamak için nodülsüz serilerin yaklaşık %58'ine alarm vermek gerekir. Eşikler aynı kat dışı
tahminler üzerinde seçildi ve GA verilmedi; değerler bir miktar iyimser olabilir. Nodül etiketi rapordan
türetilmiştir ve benign ile malign nodülleri birlikte içerir.

### 4.4 Tarama-rapor eşleştirmesi (460 çalışma)

| Model / yön | R@1 | R@5 | R@10 | R@50 | MedR |
|---|---:|---:|---:|---:|---:|
| SPECTRE, görüntüden rapora (I2T) | **%10,9** [8,2; 14,0] | **%28,3** [24,2; 32,3] | **%37,2** [33,0; 41,7] | **%62,4** [57,9; 67,0] | **26,5** [21; 35] |
| SPECTRE, rapordan görüntüye (T2I) | **%12,2** [9,3; 15,2] | **%30,7** [26,5; 34,9] | **%40,7** [36,1; 45,3] | **%65,2** [60,7; 69,7] | **20,5** [14; 27] |
| M3D, görüntüden rapora (I2T) | %0,2 [0,0; 0,7] | %1,1 [0,2; 2,2] | %2,6 [1,3; 4,2] | %13,3 [10,3; 16,2] | 227,5 [206; 250] |
| M3D, rapordan görüntüye (T2I) | %0,4 [0,0; 1,1] | %0,7 [0,0; 1,5] | %1,7 [0,7; 3,0] | %13,5 [10,5; 16,7] | 216,5 [195; 239] |
| Rastgele beklenti | %0,2 | %1,1 | %2,2 | %10,9 | 230,5 |

| SPECTRE − M3D (yüzde puan) | R@10 | R@50 |
|---|---:|---:|
| Görüntüden rapora (I2T) | +34,6 [30,3; 39,1] | +49,1 [44,1; 54,5] |
| Rapordan görüntüye (T2I) | +38,9 [33,9; 43,8] | +51,7 [46,2; 56,9] |

SPECTRE'ye bir tarama verildiğinde, 460 rapor içinden doğru rapor vakaların %37'sinde
ilk 10 aday arasında çıkıyor. Bir rapor verildiğinde doğru tarama vakaların %41'inde ilk 10 arasında.
Bu, rastgele beklentinin yaklaşık 17-19 katı. M3D'de değerler rastgele düzeye yakın. SPECTRE'nin görüntü
ile rapor arasında gerçek bir anlam eşleşmesi kurduğu açık; buna rağmen doğru eş vakaların üçte ikisinde
ilk 10'da değil. Bu düzey bir araştırma sinyalidir, otomatik vaka arama için yeterli değildir.

## 5. BIMCV-R sonuçları

### 5.1 Genel bulgu temsili

| Model | 317 seri: Macro-AUC [%95 GA] | 317: Micro-AUC [%95 GA] | 317: Macro-AP | Temiz 256: Macro-AUC [%95 GA] | Temiz 256: Micro-AUC |
|---|---:|---:|---:|---:|---:|
| SPECTRE-Large | **0,622 [0,604; 0,641]** | **0,692 [0,676; 0,709]** | **0,265** | **0,615 [0,594; 0,637]** | **0,693** |
| M3D-CLIP | 0,551 [0,533; 0,571] | 0,616 [0,601; 0,632] | 0,181 | 0,551 [0,529; 0,574] | 0,625 |
| MG-3D Swin-B | 0,528 [0,509; 0,549] | 0,590 [0,572; 0,609] | 0,169 | 0,535 [0,513; 0,557] | 0,599 |

| Eşleştirilmiş fark, ΔMacro-AUC | 317 seri [%95 GA] | Temiz 256 [%95 GA] |
|---|---:|---:|
| SPECTRE − M3D | +0,071 [0,045; 0,097] | +0,064 [0,037; 0,092] |
| SPECTRE − MG-3D | +0,094 [0,067; 0,119] | +0,080 [0,054; 0,106] |
| M3D − MG-3D | +0,023 [−0,004; 0,047] | +0,016 [−0,013; 0,043] |

SPECTRE BIMCV'de de açık farkla birinci ve sorunlu seriler çıkarıldığında sıralama değişmiyor. Mutlak
başarı CT-RATE'e göre düşük. BIMCV'nin raporları İspanyolcadan makine çevirisi, protokolleri karışık
(torako-abdominal, anjiyo) ve etiketleri daha gürültülü. BIMCV hiçbir modelin ön-eğitim verisinde yok;
bu nedenle buradaki üstünlük SPECTRE için CT-RATE'tekinden daha güçlü bir dış kanıt.

### 5.2 Seçilmiş bulgular (317 seri)

`*` Holm düzeltmesi sonrası p < 0,05 (25 bulgu, 3 model çifti). Tabloda olmayan bulgularda düzeltme
sonrası anlamlı fark yok.

| Bulgu | Pozitif | SPECTRE | M3D | MG-3D | Düzeltme sonrası anlamlı fark |
|---|---:|---:|---:|---:|---|
| Plevral efüzyon | 57 | 0,864 | 0,637 | 0,621 | SPECTRE > M3D*, SPECTRE > MG-3D* |
| Amfizem | 37 | 0,820 | 0,631 | 0,485 | SPECTRE > M3D*, SPECTRE > MG-3D* |
| COVID-19 | 88 | 0,790 | 0,574 | 0,615 | SPECTRE > M3D*, SPECTRE > MG-3D* |
| Operasyon | 25 | 0,771 | 0,710 | 0,565 | SPECTRE > MG-3D* |
| Buzlu cam | 120 | 0,756 | 0,624 | 0,549 | SPECTRE > M3D*, SPECTRE > MG-3D* |
| Pnömoni | 101 | 0,734 | 0,519 | 0,489 | SPECTRE > M3D*, SPECTRE > MG-3D* |
| Kalsifiye dansiteler | 62 | 0,630 | 0,456 | 0,544 | SPECTRE > M3D* |
| Pulmoner kitle | 28 | 0,629 | 0,622 | 0,589 | Yok |
| Nodül | 83 | 0,576 [0,508; 0,641] | 0,573 | 0,462 | Yok |
| Artmış dansite | 21 | 0,484 | 0,700 | 0,510 | Yok (temiz 256'da M3D > SPECTRE*) |

- SPECTRE'nin BIMCV'deki üstünlüğü de yaygın parankim ve sıvı bulgularında toplanıyor.
- Nodül ve pulmoner kitlede SPECTRE ile M3D aynı düzeyde. Temiz 256 seride nodül AUC'si SPECTRE
  `0,607 [0,535; 0,681]`, M3D `0,596`, MG-3D `0,511`.
- Artmış dansite, M3D'nin SPECTRE'yi geçtiği tek bulgu. Az pozitifli (21) ve tanımı belirsiz bir
  etiket; tek başına yorumlanmamalı.

### 5.3 Tarama-rapor eşleştirmesi (317 seri)

| Model / yön | R@1 | R@5 | R@10 | R@50 | MedR |
|---|---:|---:|---:|---:|---:|
| SPECTRE, görüntüden rapora (I2T) | **%6,0** [3,5; 8,9] | **%18,3** [14,0; 22,7] | **%28,4** [23,7; 33,3] | **%58,4** [52,9; 63,6] | **36** [29; 44] |
| SPECTRE, rapordan görüntüye (T2I) | **%5,0** [2,8; 7,6] | **%17,4** [13,3; 21,5] | **%24,0** [19,4; 28,9] | **%54,3** [48,9; 59,7] | **38** [26,5; 52] |
| M3D, görüntüden rapora (I2T) | %0,6 [0,0; 1,6] | %2,8 [1,3; 4,8] | %7,3 [4,4; 10,4] | %27,1 [22,4; 31,9] | 130 [112; 145] |
| M3D, rapordan görüntüye (T2I) | %1,0 [0,0; 2,2] | %3,2 [1,3; 5,3] | %6,6 [4,1; 9,5] | %24,3 [19,6; 29,1] | 123 [102; 145] |
| Rastgele beklenti | %0,3 | %1,6 | %3,2 | %15,8 | 159 |

SPECTRE, makine çevirisi ve karışık protokollere rağmen BIMCV'de de raporu görüntüyle anlamlı biçimde
eşleştiriyor. Bir tarama için doğru rapor vakaların %28'inde ilk 10 aday arasında; M3D'de %7. Değerler
sorunlu 61 seriyi de içeriyor.

## 6. Sybil'in kaçırdığı nodüller: SPECTRE ek bir katman olabilir mi?

### 6.1 Soru ve kurulum

Sybil bir yıllık akciğer kanseri riskini tahmin eden bir modeldir; nodül dedektörü değildir. Bu analiz
şu pratik soruyu soruyor: Sybil'in alarm vermediği taramalara ikinci bir göz olarak SPECTRE bakarsa,
raporunda nodül bulunan vakaları öne çıkarabilir mi?

Kurulum:

- Veri: BIMCV'nin 317 serisi ve rapordan türetilmiş nodül etiketi. Kanser etiketi yok.
- Sybil'in 1. yıl risk skoru, önceden sabitlenmiş 0,20 eşiğinde. Sybil bu eşikte 16 seride alarm veriyor.
- Sybil'in alarm vermediği ama raporunda nodül olan seriler bu analizde "kaçan nodül" olarak sayıldı.
  Bunlar gerçek Sybil hatası değil: Sybil'in benign bir nodüle düşük risk vermesi beklenen bir davranış.
- Her yeni modele Sybil'in alarm sayısı kadar, yani 16 ek alarm hakkı verildi. Model, Sybil'in negatif
  bıraktığı seriler arasından nodül skoru en yüksek 16 seriyi işaretledi. Böylece üç model aynı ek iş
  yükünde karşılaştırıldı.

| Sybil, nodül etiketine karşı | 317 seri | Temiz 256 |
|---|---:|---:|
| Alarm ve nodül var | 9 | 6 |
| Alarm yok, nodül var ("kaçan nodül") | 74 | 59 |
| Alarm var, nodül yok | 7 | 7 |
| Alarm yok, nodül yok | 227 | 184 |

### 6.2 Sonuçlar

317 seri. Sybil'in negatif bıraktığı 301 seride 74 nodül var (%24,6). 16 ek alarmda rastgele
seçimle ortalama 3,9 nodül beklenir.

| Model | Nodül AUC [%95 GA] | 16 ek alarmda yakalanan nodül | Ek yanlış alarm | Ek alarmların nodül oranı | Keşifsel p |
|---|---:|---:|---:|---:|---:|
| SPECTRE-Large | 0,585 [0,514; 0,655] | **8** | 8 | **%50** | 0,021 |
| M3D-CLIP | 0,574 [0,508; 0,640] | 5 | 11 | %31 | 0,35 |
| MG-3D Swin-B | 0,460 [0,396; 0,526] | 6 | 10 | %38 | 0,17 |

Temiz 256 seri (duyarlılık analizi). Sybil'in negatif bıraktığı 243 seride 59 nodül var (%24,3).
Sybil burada 13 alarm veriyor; 13 ek alarmda rastgele beklenen 3,2 nodül.

| Model | Nodül AUC [%95 GA] | 13 ek alarmda yakalanan nodül | Ek yanlış alarm | Ek alarmların nodül oranı | Keşifsel p |
|---|---:|---:|---:|---:|---:|
| SPECTRE-Large | 0,626 [0,545; 0,702] | **8** | 5 | **%62** | 0,004 |
| M3D-CLIP | 0,600 [0,518; 0,677] | 6 | 7 | %46 | 0,065 |
| MG-3D Swin-B | 0,505 [0,427; 0,579] | 3 | 10 | %23 | 0,65 |

Keşifsel p, aynı sayıda serinin rastgele seçilmesi durumunda en az bu kadar nodül yakalanma olasılığıdır
(hipergeometrik test).

### 6.3 Akciğer parankiminde malignite bulgusu olan vakalar

Nodül etiketi benign nodülleri de içerdiği için aynı soru, raporunda akciğer parankiminde malignite
bulgusu olan vakalarda ayrıca incelendi. Bu gruba güncel primer akciğer tümörü, şüpheli primer pulmoner
lezyon ya da pulmoner metastaz tanımlanan 13 seri girdi. Modellerin doğrudan bir malignite çıktısı
olmadığı için her modelin nodül ve pulmoner kitle olasılıklarından büyük olanı skor olarak kullanıldı;
yeni bir sınıflandırıcı eğitilmedi.

| 317 seri, 13 parankim malignitesi | Sybil | SPECTRE | M3D | MG-3D |
|---|---:|---:|---:|---:|
| AUC [%95 GA] | 0,647 [0,453; 0,824] | 0,650 [0,533; 0,764] | 0,673 [0,491; 0,827] | 0,643 [0,487; 0,778] |
| Sybil 0,20 eşiğinde yakalanan / kaçırılan | 4 / 9 | - | - | - |
| Sybil'in negatif bıraktığı 301 seride AUC (9 pozitif) | - | 0,704 | 0,653 | 0,655 |
| 16 ek alarmda yakalanan kaçmış vaka (rastgele beklenen 0,48) | - | 1 | 1 | 2 |
| En yüksek skorlu 60 seride (havuzun %20'si) yakalanan | - | 3 | 4 | 3 |

Sybil parankim malignitesi olan 13 vakanın 9'unu 0,20 eşiğinin altında bıraktı. Üç model de bu vakaları
rastgele sıralamadan biraz daha iyi sıralıyor, ama güven aralıkları çok geniş ve modeller arasında fark
yok. Sybil kadar ek alarmla SPECTRE kaçan 9 vakadan yalnız 1'ini yakalıyor. Pozitif sayısı bu kadar az
olduğunda sonuç ancak betimsel okunabilir. Ayrıca bu malignite etiketi raporlardan kural tabanlı olarak
türetildi ve ikinci bir değerlendiriciyle doğrulanmadı.

### 6.4 FN azaltma açısından ne anlama geliyor?

Sybil tek başına 83 rapor-nodülünün 9'unu işaretliyor. SPECTRE'nin 16 ek alarmı eklenince bu
sayı 17'ye çıkıyor; kaçan nodül 74'ten 66'ya iniyor (%10,8 azalma). Temiz alt kümede kaçan nodül 59'dan
51'e iniyor (%13,6 azalma). SPECTRE'nin ek alarmlarının yarısı nodüllü seriye düşüyor; havuzdaki nodül
oranı %24,6.

Bunun karşılığında toplam alarm sayısı 16'dan 32'ye, yani iki katına çıkıyor. Kurtarılan her nodül için bir
yanlış alarm ekleniyor. Buna rağmen nodüllerin %80'i hâlâ alarmsız kalıyor.

Sonuç umut verici olsa da istatistiksel dayanağı zayıf:

- Üç model birlikte değerlendirildiği için p değerleri düzeltilmeli. Düzeltmeden sonra birincil 317
  serilik analizde p = 0,063 ve %5 eşiğinin altında kalmıyor. Temiz alt kümede düzeltilmiş p = 0,012;
  ama bu alt küme aynı kohortun ikincil analizi, bağımsız bir doğrulama değil.
- SPECTRE'nin M3D'den üstün olduğu gösterilemedi. Nodül AUC'lerinin güven aralıkları büyük ölçüde
  örtüşüyor ve M3D'nin AUC'si de rastgele düzeyin biraz üzerinde. SPECTRE'nin ayrıştığı yer, sabit ek
  alarm bütçesinde en üstteki skorların nodül bakımından zenginleşmesi.
- Hipergeometrik test sabit kat dışı skorlar üzerinde yapıldı. Sınıflandırıcının yeniden eğitilmesini,
  kat yapısını ve hasta kümelenmesini hesaba katmıyor. Bu yüzden keşifsel bir zenginleşme testi olarak
  okunmalı. Hasta düzeyinde etiket permütasyonuyla bütün hattı yeniden çalıştıran bir test yapılmadı.
- Hedef kanser değil, rapor-kökenli nodül; benign nodülleri de içeriyor.

### 6.5 SPECTRE bu amaçla kullanılabilir mi?

Klinik bir güvenlik katmanı olarak şu an kullanılamaz. Kazanç küçük: 74 kaçan nodülden 8'i. Alarm yükü iki
katına çıkıyor. Birincil analizde sonuç çoklu karşılaştırmadan sonra anlamlı değil. Parankim malignitesi olan
vakalarda da SPECTRE belirgin bir katkı göstermedi (bölüm 6.3). En önemlisi, ölçülen hedef kanser değil.

Araştırma amacıyla ise üç model içinde denenmeye en uygun olanı SPECTRE. Sabit ek alarm bütçesinde en
güçlü zenginleşmeyi gösteren model o. Sinyal görüntüsü temiz serilerde daha belirgin. Ayrıca genel bulgu
temsilinde ve eşleştirmede diğer iki modelden açıkça iyi. Tamamlayıcı olarak ciddiye alınması için şunlar
gerekiyor:

1. Kanser etiketi olan ve Sybil ile SPECTRE'nin eğitimde görmediği bağımsız bir kümede doğrulama.
2. Eşiğin ve alarm bütçesinin önceden belirlenmesi, sonuçların o kümede sınanması.
3. Bütün hattı yeniden çalıştıran permütasyon testiyle istatistiksel güvenin sağlamlaştırılması.
4. Nodül için tüm-hacim embeddingi yerine parça ya da lezyon düzeyinde bir temsilin denenmesi. Üç model
   de nodülde en zayıf; sınırlayıcı etken muhtemelen temsilin kendisi.

## 7. Genel değerlendirme

- Sıralama tutarlı. SPECTRE iki veri kümesinde, genel bulgu temsilinde ve eşleştirmede birinci.
  M3D ile MG-3D arasındaki farklar küçük ve veri kümesine göre yön değiştiriyor: CT-RATE'te MG-3D,
  BIMCV'de M3D sayısal olarak önde.
- SPECTRE en iyi genel aktarılabilir hacim temsilini üretiyor. Bu, rapordaki bulguların
  ayrılabilirliği ve tarama-rapor eşleşmesiyle ölçüldü. Anatomik lokalizasyon ve lezyon tespiti
  ölçülmediği için "anatomiyi en iyi temsil eden model" demek bu çalışmanın gösterdiğinden geniş bir
  iddia olur.
- Güç yaygın bulgularda, zayıflık küçük lezyonlarda. Sıvı, konsolidasyon, buzlu cam, amfizem ve
  kalsifikasyonda fark büyük. Nodülde fark küçük, BIMCV'de hiç yok.
- BIMCV sonuçları veri kalitesiyle sınırlı. Serilerin yaklaşık beşte biri bu karşılaştırma için
  güvenilir değil ve etiketler gürültülü. Buna rağmen model sıralaması temiz alt kümede değişmiyor.

## 8. Kullanım kararı

| Kullanım | Karar |
|---|---|
| Genel amaçlı 3B BT hacim temsili | SPECTRE birinci tercih; iki veri kümesinde de açık farkla en iyi |
| Tarama-rapor eşleştirmesi | SPECTRE; güçlü araştırma sinyali, otomatik vaka arama için yeterli değil. M3D uygun değil |
| Akciğer nodülü temsili | SPECTRE önde ama orta-zayıf; tek başına tarama aracı olarak yetersiz |
| Sybil'in alarm vermediği serilerde nodül tamamlayıcısı | SPECTRE keşifsel araştırma adayı; birincil sonuç düzeltme sonrası anlamlı değil, M3D'ye üstünlüğü gösterilmedi |
| Sybil'in kaçırdığı kanserleri yakalama | Bu veri kümeleriyle karar verilemez |
| M3D-CLIP | Genel temsilde SPECTRE'nin gerisinde; eşleştirme için uygun değil |
| MG-3D Swin-B | BIMCV'de en zayıf; bu çalışmanın amacı için öncelikli değil |

## 9. Sınırlar

- Etiketler: CT-RATE ve BIMCV bulgu etiketleri rapordan otomatik türetilmiş gümüş etiketlerdir;
  patoloji değildir.
- Ölçülen şey: Dondurulmuş embedding ve lineer sınıflandırıcı başarısı; ince ayarlı model değil.
  Lokalizasyon, lezyon tespiti ve segmentasyon ölçülmedi.
- Örneklem: Küçük (491 ve 317 seri); seyrek bulgularda güven aralıkları geniş.
- Güven aralıkları koşullu: Sabit kat dışı tahminler üzerinde hesaplandı. Sınıflandırıcı eğitim
  belirsizliğini tam içermiyor; sınırdaki p değerleri iyimser olabilir.
- Çalışma noktaları: Duyarlılık ve özgüllük noktaları aynı veride seçildi; GA verilmedi. Klinik
  eşik olarak kullanılmadan önce iç katlarda seçilmeli ya da dış veride doğrulanmalı.
- Eşdeğerlik: Karşılaştırma uçtan uca tam eşdeğer değil (bölüm 2.4).
- Ön-eğitim maruziyeti: CT-RATE'teki farkın bir kısmı SPECTRE ve MG-3D için alan içi avantajdan
  gelebilir.
- Yönelim: CT-RATE girdileri SPECTRE'nin kendi CT-RATE ön işlemesiyle aynı yönelim kuralıyla
  hazırlandı; BIMCV girdileri NIfTI başlığına göre RAS yönelimine çevrildi.
- BIMCV veri sorunları: 61 seri birincil analizde yer alıyor (bölüm 3.2). Görsel kalite
  sınıflaması tek okuyucuya dayanıyor.
- Sybil analizi: Keşifsel. Hedef rapor-kökenli nodül; eşik ve alarm bütçesi dış veride
  doğrulanmadı; hipergeometrik p tam hattın belirsizliğini içermiyor.

## 10. Öneriler

1. **Bağımsız doğrulama.** SPECTRE'nin Sybil'e katkısı, kanser etiketi olan ve iki modelin eğitimde
   görmediği bir kümede önceden belirlenmiş eşikle sınanmalı. NLST uygun değil: Sybil NLST'de eğitildi,
   SPECTRE NLST'yi ön-eğitimde gördü.
2. **Permütasyon testi.** Mevcut veride Sybil tamamlayıcılığı için hasta düzeyinde etiket permütasyonuyla
   bütün hattı yeniden çalıştıran bir test yapılabilir.
3. **Doğru kütüphane kullanımı.** SPECTRE başka veride kullanılırken spectre-fm 0.2.1'in
   `load_and_window(spacing=…)` yolu kullanılmamalı; voksel boyutunu `MetaTensor` üzerinden veren yol
   ya da düzeltmeyi içeren sürüm seçilmeli. Her çıkarımda sentetik küp testi, seri başına
   geri-korelasyon ve birkaç serinin orta kesit kontrolü yapılmalı.
4. **Görüntü kalite kontrolü.** Girdi görüntüleri modele girmeden önce gözle kontrol edilmeli; mümkünse
   iki okuyucu ve kayıtlı uyuşmazlık çözümüyle.
5. **Veri bildirimi.** BIMCV-R'nin veri sorunları veri kümesi sorumlularına bildirilebilir.

## 11. Yeniden üretim

| Öğe | Konum |
|---|---|
| Değerlendirme betiği (CPU, yaklaşık 15 dk) | `scripts/84_vlm33_benchmark_degerlendirme.py` |
| Değerlendirme çıktıları | `outputs/vlm33/sonuclar.json`, `outputs/vlm33/ozet.txt` |
| Parankim malignitesi analizi (bölüm 6.3) | `scripts/86_vlm33_parankim_malignite.py`, `outputs/vlm33/parankim_malignite.json`, `outputs/vlm33/bimcv317_parankim_malignite_etiket.csv` |
| SPECTRE embedding çıkarım betiği (GPU) | `scripts/85_vlm33_spectre_embedding_cikarimi.py` |
| SPECTRE kontrol raporları ve seri manifestleri | `outputs/vlm33/kapi_raporu_*.md`, `outputs/vlm33/spectre_*_manifest.csv` |
| SPECTRE embeddingleri ve çıkarım logları (yerel, depoya girmez) | `data/external/vlm33_spectre/` |
| BIMCV görsel kalite sınıflaması | `outputs/vlm33/bimcv317_gorsel_kalite.csv` |
| Önizleme sayfaları (yerel, hasta görüntüsü içerdiği için depoya girmez) | `outputs/vlm33/onizleme_yerel/` |
| Sybil skorları | `bimcv-analysis/BIMCV_Sybil_Pillar_Astra_317_Clean_Results.xlsx` |

SPECTRE embedding dosyalarının sha256 değerleri:

- `spectre_ctrate_500_v5_embeddings.npz`: `7f2a64759172a26824babcdd330982f1825e1c8d094a45b0ee46b7f5554c7651`
- `spectre_bimcv_317_v5_embeddings.npz`: `3d795370fe2b17a5a31c97f7750475439a6e286b401c130d2c79d084dcbf624c`

M3D-CLIP ve MG-3D embeddinglerinin, kat dosyasının ve kohort manifestinin alındığı Hugging Face paketleri:

| Model | Depo | Revizyon |
|---|---|---|
| M3D-CLIP | [chn123/m3d-ctrate-bimcv-500-benchmarks](https://huggingface.co/datasets/chn123/m3d-ctrate-bimcv-500-benchmarks) | `281993abf10cbc22169930fa2d71486ecc385cc3` |
| MG-3D Swin-B | [chn123/mg3d-ctrate-bimcv-500-benchmarks](https://huggingface.co/datasets/chn123/mg3d-ctrate-bimcv-500-benchmarks) | `5e07f9cc4e9b85a347063e16effdcd8be8447798` |
