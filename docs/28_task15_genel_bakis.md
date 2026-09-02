# TASK-15 · Dil Ablasyonu — Genel Bakış

**Durum:** yürütmede · **Son güncelleme:** 2026-09-02
**Kapsam:** RadTr toraks BT raporları · `test` bölümü açılmadı

Bu belge TASK-15'in tamamını tek yerden anlatır: hangi soruya cevap arandığı,
deneyin nasıl kurulduğu, şimdiye kadar ne ölçüldüğü ve neyin kaldığı.
Ayrıntılar için: dondurulmuş tasarım [docs/19](19_task15_deney_tasarimi_dondurma.md),
kararlar ve gerekçeleri [docs/kararlar.md](kararlar.md).

---

## 1 · Cevaplanan soru

> **Faz 3'te altın etiketlemeyi Türkçe mi, İngilizce mi yapmalı?**

Türkçe veri toplamak pahalı ve yavaş. Raporları İngilizceye çevirip mevcut
araçlarla çalışmak ucuz. Ama çeviri bilgi kaybettiriyorsa bu tasarruf yanlış
olur.

TASK-15 bu ikilemi **ölçülebilir** hâle getirir: aynı raporu iki yoldan okut,
ne kadarının aynı çıktığını say. Fark varsa, o fark çevirinin maliyetidir.

---

## 2 · Deneyin kurgusu

Aynı 46 `dev` belgesi (ve 223 `train` belgesi) üç farklı metin biçiminde
üretilir. Her biri **aynı** çıkarım sisteminden geçer; **dil dışında hiçbir şey
değişmez.**

```
                     RadTr Türkçe raporu
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
       TR                 EN-genel              EN-ucuz
   (çeviri yok)        Google NMT           Opus-MT (cümle düzeyi)
    referans        "iyi çeviriyle ne      "ucuza çevirsem ne
                      kaybederim?"            kaybederim?"
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              BİRİNCİL ölçüm      İKİNCİL ölçüm
           dondurulmuş sözlük    tek dil modeli
            (deterministik)      (farklı aileden)
                    │                   │
                    └─────────┬─────────┘
                              │
              aynı yön → sonuç sağlam
              farklı yön → "yönteme bağımlı", dil hükmü kurulmaz
```

**Dördüncü bir kol** (EN-tıbbi: Google → tıbbi post-edit) planlanmıştı ve
**düşürüldü** — üç koşuda da çıktı sözleşmesi sağlanamadı (D63,
[rapor](../reports/task15_medgemma_kol_dusurme.md)).

### Neden iki ayrı ölçüm

| | **sözlük (birincil)** | **model (ikincil)** |
|---|---|---|
| rolü | dil kararını **veren** ölçüm | o kararın **alete bağlı olmadığının** kontrolü |
| doğası | kural tabanlı, deterministik | üretken, örnekleme kapalı |
| gücü | tekrarlanabilir; her kararın hangi kelimeden geldiğini gösterir | sözlüğün yazamadığı biçimleri de görebilir |
| zayıflığı | yazılmamış biçimi göremez | neden öyle dediğini kanıtlayamaz |

Model sözlüğü, desenleri ve birincil çıktıyı **hiç görmez** — yalnız metni ve
kapalı 144 kavramlık envanteri görür. Aksi hâlde birincil sistemi taklit eder
ve bağımsız doğrulama olmaktan çıkardı.

---

## 3 · Ölçüm aleti: iki dilli kavram sözlüğü

Sözlük bir **çeviri sözlüğü değildir.** Ortada dile ait olmayan **144 kavram**
vardır; her dil için ayrı bir dosya *"bu kavram bu dilin metninde şu biçimlerde
yazılır"* der. İki dosya birbirini görmez — karşılaştırmayı mümkün kılan budur.

```
                    ┌──────────────────────────┐
                    │   144 KAVRAM (dilsiz)    │
                    │   cardiomegaly           │
                    │   effusion  ·  rib  ...  │
                    └──────┬────────────┬──────┘
                           │            │
       turkce_yuzeyler ◄───┘            └───► anatomi_ + bulgu_sozlugu
                           │            │
   desen: kardiyomegali|   │            │   desenler: ["cardiomegaly",
          kalp boyut       │            │               "heart dimensions?",
                           │            │               "heart size"]
   kaynak: RadTr korpusu   │            │   kaynak: CT-RATE korpusu
```

Türkçe desenler **kökten** yazılır ve solda sınırlı, sağda serbesttir (Türkçe
sondan eklemelidir: `nod[uü]l` → *nodüller, nodülde, nodüler*). İngilizcede
çekim az, bileşik terim çok; desenler öbek hâlinde listelenir.

Üretimde her iki taraf da **tek birleşik eşleştirici** kullanır ve **en uzun
eşleşme kazanır** — bir metin parçası tek kavrama gider (*"lung parenchyma"* →
`lung_parenchyma`, `lung` + `parenchyma` değil).

---

## 4 · Şimdiye kadarki ana bulgular

### 4.1 İki sözlük eşit hazırlanmamıştı — onarıldı

Türkçe sözlük RadTr'nin 269 belgesini görerek türetilmişti; İngilizce sözlük
CT-RATE'te geliştirilmiş ve RadTr'nin **tek belgesini görmemişti**. Üstelik bazı
İngilizce desenleri korpusun yazdığı biçim değil, **kavram adının çevirisiydi**
(`infective pathology` — oysa metin *"viral infection"* diyor).

Bu hâliyle ölçüm yapılsaydı *"Türkçe daha iyi"* çıkardı ve **yanlış sebeple**
çıkardı.

Simetrik bir geçişle **26 kavram onarıldı** (16 Türkçe, 10 İngilizce). Yöntem
n-gram sıralaması değil, **boşluk cümlelerini okumaktı**; her onarımın gerekçesi
ve okunan cümle sözlük dosyalarında yorum olarak durur.

| | yalnız TR | yalnız EN | ikisi de | Jaccard (toplu) |
|---|---:|---:|---:|---:|
| önce | 639 | 639 | 4.166 | 0,765 |
| **sonra** | **152** | **167** | **5.009** | **0,940** |

Boşluk %75 azaldı ve **denge korundu** — onarım tek taraflı olmadı.
Ayrıntı: [sözlük onarımı raporu](../reports/task15_sozluk_onarimi_raporu.md).

### 4.2 Ölçüm aletinin kendisi bozuk çıktı

Onarıma başlamadan önce, analiz betiklerinin sözlükleri **üretimden farklı
derlediği** bulundu. Bu, sözlükte olmayan hataları sözlük hatası gibi
gösteriyordu: iki öneri geri çekildi ve daha önce raporlanan asimetri rakamları
geçersiz ilan edildi (D60).

Simetrik yeniden ölçümde **onarım öncesi asimetri 639/639, yani sıfırdı.**

Bundan çıkan kural: *bilgi hedef metinde var mı* testini **önce alete uygula.**

### 4.3 Çeviride üç ayrı kayıp türü ölçüldü

Onarımdan sonra kalan farklar gerçek çeviri olaylarıdır ve **bilerek
onarılmadı** — ölçmek istenen şey bunlardır:

| tür | örnek |
|---|---|
| cümle **düşürme** | *"…3-4 adet lenf nodu dikkati çekmiştir"* İngilizce çıktıda yok |
| terim **bozma** | *litik lezyonlar* → ***"Lithic lesions"*** (CT-RATE'te 4 anma; İngilizce radyoloji terimi değil) |
| terim **ekleme** | *buzlu cam **alanları*** (yoğunluk sözcüğü yok) → *ground-glass **opacities*** |

Üçüncüsü beklenmedikti: çeviri yalnız kaybettirmiyor, **kavram da ekliyor.**

### 4.4 Çeviri deterministik değil

Aynı 46 belge dakikalar arayla iki kez çevrildi: **5 belge (%11) farklı çıktı.**
Farkların çoğu sözcük seçimi, ama bir vakada anatomik niteleyici öbekler arası
taşındı. Sonuç: `test` çevirisi **bir kez** koşulur ve ham çıktı değişmez
artefakt olarak saklanır (D53).

### 4.5 Bölünme kirlenmesi bulundu ve düzeltildi

RadTr'nin `train.json` dosyası `dev` ve `test`in tamamını içeriyordu; bölüm
kimliği dosya adından üretildiği için test belgeleri geliştirme havuzuna
sızmıştı. Ölçülen hasar sıfıra yakındı (144 yüzeyin 0'ı yalnız test
belgelerine dayanıyordu) ama **kayıtlar düzeltildi**: bölüm kimliği artık
içerik hash'inden okunur ve her bölünme otomatik denetlenir (D49/D50).

### 4.6 Karar eksenleri ölçümden önce daraltıldı

Güç analizi, `absent` ve `uncertain` eksenlerinin 0,05'lik bir marjı **ayırt
edemeyeceğini** gösterdi (GA yarı genişliği 0,074 ve 0,065). Bu eksenler
**ölçümden önce** ana karar dışı bırakıldı ve betimleyici raporlanacakları ilan
edildi. Karar eksenleri `A1` (kavram çıkarımı) ve `present`tir (D51).

---

## 5 · Şu anki durum

```
✅ Veri hazırlığı · bölünme kirlenmesi düzeltildi
✅ Türkçe sözlük türetildi · güç analizi yapıldı
✅ Çeviri kolları: TR · EN-genel · EN-ucuz        ❌ EN-tıbbi düşürüldü
✅ Sözlük onarımı · simetrik geçiş · donduruldu
✅ Türkçe birleşik kavram çıkarıcı
❌ İkincil model doğrulaması — üç aday da elendi, kol düşürüldü
⬜ Kanonik altın + uzman incelemesi
⬜ Sürüm dondurma raporu
🔒 test — çeviri yapılmadı, skor hesaplanmadı
```

### İkincil model seçimi — devam ediyor

Adaylar `dev`de üç kolun tamamında, aynı istem ve üretim ayarlarıyla sınanır.
Seçim kapıları `test` açılmadan **önce** donduruldu:

| # | kapı | ölçüt |
|---|---|---|
| 1 | çalışabilirlik | bütün belgeler hatasız tamamlanır |
| 2 | yapısal geçerlilik | çıktıların %100'ü doğrudan ayrıştırılabilir; **sonradan onarım yok** |
| 3 | kapalı envanter | envanter dışı kimlik / geçersiz kesinlik oranı sıfır |
| 4 | doğruluk | `A1` + `present` ana; `absent`/`uncertain` betimleyici |
| 5 | dil dengesi | farkın **yönü** ve **en kötü kol**; bir dilde çöken aday seçilmez |
| 6 | eşitlik | ayrışmayan adaylarda daha düşük bellek, süre, daha açık lisans |

İlk koşuda iki aday da kapı 2'yi geçemedi. İhlallerin bir kısmının **koşucu
ayarımızdan** geldiği (üretimin token sınırında kesilmesi) tespit edildi ve
düzeltildi; kalan ihlaller modele aittir ve öyle raporlanacaktır. Ayrıntı
D64'te.

**Sonuç: üç adayın üçü de elendi ve kol düşürüldü.** Qwen3.5-4B %73,9,
Aya Expanse 8B %0 (erken durdurma), önceden ilan edilmiş yedek Qwen3-8B %20,8
(erken durdurma). Üç farklı arıza — tekrar döngüsü, Markdown çiti, envanteri yok
sayma — ama tek ortak duvar: **kapalı 144'lük listeye uymamak.** Dördüncü bir
model seçilmedi; sonucu gördükten sonra model seçmek protokolün engellediği
şeydir.

Rapora giren hüküm: *"Kapalı 144'lük envanterle katı JSON sözleşmesi 4–8B
ölçekli üç açık modelle (iki farklı aile) sağlanamadı; model tabanlı ikincil
doğrulama yapılamamıştır."*

**Ablasyon bundan etkilenmez** — dil kararını birincil ölçüm verir ve hazırdır.
Kaybedilen tek şey *"sonuç sözlüğe bağlı mı"* itirazını kapatma imkânıdır; bu
açık bir sınır olarak raporlanır. Ayrıntı:
[ikincil model raporu](../reports/task15_ikincil_model_raporu.md).

### Kalan iş — bağımlılık sırasıyla

| # | iş | engellediği |
|---|---|---|
| 1 | ~~İkincil model seçimi~~ | **kapandı** — aday havuzu tükendi (D65) |
| 2 | **Kesinlik hattı**: Türkçe çıkarıcının span'ları kesinlik atayıcıya bağlanır | `present` ekseni |
| 3 | **Kanonik altın**: iki bağımsız işaretleyici, kapalı 144 envanter, kör | `test` |
| 4 | **Uzman incelemesi**: birleşmiş liste incelenir, nihai karar verilir | `test` |
| 5 | Altın hash'lenip **kilitlenir** | `test` |
| 6 | Sürüm dondurma raporu (revizyonlar, istem, parametreler, SHA-256) | `test` |
| 7 | `test` çevirisi — **tek sefer**, ham çıktı saklanır | test skoru |
| 8 | Skorlama + eşleştirilmiş bootstrap güven aralıkları | — |

Kritik yol **3 → 4 → 5**. Uzman incelemesi dış takvime bağlıdır.

**2 hakkında:** Türkçe birleşik çıkarıcı `A1` (kavram çıkarımı) için hazırdır ve
`§4`'teki bütün sayılar onunla üretildi. `present` ekseni için bir adım daha
gerekiyor: çıkarıcı şu an belge düzeyinde **kavram kümesi** döndürüyor, kesinlik
ataması ise span konumu istiyor. İngilizce tarafta bu hat kuruludur
(`entities.py` → `context.kesinlik_ata`); Türkçe tarafta kesinlik atayıcı vardır
ama henüz çıkarıcının kendi span'larına bağlı değildir. Küçük ve tanımlı bir
iştir; skorlamadan önce tamamlanır.

---

## 6 · Deneyi koruyan kurallar

Bu kuralların hepsi **sonuç görülmeden** bağlandı. Amaçları, ölçümün kendi
sonucuna göre ayarlanmasını yapısal olarak engellemektir.

**`test` kilitlidir.** Altın hash'lenip kilitlenmeden test tahminleri veya
skorları açılmaz. Sözlük `train`de türetilir, `dev` ayar kümesidir.

**Sözlük onarımı tek geçiştir.** İki sözlüğü birbirine bakarak tekrar tekrar
düzeltmek, farkı ölçmek yerine **imal etmek** olurdu. Bir tur meşru mühendislik,
üç tur sonuç uydurmaktır; aradaki fark niyette değil tekrar sayısındadır.

**Yüzey eklemenin iki koşulu vardır:** bilgi hedef metinde gözle okunabilmeli
(değilse gerçek çeviri kaybıdır, dokunulmaz) ve aday ikinci korpusta da
desteklenmeli (değilse tek korpusa özelleşme olur).

**Çıktı onarılmaz.** Model sözleşmeyi bozarsa bozuk kalır, sayılır, raporlanır.
Onarılsa modelin talimat izleme yeteneği değil, kendi kurtarma kodumuzun
becerisi ölçülürdü.

**Durma kuralları önceden bağlanır.** Bir kolun düşürülme eşiği, sonucu görmeden
yazılır ve sonuç kötü çıkınca gevşetilmez. EN-tıbbi kolu bu kuralla düşürüldü.

**Ham çıktılar değişmez artefakttır.** Çeviri ve model yanıtları, geçersiz
olanlar dahil, olduğu gibi saklanır.

---

## 7 · Yöntemin bilinen sınırları

Bunlar gizlenmiyor; raporlarda ve kararlarda açıkça yazılı.

1. **Türkçe tarafta ikinci korpus yok.** CT-RATE'in Türkçe asılları
   yayımlanmadı. İngilizce yüzey adayları iki korpusta sınandı, Türkçe adaylar
   yalnız RadTr desteğiyle. Bu asimetri kapatılamadı.
2. **Sözlük uzman onayından geçmedi.** Her kavram `uzman_onayi: false` taşır.
   Sözlük bir ölçü aletidir, altın etiket değildir; kanonik altın ayrı üretilir
   ve uzman incelemesinden geçer.
3. **RadLex eşlemesi yapılmadı.** Erişim sağlanamadı; uydurma kimlik yerine
   kimliksiz kalındı. Şemada RadLex alanı hazır bekliyor.
4. **Kapsam toraks BT ile sınırlıdır.** 144 kavram bu korpustan türetildi;
   başka modalite veya bölge için yeniden türetilmesi gerekir.
5. **`absent` ve `uncertain` eksenleri güçsüzdür** ve bu ölçümden önce ilan
   edildi. Sorun bölünmede değil taban oranında (belge başına 1,9 anma).
6. **Bir sözlüğün boşluğu diğerinin bulgusuyla tespit edildi.** Bu dairesel
   değil ama kesin de değil; hüküm her vakada korpus sayımı ve anlam
   kontrolüyle verildi, karşı sözlüğün bulgusuna güvenilerek değil.

---

## 8 · Belge haritası

| belge | ne anlatır |
|---|---|
| [docs/16](16_dil_ablasyon_protokolu.md) | ablasyon protokolü — soruyu ölçülebilir hâle getirir |
| [docs/19](19_task15_deney_tasarimi_dondurma.md) | **dondurulmuş deney tasarımı** — kollar, kapılar, ölçütler |
| [docs/20](20_task15_kavram_altin_normalizasyon_protokolu.md) | kanonik altın normalizasyon protokolü |
| [docs/22](22_task15_kavram_normalizasyon_kilavuzu_taslak.md) | span → kavram normalizasyon kılavuzu |
| [docs/24](24_task15_ucdan_uca_elestirel_denetim.md) | bağımsız uçtan uca denetim |
| [docs/25](25_task15_bolunme_kirlenme_denetimi.md) | bölünme kirlenmesi denetimi |
| [docs/kararlar.md](kararlar.md) | **karar defteri** — koddaki `D<n>` atıflarının karşılığı |
| [reports/…_sozluk_onarimi_raporu](../reports/task15_sozluk_onarimi_raporu.md) | sözlük onarımı kapanış raporu |
| [reports/…_ceviri_dev_raporu](../reports/task15_ceviri_dev_raporu.md) | `dev` çeviri koşuları |
| [reports/…_medgemma_kol_dusurme](../reports/task15_medgemma_kol_dusurme.md) | EN-tıbbi kolunun düşürülme kaydı |
| [reports/…_ikincil_model_raporu](../reports/task15_ikincil_model_raporu.md) | **ikincil model doğrulaması** — üç modelin elenme kaydı ve gerekçesi |
