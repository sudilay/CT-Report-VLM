# İş Emri · Astra Hattının Sözleşme Uyum Denetimi

**Tarih:** 2026-09-08 · **İsteyen:** Claude · **Yürüten:** bağımsız denetçi
**Faz:** SUDE-VLM-14 · Adım 5 öncesi **kapı**

---

## 0. Bu denetim neden isteniyor

Bu bir **sayı doğrulama** değil, **sözleşme uyum denetimidir.**

Adaptör (`astra-adaptor-1.0`) ve şema (`sema-1.0`) donduruldu. Sıradaki adım
`dev` kümesini açmaktır ve **bu geri alınamaz**: adaptörde bir kusur varsa ve
`dev` açıldıktan sonra bulunursa, `dev` doğrulama kümesi olarak harcanmış olur.

**Somut gerekçe — bu turda AYNI TÜRDE İKİ HATA yapıldı ve ikisi de tesadüfen
yakalandı:**

| # | Hata | Sonucu olacaktı |
|---|---|---|
| 1 | `sablon_cumle` Astra için hiç hesaplanmamıştı | `C#nodul-kalip` kuralı **sessizce ölü** kalacaktı |
| 2 | `supheli_niteleyici` `False` sabitlenmişti | aynı kuralın ikinci dalı **sessizce ölü** kalacaktı |

Bu hata sınıfının ortak özelliği: **hata vermez, sonuç üretir, ama kural
çalışmaz.** Üçüncüsü olabilir.

**Denetimin tek sorusu:**

> Şemanın beklediği her girdi Astra hattı tarafından gerçekten sağlanıyor mu,
> ve `sema-1.0`'ın hiçbir kural dalı Astra üzerinde sessizce ölü kalıyor mu?

---

## 1. Sınırlar

- ⛔ `dev` ve `held_out` satırlarına **DOKUNULMAZ.** Yalnız `train`
  (`split == "train"`) incelenir.
- ⛔ `Kanser_Etiketi_y`, `Censor_Time`, `Pillar_Ensemble_Skoru` kolonları
  **okunmaz.**
- Kod, kilit ve belgelerin tamamı açıktır — bu bir kör denetim değildir.

---

## 2. İncelenecek artefaktlar

| Dosya | Ne |
|---|---|
| `src/radyovlm/extraction/astra.py` | Bölüm adaptörü (`astra-sozlesme-1.0`) |
| `src/radyovlm/evaluation/vlm14.py` | Seri düzeyi toplama |
| `src/radyovlm/evaluation/sema.py` | Şema (`sema-1.0`) |
| `scripts/60_...` `61_...` `62_...` | Metin katmanı · aktarım denetimi · envanter |
| `configs/astra_adaptor_kilidi.json` | Adaptör kilidi |
| `docs/39_astra_veri_sozlesmesi.md` | Veri sözleşmesi (v4) |
| `data/processed/astra_sentences.parquet` | 69.055 cümle |
| `data/processed/astra_entities_train.parquet` | 84.763 varlık |
| `data/processed/astra_relations_train.parquet` | 33.676 ilişki |

---

## 3. Yapılacak kontroller

### K1 · Girdi sözleşmesi tam mı

`sema.py`'nin okuduğu **her** alanı kendin çıkar (kaynağı tara, aşağıdaki
listeye güvenme) ve Astra hattının onu sağladığını doğrula.

Benim çıkardığım liste — **doğrula, kabul etme**:

```
normalized_concept · cumle_metni · assertion · sent_idx · sablon_cumle
entity_id · assertion_rule · supheli_niteleyici · section
dusuk_guven_kodu · dusuk_guven · assertion_cue
```

Her alan için: **var mı · null oranı · farklı değer sayısı**. Tek değerli bir
alan varsa o dalın ölü olup olmadığını incele.

### K2 · Sessizce ölü kural dalı var mı — **en önemli kontrol**

`sema.py`'deki kural listesini (`kurallar_sirali` ve `_bulgu_duzeyi` içindeki
dallar) çıkar ve her dal için sor: **Astra `train` üzerinde bu dal hiç ateşliyor
mu?**

Ateşlemeyen her dal için ayır:
- **(a) meşru** — Astra metninde o dil hiç yok (ör. `part-solid` %0,0)
- **(b) kusur** — girdi eksik/yanlış olduğu için ateşleyemiyor

Bu ayrımı yapmadan "dal ateşlemiyor" demek yetersizdir.

**Önerilen yöntem:** aynı dal setini CT-RATE geliştirme havuzunda da koştur ve
ateşleme oranlarını karşılaştır. CT-RATE'te ateşleyip Astra'da **hiç**
ateşlemeyen dal, (b) şüphesi taşır.

### K3 · Bölüm eşlemesi doğru mu

`docs/39` §3'teki kova tanımlarına karşı, **20 rastgele raporu elle** incele:

- Akciğer içeriği yanlışlıkla `dis_organ` veya `meta` kovasına düşmüş mü?
- `**Normal:**` gibi değer etiketleri bölüm açmış mı? (açmamalı)
- Kapsam dışı bırakılan bir bölümde **akciğer** bulgusu kalmış mı?

### K4 · Kilit kodla tutarlı mı

`configs/astra_adaptor_kilidi.json` içindeki `A_tablosu_kolonlari`,
`B_tablosu_kolonlari` ve `train_dogrulamasi` sayıları, kodu koşturunca
**yeniden üretiliyor mu**? Üretilmiyorsa kilit bayattır.

### K5 · Bağlayıcı kısıtlar gerçekten uygulanıyor mu

Kilitteki kısıtların her biri için kodda karşılığını bul:

1. Sürekli olasılık üretilmiyor
2. `boyut_mm` yalnız L1 (`measured_by`) kaynağından
3. `boyut_mm` teknik parametre satırından **asla**
4. Ekstratorasik eleme **sayılıyor** (sessiz kayıp yok)
5. Şemanın **kuralı** değiştirilmemiş — Astra'ya özgü her şey adaptörde
6. Şablon istatistiği yalnız `train`'den

### K6 · Sonuçlar makul mü

`train` A tablosu dağılımı: `None` 1.669 · `not_mentioned` 209 ·
`intermediate` 89 · `indeterminate` 82 · `known_malignancy` 1.

`None` ile `not_mentioned` ayrımı doğru mu? 2.050 serinin 1.669'unun `None`
çıkması beklenen bir sonuç mu, yoksa bir dal ölü olduğu için mi?

---

## 4. Kabul ölçütü

| Durum | Sonuç |
|---|---|
| K1–K5'te **hiçbir (b) tipi kusur yok** | ✅ `dev` açılabilir |
| Herhangi bir (b) tipi kusur var | ⛔ **Adım 5 durur**, kusur düzeltilir, adaptör sürümü yükseltilir |
| K6'da açıklanamayan bir dağılım | ⚠ kusur sayılmaz ama raporlanır ve karara bağlanır |

---

## 5. Çıktı

`reports/vlm14_sozlesme_uyum_denetimi.md`:

1. K1 tablosu — her şema girdisi, durumu
2. K2 tablosu — her kural dalı, Astra'da ateşliyor mu, (a) mı (b) mi
3. K3 — 20 rapor incelemesinin bulguları
4. K4 — kilit yeniden üretildi mi
5. K5 — her kısıtın kod karşılığı
6. K6 — dağılım yorumu
7. **Hüküm:** `dev` açılabilir mi

---

## 6. Bu denetimin sınırı

Bu denetim **kod ve sözleşme uyumunu** ölçer. Şunları ölçmez ve iddia etmez:

- Şemanın klinik doğruluğu (patoloji ground truth yok, D71)
- Astra raporlarının doğruluğu
- Çıkarımın duyarlılığı (kaçırılanlar)

Bunlar ayrı işlerdir ve bu denetimin hükmü onları kapsamaz.

---

# EK · `astra-adaptor-1.1` için yeniden denetim

**Tarih:** 2026-09-08 · **Kapsam:** dar — yalnız K1 ve K5 yeniden bakılır

İlk tur **KALDI** ve beş düzeltme istedi. Düzeltmelerin beşi de uygulandı,
adaptör `astra-adaptor-1.1`'e yükseltildi, train artefaktları yeniden üretildi
ve test sayısı 494'ten 501'e çıktı.

**K2, K3, K4 ve K6 ilk turda geçmişti; yeniden koşulmasına gerek yoktur** —
ancak R4 (aşağıda) K6'nın sonucunun değişmediğini doğrulamayı istemektedir.

---

## Uygulanan düzeltmeler

| # | İlk turdaki bulgu | Uygulanan düzeltme |
|---|---|---|
| K1 | Eksik zenginleştirme alanı sessizce `False` sayılıyordu | `_sema_girdisi` artık `ValueError` veriyor (`ZORUNLU_ZENGINLESTIRME`) |
| K5.1 | İki ayrı teknik ölçü tanımı | `astra.olcu_teknik_mi` — tek kaynak; `scripts/61` ve `63` bunu kullanıyor |
| K5.2 | Özet bölümlerinde anatomi düzeyi eleme yoktu | `ekstratorasik_varliklar` — `located_at` ile varlık düzeyi eleme |
| K5.2 | Bayrak organ kaybı ile bilinmeyen/meta kaybını ayırmıyordu | `qf_bilinmeyen_bolum_malignite` ayrı bayrak |
| K5.3 | `qf_mediastinum_kaynakli` üretilmiyordu | Üretiliyor (train'de 1.921 seri) |
| K5.5 | `boyutlu_seriler` isteğe bağlıydı | `boyutlu_seriler` ve `iliskiler` **zorunlu** |

**İlk tur raporundaki bir düzeltme:** K1'de *"hazırlık adımlarını birleştirip
`seri_ozeti` çağıran üretim girişi bulunmadı"* denmişti.
`scripts/63_vlm14_tam_kosum.py` bu girişi sağlamaktadır (satır 138, 145, 147,
149) ve muhtemelen denetim başladıktan sonra yazılmıştır. Bu, kusurun kendisini
geçersiz kılmaz; sessiz `False` yine de düzeltilmiştir.

---

## Yeniden denetimin soruları

### R1 · Zenginleştirme kapısı gerçekten kapalı mı

`_sema_girdisi` dışında, eksik bir alanı sessizce varsayılan değere düşüren
**başka bir yol** kaldı mı? Özellikle:

- `sema.kalip_nodul_kolonlarini_ekle` içindeki `else: v["sablon_cumle"] = False`
  dalı Astra hattında devreye girebiliyor mu?
- `girdi_filtresi.uygula` eksik kolonda ne yapıyor?

### R2 · Teknik tanımı gerçekten tekil mi

Kod tabanında `mAs`, `kVp`, `slice thickness`, `collimation` gibi teknik
desenleri **bağımsız olarak** tanımlayan başka bir yer kaldı mı?
`scripts/07_extract_measurements.py` kendi `TEKNIK` desenini hâlâ taşıyor;
VLM-14 hattında kullanılıyor mu, yoksa yalnız kendi betiğinde mi kalıyor?

### R3 · **Anatomi filtresi aşırı eleme yapıyor mu — en önemli soru**

Bu düzeltme **yeni bir risk** getirmiştir: train kümesinde **6.093 varlık**
elenmektedir. Bu sayı büyüktür ve doğrulanmalıdır.

- Elenen 6.093 varlığın kaçı **zaten kapsam dışı bölümdeydi** (yani eleme
  gereksiz tekrardı), kaçı **kapsam içi bölümden** elendi?
- Kapsam içinden elenenlerin her biri gerçekten akciğer dışı organa mı bağlı?
- **Karışık organlı cümlelerde toraks kanıtı korunuyor mu?** Hem akciğer dışı
  organ hem akciğer bulgusu taşıyan cümleler bulun ve akciğer kanıtının
  kaldığını doğrulayın.
- `located_at` ilişkisi yanlış anatomiye bağlanmış örnek var mı?

**Kemik yapıların bilinçli olarak filtre dışında bırakılması** (`bone`, `rib`,
`vertebra`, `sternum`) gerekçesiyle birlikte değerlendirilmelidir: kilitli sınır
takımının `C5-03` vakası vertebra metastazını `known_malignancy` olarak
hedeflemektedir. Bu asimetri savunulabilir mi, yoksa tutarsızlık mı?

### R4 · Düzeltmeler gerileme yarattı mı

Sınıf dağılımının değişmediği iddia edilmektedir
(`None` 1.669 · `not_mentioned` 209 · `intermediate` 89 · `indeterminate` 82 ·
`known_malignancy` 1). **Bağımsız olarak doğrulayın.**

Değiştiyse hangi seriler ve neden? Bir düzeltmenin dağılımı değiştirmesi kusur
değildir, ancak **açıklanamayan** bir değişiklik kusurdur.

### R5 · Kilit tutarlı mı

`configs/astra_adaptor_kilidi.json` sürüm `astra-adaptor-1.1`, revizyon
defteri ve `train_dogrulamasi` sayıları kodu koşturunca yeniden üretiliyor mu?

---

## Kabul ölçütü

| Durum | Sonuç |
|---|---|
| R1–R5'te (b) tipi kusur yok | ✅ `dev` açılabilir |
| Anatomi filtresi **aşırı eleme** yapıyor | ⛔ Filtre daraltılır, `1.2` sürümü |
| Başka (b) tipi kusur | ⛔ Adım 5 yine durur |

## Çıktı

`reports/vlm14_sozlesme_uyum_denetimi_v11.md` — R1–R5 bulguları ve hüküm.

## Sınırlar

Önceki turla aynı: yalnız `train`; `dev` ve `held_out` satırlarına dokunulmaz;
etiket ve skor kolonları okunmaz.
