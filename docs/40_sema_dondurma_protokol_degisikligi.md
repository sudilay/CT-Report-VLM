# Şema Dondurma · Kalan Uyumsuzlukların Gerekçelendirilmesi ve Protokol Değişikliği

**Faz A · A2 · A4 · A5 tamamlandı · A3 aşağıda ilan edildi**
**Tarih:** 2026-09-08 · **Şema:** `sema-0.9-taslak` → hedef `sema-1.0`
**Kapsam:** yalnız CT-RATE kilitli sınır takımı. Astra kanıtı bu belgeye girmez.

---

## 1. Amaç

Şema iki kez sınandı ve iki kez dondurulmadı. Bu belge, **dondurulamama
nedenlerinin her birini tek tek karara bağlar** ve kabul ölçütünün neden
mevcut hâliyle sağlanamayacağını gösterir.

Bu belge bir mazeret değil, bir **kayıttır**. Bağımsız denetimin hükmü
(`configs/task17_dagilim_capasi.json`) yolu şöyle tarif etmiştir:

> *"Ön kayıt, GEÇERSİZ bir ölçütü uygulamaya devam etmeyi değil; sonradan
> yapılan düzeltmeyi açıkça **'PROTOKOL DEĞİŞİKLİĞİ'** olarak kaydedip mevcut
> sonucu **YENİDEN ADLANDIRMAMAYI** gerektirir."*

Buna uyulur: **24/30 sonucu "geçti" diye yeniden adlandırılmaz.**

---

## 2. Mevcut durum

| Kapı | Eşik | Sonuç | Geçti mi |
|---|---|---|---|
| Hedef uyumu (sınır takımı) | %100 | **24/30** | ❌ |
| Yanlış pozitif koruma kapısı | toleranssız, 0 malignite | **0 ihlal / 23** | ✅ |
| Dağılım kapısı | %0,5–3,0 | %0,049 | ⚠ **karar veremez** ilan edildi |

Dağılım kapısı hakkında yeni bir iş yapılmayacaktır: çapa zaten türetilmiş ve
estimand uyumsuzluğu nedeniyle geçersiz bulunmuştur. Yerine gelecek protokol
A5'in konusudur.

---

## 3. Altı uyumsuzluğun tek tek karara bağlanması

### 3.1 · C12-benign-belirsiz-03 — **KALICI** · iki kabul ölçütü çelişiyor

```
cümle : "In the posterobasal segment of the lower lobe of the right lung,
         a 5.5 mm diameter nodule developed on the subpleural possible
         sequelae is observed."
hedef : low          motor: not_mentioned
```

Şemanın kendi ilan edilmiş sınırı:

> *"`low` düzeyi PRATİKTE ÜRETİLEMİYOR. `low` üretmek **denendi ve GERİ
> ALINDI**: `low` malignite üreten sınıflardandır, **koruma kapısını kırıyor**
> ve şablon negatifler `low`a kayıyordu."*

Sınır takımında `low` hedefli **tek** vaka budur (hedef dağılımı:
`intermediate` 6 · `indeterminate` 6 · `None` 5 · `known_malignancy` 5 ·
`not_mentioned` 4 · `high` 3 · **`low` 1**).

**Karar:** kapatılamaz. Kapatmak için `low` üretilmesi gerekir; `low` üretmek
şu an geçen **tek** kapıyı (yanlış pozitif koruması) kırar.

> **Hüküm:** Bu bir başarısızlık değil, **kabul ölçütünün kendi içinde
> tutarsız** olduğunun kanıtıdır. Hedef uyumu kapısı ile koruma kapısı bu vaka
> üzerinde aynı anda sağlanamaz. A3'ün birincil gerekçesi budur.

### 3.2 · C5-stabil-malignite-02 · 3.3 · C5-stabil-malignite-03 · 3.4 · C13-ekstratorasik-01 — **KALICI** · ölçülmüş bozuk eksen

```
C5-02  "According to the previous examination, hypodense lesions were
        observed in the liver..."            hedef high              → not_mentioned
C5-03  "There was no significant change in the dimensions of metastatic
        masses observed in T1 and L1 vertebrae."  hedef known_malignancy → not_mentioned
C13-01 "the disease is progressive due to newly emerged metastases in
        the liver and spleen."               hedef known_malignancy → not_mentioned
```

Şemanın kendi ilan edilmiş sınırı:

> *"Stabil takipteki bilinen kanser görünmüyor. Cümlede 'previous examination'
> geçtiğinde varlığa `prior` atanıyor, F1 doğru şekilde susturuyor. **Filtre
> çalışıyor, GİRDİSİ yanlış (K7 F1 %36,4).** Kanıt: C5-stabil-malignite
> ailesinin üçü de kayboluyor."*

Ölçülen değerler (`reports/task16_girdi_filtresi_olcum.json`):

| | |
|---|---:|
| Zaman ekseni F1 (K7) | **%36,4** — kendi eşiğini geçemedi |
| `temporality` değerlerinin varsayılan oranı | **%99,24** |
| `F1_gecmis_bulgu` ile düşük güvene düşen varlık | 4.746 |

Filtre kuralının gerekçesi kayıtlıdır: *"Geçmiş bir bulgunun rapor sınıfını
yükseltmesi, ölçülmüş bir hatanın sonuca taşınması olurdu."*

**Karar:** kapatılamaz. Kapatmak için `F1_gecmis_bulgu` kuralının gevşetilmesi
gerekir; bu, F1'i %36,4 ölçülmüş bir ekseni karar ağırlığı taşır hâle getirmek
demektir.

> **Hüküm:** Kural gevşetilmeyecektir. Bu üç uyumsuzluk, zaman ekseninin
> ölçüm kalitesi düzelmediği sürece kalıcıdır ve şemanın kusuru değil,
> **çıkarım katmanının ölçülmüş sınırıdır.**

### 3.5 · C11-olumsuz-belirsiz-02 — **KALICI** · ölçülerek karara bağlandı

```
cümle : "Since contrast material was not given, it is not possible to comment
         on the size and number of lesions in the liver."
hedef : indeterminate     motor: not_mentioned
```

**Kök neden bulundu.** Motor cümle üzerinde koşturuldu: `lesion` ve `liver`
varlıkları **çıkarılıyor**, sorun çıkarımda değil. `MALIGNITE_KAVRAMLARI`
envanterinde (22 kavram) `lytic_destructive_lesion` ve `space_occupying_lesion`
var, ama **çıplak `lesion` yok**.

İlk bakışta tek kelimelik bir eksik gibi görünüyordu ve koruma kapısını da
kırmıyordu (`lesion` 23 negatif kontrolün **0**'ında geçiyor). Bu nedenle
korpus geneline bakıldı.

**Ölçüm** (`scripts/64_fazA_lesion_dagilim_olcumu.py` →
`reports/fazA_lesion_dagilim_olcumu.json`) · geliştirme havuzu 20.576 çalışma,
971.783 varlık, **değerlendirme kilidi okunmadı**:

| | Değer |
|---|---:|
| `lesion` varlık satırı | 10.224 |
| Geçtiği çalışma | 5.949 |
| **Sınıfı değişen çalışma** | **2.413 (%11,7)** |
| `None` → `intermediate` | 2.042 |
| `not_mentioned` → `intermediate` | 252 |
| `indeterminate` → `intermediate` | 71 |

**Karar:** `lesion` envantere **eklenmeyecektir.** Tek bir sınır vakasını
kurtarmak için korpusun %11,7'sinin sınıfını kaydırmak — üstelik büyük
çoğunluğunu temizden şüpheliye çekerek — orantısızdır.

> **Hüküm:** Kalıcı. Bu karar, koruma kapısının 23 vakalık kontrol kümesinin
> **tek başına yeterli kanıt olmadığını** da göstermiştir: kapı kırılmıyordu
> ama dağılım ciddi biçimde kayıyordu.

### 3.6 · C5-stabil-malignite-01 — **KALICI** · çıpa deseni tetiklemiyor

```
cümle : "Stable soft tissue density thought to belong to regressed primary
         malignancy in the left upper lobe"
hedef : known_malignancy     motor: intermediate
```

`malignancy` varlığı **çıkarılıyor** ve envanterde **var**. Motor sınıf
üretiyor, ama bir basamak aşağıda. Bu bir sözlük veya kod hatası değildir.

Fark tanımdadır: `known_malignancy` tetikleyicisi raporda *yazılı,
belgelenmiş* kanser öyküsü arar. *"thought to belong to regressed primary
malignancy"* ifadesini hedef atayan taraf belgelenmiş saymış, motor şüphe
saymıştır.

**Kural üzerinde sınandı.** `_bilinen_kanser` bu cümlede tetiklenmiyor:

| | |
|---|---|
| `KANSER_TERIMI_METIN` eşleşti | ✅ (`malignancy`) |
| **`KANSER_OYKUSU_CIPASI` eşleşti** | ❌ |
| Tetikledi mi | **Hayır** |

Çıpa deseni `known` · `followed up for/due to` · `in the follow-up` ·
`operated for/due to` · `history of` · `diagnosed with/as` arıyor.
*"thought to belong to regressed primary malignancy"* bunların hiçbirini
taşımıyor.

Tetiklemesi için **çıpanın genişletilmesi** gerekir. Ama D97 bu dalı yeni
daralttı ve gerekçesi ölçülmüştü: kör yargıda çıkan **dört yanlış pozitifin
dördü de** `due to + malignan*` dalındandı (*"due to malignant infiltration"*,
*"may be due to malignancies"*) — radyolojik nedensellik, belgelenmiş öykü değil.

**Karar:** kapatılamaz. Genişletmek, ölçülerek daraltılmış bir deseni geri açmak
olur.

> **Hüküm:** Kalıcı. A4'ün kör puanlaması **bu vakayı çözmez** — A4 farklı bir
> soruyu yanıtlar: tetikleyicinin ürettiği `known_malignancy` etiketleri doğru mu
> (kesinlik ≥ %85), yani **kural ayakta kalıyor mu**.

---

## 4. Özet

| Vaka | Hedef | Motor | Kök neden | Hüküm |
|---|---|---|---|---|
| C12-benign-belirsiz-03 | `low` | `not_mentioned` | `low` üretilemiyor; koruma kapısını kırıyor | 🔴 **kalıcı** — ölçütler çelişiyor |
| C5-stabil-malignite-02 | `high` | `not_mentioned` | `F1_gecmis_bulgu`, K7 F1 %36,4 | 🔴 **kalıcı** |
| C5-stabil-malignite-03 | `known_malignancy` | `not_mentioned` | aynı | 🔴 **kalıcı** |
| C13-ekstratorasik-01 | `known_malignancy` | `not_mentioned` | aynı | 🔴 **kalıcı** |
| C11-olumsuz-belirsiz-02 | `indeterminate` | `not_mentioned` | `lesion` envanterde yok; eklemek %11,7 kaydırıyor | 🔴 **kalıcı** — ölçüldü |
| C5-stabil-malignite-01 | `known_malignancy` | `intermediate` | çıpa deseni tetiklemiyor; genişletmek D97'yi geri alır | 🔴 **kalıcı** |

**Altı uyumsuzluğun altısı da kalıcıdır. Ulaşılabilir tavan: 24/30 (%80,0).**
Eşik %100'dür.

⚠ Bu satır ilk sürümde "25/30, C5-01 A4'e bağlı" diyordu. Kural cümle üzerinde
sınanınca C5-01'in de kalıcı olduğu görüldü ve düzeltildi.

---

## 4.1 · A4 sonucu — `known_malignancy` kör metin puanlaması

**Kaynak:** `reports/km_kor_v2_yargi.md` · paket
`outputs/task17/km_kor_v2/KOR_known_malignancy_v2.csv` (SHA-256 doğrulandı)
· protokol `docs/37` · iş emri `docs/42`

| Yargı | Sayı |
|---|---:|
| `E` | 32 |
| `H` | 4 |
| `?` | 4 |

| Ölçüm | Sonuç |
|---|---:|
| **Protokol kesinliği** `E/(E+H)` | **%88,9** |
| Duyarlılık kontrolü `E/40` (`?`=`H`) | %80,0 |
| %95 Clopper-Pearson aralığı | **%73,9 – %96,9** |

**Kapı sonucu: GEÇTİ.** Nokta tahmin önceden ilan edilen %85 eşiğinin
üzerindedir. `known_malignancy` basamağı **ayakta kalır** — yalnız *"raporda
yazılı kanser öyküsünü yakalama"* ekseninde; klinik doğruluk iddiası yoktur.

### 4.1.1 · Üç ilan edilmiş sınır

**1. Güç yetersizliği.** Güven aralığının alt sınırı (%73,9) eşiğin
altındadır: örneklem, gerçek kesinliğin %85 üzerinde olduğunu **istatistiksel
olarak göstermemektedir.** n=40 ile %88,9'luk bir nokta tahmin bunu
gösteremez — bu, protokolün **tasarım sınırıdır**, sonucun kusuru değil.
Eşik sonuç görüldükten sonra değiştirilmez.

**2. Ön maruziyet.** Yargıç, iş emrinin okumaya izin verdiği `docs/37`'nin
denetim ekinde v1 turunun yargı sayılarını (32/4/4) ve örüntüsünü görmüştür
ve bunu kendisi beyan etmiştir. v2 sonucu **birebir aynı dağılımı** (32/4/4)
vermiştir.

⚠ Bu bir çakışma olarak kaydedilir. Buna karşılık **içerik farklıdır**:
v1'in dört `H` vakası tümüyle `due to + malignan*` dalındandı; v2'nin dört
`H` vakası `evaluated in favor of`, `may be compatible with`, `thought to be
due to` kalıplarındandır. Yani D97 daraltması eski yanlış pozitif kaynağını
**gerçekten kapatmış**, yerine başka kalıplar görünür olmuştur. Vaka
kimlikleri de tümüyle farklıdır. Sonuç bu gerekçeyle kabul edilir, maruziyet
gizlenmez.

**3. Duyarlılık ölçülmemiştir.** Örneklem yalnız kuralın **tetiklendiği**
vakalardan çekilmiştir; kaçırılanlar ayrı bir örneklem ister.

### 4.1.2 · Devredilen bulgular — **şimdi uygulanmayacak**

Protokol açıktır: *"hatalı bulunan vakalar incelenip desen daraltılırsa bu
YENİ BİR SÜRÜMDÜR ve bu doğrulama GEÇERSİZ sayılır, yeni örneklem çekilir."*
Bu nedenle aşağıdakiler **kayda geçirilir, uygulanmaz**:

| # | Bulgu | Kanıt |
|---|---|---|
| **B1** | `tumor` kavramı malignite envanterinde, ama *"kidney tumor"* / *"breast tumor"* / *"lung tumor"* malign olduğunu söylemez | `?` yanıtlarının **dördü de** çıplak `tumor` |
| **B2** | Çıpa ve kanser terimi **aynı cümlede herhangi bir yerde** olunca tetikleniyor; terim hedge'li çıkarım dilinde geçse bile | `H` yanıtlarının dördü: `evaluated in favor of`, `may be compatible with`, `thought to be due to` |

B2, C5-01 ile aynı dil ailesidir (*"thought to belong to regressed primary
malignancy"*) — ama orada çıpa hiç eşleşmediği için tetiklenmiyor. Yani kural
bu aileye **tutarsız** davranmaktadır: çıpa varsa tetikliyor, yoksa
tetiklemiyor; oysa dil aynı. Bu, gelecek bir sürümün konusudur.

---

## 4.2 · A5 sonucu — dağılım kapısının ayrıştırılması

**Kaynak:** `scripts/65_fazA_dagilim_ayrik_olcum.py` →
`reports/fazA_dagilim_ayrik_olcum.json` · geliştirme havuzu 20.570 çalışma,
değerlendirme kilidi okunmadı.

Birleşik kapı (`malignite_pozitif` = `high` ∪ `known_malignancy`) estimand
uyumsuzluğu nedeniyle **karar veremez** ilan edilmişti. Kayıtlı gelecek
protokol (`configs/task17_dagilim_capasi.json` → `gelecek_protokol`) ayrımı
zaten tarif etmişti:

> `high` : radyolojik yüksek şüphe — **derece dili çapası UYGULANABİLİR**
> `known_malignancy` : raporda yazılı kanser öyküsü — **AYRI doğrulama ister**

`known_malignancy` ayrı doğrulaması **A4'te yapıldı** (§4.1, kesinlik %88,9).
Bu bölüm `high` basamağını ayrı ölçer.

| Basamak | Çalışma | Oran |
|---|---:|---:|
| **`high`** | 13 | **%0,0632** |
| `known_malignancy` | 156 | %0,7584 |
| *(eski birleşik estimand)* | 169 | %0,8216 |

**Önceden dondurulmuş aralık: [%0,0336 – %0,108] → `high` ARALIK İÇİNDE.**

### 4.2.1 · Bu neden "sonuca bakıp ölçüt seçmek" değil

Kapının **kendi türeyiş metni** `high`-only varsayıyordu:

> *"Motor `known_malignancy` ÜRETMEZ (docs/33 §4.1, ilan edilmiş sınır), yani
> `malignite_pozitif` pratikte YALNIZ `high`'tır."* — `scripts/49` satır 59-61

D92 tam olarak bu varsayımı kırdı (`known_malignancy` 0 → 156). Yani geçersiz
olan **aralık değil, kapının öncülüydü**. `high`-only değerlendirme kapıyı
**orijinal tasarımına döndürür**; yeni bir ölçüt seçmez. Aralık ve çapa
desenleri koşumdan önce dondurulmuştu ve **değiştirilmemiştir**.

### 4.2.2 · İlan edilen sınırlar

1. **Kapı düşük güçlüdür** (kendi kaydı): *"Çapa tabanı 13 çalışmadır; Poisson
   örneklem hatası ±3,6 (%28 bağıl). Kapı yalnız KABA DEJENERASYONU
   yakalayabilir... KAPININ GEÇİLMESİ, ŞEMANIN DAĞILIMININ DOĞRU OLDUĞUNUN
   KANITI DEĞİLDİR."*
2. **Post-hoc zamanlama:** bu ölçüm, birleşik kapı koşulduktan sonra
   yapılmıştır. Aralık önceden dondurulmuştu, ama zamanlama ilan edilir.
3. **Birleşik kapının mevcut kaydı değiştirilmez** — "geçti" diye yeniden
   adlandırılmaz. Ayrık ölçüm **yeni bir kayıttır**, eskisinin yerine geçmez.

---

## 5. A3 · **PROTOKOL DEĞİŞİKLİĞİ — İLAN**

⛔ Bu bölüm bağlayıcıdır. Yazıldıktan sonra §3 ve §4'teki hükümler
değiştirilmez.

### 5.1 · Değişen ölçüt

**Eski (koşumdan önce yazılmıştı):**

> Hedef uyumu (kilitli sınır takımı) = **%100**

**Bu ölçüt sağlanamaz.** Gerekçe bir başarısızlık değil, **ölçütün
varsayımının yanlış olmasıdır**: ölçüt, her uyumsuzluğun düzeltilebilir
olduğunu varsayıyordu. §3'te altı uyumsuzluğun **altısının da yapısal olarak
kapatılamaz** olduğu tek tek gösterilmiştir.

**Yeni ölçüt (yapısal, sayıya bağlı değil):**

> Kilitli sınır takımındaki **her** uyumsuzluk için:
> 1. Kök neden **belgelenmiş** olmalıdır,
> 2. Kök neden **şema kaynaklı olmamalıdır**,
> 3. Kapatılmama gerekçesi ya **ölçülmüş** ya da şemanın **ilan edilmiş bir
>    sınırına** dayanmalıdır.
>
> Bu üç şart altı uyumsuzluğun **altısında da** sağlanmaktadır (§4 özet
> tablosu).

**Neden sayısal eşik yerine yapısal ölçüt:** mevcut sonuca (24/30 = %80,0)
eşit bir sayı seçmek, sonuca bakıp ölçüt belirlemek olurdu. Yapısal ölçüt
sayıdan bağımsızdır ve denetlenebilir: her uyumsuzluğun gerekçesi §3'te
kaynağıyla yazılıdır.

### 5.2 · Değişmeyen her şey

- **24/30 sonucu "geçti" diye YENİDEN ADLANDIRILMAZ.** Şemanın hedef uyumu
  24/30'dur ve her yayında bu sayıyla raporlanır.
- Yanlış pozitif koruma kapısı **gevşetilmez** — toleranssız, 0 ihlal / 23.
- Girdi kalite filtresinin `F1`/`F2` kuralları **gevşetilmez**.
- Birleşik dağılım kapısının mevcut kaydı **değiştirilmez** (§4.2.2).
- `known_malignancy` kör doğrulamasının %85 eşiği **değiştirilmez** (§4.1).

### 5.3 · Kabul ölçütü setinin iki yapısal sınırı — ilan edilir

**Sınır 1 — İki kabul ölçütü C12 üzerinde birbirini dışlar** (§3.1). Hedef
uyumu kapısını geçmek `low` üretmeyi gerektirir; `low` üretmek koruma kapısını
kırar. Ölçüt seti bu vaka üzerinde **kendi içinde tutarsızdır**.

**Sınır 2 — Kör doğrulama güç yetersizdir** (§4.1.1). n=40 ile %88,9'luk bir
nokta tahmin, gerçek kesinliğin %85 üzerinde olduğunu gösteremez
(%95 GA %73,9–%96,9). Kapı nokta tahminle geçer, **istatistiksel olarak
gösterilmiş değildir.**

Bu iki sınır, `sema-1.0`'ı kullanan her çalışmada beyan edilir.

### 5.4 · Dondurma hükmü

Yukarıdaki yeni ölçüt ve üç kapının durumu:

| Kapı | Durum |
|---|---|
| Hedef uyumu (yapısal ölçüt, §5.1) | ✅ altı uyumsuzluğun altısı da gerekçeli |
| Yanlış pozitif koruması | ✅ 0 ihlal / 23, toleranssız |
| `known_malignancy` kör doğrulaması (A4) | ✅ %88,9 ≥ %85 · güç sınırı ilan edildi |
| Dağılım — `high` ayrık (A5) | ✅ %0,0632 ∈ [%0,0336–%0,108] · düşük güç ilan edildi |

→ **`sema-1.0` DONDURULUR** (A7), yukarıdaki dört sınır beyanıyla birlikte.

## 6. Kanıt zinciri

| İddia | Kaynak |
|---|---|
| Sınav sonucu 24/30, altı uyumsuzluk, sebep dağılımı | `reports/task16_sema_sinavi.json` |
| Sınır takımı vaka metinleri ve hedefleri | `data/processed/sema_sinir_vakalari.csv` (`takim-1.1`, SHA256 doğrulandı) |
| `low` üretilemiyor, denendi ve geri alındı | `configs/degerlendirme_semasi.json` → `ilan_edilen_sinirlar` |
| K7 F1 %36,4 · `temporality` %99,24 varsayılan | `reports/task16_girdi_filtresi_olcum.json` |
| `lesion` dağılım ölçümü %11,7 | `scripts/64_fazA_lesion_dagilim_olcumu.py` → `reports/fazA_lesion_dagilim_olcumu.json` |
| Kör paketin geçersizliği | `docs/37_task17_known_malignancy_kor_dogrulama.md` §3 |
| Dağılım kapısının karar veremez hükmü | `configs/task17_dagilim_capasi.json` → `denetim_hukmu` |
| Protokol değişikliği ilkesi | aynı dosya → `denetim_hukmu.ilke` |
| A4 kör puanlama yargısı | `reports/km_kor_v2_yargi.md` · paket SHA `1641142...` |
| A5 ayrık dağılım ölçümü | `scripts/65_fazA_dagilim_ayrik_olcum.py` → `reports/fazA_dagilim_ayrik_olcum.json` |
| Kapının `high`-only öncülü | `scripts/49` satır 59-61 |
| Ayrımın kayıtlı gelecek protokolü | `configs/task17_dagilim_capasi.json` → `gelecek_protokol` |
