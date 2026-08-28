# Alan Sözlüğü Belgesiyle Uyum Analizi

**Belge:** *Akciğer BT Raporlarından BDM ile Yapılandırılmış Veri Çıkarımı — Alan Sözlüğü
ve Veri Rehberi (Sybil Modeli Veri Analizi İçin)*, v12, 2026-07-07
**Analiz:** Claude Code · 2026-08-27 · TASK-13'e geçmeden önce

---

## 0. Belge ne istiyor

Akciğer BT raporu metninden çıkarılabilecek **~250 adlandırılmış alan** tanımlıyor.
16 bölüm: genel özet, nodül (nodül başına satır), kitle/malignite dili, lenf nodu
(bölge başına satır), enfeksiyon/COVID, amfizem, fibrozis, atelektazi, plevra,
Sybil özet alanları, **Türkçe negasyon/belirsizlik eşleme tablosu**, kalite kontrol,
teknik parametre, **patoloji raporu alanları** ve PET-BT klinik öykü.

Her alan için istenen çıktı yapısı:
`value · status · certainty · evidence_text · source_section · extraction_confidence`

Temel kural: *"Rapor metninde açıkça bulunmayan hiçbir bilgi doldurulmamalı;
ilgili alan `not_mentioned` olarak işaretlenmelidir."*

---

## 1. Güçlü uyum — bunlar zaten örtüşüyor

| Belge | Bizde | Durum |
|---|---|---|
| `present / absent / uncertain / not_mentioned` | `present / absent / uncertain / not_processed` | ✅ üç değer aynı, dördüncü farklı (bkz. 3.1) |
| **Kritik kural 1:** *"dışlanamaz"* → `uncertain`, `present` değil | `cannot_be_excluded` → `uncertain`, **K11 ölçütü %100** | ✅ **birebir** |
| **Kritik kural 3:** öneri ifadeleri status değiştirmemeli | `recommended to be evaluated` belirsizlik ipucundan **çıkarıldı** | ✅ birebir |
| `growth_status`: `new/increased/stable/decreased/resolved` | `change_type`: aynı beş değer + `none`/`unknown` | ✅ **birebir** |
| `evidence_text` — kaynak cümle | `raw_text` + **karakter ofsetleri** + `assertion_cue` | ✅ **daha güçlü** |
| `source_section` | `section` (findings/impression) | ✅ |
| *"Metinde olmayan bilgi doldurulmaz"* | *"Veri hazırlığı korur, karar vermez"* | ✅ aynı ilke |
| `stabil` ifadesi ayrı alan | `change_type=stable`, klinik yorum Faz 6'da (D17) | ✅ |
| Türkçe *"lehine değerlendirilmiştir"* | `in favor of` ipucu (7.910 cümle) | ✅ ölçüldü |
| `laterality`: right/left/bilateral/midline/unknown | aynı beş değer | ✅ birebir |

**Belgeden bağımsız aynı sonuca varmışız.** Özellikle "dışlanamaz" tuzağı: belge bunu
*Kritik kural 1* diye işaretlemiş, biz de ölçüp %100 eşikli ayrı bir kabul ölçütü
(K11) koymuşuz.

---

## 2. Ölçüm: belgenin alanlarının kaçı bu korpusta var?

66 alan CT-RATE train korpusunda tarandı (449.868 cümle):

| | Alan |
|---|---|
| **Var** (≥100 cümle) | **29** |
| Seyrek (<100) | 27 |
| **Korpusta hiç yok** | **10** |

### 2.1 Korpusta hiç geçmeyen 10 alan — bu işi yapmaya gerek yok

`vascular_convergence` · `chest_wall_invasion_suspected` · `pleural_invasion_suspected` ·
`vascular_invasion_suspected` · **`nodal_station`** · **`co_rads_score`** ·
`tracheobronchomalacia_suspected` · `architectural_distortion` ·
`mass_like_consolidation` · `known_lung_cancer_history`

İki tanesi özellikle dikkat çekici:

**`nodal_station` = 0.** Belge lenf nodu istasyonunu `4R, 7, 10R` biçiminde istiyor.
CT-RATE raporları istasyon numarası **hiç kullanmıyor**; bunun yerine betimleyici ad
kullanıyor (`prevascular` 9.132 · `paratracheal` 11.478 · `subcarinal` 9.544). Bunlar
**bizim sözlüğümüzde zaten var**. Sayısal istasyona eşleme yapılabilir ama bu bir
**dönüştürmedir**, metinden çıkarım değil.

**`co_rads_score` = 0** — oysa COVID korpusta çok yaygın (aşağıda). Skor verilmemiş;
COVID yalnızca serbest metinden çıkarılabilir.

### 2.2 ⚠ Korpusta VAR ama bizim sözlüğümüzde YOK — 28 alan

| Alan | Cümle | |
|---|---|---|
| **`covid_suspected`** | **7.896** | ⚠ **en büyük boşluk** |
| `atelectasis_type` | 4.600 | |
| `linear_scar_or_band` | 2.952 | |
| `largest_short_axis_mm` | 1.575 | onkolojik ölçüde temel |
| `pleural_effusion_size` | 1.413 | |
| `follow_up_recommended` | 1.323 | |
| `loculated_effusion` | 1.096 | |
| `emphysema_type` | 1.062 | |
| `pleural_nodule` | 1.005 | |
| `volume_loss` · `emphysema_severity` · `centrilobular_nodules` · `calcified_ln` | 855–609 | |
| `rsna_category` · `honeycombing` · `pleural_based` · `pleural_retraction` · `traction_bronchiectasis` | 482–210 | |
| `pet_bt_recommended` · `blebs` · `prior_lung_surgery` · `pleural_plaque` · `reactive_ln` · `mucus_plugging` · `likely_intrapulmonary_LN` · `tb_suspected` · `air_trapping` · `prior_radiotherapy` | 192–101 | |

**COVID kaçırılmış olması ciddi.** 8.462 cümle, **5.406 çalışma** — korpusun **%21'i**.
CT-RATE pandemi döneminde toplanmış. Sözlüğümüzde `pneumonia` var ama COVID'e özgü
hiçbir kavram yok. Belgenin 6. bölümü tamamen buna ayrılmış.

---

## 3. Yapısal farklar — karar gerektirenler

### 3.1 `not_mentioned` bizde yok

Belge her alan için dört durum istiyor; dördüncüsü **`not_mentioned`** = *"bu bilgi
raporda geçmiyor"*. Bizim dördüncü değerimiz `not_processed` = *"bu alan henüz
işlenmedi"* — **farklı bir kavram**, boru hattı durumu.

Bu fark, çıktı biçiminden doğuyor (aşağıda). Alan düzeyi çıktı ürettiğimizde
`not_mentioned` **zorunlu** olacak.

### 3.2 ⚠ En büyük yapısal fark: ALAN odaklı vs VARLIK odaklı çıktı

**Belge istiyor:** rapor başına sabit şemalı ~250 adlandırılmış alan, artı **nodül
başına ayrı satır** (`nodule_id`, `dominant_nodule`, `size_max_mm`, …).

**Bizde var:** metindeki her **anma** için bir satır — 1.180.408 varlık, karakter
ofsetleriyle.

Bunlar farklı biçimler. **Bizimki daha ham ve daha izlenebilir**; belgenin istediği
biçim bizimkinden **türetilebilir** ama o katman şu an **tanımlı değil ve planda yok**.

Örnek: bizde `nodule` kavramının 27.465 anması var. Belgenin istediği
`has_any_nodule = yes`, `max_nodule_size_mm = 12`, `dominant_nodule_lobe = RUL`.
Birinciden ikinciye geçmek bir **toplama (aggregation)** işi.

### 3.3 Lezyon düzeyi gruplama yok

Belge "her nodül için ayrı satır" istiyor. Bu, aynı nodülün farklı cümlelerdeki
anmalarını **tek lezyonda birleştirmeyi** gerektirir (coreference). TASK-11'de bunu
bilerek kapsam dışı bıraktık (`is_cross_sentence` hep `False`).

### 3.4 Teknik çekince: iki yaklaşım farklı

| | Belge | Bizde |
|---|---|---|
| *"değerlendirilemedi"* | `uncertain` + `image_quality_issue=present` | assertion **değişmez**, ayrı eksen |

Bizim gerekçemiz ölçülmüştü: teknik çekince taşıyan cümlelerin **%42'sinde** bağımsız
gerçek negasyon var; çekinceyi kesinliğe karıştırmak o bulguları bozar. Ama belge
alan düzeyinde konuşuyor — bir **alan** teknik nedenle değerlendirilememişse
`uncertain` demek makul.

**İkisi çelişmiyor:** varlık düzeyinde bizim kuralımız, alan düzeyinde belgeninki
uygulanabilir. Alan toplama katmanında karara bağlanmalı.

### 3.5 `certainty` ve `extraction_confidence` bizde yok

Belge her alan için sayısal güven istiyor. Bizim çıkarımımız **deterministik kural
tabanlı** (D15) — uydurma bir olasılık üretmek yanlış olur. Karşılığımız
`assertion_rule` + `assertion_cue`: hangi kuralın ürettiği. LLM tabanlı bir katman
eklenirse (Faz 4) oradan gerçek confidence gelebilir.

### 3.6 Belge BDM (LLM) çıkarımı varsayıyor, bizim Faz 2 kural tabanlı

Bu **çelişki değil, mimari**: Faz 2'nin deterministik çıktısı **referans katman**,
Faz 4 LLM'leri o referansa karşı ölçüyor (D15 — aksi hâlde LLM kendi girdisini
değerlendirmiş olurdu). Ama belgenin nihai beklentisi LLM üretimi alanlar olabilir;
**netleştirilmeli** (bölüm 6).

---

## 4. Önceki aşamalarda güncellenmesi gerekenler

### 4.1 Faz 1 — `ClinicalInformation` alanı hiç bölütlenmedi ⚠

Belgenin **16. bölümü** (sigara öyküsü, bilinen kanser, geçirilmiş cerrahi, semptomlar)
için kaynak bu alan. Ölçtüm:

| | |
|---|---|
| Dolu çalışma | **12.726 / 25.692 (%49,5)** |
| `cough` | 2.427 |
| `dyspnea` | 1.101 |
| `surgery` | 403 |
| `cancer history` | 157 |
| `hemoptysis` | 98 |
| **`smoking`** | **15** |

Faz 1'de yalnızca `Findings` + `Impression` bölütlendi. Bu alan **hiç işlenmedi**.

**Ama abartmamak lazım:** sigara öyküsü **15 çalışmada** — belgenin `pack_years`,
`current_smoker`, `former_smoker` alanları bu korpustan **doldurulamaz**. Semptomlar
ise doldurulabilir.

### 4.2 Sözlük genişletmesi — 28 alan

Öncelik sırası ölçülen hacme göre: **COVID** (7.896) · atelektazi tipi (4.600) ·
lineer skar (2.952) · kısa aks (1.575) · efüzyon miktarı (1.413) · öneri ifadeleri
(1.323) · loküle (1.096) · amfizem tipi (1.062) · plevral nodül (1.005).

### 4.3 Faz 3 planı — belgeden gelen kazanımlar

- **`radiology_malignancy_suspicion_level`** 7 düzeyli ölçek — bizim Faz 3 şemamız
  4 sınıflıydı. Belgenin ölçeği daha ayrıntılı; hizalanmalı.
- Belgenin **12.1** bölümü alan başına **20 Türkçe ifade** veriyor. Bu, çeviri
  artefaktlarımızı doğrulamak için birinci elden kaynak: örneğin *"lehine
  değerlendirilmiştir"* → bizim `in favor of` bulgumuz.
- Faz 3'ün benign gösterge sözlüğü için `likely_granuloma` / `likely_hamartoma` /
  `perifissural` alanları — **ölçtük, korpusta seyrek** (112 / 20 / 6).

### 4.4 Faz 7 (patoloji) — artık alan şeması VAR

Belgenin **15. bölümü** patoloji raporu çıkarımı için tam bir şema veriyor:
makroskopik, mikroskopik (WHO 2021), **IHC** (TTF-1, p40, sinaptofizin, Ki-67),
**pTNM (AJCC 8)**, cerrahi sınır, **moleküler** (EGFR, KRAS G12C, ALK, ROS1, BRAF,
MET, RET, PD-L1, TMB, NGS).

Bu, TASK-04'ün ve Faz 7'nin şu ana kadar **tanımsız olan** çıktısını tanımlıyor.
Patoloji verisi geldiğinde **ayrı bir çıkarım hattı** gerekecek — BT raporu hattından
tamamen farklı sözlük ve şema.

### 4.5 Kalite kontrol alanları (13. bölüm)

`conflicting_statements_detected` (Findings–Impression çelişkisi) bizde yok;
`promoted_to_impression` sinyalimiz var ama **çelişki tespiti** ayrı bir iş.
`extraction_model_version` ↔ bizim sürüm zincirimiz karşılıyor. ✅

---

## 5. Yeniden yapılması gereken bir şey var mı?

**Hayır.** Yapılanların hiçbiri belgeyle çelişmiyor; eksik olan **üstüne eklenecek**
katmanlar:

| | İş | Nereye |
|---|---|---|
| 1 | Sözlüğe 28 kavram eklemek (önce COVID) | TASK-11 genişletmesi |
| 2 | `ClinicalInformation` bölütleme | Faz 1'e dönüş, dar kapsam |
| 3 | Varlık → **alan** toplama katmanı | **yeni görev**, Faz 3 başı |
| 4 | Lezyon düzeyi gruplama (nodül başına satır) | **yeni görev** |
| 5 | `not_mentioned` değerini şemaya eklemek | alan katmanıyla birlikte |
| 6 | Faz 3 malignite ölçeğini 7 düzeye hizalamak | TASK-14 |
| 7 | Patoloji alan şemasını kaydetmek | Faz 7 / TASK-04 |

**TASK-13 bunlardan etkilenmez** — o, mevcut çıkarımın doğruluğunu ölçüyor. Sözlük
genişlemesi TASK-13'ten sonra yapılırsa ölçüm yeniden koşturulur; önce yapılırsa
TASK-13 daha geniş bir sözlüğü ölçer.

---

## 5-B. ⚠ DİL SORUNU — belgenin ortaya çıkardığı en önemli mesele

Belgenin **12. bölümü tamamen Türkçe** (*"Gerçek Türkçe BT raporlarında aynı bulgu farklı
hekimlerce farklı ifadelerle yazılır"*) ve alan başına **20 Türkçe ifade** veriyor.
Bu, hedef metnin **Türkçe** olduğunu gösteriyor. Oysa üzerinde çalıştığımız veri
tamamen İngilizce. Durum netleştirildi:

### Elimizdeki veri: %100 İngilizce

| | |
|---|---|
| Rapor kolonları | **yalnızca** `ClinicalInformation_EN`, `Technique_EN`, `Findings_EN`, `Impressions_EN` |
| Türkçe karakter içeren rapor | **9 / 25.692** (artık) |
| HuggingFace deposunda Türkçe sürüm | **yok** |

### Orijinal Türkçe — doğrulandı

CT-RATE, **İstanbul Medipol Mega Üniversite Hastanesi**'nden (Mayıs 2015 – Ocak 2023).
Raporlar **aslen Türkçe yazılmış**, makineyle İngilizceye çevrilmiş ve **iki dilli tıp
öğrencileri** tarafından düzeltilmiş. Türkçe orijinaller **yayımlanmamış**.

### Geri çeviri (back-translation) YAPILMAMALI

Üç gerekçe:

1. **Çevirinin çevirisi orijinali geri getirmez.** İki katmanlı bozulma olur; üstelik
   ilk çeviri insan eliyle düzeltilmiş, o düzeltmeler geri çeviride kaybolur.
2. **Sözlüğümüz çeviri artefaktları üzerine kurulu.** `in favor of` (7.910),
   `CTO` (2.003), `space-occupying lesion` (18.315), `effusion-thickening` (17.839) —
   bunların hiçbiri Türkçe orijinalde bu biçimde yok. Geri çeviri bu artefaktları
   rastgele başka Türkçe ifadelere dönüştürür.
3. **Hedef Türkçe ise sistem Türkçe metinde çalışmalı.** Hekimler Türkçe yazacaksa,
   çıkarım hattı Türkçe girdiyi doğrudan işlemeli — arada çeviri katmanı olmamalı.

### Mimarimiz taşınmaya ne kadar hazır — ölçüldü

| Katman | Nerede | Taşınma maliyeti |
|---|---|---|
| **Kavram kimlikleri** (`nodule`, `effusion`, `spiculated`) | sözlük YAML | **Sıfır** — dilden bağımsız |
| **Desenler** | `configs/*_sozlugu.yaml` — **366 desen** | YAML düzenlemesi, kod değişmez |
| Şema, ilişki tipleri, doğrulama kuralları | `extraction_schema.json` | **Sıfır** |
| Ofset/sürüm/izlenebilirlik altyapısı | kod | **Sıfır** |
| **Koda gömülü İngilizce** | **6 sabit** | Kod değişikliği (küçük) |
| **Cümle bölütleme** | PyRuSH (İngilizce kurallı) | ⚠ **Yeniden çözülmeli** |

Koda gömülü altı sabit: `ZAMANSAL_REFERANS` ve `KONUM_EDATI` (`context.py`,
`entities.py`), `EN_BUYUGU`, ölçüdeki `NITELIKSEL` (*millimetric*) ve iki `TEKNIK`
deseni. Bunlar da sözlüğe taşınabilir — mimari zaten buna uygun.

**Sonuç: taşınma maliyetinin büyük kısmı sözlük yazımı, kod yeniden yazımı değil.**
Kavram/desen ayrımını baştan yapmış olmamız burada karşılığını veriyor.

### Ayrıca yeniden ölçülmesi gerekecekler

Faz 1'in tüm sayıları İngilizce korpusa özgüdür ve Türkçe veride **yeniden ölçülmelidir**:
şablon cümle oranı (%71), ipucu frekansları, ardıl negasyon oranı (%19,9), kelime
dağarcığı kapalılığı (300 terim → %98,2). Yöntem taşınır, **sayılar taşınmaz**.

---

## 5-C. Türkçe veri kaynakları — araştırıldı ve doğrulandı (2026-08-27)

### CT-RATE'in Türkçesi: kapalı — makalenin kendi ifadesiyle

> *"…translated from Turkish to English using the **Google Translate API**, and bilingual
> final-year medical students review and correct all translations."*
> *"**Only the English versions of these reports are included in our CT-RATE dataset.**"*

HuggingFace'te `radiology_text_reports` klasöründe yalnızca `train_reports.csv` ve
`validation_reports.csv` var; ikisi de İngilizce. Talep prosedürü tanımlı değil.

### Bulunan Türkçe kaynaklar

| | RadTr | PARROT |
|---|---|---|
| Rapor | **1.056** | 2.658 (14 dil, TR dahil) |
| Gerçek mi | **Sentetik** — radyologlar kendi deneyimlerinden yazmış (mahremiyet nedeniyle gerçek hasta verisi kullanılamamış) | **Kurgusal** |
| Modalite | **Tamamı BT, toraks odaklı** (göğüs, akciğer, kalp, batın) | CT %36 · göğüs ~%20 |
| Etiket | **9 varlık etiketi** | ICD-10 |
| İlişki | **Yok** — yalnızca varlık | yok |
| Biçim | `train/dev/test.json` (DyGIE++) | JSONL |
| Erişim | GitHub, depo MIT | GitHub, **CC-BY-NC-SA 4.0** |
| Özellik | **Etiketli altın set** | **Aynı raporun TR + EN çevirisi bir arada** |
| Kaynak | `BIGDaTA-Lab-AI/dygiepp-multilingual-radiology` · Diagn Interv Radiol 2025 | `PARROT-reports/PARROT_v1.0` |

Ayrıca **BioBERTurk** (Türkçe Wikipedia + radyoloji raporları + biyomedikal metinle ön
eğitilmiş) RadTr üzerinde **F1 80,1** bildirmiş — Türkçe için hazır bir taban.

### ⚠ RadTr'ın etiket seti bizimkiyle şaşırtıcı ölçüde örtüşüyor

| RadTr etiketi | Bizdeki karşılığı |
|---|---|
| `Obs_Present` | `observation` + `assertion=present` |
| `Obs_Absent` | `observation` + `assertion=absent` |
| `Obs_Uncertain` | `observation` + `assertion=uncertain` |
| `Obs_Anatomy` | `anatomy` |
| `Obs_Technical` | `teknik_cekince` / `has_technical_caveat` |
| `Obs_Advice` | ⚠ bizde yok (belgede `pet_bt_recommended`) |
| `Symptom_P` / `Symptom_A` | ⚠ bizde yok — **`ClinicalInformation` bölütlenmedi** |
| `Differential_Diagnosis` | `belirsizlik.ayirici_tani` ipucumuz var |

RadTr, RadGraph gibi **varlık tipi ile kesinliği tek etikette birleştiriyor**; biz
bilerek ayırmıştık (`sema-1.1` sapması). Dönüşüm kayıpsız.

**RadTr'da ilişki yok** — `located_at` / `modify` / `measured_by` bizde var, orada yok.

**İki eksiğimizi bağımsız olarak doğruluyor:** öneri ifadeleri (`Obs_Advice`) ve
semptomlar (`Symptom_P/A` — bizim bölütlemediğimiz `ClinicalInformation` alanı).

### ⚠ Önemli asimetri

**Türkçe tarafta etiketli bir altın set VAR (RadTr), İngilizce tarafta YOK.**
TASK-13'te İngilizce için altın açıklamayı kendimiz üreteceğiz; Türkçede RadTr hazır
bir değerlendirme zemini ve **yayımlanmış bir taban skor** (F1 80,1) veriyor.

---

## 6. Belgeden doğan, sorulması gereken sorular

1. **Sybil.** Belgenin alt başlığı *"Sybil Modeli Veri Analizi İçin"*. Sybil, BT
   görüntüsünden akciğer kanseri riski öngören bir model. Çıkarılan rapor alanları
   Sybil çıktısıyla **karşılaştırılacak mı**, yoksa ona **girdi mi** olacak? Bu,
   projenin hedef metriklerini değiştirir.
2. **Çıktı biçimi.** Nihai teslim **alan tablosu** mu (rapor başına ~250 kolon) yoksa
   bizim **varlık tablosu** mu? İkisi birbirinden türetilebilir ama hangisinin asıl
   olduğu netleşmeli.
3. **LLM mi kural mı?** Belge BDM çıkarımı varsayıyor. Bizim Faz 2 bilerek kural
   tabanlı (Faz 4'ün karşılaştırma zemini bozulmasın diye). Nihai beklenti LLM
   üretimi alanlar mı?
4. **Korpus.** Belge nodül boyutu, Lung-RADS, tarama turu gibi **tarama kohortu**
   alanları içeriyor; CT-RATE ise insidental hastane kohortu. Alan sözlüğü hangi
   veri için düşünüldü — CT-RATE mi, Sağlık Bakanlığı verisi mi, NLST mi?
5. **Patoloji.** 15. bölüm ayrıntılı bir patoloji şeması veriyor. Bu, patoloji
   verisinin **geleceğinin** işareti mi? Öyleyse hangi kaynaktan?
