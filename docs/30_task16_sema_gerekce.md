# TASK-16 · Şema Gerekçesi — A Tipi Kuralların Aktarımı

**Tarih:** 2026-09-03 · **Adım:** 2 (docs/29 §8.5)
**Kabul ölçütü:** her A kuralı için kaynağın **spesifik tablo/paragrafı** gösterilir (docs/29 §8.2)

**A tipi kural** = kaynakta **karar kuralı olarak açıkça yazılı** olan kural.
Alan tanımı A yapmaz; kuralın kendisi cümle olarak yazılı olmalıdır (docs/29 §2.2).

Bu belge yalnız **doğrulanmış** aktarımları içerir. Okunmamış kaynaktan kural
yazılmamıştır.

---

## 1 · Kaynak doğrulama durumu

| kaynak | erişim | durum |
|---|---|---|
| **Alan Sözlüğü v12** §12.2 | dosya depoda, **tam metni okundu** | ✅ **doğrulandı** — §2 |
| **RECIST 1.1** | PDF indirildi ve okundu | ✅ **doğrulandı** — §3 |
| **ACR Lung-RADS v2022** | elle indirildi → `data/raw/kilavuzlar/lung_rads_v2022.pdf` (2 sayfa), **tam metni okundu** | ✅ **doğrulandı** — §4 |
| **Fleischner Society 2017** | elle indirildi → `data/raw/kilavuzlar/fleischner_2017.pdf` (16 sayfa), **okundu** | ✅ **doğrulandı** — §5 |

⚠ **Erişim notu:** Lung-RADS ve Fleischner **ücretsizdir ama programla
indirilemez** (302 yönlendirme / 403). İnsan tarayıcısıyla indirilip depoya
konuldu. `data/raw/` gitignore'dadır — telifli içerik commit'e girmez.

⚠ **Aktarımın düzeyi:** her iki kılavuz da **görüntüden nodül yönetimi** için
yazılmıştır; bu şema **rapor metnini sınıflandırır**. Aktarılan şey **ilke ve
tanımlardır**, yönetim önerileri değil. Boyut/hacim eşikleri kayda geçirilir ama
şemaya girmez — korpusta ölçü-nodül bağı bu düzeyde çözülmemiştir.

---

## 2 · Alan Sözlüğü §12.2 — 20 doğrulanmış kural

Belgenin §12.2'si *"Negasyon ve Belirsizlik Eşleme Tablosu"* başlığını taşır ve
**ifade → değer** eşlemesini açıkça yazar. Üç *"Kritik kural"* ile birlikte
**20 A kuralı** verir.

### 2.1 Kesinlik ekseni

| # | ifade sınıfı (belge örnekleri) | değer | belge |
|---|---|---|---|
| A1 | *"saptanmamıştır", "izlenmemiştir", "görülmemiştir", "mevcut değildir", "seçilmemiştir"* | `absent` | §12.2 satır 1 |
| A2 | *"düşündürecek görünüm saptanmadı", "aleyhine bulgu yoktur", "kesin olarak dışlanmıştır", "ekarte edilmiştir"* | `absent` (güçlü negatif) | §12.2 satır 2 |
| A3 | *"dışlanamaz", "ekarte edilememektedir", "olasılığı gündemdedir", "göz ardı edilemez"* | **`uncertain`** — belge vurgusuyla *"present değil!"* | §12.2 satır 3 · **Kritik kural 1** |
| A4 | *"ayırt edilemedi", "ayırıcı tanısı yapılamadı", "net olarak karakterize edilemedi"* | `uncertain` | §12.2 satır 4 |
| A5 | *"şüpheli", "şüpheli görünüm", "kuşkulu görünüm"* | `present` + `suspicious_appearing=yes` | §12.2 satır 5 |
| A6 | *"olası", "olasılıkla", "büyük olasılıkla", "muhtemel"* | `present` (orta-yüksek kesinlik) | §12.2 satır 6 |
| A7 | *"ile uyumludur", "ile uyumlu görünüm", "ile örtüşmektedir"* | `present` | §12.2 satır 7 |
| **A8** | ⭐ *"**lehine değerlendirilmiştir**", "lehine yorumlanmıştır", "lehinedir", "lehine bulgular"* | **`present`** | §12.2 satır 8 |
| A9 | *"belirsiz karakterde", "net karakterize edilemeyen", "indeterminate görünüm"* | `uncertain` | §12.2 satır 15 |
| A10 | bulgu hiç geçmiyor | `not_mentioned` | §12.2 son satır |

### 2.2 Zaman / değişim ekseni

| # | ifade sınıfı | değer | belge |
|---|---|---|---|
| A11 | *"stabildir", "değişiklik göstermemiştir", "önceki ile aynı boyuttadır", "benzer boyut ve görünümdedir"* | `stable_nodule=yes` / `growth_status=stable` | §12.2 satır 9 |
| A12 | *"yeni gelişen", "önceki tetkikte izlenmeyen", "de novo", "ilk defa saptanmıştır"* | `growth_status=new` | §12.2 satır 10 |
| A13 | *"artmıştır", "boyut artışı göstermiştir", "büyümüştür", "progresyon göstermektedir"* | `growth_status=increased` | §12.2 satır 11 |
| A14 | *"azalmıştır", "küçülmüştür", "regresyon göstermiştir", "gerilemiştir"* | `growth_status=decreased` | §12.2 satır 12 |
| A15 | *"kaybolmuştur", "rezolüsyon göstermiştir", "artık izlenmemektedir"* | `growth_status=resolved` | §12.2 satır 13 |

### 2.3 Teknik ve aksiyon ekseni

| # | ifade sınıfı | değer | belge |
|---|---|---|---|
| A16 | *"değerlendirilemedi", "teknik olarak sınırlı", "solunum artefaktı nedeniyle sınırlı"* | `uncertain` + `image_quality_issue=present` | §12.2 satır 14 |
| A17 | *"klinik korelasyon önerilir", "kontrol BT önerilir", "PET/BT ile değerlendirme önerilir"* | **status DEĞİL** → ayrı alan (`pet_bt_recommended` / `biopsy_recommended`) | §12.2 satır 16 · **Kritik kural 3** |

### 2.4 Üç Kritik kural

| # | kural | belge |
|---|---|---|
| **A18** | *"Dışlanamaz"* ifadesi **`present` değil `uncertain`** olarak kodlanmalıdır — negatif cümle yapısı yanıltabilir | Kritik kural 1 |
| **A19** | *"Düşündürecek görünüm saptanmadı"* gibi **güçlü negatif** ile sade *"saptanmadı"* **aynı** `absent` değerine eşlenir | Kritik kural 2 |
| **A20** | *"Klinik/radyolojik korelasyon önerilir"* bir **status değeri değil, aksiyon önerisidir**; ayrı alana yönlendirilir | Kritik kural 3 |

### 2.5 ⭐ A8 bir C kararını doğruladı

**A8** (*"lehine değerlendirilmiştir"* → `present`), docs/31 §2'de bulunan üçüncü
ölçüm artefaktını **kaynaktan doğrular**: `in favor of` (Türkçe *"lehine"*)
belirsizlik ifadesi **değildir**, kesin bir hükümdür.

Bu, iki bağımsız kaydı örtüştürüyor:

| kayıt | ne diyordu |
|---|---|
| **D29** (proje, TASK-12) | belirsizlik ipuçları `cikarim_ifadesi` → `present` |
| **A8** (belge §12.2) | *"lehine değerlendirilmiştir"* → `present` |

Sonuç: **docs/31 #12'nin varsayılan değişikliği (`low` → benign) A tipi dayanak
kazandı**, yalnız örneğe dayanmıyor.

### 2.6 Aktarımın dil sınırı

§12.2 **Türkçe yüzeyler** verir; çalışma korpusu (CT-RATE) İngilizcedir. Aktarılan
şey **yüzey değil kuraldır** — *"çıkarım ifadesi `present`e eşlenir"* dilden
bağımsızdır. İngilizce yüzey karşılıkları TASK-17'nin işidir; bu belge
**kavram düzeyinde** aktarır.

---

## 3 · RECIST 1.1 — 4 doğrulanmış kural

Kaynak: Eisenhauer et al., *Eur J Cancer* 2009;45:228 · PDF indirildi ve okundu.

| # | kural | değer |
|---|---|---|
| **A21** | Ölçülebilir lezyon eşiği | en uzun çap **≥10 mm** |
| **A22** | ⭐ **Lenf nodu kısa aksından ölçülür** ve ölçülebilirlik eşiği | kısa aks **≥10 mm** (`<10 mm` ölçülemez) |
| **A23** | Progresif hastalık | hedef lezyon çap toplamında **≥%20 artış** |
| **A24** | Stabil hastalık | **<%20** değişim (her iki yönde) |

### 3.1 Kapsam uyarısı

RECIST **onkolojik takip** protokolüdür; hedef lezyon seçimi ve yanıt
değerlendirmesi için yazılmıştır. Bu şema **tek zamanlı rapor sınıflandırması**
yapar, yanıt değerlendirmesi yapmaz.

**Bu yüzden:** A22 (kısa aks kuralı) doğrudan kullanılabilir — ölçüm
konvansiyonudur. A23/A24 (%20 eşikleri) **kullanılmıyor**; korpusta önceki
tetkikle sayısal karşılaştırma yapan cümle **çok az** (`prior` ekseni zaten
zayıf, K7 F1 %36,4). Kayıt için yazıldı, şemaya girmiyor.

---

## 4 · ACR Lung-RADS v2022 — 7 doğrulanmış kural

Kaynak: `data/raw/kilavuzlar/lung_rads_v2022.pdf`, Release Date Kasım 2022.

| # | kural | kaynak |
|---|---|---|
| **A25** | ⭐ **"Each exam should be coded 0-4 based on the nodule with the *highest degree of suspicion*."** | Note 1 |
| **A26** | ⭐ **Benign özellikler tanımlı ve DARDIR:** yalnız *"Complete, central, popcorn, or concentric ring calcifications"* **veya** *"Fat-containing"* nodül Kategori 1'e (Negatif) girer | Kategori 1 |
| **A27** | ⭐ **Enfeksiyöz/inflamatuvar süreç AYRI KANALA gider:** *"Findings suggestive of an inflammatory or infectious process"* → **Kategori 0** (Incomplete), şüphe düzeyi değil | Kategori 0 · Note 10 |
| **A28** | ⭐ **Yavaş büyüyen solid/part-solid nodül**, eşiği geçmese bile *"**is suspicious** and may be classified as Lung-RADS 4B"* | Note 8 |
| **A29** | **Büyüme tanımı:** ortalama çapta **> 1,5 mm** artış (**> 2 mm³**), **12 aylık** aralıkta | Note 6 |
| **A30** | **Ölçüm:** uzun ve kısa aks ölçülüp **ortalaması** alınır, 0,1 mm hassasiyetle | Note 4 |
| **A31** | **İkili eşleme emsali:** negatif tarama = Kategori **1-2**; pozitif tarama = Kategori **3-4** | Note 3 |

Ek olarak kayda geçirilen (şemaya girmiyor, §1 aktarım düzeyi notu): jukstaplevral
nodül < 10 mm + solid + düzgün kenar + oval/lentiform/üçgen → Kategori 2 (benign);
solid nodül boyut eşikleri < 6 / 6–8 / ≥ 8 / ≥ 15 mm.

---

## 5 · Fleischner Society 2017 — 4 doğrulanmış kural

Kaynak: `data/raw/kilavuzlar/fleischner_2017.pdf` · MacMahon et al.,
*Radiology* 2017;284(1):228.

| # | kural | kaynak |
|---|---|---|
| **A32** | ⭐ **Kapsam kılavuzun kendisi tarafından yazılı:** *"These guidelines **do not apply** to lung cancer screening, patients with immunosuppression, or patients with **known primary cancer**"* · *"do not apply to patients younger than 35 years"* · **"For lung cancer screening, adherence to the existing ACR Lung-RADS guidelines is recommended."** | Öneri tablosu notu · Implications for Patient Care |
| **A33** | *"Use **most suspicious nodule** as guide to management."* | Tablo A/B, çoklu nodül satırları |
| **A34** | ⭐ **Benign görünen konum tek başına benignlik göstermez:** perifissural/jukstaplevral nodüller genelde intrapulmoner lenf nodudur ve takip gerekmez, **ancak** *"perifissural or juxtapleural location **does not in itself reliably indicate benignancy**, and the specific nodule morphology must be considered. A **spiculated border**, displacement of the adjacent fissure, or a **history of cancer** increase the possibility of [malignancy]"* | Perifissural Nodules |
| **A35** | **Ölçüm:** *"Dimensions are average of long and short axes, rounded to the nearest millimeter."* Boyut eşikleri solid < 6 / 6–8 / > 8 mm; subsolid < 6 / ≥ 6 mm | Tablo A ve B dipnotları |

### 5.1 ⭐ A32 bir C kararını ORTADAN KALDIRDI

`docs/31` #19 *"kılavuzlar çatışırsa hangisi öncelikli"* diye soruyordu ve
varsayılan *"Fleischner > Lung-RADS, çünkü kohortumuz insidental"* idi.

**Soru yanlış kurulmuştu: iki kılavuz çatışmıyor.** Fleischner kendi kapsamını
yazılı olarak sınırlıyor ve tarama için **açıkça Lung-RADS'a yönlendiriyor**.
Kapsamlar **ayrık**.

| durum | geçerli kılavuz |
|---|---|
| insidental nodül, 35+ yaş, bağışıklığı normal, bilinen kanser yok | **Fleischner** |
| akciğer kanseri **taraması** | **Lung-RADS** (Fleischner böyle diyor) |
| **bilinen primer kanser** · bağışıklık baskılı · < 35 yaş | ⚠ **hiçbiri** — Fleischner dışlıyor, Lung-RADS tarama için |

**#19 düşürüldü.** Yerine bir **kapsam kuralı** geçti: şema, kılavuz seçmez;
kılavuzların kendi ilan ettiği kapsamı uygular. Üçüncü satır bu korpus için
gerçektir — karaciğer metastazlı vakalar gördük — ve **kılavuzsuz bölge olarak
kaydedilir.**

### 5.2 A26 + A34 birlikte #7'yi doğruluyor ve keskinleştiriyor

`docs/31` #7 *"kalsifikasyon tek başına benign göstergesi değildir"* diyordu ve
gerekçesi yalnız korpus örneğiydi. Şimdi iki kaynaklı:

- **A26:** benign kabul edilen kalsifikasyon **dar bir listedir** — *complete,
  central, popcorn, concentric ring*. Genel *"kalsifik"* ifadesi bu listede yok.
- **A34:** aynı ilke konum için de yazılı — benign görünen bir özellik
  (perifissural konum) *"tek başına benignliği güvenilir biçimde göstermez"*,
  **spiküle kenar** ve **kanser öyküsü** olasılığı artırır.

Korpus örneğimiz tam bu ilkeyi gösteriyordu: *"A **spiculated** contoured
**calcific** nodule causing … **retraction in the pleura**"*.

⚠ **Korpus sonucu:** TASK-10'da ölçülmüştü — `popcorn` **0**, `central` 26,
`laminated` 26, `concentric` yok. Yani **A26'nın benign listesi bu korpusta
pratikte yok**; `calcific*` ise 17.193 kez geçiyor. Sonuç: **korpustaki
"kalsifik" ifadelerinin ezici çoğunluğu A26'nın benign tanımını karşılamıyor**
ve benign sayılamaz. #7'nin varsayılanı bu ölçümle güçleniyor.

### 5.3 A25 + A33 #9'u doğruluyor

`docs/31` #9 (bulgu → rapor toplama kuralı) *"en yüksek şüphe kazanır"* diyordu
ve yapısal bir C kararıydı. **İki kılavuz da aynı kuralı yazılı olarak
kullanıyor** (A25, A33). C-1'den **A**'ya taşınır.

### 5.4 A27 #2'yi, A28 #15'i doğruluyor

- **A27:** Lung-RADS enfeksiyöz/inflamatuvar bulguyu **Kategori 0**'a — yani
  şüphe ölçeğinin **dışına** — koyuyor. `docs/31` #2'nin *"enfeksiyon belirsizliği
  malignite eksenine girmez"* varsayılanı **kaynaklı** hâle geldi.
- **A28:** *"yavaş büyüyen nodül suspicious"* — büyümenin şüphe yükselttiği
  yazılı. `docs/31` §4.1'de geri çekilen gerekçe **Lung-RADS Note 8 ile geri
  geliyor** (Fleischner'la değil). #15'in tavanı korunur: A28 şüphe yükseltir,
  **malignite ilan etmez**.

## 5 · Özet

| kaynak | kural |
|---|---:|
| Alan Sözlüğü §12.2 | **20** (A1–A20) |
| RECIST 1.1 | **4** (A21–A24; ikisi kapsam dışı) |
| ACR Lung-RADS v2022 | **7** (A25–A31) |
| Fleischner Society 2017 | **4** (A32–A35) |
| **Toplam doğrulanmış A kuralı** | **35** |

### C kaydına etkisi

| docs/31 maddesi | önce | sonra |
|---|---|---|
| #2 enfeksiyon ayrı eksen | C-1 | **A** (A27) |
| #7 kalsifikasyon tek başına benign değil | C-1 | **A** (A26 + A34), korpus ölçümüyle güçlendi |
| #9 en yüksek şüphe kazanır | C-1 | **A** (A25 + A33) |
| #15 büyüme şüpheyi yükseltir | C, dayanaksız | **A** (A28); tavan C olarak kalır |
| ~~#19~~ kılavuz önceliği | C-3 | **DÜŞÜRÜLDÜ** — çatışma yok (A32) |

**C kaydı 16 maddeden 11'e indi.** Dördü A'ya taşındı, biri düşürüldü.

**Aktarımın kapsadığı eksenler:** kesinlik (`present`/`absent`/`uncertain`),
zaman/değişim (`stable`/`new`/`increased`/`decreased`/`resolved`), teknik
çekince, aksiyon önerisi, lenf nodu ölçüm konvansiyonu.

**Aktarımın kapsamadığı eksen:** nodül boyut ve dansite eşikleri **kayda
geçirildi ama şemaya girmedi** — korpusta ölçü-nodül bağı bu düzeyde çözülmemiş
ve dansite sözlüğü zaten yok (`subsolid` 5, Fleischner üçlüsü yok).

**Kılavuzsuz bölge (A32):** bilinen primer kanserli, bağışıklığı baskılı ve
< 35 yaş hastalar için **hiçbir kılavuz geçerli değildir**. Bu korpusta böyle
vakalar vardır (karaciğer metastazı örnekleri). Şema bu bölgede yalnız C
varsayılanlarıyla çalışır ve bu **ilan edilir**.

⚠ **Bu 23 kural, malignite şüphe düzeyini üretmez.** Hepsi *cümleyi alan değerine
çevirme* kurallarıdır. *Alan değerlerini birbiriyle tartma* kuralı hiçbir
kaynakta yazılı değildir ve `docs/31`'in konusudur (docs/29 §1.1).

---

## 6 · B tipi ölçümler — A kurallarının korpustaki karşılığı

**Adım 3** · `scripts/43_task16_b_olcumleri.py` → `reports/task16_b_olcumleri.json`
Kapsam: geliştirme havuzu (383.644 cümle / 20.576 çalışma). Kilit okunmadı.

Kural (docs/29 §9-B.4): **korpusta karşılığı olmayan A kuralı şemaya girmez.**
Ölçüm yalnız kapsam belirler, klinik ağırlık vermez (§2.2/B).

### 6.1 ⭐ A26 — benign kalsifikasyon listesi bu korpusta YOK

| Lung-RADS'in benign saydığı patern | cümle | çalışma |
|---|---:|---:|
| popcorn | **0** | 0 |
| central calcification | 17 | 13 |
| concentric / laminated | 16 | 13 |
| complete calcification | 3 | 3 |
| **dördü toplam** | **~36** | — |
| | | |
| **genel "calcific"** | **13.862** | **7.156 (%34,8)** |

**Hüküm:** korpustaki kalsifikasyon ifadelerinin **%99,7'si** kılavuzun benign
tanımını karşılamıyor. `docs/31` #7 (*"kalsifikasyon tek başına benign göstergesi
değildir"*) bu korpusta yalnız doğru değil, **neredeyse istisnasız** doğrudur.

⚠ `fat-containing` 1.126 çıktı ama desen `fatty` içeriyor ve *"fatty liver"*
yakalıyor — **şişkin**, benign nodül göstergesi olarak kullanılamaz.

### 6.2 A34 — perifissural nodül kavramı korpusta yok

| | cümle | çalışma |
|---|---:|---:|
| perifissural | **6** | 5 |
| intrapulmonary lymph node | 122 | 69 |
| juxtapleural / subpleural | 5.198 | 3.715 (%18,1) |

Son satır **konum betimlemesidir** (*"subpleural area"*), Fleischner'ın kastettiği
morfolojik nodül tipi değil. **A34'ün spesifik kuralı uygulanamaz**; taşınan şey
yalnız **ilkesidir** (benign görünen özellik tek başına benignlik göstermez) ve o
ilke #7'de zaten kullanılıyor.

### 6.3 ⭐⭐ A32 — kılavuzsuz bölge korpusun DÖRTTE BİRİ

| Fleischner'ın dışladığı grup | çalışma | oran |
|---|---:|---:|
| **< 35 yaş** | **5.046** | **%24,53** |
| bilinen primer kanser (metinden) | 220 | %1,07 |
| bağışıklık baskılanması | 5 | %0,02 |

**Bu, planlarken tahmin edilenden çok büyük.** Fleischner *"do not apply to
patients younger than 35 years"* diyor ve korpusun **dörtte biri** bu grupta.
Lung-RADS ise tarama içindir, bu korpus tarama değildir.

**Sonuç:** korpusun yaklaşık **%25'inde hiçbir kılavuz geçerli değildir.** Şema
o bölgede yalnız C varsayılanlarıyla çalışır. **Bu, raporda ilan edilir** —
sonradan fark edilecek bir sınır değil, ölçülmüş ve kaydedilmiş bir sınırdır.

### 6.4 ⭐⭐ A28/A29 — büyüme ekseni korpusta YOK

Bu ölçüm **dördüncü ölçüm artefaktını** ortaya çıkardı ve en büyüğü:

| ölçüm | cümle | not |
|---|---:|---|
| geniş desen | 34.262 | %80 çalışma — kullanılamaz |
| ⤷ artefakt: *"density/thickness increase"* | 8.995 | bulgu betimlemesi |
| dar desen | 14.378 | hâlâ şişkin |
| ⤷ ⚠ artefakt: **`"enlarged lymph node"`** | **12.233** | **`enlarged` bu korpusta "büyümüş" değil "BÜYÜK" demek** — statik boyut, üstelik çoğu olumsuzlanmış (*"No enlarged lymph nodes were detected"*) |
| zamansal atıf (önceki tetkike gönderme) | 7.534 | |
| **gerçek büyüme = dar desen ∩ zamansal atıf** | **167** | **çalışmaların %0,64'ü** |
| yeni gelişen | 850 | %2,82 |

**Hüküm: büyüme ekseni bu korpusta yoktur.** 383.644 cümlede 167 gerçek büyüme
ifadesi var.

**Bunun üç sonucu var:**

1. **A28 ve A29 şemaya girmez** (docs/29 §9-B.4 kuralı). Lung-RADS'in büyüme
   tanımı (>1,5 mm / 12 ay) uygulanamaz — korpus bu bilgiyi taşımıyor.
2. **`docs/31` #15 ve #17 düşürülür** — ikisi de büyüme temelliydi.
3. Daha önce düşürülen ~~#3~~ ~~#14~~ ~~#18~~'in sebebi **geriye dönük olarak
   açıklanıyor**: hepsi büyüme temelliydi ve büyüme yoktu.

Bu, projenin bildiği bir olguyla tutarlıdır: **K7 (`prior` ekseni) F1 %36,4 ile
eşiği geçememişti** ve raporların %99,6'sında tarih yok. Korpus büyük ölçüde
**tek zamanlıdır**.

### 6.5 #4 — derece kelimeleri kullanılabilir

| derece ifadesi | cümle | çalışma |
|---|---:|---:|
| compatible / consistent with | 10.403 | 6.247 (%30,4) |
| **in favor of** (A8 → `present`) | 6.720 | 4.716 (%22,9) |
| may / probable / possible | 2.867 | 2.230 (%10,8) |
| suspicious (yalın) | 1.835 | 1.451 (%7,1) |
| cannot be excluded | 427 | 306 (%1,5) |
| high suspicion | 392 | 230 (%1,1) |

**#4'ün derece kuralı korpusta gerçek karşılık buluyor.** En büyük iki grup
(`compatible with`, `in favor of`) A7 ve A8 ile **`present`e** eşleniyor — yani
zaten A tipi.

### 6.6 A22 — kısa aks kuralı kullanılabilir

`short axis` **1.340 cümle / 1.202 çalışma (%5,8)** · `long axis` 125.
Lenf nodu ölçümü kısa akstan yapılıyor; A22 uygulanabilir.

### 6.7 Adım 3'ün özeti

| A kuralı | korpusta karşılığı | karar |
|---|---|---|
| A26 benign kalsifikasyon | ~36 cümle vs 13.862 genel | ✅ **kullanılır** — dışlayıcı olarak: kalsifikasyon benign yapmaz |
| A34 perifissural | 6 cümle | ⚠ **spesifik kural girmez**, ilkesi #7'de kullanılır |
| A32 kapsam | **%25 kılavuzsuz bölge** | ✅ **kullanılır** ve ilan edilir |
| A28/A29 büyüme | **167 cümle (%0,64)** | ❌ **ŞEMAYA GİRMEZ** |
| A22 kısa aks | 1.340 cümle | ✅ kullanılır |
| A7/A8 çıkarım ifadeleri | 17.123 cümle | ✅ kullanılır |
