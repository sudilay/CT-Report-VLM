# İşaretleme Kılavuzu — Radyoloji Raporlarından Bulgu Çıkarımı

**Sürüm:** kilavuz-1.0 · 2026-08-27

> Bu kılavuz **bir yazılımı tarif etmez.** Radyoloji raporlarında neyin bulgu, neyin
> anatomi sayıldığını ve bir ifadenin ne anlama geldiğini tanımlar. Kuralların
> tamamı **dış kaynaklardan** alınmıştır (bölüm 8). Yazılımı hiç görmemiş biri bu
> kılavuzu okuyup işaretleme yapabilmelidir.

---

## 1. İki ayrı iş var

| Dosya | Ne yapacaksın | Ne ölçüyor |
|---|---|---|
| **A · Kör listeleme** | Cümleyi okuyup **içinde ne varsa yazacaksın** | Sistemin **kaçırdığı** şeyleri |
| **B · Yargılama** | Sana gösterilen adayın **doğru olup olmadığını** söyleyeceksin | Sistemin **yanlış bulduğu** şeyleri |

**A'yı önce yap.** B'yi yaptıktan sonra A'ya dönersen, gördüğün adaylar aklını
yönlendirir ve gerçekte kaçırılanı fark edemezsin.

⚠ **A dosyasında sana hiçbir aday gösterilmiyor. Bu kasıtlı.**

---

## 2. A · Kör listeleme nasıl doldurulur

Her satırda bir cümle var. İki kolon dolduracaksın:

| Kolon | Ne yazılır |
|---|---|
| `bulgular` | Cümlede geçen **radyolojik gözlemler**, virgülle ayrılmış |
| `anatomiler` | Cümlede geçen **anatomik yapılar**, virgülle ayrılmış |

**Metinde geçtiği hâliyle yaz.** Yorumlama, çevirme, standartlaştırma yapma.

> *"No pleural effusion or thickening was observed in the right lung."*
>
> `bulgular` → `effusion, thickening`
> `anatomiler` → `pleural, lung`

**Önemli:** Bulgunun **var olup olmaması fark etmez.** Yukarıdaki cümlede efüzyon
**yok** ama yine de listeye yazılır — çünkü metinde **geçiyor**. Var/yok ayrımı B
dosyasının işi.

Cümlede hiçbir şey yoksa kolonu **boş bırak** — "yok" yazma.

---

## 3. B · Yargılama nasıl doldurulur

Her satırda bir **aday** var: cümle + sistemin bulduğunu iddia ettiği bir ifade.
Dört kolon dolduracaksın.

### `dogru_varlik_mi` → `E` / `H`

Gösterilen ifade gerçekten bir **bulgu veya anatomik yapı** mı?

- `E` — evet, bu bir bulgu/anatomi
- `H` — hayır, bu alakasız bir kelime

⚠ **Listede kasıtlı olarak yanlış adaylar var.** Hepsine `E` demeyi bekleme. Bu,
işaretlemenin dikkatli yapıldığını denetlemek için konuldu.

### `dogru_kavram_mi` → `E` / `H`

Yalnızca üsttekine `E` dediysen doldur. Sisteme atanan **kavram adı** uygun mu?

> Aday: `"nodules"` · kavram: `nodule` → `E`
> Aday: `"nodules"` · kavram: `mass` → `H`

### `kesinlik_ne_olmali` → `mevcut` / `yok` / `belirsiz`

Cümleye göre bu bulgu **var mı, yok mu, belirsiz mi?** Bölüm 4'teki tabloya bak.

### `zaman_ne_olmali` → `guncel` / `onceki` / `bilinmiyor`

Bu bulgu **bu tetkike mi** ait, **önceki bir tetkike mi?**

---

## 4. Kesinlik tablosu — bu tablo bağlayıcıdır

Kaynak: alan sözlüğü belgesi §12.2 eşleme tablosu.

| İfade türü | Örnek | Kesinlik |
|---|---|---|
| Açık olumsuzlama | *"izlenmemiştir"*, *"saptanmadı"*, *"was not observed"*, *"no … was detected"* | **yok** |
| Güçlü olumsuzlama | *"düşündürecek görünüm saptanmadı"*, *"lehine bulgu izlenmemiştir"* | **yok** |
| **Dışlanamaz** | *"malignite dışlanamaz"*, *"cannot be excluded"* | ⚠ **belirsiz** |
| Ayırt edilemedi | *"net olarak karakterize edilemedi"* | **belirsiz** |
| Şüpheli | *"şüpheli görünüm"*, *"suspicious"* | **mevcut** |
| Olası / muhtemel | *"olasılıkla"*, *"muhtemel"* | **mevcut** |
| Uyumlu | *"ile uyumludur"*, *"compatible with"* | **mevcut** |
| Lehine | *"lehine değerlendirilmiştir"*, *"in favor of"* | **mevcut** |
| Düz beyan | *"nodül izlenmektedir"* | **mevcut** |

### ⚠ En kritik kural — anatomi olumsuzlanmaz

**Bir bulgu bir YERDE yoksa, o YER hâlâ mevcuttur.** Olumsuzlanan bulgudur,
bulgunun arandığı yer değil.

> *"**No** mass was observed **in both lungs**."*
> `mass` → **yok** · `lungs` → **mevcut**   ← akciğerler yerinde duruyor

> *"**No** pathologically enlarged lymph nodes were detected **in the mediastinum**."*
> `enlarged lymph node` → **yok** · `mediastinum` → **mevcut**

Ölçüt basit: **cümle o yapının yokluğunu mu söylüyor, yoksa orada bir şey
bulunmadığını mı?** İkincisi ise yapı `mevcut`tur.

**İstisna — yapı gerçekten yoksa `yok` yazılır:**

> *"The right breast was **not observed** secondary to the **operation**."*
> `breast` → **yok**   ← meme ameliyatla alınmış, gerçekten orada değil

> *"**Status post** left nephrectomy."*
> `kidney` → **yok**

Ayırt etme yolu: cümlede o yapıda **aranan bir bulgu** var mı? Varsa yer
`mevcut`tur. Yoksa ve yapının kendisi kayıpsa `yok`tur.

⚠ Bu kural **belirsizlik** için de geçerlidir:
*"A nodule that cannot be characterized **in the liver**"* → `liver` **mevcut**.

### ⚠ Üç kritik kural

**Kural 1 — "dışlanamaz" `belirsiz`dir, `yok` değildir.**
Cümlede *"değil / not"* geçiyor diye `yok` deme. *"Malignite dışlanamaz"* demek
*"malignite olabilir"* demektir.

**Kural 2 — Teknik kısıtlılık kesinliği hiç değiştirmez.**
*"Kalp optimal değerlendirilemedi"* → kalp **mevcut**. `yok` değil, `belirsiz` de
değil.

Sebep: bu cümle kalbin *varlığı* hakkında bir şey söylemiyor, **görüntünün
kalitesi** hakkında söylüyor. İkisi ayrı eksen. Teknik çekince ayrı bir alanda
(`technical_limitation`) tutulur. Kesinliğe katlanırsa *"bulgu belirsiz"* ile
*"görüntü yetersiz"* ayırt edilemez hâle gelir ve ikisi de geri kazanılamaz.

⚠ *"dışlanamaz"* ile karıştırma: o **bulgu** hakkındadır → `belirsiz`.

**Kural 3 — Öneri ifadesi kesinliği değiştirmez.**
*"Klinik korelasyon önerilir"*, *"PET/BT önerilir"* bir **öneridir**. Yanındaki
bulgunun var/yok durumunu **etkilemez**.

### Kapsam nerede biter

Olumsuzlama **noktalı virgüle, "ancak/however/but"a, "dışında/apart from"a kadar**
sürer.

> *"No consolidation; **however**, newly developed effusion is observed."*
> → konsolidasyon **yok** · efüzyon **mevcut**

Bir olumsuzlama **birden çok bulguyu** kapsayabilir:

> *"No pleural effusion **or** thickening was observed."*
> → **ikisi de yok**

---

## 5. Zaman tablosu

| Durum | Örnek | Zaman |
|---|---|---|
| Bu tetkikte gözlenmiş | *"nodül izlenmektedir"* | **guncel** |
| Yalnızca önceki tetkikte | *"önceki tetkikte 18 mm ölçülmüştü"* | **onceki** |
| Kıyas referansı, bulgu şimdiki | *"önceki tetkike göre büyümüş"* | **guncel** |
| Ayırt edilemiyor | — | **bilinmiyor** |

⚠ *"Önceki tetkike göre…"* ifadesi bulguyu **önceki** yapmaz. Bulgu **şimdi vardır**;
önceki tetkik yalnızca **karşılaştırma noktasıdır**.

---

## 6. Sınır durumlar

| Durum | Ne yapılır |
|---|---|
| `nonspecific nodule` | Nodül **mevcut**. `non-` öneki burada olumsuzlama değil, niteleyicidir |
| `non-calcified nodule` | Nodül **mevcut**, kalsifikasyon **yok** |
| Aynı bulgu iki kez geçiyor | **İkisini de** yaz (A) / ayrı ayrı yargıla (B) |
| Bulgu mu anatomi mi belirsiz | Vücutta bir **yapı** ise anatomi; o yapıda **görülen bir şey** ise bulgu |
| Kısaltma (`LAP`, `GGO`, `CTO`) | Bildiğin bir kısaltmaysa yaz; emin değilsen `notlar`a yaz |
| Normallik beyanı (*"trakea açık"*) | Trakea **anatomi** olarak yazılır ve **mevcuttur**. Buradan "patoloji yok" **çıkarma** |
| Cihaz (kateter, stent) | Anatomiye değil, ayrı yaz ve `notlar`a "cihaz" düş |
| Cümle anlaşılmıyor | Boş bırak, `notlar`a yaz. **Tahmin etme** |

---

## 7. Emin olamadığında

**Boş bırak ve `notlar`a yaz.** Tahmin edilmiş bir işaretleme, boş bir işaretlemeden
daha zararlıdır — boş satırlar hesaptan çıkarılır, yanlış satırlar sonucu bozar.

---

## 8. Bu kılavuzdaki kuralların kaynağı

| Kural | Kaynak |
|---|---|
| Gözlem / anatomi ayrımı | **RadGraph-XL** — ANAT/OBS şeması, ACL Findings 2024 |
| `mevcut / yok / belirsiz` | **Alan sözlüğü belgesi §12.2** eşleme tablosu |
| *"dışlanamaz"* → belirsiz | Belge **Kritik kural 1** |
| Güçlü olumsuzlama da `yok` | Belge **Kritik kural 2** |
| Öneri kesinliği değiştirmez | Belge **Kritik kural 3** |
| Etiket kapsamı | **RadTr** 9 etiketli şema, Diagn Interv Radiol 2025 |
| Zaman sınıfları | Belge `growth_status` / `temporality` |

Hiçbir kural bu projenin kodundan türetilmemiştir.

---

## 9. İşi bitirdiğinde

1. İki dosyayı da kaydet (CSV, UTF-8).
2. Kaç satırı boş bıraktığını söyle — rapora yazılacak.
3. Zorlandığın yerleri belirt — kılavuz eksikse **kılavuz düzeltilir**, sonuç değil.

**Uyuşmazlık çıkarsa** kazanan seçilmez; kılavuz netleştirilir ve işaretleme
yenilenir. Bu, puanlamadan **önce** yapılır.
