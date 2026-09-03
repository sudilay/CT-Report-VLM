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

⚠ **Adım 2 bu kaydı küçülttü.** Kılavuzlar okunduktan sonra **dört madde A tipine
taşındı** (kaynakta yazılı çıktı) ve **biri düşürüldü** (çatışma yokmuş).
Ayrıntı: [`docs/30`](30_task16_sema_gerekce.md) §5.1–5.4. **Kalan C kaydı: 10 madde** (adım 3'te iki büyüme maddesi daha düştü).

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
için **düşürüldü** (§3.2) → 16. Adım 2'de 4 madde A'ya taşındı, 1'i daha düşürüldü → **kalan 11 madde.**

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
| ~~3~~ | benign bulgu büyüyor *(gerekçesi de geri çekildi, docs/30 §4.1)* | 1.780 | **13** | *"**enlargement of pulmonary venous structures** … calcific sequelae changes"* — büyüyen şey **damar**, sekel lezyon değil. *"**new infectious** process accompanied by sequelae"* — yeni olan **enfeksiyon** | **DÜŞÜRÜLDÜ** |
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

**10 madde** (adım 2'de 4'ü A'ya taşındı; adım 2-3'te toplam 7'si düşürüldü). Sütunlar: **hacim** = geliştirme havuzundaki benzersiz cümle ·
**dayanak** = varsayılanın gerekçesi.

### C-1 · Çekirdek

| # | karar | hacim | varsayılan | dayanak |
|---|---|---:|---|---|
| **1** | Olumsuzlanmış malignite ifadesi | 7.405 | Negasyon **kapsamı içindeyse** → `None`; dışındaysa olumsuzlanmamış sayılır | Cümlede olumsuzluk bulunması yetmez, **neyi kapsadığı** belirleyicidir (§3.3). Kapsamı `ctx-1.1` varlık düzeyinde çözer |
| **4** | Belirsizlikle nitelenmiş malignite | 477 | **Derece kelimesine göre:** *high suspicion*→`high` · *may/probable*→`intermediate` · *cannot be excluded*→`indeterminate` | Tek düzey atamak popülasyonu bozar (§3.4) |
| **5** | Stabil malignite bulgusu | 213 | **`known_malignancy`** — stabilite tanıyı değiştirmez | *"Stable, calcific parenchymal metastases"* — kanıtlanmış metastaz. Stabilite yönetimi etkiler, tanıyı değil |
| **6** | Malignite + benign aynı cümlede | 40 | **`indeterminate`** — kazanan aranmaz | İlan edilmiş belirsizlik / ayırıcı tanı (§3.3) |
| **8** | 6+1 ölçeğinin 4 sınıfa eşlemesi | yapısal | `None`→negatif · `low`,`indeterminate`,`intermediate`→belirsiz · `high`,`known_malignancy`→pozitif · benign niteleyici baskınsa→benign | Kayıplı indirgeme (docs/29 §5.1); yanlış pozitif/negatif oranını doğrudan belirler |
| **10** | `indeterminate` ↔ `intermediate` farkı | yapısal | `indeterminate` = karar verilemiyor (epistemik) · `intermediate` = orta düzey şüphe (derece) | Belge ikisini aynı ölçeğe koyar, farkı tanımlamaz. Ayrım yapılmazsa ölçek sıralı olmaktan çıkar |

### C-2 · Ağırlıklı

| # | karar | hacim | varsayılan | dayanak |
|---|---|---:|---|---|
| 11 | Olumsuzlanmış belirsizlik | 2.037 | Belge §12.2 Kritik kural 1: *"dışlanamaz"* → `uncertain` | büyük ölçüde **A** |
| 12 | Benign + belirsizlik | 758 | **benign (`None`)** | Popülasyon `in favor of` artefaktı; *"evaluated as a priority in favor of"* kararlı benign hükmüdür (§3.3) |
| 13 | Ekstratorasik malignite bulgusu kapsama girer mi | 472 | **EVET** | Karaciğer ve sürrenal en sık uzak metastaz bölgeleri; örnekler gerçek karaciğer metastazı (§3.1) |
| 16 | Malignite + enfeksiyon | 106 | **`indeterminate`** | *"may be due to other viral infections **as well as** lymphangitis carcinomatosa"* — ayırıcı tanı (§3.3) |

### A tipine taşınanlar — artık C değil

| # | karar | kaynak | not |
|---|---|---|---|
| ~~2~~ | Enfeksiyon ayrı eksende mi | **A27** — Lung-RADS enfeksiyöz/inflamatuvar bulguyu **Kategori 0**'a, şüphe ölçeğinin dışına koyuyor | varsayılan doğrulandı |
| ~~7~~ | Kalsifikasyon tek başına benign mi | **A26** — benign kalsifikasyon listesi **dar**: *complete, central, popcorn, concentric ring* · **A34** — benign görünen özellik tek başına benignlik göstermez | ⭐ korpus ölçümüyle güçlendi: bu listedeki paternler korpusta **pratikte yok** (`popcorn` 0), `calcific*` ise 17.193 |
| ~~9~~ | Bulgu → rapor toplama kuralı | **A25** (*"the nodule with the highest degree of suspicion"*) · **A33** (*"Use most suspicious nodule as guide"*) | iki kılavuz da aynı kuralı yazıyor |
| ~~15~~ | Büyüme şüpheyi yükseltir mi | **A28** — *"yavaş büyüyen nodül **is suspicious**"* | yükseltme A oldu; **tavan `intermediate` C olarak kalıyor** (kılavuz tavan yazmıyor) |

### Düşürülenler

| # | sebep |
|---|---|
| ~~3~~ ~~14~~ ~~18~~ ~~15~~ ~~17~~ | ⭐ **Hepsi büyüme temelliydi ve BÜYÜME EKSENİ BU KORPUSTA YOK.** Adım 3'te ölçüldü: 383.644 cümlede **167 gerçek büyüme ifadesi** (%0,64 çalışma). `enlarged` bu korpusta *"büyümüş"* değil *"büyük"* demek — dar desenin 14.378 eşleşmesinin **12.233'ü** *"enlarged lymph node"*, statik boyut. A28/A29 şemaya girmiyor (docs/30 §6.4). Bu, K7 (`prior` F1 %36,4) ile tutarlı: korpus tek zamanlı |
| ~~19~~ | ⭐ **Soru yanlış kurulmuştu — kılavuzlar çatışmıyor.** **A32**: Fleischner kendi kapsamını yazılı olarak sınırlıyor (*"do not apply to lung cancer screening, patients with immunosuppression, or patients with known primary cancer"*) ve tarama için **açıkça Lung-RADS'a yönlendiriyor**. Yerine bir **kapsam kuralı** geçti (aşağı) |

### ⚠ Kılavuzsuz bölge — A32'den doğan yeni kayıt

| durum | geçerli kılavuz |
|---|---|
| insidental nodül · 35+ yaş · bağışıklık normal · bilinen kanser yok | **Fleischner** |
| akciğer kanseri taraması | **Lung-RADS** |
| **bilinen primer kanser** · bağışıklık baskılı · < 35 yaş | ⚠ **hiçbiri** |

Üçüncü satır bu korpusta **gerçektir** — karaciğer metastazlı vakalar görüldü
(#13). Şema bu bölgede yalnız C varsayılanlarıyla çalışır ve bu **ilan edilir.**

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

## 5-B · İkinci bağımsız denetim sonrası eklenenler — v1.1

**Kaynak:** `docs/33_task16_denetim2_ve_duzeltme_plani.md` · Adım 4'te
kilitlenen 45 vakanın hedefleri ikinci bir bağımsız denetimden geçirildi; 6
hedef düzeltildi, kontrol takımı 15→23 vakaya çıkarıldı, 5 çok cümleli rapor
vakası eklendi. Bu bölüm o denetimin **kayda giren üç yeni C kararını** ve
büyüme kuralının kısmi geri dönüşünü içerir.

### Yeni C kararı — `known_malignancy` eşiği

Kaynak belge bu eşiği tanımlamıyor, biz de tanımlamamıştık. **Varsayılan:**
raporda **yazılı** bilinen/belgelenmiş kanser gerekir (*"known primary"*,
*"bladder ca in the follow-up"*, *"regressed primary malignancy"*). Yalnız
radyolojik hüküm (*"metastatic masses"* gibi doğrudan ifadeler) en fazla
`high` üretir. → `C4-derece-yuksek-01` bu kuralla `known_malignancy`'den
`high`'a düzeltildi.

### Yeni C kararı — radyoloğun kesin benign hükmü, belgelenmiş spikülasyonu ezer mi

**Varsayılan: EVET, hüküm kazanır.** Gerekçe: A8 (*"in favor of X"* = X
present) + #12 + projenin yanlış pozitif azaltma misyonu.

⚠ **Karşı kanıt kayıtlı:** A34 (Fleischner) *"a spiculated border … increase[s]
the possibility of malignancy"* diyor — yani bu karar **bir bilgi kaybı
taşıyor** ve bilerek alınıyor. → `C6-malignite-benign-02` bu kuralla `low`'dan
`None`'a düzeltildi.

### Yeni C kararı — teknik çekincede lezyon var mı yok mu ayrımı

| durum | sonuç |
|---|---|
| Lezyon **tarif edilmiş**, karakterize edilemiyor | `indeterminate` |
| Hiçbir bulgu tarif edilmemiş, yalnız genel inceleme kısıtlılığı var | `not_mentioned` |

Örnek: *"thyroid … hypodensity … cannot be clearly distinguished from
artifact, which may also be compatible with the nodule"* → tanımlı bir bulgu
var → `indeterminate`. *"Lung parenchyma … could not be optimally evaluated"*
→ tarif edilen bulgu yok → `not_mentioned`.

### Yeni C kararı — negatif belirsizlik: *"no suspicious X was observed"*

Çok cümleli rapor vakası R5'te bulundu. A3/A18'in kapsadığı *"X cannot be
excluded"* kalıbından **farklı**: orada şüphe **ortadan kaldırılamıyor**
(→ `uncertain`/`indeterminate`); burada şüphe **açıkça dışlanıyor**
(*"no suspicious mass … was observed"* → **`None`**). Ayrım, C#1'in negasyon
kapsamı ilkesinin şüphe ifadelerine uygulanmış hâlidir.

### Büyüme kuralının kısmi geri dönüşü

İkinci denetim, #15/#17'nin **yalnızca hacim** gerekçesiyle düşürüldüğünü
doğru buldu — bu, kendi *"hacim ≠ önem"* ilkemle çelişiyordu (§5). #3/#14/#18
için düşürme gerekçesi farklıydı (tarif edilen vaka popülasyonda hiç yoktu) ve
o üçü **düşük kalır**.

**Geri gelen temel kural:** A28 yazılı bir kuraldır (*"yavaş büyüyen nodül is
suspicious"*) ve korpusta 167 gerçek örneği var. Belgelenmiş lezyon büyümesi
**şüpheyi bir kademe artırır, tavan `intermediate`**dir — hacmi az olsa da
şemada bir dal olarak kalır. Ayrı bir C maddesi olarak numaralandırılmaz;
A28'in aktarımına ek not olarak `docs/30`'da işlenecektir.

### A/C ayrımının etiketi düzeltildi

Manifest ve önceki raporlarda *"hedefi A kuralına dayanan vakalar = gerçek dış
denetim"* ifadesi kullanılmıştı. **Bu yanlıştı** — hangi A kuralının
uygulanacağına ve hedefe kural yazarı karar veriyor; `C16-malignite-enf-03`'ün
kendi A20 kuralını ihlal etmesi bunun kanıtı. Düzeltilmiş etiket: hedefi A
kuralına dayanan vakalar **"kılavuz atıflı yazar ataması"**dır — gerçek
bağımsız denetim ancak adım 7'de (Codex kör yargılaması) gelir.

### Sayım güncellemesi

C kaydı üç yeni kararla **10 → 13** maddeye çıktı (üç yeni karar eklendi,
mevcut 10 madde sayıca sabit kaldı — sadece hedefleri düzeltildi).

---

## 6 · Sonraki bağ

Kayıttaki her madde, adım 4'te üretilecek **sınır vakası takımında** en az bir
gerçek cümleyle temsil edilecektir. Takım kurallar yazılmadan önce kilitlenir
(docs/29 §8.1). §2'deki artefaktlar örneklemeye taşınmayacaktır.

**v1.1 güncellemesi (2026-09-03):** takım ikinci bağımsız denetimden geçirildi,
6 hedef düzeltildi, kontrol takımı 23 vakaya çıkarıldı, 5 çok cümleli rapor
vakası eklendi. Ayrıntı: `docs/33_task16_denetim2_ve_duzeltme_plani.md`.
