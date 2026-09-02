# TASK-15 · Uçtan Uca Eleştirel Denetim

**Tarih:** 2026-09-01  
**Denetim türü:** bağımsız uçtan uca inceleme  
**Durum:** **DURDURMA / düzeltme gerekli**  
**Test erişimi:** Bu denetimde RadTr `test.json` içeriği açılmadı  
**Model/çeviri:** Model indirilmedi, çeviri veya dış servis çağrısı yapılmadı

## 1. Yönetici özeti

TASK-15'in deney disiplini, kör paket ayrımı, kapalı kavram envanteri,
train/dev kapıları ve hash kayıtları doğru yönde. Ancak denetimde bir **P0
span-ofset sorunu** bulundu. Bu sorun çözülmeden mevcut `dev` normalizasyon
paketi, 150-span pilotu ve B ön-işaretlemesi yöntemsel olarak güvenilir kabul
edilemez.

Bu bulgu `test` açılmadan, model indirilmeden ve çeviri yapılmadan yakalandı.
Dolayısıyla geri döndürülemez bir sonuç üretilmedi. Eski artefaktlar silinmeyecek;
denetim izi olarak korunacak, fakat sonraki aşamalarda kullanılmayacak.

**Şimdilik yasak:** bağımsız A işaretlemesi, A/B uzlaştırması, gerçek çeviri,
model seçimi ve `test` paketleme.

## 2. P0 · RadTr span indeks semantiği kanıtlanmadan `-1` kaydırılmış

### Mevcut uygulama

`scripts/16_extract_radtr_thorax.py`, RadTr `[b, e, label]` indekslerini
1-tabanlı kabul edip şunu yapıyor:

```python
span_text = tokens[b - 1:e]
tok_bas = b - 1
tok_son = e - 1
```

Gerekçe olarak, iç noktalamayı azaltan `-1` kaymasının en düşük oranı verdiği
yazılmış. Bu ölçüt semantik doğruluk ölçütü değildir; spanı sola kaydırmak
cümle-sonu noktalamasını mekanik olarak azaltabilir.

### Resmî kaynakla çelişki

RadTr deposu standart DyGIE++ okuyucusunu değiştirmeden kullanıyor:

- [DyGIE++ veri formatı](https://github.com/dwadden/dygiepp/blob/master/doc/data.md)
  `ner` kayıtlarını belge düzeyinde `[start_tok, end_tok, label]` olarak
  tanımlar; örnekler 0'dan başlar ve son indeks kapsayıcıdır.
- [RadTr resmî veri okuyucusu](https://github.com/BIGDaTA-Lab-AI/dygiepp-multilingual-radiology/blob/main/dygie/data/dataset_readers/document.py)
  indeksleri doğrudan alır, yalnız cümle başlangıcını çıkarır ve metni
  `start:end + 1` dilimiyle üretir.
- [RadTr eğitim yapılandırması](https://github.com/BIGDaTA-Lab-AI/dygiepp-multilingual-radiology/blob/main/training_config/radtr.jsonnet)
  bu okuyucuyu ve `max_span_width: 4` ayarını kullanır.

Bu nedenle resmî benchmark semantiği **0-tabanlı, kapsayıcı** okumadır:

```python
span_text = tokens[b:e + 1]
tok_bas = b
tok_son = e
```

### `train/dev` üzerinde görülen etki

Aynı 150 pilot kimliği iki okumayla karşılaştırıldığında span metinlerinin
tamamı bir token yer değiştiriyor. Örnekler:

| etiket | mevcut `-1` | resmî `0` okuma |
|---|---|---|
| `Obs_Uncertain` | `açısından değerlendirme optimal` | `değerlendirme optimal yapılamamıştır.` |
| `Obs_Absent` | `artmıştır. Perikardiyal efüzyon` | `Perikardiyal efüzyon saptanmadı.` |
| `Differential Diagnosis` | `olup bronkopnömoni ile` | `bronkopnömoni ile uyumlu` |
| `Obs_Present` | `1 cmden küçük sayıda lenf` | `cmden küçük sayıda lenf nodu` |

Her iki okumada da bazı garip sınırlar var; RadTr altınının kendi span gürültüsü
bulunabilir. Fakat resmî biçimi tek taraflı bir noktalama sezgisiyle değiştirmek
benchmark uyumunu bozar. Kaynak Doccano export'u veya yazar doğrulaması olmadan
`-1` düzeltmesi savunulamaz.

### Karar

- Mevcut `data/processed/radtr_toraks_dev.jsonl`, `dev_packages`, 150-span
  pilot ve B v2 **silinmeyecek ama geçersiz/karantinada** sayılacak.
- Önce resmî 0-tabanlı semantik uygulanıp yeni sürüm adlarıyla `dev` paketleri
  üretilecek.
- Eski dosyaların üzerine yazılmayacak.
- En az 50 katmanlı `train/dev` spanı resmî okuma ile kaynak etiketi açısından
  insan gözüyle kontrol edilecek. Mümkünse özgün Doccano export'u veya veri
  yazarından indeks doğrulaması istenecek.
- Bu kontrol bitmeden A/B pilotu yeniden başlamayacak.

## 3. P0/P1 · “Test hiç açılmadı” ifadesi tarihsel olarak fazla güçlü

`reports/turkce_bolunme_dondurma.md`, TASK-14 öncesinde 429 belgenin tamamında
82 desenin toplam frekanslarının sayıldığını ve test bölümünün toplu
istatistiklerinin bilindiğini açıkça kaydediyor. Belge metinleri tek tek
incelenmemiş ve bu maruziyetin 72/82 kapsam sonucuna katkısı sıfır ölçülmüş.

Bu durum deneyi otomatik olarak iptal etmez; fakat doğru ifade şudur:

> TASK-15 sırasında yeni belge-düzeyi test incelemesi yapılmadı; TASK-14'ten
> kayıtlı, yalnız toplu frekans/sayım maruziyeti vardır ve etkisi sıfır ölçülmüştür.

Bundan sonra “test hiç açılmadı / sıfır maruziyet” yazılmamalı. `test.json`
belge içeriği yine tek kontrollü TASK-15 açılışına kadar okunmayacak.

## 4. P1 · Yayımlanmış 80,1 F1 doğrudan karşılaştırma değildir

[RadTr makalesi](https://www.dirjournal.org/articles/deep-learning-for-named-entity-recognition-in-turkish-radiology-reports/doi/dir.2025.243100)
1.056 rapor ve tüm yayımlanmış NER değerlendirmesini anlatıyor. Yerel resmî
depo ise proje kayıtlarına göre 1.364 rapor; bizim toraks filtremiz bunun 429
belgesini kullanıyor. Dolayısıyla yayımlanmış 80,1 F1:

- aynı kaynak bölünme adlarını kullansa bile aynı belge altkümesi değildir,
- aynı kapalı 144-kavram görevi değildir,
- resmî model `max_span_width=4` nedeniyle uzun altın spanları eğitim/ölçümde
  atlar.

`train+dev`de 31.847 anotasyonun **3.542'si (%11,12)** dört tokendan uzundur.
Oran `Obs_Technical` için %65,7, `Obs_Advice` için %58,1'dir.

**Karar:** 80,1 yalnız büyüklük mertebesi referansı olabilir. Doğrudan
karşılaştırma için resmî checkpoint'in bizim tam 429-belge/etiket kapsamımızda
yeniden koşulması ve uygun span paydasının açıkça eşlenmesi gerekir.

## 5. P1 · Uygulama sözleşmelerindeki açıklar

### Test erişim kapısı

`scripts/16_extract_radtr_thorax.py` argümansız çalışmıyor; bu iyi. Ancak
`--bolum test` ve `--bolum all` hâlâ açık. Yani ayrı tek-kullanımlık komut hazır
olmadan genel betik test verisini açıkça okuyabilir. TASK-15 geliştirme
sürümünde bu seçenekler kapatılmalı; test yalnız sonradan yazılacak özel komutta
açılmalı.

### Paket yazımı tam işlem atomikliği sağlamıyor

`write_package_pair` her dosyayı ayrı ayrı atomik yazıyor; fakat dört dosyanın
tamamı tek işlem olarak atomik değil. Süreç ortada kesilirse çeviri paketi var,
manifest/ledger yok biçiminde yarım çıktı kalabilir. Ledger tamamlanma işareti
olarak kullanılabilir, fakat docstring'teki “iki paketi atomik yazma” iddiası
fazla güçlüdür. Tek-kullanımlık test komutu geçici kardeş dizine yazıp tamamlanmış
dizini tek rename ile yayımlamalı.

### No-overwrite yarış koşulu

`_atomic_text`, önce `exists()` kontrolü yapıp sonra `os.replace()` çağırıyor.
İki eşzamanlı süreçte hedef arada oluşursa `os.replace` var olan dosyanın
üzerine yazabilir. Tek süreçte sorun yok; fakat “asla üzerine yazmaz” sözleşmesi
yarış altında doğru değil. `O_EXCL` veya aynı dosya sisteminde atomik hard-link
yayını kullanılmalı.

### Kör paket kapsamı

`write_package_pair`, normalizasyon belge kimliklerinin çeviri kimliklerinin
yalnız altkümesi olmasını kabul ediyor. Bu, bir belgenin bütün spanlarının
yanlışlıkla düşürülmesini sessizce kabul edebilir. Kaynakta sıfır-span belge
politikası önceden tanımlanmalı; mevcut RadTr kapsamında belge kümeleri eşit
olmalı ve kaynak span sayısı manifestte doğrulanmalı.

### Kilit provenance'ı

Genel A/B kilidi kör paket hash'ini kaydediyor; katalog, kılavuz, istem ve tam
model revizyonunu zorunlu manifest alanı yapmıyor. B için ek provenance dosyası
elle üretildi, fakat A komutu bunu otomatik zorlamıyor. A başlamadan:

- pilot manifesti,
- katalog hash'i,
- kılavuz hash'i,
- annotator model/ürün kimliği ve erişilebiliyorsa revision,
- kilitleme kodu hash'i

tek provenance kaydında zorunlu olmalı. Hizmet kesin revision göstermiyorsa
uydurulmamalı; “sağlayıcı tarafından açıklanmadı” diye yazılmalı.

## 6. P1/P2 · Puanlama ve karar edge-case'leri

1. `score_assertions` geçersiz assertion değerini şu anda sessizce hiçbir
   sınıfa saymayabilir. Skor öncesi kapalı assertion doğrulaması zorunlu olmalı.
2. Bootstrap temel `document_ids` listesinin tekilliğini denetlemiyor. Temel
   listede tekrar varsa örnekleme ağırlığı yanlış olur; yalnız bootstrap
   örneklemi içinde tekrar normaldir.
3. Model JSON'u aynı `(concept_id, assertion)` çiftini tekrar ederse kabul
   ediliyor. Puanlayıcı setle tekilleştireceği için yapısal hata gizlenir;
   doğrudan reddedilmeli.
4. A/B uzlaştırma sırası A dosyasının satır sırasına bağlı; kör paketin kanonik
   sırası kullanılmalı.
5. Karar kuralındaki “GA destekliyor” ifadesi matematiksel olarak dondurulmalı:
   non-inferiority için `EN−TR` alt sınırı `>-0,05`; Türkçe üstünlüğü için üst
   sınır `<-0,05` olmalı.
6. A1, present ve absent üç ana ekseninden “herhangi biri” ile karar vermek
   çoklu karşılaştırma riskini artırır. Noktasal %95 aralıklar yerine aile
   düzeyi eşzamanlı aralık veya önceden yazılmış muhafazakâr düzeltme gerekir.
7. Bootstrap örnekleminde bir sınıfın desteği sıfır olursa o iterasyondaki F1
   politikasının ne olduğu dondurulmalı; sessizce 0 yazmak ile iterasyonu
   tanımsız saymak farklı sonuç verir.

## 7. P1/P2 · Şema ve model çalıştırma edge-case'leri

- Protokoldeki JSON örneği `pulmonary_nodule` ve `pleural_effusion` kullanıyor;
  gerçek katalog kimlikleri `nodule` ve `effusion`. Prompt yazılmadan düzeltilmeli.
- RadTr kaynağında standart dokuz etikete ek yazım/şema dışı etiketler
  (`Obs_Critical`, `Obs_Insidental`) `train/dev` dış-toraks kayıtlarda görüldü.
  Test görülmeden “bilinmeyen etiket” politikası dondurulmalı. En güvenlisi:
  paketle, görünür `schema_unknown` olarak raporla, ana metrikten dışla; yeni
  kavrama veya assertion'a çevirmeme.
- Google adaptörü için ham sağlayıcı yanıtı, model kimliği, istek zamanı ve
  request ID; üretken modeller için revision, nicemleme, decoding, prompt hash'i
  henüz çalışma manifestinde zorunlu değil.
- MedGemma post-editinin sayı/birim, negasyon, belirsizlik ve bulgu
  ekleme-silme yasağı yalnız metin halinde. `dev`de otomatik sayı/birim koruma
  denetimi ve kör insan anlam-koruma kontrolü olmadan test post-editi hazır
  sayılmamalı.
- Aynı İngilizce istemi üç dil kolunda kullanmak girdi dilini daha iyi izole
  eder, fakat Türkçe kola yabancı-dil talimat yükü getirir. Sonuç “saf dil” değil
  “dondurulmuş pipeline dili” etkisi olarak yorumlanmalı.
- Türkçe sözlük RadTr `train/dev` üzerinde, İngilizce sözlük CT-RATE'in
  makine-çeviri artefaktları üzerinde geliştirilmiştir. Dil etkisi ile sözlük
  olgunluğu/veri kaynağı tam ayrılamaz; bu ana sınırlara eklenmeli.

## 8. Sağlam kalan kısımlar

- Çeviri paketi altın span/etiket taşımıyor; kör normalizasyon paketi sistem
  tahmini/çeviri taşımıyor.
- Pilot seçimi yalnız RadTr etiketi, sabit tohum ve belge sınırıyla yapıldı;
  metin veya sistem skoru seçime girmedi.
- 144-kavram kapalı katalog sistem yüzey/desen/frekansı taşımıyor.
- A/B tam kapsam ve farklı annotator denetimleri mevcut.
- Belge düzeyi set puanlama ve eşleştirilmiş bootstrap yönü `EN−TR` olarak
  doğru kurulmuş; yukarıdaki doğrulama/karar ayrıntıları eksik.
- Bu denetimde `test.json` içeriği, model çıktısı veya çeviri görülmedi.
- 271 test geçiyordu; fakat bu sayı semantik ofset hatasını yakalamadı, çünkü
  testlerin tamamı sentetikti ve resmî RadTr okuyucusuyla çapraz test yoktu.

## 9. Bundan sonraki güvenli sıra

1. **DUR:** A, uzlaştırma, çeviri, model ve test yok.
2. Resmî RadTr 0-tabanlı kapsayıcı semantiğe göre çıkarıcıyı düzelt; resmî
   okuyucuyla aynı spanı verdiğini regresyon testi yap.
3. Eski `dev` artefaktlarını koru ama `INVALID_OFFSET_MINUS1` olarak işaretle;
   yeni dosyaları sürümlü ayrı dizine üret.
4. 50+ katmanlı `train/dev` spanı insan gözüyle kontrol et; sınır gürültüsü ile
   kod hatasını ayır. Mümkünse özgün Doccano export/yazar teyidi al.
5. Test kapısı, atomik dizin yayını, provenance, kapalı etiket/assertion ve
   bootstrap edge-case düzeltmelerini sentetik + gerçek `dev` testleriyle kapat.
6. Yeni kör `dev` pilotunu üret; B'yi baştan, ardından bağımsız A'yı çalıştır.
7. Radyolog kılavuzu ve birleşik pilotun tamamını onaylasın; payda/istem/hash
   dondurulsun.
8. Ancak bundan sonra, kullanıcıya indirme ve çeviri komutları gösterilerek
   Google/MedGemma/TranslateGemma ve Qwen/Aya `dev` aşamasına geçilsin.
9. Kesin test komutu en son ayrıca gösterilsin.

## 10. Son hüküm

**Şu ana kadar yapılanlar kurtarılabilir ve denetim izi iyi; fakat mevcut
normalizasyon pilotu/B çıktısı üzerinden ilerlemek doğru değil.** En ciddi hata
testten önce yakalandı. Doğru sonraki adım model indirmek veya A'yı başlatmak
değil, span semantiğini resmî okuyucuyla düzeltip `dev` artefaktlarını yeniden
üretmektir.
