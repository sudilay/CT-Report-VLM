# Astra Rapor Veri Sözleşmesi

**Sürüm:** belge v5 · sözleşme `astra-sozlesme-1.1` · 2026-09-08 · bağımsız ölçüm **ve** sözleşme uyum denetimiyle revize edildi
**Kapsam:** SUDE-VLM-14 Adım 0 · `astra_radiology_reports_with_labels_all.xlsx`
**Bağlayıcı:** Bu belge onaylanmadan hiçbir çıkarım motoru Astra metni üzerinde
koşturulmaz.

---

## 1. Neden bu sözleşme koddan önce geliyor

Ölçüldü: raporların **%56,6'sında (1.679 rapor)** akciğer dışı bir bölümde
malignite sözcüğü geçiyor.

| Bölüm | Malignite sözcüğü içeren rapor | Oran |
|---|---:|---:|
| Meme | 1.052 | %35,5 |
| Kemik | 1.023 | %34,5 |
| Tiroid | 1.003 | %33,8 |
| Kalp | 946 | %31,9 |
| Özofagus | 502 | %16,9 |
| Abdomen | 343 | %11,6 |

Bu **bir hata kaynağı değil, bir kayıt zorunluluğudur** (§3.3.1). Şema
bölge-bağımsızdır: ekstratorasik malignite rapor düzeyi sınıfı meşru biçimde
yükseltir. Ancak NLST altın standardı *akciğer* kanseridir. Bu iki hedef
farklıdır ve fark **ölçülüp kaydedilmezse** aşağı katman kaynağını bilmediği bir
sinyalle çalışır.

Sözleşmenin görevi bu payı bastırmak değil, **görünür kılmaktır.**

---

## 2. Başlık envanteri

> ⚠ **Bu bölüm bağımsız ölçümle revize edildi**
> (`reports/vlm14_bagimsiz_ayirici_olcumu.md`, kapı KALDI).

### 2.0 Astra İKİ başlık sözdizimi kullanır

İlk sürüm yalnız `**Kalın:**` desenini tanıyordu. **Eksikti.**

| Sözdizimi | İçeren rapor |
|---|---:|
| `**Kalın:**` | 2.869 |
| Markdown `# Başlık` | **900** |
| İkisi de yok (gerçekten başlıksız) | **79 (%2,7)** |

**Başlıksız rapor sayısı 123 değil 79'dur.** İlk sayı, `#` başlıklarının
görülmemesinden kaynaklanıyordu.

**Kural:** ayırıcı **her iki sözdizimini de** başlık kabul eder. Satır başındaki
`#{1,6}` başlıkları ve satır başındaki iki noktayla biten kalın etiketler.

### 2.1 Envanter büyüklüğü

Farklı normalize başlık: **353–384** (normalleştirme yöntemine göre; bağımsız
ölçüm 384 buldu, bağıl fark %8,8 — kabul aralığında). Uzun kuyruk baskındır;
bu nedenle sözleşme **tam liste değil, varsayılan kural** üzerine kuruludur (§4).

### 2.2 Bir tuzak: `normal` başlık değildir

En sık "başlık" olarak görünen `normal` (5.975 geçiş) bir bölüm başlığı değil,
kalın yazılmış bir **değerdir** (*"**Normal**"* biçiminde bulgu niteleyicisi).
Başlık çıkarıcı bunu başlık saymamalıdır.

**Kural:** bir kalın metin ancak kendisinden sonra **iki nokta üst üste veya
satır sonu** geliyorsa ve ardından içerik varsa başlık sayılır. Değer konumunda
duran kalın metinler başlık değildir. Bu kural bir gerileme testine bağlanır.

✅ **Bağımsız ölçümle doğrulandı (V1 kapandı):** `normal` **0** kez yapısal
başlık, 7.050 kez değer konumunda; hepsi madde işaretli satırda.

---

## 3. Bölüm sınıflandırması

İki kova vardır: **klinik içerik** (kapsam içi) ve **meta/şablon** (kapsam
dışı). Kapsam içi kanıtlar ayrıca anatomik çıpalarıyla etiketlenir — bastırılmaz
(§3.3.1).

Her kanıt satırı `kaynak_bolum` ve `kapsam_ici` alanlarını taşır. Kapsam dışı
bırakılan malignite kanıtı seri düzeyinde
`qf_ekstratorasik_malignite_elendi` ile sayılır.

### 3.1 Kapsam içi — akciğer, plevra, havayolu

```
lung · lungs · left lung · right lung
pleura · left pleura · right pleura · pleural effusion · pleural thickening
trachea · trachea and bronchie · bronchie · bronchi · bronchial tree
bronchus · bronchioles · bronchial wall thickening
emphysema · severe emphysema · atelectasis · bronchiectasis
air trapping · air-trapping · airspace consolidation · airspace opacities
```

### 3.2 Kapsam içi — mediastinum (**ayrı bayrakla**)

```
mediastinum · mediastinal lymph nodes
```

**Karar (2026-09-08):** kapsam **içi**. Mediastinal lenf nodu akciğer kanserinin
**N evrelemesidir**, gerçek kanıttır ve 1.959 raporda geçer. Kapsam dışı
bırakmak kanserli vakalarda kanıt kaybettirir.

Mediastinum **torasiktir**, kapsam içidir. Kanıtları `qf_mediastinum_kaynakli=true`
taşır ki katkısı sonradan ayrıştırılabilsin.

### 3.3 Kapsam içi — rapor düzeyi özet bölümleri

```
findings · description of findings · abnormalities · abnormal · abnormality
abnormal findings · additional findings · significant findings
conclusion · diagnosis · final diagnosis · impression · summary
```

#### 3.3.1 Anatomik kapsam: **toraks** (karar 2026-09-08)

Bu bölüm iki kez revize edildi; ikisi de kayıt altındadır.

**v1 (yanlış):** "akciğer dışı organ kaynaklı malignite kanıtı düzeyi
yükseltemez" — bir **şema kuralı** gibi yazılmıştı. Şema bölge-bağımsızdır
(`C13-ekstratorasik`, hedef gerekçesi *"ekstratorasik ELENMEZ"*), dolayısıyla
bu şemanın kuralını Astra'ya uydurmak olurdu. Geri alındı.

**v2 (fazla temkinli):** her şey kapsam içi, anatomi yalnız etiketlenir.

**v3 (yürürlükte):** akciğer dışı organ bölümleri **girdi kapsamının dışındadır.**

**Ayrım şudur:** şemanın *kuralını* değiştirmek yasaktır; şemaya *hangi metni
verdiğimizi* seçmek ise kapsam kararıdır ve meşrudur — `Prepared by` bölümünü
dışarıda bırakmakla aynı türden bir karardır. Şema, kendisine verilen toraks
metni üzerinde bölge-bağımsız çalışmaya devam eder.

**Ölçülmüş gerekçe.** NLST `train` (838 PID · 2.062 seri · 99 kanserli), akciğer
dışı organ + olumsuzlanmamış malignite terimi:

| | Seri | Oran |
|---|---:|---:|
| **Kanserli seride** | **1 / 99** | %1,0 |
| Kansersiz seride | 4 / 1.963 | %0,2 |

NLST bir **tarama** kohortudur: hastalar çoğunlukla asemptomatik, yakalanan
kanserler erken evredir, uzak metastaz nadirdir. Tanısal veya evreleme
kohortlarında bu oran yüksek olurdu; burada değildir.

> **Karar:** akciğer dışı organ bölümleri kapsam dışı. Maliyet ölçüldü ve
> raporlanacak: bu kararla 99 kanserli serinin 1'inde malignite kanıtı elenmiştir.

**Geri dönülebilirlik — tek bayrak:**

```
qf_ekstratorasik_malignite_elendi   bool   (seri düzeyi)
```

Elenen kanıt sayılır ve sonuç raporunda beyan edilir. Sessiz kayıp yasaktır.

#### 3.3.2 Özet bölümlerinin ölçülen içeriği

**Ölçüldü:** özet bölümleri akciğer dışı organ malignitesi **sızdırıyor**, az ama
sıfır değil:

| Bölüm | Bölüm var | İçinde akciğer dışı organ + malignite | Oran |
|---|---:|---:|---:|
| `conclusion` | 1.872 | 8 | %0,4 |
| `abnormalities` | 341 | 4 | %1,2 |
| `findings` | 482 | 14 | %2,9 |

Örneklerin bir kısmı olumsuzlanmıştır (*"No acute pathology ... in the abdomen,
bone, breast, esophagus, heart"*) ve negasyon katmanı bunları zaten eler. Ancak
gerçek olanlar da vardır:

> *"The chest CT reveals a large, heterogeneous mass in the **right kidney**..."*
> *"multiple hypodense lesions in the **liver**, consistent with **metastatic
> disease**."*

Bu satırlar §3.3.1 gereği **elenir** ve `qf_ekstratorasik_malignite_elendi`
bayrağını kaldırır.

⚠ **Yukarıdaki üç oran (%0,4 / %1,2 / %2,9) genel kelimelerle ölçülmüştür**
(`mass|tumor|nodul|lesion`). Gerçek malignite terimleriyle
(`malign|metasta|carcinom|neoplas`) ve olumsuzlama elenince oran **%0,2'ye**
düşer. Genel kelime taramaları bu belgede sistematik olarak şişirmiştir — bkz.
§10 V8.

**Not:** `conclusion`'ı `impression`'a eşleme **zorunluluğu yoktur.** Doğrulandı:
`src/radyovlm/evaluation/sema.py` içinde hiçbir `section == 'impression'`
mantığı yoktur; `section` yalnız cümle anahtarının parçasıdır (`sema.py:543`).
`scripts/04_segment_sentences.py`'nin `Findings_EN` / `Impressions_EN`
bağımlılığı yalnız o **betiktedir**, kütüphanede değildir. Bölüm kimliğinin
kararlı olması yeterlidir.

#### 3.3.3 Anatomi düzeyi eleme — **bölüm kapsamı tek başına yetmez**

> ⚠ Bu kural, bağımsız sözleşme uyum denetiminin **K5.2** bulgusuyla eklendi
> (`astra-adaptor-1.1`).

Bölüm düzeyi kapsam, özet bölümlerinde (`conclusion` · `findings` ·
`abnormalities`) yetersizdir: bu bölümler kapsam içidir ve içlerinde karaciğer
metastazı gibi akciğer dışı kanıt geçebilir. Denetim, train kümesinde böyle iki
cümle bulmuştur; birinde karaciğer metastazı ile pulmoner nodül **aynı
cümlededir**.

**Kural:** `located_at` ilişkisi ile kesin olarak akciğer dışı bir organa
bağlanan gözlem, kapsam içi bölümde bulunsa dahi elenir.

```
EKSTRATORASIK_ANATOMI = abdomen · adrenal_gland · breast · esophagus
                        gallbladder · kidney · liver · pancreas · spleen · thyroid
```

**İki tasarım kararı:**

1. **Eleme varlık düzeyindedir, cümle düzeyinde değil.** Karışık organlı bir
   cümlede toraks kanıtı **korunur**.
2. **Kemik yapılar bu kümede değildir**, bölüm listesinde kapsam dışı olsalar
   bile. Gerekçe: kilitli sınır takımının `C5-03` vakası (*"metastatic masses in
   T1 and L1 vertebrae"*) hedefi `known_malignancy`'dir; şema onları sayar.
   Bu asimetri bilinçlidir ve burada ilan edilmiştir.

**Kalite bayrakları ayrıştırıldı.** Önceki sürümde organ kaynaklı eleme ile
bilinmeyen/meta bölüm kaybı tek bayrakta toplanıyordu:

```
qf_ekstratorasik_malignite_elendi   organ kaynaklı eleme
qf_bilinmeyen_bolum_malignite       bilinmeyen veya meta bölümde kalan kanıt
qf_mediastinum_kaynakli             mediastinum katkısı ayrıştırılabilsin diye
```

---

### 3.4 Kapsam dışı — diğer organlar

§3.3.1 kararı. Çıkarılır ama **silinmez, işaretlenir**; elenen malignite kanıtı
`qf_ekstratorasik_malignite_elendi` bayrağıyla sayılır.

```
breast · breasts · breast parenchyma
thyroid
abdomen · liver · spleen · kidneys · pancreas · bowel · bladder
adrenal glands · adrenals
bone · ribs
esophagus
heart
aorta · aortic aneurysm · aortopulmonary window
```

### 3.5 Kapsam dışı — meta ve şablon

```
patient information · prepared by · report prepared by · reviewed by
date · date of examination · clinical history · clinical context
imaging details · imaging modality · imaging technique · image type
image quality · note · important note · disclaimer
chest ct report · chest ct image analysis report · chest ct image analysis
chest ct scan report · comprehensive chest ct diagnosis report
comprehensive chest ct report
```

---

## 4. Varsayılan kural — bilinmeyen başlık

353 başlığın çoğu uzun kuyrukta. Tam liste tutmak sürdürülebilir değildir.

**Kural: bilinmeyen başlık kapsam DIŞIDIR (fail-closed) ve işaretlenir.**

```
kapsam_ici        = false
bilinmeyen_baslik = true
```

Bu güvenli yöndür — bilinmeyen bir bölüm sessizce akciğer kanıtı üretemez. Ancak
**kayıp ölçülür**: Adım 2'de bilinmeyen başlıklarda ne kadar malignite kanıtı
kaldığı raporlanır. Kayıp anlamlıysa sözleşme **bir kez** revize edilir ve
`astra-adaptor` sürümü yükseltilir.

**Sessiz kayıp yasaktır:** bilinmeyen başlık oranı her koşumda raporlanır.

---

## 5. Başlıksız metin

**79 rapor (%2,7)** hiç başlık içermiyor — iki sözdizimi de yok (§2.0).
İlk sürümdeki 123 sayısı `#` başlıklarının görülmemesinden kaynaklanıyordu.

**Kural:** başlıksız rapor gövdesi `bolum_ham = "__bassiz__"` alır ve
`kapsam_ici = false`, `bilinmeyen_baslik = true` işaretlenir. §4'teki ölçüm
bunları da kapsar. Başlıklı raporlarda ilk başlıktan **önce** gelen metin de
aynı kovaya düşer.

---

## 6. Giriş kolonu kısıtı (**bağlayıcı**)

Çıkarım hattı kaynak dosyadan **yalnız** şu kolonları okur:

```
PID · Seri_Anahtari · Radyoloji_Raporu
```

`Kanser_Etiketi_y`, `Censor_Time`, `Pillar_Ensemble_Skoru` ve diğer etiket veya
skor kolonları çıkarım hattında **okunmaz**. Bunlar yalnız ayrı `train` analiz
betiğinde kullanılır.

**Gerekçe:** held-out serileri için özellikler kör biçimde üretilecektir; hattın
etiketi hiç görmemesi bunu yapısal olarak garanti eder, disipline bırakmaz.

**Test:** çıktı şemasında bu alanların bulunmadığı ve hattın bunları okumadığı
gerileme testiyle kanıtlanır.

---

## 7. Teknik parametre satırları

> ⚠ **BU BÖLÜMDE CİDDİ BİR KUSUR BULUNDU VE DÜZELTİLDİ.**

### 7.1 Bulunan kusur

İlk sürümdeki desen şuydu:

```
slice thickness · reconstruction interval · scan interval · kernel · kVp · mAs
```

Harf duyarsız uygulandığında **`mAs` alternatifi `mass` ve `masses`
kelimeleriyle eşleşiyor.** Ölçüldü:

| | Rapor |
|---|---:|
| Sayısal `mm`/`cm` ölçüsü geçen | 222 |
| **Kusurlu desenle "teknik" sayılan** | **221** |
| Güvenli desenle teknik sayılan | 1 |
| **Gerçek `mAs` tokeni (`mAs`)** | **0** |

Teknik satırlar ölçü çıkarımından dışlandığı için bu kusur, *"a mass measuring
12 mm"* gibi **tam da aradığımız lezyon ölçümlerini** eleyecekti.

⚠ **Ve kusur, doğru görünen bir sayı üretmişti:** kusurlu yöntemin "temizlik
sonrası 91 rapor" sonucu, bağımsız ölçümün güvenli desenle bulduğu 97 ile
%6,6 farkla uyuşuyordu. **Uyuşan sayı, yöntemin doğruluğunu kanıtlamaz.**

### 7.2 Yürürlükteki desen

Bağlam **zorunlu**, sözcük sınırı **zorunlu**, `mAs`/`kVp` **harf duyarlı**:

```
slice thickness  ·  section thickness
reconstruction thickness  ·  reconstruction interval
slice interval  ·  collimation
kernel  ·  kVp  ·  mAs     (harf duyarlı)
```

**Çıplak `interval` kullanılmaz** — bağımsız ölçüm de aynı gerekçeyle dışladı
(`no interval growth/change` klinik karşılaştırmadır). Bu korpusta klinik
kullanım 0 kez geçiyor; desen yine de savunmacı tutulur.

> ⚠ **K5.1 (uyum denetimi):** Bu desen ile ölçü çıkarımının kendi teknik
> penceresi **iki ayrı tanım** oluşturuyordu. Sentetik sözleşme vakası
> `"Tube current 100 mAs; reconstructed at 5 mm."` ikisini ayrıştırdı: adaptör
> teknik der, ölçü filtresi demezdi ve ölçü `measured_by` ilişkisine
> girebilirdi. Tanım `astra.olcu_teknik_mi` içinde **tekilleştirildi**; iki
> koşuldan biri yeterlidir — ölçünün çevresindeki pencerede teknik bağlam
> olması ya da satırın tamamının teknik parametre bildirmesi.

**Yürürlükteki sayı:** teknik temizlik sonrası doku ölçüsü kalan rapor
**97 (%3,3)** — ilk sürümdeki 91 değil.

Teknik satırlar `is_technical_param=true` alır; **silinmez**. Ölçü çıkarımı bu
satırları kaynak almaz.

### 7.3 Zorunlu gerileme testi

Ölçü içeren bir cümlede `mass` veya `masses` geçiyorsa ve satırda açık teknik
bağlam yoksa, satır **teknik sayılmamalıdır**. Sabit test vakası:

```
"a mass measuring 12 mm in the right upper lobe"  →  is_technical_param = False
```

## 8. Cümle anahtarı

```
(seri_anahtari, bolum_ham, cumle_idx)
```

**D96 dersi:** bölüm bilgisi olmadan `cumle_idx` kullanmak yasaktır. Önceki
korpusta 77.855 anahtar iki bölümde tekrar etmiş ve 155.710 satır etkilenmişti.

`bolum_ham` ham başlık metnidir; `bolum_eslenmis` §3'teki kovadır. Anahtar
**ham** başlıkla kurulur ki eşleme değişse bile anahtar kararlı kalsın.

---

## 9. Karara bağlanacak açık maddeler

| # | Madde | Öneri |
|---|---|---|
| **S1** | `recommendations` (978) · `recommendation` (35) · `further evaluation` (27) · `clinical correlation` (24) · `biopsy consideration` kapsam içi mi? | **Kapsam dışı.** Öneri metni bulgu değildir; *"biopsy is recommended"* bir gözlem değil bir eylem önerisidir ve malignite düzeyini yükseltmemelidir. Ancak ayrı bayrakla saklanabilir — sonradan kanıt füzyonunda kullanılabilir. |
| **S2** | `region analysis` (266) · `region-by-region analysis` (210) · `image description` (417) · `region of interest` (22) — bunlar **kapsayıcı** başlıklar, içlerinde hem akciğer hem akciğer dışı içerik var | **İç içe başlık çözümlemesi**: kapsayıcı başlık kendi başına kova atamaz; içindeki alt başlıklar sınıflandırılır. Alt başlık yoksa `bilinmeyen_baslik`. |
| **S3** | `calcification` başlığı (nadir) kapsam içi mi? | Belirsiz — kalsifikasyon hem akciğer benign kanıtı hem başka organ bulgusu olabilir. Varsayılan: bilinmeyen (fail-closed). |

---

## 10. Doğrulanmamış varsayımlar — **denetlenmeli**

Bu belgedeki her karar ölçüme dayanmıyor. Aşağıdakiler **isim benzerliğine veya
sezgiye** dayanıyor ve Adım 1'de kodlanmadan önce doğrulanmalıdır.

| # | Varsayım | Risk | Nasıl denetlenir |
|---|---|---|---|
| ~~V1~~ | `normal` ayıklama kuralı | ✅ **KAPANDI** — bağımsız ölçüm: 0 yapısal başlık, 7.050 değer konumu. Kural doğru |
| ~~V2~~ | Bölüm ayırıcının doğruluğu | ✅ **KAPANDI, KUSURLU ÇIKTI** — (a) `#` başlıkları hiç görülmemiş, (b) `mAs`→`mass` regex kusuru. İkisi de §2.0 ve §7'de düzeltildi |
| ~~V3~~ | `emphysema`/`atelectasis`/`bronchiectasis`/`pleural effusion` başlık mı değer mi | ✅ **KAPANDI** — iki noktalı, içerikli **alt başlıklar**; `normal`dan farklı. §3.1'de doğru yerdeler |
| **V4** | §3.4'teki organ listesi rapor içeriğine değil **başlık adına** bakıyor | `abdomen` başlığı altında akciğer tabanı bulgusu olabilir | Örnekleme ile içerik denetimi |
| **V5** | S2'deki iç içe başlık çözümlemesi — `region analysis` gerçekten alt başlık **içeriyor mu**? | İçermiyorsa çözüm gereksiz karmaşıklık | 20 örnek raporun yapısına bak |
| **V6** | Akciğer dışı bölüm sınırının doğru çizildiği | Yanlış çizilirse toraks kanıtı da elenir | Elenen içeriği örnekle denetle |
| **V9** | İç içe başlıkta içeriğin **en yakın başlığa** bağlanması | Bağımsız ölçüm bu kuralı kullandı; ilk ayırıcım alt başlık içeriğini ebeveyne taşımış olabilir (`abnormalities` sızıntısı 4 vs 1) | Adaptörde en-yakın-başlık kuralı **açıkça** uygulanır ve test edilir |
| **V8** | ⚠ **Bu belgedeki genel kelime taramaları (`lesion\|nodule\|mass`) oranları SİSTEMATİK OLARAK ŞİŞİRDİ.** T8 %56,6 dedi, gerçek malignite terimleriyle %0,2 | Aynı hata başka ölçümde de olabilir | Her oran için sor: *genel kelime mi saydım, malignite terimi mi?* |
| **V7** | ⚠ **Bu belgenin ilk hâli ekstratorasik kanıtı bastırıyordu ve şemaya aykırıydı.** Düzeltildi | Benzer bir "temizlik" hatası başka yerde de olabilir | Sözleşmenin her kuralı için sor: *şemanın bir kararını sessizce değiştiriyor muyum?* |

**V1 ve V2 en kritiktir:** ikisi de bu belgedeki sayıların doğruluğunu etkiler.
V2 doğrulanana kadar T8'in %56,6 değeri **ön ölçüm** olarak anılmalıdır.

---

## 11. Gerileme testleri

`tests/test_vlm14_astra.py`:

1. `normal` hiçbir raporda başlık olarak sınıflandırılmaz (§2.1).
2. Sözleşmede tanımsız hiçbir başlık `kapsam_ici=true` alamaz (§4).
3. Cümle anahtarı `(seri_anahtari, bolum_ham, cumle_idx)` benzersizdir (§8).
4. 2.965 serinin tamamı işlenir, 0 kayıp.
5. Teknik satır içeren rapor sayısı ≈ 175 (§7); sapma gerekçelendirilir.
6. Çıkarım hattı `Kanser_Etiketi_y` / `Censor_Time` / `Pillar_Ensemble_Skoru`
   kolonlarını okumaz ve çıktı şemasında bunlar bulunmaz (§6).
7. **Akciğer dışı organ bölümleri kapsam dışıdır** (§3.3.1) ve elenen her
   malignite kanıtı `qf_ekstratorasik_malignite_elendi` bayrağını kaldırır.
   Sessizce elenirse test **kırmızıya döner** — sayılmayan kayıp yasaktır.
8. Başlıksız **79** rapor `__bassiz__` kovasına düşer (§5). Ayırıcı hem
   `**Kalın:**` hem Markdown `#` sözdizimini tanır (§2.0).
9. **Kapsam eleme (§3.3.1):** korpustan alınmış *"mass in the right kidney"* ve
   *"hypodense lesions in the liver, consistent with metastatic disease"*
   cümleleri kapsam dışı bölümdeyse elenir **ve sayılır**. Sabit test vakalarıdır.
10. **Şema kuralı korunur:** sınır takımının `C13-ekstratorasik-01` cümlesi
   (*"newly emerged metastases in the liver and spleen"*) doğrudan şemaya
   verildiğinde `known_malignancy` üretmeye devam eder. Adaptörün girdi kapsamı
   kararı şemanın **kuralını** değiştirmez — yalnız ona verilen metni seçer.
