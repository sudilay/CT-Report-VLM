# TASK-15 · Dil Ablasyonu — Çalışma Planı ve İlerleme

**Soru:** Türkçe veri seti gerekli mi?
**Çıktı:** Bir sayı değil, bir **karar** — Faz 3 altın standart etiketlemesi
hangi dilde yapılacak.

> Yaşayan kayıt. İş bitince kutu işaretlenir ve **ne görüldüğü** yazılır —
> yalnızca "yapıldı" değil, çıkan sayı ve varsa sürpriz.
> Yöntem gerekçeleri: [`16_dil_ablasyon_protokolu.md`](16_dil_ablasyon_protokolu.md)
> Model, değerlendirme ve karar dondurması:
> [`19_task15_deney_tasarimi_dondurma.md`](19_task15_deney_tasarimi_dondurma.md)

**Durum:** Altyapı hazır · **çeviri koşusu başlıyor** · `test` açılmadı.
Kod, `dev` paketleri (v2), çeviri adaptörleri ve puanlayıcı yazıldı; 291 test
geçiyor. Kavram altını (Adım 4'ün girdisi) **bilinçli olarak sona bırakıldı** —
önce TR/EN farkını `dev` üzerinde görüyoruz.

Kanonik kavram altını protokolü:
[`20_task15_kavram_altin_normalizasyon_protokolu.md`](20_task15_kavram_altin_normalizasyon_protokolu.md)

---

## Kim ne yapıyor

Bu tabloya bakarak "sırada bende ne var" sorusunu cevaplayabilirsin.

| # | iş | kim | durum |
|---|---|---|---|
| 0 | Kod, paketler, adaptörler, testler | otomasyon | ✅ bitti |
| 1 | Google Cloud: proje · faturalandırma · **bütçe uyarısı** · Translation API | **yürütücü** | ✅ API açıldı |
| 2 | `gcloud auth application-default login` | **yürütücü** | ⬜ |
| 3 | HF: MedGemma koşullarını kabul + `huggingface-cli login` | **yürütücü** | ⬜ |
| 4 | Bağımlılık kurulumu (`requirements-ceviri.txt` + torch) | **yürütücü** (tek komut) | ⬜ |
| 5 | EN-ucuz koşusu (Opus-MT, CPU, bu makine) | yürütücü çalıştırır · otomasyon okur | ⬜ |
| 6 | EN-genel koşusu (Google) | yürütücü çalıştırır · otomasyon okur | ⬜ |
| 7 | Çeviri kalite kontrolü, revizyon sabitleme | otomasyon | ⬜ |
| 8 | EN-tıbbi koşusu (MedGemma, **uzak 8 GB makine**) | yürütücü çalıştırır · otomasyon okur | ⬜ |
| 9 | Sözlük sistemini üç girdide koşma, `dev` TR/EN farkı | otomasyon | ⬜ |
| 10 | İkincil model seçimi (Qwen vs Aya, `dev`) | otomasyon yazar · yürütücü koşar | ⬜ |
| 11 | **İKİ sözlüğün onarımı** (çeviri bitti, boşluk ölçüldü, aday listesi hazır) | otomasyon | 🔄 [`docs/26`](26_task15_sozluk_onarimi_devir.md) |
| 12 | Kavram altını: pilot → B → A → **radyolog** | otomasyon + **radyolog** | ⬜ ertelendi |
| 13 | `test` paketleme ve tek koşu | yürütücü onaylar · otomasyon yazar | ⬜ kilitli |

**Neden otomasyon çalıştırmıyor:** kimlik doğrulama (gcloud/HF) ve uzak GPU makinesi
senin oturumunda. Komutları ben yazıyorum, çıktıyı birlikte okuyoruz.

⛔ 12 ve 13 diğer her şey bitmeden açılmaz. Adım 9'da `dev` üzerinde görülecek
TR/EN farkı **geliştirme gözlemidir** (D31), ablasyonun cevabı değildir.

### 2026-09-01 · İlk uygulama dilimi

`src/radyovlm/evaluation/task15.py` içinde sağlayıcıdan bağımsız altyapı kuruldu:

- çeviri ve ikincil model adaptör sözleşmeleri,
- yalnız `train/dev` kabul eden split kapısı,
- aynı kaynak geçişinden altınsız çeviri ve tahminsiz kör normalizasyon paketi,
- doğrudan ayrıştırılan kapalı JSON ve 144 kavramlık envanter doğrulaması,
- span→`concept_ids` A/B işaretleme şeması, bağımsız hash kilidi ve tüm listeyi
  radyolog kuyruğuna taşıyan uzlaştırma,
- belge düzeyi A1/A2/A3 puanları ve yönü sabit `EN−TR` olan 10.000 eşleştirilmiş
  bootstrap.

Ölçülenler: dondurulmuş envanter **144** kavramdır; tam SHA-256
`b5e2058a04b9a0870d3329cbbc5a2dc25f1f25c41a2e55e34f0cd397179fc8dd`.
Yeni 16 sentetik/yapısal TASK-15 testiyle birlikte depo testi **269/269** geçti
(1 mevcut uyarı, son koşu 98,83 sn). RadTr'nin birleşik JSONL dosyası, `test` belgeleri,
dış servisler ve model depoları bu dilimde hiç açılmadı; model indirilmedi,
çeviri üretilmedi ve kalıcı deney çıktısı yazılmadı.

Uygulama denetimi iki riski kod üretilirken yakaladı: ilk A/B kilidi iki
işaretleyicinin aynı satırları atlamasını görünür kılmıyordu ve hash'li çıktı
mevcut dosyanın üzerine yazılabiliyordu. A/B çıktısı artık kör paketin tam
anahtar kümesine ve kaynak metin hash'ine bağlıdır; kilitli hedef varsa bütün
yazıcılar durur. Çeviri paketi de fazla alanı (ör. altın etiket) reddeder.

Bu ilk dilimin sonunda henüz tamamlanmayanlar: gerçek `train/dev` paketleri,
normalizasyon kılavuzu ve pilot, Google/MedGemma/TranslateGemma bağlantıları,
Qwen/Aya dev seçimi, prompt ve çalışma ortamı dondurmasıydı. Bu yüzden 1.
adımın kutusu işaretlenmedi ve kesin test komutu bilerek yazılmadı.

### 2026-09-01 · Gerçek `dev` paketleri ve kılavuz taslağı

Yalnız `data/external/radtr/dev.json` okunarak 132 kaynak belgeden 46 toraks
belgesi çıkarıldı; `test.json` ve birleşik RadTr JSONL açılmadı. Aynı geçişte
46 kayıtlık altınsız çeviri paketi ve **1.490** kayıtlık tahminsiz kör
normalizasyon paketi üretildi. 46/46 belge hizalı, 1.490/1.490 span kimliği
benzersiz, bağlamında bulunmayan span 0, yasak alan sızıntısı 0 ve iki paket
hash'i manifestle uyumludur. Ayrıntılı alan sözleşmeleri, komutlar, sayımlar ve
hash'ler `docs/21_task15_altyapi_ve_dev_paketleri.md` içindedir.

Kapalı envanter için `configs/task15_kavram_katalogu.yaml` oluşturuldu:
56 anatomi + 56 gözlem + 26 niteleyici + 6 cihaz = **144** kimlik; kaynak
envanterle birebir ve eksik/fazla kimlik yok. Katalog regex, frekans veya
span-başına sistem eşleşmesi taşımaz. Normalizasyon kuralları
`docs/22_task15_kavram_normalizasyon_kilavuzu_taslak.md` içinde yazıldı. İki
dosya da **taslaktır**, uzman onayı yoktur ve test için dondurulmamıştır.

Güvenlik sıkılaştırması: `scripts/16_extract_radtr_thorax.py` artık `--bolum`
argümanını zorunlu ister; argümansız çağrı bütün bölümleri varsayılan olarak
açamaz. TASK-15 paket üretimi yalnız `train/dev` kabul eder ve mevcut kilitli
çıktının üzerine yazmaz.

### 2026-09-01 · İlk gerçek çeviriler koşuldu (`dev`, 46 belge)

**Ortam:** gcloud kullanıcı-yerel kuruldu, ADC ile giriş yapıldı (organizasyon
politikası servis hesabı anahtarını yasaklıyor). Proje
`project-f2268a84-fe63-4000-bae` · Translation API açık · faturalandırma bağlı.
Harcanan 104 bin karakter (iki koşu), aylık ücretsiz katmanın %21'i.

#### EN-genel (Google NMT) — ✅ tamam

46/46 belge. `outputs/task15/ceviri_dev/en_genel_dev.jsonl`, provenance yazıldı.
Kalite iyi; ölçülen tek gerçek içerik kaybı `_10_124` belgesinde: iki Türkçe
cümle (*"birbirine komşu 3-4 adet lenf nodu dikkati çekmiştir"* ve *"Sağda 4 ve
5."*) İngilizce çıktıda **hiç yok**. 46'da 1 — ama ablasyonun ölçmek istediği
kaybın tam örneği.

#### ⚠ Google NMT deterministik değil (D53)

Provenance yazımında bir yol hatası ilk koşuyu yarıda bıraktı (çeviri tamamdı).
Düzeltip yeniden koşunca **46 belgenin 5'i (%11) farklı çıktı** — aynı girdi,
aynı ayar, dakikalar arayla. Çoğu sözcük seçimi (`taken`→`obtained`,
`EXAMINATION`→`SCANNING`) ama bir vakada anatomik niteleyici öbek değiştirdi
(`abdominal sections … lobulated` → `cross-sections … lobulated in the abdomen`).

Sonucu: `test` çevirisi **yeniden koşularak doğrulanamaz**; artefaktın kendisi
kayıttır. Kanıt `outputs/task15/ceviri_dev/determinizm_kanit/`.

#### EN-ucuz (Opus-MT) — ❌ karantinada

Belge düzeyinde çöküyor: ortalama çıktı 478 karakter (Google 1278), yani
içeriğin %62'si düşüyor; Türkçe kalıntı ve uydurma üretiyor. Teşhis doğrulandı —
Marian/OPUS bir **cümle** çevirmeni. Tek cümlede kusursuz
(*"Sağ hemitoraksta plevral sıvı saptanmadı."* → *"No pleural fluid was detected
in the right hemithorax."*), belgede dağılıyor.

`outputs/task15/ceviri_dev/KARANTINA_opus_belge_duzeyi/`. Kolun geleceği
`docs/19` §4/1'in (parçalama yasağı) ucuz kol için gevşetilip gevşetilmeyeceğine
bağlı — karar bekliyor.

#### Denetimde bulunan kendi hatam

`sayi_korunumu_ihlalleri` Türkçe→İngilizce kıyasta yanlış alarm üretiyordu:
Türkçe eki birime yapıştırıyor (`1 cm'yi`, `5 mmlik`) ve `cm` bunu görmüyor.
Google'ın "6 ihlali" gerçekte **1**'di. `birim_kontrolu` parametresi eklendi;
birim karşılaştırması yalnız aynı dilde (MedGemma EN→EN post-editi) anlamlı.
Teste bağlandı. Toplam **292/292**.

#### Uzak makine paketi

`outputs/task15/UZAK_MAKINE_medgemma/` (121 KB) — kod, girdi ve `OKU_BENI.md`
ile adım adım kurulum. MedGemma 8 GB GPU makinesinde koşacak.

### 2026-09-01 · Çeviri hattı yazıldı (model indirilmedi)

**Kollar donduruldu (D52):** EN-genel Google NMT · EN-tıbbi Google → MedGemma
1.5 4B · EN-ucuz Opus-MT tc-big (CC-BY-4.0). NLLB CC-BY-NC olduğu için
çıkarıldı. Gerekçe: CT-RATE'in İngilizcesi Google Translate ile üretildi ve
İngilizce sözlüğümüz o metnin üzerinde geliştirildi; başka bir çevirmen EN
kolunu haksız yere kötü gösterir. Ayrıntı `docs/19` "Neden Google".

**Yazılanlar:**

- `src/radyovlm/evaluation/translation.py` · üç adaptör + `run_post_edit`.
  Ağır bağımlılıklar tembel yükleniyor; modül torch olmadan import edilebiliyor.
- **Sayı/birim korunum denetimi** (`sayi_korunumu_ihlalleri`) — `docs/24` §7'nin
  istediği otomatik kapı. Post-edit bir ölçümü değiştirirse koşu durur.
  Ondalık ayırıcı normalize ediliyor (`1,5 cm` = `1.5 cm`), yanlış alarm yok.
  Negasyon/belirsizlik korunumu mekanik doğrulanamaz; kör insan kontrolüne kalır.
- `scripts/28_task15_ceviri.py` · kilitli çıktı + provenance (model, revizyon,
  decoding, istem hash'i, girdi/çıktı SHA-256, zaman). Sağlayıcı revizyon
  vermezse *"saglayici tarafindan aciklanmadi"* yazılır, uydurulmaz.
- `tests/test_ceviri.py` · 13 test, sahte adaptörlerle, model indirmeden.
- `requirements-ceviri.txt` · ana requirements'a bilerek eklenmedi.

**Uygulanan tasarım kuralları:** çeviri birimi belgenin tamamı — model penceresi
yetmezse görünür hata, sessiz kırpma yok (§4/1). `en-tıbbi`nin girdisi Türkçe
paket değil **`en-genel` çıktısı**; iki EN kolu arasındaki tek değişken post-edit.
Örnekleme kapalı, decoding sabit (§4/5).

**Donanım sırası:** EN-genel yalnız ağ ister, EN-ucuz CPU'da koşar → **ikisi de
bu makinede** çalıştırılabilir. Yalnız EN-tıbbi 8 GB'lık uzak makineyi bekliyor.

### 2026-09-01 · İki denetim, iki hata, düzeltme dilimi

**Bulunan iki hata** (bağımsız, ikisi de testten önce yakalandı):

1. **Span ofseti** (`docs/24`, Codex): indeksler `-1` kaydırılmıştı; doğrusu
   0-tabanlı kapsayıcı. Altı ayrı testle doğrulandı, gerekçe `docs/25` §10'da.
2. **Bölünme kirlenmesi** (`docs/25`, Opus): RadTr `train.json`, `dev.json` ve
   `test.json` belgelerinin tamamını içeriyor. Bölüm kimliği dosya adından
   üretildiği için 56 test toraks belgesi geliştirme havuzuna sızmıştı.
   **Ölçülen hasar sıfıra yakın:** 144 yüzeyin 0'ı, 28 ipucunun 1'i (`stabil`,
   zaten düşürülmüş K7 ekseninde) yalnız test belgelerine dayanıyor. Test
   üzerinde hiçbir skor hesaplanmadı; sözlük yeniden türetilmiyor.

**Uygulanan düzeltmeler:**

- `scripts/26_bolunme_denetimi.py` · içerik hash'iyle bölünme denetimi ve
  `--yaz-harita` ile `icerik SHA-256 -> gerçek bölüm` haritası (1.051 belge:
  train 744 · dev 132 · test 175). Harita yalnız hash taşır, metin taşımaz.
- `scripts/16_extract_radtr_thorax.py` · bölüm artık haritadan okunuyor;
  `--bolum test` ve `--bolum all` kaldırıldı, yerine `gelistirme` (train+dev)
  geldi. Ofset 0-tabanlı kapsayıcı. Belge kimliği `{doc_key}#{hash8}` —
  `doc_key` benzersiz değil (iki çakışma). Üzerine yazma kapısı koşulsuz.
- `scripts/27_task15_guc_analizi.py` · eksen bazlı GA genişliği ölçümü.
- `task15.py` · tekrarlı `(concept_id, assertion)` reddi; `score_assertions`
  kapalı assertion doğrulaması; bootstrap taban tekilliği ve **tanımsız
  iterasyon politikası** (`nan` = atla ve say, %5 üstü ise dur).
- `tests/test_task15.py` · 7 yeni test; ofset semantik çapası ve bölünme
  çakışması artık **gerçek veriye karşı** koşuyor. Toplam **278/278** geçiyor.

**Ölçülenler:** temiz geliştirme korpusu 429 değil **269 belge** · 8.648 varlık.
`dev` paketleri v2: 46 çeviri belgesi + 1.490 kör span, sayımlar aynı, span
metinleri düzeldi (*"plevral sıvı"* → *"sıvı saptanmadı."*).

**Güç ölçümü (`scripts/27`):** GA yarı genişliği A1 0,022 · `present` 0,031 ·
`absent` 0,074 · `uncertain` 0,065. `absent` n=150'de bile 0,048 — yeniden
bölmek çözmüyor, taban oran düşük. **RadTr bölünmesi korunuyor;** karar
eksenleri A1 + `present` olmalı (D51, onay bekliyor).

**Karantina:** `-1` ofsetiyle üretilen her şey
`outputs/task15/KARANTINA_INVALID_OFFSET_MINUS1/` altında korunuyor — `dev`
paketleri, 150-span pilot ve B kilidi. Silinmedi; B yeniden işaretlenecek.

### 2026-09-01 · Kör `dev` pilotu ve bağımsız B ön-işaretlemesi

Kullanıcı onayıyla yalnız RadTr etiketi, sabit tohum `20260901` ve belge başına
en çok 5 span kullanılarak **150 spanlık** pilot üretildi. Metin, sözlük
eşleşmesi, çeviri veya sistem tahmini seçime girmedi. Kotalar tam karşılandı:
anatomi 40 · present 40 · absent 20 · uncertain 20 · differential 10 · teknik
8 · öneri 5 · semptom 7. Pilot 46 `dev` belgesinin tamamını kapsıyor; belge
başına 3–4 span içeriyor. Pilot SHA-256:
`9f8162860c98dfcd29b2ca31973321c4a70edd9f364587dfe5a0f5d67d787799`.

Bağımsız B işaretleyicisi yalnız kör pilotu, 144 kavramlık kataloğu ve kılavuz
0.1'i gördü; çeviri, sözlük/model tahmini ve diğer işaretleyici cevabı görmedi.
150/150 satır kilitlendi: **82 `mapped` · 54 `unmapped` · 14
`needs_adjudication`**. Geçerli kilit:
`outputs/task15/dev_pilot/private_B/pilot_B_codex_v2.jsonl`, SHA-256
`5284be3251548ff8f24a63c18ed5ff6d87bd04113f7d93cdbe26916a2c466847`.
Satır kararları A'nın bağımsızlığını korumak için genel günlüklere taşınmadı.

İlk kilit denetiminde doğrulayıcının kılavuzdaki not kuralını zorlamadığı
görüldü: 18 `mapped` satırın açıklama notu doluydu. Kavram ve durum kararları
değiştirilmeden sözleşme sıkılaştırıldı; eski kilit silinmedi, denetim izi
olarak tutuldu ve v2 açıkça geçerli sürüm yapıldı. V2'de tam kapsam, kaynak
alan değişmezliği, kapalı envanter, boş `mapped` notu ve gerekçeli diğer
durumlar %100 geçti. Tüm test koleksiyonu **271/271** geçti (1 mevcut uyarı,
99,21 sn).

Pilotun erken çekincesi: çok sayıda span cümle ortasında kesiliyor veya komşu
cümleden sözcük taşıyor. 14 uzlaştırma kaydının ana nedeni bu sınır sorunudur;
bağlamdan kavram uydurmak yerine görünür bırakıldı. PTE/trombüs, dispne,
hemotoraks, mukus impaksiyonu ve çekim tekniği gibi katalog dışı ifadeler de
`unmapped` bırakıldı; bunlar zorla yakın kavrama bağlanmadı. Bunun yeterli
ölçüm etkisi A tamamlanıp iki işaretleyici karşılaştırılmadan yorumlanmayacak.

Bağımsız A için yalnız izinli üç girdiyi ve durma koşullarını gösteren devir
notu `docs/23_task15_pilot_isaretleyici_a_devir.md` olarak yazıldı. Bu aşamada
model indirilmedi, dış servise veri gönderilmedi, çeviri yapılmadı ve RadTr
`test` açılmadı.

---

## 🔴 Kırmızı çizgi — en önemli kural

`test` bölümünün **56 belgesi bir kez açılır.** Sonucu görüp yüzey, ipucu,
kapsam mantığı veya kural değiştirilirse **bu sürüm iptal edilir**, yeni bir
sürüm çekilir ve raporda eski skorun geçersiz olduğu yazar (D26/5, D31).

Ayrışma çıkarsa yapılabilecek **tek** şey: şema farkı mı diye bakmak ve farkı
**raporlamak** — sistemi değiştirmek değil.

⚠ Geliştirme yapılacaksa `train` (327) ve `dev` (46) serbesttir. Bunlarla
sınırsız çalışılabilir; `test`e dokunulmaz.

---

## Hazır olanlar — TASK-14'ten devralındı

| bileşen | sürüm | SHA-256 |
|---|---|---|
| `configs/turkce_yuzeyler_taslak.yaml` | **tr-1.0** · 144 kavram | `b5e2058a04b9a087` |
| `configs/turkce_ipuclari_taslak.yaml` | **tr-ipucu-1.0** · 28 ipucu | `4f4efd3fbedf1445` |
| kapsam mantığı → `scripts/23_turkce_dev_olcum.py` | — | `34ece92a1344d04a` |
| `data/processed/radtr_toraks.jsonl` | — | `8ce5ef37cdfd4504` |

Dondurma kaydı: [`reports/turkce_dondurma.md`](../reports/turkce_dondurma.md)
Bölünme kaydı: [`reports/turkce_bolunme_dondurma.md`](../reports/turkce_bolunme_dondurma.md)

**Ölçüm kümesi:** RadTr `test` — 56 belge · 7.784 kelime · 1.817 varlık
(`present` 613 · `absent` 86 · `uncertain` 128)

---

## Adımlar

### ⬜ 1 · Çeviri paketini hazırla

- [x] Yalnız `train/dev` için kapalı 144 kavramlık span→kavram katalogu ve
  kılavuz 0.1 taslağı hazırlandı
- [x] 150 spanlık etiket-katmanlı kör `dev` pilotu, sistem tahmini kullanılmadan
  üretildi ve hash ile kilitlendi
- [x] Bağımsız B ön-işaretlemesi 150/150 tamamlandı ve geçerli v2 kilitlendi
- [ ] Bağımsız A, B dosyalarını görmeden aynı 150 spanı işaretler ve kilitler
- [ ] A/B karşılaştırmasından sonra uzman kılavuzu ve birleşik listenin tamamını
  onaylar
- [ ] Tek kontrollü test komutu aynı açılışta iki ayrı paket üretir:
  çeviri paketi ve kör kavram-normalizasyon paketi
- [ ] `test`in 56 belgesini çeviriye gidecek biçimde ayrı dosyaya çıkar
- [x] Belge kimliği korunur — `dev`de 46/46 iki pakette hizalı; çeviri sonrası hizalama buna dayanıyor
- [x] ⚠ Altın etiketler **çeviri paketine konmaz** — kapalı alan doğrulaması ve sızıntı testi geçti
- [x] Normalizasyon paketinde yalnız Türkçe cümle/span ve özgün RadTr etiketi
  bulunur; sözlük/model tahmini veya çeviri bulunmaz
- [x] İki paket ve manifest aynı anda SHA-256 ile kilitlenir — `dev` hash'leri manifestle doğrulandı

**Betik önerisi:** `scripts/24_ceviri_paketi.py` → `data/processed/ablasyon_test_tr.jsonl`

### ⬜ 2 · İki yoldan İngilizce üret

- [ ] **EN-genel** — Google Cloud Translation Advanced `general/nmt`,
  `tr → en`, glossary/özelleştirme yok
- [ ] **EN-tıbbi** — aynı Google çıktısına MedGemma 1.5 4B ile anlam-koruyucu
  tıbbi post-edit
- [ ] TranslateGemma 4B yalnız `train/dev` açık model kontrolü; ana test kolu değil
- [ ] Her ikisinde de belge kimliği ve belge sırası korunur

**Neden iki yol:** çeviriyi de bir değişken yapar ve kaybın **çeviriden mi
dilden mi** geldiğini ayrıştırır. Tek çeviriyle bu ayrım yapılamaz.

### ⬜ 3 · Üç girdiyi iki çıkarım sistemiyle koş

| girdi | dondurulmuş çıkarım | dev'de seçilip dondurulan model |
|---|---:|---:|
| **TR** · Türkçe asıl | ✅ birincil | ✅ ikincil |
| **EN-genel** · Google NMT | ✅ birincil | ✅ ikincil |
| **EN-tıbbi** · Google NMT → MedGemma | ✅ birincil | ✅ ikincil |

- [ ] Altı koşu da **aynı** altın veriye karşı puanlanır
- [ ] İkincil model yalnız `dev` üzerinde seçilir: Qwen3.5-4B ana aday ve Aya
  Expanse 8B zorunlu karşılaştırma; Qwen3-8B yalnız Qwen3.5-4B yapısal kapıyı
  geçemezse koşullu yedek
- [ ] Seçim; çalışabilirlik, %100 geçerli kapalı JSON, sıfır envanter dışı
  değer, A1/kesinlik doğruluğu, dil dengesi ve kaynak maliyeti sırasıyla yapılır
- [ ] Adayların tüm dev sonuçları saklanır; tek model testten önce dondurulur
- [ ] Seçilen model her dili ayrı görür; aynı model, İngilizce talimat, JSON
  şeması ve sabit decoding kullanılır
- [ ] Birincil dil kararı dondurulmuş sistemden, ikincil doğrulama seçilen modelden gelir

### ⬜ 4 · Puanla — belge düzeyinde

Span düzeyi **kullanılamaz**: altın etiketler Türkçe karakter konumlarına bağlı,
çeviriyle anlamsızlaşır. Bunun yerine belge düzeyinde kavram kümesi:

```
altın(belge)    = { (kavram, kesinlik), ... }
TR-çıktı(belge) = { (kavram, kesinlik), ... }
EN-çıktı(belge) = { (kavram, kesinlik), ... }
```

- [ ] **A1** kavram çıkarımı — Opus ve Codex'in kör bağımsız ön-işaretlemesi
  sonrası radyoloğun tamamını onayladığı kanonik altına karşı belge düzeyi P/R/F1
- [ ] **A2** kesinlik ataması — `(belge, kavram, kesinlik)` üçlüsünde makro-F1
- [ ] **A3** eksen kırılımı — `present` / `absent` / `uncertain` **ayrı**
- [ ] Fark `EN − TR`; 10.000 eşleştirilmiş belge bootstrap'ı ve %95 güven aralığı

⚠ RadTr'nin yerel etiketi kanonik `concept_id` vermez. Türkçe sözlük eşlemesi
altın kabul edilmez. Testte yeni kavram eklenmez; eşlenemeyen span `unmapped`
olarak raporlanır. Altın dosya kilitlenmeden test tahminleri/skorları açılmaz.

⚠ **A3 zorunlu.** Tek ortalama, çevirinin nerede kırıldığını gizler.
Beklenen: çeviri en çok **belirsizliği** bozar — sınanabilir bir tahmin.

⚠ Bedeli açıkça yazılır: **span sınırı doğruluğu ölçülmez.**

### ⬜ 5 · Ek kontrol — geri çeviri

- [ ] TR → EN → TR yapıp çıkarımı tekrar koş
- [ ] Kayıp kadar terminoloji normalizasyonu da raporlanır

Geri çeviri bir **stres kontrolüdür**, geçerlilik kapısı değildir. İki
çeviriden geçmiş metin daha iyi çıkabilir; böyle bir sonuç ölçümü iptal etmez,
standartlaşan ifadelerle açıklanır.

### ⬜ 6 · Raporla ve **kararı ver**

- [ ] `reports/dil_ablasyon_raporu.md`
- [ ] Karar tablosuna göre Faz 3 dil kararı

---

## Karar tablosu — **ölçümden önce donduruldu**

| bulgu | karar |
|---|---|
| EN, A1 + `present` + `absent` eksenlerinde TR'den **5 F1 puanından** fazla düşük değil; %95 GA destekliyor | İngilizce etiketleme savunulabilir |
| TR, A1 veya `present`/`absent` ekseninde **5 puandan fazla ve güvenilir** üstün | Türkçe etiketlemeye geçilir |
| TR belirgin **düşük** ama sebep desen zayıflığı | Uzman onaylı sözlükle **tekrar** ölçülür; karar ertelenir |
| Genel/tıbbi EN, dondurulmuş sistem/seçilen model veya eksenler **çelişiyor** | Tek karar verilmez; çevirmen, yöntem veya eksen bağımlılığı raporlanır |
| Güven aralığı 5 puanlık sınırı kesiyor | Kanıt yetersiz; tek dil kararı verilmez |

⚠ Üçüncü satır kritik: Türkçe tarafın düşük çıkması tek başına *"Türkçe veri
gereksiz"* demek **değildir**. Yüzeyler uzman onayından geçmediği sürece
düşüklüğün dilden mi araçtan mı geldiği ayrılamaz.

---

## ⛔ Ölçmeyeceğimiz şeyler — sebepleriyle

### Zaman ekseni

RadTr `train+dev`'de *önceki tetkik* **4 anma**, *stabil* **1**. Kaynak tek
zamanlı sentetik raporlardan oluşuyor. **Bu eksende hiçbir sayı
raporlanmayacaktır.** İngilizce `test-v2`de K7 zaten eşiği geçememişti.

### Yapılandırılmış model değerlendirmesi ile serbest yorum ayrımı

Dev protokolüyle seçilip dondurulan tek model, üç girdiyi **ayrı ayrı**, aynı
kapalı kavram envanteri ve JSON şemasıyla işler; bu ikincil ve sayısal
değerlendirmedir. Model sonucu tek başına dil kararını belirlemez.

Bir modele Türkçe ve İngilizce metni aynı anda verip serbestçe *"yorumla"*
demek sonuç ölçümü değildir. Bu kullanım yalnız sayılar çıktıktan sonra hata
taksonomisi ve hipotez üretimi içindir; skor hanesine yazılmaz.

---

## ⚠ Şema farkı — sonuç iki türlü raporlanacak

RadTr *"değerlendirme optimal yapılamamıştır"* ifadesini `Obs_Uncertain`
sayıyor. Bizim **D30**'umuz teknik çekinceyi ayrı eksende tutuyor.

`dev`de ölçüldü: altın `uncertain`ın **%51'i** bu türden.

**D30 korunuyor** (D43). Rapor **iki sayı** verir ve hangisinin hangi şemaya ait
olduğunu yazar. `dev`de fark şuydu: ham doğruluk %84,5 → şema farkı hariç %92,4.

---

## Bilinen sınırlar — rapora aynen geçecek

| sınır | etkisi |
|---|---|
| RadTr **sentetik** (radyolog yazımı, gerçek hasta değil) | Sonuç *"RadTr benzeri Türkçe metinlerde"* diye yazılır |
| **56 belge** | Güven aralığı geniş; tek nokta tahmini sunulmaz |
| **Hizalı çift yok** | Aynı raporun insan yazımı TR *ve* EN hâli yok; EN kolu makine çevirisi. Çeviri hatası ile dil etkisi **tam ayrılamaz** |
| Yüzeyler **uzman onaysız** | Düşüklük dilden mi araçtan mı ayrılamaz |
| Altın span'ların **%10,9'u** cümle sınırını aşıyor | Ölçüme tavan koyuyor |
| Türkçe kaynak **tek** | İkinci kaynak bulunursa genellenebilirlik artar |

> **CT-RATE Türkçe aslı elimize geçerse** ilk üç sınır birden kalkar: hizalı
> çift, gerçek hasta, binlerce belge. RadTr ablasyonu sorunun cevabını verir,
> CT-RATE Türkçesi cevabı **kesinleştirir**.

---

## Devralınan bulgular — Türkçe tarafta beklenecekler

TASK-14'te `dev` üzerinde ölçülenler (**geliştirme gözlemi**, D31):

| sınıf | destek | F1 |
|---|---|---|
| `present` | 450 | %90,4 |
| **`absent`** | 72 | **%90,3** (duyarlılık %97,2) |
| `uncertain` | 96 | %23,6 (şema farkı hariç %43,6) |

`test`te bunlardan **düşük** çıkması normaldir — `dev`de düzeltme yaptık,
`test`te yapmadık. Aradaki fark **iyimserlik payıdır** ve raporda ayrıca yazılır.

**Türkçeye özgü üç bulgu** (D41, D42, D43) — çeviri kolunu yorumlarken lazım:

1. **Yön ters** (D41) — Türkçede negasyon ipuçlarının %97'si cümle sonunda.
   İngilizceye çevrilen metinde bu **başa** kayacak; EN kolunda İngilizce
   ipuçları zaten ileri yönlü çalışıyor.
2. **Betimleyici kalıp** (D42) — *"kalp boyutları artmıştır"*. Çeviri bunu
   *"cardiomegaly"* yaparsa EN kolu **avantajlı** olur; yapmazsa dezavantajlı.
   ⚠ Bu, ablasyonun en ilginç yeri olabilir — çeviri kavramı **normalize
   ediyor** mu?
3. **Teknik çekince negasyondan büyük** (D43) — 961'e 843.
