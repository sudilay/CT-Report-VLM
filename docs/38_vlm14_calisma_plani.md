# SUDE-VLM-14 · Çalışma Planı (kod + değerlendirme)

**Görev:** Yapılandırılmış çıkarım motorunun Astra/NLST rapor kohortuna
uygulanması ve seri düzeyi yapılandırılmış tablonun üretilmesi.
**Kohort:** 2.965 seri / 1.201 PID · değerlendirmeye uygun 2.940 / 1.198
**Bölünme kilidi:** `astra-split-1.0`
**Plan sürümü:** v4 · 2026-09-08 · **GÖREV TAMAMLANDI**

---

## 0. Sürüm notu

v2, bağımsız incelemeye verildi ve **uygulamaya hazır bulunmadı**. İnceleme on
bir düzeltme istedi; dosya alıntılarının tamamı doğrulandı ve **tamamı kabul
edildi**. Ölçülebilir iki iddia yeniden ölçüldü; biri doğrulandı, biri
doğrulanmadı (§2 T8, T9).

| # | Düzeltme | v3'teki karşılığı |
|---|---|---|
| 1 | Lung-RADS'in yeni kohortu belirsiz; tanısal BT veya COVID kohortu yetmez, **tarama LDCT** gerekir | §6.1 — kohort adı verilmiyor |
| 2 | Şema dondurması VLM-11'in kapsamı, VLM-14'ün değil | §1 — dondurma çıkarıldı, yerine **aktarım denetimi** |
| 3 | Kör paket geçersiz; daraltılmış kural **yeni kör örneklem** ister | §6.2 — VLM-11'e devredildi |
| 4 | Dağılım çapası zaten türetilmiş ve **karar veremez** ilan edilmiş | §6.2 — "yeniden türet" adımı kaldırıldı |
| 5 | train → dev → tam kohort akışında eksik halka; 2.940 / 2.965 tutarsızlığı | §3 — akış yeniden yazıldı |
| 6 | Astra bölüm eşleme sözleşmesi yok | **Adım 0** — kod öncesi ilk teslim |
| 7 | Kolon sözleşmesi çoklu nodülü temsil edemiyor | §4 — iki tablo |
| 8 | "NPV'si yok" istatistiksel olarak yanlış ifade | §2 T4 — yeniden yazıldı |
| 9 | `%5 sözlük boşluğu` kapısının kaynağı yok | Adım 2 — kapı kaldırıldı, betimleyici |
| 10 | Held-out beyanı kendi içinde çelişkili | Adım 6 — "açılmadı" yerine "etiketle değerlendirilmedi" + kolon kısıtı |
| 11 | VLM-18 ve VLM-20 hâlâ Lung-RADS bekliyor | §6.3 |

Ayrıca inceleme, adım başına ayrı betik üretmeyi gereksiz buldu. Kabul edildi:
altı betik dörde indi, işin çoğu mevcut çıkarım modüllerinde yapılıyor.

---

## 1. Kapsam

**Bu görev:** dondurulmuş çıkarım motorunun Astra metnine **aktarılabilirliğini
denetler**, gerekiyorsa Astra'ya özgü adaptörü ayrı sürümle üretir ve seri
düzeyi yapılandırılmış tabloyu çıkarır.

**Önce yapılacak (Faz A, VLM-11 kapsamı):** şema dondurması. Karar
(2026-09-08): şema taslak bırakılmayacak, **düzgün biçimde dondurulacak**.
Yöntem ve gerekçesi §3.A'da.

**Bu görev değil:**

- Metrik, kalibrasyon, held-out değerlendirmesi → **VLM-23**
- Lung-RADS kategorisi → ayrı görev, tarama kohortu belirlendikten sonra (§6.1)
- Prompt revizyonu → **VLM-13** (§6.4)

**Kritik ayrım:** Şemanın kalan hedef uyumsuzlukları **CT-RATE kilitli sınır
takımına** aittir. Bunları Astra kapsam ölçümüyle çözmek metodolojik olarak
yanlıştır — gerçek rapor şemasını model üretimi metne uydurmak olur. Astra'ya
göre değişen her şey **ayrı sürümlü adaptörde** yaşar, şemanın kendisinde değil.

**Bağımlılık:** VLM-11 sürerken Adım 0–3 paralel yürür; bunlar dondurulmuş
şema gerektirmez. Yalnız Adım 4 (dondurma) ve sonrası VLM-11'in çıktısını bekler.

---

## 2. Tespitler

| # | Tespit | Durum |
|---|---|---|
| T1 | Nodül–ölçü aynı cümlede yalnız **37 raporda (%1,2)** bağlanabiliyor | ölçüldü |
| T2 | mm/cm geçen rapor **222**; güvenli teknik desenle temizlenince ölçüsü kalan **97 (%3,3)** | ⚠ ilk sayı (175 teknik / 91 temiz) **kusurluydu**: `mAs` deseni `mass` ile eşleşiyordu. Bağımsız ölçümle düzeltildi |
| **T12** | Astra **iki** başlık sözdizimi kullanır: `**Kalın:**` (2.869 rapor) ve Markdown `#` (900). Gerçekten başlıksız: **79 (%2,7)** | ilk sürüm `#` başlıklarını görmüyordu |
| T3 | `part-solid`/`subsolid` **%0,0** · `solid` %0,3 · spikülasyon %0,3 | ölçüldü |
| T4 | Astra'nın "nodül yok" dediği 672 raporda kanser oranı **%5,8**, kohort taban oranı **%4,7** | ölçüldü · §2.1 |
| T5 | Yer tutucu: köşeli parantez **%43,1** · `not visible` **%14,6** · `not given` %0 | ölçüldü, tek sayıya indirgenmez |
| T6 | Şemada zaten sıralı malignite ekseni var: `None/low/indeterminate/intermediate/high/known_malignancy` | `configs/degerlendirme_semasi.json` |
| T7 | Held-out, bölünmeden bir gün önce etiketlerle analiz edilmiş; bir eşik o analizde denenmiş | `bd9868b` (09-07) < `9fe6741` (09-08) |
| ~~T8~~ | ~~Raporların %56,6'sında akciğer dışı bölümde malignite sözcüğü var~~ | ⚠ **GERİ ALINDI** — genel kelime (`lesion\|nodule\|mass`) taramasıydı, şişik. Gerçek malignite terimleriyle → **T11** |
| **T11** | Akciğer dışı organ + olumsuzlanmamış malignite terimi, NLST `train`: **kanserlide 1/99 (%1,0)** · kansersizde 4/1.963 (%0,2) | ölçüldü · akciğer dışını elemenin maliyeti bu |
| **T10** | **Şema bölge-bağımsızdır:** sınır takımının 10/30 vakası akciğer dışı organ içerir; `C13-ekstratorasik` (472 kişilik aile) hedef gerekçesi **"ekstratorasik ELENMEZ"** | `data/processed/sema_sinir_vakalari.csv` (`takim-1.1`, SHA256 doğrulandı) |
| **T9** | `interval` 35 raporda geçiyor; **33'ü teknik, 0'ı klinik** (`no interval growth/change` hiç yok) | ölçüldü — teorik risk, bu korpusta gerçekleşmemiş |

**T10 + T11 birlikte okunur.** Şema bölge-bağımsızdır (T10) ve bu şemanın
kuralıdır — değiştirilmez. Ancak şemaya **hangi metni verdiğimiz** ayrı bir
karardır: NLST bir tarama kohortudur ve akciğer dışı malignite kanıtı kanserli
serilerin yalnız %1,0'inde vardır (T11).

**Karar (2026-09-08):** akciğer dışı organ bölümleri **girdi kapsamının
dışında.** Şemanın kuralına dokunulmaz; ona toraks metni verilir. Elenen kanıt
`qf_ekstratorasik_malignite_elendi` ile sayılır ve raporda beyan edilir.

⚠ Bu karar üç kez revize edildi (bastır → etiketle → kapsam dışı); üçü de
`docs/39` §3.3.1'de kayıtlı. İlk hâl şema kuralını çiğniyordu, ikincisi
ölçülmemiş bir maliyet varsayıyordu.

**T9**, incelemenin uyardığı `interval` sorununun bu korpusta gerçekleşmediğini
gösteriyor. Düzeltme yine de uygulanır (bağlamlı desen kullanılır) çünkü maliyeti
sıfır ve başka korpusta gerçekleşebilir — ancak **var olmayan bir sorun
düzeltilmiş gibi raporlanmaz**.

### 2.1 T4'ün doğru ifadesi

"NPV'si yok" **yanlış ifadedir** — sözlük anlamıyla NPV ≈ %94,2'dir. Doğru bulgu:

> Astra'nın negatif nodül beyanı, kanser riskini kohort taban oranına göre
> **azaltmamaktadır**; ayırt edici negatif kanıt sağlamamaktadır.

Bu analiz Adım 3'te **birincil olarak PID düzeyinde**, seri düzeyi ikincil olarak
ve **hasta-kümeli bootstrap güven aralığıyla** raporlanır. Aynı hastanın birden
fazla serisi bağımsız gözlem sayılamaz.

---

## 3. Adımlar

### Faz A · Şema dondurması ✅ **TAMAMLANDI** — `sema-1.0`

**Karar (2026-09-08):** şema `sema-0.9-taslak` olarak bırakılmayacak.

**Neden düz bir "çalışıp geçelim" mümkün değil.** Kabul ölçütü sonuç görülmeden
yazıldı ve hedef uyumu için **%100** diyor; mevcut sonuç **24/30**. Kalan altı
uyumsuzluğun dağılımı:

| Kaynak | Adet | Durum |
|---|---:|---|
| Girdi kalite filtresinin **bilinen etkisi** (`F1_gecmis_bulgu`, `F2_kanitsiz_present`) | 4 | Ancak ölçülmüş bir güvenlik kuralı gevşetilerek "çözülür" |
| Hedef atama yordamı ↔ motor yorum farkı | 1 | Karara bağlanabilir |
| Kavram listesi eksiği | 1 | Kapatılabilir |

O dört uyumsuzluğun kaynağı olan filtre kuralları keyfi değildir: zaman
ekseninin ölçülen F1'i **%36,4** ile eşiği geçemediği ve `temporality`
değerlerinin **%99,24'ü varsayılan** olduğu için konmuşlardır (D39,
`reports/task16_girdi_filtresi_olcum.json`). Bu kuralları gevşetip 30/30'a
çıkmak, **ölçülmüş bir hatayı sonuca taşımak** olur. Bu yol reddedilmiştir.

**Uygulanacak yol — ilan edilmiş protokol değişikliği.** Bağımsız denetim hükmü
bu durumu zaten tarif etmiştir (`configs/task17_dagilim_capasi.json`):

> *"Ön kayıt, GEÇERSİZ bir ölçütü uygulamaya devam etmeyi değil; sonradan
> yapılan düzeltmeyi açıkça 'PROTOKOL DEĞİŞİKLİĞİ' olarak kaydedip mevcut
> sonucu YENİDEN ADLANDIRMAMAYI gerektirir."*

Faz A çıktısı `docs/40_sema_dondurma_protokol_degisikligi.md`:

- **A1.** İki çözülebilir uyumsuzluk (kavram eksiği, yordam yorum farkı) tek tek
  karara bağlanır → beklenen 26/30.
- **A2.** Kalan dört uyumsuzluğun her biri için, hangi filtre kuralından
  geldiği ve neden gevşetilmediği tek tek yazılır.
- **A3.** `%100` eşiğinin neden ulaşılamaz olduğu ilan edilir. **24/30 veya
  26/30 sonucu "geçti" diye yeniden adlandırılmaz.** Yeni ölçüt, gerekçesiyle
  ve değişikliğin kendisi kayıt altına alınarak ilan edilir.
- **A4.** `known_malignancy` doğrulaması: mevcut kör paket **geçersizdir**.
  Daraltılmış dal yeni bir kural sürümüdür ve **yeni kör örneklem** ister; eski
  40 vaka yeniden puanlanamaz (`docs/37_task17_known_malignancy_kor_dogrulama.md`
  §3). Yeni tohum, yeni örneklem, bağımsız kör puanlama.
- **A5.** Dağılım kapısı: **çapa yeniden türetilmez** — türetildi ve estimand
  uyumsuzluğu nedeniyle *karar veremez* ilan edildi. Yerine yeni protokol:
  `high` için radyolojik şüphe doğrulaması, `known_malignancy` için ayrı metin
  doğrulaması; ikisi **tek prevalans kapısında birleştirilmez**.
- **A6.** `configs/degerlendirme_semasi.json` güncellenir (bayat kayıt: hedef
  uyumu 20/30 yazıyor, gerçek 24/30; sözlük önkoşulu kapandı).
- **A7.** `sema-1.0` dondurulur.

**Bağlayıcı kısıt:** Faz A **yalnız CT-RATE kilitli sınır takımı kanıtıyla**
yürütülür. Astra kapsam ölçümü Faz A'ya girdi olamaz — gerçek rapor şemasını
model üretimi metne uydurmak olur.

**Paralellik:** Adım 0–3 Faz A'yı beklemez; dondurulmuş şema gerektirmezler.
Yalnız Adım 4 ve sonrası `sema-1.0`'ı bekler.

---

### Adım 0 · Astra veri sözleşmesi ✅ (`docs/39` v4)

**Çıktı:** `docs/39_astra_veri_sozlesmesi.md`
**Bu belge onaylanmadan hiçbir motor Astra metni üzerinde koşturulmaz.**

Ölçülmüş bölüm envanteri (2.965 rapor, `**Başlık:**` deseni):

| Bölüm | Rapor | Bölüm | Rapor |
|---|---:|---|---:|
| conclusion | 2.049 | thyroid | 1.955 |
| pleura | 1.992 | abdomen | 1.954 |
| esophagus | 1.972 | bone | 1.954 |
| heart | 1.960 | trachea and bronchie | 1.940 |
| mediastinum | 1.959 | patient information | 1.348 |
| breast | 1.955 | recommendations | 978 |
| lung | 1.955 | note | 777 |
| | | prepared by | 701 |

Sözleşmede **karara bağlanacaklar:**

1. **Kapsam içi akciğer bölümleri:** `lung`, `left lung`, `right lung`, `pleura`,
   `trachea and bronchie`, `bronchi`, `trachea`, `abnormalities`
2. **`mediastinum` kapsam İÇİ, ayrı bayrakla** (karar 2026-09-08). Mediastinal
   lenf nodu akciğer kanserinin **N evrelemesidir**, gerçek kanıttır ve 1.959
   raporda geçer. Kapsam dışı bırakmak kanserli vakalarda kanıt kaybettirir.
   Her kanıt satırı `kaynak_bolum` taşır; mediastinumun katkısı sonradan
   ayrıştırılabilir ve T8 riski ölçülebilir kalır.
3. **Bölüm anlamı şemada kullanılmıyor — doğrulandı.** `sema.py` içinde hiçbir
   `section == 'impression'` mantığı yoktur; `section` yalnız cümle anahtarının
   parçasıdır (`sema.py:543`). Bu nedenle `conclusion`'ı `impression`'a eşleme
   zorunluluğu **yoktur**; bölüm kimliğinin kararlı olması yeterlidir.
   `scripts/04_segment_sentences.py`'nin `Findings_EN` / `Impressions_EN`
   bağımlılığı yalnız o **betiktedir**, kütüphanede değildir.
4. **Kapsam dışı organ bölümleri:** `breast`, `thyroid`, `abdomen`, `bone`,
   `esophagus`, `heart` → çıkarılır ama **silinmez, işaretlenir**. T8 gereği bu
   bölümlerdeki malignite sözcükleri **akciğer** malignite düzeyine asla
   yükselemez.
6. **Tamamen kapsam dışı meta:** `patient information`, `prepared by`,
   `report prepared by`, `date`, `note`, `important note`, `imaging details`,
   `imaging modality`, `imaging technique`
7. **`recommendations`** kapsam içi mi? Öneri metni bulgu değildir; varsayılan
   kapsam dışı, gerekçesiyle.
8. **Başlıksız metin** ve envanterde görünmeyen başlıklar nereye düşer.

**Giriş kolonu kısıtı (bağlayıcı):** çıkarım hattı kaynak dosyadan **yalnız**
`PID`, `Seri_Anahtari`, `Radyoloji_Raporu` kolonlarını okur.
`Kanser_Etiketi_y`, `Censor_Time`, `Pillar_Ensemble_Skoru` yalnız ayrı `train`
analiz betiğinde kullanılır. Çıktı şemasında bu alanların **bulunmadığı test
edilir**.

**Teknik satır deseni:** `slice thickness`, `reconstruction interval`,
`scan interval`, `kernel`, `kVp`, `mAs` — **bağlamlı desenler**. Çıplak
`interval` kullanılmaz (T9).

---

### Adım 1 · Astra adaptörü ve metin katmanı ✅

**Kod:** `src/radyovlm/extraction/astra.py` ·
`scripts/60_vlm14_astra_metin_katmani.py`
**Çıktı:** `data/processed/astra_sentences.parquet` (tüm 2.965 seri, `split`
etiketli)

Kolonlar: `seri_anahtari`, `pid`, `split`, `included_in_evaluation`,
`bolum_ham`, `bolum_eslenmis`, `kapsam_ici`, `cumle_idx`, `cumle_metni`,
`is_technical_param`, `has_placeholder`.

- Adaptör **salt okunur** ve Adım 0 sözleşmesini uygular.
- **D96 dersi:** cümle anahtarı `(seri_anahtari, bolum_ham, cumle_idx)` üçlüsü.
  Bölüm bilgisi olmadan `cumle_idx` kullanmak yasak.
- Dışlanan 25 seri de bölütlenir, `included_in_evaluation=false` alır.

**Test** (`tests/test_vlm14_astra.py`):
- Cümle anahtarı benzersiz; 2.965 seri, 0 kayıp.
- Sözleşmede tanımsız hiçbir başlık `kapsam_ici=true` alamaz.
- Teknik satır sayısı ≈ 175 rapor (T2).
- Kaynak dosyadan etiket kolonlarının okunmadığı kanıtlanır.

---

### Adım 2 · Aktarım denetimi ✅ — sözlük boşluğu **%0**

**Kod:** `scripts/61_vlm14_train_aktarim_denetimi.py`
**Çıktı:** `data/processed/astra_entities_train.parquet` ·
`reports/vlm14_aktarim_denetimi.json`

`train` (838 PID / 2.050 seri) üzerinde çıkarım koşturulur. **Amaç ölçüm.**

D56 dersi: sözlükler CT-RATE metninde geliştirildi, Astra'nın dağılımını hiç
görmedi. Ölçülecek: kapsanmayan yüzey oranı, Astra'ya özgü kalıplar, bölüm
bazında varlık yoğunluğu, kapsam içi/dışı bölüm karşılaştırması.

**Kapı yoktur.** v2'deki `%5` eşiği geri çekildi — TASK-17'de böyle genel bir
kabul eşiği tanımlanmadı; oradaki `%4,0 → %0,4` ölçümü sabit malignite bağlamlı
evrene özgüydü ve farklı paydalı oranlar birbirine taşınmaz. Bu koşumda kapsam
**betimleyici metrik** olarak raporlanır; adaptör düzeltmesi gerekiyorsa
gerekçesiyle yapılır ve sürümlenir.

**Test:** ölçüm yeniden üretilebilir; `dev` / `held-out` satırlarına
erişilmediği gerileme testiyle kanıtlanır.

---

### Adım 3 · Ölçülebilirlik envanteri (`train`)

**Kod:** `scripts/62_vlm14_olculebilirlik_envanteri.py`
**Çıktı:** `reports/vlm14_olculebilirlik_envanteri.json` + `.md`

Lung-RADS kolonu üretilmiyor. Bu adım **Astra raporlarının kılavuz uygulamaya ne
kadar elverdiğini ölçer** ve görev tanımı revizyonuna sayısal dayanak üretir.

**(a) Ölçü–lezyon bağı.** Üretim boyutu yalnız mevcut `measured_by` ilişkisinden
gelen **L1** (aynı cümle) ile sınırlıdır. Aynı bölüm / aynı rapor içindeki
ölçüler `boyut_mm` olarak **kullanılmaz**; yalnız denetim kaydı ve ortak-bulunma
istatistiği olarak raporlanır. Lung-RADS çıktığı için ayrı bir çok düzeyli
bağlama motoru **yazılmaz**.

**Zorunlu negatif kontrol (T2):** teknik parametre satırındaki bir ölçü hiçbir
lezyona bağlanmamalı. Bağlanırsa adım durur.

**(b) Kılavuz ekseni envanteri:** nodül tipi, büyüme ifadesi, lob, benign
kalsifikasyon paterni — her biri için kapsam oranı.

**(c) Negatif beyan analizi (T4).** §2.1'deki doğru ifadeyle: **PID düzeyi
birincil**, seri düzeyi ikincil, hasta-kümeli bootstrap güven aralığıyla.
Yer tutucu içeren/içermeyen ayrı ayrı. Etiket yalnız `train` PID'lerinde
kullanılır. **Bu bağımsız bir bulgudur** ve sonuç raporunda kendi bölümünü alır.

---

### Adım 4 · Adaptör ve kolon sözleşmesinin dondurulması ✅ — `astra-adaptor-1.0`

**Kod:** `src/radyovlm/evaluation/vlm14.py` (seri düzeyi toplama)
**Kilit:** `configs/astra_adaptor_kilidi.json` (`astra-adaptor-1.0`)

Adım 0–3 kanıtıyla adaptör, bölüm eşlemesi ve kolon sözleşmesi dondurulur.
Bu noktadan sonra `dev` ve tam kohort **aynı dondurulmuş kodla** koşar.

Şema sürümü VLM-11'den gelir. VLM-11 `sema-1.0`'ı dondurmamışsa
`sema-0.9-taslak` ile koşulur ve bu sınırlılık **çıktı tablosunun her
teslimatında ve raporun her tablosunda beyan edilir**.

---

### Adım 5 · `dev` doğrulaması ✅ (tek seferlik, kural değişmedi)

**Küme:** 180 PID / 450 seri
**Çıktı:** `reports/vlm14_kosum_gunlugu_dev.json` (koşum günlüğü; karşılaştırma sonuç raporunun ilgili bölümündedir)

Adaptör Adım 4'te **kilitlendikten sonra** `dev` bir kez açılır. `dev`'de görülen
sonuca göre adaptör değiştirilirse bu **açıkça kaydedilir** ve `dev` artık
doğrulama kümesi sayılmaz.

---

### Adım 6 · Tam koşum ✅ (**kör**)

**Kod:** `scripts/63_vlm14_tam_kosum.py`
**Çıktı:** `outputs/vlm14/astra_seri_duzeyi.parquet` ·
`outputs/vlm14/astra_kanit_duzeyi.parquet` + `.xlsx`

- 2.965 serinin tamamı işlenir; 25 seri `included_in_evaluation=false` alır.
- Held-out satırları için **özellikler kör biçimde üretilir**: etiketle
  birleştirilmez, metrik hesaplanmaz, sonuçlara göre kural değiştirilmez.
- Adım 0'daki giriş kolonu kısıtı burada da geçerli ve testlidir.
- Çalıştırma günlüğü: sürümler, tohum, sözlük ve şema sürümleri, adaptör kilidi.

**Beyan biçimi (bağlayıcı):** "held-out açılmadı" **denmez** — kolon üretildiği
için teknik olarak işlenmiştir. Doğru ifade:

> Held-out serileri için özellikler dondurulmuş motorla kör biçimde üretilmiştir;
> etiketle birleştirilmemiş, hiçbir metrik hesaplanmamış ve sonuçlara göre hiçbir
> kural değiştirilmemiştir. Etiketli değerlendirme VLM-23'e bırakılmıştır.

---

### Adım 7 · Sonuç raporu ✅

**Çıktı:** `reports/vlm14_sonuc_raporu.md` · AGENTS.md güncellemesi · tek commit

Ayrı bölüm olarak: aktarım denetimi (CT-RATE ↔ Astra sözlük farkı, D56 dersinin
tekrarı mı değil mi) · bölüm eşleme sözleşmesi ve T8 riskinin nasıl kapatıldığı ·
ölçülebilirlik envanteri · **negatif beyan analizi (T4)** · adaptör sürümü ve
şema sürümü beyanı · held-out kör üretim beyanı.

---

## 4. Kolon sözleşmesi — iki tablo

Tek tablo çoklu nodülü temsil edemiyor. İki tablo üretilir.

**A · Seri düzeyi özet** (`astra_seri_duzeyi.parquet`)

```
seri_anahtari                    str
pid                              str
split                            train|dev|holdout
included_in_evaluation           bool
nodul_var_mi                     true | false | not_assessable
loblar                           list[RUL|RML|RLL|LUL|LLL]
report_derived_malignancy_label  şema ekseni (T6) — YENİ EKSEN YOK
benign_evidence_present          bool
evidence_count                   int
measurement_available            bool
nodule_type_available            bool
qf_placeholder                   bool
qf_bolum_eksik                   bool
qf_ekstratorasik_malignite_elendi bool  (T11 · elenen kanıt sayılır)
qf_mediastinum_kaynakli          bool   (mediastinum katkısı ayrıştırılabilsin)
sema_surumu                      str
adaptor_surumu                   str
```

**B · Kanıt düzeyi uzun tablo** (`astra_kanit_duzeyi.parquet`)

```
kanit_id · seri_anahtari · kaynak_bolum · bolum_eslenmis · cumle_idx
varlik_id · normalized_concept · assertion · temporality
boyut_mm            float | null   (yalnız L1 measured_by ilişkisinden)
boyut_bag_duzeyi    L1 | denetim_kaydi
lob                 str | null
kanit_metni         str
```

**Bağlayıcı kısıtlar:**

- **Sürekli olasılık üretilmez.** Kural motoru kategorik kanıt üretir; tek
  olasılık üreten yer VLM-20'nin lojistik regresyonudur. Etiketlere fit edilmiş
  bir skoru aynı veriye fit edilecek modele özellik olarak vermek hedef
  sızıntısıdır (toplam 72 pozitif PID, `train`'de 50).
- `boyut_mm` teknik parametre satırından **asla** alınmaz (T2), L2/L3/L4'ten
  alınmaz (Adım 3a).
- Şemanın **kuralı** değiştirilmez (T10). Akciğer dışı organ bölümleri **girdi
  kapsamı** kararıyla elenir (T11) ve elenen kanıt sayılır — sessiz kayıp yok.
- `report_derived_malignancy_label` adı korunur — rapordan çıkarılan sınıf hasta
  sonucu değildir (AGENTS §4 Adlandırma).
- `nodul_var_mi` üç değerlidir; `not_assessable` ≠ `false`.

---

## 5. Kapanış ölçütü ve yapılmayacaklar

**Kapanış:**

1. `sema-1.0` donduruldu ve `docs/40_sema_dondurma_protokol_degisikligi.md`
   yazıldı (Faz A).
2. `docs/39_astra_veri_sozlesmesi.md` yazıldı ve onaylandı (Adım 0).
3. `astra-adaptor-1.0` donduruldu (Adım 4).
4. İki tablo `outputs/vlm14/` altında üretildi (Adım 6).
5. Ölçülebilirlik envanteri ve negatif beyan analizi raporlandı (Adım 3).
6. Gerileme testleri geçiyor; `reports/vlm14_sonuc_raporu.md` yazıldı.
7. Held-out etiketle değerlendirilmedi.

**Yapılmayacaklar:**

- `lung_rads_*` kolonları üretilmeyecek.
- Şema Astra kanıtıyla dondurulmayacak — Faz A yalnız CT-RATE kanıtı kullanır.
- Şemanın klinik anlamı Astra metnine göre değiştirilmeyecek; Astra'ya özgü her
  şey ayrı sürümlü adaptörde yaşayacak.
- Yeni sıralı şüphe ekseni icat edilmeyecek (T6).
- Sürekli malignite olasılığı üretilmeyecek — o VLM-20'nin işi.
- Held-out etiketle birleştirilmeyecek.
- Çok düzeyli ölçü bağlama motoru yazılmayacak.

---

## 6. Devredilen işler ve zincir güncellemeleri

### 6.1 Lung-RADS değerlendirmesi → ayrı görev
Karar (2026-09-08): Lung-RADS değerlendirmesi **gerçek hekim raporları**
üzerinden yapılacak; görev tanımı revize edilecektir. Astra çıktıları üzerinde
uygulanamayacağı ölçüldü (T1–T3); Adım 3 envanteri bu revizyonun dayanağıdır.

**Kohort adı verilmiyor.** ACR, Lung-RADS'i akciğer kanseri **tarama** sistemi
olarak tanımlar. Aday kohortun gerçek hekim raporu olması yetmez; **tarama LDCT**
incelemesine ait olması ve nodül tipi, ölçüm ve takip alanlarını taşıması
gerekir. Tanısal BT veya pnömoni/COVID ağırlıklı bir kohort bu şartı sağlamaz.
Hedef kohort, tarama bağlamı ve gerekli alanların varlığı **doğrulanmadan
seçilmeyecektir.**

### 6.2 Şema dondurması → **Faz A'da yapılıyor** (VLM-11 kapsamı)
Karar 2026-09-08: taslak bırakılmıyor, dondurulacak. Yöntem §3.A'da.
Kalan uyumsuzluklar CT-RATE kilitli sınır takımına aittir; Astra kanıtıyla
çözülemez. Faz A'nın kalemleri:

- Altı sınır vakasının tek tek karara bağlanması.
- `known_malignancy` doğrulaması: **mevcut kör paket geçersizdir.** Daraltılmış
  dal yeni bir kural sürümüdür ve **yeni kör örneklem** ister; eski 40 vaka
  yeniden puanlanamaz (`docs/37_task17_known_malignancy_kor_dogrulama.md` §3).
- Dağılım kapısı: **çapa yeniden türetilmeyecek** — zaten türetildi ve estimand
  uyumsuzluğu nedeniyle *karar veremez* ilan edildi
  (`configs/task17_dagilim_capasi.json`). Gereken **yeni protokol**: `high` için
  radyolojik şüphe doğrulaması ve `known_malignancy` için ayrı metin
  doğrulaması, bu ikisini tek prevalans kapısında **birleştirmeden**.
- `configs/degerlendirme_semasi.json` bayat kaydının güncellenmesi (hedef uyumu
  20/30 yazıyor, gerçek 24/30; sözlük önkoşulu kapandı).

### 6.3 Zincir güncellemeleri → SUDE-VLM-18 ve SUDE-VLM-20
Lung-RADS yalnız VLM-14'ten çıkarılırsa zincir tutarsız kalır:

- **VLM-18** kanıt birleştirmede Astra Lung-RADS şüphe skoru bekliyor.
- **VLM-20** lojistik regresyon girdisi olarak Astra Lung-RADS bekliyor.

İkisinin de girdisi şu olarak güncellenmeli: `report_derived_malignancy_label`
(one-hot), `boyut_mm`, `benign_evidence_present`, `evidence_count` ve eksiklik
bayrakları. Sınıfları lojistik regresyona düz sayı olarak vermek, düzeyler arası
uzaklığın eşit olduğunu varsayar; bu gösterilmemiştir.

### 6.4 Prompt pilotu → SUDE-VLM-13
`train` içinden tabakalı 30–50 seri; mevcut ve yeni prompt aynı görüntülerde
koşulur; üretilen ölçüler NLST lezyon anotasyonuyla karşılaştırılır; **kapsam
artışı kadar yanlış ve uydurma ölçü oranı da raporlanır.** Yeni prompt ancak
doğruluk bozulmadan kapsamı artırıyorsa genişletilir. Hesaplama maliyeti sunucu
tarafıyla ayrıca belirlenecektir.

---

## 7. Açık riskler

| Risk | Etki | Kontrol |
|---|---|---|
| **T11** — akciğer dışı kapsam kararı 1 kanserli seride kanıt eliyor | 99 train pozitifinin 1'i | `qf_ekstratorasik_malignite_elendi` sayılır ve sonuç raporunda beyan edilir |
| Faz A'da `%100` eşiği ulaşılamaz çıkarsa | Dondurma protokol değişikliği ile yapılır | A3: değişiklik ilan edilir, sonuç yeniden adlandırılmaz |
| **T7** — held-out maruziyeti | Dış geçerlilik iddiası zayıflar | Bu görevde etiketle değerlendirilmez; karar VLM-23'te · **AGENTS.md'ye karar olarak düşülmeli** |
| Kohortun pozitif seri sayısı artırılabilir | `astra-split-1.0` yeniden üretilir | VLM-12 "tamamlandı" durumunda bekliyor; kohort değişirse bölünme ve bu görevin çıktısı yeniden koşulur |
