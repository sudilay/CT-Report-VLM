# Proje Stratejisi — Veri, Dil ve Model Yol Haritası

**Tarih:** 2026-08-27 · **Durum:** öneri — onay bekliyor
**Tetikleyen:** CT-RATE'in Türkçe veri içermediğinin doğrulanması

---

## 1. Neyi yeniden kurguluyoruz ve neden

CT-RATE, **Türkçe veri içerdiği varsayımıyla** seçilmişti. Bu varsayım **yanlış**:
makale açıkça *"Only the English versions of these reports are included"* diyor.

Bu, projenin temelini yıkmıyor ama **rollerin yeniden dağıtılmasını** gerektiriyor.
Bu belge o dağıtımı tanımlar.

---

## 2. Elimizdeki varlıklar — doğrulanmış

| Kaynak | Dil | Gerçek mi | Ölçek | Görüntü | Etiket | Erişim |
|---|---|---|---|---|---|---|
| **CT-RATE** | İngilizce (TR'den Google Translate) | ✅ gerçek | 25.692 çalışma · 479.051 cümle | ✅ **3B hacim** | 18 anormallik (otomatik) | ✅ elimizde |
| **RadTr** | **Türkçe** | ❌ sentetik (radyolog yazımı) | 1.056 rapor | ❌ | ✅ **9 varlık etiketi** | GitHub, MIT |
| **PARROT** | **Türkçe** + 13 dil | ❌ kurgusal | 2.658 (TR payı küçük) | ❌ | ICD-10 | GitHub, CC-BY-NC-SA |
| **Alan sözlüğü belgesi** | **Türkçe** | — | 360 ifade · ~250 alan | — | hedef şema | ✅ elimizde |
| **Sağlık Bakanlığı verisi** | **Türkçe** (?) | ✅ gerçek | ? | ? | ? | ⏳ netleşmedi |
| **NLST** | İngilizce | ✅ gerçek | ? | ✅ | patoloji sonucu | ⏳ netleşmedi |

**Hiçbiri tek başına yeterli değil. Birlikte yeterliler.**

---

## 3. Rol dağıtımı

### CT-RATE — kalır, rolü daralır

| Kalır | Kalmaz |
|---|---|
| **Faz 5 — 3B görüntü benchmark.** 3B göğüs BT'yi serbest metin raporla eşleştiren **ilk ve en büyük** açık set; ReXGroundingCT, RadGenome-Chest CT, CTRATE-IR hepsi onun üstüne kurulmuş. **Pratik alternatifi yok.** | Türkçe dil korpusu — hiç değildi |
| **Ölçek.** 479.051 cümle — sözlük madenciliği ve yöntem geliştirme için gerekli hacim. RadTr'ın 1.056 raporu buna yetmez. | Teslim edilecek sistemin veri kaynağı |
| **Kavram envanteri.** İçerik Türk klinik pratiğini yansıtıyor (Medipol). | Patoloji ground truth |

### Türkçe kaynaklar — dört parça, tek iş

Türkçe sözlüğü kurmak ve doğrulamak için birbirini tamamlıyorlar:

| Kaynak | Rolü | Neden başkası yapamaz |
|---|---|---|
| **Alan sözlüğü belgesi §12.1** | **Tohum** — 18 alan × 20 Türkçe ifade | Uzman derlemesi; korpustan çıkarılamaz |
| **PARROT** | **Eşleme haritası** — aynı raporun TR + EN hâli | *"Bizim `in favor of` Türkçede ne?"* sorusunun tek doğrudan cevabı |
| **RadTr** | **Altın set** — 9 etiketli 1.056 toraks BT raporu | Türkçe sözlüğün kesinlik/duyarlılığını ölçebilecek tek etiketli kaynak |
| **Uzman (Zeynep hoca)** | **Doğrulama** | Klinik yargı veriden türetilemez |

---

## 4. Önerilen sıra

| # | Aşama | Veri | Yöntem | Çıktı |
|---|---|---|---|---|
| 1 | **TASK-13** (şimdi) | CT-RATE EN | kural tabanlı | Mevcut çıkarımın doğruluğu — **yöntem doğrulanır** |
| 2 | **Dil geçişi** | belge + PARROT + RadTr | sözlük yazımı | `*_sozlugu_tr.yaml` · RadTr üzerinde ölçüm |
| 3 | **Faz 3** | ⚠ **karar noktası** | altın standart etiketleme | Proje bu noktada bir dile **bağlanır** |
| 4 | **Faz 4** | metin | LLM karşılaştırması (+ BioBERTurk tabanı) | Model başarımları |
| 5 | **Faz 5** | **CT-RATE zorunlu** | 3B VLM | Görüntü benchmark |
| 6 | **Faz 6** | — | karar kuralları | Vaka düzeyi malignite kararı |
| 7 | **Faz 7** | SB verisi / NLST | patoloji çıkarımı (belge §15 şeması) | Ground truth |

### ⚠ Neden dil geçişi Faz 3'ten ÖNCE

Faz 3 **altın standart etiketleme** üretiyor. O etiketleme hangi dilde yapılırsa proje
**o dile bağlanır** — sonraki her metrik, her karşılaştırma, her eşik o kümeye dayanır.

Yanlış dilde altın standart üretmek, sonradan **tamamının yeniden etiketlenmesi**
demektir. Bu, projenin en pahalı geri dönüşü olur.

TASK-13'ü İngilizce bitirmek mantıklı çünkü **yöntemi** doğruluyor ve neredeyse bitmiş
durumda. Ama Faz 3'e girmeden önce dil kararı verilmiş olmalı.

---

## 5. Model tarafı

| Faz | Yöntem | Gerekçe |
|---|---|---|
| Faz 2 (EN ve TR) | **Deterministik kural tabanlı** | D15 — Faz 4 LLM'leri değerlendirecek; referans katman LLM olamaz (döngüsellik) |
| Faz 2-TR karşılaştırma | **BioBERTurk** | RadTr üzerinde yayımlanmış taban: **F1 80,1**. Karşılaştırma tabanı, referans değil |
| Faz 4 | LLM'ler (metin) | Asıl karşılaştırma |
| Faz 5 | 3B VLM (CT-CLIP, Merlin, RadFM…) | TASK-03'ün açık kararı; donanım kısıtı 8 GB VRAM |
| Faz 6 | Kural tabanlı karar katmanı | Model değil — kanıt birleştirme |

---

## 6. Taşınan ve taşınmayan

| Taşınır | Taşınmaz |
|---|---|
| Mimari · şema (`sema-1.2`) · D1–D26 kararları | 366 desen |
| Yöntem: önce ölç, ipucu kapsamı, izlenebilirlik | Tüm ölçülmüş sayılar (%71 kalıp, %19,9 ardıl…) |
| 131 kavramlık envanter (kimlikler dilden bağımsız) | Cümle bölütleyici (PyRuSH İngilizce kurallı) |
| **Sınır durum kataloğu** — tuzaklar iki dilde de aynı | |
| Kabul ölçütü ve değerlendirme disiplini (D26) | |

Sınır durumların taşınması özellikle önemli: belgenin *"Kritik kural 1"*i
(**"dışlanamaz" → uncertain**) bizim K11 ölçütümüzle aynı. **Mantık taşınıyor,
yalnızca tetikleyen kelimeler değişiyor.**

---

## 7. Bir asimetri — Türkçe tarafta ölçüm zemini daha iyi

**Türkçede etiketli altın set var (RadTr). İngilizcede yok.**

TASK-13'te İngilizce altın açıklamayı kendimiz üretiyoruz. Türkçede RadTr hazır bir
değerlendirme zemini **ve yayımlanmış bir taban skor** veriyor.

Yani Türkçeye geçmek ölçüm açısından **daha iyi** bir konum.

---

## 7-B. ⚠ RadTr indirildi ve incelendi — beklenenden zayıf

Veri `data/external/radtr/` altında. **Ölçüm sonuçları:**

| | |
|---|---|
| Belge | **1.364** (train 1.057 · dev 132 · test 175) |
| Token · varlık | 155.845 · 36.520 |
| **İlişki** | **0** — yalnızca varlık |
| **Başlıkta toraks/akciğer geçen** | **442 (%32,4)** — 60.628 token |

### Sorun 1: Tetkik bağlamı bizimkiyle uyuşmuyor

Toraks belgelerinin tamamına yakını **ACİL** tetkik:
`ACİL KONTRASTSIZ TORAKS BT` 236 · `ACİL PULMONER BT ANJİYOGRAFİ` 123 ·
`ACİL TORAKS BT` 43 · `TORAKOABDOMİNAL AORTA ANJİYOGRAFİ` 26.

Konu dağılımı (442 toraks belgesi içinde):

| Konu | RadTr | CT-RATE (karşılaştırma) |
|---|---|---|
| nodül | %37,8 | **%70,1** |
| kitle | %4,1 | %49,4 |
| malignite/kanser | %4,8 | %4,9 |
| **spikülasyon** | **3 belge (%0,7)** | 134 çalışma |
| emboli | **%19,7** | %0,2 |
| travma | **%14,9** | %6,5 |
| pnömotoraks | %9,5 | — |
| efüzyon · pnömoni | %82,8 · %79,6 | — |

**RadTr acil/travma/emboli ağırlıklı; bizim konumuz insidental nodül ve malignite.**
Spikülasyon — malignitenin en değerli göstergesi — **üç belgede** geçiyor.

### Sorun 2: Açıklama kalitesi düzensiz

- **Span kayması var.** `[b-1:e]` okuması `[b:e+1]`den belirgin daha tutarlı
  (anatomi eşleşmesi %42,9 vs %28,7). Altın set olarak kullanılmadan önce
  hizalama düzeltilmeli.
- **Etiket seti düzensiz:** `Symptom_A` 13, `Obs_Critical` 2, `Obs_Insidental` 1 —
  makalede 9 etiket deniyor, veride 11 var ve üçü neredeyse boş.
- Gözle bakıldığında bazı etiketler açıkça yanlış (`Symptom_P` → *"TEKNİK: Acil"*,
  `Differential Diagnosis` → *"Ulna orta"*).
- **Sentetik** — radyolog yazımı, gerçek hasta raporu değil.

### Sonuç: RadTr korpus değil, SÖZLÜK TOHUMU

| Ne için **kullanılabilir** | Ne için **kullanılamaz** |
|---|---|
| **Gerçek Türkçe radyoloji ifadesi kaynağı** — 60.628 token toraks metni | Proje korpusu |
| Sözlüğün kaba bir aklıselim kontrolü | **Altın standart** (hizalama + etiket sorunları) |
| Negasyon/belirsizlik kalıplarının Türkçe karşılıkları | Malignite/nodül dili ölçümü (spikülasyon 3 belge) |

**Kritik yol netleşti: gerçek Türkçe toraks BT raporları (Sağlık Bakanlığı verisi)
olmadan Faz 3'e girilemez.**

---

## 8. Karar bekleyen sorular

1. **Teslim edilecek sistem hangi dilde çalışacak?** — Her şey buna bağlı
2. **Sağlık Bakanlığı verisi Türkçe mi, ne zaman gelecek?**
3. **Faz 3'ün altın standardı hangi dilde etiketlenecek?** — geri dönüşü en pahalı karar
4. **Sybil ne rol oynuyor?** — alan sözlüğü belgesinin alt başlığı
5. **CT-RATE'in Türkçe orijinalleri Medipol'den talep edilebilir mi?**
