# TASK-13 · Ayar Kümesi Ölçümü — ara rapor

**120 cümle · 513 aday (400 gerçek + 113 çeldirici) · iki bağımsız işaretleyici · 2026-08-28**

> ⚠ Ayar kümesi (D26). Bu değerler **geliştirme gözlemidir**, sonuç değildir.
> Raporlanacak doğruluk `test-v1`den gelecek.

---

## 1. Kapı denetimi — geçti

| işaretleyici | çeldirici reddi | eşik | durum |
|---|---|---|---|
| A | %100 (113/113) | %80 | geçti |
| B | %100 (113/113) | %80 | geçti |

İkisi de aynı dağılımla reddetti (74 varlık · 39 kavram). Çeldiriciler sistemin
**üretmediği** sahte adaylardır; her şeye *"doğru"* diyen bir işaretleyici burada
yakalanır. Geçtikleri için diğer sayılar yorumlanabilir.

---

## 2. Duyarlılık — **ilk kez ölçüldü**

Kör listelemeden. İşaretleyici sistem çıktısını **görmeden** cümlede ne varsa yazdı.

| işaretleyici | listelenen | bulundu | kaçırıldı | **K5** | eşik |
|---|---|---|---|---|---|
| A | 341 | 310 | 31 | **%90,9** | %80 ✅ |
| B | 350 | 302 | 48 | **%86,3** | %80 ✅ |

**İkisinin kaçırdıkları örtüşüyor** — bu, gerçek sözlük boşluğu demektir:

`lymph node` (patolojik boyutta) · `infective pathology` · `aortic valve` ·
`pulmonary conus` · `aneurysmatic appearance` · `hepatic steatosis` · `goiter` ·
`edema` · `small airway disease` · `small vessel disease` · `wall` ·
`non-hodgkin lymphoma` · `adiposity`

Eşleştirme dize düzeyinde ve **gevşektir** (kapsama + kelime örtüşmesi); işaretleyici
serbest metin yazdığı için katı kavram eşlemesi mümkün değil. Bu, duyarlılığı
**olduğundan yüksek** gösterebilir; sınır olarak okunmalı.

---

## 3. Kesinlik ve kesinlik ataması — **iddia edilemez**

| ölçüt | A | B |
|---|---|---|
| K4 varlık kesinliği | %99,0 | %85,8 |
| K6 kesinlik ataması (makro-F1) | %90,4 | %59,2 |
| K7 zaman | %99,7 | %66,4 |

Aynı sistem, aynı cümleler — biri eşiği geçiyor, diğeri kalıyor. Sebep bulundu.

### İşaretleyiciler arası uyum

| eksen | n | uyum | kappa | yorum |
|---|---|---|---|---|
| varlık (E/H) | 557 | %94,3 | 0,781 | güçlü |
| kavram (E/H) | 455 | %90,5 | 0,586 | orta |
| **kesinlik** | 420 | %78,8 | **0,479** | **orta** |
| zaman | 420 | %98,3 | 0,000 | *(yorumlanamaz)* |

⚠ Zaman ekseninde kappa 0 ama uyum %98,3 — bu **kappa paradoksu**: neredeyse
her şey `guncel` olduğu için şans uyumu da %98. Bu sayı bir şey söylemiyor.

### Ayrışma tek bir noktada toplanıyor

**113 ayrışan satırın 99'u anatomi.** Yön tek taraflı: A `mevcut`, B `yok`.

| tip | ayrışma |
|---|---|
| **anatomy** | **%33** (77/234) |
| observation | %4 (6/147) |
| qualifier | %15 (6/39) |

> *"**No** mass or infiltrative lesion was observed **in both lungs**."* → `lungs`
> A: **mevcut** · B: **yok**

---

## 4. Sebep: kılavuzda eksik kural — kural yazarının hatası

Pilotta bulunan ve düzeltilen hata (**D28**: negasyon anatomiye sıçramaz) sisteme
uygulanmış, **kılavuza yazılmamıştı**. `docs/11` ve `docs/12` bu konuda sessizdi.

Sonuç: iki işaretleyici de **kendi içinde tutarlı** davrandı, ama farklı kural
seçtiler.

| | önceki cevapları (75 etkilenen satır) |
|---|---|
| A | `mevcut` 75 |
| B | `yok` 58 · `mevcut` 14 · `belirsiz` 2 |

Bu dikkatsizlik değil; **şartname boşluğudur**.

### Neden A'nın %90,4'ü kabul edilmiyor

A'nın sistemle aynı kararı vermiş olması **bağımsız kanıt değildir**. Yazılı kural
olmadığı için ikisi de tahmin etti; A'nınki sistemle örtüştü. Bu tesadüf de olabilir,
doğal okuma da olabilir — **doğrulama değildir**.

⚠ Ayrıca bu boşluğun kapatılması **sistemi iyi gösterecek yöndedir**. Tam da
kendini kandırmaya müsait yer. Bu yüzden:

- kural kılavuza yazıldı, **karar işaretleyiciye bırakıldı** (kural yazarı uygulamadı)
- eski cevaplar `_onceki_cevap` kolonunda **tutuluyor**, değişim izlenebilir
- skor **iki türlü** raporlanacak: düzeltmeli ve düzeltmesiz

---

## 5. Durum

| ölçüt | durum |
|---|---|
| Çeldirici kapısı | ✅ geçti |
| **K5 duyarlılık** | ✅ **%86–91 · güvenilir** (iki işaretleyici hemfikir) |
| K4 varlık kesinliği | ⏸ yeniden yargılama bekliyor |
| K6 kesinlik ataması | ⏸ yeniden yargılama bekliyor |
| K7 zaman | ⏸ örneklem yetersiz (`prior` desteği 0–5) |

**Açık işler**

1. 75 etkilenen satır yeniden yargılanacak → `YENIDEN_codex.csv` · `YENIDEN_gemini.csv`
2. Kappa yeniden hesaplanacak; yükselirse boşluğun sebep olduğu doğrulanır
3. Kör listelemenin bulduğu sözlük boşlukları kapatılacak (ayar kümesinde meşru, D26)
4. Sonra kurallar dondurulup `test-v1` **bir kez** açılacak (D31)

⚠ `prior` sınıfının desteği 0–5. Zamansallık hakkında bu kümeyle karar verilemez;
`test-v1` örnekleminde `onceki_tetkik` grubunun ağırlığı gözden geçirilmeli.
