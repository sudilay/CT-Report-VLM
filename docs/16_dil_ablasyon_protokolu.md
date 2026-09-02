# Dil Ablasyon Protokolü — TASK-15

**Sorulan soru:** Türkçe veri seti gerekli mi?

Bu belge, o soruyu **ölçülebilir** hâle getirir. Ölçüm başlamadan yazıldı;
sonucu görüp değiştirilirse sürüm iptal edilir (D26/5, D31).

**Kesin model, değerlendirme ve karar dondurması:**
[`19_task15_deney_tasarimi_dondurma.md`](19_task15_deney_tasarimi_dondurma.md).
Bu belgede daha önce genel bırakılmış model rolleri ve “fark küçük” tanımı,
ölçüm başlamadan önce bu yeni kayıtta kesinleştirilmiştir.

---

## 1. Soruyu ölçülebilir hâle getirmek

Ham hâliyle *"Türkçe veri önemli mi"* bir ölçüm sorusu değil. Ölçülebilir hâli:

> **Aynı belge Türkçe okunduğunda mı, İngilizceye çevrilip okunduğunda mı
> daha doğru çıkarım üretiyor? Fark varsa hangi eksende ve ne kadar?**

### ⚠ Ölçüm olmayan tasarım — ve neden

Bir modele hem Türkçesini hem İngilizcesini verip *"yorumla"* demek **ölçüm
değildir**:

| sorun | sonucu |
|---|---|
| Modelin kendi yanlılığı sonuca karışır | Ölçtüğümüz şey dil değil, model olur |
| Tekrarlanabilir değil | Aynı girdi farklı cevap verir |
| Karşılaştırılabilir sayı üretmez | Raporda "şu kadar kayıp" yazılamaz |

Model yorumu **atılmıyor** — hata analizinde niteliksel destek olarak kalıyor
(bölüm 7). Yalnızca *sonuç* hanesine yazılmıyor.

Bu yasak, iki dili aynı anda gören **serbest yoruma** aittir. Dilleri ayrı
koşan, kapalı JSON şemalı ve yalnız `dev`de seçilip testten önce dondurulan
model değerlendirmesi ikincil sayısal kontroldür; birincil dil kararının
yerine geçmez.

---

## 2. Tek değişkenli tasarım — bağlayıcı

| sabit | değişen |
|---|---|
| aynı belgeler (RadTr test · 56) | **girdinin dili** |
| aynı görev (varlık + kesinlik çıkarımı) | |
| aynı altın açıklama | |
| aynı ölçütler ve eşikler | |

Üç girdi:

| kol | girdi | üretim/kullanılan sözlük |
|---|---|---|
| **TR** | Türkçe asıl | Türkçe yüzeyler (`tr-0.2+`) |
| **EN-genel** | Google Cloud `general/nmt` | glossary yok · mevcut İngilizce sözlük |
| **EN-tıbbi** | Google NMT → MedGemma 1.5 4B post-edit | mevcut İngilizce sözlük |

Çeviriyi **iki yoldan** üretmek, çeviriyi de bir değişken yapar ve kaybın
**çeviriden mi dilden mi** geldiğini ayrıştırır. Tek çeviriyle bu ayrım
yapılamaz.

Her girdi iki sistemle ayrı koşulur: dondurulmuş sözlük/kapsam sistemi
**birincil**, `dev`de seçilip dondurulan tek model aynı kapalı JSON şemasıyla
**ikincil** değerlendirmedir. Model Türkçe ve İngilizce metni aynı anda görmez.

---

## 3. Puanlama — **belge düzeyinde**, span düzeyinde değil

### Sorun

RadTr'nin altın etiketleri Türkçe metnin **karakter konumlarına** bağlı. Belge
İngilizceye çevrilince o konumlar anlamsızlaşır; İngilizce çıktı neye karşı
puanlanacak?

### Çözüm

Span değil, **belge düzeyinde kavram kümesi** karşılaştırılır:

```
altın(belge)     = { (kavram, kesinlik), ... }
TR-çıktı(belge)  = { (kavram, kesinlik), ... }
EN-çıktı(belge)  = { (kavram, kesinlik), ... }
```

Üçü de **çeviriden bağımsızdır** — karakter konumu yok, yalnızca kavram ve
kesinlik.

### Kanonik kavram altını neden ayrıca üretilecek?

RadTr span ve `Obs_Present/Absent/Uncertain/Anatomy` etiketlerini verir, fakat
span'ın `nodule`, `effusion` gibi kanonik `concept_id` değerini vermez. Bu
nedenle sözlüğün kendi eşlemesi A1 altını yapılamaz; dairesel olur.

Kapalı 144 kavramla iki bağımsız işaretleyici birbirinden ve sistem tahminlerinden kör
bağımsız ön-işaretleme yapar. Radyolog birleşmiş listenin tamamını kontrol edip
nihai altını onaylar. Ayrıntı ve sıra:
[`20_task15_kavram_altin_normalizasyon_protokolu.md`](20_task15_kavram_altin_normalizasyon_protokolu.md).

Bu iş kod ve `train/dev` geliştirmesinden sonra yapılabilir; fakat test
tahminleri veya skorları görülmeden tamamlanıp hash ile kilitlenmelidir.

**Bedeli açıkça yazılır:** span sınırı doğruluğu ölçülmez. Ablasyonun sorusu o
olmadığı için kabul edilebilir; ama rapora "bu ölçüm span sınırı hakkında bir
şey söylemez" diye yazılır.

### Ölçütler

| kod | ne | nasıl |
|---|---|---|
| **A1** | kavram çıkarımı | belge düzeyinde P / R / F1 |
| **A2** | kesinlik ataması | eşleşen kavramlarda makro-F1 (`present`/`absent`/`uncertain`) |
| **A3** | eksen kırılımı | A2 sınıf başına ayrı — çevirinin etkisi eksenlere **eşit değil** |

⚠ **A3 zorunlu.** Tek bir ortalama, çevirinin nerede kırıldığını gizler.
İngilizce ölçümde `absent` neredeyse kusursuzken `uncertain` zayıftı; çevirinin
en çok belirsizliği bozması beklenir ve bu **sınanabilir bir tahmindir**.

---

## 4. Ölçüm kümesi

| | |
|---|---|
| belge | **56** (RadTr `test`) |
| kelime | 7.784 |
| varlık | 1.817 |
| kesinlik desteği | present 613 · absent 86 · **uncertain 128** |

Bölünme ve kilit: `reports/turkce_bolunme_dondurma.md`

`uncertain` desteği İngilizce `test-v2`dekinden (69/82) **yüksek** — belirsizlik
ekseni Türkçede daha iyi ölçülebilir.

⚠ Varlıkların %54'ü kesinlik eksenine eşlenmiyor (RadTr `Obs_Anatomy` etiketine
kesinlik vermiyor). A2/A3 yalnızca eşlenen alt kümede ölçülür ve payda yazılır.

---

## 5. Ek kontrol — geri çeviri

Türkçe metin İngilizceye çevrilip **tekrar** Türkçeye çevrildiğinde çıkarımın ne
kadar saptığı ölçülür. Bu bir **stres ve normalizasyon kontrolüdür**; geçerlilik
kapısı değildir. İki çeviriden geçen metin daha kötü olmak zorunda değildir:
çeviri, betimleyici ifadeyi sözlüğün daha kolay yakaladığı standart terime
dönüştürebilir. Daha iyi sonuç ölçümü iptal etmez; normalizasyon örnekleriyle
raporlanır.

---

## 6. Yayımlanmış tabanla karşılaştırma

Türkçe varlık çıkarımında yayımlanmış bir taban skoru **bu bölünmede**
ölçülmüştür ve karşılaştırma yapılabilir.

⚠ İki uyarı:

1. **Taban öğrenen bir model, bizimki kural tabanlı.** Bu adil bir yarış değil,
   **farklı bir soru**. Sorulacak soru *"bizimki daha iyi mi"* değil,
   *"kural tabanlı katman öğrenen bir tabanla aynı bantta mı"*.
2. Bölünme birebir devralınamazsa yayımlanmış skorla **doğrudan** karşılaştırma
   yapılamaz; kendi bölünmemizde yeniden koşulur. Bu da mümkün değilse taban
   referans değil yalnızca **büyüklük mertebesi göstergesi** olarak anılır.

---

## 7. Yapılandırılmış model değerlendirmesi ve serbest yorum

İkincil model seçimi yalnız `train/dev`de, test sonucu görülmeden yapılır.
Qwen3.5-4B ana aday, Aya Expanse 8B zorunlu karşılaştırmadır; Qwen3-8B yalnız
Qwen3.5-4B çalışabilirlik veya kapalı çıktı kapısını geçemezse koşullu yedektir.
Kesin seçim kapıları ve sırası `docs/19_task15_deney_tasarimi_dondurma.md` §2'de
bağlayıcıdır.

Seçilip dondurulan tek model üç girdide aynı kavram envanteri, İngilizce
talimat, JSON şeması ve sabit decoding ile ayrı ayrı çalışır. Bu ikincil sayısal
değerlendirmedir; birincil dil kararını tek başına belirlemez.

Sonuç sayıları çıktıktan **sonra**, ayrışan belgeler bir modele hem Türkçe hem
İngilizce hâliyle verilip *"burada ne kaybolmuş"* diye sorulabilir. Bu ikinci
kullanım serbest hata analizidir.

| | |
|---|---|
| ✅ yapılandırılmış seçili model | ikincil skor ve model bağımlılığı kontrolü |
| ✅ serbest çift-dilli yorum | hata taksonomisi kurmak, hipotez üretmek |
| ⛔ serbest çift-dilli yorum | skor üretmek, sonuç iddia etmek |

---

## 8. Sonuç bir sayı değil, bir **karar**

Ablasyonun çıktısı şu sorunun cevabıdır:

> **Faz 3 altın standart etiketlemesi hangi dilde yapılacak?**

Karar tablosu — ölçümden **önce** donduruldu:

| bulgu | karar |
|---|---|
| EN, A1 + `present` + `absent` eksenlerinde TR'den 5 F1 puanından fazla düşük değil; %95 GA destekliyor | İngilizce etiketleme savunulabilir |
| TR, A1 veya `present`/`absent` ekseninde 5 puandan fazla ve güvenilir üstün | Türkçe etiketlemeye geçilir |
| TR belirgin **düşük** ama sebep desen zayıflığı | Uzman onaylı sözlükle **tekrar** ölçülür; karar ertelenir |
| Genel/tıbbi EN, dondurulmuş sistem/seçilen model veya eksenler çelişiyor | Tek karar verilmez; bağımlılık raporlanır |
| %95 güven aralığı 5 puanlık sınırı kesiyor | Kanıt yetersiz; tek dil kararı verilmez |

Fark `EN − TR` olarak tanımlanır. Belgeler 10.000 kez eşleştirilmiş bootstrap
ile örneklenir ve %95 güven aralığı hesaplanır. Pratik eşdeğerlik/kabul
edilebilir kayıp marjı `0,05` F1'dir.

⚠ Üçüncü satır önemli: Türkçe tarafın düşük çıkması tek başına *"Türkçe veri
gereksiz"* demek **değildir**. Desenler uzman onayından geçmediği sürece
düşüklüğün dilden mi araçtan mı geldiği ayrılamaz.

---

## 9. Bu ölçümü geçersiz kılacak şeyler

1. `test` bölümüne desen geliştirirken bakmak
2. Sonucu görüp desen/sözlük/kural değiştirmek → sürüm iptal, yeni bölünme
3. Türkçe ve İngilizce kolların **farklı** altın veriye karşı puanlanması
4. Serbest çift-dilli model yorumunun sonuç hanesine yazılması
5. Seçilen modelin dillerden birinde farklı istem, şema veya üretim ayarıyla koşulması

---

## 10. Bilinen sınırlar — rapora aynen geçer

| sınır | etkisi |
|---|---|
| RadTr **sentetik** (radyolog yazımı, gerçek hasta değil) | Sonuç *"RadTr benzeri Türkçe metinlerde"* diye yazılır |
| **56 belge** | Güven aralığı geniş; tek nokta tahmini sunulmaz |
| Türkçe yüzeyler **uzman onaysız** | Düşüklük dilden mi desenden mi ayrılamaz |
| Span sınırı ölçülmüyor | Belge düzeyi puanlamanın bilinen bedeli |
| **Hizalı çift yok** | RadTr'de aynı raporun insan yazımı Türkçe *ve* İngilizce hâli yok; İngilizce kol **makine çevirisi**. Çeviri hatası ile dil etkisi tam ayrılamaz — CT-RATE Türkçe aslı bu sınırı kaldırırdı |
