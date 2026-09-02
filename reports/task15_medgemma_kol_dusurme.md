# TASK-15 · EN-tıbbi kolu DÜŞÜRÜLDÜ — MedGemma post-edit kapanış kaydı

**Tarih:** 2026-09-02 (Europe/Sofia) · **Durum:** kol düşürüldü, dördüncü deneme yok
**Karar dayanağı:** D59 — durma kuralı sonuç görülmeden bağlandı

---

## Hüküm

> **Tıbbi post-edit, 4B ölçekli açık bir modelle sözleşmeye uygun biçimde
> yapılamadı.**

Ablasyon **TR + EN-genel (Google) + EN-ucuz (Opus-MT)** ile devam eder.
Bu bir başarısızlık değil, **ölçülmüş bir bulgudur** ve rapora böyle girer.

---

## Üç koşunun tamamı

| koşu | istem | birim | temiz belge | sonuç |
|---|---|---|---:|---|
| 1 | v1 | belge | **0 / 46** | model post-edit değil, rapor yeniden yazdı |
| 2 | v2 | belge | **26 / 46 (%57)** | istem düzeltmesi işe yaradı, yetmedi |
| 3 | v3 | **cümle** | **1 / 8 (%12,5)** | **erken durdurma** — eşiğin çok altında |

D59'un eşiği %90'dı. Koşu 3 ilk 8 belgede %12,5'te kaldı.

---

## Koşu 3 — ham kayıt

```
Tarih   : 2026-09-02 (Europe/Sofia)
Durum   : ERKEN DURDURMA (tekrar koşulmadı)
Komut   : ./.venv/bin/python scripts/28_task15_ceviri.py --kol en-tibbi \
            --gevsek-sayi --girdi girdi/en_genel_dev.jsonl \
            --cikti cikti/en_tibbi_dev.jsonl
Girdi SHA-256 : ca1ab8463606f1cd382b9e16c3a57bb7bf9a296de8f4b8657d0daab30af8a8a1
```

**Ortam**

| | |
|---|---|
| GPU | NVIDIA Quadro RTX 4000, 8.192 MiB |
| başlangıç GPU belleği | 17 MiB |
| ölçülen tepe GPU belleği | 3.624 MiB |
| toplam süre | ~22 dk 50 sn |
| Python | 3.10.12 |
| PyTorch | 2.6.0+cu124 |
| Transformers | 5.16.1 |

**Betiğin hata mesajı (aynen)**

```
SOZLESME HATASI: ERKEN DURDURMA: ilk 8 belgenin 7'i korunum sozlesmesini bozdu.
Model bu istemle gorevi yapmiyor; kalan 38 belgeyi kosmak zaman kaybi.
Ornek: sayi eklendi: ['1','2','3','4','55','55','55','55','55','55','55','55',
'55','55','55','55','55','55','55','55','55','94','94','94','94','95'];
Markdown bicimleme; dusunme izi
```

**Artefaktlar:** atomik yazma nedeniyle kısmi çıktı bırakılmadı. Şu iki dosya
**üretilmedi** ve bu bilinçlidir:

- `cikti/en_tibbi_dev.jsonl`
- `cikti/en_tibbi_dev.jsonl.provenance.json`

Talimat gereği koşu yeniden denenmedi.

---

## Ne öğrendik

### 1 · Cümle düzeyine inmek bu modelde işe yaramadı

D55'te Opus-MT'yi cümle düzeyine almak çözmüştü; aynı ilaç MedGemma'da
**çalışmadı** — hatta belge düzeyindeki %57'den %12,5'e düştü. Sebep muhtemelen
tek cümlenin modele daha az bağlam vermesi ve "yardımcı asistan" davranışını
daha kolay tetiklemesi.

**Genelleme:** *"parçalama biçim ihlallerini azaltır"* bir model özelliği değil,
model-istem çiftine bağlı bir gözlemdir. Opus-MT'de doğruydu, MedGemma'da yanlış.

### 2 · Kalan ihlaller aynı üç sebep

`sayı eklendi` · `Markdown biçimleme` · `düşünme izi` — koşu 2'de tespit edilen
üçü de sürdü. Örnekteki `55 55 55 … 94 94 95` dizisi düşünme izindeki madde
numaralarıdır; D59'da bu tanı konmuştu ve v3'ün açık *"hemen cevapla, adım adım
düşünme"* talimatı bunu **engellemedi**.

### 3 · Önceden bağlanan durma kuralı işini yaptı

Karar sonuç görülmeden verilmişti. Sonuç kötü çıkınca kuralı gevşetme baskısı
oluşmadı, çünkü gevşetilecek bir yer bırakılmamıştı. Erken durdurma da oransal
kurala (ilk 8'in %60'ı) göre tetiklendi — koşu 2'de "hepsi" kuralı
tetiklenmemişti, düzeltme işe yaradı.

---

## Ablasyona etkisi

| kol | durum |
|---|---|
| **TR** · RadTr Türkçe aslı | ✅ hazır |
| **EN-genel** · Google NMT | ✅ hazır |
| **EN-ucuz** · Opus-MT (cümle düzeyi) | ✅ hazır |
| **EN-tıbbi** · Google → MedGemma | ❌ **düşürüldü** |

**Kaybedilen kontrast:** D52, EN-tıbbi kolunu *"CT-RATE'in kendi hattının
(Google → insan tıbbi düzeltme) makine karşılığı"* olarak tanımlamıştı. Bu kol
düştüğü için **"tıbbi post-edit çeviri kaybını kapatır mı"** sorusu bu çalışmada
cevaplanamayacak; yerine *"4B ölçekli açık modelle denendi ve yapılamadı"*
bulgusu raporlanır.

**Korunan kontrast:** EN-genel ile EN-ucuz arasındaki fark hâlâ ölçülüyor —
*"25 bin raporu ucuza çevirsem ne kaybederim"* sorusu (D55) ayakta.

---

## Kanıt yolları

| koşu | yer |
|---|---|
| 1 | `outputs/task15/ceviri_dev/KARANTINA_medgemma_belge_duzeyi/` |
| 2 | `outputs/task15/ceviri_dev/KARANTINA_medgemma_kosu2_istem_v2/` |
| 3 | `outputs/task15/MEDGEMMA_KOSU3_SON/` (paket) · çıktı üretilmedi, kayıt bu belgedir |
