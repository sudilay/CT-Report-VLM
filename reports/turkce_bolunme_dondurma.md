# Türkçe Bölünme Dondurma — TASK-14

**2026-08-31 · Türkçe yüzey geliştirmesi başlamadan önce**

> Bu belge, dil ablasyonunun (TASK-15) hangi belgeler üzerinde ölçüleceğini
> sabitler. Dondurma sonrası `test` bölümünün 56 belgesine **yüzey geliştirirken
> bakılırsa** ölçüm geçersizdir.

---

## 1. Neden bölünme şart — ve neden **şimdi**

Elimizde **tek** Türkçe kaynak var: RadTr. Aynı kaynak hem Türkçe yüzey
sözlüğünü kurmakta hem de dil ablasyonunda ölçüm yapmakta kullanılacak. Bu ikisi
aynı belgelerde olursa, sözlüğü kuran veriyle sözlük sınanmış olur.

⚠ **Kirlenmenin yönü tehlikeli.** Desenler test'e uydurulursa Türkçe taraf
haksız yere iyi çıkar ve ablasyondan yanlışlıkla *"Türkçe veri önemliymiş"*
sonucu çıkar. Yani kirlenme, **tam da varmak istediğimiz sonucu** bozar.

Bölünme sözlük kurulmadan **önce** yapılmalı; sonra yapmak işe yaramaz.

---

## 2. Bölünme — **uydurulmadı, RadTr'nin kendi bölünmesi**

`scripts/16_extract_radtr_thorax.py` kaynak bölümü `kaynak_bolum` alanında
korumuştu. Kendi bölünmemizi uydurmuyoruz.

| bölüm | belge | kelime | varlık | present | absent | uncertain | SHA-256 |
|---|---|---|---|---|---|---|---|
| **train** | 327 | 44.841 | 10.522 | 3.615 | 573 | 706 | `9a4fd147d2774785` |
| **dev** | 46 | 6.416 | 1.490 | 502 | 87 | 106 | `b8aaeabe3b701244` |
| **test** | 56 | 7.784 | 1.817 | 613 | **86** | **128** | `55d21d9b5a3bf328` |

`data/processed/radtr_toraks.jsonl` → `8ce5ef37cdfd4504`

### ⚠ Ofset düzeltmesi — 2026-08-31, dondurmadan sonra

Adım 6'ya girerken RadTr altın span'larının **bir token sağa kaymış** olduğu
görüldü: `Obs_Anatomy` etiketi *"artmıştır."* fiiline denk geliyor, span'lar
cümle sınırını aşıyordu. RadTr token indeksleri **1-tabanlı**; çıkarım betiği
0-tabanlı varsaymıştı.

Nesnel ölçüt — iyi hizalanmış span, son tokeni dışında nokta ile biten token
**içermez**:

| kayma | span-içi nokta (31.847 span) |
|---|---|
| −1 | **%9,6** ✅ |
| 0 (hatalı) | %16,3 |
| +1 | %22,7 |

İkinci doğrulama: `Obs_Anatomy` span'larının yüklemle bitme oranı
**%8,3 → %2,4**.

⚠ Bu hata daha önce bir kez *"ofset 0 doğru"* diye **yanlış doğrulanmıştı**;
o doğrulama örneklere göz atmaya dayanıyordu, bu nesnel ölçüte dayanıyor.

**Dondurma bozulmadı:** bölüm üyeliği sağlama toplamları (`train`
`9a4fd147…`, `dev` `b8aaeabe…`, `test` `55d21d9b…`) **değişmedi** — onlar belge
kimliği ve belge metnini özetliyor, düzeltme yalnızca span alanını etkiledi.
Belge sayıları ve varlık sayıları da aynı (429 / 13.829).

⚠ Düzeltme **puanlamada kullanılmadan önce** yakalandı; hatalı span'larla hiçbir
ölçüm yapılmadı.

### Yayımlanmış bölünmeyi kullanmanın ek faydası

Türkçe varlık çıkarımında yayımlanmış bir taban skoru **bu bölünmede** ölçülmüş.
Kendi bölünmemizi uydursaydık o skorla karşılaştırma imkânsız olurdu.

---

## 3. Kullanım kuralı

| bölüm | rol | kaç kez bakılır |
|---|---|---|
| **train** 327 | Türkçe desen geliştirme | sınırsız |
| **dev** 46 | ayar kümesi — desen düzeltme burada ölçülür | sınırsız |
| **test** 56 | **dil ablasyonu ölçümü** | **bir kez** |

Bu, İngilizce tarafta uygulanan ayar/test disiplininin birebir aynısıdır
(D26, D31).

### Kilit

`scripts/20_turkce_yuzey_taslagi.py` yalnızca `train+dev` üzerinde çalışır.
`--bolum test` çağrısı `sys.exit` ile durur.

---

## 4. Maruziyet kaydı — **gizlenmiyor, sınırı çiziliyor**

`tr-0.1` sayımları bölünmeden **önce** 429 belgenin tamamında bir kez yapıldı.
Bu bir maruziyettir ve kayda geçiyor. Sınırları:

- **Hiçbir belge okunmadı** — yalnızca 82 desenin toplam frekansı sayıldı
- **Hiçbir skor hesaplanmadı** — ölçülen kapsamaydı, doğruluk değil
- **Hiçbir desen skora bakılarak seçilmedi** — desenler Türkçe radyoloji
  terminolojisinden yazıldı, RadTr'den madenlenmedi
- Bir desen hatası bu sayımla yakalandı (`b[uü]l` deseni *"bulgu"* ve
  *"bulunmaktadır"* yakalıyordu). Düzeltme dile özgü bir kural hatasıydı,
  skora göre ayar değildi.

### Maruziyetin etkisi **ölçüldü — sıfır**

| ölçüm tabanı | kelime | geçen kavram |
|---|---|---|
| tümü (`tr-0.1`) | 59.041 | **72 / 82 · %88** |
| **train+dev (`tr-0.2`)** | 51.257 | **72 / 82 · %88** |
| test (referans, kullanılmadı) | 7.784 | 65 / 82 · %79 |

`test` bölümü %88 sonucuna **hiçbir şey katmamıştır**; sonuç train+dev üzerinde
birebir yeniden üretilmiştir. Bu yüzden `tr-0.1` maruziyeti ölçümü geçersiz
kılmaz — ama kayda geçer.

---

## 5. Dondurulan taslak

| | |
|---|---|
| dosya | `configs/turkce_yuzeyler_taslak.yaml` |
| sürüm | **tr-0.2** |
| kaynak | RadTr train+dev (373 belge) — **test hariç** |
| SHA-256 | `671ba5718ee288a8` |
| kavram | 82 · RadTr'de geçen **72** |
| uzman onayı | ⛔ **hiçbir girdide yok** (`uzman_onayi: false`) |

⚠ Bu taslak sistemin kalıcı sözlüğüne (`bulgu_sozlugu.yaml`,
`anatomi_sozlugu.yaml`) **girmez**. Dil ablasyonunda ayrı bir deney sözlüğü
olarak kullanılır. Uzman onayından geçmeden kalıcı sözlüğe alınamaz.

---

## 6. Bu bölünmeyi geçersiz kılacak şeyler

1. `test` bölümüne yüzey geliştirirken bakmak
2. Ablasyon sonucunu görüp desen/sözlük değiştirmek → `test-v2`deki kuralın
   aynısı: sürüm iptal edilir, yeni bölünme gerekir
3. `radtr_toraks.jsonl` sağlama toplamının değişmesi

---

## 7. Bilinen sınırlar

| sınır | etkisi |
|---|---|
| RadTr **sentetik** — radyolog yazımı ama gerçek hasta değil | Sonuç *"Türkçe raporlarda"* değil *"RadTr benzeri Türkçe metinlerde"* diye yazılır |
| **56 belge** küçük | Güven aralığı geniş; tek nokta tahmini olarak sunulamaz |
| Türkçe yüzeyler **uzman onayı yok** | Türkçe tarafın düşük çıkması dilden mi desenden mi ayrılamaz — yorum askıda kalır |
| Varlıkların %54'ü kesinlik eksenine eşlenmedi | RadTr `Obs_Anatomy` etiketine kesinlik vermiyor; ablasyon kesinlik ölçümü eşlenen alt kümede yapılır |
