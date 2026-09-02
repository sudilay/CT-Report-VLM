# KARANTINA · MedGemma koşu 2 (istem v2, belge düzeyi)

2026-09-01, uzak GPU, 46 belge, 33 dakika. İstem v2 kullanıldığı provenance
hash'iyle doğrulandı. Girdi zinciri doğru.

**İlerleme var ama yeterli değil:**

| | temiz belge |
|---|---|
| koşu 1 (istem v1) | 0 / 46 |
| **koşu 2 (istem v2)** | **26 / 46 (%57)** |

Kalan ihlaller:

| sorun | belge |
|---|---:|
| Markdown biçimleme | 20 |
| **düşünme izi çıktıya sızmış** | 8 |
| metin uzamış | 9 |
| sayı eklenmiş | 9 |

Düşünme izi örneği:

```
<unused94>thought
The user wants me to correct medical terminology...
Let's break down the text sentence by sentence:
1. ...
```

"Sayı eklenmiş" ihlallerinin çoğu bu izdeki madde numaralarından geliyor.

**Erken durdurma tetiklenmedi:** ilk 5 belgenin 4'ü ihlalliydi, kural "hepsi"
diyordu. Kural oransal hale getirildi (ilk 8'in %60'ı).

Bu artefakt ölçüme girmeyecek. Koşu 3 cümle düzeyinde ve son deneme.
