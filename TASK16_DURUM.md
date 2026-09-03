# TASK-16 · Adım Adım Durum

**Görev:** Malignite değerlendirme şemasının tanımlanması
**Kaynak listedeki yeri:** T-03 (→ TASK-16, 17, 18, 19) · Faz 3'ün ilk görevi
**Son güncelleme:** 2026-09-03 · **İlerleme: 5 / 9 adım**

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

---

## ✅ Adım 4 · Sınır vakası ve kontrol takımları

**Bu adım ne yapar:** Şemanın sınavını hazırlar — **kurallar yazılmadan önce.**
Sıra kritik: vakaları da kuralları da aynı anda yazarsak kabul ölçütü
kendiliğinden sağlanır ve hiçbir şey ölçmez.

- [x] Vakalar **ilan edilmiş yordamla** örneklendi (sabit tohum `20260904`,
      popülasyon başına kota) — *"zor görünen cümleyi elle seç"* yapılmadı
- [x] **30 sınır vakası** + **15 negatif kontrol vakası** seçildi
- [x] Her vakanın **hedef sınıfı** kurallardan önce atandı, dayanağı ve
      gerekçesiyle
- [x] Takımlar hash'lenip **kilitlendi**; üzerine yazma reddediliyor
- [x] 10 otomatik test yazıldı

**Örnekleme havuzu:** 124.831 benzersiz özgün cümle — geliştirme havuzu, şablon
cümleler hariç, maruz kalınan 17 hasta hariç.

**Sınır takımı — hedef dağılımı:**

| hedef | vaka |
|---|---:|
| indeterminate | 7 |
| known_malignancy | 6 |
| intermediate | 5 |
| low | 5 |
| None | 3 |
| high | 2 |
| not_mentioned | 2 |

Ölçeğin **yedi değerinin hepsi** temsil ediliyor — dejenere bir takım değil.

**Kontrol takımı:** 15 vaka, hiçbiri malignite üretmemeli. **Toleranssız kapı**
— şema birinde bile malignite üretirse dondurulmaz.

**⚠ Kaydedilen artık sınır:** hedefleri atayan taraf ile kuralları yazacak taraf
**aynı**. Tam bağımsız bir sınav değil. Üç azaltıcı önlem alındı ve sonuç ikiye
ayrılarak raporlanacak:

| | vaka | ne ölçer |
|---|---:|---|
| Hedefi **A kuralına** dayanan | **13 / 30** | gerçek dışarıdan denetim |
| Hedefi **C varsayılanına** dayanan | 17 / 30 | iç tutarlılık kontrolü |

**Ne bulundu — bir kod hatası:**

> Ölçeğin **`None`** değeri (belgenin ölçeğindeki *"şüphe yok"* düzeyi), pandas
> tarafından **boş hücre** sanılıyor. `None` pandas'ın varsayılan "eksik veri"
> listesinde. Testler bunu yakaladı: 4 kontrol vakasının hedefi boş görünüyordu.
>
> Düzeltildi: bu dosyalar her zaman `keep_default_na=False` ile okunuyor ve
> uyarı koda yazıldı. Şema kodunda tekrar etmesin diye.

**Çıktı:** `data/processed/sema_sinir_vakalari.csv` · `sema_negatif_kontrol.csv` ·
`configs/sema_takim_kilidi.json` · `scripts/44` · `scripts/45` ·
`tests/test_task16_takim.py`

---

## ⬜ Adım 5 · Girdi kalite filtresi

**Bu adım ne yapar:** Şemanın girdisi Faz 2'nin çıkarımı ve o katmanın kusurları
**ölçülmüş**: zaman ekseni F1 **%36,4** (eşiği geçemedi), belirsizlik duyarlılığı
%71/%46.

Risk: çıkarım geçmiş bir nodülü `present` verirse, *"en yüksek şüphe kazanır"*
kuralı raporu haksız yere maligniteye yükseltir — **projenin ana hedefinin tam
tersi.**

- [ ] Çelişkili varlıklar ayrı kanala düşecek, rapor sınıfını yükseltemeyecek
- [ ] Hata bütçesi yazılacak
- [ ] Duyarlılık analizi koşulacak

---

## ⬜ Adım 6 · Şemanın yazılması

- [ ] `configs/degerlendirme_semasi.json`
- [ ] Doğrulayıcı + testler

**Geçmesi gereken üç kapı:** kilitli hedef sınıflarla %100 uyum · negatif koruma
kapısı %100 · dağılım önceden dondurulmuş aralıkta

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
- [ ] Gerekçe belgesi tamamlanacak (adım 6'dan sonra)

---

## Bu görevin bilinen sınırları

1. **Klinik uzman onayı olmayacak** — 10 C kararı belgelenmiş mühendislik
   varsayılanı kalacak (D71)
2. **Korpusun ~%25'i kılavuzsuz bölge** — 35 yaş altı
3. **Büyüme ekseni yok** — 167 cümle; kılavuzun büyüme kuralları uygulanamıyor
4. **Girdi katmanının zaman ekseni zayıf** — F1 %36,4
5. **Patoloji ground truth'u yok** — ölçülebilen şey rapor uyumu, klinik doğruluk
   değil
