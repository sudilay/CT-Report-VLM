# Kalan İşaretleme Görevi — 120 cümle

**Pilot bitti ve amacına ulaştı.** Bu, tam ayar kümesinin kalan kısmıdır.

| | |
|---|---|
| Cümle | **120** (pilotun 30'u düşüldü) |
| Aday | **513** — bunların **113'ü çeldirici** (%22) |
| Süre | ~4 saat (pilot 112 adayla ~1 saat sürdü) |
| Kılavuz | [docs/12_pilot_rehberi.md](12_pilot_rehberi.md) — **kurallar değişmedi**, aşağıdaki iki düzeltme dışında |

---

## Dosyalar

| Sıra | Dosya | Ne yapılacak |
|---|---|---|
| **1** | `data/processed/KALAN_A_kor_listeleme.csv` | 120 satır · `bulgular` + `anatomiler` doldurulur |
| **2** | `data/processed/KALAN_B_yargilama.csv` | 513 satır · 4 kolon doldurulur |

⚠ **A önce bitirilir.** B'de sistemin bulduğu adaylar görünür; onları gördükten
sonra A'ya dönmek duyarlılık ölçümünü geçersiz kılar — sistemin **kaçırdığı** şey
artık akla gelmez. Duyarlılık (K5) şu ana kadar **hiç ölçülmedi**; tek kaynağı A.

`KALAN_B_anahtar*` diye bir dosya **açılmaz** — çeldirici anahtarı orada.

---

## Pilottan sonra değişen İKİ kural

Pilot iki sistematik hata buldu, sistem düzeltildi. Kılavuzda da iki düzeltme oldu:

### 1 · Teknik yetersizlik kesinliği DEĞİŞTİRMEZ

> *"In the non-contrast examination, the mediastinal could not be evaluated optimally."*
> → `mediastinum` **mevcut** — `belirsiz` değil, `yok` değil

Cümle yapının **varlığı** hakkında değil, **görüntünün kalitesi** hakkında konuşuyor.
İkisi ayrı eksen.

⚠ *"cannot be excluded"* / *"dışlanamaz"* bundan **farklıdır** — o **bulgu**
hakkındadır → **belirsiz**.

### 2 · Çıkarım ifadeleri MEVCUTtur

| İfade | Kesinlik |
|---|---|
| *"compatible with"*, *"consistent with"*, *"ile uyumlu"* | **mevcut** |
| *"in favor of"*, *"lehine"* | **mevcut** |
| *"suspicious"*, *"şüpheli"* | **mevcut** |
| *"probably"*, *"olasılıkla"*, *"muhtemel"* | **mevcut** |
| *"is thought to be"*, *"düşünülmektedir"* | **mevcut** |

Bulgu **vardır**; yalnızca dayanağı çıkarımdır. Tereddüt ayrı bir eksenin işidir.

**`belirsiz` yalnızca şunlarda:**

| | |
|---|---|
| *"cannot be excluded"*, *"dışlanamaz"* | belirsiz |
| *"(cyst?)"* — parantez içi soru işareti | belirsiz |
| *"cannot be characterized"*, *"ayırıcı tanıda"* | belirsiz |

**Negasyon çıkarımı yener:** *"**No** findings **compatible with** pneumonia"* → **yok**.

---

## Terim sözlüğü — 120 cümlede geçenler

Pilottakilere ek olarak **46 yeni kavram** var.

### Bulgular

| Terim | Türkçesi |
|---|---|
| `atelectasis` | atelektazi — akciğerin sönmesi |
| `pneumothorax` | pnömotoraks — akciğer zarı arasında hava |
| `cardiomegaly` | kardiyomegali — kalp büyümesi |
| `metastasis` | metastaz |
| `granuloma` | granülom |
| `cavitation` | kavitasyon — lezyon içinde boşluk |
| `fibrosis` | fibrozis — nedbeleşme |
| `septal_thickening` | septal kalınlaşma |
| `air_bronchogram` | hava bronkogramı |
| `aneurysm` | anevrizma — damar balonlaşması |
| `dilatation` | dilatasyon — genişleme |
| `atheroma_plaque` | aterom plağı |
| `density_increase` | dansite artışı |
| `hepatosteatosis` | hepatosteatoz — karaciğer yağlanması |
| `hernia` | herni — fıtık |
| `degenerative_change` | dejeneratif değişiklik |
| `spondylosis` | spondiloz — omurga dejenerasyonu |
| `lytic_destructive_lesion` | litik destrüktif lezyon — kemik eriten |
| `sequela_change` | sekel değişiklik — geçirilmiş hastalığın izi |

### Anatomi

| Terim | Türkçesi |
|---|---|
| `middle_lobe` · `lingula` | orta lob · lingula (sol akciğerin dil biçimli bölümü) |
| `lung_apex` | akciğer apeksi — tepe kısmı |
| `hilum` | hilus — damar ve bronşların akciğere girdiği yer |
| `hemithorax` | hemitoraks — göğüs boşluğunun bir yarısı |
| `anatomic_segment` | anatomik segment |
| `chest_wall` · `soft_tissue` | göğüs duvarı · yumuşak doku |
| `bone` · `vertebra` | kemik · vertebra (omur) |
| `breast` | meme |
| `coronary_artery` | koroner arter — kalbi besleyen damar |
| `gallbladder` · `spleen` · `abdomen` | safra kesesi · dalak · abdomen (karın) |
| `station_axillary` · `station_supraclavicular` | aksiller · supraklaviküler lenf nodu istasyonu |

### Niteleyiciler

| Terim | Türkçesi |
|---|---|
| `solid` · `part_solid` | solid · parça-solid |
| `spiculated` | spiküle — dikensi kenarlı |
| `calcific` | kalsifik — kireçli |
| `apical` · `basal` · `peripheral` | apikal (tepe) · bazal (taban) · periferik (dış kesim) |
| `subpleural` | subplevral — akciğer zarının hemen altında |
| `halo` | halo — lezyonu saran buzlu cam halkası |
| `sequela` | sekel — geçirilmiş hastalığın kalıntısı |

⚠ `sequela` (niteleyici) ile `sequela_change` (bulgu) ayrı kavramlardır. Hangisinin
gösterildiğine `aday_tip` kolonundan bak.

---

## Bitirince bildirilecekler

1. Kaç satır **boş** bırakıldı ve neden
2. Kılavuzun **yetmediği** yerler — rehber eksikse **rehber** düzeltilir, cevap değil
3. Süre
4. **A, B'den önce mi dolduruldu** — açıkça teyit

---

## Bu ölçüm ne işe yarayacak

Pilot **kesinliği** ölçtü (%96,5) ve kesinlik atamasını (%87,8). Bu 120 cümle:

- **Duyarlılığı ilk kez ölçecek** (K5) — sistemin ne kaçırdığı
- `uncertain` sınıfına yeterli örnek verecek (pilotta destek yalnızca **8**'di)
- Ölçü–bulgu bağı doğruluğunu ölçecek (K8/K9)

Sonrasında kurallar dondurulur ve değerlendirme kümesi **bir kez** açılır.
