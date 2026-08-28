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
