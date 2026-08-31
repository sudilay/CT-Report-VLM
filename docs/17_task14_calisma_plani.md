# TASK-14 · Türkçe Hattı — Çalışma Planı ve İlerleme

**Amaç:** Faz 2'de kurulan çıkarım katmanını Türkçe okuyabilir hâle getirmek ve
dil ablasyonunun (TASK-15) ölçüm yapabileceği zemini hazırlamak.

> Bu belge **yaşayan** bir kayıttır. İş bitince kutu işaretlenir ve **ne
> görüldüğü** yazılır — yalnızca "yapıldı" değil, çıkan sayı ve varsa sürpriz.
> Diğer agent da buradan takip eder.

**Durum:** 6/7 adım bitti · son güncelleme 2026-08-31

---

## Neden bu görev Faz 3'ten önce

Faz 3 **altın standart etiketleme** üretiyor. O etiketleme hangi dilde yapılırsa
proje o dile **bağlanır** — geri dönüşü en pahalı karar bu. Dil kararı
verilmeden Faz 3'e girilmez.

CT-RATE aslında Türkçe yazılmış (Medipol), Google Translate ile İngilizceye
çevrilmiş ve **yalnızca İngilizcesi yayımlanmış**. Yani bugüne kadarki tüm
İngilizce sonuçlarımız bir çevirinin üzerinde duruyor. Türkçe verinin gerekli
olup olmadığı **ölçülmeli**, varsayılmamalı.

---

## Bağlayıcı kısıtlar — her adımda geçerli

| kısıt | gerekçe |
|---|---|
| ⛔ `test` bölümünün 56 belgesine **bakılmaz** | Ablasyon ölçümü orada yapılacak (D26/D31 disiplini) |
| ⛔ Türkçe yüzeyler **kalıcı sözlüğe girmez** | Uzman onayı yok; ayrı deney sözlüğü olarak durur |
| ⛔ Sonuç görülüp kural değiştirilmez | `test-v2`de olduğu gibi: sürüm iptal olur |
| ✅ Her kapsam kararı **kılavuza da** yazılır | K16 denetliyor — yazılmazsa değişmez ihlali |

⚠ **Kirlenmenin yönü tehlikeli:** desenler test'e uydurulursa Türkçe taraf haksız
yere iyi çıkar ve ablasyondan yanlışlıkla *"Türkçe veri önemliymiş"* sonucu
çıkar. Yani kirlenme **tam da varmak istediğimiz sonucu** bozar.

---

## Adımlar

### ✅ 1 · RadTr bölünmesini dondur

**Bitti — 2026-08-31.** → [`reports/turkce_bolunme_dondurma.md`](../reports/turkce_bolunme_dondurma.md)

**Ne görüldü:** RadTr **kendi yayımlanmış bölünmesini taşıyor** ve çıkarım
betiği bunu zaten korumuş — kendi bölünmemizi uydurmak zorunda kalmadık.

| bölüm | belge | kelime | varlık | present | absent | uncertain | rol |
|---|---|---|---|---|---|---|---|
| train | 327 | 44.841 | 10.522 | 3.615 | 573 | 706 | geliştirme · sınırsız |
| dev | 46 | 6.416 | 1.490 | 502 | 87 | 106 | ayar · sınırsız |
| **test** | **56** | 7.784 | 1.817 | 613 | **86** | **128** | **bir kez** |

**Beklenmeyen kazanç:** yayımlanmış bölünmeyi kullandığımız için Türkçe varlık
çıkarımındaki yayımlanmış taban skoruyla karşılaştırma **mümkün kaldı**. Kendi
bölünmemizi uydursaydık bu imkânsız olurdu ve muhtemelen fark edilmezdi.

**Maruziyet ölçüldü — sıfır:** `tr-0.1` sayımları bölünmeden önce 429 belgenin
tamamında yapılmıştı. Kapsama sonucu test **dahil %88**, **hariç %88** — birebir
aynı (72/82). Test bölümü o sonuca hiçbir şey katmamış. Kayda geçti, gizlenmedi.

---

### ✅ 2 · Taslağı `train+dev`'e daralt, test'e kilit koy

**Bitti — 2026-08-31.** `configs/turkce_yuzeyler_taslak.yaml` → **`tr-0.2`**

- Ölçüm tabanı 429 → **373 belge** (test hariç)
- `scripts/20_turkce_yuzey_taslagi.py --bolum test` artık `sys.exit` ile duruyor
- Kapsama yeniden ölçüldü: **72/82 · %88** (değişmedi)

---

### ✅ 3 · K16 değişmezi + kılavuz tanımları

**Bitti — 2026-08-31.** `scripts/13_check_invariants.py` · `tests/test_invariants.py`

**Kural:** sözlükte `kilavuz_karari: true` taşıyan kavram, işaretleme
kılavuzunda adıyla veya bir deseniyle geçmelidir.

**Ne görüldü — ölçüt kendi doğuş sebebini yeniden buldu:** ilk koşuda **7
karardan 3'ü ihlal** çıktı ve bunlar tam da `test-v2`'de K4'ü tek sayı olmaktan
çıkaran kavramlardı: `anatomic_segment`, `abdomen`, `density_increase`.

Tanımlar `docs/11` §6'ya yazıldı → **K16 %100**. `qualifier` türünün
`dogru_varlik_mi` tanımında kapsanmaması da aynı bölümde kapatıldı.

Değişmezler: **K11–K16 hepsi geçti.** Testler **253/253**.

**Yan bulgu:** K16 için kılavuzu açtığımda `test-v2` K7 teşhisimin **yanlış**
olduğunu gördüm — zaman kuralı `docs/12`'de zaten yazılıydı. Rapor düzeltildi,
K7 "ölçülemedi"den **"ölçüldü ve KALDI"**ya çevrildi (D39).

---

### ✅ 4 · Kavram yüzeylerini tamamla — **144 kavramın hepsi**

**Bitti — 2026-08-31.** `configs/turkce_yuzeyler_taslak.yaml` → **`tr-0.3`**

62 eksik kavrama Türkçe yüzey yazıldı; `train+dev` (373 belge) üzerinde ölçüldü.

| | önce (`tr-0.2`) | sonra (`tr-0.3`) |
|---|---|---|
| yüzeyi olan kavram | 82 | **144** |
| RadTr'de geçen | 72 (%88 / 82) | **123 (%85 / 144)** |
| geçmeyen | 10 | 21 |

#### ⚠ En önemli bulgu — Türkçe **betimleyici kalıp** kuruyor

`cardiomegaly` deseni (*"kardiyomegali"*) **0 anma** verdi. Ama:

> *"**Kalp boyutları** artmıştır."* · *"**Kalp boyutları** normal sınırlardadır."*
> → **313 anma**

Türkçe raporlar Latince adlaştırma yerine **tam cümle** kuruyor. Bu, kavram
envanterinin taşındığı ama **yüzeyin biçim değiştirdiği** anlamına gelir —
birebir terim çevirisi yetmez.

⚠ **Bunun bir yan etkisi var ve adım 5'e devrediliyor:** kesinliği taşıyan kelime
kalıbın **içinde** (*"artmıştır"* = present, *"normal sınırlardadır"* = absent).
İngilizce'de `cardiomegaly` kavram, `no cardiomegaly` olumsuzlama — ayrıktı.
Türkçe'de ayrık değil. İpucu sözlüğü bunu ele almalı.

Aynı düzeltmeyle `tumor` (*"neoplazik"*, *"kitlesel"*), `diaphragm`
(*"diyafragmatik"*), `fat_containing` (*"yağlı"*), `well_defined`
(*"düzgün konturlu"*) de bulundu — **5 kavram** betimleyici/varyant yüzeyle geldi.

#### D34 denetimi — bir yanlış pozitif yakalandı

`catheter` deseni *"port"* idi ve **"portal hilus"** yakalıyordu (karaciğer portal
bölgesi, port kateteri değil). *"port kateter|port hazne"* olarak daraltıldı.

Diğer şüpheli desenler tek tek bağlam içinde denetlendi ve temiz çıktı:
`solid`, `nekro`, `perifer`, `sekel`, `foramen`, `litik`, `kosta`, `greft`, `lümen`.

#### Öztürkçe tercih ediliyor — ölçülmüş

| kavram | Latince | Öztürkçe |
|---|---|---|
| `diffuse` | *difüz* **0** | *yaygın* **161** |
| `central` | *santral* **28** | *merkezi* **0** |

Yön sabit değil — her kavramda **ölçmek** gerekiyor, varsaymak değil.

#### Geçmeyen 21 kavram

`adiposity` · `cholelithiasis` · `drainage_tube` · `effusion_thickening` ·
`fluid_collection` · `goiter` · `granuloma` · `granulomatous` · `halo` ·
`hepatosteatosis` · `intervertebral_disc` · `lymphadenomegaly` · `lymphoma` ·
`nephrolithiasis` · `part_solid` · `punctate` · `small_vessel_disease` ·
`spondylosis` · `station_hilar_axillary` · `station_supraclavicular` · `vena_cava`

Çoğu **abdominal** (safra/böbrek taşı, hepatosteatoz) veya seyrek. 373 belgede
geçmemesi *"Türkçe'de yok"* demek değil, *"bu alt kümede yok"* demektir.

---

### ✅ 5 · Türkçe ipucu sözlüğü — **en kritik adım**

**Bitti — 2026-08-31.** `scripts/22_turkce_ipucu_taslagi.py` →
`configs/turkce_ipuclari_taslak.yaml` (**`tr-ipucu-0.1`**)

İpuçları **ithal edilmedi, korpustan türetildi** — İngilizce tarafta olduğu gibi (D16).

#### ⚠ Bulgu 1 · **Yön ters** — mimariyi doğrudan etkiliyor

| | negasyon ipucu cümlenin **sonunda** |
|---|---|
| İngilizce (CT-RATE) | **%19,9** |
| **Türkçe (RadTr)** | **%97** |

Türkçe **fiil-sonlu** bir dil; olumsuzluk ayrı kelime değil **son ek** (*-ma/-me*).

> *"Mediastende ve her iki hilusta patolojik boyutta lenf nodu **saptanmadı**."*

İngilizceye göre ayarlanmış **ileri yönlü** bir kurulum, Türkçede negasyonun
**neredeyse tamamını kaçırır**. Sistemimiz `yon: geri` destekliyor (K15 bu yüzden
var) — ama varsayılan yön çevrilmeli.

#### ⚠ Bulgu 2 · Teknik çekince **gerçek negasyondan büyük**

| | anma |
|---|---|
| teknik çekince (*"kontrast verilmediğinden"*, *"yapılamamıştır"*, *"optimal değerlendirilemedi"*) | **961** |
| gerçek negasyon (*"saptanmadı"*, *"izlenmedi"*) | **843** |

Bunların **hepsi** *-ma/-me* eki taşıyor. Genel bir *"-ma/-me olumsuzluktur"*
kuralı 961 anmayı da olumsuzlama sayar → **kitlesel yanlış `absent`**.

**D30 (teknik çekince kesinliği değiştirmez) Türkçede İngilizceden daha kritik.**

#### İthal liste ölçüldü ve reddedildi — İngilizcedeki sonucun aynısı

Ders kitabı bir Türkçe olumsuzlama listesi şunları içerirdi:

| aday | anma | alındı mı |
|---|---|---|
| *görülmedi* | **0** | ⛔ |
| *rastlanmadı* | **0** | ⛔ |
| *tespit edilmedi* | **0** | ⛔ |
| *bulunmamaktadır* | **0** | ⛔ |
| *negatif* | **0** | ⛔ |
| *mevcut değil* | 1 | ⛔ |
| **saptanmadı** | **583** | ✅ |
| **izlenmedi** | **260** | ✅ |

**İki biçim 843 anmanın tamamını taşıyor.** İngilizce tarafta ithal NegEx
listesinin 272 tetikleyicisinin 220'si hiç geçmiyordu — aynı sonuç, aynı sebep.
Sıfır destekli ipuçları kayıtta tutuldu (*"denenmedi"* ile *"denendi, çıkmadı"*
ayrı şeylerdir).

#### D29 taşınıyor · belirsizlik taşınıyor

`cikarim_ifadesi`: *uyumlu* 166 · *olası* 101 · *lehine* 41 · *öncelikle* 32 ·
*düşünül* 23 · *şüpheli* 12 → hepsi `present`.

`belirsizlik`: **parantez-soru 117** (*"(küçük hava yolu hastalığı?)"*) ·
*ayırıcı tanı* 6 · *ekarte edilemez* 10.

#### ⛔ Zaman ekseni RadTr'de **ölçülemez**

| ipucu | anma |
|---|---|
| *önceki tetkik / önceki inceleme* | **4** |
| *karşılaştır / göre* | 10 |
| *stabil / değişiklik yok* | 1 |

RadTr **tek zamanlı sentetik** raporlardan oluşuyor; önceki tetkik referansı
neredeyse yok. `artmış/artış` 280 kez geçiyor ama açık zaman referansı olmadan —
İngilizce tarafta ölçülen sonucun aynısı (artış bildiren 25.522 cümlenin yalnızca
%3,4'ünde açık zaman referansı vardı).

⚠ **Ablasyon zaman eksenini ölçemeyecek.** Bu, ölçüm yapılmadan **önce** bilinen
bir sınırdır ve rapora böyle geçer. `test-v2`de K7 zaten eşiği geçememişti;
Türkçe tarafta karşılaştırma yapılamayacak.

---

### ✅ 6 · `dev` üzerinde sına ve düzelt

**Bitti — 2026-08-31.** `scripts/23_turkce_dev_olcum.py` · 46 belge · 618 varlık

İlk kez **Türkçe metinden Türkçe sözlükle** çıkarım yapıldı ve ölçüldü.

#### Sonuç · D2 kesinlik ataması

Altın kesinlik RadTr'nin **kendi etiketinden** gelir, bizim sözlüğümüzden
bağımsızdır — bu yüzden ölçüm dairesel değildir.

| sınıf | destek | P | R | **F1** |
|---|---|---|---|---|
| `present` | 450 | %84,3 | %97,6 | **%90,4** |
| **`absent`** | 72 | %84,3 | **%97,2** | **%90,3** |
| `uncertain` | 96 | %92,9 | %13,5 | %23,6 |

**Doğruluk %84,5.**

#### 🎯 **Negasyon Türkçede çalışıyor**

`absent` **F1 %90,3 · duyarlılık %97,2**. Adım 5'te ölçtüğümüz "yön ters"
bulgusuna göre kurulan **geri yönlü** kapsam işe yaradı. İngilizce tarafta
`absent` en güçlü eksendi; Türkçede de öyle.

Bu, TASK-14'ün asıl sorusunun cevabı: **çıkarım katmanı Türkçeye taşınıyor.**

#### İki düzeltme yapıldı — ikisi de ölçümle gerekçeli

**① Belirsizlik kapsamı çok genişti.** İlk sürüm cümlede parantez-soru görünce
**tüm** varlıkları `uncertain` yapıyordu. Ölçüldü: altın `present` span'ların
41/450'sinin cümlesinde parantez-soru var — ve hatamız **tam 41 satırdı**.
Birebir bu sebepti.

> *"Mozaik atenüasyon paterni (küçük hava yolu hastalığı?)"*
> → mozaik atenüasyon **MEVCUT**, küçük hava yolu hastalığı **BELİRSİZ**

Belirsizlik parantezin **içindedir**. Kapsam daraltıldı → `present` F1 %85,3 →
%89,9, `uncertain` kesinliği %19,2 → %87,5.

**② Parantezsiz soru işareti eksikti.** Türkçe raporlar ayırıcı tanıyı
parantezsiz de yazıyor:

> *"KLİNİK BİLGİ: **PTE? PNÖMONİ?**"* · *"nodül? metastaz?"*

Ölçüldü: parantezsiz biçim **461 anma**, parantezli biçimin **4 katı** (117).
Eklendi → `uncertain` F1 %13,5 → **%23,6**, doğruluk %83,5 → **%84,5**.

#### ⚠ `uncertain` neden hâlâ düşük — ölçüldü, iddia edilmedi

Altın `uncertain`ın (106) nereye gittiği:

| sebep | n | pay |
|---|---|---|
| **teknik ifade — şema farkı** | 54 | **%51** |
| gerçek kaçak | 25 | %24 |
| çıkarım ifadesi (D29 gerilimi) | 10 | %9 |
| span'ın cümlesi bulunamadı | 10 | %9 |
| doğru yakalandı | 7 | %7 |

**Yarısı sistem hatası değil, şema farkı.** RadTr *"değerlendirme optimal
yapılamamıştır"* ifadesini `Obs_Uncertain` sayıyor; bizim **D30**'umuz teknik
çekinceyi ayrı eksende tutuyor ve kesinliği değiştirmiyor. İki şema aynı fikirde
değil — ve bu, kuralı değiştirme gerekçesi değil, **raporlanacak bir farktır**.

Şema farkı dışlanınca:

| sınıf | destek | P | R | **F1** |
|---|---|---|---|---|
| `present` | 450 | %93,8 | %97,6 | **%95,6** |
| `absent` | 72 | %84,3 | %97,2 | **%90,3** |
| `uncertain` | 42 | %92,3 | %28,6 | **%43,6** |

**Doğruluk %92,4.** İki sayı da rapora girer; hangisinin okunacağı şema
tercihine bağlıdır ve bu açıkça yazılır.

**D29 gerilimi Türkçede de var:** *"ile uyumlu"* ifadesini biz `present`
sayıyoruz (D29), RadTr `uncertain` sayıyor. İngilizce `test-v2`de de aynı
gerilim `uncertain` duyarlılığını düşürmüştü. Aynı karar, iki dilde aynı fatura.

#### ⚠ Ofset hatası yakalandı — puanlamada kullanılmadan önce

Adım 6'ya girerken RadTr altın span'larının **bir token kaymış** olduğu görüldü:
`Obs_Anatomy` etiketi *"artmıştır."* fiiline denk geliyordu. RadTr indeksleri
**1-tabanlı**, çıkarım betiği 0-tabanlı varsaymıştı.

Nesnel ölçütle sınandı (span, son tokeni dışında nokta ile biten token içermez):
kayma −1 → %9,6 · **0 (hatalı) → %16,3** · +1 → %22,7. İkinci doğrulama:
`Obs_Anatomy` span'larının yüklemle bitme oranı **%8,3 → %2,4**.

⚠ Bu hata daha önce bir kez *"ofset 0 doğru"* diye **yanlış doğrulanmıştı** —
o doğrulama örneklere göz atmaya dayanıyordu. Dondurma bozulmadı: bölüm üyeliği
sağlama toplamları değişmedi.

#### Altın veri kalitesi — denetlendi

`Obs_Present` span'larının yalnızca **%0,1'i** (4/3939) negasyon ipucu taşıyor.
Bir örnekte *"sıvı saptanmadı."* `Obs_Present` etiketliydi; nadir bir altın
hatası, sistemik değil. Span'ların **%10,9'u** hâlâ cümle sınırını aşıyor —
ölçümde 77 span'ın cümlesi bulunamadı.

---

### ⬜ 7 · Ablasyona devret → TASK-15

- [ ] `tr-1.0` donduruldu, sağlama toplamları kayıtlı
- [ ] `test` 56 belge hâlâ **açılmamış**
- [ ] Protokol hazır → [`docs/16_dil_ablasyon_protokolu.md`](16_dil_ablasyon_protokolu.md)
- [ ] ⛔ **Zaman ekseni ölçülmeyecek** — RadTr'de önceki-tetkik referansı 4 anma (adım 5)

Bundan sonrası TASK-15: 56 belgeyi iki yolla İngilizceye çevir, üç kolu
(TR · EN-çeviri · EN-tıbbi) aynı altın veriye karşı puanla, **dil kararını** ver.

---

## Zaman tahmini

| adım | süre |
|---|---|
| 4 · kavram yüzeyleri | ~1 gün |
| 5 · ipucu sözlüğü | ~1 gün |
| 6 · `dev` üzerinde sına | ~1 gün |
| **çeviri aşaması açılır** | **3–4 iş günü sonra** |

---

## Uzman onayı — ne zaman gerekiyor

**Şu an bloke değil.** Ablasyon karşılaştırmalı bir soru soruyor; Türkçe
desenlerin mükemmel olmasını gerektirmiyor. İki taraf da aynı sistemle, aynı
altın veriye karşı ölçülüyor.

Onay **sonucu yorumlarken** gerekiyor:

> Türkçe tarafı düşük çıktı diyelim. Sebep **dilin kendisi mi**, yoksa **yazılan
> desenlerin zayıflığı mı**? Bu ikisini ayırmak radyolog gözü ister.

Bu yüzden ablasyon raporunda *"düşüklük dilden mi araçtan mı ayrılamaz"* sınırı
açıkça yazılacak ve karar tablosunun üçüncü satırı bu durumda **kararı
erteliyor**.

---

## Bilinen sınırlar — ablasyon raporuna aynen geçecek

| sınır | etkisi |
|---|---|
| RadTr **sentetik** (radyolog yazımı ama gerçek hasta değil) | Sonuç *"RadTr benzeri Türkçe metinlerde"* diye yazılır |
| **56 belge** ölçüm kümesi | Güven aralığı geniş; tek nokta tahmini sunulmaz |
| **Hizalı çift yok** | Aynı raporun insan yazımı TR *ve* EN hâli yok; EN kolu makine çevirisi. Çeviri hatası ile dil etkisi tam ayrılamaz |
| Yüzeyler **uzman onaysız** | Yukarıda |
| Türkçe kaynak **tek** | İkinci bir kaynak bulunursa genellenebilirlik artar |

> **CT-RATE Türkçe aslı elimize geçerse** ilk üç sınır birden kalkar: hizalı
> çift, gerçek hasta, binlerce belge. RadTr ablasyonu sorunun cevabını verir,
> CT-RATE Türkçesi cevabı **kesinleştirir**.
