# Malignite Gösterge Sözlüğünün Genişletilmesi ve Değerlendirme Şemasına Etkisi

**TASK-17 Sonuç Raporu · 2026-09-07**
Korpus: CT-RATE toraks BT, 25.692 rapor — geliştirme havuzu 20.576 çalışma

---

## 1. Özet

TASK-17, malignite değerlendirme şemasının kullanamadığı terimleri çıkarım
sözlüğüne kazandırmak ve sözlük kaynaklı uyumsuzlukları gidermek amacıyla
yürütüldü. Çıkarım sözlüğü 88'den 106 kavrama, şemanın malignite envanteri
10'dan 22 kavrama çıkarıldı. Sabit bir evrende ölçüldüğünde, malignite
bağlamlı 10.081 cümlenin yapılandırılmış malignite kavramı üretmeyen oranı
%4,0'ten %0,4'e indi. Kilitli sınır takımındaki sözlük kaynaklı üç
uyumsuzluğun üçü de giderildi; genel uyum 20/30'dan 24/30'a yükseldi ve 23
kontrol vakasında yanlış pozitif koruma ihlali görülmedi.

Buna karşılık hedef uyumu eşiği sağlanmadı, dağılım kapısı karar veremez
bulundu ve yeni eklenen `known_malignancy` tetikleyicisinin son sürümü henüz
bağımsız olarak doğrulanmadı. Bu nedenle **TASK-17 kendi kapsamı bakımından
tamamlanmış, ancak değerlendirme şeması `sema-0.9-taslak` olarak
bırakılmıştır.**

---

## 2. Amaç ve kapsam

Bir önceki görevde malignite değerlendirme şeması yazıldı ve kilitli bir
sınama kümesine karşı sınandı; üç kabul kapısından yalnız biri geçildi.
Devredilen teşhis, geçilemeyen iki kapının ortak kök nedeninin çıkarım
sözlüğü olduğuydu: şema doğru kural yazsa bile, tanımadığı bir terim için
hiçbir varlık üretilmediğinden kural tetiklenemiyordu.

Bu görevin kapsamı sözlük katmanıdır. Karar kuralları önceki görevde
yazılmıştır ve dilden bağımsızdır; burada yalnızca *hangi metin ifadesinin
hangi kavramı tetiklediği* belirlenmiştir. Tek istisna, önceki görevde karara
bağlanıp kodlanmamış bir kuralın uygulanmasıdır (§4).

Klinik uzman onayı bu görevin kapsamı dışındadır ve alınmamıştır.

---

## 3. Yöntem

Sözlüğe eklenen her girdi üç alan taşır: dayandığı belge, korpustaki ölçülmüş
desteği ve amacı. Bu ayrım kapsam iddiasının şişmesini engeller; sözlüğün 12
yeni girdisi bu korpusta ölçülmüş desteğe sahiptir, 6'sı hiç geçmez ve yalnız
hedef kohortta kaçırmamak için transfer amaçlı eklenmiştir.

Liste SHA-256 ile dondurulduktan sonra varlık tablosu tüm korpus üzerinde
yeniden üretildi. Bu sıra bağlayıcı tutuldu: sonuç görülüp sözlüğün
değiştirilmesi yapısal olarak engellensin diye.

Mühürlü `test-v2` kümesine, önceden yazılmış bir protokolle bir kez bakıldı
(§6.3).

---

## 4. Temel sonuçlar

| ölçüt | önce | sonra |
|---|---:|---:|
| Sözlük boşluğu (sabit evren, 10.081 cümle) | %4,0 | **%0,4** |
| Şema sınavı — sınır takımı | 20/30 | **24/30** |
| Sözlük kaynaklı uyumsuzluk | 3 | **0** |
| `known_malignancy` üretimi | 0 | **156 çalışma** |
| Yanlış pozitif koruma kapısı | 0 ihlal | **0 ihlal** |
| Çıkarım sözlüğü | 88 kavram | **106** |
| Malignite envanteri | 10 kavram | **22** |
| Otomatik test | 400 | **450** |

Sınır takımında kalan altı uyumsuzluğun dördü girdi kalite filtresinin
bilinen etkisidir; biri hedef atama yordamı ile motorun yorum farkından,
biri kavram listesindeki bir eksikten kaynaklanır. Rapor takımındaki iki
uyumsuzluk ise önceki görevde kalıcı olarak ilan edilmiş ayrı bir yordam
farkıdır ve sınır takımıyla karıştırılmamalıdır.

Yanlış pozitif koruması ihlalsizdir: açıkça benign, normal veya olumsuzlanmış
23 kontrol vakasının hiçbirinde malignite şüphesi üretilmemiştir.

### Kodlanmamış bir şema kuralı uygulandı

Ölçeğin en üst basamağı olan *bilinen kanser* düzeyi, önceki görevde karara
bağlanmış ancak kodlanmamıştı; tanımlıydı, örnekleri yazılmıştı, fakat hiç
üretilemiyordu. Tetikleyicisi korpustan ölçülerek yazıldı. Geliştirme
havuzundaki aday incelemesinde en yüksek oranlı işaret, *"in the follow-up"*
ifadesinin bir kanser terimiyle birlikte geçmesiydi (104 cümlenin 74'ü).

Kuralın ürettiği çalışma sayısı üç aşamada değişti: ilk koşumda 166 çalışma
üretildi; bölüm anahtarı düzeltmesi (§6.2) bunu 160'a, radyolojik nedenselliği
kanser öyküsü sayan `due to / because of` dalının kaldırılması ise **156**'ya
düşürdü. Son sürümün kör doğrulaması henüz tamamlanmamıştır.

Bu görevde yazılan ikinci bir kural — şablon nodüllerin bastırılması — dış
inceleme sonucunda yeterli dayanağı bulunmadığı için geri alınmıştır (§7).

### Türkçe yüzeyler

Hedef kohort Türkçe orijinal raporlardan oluşacağı için Türkçe yüzey
envanterine, kaynakla veya korpus ölçümüyle doğrulanan 16 karşılık eklendi;
yüzey sayısı 144'ten 160'a çıktı. Güvenilir karşılığı gösterilemeyen
`complete_calcification` eklenmedi.

---

## 5. Sözlük kararları ve reddedilen adaylar

Bir terimin sözlüğe girmesi için korpusta geçmesi yeterli sayılmadı;
deseninin ne yakaladığına bakıldı. Üç aday bu nedenle ölçülüp reddedildi:

- *"Diffüz kalsifikasyon"* 491 cümlede geçiyor, ancak tamamı damar
  ateromudur; kılavuzun benign nodül ölçütü olan tam kalsifikasyon ile aynı
  kavram değildir.
- *"Konsantrik"* 16 cümlede geçiyor ve tamamı damar veya organ duvarı
  kalınlaşmasıdır.
- *"Malignant"* sıfatı 142 cümlede geçiyor; gözlem kavramı olarak eklenmesi
  kavram adının metnin söylemediğini iddia etmesi olurdu, bu nedenle
  niteleyici olarak eklendi.

Planın bir varsayımı da ölçümle düzeltildi. Önceki görev `lymphoma`,
`sarcoma` ve `mesothelioma` terimlerini korpusta hiç geçmeyen örnekler olarak
göstermişti; ölçüm bunları sırasıyla 98, 18 ve 17 cümlede buldu ve terimler
ölçüm değiştiren kademeye alındı.

Genişletme tamamlandıktan sonra kalan boşluk ayrıca tarandı. Tarama üç eksik
buldu: en yalın terim olan `cancer` sözlükte hiç yoktu, `malignant` sıfatı
141 cümlenin 49'unda tek kanıttı ve `metastasized` fiil biçimi kaçıyordu.
Üçü de kapatıldı. Kalan %0,4'ün doğası uzun kuyruktur; eşleştirici desenleri
kelime sınırıyla sardığı için önekli bileşikler (`cholangiocarcinoma`, 3
cümle) kaçmaktadır. Bu sınır kasıtlıdır: sınır kaldırılırsa `mass` deseni
`massive` içinde de eşleşir.

---

## 6. Veri bütünlüğü sorunları ve düzeltmeler

Aşağıdaki iki sorun bu görevin ürünü değil, mevcut durumun tespitidir; ikisi
de düzeltilmiştir.

### 6.1 Dondurulmuş varlık tablosu kendi sözlüğüyle uyuşmuyordu

Tablo 2026-08-28'de üretilmiş, sözlük 2026-09-02'de onarılmış, ancak tablo
bir daha üretilmemişti. Onarımla eklenen bir yazım biçimi eski tabloda hiç
geçmezken yeniden üretimde 7.294 kez geçmektedir. Bu, önceki görevin
ölçümlerinin ilan ettikleri sözlük sürümünü tarif etmediği anlamına gelir.

Etkiyi karıştırmamak için temiz bir referans tablo üretildi ve iki fark
ayrıldı: uygulanmamış onarımların payı 17.421 varlık, bu görevin sözlük
genişletmesinin payı 629 varlıktır. İlgili dondurma kaydına düzeltme eki
yazılmıştır.

Sürüm etiketi bugün yalnız kodu tarif etmektedir; üretimde kullanılan sözlük
sürümü üretilen tabloda taşınmadığı için bu tutarsızlık üç aydır fark
edilmemişti.

### 6.2 Cümle indisi bölüm bilgisi olmadan kullanılıyordu

Rapor bölümleri ayrı indislendiğinden, bölüm bilgisi olmadan yapılan
birleştirme iki bölümün aynı indisli cümlelerini karıştırmaktadır. Korpusta
77.855 `(study_id, sent_idx)` anahtarı iki bölümde birden tekrar etmekte ve
toplam 155.710 cümle satırı bu çakışmalardan etkilenmektedir.

Sonucu, varlığa yanlış cümle metninin bağlanması ve şemanın bütün cümle
düzeyi kurallarının etkilenmesidir; Findings bölümündeki bir benign hüküm,
Impression bölümünün aynı indisli cümlesini ezebilmekteydi. Kusur beş yerde
bulunup düzeltilmiş, bu hata sınıfını yakalayan iki gerileme testi
eklenmiştir.

### 6.3 Mühürlü test kümesine tek bakış

`test-v2` kümesine, önceden yazılmış bir protokolle bir kez bakıldı. TASK-17'nin
eklediği kavramlar bu kümenin 295 cümlesinde yalnızca bir yeni varlık üretti;
duyarlılık ölçüsündeki değişim bir işaretleyici için +0,1, diğeri için 0,0
puandır. Bu bir etkisizlik kanıtı değil, ölçüm gücü yokluğudur: yeni kavramlar
nadirdir ve 295 cümlelik bir kümede beklenen sayı zaten sıfıra yakındır.

Aynı ölçüm §6.1'deki bulguyu da doğrulamıştır: bayat tablonun düzeltilmesi tek
başına duyarlılığı yaklaşık 1,5 puan değiştirmektedir; yani önceki görevde
raporlanan doğruluk sayısı, uygulanmamış sözlük onarımları nedeniyle olması
gerekenden düşüktür.

---

## 7. Geçerlilik ve sınırlılıklar

Dış incelemeler sonucunda planın kabul ölçütleri sıkılaştırıldı, yeterli
dayanağı olmayan nodül bastırma kuralı geri alındı, dağılım kapısının hedef
değişkenle uyumsuz olduğu gösterildi ve bölüm anahtarı hatası düzeltildi.
Kabul edilen değişiklikler karar kayıtlarına ve gerileme testlerine
işlenmiştir.

Bilinen sınırlar:

1. Klinik uzman onayı alınmamıştır; kaynakta yazılı karşılığı olmayan her
   öncelik ve eşik belgelenmiş mühendislik varsayılanı olarak kalır.
2. Patoloji doğrulaması yoktur. Ölçülen şey modelin radyoloğun raporuyla
   uyuşmasıdır, klinik doğruluk değildir.
3. `known_malignancy` tetikleyicisinin son sürümü bağımsız olarak
   doğrulanmamıştır. Kırk vakalık kör doğrulama paketi hazırdır.
4. Benign gösterge envanteri korpustan türetilememiştir. Türetme ölçütü
   sınanmış ve geçersiz çıkmıştır: korpusun baskın benign terimi 9.641
   cümlede geçmesine karşın açık benign hükümle kesişimi sıfırdır, çünkü
   sekel tartışılmaz, olgu olarak yazılır. Mevcut envanter değiştirilmemiş,
   statüsü belgelenmiş mühendislik varsayılanı olarak düzeltilmiştir.
5. Türkçe yüzeyler uzman onayından geçmemiştir; `neoplasm` kavramı için
   İngilizce ve Türkçe dosyalar arasında ilan edilmiş bir çelişki vardır.
6. Kohort uyumsuzluğu sürmektedir: kılavuzlar tarama ve insidental nodül
   bağlamına yazılmıştır, korpus ise genel toraks BT'dir (yaş medyanı 46,
   %21 COVID).

---

## 8. Kapanış hükmü ve devredilen işler

TASK-17'nin sözlük kapsamı tamamlanmıştır. Aşağıdaki işler TASK-17'nin eksik
kalemleri değil, `sema-1.0` dondurmasının önkoşulları olarak devredilmiştir.

Şema iki nedenle dondurulmamıştır. Hedef uyumu %100 eşiğini geçmemektedir
(24/30); kalan uyumsuzlukların kök nedenleri belirlenmiştir ve hiçbiri sözlük
kaynaklı değildir. Dağılım kapısı ise karar verememektedir: kapının çapası
şüphe dilini ölçer, oysa bu görevde çalışır hâle gelen bilinen kanser düzeyi
şüphe değil belgelenmiş olgudur. Kapının kendi türeyiş metni, motorun bu
düzeyi üretmediği varsayımını açıkça yazmaktaydı; bu görev o varsayımı
geçersiz kılmıştır. Dış incelemenin hükmüyle kapı kalmış olarak kaydedilmiş,
ancak şema hakkında kabul-ret kararı veremez ilan edilmiştir.

Devredilen üç iş:

1. `known_malignancy` tetikleyicisinin kör doğrulaması (paket hazır).
2. Kalan altı hedef uyumsuzluğunun tek tek karara bağlanması; dördü girdi
   kalite filtresinin etkisi olduğundan çözümü çıkarım katmanındadır.
3. Dağılım kapısının, radyolojik şüphe ile belgelenmiş kanser öyküsünü ayrı
   doğrulayacak biçimde yeniden tanımlanması.

---

## 9. Sürümler ve yeniden üretilebilirlik

| bileşen | önce | sonra |
|---|---|---|
| Çıkarım sözlüğü | `bulgu-1.1` | `bulgu-1.2` |
| Varlık tablosu | `ent-1.0` | `ent-1.1` |
| Türkçe yüzey envanteri | `tr-1.0` | `tr-1.1` |
| Değerlendirme şeması | `sema-0.9-taslak` | değişmedi |

Rapordaki sayıların tümü depodaki betiklerle yeniden üretilebilir; hiçbiri
elle yazılmamıştır. Ölçüm betikleri `scripts/52`–`scripts/58`, şema sınavı ve
dağılım `scripts/48`–`scripts/49` numaralarındadır. Sözlük genişletmesinin
kilidi `configs/task17_tier_kilidi.json`, alınan bağlayıcı kararlar ve
ölçülmüş gerekçeleri `docs/kararlar.md` içindedir.
