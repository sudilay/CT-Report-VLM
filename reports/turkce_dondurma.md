# Türkçe Sözlük Dondurma — `tr-1.0`

**2026-08-31 · TASK-14 kapanışı · dil ablasyonu (TASK-15) açılmadan önce**

> Bu belge, ablasyonda ölçülecek **Türkçe sistemin tam olarak ne olduğunu**
> sabitler. Dondurma sonrası bu dosyalardan biri değişirse ölçüm geçersizdir ve
> yeni bir sürüm çekilmesi gerekir (D26/5, D31 — İngilizce tarafta `test-v2`
> için uygulanan kuralın aynısı).

---

## 1. Dondurulan sürümler

| bileşen | sürüm | SHA-256 (ilk 16) |
|---|---|---|
| `configs/turkce_yuzeyler_taslak.yaml` | **tr-1.0** | `b5e2058a04b9a087` |
| `configs/turkce_ipuclari_taslak.yaml` | **tr-ipucu-1.0** | `4f4efd3fbedf1445` |
| `scripts/23_turkce_dev_olcum.py` (kapsam mantığı) | — | `34ece92a1344d04a` |
| `data/processed/radtr_toraks.jsonl` | — | `8ce5ef37cdfd4504` |

Bölünme dondurması: [`turkce_bolunme_dondurma.md`](turkce_bolunme_dondurma.md)

---

## 2. Dondurulan içerik

| | |
|---|---|
| kavram yüzeyi | **144** (İngilizce sözlüğün tamamı) |
| RadTr `train+dev`'de geçen | **123** (%85) |
| ipucu bölümü | 8 |
| ipucu | **28** |
| **uzman onaylı girdi** | ⛔ **0** |

⚠ Hiçbir yüzey ve hiçbir ipucu radyolog onayından geçmedi. Bu sözlük sistemin
kalıcı sözlüğüne (`bulgu_sozlugu.yaml`, `anatomi_sozlugu.yaml`) **girmez**;
ablasyonda ayrı bir deney sözlüğü olarak kullanılır.

---

## 3. `dev` üzerinde ölçülenler — **geliştirme gözlemi, sonuç değil**

`dev` ayar kümesidir ve üzerinde düzeltme yapılmıştır. Bu sayılar tarafsız
tahmin **değildir** (D31). Raporlanacak sayı `test`ten gelecektir.

| sınıf | destek | P | R | F1 |
|---|---|---|---|---|
| `present` | 450 | %84,3 | %97,6 | **%90,4** |
| **`absent`** | 72 | %84,3 | **%97,2** | **%90,3** |
| `uncertain` | 96 | %92,9 | %13,5 | %23,6 |

**Doğruluk %84,5** (n=618 · 46 belge)

Şema farkı (aşağıda) dışlanınca: doğruluk **%92,4**, `uncertain` F1 **%43,6**.

### Ana bulgu

**Negasyon Türkçede çalışıyor** — `absent` duyarlılık %97,2. Bu, TASK-14'ün
sorduğu asıl soruya cevaptır: **çıkarım katmanı Türkçeye taşınıyor.**

---

## 4. Ablasyondan **önce** bilinen sınırlar

Bunlar ölçüm yapılmadan önce yazıldı; sonuç görülüp eklenmedi.

### 4a. ⛔ Zaman ekseni **ölçülemeyecek**

| ipucu | `train+dev`'de anma |
|---|---|
| *önceki tetkik / önceki inceleme* | **4** |
| *stabil / değişiklik yok* | 1 |

RadTr **tek zamanlı sentetik** raporlardan oluşuyor. Ablasyon `prior` eksenini
ölçemez ve bu eksende hiçbir sayı raporlanmayacaktır.

### 4b. ⚠ Şema farkı — `uncertain` iki türlü okunur

RadTr *"değerlendirme optimal yapılamamıştır"* ifadesini `Obs_Uncertain`
sayıyor. Bizim **D30**'umuz teknik çekinceyi ayrı eksende tutuyor ve kesinliği
değiştirmiyor.

`dev`de ölçüldü: altın `uncertain`ın **%51'i** bu türden.

**Karar: D30 korunuyor.** Gerekçe — teknik çekince *"bulgu belirsiz"* değil
*"görüntü yetersiz"* demektir; ikisi katlanırsa geri kazanılamaz biçimde
karışır. Ablasyon raporunda **iki sayı da** verilecek ve hangisinin hangi şemaya
ait olduğu yazılacaktır.

### 4c. D29 gerilimi — iki dilde de aynı

*"ile uyumlu"* / *"in favor of"* ifadesini D29 `present` sayıyor. Hem
İngilizce `test-v2`de hem Türkçe `dev`de bu karar `uncertain` duyarlılığını
düşürüyor. **İki bağımsız ölçüm, aynı yönde.**

⚠ Kural değiştirilmedi. Değiştirilecekse etkisi yeni bir sürümde ölçülür.

### 4d. Altın veri kalitesi

| ölçüm | sonuç |
|---|---|
| `Obs_Present` span'ında negasyon ipucu | 4/3.939 = **%0,1** |
| Span cümle sınırını aşıyor | **%10,9** |
| `dev`de cümlesi eşleşmeyen span | 77 |

Altın veri büyük ölçüde temiz; span sınırı gürültüsü ölçüme bir tavan koyuyor.

### 4e. Devralınan sınırlar

| sınır | etkisi |
|---|---|
| RadTr **sentetik** | Sonuç *"RadTr benzeri Türkçe metinlerde"* diye yazılır |
| `test` **56 belge** | Güven aralığı geniş; tek nokta tahmini sunulmaz |
| **Hizalı çift yok** | İngilizce kol makine çevirisi; çeviri hatası ile dil etkisi tam ayrılamaz |
| Yüzeyler **uzman onaysız** | Türkçe tarafın düşük çıkması dilden mi araçtan mı ayrılamaz |

---

## 5. `test` bölümü — **açılmadı**

| betik | kilit |
|---|---|
| `20_turkce_yuzey_taslagi.py` | `GELISTIRME_BOLUMLERI = ("train","dev")` · `--bolum test` → `sys.exit` |
| `22_turkce_ipucu_taslagi.py` | `GELISTIRME = ("train","dev")` · `--bolum test` → `sys.exit` |
| `23_turkce_dev_olcum.py` | `--bolum` yalnızca `train`/`dev` kabul eder → `sys.exit` |

`test` bölümünün 56 belgesi TASK-15'te **bir kez** açılacaktır.

---

## 6. Bu dondurmayı geçersiz kılacak şeyler

1. `test` bölümüne yüzey/ipucu geliştirirken bakmak
2. Ablasyon sonucunu görüp yüzey, ipucu veya kapsam mantığı değiştirmek
3. Yukarıdaki sağlama toplamlarından birinin değişmesi

Ayrışma çıkarsa yapılabilecek **tek** şey: şema farkı mı diye bakmak ve farkı
**raporlamak** — sistemi değiştirmek değil.

---

## 7. TASK-15'e devir

Hazır olanlar:

- ✅ Türkçe sözlük donduruldu (`tr-1.0`)
- ✅ Bölünme donduruldu, `test` açılmadı
- ✅ Ablasyon protokolü yazıldı → [`docs/16_dil_ablasyon_protokolu.md`](../docs/16_dil_ablasyon_protokolu.md)
- ✅ Bilinen sınırlar ölçümden **önce** kayıtlı

Sıradaki iş: `test`in 56 belgesini iki yolla İngilizceye çevir, üç kolu
(TR · EN-çeviri · EN-tıbbi) **aynı** altın veriye karşı puanla, **dil kararını**
ver.


---

## ⚠ SONRADAN EKLENEN — 2026-09-07 · `tr-1.0` → `tr-1.1` (TASK-17 madde 10, D91)

**Bu bölüm EKLENMİŞTİR; yukarısı silinmemiş, değiştirilmemiştir.**

`bulgu-1.2` ile eklenen kavramların Türkçe karşılıkları yazıldı.
**144 → 160 yüzey.** Yeni hash: `5d230e1e4d74c5cc` *(eski `b5e2058a04b9a087`)*.

### Neden dondurma kırıldı ve nasıl ele alındı

D88'in dersi uygulandı: sürüm **yükseltildi**, dondurma kaydı **üstüne
yazılmadı**, ek olarak bu bölüm eklendi. Eski hash yukarıda duruyor.

⚠ **Mevcut 144 yüzeyin HİÇBİRİ değiştirilmedi** — yalnız 16 yeni girdi
eklendi. TASK-15'in ölçümleri mevcut yüzeylere dayanıyordu ve onlar
olduğu gibi duruyor.

### Mezuniyet yolu — her girdide yazılı

| yol | ne demek | kaç girdi |
|---|---|---|
| **künye** | Türk radyoloji literatüründe belgelenmiş | 15 |
| **ölçüm** | RadTr train+dev'de geçti (test MÜHÜRLÜ) | 1 (`malignant_character`, 7 anma) |

### ⛔ Girmeyen: `complete_calcification`

Terminoloji araştırması bu kavramı **yanlış eşleyerek** doğrulamıştı
(*"diffüz kalsifikasyon"*); o eşleme D83'te ölçülüp **çürütüldü** (491
cümle, tamamı damar ateromu). Doğru kavram için Türkçe künye **yok** ve
RadTr'de **0**. Kural gereği hazırlık dosyasında bekliyor — **tahminle
sözlüğe alınmadı.**

### ⚠ İlan edilen çelişki: `neoplasm`

`neoplaz` bu dosyada **zaten** `tumor` deseninin içinde
(`t[uü]m[oö]r|neoplaz|kitlesel`). İngilizce tarafta `neoplasm` artık
**ayrı** kavram. Ayırmak `tumor`un davranışını değiştirirdi, o yüzden
**yapılmadı**; çelişki ilan edildi ve `tr-2.0` yeniden türetmesine
bırakıldı (plan §5 zaten kapsam dışı bırakmıştı).

### Doğrulama

`tr_matcher_kur` 160 yüzeyle sorunsuz kuruldu; 8 sentetik cümlede **8/8**.
Kritik ayrım doğrulandı: *"Malignite"* → `malignancy`, *"Malign
görünümlü"* → `malignant_character` (kelime sınırı `malign` sayesinde).
