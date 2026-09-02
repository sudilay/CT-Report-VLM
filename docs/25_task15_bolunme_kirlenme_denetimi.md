# TASK-15 · RadTr Bölünme Kirlenmesi — Denetim Kaydı

**Tarih:** 2026-09-01
**Denetim türü:** bağımsız bölünme denetimi
**Durum:** Kirlenme **doğrulandı**; ölçülen hasar **sıfıra yakın**; kayıtlar düzeltilecek
**Maruziyet:** Bu denetimde hiçbir belge içeriği okunmadı, basılmadı veya yazıldı.
Her belge tek bir SHA-256 değerine indirgendi; yalnız sayımlar üretildi.

Bu belge [`24_task15_ucdan_uca_elestirel_denetim.md`](24_task15_ucdan_uca_elestirel_denetim.md)
(span ofseti, `docs/24`) ile birlikte okunur. İki bulgu bağımsızdır; bu belgedeki
sorun ofset sorununun **yukarısındadır** ve önce çözülmelidir.

---

## 1. Bulgu

RadTr'nin yayımlanmış `train.json` dosyası, `dev.json` ve `test.json`
belgelerinin **tamamını birebir içerir** — metin ve `ner` etiketleri dahil.

```
train.json = 1.057 kayıt
           = 925 özgün belge  +  dev.json'un 132 kaydı (train[925:1057] == dev, birebir)
175 test belgesinin 175'i de bu 925'in içinde (metin hash + ner hash aynı)
```

| | kayıt | benzersiz |
|---|---:|---:|
| train | 1.057 | 1.051 |
| dev | 132 | 132 |
| test | 175 | 175 |
| **toplam** | **1.364** | **1.051** |

Toraks alt kümesinde:

| | |
|---|---:|
| test toraks belgesinin `train.json` içindeki | **56 / 56** |
| dev toraks belgesinin `train.json` içindeki | **46 / 46** |
| benzersiz toraks belgesi | **325** |
| meşru geliştirme havuzu (train+dev, test hariç) | **269** |
| test/dev'den arınmış saf train havuzu | 223 |

Ayrıca `doc_key` **benzersiz bir kimlik değildir**: `_66_263.txt` ve `_71_42.txt`
her biri iki farklı belgeyi adlandırıyor.

**Yeniden üretim:**

```powershell
.\.venv\Scripts\python.exe scripts\26_bolunme_denetimi.py
```

Kirlenme bulursa çıkış kodu 1'dir; regresyon kapısı olarak kullanılabilir.

---

## 2. Test kilidi neden boşa döndü

Kilit koddaydı ve çalıştı — ama yanlış şeyi kilitliyordu.

`scripts/16_extract_radtr_thorax.py` bölüm kimliğini **dosya adından** üretiyor:

```python
d["_bolum"] = f          # f = "train" | "dev" | "test"
```

`train.json` içinden okunan bir test belgesi bu yüzden `kaynak_bolum="train"`
etiketi alıyor. `scripts/20_turkce_yuzey_taslagi.py` ve
`scripts/22_turkce_ipucu_taslagi.py` geliştirme havuzunu

```python
secili = [b for b in belgeler if b["kaynak_bolum"] in ("train", "dev")]
```

diye süzüyor. Süzgeç yalnız `test.json`'dan okunan 175 kaydı dışarıda bırakıyor;
onların `train.json` içindeki birebir ikizlerini içeri alıyor.

**Bölünme kimliği içerikten değil dosya adından geliyordu.** Kaynak dosyalar
çakışınca kilit anlamını kaybetti.

## 3. Maruziyet kaydı kanıtı ters okumuş

`scripts/20_turkce_yuzey_taslagi.py` başlığındaki kayıt şöyle diyor:

> *"72/82 = %88, test dahil ve hariç aynı. Test bölümü o sonuca hiçbir şey
> katmadı."*

Bu, temizliğin kanıtı sayıldı. Gerçekte **çoğaltmanın imzasıydı**: `test.json`'u
eklemek hiçbir şey değiştirmiyor, çünkü o belgeler zaten `train.json` içinden
sayılmıştı. Sıfır fark, "test'e dokunmadık"ın değil, "test'e zaten
dokunmuştuk"un işaretidir.

**Kural:** bir kümeyi eklemenin sonucu değiştirmemesi bağımsızlık kanıtı
değildir. Bağımsızlık ancak kimlik düzeyinde — içerik hash'iyle — gösterilir.

## 4. Ölçülen hasar — sıfıra yakın

Kirlenme gerçek, fakat etkisi ölçüldü. Her yüzey/ipucu deseni, fiilen madenlenen
325 belgelik havuzda ve meşru 269 belgelik havuzda ayrı ayrı sayıldı:

| sözlük | girdi | desteği **yalnız** test belgelerinden gelen |
|---|---:|---:|
| `tr-1.0` Türkçe yüzeyler | 144 kavram | **0** |
| `tr-ipucu-1.0` ipuçları | 28 desen | **1** (`degisim/stabil`, destek 1) |

Tek etkilenen ipucu zaman ekseninin parçası; K7 zaten eşiği geçemediği için
**bu eksende hiçbir sayı raporlanmayacaktı** (TASK-14, D39). Yani ölçüme giren
hiçbir desen test belgelerine bağımlı değil.

Desteği 5'in altına düşen 10 kavram: `airway` 3→2, `bulla` 3→1,
`drainage_tube` 5→4, `isodense` 2→1, `occlusive_pathology` 4→2, `pancreas` 5→4,
`prosthesis` 3→2, `spiculated` 2→1, `station_axillary` 2→1, `tumor` 4→3.
Hiçbiri sıfıra düşmüyor.

⚠ **Bu ölçümün sınırı:** frekans desteğini ölçer, niteliksel keşfi ölçmez.
D42 türü bulgular (*"kardiyomegali" 0 anma → "kalp boyutları" 313*) korpus metni
okunarak bulundu. Her yüzeyin meşru havuzda bağımsız desteği olduğu için temiz
havuzda yeniden türetmenin aynı desenleri vereceği beklenir, fakat bu bir
beklentidir; yeniden türetme koşulup fark raporlanmalıdır.

**Ayrıca ihlal edilmeyen:** test belgeleri üzerinde hiçbir zaman skor
hesaplanmadı. `scripts/23_turkce_dev_olcum.py` yalnız `kaynak_bolum=="dev"`
süzüyor, o da doğru 46 belge. D31'in "sonucu görüp kural değiştirme" yasağı
çiğnenmedi. Kirlenen şey desen türetme havuzunun temizliği, ölçüm değil.

## 5. Geçersiz olan iddialar

1. `configs/turkce_yuzeyler_taslak.yaml` ve `configs/turkce_ipuclari_taslak.yaml`
   başlığındaki **"RadTr toraks train+dev (373 belge) - test HARIC"** yanlıştır.
   Doğrusu: 325 benzersiz belge, 56 test belgesi dahil.
2. `scripts/20_turkce_yuzey_taslagi.py` içindeki maruziyet kaydı yanlış
   gerekçeye dayanıyor (§3).
3. **Yayımlanmış 80,1 F1 tabanı geçersizdir.** RadTr modeli `train.json`
   üzerinde eğitildi; o dosya kendi test setini içeriyor — model kendi test seti
   üzerinde eğitilmiş. [`16_dil_ablasyon_protokolu.md`](16_dil_ablasyon_protokolu.md)
   §6'daki karşılaştırma tamamen düşer. (`docs/24` bunu §4'te "aynı altküme değil"
   diye P1 saymıştı; gerçek sebep daha temeldir ve maddeyi ortadan kaldırır.)
4. **Bütün korpus istatistikleri şişkindir.** "429 toraks belgesi" gerçekte 325;
   "train+dev 31.847 span" dev'i iki kez sayıyor; 82 desenin frekansları, D41'in
   %97 ölçümü, D42'nin anma sayıları ve %88 kapsam oranı tekilleştirilmiş
   havuzda yeniden sayılmalıdır.
5. **`dev` tutulmuş bir küme değildir**, `train`in alt kümesidir. TASK-14'ün
   *"dev'de sına ve düzelt"* adımından çıkan present F1 %90,4 bir ayar kümesi
   tahmini değil, eğitim kümesi sayısıdır. D31'de her ikisi de "sınırsız"
   olduğu için ihlal yok; yalnız kaydın dili düzeltilmelidir.

## 6. Yapılacaklar

1. `scripts/26_bolunme_denetimi.py` regresyon kapısı olarak korunur.
2. Bölüm kimliği **içerik hash'inden** üretilir; `kaynak_bolum` alanı bu haliyle
   yanlış bilgi taşıdığı için kaldırılır veya hash'ten türetilir.
3. Belge kimliği `doc_key` olamaz; `{bolum}:{doc_key}:{satir}` veya içerik hash'i
   kullanılır. `span_id` buna bağlanır.
4. Şişkin korpus sayıları tekilleştirilmiş havuzda yeniden üretilir.
5. Sözlükler temiz havuzda yeniden türetilir; `tr-1.0` ile farkı raporlanır.
   Ölçülen hasar sıfıra yakın olduğu için bunun bir doğrulama koşusu olması,
   sözlüğü değiştirmemesi beklenir.
6. Bölünme yeniden kurulacaksa (bkz. §7) 2–5 ondan sonra tek seferde yapılır.

## 7. Bölünme kararı — ölçüldü, yeniden bölmeye gerek yok

Kirlenme hasarı sıfıra yakın olduğu için yeniden bölmenin tek gerekçesi
**istatistiksel güç** kalmıştı. O da ölçüldü.

`scripts/27_task15_guc_analizi.py` gerçek `dev` belge-başına eksen desteğini
kullanıp, projenin kendi `paired_bootstrap_difference` fonksiyonuyla, gerçek
fark sıfırken güven aralığının yarı genişliğini üretir:

| eksen | belge başına destek | n=56 | n=100 | n=150 |
|---|---:|---:|---:|---:|
| A1 kavram | ~25 | **0,022** | — | — |
| `present` | 10,9 | **0,031** | 0,025 | 0,019 |
| `absent` | 1,9 | **0,074** ⚠ | 0,053 ⚠ | 0,048 |
| `uncertain` | 2,3 | **0,065** ⚠ | 0,050 | 0,042 |

Yarı genişlik 0,05 marjından büyükse o eksen 0,05'lik bir farkı ayırt edemez;
gerçek fark ne olursa olsun sonuç *"kanıt yetersiz"* çıkar.

**İki sonuç:**

1. **A1 ve `present` 56 belgede yeterince güçlü.** Karar kuralının bu iki
   ayağı sağlam. Belge başına ~25 kavram düştüğü için etkin örneklem 56 değil
   ~1.400'dür; "56 belge az" sezgisi bu eksenler için yanlıştı.
2. **`absent` ve `uncertain` yapısal olarak güçsüz ve yeniden bölmek bunu
   çözmüyor.** `absent` n=150'de bile 0,048 — yani 325 toraks belgesinin
   yarısını teste ayırsak dahi ancak sınıra değiyor ve geriye türetme için
   175 belge kalıyor. Taban oran (1,9 absent/belge) fazla düşük; sorun
   bölünmede değil korpusta.

**Karar: RadTr'nin yayımlanmış bölünmesi korunur.** Yeniden bölmek A1 ve
`present`te zaten olan gücü tekrarlar, kırık ekseni düzeltmez ve türetme
havuzunu küçültür.

⚠ Bu tablo **iyimser**: span sayımı kullanıyor (gerçek A2/A3 üçlüleri
tekilleştirecek) ve `dev`in absent yoğunluğu (1,9/belge) `test`inkinden
(86/56 = 1,5/belge) yüksek. Gerçek `absent` aralığı buradan daha geniş olacak.

### Bunun karar kuralına etkisi — D45 değişmeli

[`19_task15_deney_tasarimi_dondurma.md`](19_task15_deney_tasarimi_dondurma.md)
§8 ve D45, **A1 + `present` + `absent`** üçünü eşit ana eksen sayıyor. Ölçüm
gösteriyor ki bu üçüncüsü ölçüm başlamadan hükümsüz. Sonucu görmeden şimdi
düzeltilmeli; ölçümden sonra düzeltmek D31 anlamında hile olur.

Önerilen düzeltme:

- **Karar eksenleri:** A1 ve `present`. İkisi üzerinden aile düzeyi düzeltme
  yapılır (iki karşılaştırma; %97,5'lik aralıklarda yarı genişlik ~0,025 ve
  ~0,035 — ikisi de marjın içinde kalır).
- **Betimleyici eksenler:** `absent` ve `uncertain`. Nokta tahmini ve güven
  aralığıyla raporlanır, karara girmez ve **güçsüz oldukları ölçümden önce
  ilan edilir**.
- Bootstrap örnekleminde bir sınıfın desteği sıfıra düştüğünde F1 politikası
  ayrıca dondurulur (`docs/24` §6.7). Mevcut kod bu durumda 0,0
  döndürüyor; bu tercih bilinçli olarak yazılmalı veya değiştirilmelidir.

---

## 8. Bu denetimde yapılan değişiklikler

| dosya | değişiklik |
|---|---|
| `scripts/26_bolunme_denetimi.py` | **yeni** · içerik hash'iyle bölünme çakışma denetimi; kirlenme varsa çıkış kodu 1 |
| `docs/25_...` (bu dosya) | **yeni** · denetim kaydı |
| `AGENTS.md` | D49 ve D50 eklendi; durum tablosu ve son güncelleme satırı değişti |
| `configs/turkce_yuzeyler_taslak.yaml` | başlığa düzeltme bloğu eklendi; **veri değişmedi** |
| `configs/turkce_ipuclari_taslak.yaml` | başlığa düzeltme bloğu eklendi; **veri değişmedi** |

İki sözlük dosyasında yalnızca yorum bloğu eklendi; hiçbir desen, sayı veya
kavram değiştirilmedi. Yanlış "test HARIC" ifadesi başka bir agent'ı yanıltacağı
için düzeltme yerinde yapıldı. Hash'ler bu yüzden değişti:

| dosya | eski SHA-256 | yeni SHA-256 |
|---|---|---|
| `turkce_yuzeyler_taslak.yaml` | `b5e2058a04b9a0870d3329cbbc5a2dc25f1f25c41a2e55e34f0cd397179fc8dd` | `442ae24c218e010545238e86d57b65689fc58b62f02b820e21d5312c0eba27a8` |
| `turkce_ipuclari_taslak.yaml` | `4f4efd3fbedf14457c490cd46e9a31b60e743c304c201b8ba5eebbee3790da7c` | `3fbbffd323afc170195b8416ab25f70e3e0440104eb2c82d10e7c1059d76ba7d` |

⚠ [`21_task15_altyapi_ve_dev_paketleri.md`](21_task15_altyapi_ve_dev_paketleri.md)
§7'de ve [`23_task15_pilot_isaretleyici_a_devir.md`](23_task15_pilot_isaretleyici_a_devir.md)
içinde kayıtlı eski yüzey hash'i artık **bayattır**. O paketlerin tamamı zaten
karantinada olduğu için ayrıca düzeltilmedi; yeniden üretimde doğru hash yazılacak.

## 9. Hiçbir zaman yapılmayanlar

- `test.json` dosyası bir kez bile geliştirme amacıyla açılmadı.
- Test belgeleri üzerinde hiçbir skor, metrik veya tahmin üretilmedi.
- Bu denetimde hiçbir belge içeriği basılmadı, dosyaya yazılmadı veya özetlendi.
- Model indirilmedi, çeviri yapılmadı, dış servise veri gönderilmedi.
- Hiçbir artefakt silinmedi; eski `dev` paketleri ve pilot denetim izi olarak duruyor.

---

## 10. Ofset doğrulaması — altı test, tek sonuç

Bu satır iki kez yanlış "düzeltildi". Üçüncüsü olmasın diye kararın dayandığı
bütün kanıt burada; hangi testin neden işe yaramadığı dahil.

| # | test | sonuç | işe yaradı mı |
|---|---|---|---|
| 1 | Resmî DyGIE++ okuyucu semantiği (`text[start:end+1]`, 0-tabanlı) | **0** | ✅ tanım gereği bağlayıcı |
| 2 | `Obs_Absent` spanı negasyon ipucu **içermeli** | −1 %32,3 · **0 %76,1** · +1 %56,2 | ✅ **gerçek iç tepe** |
| 3 | Negasyon ipucunu spanın **son tokenine** koyan kayma | mod **0** (1122) · −1 (603) · +1 (221) | ✅ iki taraflı, 0'da tepe |
| 4 | `Obs_Anatomy` spanı çekimli fiil **içermemeli** | −1 %6,4 · 0 %15,2 | ❌ **sola yanlı** |
| 5 | `Obs_Anatomy` spanı anatomi terimi **içermeli** | −2 %48,5 → +2 %24,4, monoton | ❌ **sola yanlı** |
| 6 | 2-token spanların tekrar yoğunlaşması | 0,53–0,57, düz | ❌ ayırt etmiyor |

**4 ve 5 neden çöp:** Türkçe radyoloji cümlesi `[anatomi] [bulgu] [yüklem]`
yapısında. Sola kaydırmak fiili mekanik olarak dışarı atar (test 4) ve anatomi
terimine yaklaştırır (test 5). İkisi de kendini kanıtlayan ölçüt — 2026-08-31'de
`-1` kaymasını koyduran "iç noktalama" ölçütünün aynı tuzağı. **Yokluk ölçütü
kaydırmayla iyileşir; içerme ölçütü iyileşmez.** Test 2 içerme ölçütüdür ve
monoton değil, tepe yapar.

**Sınanıp elenen alternatif hipotez:** kaymanın sabit değil konuma bağlı olduğu
(kaynakta `geniştir..Perikardiyal` gibi birleşmiş tokenler var). Ölçüldü:
tokenlerin yalnız %0,2'si böyle ve span öncesindeki birleşmiş token sayısıyla
en iyi kayma korele değil (her grupta medyan +0). Hipotez **reddedildi**.

### Kalan sınır: RadTr'nin kendi span gürültüsü

Doğru ofsette bile `Obs_Absent` spanlarının **%24'ü** negasyon ipucu taşımıyor
(*"yada taş dansitesi"*, *"lümen içi"*). Test 3'te en iyi kaymanın %49'u 0'da,
kalanı −1/+1'e dağılıyor. Bu bir kod hatası değil, kaynak veri gerçeği:
RadTr span sınırları gevşek.

**Etkisi:** kavram normalizasyon pilotunda bir kısım span kavrama net
eşlenemeyecek. Karantinadaki pilotta gözlenen "14 kayıt span sınırı
yüzünden `needs_adjudication`" bulgusu ofset düzeltmesinden **sonra da
sürecektir** — azalır, sıfırlanmaz. D48 bu durumu zaten doğru kurmuş:
bağlamdan kavram uydurulmaz. Bu sınır rapora geçmelidir.
