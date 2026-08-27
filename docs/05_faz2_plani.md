# Faz 2 — Yapılandırılmış Çıkarım Planı

**Kaynak görev listesindeki yeri:** T-02
**Kapsadığı görevler:** TASK-10, TASK-11, TASK-12, TASK-13
**Durum:** onaylandı · **TASK-10 ✅** · **TASK-11 — çıktı üretildi, doğruluk TASK-13'e kaldı** · sırada TASK-12
**Hazırlayan:** Claude Code · 2026-08-26

> Uygulama sırasında plandan sapmalar oldu; her biri gerekçesiyle
> `docs/04_uygulama_gunlugu.md` bölüm 3-C ve 3-D'de kayıtlı. Şema gerekçesi:
> `docs/06_sema_gerekce.md`.

---

## 0. Faz 2 ne yapar, ne yapmaz

**Yapar:** Serbest metin cümleyi, makinenin üzerinde işlem yapabileceği **yapılandırılmış
kayda** çevirir. "Sağ akciğer üst lobda 8 mm spiküle nodül izlendi" cümlesi şuna dönüşür:

| bulgu | anatomi | taraf | niteleyici | ölçü | varlık durumu |
|---|---|---|---|---|---|
| nodül | üst lob, akciğer | sağ | spiküle | 8 mm | mevcut |

**Yapmaz:** Bu bulgunun malign olup olmadığına karar vermez. Spikülasyonun malignite
göstergesi olduğu bilgisi **Faz 3'ün** sözlüğünde, o kararın verilmesi **Faz 6'nın**
karar katmanındadır.

Faz 1'in kuralı aynen sürer: **veri hazırlığı korur, karar vermez.**

---

## 1. İnceleme önerilerinin değerlendirmesi

Altı öneri ve bir yöntem önerisi incelendi. Sonuç: **6 kabul, 1 kısmen kabul.**
Kabul edilenlerin hepsi genişletilerek veya bir noktası düzeltilerek alındı.

### Öneri 1 — Faz 2'nin üreteceği veri tabloları tanımlanmamış → **KABUL**

Haklı. Plan yalnızca `extraction_schema.json`, `entities.py`, `context.py` diyordu;
bunlar **kod ve konfigürasyon**, veri değil. Faz 3'ün üzerinde çalışacağı tablo
tanımsızdı. Faz 1'de aynı hatayı yapmamıştık (`sentences.parquet`, `measurements.parquet`
baştan tanımlıydı); Faz 2'de yapılmış.

**Eklenerek alındı:** Önerilen alan listesinde **taraf (laterality)** yok. Faz 1'de
sayıları maskelerken anatomiyi ve tarafı bilerek korumuştuk (D3) — çünkü klinik olarak
anlamlı. Şemada karşılığı olmazsa o bilgi burada kaybolur. `laterality` alanı eklendi.

→ Ayrıntı: bölüm 3.

### Öneri 2 — Ölçülerin bulgulara bağlanması unutulmuş → **KABUL**

Haklı ve önemli. `docs/03` satır 97 ve `AGENTS.md` bunu söylüyor ama **görev metninde
yazmıyor**. Görev metninde yazmayan iş yapılmaz.

Kalıcı `measurement_id` gerçek bir boşluk: şu anda ölçünün kimliği yok, yalnızca
`(study_id, section, sent_idx, meas_idx)` bileşik anahtarı var. İlişki tablosundan
referans verilebilmesi için tek alanlık kalıcı kimlik şart.

**Eklenerek alındı — `attachment_rule` alanı.** Ölçüyü bulguya hangi kuralın bağladığı
kaydedilir (`tek_aday`, `en_yakin_sol`, `en_yakin_sag`, `en_buyugu_ifadesi`, `belirsiz`). Faz 1'in
ofset izlenebilirliği disiplininin aynısı: **bir çıkarım hatası bulunduğunda hangi
kuralın ürettiği görülebilmeli.** Bu alan olmadan hata analizi tahmine dönüşür.

**Ölçüldü — sorunun gerçek büyüklüğü:** ölçü içeren 45.606 cümlenin **%81,5'i kolay
vaka** (tek ölçü, en fazla tek bulgu). Belirsizlik yalnızca **%18,5'te** (8.442 cümle).
Bu, doğruluk ölçümünün nasıl raporlanacağını değiştirir — bkz. Öneri 6.

### Öneri 3 — Görev bağımlılığı yanlış → **KISMEN KABUL** (dayanağı düzeltilerek)

Altındaki gözlem doğru, dayanağı yanlış.

**Doğru olan:** medspaCy ConText, niteleyicileri (negasyon, belirsizlik) **hedef
varlıklara** bağlar. Hedef yoksa bağlayacak bir şey yoktur. Varlık çıkarımı önce gelmeli.

**Yanlış olan:** "Sıra yanlış" iddiası. Excel'deki sıra **zaten doğru**:

```
TASK-10 Şema → TASK-11 Varlık → TASK-12 Negasyon → TASK-13 Manuel doğrulama
```

Öneri, `AGENTS.md`'deki Faz 2 notunu okumuş; **o notta görev numaraları hatalı**
(negasyona TASK-13, doğrulamaya TASK-12 demiş). Excel'de böyle değil. Yanlış olan not.

**Gerçek kusur — önkoşul alanları:**

| Görev | Yazılı önkoşul | Olması gereken |
|---|---|---|
| TASK-12 (negasyon) | TASK-08 *(Faz 1 bölütleme)* | **TASK-11** |
| TASK-13 (doğrulama) | TASK-12 | **TASK-11 · TASK-12** |

Excel'in referans denetleyicisi bunu yakalayamaz: yalnızca "atıf var mı" ve "ileriye
bağımlılık yok mu" diye bakar. **Yeterince güçlü olmayan** bir önkoşul geçerli görünür.
Bu, denetleyicinin bilinen sınırıdır; anlamsal doğruluk elle korunur.

→ Üç düzeltme de yapıldı: iki önkoşul alanı + `AGENTS.md` notu.

### Öneri 4 — Stabilite çıkarımı ile klinik yorum birbirine karışmış → **KABUL**

Haklı, üstelik **kendi bağlayıcı kuralımıza aykırıydı.** TASK-12'nin metni şöyle
diyordu:

> *"…stabilite güçlü bir benign göstergesi olduğundan yanlış pozitif azaltmada
> doğrudan kullanılır."*

Bu bir **karar kuralıdır** ve karar kuralları Faz 6'ya aittir. Faz 1'de ölçü aralıkları
için tam bu sebeple "üst sınırı al" demeyi reddetmiştik (D6). Aynı hata Faz 2 metnine
sızmış. Cümle kaldırıldı.

Faz 2'nin çıkaracağı, yalnızca metnin söylediği:

| Alan | Değerler |
|---|---|
| `change_type` | `stable` · `new` · `increased` · `decreased` · `resolved` · `none` |
| `temporality` | `current` · `prior` · `unknown` |
| `comparison_interval` | süre (gün) veya `null` |
| `change_target` | değişimin ait olduğu `entity_id` |

**Ölçülen destek — öneriden daha güçlü bir gerekçe var.** Faz 1'de ölçtük: raporların
**%99,6'sında tarih yok**. Yani `comparison_interval` bu korpusta **neredeyse her zaman
`null` olacak.** "Stabil" diyen 4.314 cümlenin ne kadar süredir stabil olduğu **bilinmiyor.**

Klinik olarak bu belirleyicidir: Fleischner kılavuzunda solid nodülde stabilite ancak
belirli bir izlem süresinden sonra benign lehine yorumlanır, subsolid nodülde daha uzun
süre gerekir. Süresi bilinmeyen stabilite **tek başına benign kanıtı değildir.**

→ Öneri kabul; gerekçesi korpus ölçümüyle güçlendirildi.

### Öneri 5 — Findings→Impression önem sinyali görevlerden düşmüş → **KABUL**

Haklı. D8 bu işi Faz 1'den Faz 2'ye taşımıştı ama **hiçbir Faz 2 görevi üstlenmemişti.**
Taşınan iş kaybolmuş.

Üretilecek yardımcı alanlar:

- `mentioned_in_findings`
- `mentioned_in_impression`
- `promoted_to_impression` — Findings'te geçip Impression'da da geçen kavram

**Eklenerek alındı — uygulama tuzağı.** D14'te ölçtük: **825 çalışmada Impression yok**
(811'i `"Not given."`, 14'ü boş). `"Not given."` metni bölütlemede **normal bir cümle
gibi** görünür ve o çalışmalar `impression` bölümüne sahipmiş gibi durur. Bu sinyal
hesaplanırken `impression_is_null` çalışmaları **dışlanmalı**, yoksa 825 çalışmada
"hiçbir bulgu Impression'a taşınmadı" gibi sahte bir sinyal üretilir.

Kapsam: 25.692 çalışmanın **25.675'inde** her iki bölüm de var — sinyal neredeyse tüm
korpusta uygulanabilir.

**Sınır:** Bu **yardımcı sinyaldir.** Klinik önem veya malignite etiketi olarak
kullanılmaz. Faz 1'in `is_stock_phrasing` bayrağıyla aynı statüde — yapısal gözlem,
değer yargısı değil.

### Öneri 6 — Manuel doğrulama görevi ölçülebilir değil → **KABUL** (eşikler değiştirilerek)

Haklı. "Doğruluk raporlanır" ölçülebilir bir ifade değil. Faz 1'in yapısı burada da
kullanılır: 100 rastgele + 100 hedefli zor vaka, kabul ölçütleri sonuç görülmeden yazılır.

**İki noktada öneriden ayrılıyorum:**

**(a) Tek F1 eşiği yanlış tabloyu gizler.** Kural tabanlı sözlük çıkarımında **kesinlik
(precision) doğal olarak yüksek, duyarlılık (recall) düşük** olur — sözlükte olmayan
terimi bulamaz. Tek bir F1 sayısı bu asimetriyi gizler ve yanlış güven verir. Kesinlik
ve duyarlılık **ayrı ayrı**, ayrı tabanlarla raporlanır.

**(b) Ölçü-bulgu bağında %95'lik tek sayı anlamsız.** Ölçülü cümlelerin %81,5'i tek
ölçü–tek bulgu; orada bağlama zaten doğru olur. Genel %95 bu kolay çoğunlukla
sağlanır ve **zor %18,5 hakkında hiçbir şey söylemez.** Doğru raporlama: kolay ve
belirsiz alt kümeler **ayrı ayrı**.

**(c) Öneride olmayan zorunluluk: altın açıklama seti.** Kesinlik/duyarlılık hesaplamak
için 200 cümlenin **elle işaretlenmiş doğru cevabı** gerekir. Bu, TASK-13'ün gerçek
işidir ve kısa bir işaretleme kılavuzu ister. Yoksa "doğruluk" ölçülemez, yalnızca
gözden geçirilir. Faz 1'deki aykırı değer CSV'si yöntemi burada da işe yarar: iki
bağımsız değerlendirme, uyuşmazlıkların ayrı incelenmesi.

→ Eşikler bölüm 6'da.

### Yöntem önerisi — RadGraph-XL esas alınsın → **KISMEN KABUL**

**Katıldığım:** Orijinal RadGraph yalnızca **göğüs röntgeni** raporlarından geliştirildi.
Göğüs röntgeni şemasını olduğu gibi toraks BT'ye taşımak yanlış olur — BT'de lob ve
segment düzeyi lokalizasyon, çok eksenli ölçü ve dansite niteleyicileri var; röntgende
yok. Şema seçimi bu farkı gözetmeli.

**Katılmadığım / düzelttiğim üç nokta:**

**(a) Veri erişimi ile şema erişimi karıştırılmış.** PhysioNet kimlik doğrulaması ve
veri kullanım sözleşmesi **veri setine** erişim içindir. Bizim TASK-10'da ihtiyacımız
olan **şema tanımı** — varlık tipleri ve ilişki kümesi — makalede açıktır. **TASK-10
PhysioNet'e bağlanmaz.** Kredilendirme süreci uzun olduğu için paralel başlatılır, ama
şema tasarımı onu beklemez.

**(b) İlişki kümesi ezberden yazılmaz.** Önerideki `located_at / modify / suggestive_of /
measured_by / comparison_of` listesinin ilk üçü RadGraph'tan tanıdık; son ikisi
tanıdık değil. **Hangi ilişkilerin RadGraph-XL'de tanımlı olduğu makaleden okunup
doğrulanacak** (TASK-05). Faz 1'in kuralı: iddia ediliyorsa ölçülür veya kaynağı
gösterilir; ezberse ezber olduğu söylenir.

**(c) Önerinin gözden kaçırdığı, bu projede en belirleyici olan risk:**

> **RadGraph İngilizce yazılmış raporlardan geliştirildi. CT-RATE raporları Türkçe
> yazılıp makineyle İngilizceye çevrildi.**

Bu teorik bir kaygı değil, **ölçtüm:**

| İngilizce radyoloji deyimi | CT-RATE'te cümle sayısı |
|---|---|
| `unchanged` | **3** |
| `compared` | **15** |
| `unremarkable` | **1** |
| `free of` | **0** |
| **`in favor of`** | **8.428** |

Standart bir İngilizce radyoloji sözlüğü `unchanged` arar — korpusta **3 kez** geçiyor.
Buna karşılık Türkçe *"…lehine değerlendirilmiştir"* ifadesinin çevirisi olan
**`in favor of` 8.428 cümlede** ve bu, standart ConText/NegEx sözlüklerinde **yok**.

→ **Bağlayıcı sonuç:** ithal sözlük **başlangıç noktasıdır, bitiş noktası değil.**
İpucu sözlüğü **korpustan türetilir** (yalnızca train). Bu, Faz 1'de tekrar tekrar
öğrendiğimiz şeyin aynısı: *"nodule" içindeki "no"*, *"may" ay adı sanılması*,
*`thickness` kelimesinin teknik sanılması* — hepsi ithal varsayımın veriye çarpmasıydı.

---

## 2. Faz 2 tasarımına girdi olan ölçümler

Hepsi mevcut korpustan ölçüldü, tahmin değil.

### Ölçü–bulgu bağlama zorluğu

| | Cümle | Pay |
|---|---|---|
| Ölçü içeren cümle | 45.606 | — |
| **Tek ölçü + en fazla tek bulgu** (kolay) | **37.164** | %81,5 |
| **Çoklu ölçü VEYA çoklu bulgu** (belirsiz) | **8.442** | %18,5 |
| Ölçü var, lezyon baş ismi yok | 10.627 | %23,3 |

Cümle başına ölçü: 1→41.456 · 2→3.620 · 3→399 · 4+→131 (en fazlası tek cümlede 20).

**Son satır önemli:** 10.627 ölçülü cümlede lezyon adı geçmiyor. Bunlar **organ
ölçüleridir** (aort çapı, trakea, tiroid, kalp). Şemada yalnızca gözlem tipi olursa
bu ölçüler **öksüz kalır** — bağlanacak bulgu bulunamaz.

*TASK-10 güncellemesi:* ayrı bir varlık tipi gerekmedi. **`measured_by` ilişkisinin
hedefi `anatomy` de olabiliyor**; "aorta" zaten bir anatomi varlığı olduğundan ölçü
doğrudan ona bağlanıyor. Gerekçe: `docs/06_sema_gerekce.md` bölüm 6.

### Bulgu yoğunluğu

| Cümlede bulgu baş ismi | Cümle |
|---|---|
| 0 | 267.191 |
| 1 | 151.975 |
| **2+** | **59.885 (%12,5)** |

En sık baş isimler (cümle sayısı): `lesion` 50.222 · `thickening` 42.263 ·
`effusion` 38.839 · `lymph node` 35.194 · `nodule` 26.682 · `mass` 18.162 ·
`ground-glass` 13.280 · `infiltration` 9.981 · `tumor` 8.863 · `atelectasis` 8.680 ·
`emphysema` 8.633 · `consolidation` 8.073.

### Zamansal dil

Karşılaştırma/değişim dili içeren cümle: **36.855 (%7,7)**, 15.282 çalışmada.

**Tuzak — `increase` tek başına değişim kanıtı değil.** `increas*` 25.522 cümlede
geçiyor ama yalnızca **%3,4'ünde açık zamansal referans var** (`previous`, `control`,
`follow-up`, `compared`…). Kalanı **tanımlayıcıdır, zamansal değil**:

> *"No pericardial effusion or **thickness increase** was observed."*
> *"Minimal bronchiectatic changes and mild peribronchial **thickness increases**."*

Bunlar Türkçe *"kalınlık artışı"*nın çevirisi — durağan bir tanımdır, zaman içinde
büyüme değil. `increase` gördüğünde `change_type = increased` yazan bir kural
**25 bin cümlede yanılır.**

Diğer sayımlar: `stable` 4.314 · `previous*` 6.591 · `follow*` 3.800 ·
`decrease*` 3.220 · `new*` 1.786 · `regress*` 954 · `progress*` 408.

### Belirsizlik dili

`favor` **8.534** · `?` işareti 8.448 · `compatible with` 7.068 · `consistent with`
5.985 · `may` 3.580 · `suspicious` 2.214 · `differential` 2.098 ·
`cannot be excluded` 384.

*Not: `may` sayımına İngilizce kip fiili dahildir; Faz 1'de ay adı sanılıp %10,79 sahte
sonuç verdiği yer burasıydı. Belirsizlik ipucu olarak kullanılmadan önce ayrıştırılmalı.*

### Bölüm varlığı

Her iki bölüm de olan çalışma: **25.675** · yalnızca Findings: **16**.
*Ama D14: 825 çalışmanın Impression'ı `"Not given."` veya boş — sinyal hesabında dışlanır.*

---

## 3. Veri modeli

Faz 1'in modeli korunur, üzerine iki tablo eklenir ve bir tablo genişletilir.

```
reports_study_level.parquet     1 satır = 1 çalışma          [VAR]
  │
  ├─ sentences.parquet          1 satır = 1 cümle            [VAR]
  │     │
  │     ├─ entities.parquet     1 satır = 1 varlık anması    [YENİ]
  │     │     │
  │     │     └─ relations.parquet  1 satır = 1 ilişki       [YENİ]
  │     │
  │     └─ measurements.parquet 1 satır = 1 ölçü ifadesi     [GENİŞLETİLİR]
```

Ofsetler **`report_text`'e göre** kalır (D10). Her varlık kaynak cümleye ve oradan
kaynak metne birebir geri izlenebilir.

### `entities.parquet`

| Kolon | Tip | Açıklama |
|---|---|---|
| `entity_id` | str | Kalıcı kimlik (hash) |
| `study_id`, `section`, `sent_idx` | | Kaynak cümle |
| `char_start`, `char_end` | int | `report_text` üzerinde ofset |
| `raw_text` | str | Metinde geçtiği hâli — **değiştirilmez** |
| `entity_type` | str | `observation` · `anatomy` · `qualifier` · `device` — *TASK-10'da sadeleşti: `anatomical_measurement` tipi gerekmedi, `measured_by` ilişkisinin hedefi `anatomy` olabildiği için organ ölçüleri zaten bağlanıyor. Gerekçe: `docs/06_sema_gerekce.md` bölüm 6* |
| `normalized_concept` | str? | Sözlükteki karşılık; yoksa `null` |
| `concept_source` | str? | `radlex` · `yerel_sozluk` · `null` |
| `laterality` | str? | `right` · `left` · `bilateral` · `null` |
| `assertion` | str | `present` · `absent` · `uncertain` *(TASK-12 doldurur)* |
| `temporality` | str | `current` · `prior` · `unknown` *(TASK-12)* |
| `change_type` | str? | `stable`/`new`/`increased`/`decreased`/`resolved`/`none` *(TASK-12)* |
| `mentioned_in_findings` | bool | *(türetilmiş)* |
| `mentioned_in_impression` | bool | *(türetilmiş)* |
| `promoted_to_impression` | bool | *(türetilmiş, D8)* |
| `extraction_rule` | str | Bu varlığı hangi kural üretti — hata analizi için |
| `segmentation_version`, `template_version`, `entity_version` | str | Sürüm zinciri |

### `relations.parquet`

| Kolon | Açıklama |
|---|---|
| `relation_id` | Kalıcı kimlik |
| `study_id` | Kaynak çalışma |
| `head_id`, `tail_id` | Bağlanan iki tarafın `entity_id` / `measurement_id`'si |
| `head_kind`, `tail_kind` | `entity` · `measurement` — hangi tablodan geldiği |
| `relation_type` | `located_at` · `modify` · `suggestive_of` · `measured_by` · `change_of` |
| `attachment_rule` | Bu bağı hangi kural kurdu — uygulanan küme: `tek_aday`, `en_yakin_sol`, `en_yakin_sag`, `ayni_oge`, `esitlikte_sag`, `gozlem_onceligi`, `konum_edati_atlandi`, `en_buyugu_ifadesi`, `bolum_arasi`; kurulamayan bağlar `unresolved_attachments`'a `belirsiz`/`aday_yok` sebebiyle yazılır |
| `is_cross_sentence` | Cümleler arası bağ mı (Impression↔Findings) |
| `relation_version` | Sürüm |

**İlişki kümesi TASK-10'da kesinleşir.** Yukarıdaki liste çalışma taslağıdır; RadGraph-XL
makalesindeki tanımlar okunduktan sonra sadeleştirilebilir veya adlandırma değişebilir.
**Karar TASK-10'da, kaynağa bakılarak verilir; şu an sabitlenmedi.**

### `measurements.parquet` — genişletme (`meas-1.1`)

| Yeni kolon | Açıklama |
|---|---|
| `measurement_id` | Kalıcı kimlik — ilişki tablosundan referans verilebilmesi için |
| `temporality` | `current` · `prior` · `unknown` — 804 cümlede iki tetkik ölçüsü bir arada |

Mevcut kolonlar ve ofsetler **değişmez**; yalnızca kolon eklenir. `measurement_version`
`meas-1.0` → `meas-1.1` olur, testler eski kolonların korunduğunu doğrular.

---

## 4. Görev sırası, kapsamı ve bağımlılıkları

```
TASK-10  Şema
   ↓
TASK-11  Varlık ve ilişki çıkarımı ────┐
   ↓                                   │
TASK-12  Negasyon · belirsizlik · zaman│
   ↓                                   │
TASK-13  Manuel doğrulama  ←───────────┘
```

### TASK-10 — Yapılandırılmış Çıkarım Şemasının Tanımlanması

Varlık tipleri, ilişki kümesi, alan tipleri ve doğrulama kuralları. RadGraph-XL'in
toraks BT kapsamı **makaleden doğrulanır**; göğüs röntgeni şeması olduğu gibi
alınmaz. Her varlık kaynak cümleye bağlanabilir olmalı — dayanak alanı zorunlu.

**Çıktı:** `configs/extraction_schema.json` · `docs/06_sema_gerekce.md`
**Önkoşul:** TASK-05

### TASK-11 — Bulgu, Anatomik Bölge ve Niteleyici Çıkarımı

Varlık çıkarımı, toraks anatomi sözlüğü, RadLex eşlemesi; niteleyicilerin
(kenar, dansite, kalsifikasyon paterni) ilgili bulguya bağlanması. **Ölçülerin
bulgulara bağlanması bu görevin işidir**: her ölçüye kalıcı kimlik verilir, en yakın
uygun bulguya bağlanır, bağı kuran kural kaydedilir. Aynı cümlede birden çok lezyon
veya ölçü olduğunda (8.442 cümle) bağ `belirsiz` işaretlenip TASK-13'te incelenir.
Organ ölçüleri (10.627 cümle) `measured_by` ile doğrudan anatomik yapıya bağlanır.

**Çıktı:** `entities.parquet` · `relations.parquet` · `measurements.parquet` (meas-1.1)
· `src/radyovlm/extraction/entities.py` · `configs/anatomi_sozlugu.yaml`
**Önkoşul:** TASK-10

### TASK-12 — Negasyon, Belirsizlik ve Zamansal İfade Çözümlemesi

Varlıklara `assertion`, `temporality` ve `change_type` atanması. ConText/NegEx
yaklaşımıyla kapsam sınırları hesaplanır. **İpucu sözlüğü korpustan türetilir**
(yalnızca train): İngilizce radyoloji deyimleri bu çeviri korpusta yok
(`unchanged` 3, `compared` 15), buna karşılık `in favor of` 8.428 cümlede.
`increase` ifadesinin %96,6'sı tanımlayıcıdır, zamansal değil — tek başına değişim
kanıtı sayılmaz. Faz 1'in `is_stock_phrasing` bayrağıyla birleştiğinde
"rutin negatif" ile "kasıtlı negatif" ayrımı elde edilir.
**Bu görev metnin ne söylediğini kaydeder; söylenenin klinik anlamını yorumlamaz.**

**Çıktı:** `src/radyovlm/extraction/context.py` · `configs/ipucu_sozlugu.yaml`
· güncellenmiş `entities.parquet` · **ayrıntılı plan: `docs/07_task12_plani.md`**
**Önkoşul:** TASK-11

### TASK-13 — Çıkarım Doğruluğunun Manuel Örneklemle Ölçülmesi

200 cümlelik altın açıklama seti (100 rastgele + 100 hedefli zor vaka) üretilir ve
kısa bir işaretleme kılavuzuna göre elle etiketlenir. Varlık kesinliği ve duyarlılığı
ayrı ayrı, negasyon ve belirsizlik makro-F1, ölçü-bulgu bağı **kolay ve belirsiz alt
kümeler ayrı**, zamansal sınıf doğruluğu ölçülür. Hata tipleri sınıflandırılır ve
`extraction_rule` / `attachment_rule` alanları üzerinden hangi kuralın ürettiği
gösterilir.

**Çıktı:** `data/processed/altin_aciklama_faz2.csv` · `docs/08_isaretleme_kilavuzu.md`
· `reports/cikarim_dogruluk_raporu.md`
**Önkoşul:** TASK-11 · TASK-12

---

## 5. Kararlar

### `[KARAR] D15` — Faz 2 çıkarımı LLM ile yapılmaz

Faz 2 çıktısı Faz 3'ün altın standardını ve Faz 4'ün karşılaştırma tabanını besler.
Faz 4 tam olarak **LLM'lerin çıkarım başarısını ölçer**. Faz 2'yi bir LLM'e yaptırırsak
Faz 4 kendi girdisini değerlendirmiş olur — **döngüsel** ve geçersiz.

→ Faz 2 **deterministik ve denetlenebilir** yöntemle kurulur: sözlük + kural + ConText.
Aynı girdi her zaman aynı çıktıyı verir; her çıkarımın hangi kuraldan geldiği kayıtlıdır.
Eğitilmiş bir çıkarım modeli (ör. RadGraph-XL) **karşılaştırma amacıyla** koşulabilir
ama **gerçeğin kaynağı olarak kullanılmaz**.

### `[KARAR] D16` — Negasyon ve belirsizlik ipucu sözlüğü korpustan türetilir

İthal İngilizce sözlük başlangıç noktasıdır, bitiş noktası değil. Gerekçe ölçüldü
(bölüm 1, yöntem önerisi). Sözlük **yalnızca train'den** türetilir — D11'in aynısı.

### `[KARAR] D17` — Stabilite yorumu Faz 2'de yapılmaz

`change_type` ve `temporality` kaydedilir; "stabil olduğu için benign" kararı Faz 6'ya
aittir. Korpusta karşılaştırma aralığı neredeyse hiç bilinmediğinden (tarih yok, %99,6)
süresi bilinmeyen stabilite tek başına benign kanıtı sayılmaz.

### `[KARAR] D18` — Ölçü-bulgu bağı kaydedilirken bağı kuran kural da kaydedilir

`attachment_rule` alanı zorunludur. Belirsiz vakalar `belirsiz` etiketiyle işaretlenir,
tahmine dayalı bir bağ **sessizce** kurulmaz.

### `[KARAR] D19` — Findings→Impression sinyali yalnızca yardımcıdır

`promoted_to_impression` yapısal bir gözlemdir; klinik önem veya malignite etiketi
olarak kullanılmaz. `impression_is_null` çalışmaları hesaptan dışlanır.

### `[KARAR] D20` — Eşit uzaklıkta bağlama yön kuralı *(TASK-11'de eklendi)*

`modify` ve `measured_by` ilişkilerinde iki aday eşit uzaklıktaysa **sağdaki** seçilir.
Gerekçe dil bilgiseldir: İngilizce isim öbeğinde niteleyici baş isimden önce gelir
(*"Mediastinal **millimetric** lymph nodes"* → baş isim sağda). Ayrı kural adıyla
(`esitlikte_sag`) kaydedilir ki eşitlikten gelen bağ kesin bağdan ayırt edilebilsin.

`located_at`'te böyle bir yön kuralı **yoktur** — gözlem ile anatomi arasında dilbilgisel
bir sıra zorunluluğu olmadığı için eşitlik bağ kurdurmaz (D18).

### `[KARAR] D21–D24` — TASK-11 incelemesinden doğan kararlar

| | |
|---|---|
| **D21** | TASK-12 koşmadan **kesinlik ve zaman iddia edilmez** (`not_processed` / `unknown`). `uncertain` bu amaçla kullanılamaz — o klinik belirsizliktir. |
| **D22** | **Hiçbir bağ sessizce düşürülmez** — `unresolved_attachments` tablosu. |
| **D23** | Ölçü **bulguyu** ölçer, organı değil — konum edatı eleme + koşullu gözlem önceliği. |
| **D24** | Sözlük kavram adı metnin **söylemediğini iddia edemez** — ayırt edemeyen desen genel kavrama düşer. |

Gerekçeler ve ölçümler: `docs/04_uygulama_gunlugu.md` §3-E.

*D1–D14 için `docs/03_standartlastirma_plani.md`.*

---

## 6. Kabul ölçütleri

**Sonuç görülmeden yazıldı.** Faz 1'in kuralı: ölçüt sağlanmazsa ölçüt gevşetilmez,
iş düzeltilir.

| # | Ölçüt | Eşik | Sağlanmazsa |
|---|---|---|---|
| K1 | Her varlığın ofseti metne birebir oturur | **%100** | Yazma reddedilir |
| K2 | Her ilişkinin iki ucu var olan kimliklere işaret eder | **%100** | Yazma reddedilir |
| K3 | Sürüm zinciri tüm tablolarda korunur | **%100** | Yazma reddedilir |
| K4 | Varlık **kesinliği** (200 cümlelik altın set) | **≥ %90** | Sözlük daraltılır |
| K5 | Varlık **duyarlılığı** (aynı set) | **≥ %80** | Sözlük genişletilir |
| K6 | Negasyon makro-F1 | **≥ %85** | ConText kuralları gözden geçirilir |
| K7 | Belirsizlik makro-F1 | **≥ %75** | İpucu sözlüğü genişletilir |
| K8 | Ölçü-bulgu bağı — **kolay** alt küme | **≥ %97** | Kural hatalıdır, düzeltilir |
| K9 | Ölçü-bulgu bağı — **belirsiz** alt küme | **≥ %80** | Kalanı `belirsiz` bırakılır |
| K10 | Zamansal sınıf (`current`/`prior`) doğruluğu | **≥ %85** | Zaman kuralları gözden geçirilir |

**Eşiklerin gerekçesi.** K4 > K5: kural tabanlı sözlük çıkarımında kesinlik yüksek,
duyarlılık düşük olur; tek bir F1 sayısı bu asimetriyi gizler. K7 < K6: belirsizlik
sınıfı doğası gereği daha öznel, sınırı bulanık; negasyondan yüksek beklenti gerçekçi
değil. K9 < K8: belirsiz alt küme zaten çözülemeyen vakaları içerir; **oradaki hedef
%100 doğru bağlamak değil, yanlış bağlamamaktır** — çözülemeyeni `belirsiz` bırakmak
kabul edilebilir bir sonuçtur, uydurma bağ kurmak değildir.

**Altın açıklama seti bileşimi:**

| Küme | Adet | İçerik |
|---|---|---|
| Rastgele | 100 | Korpustan tesadüfi (train) |
| Hedefli zor | 100 | Negasyon 20 · belirsizlik 20 · çoklu bulgu 20 · önceki tetkik 20 · çoklu ölçü 20 |

---

## 7. Karar bekleyen noktalar

Kodlamaya başlamadan önce iki başlıkta onay gerekiyor.

### (1) Çıkarım yönteminin omurgası — D15

Öneri: **deterministik sözlük + kural + ConText.** Gerekçe döngüsellik (bölüm 5).
Alternatif, eğitilmiş bir çıkarım modelini (RadGraph-XL) omurga yapmaktı; bu, Faz 4'ün
karşılaştırma zeminini bulandırır ve dışarıdan gelen bir modelin kararlarını
denetleyemeden kabul etmek anlamına gelir.

### (2) PhysioNet kredilendirmesi şimdi başlatılsın mı

**TASK-10 buna bağlı değil** — şema tanımı makalede. Ama süreç haftalar sürüyor ve
ücretsiz. Başvurunun **şimdi, paralel olarak** başlatılmasını öneriyorum; TASK-11'de
karşılaştırma koşusu yapmak istersek hazır olur, istemezsek bir kaybımız olmaz.

---

## 8. Riskler

| Risk | Etki | Karşılık |
|---|---|---|
| Çeviri artefaktları ithal sözlüğü boşa düşürür | **Yüksek** | D16: sözlük korpustan türetilir; ölçüldü |
| `increase` gibi tanımlayıcı ifadeler zamansal sanılır | **Yüksek** | Açık zamansal referans şartı; %3,4 ölçüldü |
| Organ ölçüleri bağlanacak bulgu bulamaz | Orta | ✅ **çözüldü (TASK-10):** `measured_by` hedefi `anatomy` olabilir; 10.627 cümle ölçüldü |
| Anatomi sözlüğü kapsamı yetersiz kalır | Orta | K5 duyarlılık eşiği; sözlük genişletilir |
| RadLex kullanım koşulları doğrulanmamış | Orta | **TASK-11'e kaydı** — şemada `concept_source` alanı hazır, eşleme orada yapılacak |
| Cümleler arası gönderme çözülemez (*"It is stable."*) | Orta | `is_cross_sentence` alanı; çözülemeyen `unresolved` bırakılır |
| Şema sonradan değişirse tablolar yeniden üretilir | Düşük | Sürüm zinciri var; yeniden üretim ucuz |

---

## 9. Faz 1'den taşınan, Faz 2'de karşılanan işler

| Taşınan | Karar | Faz 2'deki yeri |
|---|---|---|
| Şablon tipi dörtlü sınıflandırması | D12 | TASK-12 (`assertion` üzerinden) |
| Findings→Impression önem sinyali | D8 | TASK-11 türetilmiş alanları |
| Güncel/önceki ölçü ayrımı (804 cümle) | — | TASK-12 (`temporality`) |
| Ölçünün hangi lezyona ait olduğu (712 cümle) | — | TASK-11 (`measured_by`) |
