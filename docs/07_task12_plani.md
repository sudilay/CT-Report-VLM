# TASK-12 — Negasyon, Belirsizlik ve Zamansal İfade Çözümlemesi

**Faz 2 · Önkoşul:** TASK-11 ✅ · **Durum:** B0–B6 uygulandı · doğruluk ölçümü TASK-13'te
**Hazırlayan:** Claude Code · 2026-08-27

---

## 1. Ne yapar, ne yapmaz

**Yapar:** TASK-11'in çıkardığı 1.180.408 varlığa üç alan yazar.

| Alan | Şu an | Sonra |
|---|---|---|
| `assertion` | `not_processed` | `present` · `absent` · `uncertain` |
| `temporality` | `unknown` | `current` · `prior` · `unknown` |
| `change_type` | `unknown` | `none` · `stable` · `new` · `increased` · `decreased` · `resolved` · `unknown` |

**Yapmaz:** Bunların klinik anlamını yorumlamaz. *"Stabil olduğu için benign"* kararı
**Faz 6'ya** aittir (D17). *"Kalibrasyonu doğal, o hâlde damar patolojisi yok"* çıkarımı
**Faz 3'e** aittir. Faz 2 **metnin söylediğini kaydeder.**

---

## 2. Ölçülen tasarım girdileri

Hepsi train korpusunda (449.868 cümle) ölçüldü, 2026-08-27.

### 2.1 Negasyon yönü — hipotezimi kısmen çürüttü

Türkçe fiil-sonlu bir dil (*"…izlenmedi"*), o yüzden **çeviride negasyonun cümle sonunda
toplanacağını** varsaymıştım. Ölçüm bunu **kısmen** doğruladı:

| Biçim | Cümle |
|---|---|
| Cümle `"No …"` ile başlıyor (öncül) | **75.391** |
| `no significant` (öncül) | 16.207 |
| `was not detected` (ardıl) | 11.346 |
| `was not observed` (ardıl) | 10.801 |
| `is/are not present` (ardıl) | 1.261 |

Varlık konumuna göre **doğrudan ölçüm** (60.000 cümlelik örnek):

| İpucunun bulguya göre konumu | Cümle | Pay |
|---|---|---|
| **ÖNCE** (ileri kapsam) | 22.603 | %80,1 |
| **SONRA** (geri kapsam) | 5.626 | **%19,9** |

→ **Baskın yön ileri, ama beşte bir geri.** Yalnızca ileri kapsamlı bir NegEx
kurulumu **her beş negatif cümleden birini kaçırır.** ConText **çift yönlü**
yapılandırılacak; ardıl ipuçları `BACKWARD` olarak tanımlanacak.

*Not: `no evidence of` 91, `free of` 0, `negative for` 0 — klasik İngilizce NegEx
tetikleyicileri bu korpusta neredeyse yok. İthal liste tek başına işe yaramaz (D16).*

### 2.2 Koordinasyon — tek negasyon birden çok bulguyu kapsıyor

`"no … or …"` kalıbı **17.291 cümlede**. *"No pleural effusion or thickening was
observed"* → **ikisi de** `absent`. Kapsam ilk bulguda kesilirse ikincisi yanlışlıkla
`present` kalır.

### 2.3 Kapsam sonlandırıcılar

Noktalı virgül **26.579** · `apart from` 1.730 · `however` 1.699 · `although` 849 ·
`except` 257 · `but` 538.

### 2.4 Belirsizlik — korpusa özgü işaretler

| İşaret | Cümle |
|---|---|
| `evaluated` — ⚠ **çıplak hâli ipucu DEĞİL**, bkz. 4.15 | 24.432 |
| `in favor of` (*"…lehine"*) | **7.910** |
| **Parantez içi soru işareti** `(cyst?)` | **5.540** |
| `compatible with` | 6.637 |
| `consistent with` | 5.607 |
| `may` (kip fiili) | 3.363 |
| `primarily` | 2.294 |
| `suspicious` | 2.049 |
| `differential` | 1.957 |
| `thought to be` | 754 |
| `cannot be excluded` | 365 |

Toplam soru işareti 7.859; bunun **%70'i parantez içinde**. Bu, standart hiçbir
belirsizlik sözlüğünde yoktur — korpusa özgüdür.

⚠ `evaluated` sayısı yanıltıcıdır ve **çıplak hâliyle ipucu olarak alınamaz** — bölüm 4.15.

### 2.5 Zamansallık

`previous*` 6.208 · `stable` 4.085 · `follow-up` 2.627 · `in the current examination`
1.980 · `control` 901 · `regress*` 884 · `newly developed` 800 · `new` 478 ·
`progress*` 385 · `disappeared/resolved` 111 · **`compared to/with` yalnızca 13.**

**Aynı cümlede hem güncel hem önceki:** 661 cümle
(*"…51x42 mm in the current examination and 46x36 mm in the previous PET-CT"*).

### 2.6 Normallik beyanları — negasyon değil

`normal` 69.287 · `are open` 19.030 · `is/are natural` 17.787 · `preserved` 9.282 ·
`within normal limits` 2.904 · `natural calibration` 452.

Bunlar **negasyon ipucu içermez** ama klinik olarak "patoloji yok" der. Kararımız
bölüm 4.6'da.

---

## 3. Yöntem

**medspaCy ConText.** Hedef varlıklar TASK-11'den geliyor; ConText niteleyicileri
onlara bağlar. D15 gereği **deterministik**: aynı girdi → aynı çıktı, her atama
hangi ipucundan geldiği kayıtlı.

**İpucu sözlüğü korpustan türetilir (D16).** `data/external/negex/negex_triggers.txt`
**başlangıç noktasıdır**, olduğu gibi kullanılmaz: yukarıdaki ölçümler standart
listenin buraya oturmadığını gösteriyor.

### Yeni alanlar — izlenebilirlik

`extraction_rule` mantığının aynısı; hangi ipucunun hangi atamayı ürettiği kaydedilir:

**İnceleme sonrası genişletildi** — ilk taslakta yalnızca üç alan vardı ve
zamansallık ile değişim için kural adı yoktu; o hâlde bir zamansal hata bulunduğunda
hangi kuralın ürettiği görülemezdi.

| Tablo | Kolon | Açıklama |
|---|---|---|
| `entities` | `assertion_cue` | Atamayı üreten ipucunun ham metni (`"was not observed"`) |
| `entities` | `assertion_rule` | Uygulanan kural adı (`negasyon_ardil`, `belirsizlik_parantez`, …) |
| `entities` | `temporality_cue` | Zamansal atamayı üreten ipucu |
| `entities` | **`temporality_rule`** | Zamansal kural adı |
| `entities` | **`change_cue`** | Değişim atamasını üreten ipucu |
| `entities` | **`change_rule`** | Değişim kural adı |
| `measurements` | **`temporality_cue`** · **`temporality_rule`** | Ölçü düzeyi zamansallık da izlenebilir olmalı (4.9) |

Bunlar `sema-1.2`'ye eklenecek. Gerekçe: TASK-13'te bir hata bulunduğunda **hangi
ipucunun ürettiği** görülebilmeli, yoksa hata analizi tahmine döner.

### `comparison_interval` — açıkça ERTELENDİ

`docs/05` bölüm 1'de Faz 2 alanları arasında sayılmıştı ama bu planın şema adımlarında
yoktu. **Bilerek ertelendiği** burada kayda geçiyor:

Raporların **%99,6'sında tarih yok** (Faz 1'de ölçüldü). Alan üretilse **neredeyse her
satırda `null`** olurdu. Boş bir kolon eklemek yerine, gerektiğinde `sema-1.3`'te
eklenmesi tercih edildi. Faz 6'ya bildirilecek sınır: **stabilitenin süresi bu korpusta
bilinmiyor** (D17).

---

## 4. Sınır durumlar (edge case) kataloğu

Her biri ölçüldü. Bu bölüm planın asıl gövdesidir — kurallar buradan yazılacak.

### 4.1 ⚠ `cannot be excluded` — anlamı TERS çeviren tuzak

> *"…underlying pneumonic infiltration **cannot be excluded**."*

İçinde `not` geçiyor. Naif bir negasyon kuralı bunu `absent` yazar — **anlamın tam
tersi.** Doğrusu `uncertain`: bulgu **olabilir**.

**Kural:** `cannot be excluded` / `can not be excluded` / `cannot be ruled out`
**belirsizlik önceliklidir**, negasyon kuralından **önce** uygulanır. 365 cümle.

### 4.2 ⚠ `non-` ve `un-` önekli niteleyiciler — negasyon değil

> *"A millimetric **nonspecific** subpleural nodule was observed."*

`non`/`un` öneki gördüğünde negasyon sayan kural, **12.992 cümlede** nodülü yok eder.
`nonspecific` bir **niteleyicidir**; nodül **mevcuttur**.

**Ama iki ayrı durum var, karıştırılmamalı:**

| İfade | Doğru sonuç |
|---|---|
| `nonspecific nodule` | nodule = `present` (niteleyici, negasyon değil) |
| `non-calcified nodule` | nodule = `present`, calcific = **`absent`** |

İkincisinde negasyon **niteleyiciye** aittir, bulguya değil. `non-` öneki yalnızca
**niteleyici varlığın kendisine** uygulanır, komşu gözleme değil.

### 4.3 ⚠ Teknik çekince ≠ bulgu yokluğu

> *"The heart and mediastinal vascular structures **could not be evaluated optimally**."*

`could not be evaluated` 3.671 · `not evaluated optimally` 5.280 ≈ **9.000 cümle.**
Bu, "kalp yok" demek değil; **tetkikin sınırı** demektir.

**Kural — İNCELEME SONRASI DÜZELTİLDİ.** İlk yazımda bu kural karar önceliğinin
başına *"teknik çekince bağlamı → negasyon uygulanmaz"* diye konmuştu. **Bu yanlıştı:**
kural cümle düzeyinde çalışıyordu ve teknik çekince taşıyan bir cümledeki **gerçek**
negasyonu da susturuyordu.

**Ölçüldü:** Teknik çekince işaretli 26.325 cümlenin — teknik ifadenin kendisi metinden
çıkarıldıktan sonra — **11.044'ünde (%42,0)** hâlâ bağımsız bir negasyon ipucu var.

> *"In the upper abdominal sections within the image, **no solid mass was detected**
> as far as can be observed within the borders."*

Burada *"as far as can be observed"* teknik çekince, *"no solid mass was detected"*
**gerçek negasyon**. Cümle düzeyi susturma bu bulguyu `present` yapardı — sessizce yanlış.

**Doğru kural:** Teknik çekince, **kendi ipucu kapsamında** negasyon üretmez; cümledeki
**diğer** negasyon ipuçlarını etkilemez. Yani:

| İfade | Etki |
|---|---|
| `could not be evaluated` · `cannot be assessed` | negasyon tetikleyicisi **değil** — kendi kapsamında etkisiz |
| Aynı cümledeki başka bir `no …` / `was not detected` | **normal işler**, kapsamı geçerli |

`has_technical_caveat` bayrağı susturma amacıyla **kullanılmaz**; yalnızca TASK-13'te
hedefli örneklem çekmek için kullanılır.

Bu, Faz 1'de kurduğumuz bağımsız eksen ilkesinin karşılığını buluyor: teknik çekince
negasyondan **ayrı bir eksendir** ve bir cümle ikisini birden taşıyabilir.

### 4.4 ⚠ Negasyon + belirsizlik aynı cümlede

> *"**No suspicious** nodular or mass-occupying lesion was detected."*

983 cümle. `suspicious` belirsizlik ipucu, ama **olumsuzlanan isim öbeğinin içinde.**
Bulgu `absent`'tır, `uncertain` değil.

**Kural:** Belirsizlik ipucu bir negasyon kapsamının **içindeyse** yok sayılır;
negasyon kazanır. İstisna 4.1 (`cannot be excluded`).

### 4.5 Koordinasyon kapsamı

> *"No pleural **effusion** or **thickening** was observed."*

17.291 cümle. Negasyon kapsamı `or` / `and` / virgül ile bağlı **tüm** bulguları
kapsar; ilk bulguda kesilmez.

Kapsam **sonlandırıcıda** biter: noktalı virgül (26.579), `however`, `apart from`,
`except`, `but`, `although`.

> *"…no significant difference; **however**, newly developed consolidation is observed."*
> → ilk kısım `absent`, `however`dan sonrası `present`.

### 4.6 Normallik beyanları — bilinçli olarak çıkarım YAPILMAZ

> *"Trachea and both main bronchi **are open**."* (19.030)
> *"Vascular structures are of **natural calibration**."* (452)
> *"Vertebral corpus heights are **preserved**."* (9.282)

Bu cümleler negasyon ipucu içermez ama "patoloji yok" der.

**Karar (D25 adayı):** Bu cümlelerden **bulgu yokluğu türetilmez.** Sebep: ortada
olumsuzlanacak bir **gözlem varlığı yok** — yalnızca anatomi varlıkları var
(`trachea`, `bronchus`, `vertebra`) ve onlar gerçekten **mevcuttur**, dolayısıyla
`present` doğru cevaptır.

*"Kalibrasyonu doğal"dan "damar patolojisi yok" sonucunu çıkarmak bir **çıkarımdır**
ve gösterge sözlüğü gerektirir — o Faz 3'ün işidir.* Faz 2 metnin söylediğini kaydeder.

Bu kararın kaydı önemli: sonradan "neden normallik beyanlarını işlemedik" sorusunun
cevabı burada.

### 4.7 `no increase` — hedefi doğru seçmek

> *"There is **no** pathological wall **thickness increase** in the esophagus."* (5.541)

İlk bakışta tuzak gibi görünüyor ama **bizde değil**: TASK-11'in sözlüğünde
`thickening` kavramı zaten `"thickness increases?"` yüzeyini kapsıyor. Yani
olumsuzlanan **varlığın kendisi** `thickening`; sonuç `absent(thickening)` ve **doğru.**

Kayda geçiriliyor çünkü sözlük farklı kurulmuş olsaydı burası hata üretirdi.

### 4.8 `no significant change` — değişimi olumsuzlar, bulguyu değil

228 cümle. `change_type` alanını etkiler (`stable`), `assertion` alanını **etkilemez.**

### 4.9 Zamansallık cümle düzeyinde atanamaz

> *"…a cavitary mass measuring **51x42 mm in the current examination** and
> **46x36 mm in the previous PET-CT**."*

661 cümle. **Aynı cümlede iki farklı zamana ait iki ölçü var.**

**Kural:** `temporality` **ölçü düzeyinde** de atanır (`measurements.parquet` →
`meas-1.2`). Ölçünün en yakın zamansal ipucu neyse o geçerlidir; varlık düzeyindeki
`temporality` cümlenin baskın zamanıdır.

### 4.10 Hem güncel hem önceki olan bulgular

> *"Hypodense lesions, **which were also observed in the previous examination**, are
> observed in the liver."* (251)

Bulgu **her iki tetkikte de var**. `temporality=current` doğrudur (şu an mevcut);
önceki tetkikte de bulunması `change_type=stable` bilgisidir.

### 4.11 `increase` — %96,6'sı zamansal değil

Faz 2 planında ölçülmüştü: `increas*` 25.522 cümlede ama yalnızca **%3,4'ünde** açık
zamansal referans var. *"Peribronchial thickness increases"* durağan bir tanımdır.

**Kural:** `change_type=increased` yazmak için **açık zamansal referans şartı**
(`previous`, `control`, `follow-up`, `current examination`, `newly`) aranır.

### 4.12 Süresi bilinmeyen stabilite

`stable` 4.085 cümle, ama raporların %99,6'sında tarih yok →
`comparison_interval` neredeyse hep `null`.

**Kural (D17):** `change_type=stable` kaydedilir, **yorumlanmaz.** "Ne kadar süredir
stabil" bilinmiyor ve bu Faz 6'nın karar katmanına açıkça bildirilir.

### 4.13 Cümleler arası gönderme

> *"It is stable."* · *"Other findings are stable."*

Cümlede varlık yok, gönderme önceki cümleye. TASK-11'de çözülmedi.

**Karar:** TASK-12'de de **çözülmez.** Kapsam dışı bırakılıyor ve
`unresolved_attachments`'a benzer şekilde sayılıp raporlanacak — sessizce geçilmeyecek.

### 4.15 ⚠ `evaluated` çıplak hâliyle belirsizlik ipucu DEĞİL

24.432 cümlede geçiyor ve ilk taslakta belirsizlik ipuçları arasına konmuştu.
**Ölçüm bunun yanlış olduğunu gösterdi** — bağlamlara ayrıldığında:

| Bağlam | Cümle | Belirsizlik mi |
|---|---|---|
| `evaluated in favor of` | **5.180** | ✅ evet |
| `evaluated as` | **3.809** | ✅ evet |
| `evaluated compatible/consistent with` | 16 | ✅ evet |
| `cannot be evaluated` / `not evaluated optimally` | **4.206** | ❌ **teknik çekince** |
| `recommended to be evaluated` / `be evaluated together` | **3.667** | ❌ **öneri cümlesi** |
| `is/are evaluated` (nötr) | 1.686 | ❌ nötr |

> *"It is **recommended to be evaluated** together with clinical and laboratory."*

Bu bir belirsizlik bildirimi değil, bir **öneri**. Çıplak `evaluated` ipucu sayılsaydı
**~15.000 cümle** yanlış `uncertain` olurdu.

**Kural:** Yalnızca **tam kalıplar** alınır — `evaluated in favor of`,
`evaluated as`, `evaluated (to be) compatible/consistent with`. Çıplak `evaluated`
alınmaz. Aynı disiplin `thickness` (Faz 1) ve `increase` (4.11) için de uygulanmıştı.

### 4.14 `may` — kip fiili mi, ay adı mı

3.363 cümlede `may`. Faz 1'de bu kelime naif regex'le **ay adı** sanılıp %10,79 gibi
sahte bir sonuç üretmişti. Belirsizlik ipucu olarak alınmadan önce
büyük harf ve tarih bağlamı ayrıştırılacak.

---

## 4-B. Karar tablosu — `none` / `unknown` ve zaman atama

İnceleme haklı olarak bu ikisinin anlamının ve aynı cümledeki farklı zamanlı varlıkların
nasıl atanacağının **net bir tabloyla** tanımlanmasını istedi. Aksi hâlde iki farklı
"bilgi yok" hâli karışır.

### `change_type` — üç farklı "değişim yok" hâli

| Değer | Anlamı | Ne zaman yazılır |
|---|---|---|
| `none` | **Karşılaştırma yapılmamış.** Metin önceki bir tetkikten söz etmiyor. | Cümlede hiçbir zamansal/karşılaştırma ipucu yok |
| `stable` | **Karşılaştırma yapılmış, değişim yok.** | Açık ipucu var: `stable`, `unchanged`, `no significant change` |
| `unknown` | **Karşılaştırma var ama yönü çıkarılamadı.** | Zamansal ipucu var (`previous`, `control`) ama değişim yönü belirsiz |

Ayrım önemli: `none` "kıyas yok" der, `stable` "kıyas var, aynı" der. İkisini
birleştirmek **Faz 6'da stabiliteyi kanıt sayarken** yanlış sonuç doğururdu — hiç
karşılaştırılmamış bir bulgu "stabil" sayılamaz.

### `temporality` — üç hâl

| Değer | Anlamı |
|---|---|
| `current` | Bu tetkikte gözlenmiş |
| `prior` | **Yalnızca** önceki tetkikte; bu tetkikte anılıyor ama şimdi ait değil |
| `unknown` | Ayırt edilemedi |

### Aynı cümlede farklı zamanlı varlıklar

661 cümlede iki zaman bir arada (4.9). Atama **varlık başına**, en yakın ipucuna göre:

| Durum | Örnek | Karar |
|---|---|---|
| Varlık bir `prior` ipucunun **kapsamında** | *"**In the previous** CT examination, its size was 18 mm"* | `prior` |
| Varlık bir `current` ipucunun **kapsamında** | *"…**in the current examination**…"* | `current` |
| Varlık **hiçbir** zaman kapsamında değil | çoğunluk | **`current`** — rapor bu tetkiki anlatır |
| Bulgu **hem** güncel **hem** önceki | *"…which were also observed in the previous examination…"* (251) | `current` + `change_type=stable` |

> **Kural uygulama sırasında daraltıldı.** İlk tabloda *"cümlede tek zaman ipucu varsa
> onun zamanını al"* satırı vardı. Deneme bunun yanlış olduğunu gösterdi:
>
> *"The nodule has increased **compared to the previous examination**."*
>
> Bu kural nodülü `prior` yapıyordu — oysa nodül **şimdiki**; *"previous"* yalnızca
> **karşılaştırma referansı**. Yeni kural: bir varlık ancak bir `prior` ipucunun
> **kapsamında** ise `prior` olur; aksi hâlde `current`. Çoklu ipucu durumu da
> buna indi — 661 cümlelik "aynı cümlede iki zaman" vakasında **varlık** güncel,
> zaman farkı **ölçü düzeyinde** taşınır (4.9).

> **Değişim ipuçları çift yönlü olmalı.** İlk kurulumda ileri yönlüydüler ve
> *"The nodule **has increased**"* cümlesinde özneyi kaçırıyorlardı — İngilizcede
> değişim fiili özneden **sonra** gelir. `yon: cift` yapıldı.

**Ölçü düzeyi ayrı hesaplanır** (4.9): ölçünün kendi en yakın zaman ipucu geçerlidir,
varlığınkinden farklı olabilir. `measurements.temporality` bu yüzden var.

---

## 5. Uygulama sırası

| Adım | İş | Çıktı |
|---|---|---|
| **B0** | **Ayar (150) ve değerlendirme (200) örneklemlerini ayrı çalışmalardan çek, sabit tohumla dosyaya yaz** (7.0) | `data/processed/task12_ayar.csv` · `task12_degerlendirme.csv` |
| **B1** | İpucu sözlüğünü korpustan türet; ithal listeyi tara ve hangi tetikleyicilerin burada karşılığı olduğunu ölç | `configs/ipucu_sozlugu.yaml` |
| **B2** | ConText'i çift yönlü kur, hedefleri TASK-11 varlıklarına bağla | `src/radyovlm/extraction/context.py` |
| **B3** | Sınır durum kurallarını öncelik sırasıyla uygula (bölüm 6) | aynı modül |
| **B4** | Zamansallık ve `change_type`; ölçü düzeyi zamansallık | `meas-1.2` |
| **B5** | Şemayı `sema-1.2`'ye çıkar (`assertion_cue`, `assertion_rule`, `temporality_cue`) | `extraction_schema.json` |
| **B6** | Tam koşu + şema doğrulaması + zor vaka takımı | güncel `entities.parquet` |
| **B7** | Ölçüm raporu ve elle inceleme örneği | `reports/` |

---

## 6. Karar önceliği — sırayla uygulanır

Determinizm için sıra sabittir. İlk eşleşen kazanır.

Öncelik **ipucu kapsamı düzeyinde** uygulanır, cümle düzeyinde **değil**. Bir cümlede
birden çok ipucu olabilir ve her varlık **kendi** kapsamına göre değerlendirilir.

1. **`cannot be excluded` ailesi** varlığı kapsıyorsa → `uncertain` (4.1)
2. **Negasyon ipucu** varlığı kapsıyorsa → `absent` (4.4: kapsam içi belirsizlik yok sayılır)
3. **Belirsizlik ipucu** varlığı kapsıyorsa → `uncertain`
4. **Hiçbiri** → `present`

**Teknik çekince ifadeleri bu listede yer almaz** çünkü hiçbir varlığa `absent`
yazdırmazlar — yalnızca **negasyon tetikleyicisi olarak sayılmazlar**. Aynı cümledeki
başka negasyon ipuçları normal işler (4.3).

`non-` öneki (4.2) yalnızca **niteleyici varlığın kendisine** uygulanır; komşu gözleme
sıçramaz.

---

## 7. Kabul ölçütleri

### 7.0 ⚠ Ayar kümesi ile değerlendirme kümesi AYRILIR (D26 adayı)

**İnceleme bir metodoloji açığı buldu ve haklı.** İlk taslakta her ölçütün yanında
*"sağlanmazsa kurallar gözden geçirilir"* yazıyordu. Ama kurallar **aynı 200 örnek
üzerinde** düzeltilirse, sonra bildirilen skor o örneklere **uydurulmuş** olur —
iyimser çıkar ve gerçek başarımı göstermez.

Bu, projenin kendi bağlayıcı kuralının ihlaliydi:
*"Karar eşiği yalnızca dev kümesinde belirlenir; test üzerinde eşik seçmek geçersizdir."*
Şablon kataloğunu yalnızca train'den hesaplamamızın (D11) sebebi de aynıydı.

### ⚠ Belirleyici gerekçe: sözlük TÜM train'den türetildi

İncelemenin gözden kaçırdığı — benim de yazmadığım — nokta şu:

> **Sözlük madenciliği (`terim_madeni.py`) ve her `korpus` sayısı `split == "train"`
> üzerinde, yani TÜM train cümleleri üzerinde yapıldı.**

Dolayısıyla **hiçbir train cümlesi "görülmemiş" sayılamaz.** Ayırıp kenara koyduğumuz
bir train hastası bile sözlüğe katkıda bulunmuştur; onun üzerinde ölçülen başarım
**iyimserdir**. Bu, değerlendirmenin neden **valid** hastalarından gelmesi gerektiğinin
en güçlü gerekçesidir — valid, sözlüğe hiç katkı vermedi.

### Mevcut kirlilik — ölçüldü

Faz 1 ve TASK-11'in inceleme örneklerinde **valid çalışmalar da var**:

| Dosya | train | valid | hasta |
|---|---|---|---|
| `bolutleme_sinir_dogrulama.csv` | 88 | **12** | 99 |
| `olcu_rastgele_100.csv` | 94 | **6** | 100 |
| `varlik_cikarim_ornegi.csv` | 94 | **6** | 100 |
| `olcu_cok_eksenli.csv` | 74 | **2** | 68 |
| `olcu_aykiri_degerler.csv` | 22 | **2** | 22 |
| `olcu_teknik_isaretliler.csv` | 5 | **1** | 6 |

Bu çalışmaların hepsi **görülmüş** sayılır ve değerlendirme kümesine **giremez.**

**Kural (D26):**

| Küme | Kaynak | Adet | Kural değiştirilebilir mi |
|---|---|---|---|
| **Ayar (dev)** | **train** hastaları, yanmış liste hariç | 150 cümle | ✅ serbestçe |
| **Değerlendirme (test-v1)** | **valid** hastaları, yanmış liste hariç | 200 cümle | ❌ **bir kez açılır** |

1. Ayrım **hasta düzeyinde** yapılır, çalışma düzeyinde değil — aynı hastanın iki
   çalışması iki kümeye düşemez. (Projenin bağlayıcı kuralı zaten bu.)
2. **Yanmış liste:** bugüne kadar incelenen tüm örneklem dosyalarındaki çalışmaların
   hastaları `data/processed/incelenmis_hastalar.csv`'ye yazılır ve teste **giremez.**
3. **Dev yalnızca train'den**, **test yalnızca valid'den.**
4. Örnekleme kodu iki şeyi **otomatik reddeder**: (a) dev ∩ test hasta kesişimi,
   (b) yanmış listeden test'e sızma. İhlal varsa dosya **yazılmaz** — şema kapısının aynısı.
5. Test sonucuna bakıp kural değiştirilirse **test-v1 iptal edilir**, yeni `test-v2`
   çekilir, eski skor geçersiz sayılır ve **raporda yazar.**
6. **Rastgele ve hedefli zor örneklerin skorları AYRI raporlanır**, birleştirilmez.
   Hedefli küme kasıtlı olarak zor seçildiği için birleşik ortalama hiçbir şeyi temsil
   etmez — K8/K9'da (kolay/belirsiz ayrımı) verdiğimiz kararın aynısı.

**Ek — Faz 3'e borç:** Test kümesi valid'den çekildiği için **bir miktar valid hastası
tüketilir.** Tüketilen hasta kimlikleri dosyaya yazılır ki **TASK-18 (bölme dondurma)**
bunları hesaba katabilsin. Sessizce tüketilmez.

### Önceki görevler yeniden yapılmayacak

A1–A5 ve TASK-11'in örnekleri **geliştirme/regresyon seti** sayılır. Onlardan bildirilen
sayılar (ör. şablon doğrulamasında "100/100") **geliştirme gözlemidir, bağımsız başarım
ölçümü değildir** — bu, ilgili günlük kayıtlarına not düşülüyor.

Faz 2 hattının uçtan uca başarımı **TASK-13'te, yeni hasta düzeyi holdout üzerinde**
ölçülecek. Geriye dönüp Faz 1'i yeniden ölçmeye gerek yok: oradaki iddiaların çoğu
(ofset doğruluğu, birim dönüşümü, bütünlük) **tüm veri üzerinde mekanik olarak**
doğrulanabiliyor ve örnekleme dayanmıyor.

---

`docs/05` bölüm 6'daki K6, K7, K10 geçerli. TASK-12'ye özgü eklemeler
**sonuç görülmeden** yazıldı. *"Sağlanmazsa"* sütunundaki düzeltmeler **yalnızca ayar
kümesine** bakarak yapılır:

| # | Ölçüt | Eşik | Sağlanmazsa |
|---|---|---|---|
| K6 | Negasyon makro-F1 | ≥ %85 | ConText kuralları gözden geçirilir |
| K7 | Belirsizlik makro-F1 | ≥ %75 | İpucu sözlüğü genişletilir |
| K10 | Zamansal sınıf doğruluğu | ≥ %85 | Zaman kuralları gözden geçirilir |
| **K11** | **`cannot be excluded` vakalarının hiçbiri `absent` olmamalı** | **%100** | Kural sırası hatalı, düzeltilir |
| **K12** | Teknik çekince **ifadesinin kendi kapsamındaki** varlıklar `absent` olmayacak *(cümlenin tamamı değil — aynı cümledeki bağımsız negasyon geçerlidir, 4.3)* | **%100** | Kapsam cümle düzeyine kaymış, düzeltilir |
| **K13** | Koordinasyonlu `no … or …` cümlelerinde **ikinci** bulgu da `absent` | ≥ %90 | Kapsam kuralı düzeltilir |
| **K14** | `assertion_cue` alanı `absent`/`uncertain` satırlarda dolu | %100 | Yazma reddedilir |
| **K15** | Ardıl ipuçlu cümlelerde `absent` yakalanma oranı | ≥ %85 | Geri yön kapsamı düzeltilir |

K11 ve K15 doğrudan bölüm 4'ün iki en kritik bulgusunu koruyor.

---

## 8. Bilinen sınırlar — gizlenmiyor

| Sınır | Ölçü | Nereye |
|---|---|---|
| Cümleler arası gönderme çözülmez | *"It is stable."* | sayılıp raporlanacak |
| `comparison_interval` neredeyse hep `null` | raporların %99,6'sında tarih yok | Faz 6'ya bildirilecek |
| Kural tabanlı kapsam sözdizimsel değil | — | TASK-13 ölçecek |
| Belirsizlik sınıfı doğası gereği öznel | K7 eşiği bu yüzden K6'dan düşük | — |

---

## 9. Riskler

| Risk | Etki | Karşılık |
|---|---|---|
| Ardıl negasyonun kaçırılması | **Yüksek** — negatif cümlelerin %19,9'u | K15 ölçütü; çift yönlü ConText |
| `cannot be excluded` tersine çevrilmesi | **Yüksek** — anlam tam ters | K11 ölçütü (%100) |
| `non-` önekinin bulguyu yok etmesi | **Yüksek** — 12.992 cümle | Önek yalnızca niteleyiciye |
| Teknik çekincenin negasyon sanılması | Orta — ~9.000 cümle | K12 ölçütü; `has_technical_caveat` çapraz denetimi |
| Koordinasyonda kapsamın erken kesilmesi | Orta — 17.291 cümle | K13 ölçütü |
| İthal sözlüğe güvenmek | Orta | D16; `no evidence of` 91, `free of` 0 ölçüldü |
