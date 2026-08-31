# TASK-15 · Dil Ablasyonu — Çalışma Planı ve İlerleme

**Soru:** Türkçe veri seti gerekli mi?
**Çıktı:** Bir sayı değil, bir **karar** — Faz 3 altın standart etiketlemesi
hangi dilde yapılacak.

> Yaşayan kayıt. İş bitince kutu işaretlenir ve **ne görüldüğü** yazılır —
> yalnızca "yapıldı" değil, çıkan sayı ve varsa sürpriz.
> Yöntem gerekçeleri: [`16_dil_ablasyon_protokolu.md`](16_dil_ablasyon_protokolu.md)

**Durum:** 0/6 adım · başlamaya hazır

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

- [ ] `test`in 56 belgesini çeviriye gidecek biçimde ayrı dosyaya çıkar
- [ ] Belge kimliği korunur — çeviri sonrası hizalama buna dayanıyor
- [ ] ⚠ Altın etiketler **çeviri paketine konmaz**

**Betik önerisi:** `scripts/24_ceviri_paketi.py` → `data/processed/ablasyon_test_tr.jsonl`

### ⬜ 2 · İki yoldan İngilizce üret

- [ ] **EN-çeviri** — genel amaçlı çeviri
- [ ] **EN-tıbbi** — tıbbi metinde eğitilmiş model
- [ ] Her ikisinde de belge kimliği ve belge sırası korunur

**Neden iki yol:** çeviriyi de bir değişken yapar ve kaybın **çeviriden mi
dilden mi** geldiğini ayrıştırır. Tek çeviriyle bu ayrım yapılamaz.

### ⬜ 3 · Üç kolu koş

| kol | girdi | sözlük |
|---|---|---|
| **TR** | Türkçe asıl | `tr-1.0` + `tr-ipucu-1.0` |
| **EN-çeviri** | genel çeviri | mevcut İngilizce sözlük (`bulgu-1.1` / `anat-1.1` / `ipucu-1.0`) |
| **EN-tıbbi** | tıbbi model çevirisi | aynı İngilizce sözlük |

- [ ] Üçü de **aynı** altın veriye karşı puanlanır
- [ ] Üçünde de **aynı** ölçütler ve eşikler

### ⬜ 4 · Puanla — belge düzeyinde

Span düzeyi **kullanılamaz**: altın etiketler Türkçe karakter konumlarına bağlı,
çeviriyle anlamsızlaşır. Bunun yerine belge düzeyinde kavram kümesi:

```
altın(belge)    = { (kavram, kesinlik), ... }
TR-çıktı(belge) = { (kavram, kesinlik), ... }
EN-çıktı(belge) = { (kavram, kesinlik), ... }
```

- [ ] **A1** kavram çıkarımı — belge düzeyinde P / R / F1
- [ ] **A2** kesinlik ataması — eşleşen kavramlarda makro-F1
- [ ] **A3** eksen kırılımı — `present` / `absent` / `uncertain` **ayrı**

⚠ **A3 zorunlu.** Tek ortalama, çevirinin nerede kırıldığını gizler.
Beklenen: çeviri en çok **belirsizliği** bozar — sınanabilir bir tahmin.

⚠ Bedeli açıkça yazılır: **span sınırı doğruluğu ölçülmez.**

### ⬜ 5 · Ek kontrol — geri çeviri

- [ ] TR → EN → TR yapıp çıkarımı tekrar koş
- [ ] İki çeviriden geçmiş metin, bir çeviriden geçmişten **daha kötü** olmalı

Olmuyorsa ölçüm düzeneğinde sorun var demektir. Bu, çeviri kaybının **üst
sınırını** verir.

### ⬜ 6 · Raporla ve **kararı ver**

- [ ] `reports/dil_ablasyon_raporu.md`
- [ ] Karar tablosuna göre Faz 3 dil kararı

---

## Karar tablosu — **ölçümden önce yazıldı**

| bulgu | karar |
|---|---|
| TR ≈ EN (fark küçük, eksenler tutarlı) | İngilizce devam; Türkçe veri **kritik değil**, gerekçesi kayıtlı |
| TR belirgin **üstün** | Türkçe etiketlemeye geçilir; CT-RATE Türkçe aslı öncelikli hedef |
| TR belirgin **düşük** ama sebep desen zayıflığı | Uzman onaylı sözlükle **tekrar** ölçülür; karar ertelenir |
| Eksenler **çelişiyor** | Tek karar verilmez; eksen bazlı rapor edilir |

⚠ Üçüncü satır kritik: Türkçe tarafın düşük çıkması tek başına *"Türkçe veri
gereksiz"* demek **değildir**. Yüzeyler uzman onayından geçmediği sürece
düşüklüğün dilden mi araçtan mı geldiği ayrılamaz.

---

## ⛔ Ölçmeyeceğimiz şeyler — sebepleriyle

### Zaman ekseni

RadTr `train+dev`'de *önceki tetkik* **4 anma**, *stabil* **1**. Kaynak tek
zamanlı sentetik raporlardan oluşuyor. **Bu eksende hiçbir sayı
raporlanmayacaktır.** İngilizce `test-v2`de K7 zaten eşiği geçememişti.

### "Bir model yorumlasın" tasarımı

Bir modele hem Türkçesini hem İngilizcesini verip *"yorumla"* demek **ölçüm
değildir**: modelin yanlılığı sonuca karışır, tekrarlanabilir değildir,
karşılaştırılabilir sayı üretmez.

Model yorumu **atılmıyor** — sonuç sayıları çıktıktan *sonra*, ayrışan
belgelerde hata taksonomisi kurmak ve hipotez üretmek için kullanılır.
Yalnızca **sonuç hanesine yazılmaz**.

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
