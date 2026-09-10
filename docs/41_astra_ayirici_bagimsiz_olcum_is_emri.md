# İş Emri · Astra Bölüm Ayırıcısının Bağımsız Ölçümü

**Tarih:** 2026-09-08 · **İsteyen:** Claude · **Yürüten:** bağımsız ikinci agent
**Kapsam:** SUDE-VLM-14 Adım 0 · tek seferlik kapı

---

## 0. Bu neden bağımsız ölçüm

`docs/39_astra_veri_sozlesmesi.md` içindeki bütün sayılar **tek bir bölüm
ayırıcısıyla** üretildi ve o ayırıcı basit bir `re.split` idi. İç içe
başlıkları (`**Lung:** ... **Right Lung:** ...`) doğru ayırmıyor olabilir. Eğer
ayırıcı hatalıysa sözleşmenin **bütün sayıları** ve buna dayanan kapsam
listeleri hatalıdır.

Aynı hatayı iki kez yapmamak için ölçüm bağımsız tekrarlanacaktır.

**Bağımsızlık şartı:** ayırıcını **kendin yaz.** Aşağıdaki sayıları üreten kodu
arama, okuma veya yeniden kullanma. Yalnız kaynak dosyaya ve bu iş emrine bak.
Yöntemini kendin seç ve yazdığın yöntemi raporla.

---

## 1. Kaynak

```
astra_radiology_reports_with_labels_all.xlsx
```

Kullanılacak kolonlar: `Seri_Anahtari`, `Radyoloji_Raporu`.
**Etiket kolonlarını kullanma** (`Kanser_Etiketi_y`, `Censor_Time`,
`Pillar_Ensemble_Skoru`) — tek istisna madde 2.6.

Toplam 2.965 satır beklenir.

---

## 2. Ölçülecekler

### 2.1 Bölüm ayırıcı
Her rapor için `(başlık, içerik)` çiftleri üret. İç içe başlık varsa nasıl
çözdüğünü **açıkça yaz** (en yakın başlığa mı, hiyerarşik mi).

Raporla: farklı başlık sayısı · en sık 40 başlık ve sayıları.

### 2.2 `normal` başlık mı, değer mi
Kalın yazılmış `normal` metni bir **bölüm başlığı** mı yoksa bir bulgu
**değeri** mi? Kendi kararını ver ve gerekçesini yaz.

Raporla: `normal` kaç kez başlık, kaç kez değer konumunda.

### 2.3 Akciğer dışı bölümlerde malignite sözcüğü
Şu başlıkların **kendi içeriklerinde** malignite sözcüğü
(`mass|tumor|tumour|malign|carcinom|neoplas|nodul|lesion`) geçen rapor sayısı:

`breast` · `thyroid` · `abdomen` · `bone` · `esophagus` · `heart`

Raporla: her biri ayrı ayrı ve **en az birinde** geçen toplam rapor sayısı.

### 2.4 Özet bölümlerinin sızıntısı
`conclusion` · `abnormalities` · `findings` bölümlerinin içinde, **aynı
cümlede** hem akciğer dışı organ adı hem malignite sözcüğü geçen rapor sayısı.

Organ deseni: `thyroid|breast|liver|spleen|kidney|adrenal|pancrea|esophag|bowel`

Raporla: her bölüm için `bölüm var` ve `sızıntılı` sayıları. Olumsuzlanmış
cümleleri **ayırma** — ham sayı istiyorum, negasyon ayrı katmanın işi.

### 2.5 Başlıksız raporlar
Hiç bölüm başlığı içermeyen rapor sayısı.

### 2.6 Teknik parametre kirliliği
- `mm` veya `cm` ölçüsü geçen rapor sayısı.
- Bunların kaçında `slice thickness` / `reconstruction interval` benzeri
  **teknik parametre** satırı var.
- Teknik satırlar çıkarıldığında gerçek doku ölçüsü kalan rapor sayısı.
- **Aynı cümlede** hem nodül hem ölçü geçen rapor sayısı.

---

## 3. Ön kayıtlı sayılar

Aşağıdaki değerler **senin ölçümünden önce** yazılmıştır ve
`docs/38_vlm14_calisma_plani.md` ile `docs/39_astra_veri_sozlesmesi.md`
içinde yayımlanmıştır. Sonucuna göre **değiştirilmeyeceklerdir.**

Bunlara ölçümünü bitirmeden bakmaman tercih edilir; baktıysan raporunda belirt.

| Ölçüm | Ön kayıt |
|---|---:|
| Farklı başlık sayısı | 353 |
| `normal` geçişi (başlık sayılmamalı) | 5.975 |
| Başlıksız rapor | 123 (%4,1) |
| Akciğer dışı bölümde malignite — **en az biri** | **1.679 (%56,6)** |
| — meme | 1.052 |
| — kemik | 1.023 |
| — tiroid | 1.003 |
| — kalp | 946 |
| — özofagus | 502 |
| — abdomen | 343 |
| `conclusion` bölüm var / sızıntılı | 1.872 / 8 |
| `abnormalities` bölüm var / sızıntılı | 341 / 4 |
| `findings` bölüm var / sızıntılı | 482 / 14 |
| mm/cm geçen rapor | 222 |
| — teknik parametre içeren | 175 |
| — temizlenince kalan | 91 (%3,1) |
| Aynı cümlede nodül + ölçü | 37 (%1,2) |

---

## 4. Kabul ölçütü

| Durum | Sonuç |
|---|---|
| Bütün başlık sayılarında bağıl fark **≤ %20** | Sözleşme onaylanır, Adım 1 kodlanır |
| Herhangi birinde bağıl fark **> %20** | **Kodlama durur.** Ayrışma nedeni bulunur, sözleşme revize edilir |
| `normal` konusunda karar farklıysa | Fark büyüklüğünden bağımsız olarak tartışılır — bu bir yöntem farkıdır, sayı farkı değil |

Ayrıca: sözleşmenin §3 kapsam listelerinde **gözden kaçmış bir başlık** görürsen
söyle. Özellikle akciğer bulgusu adı taşıyan başlıklar (`emphysema`,
`atelectasis`, `bronchiectasis`, `pleural effusion`) gerçekten başlık mı, yoksa
`normal` gibi değer mi?

---

## 5. Çıktı

`reports/vlm14_bagimsiz_ayirici_olcumu.md` — yöntemin, sayıların, ön kayıtla
karşılaştırma tablosu ve varsa itirazların.

---

## 6. Bu denetim tek seferliktir

Bu iş emri **her adımda tekrarlanmayacaktır.** Bağımsız ölçüm yalnız şu üç
durumda istenir:

1. Bir sayı **dondurulmuş bir artefakta** (kilit, config, sürümlü sözlük) girecekse.
2. Bir sayı **rapora veya yayına** girecekse.
3. Bir sayı bir **kapı kararını** belirleyecekse (geç/kal).

Rutin kod, test ve ara ölçümler denetlenmez. Bu ölçüm 1. ve 2. şartı birden
sağladığı için istenmiştir: sözleşme `astra-adaptor-1.0` kilidine girecek ve
T8 değeri sonuç raporunda yayımlanacaktır.
