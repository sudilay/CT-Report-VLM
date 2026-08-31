# `test-v2` — Çıkarım Doğruluk Raporu

**TASK-13'ün son ölçümü.** Kurallar 2026-08-28'de donduruldu
([task13_dondurma.md](task13_dondurma.md)); küme **bir kez** açıldı.
Bu belgedeki sayılar geliştirme gözlemi değil, **raporlanan sayılardır**.

| | |
|---|---|
| küme | `test-v2` — 295 cümle · 231 hasta · hepsi `valid` bölümünden |
| yargılanan aday | 1.105 (838 gerçek + **267 çeldirici**) |
| işaretleyici | iki bağımsız, birbirinin dosyasını görmeden |
| betik | [21_score_testv2.py](../scripts/21_score_testv2.py) |
| sürümler | `bulgu-1.1` · `anat-1.1` · `ipucu-1.0` · `sema-1.3` · `ent-1.0` · `ctx-1.1` |

---

## 0. Ölçüm öncesi bir düzeltme — kaydedilmesi gerekiyor

Puanlama betiğinin **ilk sürümünde çeldirici kapısını yanlış yazdım**: yalnızca
`dogru_varlik_mi == H` cevaplarını "yakalandı" sayıyordu ve iki işaretleyiciyi de
düşürüyordu (%72,3 / %63,3).

Hata bendeydi, işaretlemede değil. Çeldirici üretici cümleden **gerçek** bir
kelime seçip ona **rastgele** bir kavram atıyor; kelime çoğu zaman gerçekten bir
varlıktır (`trachea`, `heart`) ve sahtelik **kavramdadır**. Kılavuz
([docs/11 §3](../docs/11_isaretleme_kilavuzu.md)) iki kolonu ayrı tanımlar, bu
yüzden `trachea → fracture` satırına `E`/`H` demek kılavuza **uyan** ve
çeldiriciyi **reddeden** cevaptır.

Doğru ölçüt: *tam kabul edilmediyse* — yani `(varlık=E ∧ kavram=E)` değilse —
çeldirici yakalanmıştır.

**Eşik sonucu görülüp gevşetilmedi.** Bunun kanıtı: aynı hatalı ölçüt yayımlanmış
**ayar** kümesinde %65,5 veriyor, oysa ayar raporunda **%100** yazıyor. Çelişki
ölçütün bende yanlış yazıldığını gösterdi; doğru ölçüt ayar kümesinde de %100
üretir. Yani ölçüt test açılmadan önce sabitti, ona geri dönüldü.

---

## 1. Çeldirici kapısı — ikisi de geçti

| işaretleyici | yakalanan | oran | eşik |
|---|---|---|---|
| A | 263 / 267 | **%98,5** | %80 ✅ |
| B | 265 / 267 | **%99,3** | %80 ✅ |

### ⚠ Ama kapının bir kör noktası var

Çeldirici kapısı **aşırı kabulü** yakalar — her şeye `E` diyeni görür. **Aşırı
reddi göremez**; tersine, çok reddeden bir işaretleyici bu kapıdan *daha iyi*
puanla geçer. Aşağıdaki 3. bölüm tam olarak bu durumdur.

Sonraki turlar için gereken: kapının ikinci bir kolu — **doğruluğu bilinen
adaylardan** oluşan bir pozitif kontrol örneklemi. *(Bu ölçüme uygulanmadı;
gelecek sürümün yöntem notudur.)*

---

## 2. K5 · Duyarlılık — kör listelemeden

Sistem çıktısı **görülmeden** doldurulan listelerden. Eşleştirme dize düzeyinde
ve **gevşektir** (kapsama + kelime örtüşmesi); işaretleyici serbest metin yazdığı
için katı kavram eşlemesi mümkün değil. Bu, duyarlılığı **olduğundan yüksek**
gösterir — **üst sınır** olarak okunmalı.

| işaretleyici | listelenen | bulundu | kaçan | **K5** | eşik |
|---|---|---|---|---|---|
| A | 763 | 672 | 91 | **%88,1** | %80 ✅ |
| B | 707 | 686 | 21 | **%97,0** | %80 ✅ |

Eksen kırılımı:

| | A | B |
|---|---|---|
| bulgu | %76,6 | %98,3 |
| anatomi | %91,2 | %91,9 |

**Anatomi ikisinde de aynı** (%91). Bulgu ekseni ayrışıyor (%76,6 / %98,3) çünkü
iki işaretleyici bulgu olarak **neyi listelemeye değer bulduğunda** ayrışıyor —
A 398, B 299 kalem yazmış. Bu bir sistem ölçüsü değil, listeleme eşiği farkı.

Ayar kümesinde K5 %93,0 / %86,3 idi. `test-v2`de **%88,1 / %97,0** — aynı bantta,
düşüş yok.

---

## 3. K4 · Varlık kesinliği — **iki işaretleyici ayrıştı**

| | rastgele | hedefli | hepsi |
|---|---|---|---|
| A | %100,0 | %99,3 | **%99,5** ✅ |
| B | %79,1 | %82,6 | **%81,6** ❌ |

Eşik %90. Biri fazlasıyla geçiyor, diğeri kalıyor. **Bu farkı açıklamadan hiçbir
sayı raporlanamaz.** Ayrışma iki ayrı yerde ve iki ayrı sebeple:

### 3a. Varlık ekseni — 49 ayrışma · **gerçek kılavuz boşluğu (benim hatam)**

| kavram | ayrışma | A | B |
|---|---|---|---|
| `anatomic_segment` | 22 | %100 `E` | **%0 `E`** |
| `abdomen` | 15 | `E` | `H` |
| diğer (dağınık) | 12 | | |

37/49 iki kavramda toplanıyor ve yön **tek taraflı** — bu, dikkatsizlik değil
**kural belirsizliği** imzasıdır.

Sebep: *"segment" tek başına anatomik yapı sayılır mı*, *toraks BT'de `abdomen`
çıkarılır mı* kararları **sözlükte** verildi ve orada yorumla belgelendi, ama
**işaretleme kılavuzuna hiç yazılmadı**. İşaretleyiciye sorulmayan bir kuralda
ayrışması beklenir.

> Bu, ayar kümesindeki D28 olayının **birebir aynısı**: sistemde uygulanan ama
> kılavuza geçirilmeyen karar. İkinci kez oldu. Kalıcı önlem 6. bölümde.

Bu iki kavram dışlanırsa B %81,6 → **%85,5** olur; A değişmez (%99,5). Yani
kılavuz boşluğu farkın **yaklaşık dörtte birini** açıklıyor, hepsini değil.

### 3b. Kavram ekseni — 104 ayrışma · **kural boşluğu değil, işaretleyici gürültüsü**

A gerçek adayların **786/786'sına** `E` dedi; B **104'üne** `H`. Yön yine tek
taraflı ama bu kez arkasında tutarlı bir okuma **yok**:

| B'nin reddettiği 104 aday | sayı |
|---|---|
| span metni ile kavram adı **birebir aynı** | **31** |
| gövde örtüşüyor (çoğul / sıfat / çekim farkı) | 100 |
| hiçbir örtüşme yok — gerçekten tartışılır | **4** |

Reddedilenlerden örnekler:

> `'lytic-destructive lesion'` → `lytic_destructive_lesion` — **birebir aynı dize**
> `'Mosaic attenuation'` → `mosaic_attenuation` · `'main bronchi'` → `bronchus`
> `'Pericardial'` → `pericardium` · `'densities'` → `density`

Bir kavram adının kendi span'i için yanlış olduğunu söylemek **kendi içinde
çelişkilidir**; bu, sonuca bakılmadan da geçersizdir. Gerçekten tartışılır olan
yalnızca 4 satır: `fatty → fat_containing` (×2), `opacities → density`,
`renal → kidney`.

B'nin **çeldirici kapısını %99,3 ile geçmesi bu hatayı gizledi** — çünkü kapı
aşırı reddi ödüllendiriyor (bkz. 1. bölüm).

### K4 · raporlanan okuma

| okuma | değer |
|---|---|
| A (tek işaretleyici) | %99,5 |
| B (tek işaretleyici) | %81,6 |
| **ikisi de kabul — alt sınır** | **%81,4** |
| en az biri kabul — üst sınır | %99,8 |

**Dürüst ifade:** K4 için tek bir sayı iddia edilemez. Gerçek değerin **%85,5 ile
%99,5 arasında**, üst uca yakın olduğu düşünülüyor (B'nin 104 reddinin 31'i
birebir aynı dize), ama bu **çıkarım**, ölçüm değil. Kavram ekseni tek
işaretleyiciye dayanıyor ve bu bir zayıflıktır.

---

## 4. K6 · Kesinlik ataması — **geçti, ve zayıf noktası bulundu**

| | A | B | eşik |
|---|---|---|---|
| rastgele | **%87,9** ✅ | %76,1 ❌ | %85 |
| hedefli | **%88,9** ✅ | %83,2 ❌ | %85 |

Karışıklık matrisleri (satır = altın, sütun = sistem) — **ikisi de aynı şeyi
söylüyor**:

| altın \ sistem | absent | present | uncertain |
|---|---|---|---|
| **A** · absent | **73** | 0 | 0 |
| **A** · present | 11 | **675** | 6 |
| **A** · uncertain | 0 | **20** | 49 |
| **B** · absent | **67** | 3 | 0 |
| **B** · present | 2 | **519** | 11 |
| **B** · uncertain | 0 | **44** | 38 |

### Ne öğrendik

**`absent` neredeyse kusursuz.** A'da 73/73, B'de 67/70. Negasyon çözüldü.

**`present` çok güçlü.** %97,5 / %97,6.

**`uncertain` zayıf ve kaçaklar tek yöne gidiyor** — sistem belirsiz bulguları
`present` sayıyor: A'da 20 kaçak, B'de 44. Duyarlılık **%71 / %46**.

Bu doğrudan **D29'un faturasıdır.** *"compatible with"*, *"in favor of"*,
*"suspicious"*, *"probably"* ifadelerini `belirsizlik`ten çıkarıp
`cikarim_ifadesi` → `present` yapan karar, `uncertain` duyarlılığını düşürüyor.
`cikarim` grubu (89 aday) tam da bunu sınamak için konmuştu ve **cevap verdi**.

⚠ **Bu bulgu üzerine şimdi kural değiştirilmedi ve değiştirilmeyecek** (D26/5,
D31). `test-v2` kapandı. Bu, bir sonraki sürümün girdisidir ve etkisi ancak
`test-v3`te ölçülebilir.

`uncertain` ayar kümesinde 4–16 destekle ölçülemiyordu; **bu kümede 69/82 destekle
ilk kez ölçüldü.** D33'ün zenginleştirmesi amacına ulaştı.

---

## 5. K7 · Zaman — **ölçüldü ve KALDI** *(bu bölüm düzeltildi)*

### ⚠ Önceki teşhisim yanlıştı — kayda geçiyor

Bu bölümün ilk hâlinde *"K7 ölçülemedi, çünkü kılavuz önceki-tetkik cümlesini
tanımlamıyor"* yazmıştım. **Yanlış.** Kılavuzu K16 için açtığımda kuralın
`docs/12_pilot_rehberi.md`'de — işaretleyicilere okumaları söylenen dosyada —
⚠ işaretiyle ve tam bu vakayla yazılı olduğunu gördüm:

> | ⚠ *"has increased **compared to the previous** examination"* | **guncel** |
>
> **Son satır önemli:** *"önceki tetkike göre büyümüş"* cümlesinde bulgu
> **şimdi vardır**. "Önceki" sadece kıyas noktasıdır.

`docs/11_isaretleme_kilavuzu.md` §5 de aynı kuralı yazıyor.

Yani bu bir **kılavuz boşluğu değil**. Ayrışan 62 satırın tamamı bu kuralın
kapsadığı vakalar: *"önceki tetkike göre artmış"*, *"önceki tetkikte de
gözlenen"*. **A kuralı uyguladı, B uygulamadı.**

Bu, B'nin kavram ekseninde de görülen güvenilmezliğiyle (3b) **aynı yönde**.

### Sonuç: K7 ölçülebilir — A'nın işaretlemesinden

| | değer |
|---|---|
| doğruluk (tüm eksen) | %96,6 |
| **`prior` desteği** | **15** |
| `prior` kesinlik | **%27,6** |
| `prior` duyarlılık | **%53,3** |
| `prior` F1 | **%36,4** |
| yanlış `prior` ataması | **21** |

**K7 eşiği geçmiyor.** Sistem `prior` sınıfında hem kaçırıyor (15'in 7'si) hem
uyduruyor (21 yanlış atama). Doğruluğun %96,6 olması aldatıcıdır — neredeyse her
şey `guncel` olduğu için kör atış bile yüksek çıkar.

⚠ **Bu okuma tek işaretleyiciye dayanıyor** ve bunu uyum katsayısıyla
doğrulayamıyoruz (kappa 0,017). Dayanağı uzlaşma değil **kurala uygunluk**:
A'nın cevapları yazılı kuralla tutarlı, B'ninkiler değil. Bu bir gerekçedir,
kanıt değil — okuyucu bu gerekçeye katılmayabilir.

`prior` desteğinin yalnızca 15 olması ayrı bir sorundur. `onceki_tetkik` grubuna
60 cümle konmuştu ama bunların çoğu *"önceki tetkike göre"* kıyas cümlesi çıktı
ve kural gereği `guncel` sayıldı. **Hedefleme deseni yanlış şeyi yakalamış** —
D33 kotası bu eksende amacına ulaşmadı.

---

## 6. İşaretleyiciler arası uyum — özet

| eksen | n | uyum | kappa | okuma |
|---|---|---|---|---|
| varlık (E/H) | 1.105 | %92,7 | **0,760** | güçlü |
| kavram (E/H) | 1.105 | %68,0 | **0,336** | zayıf — 3b |
| kesinlik | 838 | %82,0 | **0,542** | orta |
| zaman | 838 | %85,0 | **0,017** | geçersiz — 5 |

---

## 7. Sonuç

| ölçüt | eşik | sonuç |
|---|---|---|
| çeldirici kapısı | %80 | ✅ %98,5 / %99,3 |
| **K5** duyarlılık | %80 | ✅ **%88,1 / %97,0** *(üst sınır)* |
| **K4** varlık kesinliği | %90 | ⚠ **%81,4 – %99,5** — tek sayı iddia edilemez |
| **K6** kesinlik ataması | %85 | ✅ **%87,9 / %88,9** (A) · ❌ %76,1 / %83,2 (B) |
| **K7** zaman | %85 | ❌ **KALDI** — `prior` F1 %36,4 (tek işaretleyici) |

### Savunulabilir olan

- **Negasyon çözüldü.** `absent` iki işaretleyicide de ~%100.
- **`present` güvenilir.** %97,5.
- **Duyarlılık eşiğin üstünde**, gevşek eşleştirmenin payı açıkça yazıldı.
- Ölçüm **hasta düzeyinde ayrık** bir kümede, kurallar **dondurulmuş** hâlde,
  **tek atışta** yapıldı. Sonucu gören hiçbir kural değişmedi.

### Savunulamayan — açıkça yazılıyor

1. **K4 tek sayı olarak iddia edilemez.** Kavram ekseni pratikte tek
   işaretleyiciye dayanıyor.
2. **K7 tek işaretleyiciye dayanıyor** ve eşiği geçmiyor: `prior` F1 %36,4. Dayanağı uzlaşma değil kurala uygunluk.
3. **`uncertain` duyarlılığı düşük** (%71 / %46) ve sebebi bilinen bir karardır
   (D29).
4. **K5 üst sınırdır**, gevşek dize eşleştirmesinden.
5. **Kılavuz boşluğu ikinci kez** ölçümü bozdu (`anatomic_segment`, `abdomen`).

---

## 8. Bundan sonrası — kalıcı önlem

Kılavuz boşluğu iki turda iki kez ölçüm bozdu. Tek seferlik yama yetmiyor:

1. **Sözlük kararı ⇄ kılavuz eşleşmesi zorunlu hâle gelir.** Bir kavram sözlüğe
   girdiğinde veya bir kapsam kararı alındığında, kılavuzda karşılığı yoksa bu
   bir **değişmez ihlali** sayılır ve `13_check_invariants.py` ile denetlenir.
   *(K16 — yazılacak.)*
2. **Çeldirici kapısına pozitif kontrol kolu eklenir** — aşırı reddi görebilmek
   için.
3. **Kılavuza yazıldı:** `anatomic_segment`, `abdomen`, `density_increase` kapsamı
   ve `qualifier` türü. Zaman kuralı **zaten yazılıydı** — eksik olan kural
   değil, işaretleyicinin ona uymasıydı.
4. **`uncertain` / D29** yeniden değerlendirilir; etkisi `test-v3`te ölçülür.

⚠ 1–4'ün hiçbiri `test-v2` sayılarını değiştirmez. Bu küme **kapandı**.
