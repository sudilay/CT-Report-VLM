# TASK-15 · Dil Ablasyonu — Kapanış ve Sürüm Dondurma

**2026-09-03 · Durum: ASKIYA ALINDI, mevcut kanıt düzeyinde raporlandı**
**`test` bölümü açılmadı — mühürlü**

> Bu belge TASK-15'i kapatır. Deney **iptal edilmedi**: ölçüm altyapısı
> tamamlandı ve doğrulandı, `test` mühürlü duruyor, açma koşulu §5'te yazılı.
> Koşul oluştuğunda protokol aynen koşar.

---

## 1 · Hüküm

Sorulan soru: **Faz 3'te altın etiketleme Türkçe mi İngilizce mi yapılmalı?**

Verilen cevap ve **dayanağı**:

> **Türkçe.** Gerekçe doğruluk üstünlüğü **değildir** — Türkçe ile iyi bir
> İngilizce çeviri arasındaki fark ölçüm hassasiyetimizin altındadır (§3).
> Gerekçe şudur: **(a)** makine çevirisi deterministik değildir — aynı 46 rapor
> dakikalar arayla iki kez çevrildiğinde **5'i (%11)** farklı çıktı (D53);
> **(b)** ucuz çeviri kavramların **%17'sini** kaybettiriyor; **(c)** hedef
> kohort (Bakanlık verisi) Türkçe yazılacak, çeviri katmanı gereksiz bir
> bağımlılık ve tekrarlanamazlık kaynağıdır.

Yani ablasyonun cevabı *"dil önemsiz"* değil, **"hangi dilde çalıştığın değil,
nasıl çevirdiğin belirleyici — ve çeviri hattı tekrarlanabilir değil."**

---

## 2 · Ne ölçüldü, ne ölçülmedi

| | durum |
|---|---|
| Ölçüm altyapısı · üç çeviri kolu · dondurulmuş sözlük | ✅ tamamlandı |
| Sözlük simetrik onarımı (26 kavram, tek geçiş) | ✅ D62 |
| Türkçe birleşik kavram çıkarıcı | ✅ D61 |
| `dev` üzerinde kol karşılaştırması | ✅ betimleyici (§3) |
| Çeviri determinizm testi | ✅ D53 |
| EN-tıbbi kolu (MedGemma post-edit) | ❌ düşürüldü — D63 |
| Model tabanlı ikincil doğrulama | ❌ düşürüldü — D65, kanıtı D69 |
| **Kanonik altın · uzman incelemesi** | ⬜ **yapılmadı — radyolog erişimi yok** |
| **`test` çevirisi · skorlama** | 🔒 **açılmadı** |

**Hiçbir `test` belgesi çevrilmedi, hiçbir `test` skoru hesaplanmadı.**

---

## 3 · Altın-bağımsız fark üst sınırı — bu kapanışın ana sayısal iddiası

Kanonik altın üretilemediği için A1 F1 **doğrudan** ölçülemedi. Ancak
**hesaplanabilir bir üst sınır** vardır ve karar ölçütünü karşılamaya yeter.

### Mantık

İki kol **aynı** altına karşı puanlanacaktı. Ayrışmadıkları her belge-kavramda
puanları da aynıdır. Dolayısıyla F1 farkı, ayrışma miktarıyla **matematiksel
olarak sınırlıdır** — altının ne olduğu bilinmeden.

### Girdi (`dev`, 46 belge, dondurulmuş sözlük, `scripts/31`)

| | |
|---|---:|
| ortak belge-kavram | **1.039** |
| yalnız TR | **18** |
| yalnız EN-genel | **22** |
| simetrik fark | **40** |
| Jaccard | **0,963** |
| P_TR · P_EN büyüklüğü | 1.057 · 1.061 |

### Sonuç

Altının bütün olası biçimleri tarandı (ortak bulguların kaçının doğru olduğu,
iki sistemin de kaçırdığı kaç kavram olduğu dahil):

| senaryo | azami F1 farkı |
|---|---:|
| ortak bulguların %100'ü doğru | **1,89 puan** |
| %90'ı doğru | **2,00 puan** |
| %80'i doğru | **2,12 puan** |
| %70'i doğru | **2,25 puan** |
| **mutlak en kötü hal** (hiçbir varsayım yok, dejenere senaryo) | **4,06 puan** |
| **docs/19 §5 kabul marjı** | **5,00 puan** |

> **TR ile EN-genel arasındaki A1 F1 farkı, hangi altın standart kullanılırsa
> kullanılsın, 4,06 puanı aşamaz; gerçekçi bölgede ~2 puandır. Önceden bağlanmış
> 5 puanlık kabul marjının altındadır.**

docs/19'un karar kuralı — *"EN, A1'de TR'den 5 puandan fazla düşük değilse
İngilizce etiketleme savunulabilir"* — **altın olmadan sağlanmıştır.**

Yeniden üretmek için: `scripts/31_task15_kol_karsilastirma.py` ortak/yalnız
sayılarını verir; üst sınır taraması bu rapordaki üç parametre üzerinden
(ortak kesinlik, tek-taraflı ayrışmalar, kaçırma) yapılır.

### Bu sınırın söylemediği

1. **Mutlak doğruluk iddiası değildir.** İki sistemin *ayırt edilemez* olduğunu
   söyler, *doğru* olduklarını söylemez. İkisi birden aynı biçimde yanılıyor
   olabilir.
2. **`dev` bölümüne aittir** ve Türkçe sözlük `dev`'i gördüğü için TR lehine
   hafif yanlıdır (docs/28 §7/7). `test`'te ayrışma büyürse sınır gevşer.
3. **A1 eksenine aittir.** `present` ekseni için karşılık gelen ölçüm D66'dır:
   iki tarafta da bulunan 1.039 kavramın **%2,6'sında** kesinlik ayrışıyor ve
   incelenen örneklerin hiçbiri çeviri hatası değil, **şema farkıydı**.
4. `absent`/`uncertain` eksenleri **ölçümden önce** güçsüz ilan edilmişti (D51).

---

## 4 · Dondurulan sürümler

| bileşen | SHA-256 (ilk 16) |
|---|---|
| `configs/turkce_yuzeyler_taslak.yaml` | `f74ea2d9d26a0de0` |
| `configs/anatomi_sozlugu.yaml` | `405e3b5369f7ae01` |
| `configs/bulgu_sozlugu.yaml` | `d820c9251ca6f6f1` |
| `configs/task15_kavram_katalogu.yaml` | `eb9299f0488d5e6a` |
| `src/radyovlm/extraction/turkce_varliklar.py` | `9e8bff80446980be` |
| `data/processed/radtr_toraks.jsonl` | `5776dce1b96903a3` |
| `outputs/task15/ceviri_dev/en_genel_dev.jsonl` | `ca1ab8463606f1cd` |
| `outputs/task15/ceviri_dev/en_ucuz_dev.jsonl` | `07bbebcbf2aefe88` |

⚠ **Bütünlük notu.** `turkce_dondurma.md` (TASK-14) Türkçe yüzey dosyasını
`b5e2058a04b9a087` ile dondurmuştu; şimdiki hash `f74ea2d9d26a0de0`. Fark
**D62'nin tek geçişlik simetrik sözlük onarımıdır** (16 TR + 10 EN kavram) ve
belgelidir — dondurma ihlali değildir. Ancak
`configs/task15_kavram_katalogu.yaml` içindeki `envanter_sha256: b5e2058a…`
alanı **artık eskidir** ve onarım öncesi sürümü gösteriyor. Katalog yeniden
dondurulduğunda güncellenmelidir.

---

## 5 · `test` açma koşulu — sonucu görmeden yazıldı

`test` (56 belge, `55d21d9b5a3bf328`) şu **ikisi birlikte** sağlandığında açılır:

1. **A1 altını (veya ilan edilmiş gümüş standardı) üretilmiş, hash'lenmiş ve
   salt okunur kilitlenmiştir.** Gümüş standart kullanılırsa adı raporda
   *"uzman onaysız gümüş standart"* olarak geçer, "altın" denmez.
2. **Sayının değiştireceği gerçek bir karar vardır.** Örnek: mentör kapanış
   rakamı istiyor; ya da Bakanlık kohortu gelmeden önce taban ölçüm gerekiyor.

Şu an (2) **sağlanmıyor** — dil kararı §1'de verildi ve `test` skoru onu
değiştirmiyor. Bu yüzden mühür duruyor.

⚠ **Süresiz saklamak da bir kayıptır.** Harcanmayan held-out kümenin değeri
yoktur. RadTr `test`, elimizdeki **tek temiz Türkçe held-out küme**dir
(56 belge · 1.817 varlık); Bakanlık verisi gelmezse Türkçe çıkarım katmanını
görülmemiş veride ölçebileceğimiz başka kaynak yoktur. Koşul oluştuğunda
**tereddüt edilmeden açılır.**

**Açıldığında sıra** (docs/20 §7'den, değişmedi): altın kilitlenir → `test` tek
komutla paketlenir → çeviri **tek sefer** koşulur, ham çıktı değişmez artefakt
olarak saklanır → skorlama + 10.000 eşleştirilmiş bootstrap.

---

## 6 · Bilinen sınırlar — hepsi açıkça ilan edilmiştir

1. **Kanonik altın üretilmedi**; A1 F1 doğrudan ölçülmedi, üst sınırla
   sınırlandı (§3).
2. **Model tabanlı ikincil doğrulama yapılamadı.** Üç açık model (iki aile,
   4–8B) kapalı 144'lük envanterle katı JSON sözleşmesini sağlayamadı (D65).
   Tekrar kontrolü eksikliğinin belirleyici olmadığı ölçüldü (D69). Kaybedilen:
   *"sonuç sözlüğe bağlı mı"* itirazını kapatma imkânı.
3. **Türkçe tarafta ikinci korpus yok** — CT-RATE'in Türkçe asılları
   yayımlanmadı; Türkçe yüzey adayları yalnız RadTr desteğiyle sınandı.
4. **Sözlük uzman onayından geçmedi**; her kavram `uzman_onayi: false` taşır.
5. **`dev` sayıları Türkçe lehine hafif yanlıdır** — TR sözlüğü `dev`'i gördü,
   EN sözlüğü görmedi.
6. **İki sözlük de aynı 144'lük pencereden bakıyor.** Pencerenin dışındaki
   çeviri kaybı ölçülemez. D67 (`plevral sıvı`) ve D69'un 11 kapsam boşluğu
   bunun kanıtıdır — **ikisi de simetriktir**, karşılaştırmayı bozmaz.
7. **`absent`/`uncertain` eksenleri güçsüzdür** ve bu ölçümden önce ilan
   edildi (D51).
8. **Normallik beyanları** (*"kalp boyutları normaldir"* → `present`) hâlâ
   düzeltilmedi (D68). Simetriktir, karşılaştırmayı bozmaz; `present` ekseninin
   **mutlak** doğruluğunu etkiler.

---

## 7 · Bu kapanışın koruduğu şey

Deneyi koruyan kuralların hiçbiri gevşetilmedi:

- `test` kilitli kaldı ve açma koşulu **sonucu görmeden** yazıldı (§5)
- Sözlük onarımı tek geçişti ve donduruldu (D62)
- Düşürülen iki kol, önceden bağlanmış durma kurallarıyla düştü (D59/D63, D65)
- Model çıktısı onarılmadı; ham yanıtlar değişmez artefakt olarak duruyor
- Sonucu gördükten sonra dördüncü model seçilmedi
- D69'da bulunan **kendi hatamız** (tekrar kontrolü eksikliği) gizlenmedi;
  ölçüldü, belirleyici olmadığı gösterildi, atıf düzeltildi

**Devralınan açık işler** — hiçbiri `test` gerektirmiyor:

| # | iş | not |
|---|---|---|
| 1 | D68 · normallik beyanları | kılavuz kararı, iki tarafa simetrik uygulanır |
| 2 | TR kesinlik hattının birleşik çıkarıcıya resmen bağlanması | küçük, tanımlı |
| 3 | D67 + D69/sınıf-3 · envanter kapsam boşlukları | **gelecek sürüm**, şimdi eklenmez |
| 4 | `task15_kavram_katalogu.yaml` · eski `envanter_sha256` | §4 |
| 5 | A1 gümüş standardı pilotu (`dev_packages_v2`) | `test`'i açan tek şey |

---

## 8 · Belge haritası

| belge | ne anlatır |
|---|---|
| [docs/28](../docs/28_task15_genel_bakis.md) | genel bakış — soru, kurgu, bulgular |
| [docs/19](../docs/19_task15_deney_tasarimi_dondurma.md) | dondurulmuş deney tasarımı |
| [docs/kararlar.md](../docs/kararlar.md) | karar defteri (D49–D69) |
| [sözlük onarımı](task15_sozluk_onarimi_raporu.md) | D62 |
| [çeviri `dev` raporu](task15_ceviri_dev_raporu.md) | D53, D55 |
| [EN-tıbbi düşürme](task15_medgemma_kol_dusurme.md) | D63 |
| [ikincil model](task15_ikincil_model_raporu.md) | D65 |
| [**masabaşı analiz**](task15_ikincil_model_masabasi_analiz.md) | **D69 — kapanış kanıtı** |
