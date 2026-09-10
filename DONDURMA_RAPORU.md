# CT-Report-VLM · Kapanış ve Dondurma Raporu

**Tarih:** 2026-09-10 · **Durum:** Proje dondurulmuştur · **Yürütücü:** Sude Dilay Tunç

> **Klinik kullanım hükmü.** Bu projede geliştirilen hiçbir model, şema, sözlük
> veya çıkarım çıktısı klinik kullanım için doğrulanmamıştır. Buradaki sayılar
> araştırma amaçlı ölçümlerdir; tanı, tarama, triyaj veya karar desteği amacıyla
> kullanılamaz. Değerlendirmelerin hiçbirinde radyolog onaylı referans standart
> yoktur ve kullanılan malignite şeması klinik uzman onayından geçmemiştir.

---

## Bir bakışta

Proje, akciğer kanseri taramasında görüntü tabanlı risk modellerinin ürettiği
gereksiz alarmları, radyoloji raporundan çıkarılan bilgiyle azaltmayı hedefledi.

Üç rapor üreten sistem (Astra, MedMo, BTB3D) ve iki sürekli risk modeli
(Sybil, Pillar) üç kohortta değerlendirildi. On beş yol denendi. Ana fikrin
sınanabilmesi için gereken veri bileşiminin elde bulunmadığı anlaşıldı.

1. Rapor üreten modeller gerçek rapora benzeyen metinler üretiyor, ancak
   hasta-özgü klinik doğruluk yeterli düzeyde gösterilemedi.
2. Bu durum yaygın metin benzerliği ölçütleriyle görünmüyor; o ölçütler şablon
   taklidini başarı olarak sayabiliyor.
3. Ana tez (benign kanıtın yanlış alarmları azaltması) ne doğrulandı ne
   çürütüldü. Gereken veri bileşimi hiçbir kohortta bulunmadığından mevcut
   veriyle değerlendirilemedi.

---

## Dondurmanın kapsamı ve gerekçesi

**Duran:** deneyler, veri toplama ve model çıkarımı. Yeni ölçüm koşulmayacak.
**Korunan:** kod, sürüm kilitleri ve belgeler. Bakım yapılmayacak, ancak çalışır
ve devredilebilir durumda.

Proje bütünüyle sonlandırılmıyor; duran şey ana tezin sınanmasıdır.

**Gerekçe.** Bir sonraki deneyin proje kararını değiştirebilmesi için yeni veri
gerekiyor. Mevcut artefaktlarla yapılacak ek analizler beklenen bilgiyi
üretmeyecektir: ana tezi sınayacak veri bileşimi hiçbir kohortta yok, denenen on
dört yolun her biri bir ölçümle kapandı, kalan yol aynı veri kısıtının içinde.
Bu bir yöntem yetersizliği değil, veri erişimi kısıtıdır.

---

## 1. Proje ne yapmak istedi

Sybil ve Pillar gibi üç boyutlu risk modelleri duyarlılık konusunda güçlüdür,
ancak çok sayıda **yanlış alarm** üretirler. Radyoloğun raporu bu alarmların bir
kısmını eleyebilecek bilgiyi taşır: "kalsifiye granülom", "eski enfeksiyon
sekeli", "iki yıldır değişmemiş".

> **Rapordan otomatik çıkarılan benign kanıt, risk modelinin yanlış alarmlarını,
> gerçek kanserleri kaçırmadan azaltabilir mi?**

Üç iş gerekiyordu: raporlardan güvenilir bilgi çıkarmak, bunu bir malignite
şemasına bağlamak, şemayı risk skoruyla birleştirip yanlış alarm azalmasını
ölçmek. İlk ikisi tamamlandı; üçüncüsü bölüm 4'teki nedenle yapılamadı.

---

## 2. Yolculuk ve sınırlayıcı bulgular

### 2.1 CT-RATE korpusu

25.692 çalışma, 21.304 hasta. Bir çekimin farklı rekonstrüksiyonları birebir
aynı rapor metnini taşıdığı için korpus çalışma düzeyinde tekilleştirildi;
aksi hâlde aynı rapor hem eğitime hem teste düşerdi.

Projenin en belirleyici gözlemi burada çıktı:

> **Bir kelimenin raporda geçmesi, o bulgunun hastada bulunduğu anlamına
> gelmiyor.**

"Tümöral" geçen cümlelerin tamamı, "kitle" geçenlerin %93'ü olumsuz. Cümlelerin
%71'i birden fazla kez geçen şablon cümleler. 479.051 cümle karakter
ofsetleriyle bölütlendi, 50.513 ölçü çıkarıldı.

**Sınırlayıcı bulgu.** CT-RATE'te malignite referans standardı yok; 18 anormallik
etiketi arasında kanser, malignite, kitle veya tümör bulunmuyor ve bu etiketler
raporlardan otomatik üretilmiş, radyolog onaylı değil. Bu nedenle rapordan
çıkarılan her sınıf `report_derived_*` diye adlandırıldı.

### 2.2 Yapılandırılmış çıkarım katmanı

Bulgu ve anatomi tanıma, ilişki kurma, ölçü normalizasyonu ve bağlam çözümleme
(var, yok, şüpheli, geçmiş) katmanları kuruldu. `ctx-1.1` mühürlü test kümesinde
doğrulandı: çeldirici reddi %98'in üzerinde, kapsama %88 ile %97 arasında.

**Sınırlayıcı bulgu.** İki zayıflık ölçüldü ve kayda geçirildi. **Zaman ekseni
düşük başarımlı** (`prior` F1 %36,4), yani stabilite bilgisi güvenilir biçimde
çıkarılamıyor ve bu benign filtrenin planlanan girdilerinden biriydi. **Kavram
düzeyi işaretleyici uyumu zayıf** (kappa 0,34), oysa bulgu var mı yok mu
sorusunda uyum güçlü (kappa 0,76).

### 2.3 Türkçe hat ve dil ablasyonu

Hedef kohort Türkçe olacağı için Türkçe çıkarım katmanı kuruldu: yüzey sözlükleri
korpustan türetildi, 144 kavramlık kapalı envanter kilitlendi, negasyon
çözümlemesi ölçüldü (F1 %90,3).

Ardından bir yöntem sorusu sınandı: etiketleme Türkçe mi İngilizce mi yapılmalı?
Aynı 46 rapor üç yoldan işlendi (doğrudan Türkçe, makine çevirisi, çeviri artı
tıbbi düzeltme). Tasarım sonuçlar görülmeden donduruldu.

- Makine çevirisi deterministik değil: aynı 46 rapor iki kez çevrildi, 5'i (%11)
  farklı çıktı.
- Ucuz çeviri kavramların %17'sini kaybettiriyor.
- Türkçe ile iyi bir çeviri arasındaki fark, hangi altın standart kullanılırsa
  kullanılsın 4,06 puanı aşamıyor; kabul marjı 5 puandı.

Son madde yöntemsel olarak dikkat çekicidir: **karar, altın standart etiket hiç
üretilmeden alınabildi.** Hüküm: belirleyici olan hangi dilde çalışıldığı değil,
nasıl çevrildiği.

Aynı aşamada üç açık kaynak model (Qwen3.5-4B, Aya, Qwen3-8B) ikincil
değerlendirici olarak sınandı ve eleme kapılarından geçemedi; tıbbi düzeltme kolu
düşürüldü. Bu deneyler bölüm 2.6'daki rapor üreten sistemlerden ayrıdır.

**Sınırlayıcı bulgu.** RadTr korpusunda 429 belgenin yalnızca 7'sinde malignite
geçiyor, korpusa ait görüntü ve patoloji sonucu yok, kanonik altın standart için
radyolog erişimi sağlanamadı. Ayrıca bölünme kirlenmesi denetimi, RadTr'nin
`train.json` dosyasının test belgelerinin 56'sının 56'sını birebir içerdiğini
gösterdi. **RadTr test bölümü skorlanmadı, ancak belgeleri kaynak train
dosyasında da bulunduğundan tam bağımsız held-out olarak değerlendirilemez.**

### 2.4 Malignite değerlendirme şeması

Ölçek **altı sıralı düzeyden** oluşuyor (`None`, `low`, `indeterminate`,
`intermediate`, `high`, `known_malignancy`) ve bunlara ek **ölçek dışı** bir
`not_mentioned` durumu var. `not_mentioned` sıraya girmez ve "şüphe yok" anlamına
gelmez.

Sınav takımları kurallar yazılmadan önce kilitlendi, kör paket SHA-256 ile
mühürlendi.

**Sınırlayıcı bulgu.** Hedeflenen "%100 uyum" eşiği ulaşılamaz çıktı; iki kabul
ölçütü belirli bir vaka üzerinde birbirini dışlıyordu. Ölçüt yapısal olarak
yeniden tanımlandı, ancak **24/30 sonucu "geçti" diye yeniden adlandırılmadı.**
Şema sınırları ilan edilerek donduruldu (bölüm 9).

### 2.5 NLST'ye geçiş

CT-RATE'te kanser sonucu bulunmadığı için kohort değiştirildi. NLST'de her
katılımcının takip süresince kanser tanısı alıp almadığı kayıtlı; metinden
bağımsız bir dış referans var. 2.965 seri (1.201 hasta) üzerinde çalışıldı,
bölünme hasta düzeyinde ve etikete göre katmanlı yapılıp kilitlendi.

**Held-out durumu.** Split sonrasında yürütülen çıkarım koşumunda held-out
etiketleri kullanılmadı. Ancak split dondurulmadan önce tüm kohort etiketlerle
incelendiği için **held-out bağımsız ve görülmemiş test sayılmaz** (bölüm 3).

**Sınırlayıcı bulgu.** Klinik çerçeve olarak seçilen Lung-RADS uygulanamadı.
Lung-RADS nodül boyutu ve yapısı ister, ancak Astra raporlarında nodül ve ölçü
aynı cümlede yalnızca **%1,2** oranında birlikte geçiyor, "yarı-solid" nitelemesi
hiç geçmiyor (%0,0). Değerlendirme, proje içinde geliştirilen şema üzerinden
yürütüldü.

Ayrıca **negatif beyan risk azaltmıyor**: "nodül yok" yazan hastaların kanser
oranıyla genel oran istatistiksel olarak ayrışmadı, güven aralıkları örtüştü.

### 2.6 Üç kohortta model değerlendirmesi

| Kohort | Büyüklük | Referans | Değerlendirilenler |
|---|---|---|---|
| NLST | 2.965 seri | Doğrulanmış kanser tanısı | Astra, MedMo, BTB3D, Pillar, Sybil |
| BIMCV-R | 317 seri | İspanyol hekim raporu | Astra, Sybil, Pillar |
| CT-RATE | 500 seri | Hekim raporu | BTB3D |

Metin benzerliği kullanılmadı: her iki metin de olumsuzlamayı ayırt eden çıkarım
hattından geçirilip standart patolojilere indirgendi ve aynı hastada aynı
bulgular tarif ediliyor mu diye soruldu.

**BTB3D, CT-RATE'te hasta-özgü uyum gösteremedi.** Bulgu düzeyinde uyum 0,183;
aynı sayıda bulguyu rastgele dağıtan bir sistemin skoru 0,151. Yöntemsel bulgu
daha önemli: geliştiricilerin kendi değerlendirme betiği yeniden koşuldu ve
yayınlanan metin benzerliği değerleri birebir üretildi. Model kendi yayınladığı
ölçütte başarılı görünürken klinik içerikte şans düzeyinden ayrışmadı.

**BTB3D, NLST'de yeterli klinik ayırt edicilik gösteremedi.** Bir yıl içinde
kanser tanısı alan 34 hastanın 33'ünde akciğer malignitesi bildirilmedi.

**MedMo temkinli davranıyor.** Aktif kanserlerde duyarlılık %12 ölçüldü. Bu sayı
**yalnız izlenim bölümüne ve o dönemde kullanılan geniş alarm tanımına** aittir;
tüm rapor metni veya dar pulmoner tanımla sonuç farklılaşır.

**Astra tek başına ümit verici görünüyor**: çekildiği yıl tanı alanların %70'inde
şüphe dile getiriyor. Bölüm 3, bu sayının hangi koşullarda üretildiğini açıklıyor.

**BIMCV-R'de sistemler birbirini doğrulamıyor.** Altı ikili karşılaştırmanın
dördünde uyum şans düzeyinden ayrışmadı. Raporda lezyon tarif edilen 68 serinin
31'inde üç sistem de sessiz; üçünün birden işaret ettiği seri sayısı 4. Pillar
serilerin yaklaşık üçte birine alarm verdi ve bu alarmların neredeyse tamamında
raporda kanser kanıtı yoktu.

Astra'nın rapor uyumu bulgu tipine göre ayrıştı: plevral efüzyonda %79, nodülde
%14. Biçimsel kusurlar da saptandı: taraf ters verme, karşılığı olmayan lezyon
tarif etme, doldurulmamış şablon ve **görüntü kapsamı doğrulanmadan** abdomen ile
meme hakkında rutin bölüm yazma. Bazı vakalarda beyin ve prostat gibi kesinlikle
kapsam dışı anatomiler için de bölüm üretildi.

**Sınırlayıcı bulgu.** Üç rapor üreten sistemin hiçbirinde hasta-özgü klinik
doğruluk yeterli düzeyde gösterilemedi; bu üç sistem ve üç kohortta tekrarlanan
bir örüntü.

### 2.7 Keşifsel kurtarma denemesi

Keşifsel bir soru soruldu: Astra'nın pozitif lezyon alarmı Pillar'ınkine mantıksal
VEYA ile eklenirse ne olur? Ölçüm kilit altında, **yalnız eğitim bölümünde**,
**seri düzeyinde** ve önceden ilan edilmiş 0,20 eşiğiyle yapıldı.

| Sistem | AUC (eğitim bölümü, seri düzeyi) |
|---|---|
| Pillar | 0,791 (o yıl tanı alan alt kümede 0,981) |
| Astra metin bulgusu | 0,532 |

AUC, rastgele seçilen kanserli bir örneğe kanserli olmayandan yüksek skor verme
olasılığıdır; 0,5 şans düzeyi demektir. Pillar eğitim bölümünde seri düzeyinde
ayırt edici bir sinyal gösterdi. **Bu bağımsız doğrulama değildir**: eğitim
bölümünde ölçülmüştür ve birincil estimand hasta düzeyiyken hesap seri
düzeyindedir.

Kurtarma kuralının sonucu: Pillar'ın kaçırdığı 49 kanserli seriden 5'ini Astra
işaretliyor, buna karşılık Pillar'ın doğru biçimde sessiz kaldığı 1.751 seride
273 kez alarm veriyor.

> Eğitim kümesinde, seri düzeyinde ve 0,20 eşiğinde, ek işaretlenen her kanserli
> seriye karşılık yaklaşık 55 kanser etiketi taşımayan seri işaretlendi. Bu oran
> bu bölüme ve bu eşiğe özgüdür.

**Sınırlayıcı bulgu ve kapsamı.** Astra'nın pozitif lezyon alarmını Pillar'a
ekleyen keşifsel kurtarma kuralı elverişsiz bir yanlış alarm değiş tokuşu üretti.
**Bu deney, rapordan çıkarılan benign kanıtın yanlış alarmları azaltıp
azaltmadığını doğrudan sınamamaktadır**; farklı yönde bir soruyu, pozitif
kurtarmayı incelemektedir.

Önceden tanımlı bir klinik fayda fonksiyonu bulunmadığından **net fayda
hesaplanmamıştır**; gözlenen yanlış alarm yükü bu kullanım biçimini desteklemedi.

---

## 3. Astra'nın iki analizi neden karşılaştırılamaz

7 Eylül tarihli değerlendirme Astra ile Sybil birleştirildiğinde yakalamanın
%70'ten %90'a çıktığını bildiriyor. 10 Eylül tarihli ölçüm marjinal katkıyı
elverişsiz buluyor. **İki sayı doğrudan karşılaştırılamaz.**

| | 7 Eylül | 10 Eylül |
|---|---|---|
| Kapsam | Tüm kohort, bölünme kilitlenmeden önce | Yalnız eğitim bölümü |
| Hedef | O yıl tanı alan aktif kanserler | Altı yıllık kanser etiketi |
| Risk sistemi | Sybil | Pillar |
| Alarm tanımı | Geniş otomatik tanım | Dar, kilitli tanım |
| Eşik | Ön kayıtlı değil | Önceden ilan edilmiş |

İlk analiz tüm kohortta, geniş bir otomatik alarm tanımı ve ön kayıtlı olmayan
eşikle yapılmıştır; ikinci analiz eğitim bölümünde farklı hedef ve eşikle
marjinal katkıyı incelemiştir. Dondurma kararının dayanağı ikincisidir.

**Held-out maruziyeti.** İlk analiz tüm 2.965 seriyi etiketlerle inceledi ve bir
eşik denemesi içeriyordu; bölünme kilidi ertesi gün kondu. Hasta sızıntısı yok,
ancak eşik seçimi ve sonuç görme maruziyeti var.

---

## 4. Neden durduk: veri açmazı

Ana tezi doğrudan sınamak için üç şeyin **aynı kohortta** bulunması gerekir:
gerçek hekim raporu, görüntü tabanlı risk skoru ve doğrulanmış kanser sonucu.

| Kohort | Hekim raporu | Risk skoru | Kanser sonucu |
|---|:--:|:--:|:--:|
| NLST | Yok, yalnız model üretimi metin | Var | Var |
| BIMCV-R | Var | Var | Yok |
| CT-RATE | Var | Yok | Yok |

Her satırda tam bir eksik var ve kohortları birleştirmek bunu kapatmıyor, çünkü
hastalar farklı. Boşluk kapatılmadan ana tez ne doğrulanabilir ne çürütülebilir;
ölçüm yapılsa bile sonuç yorumlanamayacaktır.

---

## 5. Denenen yolların özeti

| Denenen | Kapanma nedeni |
|---|---|
| RadLex ontoloji eşlemesi | Mevcut şema yeterli görüldü, kapsam dışına alındı |
| Fleischner kılavuzu | ACR Lung-RADS v2022 lehine bırakıldı |
| RadTr üzerinden ilerleme | 429 belgenin 7'sinde malignite; görüntü ve patoloji yok |
| Dil ablasyonu | Fark 4,06 puanı aşamıyor, kabul marjı 5 puandı |
| Üç açık kaynak ikincil model | Eleme kapılarından geçemedi |
| Tıbbi düzeltme kolu | Düşürüldü |
| Lung-RADS'ı model raporlarına uygulamak | Nodül ve ölçü aynı cümlede %1,2, yarı-solid %0,0 |
| Şema için %100 uyum eşiği | Ulaşılamaz ölçüldü, sınırlar ilan edilerek donduruldu |
| Negatif beyanın risk azaltması | Güven aralıkları örtüştü |
| Pozitif kurtarma kuralı | Elverişsiz yanlış alarm değiş tokuşu |
| Sistemleri birleştirmek (ensemble) | Ortak karar 4 seri; lezyonların %45'inde üçü de sessiz |
| BTB3D | Rastgele dağıtımdan güvenilir biçimde ayrışmadı |
| MedMo | İzlenim bölümü duyarlılığı %12 (geniş alarm tanımıyla) |
| Makine çevirisi üzerinden çıkarım | Terimlerin %38'i İngilizce metinde doğru bulunamıyor |
| **Benign kanıtın yanlış alarm azaltması** | **Sınanmadı**, bölüm 4'teki veri açmazı nedeniyle |

---

## 6. Ne geliştirdik

Sözlükler ve desenler bu korpuslardan ölçülerek türetildi. **82 betik yazıldı,
78'i depoda; 508 gerileme testi geçiyor.**

**Metin işleme.** Radyolojiye uyarlanmış cümle bölütleyici (`seg-1.1`, 479.051
cümle, ofsetler %100 doğrulandı), şablon karakterizasyonu (`tmpl-1.0`, eşik iki
bağımsız incelemeyle doğrulandı), ölçü çıkarım motoru (`meas-1.2`, 50.513 kayıt,
yakalama %99,92).

**Bilgi çıkarımı.** Varlık ve ilişki çıkarımı (`ent-1.1`, `rel-1.0`) ile korpustan
türetilmiş anatomi ve bulgu sözlükleri; bağımsız inceleme yedi kusur buldu,
yedisi düzeltildi. Bağlam çözümleme (`ctx-1.1`), dokuz bölüme ayrılmış 47 ipucu;
pilot iki sistematik hatayı ortaya çıkardı ve düzeltmeler bir ölçütü %63,5'ten
%87,8'e taşıdı.

**İki şema.** Çıkarım şeması `sema-1.3` hangi alanların çıkarılacağını tanımlar;
malignite değerlendirme şeması `sema-1.0` bulguları altı sıralı düzeye çevirir
(hedef uyumu 24/30, yanlış pozitif koruması 23 vakada sıfır ihlal, kör doğrulama
%88,9). Adları benzer, nesneleri farklıdır. Gösterge sözlüğü genişletmesiyle
sözlük boşluğu %4,0'ten %0,4'e indirildi.

**Değerlendirme altyapısı.** Kör paketleme sistemi (paket üretir, anahtarı ayırır,
SHA-256 ile mühürler); şans düzeltmeli karşılaştırma protokolü (18 patoloji,
kappa ve MCC, hasta düzeyinde kümeli bootstrap) ve protokolün en ayırt edici
parçası olan **ölçüm aracının kendi hata payının ayrıştırılması** (hattın hekim
raporlarındaki doğruluğu ayrıca ölçülüyor, macro-F1 0,885). Ölçülebilirlik
envanteri bir şemanın korpusa uygulanabilir olup olmadığını önceden ölçer;
Lung-RADS'ın uygulanamazlığı bununla, deneye girmeden bulundu.

**Türkçe hat.** 144 yüzeyi tek düzenli ifadede toplayan matcher (`tr-1.1`), 144
kimlikli kavram kataloğu, Türkçe negasyon çözümlemesi (F1 %90,3), çeviri
değerlendirme hattı, bölünme kirlenmesi denetleyicisi (RadTr kirlenmesi bununla
bulundu) ve insan gözüyle denetim için HTML inceleme tezgâhı.

**Kohort bağlama.** Hasta düzeyi bölünme motoru (`astra-split-1.0`, 2.940 seri /
1.198 hasta, on iki gerileme testi ve bağımsız kaynak denetimiyle doğrulandı) ve
model çıktısı adaptörü (`astra-adaptor-1.2`, iki denetim turuyla revize).

**Yöntem disiplini.** Kabul ölçütleri sonuç görülmeden yazıldı ve olumsuz sonuçta
gevşetilmedi; sınav takımları kurallardan önce kilitlendi; kör paketler
mühürlendi; bir test kusur ortaya çıkardığında susturulmadı, ölçülmüş bir sınıra
çevrildi. Üç bağımsız denetim yapıldı, ikisi kapıyı durdurdu, bulunan dokuz
kusurun dokuzu düzeltilip teste bağlandı (Ek B).

BIMCV kohortunda sınıflamanın tekrarlanabilirliği ayrıca ikinci bir
değerlendiriciyle sınandı: 76 seri, katmanlı örneklem, ikinci değerlendirici
yalnız rapor metnini ve talimatı gördü. Deneylerde fiilen kullanılan katmanlarda
uyum yüksek (geniş torasik malignite kappa 0,828, dar hedef 0,669), yedi kademeli
ince ölçekte orta (0,507). Ayrışmaların incelenmesi iki gerçek kural kusuru
ortaya çıkardı ve ikisi de düzeltildi: çekinceli malignite ifadelerinin kesin
beyan gibi işlenmesi ve benign nitelemenin nodül sözcüğünden uzakta kaldığında
görülmemesi.

---

## 7. Ne öğrenildi

Bu bulgular ana tezden bağımsız olarak geçerlidir.

**Metin benzerliği ölçütleri radyolojide yanıltıcı olabilir.** Raporlar
şablonludur ve cümlelerin çoğu olumsuzdur; şablonu öğrenen bir model görüntüden
bağımsız olarak yüksek BLEU alabilir. Bu doğrudan gösterildi.

**Ölçüm aracının kendi hatası ayrıştırılabilir ve ayrıştırılmalıdır.** Kör
değerlendiriciyle uyumun hem hekim hem model metinlerinde aynı olduğu
gösterilerek, düşük skorun ölçüm yanlılığından kaynaklanmadığı ortaya konabildi.

**Ham örtüşme oranı tek başına kullanılamaz.** İki sistem de nadiren "var"
diyorsa, "yok" konusunda birleştikleri için örtüşme yapay olarak yükselir.

**Makine çevirisi radyoloji metninde güvenilir değil.** En sorunlu hata,
kelimenin çevrilmemesi değil, akıcı görünen ancak yanlış olan çeviridir.

**Rapor üreten modellerin biçimsel kusurları sistematik ve saptanabilir**, üstelik
kanser etiketi gerektirmeden ölçülebilir.

---

## 8. Yeniden açma kapısı ve devam yolları

### Kapı koşulları

| Koşul | Gerekçe |
|---|---|
| **Aynı hastalarda** hekim raporu, risk skoru ve doğrulanmış sonuç | Bölüm 4'teki açmazın kapanması |
| Analiz birimi **hasta düzeyi** | Seri düzeyi tekrarlı ölçüm sorunları üretir |
| **Önceden kayıtlı** sonlanım tanımı ve eşikler | Sonuç görüldükten sonra eşik seçimi bu projede bir zayıflık oldu |
| **Yeterli pozitif sayısı** | Mevcut bölünmede pozitif hasta sayısı eşik sınamasına elvermiyordu |

Bu dört koşuldan biri bile eksikse aynı açmaz tekrarlanır.

### Yol 1: NLST'nin yapılandırılmış radyolog bulguları

**NLST'nin yapılandırılmış radyolog bulguları temin edilebilirse benign kanıt
hipotezi dolaylı olarak sınanabilir. Bu analiz, metin çıkarımının uçtan uca
klinik doğrulaması olmayacak; yapılandırılmış benign bilginin risk skoruna
potansiyel katkısını test edecektir.**

**Önkoşul.** NLST CT anormallik verisinin temin edilebilirliği doğrulanmalıdır.
Bu verinin mevcut veri talebi kapsamında olduğu ve ek etik süreç gerektirmediği
**teyit edilmemiştir**; yola girmeden önce netleştirilmelidir.

**İlk adım.** Pillar belirli bir eşikte eğitim bölümünde yaklaşık 200 yanlış
alarm üretiyor. Bu alarmların kaçında radyolog benign kanıt kodlamış, doğru
alarmların kaçında kodlamış.

**Sınırı.** Girdi radyolog kodudur, serbest metin değildir. Çıkarım doğruluğunu
başka kohortlardan bu sonuca zincirlemek güçlü bir taşınabilirlik varsayımı
gerektirir ve açıkça beyan edilmeden kullanılmamalıdır.

### Yol 2: Türkçe hastane kohortu

Kapı koşullarının tamamının sağlanabileceği öngörülen tek kaynak. Hastane
kaynaklı bir kohort hem rapor hem takip verisi taşıyabilir.

**Önkoşul.** Veri erişimi ve etik onay; proje kontrolü dışında, uzun ufuklu.
**Hazır olan.** Dil kararı ve gerekçesi, Türkçe sözlükler, matcher altyapısı,
bölünme kirlenmesi denetleyicisi.
**Uyarı.** Mevcut Türkçe korpus bu iş için yetersizdir; yeni veri gerekir.

### Yol 3 (ikincil): Rapor biçimsel kalite denetimi

Rapor üreten modellerin biçimsel kusurları bu projede ölçüldü ve otomatik
saptanabilir olduğu görüldü. Klinik olarak konuşlandırılabilir bir güvenlik
katmanı olduğu **gösterilmemiştir**; dış doğrulama olmadan ayrı bir proje
kapsamına girer. Mevcut artefaktların yeniden kullanılabileceği bir yön olarak
kaydedilmiştir.

### Yeniden açılmaması önerilen yollar

Metin alarmını risk modeline pozitif kurtarma olarak eklemek (elverişsiz değiş
tokuş ölçüldü), sistemleri birleştirmek (üyeler tek tek şans düzeyinden
ayrışmadı), sıfırdan model eğitimi (veri, bütçe ve süre mevcut değil).

---

## 9. Dondurulan sürümler ve kilitler

| Bileşen | Sürüm |
|---|---|
| Cümle bölütleme | `seg-1.1` |
| Şablon karakterizasyonu | `tmpl-1.0` |
| Ölçü çıkarımı | `meas-1.2` |
| Varlık / ilişki çıkarımı | `ent-1.1` / `rel-1.0` |
| Bağlam çözümleme | `ctx-1.1` |
| **Çıkarım şeması** | **`sema-1.3`** (`configs/extraction_schema.json`) |
| **Malignite değerlendirme şeması** | **`sema-1.0`** (`configs/degerlendirme_semasi.json`) |
| Türkçe yüzey sözlüğü | `tr-1.1` |
| Model çıktısı adaptörü | `astra-adaptor-1.2` |
| Veri sözleşmesi | `astra-sozlesme-1.1` |
| Hasta düzeyi bölünme | `astra-split-1.0` |

**Kilit durumları.** `astra-split-1.0`: geliştirme bölümü bir kez açıldı, sonucuna
göre kural değiştirilmedi; held-out split sonrası kullanılmadı ancak split öncesi
kohort incelemesi nedeniyle bağımsız test sayılmaz. RadTr Türkçe test bölümü:
skorlanmadı, tam bağımsız held-out değil.

**`sema-1.0` ile ilan edilen sınırlar** (kilit dosyasında kayıtlı):
`known_malignancy` otomatik üretilmez · `low` düzeyi pratikte üretilemiyor
(üretme denemesi yanlış pozitif koruma kapısını kırdığı için geri alındı) ·
derece kapsamı cümle düzeyindedir · sözlük boşluğu bulunmakta ve ölçülmüştür ·
stabil takipteki bilinen kanser görünmüyor (girdisi zaman ekseninin düşük
başarımından etkileniyor) · hedef atama yordamı motorun kavram listesiyle birebir
aynı değildir.

Buna ek olarak şemanın otorite modeli, klinik yargıya dayanan kuralların **uzman
onayından geçmediğini** açıkça beyan eder.

---

## 10. Arşiv ve veri yönetimi

| Kalem | Değer |
|---|---|
| Depo | `github.com/sudilay/CT-Report-VLM` (özel) |
| Etiket | Dondurma commit'ine `dondurma-2026-09-10` konulmalıdır |
| Ortam | Python 3.11.9, `requirements.txt`, `requirements-ceviri.txt`, `pytest.ini` |
| İzlenen dosya | 304 · **508 test geçiyor** (2026-09-10) |
| Model çıkarımları | Baykar sunucusu; raporlar `chn123/astra-nlst-reports`, `chn123/medmo-nlst-reports` |

**Dosya sınıflandırması.** Git'e girer: kod, testler, yapılandırma ve kilit
dosyaları, teknik belgeler, sonuç raporları. Güvenli arşivde tutulur: ham model
çıktıları, kohort tabloları, GradCAM dosyaları, lisanslı veri. Yalnız yerel: ara
çıktılar, devir notları, kanban dışa aktarımları.

Depo dışında tutulan veri: `bimcv-analysis/` **16 GB** (kohort tabloları, Astra
raporları, GradCAM), `data/` 268 MB (CT-RATE, RadTr, kılavuzlar), `outputs/`
25 MB, kök dizindeki tablolar ~14 MB.

**Yapılması gerekenler:**

1. `bimcv-analysis/`, `data/` ve kök dizindeki kohort tablolarının **yedekli bir
   arşive** alınması; şu anda yalnız tek makinede bulunuyor.
2. Arşivlenen dosyaların **SHA-256 özetlerinin** bir manifest dosyasına yazılması;
   şu anda veri bütünlüğünü doğrulayacak kayıt yok.
3. `.gitignore` dışında kalan 26 izlenmeyen dosyanın sınıflandırılması.
4. Dondurma commit'ine etiket konulması.

**Lisans.** CT-RATE `CC-BY-NC-SA-4.0` lisanslıdır ve ticari kullanıma kapalıdır;
NLST ve BIMCV-R kendi koşullarına tabidir. Ham veri hiçbir koşulda depoya
konulmamalıdır.

---

## Ek A: Teknik borçlar

| Borç | Etki |
|---|---|
| Held-out maruziyeti | Held-out bağımsız test olarak sunulamaz |
| BIMCV ikinci değerlendirmesinde uzman yok | İki değerlendirici de otomatik çıkarım kullandı ve hiçbiri radyolog değil; kappa değerleri uzmanlar arası uyum olarak okunamaz, yalnızca şemanın tekrarlanabilirliğini gösterir |
| Astra raporlarında çıkarım hattı daha az güvenilir | Astra ile ilgili sayılar daha az kesin |
| Zaman ekseni düşük başarımlı | Stabilite değerlendirmesi güvenilir değil |
| Kavram düzeyi işaretleyici uyumu zayıf | Kavram eşlemesi tek işaretleyiciye dayandırılamaz |
| Prompt sürümleme ve model kayıt defteri yok | Model çıkarımlarının yeniden üretilebilirliği eksik |
| SUDE-VLM-31 kısmi | Benign filtre ve boyuta göre katmanlı yakalama ölçülmedi |
| Bazı belgelerde kırık atıf | Birkaç atıf oluşturulmamış veya bilerek depo dışında tutulan dosyalara işaret ediyor |
| Veri manifesti ve arşiv yok | Bölüm 10'daki dört madde |

---

## Ek B: Denetimden öğrenilenler

**Makul görünen sayı doğru olduğu anlamına gelmez.** Bir desen hatası (`mAs`
deseninin harf duyarsız olması nedeniyle `mass` ile eşleşmesi) ölçülü 222 raporun
221'ini yanlış sınıflandırıyordu. Buna rağmen kusurlu yöntemin sonucu doğru
yöntemle yalnızca %6,6 farkla uyuşuyor ve kabul aralığında görünüyordu.

**Sessiz varsayılan değerler kural dallarını görünmez biçimde öldürür.** Aynı hata
sınıfı üç kez tekrarlandı: eksik bir alan sessizce "yok" sayılınca kural dalı hata
vermeden sonlanıyordu. Düzeltme, eksik alanda açık hata vermek oldu.

---

## Ek C: Belge haritası

| Belge | İçerik |
|---|---|
| [`reports/bimcv_317_degerlendirme_raporu.md`](reports/bimcv_317_degerlendirme_raporu.md) | BIMCV-R, altı deney (etiketleme güvenilirliği dahil) |
| [`reports/btb3d_ctrate_degerlendirme_raporu.md`](reports/btb3d_ctrate_degerlendirme_raporu.md) | CT-RATE, kalibre edilmiş bulgu uyumu ve kör değerlendirme |
| [`reports/btb3d_nlst_degerlendirme_raporu.md`](reports/btb3d_nlst_degerlendirme_raporu.md) | NLST, kanser sonucuna karşı üç sistem |
| [`reports/nlst_astra_medmo_kapsamli_degerlendirme_raporu.md`](reports/nlst_astra_medmo_kapsamli_degerlendirme_raporu.md) | NLST, Astra ile MedMo. Bölüm 3'teki kapsam uyarısıyla okunur |
| [`reports/nlst_gercek_etiket_olcumu.txt`](reports/nlst_gercek_etiket_olcumu.txt) | Kilit altında marjinal katkı ölçümü |
| [`reports/faz1_veri_hazirligi_raporu.md`](reports/faz1_veri_hazirligi_raporu.md) | CT-RATE korpusu, şablon yapısı, ölçü çıkarımı |
| [`reports/cikarim_dogruluk_raporu.md`](reports/cikarim_dogruluk_raporu.md) | Çıkarım hattının mühürlü test kümesindeki doğruluğu |
| [`reports/vlm14_sonuc_raporu.md`](reports/vlm14_sonuc_raporu.md) | Metin katmanının uygulanması, Lung-RADS uygulanamazlığı |
| [`reports/vlm12_sonuc_raporu.md`](reports/vlm12_sonuc_raporu.md) | Hasta düzeyinde bölünme dondurması |
| [`docs/40_sema_dondurma_protokol_degisikligi.md`](docs/40_sema_dondurma_protokol_degisikligi.md) | Şema dondurma gerekçesi ve protokol değişikliği |
| [`docs/kararlar.md`](docs/kararlar.md) | Karar defteri |
| [`reports/task15_dondurma.md`](reports/task15_dondurma.md) | Dil ablasyonu kapanışı |
| [`docs/28_task15_genel_bakis.md`](docs/28_task15_genel_bakis.md) | Dil ablasyonunun anlatısı |
| [`docs/25_task15_bolunme_kirlenme_denetimi.md`](docs/25_task15_bolunme_kirlenme_denetimi.md) | RadTr bölünme kirlenmesi denetimi |
| [`reports/task15_ikincil_model_raporu.md`](reports/task15_ikincil_model_raporu.md) | Üç açık kaynak modelin elenmesi |
| [`reports/turkce_dondurma.md`](reports/turkce_dondurma.md) | Türkçe çıkarım katmanının dondurulması |
| [`reports/task17_sonuc_raporu.md`](reports/task17_sonuc_raporu.md) | Malignite gösterge sözlüğünün genişletilmesi |
