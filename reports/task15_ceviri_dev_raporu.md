# TASK-15 · `dev` Çeviri Koşuları — Ne Oldu, Ne Anlama Geliyor

**Tarih:** 2026-09-01
**Kapsam:** RadTr `dev` bölümü, 46 toraks belgesi. `test` açılmadı.
**Kime:** Sude — teknik ayrıntı değil, karar için gereken özet.

---

## 🟢 Şu an neredeyiz — sade özet

**Soru:** Faz 3'te altın etiketlemeyi Türkçe mi İngilizce mi yapalım?
Bunu ölçmek için aynı raporu Türkçe aslından ve İngilizceye çevirip okuyoruz.

**Bugün ne oldu:** 46 belgeyi üç yoldan çevirdik, sonra sorduk — Türkçe okuyunca
bulduğumuz kavramları İngilizce okuyunca da buluyor muyuz?

**Cevap "hayır" çıktı, ama sebebi çeviri değildi.** İki sözlüğümüz eşit
hazırlanmamış. İki öğrenciyi aynı sınava sokup birinin asıl ders kitabından,
diğerinin başka kitaptan çalışmış olması gibi.

> Türkçe rapor *"Kalp boyutları artmıştır"* → Google doğru çeviriyor:
> *"Heart dimensions were increased"* → ama İngilizce sözlüğümüz *"heart size"*
> arıyor, bunu tanımıyor. **189 belgede kaçırıyor.**
>
> Ters yönde de aynısı: `mediastinal` korpusta 214 kez geçiyor ama Türkçe
> desenimiz onu yakalamıyor.

**Neden önemli:** bugün ölçüm yapsaydık *"Türkçe daha iyi"* çıkardı ve yanlış
sebeple çıkardı. Gerçek cevap *"Türkçe sözlüğümüz daha iyi hazırlanmıştı"*
olurdu.

**Sırada:** iki sözlüğün de deliklerini korpusta sayarak kapatmak, sonra
karşılaştırmayı tekrarlamak, ancak sonra `test`e geçmek.

| kol | durum |
|---|---|
| TR (Türkçe aslı) | ✅ hazır |
| EN-genel (Google) | ✅ hazır |
| EN-ucuz (Opus-MT) | ✅ hazır (cümle düzeyinde) |
| EN-tıbbi (MedGemma) | ⚠ 2 koşu başarısız · **3. ve son deneme** (cümle düzeyi) |
| İki sözlüğün onarımı | ⬜ sıradaki iş |
| Altın veri + radyolog | ⬜ sona bırakıldı |

Ayrıntılar aşağıda; okumak zorunda değilsin.

---

## Kısa hüküm

| kol | durum | tek cümlede |
|---|---|---|
| **TR** (Türkçe aslı) | ✅ hazır | çeviri yok, referans |
| **EN-genel** (Google) | ✅ **kullanılabilir** | kalite iyi, bir belgede içerik kaybı |
| **EN-tıbbi** (MedGemma) | ❌ **karantinada** | model post-edit değil, rapor yeniden yazdı |
| **EN-ucuz** (Opus-MT) | 🔄 düzeltildi, yeniden koşuyor | belge düzeyinde çöküyordu, cümle düzeyine alındı |

**Hiçbir tasarım kararı değişmedi.** İki uygulama hatası bulundu ve düzeltildi.
Ölçüm henüz yapılmadı — bunlar çevirinin kendisinin kalite kontrolü.

---

## 1 · Google çevirisi — çalışıyor

46/46 belge çevrildi. Ölçümler korundu, cümleler yerinde, Türkçe kalıntı yok.

**Bir gerçek kayıp bulundu.** `_10_124` belgesinde iki Türkçe cümle İngilizce
çıktıda hiç yok:

> *"…birbirine komşu **3-4 adet** lenf nodu dikkati çekmiştir."*
> *"Sağda **4 ve 5.**"* (kotlar)

Yani Google bir bulguyu düşürmüş. 46'da 1 — ama bu, ablasyonun ölçmek istediği
kaybın tam örneği. Sonuca "çeviri bilgi kaybettirir mi" diye baktığımızda böyle
vakalar sayılacak.

### ⚠ Google iki kez aynı sonucu vermiyor

Aynı 46 belgeyi dakikalar arayla iki kez çevirdik. **5 belge (%11) farklı çıktı.**

| koşu 1 | koşu 2 |
|---|---|
| `taken` | `obtained` |
| `EXAMINATION` | `SCANNING` |
| `abdominal sections … lobulated` | `cross-sections … lobulated in the abdomen` |

Son satır sadece kelime tercihi değil — anatomik konum bir öbekten diğerine
taşınmış.

**Ne demek:** `test` çevirisini yeniden koşarak doğrulayamayız. Bir kez koşulur,
çıkan dosya **kaydın kendisi** olur. Bu yüzden ham çıktıları saklıyoruz.
Ayrıca TR/EN farkının küçük bir kısmı bu titremeden gelecek; büyüklüğünü
iki koşuyu da puanlayarak ölçebiliriz.

---

## 2 · MedGemma — post-edit yapmadı, rapor yeniden yazdı

Uzak makinede 46 belge, 22 dakika, teknik olarak sorunsuz koştu. Girdi zinciri
doğrulandı: MedGemma gerçekten bizim Google çıktımızı işlemiş.

**Sorun teknik değil, davranışsal.**

| ölçüm | sonuç |
|---|---|
| Sayıları koruyan **ve** biçimi bozmayan belge | **0 / 46** |
| Markdown (kalın yazı, madde imi) içeren çıktı | 37 / 46 |
| Ölçüm düşen | 21 / 46 |
| `TECHNIQUE` bölümü kaybolan | 13 / 44 |
| En çok kısalan belge | asıl uzunluğun **%13'ü** |

### En açık örnek

Girdi (`_59_140`), ölçülü ve ayrıntılı:

> *Fracture lines were observed in the lateral sections of the right 3rd and 6th
> ribs… A **2 cm** thick pneumothorax was observed… A pneumatocele, approximately
> **30x25 mm** in size…*

MedGemma çıktısı, tamamı:

```
**IMPRESSION:**
RIGHT-SIDED RIB FRACTURES WITH PNEUMOTHORAX AND PNEUMATOCOLE.
RIGHT-SIDED THYROID NODULE.
ASCENDING AORTA ANEURYSM.
```

Bütün ölçümler yok. Rapor bir **impression** özetine dönmüş. Bu, deneyin
kurallarının (`docs/19` §4/4 — *"bulgu silemez, sayısal değeri değiştiremez,
özetleyemez"*) doğrudan ihlali.

### Neden oldu

İstemimiz *"Rewrite the English radiology report"* diyordu. **"Rewrite" bir
yeniden yazma davetidir.** Markdown ve impression üretmek ayrıca yasaklanmamıştı.
Model, kendisine verilen serbestlikle varsayılan davranışına döndü: yardımcı bir
radyoloji asistanı gibi rapor özetledi.

Yani hata modelin değil, bizim istemimizin.

---

## 3 · Opus-MT — cümle çevirmenine belge vermişiz

İlk koşuda içeriğin %62'sini düşürdü, uydurma üretti. Sebep: Marian/OPUS
modelleri **cümle** çevirir. Tek cümlede kusursuz:

> *"Sağ hemitoraksta plevral sıvı saptanmadı."*
> → *"No pleural fluid was detected in the right hemithorax."*

Belge verince dağılıyor. Kola cümle düzeyinde çalışma izni verildi (senin
onayınla); bölücü **kayıpsız** olmak zorunda — parçalar asıl metni yeniden
üretmezse koşu durur. Türkçeye özgü tuzaklar test edildi: `5. kotlarda` ve
`1.5 cm` bölünmüyor.

---

## 4 · Bulduğum kendi hatalarım

Şeffaflık için: bu turda benim ürettiğim üç hata çıktı ve üçü de düzeltildi.

1. **Yanlış alarm:** sayı/birim denetimi Türkçe→İngilizce kıyasta hatalıydı.
   Türkçe eki birime yapıştırıyor (`1 cm'yi`) ve denetim bunu görmüyordu.
   Google'ın "6 ihlali" gerçekte **1**'di.
2. **Çöken betik:** provenance yazarken bir yol hatası ilk Google koşusunu
   yarıda bıraktı. Çeviri tamamdı, sadece kayıt dosyası yazılamadı.
3. **Eksik denetim:** sayı korunumu tek başına yetmiyormuş. MedGemma ölçümleri
   koruyup metni yine de Markdown'a çevirebiliyor. Yapısal denetim eklendi.

---

## 5 · Ne değişti, ne değişmedi

**Değişmedi:** kollar, karar kuralı, ölçütler, Google tercihi, `test` kilidi.

**Değişti (uygulama):**
- MedGemma istemi v2 — görev "rapor yaz"dan "metin içi terim düzelt"e daraltıldı;
  Markdown, impression ve önsöz açıkça yasaklandı
- Yapısal denetim eklendi — Markdown, özet başlığı, sohbet önsözü ve %70–%140
  dışındaki uzunluk oranı koşuyu durdurur
- Ucuz kol cümle düzeyine alındı, kayıpsızlık zorunlu kılındı

---

## 6 · Sırada ne var

| iş | kim | not |
|---|---|---|
| MedGemma'yı **istem v2 ile** yeniden koş | Sude (uzak makine) | aynı komut, ~22 dk |
| TR + EN-genel + EN-ucuz ile ilk ölçüm | Claude | MedGemma'yı beklemiyor |
| Qwen vs Aya seçimi | Sude koşar | GPU makinesi boşalınca |

**MedGemma çöpe atılmadı.** Model ölçümleri 23 belgede korudu ve akıcı İngilizce
üretti — yapamadığı şey kendini sınırlamaktı, ve o sınırı biz koymamıştık.
İstem v2 çözmezse kol düşürülür; o zaman iki EN kolumuz (Google ve ucuz) kalır
ve rapora *"tıbbi post-edit 4B ölçekli açık modelle güvenilir yapılamadı"*
diye yazılır. Bu da bir bulgudur.

**Bunların hepsi `dev` üzerinde oldu — `test` hiç açılmadı.** `dev`in var olma
sebebi tam olarak buydu.

---

# EK · İlk kol karşılaştırması — ve neden ölçümü şimdi yapamayız

`scripts/31_task15_kol_karsilastirma.py` · 46 `dev` belgesi · 144 kavram

## Ham sayılar

| kol | belge başına bulunan kavram | TR ile Jaccard uyumu |
|---|---:|---:|
| TR (Türkçe aslı) | 24,8 | — |
| EN-genel (Google) | 24,6 | **0,813** |
| EN-ucuz (Opus cümle) | 21,4 | 0,699 |

İlk bakışta okunuşu: *"İngilizceye çevirince kavramların %19'unu kaybediyoruz."*

**Bu okuma yanlış.**

## Kaybın sebebi çeviri değil, sözlük

TR'de bulunup EN'de bulunamayan 122 kavramın en sık 8'i toplamın %78'ini
oluşturuyor. Dördünü tek tek açtım:

| kavram | kayıp | Türkçe metin | Google çevirisi | İngilizce sözlüğün aradığı |
|---|---:|---|---|---|
| `cardiomegaly` | 38 | *Kalp boyutları artmıştır* | *Heart **dimensions** were increased* | `cardiomegaly`, `heart **size** increase` |
| `calcification` | 10 | *kalsifik plaklar* | *calcific plaques* | `calcifications?` |
| `infective_pathology` | 9 | *viral enfeksiyon* | *viral infection* | `infective pathology` |
| `nodule` | 8 | *nodüler infiltrasyonlar* | *nodular infiltrations* | `nodules?`, `nodular formations?` |

Dördünde de **çeviri kusursuz.** *"Heart dimensions were increased,
predominantly left-sided"* cümlesi *"Kalp boyutları sol ağırlıklı olarak
artmıştır"*ı birebir karşılıyor. Bilgi kaybolmuyor — **İngilizce sözlüğümüz o
ifadeyi tanımıyor.**

## Neden böyle oldu

| | Türkçe sözlük | İngilizce sözlük |
|---|---|---|
| geliştirildiği korpus | **RadTr** (bu deneyin verisi) | **CT-RATE** (başka korpus) |
| gördüğü ifadeler | RadTr'nin yazım biçimi | CT-RATE'in yazım biçimi |

Ve kritik ayrıntı: CT-RATE'in İngilizcesi Google çevirisi **artı iki dilli tıp
öğrencilerinin düzeltmesi**. O öğrenciler *"heart dimensions"*ı büyük ihtimalle
*"heart size"* ya da *"cardiomegaly"* diye normalize etti — sözlüğümüzde
`heart size increase` yazmasının sebebi bu.

Yani İngilizce sözlüğümüz **düzeltilmiş** İngilizce bekliyor, biz ona **ham
makine çevirisi** veriyoruz.

## Bunun sonucu

Ablasyonu bugün koşsak sonuç *"Türkçe veri gerekli"* çıkardı — ve **yanlış
sebeple** çıkardı. TASK-14'ün en başta uyardığı hatanın tam kendisi:

> *"Kirlenmenin yönü tehlikeli: Türkçe taraf haksız yere iyi çıkar ve
> ablasyondan yanlışlıkla 'Türkçe veri önemliymiş' sonucu çıkar."*

Kirlenme değil ama **etkisi aynı yönde**: iki kol eşit koşullarda yarışmıyor.

## Ne yapılmalı

Bu, oturumun başında işaretlediğim ve senin onayladığın **EN simetrik sözlük
geçişi**nin gerekçesi. Artık isteğe bağlı bir iyileştirme değil, **sonuç
açıklamadan önce yapılması zorunlu** bir adım:

1. RadTr `train` (223 temiz toraks belgesi) Google ile İngilizceye çevrilir
2. İngilizce sözlük **o metin üzerinde** genişletilir — Türkçe sözlüğün RadTr'de
   gördüğü fırsatın aynısı
3. `test` açılmadan dondurulur
4. Ancak sonra iki kol eşit koşullarda karşılaştırılabilir

⚠ Bu bir "İngilizceyi kayırma" değil, simetri kurma işlemidir. Türkçe sözlük
RadTr'nin 269 belgesini gördü; İngilizce sözlük aynı korpusun tek bir belgesini
görmedi.

**Bu ek ölçüm bir sonuç değildir** (D31). Kanonik altın üretilmedi, F1
hesaplanmadı. Ölçülen şey kolların birbiriyle uyumu ve o uyumun neden bozuk
olduğudur.

---

# EK 2 · Simetrik geçiş — `train` çevirildi, boşluk ölçüldü

**Tarih:** 2026-09-01 · 223 `train` toraks belgesi · 245.187 karakter Google'dan geçti

## Boşluğun büyüklüğü

| ölçüm | sonuç |
|---|---|
| TR bulup EN bulamadığı | **678** belge-kavram |
| ikisinin de bulduğu | 4.840 |
| **boşluk oranı** | **%12,3** |
| etkilenen kavram | **41 / 144** |

`dev`de %19 görünmüştü, `train`de %12,3. Aynı yönde, aynı sebep.

## İki tür boşluk var

**A · Tam kör noktalar** — İngilizce sözlük o kavramı bu korpusta **hiç**
bulamıyor (`ikisinde de var = 0`):

| kavram | boşluk | İngilizce metinde geçen | sözlüğün aradığı |
|---|---:|---|---|
| `cardiomegaly` | **189** | *Heart **dimensions** were increased* | `cardiomegaly`, `heart size increase` |
| `infective_pathology` | 34 | *viral **infection*** | `infective pathology` |
| `tumor` | 3 | *metastatic solid nodules* | `tumou?rs?`, `tumou?ral` |
| `lytic_destructive_lesion` | 3 | *lytic hypodense areas* | `lytic-destructive lesion` |

**B · Kısmi boşluklar** — bazı yüzeyler var, bazıları eksik:

| kavram | boşluk | ikisinde de var |
|---|---:|---:|
| `diffuse` | 67 | 1 |
| `dilatation` | 58 | 44 |
| `calcification` | 41 | 44 |
| `lower_lobe` | 36 | 119 |
| `lobulated` | 32 | 6 |
| `nodule` | 32 | 56 |

## Kök sebep tek cümlede

**Türkçe sözlüğün desenleri korpustan türetildi, İngilizce sözlüğünkiler kavram
adının çevirisi.**

Türkçe tarafta D42 bunu zaten kaydetmişti: *"cardiomegaly için 'kardiyomegali'
deseni 0 anma verdi, 'kalp boyutları' 313."* Yani Türkçe sözlük korpusun nasıl
yazdığına bakıp deseni ona göre yazdı.

İngilizce tarafta bu yapılmadı: `infective pathology` deseni Türkçe *"enfektif
patoloji"*nin birebir çevirisi, ama metin *"viral infection"* diyor. `cardiomegaly`
deseni sözlük terimini arıyor, metin *"heart dimensions"* diyor.

## ⚠ Yöntemin sınırı — dürüstlük notu

Yukarıdaki "İngilizce metinde geçen" sütununu, Türkçe eşleşmenin bulunduğu
cümlenin **aynı sıradaki** İngilizce karşılığını alarak ürettim. Google cümle
sırasını genelde koruyor ama **her zaman değil** — `infective_pathology`
örneklerinin 3'ünden 2'si yanlış cümleye denk geldi.

Bu hizalama yalnızca **aday yüzey önermek** için kullanılıyor, ölçüme girmiyor.
Gerçek yüzey türetmesi frekans tabanlı yapılacak (D16: korpustan türet, ithal
etme).

## Bu bir kayırma değil, simetri

Eklenecek yüzeyler *"EN kazansın diye"* seçilmiyor. Ölçüt Türkçe tarafta
uygulananın aynısı:

1. Yüzey kavramı **gerçekten ifade etmeli** — *"heart dimensions were increased"*
   kardiyomegalidir, bunu bir radyolog tartışmaz
2. Korpusta **ölçülmüş desteği** olmalı (D16)
3. Yalnız `train`de türetilir, `test` görülmeden dondurulur

Türkçe sözlük RadTr'nin 269 belgesinde bu fırsatı kullandı; İngilizce sözlük
şimdiye kadar tek belgesini görmedi.

## Ters yön de ölçülmeli

`dev`de EN'de bulunup TR'de bulunamayan 112 kavram-belge vardı. Simetri için o
yön de `train`de ölçülüp raporlanacak — eksik olan yalnız İngilizce sözlük
olmayabilir.

---

# EK 3 · Ters yön ölçüldü — ve önceki teşhisim tek yanlıymış

EK 2'de *"İngilizce sözlük geride"* demiştim. Ters yönü de ölçünce tablo
değişti: **iki sözlüğün de boşluğu var.**

| yön | belge-kavram | etkilenen kavram | anlamı |
|---|---:|---:|---|
| yalnız TR buldu | **678** | 41 | İngilizce sözlük boşluğu |
| yalnız EN buldu | **562** | **58** | **Türkçe sözlük boşluğu** |
| ikisi de buldu | 4.840 | | |

Türkçe sözlük **daha çok kavramda** (58 vs 41) boşluk veriyor, İngilizce sözlük
**daha çok belgede** (678 vs 562). Net fark 116 — 678 rakamının tek başına
düşündürdüğünden çok daha dengeli.

## Türkçe sözlükte bulunan gerçek hatalar

Korpusta ölçtüm, ikisi tartışmasız:

| kavram | mevcut desen | bulduğu | korpusta geçen | kaçırdığı |
|---|---|---:|---|---|
| `mediastinum` | `mediasten` | 82 | **`mediastinal` 214** | çoğunluk |
| `rib` | `kosta\|kaburga` | 15 | `kot` 12 · `kotlarda` 5 · `kotta` 5 | 22 |

`mediasten` deseni `mediastinal`i **yakalamıyor** — Türkçe radyoloji "mediastinal"
yazıyor (i ile), desen "mediasten" arıyor (e ile). Aynı şekilde Türkçe radyolojide
kaburga "kot" diye geçiyor; desende yok.

Bunlar tasarım tercihi değil, **desen hatası.**

`stent` (78) ve `density` (32) farkı ise açıklanmadı — Türkçe desenleri çekimli
biçimleri zaten yakalıyor. Bunlar ya gerçek çeviri farkı ya İngilizce desenin
fazla ateşlemesi; ayrıca incelenecek.

## Bunun planı nasıl değiştirdiği

**Değişen:** simetrik geçiş yalnız İngilizce sözlüğü değil, **iki sözlüğü birden**
düzeltmeli. Yoksa bu sefer ters yönde eşitsizlik kurmuş oluruz.

**Değişmeyen:** iş yine `train`de yapılır, korpustan ölçülerek türetilir,
`test` görülmeden dondurulur.

⚠ Yöntem notu: bir sözlüğün boşluğunu diğerinin bulgusuyla tespit ediyoruz. Bu
dairesel değil ama **kesin de değil** — biri buluyor diğeri bulamıyorsa
*birisi* yanılıyordur; hangisi olduğuna korpus ölçümü ve anlam kontrolü karar
verir. `mediastinal` örneğinde Türkçe sözlüğün yanıldığı korpus sayımıyla
gösterildi, İngilizce sözlüğün bulgusuna güvenilerek değil.

## Aday yüzey türetmesi çalışıyor

`scripts/33_task15_en_yuzey_adaylari.py` boşluk/kontrol belge karşılaştırmasıyla
aday üretiyor. Net vakalarda doğru cevabı veriyor:

| kavram | üretilen aday | boşluk kapsaması | gürültü |
|---|---|---:|---:|
| `cardiomegaly` | **`heart dimensions`** | %80 | %0,0 |
| `diffuse` | **`widespread`** | %99 | %0,0 |
| `infective_pathology` | **`infection`** | %65 | %1,6 |

Ama gürültü de üretiyor: `cardiomegaly` için `main bronchi are`, `diffuse` için
`coronary artery` gibi **birlikte geçen kalıp metin** adayları. Sebep raporların
şablonlu olması. Bu yüzden betik aday üretiyor, sözlük yazmıyor — her aday
anlam kontrolünden geçecek.


---

# EK 4 · MedGemma koşu 2 sonucu ve son deneme kararı

| koşu | istem | birim | temiz belge |
|---|---|---|---|
| 1 | v1 | belge | **0 / 46** |
| 2 | v2 | belge | **26 / 46 (%57)** |
| 3 | v3 | **cümle** | son deneme |

İstem düzeltmesi sıfırdan %57'ye çıkardı ama yetmedi. Kalan iki sorun:

**Markdown biçimleme (20 belge)** — model raporu yeniden biçimlendiriyor.

**Düşünme izi (8 belge)** — model cevaptan önce yüksek sesle düşünüyor ve bunu
çıktıya yazıyor:

```
<unused94>thought
The user wants me to correct medical terminology...
Let's break down the text sentence by sentence:
1. ...
```

"Sayı eklenmiş" ihlallerinin çoğu bu izdeki madde numaralarından geliyor.

## Koşu 3'te değişenler

1. **Cümle cümle post-edit** — tek cümleyi rapor biçimine sokamazsın, "adım adım
   inceleyelim" planı da yapamazsın. Aynı çözüm Opus-MT'de işe yaramıştı (D55).
2. **İstem v3** — açık "hemen cevapla, adım adım düşünme" talimatı
3. **Düşünme izi ihlal sayılıyor** — silinmiyor, işaretleniyor. Silmek cevabın
   nerede başladığını tahmin etmek olurdu ve sessizce veri bozardı.
4. **Erken durdurma düzeltildi** — koşu 2'de ilk 5'in 4'ü bozuktu ama kural
   "hepsi" diyordu, tetiklenmedi. Artık ilk 8'in %60'ı yeterli.
5. `max_new_tokens` 1024 → 320

## ⛔ Önceden bağlanan durma kuralı

**Koşu 3'te temizlik %90'ın altında kalırsa kol düşürülür.** Dördüncü deneme
yok. Karar sonucu görmeden verildi.

Kol düşerse rapora şu yazılır: *"tıbbi post-edit 4B ölçekli açık modelle
sözleşmeye uygun biçimde yapılamadı"* — bu da bir bulgudur. TR + EN-genel +
EN-ucuz ile devam edilir.
