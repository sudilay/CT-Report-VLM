# TASK-16 · Adım 4 (v1.1) — Gözle İnceleme

**Kilit sürümü:** `takim-1.1` · **Kilit tarihi:** 2026-09-03

Bu belge kilitli CSV dosyalarından **doğrudan üretildi** — elle yazılmadı.
🔄 işareti v1.1'de değişen/eklenen vakaları gösterir.

---

## 1 · Sınır Vakaları (30)

Bunlar şemanın **klinik yargı gerektiren kararlarını** (C listesi) sınayan vakalar.

### C1-negasyon-kapsami

**`C1-negasyon-kapsami-01`**  —  hedef: **`None`**  (dayanak: `A1+A19`)

> No metastases and lytic-destructive lesions were observed in bone structures.

*Gerekçe:* Metastaz negasyon KAPSAMI icinde: 'No metastases ... were observed'

**`C1-negasyon-kapsami-02`**  —  hedef: **`intermediate`**  (dayanak: `C#1+C#4`)

> Although the examination could not be characterized because it was not performed for the liver, it was thought that the described appearances might belong to metastasis.

*Gerekçe:* Negasyon INCELEMEYE ait ('could not be characterized'), metastaza degil; bulgu 'might belong to metastasis' = orta derece

**`C1-negasyon-kapsami-03`**  —  hedef: **`None`**  (dayanak: `A1`)

> Thoracic esophagus calibration was normal within the sections, and no significant tumoral wall thickening was detected.

*Gerekçe:* 'no significant tumoral wall thickening was detected' - tumoral kapsam icinde


### C4-derece-yuksek

**`C4-derece-yuksek-01`** 🔄  —  hedef: **`high`**  (dayanak: `C#4+C#new-esik`)

> Anasarca-style edema, bilateral pleural effusion, diffuse intra-abdominal free fluid, metastatic masses in the liver, highly suspicious nodular in favor of metastasis in both lungs

*Gerekçe:* v1.1 DUZELTME (2. denetim, bulgu 1.3): raporda YAZILI bilinen primer kanser YOK; 'metastatic masses' radyolojik HUKUM, patoloji degil. YENI C KARARI (docs/33 §4.1): known_malignancy esigi = raporda YAZILI bilinen/belgelenmis kanser gerekir (ornek: 'known primary', 'bladder ca in the follow-up'). Yalniz radyolojik hukum en fazla high uretir.

**`C4-derece-yuksek-02`**  —  hedef: **`high`**  (dayanak: `C#4`)

> A highly suspicious mass lesion in favor of malignancy extending to the upper lobe posterior segment in the superior segment of the left lung lower lobe, histopathological diagnosis will be appropriate.

*Gerekçe:* 'highly suspicious ... in favor of malignancy' - yuksek derece ama patoloji yok; 'histopathological diagnosis will be appropriate'


### C4-derece-orta

**`C4-derece-orta-01`**  —  hedef: **`intermediate`**  (dayanak: `C#4`)

> Contour lobulation, which may be compatible with capsular metastasis, is observed in the anterior left lobe.

*Gerekçe:* 'may be compatible with capsular metastasis' - orta derece

**`C4-derece-orta-02`**  —  hedef: **`indeterminate`**  (dayanak: `C#16`)

> Nodular consolidative lesions with peripheral ground-glass density increases in both lungs, the appearance may be of fungal infection or metastasis.

*Gerekçe:* 'may be of fungal infection OR metastasis' - ayirici tani, taraf tutulmaz


### C4-derece-dislanamaz

**`C4-derece-dislanamaz-01`**  —  hedef: **`indeterminate`**  (dayanak: `A3+A18`)

> However, metastasis cannot be excluded.

*Gerekçe:* 'metastasis cannot be excluded' - Kritik kural 1: present degil

**`C4-derece-dislanamaz-02`**  —  hedef: **`indeterminate`**  (dayanak: `A3+A18`)

> At this level, malignancy cannot be excluded.

*Gerekçe:* 'malignancy cannot be excluded'


### C5-stabil-malignite

**`C5-stabil-malignite-01`**  —  hedef: **`known_malignancy`**  (dayanak: `C#5`)

> Stable soft tissue density thought to belong to regressed primary malignancy in the left upper lobe

*Gerekçe:* 'regressed primary malignancy' bilinen; 'stable' tanıyı degistirmez

**`C5-stabil-malignite-02`**  —  hedef: **`high`**  (dayanak: `A8+C#5`)

> In the upper abdominal sections in the study area; According to the previous examination, hypodense lesions were observed in the liver, the largest of which was observed in the previous examination, with a diameter of 22 mm in the left lobe, which was evaluated in favor of metastasis in the first plan, stable.

*Gerekçe:* 'evaluated in favor of metastasis' = present (A8); patoloji yok, 'stable' dusurmez

**`C5-stabil-malignite-03`**  —  hedef: **`known_malignancy`**  (dayanak: `C#5`)

> There was no significant change in the dimensions of metastatic masses observed in T1 and L1 vertebrae.

*Gerekçe:* 'metastatic masses observed in T1 and L1' HUKUM; 'no significant change' yalniz degisimi olumsuzluyor


### C6-malignite-benign

**`C6-malignite-benign-01`**  —  hedef: **`intermediate`**  (dayanak: `C#4`)

> Nodules with a diameter of 5 mm in the right lung apex, 6 mm in diameter in the left upper lobe anterior segment and 5 mm in the lower lobe superior segment between pleuroparenchymal sequelae in the middle lobe, which may be compatible with metastasis, are observed.

*Gerekçe:* Nodullar sekel arasinda ama 'may be compatible with metastasis' - orta derece

**`C6-malignite-benign-02`** 🔄  —  hedef: **`None`**  (dayanak: `A8+C#12`)

> Structural distortion in the vicinity of the volume loss accompanying the right lung upper lobe anterior segment and a spiculated contour lesion, which is evaluated in favor of sequela fibrotic nodular formation, is observed in which volume loss is observed.

*Gerekçe:* v1.1 DUZELTME (2. denetim, bulgu 1.2): radyolog 'in favor of sequela fibrotic nodular formation' diye KESIN HUKUM vermis (A8: in favor of = present). #12'nin varsayilani da kararli benign hukmunun kazanmasi yonunde. YENI C KARARI (docs/33 §4.2): radyologun kesin benign hukmu, belgelenmis spikulasyonu ezer mi? Varsayilan EVET. KARSI KANIT KAYITLI: A34 (Fleischner) spikule kenarin malignite olasiligini ARTIRDIGINI yaziyor - bu karar bir bilgi kaybi tasir ve ilan edilir.

**`C6-malignite-benign-03`**  —  hedef: **`indeterminate`**  (dayanak: `A3+A18`)

> Volume loss in the upper lobe apex of both lungs, areas of structural distortion and atelectatic fibrotic sequelae changes, underlying malignancy cannot be excluded.

*Gerekçe:* Sekel degisiklikler + 'underlying malignancy cannot be excluded'


### C11-olumsuz-belirsiz

**`C11-olumsuz-belirsiz-01`**  —  hedef: **`None`**  (dayanak: `A1`)

> No suspicious nodular or mass-occupying lesion infiltrative involvement or consolidation area was detected in the lung parenchyma.

*Gerekçe:* 'No suspicious nodular or mass-occupying lesion ... was detected' - supheyi olumsuzluyor

**`C11-olumsuz-belirsiz-02`**  —  hedef: **`indeterminate`**  (dayanak: `A16`)

> Since contrast material was not given, it is not possible to comment on the size and number of lesions in the liver.

*Gerekçe:* Teknik kisitlilik: 'not possible to comment' + karaciger lezyonlari VAR ama karakterize edilemiyor


### C12-benign-belirsiz

**`C12-benign-belirsiz-01`** 🔄  —  hedef: **`None`**  (dayanak: `A26+C#12`)

> Lymphadenomegaly in the left axilla, the largest of which has a narrow diameter of 11 mm, hilar fat contents selected, possibly benign, and a few lymph nodes smaller than 1 cm in the right axilla

*Gerekçe:* v1.1 DUZELTME (2. denetim, bulgu 1.4): docs/31 #12'nin varsayilani 'benign (None)' idi, CSV'de 'low' yazilmisti - IC CELISKI. A26: fat-containing Lung-RADS'in benign ozellik listesinde; 'hilar fat contents ... possibly benign' radyologun hukmu. Yagli hilus iceren lenf nodu reaktif/benign lenf nodunun klasik tanimidir.

**`C12-benign-belirsiz-03`**  —  hedef: **`low`**  (dayanak: `C#12`)

> In the posterobasal segment of the lower lobe of the right lung, a 5.5 mm diameter nodule developed on the subpleural possible sequelae is observed.

*Gerekçe:* 'nodule developed on the subpleural possible sequelae' - benign zemin, kucuk nodul


### C13-ekstratorasik

**`C13-ekstratorasik-01`**  —  hedef: **`known_malignancy`**  (dayanak: `C#13`)

> In the current examination, the disease is progressive due to newly emerged metastases in the liver and spleen.

*Gerekçe:* 'newly emerged metastases in the liver and spleen' HUKUM; ekstratorasik ELENMEZ

**`C13-ekstratorasik-02`** 🔄  —  hedef: **`intermediate`**  (dayanak: `C#13`)

> In the upper abdominal sections included in the examination area, faintly circumscribed hypodense lesions at the level of liver segment 6, the largest of which was measured at 20 mm angle, were observed and were not detected in the previous examination (metastasis?).

*Gerekçe:* v1.1 DUZELTME (2. denetim, bulgu 1.5): '(metastasis?)' bir HIPOTEZDIR, ayirt edilemezlik degil. Yeni ortaya cikan 20mm karaciger lezyonu + metastaz hipotezi = yonlu supheler. C1-02 ve C4-orta-01 ile tutarlilik: ikisi de yonlu suphe icin intermediate aliyor. indeterminate ayirt edilemeyen ayirici tani (C4-orta-02, C16-02) ve teknik yetersizlik (C11-02) icin ayrilir.

**`C13-ekstratorasik-03`**  —  hedef: **`known_malignancy`**  (dayanak: `C#13`)

> Bladder ca in the follow-up, sporadic interlobular septal thickenings in both lungs, ground glass areas and peribronchial thickenings (primarily evaluated in favor of lymphangitis carcinomatosus), lung nodules, liver metastases .

*Gerekçe:* 'Bladder ca' bilinen + 'liver metastases' + lenfanjitis karsinomatoza


### C16-malignite-enf

**`C16-malignite-enf-01`** 🔄  —  hedef: **`known_malignancy`**  (dayanak: `C#5+C#16`)

> A few nodular densities measuring up to 7 mm in both lungs, more prominent in the right lung upper lobe posterior and lower lobe superior segment, were initially evaluated in favor of new metastatic nodular lesions due to the patient's known primary and lung metastasis, and are included in the diagnosis of infectious process differential.

*Gerekçe:* 'patient's known primary and lung metastasis' asserted; enfeksiyon ayirici tanida ama malignite BILINEN

**`C16-malignite-enf-02`**  —  hedef: **`indeterminate`**  (dayanak: `C#16`)

> irregularly circumscribed nodular consolidation areas may belong to infection, metastasis could not be excluded.

*Gerekçe:* 'may belong to infection, metastasis could not be excluded' - ayirici tani

**`C16-malignite-enf-03`** 🔄  —  hedef: **`not_mentioned`**  (dayanak: `A20+A27`)

> Although there is widespread infection, control for neoplasia is recommended.

*Gerekçe:* v1.1 DUZELTME (2. denetim, bulgu 1.1): 'control for neoplasia is recommended' bir AKSIYON ONERISIDIR, status degil (A20/Kritik kural 3). Bulgu enfeksiyon; A27 enfeksiyonu malignite olceginin DISINA koyuyor. Eski hedef 'low' kendi A20 kuralimizi ihlal ediyordu.


### A8-cikarim-ifadesi

**`A8-cikarim-ifadesi-01`**  —  hedef: **`not_mentioned`**  (dayanak: `A7`)

> There are radiological findings compatible with COPD with increased parenchymal aeration.

*Gerekçe:* 'compatible with COPD' - malignite ekseninde ifade YOK

**`A8-cikarim-ifadesi-02`**  —  hedef: **`not_mentioned`**  (dayanak: `A7`)

> Sequelae changes in the lingular segment of the left lung or a bud branch appearance compatible with the focal infective area are observed.

*Gerekçe:* Sekel + enfektif alan; malignite ekseninde ifade YOK


### A26-kalsifikasyon

**`A26-kalsifikasyon-01`**  —  hedef: **`intermediate`**  (dayanak: `A26+C#7`)

> When examined in the lung parenchyma window; Areas measuring up to 7 mm with spiculated contours containing calcifications are observed in the right lung lower lobe superior.

*Gerekçe:* 'spiculated contours CONTAINING CALCIFICATIONS' - kalsifikasyon A26 benign listesinde degil, spikulasyon supheli

**`A26-kalsifikasyon-02`**  —  hedef: **`intermediate`**  (dayanak: `A26+C#5+C#7`)

> When examined in the lung parenchyma window; nodular lesion with amorphous calcification in the periphery and spicular contour observed in the anterior segment of the right lung upper lobe was stable with a size of 11 mm.

*Gerekçe:* 'AMORPHOUS calcification' A26 listesinde YOK; 'spicular contour' supheli; 'stable' dusurmez


### A26-kalsifiegranulom

**`A26-kalsifiegranulom-01`** 🔄  —  hedef: **`not_mentioned`**  (dayanak: `A10`)

> Calcific granuloma with a diameter of 3 mm is observed in the anteromedial segment of the lower lobe of the left lung.

*Gerekçe:* Kalsifiye granulom; A26'nin benign kalsifikasyon paternlerinden biri degil ama 'granuloma' terimin kendisi kesin benign tanidir; malignite ifadesi yok -> not_mentioned degil None (aktif benign bulgu var, sadece malignite ekseninde deger yok). NOT: A10 kurali 'bulgu hic gecmiyor -> not_mentioned' idi; burada malignite BULGUSU gecmiyor ama BASKA bir bulgu (granulom) var. Dogru deger not_mentioned (malignite ekseninde ifade yok).


---

## 2 · Negatif Kontrol Takımı (23)

**Şema bu vakaların hiçbirinde malignite üretmeyecek — toleranssız kapı.**

### K-olumsuz-kitle

**`K-olumsuz-kitle-01`**  —  hedef: **`None`**

> In the upper abdominal sections within the image, no solid mass was detected as far as it can be observed within the borders of non-contrast CT. No intraabdominal free fluid or loculated collection is observed. A 30 mm defect is observed in the anterior abdominal wall at the epigastric level, and herniation of the colonic loops into the subcutaneous fatty tissue is observed.

*Gerekçe:* 'no solid mass was detected'

**`K-olumsuz-kitle-02`**  —  hedef: **`None`**

> A pleuroparenchymal sequela change is observed that does not give a subpleural mass contour to the right lung lower lobe superior segment.

*Gerekçe:* 'does not give a subpleural mass contour'

**`K-olumsuz-kitle-03`**  —  hedef: **`None`**

> In the upper abdominal organs within the sections, there is no mass with distinguishable borders as far as it can be observed within the borders of non-enhanced CT. Left-facing rotoscoliosis was observed in the thoracic vertebrae.

*Gerekçe:* 'no mass with distinguishable borders'

**`K-olumsuz-kitle-04`**  —  hedef: **`None`**

> When examined in the lung parenchyma window; No mass or nodule was detected in both lung parenchyma.

*Gerekçe:* 'No mass or nodule was detected'


### K-sekel-benign

**`K-sekel-benign-01`**  —  hedef: **`not_mentioned`**

> There are sequelae changes, nonspecific nodules in millimetric dimensions are observed.

*Gerekçe:* Sekel + nonspesifik nodul; malignite ifadesi yok

**`K-sekel-benign-02`**  —  hedef: **`not_mentioned`**

> Sequelae of parenchymal changes in both lungs and nonspecific nodules in millimeter sizes, some of them calcified.

*Gerekçe:* Sekel + kalsifiye nonspesifik nodul; malignite ifadesi yok

**`K-sekel-benign-03`**  —  hedef: **`not_mentioned`**

> Sequelae changes in both lungs and formation of a few millimetric nonspecific nodules.

*Gerekçe:* Sekel + nonspesifik nodul

**`K-sekel-benign-04`**  —  hedef: **`not_mentioned`**

> Pleuroparenchymal sequelae and mildly dependent increases in density in the lower lobes of both lungs

*Gerekçe:* Plevroparankimal sekel + dansite artisi


### K-enfeksiyon

**`K-enfeksiyon-01`**  —  hedef: **`not_mentioned`**

> Calcifications in the walls of the main bronchi and lobar bronchi Atelectasis in the right middle lobe Cylindrical-cystic bronchiectasis in the bilateral lungs Cylindrical bronchiectasis in the upper lobe of the right lung, minimal bud branch appearance Sequelae changes in the left lung upper lobe, infected bronchiectasis?

*Gerekçe:* Bronsektazi, atelektazi, kalsifikasyon; malignite ifadesi yok

**`K-enfeksiyon-02`**  —  hedef: **`not_mentioned`**

> However, viral pneumonia cannot be excluded.

*Gerekçe:* 'viral pneumonia cannot be excluded' - belirsizlik ENFEKSIYONA dair, malignite eksenine GIRMEZ

**`K-enfeksiyon-03`**  —  hedef: **`not_mentioned`**

> Structural distortion and areas of increase in density accompanying volume loss are observed in both lung lower lobe posterobasal segments, compatible with sequela parenchymal changes, and pneumonic infiltration is not observed in both lungs.

*Gerekçe:* Sekel + pnomonik infiltrasyon


### K-stabil-benign

**`K-stabil-benign-01`**  —  hedef: **`not_mentioned`**

> Sequelae fibroatelectasis changes causing structural distortion and volume loss in both lungs and calcified pleural plaque adjacent to the posterobasal segment of the left lung lower lobe ( findings are stable).

*Gerekçe:* Sekel fibroatelektazi + kalsifiye plevral plak

**`K-stabil-benign-02`**  —  hedef: **`not_mentioned`**

> Possible postoperative sequelae changes in the right lung upper lobe posterior segment, adjacent to the fissure and in the rib, are stable.

*Gerekçe:* 'Possible postoperative sequelae ... are stable'


### K-teknik

**`K-teknik-01`**  —  hedef: **`not_mentioned`**

> Lung parenchyma secondary to motion artifacts could not be optimally evaluated.

*Gerekçe:* 'could not be optimally evaluated' - teknik cekince

**`K-teknik-02`** 🔄 (v1.1'de eklendi)  —  hedef: **`indeterminate`**

> The right lobe of the thyroid gland is wider than normal, and hypodensity is observed, which cannot be clearly distinguished from artifact, which may also be compatible with the nodule.

*Gerekçe:* v1.1 DUZELTME (docs/33 §4.3 yeni C karari): tiroidde tanimli bir hipodansite/olasi nodul VAR ama artefaktan ayirt edilemiyor -> lezyon var, karakterize edilemiyor kuralina gore indeterminate. K-teknik-01'den farki: orada hicbir lezyon tarif edilmiyor, yalniz genel degerlendirme kisitliligi var.


### K-sablonnegatif

**`K-sablonnegatif-01`** 🔄 (v1.1'de eklendi)  —  hedef: **`not_mentioned`**

> Pericardial effusion-thickening was not observed.

*Gerekçe:* 

**`K-sablonnegatif-02`** 🔄 (v1.1'de eklendi)  —  hedef: **`not_mentioned`**

> No enlarged lymph nodes in prevascular, pre-paratracheal, subcarinal or bilateral hilar-axillary pathological dimensions were detected.

*Gerekçe:* 


### K-postop

**`K-postop-01`** 🔄 (v1.1'de eklendi)  —  hedef: **`not_mentioned`**

> Postoperative changes in the sternum.

*Gerekçe:* 

**`K-postop-02`** 🔄 (v1.1'de eklendi)  —  hedef: **`not_mentioned`**

> Postoperative changes in the pericardium.

*Gerekçe:* 


### K-amfizem

**`K-amfizem-01`** 🔄 (v1.1'de eklendi)  —  hedef: **`not_mentioned`**

> Paraseptal and minor centrilobular emphysematous changes in both lungs .

*Gerekçe:* 

**`K-amfizem-02`** 🔄 (v1.1'de eklendi)  —  hedef: **`not_mentioned`**

> Emphysema, mosaic density differences, sequela fibrotic changes and millimetric nonspecific nodules in both lungs.

*Gerekçe:* 


### K-koroner

**`K-koroner-01`** 🔄 (v1.1'de eklendi)  —  hedef: **`not_mentioned`**

> There is calcification in the coronary arteries.

*Gerekçe:* 

**`K-koroner-02`** 🔄 (v1.1'de eklendi)  —  hedef: **`not_mentioned`**

> Calcific plaques and coronary stents are present in the aorta and coronary arteries.

*Gerekçe:* 


---

## 3 · Çok Cümleli Rapor Vakaları (5)

Toplama kuralının ("en yüksek şüpheli bulgu kazanır") tek testi. Her rapor
Findings bölümünün tamamıdır; belirleyici cümle işaretli.

### `R1-karisik` — train_10004_a  (14 cümle, profil: malignite+benign karisik (yuzeysel))

**Bileşik hedef: `None`**  (dayanak: `A1+C#1`)

**Belirleyici cümle (#7):**
> Thoracic esophageal calibration was normal and no significant tumoral wall thickening was detected.

*Gerekçe:* 14 cumlede tek malignite-eksenindeki kelime (tumoral) NEGATIF KAPSAMDA: 'no significant tumoral wall thickening'. Diger butun cumleler (amfizem, sekel, lenf nodu normal, bobrek kisti?) malignite ekseni disinda. Toplama kurali (#9, en yuksek supheli bulgu kazanir) uygulaninca, tek malignite-eksenindeki bulgu negatif oldugu icin sonuc None. Bu vaka onemli: yuzeysel 'malignite+benign birlikte' profili, cumle duzeyinde cozulunce TEK BASINA NEGATIF cikti - toplama kuralinin dogru calistigini gosterir.

### `R2-net-pozitif-negatif` — train_10001_a  (13 cümle, profil: malignite VAR (yuzeysel))

**Bileşik hedef: `None`**  (dayanak: `A1`)

**Belirleyici cümle (#5):**
> Thoracic esophageal calibration was normal and no significant tumoral wall thickening was detected.

*Gerekçe:* Tek malignite-eksenindeki cumle NEGATIF KAPSAMDA (ayni kalip). Ground-glass dansiteler, 2mm nonspesifik nodul, karaciger/sürrenal 'space-occupying lesion yok' - hicbiri malignite terimi tasimiyor. Composite None.

### `R3-yalniz-benign` — train_10051_a  (14 cümle, profil: yalniz benign VAR)

**Bileşik hedef: `not_mentioned`**  (dayanak: `A10`)

**Belirleyici cümle (#6):**
> Mild sequelae changes are observed at the apical level.

*Gerekçe:* Raporda HICBIR malignite-eksenindeki terim gecmiyor (M-deseni 0 eslesme). Sekel degisiklikler, peribronsiyal kalinlik, D12 vertebrada hemanjiyom (benign vaskuler lezyon, ayri terim) - malignite ekseninde ifade yok. Composite not_mentioned.

### `R4-tamamen-normal` — train_10006_a  (10 cümle, profil: hicbiri yok (normal))

**Bileşik hedef: `not_mentioned`**  (dayanak: `A10`)

**Belirleyici cümle (#7):**
> In the examination made in the lung parenchyma window; No active infiltration or mass lesion was detected in both lungs.

*Gerekçe:* 'mass lesion' M-deseninde (malignan/metasta/carcinom/tumoral/neoplas/spicul) YAKALANMIYOR - kelime dagarcigi disinda. Raporda malignite-eksenindeki hicbir terim yok. Composite not_mentioned.

### `R5-negatif-belirsizlik` — train_1000_a  (10 cümle, profil: yalniz belirsiz VAR (yuzeysel))

**Bileşik hedef: `None`**  (dayanak: `A1+C#new-negbelirsiz`)

**Belirleyici cümle (#7):**
> No suspicious mass or nodular space-occupying lesion was observed in the lung parenchyma.

*Gerekçe:* YENI GOZLEM: 'suspicious' kelimesi BELIRSIZ deseninde ama burada NEGATIF KAPSAMDA - 'no suspicious mass ... was observed' supheli bulgunun VARLIGINI degil YOKLUGUNU bildiriyor. Bu, A3/A18'in kapsadigi 'X cannot be excluded' (supheyi ORTADAN KALDIRAMAYAN belirsizlik) kaliplarindan FARKLI bir kaliptir: burada suphe acikca DISLANMIS. YENI C KARARI: 'no suspicious X was observed/detected' -> None (supheyi degil, bulgunun kendisini olumsuzluyor), 'X cannot be excluded' -> uncertain/indeterminate (supheyi ortadan KALDIRAMIYOR). Ayrim negasyonun NEYI kapsadigina gore yapilir (C#1 ile ayni ilke, suphe ifadesine uygulanmis hali).

---

## 4 · Revizyon defteri (v1.0 → v1.1)

| vaka | eski hedef | yeni hedef | sebep |
|---|---|---|---|
| `C16-malignite-enf-03` | low | not_mentioned | A20 ihlali: oneri status degildir; enfeksiyon A27 ile olcek disi |
| `C6-malignite-benign-02` | low | None | A8 + #12: radyologun kesin benign hukmu kazanir (karsi kanit A34 kayitli) |
| `C4-derece-yuksek-01` | known_malignancy | high | Yeni C karari: known_malignancy esigi yazili bilinen kanser gerektirir |
| `C13-ekstratorasik-02` | indeterminate | intermediate | '(metastasis?)' yonlu hipotez, ayirt edilemezlik degil |
| `C12-benign-belirsiz-01` | low | None | docs/31 #12 ile ic celiski duzeltildi (A26 fat-containing benign patern) |
| `C12-benign-belirsiz-02` | low (VAKA CIKARILDI) | - | C12-01 ile neredeyse ayni cumle (mukerrer); yerine A26-kalsifiegranulom-01 eklendi |
| `K-teknik-02` | not_mentioned | indeterminate | Yeni C karari: tarif edilen lezyon (tiroid hipodansitesi) var, karakterize edilemiyor |
| `C16-malignite-enf-01` | - | - (dayanak etiketi duzeltildi) | Klerikal: dayanak C#13 -> C#5+C#16 |
| `MALIGN_URETIR (kod)` | indeterminate DAHIL | indeterminate HARIC | indeterminate yonlu suphe degil epistemik belirsizliktir (docs/31 #8 ile uyum) |