# TASK-15 · Span→Kanonik Kavram Normalizasyon Kılavuzu

**Sürüm:** 0.1 taslak  
**Tarih:** 2026-09-01  
**Kapsam:** RadTr `train/dev` pilotu; `test` için henüz dondurulmadı  
**Uzman onayı:** Yok

Bu kılavuz, RadTr'nin altın Türkçe span'larını kapalı 144 `concept_id`
envanterine bağımsız biçimde eşlemek içindir. Sistem tahmini üretmez ve hasta
tanısı vermez. Nihai çıktı yalnız raporun ne söylediğine ilişkin radyolog-onaylı
rapor-anlamı altınının ön işaretlemesidir.

Katalog: `configs/task15_kavram_katalogu.yaml`. Katalog yalnız kimlik, tür ve
kısa iki dilli ad taşır; regex, frekans ve span başına otomatik eşleşme içermez.

## 1. İşaretleyicinin göreceği veri

Her satırda yalnız şunlar bulunur:

```text
document_id · span_id · sentence_text · span_text · radtr_label
```

İşaretleyici şunları görmez:

- Türkçe veya İngilizce sözlük eşleşmesi,
- çeviri,
- birincil sistem tahmini,
- Qwen/Aya veya başka model çıktısı,
- diğer bağımsız işaretleyicinin cevabı,
- skor veya altın anahtar.

## 2. Yazılacak alanlar

| alan | kural |
|---|---|
| `concept_ids` | katalogdaki sıfır, bir veya birden çok kimlik; tekrar yok |
| `mapping_status` | `mapped`, `unmapped`, `needs_adjudication` |
| `annotator_id` | dosya boyunca tek ve değişmez kimlik |
| `note` | yalnız `unmapped`/ayrışma gerekçesi; kısa ve metne dayalı |

- `mapped`: en az bir `concept_id` zorunlu.
- `unmapped`: `concept_ids` boş olmalı; katalogda doğru karşılık yoktur.
- `needs_adjudication`: iki makul kanonik okuma veya kural boşluğu vardır;
  olası kimlikler verilebilir. Bu durum klinik `uncertain` anlamına gelmez.

Kaynak kimlik, cümle, span ve RadTr etiketi değiştirilmez. Bir satır bile
atlanamaz; A/B kilidi kör paketin tam anahtar kümesini denetler.

## 3. Temel karar sırası

1. Önce yalnız `span_text`in rapor bağlamındaki anlamını oku.
2. `radtr_label`ı değiştirilecek bir tahmin değil, span'ın özgün tür/kesinlik
   bilgisi olarak koru.
3. Katalogda anlamı doğrudan karşılayan en özgül kanonik kimliği seç.
4. Span açıkça birden fazla bağımsız katalog kavramı taşıyorsa hepsini yaz.
5. Metnin söylemediği hastalık, organ, malignite veya nedensellik çıkarımı yapma.
6. Doğru karşılık yoksa yeni kimlik uydurma; `unmapped` bırak.
7. İki kural gerçekten çatışıyorsa tahmin etme; `needs_adjudication` kullan.

## 4. Özgüllük ve bileşik spanlar

### En özgül kapalı kavram kazanır

Katalogda bütün ifadeyi karşılayan tek bir kavram varsa sözcük parçaları ayrıca
eklenmez.

| span anlamı | yaz | ayrıca yazma |
|---|---|---|
| nodüler lezyon | `nodular_lesion` | `nodule`, `lesion` |
| septal kalınlaşma | `septal_thickening` | `thickening` |
| yer kaplayan lezyon | `space_occupying_lesion` | `lesion` |
| yumuşak doku dansitesi | `soft_tissue_density` | `soft_tissue`, `density` |
| küçük hava yolu hastalığı | `small_airway_disease` | `airway` |

Bu kural, aynı kavramı bileşenleri üzerinden iki kez saymayı engeller.

### Birden çok açık kavram

Span gerçekten iki bağımsız anlam taşıyorsa liste kullanılır:

| span anlamı | `concept_ids` |
|---|---|
| kalsifiye nodül | `calcific`, `nodule` |
| buzlu cam nodülü | `ground_glass`, `nodule` |
| nekrotik kitle | `necrotic`, `mass` |
| spiküle solid lezyon | `spiculated`, `solid`, `lesion` |

Bir sıfat yalnız başına RadTr span'ıysa yalnız niteleyici kimliği yazılır.

### Birleşik ile koordinasyon aynı değildir

- Tek kanonik birleşik ifade *“efüzyon-kalınlaşma”* ise
  `effusion_thickening`.
- İki ayrı bulgu *“efüzyon ve plevral kalınlaşma”* ise `effusion`, `thickening`.

Bu ayrım pilotta örneklerle sınanacak; ayrışma yüksekse kural revize edilip yeni
taslak hash'i yazılacaktır.

## 5. Metnin söylemediğini eklememe kuralları

- `mass`, `tumor`, `lesion` ve `nodule` birbirinin eş anlamlısı sayılmaz.
- `malign`, `şüpheli` veya takip önerisi tek başına `tumor`/`metastasis` üretmez.
- `cardiothoracic_ratio` kardiyomegali değildir. *“KTO artmış”* yalnız oranı;
  açık kalp büyüklüğü ifadesi `cardiomegaly`yi karşılar.
- Çıplak `density` → `density`; yalnız açık artış → `density_increase`.
- Çıplak `parenchyma` → `parenchyma`; organ açıkça akciğerse
  `lung_parenchyma`.
- Çıplak `segment` → `anatomic_segment`; organ bağlamdan tahmin edilmez.
- `calcification` adlandırılmış bulgudur; `calcific` başka bir bulgunun
  kalsifik niteliğidir.
- `sequela_change` bulgu; `sequela` niteleyicidir.
- `lung_apex` anatomik yapı; `apical` konum niteleyicisidir.
- `lymph_node` anatomidir; açık büyüme/patoloji
  `enlarged_lymph_node` gözlemidir.
- `soft_tissue` anatomi; `soft_tissue_density` gözlemdir.
- Cihaz adı açık değilse görüntü artefaktından cihaz çıkarımı yapılmaz.

## 6. Betimleyici Türkçe ifadeler

Normalizasyon yüzey eşitliği değildir. Span katalog terimini kelimesi kelimesine
kullanmadan aynı anlamı açıkça söylüyorsa kanonik kimliğe eşlenir:

- *kalp boyutlarında artış* → `cardiomegaly`,
- *karaciğerde yağlanma* → `hepatosteatosis`,
- *safra kesesinde taş* → `cholelithiasis`,
- *böbrek taşı* → `nephrolithiasis`.

Ancak bu eşleme açık rapor anlamına dayanır; dolaylı klinik çıkarım yapılmaz.

## 7. Kesinlik ve RadTr etiketi

İşaretleyici assertion üretmez; özgün `radtr_label` korunur. Kanonik kavramla
birleşen assertion daha sonra dondurulmuş tabloda türetilir:

| RadTr etiketi | assertion adayı |
|---|---|
| `Obs_Present` | `present` |
| `Obs_Absent` | `absent` |
| `Obs_Uncertain` | `uncertain` |
| `Differential Diagnosis` | `uncertain` |
| `Obs_Anatomy` | yok; yalnız A1 |

D30 korunur: `Obs_Technical` klinik `uncertain`a çevrilmez. `Obs_Advice`
kesinliği değiştirmez.

## 8. Payda kapsamı — dondurma önerisi, henüz karar değil

Paketin **1.490 span'ının tamamı** işaretlenir ve radyolog kontrolüne girer.
Ana metrik kapsamı için yöntemden türetilen öneri:

| RadTr etiketi | A1 | A2/A3 | gerekçe |
|---|---:|---:|---|
| `Obs_Anatomy` | evet | hayır | anatomi kavramdır; assertion yoktur |
| `Obs_Present/Absent/Uncertain` | evet | evet | ana gözlem eksenleri |
| `Differential Diagnosis` | evet | evet, `uncertain` | kaynak eşleme kararı |
| `Obs_Technical` | hayır | hayır | D30 ayrı eksen |
| `Obs_Advice` | hayır | hayır | öneri bulgu kesinliği değildir |
| `Symptom_P/Symptom_A` | hayır | hayır | kapalı envanter radyolojik bulgu/anatomi odaklıdır |

Bu tablo sonuç görülerek seçilmedi; şema ve deney sorusundan türetildi. Yine de
bağlayıcı hâle gelmeden önce radyolog onayı gerekir. Pilot raporu bütün etiket
desteklerini ve `mapped/unmapped` oranlarını ayrıca gösterecek; dışlanan satırlar
gizlenmeyecektir.

## 9. Bağımsızlık ve kilitleme

1. A ve B aynı kör paketi, katalogu ve bu kılavuzu alır.
2. Birbirinin dosyasını veya ara sonucunu görmez.
3. Her çıktı tam kapsam doğrulamasından sonra ayrı SHA-256 ile kilitlenir.
4. Tam eşleşme/ayrışma otomatik hesaplanır.
5. Radyolog yalnız ayrışmaları değil birleşmiş listenin tamamını onaylar.
6. Kılavuz değişirse yalnız `train/dev`de yeni sürüm ve hash üretilir.
7. Testte yeni kavram veya kural eklenmez.

## 10. Pilot kabul kaydı

Henüz doldurulmadı. Pilot tamamlanınca en az şunlar yazılacak:

- işaretlenen span sayısı ve etiket dağılımı,
- tam A/B eşleşme oranı,
- `mapped/unmapped/needs_adjudication` sayıları,
- bileşik span sayısı,
- ayrışma taksonomisi,
- radyologca değiştirilen tam eşleşme ve ayrışma sayısı,
- katalog/kılavuz/istem/model sürümü ve SHA-256 değerleri.
