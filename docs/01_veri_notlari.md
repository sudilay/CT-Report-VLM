# CT-RATE Veri Notlari (dogrulanmis)

Bu belgedeki tum sayilar indirilen veri uzerinde **olculerek** uretildi, tahmin degil.

## Elimizde ne var

| Dosya | Boyut | Icerik |
|---|---|---|
| `train_reports.csv` | 76 MB | 47.149 hacim icin rapor metni |
| `validation_reports.csv` | 5 MB | 3.039 hacim |
| `*_predicted_labels.csv` | 2.9 MB | 18 anormallik etiketi (otomatik uretilmis) |
| `*_metadata.csv` | 16 MB | 44 DICOM alani (yas, cinsiyet, kernel, spacing...) |
| `no_chest_*.txt` | 42 KB | Gogus disi (beyin) taramalarin listesi |

Rapor kolonlari: `VolumeName, ClinicalInformation_EN, Technique_EN, Findings_EN, Impressions_EN`

**Goruntuler indirilmedi** (terabaytlar). Yukaridakiler metin tarafinin tamami.

## Kritik bulgu 1 — Hacim != Calisma. Tekillestirmeden calisma yapilamaz.

`VolumeName` formati: `{split}_{hasta}_{calisma}_{rekonstruksiyon}.nii.gz`

47.149 hacim aslinda **24.128 calisma**. Cogu calismanin 2 rekonstruksiyonu var:

| Rekonstruksiyon/calisma | Calisma sayisi |
|---|---|
| 2 | 21.827 |
| 1 | 1.972 |
| 5 | 235 |
| 3+ | 94 |

Ve **ayni calismanin tum rekonstruksiyonlari birebir ayni rapor metnini tasiyor** — metni farkli olan calisma sayisi: **0**.

> **Tuzak:** Hacim duzeyinde rastgele train/test bolersen ayni rapor hem egitimde hem testte cikar. Sonuclarin sisirilir. Bolme **hasta duzeyinde** yapilmali.

Tekillestirme sonrasi: **25.692 calisma / 21.304 hasta** — bu sayi CT-RATE makalesinin bildirdigi degerle birebir ayni, yani mantik dogrulanmis durumda.

## Kritik bulgu 2 — Anahtar kelime saymak ise yaramaz, negasyon her seyi degistiriyor

Ham prevalans yaniltici. 24.128 tekil calisma uzerinde olculen degerler:

| Terim | Gectigi calisma | Negasyon/normal ifadesi iceren |
|---|---|---|
| `tumoral` | 8.184 | **%100** |
| `mass` | 11.947 | **%93** |
| `nodule` | 12.232 | %50 |
| `malignan` | 217 | %16 |
| `spicul` | 134 | %4 |

Sebep: raporlarda kalip cumleler var —
- *"Thoracic esophagus calibration was normal and no significant **tumoral** wall thickening was detected."*
- *"No **mass** lesion-active infiltration with distinguishable borders was detected in both lungs."*

`tumoral` kelimesinin %100'u sablon bir **negatif** cumleden geliyor. Naif bir siniflandirici bunu "tumor var" diye okur.

> **Uyari — kendi yasadigimiz hata:** Ilk olcumde `\bno\w*\b` regex'i kullandik ve "**no**dule" kelimesi "no" negasyonu sanildi; `nodule` icin %100 negasyon gibi sahte bir sonuc cikti. Tam kelime siniriyla duzeltince gercek deger %50 oldu. **Ders: cumle icinde anahtar kelime aramak negasyon tespiti degildir.** Kapsam (scope) hesabi yapan ConText/NegEx kullanilmali — `medspacy` bunu saglar.

## Kritik bulgu 3 — CT-RATE'te malignite ground truth'u YOK

18 etiketin tam listesi:

`Medical material, Arterial wall calcification, Cardiomegaly, Pericardial effusion, Coronary artery wall calcification, Hiatal hernia, Lymphadenopathy, Emphysema, Atelectasis, Lung nodule, Lung opacity, Pulmonary fibrotic sequela, Pleural effusion, Mosaic attenuation pattern, Peribronchial thickening, Consolidation, Bronchiectasis, Interlobular septal thickening`

Icinde **`malignancy`, `mass`, `cancer` veya `tumor` etiketi yok.** En yakini `Lung nodule` ve `Lymphadenopathy` — ikisi de malignite demek degil.

Ayrica bu etiketler **raporlardan otomatik uretilmis** (`predicted_labels`), radyolog dogrulamasi degil. Yani onlari ground truth saymak dairesel olur.

Kanit gucu: `biopsy` kelimesi 47.149 raporun sadece **16**'sinda geciyor. Patoloji bilgisi pratikte sifir.

> **Sonuc:** T-03 etiketleme semasini kendimiz kurmak zorundayiz ve T-11/T-12 icin CT-RATE tek basina yeterli degil. Harici bir patoloji kaynagi sart.

## Kritik bulgu 4 — Sinif dengesizligi cok agir olacak

Gercek malignite dili nadir: `malignan` %0.9, `carcinoma` %0.5, `neoplas` %0.1, `spicul` %0.6.

Bu bir tarama/rutin kohortu, onkoloji kohortu degil. Pozitif vaka sayisi birkac yuzu gecmeyecek.

> **Sonuc:** NPV yuksek cikacak ama bu *basari degil, prevalans etkisi*. Rapor ederken prevalansi mutlaka belirt. Test setini suni dengelersen NPV klinik gercekligi yansitmaz.

## Veri kalitesi kontrol listesi (resmi `data_correction_note.md`)

1. **v1 vs v2** — v1 kullaniyorsan yogunluk duzeltmesi gerekiyor: `corrected = raw * RescaleSlope + RescaleIntercept`. NIfTI basliklarinda `scl_slope=1, scl_inter=0` kalmis. v2'de duzeltilmis.
2. **Beyin taramalari** — 752 train + 37 valid tarama gogus CT'si degil. `no_chest_*.txt` ile atilmali. *(Bizim scriptimiz bunu yapiyor.)*
3. **Eksik z-spacing** — 3 hacimde NaN: `train_1267_a_4`, `train_11755_a_3`, `train_11755_a_4`. Elle deger atanmali.

## Dil meselesi

Raporlar aslen **Turkce** yazilip Ingilizceye cevrilmis. `*_EN` son eki bundan. Sablon cumlelerin tekrar etmesi (yukaridaki %100'ler) kismen ceviri kaynakli.

Kendi hastane verinle calisacaksan raporlar Turkce olacak ve model performansi ayni cikmaz. Bunu bir **deney degiskeni** olarak plana koy.

## Lisans

`CC-BY-NC-SA-4.0` — **ticari kullanim yok**. Turev calismalar da ayni lisansla paylasilmak zorunda. Urunlestirme dusunuyorsan bu bastan engel.
