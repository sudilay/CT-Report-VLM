# TASK-15 · İkincil Model Doğrulaması — Kapanış Raporu

**Tarih:** 2026-09-02 · **Kapsam:** RadTr `dev`, 46 belge × 3 kol · **`test` açılmadı**
**Donanım:** NVIDIA A100-SXM4-40GB · torch 2.6.0+cu124 · transformers 5.16.1

> **Hüküm:** Kapalı 144'lük envanterle katı JSON sözleşmesi, 4–8B ölçekli **üç
> açık modelle (iki farklı model ailesi)** sağlanamadı. Model tabanlı ikincil
> doğrulama yapılamamıştır; birincil sonuç bu sınırla birlikte raporlanır.

---

## 1 · İkincil model neyi doğrulayacaktı

Dil kararını **birincil ölçüm** verir: dondurulmuş sözlük/kapsam sistemi.
İkincil model, o kararın **alete bağlı olmadığını** sınamak içindi — sözlüğü,
desenleri ve birincil çıktıyı hiç görmeden, yalnız metni ve kapalı 144 kavramlık
envanteri görerek aynı işi yapacaktı.

- İki sistem **aynı yönü** gösterirse → sonuç sağlam
- **Farklı yön** gösterirse → *"yönteme/model ailesine bağımlı"* diye raporlanır

Adaylar ve sıraları `test` açılmadan **önce** ilan edilmişti: ana aday
Qwen3.5-4B, zorunlu karşılaştırma Aya Expanse 8B, yalnız yapısal kapılardan
biri geçilemezse devreye giren yedek Qwen3-8B.

---

## 2 · Sonuç

Kapı 2 çıktıların **%100'ünün** doğrudan ayrıştırılabilmesini, kapı 3 envanter
dışı kimlik / geçersiz kesinlik oranının **sıfır** olmasını ister.

| model | kol | geçerli | oran | erken durdu | kapı 2 | kapı 3 |
|---|---|---:|---:|---|---|---|
| **Qwen3.5-4B** | `tr` | 37/46 | %80,4 | hayır | ❌ | ❌ |
| | `en-genel` | 31/46 | %67,4 | hayır | ❌ | ❌ |
| | `en-ucuz` | 34/46 | %73,9 | hayır | ❌ | ❌ |
| **Aya Expanse 8B** | üç kol | 0/8 | %0 | **evet** | ❌ | ölçülemedi |
| **Qwen3-8B** | `tr` | 1/8 | %12,5 | **evet** | ❌ | ❌ |
| | `en-genel` | 2/8 | %25,0 | **evet** | ❌ | ❌ |
| | `en-ucuz` | 2/8 | %25,0 | **evet** | ❌ | ❌ |

**Dördüncü bir model seçilmeyecek.** Aday havuzu tükendi ve sonucu gördükten
sonra model seçmek, protokolün engellemek için var olduğu şeydir.

---

## 3 · Üç farklı arıza, tek ortak duvar

Modeller **aynı hatayı yapmadı** — bu ayrım önemlidir, çünkü aynı hatayı
yapsalardı ortak sebep bizim kurulumumuz olurdu.

### Qwen3.5-4B — tekrar döngüsü ve bozuk JSON

Model kilitleniyor ve bitiremiyor. Bir belgede **7.000 karakter, 118 kavram
kimliği ama yalnız 47 benzersiz**; `station_hilar_axillary` tek başına **72
kez** tekrarlanıyor. Ayrıca anahtar adını düşürüyor:

```json
{"concept_id": "pacemaker", "assertion": "present"},
{"cardiothoracic_ratio", "assertion": "absent"}
      ↑ "concept_id": yok
```

### Aya Expanse 8B — Markdown çiti

24 denemenin **24'ü de tek tip**: cevabını ```` ```json … ``` ```` içine sarıyor.
İçerideki JSON bozuk değil; sarmalayıcı sözleşmeyi ihlal ediyor. Sonuç: Aya'nın
ne bulduğu hiç görülemedi.

### Qwen3-8B — envanteri yok sayma

Büyük model JSON'u **daha iyi** biçimlendiriyor; ihlallerinin neredeyse tamamı
biçim değil **kimlik uydurma**. Yani ölçek biçim sorununu çözüyor, envanter
sorununu çözmüyor.

### Ortak nokta

| model | uydurulan kimlik | benzersiz | etkilenen belge | en sık |
|---|---:|---:|---:|---|
| Qwen3.5-4B | 34 | 22 | 25 | `bronchi` · `cavitary` · `pneumatocele` |
| Aya 8B *(teşhis)* | 161 | 111 | 21 | `pleural_fluid` · `mediastinal_vascular_structures` |
| Qwen3-8B | 78 | 63 | 16 | `pleural_effusion` · `main_bronchi` · `pneumocyst` |

⚠ Aya satırı bir **teşhistir, kapı sonucu değil**: çıktılardaki Markdown çiti
analiz amacıyla kaldırılıp bakıldı — çit olmasa bile **24 belgenin 23'ü** yine
düşerdi. Uydurduğu kimlikler rapor metnindeki öbeklerin `snake_case` hâli; Aya
envanteri okumuyor, kendi kimliklerini metinden üretiyor.

**İki tür uydurma:**

- **Yeniden adlandırma** — `pleural_effusion` (bizde `effusion`),
  `hiatal_hernia` (bizde `hernia`). Model doğru kavramı buluyor, verdiğimiz adı
  kullanmıyor.
- **Kapsam dışı** — `pneumatocele`, `scoliosis`, `cavitary`, `suture`,
  `electrode`, `bronchopneumonia`. Gerçek toraks BT bulguları ama 144'lük
  listede **yoklar**; model karşılığı olmayan bir şey görüp ad uyduruyor.

---

## 4 · Bizim payımız, modellerin payı

| sebep | kim | durum |
|---|---|---|
| **Kesilme** — üretim token sınırında duruyordu | **biz** | Düzeltildi (1024 → 2048), koşu tekrarlandı. Yalnız **3 belge** kurtardı — kesilenlerin çoğu tekrar döngüsüymüş |
| **Çıktı biçimi zorlanmıyordu** | **biz** | Düzeltme önerildi, **geri çekildi** (aşağıda) |
| **Tekrar kontrolü yoktu** — koşucuda `repetition_penalty` hiç ayarlanmamıştı | **biz** | ⚠ 2026-09-03'te masabaşı analizle ölçüldü: eklenseydi tavan **%74,6**'da kalırdı, eşik %100'dü. **Belirleyici değildi** → [masabaşı analiz](task15_ikincil_model_masabasi_analiz.md) |
| Bozuk JSON | model | Ayarla çözülmez |
| Envanter dışı kimlik | model | Sınavın kendisi — **36 başarısızlığın 25'i** |

⚠ **Düzeltme (2026-09-03).** Bu tablo önceden *"tekrar döngüsü, bozuk JSON —
model, ayarla çözülmez"* diyordu. Koşucuda hiçbir tekrar kontrolü ayarlanmamış
olduğu için o atıfın dayanağı eksikti. Kayıtlı ham yanıtlar yeniden okunarak
ölçüldü: tekrar döngüsü **138 belgenin yalnız 4'ünde** görüldü ve bunların
**yalnız 1'i** envanter ihlali içermediği için kurtulabilirdi. Elenme sebebi
tekrar değil, **envanter dışı kimliktir**. Hüküm değişmedi, dayanağı güçlendi.

### Geri çekilen düzeltme

Aya'nın çitini engellemek için modelin cevabını `{"findings":` ile başlatmak
(asistan ön-doldurma) önerilmişti. Koşucu tarafındaki bağımsız inceleme itiraz
etti ve **itiraz kabul edildi**:

Ön-doldurma sonradan onarmıyor ama **üretimden önce modelin ağzına kelime
koyuyor**. Kapı 2 böylece *"model talimatı izledi mi"* olmaktan çıkıp *"biz
doğru ön eki seçtik mi"*yi ölçerdi. Aya'nın Markdown sarması **gerçek bir model
bulgusudur**; ön-doldurma onu düzeltmez, tekrar üretilemez hâle getirir. Ayrıca
`raw_response` saf model çıktısı olmaktan çıkardı.

### Kısıtlı decoding neden kullanılmadı

Grammar/JSON şemasıyla envanter dışı kimliği üretim anında imkânsız kılmak
mümkündü. Yapılmadı: kapalı listeye uymak **kapı 3'ün ölçtüğü şeydir**; orada
yardım etmek kapıyı sahte hâle getirirdi. Bu tercih, *"neden denemediniz"*
sorusunun cevabı kayıtta dursun diye açıkça yazılmıştır.

---

## 5 · Dil hakkında ne gösteriyor

**Güvenilir hiçbir şey.** Ama iki gözlem kayda değer.

### Kullanılamayacak olan

Qwen3.5-4B'nin **üç kolda da geçerli çıktı verdiği 22 belgede** (46'nın 22'si):

| karşılaştırma | Jaccard | | belge başına kavram | |
|---|---:|---|---|---:|
| `tr` ↔ `en-genel` | 0,405 | | `tr` | 18,8 |
| `tr` ↔ `en-ucuz` | 0,527 | | `en-genel` | 11,2 |
| `en-genel` ↔ `en-ucuz` | 0,475 | | `en-ucuz` | 13,7 |

Model Türkçede belge başına **%68 daha fazla** kavram buluyor. Sözlük sistemi
ise onarımdan sonra iki tarafı dengede gösteriyor (toplu Jaccard **0,940**).

**Bu sayı üç sebeple kullanılamaz:**

1. **Model kapılardan geçemedi.** 46 belgenin 25'inde kimlik uyduran, bir
   belgede aynı kavramı 72 kez tekrarlayan sistem güvenilir okuyucu değildir.
2. **Alt küme yanlı.** 22 belge rastgele değil, *üç kolda da modelin başarılı
   olduğu* belgeler — muhtemelen daha kısa ve basit olanlar.
3. **Daha çok kavram, daha çok bilgi demek değil.** Model Türkçe girdide 3 kat
   uzun çıktı üretiyor; uzunluk artışı ayrıntı ya da tekrar olabilir.

### Gerçek olan: işlem maliyeti

| model | `tr` | `en-genel` | `en-ucuz` |
|---|---:|---:|---:|
| Qwen3.5-4B | 20,1 | 16,8 | 9,9 |
| Aya 8B | 13,0 | 14,8 | 9,9 |
| **Qwen3-8B** | **29,8** | 10,3 | 8,8 |

Saniye/belge. Qwen3-8B'de Türkçe girdi İngilizceden **2,9 kat** pahalı. Bu bir
**bilgi** bulgusu değil **işlem maliyeti** bulgusudur; ana ölçüme girmez, ayrı
bir gözlem olarak raporlanır.

---

## 6 · Sözlük sistemine beklenmedik katkı

Modellerin uydurduğu **kapsam dışı** kimlikler, envanterin bedava bir dış
denetimidir: üç model de bizde karşılığı olmayan gerçek toraks BT bulgularına
ad uydurdu (`pneumatocele`, `scoliosis`, `cavitary`, `suture`, `electrode`,
`bronchopneumonia`).

**Şimdi eklenmeyecekler.** İki sebep: sözlük tek geçişle onarılıp
**donduruldu**; ve model çıktısına bakarak envanter büyütmek yeni bir kirlenme
yolu açar — ölçtüğümüz sistemi, ölçmeye çalıştığımız şeyin çıktısıyla beslemek
olur.

Envanterin **gelecek sürümü için kapsam boşluğu adayı** olarak kayda geçtiler.

---

## 7 · Deney tasarımında değişmesi gereken

**Kapılarda düzeltilecek bir kusur çıkmadı.** Gevşetilmeleri gerekmedi ve
gevşetilmediler; erken durdurma üç modelde de doğru tetiklendi ve boşa GPU
zamanı harcanmasını engelledi. Ön-doldurma itirazı, koruma mekanizmasının
dışarıdan bir gözle de çalıştığının kanıtıdır.

**Gelecek bir sürüm için:** kapalı envanterin model kimliklerine bu ölçekte
dayatılması çalışmıyor. İleride ikincil doğrulama denenirse ya kısıtlı decoding
kullanılmalı (ve kapı 3 ayrı bir yöntemle ölçülmeli), ya envanter modellerin
tanıdığı adlarla hizalanmalı — **ikisi de önceden ilan edilerek**.

---

## 8 · Artefaktlar ve yeniden inceleme

```
outputs/task15/ikincil_model/
├── kosu_v2/      ilk koşu (max_new_tokens=1024)
├── kosu_v2_1/    token tavanı düzeltilmiş koşu
└── kosu_v2_2/    Qwen3-8B yedek koşusu
```

Her koşuda model × kol başına üç dosya: `.jsonl` (belge başına ham yanıt +
doğrulama), `.ozet.json` (kapı ölçümleri), `.provenance.json` (model, revizyon,
üretim parametreleri, SHA-256, ortam). **Ham yanıtlar geçersiz olanlar dahil
saklandı**; erken duran koşuların kısmi dosyaları da kayıttır.

⚠ Kollar arası sayı karşılaştırırken **yalnız üç kolda da geçerli belgeler**
kullanılmalıdır. Geçerli belge sayıları kollarda farklıdır (37 / 31 / 34); ham
ortalamalar farklı belge kümelerini karşılaştırır. Kapı 2'nin %100 istemesinin
sebebi budur.

---

## 9 · Ablasyona etkisi

**Yok.** Dil kararını birincil ölçüm verir ve o hazırdır. Kaybedilen tek şey
şu itirazı kapatma imkânıdır: *"sonuç sözlüğü nasıl yazdığınıza bağlı
olabilir."* Bu artık kapatılamıyor ve raporda açık bir sınır olarak duruyor.

Kolun kapanması takvimi **kısaltır**: model seçim raporu ve o kolun skorlaması
artık yoktur.
