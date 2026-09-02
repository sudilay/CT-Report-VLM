# TASK-15 · Deney Tasarımı Dondurma Kaydı

**Tarih:** 2026-09-01  
**Sürüm:** 1.3  
**Kapsam:** Yalnızca RadTr · train 327 · dev 46 · test 56  
**Durum:** Yöntem, çeviri kolları, ikincil model seçimi ve bağımsız kanonik
kavram altını protokolü kararlaştırıldı; uygulama başlamadı; `test` bölümü
açılmadı. İkincil modelin kimliği yalnız `dev` karşılaştırmasından sonra
dondurulacaktır.

**1.1 değişikliği:** 2026-08-31 tarihli ilk kayıtta ikincil model doğrudan Aya
Expanse 8B olarak seçilmişti. Test açılmadan önce yapılan yeniden değerlendirmeyle
bu kimlik seçimi kaldırıldı; yerine aşağıdaki sınırlı, önceden tanımlanmış
`train/dev` model seçim protokolü kondu. Çeviri kolları ve karar metrikleri
değişmedi.

**1.2 değişikliği:** RadTr'nin yerel altın etiketlerinin kanonik `concept_id`
vermediği doğrulandı. A1 kavram F1'in dairesel olmaması için iki bağımsız model
ön-işaretlemesi ve tam radyolog kontrolüyle kanonik kavram altını üretme
protokolü eklendi. Ayrıntı:
[`20_task15_kavram_altin_normalizasyon_protokolu.md`](20_task15_kavram_altin_normalizasyon_protokolu.md).

Bu kayıt, [`16_dil_ablasyon_protokolu.md`](16_dil_ablasyon_protokolu.md) ve
[`18_task15_calisma_plani.md`](18_task15_calisma_plani.md) belgelerindeki genel
tasarımı model, değerlendirme ve karar kuralları düzeyinde kesinleştirir. Çelişki
olursa bu belgedeki daha yeni ve daha ayrıntılı karar uygulanır.

---

## 1. Soru ve sonuç

**Soru:** Aynı RadTr raporu doğrudan Türkçe işlendiğinde mi, İngilizceye
çevrilerek işlendiğinde mi kavram ve kesinlik bilgisini daha doğru korur?

**Sonuç:** Bir model sıralaması değil, şu karar üretilecektir:

> Faz 3 altın standart etiketlemesi Türkçe mi İngilizce mi yapılmalı?

Zaman ekseni ölçülmeyecektir. Span sınırı doğruluğu ölçülmeyecektir. Sonuç
yalnızca *RadTr benzeri sentetik Türkçe toraks BT raporları* için geçerlidir.

---

## 2. Model ve araç rolleri — dondurulan tasarım

| rol | araç/model | kullanım |
|---|---|---|
| genel çeviri | **Google Cloud Translation Advanced · `general/nmt`** | `tr → en`; glossary ve özelleştirme yok |
| tıbbi İngilizce | **Google NMT → MedGemma 1.5 4B** | Google çıktısına anlam-koruyucu tıbbi post-edit |
| ucuz/açık çevirmen kolu | **Helsinki-NLP `opus-mt-tc-big-tr-en`** (CC-BY-4.0) | sonucun çeviri kalitesine duyarlılığı + sabit revizyonla tekrar üretilebilirlik çapası |
| birincil çıkarım/değerlendirme | **dondurulmuş sözlük ve kapsam sistemi** | TR ve iki EN girdisinde belge düzeyi kavram/kesinlik çıkarımı |
| ikincil model değerlendirmesi | **`dev`de seçilecek tek model** | Qwen3.5-4B ile Aya Expanse 8B karşılaştırılır; Qwen3-8B yalnız koşullu yedektir |

### Neden Google — ve neden TranslateGemma değil (1.3, 2026-09-01)

Bu, "daha modern model daha iyidir" sezgisinin yanlış olduğu bir yer.

**CT-RATE'in İngilizcesi Google Translate API ile üretildi**, ardından iki dilli
tıp öğrencilerince düzeltildi. Bizim İngilizce sözlüklerimiz
(`bulgu-1.1` · `anat-1.1` · `ipucu-1.0`) tam olarak o metnin üzerinde
geliştirildi.

Dolayısıyla RadTr'yi başka bir çevirmenle (TranslateGemma, NLLB) çevirmek,
İngilizce sözlüğün hiç görmediği bir kelime dağılımı üretir. Sözlük daha çok
kaçırır, EN kolu **haksız yere** kötü çıkar ve ablasyondan *"Türkçe veri
gerekli"* sonucu çıkar — TASK-14'ün baştan uyardığı yanlış sonucun ta kendisi.
Çevirmeni "modernize etmek" bu deneyde tarafsız bir iyileştirme değildir.

Ayrıca **EN-tıbbi kolu (Google → MedGemma), CT-RATE'in kendi üretim hattının
makine karşılığıdır** (Google → insan tıbbi düzeltme). Dağılım olarak
sözlüğümüze en yakın kol budur.

⚠ Yakın, ama aynı değil: CT-RATE'te düzeltmeyi **insan** yaptı, bizde
**makine** yapıyor. Bu fark rapora sınır olarak yazılır.

**Aile örtüşmesi:** Çevirmen ile post-editörün aynı model ailesinden olması,
post-editörün kendi ailesinin çıktısında düzeltecek az şey bulmasına ve
"tıbbi post-edit katkısı"nın olduğundan küçük ölçülmesine yol açardı. Google
(tescilli) → MedGemma (Gemma) farklı soylar olduğu için bu sorun doğmuyor.
TranslateGemma'yı ana kola almak bu sorunu **yaratırdı**.

**NLLB-200 çıkarıldı:** CC-BY-NC 4.0 lisansı ticari kullanımı yasaklıyor.
Yerine `opus-mt-tc-big-tr-en` kondu: **CC-BY-4.0** — atıf zorunlu ama ticari
kullanım serbest, yani NLLB'nin kısıtı yok. ~0,2B parametre, CPU'da koşar,
revizyonu sabitlenir.

**Çevirmen seçiminde cheat sınırı:** kolların hepsi ölçümden önce ilan edilir ve
**hepsi raporlanır**. Çevirmeni test skoruna bakarak seçmek — "hangisi EN'i
kazandırıyor" denemesi — sürümü iptal eder. Seçim yoksa seçim yanlılığı da yoktur.

**Ölçeklenme:** ucuz kol bir kısıt değil ek bir bulgudur. Google'la EN kazanıp
Opus-MT'yle kaybediyorsa doğru sonuç *"İngilizce çalışılabilir, ama ucuz
çeviriyle değil"* olur.

### Neden MedGemma doğrudan çevirmen değil?

MedGemma tıbbi metin anlama için eğitilmiştir, özel bir makine çevirisi modeli
değildir ve resmî değerlendirmeleri ağırlıklı olarak İngilizcedir. Doğrudan
`tr → en` üretim yerine Google çevirisinin tıbbi post-editinde kullanılması,
ikinci İngilizce kolun yorumunu temizler: iki EN kolu arasındaki ek değişken
tıbbi post-edittir.

### Neden MedGemma değerlendirme modeli değil?

Aynı modelin hem İngilizce metni değiştirmesi hem kendi değiştirdiği metni
değerlendirmesi döngüsellik yaratır. İkincil değerlendirme farklı bir model
ailesinden seçilir; MedGemma aday değildir.

### İkincil model adayları ve seçim sırası

| sıra | aday | rol |
|---:|---|---|
| 1 | **Qwen3.5-4B** | ana aday; güncel, çok dilli, Apache 2.0 ve 8 GB GPU için pratik boyut |
| 2 | **Aya Expanse 8B** | zorunlu `dev` karşılaştırması; Türkçe desteği açık çok dilli aday |
| 3 | **Qwen3-8B** | yalnız Qwen3.5-4B aşağıdaki yapısal kapılardan birini geçemezse devreye giren yedek |

Qwen3.5-4B ve Aya aynı `dev` girdilerinde, altın etiketi isteme koymadan ve aynı
kapalı çıktı sözleşmesiyle çalıştırılır. Qwen3-8B baştan üçüncü bir skor avı için
koşulmaz. Yalnız Qwen3.5-4B; bellek/çalışma, çıktı geçerliliği veya şema uyumu
kapısını geçemezse onun yerine aynı protokole alınır.

### Dev model seçim kapıları — testten önce donduruldu

Her aday `dev`de TR, EN-genel ve EN-tıbbi girdilerin tamamında sınanır. Seçim
sırası şöyledir:

1. **Çalışabilirlik:** bütün planlı belgeler 8 GB GPU ortamında OOM, kesilme veya
   kalıcı çalışma hatası olmadan tamamlanır.
2. **Yapısal geçerlilik:** çıktıların %100'ü doğrudan ayrıştırılabilir ve kapalı
   JSON şemasına uygundur; sonradan içerik onarımı yapılmaz.
3. **Kapalı envanter:** envanter dışı `concept_id`, geçersiz kesinlik veya serbest
   tanı ekleme oranı sıfırdır.
4. **Doğruluk:** kapıları geçen adaylarda A1, `present`, `absent` ve `uncertain`
   ayrı ayrı raporlanır. Ana karşılaştırma A1 + `present` + `absent` üzerinden;
   `uncertain` ham ve D30 uyumlu iki görünümle ayrıca yapılır.
5. **Dil dengesi:** yalnız yüksek ortalama değil, TR ile iki EN kolu arasındaki
   farkların yönü ve en kötü kol da incelenir. Bir dilde belirgin çöküş gösteren
   aday seçilmez.
6. **Eşitlik:** doğruluk ve dil dengesi bakımından pratik olarak ayrışmayan
   adaylarda daha düşük tepe VRAM, daha kısa süre ve daha açık lisans tercih edilir.

Tüm aday sonuçları ve seçim gerekçesi rapora yazılır; yalnız kazanan raporlanmaz.
Bu, iki adayla sınırlı standart `dev` model seçimidir. `test`te birden fazla
model çalıştırıp en iyi sonucu seçmek yasaktır.

### Kesin sürüm dondurması

Seçilen modelin depo revizyonu, nicemlemesi, istemi, üretim parametreleri; API
model kimliği, çağrı zamanı ve çıktı dosyalarının SHA-256 değerleri `dev` koşusu
tamamlanınca ayrı bir çeviri/model dondurma raporuna yazılır. Bunlar yazılmadan
`test` açılmaz. Yönetilen Google modeli sonradan değişebileceği için ham API
yanıtları değişmez deney artefaktı olarak saklanır.

---

## 3. Üç girdi, iki çıkarım sistemi — altı koşu

| girdi | dondurulmuş sistem | dev'de seçilip dondurulan model |
|---|---:|---:|
| **TR** · RadTr Türkçe aslı | ✅ birincil | ✅ ikincil |
| **EN-genel** · Google NMT | ✅ birincil | ✅ ikincil |
| **EN-tıbbi** · Google NMT → MedGemma post-edit | ✅ birincil | ✅ ikincil |

Seçilen model, Türkçe ve İngilizce metinleri **aynı anda görmez**. Üç girdi birbirinden
bağımsız koşulur. Aynı model revizyonu, İngilizce talimat, kavram envanteri,
JSON şeması ve üretim ayarları kullanılır. Girdinin dili dışındaki hiçbir şey
değişmez.

Birincil dil kararı dondurulmuş sistemden gelir. Seçilen modelin sonucu model tabanlı
ikincil doğrulamadır. İki sistem farklı yön gösterirse sonuç *yönteme/model
ailesine bağımlı* diye raporlanır; genel bir dil hükmü kurulmaz.

---

## 4. Çeviri üretim kuralları

1. Çeviri birimi **belgenin tamamıdır**; parçalama ve sonradan birleştirme yoktur.
2. Belge kimliği ve sıra korunur; altın etiketler çeviri paketine girmez.
3. Google kolunda glossary, özel model, uyarlamalı çeviri ve insan düzeltmesi yoktur.
4. MedGemma yalnız tıbbi post-edit üretir; bulgu ekleyemez, silemez, kesinliği
   veya sayısal değeri değiştiremez, özetleyemez ve açıklama ekleyemez.
5. Üretken modellerde örnekleme kapalıdır; Qwen için düşünme modu kapatılır;
   sabit ve tekrarlanabilir decoding kullanılır.
6. Boş çıktı, kesilme, istem sızıntısı, JSON dışı model yanıtı ve kimlik/sıra
   bozulması görünür hata olarak kaydedilir.
7. Testte yalnız taşıma/API hatası aynı istekle yeniden denenebilir. İçeriğe
   göre istem değiştirme, elle düzeltme veya alternatif model seçme yapılamaz.

TranslateGemma ve NLLB ana test sonucunda en iyi çevirmeni seçmek için
kullanılmaz. Açık model kontrolü `train/dev` ile sınırlıdır.

---

## 5. İkincil model çıktı sözleşmesi

Serbest yorum yerine kapalı yapı istenir:

```json
{
  "findings": [
    {"concept_id": "pulmonary_nodule", "assertion": "present"},
    {"concept_id": "pleural_effusion", "assertion": "absent"}
  ]
}
```

- `concept_id` yalnız dondurulmuş envanterden seçilir.
- `assertion` yalnız `present`, `absent`, `uncertain` olabilir.
- Anatomi A1 kavram ölçümüne girer; RadTr anatomiye kesinlik vermediği için
  A2/A3'e girmez.
- Açıklama, Markdown, tanı önerisi ve zaman yorumu kabul edilmez.
- Aynı kavram belgede birden fazla kesinlikle geçiyorsa bilgiler katlanmaz;
  her `(belge, kavram, kesinlik)` üçlüsü ayrı korunur.

Sonuçlar çıktıktan sonra Türkçe ve İngilizce metni birlikte gören serbest model
yorumu yalnız hata taksonomisi ve hipotez üretimi içindir; skor hanesine girmez.

---

## 6. RadTr kanonik kavram altını

RadTr'nin `Obs_Present`, `Obs_Absent`, `Obs_Uncertain` ve `Obs_Anatomy`
etiketleri span, tür ve kesinlik sağlar; `nodule` veya `effusion` gibi kanonik
`concept_id` sağlamaz. Bu nedenle Türkçe sözlüğün eşlemesi altın kabul edilmez.

Kanonik altın, kapalı 144 envanterle Opus ve Codex tarafından birbirinden ve
sistem tahminlerinden kör biçimde bağımsız ön-işaretlenir. Radyolog birleşmiş
listenin tamamını inceler ve nihai kararı verir. Testte yeni kavram eklenmez;
karşılığı bulunmayan span `unmapped` kalır. Altın hash'lenip kilitlenmeden test
tahminleri veya skorları açılmaz.

## 7. Ölçütler

### A1 · Kavram çıkarımı

Radyolog-onaylı kanonik altındaki her belgede benzersiz `concept_id` kümesi
üzerinden P/R/F1. Hem toplu mikro değer hem belge düzeyindeki dağılım raporlanır.

### A2 · Kesinlik ataması

Kanonik kavram eşlemesi ile RadTr assertion etiketinin birleştiği
`(belge, kavram, kesinlik)` üçlüsü üzerinden makro-F1. Bir kavramın belgede
birden fazla kesinlikle geçmesi keyfî bir baskın sınıfa indirgenmez.

### A3 · Zorunlu eksen kırılımı

`present`, `absent`, `uncertain` için destek, P, R ve F1 ayrı verilir. Tek
ortalama sonuç olarak sunulmaz.

### Şema farkı

RadTr'nin teknik yetersizliği `uncertain` sayması ile D30 arasındaki fark için
iki sonuç verilir:

1. ham RadTr şeması,
2. teknik çekince şema farkı hariç D30 uyumlu sonuç.

Sistem veya altın etiket değiştirilmez.

### İkincil çeviri kalite alanları

Anatomi/konum, taraf, sayı-birim, negasyon dönüşü, gerçek belirsizlik, teknik
yetersizlik, bulgu ekleme-silme, terminoloji normalizasyonu ve çeviri yerine
özet üretme hata analizi tablosunda tutulur. RadTr bu alanların tümü için
bağımsız altın sağlamadığından ana karar metriği yapılmaz.

---

## 8. Belirsizlik ve karar kuralı — testten önce donduruldu

Her EN kolu için fark `EN − TR` olarak tanımlanır. Belgeler 10.000 kez
eşleştirilmiş bootstrap ile örneklenir; her örneklemde toplu metrik yeniden
hesaplanır ve %95 güven aralığı verilir.

**Pratik eşdeğerlik / kabul edilebilir kayıp marjı: 5 F1 puanı (`0,05`).**

| bulgu | karar |
|---|---|
| EN, A1 + `present` + `absent` eksenlerinde TR'den 5 puandan fazla düşük değil; güven aralığı bunu destekliyor | İngilizce etiketleme savunulabilir |
| TR, A1 veya `present`/`absent` eksenlerinden birinde 5 puandan fazla ve güvenilir üstün | Türkçe etiketleme gerekli |
| Genel EN ile tıbbi EN farklı yön gösteriyor | Sonuç çevirmene bağlı; tek dil kararı verilmez |
| Dondurulmuş sistem ile seçilen model farklı yön gösteriyor | Sonuç yönteme/model ailesine bağlı; tek dil kararı verilmez |
| `uncertain` diğer eksenlerle çelişiyor | Ham ve şema-farkı-hariç sonuçlarla eksen bazlı karar |
| Güven aralığı karar sınırını kesiyor | Kanıt yetersiz; tek dil kararı verilmez |

Türkçe tarafın düşük çıkması, yüzeyler uzman onaysız olduğu için tek başına
Türkçe verinin gereksiz olduğunu göstermez.

---

## 9. Geri çeviri — stres kontrolü, geçerlilik kapısı değil

TR → EN → TR koşusu çeviri kaybı ve terminoloji normalizasyonunu görmek için
yapılır. İki çeviriden geçen metnin zorunlu olarak daha kötü olacağı varsayılmaz.
Geri çeviri, betimleyici Türkçe ifadeyi sözlüğün daha kolay yakaladığı standart
bir terime dönüştürüp skoru artırabilir.

- Daha kötü çıkarsa birikimli çeviri kaybı raporlanır.
- Daha iyi çıkarsa normalizasyon örnekleri raporlanır.
- Tek başına hiçbir sonuç ölçüm düzeneğini geçersiz kılmaz.

---

## 10. Seçim yanlılığı ve test sınırı

- Adayları `train/dev` üzerinde önceden yazılmış yapısal ölçütlerle sınamak
  serbesttir.
- Aday taraması Qwen3.5-4B ve Aya ile sınırlıdır. Qwen3-8B yalnız önceden
  yazılmış yapısal kapı tetiklenirse kullanılır.
- Adayların tüm dev sonuçları saklanır; yalnız kazananı göstererek seçim izi
  gizlenmez.
- `test` sonucunu görüp çevirmen, model, istem, nicemleme, sözlük, kapsam veya
  karar kuralı değiştirmek ölçümü geçersiz kılar.
- Ayrışma sonrası yalnız şema farkı ve hata türü raporlanabilir.

---

## 11. Uygulama ve devir sırası

1. Çeviri paketi, kör kavram-normalizasyon paketi, adaptörler, çıktı doğrulayıcı
   ve belge düzeyi puanlayıcı yazılır.
2. Tüm kod ve kanonik eşleme kılavuzu yalnız `train/dev` ve sentetik test
   örnekleriyle doğrulanır.
3. Google, MedGemma ve TranslateGemma bağlantıları `dev` üzerinde sınanır;
   Qwen3.5-4B ile Aya seçim protokolüne göre karşılaştırılır. Qwen3-8B yalnız
   koşullu kapı açılırsa çalıştırılır.
4. Tek ikincil model seçilir; seçim tablosu, kesin model revizyonu, istem,
   parametreler ve hash'ler dondurma raporuna yazılır.
5. Opus/Codex bağımsız `dev` normalizasyon pilotu ve radyolog kılavuz kontrolü
   tamamlanır; kılavuz/istem/hash'ler dondurulur.
6. Dev bulguları ve iki ayrı paketi aynı anda üretecek kesin test komutu
   kullanıcıya sunulur.
7. Ancak bundan sonra RadTr `test` 56 belge için bir kez açılır; çeviri paketi
   altınsız, normalizasyon paketi tahminsiz üretilir.
8. Opus ve Codex kör bağımsız işaretler; radyolog tüm nihai listeyi onaylar;
   kanonik altın hash'lenip kilitlenir.
9. Ancak sonra altı test koşusu açılır/çalıştırılır, puanlanır, geri çeviri
   stresi uygulanır ve dil kararı raporlanır.

**Pratik önkoşullar:** Google Cloud Translation kimlik doğrulaması ve faturalama;
Hugging Face üzerinde MedGemma/TranslateGemma kullanım koşullarının kabulü;
8 GB GPU makinesinde 4-bit üretken model çalıştırma ortamı. Bunlar uygulama
altyapısının yazılmasını değil, gerçek model koşularını sınırlar.

---

## 12. Model kaynakları — 2026-09-01'de doğrulandı

- Google Cloud NMT · `general/nmt`:
  <https://docs.cloud.google.com/translate/docs/advanced/nmt-model>
- MedGemma 1.5 4B model kartı:
  <https://huggingface.co/google/medgemma-1.5-4b-it>
- TranslateGemma 4B model kartı:
  <https://huggingface.co/google/translategemma-4b-it>
- Qwen3.5-4B model kartı:
  <https://huggingface.co/Qwen/Qwen3.5-4B>
- Qwen3-8B model kartı:
  <https://huggingface.co/Qwen/Qwen3-8B>
- Aya Expanse 8B model kartı:
  <https://huggingface.co/CohereLabs/aya-expanse-8b>
- NLLB-200 distilled 600M model kartı:
  <https://huggingface.co/facebook/nllb-200-distilled-600M>
