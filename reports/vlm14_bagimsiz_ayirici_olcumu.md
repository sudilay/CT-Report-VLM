# Astra Bölüm Ayırıcısının Bağımsız Ölçümü

**Tarih:** 2026-09-08  
**Kapsam:** 2.965 Astra raporu  
**Kaynak SHA-256:** `d666d9f3b920a26ed0153dc61908b0eccfcc33cf2cacb7a4606cd3a2d4264125`  
**Kapı sonucu:** **KALDI**

## 1. Bağımsızlık beyanı

Ön kayıtlı sayılar ölçümden önce görülmüştür: `docs/38` önceki incelemede
okunmuş, ayrıca iş emri sayıları doğrudan vermiştir. Önceki ayırıcı ve
`docs/39_astra_veri_sozlesmesi.md` açılmamış, kodu kullanılmamıştır.
Ölçüm yalnız `Seri_Anahtari` ve `Radyoloji_Raporu` kolonlarından bağımsız
olarak yazılan ayırıcıyla yapılmıştır. Etiket, takip ve model skoru
kolonları yüklenmemiştir.

## 2. Yöntem

Ayırıcı iki yapıyı başlık kabul eder: Markdown `#` başlıkları ve satır
başında bulunan, iki noktayla biten kalın etiketler. Büyük/küçük harf,
numaralandırma, fazla boşluk ve sondaki noktalama normalleştirilir; eş
anlamlı başlıklar birleştirilmez. Kalın rapor adları iki nokta veya
Markdown başlık işareti taşımıyorsa bölüm sayılmaz.

İç içe yapılarda içerik **en yakın başlığa** bağlanır. Alt başlık metni
ebeveyn başlığa miras verilmez. Böylece `Lung > Right Lung` yapısında sağ
akciğer metni `right lung` bölümüne aittir.

`normal`, incelenen bütün kullanımlarda organ başlığı altındaki madde
işaretli durum/değer etiketidir; yapısal bölüm başlığı sayılmamıştır.

Ölçü deseni sayısal `mm`/`cm` ifadelerini yakalar. Teknik satır yalnız
`slice/section thickness`, `reconstruction thickness/interval`, `slice
interval` veya `collimation` açık bağlamlarından biri varsa teknik kabul
edilir; çıplak `interval` klinik büyüme karşılaştırmasını korumak için
teknik sayılmaz. Teknik satırlar çıkarıldıktan sonra kalan her sayısal
`mm`/`cm` ifadesi, bu denetimde doku ölçüsü için operasyonel karşılıktır.

## 3. Başlık envanteri

Farklı normalize başlık: **384**  
Başlıksız rapor: **79 (%2,7)**

| sıra | başlık | geçiş | rapor |
|---:|---|---:|---:|
| 1 | `pleura` | 2.910 | 2.862 |
| 2 | `esophagus` | 2.898 | 2.868 |
| 3 | `heart` | 2.886 | 2.869 |
| 4 | `breast` | 2.881 | 2.868 |
| 5 | `lung` | 2.881 | 2.869 |
| 6 | `mediastinum` | 2.881 | 2.862 |
| 7 | `abdomen` | 2.880 | 2.868 |
| 8 | `bone` | 2.880 | 2.868 |
| 9 | `thyroid` | 2.869 | 2.853 |
| 10 | `trachea and bronchie` | 2.850 | 2.837 |
| 11 | `conclusion` | 2.286 | 2.109 |
| 12 | `patient information` | 1.362 | 1.362 |
| 13 | `recommendations` | 1.122 | 1.122 |
| 14 | `note` | 779 | 763 |
| 15 | `imaging details` | 744 | 744 |
| 16 | `prepared by` | 701 | 701 |
| 17 | `findings` | 676 | 486 |
| 18 | `abnormalities` | 547 | 341 |
| 19 | `left lung` | 482 | 441 |
| 20 | `right lung` | 481 | 440 |
| 21 | `summary` | 440 | 440 |
| 22 | `image description` | 417 | 417 |
| 23 | `report prepared by` | 402 | 402 |
| 24 | `date` | 325 | 325 |
| 25 | `region analysis` | 266 | 266 |
| 26 | `region-by-region analysis` | 210 | 210 |
| 27 | `imaging modality` | 156 | 156 |
| 28 | `important note` | 155 | 155 |
| 29 | `chest ct image analysis` | 141 | 141 |
| 30 | `trachea` | 121 | 118 |
| 31 | `chest ct scan report` | 105 | 105 |
| 32 | `imaging technique` | 103 | 103 |
| 33 | `bronchi` | 99 | 95 |
| 34 | `reviewed by` | 87 | 87 |
| 35 | `date of examination` | 86 | 86 |
| 36 | `disclaimer` | 82 | 82 |
| 37 | `diagnosis` | 69 | 69 |
| 38 | `bronchie` | 57 | 57 |
| 39 | `chest ct report` | 44 | 44 |
| 40 | `pleural effusion` | 43 | 39 |

## 4. `normal` kararı

| konum/biçim | sayı |
|---|---:|
| Yapısal başlık | 0 |
| Değer konumu. toplam | 7.050 |
| İki noktalı kalın değer | 5.968 |
| Noktalı kalın değer | 1.075 |
| Yalın kalın değer | 7 |

Bütün eşleşmeler madde işaretli satırdadır. Bu nedenle `normal`ın bölüm
değil değer olduğu kararı veri düzeniyle tutarlıdır.

## 5. Akciğer dışı bölüm kirliliği

| bölüm | malignite sözcüğü geçen rapor | oran |
|---|---:|---:|
| `breast` | 1.771 | %59.7 |
| `thyroid` | 1.701 | %57.4 |
| `abdomen` | 386 | %13.0 |
| `bone` | 1.269 | %42.8 |
| `esophagus` | 704 | %23.7 |
| `heart` | 1.220 | %41.1 |
| **En az biri** | **2.491** | **%84.0** |

Sayılar yalnız hedef başlığın en yakın-başlık yöntemiyle belirlenen kendi
içeriğine aittir; olumsuz cümleler iş emri gereği ayrılmamıştır.

## 6. Özet bölümü sızıntısı

| bölüm | bölüm bulunan rapor | aynı cümlede organ + malignite |
|---|---:|---:|
| `conclusion` | 2.109 | 10 |
| `abnormalities` | 341 | 1 |
| `findings` | 486 | 12 |

## 7. Teknik parametre ve ölçü

| ölçüm | rapor | oran |
|---|---:|---:|
| Sayısal `mm`/`cm` ölçüsü | 222 | %7.5 |
| Bunların içinde teknik parametre satırı | 125 | %4.2 |
| Teknik satırlar çıkarılınca ölçüsü kalan | 97 | %3.3 |
| Aynı cümlede nodül + ölçü | 37 | %1.2 |

## 8. Ön kayıtla karşılaştırma

| ölçüm | ön kayıt | bağımsız | bağıl fark | durum |
|---|---:|---:|---:|---|
| Farklı başlık | 353 | 384 | %8.8 | ✅ |
| `normal` değer konumu | 5.975 | 7.050 | %18.0 | ✅ |
| Başlıksız rapor | 123 | 79 | %35.8 | ❌ |
| Akciğer dışı. en az biri | 1.679 | 2.491 | %48.4 | ❌ |
| Meme | 1.052 | 1.771 | %68.3 | ❌ |
| Kemik | 1.023 | 1.269 | %24.0 | ❌ |
| Tiroid | 1.003 | 1.701 | %69.6 | ❌ |
| Kalp | 946 | 1.220 | %29.0 | ❌ |
| Özofagus | 502 | 704 | %40.2 | ❌ |
| Abdomen | 343 | 386 | %12.5 | ✅ |
| Conclusion var | 1.872 | 2.109 | %12.7 | ✅ |
| Conclusion sızıntı | 8 | 10 | %25.0 | ❌ |
| Abnormalities var | 341 | 341 | %0.0 | ✅ |
| Abnormalities sızıntı | 4 | 1 | %75.0 | ❌ |
| Findings var | 482 | 486 | %0.8 | ✅ |
| Findings sızıntı | 14 | 12 | %14.3 | ✅ |
| mm/cm geçen rapor | 222 | 222 | %0.0 | ✅ |
| Teknik parametreli | 175 | 125 | %28.6 | ❌ |
| Teknik temizlik sonrası ölçü | 91 | 97 | %6.6 | ✅ |
| Aynı cümlede nodül + ölçü | 37 | 37 | %0.0 | ✅ |

## 9. Ayrışma incelemesi

### 9.1 Başlıksız rapor tanımı

| Markdown başlığı | İki noktalı kalın başlık | rapor |
|---|---|---:|
| yok | var | 1.986 |
| var | var | 686 |
| var | yok | 214 |
| yok | yok | 79 |

Bağımsız ayırıcı standart Markdown `#` başlıklarını bölüm sınırı kabul
etti. **214 rapor yalnız bu sözdizimiyle bölüm taşıyor.** Bunları
başlıksız saymak için geçerli Markdown başlıklarını dışlamak gerekir;
bu nedenle 123 sayısı mevcut başlık tanımıyla yeniden üretilemedi.

### 9.2 `normal` değer satırlarının etkisi

| bölüm | toplam | `normal` satırında | diğer satırda | ön kayıt |
|---|---:|---:|---:|---:|
| `breast` | 1.771 | 632 | 1.139 | 1.052 |
| `thyroid` | 1.701 | 611 | 1.090 | 1.003 |
| `abdomen` | 386 | 25 | 361 | 343 |
| `bone` | 1.269 | 203 | 1.066 | 1.023 |
| `esophagus` | 704 | 160 | 544 | 502 |
| `heart` | 1.220 | 199 | 1.021 | 946 |

`normal` satırları dışlandığında birleşim **1.802** olur; ön kayıt 1.679'a göre bağıl fark %7,3'tür.
Bu satırları ekleyen 691 raporun yalnız 2'si başka bir hedef bölümde de eşleşir.
Farkın ana nedeni, `normal` değerinden sonra gelen olumsuz malignite
ifadeleridir. Örnek: `**Normal:** No masses, calcifications, or
asymmetries observed.` İş emri olumsuz cümleleri ayırmamayı istediğinden
bu içerikler bağımsız sayımdan çıkarılamaz.

### 9.3 Özet bölümlerinde sınır ve cümle etkisi

| bölüm | aynı cümle | aynı satır | bölümün herhangi yerinde | ön kayıt |
|---|---:|---:|---:|---:|
| `conclusion` | 10 | 36 | 38 | 8 |
| `abnormalities` | 1 | 1 | 1 | 4 |
| `findings` | 12 | 15 | 15 | 14 |

`abnormalities` için aynı satır ve bütün bölüm kontrolleri de 1 rapor
verdi. Ön kayıttaki 4, en yakın başlık sınırıyla üretilemedi; olası neden
alt başlık içeriğinin ebeveyn bölüme taşmasıdır. `conclusion` farkında ise
aynı satırda iki desenin bulunması yeterli değildir: iş emrindeki aynı
cümle koşulu uygulanınca 36 aday 10 rapora iner.

### 9.4 Teknik parametre deseni

Açık teknik bağlam deseni, ölçülü 222 raporun **125**'ini yakaladı.
`slice thickness|reconstruction|interval|kernel|kVp|mAs` biçimindeki
geniş ve harf duyarsız desen **221** rapor yakalıyor;
çünkü `mAs` alternatifi `mass` sözcüğünün ilk üç harfiyle eşleşiyor.
Sözcük sınırı eklenmiş gerçek `mAs` tokenı ölçülü raporlarda **0** kez geçti.
Ön kayıttaki 175, ne açık teknik bağlamla ne de güvenli tam-token
yaklaşımıyla yeniden üretilebildi. Teknik satır sözleşmesinin kesin
desenlerle yeniden yazılması gerekiyor.

## 10. Kapsam listesi denetimi

- `emphysema`: **38 geçiş / 35 rapor**
- `atelectasis`: **29 geçiş / 28 rapor**
- `bronchiectasis`: **25 geçiş / 23 rapor**
- `pleural effusion`: **43 geçiş / 39 rapor**

Bu dört ifade `normal`dan farklıdır: takip eden metnin hangi bulguya ait
olduğunu belirleyen, iki noktalı ve içerikli alt başlıklardır. Ana organ
bölümü değildirler ama akciğer bulgusu kapsam listesinde alt başlık olarak
yer almalıdırlar.

## 11. Hüküm

En az bir ölçümde bağıl fark %20'yi geçtiği için kapı **KALDI**.
Veri sözleşmesi mevcut haliyle onaylanmadı ve revizyon gerektiriyor.
Adım 1 kodlaması başlamamalı; ayrışan kalemlerin başlık sınırı ve
cümle/ölçü tanımları uzlaştırılmalıdır.

Eşiği aşan kalemler: `basliksiz_rapor` (%35.8), `dis_organ_en_az_biri` (%48.4), `breast` (%68.3), `bone` (%24.0), `thyroid` (%69.6), `heart` (%29.0), `esophagus` (%40.2), `conclusion_sizinti` (%25.0), `abnormalities_sizinti` (%75.0), `teknik_rapor` (%28.6).
