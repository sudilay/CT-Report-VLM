# TASK-15 · Altyapı ve `dev` Paketleri — Teknik Kayıt

**Tarih:** 2026-09-01  
**Şema:** `task15-1.0`  
**Kapsam:** Yalnız RadTr `dev`; model/çeviri yok; RadTr `test` açılmadı

Bu belge TASK-15'in ilk uygulama diliminde yazılan kodu, deney güvenlik
sınırlarını ve üretilen gerçek `dev` artefaktlarını tek başına
olarak açıklar. Bağlayıcı yöntem sırası `docs/19` ve `docs/20`'dedir; burada
uygulamanın fiilî durumu kayıtlıdır.

## 1. Veri akışı

```text
data/external/radtr/dev.json
        │  yalnız dev okunur; test.json açılmaz
        ▼
toraks seçimi + RadTr 1-tabanlı ofset düzeltmesi
        │
        ├── data/processed/radtr_toraks_dev.jsonl
        │
        ├── translation_dev.jsonl
        │     yalnız document_id, order, text_tr
        │
        └── normalization_blind_dev.jsonl
              yalnız kaynak cümle/span ve özgün RadTr etiketi
```

İki paket aynı bellek içi kaynak kayıtlarından tek komutta üretilir. Çeviri
paketi altın span/etiket/kavram taşımaz; normalizasyon paketi çeviri, sözlük
eşleşmesi veya sistem/model tahmini taşımaz.

## 2. Kod ve sorumluluklar

| dosya | sorumluluk |
|---|---|
| `src/radyovlm/evaluation/task15.py` | veri sözleşmeleri, split kapısı, adaptör protokolleri, kapalı JSON, paket/hash yazımı, A/B kilitleme-uzlaştırma, A1/A2/A3 ve bootstrap |
| `scripts/16_extract_radtr_thorax.py` | ayrı RadTr kaynağını toraks alt kümesine çevirme; `--bolum dev` çağrısında yalnız `dev.json` okuma |
| `tests/test_task15.py` | sentetik güvenlik ve metrik gerileme testleri |
| `docs/18_task15_calisma_plani.md` | üst düzey ilerleme kaydı |

Sağlayıcı SDK'sı henüz yoktur. Çevirmenler `TranslationAdapter`, ikincil
çıkarım modelleri `SecondaryModelAdapter` sözleşmesine bağlanacaktır. Bu bilinçli
olarak küçük bir arayüzdür; sağlayıcıya özgü sınıf hiyerarşisi kurulmamıştır.

## 3. Kapalı sözleşmeler

### Çeviri paketi

Tam alan kümesi:

```text
document_id · order · text_tr
```

`radtr_label`, `span_text`, `concept_ids`, `assertion` veya başka bir fazla alan
yazıcı tarafından reddedilir.

### Kör normalizasyon paketi

Tam alan kümesi:

```text
document_id · span_id · document_order · span_order
sentence_text · span_text · radtr_label
```

Çeviri, model/sözlük tahmini ve kanonik kavram bulunmaz.

### İkincil model çıktısı

Yalnız doğrudan ayrıştırılabilir JSON kabul edilir:

```json
{"findings": [{"concept_id": "nodule", "assertion": "present"}]}
```

Markdown, açıklama, JSON onarımı, envanter dışı kavram ve `present/absent/uncertain`
dışında değer kabul edilmez. Dondurulmuş envanterin 144 kavram olması zorunludur.

### A/B normalizasyon çıktısı

Her satır kaynak kimlik/metnini aynen taşır ve şunları ekler:

```text
concept_ids · mapping_status · annotator_id · note
```

`mapping_status`: `mapped`, `unmapped`, `needs_adjudication`. `mapped` en az bir
kapalı envanter kimliği taşır; `unmapped` kimlik taşımaz. A/B çıktısı kör paketin
tam anahtar kümesine ve hash'ine bağlıdır. İki dosya aynı span'ları birlikte
atlarsa kilit başarısız olur. Uzlaştırma yalnız ayrışmaları değil **1.490 satırın
tamamını** radyolog kontrol listesine taşır.

## 4. Güvenlik ve geri döndürülebilirlik

- TASK-15 paketleme işlevi yalnız `train/dev` kabul eder; `test` isteğinde
  içerik işlenmeden durur.
- Kaynak çıkarım betiğinde `--bolum` zorunludur; argümansız çağrı artık bütün
  bölümleri varsayılan olarak açamaz.
- Gerçek `dev` koşusu doğrudan ayrı `data/external/radtr/dev.json` dosyasından
  yapıldı. Birleşik `radtr_toraks.jsonl` ve `test.json` açılmadı.
- Kilitli paket, manifest ve A/B dosyaları mevcut hedefin üzerine yazılmaz.
  Yeniden koşu gerekiyorsa yeni sürüm dizini kullanılmalıdır.
- Çıktılar SHA-256 ile kilitlidir. Manifest, iki paketin adını, satır sayısını
  ve hash'ini taşır; ayrı checksum defteri manifest hash'ini de taşır.
- Henüz commit/push, model indirme, dış API çağrısı veya gerçek çeviri yapılmadı.

İlk kod denetiminde iki kusur uygulama tamamlanmadan düzeltildi:

1. A/B çıktıları aynı satırları birlikte atlarsa payda sessizce küçülebiliyordu.
   Kör paketle tam anahtar eşitliği zorunlu yapıldı.
2. Hash'li artefakt mevcut dosyanın üzerine yazılabiliyordu. Bütün kilitli
   yazıcılara `FileExistsError` kapısı eklendi.

## 5. Çalıştırılan komut

```powershell
.\.venv\Scripts\python.exe scripts\16_extract_radtr_thorax.py `
  --bolum dev `
  --task15-paket-dir outputs\task15\dev_packages
```

Bu komut **geçmiş çalıştırma kaydıdır**. Aynı hedeflerde yeniden çalıştırılırsa
üzerine yazma kapısı nedeniyle durur. Yeni ve gerekçeli bir tekrar ayrı sürüm
dizinine yazılmalıdır.

## 6. Ölçülen `dev` sonucu

Kaynakta 132 `dev` belge vardı; toraks seçimi 46 belge verdi (%35). Paket
paydaları dondurma kaydıyla örtüştü:

| ölçüm | sonuç |
|---|---:|
| çeviri kaydı | 46 |
| kör normalizasyon span'ı | 1.490 |
| iki pakette benzersiz belge | 46 / 46 |
| benzersiz `(document_id, span_id)` | 1.490 / 1.490 |
| `span_text` kaynak bağlamında bulunmayan | 0 |
| birden çok cümle taşıyan bağlam | 0 |
| en uzun bağlam | 63 kelime |
| çeviri paketinde yasak altın alan | 0 |
| normalizasyon paketinde yasak tahmin alanı | 0 |

RadTr etiket desteği:

| etiket | span |
|---|---:|
| `Obs_Anatomy` | 696 |
| `Obs_Present` | 481 |
| `Obs_Absent` | 87 |
| `Obs_Technical` | 86 |
| `Obs_Uncertain` | 76 |
| `Differential Diagnosis` | 30 |
| `Symptom_P` | 21 |
| `Obs_Advice` | 13 |

`Obs_Present + Symptom_P = 502`; `Obs_Uncertain + Differential Diagnosis = 106`.
Bu toplamlar önceki `dev` dondurma kaydıyla örtüşür. Henüz hangi etiketlerin
A1/A2/A3 paydasına gireceği değiştirilmedi; kapsam `train/dev` normalizasyon
pilotunda ayrıca dondurulacaktır.

## 7. Artefaktlar ve hash'ler

| artefakt | SHA-256 |
|---|---|
| `data/processed/radtr_toraks_dev.jsonl` | `8c0dbc063892eeeacb90027fcc907f630b38171d8e8d9c1eb3591eb0a3b24a9e` |
| `outputs/task15/dev_packages/translation_dev.jsonl` | `7593b552de9b2ed5c9219685b8e0b096c1b28bf6efa0675b4f98f05316adbdc6` |
| `outputs/task15/dev_packages/normalization_blind_dev.jsonl` | `282cdfad8deb1e3f5edf18c58eb7cc30fbcb1a886b04805c16efd37ed021f1cf` |
| `outputs/task15/dev_packages/package_manifest_dev.json` | `310d9fa1f15738ad7a6ef8a569f310404b4c64e40e61ed25474158b9abc8c70d` |
| `outputs/task15/dev_packages/package_checksums_dev.sha256` | `0c51d0be43c8b3f753b481ce2b0965c61be8e4ceaa895d7b04db11baab18e11a` |
| `configs/task15_kavram_katalogu.yaml` | `eb9299f0488d5e6a5262cba32c9e857715bfa81bfc5f532ed5b9fc180e207a49` |
| `docs/22_task15_kavram_normalizasyon_kilavuzu_taslak.md` | `f69c7b1369ef9878633f86a0cecb35bb8ffc2f8269763ec7bd36bc278e680c8c` |
| `outputs/task15/dev_pilot/normalization_pilot_dev.jsonl` | `9f8162860c98dfcd29b2ca31973321c4a70edd9f364587dfe5a0f5d67d787799` |
| `outputs/task15/dev_pilot/private_B/pilot_B_codex_v2.jsonl` | `5284be3251548ff8f24a63c18ed5ff6d87bd04113f7d93cdbe26916a2c466847` |

Dondurulmuş kavram envanteri `configs/turkce_yuzeyler_taslak.yaml`: 144 kavram,
SHA-256 `b5e2058a04b9a0870d3329cbbc5a2dc25f1f25c41a2e55e34f0cd397179fc8dd`.

## 8. Doğrulama

- TASK-15 sentetik/yapısal testleri: **18/18**.
- Tam depo testi: **271/271**, 1 mevcut uyarı, 99,21 saniye (son koşu).
- Değiştirilen Python dosyalarında `ruff check`: temiz.

Bu sayılar deney başarımı değildir. Yalnız veri sözleşmesinin, kilitlerin ve
puanlama matematiğinin sınandığını gösterir.

## 9. Açık işler ve çekinceler

1. 144 kavramlık iki dilli kısa katalog ve span→kavram normalizasyon kılavuzu
   taslak olarak yazıldı; uzman onayı ve pilot sonrası dondurma yapılmadı.
2. 150 spanlık kör `dev` pilotu üretildi ve bağımsız B 150/150 kilitlendi
   (`mapped` 82 · `unmapped` 54 · `needs_adjudication` 14). Bağımsız A ve
   radyolog kılavuz/tüm liste onayı yapılmadı.
3. Google, MedGemma, TranslateGemma, Qwen ve Aya adaptörleri henüz bağlanmadı;
   model indirilmedi ve çeviri üretilmedi.
4. A1/A2/A3'e girecek RadTr etiket kapsamı pilot sonunda dondurulacak. Sonucu
   görüp kapsam seçmek yasaktır.
5. Kesin test komutu bilerek yoktur. Kılavuz, prompt, model ve ortam
   dondurulmadan eklenmeyecektir.

Pilotun ölçülen çekincesi: 14 uzlaştırma kaydının ana nedeni span başının/sonunun
hedef ifadeyi kesmesi veya komşu cümleden sözcük taşımasıdır. Katalog dışındaki
PTE/trombüs, dispne, hemotoraks, mukus impaksiyonu ve teknik ifadeler yakın ama
yanlış kavramlara zorlanmadı. Bu durumlar A ve uzman onayı olmadan kılavuz
değişikliği veya başarı sonucu sayılmaz.

Sıradaki güvenli adım: `docs/23_task15_pilot_isaretleyici_a_devir.md` içindeki
yalıtım kurallarıyla bağımsız A'yı tamamlamak; iki kilit hazır olmadan B'nin
satır kararlarını açmamak ve uzlaştırmaya başlamamaktır.
