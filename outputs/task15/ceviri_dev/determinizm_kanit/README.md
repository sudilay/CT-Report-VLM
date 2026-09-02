# Google NMT determinizm kanıtı

`en_genel_dev_kosu1.jsonl` ile `../en_genel_dev.jsonl` **aynı girdiden, dakikalar
arayla, aynı ayarlarla** üretildi. Çıktılar aynı değil.

| | |
|---|---|
| belge | 46 |
| farklı belge | **5 (%11)** |
| fark türü | sözcük seçimi; bir vakada **anatomik konum kayması** |

Örnekler:

| koşu 1 | koşu 2 |
|---|---|
| `taken` | `obtained` |
| `given,` | `administered,` |
| `EXAMINATION` | `SCANNING` |
| `abdominal sections,` … `lobulated,` | `cross-sections,` … `lobulated in the abdomen,` |

Son satır yalnız üslup değil: anatomik niteleyici bir öbekten diğerine taşınmış.

**Sonucu:** yönetilen Google modeli tekrar üretilebilir değildir. `test` koşusu
**bir kez** yapılır ve ham çıktı değişmez deney artefaktı olarak saklanır;
yeniden koşarak doğrulanamaz. Bkz. D53.

Koşu 1'in provenance dosyası yoktur — betikteki bir yol hatası provenance
yazımını düşürmüştü (çeviri tamamlanmıştı). Hata düzeltildi; koşu 2 tam.
