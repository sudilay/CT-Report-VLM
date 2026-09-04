# TASK-16 · Adım Adım Durum

**Görev:** Malignite değerlendirme şemasının tanımlanması
**Kaynak listedeki yeri:** T-03 (→ TASK-16, 17, 18, 19) · Faz 3'ün ilk görevi
**Son güncelleme:** 2026-09-04 · **İlerleme: 6,5 / 9 adım**

Bu dosya yalnız TASK-16'yı takip eder. Projenin geneli için → [DURUM.md](DURUM.md)

---

## Bu görev neyi üretiyor

Bir **karar şeması**: rapordan çıkarılmış bulgular verildiğinde, o raporun
malignite açısından hangi sınıfa düştüğünü söyleyen kurallar bütünü.

Neden önemli: T-04'ten T-13'e kadar her ölçüm bu şemaya dayanacak. Buradaki
belirsizlik sonraki bütün metriklere yayılır.

---

## Hazırlık — adımlar başlamadan önce

- [x] **Çalışma planı yazıldı** → [docs/29](docs/29_task16_calisma_plani.md)
- [x] **Plan bağımsız denetime verildi** → [docs/32](docs/32_task16_bagimsiz_denetim.md)
  25 bulgu çıktı; 21'i kabul, 3'ü kısmen, 1'i reddedildi. Hüküm *"bu plan
  uygulamaya hazır değildir"* idi ve kabul edildi — **v1 uygulanmadı, v2 yazıldı**

**Denetimin bulduğu üç yapısal kusur:**
1. Otorite modeli çelişkiliydi — kaynakta yazılı olmayan ~40 kural *"aktarılmış"*
   sayılmıştı
2. **Yanlış pozitif koruma kapısı yoktu** — projenin ana hedefini sınayan tek bir
   ölçüt bile yoktu. Eklendi
3. Faz 2'nin bilinen çıkarım hataları hesaba katılmamıştı — girdi kalite filtresi
   eklendi

---

## ✅ Adım 0 · Bölünme kilidi

**Bu adım ne yapar:** Şemayı yazarken korpusa bakacağız. Sonra o şemanın ne kadar
iyi olduğunu ölçeceğiz. Aynı veride ölçersek "sınav sorularını görmüş öğrenci"
oluruz. Bu yüzden veriyi **iş başlamadan önce** ikiye ayırdık.

- [x] Veri hasta düzeyinde ikiye ayrıldı
- [x] Ayrım tekrar üretilebilir yapıldı (sabit tohum `20260903`)
- [x] Üzerine yazma koruması kondu
- [x] 9 otomatik test yazıldı
- [x] Maruziyet kaydı çıkarıldı

**Sonuç:**

| | hasta | çalışma |
|---|---:|---:|
| Geliştirme havuzu — bakacağımız | **17.000** | 20.576 |
| Değerlendirme kilidi — bakmayacağımız | **4.304** | 5.116 |

**Ne bulundu:** Plan yazılırken örnek olarak kullandığım 8 cümle, bölünmeden
**önce** çekilmişti. Ölçtüm: **17 hasta** kilitte. Ama 14'ü tek bir **şablon
cümleden** geliyor (onlarca raporda birebir aynı yazılan metin, hastaya özgü
bilgi taşımıyor). **Gerçek maruziyet 3 hasta.** Hepsi sonraki takımlardan
dışlanacak.

**Çıktı:** `configs/splits_holdout.json` · `scripts/40` · `tests/test_task16_bolunme.py` · `reports/task16_maruziyet_kaydi.json`

---

## ✅ Adım 1 · Karar sayısının ölçülmesi

**Bu adım ne yapar:** Şemanın kaç yerde "klinik yargı" gerektireceğini bulur.
Tahmin etmek yerine sayar: aynı cümlede birbiriyle çelişen göstergeler varsa,
şemanın hangisinin kazandığını söylemesi gerekir — o bir karar noktasıdır.

- [x] 383.644 cümle tarandı (yalnız geliştirme havuzu)
- [x] 19 karar maddesi çıkarıldı
- [x] Her madde için varsayılan karar ve gerekçesi yazıldı
- [x] **Varsayılanların hepsi gerçek cümlelerle sınandı**

**Ne bulundu — sınav sonucu: 6 doğrulandı, 4 değişti, 3 düşürüldü**

İki varsayılanım tamamen yanlış çıktı:

> **#1** *"negasyon varsa bulgu yoktur"* → **YANLIŞ.**
> *"**No** significant difference … in terms of … **metastases**"* cümlesinde
> olumsuzlanan şey **değişiklik**, metastaz **var**. Kuralım gerçek bir metastazı
> siliyordu. Doğrusu: olumsuzluğun **neyi kapsadığına** bakmak.

> **#6** *"malignite + benign varsa malignite kazanır"* → **YANLIŞ SORU.**
> Gerçek cümleler: *"**malign-benign ayrımı yapılamadı**"*, *"TB granülomu,
> pnömokonyoz **veya** malignite ile uyumlu olabilir"*. Ortada çelişki değil,
> radyoloğun **ilan ettiği belirsizlik** var. Taraf tutmak bilgiyi bozuyor.

**Üç ölçüm artefaktı:** `büyüme` deseni fazla geniş (*"density increase"* büyüme
sanılıyordu) · `stabilite` ∩ `negasyon` sahte çelişki · **`belirsizlik`
sözlüğümün %71'i `in favor of`** ama proje bunu zaten *"çıkarım ifadesi"*
saymıştı.

**Çıktı:** [docs/31](docs/31_task16_klinik_karar_listesi.md) · `scripts/42` · `reports/task16_celisen_gosterge_taramasi.json`

---

## ✅ Adım 2 · Kaynakta yazılı kuralların aktarılması

**Bu adım ne yapar:** Şemayı biz uyduramayız (proje kuralı D27). Kaynakta
**cümle olarak yazılı** olan kuralları aktarır. Kabul ölçütü: her kural için
kaynağın **spesifik tablo/paragrafı** gösterilecek.

- [x] Alan sözlüğü §12.2 okundu → **20 kural**
- [x] RECIST 1.1 indirildi ve okundu → **4 kural**
- [x] Lung-RADS v2022 okundu → **7 kural**
- [x] Fleischner 2017 okundu → **4 kural**

**Toplam 35 doğrulanmış kural.**

⚠ Lung-RADS ve Fleischner **programla indirilemedi** (302 / 403). Kullanıcı elle
indirdi. `data/raw/` gitignore'da — telifli içerik commit'e girmiyor.

**Ne bulundu — dört kararımız artık "bizim tahminimiz" değil:**

| karar | kaynak |
|---|---|
| **#2** Enfeksiyon ayrı eksende | Lung-RADS enfeksiyöz bulguyu **Kategori 0**'a, şüphe ölçeğinin *dışına* koyuyor |
| **#7** Kalsifikasyon benign yapmaz | Lung-RADS benign listesini **dar** tanımlıyor · Fleischner aynı ilkeyi konum için yazıyor |
| **#9** En yüksek şüphe kazanır | **İki kılavuz da** bu kuralı yazılı kullanıyor |
| **#15** Büyüme şüpheyi yükseltir | *"yavaş büyüyen nodül **is suspicious**"* |

**Ve bir soru tamamen düştü:**

> **#19** *"Kılavuzlar çatışırsa hangisi öncelikli?"* → **soru yanlış kurulmuş.**
> Fleischner kendi metninde kapsamını sınırlıyor ve *"tarama için Lung-RADS'a
> bakın"* diyor. **Kapsamlar ayrık, çatışma yok.**

⚠ **Bir yanlış atıfımı geri çektim:** kılavuzları okumadan *"Fleischner büyümeyi
malignite göstergesi sayar"* yazmıştım. Okuduktan sonra iddia geri geldi — ama
Lung-RADS'tan, Fleischner'dan değil.

**Çıktı:** [docs/30](docs/30_task16_sema_gerekce.md)

---

## ✅ Adım 3 · Kuralların korpusta karşılığı var mı

**Bu adım ne yapar:** Kılavuzda yazılı olması yetmez — kural bu korpusta
uygulanabiliyor mu? Karşılığı olmayan kural şemaya girmez.

- [x] Her A kuralının korpustaki hacmi ölçüldü
- [x] Yaş dağılımı ölçüldü (metadata'dan)
- [x] Büyüme ekseni ayrıca denetlendi

**Ne bulundu — iki büyük sürpriz:**

> ### ⭐ Büyüme ekseni bu korpusta YOK
>
> `enlarged` burada *"büyümüş"* değil **"büyük"** demek. 14.378 eşleşmenin
> **12.233'ü** *"enlarged lymph node"* — statik boyut, üstelik çoğu
> olumsuzlanmış (*"**No** enlarged lymph nodes were detected"*).
>
> **Gerçek büyüme: 383.644 cümlede 167 tane** (%0,64 çalışma).
>
> Sonucu: Lung-RADS'in büyüme kuralları **şemaya girmiyor** ve **iki karar daha
> düştü** (#15, #17). Daha önce düşen #3, #14, #18'in sebebi de geriye dönük
> açıklandı — hepsi büyüme temelliydi.

> ### ⭐ Korpusun dörtte birinde hiçbir kılavuz geçerli değil
>
> Fleischner *"35 yaş altına uygulanmaz"* diyor. Korpusun **%24,53'ü**
> (5.046 çalışma) 35 yaş altı. Lung-RADS ise tarama için, bu korpus tarama değil.
>
> Şema bu bölgede yalnız kendi varsayılanlarıyla çalışacak ve **bu raporda
> yazılı olacak.**

**Kalsifikasyon:** kılavuzun benign saydığı paternler — `popcorn` **0**,
`central` 17, `concentric` 16, `complete` 3 → toplam ~36 cümle. Genel
*"calcific"* ise **13.862**. Yani **%99,7'si** benign tanımını karşılamıyor.

**Çıktı:** `scripts/43` · `reports/task16_b_olcumleri.json` · [docs/30 §6](docs/30_task16_sema_gerekce.md)

---

## 📉 Buraya kadar net sonuç

> **Klinik yargı gerektiren karar sayısı 19'dan 10'a indi.**

| ne oldu | madde | hangileri |
|---|---:|---|
| Kaynağa dayandırıldı (artık tahmin değil) | **4** | #2 #7 #9 #15 |
| Gerçek çelişki içermediği için düşürüldü | 3 | #3 #14 #18 |
| Büyüme ekseni olmadığı için düşürüldü | 1 | #17 |
| Kılavuzlar çatışmadığı için düşürüldü (kapsam kuralına dönüştü) | 1 | #19 |
| **Kalan gerçek klinik karar** | **10** | #1 #4 #5 #6 #8 #10 #11 #12 #13 #16 |

*(4 + 3 + 1 + 1 + 10 = 19 ✓)* · Ayrıca #15'in A'ya taşınmasından artakalan
"tavan" alt-kararı da büyüme ekseni olmadığı için düştü; o 19'un içinde değildi.

Kalan 10'un hepsinin varsayılanı ve gerekçesi yazılı. Uzman onayı alınmayacağı
için (bkz. karar D71) bu kayıt şemanın tek savunması.

⚠ **Bu sayı adım 4'ün ikinci denetiminde 10 → 13'e çıktı** — denetim üç yazılı
olmayan kararı ortaya çıkardı (`known_malignancy` eşiği · benign hükmün
spikülasyonu ezmesi · teknik çekincede lezyon var/yok ayrımı). Aşağıya bak.

---

## ✅ Adım 4 · Sınır vakası ve kontrol takımları — **v1.1 (2. denetim sonrası revize)**

**Bu adım ne yapar:** Şemanın sınavını hazırlar — **kurallar yazılmadan önce.**
Sıra kritik: vakaları da kuralları da aynı anda yazarsak kabul ölçütü
kendiliğinden sağlanır ve hiçbir şey ölçmez.

- [x] Vakalar ilan edilmiş yordamla örneklendi (sabit tohum `20260904`)
- [x] Her vakanın hedef sınıfı **kurallardan önce** atandı
- [x] Takımlar kilitlendi (**v1.0**)
- [x] ⭐ **İkinci bağımsız denetim istendi ve uygulandı** → [docs/33](docs/33_task16_denetim2_ve_duzeltme_plani.md)
- [x] Kilit **v1.1** olarak yeniden kilitlendi; v1.0 arşivde saklanıyor (silinmedi)

**Örnekleme havuzu:** 124.831 benzersiz özgün cümle — geliştirme havuzu, şablon
cümleler hariç, maruz kalınan 17 hasta hariç.

### İkinci denetim — ne bulundu, ne düzeltildi

Denetim **14 bulgu** çıkardı; 11'i tam, 2'si kısmen kabul edildi, 1'i kısmen
reddedildi. En ağır ikisi: **kendi yazdığım A20 kuralını kendim ihlal
etmişim** ve **`docs/31` #12'nin kaydıyla kilitlenen CSV çelişiyordu.**

**6 hedef düzeltildi:**

| vaka | eski | yeni | sebep |
|---|---|---|---|
| `C16-enf-03` | `low` | **`not_mentioned`** | A20 ihlali — öneri status değildir |
| `C6-benign-02` | `low` | **`None`** | A8 + #12: radyoloğun kesin benign hükmü kazanır |
| `C4-yuksek-01` | `known_malignancy` | **`high`** | yazılı bilinen kanser yok — yeni eşik kararı |
| `C13-ekstra-02` | `indeterminate` | **`intermediate`** | soru işareti yönlü hipotez |
| `C12-01`, `C12-02` | `low` | **`None`** | kendi kaydımla iç çelişki |

**Bir kod hatası düzeltildi:** `indeterminate` koruma kapısında "malignite
üretiyor" sayılmıştı — kendi #8 eşlememle çelişiyordu. Düzeltildi.

**Kontrol takımı 15 → 23 vakaya çıkarıldı** — şablon negatifler, post-op
değişiklik, amfizem, koroner kalsifikasyon eklendi (klinikte en çok yanlış
pozitif üreten gruplar hiç temsil edilmiyordu).

**⭐ Tamamen kaçırdığım bir şey bulundu:** 45 vakanın hepsi **tek cümleydi**,
ama şemanın çıktısı **rapor düzeyi**. Toplama kuralının (#9) hiç testi yoktu.
**5 çok cümleli rapor vakası eklendi.**

Bir de **yeni bir kural** ortaya çıktı: *"no suspicious mass was observed"* —
şüphe kelimesi var ama **açıkça olumsuzlanmış**. Bu, *"cannot be excluded"*
kalıbından farklı; burada şüphe **dışlanıyor** → `None`.

**3 yeni C kararı kayda girdi**, C toplamı 10 → 13 oldu.

**⚠ Kaydedilen artık sınır:** hedefleri atayan taraf ile kuralları yazan taraf
**aynı**. Tam bağımsız bir sınav değil; sonuç bu yüzden ikiye ayrılarak
raporlanıyor (A dayanaklı 13/30 = dışarıdan denetim · C dayanaklı 17/30 = iç
tutarlılık).

**Ne bulundu — bir kod hatası:**

> Ölçeğin **`None`** değeri, pandas tarafından **boş hücre** sanılıyor.
> Testler yakaladı: 4 kontrol vakasının hedefi boş görünüyordu. Düzeltildi:
> bu dosyalar her zaman `keep_default_na=False` ile okunuyor.

**Çıktı:** `data/processed/sema_sinir_vakalari.csv` (30) ·
`sema_negatif_kontrol.csv` (23) · `sema_rapor_vakalari.csv` (5) ·
`configs/sema_takim_kilidi.json` (v1.1) ·
`configs/arsiv/sema_takim_kilidi_v1.0_superseded.json` ·
`scripts/44-46` · `tests/test_task16_takim.py`

⚠ **Bu kilit açma ikinci bir kilit açma için emsal değil.** Kurallar
yazıldıktan sonra gelen her hedef değişikliği talebi reddedilecek — ve
adım 6'da tam olarak böyle bir talep doğdu, reddedildi (bkz. D75).

---

## ✅ Adım 5 · Girdi kalite filtresi

**Bu adım ne yapar:** Şemanın girdisi Faz 2'nin çıkarım katmanı ve o katmanın
kusurları **ölçülmüş**. Filtre, o ölçülmüş hataların rapor sınıfını **haksız
yere yükseltmesini** engeller.

- [x] Çıkarım katmanının gerçek alanları incelendi (`entities.parquet`)
- [x] Risk sayısallaştırıldı — tahminle değil ölçümle
- [x] İki filtre kuralı yazıldı, her biri ölçülmüş bir kusura dayanıyor
- [x] Hata bütçesi ve **ölçülemeyen risk** ilan edildi
- [x] 12 otomatik test

### ⭐ Ne bulundu — eksenin kendisi bilgi taşımıyormuş

> **Zamansallık ekseninin %99,24'ü varsayılan.** Yani sistem *"current"*
> derken bir şey **bulmuş** değil, **bulamamış**. "Current" bir kanıt değil,
> kanıt yokluğu. Aynısı `present` için de geçerli: **%80,33'ü** ipucu olmadan
> atanmış.

**Somut risk doğrulandı:** `prior + present` olan **4.557** varlık var ve
bunların **%81,4'ü ipucusuz**.

| kod | ne yapar | dayanağı |
|---|---|---|
| **F1** `gecmis_bulgu` | `temporality = prior` olan her varlık şüphe yükseltemez | K7 F1 **%36,4** — eşiği geçemedi (D39) |
| **F2** `kanitsiz_present` | Malignite kavramı + `present` ama **ipucu yok** → şüphe yükseltemez | `present`in %80,33'ü varsayılan (D29) |

**Filtre varlık ELEMEZ, ETİKETLER.** Düşük güvenli varlıklar kayıtta kalır —
sadece rapor sınıfını yükseltemez.

**Etkisi:** tüm varlıklarda düşük güven %2,98 · **malignite ekseninde %34,3**
(24.098 / 70.258) · en az bir düşük güvenli varlık içeren çalışma %50,7. Filtre
iyi hedeflenmiş: her şeyi bastırmıyor, **tam gerektiği yerde** ısırıyor.

⚠ **Ölçülemeyen risk ilan edildi:** *kaçırılan* `prior`'lar — geçmiş bir
bulgunun `current` sanılması. K7 eşiği geçemediği için bu yönün büyüklüğü
**ölçülemez.**

⚠ **Adım 6'da faturası göründü:** F1/F2 dört sınır vakasını da susturdu ve
üçünde hedefle uyuşmadı (aşağıda "girdi_filtresi" sebebi). Filtre yanlış
çalışmıyor — **girdisi yanlış.**

**Çıktı:** `src/radyovlm/evaluation/girdi_filtresi.py` · `scripts/47` ·
`reports/task16_girdi_filtresi_olcum.json` · `tests/test_task16_girdi_filtresi.py`

---

## 🟨 Adım 6 · Şemanın yazılması — **koruma kapısı geçti, hedef uyumu kısmi**

**Bu adım ne yapar:** Kararları koda çevirir ve kilitli takıma karşı sınar.
Kural: **sonuç zorlanmaz.** Uymayan vaka varsa ya kural düzeltilir (yazılı bir
karara dayanıyorsa) ya sebebi ilan edilir — hedef **asla** değiştirilmez.

- [x] Şema kodlandı → `src/radyovlm/evaluation/sema.py`
- [x] Kilitli takıma karşı sınandı → `scripts/48`, `reports/task16_sema_sinavi.json`
- [x] Her uyumsuzluğun **sebebi teşhis edildi** (5 sınıf, aşağıda)
- [x] 8 kural düzeltmesi uygulandı — hepsi yazılı bir A#/C# kararına atıflı
- [x] Bildirimsel kayıt yazıldı → `configs/degerlendirme_semasi.json`
- [x] 31 birim testi — kod ile bildirimsel kayıt birbirine bağlandı
- [x] Dağılım kapısı koşuldu (aralık **önce** donduruldu) → ❌ **kaldı**, D76
- [x] Duyarlılık analizi koşuldu (docs/29 §7/3)
- [ ] **Şema dondurulmadı** — üç kapıdan ikisi geçmedi (aşağıda)

### ⭐ En önemli bulgu — yazılmış, atıflı ve **hiç çalışmamış** kurallar

Sınavın ilk koşumunda uyum düşüktü. Kuralları suçlamadan önce alete bakıldı
(D60'ın kuralı) ve şu çıktı:

> `entities.parquet`'in **`raw_text` alanı varlığın kendi span'i** — ortalama
> **11 karakter** (*"ground glass"*), azami 36. Şemanın **cümle** arayan üç
> deseni bu span'de aranıyordu. Yani `C#16` (ayırıcı tanı) ve yeni negatif-şüphe
> kuralı **bir kez bile tetiklenemezdi.**

Kanıt gizlenemezdi: sınav raporundaki `belirleyici_kaynak` alanında `C#16`
atfı **sıfır kez** geçiyordu. Kurallar yazılmış, kaynağa bağlanmış, teste
girmiş — ve **ölü kod** olarak durmuştu.

Bu, D27'nin (*"atıfsız kural yazma"*) görmediği bir boşluk: **atıflı ama ölü
kural.** Kayda geçti → **D73**.

Üstelik ölü olduğu için içindeki bir hata da görünmemişti: ayırıcı tanı deseni
`may be`'yi de kapsıyordu, oysa docs/33 §3.4 ikisini **ters yönde** ayırıyor
(*"may be compatible with metastasis"* = yönlü hipotez → `intermediate`;
*"infection **or** metastasis"* = ayırt edilemezlik → `indeterminate`).

### Derece kelimesi artık okunuyor

`assertion_cue` alanı *"highly"* gibi derece kelimelerini korumuyor — *"highly
suspicious"* ile çıplak *"suspicious"* aynı cue'ya düşüyor. Ölçüldü
(`reports/task16_b_olcumleri.json`):

| desen | cümle | çalışma |
|---|---:|---:|
| **high suspicion** (`highly/strongly suspicious`, `highly suggestive`) | 392 | **230 (%1,12)** |
| suspicious (yalın) | 1.835 | 1.451 (%7,05) |

Artık derece **cümleden** okunuyor ve `high` üretilebiliyor.

⚠ **Bu tablo yanıltıcı okunabilir ve aşağıda düzeltildi:** ölçüm *"şüphe
derecesi dili"*ni sayıyor, *"malignite şüphesi derecesi"*ni değil. Dağılım
kapısı bunu ortaya çıkardı — 392 derece cümlesinin **yalnızca 15'i** kanser
terimi içeriyor.

⚠ **Sınırı yazılı:** karar hâlâ `entity_id`'ye bağlı. Metinden **yeni varlık
üretilmiyor**, yalnızca *zaten çıkarılmış* bir varlığın derecesi okunuyor. Bu,
reddedilen "raw-text yedek arama" seçeneğinden (izlenebilirliği kırardı) tam
olarak bu yüzden farklı.

### Uygulanan 8 kural düzeltmesi — hepsi yazılı bir karara dayanıyor

| düzeltme | dayanak | çözdüğü |
|---|---|---|
| C#16 assertion dalından çıkarıldı, cümle düzeyine alındı | C#16 | `C4-derece-orta-02` |
| Ayırıcı tanı deseni daraltıldı (`may be` çıktı) | docs/33 §3.4 | yanlış pozitif önlendi |
| *"cannot/could not be excluded"* cümle düzeyinde | A18 | `C16-malignite-enf-02` |
| *"cannot be clearly distinguished"* → lezyon var, karakterize edilemiyor | docs/33 §4.3 | **`K-teknik-02`** (koruma kapısı) |
| Parantez içi soru *"(metastasis?)"* → yönlü hipotez | docs/33 §3.4 | `C13-ekstratorasik-02` |
| Radyoloğun **kesin** benign hükmü malignite adayını ezer | docs/33 §4.2 | `C6-malignite-benign-02` |
| *"possibly benign"* / yağlı hilus benign hüküm sayılır | A26 + C#12 | `C12-benign-belirsiz-01` |
| `spiculated` F2'den muaf — **gözlenen morfoloji**, çıkarım değil | A34 | `A26-kalsifikasyon-01/02` |

⚠ Son kural ilk denemede fazla geniş yazılmıştı: *"possible sequelae"* de
"kesin hüküm" sayılıp iki vakayı bozdu (biri kontrol takımında). Daraltıldı —
yalnız hüküm dereceli çıkarım kuralları (`in favor of`, `compatible with`)
sayılıyor, hedge'liler (`possible`) sayılmıyor.

### Sınav sonucu — zorlanmadı

| takım | ilk koşum | **şimdi** |
|---|---:|---:|
| Sınır (30) | 11 | **20** |
| Kontrol (23) | 21 | **22** |
| Rapor (5) | 3 | 3 |
| **Koruma kapısı** (toleranssız) | ❌ 1 ihlal | ✅ **0 ihlal — GEÇTİ** |

**369 test geçiyor.**

### Kalan 13 uyumsuzluğun sebebi — hiçbiri "kural" değil (2 istisna)

| sebep | adet | ne demek |
|---|---:|---|
| `sozluk_boslugu` | 3 | Cümlede malignite terimi var, çıkarım katmanı **hiç varlık üretmemiş** → TASK-17 |
| `girdi_filtresi` | 5 | Malignite varlığı var ama F1/F2 susturmuş → girdi katmanı, kural değil |
| `known_malignancy` | 2 | docs/33 §4.1 eşiği (yazılı bilinen kanser tespiti) → TASK-17 |
| `kavram_listesi_eksik` | 1 | Varlık çıkmış ama şemanın malignite listesinde değil (`lesion`) |
| `kural` | 2 | `R3`, `R4` — aşağıya bak |

⚠ **Bu sınıflandırma uyumsuzluk sayısını düşürmez.** 13 uyumsuzluk 13
uyumsuzluktur; sebep yalnız *"kimin işi"* sorusunu cevaplar.

### ⭐ İki sistematik sınır ortaya çıktı

> **1 · Şema stabil takipteki bilinen kanseri göremiyor.**
> `C5-stabil-malignite` ailesinin **üçü de** kayboluyor: biri sözlük boşluğundan
> (*"regressed primary malignancy"* hiç varlık üretmiyor), ikisi zaman
> ekseninden (cümlede *"previous examination"* geçtiği için varlığa `prior`
> atanıyor, F1 doğru şekilde susturuyor). Filtre çalışıyor, **girdisi yanlış** —
> K7'nin ölçülmüş zayıflığı (F1 %36,4) faturasını burada kesiyor.

> **2 · `low` düzeyi pratikte hiç üretilemiyor.**
> Düşük güvenli aday varken şema `not_mentioned` diyor; oysa ölçekte `low` tam
> bunun karşılığı. Denendi ve **geri alındı**: `low` üretmek koruma kapısını
> kırıyor (`low` malignite üreten sınıflardan), şablon negatiflerin çoğu
> `low`'a kayıyordu. Ölçek altı basamaklı ama motor **beşini** kullanıyor —
> ilan edilen bir sınır.

### ⚠ Hedef atama yordamı ile motorun kavram listesi aynı değil (D75)

`R3` ve `R4`'te hedef *"raporda malignite terimi geçiyor mu"* sorusunu bir
**regex'e** sordu; motor ise kavram listesine bakıyor. `mass` kavram listesinde
var, regex'te yok → *"No active infiltration or **mass lesion** was detected"*
hedef atayıcıya görünmedi.

**Motorun cevabı tartışmasız daha doğru.** Kilit yine de açılmadı: adım 4'ün
kuralı *"kurallar yazıldıktan sonra hedef değişikliği reddedilir"* ve bu tam
olarak öyle bir talep. İki vaka **kalıcı uyumsuz** sayılıyor, sebebi yazılı.

### Sözlük boşluğu ölçüldü — "3 kelime" değil

| | dev havuzunda |
|---|---:|
| `malignan\|carcinom\|neoplas` geçen cümle | **421 cümle / 288 çalışma** |
| bunlardan **hiçbir varlık üretmeyen** | **79 (%18,8)** |

79 boş cümlenin dökümü: **28'i `carcinomatosis`** (lenfanjitik/peritoneal) ·
39'u yalın `malignan*` · 3'ü `neoplas*` · 9'u diğer.

**`carcinomatosis` bir eş anlamlı değil, ayrı bir kavram** — TASK-17'nin
listesinde ilk sırada.

### "Az şüpheli" ekseni — ölçüldü, YOK

`highly suspicious`'ın tersi arandı: `less likely` 28 cümle (malignite terimiyle
birlikte **yalnız 3**) · `low probability` 20 · `weak/faint suspicious` 6 ·
`unlikely` 3 · `least likely` ve `less suggestive` **0**.

Yukarı yön 392 cümle, aşağı yön ~7 — asimetri **~50:1**. Kural yazılmadı:
korpus desteği de yok, **yazılı bir kaynak kuralı da yok** (hiçbir kılavuz
"şu kelime geçerse bir kademe indir" demiyor). Büyüme ekseninden farkı bu —
orada A28 diye yazılı bir kural vardı. Bu korpusun radyoloğu şüpheyi
indirirken derece kelimesi değil **kesin benign hüküm** kullanıyor; şema onu
zaten C#12 yolundan işliyor.

⚠ Bakanlık kohortu Türkçe **orijinal** olacak — *"daha az olası"*, *"zayıf
ihtimalle"* orada serbestçe çıkabilir. TASK-17'ye not edildi.

### Bağlayıcı karar: sözlük genişletmesi iki kademeli (D74)

| kademe | ne | maliyet |
|---|---|---|
| **Tier A** | Bu korpusta geçen ama kavram üretmeyenler (`carcinomatosis`, `malignancy`, `neoplasm`) | `entities.parquet` değişir → `ent-1.0` kırılır, TASK-11/12/13 sayıları yeniden ifade edilmeli. **TASK-16'da yapılmadı** |
| **Tier B** | Bu korpusta **sıfır** geçen otoriter kanser terimleri (`adenocarcinoma`, `lymphoma`, `sarcoma`…) | **Yok** — hiç eşleşmeyen desen hiçbir sayıyı değiştiremez. Farklı veride kaçırmamak için saf kazanç |

*"Sıfır destekli girdi yok"* kuralı **koşullu gevşetildi**: her girdi `kaynak`,
`korpus_destegi` (0 olabilir) ve `amac: transfer` alanlarını taşıyacak. Böylece
kapsam iddiası şişmez — *"312'si ölçülmüş destekli, 88'i transfer amaçlı"*
denebilir. Kaynak hazır: alan sözlüğü §15 (WHO 2021). RadLex anahtarı
`.env.local`'de mevcut, **veri henüz indirilmedi** (TASK-11'in işi).

### ❌ Dağılım kapısı KALDI — ve sebebi projenin en öğretici bulgusu

docs/29 §8.4'ün kuralı: *"Kabul aralığı koşumdan **önce** dondurulur. Dağılım
aralığın dışına çıkarsa **kural** revize edilir — aralık değil."*

Aralık koşumdan önce donduruldu (`scripts/49`, `DONDURULMUS_ARALIK`), türeyişi
yanına yazıldı ve **yalnız `malignite_pozitif` kapıya bağlandı** — diğer
sınıflar için türetilebilir bir dış çapa yok, capasız aralığa kapı demek v1'in
reddedilen hatasını tekrarlamak olurdu.

| | |
|---|---|
| Dondurulmuş aralık | %0,5 – %3,0 |
| **Gerçek** | **%0,049** (20.576 çalışmanın **10'u**) |
| Sonuç | ❌ **KALDI** |

**Aralığa dokunulmadı.** Bunun yerine popülasyonun nerede eridiği ölçüldü:

| | cümle |
|---|---:|
| Derece cümlesi (`highly suspicious`…) | 392 |
| ↳ **kanser terimi içeren** | **15** |
| ↳ kanser terimi **içermeyen** | **377** |
| ↳ kanser terimli + malignite varlığı çıkan | 12 |
| ↳ kanser terimli ama varlık çıkmayan | 3 |

> ### ⭐ *"Highly suspicious"* bu korpusta kanser cümlesi değil
>
> Derece cümlelerinin **%96'sı** enfeksiyon/COVID şüphesi. Korpusun %21'i COVID
> (docs/08) ve *"suspicious"* ipucu `ground_glass`, `covid`, `pneumonia`
> varlıklarına bağlanıyor.
>
> Yani **çapa yanlış türetilmişti**: *"şüphe derecesi dili"* ile *"MALİGNİTE
> şüphesi derecesi dili"* eşitlenmişti. Kural doğru çalışıyor — korpusta ne
> varsa onu buluyor (15 aday cümlenin 12'sini yakalıyor, 10 çalışma).

**Kural revize EDİLMEDİ** — daha fazla `high` üretmek için kuralı gevşetmek,
korpusun desteklemediği bir sonucu zorlamak olurdu. Kapı **kalmış olarak
kayda geçti** (D76). Doğru çapa artık ölçülü: kesişim popülasyonu 15 cümle;
bir sonraki sürümün aralığı **derece ∩ kanser terimi** üzerinden türetilmeli,
derece kelimesi tek başına üzerinden değil.

### Duyarlılık analizi (docs/29 §7/3)

Çıkarım katmanının **ölçülmüş** hata oranları girdiye enjekte edildi; şema
değiştirilmedi.

| senaryo | `malignite_pozitif` | tabandan kayma |
|---|---:|---:|
| Taban | %0,049 | — |
| **S1** — zaman ekseni güvenilmez (F1 hiç susturmasa) | %0,049 | **+0,000** |
| **S2** — kanıtsız `present`ler gerçek olsa (F2 hiç susturmasa) | %0,107 | +0,058 |
| **S3** — ipuçlu `present`ler aslında `uncertain` olsa | %0,000 | −0,049 |

**Okunuşu:** şemanın malignite-pozitif çıktısı çıkarım katmanının bilinen
hatalarına karşı **çok dar bir bantta** kalıyor (en kötü durumda %0,107, yani
22 çalışma). Zaman ekseni (S1) çıktıyı **hiç** değiştirmiyor — adım 5'in
*"zaman ekseni şemada karar ağırlığı taşımaz"* kararı burada doğrulanıyor.

⚠ Bu bir sağlamlık kanıtı **değil**: bant dar çünkü popülasyon zaten çok
küçük (10 çalışma). Sözlük boşluğu kapandığında (TASK-17) bu analiz
**yeniden koşulmalı.**

### Rapor düzeyi dağılımı (kapı değil, kayıt)

| sınıf | çalışma | % |
|---|---:|---:|
| `malignite_negatif` | 17.832 | %86,66 |
| `belirsiz_yetersiz_kanit` | 1.789 | %8,70 |
| `benign_bulgu` | 182 | %0,89 |
| `malignite_pozitif` | 10 | %0,05 |

⚠ %86,66'lık `malignite_negatif` **aktif negatif hüküm** demek — korpusun
şablon ağırlıklı yapısıyla (*"No mass or nodule was detected"*) tutarlı, ama
`None` ile `not_mentioned` ayrımının bu ölçekte ne kadar anlamlı olduğu
sınanmadı. TASK-17/18'e not.

**Çıktı:** `src/radyovlm/evaluation/sema.py` · `configs/degerlendirme_semasi.json` ·
`scripts/48`, `scripts/49` · `reports/task16_sema_sinavi.json`,
`reports/task16_dagilim.json` · `tests/test_task16_sema.py` (31 test) ·
kararlar **D73, D74, D75, D76**

---

## ⬜ Adım 7 · Bağımsız kontrol

- [ ] Codex sınır vakalarını ayrı yargılayacak; ayrıştıkları öncelikli işaretlenecek

---

## ⬜ Adım 8 · Gözle inceleme sayfası

- [ ] `outputs/task16/sema_tezgahi.html` — her satırda cümle, çıkarılan varlıklar,
      hedef sınıf, şemanın kararı, tetiklenen kural ve inceleyici bayrağı

---

## ⬜ Adım 9 · Gerekçe ve karar defteri

- [x] Karar defterine D70, D71, D72 eklendi
- [x] **D73, D74, D75 eklendi** (adım 6'nın üç bağlayıcı kararı)
- [ ] Gerekçe belgesi tamamlanacak (adım 6 bitince)

---

## Şema neden dondurulmadı

Üç kabul kapısından **biri geçti, ikisi geçmedi** — ve ikisi de aynı köke
çıkıyor: çıkarım sözlüğü malignite terimlerini tanımıyor.

| kapı | eşik | sonuç |
|---|---|---|
| Negatif koruma kapısı | toleranssız | ✅ **0 ihlal** |
| Hedef uyumu | %100 | ❌ sınır 20/30 · kontrol 22/23 · rapor 3/5 |
| Dağılım aralığı | %0,5–%3,0 | ❌ %0,049 |

**Dondurma önkoşulları** (`configs/degerlendirme_semasi.json` içinde de kayıtlı):

1. Sözlük boşluğu kapansın (TASK-17, D74) — uyumsuzlukların 3'ü doğrudan buradan
2. `known_malignancy` tetikleyicisi yazılsın (docs/33 §4.1) — 2 uyumsuzluk
3. Dağılım kapısının çapası **derece ∩ kanser terimi** üzerinden yeniden
   türetilsin (D76)
4. Duyarlılık analizi sözlük genişledikten sonra yeniden koşulsun

Şema şu an `sema-0.9-taslak`. **`sema-1.0` yok.**

---

## Sıradaki iş

1. Adım 7: Codex'in bağımsız kör yargılaması (sınır vakalarını ayrı yargılayacak)
2. Adım 8: inceleme tezgâhı (`outputs/task16/sema_tezgahi.html`)
3. Adım 9: gerekçe belgesinin tamamlanması
4. TASK-17 devri: Tier A/B sözlük genişletmesi, `carcinomatosis` ilk sırada

---

## Bu görevin bilinen sınırları

1. **Klinik uzman onayı olmayacak** — 13 C kararı belgelenmiş mühendislik
   varsayılanı kalacak (D71)
2. **Korpusun ~%25'i kılavuzsuz bölge** — 35 yaş altı
3. **Büyüme ekseni yok** — 167 cümle; kılavuzun büyüme kuralları uygulanamıyor
4. **Girdi katmanının zaman ekseni zayıf** — F1 %36,4. Adım 6'da faturası
   göründü: stabil takipteki bilinen kanser şemaya görünmüyor
5. **Patoloji ground truth'u yok** — ölçülebilen şey rapor uyumu, klinik doğruluk
   değil
6. **Sözlük boşluğu** — `malignancy`, `carcinoma`, `neoplasm`, `carcinomatosis`
   çıkarım sözlüğünde yok; **288 çalışmanın 78'inde** malignite sinyali görünmez
   kalıyor (D74, TASK-17'ye devredildi)
7. **`known_malignancy` otomatik üretilmiyor** — yazılı bilinen kanser tespiti
   ayrı bir tetikleyici gerektiriyor (docs/33 §4.1, TASK-17)
8. **`low` düzeyi kullanılamıyor** — üretmek koruma kapısını kırıyor; ölçek altı
   basamaklı ama motor beşini kullanıyor
9. **Derece kapsamı cümle düzeyi** — aynı cümlede hem dereceli hem derecesiz
   şüphe varsa ikisi de yükselir. Ölçülmedi, ilan edildi
10. **Hedef atama yordamı motorun kavram listesiyle aynı değil** — iki rapor
    vakası kalıcı uyumsuz (D75)
