# Proje Durumu — nerede kaldık

**Son güncelleme:** 2026-09-03

Bu dosya sade bir takip listesidir. Ayrıntılı gerekçeler `docs/` ve `reports/`
altındadır; burada sadece **ne yapıldı, ne bulundu, ne bırakıldı, sırada ne var**
yazar.

---

## Şu an neredeyiz

Rapor metninden bulgu çıkarma katmanı **çalışıyor ve ölçüldü** (hem İngilizce hem
Türkçe). Dil kararı verildi: **Türkçe devam.** Şimdi bir üst katmana geçildi —
*"bu bulgular verildiğinde rapor malignite açısından hangi sınıfa düşer"*
sorusunu cevaplayan **karar şeması** yazılıyor (TASK-16).

---

## ✅ Tamamlananlar

### Veri hazırlığı
- ✅ Geliştirme ortamı ve proje iskeleti kuruldu
- ✅ CT-RATE veri erişimi alındı, rapor metinleri indirildi
- ✅ Rapor korpusu kuruldu — **25.692 çalışma / 21.304 hasta**
- ✅ Raporlar cümlelere bölündü — **479.051 cümle**, her cümle kaynak metindeki
  yerini taşıyor
- ✅ Şablon (kopyala-yapıştır) cümleler işaretlendi — korpusun **%71'i** şablon
- ✅ Ölçüler çıkarıldı — 50.513 ölçü (33.787 sayısal + 16.726 niteliksel)
- ✅ İnceleme araçları ve doğrulama testleri yazıldı

### Bulgu çıkarma
- ✅ Çıkarım şeması tanımlandı (hangi alan, hangi değer)
- ✅ Varlık ve ilişki çıkarımı yapıldı — anatomi, bulgu, niteleyici, cihaz
- ✅ Negasyon / belirsizlik / zaman katmanı kuruldu
- ✅ **Doğruluk elle ölçüldü** (iki bağımsız işaretleyici, kör küme):
  negasyon çözüldü (`absent` ~%100), `present` %97,5
- ✅ Türkçe hattı kuruldu ve ölçüldü — Türkçe olumsuzlama F1 **%90,3**

### Dil ablasyonu (TASK-15)
- ✅ Aynı raporun Türkçe aslı ile İngilizce çevirisi karşılaştırıldı
- ✅ **Karar: Türkçe devam.** Kapanış raporu yazıldı
- ✅ Test bölümü mühürlü bırakıldı, açma koşulu yazıldı

### Karar şeması (TASK-16) — devam ediyor
- ✅ Çalışma planı yazıldı, bağımsız denetimden geçirildi (25 bulgu, 21'i kabul)
- ✅ **Adım 0 — veri ikiye ayrıldı:** 17.000 hasta geliştirme, 4.304 hasta
  değerlendirme kilidi. Tekrar üretilebilir, üzerine yazılamaz, 9 otomatik testle
  bağlı
- ✅ **Adım 1 — karar sayısı ölçüldü:** 19 madde (10'u çekirdek). Tahmin değil,
  383.644 cümle taranarak sayıldı. Her madde için varsayılan karar ve gerekçesi
  yazıldı → `docs/31`
- ✅ **19 varsayılanın hepsi gerçek cümlelerle sınandı:** 3 madde düşürüldü
  (gerçek çelişki yokmuş), 4 varsayılan değişti, 6'sı doğrulandı
- ✅ **Adım 2 — kılavuzlar okundu, 35 kural aktarıldı.** Alan sözlüğü §12.2 (20),
  RECIST 1.1 (4), Lung-RADS v2022 (7), Fleischner 2017 (4). **Dört karar
  "bizim tahminimiz"den "kaynakta yazılı"ya taşındı**, biri düştü
- ✅ **Adım 3 — kuralların korpustaki karşılığı ölçüldü.** İki kural daha düştü.
  **Başlangıçtaki 19 madde 9'a indi**

---

## 🔍 Yol boyunca bulunanlar

Bunlar planlanmamıştı; ölçerken çıktı ve işi değiştirdi.

- 🔍 **Çeviri deterministik değil.** Aynı 46 rapor dakikalar arayla iki kez
  çevrildi, **5'i (%11) farklı çıktı.** Türkçe devam kararının en güçlü gerekçesi
  bu oldu — doğruluk değil, tekrarlanabilirlik.
- 🔍 **Ucuz çeviri pahalıya geliyor.** İyi çeviriye göre kavramların **%17'si**
  kayboluyor.
- 🔍 **Ders kitabının benign sözlüğü bu korpusta yok.** `popcorn kalsifikasyon`
  **0 kez** geçiyor. Bu korpusun benign sözcüğü **`sequela`** (12.177 kez).
- 🔍 **Çeviri artefaktları var.** `CTO` = Türkçe *"KTO"*nun harf çevirisi;
  İngilizce radyolojide böyle bir kısaltma yok. Hazır bir araç bunu yakalayamaz.
- 🔍 **Ölçüm aleti iki kez bozuk çıktı.** Sözlükte olmayan hatalar sözlük hatası
  gibi görünüyordu. Kural oldu: *önce aleti doğrula, sonra veriyi suçla.*
- 🔍 **Bu korpusta patoloji yok.** `biopsy` kelimesi 47.149 raporun **16'sında**
  geçiyor. Yani *"model gerçekte doğru mu"* ölçülemez; ancak *"model radyoloğun
  raporuyla uyuşuyor mu"* ölçülebilir.
- 🔍 **En tehlikeli vaka:** *"Stable, calcific parenchymal metastases"* — naif bir
  kural bunu iki kez benign sayar (kalsifiye + stabil), oysa **kanıtlanmış
  metastaz**. Korpusta sadece 24-40 cümle ama yanlış karar felaket.
- 🔍 **Kaynak belgede onay izi yok.** Alan sözlüğü belgesi taranınca imza, yazar
  veya gözden geçirme kaydı bulunamadı. Belge, atıf verdiği kılavuzlar ölçüsünde
  geçerli sayılıyor.
- 🔍 **"Negasyon varsa bulgu yoktur" kuralı yanlış.** *"**No** significant
  difference … in terms of … **metastases**"* cümlesinde olumsuzlanan şey
  **değişiklik**, metastaz **var**. Cümlede olumsuzluk kelimesi aramak gerçek
  metastazı siliyordu. Doğrusu: olumsuzluğun **neyi kapsadığına** bakmak.
- 🔍 **"Malignite + benign aynı cümlede, hangisi kazanır?" yanlış soruymuş.**
  Gerçek cümleler bakılınca ortada çelişki değil, radyoloğun **ilan ettiği
  belirsizlik** olduğu görüldü: *"malign-benign ayrımı yapılamadı"*,
  *"TB granülomu, pnömokonyoz **veya** malignite ile uyumlu olabilir"*.
  Taraf tutmak bilgiyi bozuyor; doğru cevap "karar verilemedi".
- 🔍 **Büyüme deseni fazla geniş.** *"density increase"* (dansite artışı) lezyon
  büyümesi sanılıyordu — 34.262 eşleşmenin **9.944'ü** böyle. Bu tek başına
  **üç karar maddesini düşürdü**: dar desenle bakınca *"büyüyen benign lezyon"*
  bu korpusta pratikte **yok** (1.780 sanılan sayı gerçekte 13).
- 🔍 **Büyüme ekseni bu korpusta YOK.** En büyük sürpriz. `enlarged` kelimesi
  burada *"büyümüş"* değil **"büyük"** demek — 14.378 eşleşmenin **12.233'ü**
  *"enlarged lymph node"*, üstelik çoğu olumsuzlanmış. Gerçek büyüme ifadesi
  383.644 cümlede **167 tane**. Beş karar maddesi bu yüzden düştü ve kılavuzun
  büyüme kuralları şemaya girmiyor.
- 🔍 **Korpusun dörtte birinde hiçbir kılavuz geçerli değil.** Fleischner
  *"35 yaş altına uygulanmaz"* diyor; korpusun **%24,5'i** 35 yaş altı.
  Lung-RADS ise tarama için. Bu bölgede şema yalnız kendi varsayılanlarıyla
  çalışacak ve bu raporda yazılı.
- 🔍 **Kılavuzun benign kalsifikasyon listesi korpusta yok.** *popcorn* 0,
  *central* 17, *concentric* 16 — toplam ~36 cümle. Ama genel *"kalsifik"*
  13.862 cümlede. Yani kalsifikasyon ifadelerinin **%99,7'si** kılavuzun benign
  tanımını karşılamıyor.
- 🔍 **İki kılavuz aslında çatışmıyor.** *"Hangisi öncelikli"* diye sormuştuk;
  Fleischner kendi metninde *"tarama için Lung-RADS'a bakın"* diyor. Kapsamlar
  ayrık, soru yanlış kurulmuştu.
- 🔍 **Belirsizlik sözlüğüm yanlıştı.** *"in favor of"* (Türkçe *"lehine"*)
  belirsizlik sandım — 9.481 eşleşmenin **6.720'si (%71)** buydu. Oysa proje
  bunu daha önce *"çıkarım ifadesi"* diye kaydetmişti: *"sekel lehine
  değerlendirilmiştir"* kararsızlık değil, **kararlı bir hüküm**.

---

## ❌ Denenip bırakılanlar

- ❌ **Geri çeviri** — İngilizceyi Türkçeye geri çevirip orijinali elde etmek.
  Çevirinin çevirisi orijinali getirmiyor.
- ❌ **Tıbbi çeviri düzeltici kolu (MedGemma).** Üç denemede de istenen çıktı
  biçimini tutturamadı (%0 → %57 → %12).
- ❌ **İkincil model doğrulaması.** Üç açık model denendi (Qwen3.5-4B, Aya
  Expanse 8B, Qwen3-8B), üçü de 144 kavramlık kapalı listeye uyamadı.
  Masabaşı analizle kanıtlandı: ayarları düzeltseydik de geçmezdi.
- ❌ **Lung-RADS kategorisi üretmek.** Kılavuzun dayandığı ölçüm ekseni bu
  korpusta yok.
- ❌ **RadTr test bölümünü açmak.** Mühürlü kaldı; açma koşulu yazılı.
- ❌ **UMLS/SNOMED erişimi.** Gerekmiyor, RadLex yeterli.
- ❌ **Sybil'in 27 özet alanı.** TASK-16 kapsamı dışına alındı, sonraya bırakıldı.
- ❌ **Klinik uzman onayı.** Alınmayacak. Sonucu: karar şemasının klinik dayanağı
  olmayacak ve bu raporda açıkça yazılacak.

---

## ⬜ Sırada olanlar

### Karar şeması (TASK-16) — devam
- ⬜ Adım 2 — kaynakta **yazılı olan** kuralların aktarılması (kılavuzlardan)
- ⬜ Adım 3 — korpus ölçümleri (hangi terim ne sıklıkta)
- ⬜ Adım 4 — **sınır vakası ve kontrol takımı**: gerçek cümleler seçilip
  kilitlenecek, kurallar yazılmadan **önce**
- ⬜ Adım 5 — girdi kalite filtresi (hatalı çıkarımlar rapor sınıfını yükseltmesin)
- ⬜ Adım 6 — **şemanın yazılması**
- ⬜ Adım 7 — Codex'le bağımsız kontrol
- ⬜ Adım 8 — gözle inceleme sayfası
- ⬜ Adım 9 — gerekçe belgesi

### Sonraki görevler
- ⬜ **TASK-17** — malignite ve benign gösterge sözlükleri
- ⬜ **TASK-18** — etiketleme kılavuzu ve altın standart alt küme
- ⬜ **TASK-19** — etiketleyici uyumu ve sınıf dengesi
- ⬜ **T-04** — malignite göstergelerinin modelle otomatik çıkarılması
- ⬜ **T-05 → T-07** — VLM karşılaştırması (3B BT görüntüsü gerekiyor)
- ⬜ **T-08 → T-10** — vaka düzeyinde malignite değerlendirmesi
- ⬜ **T-11 → T-12** — patoloji doğrulaması (serbest metin patoloji raporu
  gerekiyor; açık veride yok)
- ⬜ **T-13 → T-14** — nihai değerlendirme ve prototip

### Engelsiz ama yapılmamış
- ⬜ **RadLex eşlemesi** — API erişimi alındı ve test edildi. Yapılırsa TASK-11
  kapanır. Beklenen kapsama %67
- ⬜ **TASK-05'in kalan literatürü** — Lung-RADS 2022, Fleischner, Brock/Mayo.
  Hepsi ücretsiz erişilebilir
- ⬜ **NLST açık klinik verisinin içeriği** — indirilip kontrol edilecek; Faz 5'i
  etkiliyor

---

## Bilinen sınırlar

Bunlar gizlenmiyor, raporlara yazılı:

1. **Patoloji ground truth'u yok** — ölçülebilen şey rapor uyumu, klinik doğruluk
   değil
2. **Klinik uzman onayı olmayacak** — şema kararları belgelenmiş mühendislik
   varsayılanı kalacak
3. **Türkçe tarafta ikinci korpus yok** — RadTr tek kaynak
4. **Zaman ekseni zayıf** — geçmiş tetkik ayrımı F1 %36,4, eşiği geçemedi
5. **Kapsam toraks BT ile sınırlı** — başka bölge için yeniden türetilmesi gerekir
