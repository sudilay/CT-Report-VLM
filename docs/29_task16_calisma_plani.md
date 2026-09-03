# TASK-16 · Malignite Değerlendirme Şemasının Tanımlanması — Çalışma Planı **v2**

**Tarih:** 2026-09-03 · **Durum:** onay bekliyor, uygulamaya başlanmadı
**Kaynak listedeki yeri:** T-03 (→ TASK-16, 17, 18, 19) · **Faz 3'ün ilk görevi**
**Önkoşullar:** TASK-15 kapandı · erişim denetimi yapıldı, engel yok (§3.5)
**v1 → v2:** bağımsız denetim sonrası yeniden yazıldı → [`docs/32`](32_task16_bagimsiz_denetim.md)

> Bu belge okunup **onaylanmadan** kod yazılmaz, şema taslağı üretilmez.
> v1 uygulanmadı: bağımsız denetim 25 bulgu çıkardı, 21'i kabul edildi ve plan
> yapısal olarak değişti.

---

## 0 · İki numaralandırma sistemi — karıştırmayın

| sistem | ne | örnek |
|---|---|---|
| **`T-nn`** | kaynak listedeki **14 madde** (`radyoloji_raporu_degerlendirme_tasklari.xlsx`) | **T-03** = değerlendirme şeması · **T-13** = AUROC/duyarlılık/kalibrasyon karşılaştırması (Faz 5) |
| **`TASK-nn`** | plandaki **47 görev** (`RADYOLOJI_VLM_TASK_LISTESI.xlsx`) | **TASK-16** = bu görev · **TASK-13** = elle doğrulama, **tamamlandı** |

**T-13 ≠ TASK-13.** Bağımsız denetim bu ikisini karıştırdı; uyarı buraya kondu.

---

## 1 · Bu görev ne üretir, ne üretmez

**Üretir:** bir **karar şeması** — rapordan çıkarılmış yapılandırılmış bulgular
verildiğinde, o raporun malignite açısından hangi sınıfa düştüğünü söyleyen
kurallar bütünü.

| çıktı | dosya |
|---|---|
| şemanın kendisi (sınıflar, öncelikler, sınır kuralları) | `configs/degerlendirme_semasi.json` |
| şema doğrulayıcı + testler | `src/radyovlm/evaluation/sema.py` · `tests/test_sema.py` |
| her kararın gerekçesi ve kaynağı | `docs/30_task16_sema_gerekce.md` |
| **klinik yargı isteyen kararlar listesi** (katmanlı) | `docs/31_task16_klinik_karar_listesi.md` |
| **kilitli** sınır vakası takımı + hedef sınıfları | `data/processed/sema_sinir_vakalari.csv` + SHA-256 |
| **negatif/benign kontrol takımı** | `data/processed/sema_negatif_kontrol.csv` + SHA-256 |
| gözle inceleme sayfası (CSV'den üretilir) | `outputs/task16/sema_tezgahi.html` |

**Üretmez:** model yok, etiketleme yok, doğruluk ölçümü yok. Sözlükler TASK-17,
altın standart TASK-18, uyum ölçümü TASK-19.

### ⚠ 1.1 Alan ≠ kural — bu görevin varlık sebebi

Alan sözlüğü belgesi ~250 **alan** ve izinli değerlerini tanımlar. Şemamızın
ihtiyacı olan şey ise **öncelik kuralıdır**: çelişen kanıtta hangisi kazanır.

> **Belge NE çıkarılacağını söyler. NASIL karar verileceğini söylemez.**

Somut örnek — *"Stable, calcific parenchymal metastases in both lungs."*
Belgeye göre `stable_long_term_nodule`=yes · `metastatic_lung_disease_suspected`=yes.
**Peki `radiology_malignancy_suspicion_level` ne olacak?** Belge söylemiyor.

**Bu cümlenin doğrudan sonucu §2'dedir:** belgeden türettiğimiz her öncelik,
eşik ve ağırlık kuralı **bizim kurgumuzdur** ve klinik onay gerektirir — ama o
onay **işi bloke etmez** (§2.3b).

⚠ **İnce ayrım:** belge §12.2 *cümleyi alan değerine çevirme* kuralları verir
(*"dışlanamaz" → `uncertain`*) ve bunlar **A**'dır (§2.2b). Vermediği şey **alan
değerlerini birbiriyle tartma** kuralıdır (*iki alan çelişince hangisi kazanır*).
Şemanın ürettiği tam olarak ikincisidir.

### 1.2 Kapsam dışı — bilinçli daraltma

| dışarıda | neden | nereye |
|---|---|---|
| Sybil'in §11'deki **27 özet alanı** | Türetilmiş toplama alanları; malignite karar mantığını karmaşıklaştırır | ayrı türetme görevi, Faz 3 sonrası |
| Nodül yönetim/takip önerileri | Şema sınıf üretir, yönetim önerisi üretmez | kapsam dışı |
| ~250 alanın tamamının çıkarımı | TASK-16 şema yazar, çıkarıcı yazmaz | TASK-17 |

---

## 2 · Kim karar veriyor — otorite modeli **(v2'de yeniden çizildi)**

TASK-15 her şeyi kurup **sonunda** otoritenin olmadığını fark ettiği için askıya
alındı. Bu görevde otorite **başta** tanımlanıyor.

### 2.1 Bağlayıcı proje kuralı — D27

> **"Altın açıklamayı kural yazarı üretemez.** 'Doğru'nun tanımı dış
> kaynaklardan gelir. Kılavuzda koddan türetilmiş kural yoktur."

### 2.2 Kararların üç türü — **sınır v2'de sıkılaştırıldı**

| tür | ölçüt | örnek | onay |
|---|---|---|---|
| **A · Aktarılan** | Kaynakta **karar kuralı olarak açıkça yazılı**. Alan tanımı A yapmaz; kuralın kendisi yazılı olmalı | **Belge §12.2'nin tamamı** (§2.2b) · *"Lenf nodu kısa aksından ölçülür"* (RECIST 1.1) | ❌ atıf yeter — **tablo/paragraf düzeyinde** |
| **B · Ölçülen** | Korpustan sayılabilir nesnel olgu. **Yalnız kapsam belirler, klinik ağırlık vermez** | *"`sequela` 12.177 cümlede geçiyor → sözlük kapsamına girer"* | ❌ sayı yeter |
| **C · Klinik yargı** | Kaynakta yazılı olmayan **her** öncelik, eşik, ağırlık ve eşleme | *"kalsifikasyon kanıtlanmış metastazı ezer mi?"* · **6→4 eşleme matrisi** · kılavuz çatışma önceliği · *"`sequela` maligniteyi dışlar mı?"* | ✅ **uzman onayı** |

**⚠ v2'nin en önemli değişikliği:** v1, belgeden türetilen ~40 kuralı A saymıştı.
Belge **karar kuralı içermediği** için (§1.1) bu yanlıştı. Şimdi kural şu:

> **Kaynakta cümle olarak yazılı olmayan hiçbir öncelik/eşik/ağırlık A değildir.**

### ⭐ 2.2b Belge §12.2 gerçek bir karar kuralı tablosudur — C listesini küçültür

Belgenin **§12.2 "Negasyon ve Belirsizlik Eşleme Tablosu"** ve içindeki **üç
"Kritik kural"**, alan tanımı değil **açık karar kuralıdır**:

| ifade | eşlenen | tür |
|---|---|---|
| *"dışlanamaz", "ekarte edilememektedir", "göz ardı edilemez"* | **`uncertain`** — belgenin vurgusuyla *"present değil!"* (Kritik kural 1) | **A** |
| *"şüpheli görünüm", "kuşkulu"* | `present` + `suspicious_appearing=yes` | **A** |
| *"stabildir", "önceki ile aynı boyuttadır"* | `stable_nodule=yes` / `growth_status=stable` | **A** |
| *"artmıştır"* / *"azalmıştır"* / *"kaybolmuştur"* | `growth_status=increased / decreased / resolved` | **A** |
| *"klinik korelasyon önerilir"* | **status DEĞİL** → ayrı alan (Kritik kural 3) | **A** |
| *"düşündürecek görünüm saptanmadı"* | `absent` — sade *"saptanmadı"* ile **aynı status** (Kritik kural 2) | **A** |

**Sonuç: kesinlik, negasyon, stabilite ve büyüme okumasıyla ilgili her kural
A'dır ve C listesinden düşer.** Bu, `ctx-1.1`'de yaptığımız işi dış kaynakla
**doğruluyor** — `docs/08` §1 zaten K11 ölçütümüzün belgenin Kritik kural 1'iyle
**birebir** örtüştüğünü kaydetmişti.

### ⚠ 2.2c Belge §3'ün başlığı içeriğini karşılamıyor

§3'ün başlığı *"Lung-RADS, Fleischner ve Nodül Yönetimi Alanları"*. İçinde
**yalnız iki alan** var: `pet_bt_recommended` ve `biopsy_recommended`.
**Lung-RADS kategorisi yok, boyut eşiği yok, Fleischner dansite kuralı yok.**

Belge o kılavuzlara **atıf veriyor ama içeriklerini aktarmıyor.** Nodül
boyut/dansite eşiği gerekirse **doğrudan kılavuzdan** alınacaktır (§3.1 sıra 2-3;
ikisi de ücretsiz).

**Dürüst sonuç:** C listesi v1'e göre şişiyor (öncelik/eşik/ağırlık kuralları C
oldu) ama §12.2 sayesinde **korkulduğu kadar değil**. Gerçek sayı adım 1'de
**ölçülecek** — tahmin edilmeyecek.

### 2.3 C kararları katmanlandırılır

| katman | ne | uzman onayı |
|---|---|---|
| **C-1 · Çekirdek** | Şemanın iskeletini belirleyen kararlar | `sema-1.0` dondurması için gerekli |
| **C-2 · Ağırlıklı** | Varsayılanı yazılabilen, sonucu belirgin etkileyen | tercih edilir |
| **C-3 · Sınır** | Nadir vakalar; varsayılan yeterli | gerekmez |

Her C-2/C-3 maddesi **önceden yazılmış bir varsayılanla** şemaya girer ve
`karar_kaynagi: "gecici_varsayilan"` bayrağını taşır. Cevap gelince **yalnız o
satır** güncellenir.

### 2.3b Uzman onayı iş akışını bloke etmez

| şema hâli | ne yapılabilir | uzman onayı |
|---|---|---|
| **`sema-0.9-taslak`** | Kurulur, koşulur, TASK-17/18'e girdi olur, iterasyona alınır | gerekmez |
| **`sema-1.0`** (dondurulmuş) | Nihai sayıların (T-13) dayanağı olur | gerekir |

Şema sürümlüdür (`sema-1.x`); yanlışsa TASK-17/18'de anlaşılır ve revize edilir —
geri dönüşsüz değildir. Uzman onayının sağladığı tek şey şemaya *"klinik olarak
dayanaklı"* diyebilmektir ve bu yalnız nihai raporlamada gerekir.

Bu projede patoloji ground truth'u zaten yoktur: ölçülen şey *"model radyoloğun
raporuyla uyuşuyor mu"*dur. Şema bunun üstüne bir katman ekler; katmanın
dayanağının kaydı §2.4'tedir.

### 2.4 Uzman onayı alınmayacaktır — bağlayıcı kapsam kararı

**Bu çalışmada C kararları için klinik uzman onayı alınmayacaktır.** Karar
2026-09-03'te verilmiştir.

Sonuçları:

1. Bütün C kararları **kalıcı olarak belgelenmiş mühendislik varsayılanı** kalır.
2. Şema `sema-1.0` olarak dondurulursa, **klinik dayanağının bulunmadığı** rapora
   yazılır.
3. T-13'te raporlanacak sayılar *"modelin bu şemayla uyumu"*dur; **klinik doğruluk
   değildir.**

Bu sınır TASK-15'in kapanışındaki yöntemle işlenir: eksiklik gizlenmez, ölçülür
ve ilan edilir. C kaydı (`docs/31`) bu yüzden yine üretilir — her kararın hangi
varsayılanı aldığı ve neden aldığı yazılı olmadan şema savunulabilir olmaz.

### 2.5 Belgede onay izi YOK — kayda geçirilir

Belge tarandı: *onay · gözden geçirme · yazar · imza · revizyon · katkı ·
teşekkür · Dr./Prof./Doç.* — **hiçbiri yok.** "Radyolog" kelimesi 5 kez geçiyor,
hepsi **alan açıklamalarının içinde** (*"radyolog terminolojisine bakılır"*) —
raporu **yazan** radyoloğu tarif ediyor, belgeyi onaylayanı değil. Belge doğrudan
kaynakçayla bitiyor, imza bloğu yok.

**Meta veri:** son değiştiren `chn calisir` · şirket **BAYKAR** · 2026-07-13.

**Sonuç:** belge **atıf verdiği primer literatür oranında** meşruiyet taşır.
Belgenin kendi kurgusu olan kısımlar (özellikle 6 düzeyli şüphe ölçeği — hiçbir
atfı yok) **C**'dir.

### 2.6 İş bölümü

| kim | sorumluluk |
|---|---|
| **Claude** | Taslak şema · korpus kanıtı · sınır ve kontrol takımları · C listesi · kod, doğrulayıcı, testler |
| **Codex** | **Ayrışma dedektörü** — sınır vakalarını bağımsız yargılar; ayrıştıkları vakalar C kaydında **öncelikli** işaretlenir. *Altın üretmez* (bkz. [`docs/32`](32_task16_bagimsiz_denetim.md) §5.2) |
| **Yürütücü** | Tasarım kararları (§5) · sınır vakalarının gözle denetimi |

---

## 3 · Dış kaynaklar — tam liste

### 3.1 Klinik kaynaklar

| # | kaynak | ne sağlar | erişim |
|---|---|---|---|
| 1 | **Alan Sözlüğü ve Veri Rehberi** — *"Akciğer BT Raporlarından BDM ile Yapılandırılmış Veri Çıkarımı (Sybil Modeli Veri Analizi İçin)"*, **Versiyon 12 · 2026-07-07** · BAYKAR · 13 sayfa, 16 bölüm | ~250 alan · 6+1 şüphe ölçeği · §3 Lung-RADS/Fleischner alanları · §12 Türkçe negasyon sözlüğü · §15 patoloji · 10 kılavuza atıf | ✅ depoda |
| 2 | **ACR Lung-RADS v2022** | Nodül kategorileri, boyut eşikleri | ⚠ ücretsiz ama **otomatik indirilemiyor** — [acr.org](https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/Lung-RADS) tarayıcıdan |
| 3 | **Fleischner Society 2017** — MacMahon et al., *Radiology* 284(1):228 | İnsidental nodül; solid/subsolid/part-solid | ⚠ ücretsiz ama **otomatik indirilemiyor** (403) — [doi](https://pubs.rsna.org/doi/10.1148/radiol.2017161659) tarayıcıdan |
| 4 | **RECIST 1.1** — Eisenhauer et al., *Eur J Cancer* 2009;45:228 | Ölçülebilir lezyon, **kısa aks** kuralı | ✅ [serbest PDF](https://project.eortc.org/recist/wp-content/uploads/sites/4/2015/03/RECISTGuidelines.pdf) |
| 5 | **RSNA COVID-19 raporlama konsensusu** · **CO-RADS** | COVID BT raporlama dili, 1–5 şüphe sınıflaması | ✅ [RSNA](https://pubs.rsna.org/doi/10.1148/ryct.2020200152) · [CO-RADS](https://pubs.rsna.org/doi/10.1148/radiol.2020201473) — ⭐ **korpusun %21'i COVID** |
| 6 | **IASLC 9. TNM** · **CAP Lung Cancer Protocol** | Evreleme, patoloji şablonu | ✅ serbest — Faz 7 |
| 7 | **Brock (PanCan)** · **Mayo** modelleri | Nodül malignite **olasılığı** | TASK-16'da **gerekmiyor** — T-08 |
| 8 | **WHO Thoracic Tumours 5. baskı** · **AJCC-8** | Histoloji, evreleme | ⚠ ücretli olabilir — **Faz 7** |

### 3.2 NLP ve terminoloji

| # | kaynak | durum |
|---|---|---|
| 9 | **RadGraph-XL** — Delbrouck et al., ACL Findings 2024 | ✅ kaynağından doğrulandı |
| 10 | **RadLex** (BioPortal) | ✅ **API doğrulandı**, %67 kapsama ölçüldü (§3.7) |
| 11 | **NegEx** (2001) · **ConText** (2009) | ✅ uygulandı (`ctx-1.1`) |
| 12 | **CheXpert labeler** — Irvin et al., AAAI 2019 | belirsizlik politikası emsali — TASK-16'da yararlı |
| 13 | ~~UMLS / SNOMED~~ | ❌ gerekmiyor — RadLex yeterli |

### 3.3 ⚠ Kılavuzlar bu korpusta doğrudan uygulanamaz — ölçülmüş

| eksen | ölçüm | sonuç |
|---|---|---|
| Kalsifikasyon paterni | `popcorn` **0** · `central` 26 · `laminated` 26 · `punctate` 50 | eksen pratikte **YOK** |
| Fleischner dansite üçlüsü | `part-solid` 103 · `subsolid` **5** | üçlü **YOK** |
| Baskın eksenler | `calcific*` **17.193** · `ground-glass` **13.280** | korpusun gerçek sözlüğü |
| Benign niteleyici | `sequela` **12.177** · `granuloma` 117 | ⚠ sıklık **kapsam** belirler, **benignlik kanıtlamaz** (§2.2/B) |

**Sonuç:** TASK-17 korpus-güdümlü olacak; kılavuz **referans**, kaynak değil.

### 3.4 ⚠⚠ Kohort uyumsuzluğu — şemayı doğrudan belirliyor

| | Alan sözlüğü belgesinin varsaydığı | **CT-RATE'in gerçeği** |
|---|---|---|
| kohort | akciğer kanseri **taraması** (Sybil/NLST bağlamı) | genel toraks BT · yaş medyanı **46** · **%21 COVID** (8.462 cümle) |
| baskın soru | insidental nodül malign mi | akut/enfeksiyöz süreç var mı |

**Tarama kılavuzları akut enfeksiyöz bulguları hesaba katmaz.** Lung-RADS
mantığını doğrudan CT-RATE'e uygulamak, pnömoni ve post-op değişiklikleri
malignite şüphesine yazar ve **yanlış pozitifleri patlatır** — projenin ana
hedefinin tam tersi.

**Bağlayıcı tasarım kararı:** şemanın karar ağacında **akut enfeksiyon /
inflamasyon / atelektazi ayrımı en üst öncelikli filtredir**; Lung-RADS türevi
kurallar **yalnız izole parankimal nodüllere** uygulanır. *(Bu bir C-1
maddesidir.)*

⚠ CT-RATE'in klinik bağlamı (yatan hasta mı, ayaktan mı, acil mi) **belgelenmemiştir**;
"tarama değildir" kesin, ama kohortun tam niteliği varsayılmayacaktır.

### 3.5 Erişim denetimi — engel yok

| kaynak | hesap | bekleme |
|---|---|---|
| CT-RATE · RadLex/BioPortal | ✅ ikisi de alındı | — |
| RECIST · CO-RADS · IASLC · CAP | ❌ gerekmiyor | yok |
| ⚠ **Lung-RADS · Fleischner** | ücretsiz ama **programla indirilemiyor** (302 / 403) — insan tarayıcısıyla indirilmeli | yok |
| TCIA (görüntü + NLST açık alt küme) | ❌ kısıtsız | yok |
| ~~UMLS~~ | 3–5 iş günü | **gerekmiyor** |

**TASK-16'yı bekletecek hiçbir izin süreci yok.**

### 3.6 Faz 5 / 7 veri erişimi — **§3.5 ile uyumlulaştırıldı**

⚠ v1'de bu bölüm §3.5 ile çelişiyordu (denetim #16). Tek gerçeklik:

| ihtiyaç | durum | başvuru |
|---|---|---|
| 3B BT görüntüsü (T-05–T-07) | TCIA/IDC'de **70.000+ NLST taraması açık**; LIDC-IDRI açık | ❌ hayır |
| Patoloji **görüntüsü** (SVS) | NLST'nin 1.200+ görüntüsü TCIA'da açık | ❌ hayır |
| Klinik sonuç tabloları | NLST'nin **kamuya açık alt kümesi** TCIA'dan iniyor | ❌ hayır |
| NLST'nin **tam** veri kümesi | NCI **CDAS** başvurusu | ⚠ muhtemelen gerekmiyor |
| **Serbest metin patoloji RAPORU** (T-11) | ⛔ açık veride **yok** | ⛔ yalnız Bakanlık kohortu |

⚠ **Doğrulanmadı:** TCIA'daki NLST açık klinik alt kümesinin **hangi
değişkenleri** taşıdığı (kanser teşhisi var mı, histoloji var mı) fiilen
indirilip kontrol edilmedi. **Faz 5 planlanmadan önce yapılacak.**

**Yerel varlıklar (2026-09-03 tarandı):** `~/Desktop/nlst/` — 2.014 DICOM,
6 hasta, **yalnız görüntü, klinik tablo yok** · TCIA Data Retriever kurulu ·
COPLE-Net (COVID segmentasyon).

### 3.7 RadLex kapsama yoklaması

15 kavramlık örneklemde **tam eşleşme 10/15 (%67)**. Eşleşmeyenler tam olarak
öngörülen sınıf — **çeviri artefaktları**: `sequela` · `space_occupying_lesion` ·
`lytic_destructive_lesion` · `cardiothoracic_ratio` · `cardiomegaly`.

**Beklenti kaydı:** TASK-11'in eşlemesi %100 olmayacak; karşılığı olmayan `null`
kalacak, **uydurma kimlik yazılmayacak.**

---

## 4 · Hangi veriyle, nasıl çalışacağız

### 4.1 Korpus: CT-RATE

| | CT-RATE | RadTr |
|---|---:|---:|
| toraks raporu | **25.692** | 429 |
| `spicul\|malignan\|metasta` cümlesi | **3.253** | ~0 |
| malignite geçen belge | 217 çalışma | **7** |
| erişim | açık | `test` **mühürlü** |

RadTr'de 7 belgeyle şema sınanamaz. TASK-16 **CT-RATE üzerinde** yapılır.

### 4.2 Şema dilden bağımsızdır

TASK-15'in kurduğu ayrım: ortada **dilsiz kavramlar** var, her dil için ayrı
**yüzey** dosyası. TASK-16 kavram ve karar kuralı üretir, yüzey üretmez — yüzey
işi TASK-17'nindir ve orada iki dil de yazılır. Üstelik CT-RATE'in İngilizcesi
Türkçeden çevrilmiştir; kalıplar (`in favor of` = *"lehine"*) Türk radyoloğunun
yazımıdır.

### 4.3 ⚠ Bölünme — **v2'de somutlaştırıldı**

**Sorun (v1'de vardı):** TASK-19 sırada TASK-16/17/18'den sonra; şema tüm
korpusu görmüş olurdu. TASK-14'te bizzat yasakladığımız şey:
*"Bölünme sözlük kurulmadan **önce** yapılmalı."*

**v1'in kusuru (denetim #4):** "held-out havuz ayrılır" dedim ama **boyutunu ve
kotasını tanımlamadım**. Boyutsuz rezervasyon ya veri israf eder ya nadir
malignite vakalarını kapsayamaz.

**v2 kuralı — sayısal ve geri dönüşsüz:**

```
GELISTIRME havuzu = CT-RATE train (20.000 hasta) eksi asagidaki

DEGERLENDIRME kilidi:
  (a) CT-RATE'in KENDI resmi valid bolunmesi (1.304 hasta) — DOKUNULMAZ
      (karsilastirilabilirlik icin, AGENTS.md kurali)
  (b) train'den hasta duzeyinde %15, sabit tohum 20260903, TEK SEFER
```

- Ayırma **bir kez** yapılır, dosyaya yazılır, **geri dönülmez**
- TASK-16/17/18 bu kilide **hiç dokunmaz**; betiklere kilit konur (TASK-14 emsali)
- Sızıntı kontrolü otomatik teste bağlanır
- Test kümesinin **nihai boyutu** TASK-18'in prevalans ölçümünden sonra bu
  kilidin **içinden** seçilir — kilit sonradan **genişletilmez**

### 4.4 ⚠ Plan metnindeki örnek cümleler — maruziyet kaydı

§6'daki 8 örnek cümle, bölünme ayrılmadan **tüm korpustan** çekildi (denetim #5).

**Kayıt:** bu 8 cümlenin `study_id`'leri adım 0'da çıkarılacak ve değerlendirme
kilidine düşenler **işaretlenecek**. Maruziyet 8 cümledir ve TASK-14'te
uygulanan yöntemle (*"maruziyet ölçüldü, kayda geçti"*) raporlanır.

**Bağlayıcı kural:** adım 4'ün sınır ve kontrol takımları **yalnız geliştirme
havuzundan** çekilir.

### 4.5 İnceleme yöntemi

Kanonik kayıt **CSV**'dir (`sema_sinir_vakalari.csv`, `sema_negatif_kontrol.csv`).
`outputs/task16/sema_tezgahi.html` bu CSV'lerden **üretilir**, kendi başına veri
kaynağı değildir. Tezgâhta her satır: gerçek cümle · çıkarılmış varlıklar ve
kesinlikleri · **kilitli hedef sınıf** · şemanın verdiği sınıf · **tetiklenen
kural** · karar türü (A/B/C) · kaynak atfı · **inceleyici bayrağı
(onay/red/revizyon)**.

---

## 5 · Onay bekleyen tasarım kararları

### 5.1 Karar A — sınıf ölçeği

**Belgeden okunan ölçek** (§1, `radiology_malignancy_suspicion_level`):

```
None -> low -> indeterminate -> intermediate -> high -> known_malignancy   + not_mentioned
```

Belgenin notu: *"Rapor diline göre malignite şüphesi düzeyi. **Kesin kanser
label'ı değildir.**"*

**6 anlamlı düzey + `not_mentioned`** (sonuncusu düzey değil, veri yokluğu
işareti; ölçeğe katmak sıralamayı bozar).

⚠⚠ **Ölçeğin içinde çözülmemiş belirsizlik → C-1:** `indeterminate` ile
`intermediate` **aynı sıralı ölçekte** duruyor ama farklı şeyler — biri epistemik
(*"karar verilemiyor"*), diğeri derece (*"orta şüphe"*). Aynı eksende sıralama
anlamını yitirir.

**Öneri: belgenin 6+1 ölçeğini şemada sakla, raporlamayı 4 sınıf üzerinden yap.**

⚠ **Düzeltme (denetim #18):** v1 bu eşlemeye *"kayıpsız"* demişti. **Yanlış.**
6 kategoriyi 4'e indirgemek **kayıplıdır**. Doğrusu: *şema 6+1'i sakladığı için
**artefaktta** bilgi kaybolmaz; ama raporlanan 4 sınıf kayıplı bir görünümdür ve
hangi klinik ayrımın feda edildiği belgelenir.*

⚠⚠ **6→4 eşleme matrisi C-1'dir (denetim #14).** `intermediate` ve `low`
düzeylerinin "belirsiz"e mi "pozitif/negatif"e mi gideceği **klinik karardır** ve
doğrudan yanlış pozitif/negatif oranlarını belirler. Plan yazarı belirleyemez.

### 5.2 Karar B — karar düzeyi

Kaynak tanım *"raporların etiketlenmesi"* diyor → rapor düzeyi. Çıkarımımız
**varlık düzeyinde** (anma başına satır + ofset). Arada toplama katmanı gerekiyor.

**Öneri: iki düzeyli şema.**

```
varlik (entities.parquet, ofsetli)
      |  [GIRDI KALITE FILTRESI - §7]
      v
  BULGU SINIFI  (kanit cumlesiyle)
      |  toplama kurali  <- C-1
      v
  RAPOR SINIFI
```

Toplama kuralının kendisi (*"en yüksek şüphe kazanır"* ve istisnaları) **C-1**'dir.

---

## 6 · Şemayı gerçek cümleler üzerinde görmek

Hepsi CT-RATE'ten, `sentences.parquet` (479.051 cümle) içinden, değiştirilmeden.

### 6.1 Kolay vakalar

| gerçek cümle | sınıf |
|---|---|
| *"No active infiltration or mass lesion was observed in both lungs."* | malignite negatif |
| *"There is a sequela calcific pulmonary nodule in the posterobasal segment…"* | benign |
| *"Destruction area compatible with metastasis was observed in the sternum corpus."* | malignite pozitif |

### 6.2 Zor vakalar — C listesinin çekirdeği

| # | gerçek cümle | naif kural | doğrusu | gereken kural | tür |
|---|---|---|---|---|---|
| 1 | **"Stable, calcific parenchymal metastases in both lungs."** | `calcific`→benign · `stable`→benign | **MALİGNİTE POZİTİF** | Kalsifikasyon ve stabilite **tek başına** benign göstergesi değildir; kanıtlanmış metastaz ikisini de ezer | **C-1** |
| 2 | *"…no lytic-destructive lesion **in favor of metastasis** was detected"* | `metastasis` var → pozitif | malignite negatif | Negasyon şemadan **önce** çözülür; kelimenin varlığı değil **kapsamı** sayılır | A (belge Kritik kural) |
| 3 | *"**Suspicious** findings in terms of Covid-19 viral pneumonia."* | `suspicious` → belirsiz malignite | **malignite ile ilgisiz** | Belirsizlik **neye dair**? Enfeksiyon şüphesi malignite şüphesi değildir → §3.4 filtresi | **C-1** |
| 4 | *"13 mm hypodense lesion in **liver segment 8** is stable (**cyst?**)"* | `?` → belirsiz | **benign** | ⚠ **v1 hatası düzeltildi (denetim #25):** karaciğer *"kapsam dışı organ"* diye **elenmez** — karaciğer ve sürrenaller akciğer kanserinin **en sık uzak metastaz bölgeleridir**. Bu vaka **stabil kist** olduğu için benign; organ olduğu için değil | **C-2** |
| 5 | *"…pleural thickness increases … evaluated **in favor of** minimal sequelae"* | `in favor of` → çıkarım | benign | `in favor of` yön belirtmez; **neyin** lehine olduğu belirler | A |

⚠ **1 numaralı cümle bu görevin en önemli tek kanıtıdır.**

---

## 7 · ⚠ Girdi kalite filtresi — **v2'de eklendi (denetim #10, KRİTİK)**

Şemanın girdisi Faz 2'nin çıkarımıdır ve o katmanın kusurları **ölçülmüştür**:

| ölçüm | değer | kaynak |
|---|---|---|
| **K7 · `prior` F1** | **%36,4 — eşiği geçemedi** | `test-v2`, D39 |
| `uncertain` duyarlılığı | **%71 / %46** | `test-v2` |
| sebebi | D29 belirsizlik ipuçlarını `cikarim_ifadesi` → `present` yapmıştı | kayıtlı |

**Risk:** çıkarım katmanı **geçmiş bir nodülü `present`** verirse, toplama kuralı
raporu haksız yere maligniteye yükseltir — projenin ana hedefinin tam tersi.

**Önlem — üçü de şema dondurulmadan önce:**

1. **İzolasyon filtresi:** zamansallık veya kesinlik ekseninde çelişki taşıyan
   varlıklar (`prior` + `present`, `uncertain` + kesin ifade) şemaya **doğrudan
   girmez**; ayrı bir `dusuk_guven` kanalına düşer ve rapor sınıfını
   **yükseltemez**.
2. **Hata bütçesi:** `prior` F1 %36,4 verilmişken, zaman ekseninin şema
   çıktısına katkısı **üst sınırla** sınırlandırılır ve bu sınır yazılır.
3. **Duyarlılık analizi:** şema, çıkarım katmanının bilinen hata oranları
   enjekte edilerek koşulur; rapor sınıfı dağılımının ne kadar kaydığı ölçülür ve
   raporlanır.

---

## 8 · Kabul ölçütleri — **v2'de yeniden yazıldı**

v1'in ölçütleri ya döngüseldi ya biçimseldi (denetim #3, #8, #9). Üçü de
değiştirildi ve **bir kapı eklendi**.

### 8.1 Sınır takımı: hedef sınıflar **kurallardan önce** kilitlenir

| v1 (kusurlu) | **v2** |
|---|---|
| "Takımdaki her cümle tam bir sınıfa düşer" | "Kilitli **hedef sınıflarla** %100 uyum" |

v1'in ölçütü yalnız **kapsamayı** sınıyordu: her şeyi `indeterminate` diyen naif
bir kural firesiz geçerdi.

**v2 yordamı:**
1. Adım 4'te 25-30 sınır vakası **ilan edilmiş örneklemeyle** seçilir (sabit
   tohum, kavram/kesinlik kotası) — *"zor görünen cümleyi elle seç"* ile değil
2. Her vakanın **hedef sınıfı** kurallardan **önce** belirlenir. Hedef ya
   **A**'dan türer (kaynakta yazılı) ya **C**'dir → C kaydına girer ve o
   zamana kadar `gecici` bayrağı taşır
3. Takım + hedefler **hash'lenip kilitlenir**
4. Adım 6'da vaka **eklenmez/çıkarılmaz**; kural geçemezse **kural değişir**

### 8.2 A tipi ölçüt sıkılaştırıldı

| v1 | **v2** |
|---|---|
| "her kural bölüm numarasıyla atıflı" | "her A kuralı için **alan sözlüğünün ilgili bölümü** + **primer kılavuzun spesifik tablo/paragrafı** eşleştirilir" |

Bölüm numarası iliştirmek türetmeyi kanıtlamaz.

### 8.3 ⭐ Negatif / Benign Koruma Kapısı — **yeni, KRİTİK**

Projenin ayırt edici vurgusu *"yanlış pozitifleri azaltmak"* ve v1'de bunu
sınayan **hiçbir ölçüt yoktu** (denetim #24).

> **En az 10 kontrol vakası** — açıkça benign, stabil veya olumsuzlanmış — ayrı
> bir takımda kilitlenir. **Şema bu vakaların hiçbirinde malignite üretmeyecek.
> Toleranssız: %100.** Bir tanesi bile geçerse şema dondurulmaz.

Kontrol takımı sınır takımıyla **aynı anda ve aynı yordamla** üretilir, ayrı
dosyada tutulur, ayrı hash'lenir.

### 8.4 Prevalans denetimi — dış çapaya bağlandı

v1 *"dağılım beklenen prevalansla karşılaştırılır"* diyordu; **"beklenen"in dış
kaynağı yoktu** (denetim #1, KRİTİK) — kural sübjektif beklentiye göre bükülürdü.

**v2:** referans, korpustaki **açık onkolojik göstergelerden kör türetilmiş bir
alt sınırdır** (`malignan` 217 çalışma, `metasta`, `carcinoma` sayımları).
Kabul aralığı **sayısal olarak, koşumdan önce** dondurulur. Dağılım aralığın
dışına çıkarsa kural revize edilir — **aralık değil.**

### 8.5 Adımlar

| # | adım | çıktı | kabul ölçütü | engel |
|---|---|---|---|---|
| **0** | **Bölünme kilidi** (§4.3) + §6 örneklerinin maruziyet kaydı (§4.4) | `configs/splits_holdout.json` + kilit + test | Sızıntı testi geçer; hasta çakışması sıfır | — |
| 1 | **C listesi** — katmanlı (C-1/2/3); sayı **çelişen gösterge taramasıyla ölçülür**, tahmin edilmez | `docs/31…` | Her madde: gerçek cümle + iki olası karar + önerilen varsayılan | 0 |
| 2 | A tipi aktarım — **çekirdek malignite/benignite kurallarıyla sınırlı** | gerekçe taslağı | §8.2 | — |
| 3 | B tipi ölçümler — **yalnız nesnel terim/varlık sıklıkları**, sınıf prevalansı **değil** (denetim #2) | ölçüm tabloları | Her sayı betikle yeniden üretilebilir | 0 |
| 4 | **Sınır takımı + hedef sınıflar + negatif kontrol takımı**, kurallardan **önce**, **kilitli** | 2 CSV + SHA-256 | §8.1 yordamı; hepsi **geliştirme havuzundan** | 0 |
| 5 | **Girdi kalite filtresi** (§7) | filtre + hata bütçesi | Çelişkili varlık rapor sınıfını yükseltemiyor | 3 |
| 6 | Şema yazımı | `degerlendirme_semasi.json` + doğrulayıcı + testler | **§8.1 hedef uyumu %100** · **§8.3 koruma kapısı %100** · §8.4 dağılım aralığı | 2,3,4,5 |
| 7 | Codex **ayrışma taraması** | ayrışma tablosu | Ayrışan vakalar C kaydında öncelikli işaretlenir | 4 |
| 8 | İnceleme tezgâhı (CSV'den üretilir) | `sema_tezgahi.html` | İnceleyici her karara **onay/red/revizyon** bayrağı verebiliyor | 6 |
| 9 | Gerekçe belgesi + karar defteri | `docs/30` + `kararlar.md` | Her kararın **çeliştiği alternatif** ve korpus dayanağı yazılı | hepsi |

⚠ **Süre tahmini verilmemiştir.** v1'in "36 saat"i temenniydi (denetim #6, #7).
Gerçek maliyet **adım 1'in C sayısı ölçüldükten sonra** tahmin edilecektir.

---

## 9 · Yedek planlar

### 9-B.1 C kararları uzman onayı almadan kalır *(bu çalışmanın durumu)*
Bütün C maddeleri önceden yazılmış varsayılanlarla şemaya girer,
`karar_kaynagi: "gecici_varsayilan"` bayrağıyla; raporda *"uzman onaysız karar"*
diye listelenir. Şema `sema-0.9-taslak` olarak kullanılır ve TASK-17/18 buradan
devam eder. Bkz. §2.4.

### 9-B.2 Alan sözlüğü belgesi kullanılamaz hâle gelirse
Belgeden bağımsız, doğrudan literatüre dayanan **B-şeması iskeleti** hazırda
tutulur: Fleischner tabanlı 4 sınıf + CheXpert'in belirsizlik politikası.

### 9-B.3 Şüphe düzeyleri korpusta boş kalırsa
Eşik önceden: **<%1 veya n<30** → düzey **birleştirilir**, kayda geçer.
⚠ Ölçüm **prototip koşumundan sonra** yapılır (denetim #2) — kurallar yokken
sınıf prevalansı ölçülemez.

### 9-B.4 Belgenin alanları korpusta karşılık bulmazsa
`docs/08` emsali: 66 alandan **10'u korpusta hiç yok**. Desteksiz alan şemaya
girmez, *"belgede var korpusta yok"* diye kaydedilir.

### 9-B.5 Codex'le ayrışma yüksek çıkarsa
TASK-13 emsali: kappa 0,479 → kılavuz boşluğu → 0,845 (D37). Ayrışma
**teşhistir**. Revizyon turu **en fazla iki**.

### 9-B.6 Toplama kuralı dejenere dağılım üretirse
§8.4'ün dondurulmuş aralığına göre denetlenir; aralık dışına çıkarsa **kural**
revize edilir.

### 9-B.7 ⭐ Kılavuzlar çatışırsa *(denetim #11)*
Fleischner insidental nodülde rutin takip önerirken Lung-RADS tarama mantığıyla
daha düşük eşik koyabilir. **Öncelik sırası şema yazılmadan dondurulur** — ama
sıranın **kendisi C-1'dir**, plan yazarı belirleyemez. §3.4'ün gerekçesi
(genel toraks BT, tarama değil) C kaydına gerekçe olarak yazılır.

### 9-B.8 TASK-18'in elle etiketlemesi kaldırılamazsa
**Gümüş standart** — iki bağımsız model ön-işaretleyici + uzlaştırma + güç
hesabıyla boyutlandırılmış tabakalı örneklem. *"Uzman onaysız gümüş standart"*
diye adlandırılır.

### 9-B.9 C-1 sayısı beklenenden büyük çıkarsa
C-1 iki gruba ayrılır: şema iskeletini belirleyenler (6→4 eşleme, toplama kuralı,
akut enfeksiyon filtresi) ve kalanlar. Şema birinci grubun varsayılanlarıyla
yazılır; ikinci grup kayda geçer ve şemayı bekletmez.

### 9-B.10 Bakanlık verisi hiç gelmezse
T-03/T-04 etkilenmez · T-05–07 TCIA'nın açık taramalarıyla yapılır · T-12 NLST
açık alt kümesiyle kısmen yapılır · **T-11 düşer**. Bu senaryoda RadTr `test`
mührünü açmak anlamlı hâle gelir (TASK-15 kapanışı §5).

### 9-B.11 Şema TASK-17'de tutmazsa
`sema-1.x` sürüm zinciri; değişiklik yeni sürüm açar, eskiyi ezmez.
**"Bir kerede mükemmel" değil, sürümlenebilir.**

---

## 10 · Durum

| kapandı | |
|---|---|
| Sınıf ölçeği · karar düzeyi · bölünme oranı · adım sırası | onaylandı (§5, §4.3) |
| Uzman onayı kapsamı | alınmayacak — §2.4 |
| Sybil kapsamı | §11 okundu, kapsam dışına alındı (§1.2) |
| Alan sözlüğü sürümü | dosya adı v13, içerik v12 — fark yok |
| Erişim denetimi | TASK-16'yı bekletecek izin süreci yok (§3.5) |
| RadLex | API doğrulandı, %67 kapsama (§3.7) |
| Bağımsız denetim | 25 bulgu, 21 kabul → [`docs/32`](32_task16_bagimsiz_denetim.md) |
| **Adım 0 · bölünme kilidi** | **tamamlandı** → `configs/splits_holdout.json` |

| açık | |
|---|---|
| C kaydının gerçek büyüklüğü | adım 1'de ölçülecek |
| NLST açık klinik alt kümesinin içeriği | doğrulanacak (§3.6) — Faz 5'i etkiler |

## 12 · İlgili belgeler

| belge | ne için |
|---|---|
| [docs/32](32_task16_bagimsiz_denetim.md) | **bağımsız denetim** — v1'in kusurları ve karara bağlanması |
| [docs/08](08_alan_sozlugu_uyum.md) | alan sözlüğü uyum analizi — §4.3 Faz 3 kazanımları |
| [docs/06](06_sema_gerekce.md) | `sema-1.1` gerekçesi |
| [docs/kararlar.md](kararlar.md) | **D27** (otorite) · D29 · D30 · D31 · **D39** (K7) |
| [reports/turkce_bolunme_dondurma.md](../reports/turkce_bolunme_dondurma.md) | bölünme dondurma emsali |
| [reports/task15_dondurma.md](../reports/task15_dondurma.md) | otorite eksikliğinin bedeli |
| [reports/cikarim_dogruluk_raporu.md](../reports/cikarim_dogruluk_raporu.md) | §7'nin dayandığı `test-v2` sayıları |
