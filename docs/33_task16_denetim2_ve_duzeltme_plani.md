# TASK-16 · İkinci Bağımsız Denetim ve Düzeltme Planı

**Tarih:** 2026-09-03 · **Denetleyen:** Gemini (bağımsız) · **Durum:** ONAY BEKLİYOR
**Denetlenen:** adım 0-4'ün uygulanmış hâli + kilitli 45 vakanın hedef atamaları
**İstek belgesi:** `outputs/task16/GEMINI_DENETIM_ISTEGI.md`

> ⚠ **Bu plan onaylanmadan hiçbir düzeltme uygulanmayacak, kilit açılmayacak.**
> Adım 6 (şema yazımı) bu düzeltmeler bitmeden başlamayacak.

---

## 1 · Denetimin hükmü

> **(a)** Kilitlenen 45 vakanın hedef atamaları mevcut hâliyle **tam güvenilir
> değildir**; A20 çiğnenmiş, benignite hükümleri spikülasyon morfolojisine
> ezdirilmiş, karar #12 kilitte tersine çevrilmiş ve `indeterminate` sınıfı
> negatif kontrol betiğinde malignite sayılmıştır.
>
> **(b)** Bu hatalar düzeltilmeden, mükerrer vaka elenmeden ve çoklu cümle
> toplama köprüsü kurulmadan **şema yazımına geçilmemelidir.**

**Her iki hükme de katılıyorum.**

Denetimin en ağır bulgusu şu: **iki yerde kendi yazdığım A kuralını ihlal
etmişim.** Bu, planın "otorite modeli" iddiasını zayıflatır — bir kurala atıf
yapıp onu ihlal edebiliyorsam, o atıf tek başına güvence değildir.

---

## 2 · 14 bulgunun karara bağlanması

| # | bulgu | önem | karar |
|---|---|---|---|
| 1.1 | `C16-03` → `low`, oysa **A20** öneriyi status saymıyor | KRİTİK | ✅ **kabul** — kendi kuralımı ihlal |
| 1.2 | `C6-02` → `low`, oysa radyoloğun benign hükmü (A8) kazanmalı | KRİTİK | ✅ kabul ⚠ **yeni C kararı doğuruyor** (§4.2) |
| 1.3 | `C4-01` → `known_malignancy`, oysa yazılı bilinen primer yok | KRİTİK | ✅ kabul ⚠ gerekçe farklı (§4.3) |
| 1.4 | `docs/31` #12 `None` diyor, CSV `low` veriyor | ÖNEMLİ | ✅ **kabul** — iç çelişki, doğrulandı |
| 1.5 | `C13-02` → `indeterminate`, oysa yönlü şüphe | ÖNEMLİ | ✅ kabul — tutarlılık argümanı güçlü |
| 1.6 | `C16-01` dayanak etiketi `C#13` yazılmış | KÜÇÜK | ✅ kabul — klerikal |
| 2.1 | `C12-01` ve `C12-02` neredeyse aynı cümle | ÖNEMLİ | ✅ kabul |
| 2.2 | `known_malignancy` %20 (korpusta ~%1) | ÖNEMLİ | ⚠ **kısmen** — zenginleşme çelişki örneklemesinin doğal sonucu; 1.3 ile 5'e iner |
| 2.3 | Kontrol takımı zayıf: şablon/post-op/amfizem/koroner yok | KRİTİK | ✅ **kabul** — 3.3 ile birlikte |
| 3.1 | `MALIGN_URETIR` `indeterminate`'i malignite sayıyor | KRİTİK | ✅ **kabul** — #8 ile çelişiyor |
| 3.2 | "Büyüme ekseni yok" hükmü çifte standart | ÖNEMLİ | ⚠ **kısmen** — §5'te ayrıştırıldı |
| 3.3 | Şablon cümleler örneklemeden tamamen çıkarıldı | ÖNEMLİ | ✅ kabul (kontrol takımı için) |
| 3.4 | A/C ayrımı sahte güvence üretiyor | ÖNEMLİ | ✅ **kabul** — 1.1 bunun kanıtı |
| 4.1 | Çok cümleli rapor düzeyi vaka yok | KRİTİK | ✅ **kabul** — tamamen kaçırılmış |

**Toplam:** 14 bulgu · **11 tam kabul** · **2 kısmi** · **1 kısmi red** (§5)

---

## 3 · ⚠ İNCELENECEK: beş hedef düzeltmesi

**Bunlar klinik kararlar.** Onaylamadan önce gözle bakılması istenen kısım budur.
Her satırda: gerçek cümle · şimdiki hedef · önerilen hedef · gerekçe.

### 3.1 `C16-malignite-enf-03`

> *"Although there is **widespread infection**, **control for neoplasia is
> recommended**."*

| | |
|---|---|
| şimdiki | `low` |
| **önerilen** | **`not_mentioned`** |
| gerekçe | **A20 / Kritik kural 3:** *"klinik korelasyon önerilir"* bir **status değil, aksiyon önerisidir.* Cümledeki bulgu **enfeksiyon**, o da **A27** ile malignite ölçeğinin dışında. Malignite hakkında ne olumlu ne olumsuz bir hüküm var — yalnız bir öneri var |
| itiraz olabilir mi | *"Neoplazi kelimesi geçiyor, hiç şüphe yok mu?"* Kural şu ki öneri şüphe üretmez; üretirse her *"kontrol önerilir"* cümlesi malignite şüphesine dönüşür ve **yanlış pozitif patlar** |

### 3.2 `C6-malignite-benign-02`

> *"Structural distortion … and a **spiculated contour lesion**, which is
> **evaluated in favor of sequela fibrotic nodular formation**, is observed…"*

| | |
|---|---|
| şimdiki | `low` |
| **önerilen** | **`None`** (benign) |
| gerekçe | **A8:** *"in favor of X"* = **X present**. Radyolog kesin bir hüküm vermiş: sekel fibrotik nodüler formasyon. **#12'nin varsayılanı** da *"kararlı benign hükmü → benign"* diyor. `low` benim dayanaksız ara kararımdı |
| ⚠ **karşı kanıt** | **A34 (Fleischner) tam ters yönde uyarıyor:** *"a **spiculated border** … increase[s] the possibility of malignancy"*. Yani belgelenmiş bir malignite göstergesini atıyoruz |
| çözüm | Bu bir **yeni C kararıdır** ve kayda girmeli: *"Radyoloğun kesin benign hükmü, belgelenmiş spikülasyonu ezer mi?"* Varsayılan **evet** (hüküm kazanır) ama gerekçesi ve karşı kanıtı yazılı olacak |

### 3.3 `C4-derece-yuksek-01`

> *"Anasarca-style edema, bilateral pleural effusion, diffuse intra-abdominal
> free fluid, **metastatic masses in the liver**, **highly suspicious** nodular
> **in favor of metastasis** in both lungs"*

| | |
|---|---|
| şimdiki | `known_malignancy` |
| **önerilen** | **`high`** |
| gerekçe | Raporda **yazılı bilinen primer kanser yok**. *"Metastatic masses"* bir **radyolojik hükümdür**, patoloji değil. Ölçeğin en üst basamağı belgelenmiş kansere ayrılmalı, yoksa *"emin radyolojik karar"*a çöker |
| ⚠ **denetimin gerekçesine katılmadığım kısım** | Denetim *"`C4-02` `high` aldı, bu tutarsız"* dedi. Aslında sıralamam tutarlıydı: C4-02 **hedge'li** (*"in favor of"*), C4-01 **hüküm** (*"metastatic masses"*) — yani C4-01 daha kesin ve bir üst basamak mantıklıydı |
| **asıl sorun** | **`known_malignancy`'nin eşiği hiçbir yerde tanımlı değil.** Kaynak belge tanımlamıyor, ben de tanımlamadım. Bu **eksik bir C kararıdır** ve denetim onu ortaya çıkardı. Eşik *"raporda yazılı bilinen/belgelenmiş kanser"* olarak tanımlanınca C4-01 → `high` olur |

### 3.4 `C13-ekstratorasik-02`

> *"…faintly circumscribed hypodense lesions at the level of **liver segment 6**,
> the largest … **20 mm** …, were observed and **were not detected in the
> previous examination** (**metastasis?**)."*

| | |
|---|---|
| şimdiki | `indeterminate` |
| **önerilen** | **`intermediate`** |
| gerekçe | *"(metastasis?)"* bir **hipotezdir**, *"ayırt edemiyorum"* değil. Yeni ortaya çıkan 20 mm karaciğer lezyonu + metastaz hipotezi = **yönlü şüphe**. `C1-02` (*"might belong to metastasis"*) ve `C4-orta-01` (*"may be compatible with capsular metastasis"*) `intermediate` alırken bunun `indeterminate` alması tutarsız |
| ayrım | `indeterminate` → ayırt edilemeyen ayırıcı tanı (`C4-orta-02`, `C16-02`) ve teknik yetersizlik (`C11-02`) için ayrılır |

### 3.5 `C12-benign-belirsiz-01` ve `-02`

> *"Lymphadenomegaly in the left axilla, the largest of which has a narrow
> diameter of 11 mm, **hilar fat contents** selected, **possibly benign**, and a
> few lymph nodes smaller than 1 cm in the right axilla"*

| | |
|---|---|
| şimdiki | `low` |
| **önerilen** | **`None`** (benign) |
| gerekçe | **A26:** *fat-containing* Lung-RADS'in **benign özellik** listesinde. Üstelik *"possibly benign"* radyoloğun hükmü. **Yağlı hilus içeren lenf nodu reaktif/benign lenf nodunun klasik tanımıdır.** `docs/31` #12'nin varsayılanı da `None` — CSV'deki `low` kendi kaydımla çelişiyordu |
| ⚠ **`C12-03` FARKLI** | *"a 5.5 mm diameter **nodule developed** on the subpleural **possible** sequelae"* — burada **yeni bir nodül** var ve zemin *"possible"* sekel. Bu sadece benign hüküm değil. **`low` kalması önerilir**, denetim üçünü birlikte ele almış |

### 3.6 Özet tablo

| vaka | şimdiki | önerilen | tür |
|---|---|---|---|
| `C16-malignite-enf-03` | `low` | **`not_mentioned`** | kural ihlali düzeltmesi |
| `C6-malignite-benign-02` | `low` | **`None`** | kural ihlali + yeni C kararı |
| `C4-derece-yuksek-01` | `known_malignancy` | **`high`** | eksik C kararı (eşik tanımı) |
| `C13-ekstratorasik-02` | `indeterminate` | **`intermediate`** | tutarlılık |
| `C12-benign-belirsiz-01` | `low` | **`None`** | iç çelişki düzeltmesi |
| `C12-benign-belirsiz-02` | `low` | **`None`** | iç çelişki + mükerrer (§6/6) |
| `C12-benign-belirsiz-03` | `low` | **`low` (değişmez)** | denetimden ayrıldığım nokta |

---

## 4 · Kayda girecek üç yeni C kararı

Denetim bunları ortaya çıkardı; hiçbiri daha önce yazılı değildi.

### 4.1 `known_malignancy` eşiği nedir?
Kaynak belge tanımlamıyor. **Önerilen varsayılan:** raporda **yazılı** bilinen /
belgelenmiş kanser (*"known primary"*, *"bladder ca in the follow-up"*,
*"regressed primary malignancy"*) gerekir. Yalnız radyolojik hüküm en fazla
`high` üretir.
**Etkisi:** `C4-01` → `high`. `C5-01`, `C13-03`, `C16-01` `known_malignancy`
kalır (üçünde de yazılı bilinen kanser var).

### 4.2 Radyoloğun kesin benign hükmü, belgelenmiş spikülasyonu ezer mi?
**Önerilen varsayılan: EVET, hüküm kazanır.**
Gerekçe: A8 (*"in favor of"* = present) + #12 + projenin yanlış pozitif azaltma
misyonu.
⚠ **Karşı kanıt yazılı olacak:** A34 spiküle kenarın olasılığı artırdığını
söylüyor. Yani bu karar bir **bilgi kaybı** taşıyor ve ilan edilecek.

### 4.3 Teknik çekincede lezyon var mı yok mu ayrımı
`C11-02` (*"lesions in the liver … not possible to comment"*) → `indeterminate`
ama `K-teknik-01` (*"lung parenchyma … could not be optimally evaluated"*) →
`not_mentioned` atandı. **Ayrım şu ve yazılı değildi:**

| durum | sonuç |
|---|---|
| Lezyon **var**, karakterize edilemiyor | `indeterminate` |
| Hiçbir bulgu yok, **inceleme** yapılamıyor | `not_mentioned` |

Denetim bunu *"kapıdan geçsin diye zorlandı"* diye okudu. Ayrım kasıtlıydı ama
**hiçbir yerde yazılı olmadığı için haklı bir itiraz** — kayda giriyor.

---

## 5 · Kısmen reddettiğim bulgu — 3.2 "büyüme çifte standardı"

Denetim beş maddeyi tek sepete koydu. **İki farklı sebeple düştüler:**

| madde | gerçek sebep | denetimin okuması |
|---|---|---|
| #3, #14, #18 | Örnekler incelendi, **tarif edilen vaka popülasyonda hiç yoktu** — büyüyen şey damar (*"enlargement of pulmonary venous structures"*), büyüme olumsuzlanmış (*"No enlarged lymph nodes"*), farklı bulgular tek cümlede | ❌ "hacmi az diye düştü" |
| #15, #17 | **Yalnızca hacim** gerekçesiyle | ✅ doğru — çifte standart |

**Sonuç:** #3/#14/#18'in düşmesi doğru ve gerekçesi hacim değil. **#15/#17 için
denetim haklı** — A28 yazılı bir kural, 167 vaka gerçek ve *"hacim ≠ önem"*
ilkesini kendim yazmıştım.

**Yapılacak:** temel bir kural geri gelecek — *"belgelenmiş lezyon büyümesi
şüpheyi en az bir kademe artırır (A28), tavan `intermediate`"*.

---

## 6 · Yapılacaklar listesi

| # | iş | önem | not |
|---|---|---|---|
| 1 | **Tadilat belgesi** — kilidin neden açıldığı, revizyon defteri | önce bu | §7 |
| 2 | **6 hedef düzeltmesi** (§3.6) | KRİTİK | ⚠ onay bekliyor |
| 3 | `C16-01` dayanak etiketi `C#13` → `C#5+C#16` | KÜÇÜK | klerikal |
| 4 | `MALIGN_URETIR`'den `indeterminate` çıkar + testler | KRİTİK | #8 ile uyum |
| 5 | **Kontrol takımı 15 → 25+**: şablon negatifler · post-op değişiklik · amfizem/bül · koroner kalsifikasyon | KRİTİK | 2.3 + 3.3 |
| 6 | `C12-02` yerine yeni sınır vakası (kalsifiye granülom **veya** subsolid nodül) | ÖNEMLİ | mükerrer eleme |
| 7 | **En az 5 çok cümleli rapor vakası** + bileşik hedefleri | KRİTİK | toplama kuralının tek testi |
| 8 | Üç yeni C kararı kayda (§4) | ÖNEMLİ | C 10 → 13 |
| 9 | #15/#17 için temel büyüme kuralı geri | ÖNEMLİ | §5 |
| 10 | A/C etiketi → *"kılavuz atıflı yazar ataması"* | ÖNEMLİ | 3.4 |
| 11 | Bu belge + denetim kaydı tamamlanır | — | — |

**Tahmin: yarım gün.** Adım 6 bundan önce başlamaz.

---

## 7 · Kilidin açılması — meşruiyet gerekçesi

Takımlar `takim-1.0` olarak kilitlendi ve kural şu: *"kilitten sonra vaka
eklenemez/çıkarılamaz; kural takımı geçemezse KURAL değişir."*

**Bu düzeltme o kuralı ihlal etmiyor. Sebebi tek:**

> **Kurallar henüz yazılmadı.** Kilidin amacı *"kural geçmedi, hedefi
> değiştireyim"* davranışını engellemek. Burada olan bu değil: bulunanlar
> **kural ihlali** (A20), **iç çelişki** (#12) ve **kavramsal hata**
> (`MALIGN_URETIR`) — hiçbiri bir kural koşulup sonuç görülerek bulunmadı.

**Buna rağmen kayıtsız yapılmayacak:**

- Yeni sürüm **`takim-1.1`**
- Revizyon defteri: her değişen vaka · eski hedef · yeni hedef · **kim buldu**
- `takim-1.0` manifesti **silinmez**, `superseded` olarak saklanır
- Kilit açma **tek seferdir**; bundan sonra kural yazılınca aynı meşruiyet
  geçerli olmayacaktır ve bu yazılı olacak

⚠ **Bu, ikinci bir kilit açma için emsal değildir.** Kural yazıldıktan sonra
gelen her hedef değişikliği talebi, gerekçesi ne olursa olsun, reddedilecektir.

---

## 8 · Onaya sunulanlar

| # | karar | önerim |
|---|---|---|
| 1 | §3'teki **6 hedef düzeltmesi** — özellikle `C6-02` ve `C4-01` klinik karar | onayına |
| 2 | `C12-03`'ün `low` kalması (denetimden ayrıldığım nokta) | onayına |
| 3 | §4'teki **üç yeni C kararının varsayılanları** | onayına |
| 4 | Kilidin `takim-1.1` olarak açılması (§7) | **evet** |
| 5 | §6'daki 11 maddelik liste ve sırası | onayına |
