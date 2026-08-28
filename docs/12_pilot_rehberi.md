# Pilot İşaretleme — Adım Adım Rehber

**30 cümle · 112 aday · tahmini 1 saat**

> Bu rehber seni baştan sona yönlendirir. Radyolog olman gerekmiyor —
> **teşhis koymayacaksın**, cümlenin ne söylediğini işaretleyeceksin.

---

## Neden yapıyoruz

Sistem 1,18 milyon bulgu çıkardı ama **doğru olup olmadığını bilmiyoruz.**
Kuralları ben yazdım; benim *"doğru"* demem ölçüm sayılmaz. Bu yüzden **senin**
işaretlemene ihtiyaç var.

Pilot üç soruyu cevaplayacak:
1. Bu rehber anlaşılır mı?
2. Sen yapabiliyor musun?
3. Sistemde büyük bir sorun var mı?

Sonuca göre ya tam kümeye (150 cümle) geçeriz ya da önce rehberi düzeltiriz.

---

## Sıra önemli

| | Ne | Süre | Dosya |
|---|---|---|---|
| **0** | Terimleri oku | 10 dk | bu rehber, aşağısı |
| **1** | **A · Kör listeleme** | ~25 dk | `PILOT_A_kor_listeleme.csv` |
| **2** | **B · Yargılama** | ~35 dk | `PILOT_B_yargilama.csv` |

⚠ **A'yı önce bitir.** B'de sana sistemin bulduğu adaylar gösterilecek. Onları
gördükten sonra A'ya dönersen aklın yönlenir ve sistemin **kaçırdığını** fark
edemezsin. A'nın tüm değeri buradan geliyor.

Dosyalar: `data/processed/` klasöründe. Excel'de açabilirsin.

---

## Adım 0 · Karşılaşacağın terimler

Pilotta **yalnızca bunlar** geçiyor. Ezberlemene gerek yok, açık tut yeter.

### Bulgular — vücutta *görülen bir şey*

| Terim | Türkçesi |
|---|---|
| `nodule` | nodül — küçük yuvarlak oluşum |
| `mass` | kitle |
| `lesion` · `space_occupying_lesion` | lezyon · yer kaplayan lezyon |
| `tumor` | tümör |
| `effusion` | efüzyon — sıvı birikimi |
| `effusion_thickening` | efüzyon-kalınlaşma (tek terim) |
| `thickening` | kalınlaşma |
| `consolidation` | konsolidasyon — havasız akciğer alanı |
| `infiltration` | infiltrasyon |
| `pneumonia` | pnömoni (zatürre) |
| `emphysema` | amfizem |
| `bronchiectasis` | bronşektazi — bronş genişlemesi |
| `cyst` | kist |
| `calcification` | kalsifikasyon — kireçlenme |
| `enlarged_lymph_node` | büyümüş lenf nodu |
| `density` | dansite — yoğunluk artışı |
| `nodular_lesion` | nodüler lezyon |
| `fluid_collection` | sıvı koleksiyonu |
| `fracture` | kırık |
| `bulla` | bül — hava kesesi |
| `reticulation` | retikülasyon — ağsı görünüm |
| `mosaic_attenuation` | mozaik atenüasyon |
| `cholelithiasis` | safra taşı |
| `nephrolithiasis` | böbrek taşı |
| `cardiothoracic_ratio` | kardiyotorasik oran (raporda **CTO**) |
| `occlusive_pathology` | tıkayıcı patoloji |

### Anatomi — vücuttaki *yapılar*

| Terim | Türkçesi |
|---|---|
| `lung` · `lung_parenchyma` · `parenchyma` | akciğer · akciğer parankimi · parankim |
| `upper_lobe` · `lower_lobe` | üst lob · alt lob |
| `pleura` | plevra — akciğer zarı |
| `fissure` | fissür — loblar arası yarık |
| `trachea` · `bronchus` · `airway` | trakea · bronş · hava yolu |
| `mediastinum` | mediasten — iki akciğer arası bölge |
| `heart` · `pericardium` | kalp · perikart (kalp zarı) |
| `aorta` · `pulmonary_artery` · `vascular_structure` | aort · pulmoner arter · damar yapıları |
| `esophagus` | özofagus (yemek borusu) |
| `liver` · `kidney` · `adrenal_gland` | karaciğer · böbrek · böbreküstü bezi |
| `lymph_node` | lenf nodu |
| `station_*` | lenf nodu bölgeleri (prevascular, paratracheal, subcarinal, hilar-axillary) |

### Niteleyiciler — bulguyu *tarif eden* sıfatlar

`hypodense` (hipodens — koyu görünen) · `ground_glass` (buzlu cam) ·
`cystic` (kistik) · `lobulated` (lobüle — girintili çıkıntılı)

---

## Adım 1 · A · Kör listeleme

**30 satır.** Her satırda bir cümle var, iki kolon dolduracaksın.

### Ne yazacaksın

| Kolon | Ne |
|---|---|
| `bulgular` | Cümlede geçen **bulgular**, virgülle |
| `anatomiler` | Cümlede geçen **anatomik yapılar**, virgülle |

**Metinde geçtiği hâliyle yaz.** İngilizce kelimeyi olduğu gibi kopyala.

### ⚠ En sık yapılan hata

**Bulgunun yok olması onu listeden çıkarmaz.**

> *"Thoracic esophagus calibration was normal and **no significant pathological wall
> thickening was detected**."*
>
> `bulgular` → **`thickening`**  ← kalınlaşma YOK ama cümlede GEÇİYOR
> `anatomiler` → `esophagus`

Var/yok ayrımını **B adımında** yapacaksın. A'da sadece *"cümlede ne geçiyor"*.

### İki örnek daha

> *"In the evaluation of both lung parenchyma; No suspicious mass or infiltration was
> detected in both lungs."*
>
> `bulgular` → `mass, infiltration`
> `anatomiler` → `lung parenchyma, lungs`

> *"No enlarged lymph nodes in prevascular, pre-paratracheal, subcarinal or bilateral
> hilar-axillary pathological dimensions were detected."*
>
> `bulgular` → `enlarged lymph nodes`
> `anatomiler` → `prevascular, pre-paratracheal, subcarinal, hilar-axillary`

### Emin olamazsan

**Boş bırak, `notlar`a yaz.** Tahmin etme. Boş satır hesaptan çıkarılır ve zarar
vermez; yanlış satır sonucu bozar.

---

## Adım 2 · B · Yargılama

**112 satır.** Her satırda cümle + sistemin bulduğunu iddia ettiği bir ifade var.

### Dört kolon

**`dogru_varlik_mi`** → `E` / `H`
Gösterilen ifade gerçekten bir bulgu veya anatomi mi?

**`dogru_kavram_mi`** → `E` / `H`  *(yalnızca üstte `E` dediysen)*
Atanan kavram adı uygun mu? `"nodules"` → `nodule` doğru; `"nodules"` → `mass` yanlış.

**`kesinlik_ne_olmali`** → `mevcut` / `yok` / `belirsiz`

**`zaman_ne_olmali`** → `guncel` / `onceki` / `bilinmiyor`

### ⚠ Listede kasıtlı YANLIŞ adaylar var

**112 adayın 26'sı sahte.** Sistemin bulmadığı, benim bilerek karıştırdığım
kelimeler. Amaç senin dikkatini denetlemek — hepsine `E` dersen bunu görürüz ve
ölçümün güvenilmez olduğunu anlarız.

Gerçek bir çeldirici örneği:

> *"No enlarged lymph nodes in prevascular … pathological **dimensions** were detected."*
> **aday:** `'dimensions'` → `occlusive_pathology`
>
> `dogru_varlik_mi` → **H** — "dimensions" (boyutlar) bir bulgu değil

### Kesinlik tablosu — buna bak

| Cümlede geçen | Kesinlik |
|---|---|
| *"was not observed"*, *"no … was detected"*, *"izlenmemiştir"* | **yok** |
| ⚠ *"could not be evaluated"* — teknik yetersizlik | **mevcut** ← kesinliği DEĞİŞTİRMEZ |
| ⚠ *"cannot be excluded"*, *"dışlanamaz"* | **belirsiz** ← `yok` DEĞİL |
| *"suspicious"*, *"şüpheli"* | **mevcut** |
| *"compatible with"*, *"in favor of"*, *"lehine"* | **mevcut** |
| *"probably"*, *"olasılıkla"* | **mevcut** |
| *"(cyst?)"* — parantez içi soru işareti | **belirsiz** |
| *"cannot be characterized"*, *"ayırıcı tanıda"* | **belirsiz** |
| Düz beyan: *"nodule is observed"* | **mevcut** |

**Üç kural, ezberle:**

**1.** *"cannot be excluded"* → **belirsiz**. İçinde *"not"* var diye `yok` deme.
*"Malignite dışlanamaz"* = *"malignite olabilir"*.

**2.** *"could not be evaluated"* (değerlendirilemedi) → kesinliği **değiştirmez**.

> *"In the non-contrast examination, the mediastinal could not be evaluated optimally."*
> → mediasten **mevcut**, `belirsiz` değil

Sebep: bu cümle mediastenin *varlığı* hakkında bir şey söylemiyor — **görüntünün
kalitesi** hakkında söylüyor. İkisi ayrı eksen. Teknik çekince ayrı bir alanda
(`technical_limitation`) tutulur; kesinliğe karıştırılırsa *"bulgu belirsiz"* ile
*"görüntü yetersiz"* birbirine karışır ve ikisi de geri alınamaz.

⚠ Bunu *"cannot be excluded"* ile karıştırma. O **bulgu** hakkındadır → **belirsiz**.

**3.** *"is recommended"* (önerilir) kesinliği **değiştirmez**. Öneridir.

### Kapsam nerede biter

Olumsuzlama **noktalı virgüle**, ***however / but***'a, ***apart from***'a kadar sürer:

> *"No consolidation**;** **however**, newly developed effusion is observed."*
> → konsolidasyon **yok** · efüzyon **mevcut**

Bir olumsuzlama **birden çok bulguyu** kapsayabilir:

> *"No pleural effusion **or** thickening was observed."* → **ikisi de yok**

### Zaman

| Durum | Zaman |
|---|---|
| *"is observed"* — bu tetkikte | **guncel** |
| *"In the previous CT, it measured 18 mm"* | **onceki** |
| ⚠ *"has increased **compared to the previous** examination"* | **guncel** |
| Anlaşılmıyor | **bilinmiyor** |

**Son satır önemli:** *"önceki tetkike göre büyümüş"* cümlesinde bulgu **şimdi
vardır**. "Önceki" sadece kıyas noktasıdır.

---

## Bitirdiğinde bana söyle

1. **Kaç satırı boş bıraktın** — rapora yazılacak
2. **Nerede zorlandın** — rehber eksikse **rehber düzeltilir**, senin cevabın değil
3. **Ne kadar sürdü**

Sonra ben:
- Kesinlik ve duyarlılığı hesaplarım
- **Çeldirici ret oranına** bakarım — işaretlemenin güvenilir olup olmadığını gösterir
- Tam kümeye geçmeli miyiz, yoksa önce rehberi mi düzeltmeliyiz, birlikte karar veririz

---

## Takıldığında hatırla

| Soru | Cevap |
|---|---|
| Teşhis koymam gerekiyor mu? | **Hayır.** Cümle ne diyor, onu işaretliyorsun |
| Bu kelime bulgu mu anatomi mi? | Vücutta bir **yapı** ise anatomi; o yapıda **görülen** bir şey ise bulgu |
| Emin değilim | **Boş bırak**, nota yaz |
| Cümle çok karışık | Boş bırak, nota yaz. Zorlanman **rehberin** eksiği olabilir |
| Aynı bulgu iki kez geçiyor | İkisini de yaz |
