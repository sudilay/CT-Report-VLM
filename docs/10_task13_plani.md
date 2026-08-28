# TASK-13 — Çıkarım Doğruluğunun Ölçülmesi

**Faz 2 · Önkoşul:** TASK-11 ✅ TASK-12 ✅ · **Tarih:** 2026-08-27

---

## 1. Bu görev neyi ölçer, neyi ölçemez

TASK-11 ve TASK-12 çıktı üretti ama **doğruluğu ölçülmedi.** Bu görev o boşluğu
kapatır — ama tamamını değil, ve **hangi kısmını kapatamadığını açıkça söyler.**

| | |
|---|---|
| **Otomatik ölçülebilir** | Yapısal değişmezler — insan yargısı gerekmez |
| **İnsan yargısı gerekir** | Varlık kesinliği/duyarlılığı, negasyon F1, ölçü bağı doğruluğu |

---

## 2. ⚠ Altın açıklamayı kural yazarı üretemez

Kuralları ben yazdım. Aynı kişinin *"doğru cevap bu"* demesi, sistemi **kendine karşı**
ölçmek olur — çıkan sayı sistemin doğruluğunu değil, yazarın tutarlılığını gösterir.

**Bu, D26'nın (ayar/değerlendirme ayrımı) çözmediği ayrı bir sızıntıdır.** D26 *hangi
örneklem* sorusunu çözer; bu, *kim işaretler* sorusudur.

### Kural (D27 adayı)

| | |
|---|---|
| Altın açıklamayı **kim yapar** | Kural yazarı **dışında** biri |
| İşaretleme dosyası **ne gösterir** | **Yalnızca cümle** — sistem çıktısı gösterilmez |
| Neden | Sistem çıktısını görmek işaretleyiciyi **ona uydurur** (bağlanma yanlılığı); duyarlılık ölçümü de imkânsız hâle gelir — kaçırılan varlık görünmez |

Bu yüzden `13_build_gold_template.py` **kör bir dosya** üretir: cümle var, sistemin
bulduğu hiçbir şey yok.

---

## 2-B. Altın açıklama neye göre kurulur — yöntemsel dayanak

*"Doğru cevap"* tanımı **bizim kodumuzdan gelemez.** Gelirse ölçüm, sistemin kendi
tanımına uyup uymadığını ölçer — doğruluğunu değil. Dayanak **dış kaynaklar** olmalı.

### Her kuralın dış dayanağı

| Karar | Dayanak | Kaynak bizim mi |
|---|---|---|
| Varlık tipleri (gözlem / anatomi / niteleyici) | **RadGraph-XL** — ANAT/OBS ayrımı, ACL Findings 2024 | ❌ dış |
| Kesinlik değerleri `present/absent/uncertain` | **Alan sözlüğü belgesi §12.2** eşleme tablosu | ❌ dış |
| *"dışlanamaz"* → `uncertain` | Belge **Kritik kural 1** | ❌ dış |
| Öneri ifadesi status değiştirmez | Belge **Kritik kural 3** | ❌ dış |
| `stable/new/increased/decreased/resolved` | Belge `growth_status` | ❌ dış |
| Etiket adları ve kapsamı | **RadTr** 9 etiketli şema, Diagn Interv Radiol 2025 | ❌ dış |
| Ölçü birimi ve normalizasyon | RECIST 1.1 (kısa aks), Fleischner | ❌ dış |

**Kılavuz, kodumuza değil bu kaynaklara atıf yapar.** Kodu hiç görmemiş biri kılavuzu
okuyup işaretleyebilmeli. Kılavuzda *"sistem şöyle yapıyor"* cümlesi geçmez.

### Kılavuz çıktıdan ÖNCE yazılır

Sistem çıktısına bakıp kılavuz yazmak, kuralı sistemin davranışına uydurmaktır.
Kılavuz **yalnızca dış kaynaklardan** türetilir, sonra uygulanır.

### ⚠ Duyarlılık ve kesinlik AYRI toplanır — çünkü yanlılıkları farklı

Tek bir işaretleme biçimi ikisini birden veremez:

| Ölçüm | Biçim | Neden |
|---|---|---|
| **Duyarlılık** (K5) | **A: Kör listeleme** — yalnızca cümle gösterilir, işaretleyici içindekileri yazar | Kaçırılan varlık ancak böyle görünür. Sistem çıktısı gösterilirse kaçırdığı şey **hiç akla gelmez** |
| **Kesinlik** (K4) + kesinlik atamaları (K6/K7) | **B: Yargılama** — aday span gösterilir, *"bu doğru mu"* diye sorulur | Sunulan bir öğeyi yargılamak meşrudur; hızlıdır ve tutarlıdır |

**B'nin yanlılığı için karşı önlem: çeldirici.** Yargılama listesine sistemin
üretmediği **sahte adaylar** karıştırılır. İşaretleyici her şeye *"doğru"* diyorsa
çeldiricileri de kabul eder — ve bunu görürüz. **Çeldirici ret oranı**, işaretleme
kalitesinin denetimidir; rapora yazılır.

### Kim işaretler

| Rol | Kim | Neden |
|---|---|---|
| Birincil işaretleyici | **Kural yazarı dışında biri** | Kendi kuralını doğru sayma yanlılığı |
| İkinci işaretleyici (~%30 alt küme) | Bağımsız ikinci kişi/agent | **Cohen's kappa** — kılavuz uygulanabilir mi |
| Klinik sınır vakalar | Uzman | Klinik yargı veriden türetilemez |

**Uyuşmazlık nasıl çözülür:** kazanan seçilerek değil, **kılavuz düzeltilerek**.
Düzeltme nihai puanlamadan **önce** yapılır; sonra yapılırsa puan kılavuza uydurulmuş
olur.

Kappa düşükse sorun sistemde değil **kılavuzdadır** — ve bu, sistemi ölçmeden önce
bilinmesi gereken bir şeydir.

---

## 3. Neyi şimdi ölçebiliriz — yapısal değişmezler

K11–K15'in tamamı **altın açıklama olmadan** ölçülebilir; çünkü hepsi *"sistem kendi
kuralına uyuyor mu"* sorusudur, *"cevap doğru mu"* sorusu değil.

| # | Ölçüt | Eşik | Nasıl ölçülür |
|---|---|---|---|
| **K11** | `cannot be excluded` vakalarının hiçbiri `absent` değil | **%100** | İpucu kapsamındaki varlıkların `assertion` dağılımı |
| **K12** | Teknik çekince **kendi kapsamındaki** varlıklar `absent` değil | **%100** | Aynı cümledeki bağımsız negasyon **etkilenmemeli** |
| **K13** | `no X or Y` cümlelerinde **ikinci** bulgu da `absent` | ≥ %90 | Koordinasyon kalıbı taşıyan cümlelerde ikinci gözlem |
| **K14** | `absent`/`uncertain` satırlarda `assertion_cue` dolu | **%100** | Boş ipucu sayımı |
| **K15** | Ardıl ipuçlu cümlelerde `absent` yakalanma | ≥ %85 | Yalnızca ardıl ipucu taşıyan cümleler |

Bunlar **kural sadakati** ölçümüdür. Geçmeleri sistemin *doğru* olduğunu göstermez;
**geçmemeleri** sistemin kendi tasarımına uymadığını gösterir — ki o kesin hatadır.

---

## 4. Neyi ölçemeyiz — altın açıklama bekliyor

| # | Ölçüt | Eşik | Neden insan gerekir |
|---|---|---|---|
| K4 | Varlık **kesinliği** | ≥ %90 | Bulunan varlık gerçekten orada mı |
| K5 | Varlık **duyarlılığı** | ≥ %80 | **Kaçırılanı yalnızca insan görür** |
| K6 | Negasyon makro-F1 | ≥ %85 | Kapsam yargısı |
| K7 | Belirsizlik makro-F1 | ≥ %75 | Öznel sınır |
| K8 | Ölçü bağı — **kolay** alt küme | ≥ %97 | Hangi bulgunun ölçüsü |
| K9 | Ölçü bağı — **belirsiz** alt küme | ≥ %80 | Aynı |
| K10 | Zamansal sınıf doğruluğu | ≥ %85 | Güncel/önceki yargısı |

---

## 5. Eşleştirme kuralları — ölçümden ÖNCE sabitlenir

Sonucu görüp eşleştirmeyi gevşetmek, eşiği gevşetmekle aynı şeydir.

### 5.1 Bir varlık ne zaman "doğru" sayılır

İki ölçüt **ayrı ayrı** raporlanır:

| Ölçüt | Tanım |
|---|---|
| **Katı** | Karakter aralığı **birebir** aynı **ve** kavram aynı |
| **Gevşek** | Aralıklar **kesişiyor** **ve** kavram aynı |

Kural tabanlı çıkarımda sınırlar sık sık bir kelime kayar (*"akciğerde yaygın"* vs
*"akciğer"*). Yalnızca katı ölçüt raporlamak sistemi haksız yere düşük gösterir;
yalnızca gevşek raporlamak sınır hatalarını gizler. **İkisi birlikte.**

### 5.2 Kesinlik yalnızca EŞLEŞEN varlıklarda ölçülür

Sistem bir varlığı hiç bulamadıysa onun `assertion`'ı da yoktur. Negasyon F1'ini
kaçırılan varlıklar üzerinden hesaplamak, **varlık hatasını negasyon hatası gibi**
gösterir. K6/K7 yalnızca **her iki tarafta da bulunan** varlıklar üzerinde hesaplanır
ve eşleşme oranı ayrıca bildirilir.

### 5.3 Aynı kavramın birden çok anması

Eşleştirme **konumsaldır**, küme temelli değil. Bir cümlede iki `nodule` varsa,
birini bulup diğerini kaçırmak duyarlılığı düşürmelidir — küme karşılaştırması bunu
gizler.

### 5.4 Boş cümleler

Altın açıklamada da sistemde de varlık yoksa: bu bir **doğru** sonuçtur ama kesinlik
paydasına girmez (bölünme yok). Ayrıca sayılır ve raporlanır.

---

## 6. Raporlama — ayrı tutulacaklar

D26/6 gereği ve K8/K9 mantığıyla, şu üç ayrım **birleştirilmez**:

| Ayrım | Neden |
|---|---|
| **Rastgele** vs **hedefli zor** | Hedefli küme kasıtlı zor seçildi; birleşik ortalama hiçbir şeyi temsil etmez |
| **Kolay** vs **belirsiz** ölçü bağı | Ölçülü cümlelerin %81,5'i kolay; genel değer zor %18,5'i gizler |
| **Katı** vs **gevşek** varlık eşleşmesi | Sınır hataları görünsün |

Ayrıca **kesinlik ve duyarlılık ayrı** raporlanır — tek F1 sözlük çıkarımının
doğal asimetrisini (yüksek kesinlik, düşük duyarlılık) gizler.

---

## 7. Hangi küme kullanılır

| Küme | Kaynak | Şimdi | Kural değiştirilebilir mi |
|---|---|---|---|
| **Ayar** (`task12_ayar.csv`) | train, 150 cümle | ✅ **kullanılır** | ✅ evet |
| **Değerlendirme** (`task12_test-v1.csv`) | valid, 200 cümle | 🔒 **MÜHÜRLÜ** | ❌ hayır |

Değerlendirme kümesi **kurallar donduktan sonra bir kez** açılır (D26). Bu görevde
yapısal değişmezler her iki kümede ölçülebilir — çünkü onlar **cevaba bakmaz**,
sisteme bakar. Altın açıklama ise **önce ayar kümesinde** üretilir.

---

## 8. Sınır durumlar

| # | Durum | Nasıl ele alınır |
|---|---|---|
| 1 | İşaretleyici sistem çıktısını görürse | Kör dosya — sistem çıktısı yok (bölüm 2) |
| 2 | Sınır bir kelime kaymış | Katı + gevşek ayrı raporlanır (5.1) |
| 3 | Varlık kaçırılmış, kesinliği ölçülüyor | K6/K7 yalnızca eşleşenlerde (5.2) |
| 4 | Aynı kavram iki kez | Konumsal eşleştirme (5.3) |
| 5 | Cümlede hiç varlık yok | Ayrı sayılır, paydaya girmez (5.4) |
| 6 | Hedefli küme kolay kümeye karışır | `tur` kolonu ile ayrı (bölüm 6) |
| 7 | Kavram doğru, kesinlik yanlış | Varlık ✅ · assertion ❌ — ayrı sayılır |
| 8 | Sistem fazladan varlık üretmiş | Kesinliği düşürür; duyarlılığı etkilemez |
| 9 | Altın açıklama eksik doldurulmuş | Boş satırlar **atılır**, sayısı raporlanır — sıfır sayılmaz |
| 10 | Ölçü hiç bağlanmamış | `unresolved_attachments`'tan gelir; K9'un paydasında |

---

## 9. Uygulama sırası

| Adım | İş | Çıktı |
|---|---|---|
| **C1** | Yapısal değişmezleri ölç (K11–K15) — altın açıklama gerekmez | `reports/task13_degismezler.md` |
| **C2** | Kör işaretleme dosyası üret | `data/processed/task13_altin_ayar.csv` |
| **C3** | İşaretleme kılavuzu | `docs/11_isaretleme_kilavuzu.md` |
| **C4** | Puanlama motoru (K4–K10) — dosya dolunca çalışır | `src/radyovlm/evaluation/score.py` |
| **C5** | Testler | `tests/test_score.py` |
| **C6** | Altın açıklama doldurulunca ölçüm | `reports/cikarim_dogruluk_raporu.md` |

C1 ve C4 **şimdi** yapılır. C6 insan işaretlemesini bekler.
