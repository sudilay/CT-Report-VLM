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

---

## 6. Yeni kavramların kesinliği — ayrı ölçüldü

Sözlüğe eklenen 13 kavram 20.435 varlık üretti; işaretleyiciler bunların
hiçbirini görmemişti. Duyarlılık kazancını gösterip kesinliği ölçmeden
geçmemek için **ayrı paket** hazırlandı: 130 aday (104 gerçek + 26 çeldirici),
103 hasta, hepsi train'den, D26 kapıları geçildi.

| | A | B |
|---|---|---|
| Çeldirici reddi | %100 (26/26) | %100 (26/26) |
| **K4 kesinlik** | **%100** (104/104) | **%100** (104/104) |
| Sistemin kesinlik doğruluğu | %92,3 | %92,3 |

**13 kavramın hiçbirinde yanlış pozitif yok.** İkisi de her gerçek adayı kabul
etti; kavram bazında da tam örtüşme:

| kavram | n | A | B |
|---|---|---|---|
| covid · pleuroparenchymal · small_airway_disease · small_vessel_disease · soft_tissue_density · adiposity · edema · infective_pathology · aortic_valve · pulmonary_conus · lymphadenomegaly · lymphoma · goiter | 8'er | 8/8 | 8/8 |

⚠ Varlık ve kavram eksenlerinde kappa **hesaplanamaz**: ikisi de her satıra
`E` dediği için varyans yok. Uyum %100 ama kappa tanımsız — bu "zayıf uyum"
değildir, **ölçülemez**dir. Kappa tek sınıflı dağılımda anlamsızdır (aynı
tuzağa zaman ekseninde de düşülmüştü).

### Kesinlik ekseninde kalan ayrışma sistematik değil

12/104 satırda ayrıştılar (kappa 0,705, güçlü) ama **yön iki taraflı**:
`belirsiz→mevcut` 5 · `mevcut→belirsiz` 5 · `mevcut→yok` 2.

Anatomi boşluğundaki gibi tek yönlü değil. İçerikleri gerçek zor vakalar:

> *"Acute interstitial edema and other viral pneumonias are considered in the
> **differential diagnosis**."*
>
> *"Mass lesions-lymphadenomegaly **(lymphoma?)** that are widespread..."*
>
> *"It may belong to the area of focal adiposity, but it **cannot be clearly
> characterized** in this examination."*

Bunlar şartname boşluğu değil, **indirgenemez zorluk**. Kılavuz bu turda yeni
bir eksik göstermedi.

---

## 7. Ayar kümesi ölçümü — toplu tablo

| ölçüt | A | B | eşik | durum |
|---|---|---|---|---|
| Çeldirici reddi | %100 | %100 | %80 | ✅ |
| **K5 duyarlılık** (katı) | %93,0 | %89,7 | %80 | ✅ |
| K5 duyarlılık (tip-bağımsız) | %97,1 | %93,7 | — | |
| K4 kesinlik · özgün adaylar | %99,0 | %85,8 | %90 | ⚠ ayrışık |
| **K4 kesinlik · yeni kavramlar** | **%100** | **%100** | %90 | ✅ |
| K6 · present F1 | %98 | %97 | — | ✅ |
| K6 · absent F1 | %93 | %95 | — | ✅ |
| K6 · uncertain F1 | %50 | %21 | — | ❌ destek 4–16 |
| K6 makro-F1 | %80,3 | %70,8 | %85 | ❌ *(ölçülemez)* |
| İşaretleyici uyumu (kesinlik) | kappa **0,845** | | — | ✅ |

**Okunuşu:** sistem `present` ve `absent` sınıflarında iki bağımsız
işaretleyiciye göre de güçlü. `uncertain` hakkında **bu kümeyle bir şey
söylenemez** — destek 4–16 ve makro-F1 bu sınıfı 300+ destekli sınıflarla eşit
ağırlıklandırıyor. `test-v2` bunu düzeltmek için çekildi (belirsizlik kotası
20 → 55).

K4'teki A/B farkı kural boşluğu değil: `anatomic_segment`, `pneumonia`,
`density`, `abdomen` kavramlarının **span ve granülerlik** tartışması. Gerçek
değer %86–99 arasında; ayrışma sözlük gözden geçirme listesine girdi.
