# `known_malignancy` Kör Metin Puanlaması

**Tarih:** 2026-09-08  
**Paket:** `KOR_known_malignancy_v2.csv`  
**Paket SHA-256:** `16411428b04a359faf6765249f12c307dd1fbabecb9d74715608746c5e56a4ed`

## 1. Bağımsızlık beyanı

Proje kapsamında yalnız şu üç dosya açıldı:

- `docs/42_km_kor_puanlama_is_emri.md`
- `docs/37_task17_known_malignancy_kor_dogrulama.md`
- `outputs/task17/km_kor_v2/KOR_known_malignancy_v2.csv`

Paketin SHA-256 değeri iş emrindeki değerle birebir eşleşti. Anahtar dosyası,
şema, değerlendirme kodu, desen/kural dosyaları ve `study_id` bilgisi açılmadı
ve aranmadı. Kararlar yalnız kör paketteki cümlelere göre verildi.

İş emrinin okunmasına izin verdiği ve protokolü tanımlayan `docs/37`, v1
turunun yargı sayılarını ve örüntülerini içeren bir denetim eki de taşıyor.
Bu nedenle v2 puanlamasından önce önceki turun toplu sonucu ve örüntü bilgisi
görülmüş oldu. V2 anahtarı veya vaka eşlemesi görülmedi; yine de bu ön
maruziyet, bağımsızlık yorumunda açık bir sınırlamadır.

## 2. Yargı dağılımı

| yargı | sayı |
|---|---:|
| `E` | 32 |
| `H` | 4 |
| `?` | 4 |
| **Toplam** | **40** |

## 3. Oranlar ve güven aralığı

| ölçüm | hesap | sonuç |
|---|---|---:|
| Protokol kesinliği | `E / (E + H)` = `32 / 36` | **%88,9** |
| Duyarlılık kontrolü | `E / 40` = `32 / 40` | **%80,0** |
| %95 binom güven aralığı | Clopper-Pearson, `32 / 36` | **%73,9–%96,9** |

Protokol kesinliğinin nokta tahmini önceden belirlenen %85 eşiğini geçer.
Ancak `?` yanıtlarını hata sayan kontrol %80,0'dır ve güven aralığının alt
sınırı %85'in altındadır. Dolayısıyla örneklem, gerçek kesinliğin %85'in
üzerinde olduğunu istatistiksel olarak göstermiyor; bu gözlem önceden
belirlenen nokta tahmini kapısını değiştirmez.

## 4. `H` verilen vakalar

| vaka | gerekçe |
|---|---|
| `KM-05` | Akciğer kanseri yalnız görüntü bulgularının yorumu olarak sunuluyor. |
| `KM-06` | Metastatik görünüm radyolojik yorumdur; önceden bilinen kanser öyküsü belirtilmiyor. |
| `KM-10` | Kanser yalnız olasılık yorumu olarak geçiyor; operasyonun kanser nedeniyle olduğu yazmıyor. |
| `KM-21` | Lymphangitis carcinomatosa yalnız radyolojik nedensellik yorumudur; belgelenmiş kanser öyküsü yoktur. |

## 5. `?` verilen vakalar

| vaka | gerekçe |
|---|---|
| `KM-11` | Böbrek tümörünün malign olduğu cümleden anlaşılmıyor. |
| `KM-32` | Meme tümörünün malign olduğu cümleden anlaşılmıyor. |
| `KM-35` | Akciğer tümörünün malign olduğu cümleden anlaşılmıyor. |
| `KM-38` | Böbrek tümörünün malign olduğu cümleden anlaşılmıyor. |

## 6. Cümlelerde görülen örüntüler

`H` vakalarında ortak sorun, kanser veya metastaz ifadesinin belgelenmiş
öykü olarak değil; `evaluated in favor of`, `may be compatible with` ve
`thought to be due to` gibi radyolojik yorum ya da nedensellik dili içinde
geçmesidir. `?` vakalarının dördünde de yalnız `tumor` sözcüğü kullanılmış,
malign nitelik cümlenin kendisinde belirtilmemiştir.

Bu gözlemler yalnız verilen cümlelerden çıkarılmıştır. Kural veya desen
dosyaları incelenmemiştir.

## 7. Kapı sonucu ve sınırlar

Önceden belirlenen `E / (E + H) ≥ %85` ölçütüne göre kural **GEÇTİ** ve
yalnız “raporda yazılı kanser öyküsünü yakalama” ekseninde ayakta kalır.
Bu sonuç hastanın gerçekten kanser olup olmadığını, klinik doğruluğu veya
kaçırılan vakalara ilişkin duyarlılığı ölçmez. `?` yanıtlarının paydadan
çıkarılması sonucu iyimserleştirdiği için %80,0 duyarlılık kontrolü birlikte
raporlanmıştır.
