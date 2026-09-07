# Kural Dondurma — TASK-13 / C9

**2026-08-28 · `test-v2` açılmadan önceki son durum**

> Bu belge, `test-v2` üzerinde ölçülecek sistemin **tam olarak neyi** ölçtüğünü
> sabitler. Dondurma sonrası bu dosyalardan biri değişirse ölçüm geçersizdir ve
> `test-v3` çekilmesi gerekir (D26/D31).

---

## 1. Dondurulan sürümler

| bileşen | sürüm | SHA-256 (ilk 16) |
|---|---|---|
| `configs/bulgu_sozlugu.yaml` | **bulgu-1.1** | `ff1bd83aed120fe4` |
| `configs/anatomi_sozlugu.yaml` | **anat-1.1** | `06d0abb76f817d8c` |
| `configs/ipucu_sozlugu.yaml` | **ipucu-1.0** | `057b44ce3ec1611c` |
| `configs/extraction_schema.json` | **sema-1.3** | `06ed2549d294eaa2` |
| `src/radyovlm/extraction/entities.py` | **ent-1.0** | `c38aa26bf7545a31` |
| `src/radyovlm/extraction/context.py` | **ctx-1.1** | `35d05de8aac7e348` |

Sürüm zinciri: `seg-1.1 → tmpl-1.0 → meas-1.2 → ent-1.0 → rel-1.0 → ctx-1.1`,
şema kapısı `sema-1.3`.

## 2. Dondurulan çıktı

| | |
|---|---|
| Varlık | **1.195.300** · 144 kavram |
| present / absent / uncertain | 1.006.780 / 180.097 / **8.423** |
| İlişki | 462.858 |
| Testler | **249/249** |

## 3. Yapısal değişmezler — hepsi geçti

| kod | eşik | sonuç | payda | ihlal |
|---|---|---|---|---|
| K11 | %100 | %100,0 | 843 | 0 |
| K12 | %100 | %100,0 | 37.659 | 0 |
| K13 | %90 | %99,6 | 10.826 | 43 |
| K14 | %100 | %100,0 | 188.520 | 0 |
| K15 | %85 | %98,9 | 25.606 | 279 |

## 4. Ayar kümesinde ölçülenler — **geliştirme gözlemi, sonuç değil**

| ölçüt | A | B | eşik |
|---|---|---|---|
| Çeldirici reddi | %100 | %100 | %80 ✅ |
| K5 duyarlılık (katı) | %93,0 | %89,7 | %80 ✅ |
| K4 · özgün adaylar | %99,0 | %85,8 | %90 ⚠ |
| K4 · yeni kavramlar | %100 | %100 | %90 ✅ |
| K6 present / absent F1 | %98 / %93 | %97 / %95 | — ✅ |
| K6 uncertain F1 | %50 | %21 | — ❌ |
| İşaretleyici uyumu (kesinlik) | kappa **0,845** | | — ✅ |

⚠ Bu sayılar **ayar kümesinden** gelir ve üzerlerinde düzeltme yapılmıştır.
Raporlanacak doğruluk `test-v2`den gelecektir (D31).

## 5. Dondurma öncesi karara bağlananlar

| konu | karar | gerekçe |
|---|---|---|
| `pneumonia ← "pneumonic infiltration"` | korunuyor | pnömoninin radyolojik bulgusu; çift sayım yok (7 kesişim) |
| `abdomen ← "upper abdominal"` | korunuyor | toraks BT'de görünen abdomen zaten üst abdomen — **kapsama bağlı** |
| `density` ayrışması | korunuyor | *"X density"* → niteleyici + gözlem; bilgi kaybolmuyor |
| `soft_tissue_density` | **ayrıldı** | `soft_tissue` anatomidir; ayrılmasaydı yanlış ayrışma üretirdi |
| `anatomic_segment` | korunuyor | %92 fazlalık ama %8'inde karaciğer segment bilgisi taşıyor |
| `laterobasal` | **geri alındı** | `basal` zaten kapsıyor; 0 anma üretti |

## 6. Bilinen sınırlar — raporda yazılacak

1. **`uncertain` sınıfı ayar kümesinde ölçülemedi** (destek 4–16). `test-v2`
   bunun için zenginleştirildi (belirsizlik kotası 20 → 55).
2. **K4 aralığı %86–99.** İki işaretleyici span/granülerlik konusunda ayrışıyor;
   dördü de ölçülüp korundu ama tartışma kapanmadı.
3. **Duyarlılık eşleştirmesi gevşek** — işaretleyici serbest metin yazdığı için
   katı kavram eşlemesi mümkün değil. Katı okuma alt sınırdır.
4. **`prior` desteği ayar kümesinde 0–5.** Zamansallık hakkında karar
   verilemedi; `test-v2`de kota 20 → 60.
5. **Tek dil.** Bütün ölçümler İngilizce CT-RATE üzerinde. Türkçe başarım
   hakkında hiçbir şey söylemiyor.
6. **RadLex eşlemesi yok** — `concept_source = 'yerel_sozluk'`.

## 7. Sonraki adım

`test-v2` (295 cümle · 231 hasta) **bir kez** açılır. İki bağımsız işaretleyici
kör listeleme + yargılama yapar. Çıkan sayı **raporlanacak sayıdır**.

⚠ Teste bakıp herhangi bir kural, sözlük veya desen değiştirilirse bu sürüm
**iptal** edilir, `--surum test-v3` çekilir ve raporda eski skorun geçersiz
olduğu yazılır.


---

## 8. ⚠ SONRADAN EKLENEN DUZELTME — 2026-09-07 (TASK-17, D88/D89/D90)

**Bu bölüm dondurma kaydına EKLENMİŞTİR; yukarısı silinmemiş, değiştirilmemiştir.**

### 8.1 Dondurulan tablo, dondurulan sözlükle uyuşmuyordu

`data/processed/entities.parquet` **2026-08-28**'de üretildi.
`configs/bulgu_sozlugu.yaml` **2026-09-02**'de onarıldı (D58: `nodule`
desenine `nodular` eklendi) — **ama tablo bir daha üretilmedi**.

| kanıt | değer |
|---|---|
| Bayat tabloda `nodular` ham metniyle varlık | **0** |
| Yeniden üretimde | **7.294** |
| Toplam fark | **+17.421 varlık / 12 kavram** |

⚠ **Yukarıdaki §1'de listelenen `bulgu-1.1` hash'i, üretilen tabloyla
bağlantılı değildi.** Dondurma kaydı sözlüğün hash'ini yazıyor ama üretilen
tablo o hash'i taşımıyor; sözlük değişince hiçbir mekanizma bunu yakalamadı.

### 8.2 §4'teki `test-v2` sayıları bu yüzden düşüktür

`test-v2` üzerinde bağımsız yeniden ölçüm (`scripts/56`, protokol
`docs/36`), K5 duyarlılığı için:

| işaretleyici | bu raporda yazılı | bayat tabloyla yeniden üretim | **doğru değer** (temiz referans) |
|---|---|---|---|
| A (codex) | %88,1 | %87,9 | **%89,4** |
| B (gemini) | %97,0 | %96,9 | %96,9 |

Yeniden üretim, raporlanan sayıları **1 öge farkla** tutturdu — yani ölçüm
aleti doğrudur. **A işaretleyicisi için gerçek K5 ~%89,4'tür**; raporlanan
%88,1 uygulanmamış sözlük onarımları yüzünden ~1,5 puan düşüktür.

⚠ **B işaretleyicisi değişmedi** (%96,9) — düzeltme her iki eksende de
aynı yönde değil, yalnız A'nın kaçırdıklarını etkiliyor.

### 8.3 TASK-17'nin sözlük genişletmesinin etkisi ayrı ölçüldü

`ent-1.0r` (temiz referans) → `ent-1.1` (bulgu-1.2): `test-v2` üzerinde
**tam olarak 1 varlık** (`malignancy` 0→1), K5 **+0,1 / +0,0 puan**.

⚠ Bu **etkisizlik kanıtı değil, ölçüm gücü yokluğudur**: yeni kavramlar
nadirdir (`carcinomatosis` 1,2 milyon varlıkta 185), 295 cümlelik bir
kümede beklenen sayı zaten ~0–1'dir.

### 8.4 Kalıcı koruma önerisi — henüz UYGULANMADI

Üretilen tabloya (ya da yanına bir kayda) **üretim sırasında kullanılan
sözlük hash'i yazılmalı**, ve bir test bunu dondurma kaydıyla
karşılaştırmalı. Bugün `entity_version` kolonu var ama o **kodun**
sürümüdür; **girdi sözlüğünün** sürümü hiçbir yerde taşınmıyor. Bu
boşluk olmasaydı D88 üç ay değil, ilk koşumda yakalanırdı.
