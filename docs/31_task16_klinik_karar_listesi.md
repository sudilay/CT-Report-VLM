# TASK-16 · Klinik Yargı Gerektiren Kararlar Kaydı

**Tarih:** 2026-09-03 · **Kapsam:** yalnız geliştirme havuzu (383.644 cümle / 20.576 çalışma)
**Ölçüm:** `scripts/42_task16_celisen_gosterge_taramasi.py` → `reports/task16_celisen_gosterge_taramasi.json`

Bu belge, şemanın vermek zorunda olduğu ama **kaynakta yazılı karşılığı bulunmayan**
kararları listeler. Her karar için alınan varsayılan ve gerekçesi yazılıdır.

**Uzman onayı alınmayacaktır** (docs/29 §2.4). Bu kayıt bu yüzden daha da
gereklidir: hangi kararın hangi dayanakla alındığı yazılı olmadan şema
savunulabilir olmaz. Şemaya giren her C kararı
`karar_kaynagi: "gecici_varsayilan"` bayrağını taşır.

**Her varsayılan gerçek cümlelerle sınanmıştır** (§3). Sınavdan geçemeyen
varsayılanlar değiştirildi; hangi maddenin neden değiştiği yazılıdır.

---

## 1 · Sayı nasıl belirlendi

Tahmin edilmedi, **ölçüldü**. Yöntem: aynı cümlede birbiriyle çelişen gösterge
sınıfları birlikte geçiyorsa, o cümle bir karar noktası üretir.

| gösterge sınıfı | cümle | oran |
|---|---:|---:|
| negasyon | 134.772 | %35,13 |
| büyüme | 34.262 | %8,93 |
| ekstratorasik | 31.774 | %8,28 |
| enfeksiyon | 18.146 | %4,73 |
| malignite | 9.862 | %2,57 |
| benign | 9.848 | %2,57 |
| belirsizlik | 9.481 | %2,47 |
| kalsifikasyon | 9.478 | %2,47 |
| stabilite | 4.527 | %1,18 |

14 çelişki tarandı, 12'si ≥100 cümlede geçti. Yapısal kararlarla birlikte
**19 madde**.

⚠ **Örnek sınavından sonra bu sayı düştü:** üç madde gerçek çelişki içermediği
için **düşürüldü** (§3.2). **Kalan: 16 madde.**

---

## 2 · Ölçüm aleti — üç artefakt bulundu

D60'ın kuralı: *önce alete uygula.*

| # | artefakt | ölçüm | etkisi |
|---|---|---|---|
| 1 | **`buyume` deseni fazla geniş** | 34.262 eşleşmenin **9.944'ü (%29)** *"density increase"*, *"thickness increase"* — bulgu betimlemesi, lezyon büyümesi değil | Büyüme çelişkilerinin hacimlerini şişirdi; dar desenle **1.780 → 13**, **327 → 23** |
| 2 | **`stabilite` ∩ `negasyon` sahte** | *"no significant difference"* iki desene birden uyuyor, aynı ifade iki kez sayılıyor | Çift listeye alınmadı |
| 3 | ⭐ **`belirsizlik` sözlüğü yanlış** | 9.481 eşleşmenin **6.720'si (%71)** `in favor of` — ama **D29 bunu belirsizlik değil, çıkarım ifadesi (`present`) saymıştı** | #2, #4, #12, #17'nin hacimleri şişkin; #12'nin varsayılanı bu yüzden değişti |

`benign` ∩ `kalsifikasyon` (634) incelendi: *"sequelae calcific densities"*
çelişki değil **pekiştirme**. Alınmadı.

**Üçü de TASK-17'de düzeltilecek.** Burada kaydediliyor, düzeltilmiyor — sözlük
düzeltmesi bu görevin işi değil.

---

## 3 · Örnek sınavı

Varsayılanlar önce mantıkla yazıldı, sonra **her biri gerçek cümlelerle
sınandı.** Sonuç: 3 madde düşürüldü, 4 madde değişti, 6 madde doğrulandı.

### 3.1 Doğrulananlar

| # | kanıt cümlesi | hüküm |
|---|---|---|
| **5** | *"**Stable**, calcific parenchymal **metastases** in both lungs."* · *"Stable metastases in both lung parenchyma."* | Kanıtlanmış metastaz, stabil. Stabilite tanıyı değiştirmiyor. **Doğrulandı ve güçlendirildi:** bu vakalar `known_malignancy`'dir, yalnız "düşürülmez" değil |
| **7** | *"A **spiculated** contoured **calcific** nodule causing slight thickening and **retraction in the pleura**"* | Kalsifiye **ve** spiküle **ve** plevral çekinti — kalsifikasyon burada benignlik göstermiyor. **Doğrulandı** |
| **13** | *"**Metastatic** mass lesions … in both lobes of the **liver**"* · *"An increase in the number of **liver metastases**"* | Karaciğerdeki gerçek metastazlar. Organ gerekçesiyle elemek ciddi hata olurdu. **Doğrulandı** |
| **2** | *"The findings were evaluated primarily in favor of the **infectious** process."* · *"typical-probable **Covid**"* | Enfeksiyona yönelik ifadeler; malignite ekseniyle ilgisiz. **Doğrulandı** (hacim §2/3'e göre şişkin) |
| **6** | *"**no differentiation between malignant and benign** compression could be made"* | **Doğrulandı** (§3.3'te zaten değişmişti) |
| **1** | *"**No** significant difference … in terms of … **metastases**"* | **Doğrulandı** (§3.3'te zaten değişmişti) |

### 3.2 ⭐ Düşürülen üç madde — gerçek çelişki yokmuş

Dar desenle bakılınca bu üç maddenin **popülasyonu neredeyse boş** çıktı ve
kalan örnekler tarif edilen vakayı **hiç içermiyordu.**

| # | iddia edilen | geniş desen | dar desen | örneklerin gerçeği | karar |
|---|---|---:|---:|---|---|
| ~~3~~ | benign bulgu büyüyor | 1.780 | **13** | *"**enlargement of pulmonary venous structures** … calcific sequelae changes"* — büyüyen şey **damar**, sekel lezyon değil. *"**new infectious** process accompanied by sequelae"* — yeni olan **enfeksiyon** | **DÜŞÜRÜLDÜ** |
| ~~14~~ | kalsifiye lezyon büyüyor | 327 | **23** | *"**No enlarged** lymph nodes … 1-2 **calcific** lymph nodes"* — büyüme **olumsuzlanmış**. *"**spleen enlargement** and coarse calcifications"* — büyüyen **organ** | **DÜŞÜRÜLDÜ** |
| ~~18~~ | aynı cümlede stabilite + büyüme | 210 | **25** | *"**Newly developed** pneumothorax … **stable** consolidation areas … **newly appeared** progressive nodular consolidation"* — **farklı bulgular, farklı durumlar.** Tek lezyon hakkında çelişki yok | **DÜŞÜRÜLDÜ** — bulgu düzeyi katman zaten çözüyor |

**Ortak sebep:** üçü de `buyume` deseninin fazla genişliğinden doğmuştu (§2/1).
*"Büyüyen benign lezyon"* bu korpusta **pratikte yok**.

### 3.3 Değişen dört varsayılan

| # | ilk varsayılan | yeni | kanıt |
|---|---|---|---|
| **1** | negasyon + malignite → `None` | negasyonun **kapsamı** belirleyici | *"**No** significant difference … in terms of … **metastases**"* — olumsuzlanan **değişiklik**, metastaz **var**. Cümle düzeyi kural gerçek metastazı silerdi |
| **6** | malignite kazanır | **`indeterminate`** | *"**no differentiation between malignant and benign**"* · *"may be compatible with TB granuloma, pneumoconiosis, **or** malignancy"* — çelişki değil, **ilan edilmiş belirsizlik** |
| **12** | `low` | **benign** (`None`) | Popülasyonun çoğu `in favor of` artefaktı (§2/3): *"Sequelae were evaluated **as a priority in favor of** parenchymal change"* — bu **kararlı bir benign hükmüdür**, belirsizlik değil |
| **16** | ikisi de kaydedilir | **`indeterminate`** | *"these appearances **may be due to** other viral infections **as well as** lymphangitis carcinomatosa"* — ayırıcı tanı. #6 ile aynı çözüm |

### 3.4 Sınırı belirlenen ikisi

| # | sorun | çözüm |
|---|---|---|
| **4** | Varsayılan `intermediate` **fazla kaba.** Popülasyon karışık: *"evaluated with **high suspicion** in favor of new metastasis"* (yüksek) · *"**No** lytic-destructive lesion in favor of metastasis"* (olumsuzlanmış) · *"may be compatible with"* (orta) | **Derece kelimesi belirleyici:** *"high suspicion"* → `high` · *"may / probable"* → `intermediate` · *"cannot be excluded"* → `indeterminate`. Tek sabit düzey atanmaz |
| **15** | Tavan `intermediate`, *"high suspicion in favor of new metastasis"* gibi cümleleri düşürüyor | **Tavan korunuyor.** Büyüme kanıt üretmez; `high`'a çıkaran şey #4'ün derece kelimesidir, büyüme değil. İkisi birlikte çalışır |

---

## 4 · Kayıt

**16 madde.** Sütunlar: **hacim** = geliştirme havuzundaki benzersiz cümle ·
**dayanak** = varsayılanın gerekçesi.

### C-1 · Çekirdek

| # | karar | hacim | varsayılan | dayanak |
|---|---|---:|---|---|
| **1** | Olumsuzlanmış malignite ifadesi | 7.405 | Negasyon **kapsamı içindeyse** → `None`; dışındaysa olumsuzlanmamış sayılır | Cümlede olumsuzluk bulunması yetmez, **neyi kapsadığı** belirleyicidir (§3.3). Kapsamı `ctx-1.1` varlık düzeyinde çözer |
| **2** | Enfeksiyona yönelik belirsizlik malignite belirsizliği sayılır mı | 2.447 | **HAYIR** — malignite eksenine girmez | Korpusun %21'i COVID (docs/29 §3.4). Akut enfeksiyon filtresi en üst öncelikte |
| **4** | Belirsizlikle nitelenmiş malignite | 477 | **Derece kelimesine göre:** *high suspicion*→`high` · *may/probable*→`intermediate` · *cannot be excluded*→`indeterminate` | Tek düzey atamak popülasyonu bozar (§3.4) |
| **5** | Stabil malignite bulgusu | 213 | **`known_malignancy`** — stabilite tanıyı değiştirmez | *"Stable, calcific parenchymal metastases"* — kanıtlanmış metastaz. Stabilite yönetimi etkiler, tanıyı değil |
| **6** | Malignite + benign aynı cümlede | 40 | **`indeterminate`** — kazanan aranmaz | İlan edilmiş belirsizlik / ayırıcı tanı (§3.3) |
| **7** | Kalsifikasyon tek başına benign göstergesi midir | 23 | **HAYIR** | *"spiculated contoured calcific nodule … retraction in the pleura"* — kalsifikasyon burada benignlik göstermiyor. `popcorn` paterni bu korpusta 0 |
| **8** | 6+1 ölçeğinin 4 sınıfa eşlemesi | yapısal | `None`→negatif · `low`,`indeterminate`,`intermediate`→belirsiz · `high`,`known_malignancy`→pozitif · benign niteleyici baskınsa→benign | Kayıplı indirgeme (docs/29 §5.1); yanlış pozitif/negatif oranını doğrudan belirler |
| **9** | Bulgu → rapor toplama kuralı | yapısal | **En yüksek şüphe kazanır**, girdi kalite filtresinden geçenler arasında | Düşük güvenli çıkarımlar rapor sınıfını yükseltemez — K7 `prior` F1 %36,4 (docs/29 §7) |
| **10** | `indeterminate` ↔ `intermediate` farkı | yapısal | `indeterminate` = karar verilemiyor (epistemik) · `intermediate` = orta düzey şüphe (derece) | Belge ikisini aynı ölçeğe koyar, farkı tanımlamaz. Ayrım yapılmazsa ölçek sıralı olmaktan çıkar |

### C-2 · Ağırlıklı

| # | karar | hacim | varsayılan | dayanak |
|---|---|---:|---|---|
| 11 | Olumsuzlanmış belirsizlik | 2.037 | Belge §12.2 Kritik kural 1: *"dışlanamaz"* → `uncertain` | büyük ölçüde **A** |
| 12 | Benign + belirsizlik | 758 | **benign (`None`)** | Popülasyon `in favor of` artefaktı; *"evaluated as a priority in favor of"* kararlı benign hükmüdür (§3.3) |
| 13 | Ekstratorasik malignite bulgusu kapsama girer mi | 472 | **EVET** | Karaciğer ve sürrenal en sık uzak metastaz bölgeleri; örnekler gerçek karaciğer metastazı (§3.1) |
| 15 | Büyüme şüpheyi ne kadar yükseltir | 90 | **Bir kademe, tavan `intermediate`** | Büyüme şüphe artırır, kanıt üretmez. `high`'a çıkaran #4'ün derece kelimesidir |
| 16 | Malignite + enfeksiyon | 106 | **`indeterminate`** | *"may be due to other viral infections **as well as** lymphangitis carcinomatosa"* — ayırıcı tanı (§3.3) |
| 17 | Belirsizlik + büyüme | 140 | Bir kademe yukarı, tavan `intermediate` | #15 ile aynı; hacim §2/3'e göre şişkin |

### C-3 · Sınır

| # | karar | varsayılan | dayanak |
|---|---|---|---|
| 19 | Kılavuzlar çatışırsa öncelik | **Fleischner > Lung-RADS** | Gerekçe kılavuzun ağırlığı değil, **hasta grubunun eşleşmesi**: Lung-RADS *tarama* içindir (belirtisiz sigara içicileri, yıllık kontrol); Fleischner *insidental* nodül içindir. CT-RATE genel toraks BT'sidir — yaş medyanı 46, %21 COVID |

### Düşürülenler
~~3~~ · ~~14~~ · ~~18~~ — §3.2. Kayıtta bırakıldı; ileride `buyume` deseni
daraltılınca yeniden değerlendirilebilir.

---

## 5 · Kaydın okunması

**Hacim ≠ önem.** #6 (40) ve #7 (23) en düşük hacimli maddelerdir ama yanlış
karar verildiğinde **kanıtlanmış maligniteyi benign yazarlar** — projenin kabul
edemeyeceği hata türü. #1 en yüksek hacimlidir (7.405) ama kararı görece açıktır.

**Sıklık klinik ağırlık üretmez** (docs/29 §2.2/B). `sequela` korpusta 12.177 kez
geçer; bu onu kapsam içine sokar, benign olduğunu kanıtlamaz.

**Ölçülen hacimler ölçüm aletine bağımlıdır.** §2'deki üç artefakt, üç maddenin
düşürülmesine ve bir varsayılanın değişmesine yol açtı. Hacim rakamları TASK-17'de
sözlük daraltılınca yeniden ölçülmelidir.

**Bu kayıt şemadan önce yazılmıştır.** Varsayılanlar sonuç görülmeden bağlanmış,
gerçek cümlelerle sınanmış ve gerekirse değiştirilmiştir. Şema koşulduktan sonra
*"sonuç kötü çıktı"* gerekçesiyle değiştirilmeyecektir; değişiklik yeni şema
sürümü açar (docs/29 §9-B.11).

---

## 6 · Sonraki bağ

Kayıttaki her madde, adım 4'te üretilecek **sınır vakası takımında** en az bir
gerçek cümleyle temsil edilecektir. Takım kurallar yazılmadan önce kilitlenir
(docs/29 §8.1). §2'deki artefaktlar örneklemeye taşınmayacaktır.
