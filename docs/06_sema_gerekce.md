# Çıkarım Şemasının Gerekçesi

**Görev:** TASK-10 · **Şema sürümü:** `sema-1.1` · **Tarih:** 2026-08-26

> **`sema-1.1` değişiklikleri** (TASK-11 incelemesi sonrası):
> `assertion` kümesine **`not_processed`** eklendi ve varsayılan yapıldı; `temporality`
> varsayılanı `unknown` oldu — TASK-12 koşmadan kesinlik iddia edilmesin diye.
> **`unresolved_attachments`** tablosu eklendi: kurulamayan bağ sessizce düşmez.
> **K3e** doğrulama kuralı eklendi: niteleyici kavramı grubunun değerlerinde olmalı.
> İki bağlama kuralı eklendi: `konum_edati_atlandi`, `gozlem_onceligi`.
> Niteleyici adları sözlükle hizalandı (`fat`→`fat_containing`, `granuloma`→`granulomatous`);
> `air_bronchogram` ve `cavitary` niteleyici değil **gözlem** olduğu için çıkarıldı.
> Gerekçeler: `docs/04_uygulama_gunlugu.md` §3-E.

**Şema dosyası:** `configs/extraction_schema.json`
**Doğrulayıcı:** `src/radyovlm/extraction/schema.py` · **Testler:** `tests/test_schema.py` (37)

---

## 1. Şema neye yarar

Faz 2, "Sağ akciğer üst lobda 8 mm spiküle nodül izlendi" cümlesini makinenin
sorgulayabileceği kayda çevirecek. **Şema, o kaydın hangi alanlardan oluştuğunu ve
hangi değerleri alabileceğini önceden sabitler.**

Sabitlenmezse ne olur: bir cümlede `spiculated`, diğerinde `spiculation`, üçüncüsünde
`spicule` yazılır; Faz 3'ün gösterge sözlüğü hangisini arayacağını bilemez. Faz 1'de
ölçüleri `mm` cinsine indirmemizin sebebi buydu — aynı disiplin, artık bulgular için.

---

## 2. Neyi temel aldık, kaynaktan doğrulandı

**RadGraph-XL** (Delbrouck ve ark., ACL Findings 2024) esas alındı. İki nokta
**kaynağından teyit edildi**, ezberden yazılmadı:

| Doğrulanan | Sonuç |
|---|---|
| Toraks BT kapsıyor mu | **Evet** — göğüs BT, abdomen/pelvis BT, beyin MR, göğüs röntgeni |
| İlişki kümesi | **Üç tane:** `modify`, `located_at`, `suggestive_of` |
| Varlık etiketleri | `ANAT-DP/DA/U`, `OBS-DP/DA/U`, ayrıca `MEAS` (ölçü) |
| Değişim/zamansallık | **YOK** — o RadGraph2'nin (2023) katkısı |

### Bu doğrulama planı iki yerde düzeltti

**(a) Önerilen `measured_by` ve `comparison_of` ilişkileri RadGraph'ta yok.** Faz 2
planında bunları "doğrulanacak" diye işaretlemiştik; doğrulandı ve **yoklar**. RadGraph-XL
ölçüleri `modify` ile bağlıyor. İkisini de kullanıyoruz ama artık **RadGraph'tan
geldiklerini iddia etmiyoruz** — bilinçli sapma olarak kayıtlılar (bölüm 4).

**(b) Ölçüler RadGraph-XL'de birinci sınıf varlık (`MEAS`).** Bu, Faz 1'de ölçüleri ayrı
tabloda tutma kararımızı destekliyor; ilişki tablosundan referansla bağlanıyorlar.

---

## 3. Varlık tipleri

| Tip | Ne | Örnek |
|---|---|---|
| `observation` | Radyolojik gözlem | nodule, effusion, atelectasis |
| `anatomy` | Anatomik yapı | upper lobe, mediastinum, aorta |
| `qualifier` | Niteleyici | spiculated, ground-glass, calcific |
| `device` | Cihaz / girişim izi | catheter, stent, pacemaker |

`device` ayrı tutuldu çünkü korpusta gerçekten var (katater 1.609, stent 866, pacemaker
410 cümle) ve **gözlemle karıştırılırsa yanlış pozitif üretir** — "port kateter ucu sağ
atriyumda" bir bulgu değil, bir cihazdır.

---

## 4. RadGraph'tan bilinçli dört sapma

Her sapma şemada `sapmalar` bölümünde, **geri dönüşü mümkün mü** bilgisiyle kayıtlı.

### (a) Kesinlik ayrı alanda tutulur — *kayıpsız*

RadGraph kesinliği etikete gömüyor: `OBS-DA` = "gözlem, kesinlikle yok".
Biz ayırıyoruz: `entity_type=observation` + `assertion=absent`.

**Neden:** Projenin bağlayıcı kuralı — *negasyon, kalıp ve malignite ilgisi üç bağımsız
eksendir.* Etikete gömülürse iki eksen birleşir. Ayrıca **TASK-11 varlığı, TASK-12
kesinliği yazıyor**; ayrı görevler ayrı kolon yazmalı, aynı kolonu üst üste ezmemeli —
Faz 1'de sürüm zincirinin kopma sebebi tam olarak buydu.

Dönüşüm birebir: `observation + absent → OBS-DA`. Test bunu her kombinasyon için
denetliyor.

### (b) `qualifier` ayrı tip — *kayıpsız*

RadGraph niteleyicileri de `OBS` sayıp `modify` ile bağlıyor. Biz ayırdık, çünkü
**spikülasyon, buzlu cam ve kalsifikasyon Faz 3'ün gösterge sözlüğünün doğrudan
girdisi.** Ayrı tip olmazsa Faz 3, tüm gözlemleri tarayıp niteleyici ayıklamak zorunda
kalır.

### (c) `measured_by` ilişkisi eklendi — *kayıpsız*

RadGraph ölçüyü `modify` ile bağlıyor. Ayrı bir ilişki tipi verdik çünkü **boyut eşikleri
bu projenin merkezinde** ve ölçü-bulgu bağı doğruluğunun (K8/K9) ayrıca ölçülebilmesi
gerekiyor. RadGraph biçimine çevrilirken `modify`'a düşer.

### (d) `change_of` ve `change_type` eklendi — **kayıplı**

RadGraph-XL'de değişim ekseni yok. Ama TASK-12 bunu yapmak zorunda: **804 cümlede iki
farklı tetkikin ölçüsü bir arada.** RadGraph2'nin yaklaşımı alındı.

Bu sapma **kayıplıdır** ve şemada öyle işaretli — RadGraph-XL biçimine çevrilirse bu
bilgi düşer. "Kayıpsız" diye iddia etmek yanlış olurdu; test bunu denetliyor.

---

## 5. Şemanın alan değerleri korpustan ölçüldü

**Şemadaki her kontrollü değer, yanında kaç cümlede geçtiğiyle birlikte duruyor.**
Bu, Faz 1'in "önce ölç" disiplininin şemaya taşınmış hâli: ders kitabından terim
kopyalayıp sonra korpusta bulamamayı engelliyor.

Ayrıca reddedilen değerler **silinmedi**, `olculup_alinmayan` altında sayılarıyla
duruyor — sonradan "bunu neden almadık" sorusunun cevabı belgede.

### Ölçüm üç yerde tasarımı değiştirdi

#### (a) Kalsifikasyon paterni ekseni bu korpusta **yok**

| Terim | Cümle |
|---|---|
| `popcorn` | **0** |
| `central` | 26 |
| `laminated / concentric` | 26 |
| `eccentric` | 19 |
| `punctate` | 50 |

Faz 3 planı benign gösterge sözlüğüne *"popcorn kalsifikasyon"* yazmıştı. **Korpusta
sıfır cümlede geçiyor.** Bu eksene dayanan bir benign kuralı burada hiçbir zaman
tetiklenmez.

Cevaplanabilen tek soru: **"kalsifiye mi?"** — `calcific*` 17.193 cümlede.

Şemaya uyarı olarak yazıldı, test bunu denetliyor. **Faz 3'e taşınan bir bulgudur.**

#### (b) Fleischner'ın dansite üçlüsü de yok

| Terim | Cümle |
|---|---|
| `part-solid / semi-solid` | 103 |
| `subsolid` | **5** |
| `solid component` | 19 |
| `ground-glass` | **13.280** |
| `calcific*` | **17.193** |

Lung-RADS ve Fleischner **solid / parça-solid / nonsolid** üçlüsüne dayanır. Bu korpusta
o üçlü pratikte yok; baskın dansite ekseni **kalsifiye** ve **buzlu cam**.

Bu, klinik çerçeve kararımızı güçlendiriyor: *eşikler gösterge referansı olarak kullanılır,
**Lung-RADS kategorisi üretilmez.*** Kategori üretmek için gereken alan zaten metinde yok.

#### (c) Bu korpusun benign niteleyicisi `sequela`

`sequela` (Türkçe *"sekel"*) **12.177 cümlede**; `granuloma` yalnızca 117'de. Ders
kitabının benign sözlüğü değil, bu korpusun kendi benign sözlüğü. `chronicity` grubu
buradan doğdu.

---

## 6. Organ ölçüleri sorunu — plandan sapma

Faz 2 planında `anatomical_measurement` adında **beşinci bir varlık tipi** öngörmüştüm.
Sebep: ölçü içeren **10.627 cümlede lezyon adı geçmiyor** (aort çapı, trakea, tiroid,
kalp); bağlanacak bir bulgu yok, ölçü öksüz kalıyor.

**Şemayı yazarken daha temiz bir çözüm çıktı ve plandan saptım.** RadGraph'ın modelinde
"aorta" zaten bir `anatomy` varlığı, "34 mm" bir `MEAS`. Yeni tip icat etmeye gerek yok —
**`measured_by` ilişkisinin hedefi `anatomy` de olabilsin** yeter.

| | Plan | Uygulanan |
|---|---|---|
| Çözüm | Yeni varlık tipi | Var olan ilişkinin hedef kümesi genişletildi |
| Şema yüzeyi | 5 tip | 4 tip |
| RadGraph uyumu | Sapma | Sapma yok |

Beş yerine dört tip, bir sapma yerine sıfır sapma. Test bunu denetliyor
(`test_organ_olcusu_iliskisi_gecer`).

---

## 7. Doğrulama kuralları

Şema süs değil; **uygulanabilir.** `src/radyovlm/extraction/schema.py` üretilen tabloyu
şemaya karşı denetler ve **ihlal varsa yazmayı reddeder** — `04_segment_sentences.py`'nin
ofset doğrulaması başarısız olunca çıktı yazmayı reddetmesinin aynısı.

| Kod | Kural |
|---|---|
| K1 | `raw_text == report_text[char_start:char_end]` |
| K1b | `char_end > char_start` |
| K1c | Varlık kaynak cümlenin dışına taşmaz |
| K2 | İlişkinin iki ucu da var olan bir kimliğe işaret eder |
| K2b | Head/tail tipleri ilişki tanımına uyar |
| K2c | İlişkinin iki ucu aynı çalışmada |
| K3 | Sürüm zinciri tam ve katman başına tekil |
| K3b | `entity_id` ve `relation_id` tekrar etmez |
| K3c | Kontrollü kolonlar yalnızca tanımlı değer taşır |
| K3d | `extraction_rule` ve `attachment_rule` boş bırakılamaz (D18) |

Her ihlal sınıfının **gerçekten yakalandığı** sentetik çerçevelerle sınandı; testler
"ihlal var mı" değil, **doğru kodun üretildiğini** denetliyor.

---

## 8. Şemanın kendi tutarlılığı da test ediliyor

Alışılmadık ama Faz 1'in mantığına uygun: **şema bir veri dosyası, o hâlde
doğrulanabilir.** İçerdiği testlerden bazıları:

- Her ilişkinin `head`/`tail` listesi gerçek varlık tiplerine bakıyor mu
- Her `kume` referansı boş olmayan bir değer kümesine çözülüyor mu
- **Bir grupta kabul edilen en zayıf değer, reddedilen en güçlü değerden daha çok
  destekli mi** — bunu geçemezsek seçim tutarsızdır
- Kabul ve ret listeleri çakışıyor mu
- RadGraph eşlemesi `entity_type × assertion`'ın **her** kombinasyonunu kapsıyor mu
- Kayıplı sapma açıkça kayıplı işaretlenmiş mi

---

## 9. Sonraki göreve taşınanlar

| Konu | Nereye |
|---|---|
| `both` (95.616) → `bilateral` eşlemesi | TASK-11 sözlüğü |
| `in favor of` (8.428), `evaluated` (26.020) → `suggestive_of` ipuçları | TASK-12 |
| Kalsifikasyon paterni ekseninin boş olması | **Faz 3** gösterge sözlüğü |
| Fleischner dansite üçlüsünün yokluğu | **Faz 3** şeması |
| `sequela` (12.177) baskın benign niteleyici | **Faz 3** benign sözlüğü |
