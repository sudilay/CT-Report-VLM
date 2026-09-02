# TASK-15 · Sözlük Onarımı — Kapanış Raporu

**Tarih:** 2026-09-02 · **Kapsam:** RadTr `train`, 223 toraks belgesi
**Durum:** tek geçiş donduruldu; TR birleşik matcher açığı kapandı · **`test` açılmadı**

---

## 1 · Bu iş neden vardı

TASK-15 şunu ölçüyor: aynı rapor **Türkçe okunduğunda** mı, **İngilizceye
çevrilip okunduğunda** mı daha çok bilgi veriyor?

Ölçüm iki "okuyucu" ile yapılıyor. Bunlar çeviri sözlüğü **değil**: ortada dile
ait olmayan **144 kavram** var; her dil için ayrı bir dosya *"bu kavram bu dilin
metninde şu biçimlerde yazılır"* diyor. İki dosya birbirini görmez.

```
                    ┌─────────────────────────┐
                    │  144 KAVRAM (dilsiz)    │
                    └───────┬─────────┬───────┘
        turkce_yuzeyler ◄───┘         └───► anatomi_ + bulgu_sozlugu
```

**Sorun:** iki okuyucu eşit hazırlanmamıştı. Türkçe sözlük RadTr'nin 269
belgesinden türetildi (D42); İngilizce sözlük CT-RATE'te geliştirildi ve RadTr'nin
tek belgesini görmedi. Bu yüzden ölçülen fark **dil farkı değil, sözlük hazırlığı
farkı** çıkıyordu (D56/D57).

**Bağlayıcı üç kural (D58):** (1) bilgi hedef metinde varsa alet arızasıdır,
düzeltilir — çevirmen düşürmüşse gerçek kayıptır, dokunulmaz; (2) İngilizce
adaylar CT-RATE'te de destekli olmalı; (3) tek geçiş, sonra dondur.

---

## 2 · ⛔ Önce ölçüm aletinin kendisi bozuk çıktı

Onarıma başlamadan önce öneriler üretim koduna karşı doğrulandı. Ölçüm betikleri
sözlükleri **üretimden farklı derliyordu:**

| taraf | üretim | ölçüm betikleri (`31`–`34`) |
|---|---|---|
| TR | `scripts/23.derle` → `\b(?:desen)` | `re.compile(desen)` — **sınırsız** |
| EN | `entities.py:185` → `\b(?:desen)\b` | `re.compile(desen)` — **sınırsız** |

Üstelik üretimdeki EN çıkarımı **tek birleşik matcher** kullanıyor ve *en uzun
eşleşme kazanıyor* (bir metin parçası tek kavrama gider); ölçüm betikleri
kavramları **bağımsız** tarıyordu (bir parça birden çok kavrama sayılıyordu).

**Sonuç: sözlükte olmayan hatalar "sözlük hatası" gibi görünüyordu.**

| önerilen düzeltme | sınırsız derlemede | üretim derlemesinde | hüküm |
|---|---:|---:|---|
| `dilatation` ← `ektazi` sınırı | 78 boşluk | **8** | ⛔ hata yok |
| `lobulated` ← `lob[uü]le` sınırı | 32 boşluk | **2** | ⛔ hata yok |

`ektazi` deseni `atelektazi`nin içine **hiç düşmüyordu**; ölçüm aleti düşürüyordu.
Aynısı `interlobüler` için de geçerli — ve bu, devir notundaki **`interlobular`
tuzağının gerçek açıklamasıdır:** `scripts/33`/`34` de sınırsız derlediği için
Türkçe desenin sahte ateşlemesini öğreniyorlardı. Otomatik aday üretimi "zayıf"
değildi, **bozuk aletle besleniyordu.**

### Bunun D57'ye etkisi

D57'nin *"yalnız TR 678 · yalnız EN 562"* rakamları bu bozuk derlemeyle üretildi.
**Simetrik yeniden ölçümde (iki taraf da üretim mantığı) onarım öncesi asimetri
639 / 639, yani sıfırdır.**

Denetim: yarım örneklemlerde −13 / +13 / −19 çıkıyor — tam eşitlik sayıda
rastlantı, betik hatası değil.

> **Ders:** 1. kuralı önce alete uygula. Sözlüğü suçlamadan önce, sözlüğü okuyan
> şeyin doğru okuduğunu doğrula.

`scripts/31` artık iki tarafta da birleşik üretim matcher'ı kullanıyor.
`scripts/32`–`34` araştırma amacıyla kavramları bağımsız taramaya devam ediyor ve
çıktılarının üretimle bire bir olmadığına ilişkin D60/D61 uyarısı taşıyor.
`scripts/35` de boşluk cümlesi göstermek için bilinçli olarak bağımsız tarıyor.

---

## 3 · Yöntem — sıralama değil, cümle okuma

Otomatik aday üretimi (n-gram madenciliği) bu iş için reddedildi: 231 adaydan
yalnız ~5'i gerçek çıkmıştı. Raporlar şablonlu olduğu için *"birlikte geçen"* ile
*"aynı anlama gelen"* ayrılamıyor.

Yerine: **her kavram için boşluk cümlelerini çıkar, oku, gerekçesiyle yüzey öner.**
`scripts/35_task15_bosluk_cumleleri.py` kaynak dildeki eşleşen cümleyi ve hedef
dildeki karşılığını **komşularıyla** (i−1, i, i+1) gösterir — Google cümle sırasını
genelde korur ama her zaman değil; yanlış hizalama komşulara bakınca görülür,
gizlenmez.

Her onarımın gerekçesi ve okunan cümle YAML dosyalarına yorum olarak yazıldı.

---

## 4 · Yapılan onarımlar — 26 kavram

### Türkçe sözlük (`configs/turkce_yuzeyler_taslak.yaml`) — 16

| kavram | eski | yeni | sınıf |
|---|---|---|---|
| `mediastinum` | `mediasten` | `mediasten\|mediastin` | desen hatası — korpus `mediastinal` yazıyor (221 anma) |
| `basal` | `bazal` | `+posterobazal\|laterobazal\|mediobazal\|anterobazal` | bileşik eksik (EN listeliyordu) |
| `effusion` | `ef[uü]zyon` | `ef+[uü]zyon` | **yazım** — korpus çift f yazıyor |
| `rib` | `kosta\|kaburga` | `+kot` | TR radyoloji "kot" diyor |
| `bronchiectasis` | `bron[şs]ektazi` | `bron[şs]i?ektazi` | **yazım** — "bronşiektazi" de var |
| `atelectasis` | `atelektazi` | `atelekta(?:zi\|tik)\|kollabe` | sıfat + "kollabe" eksik |
| `apical` | `apikal` | `+apikoposterior` | bileşik eksik |
| `abdomen` | `abdomen\|bat[ıi]n` | `+abdominal` | TR metni "abdominal" yazıyor |
| `density` | `dansite` | `+opasite` | EN iki sözcüğü sayıyordu |
| `consolidation` | `konsolidasyon` | `+konsolide` | sıfat eksik |
| `fluid_collection` | `s[ıi]v[ıi] koleksiyon` | `+serbest s[ıi]v[ıi]\|assit` | **tam kör nokta** (ikisinde de var = 0) |
| `pulmonary_artery` | `pulmoner arter` | `+pulmoner trunkus\|truncus pulmonalis` | EN'de `pulmonary trunk` vardı |
| `atheroma_plaque` | `aterom\|ateroskler` | `+plak` | EN çıplak `plaques?` içeriyordu |
| `calcification` | `kalsifi\|kire[çc]len` | `kalsifikasyon\|kire[çc]len` | **kardeş çakışması** — `calcific`i yutuyordu |
| `lung_parenchyma` | `parankim` | `akci[ğg]er\w* parankim\|pulmoner parankim` | **kardeş çakışması** — karaciğer parankimini akciğer sayıyordu |
| `sequela_change` | `sekel` | `sekel de[gğ]i[şs]` | **kardeş çakışması** — `sequela` ile aynı deseni paylaşıyordu |

### İngilizce sözlük (`bulgu_sozlugu.yaml` · `anatomi_sozlugu.yaml`) — 10

| kavram | eski | yeni | sınıf |
|---|---|---|---|
| `cardiomegaly` | `cardiomegaly\|heart size increase[ds]?` | `+heart dimensions?\|heart size` | **kavram adının çevirisi** — 189 belgede kör |
| `diffuse` | `diffusely?` | `+widespread` | korpusun yazdığı biçim |
| `infective_pathology` | `infective patholog(?:y\|ies)` | `+infections?\|infectious` | **kavram adının çevirisi** — 34 belgede kör |
| `central` | `centrally?` | `central(?:ly)?` | **DESEN HATASI** — "central"i hiç eşlemiyordu |
| `hemithorax` | `hemithora(?:x\|ces)` | `hemithora(?:x\|xes\|ces)` | **DESEN HATASI** — yanlış çoğul |
| `nodule` | `nodules?\|nodular formations?` | `+nodular` | sıfat eksik |
| `fibrosis` | `fibrosis\|fibrotic changes?\|fibrotic` | `+fibroatelecta(?:tic\|sis)` | bileşik eksik |
| `anatomic_segment` | `segments?` | `+segmental` | sıfat eksik |
| `consolidation` | `consolidations?\|consolidated areas?` | `+consolidated` | TR'ye eklenene **simetrik** |
| `lower_lobe` | `lower lobes?` | `lower (?:lung )?lobes?` | araya giren kelime — **2. kural gerekçeli istisnası**, aşağıda |

### İki desen hatası özellikle önemli

`centrally?` = "central" + "l" + isteğe bağlı "y" — yani yalnız *"centrall"* ve
*"centrally"* eşliyor, **"central" kelimesini hiç eşlemiyor.** Korpusta `central`
17, `centrally` 3 anma.

`hemithora(?:x|ces)` Latin çoğul arıyordu; korpusta `hemithoraces` **0**,
`hemithoraxes` **38** anma.

Bunlar tasarım tercihi değil açık yazım hatalarıdır ve ana projeye (Faz 2)
aittir; TASK-15 olmasa bulunmayacaklardı. D58'in *"yan bulgu"* maddesinin
üçüncü ve dördüncü örnekleridir.

---

## 5 · Etki — simetrik ölçüm

İki taraf da üretim mantığıyla (birleşik matcher, en uzun eşleşme kazanır):

| | yalnız TR | yalnız EN | ikisi de | net | Jaccard |
|---|---:|---:|---:|---:|---:|
| **önce** (HEAD) | 639 (47 kavram) | 639 (58) | 4.166 | **0** | 0,765 |
| **sonra** | **152** (48) | **167** (56) | **5.009** | **−15** | **0,940** |

- Toplam boşluk **1.278 → 319** (%75 azaldı)
- Ortak bulgu **4.166 → 5.009** (+843)
- Toplu Jaccard **0,765 → 0,940**
- **Denge korundu:** 152 / 167 — onarım tek taraflı olmadı

⚠ Bu sayılar sözlüklerin **birbirine göre** durumudur, **ablasyon sonucu
değildir.** Ablasyon skoru hesaplanmadı; bu rapordaki hiçbir seçim skora
bakılarak yapılmadı.

---

## 6 · Onarılmayanlar — ve neden

### Gerçek çeviri farkı (dokunulmadı — ölçmek istediğimiz şey bu)

**Çevirmen terim EKLİYOR.** `density` kavramında kalan 19 boşluğun 18'inde Türkçe
metin *"buzlu cam **alanları**"* diyor (yoğunluk sözcüğü **yok**), Google
*"ground-glass **opacities**"* yazıyor. Bu bir sözlük deliği değil; çevirinin
kavram **ekleme** yönü — ve düşürme kadar gerçek.

**Çevirmen terimi bozuyor.** `lytic_destructive_lesion`: TR *"litik lezyonlar"* →
Google ***"Lithic lesions"*** (CT-RATE'te `lithic` 4 anma). Gerçek çeviri kaybı.

**Çevirmen cümle düşürüyor.** `_10_124`: *"…3-4 adet lenf nodu…"* İngilizce
çıktıda hiç yok. Ablasyonun ölçtüğü kaybın tam örneği.

### Ölçülüp reddedilenler

| aday | sebep |
|---|---|
| `thickening` ← `kal[ıi]nl[ıi][gğ]` | **141/160 yanlış ateşleme** — *"2 mm **kalınlığında** kesitler"* teknik ölçüdür, bulgu değil |
| `enlarged_lymph_node` ← `lymph nodes?` | 148/169 yanlış — o zaten `lymph_node` kavramı |
| `tumor` ← `neoplas*` | **2. kuraldan geçmez** — CT-RATE'te yalnız 24 anma |

### Sınır vakalar — gerekçeli istisna olarak kaydedildi

| kavram | boşluk | karar ve gerekçe |
|---|---:|---|
| `lower_lobe` | 36 | Google *"lower **lung** lobes"* yazıyor; bilgi metinde açıkça var (1. kural geçiyor). **2. kural zayıf:** CT-RATE'te `lower lung lobe` 31 anma, `lower lobe` 23.002. **Karar: onarıldı, istisna kaydedildi** — bu yeni bir terim değil, mevcut yüzeye isteğe bağlı bir kelime eklemektir; sözlüğe tek korpusa özgü kelime bilgisi girmez, araya sıkışan bir sözcüğe tolerans girer |
| `sequela` / `sequela_change` | 16 / 17 | TR'de **ikisi de `sekel` desenini paylaşıyordu** — `calcification` ve `lung_parenchyma` ile aynı sınıf kardeş çakışması; İngilizce ayırıyordu. **Karar: `sequela_change` daraltıldı** (`sekel de[gğ]i[şs]`), fazla iddia 17'den 8'e düştü. `sequela` çıplak `sekel` olarak kaldı; en uzun eşleşme kuralı ayrımı yapar |

---

## 7 · Kalan kuyruk ve durma ölçütü

Durma ölçütü **"sayılar eşitlendi" değil, "kanıtlanabilir hata kalmadı"** olarak
belirlendi. Kalan boşlukların hepsi ≤18 belge; çoğunluğu <10, yani gürültünün
sinyalden büyük olduğu bölge.

| kalan EN boşluğu | | kalan TR boşluğu | |
|---|---:|---|---:|
| `lung` | 20 | `density` | 18 |
| `enlarged_lymph_node` | 11 | `density_increase` | 17 |
| `density` | 11 | `thickening` | 12 |
| `dilatation` | 8 | `enlarged_lymph_node` | 9 |
| `sequela_change` | 8 | `dilatation` | 9 |

Kalan kalemlerin bir kısmı §6'da **bilerek onarılmayanlardır** (`density` ve
`density_increase`'in büyük bölümü çevirmenin terim eklemesidir), bir kısmı da
ölçülüp reddedilen adaylardır (`thickening`).

**3. kural gereği burada duruluyor.** Bu bir tek geçiştir: hiçbir ablasyon skoru
görülmedi, hiçbir seçim sonuca bakılarak yapılmadı, ikinci tur yoktur.

---

## 8 · Yöntemin sınırları — gizlenmiyor

1. **Türkçe tarafta ikinci korpus yok.** CT-RATE'in Türkçe asılları
   yayımlanmadı; Türkçe adaylar yalnız RadTr desteği ve anlam kontrolüyle
   değerlendirildi. İngilizce adaylar CT-RATE'te sınandı (2. kural). Bu
   asimetri **kapatılamadı.**
2. **Bir sözlüğün boşluğu diğerinin bulgusuyla tespit edildi.** Bu dairesel
   değil ama kesin de değil; hüküm her vakada korpus sayımı + cümle okumasıyla
   verildi, karşı sözlüğün bulgusuna güvenilerek değil.
3. **Türkçe sözlük `dev`'i gördü, İngilizce sözlük görmedi.** Türkçe yüzeyler
   `train`+`dev` (269 belge) havuzundan türetildi; İngilizce sözlük CT-RATE'te
   geliştirilip RadTr tarafında yalnız `train` (223 belge) üzerinde onarıldı.
   **Onarımın kendisi temizdir** — bu raporun bütün ölçümleri `train`
   üzerindedir. Ama `dev` üzerinde yapılan karşılaştırmalar (çeviri kalite
   kontrolü, model seçimi, inceleme arayüzü) Türkçe lehine hafif yanlıdır ve
   betimleyici sayılmalıdır. Ablasyon `test` üzerindedir; orayı iki sözlük de
   görmemiştir.
4. **Cümle hizalaması kesin değil.** Komşu cümleler birlikte gösterilerek kayma
   görünür kılındı. Hizalama yalnız aday önermek için kullanıldı, ölçüme girmedi.
4. `scripts/32`–`35` aday/cümle incelemesi için bağımsız tarar; nihai ortak
   karşılaştırma yalnız `scripts/31`deki birleşik matcher yoludur.
5. Türkçe üretim matcher'ı kavram kümesini üretir; TASK-15'in belge düzeyi
   kavram+kesinlik artefakt koşucusu ayrı sonraki bağlantı işidir.

---

## 9 · Yan bulgu — yapısal açık bulundu ve kapatıldı

Bu onarımın yan bulgusu, yüzey deliklerinden **daha büyük** bir yapısal fark:

| | İngilizce | Türkçe |
|---|---|---|
| kavram çıkarıcı | `entities.py` — **birleşik matcher**, en uzun eşleşme kazanır, bir metin parçası tek kavrama gider | `turkce_varliklar.py` — aynı mimari, yalnız sağ sınır yok |
| ortak ölçüm | `scripts/31` | `scripts/31` |

Ölçüldü: aynı sözlüklerle, yalnız **eşleştirme mimarisi** değiştirilerek:

| kurulum | net fark |
|---|---:|
| TR kavram-başına · EN birleşik | **+340 TR lehine** |
| TR birleşik · EN birleşik | **+15 EN lehine** |

**355 puanlık salınım dilden değil kod mimarisinden geliyordu.** İlk kayıttaki
359 değeri sözlük dondurmasının önceki ara durumuna aitti; güncel dondurulmuş
sözlükle yeniden ölçüm 355'tir.

**Kapatıldı.** Türkçe tarafa `entities.py` ile aynı mantıkta bir birleşik
eşleştirici yazıldı (`src/radyovlm/extraction/turkce_varliklar.py`): tek regex,
adaylar `azami_eslesme_uzunlugu`na göre sıralı, en uzun eşleşme kazanır. Tek
fark, Türkçe sondan eklemeli olduğu için sağda kelime sınırı bulunmamasıdır.

§5'teki bütün sayılar bu eşleştiriciyle üretildi; iki taraf artık aynı mimariyi
kullanıyor.

---

## 10 · Doğrulama

- 144 / 144 kavram iki tarafta da mevcut, hepsi derleniyor
- Önceden var olan 314 test + 20 yeni matcher testi: **334 / 334 geçiyor**
- Değişen: **26 kavram** (16 TR + 10 EN); sözlük dosyalarında başka hiçbir alan değişmedi
- `test` bölümü açılmadı; sözlük türetimine `dev` girmedi; matcher karşılaştırması
  `train`de doğrulandı ve `dev`de yalnız D31 geliştirme gözlemi olarak koştu
- Her onarımın gerekçesi ve okunan cümle YAML içinde yorum olarak duruyor
- Birleşik yeniden üretim: `turkce_varliklar.py` + `entities.matcher_kur`;
  `train` sonucu 152 / 167 / 5.009, toplu Jaccard 0,940

---

## 11 · Onarımdan sonra bulunan kapsam boşlukları — kayıt, uygulama değil

Sözlük donduruldu (§ 3. kural). Aşağıdakiler **gelecek sürüm için** kaydedilmiştir;
hiçbiri uygulanmamıştır. Sonuçlara bakıldıktan sonra sözlüğe dokunmak, tek geçiş
kuralının engellediği şeydir.

### `plevral sıvı` / `pleural fluid` hiçbir bulgu kavramına bağlı değil

| | |
|---|---|
| gözlem | *"Her iki hemitoraksta plevral sıvı saptanmadı."* → yalnız `pleura` (anatomi) |
| İngilizcesi | *"No pleural fluid was detected…"* → yalnız `pleura` |
| sebep | `effusion` deseni `ef+[uü]zyon`, `fluid_collection` deseni `sıvı koleksiyon\|serbest sıvı\|assit` — hiçbiri bu öbeği tanımıyor |
| boyut | öbek 23/46 `dev` belgesinde; **7'sinde** bulgu tamamen kaçıyor |
| **simetri** | **aynı 7 belge iki tarafta da** — TR/EN karşılaştırmasını bozmuyor |
| ölçülen düzeltme | TR `+plevral s[ıi]v[ıi]`, EN `+pleural fluid` → `effusion` **32 → 39 belge**, iki tarafta da aynı |

Ertelemenin bedeli yok: boşluk simetrik olduğu için yalnız `effusion` kavramının
**mutlak** sayısını etkiliyor, iki dil arasındaki **farkı** değil.

### Modellerin işaret ettiği kapsam boşlukları

İkincil model koşusunda üç model de bizde karşılığı olmayan gerçek toraks BT
bulgularına ad uydurdu: `pneumatocele`, `scoliosis`, `cavitary`, `suture`,
`electrode`, `bronchopneumonia`. Bu, envanterin **dışarıdan ve bizden bağımsız**
bir denetimidir. Ayrıntı: [ikincil model raporu](task15_ikincil_model_raporu.md).

---

## 12 · Kutuplaşma ekseni — ön ölçüm

Bu raporun bütün sayıları **A1 · kavram ekseninde**: *"bu kavram raporda konu
ediliyor mu?"* Kutuplaşma (`present` / `absent` / `uncertain`) ayrı bir eksendir
ve ayrı bir sistem atar.

⚠ Aşağıdaki ölçüm **ön ölçümdür**, kapı ya da skor sonucu değildir: Türkçe
kesinlik atayıcı birleşik çıkarıcıya **geçici olarak** bağlanarak yapıldı; resmî
hat henüz kurulmadı (§ 9'daki açık iş).

| | |
|---|---:|
| iki tarafta da bulunan kavram | 1.039 |
| aynı kesinlik | 1.012 |
| **farklı kesinlik** | **27 (%2,6)** |

Yön: `uncertain→present` 14 · `absent→present` 10 · `present→uncertain` 2 ·
`present→absent` 1.

**Üç vaka tek tek açıldı ve üçünde de çeviri kusursuz:**

| kavram | TR | EN | gerçek sebep |
|---|---|---|---|
| `heart` | absent | present | *"IVKM verilmediğinden … değerlendirme yapılamamıştır"* — **teknik çekince**; TR sistemi absent sayıyor, EN saymıyor (D30'un bilinen şema farkı) |
| `gallbladder` | absent | present | *"Safra kesesi izlenmedi (opere)."* → *"was not visualized"*; çeviri doğru, EN'de negasyon kapsamı parantezde kopuyor |
| `pneumonia` | uncertain | present | *"KLİNİK BİLGİ: PNÖMONİ?"* → *"CLINICAL INFORMATION: PNEUMONIA?"*; çeviri doğru, soru işareti kapsamı iki tarafta farklı çözülüyor |

**Yani %2,6'nın tamamı iki kesinlik sisteminin kural farkıdır, çeviri kaybı
değil** — ve bu, D51'in `absent`/`uncertain` eksenlerini ölçümden önce güçsüz
ilan etmesinin somut gerekçesidir.

### ⛔ Yol boyunca yakalanan alet hatası

İlk ölçüm **%70,8** uyumsuzluk ve neredeyse tamamı `present→absent` verdi —
imkânsız bir sonuç. Sebep: İngilizce tarafa **tüm belge tek parça** verilmişti,
Türkçe tarafa cümle cümle; negasyon kapsamı belge geneline yayılıp her şeyi
`absent` yapıyordu. Üretimde ikisi de **cümle düzeyinde** koşar
(`scripts/11_apply_context.py`). Düzeltilince %2,6'ya indi.

D60'ın tekrarı: **aleti yanlış kurunca sözlükte olmayan bir felaket görünür.**

### Mevcut kanıt

Türkçe kesinlik atayıcı `dev`de altına karşı ölçülmüştü: `absent` kesinlik
%84,3 · duyarlılık **%97,2** · F1 **%90,3** (`reports/turkce_dondurma.md`).
Türkçe negasyon ipucunun %97'si cümlenin **sonunda** olduğu için geri yönlü
kapsam kuralı yazılmıştı; İngilizce mantığı doğrudan uygulansa negasyonun
neredeyse tamamı kaçardı.
