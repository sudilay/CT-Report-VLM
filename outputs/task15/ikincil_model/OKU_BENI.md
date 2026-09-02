# İkincil Model Koşu Çıktıları

Bu klasör, `dev` bölümünde koşulan ikincil model adaylarının **ham çıktılarını**
ve koşu kayıtlarını taşır. İçerik uzak GPU makinesinde üretilir ve olduğu gibi
buraya alınır.

## Beklenen yapı

```
ikincil_model/
├── <koşu-etiketi>/                  örn. kosu_v2/, kosu_v2_1/
│   ├── <model>_<kol>_dev.jsonl              belge başına ham yanıt + doğrulama
│   ├── <model>_<kol>_dev.ozet.json          kapı ölçümleri
│   ├── <model>_<kol>_dev.provenance.json    model, revizyon, ayarlar, SHA-256
│   └── KOSU_RAPORU.txt                      ortam, süre, elle müdahaleler
```

## Kayıt ilkeleri

**Ham yanıt her zaman saklanır** — sözleşmeyi bozan çıktılar dahil. Geçersiz
çıktı silinmez, onarılmaz, düzeltilmez; işaretlenir ve sayılır. Model yanıtı
değişmez bir deney artefaktıdır.

**Erken duran koşuların kısmi dosyaları da saklanır.** Erken durdurma bir hata
değil, ölçülmüş bir sonuçtur.

**Aynı belgeler farklı ayarlarla tekrar koşulursa** eski koşu silinmez, ayrı bir
etiket altında durur. Hangi ayarın hangi sonucu verdiği `provenance.json` ve
adapter adından (`...:bf16:mt2048`) okunur.

Kapılar ve çıktı sözleşmesi: [docs/19](../../../docs/19_task15_deney_tasarimi_dondurma.md) §5, §"Dev model seçim kapıları".
