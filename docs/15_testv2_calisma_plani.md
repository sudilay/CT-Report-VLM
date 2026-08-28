# `test-v2` Çalışma Planı — başlamaya hazır

**Kurallar donduruldu (2026-08-28).** Bu, TASK-13'ün son adımıdır ve çıkacak
sayı **raporlanacak sayıdır**.

---

## Hazır olan

| dosya | ne | boyut |
|---|---|---|
| `TESTV2_A_codex.csv` · `TESTV2_A_gemini.csv` | kör listeleme | **295 cümle** |
| `TESTV2_B_codex.csv` · `TESTV2_B_gemini.csv` | yargılama | **1.105 aday** (267'si çeldirici, %24) |
| `task13_B_anahtar_test-v2.csv` | çeldirici anahtarı | ⛔ **işaretleyiciye verilmez** |

Kümenin kendisi: 295 cümle · 231 hasta · hepsi **valid** bölümünden
(sözlüğe hiç katkı vermemiş hastalar).

Grup dağılımı — nadir sınıflar için **ölçülerek** zenginleştirildi (D33):

| grup | cümle | neden |
|---|---|---|
| rastgele | 100 | yanlılıksız temel |
| **onceki_tetkik** | **60** | `prior` desteği ayar kümesinde 0–5'ti |
| **belirsizlik** | **55** | `uncertain` desteği 4–16'ydı |
| negasyon | 20 | |
| **cikarim** | **20** | D29 kararı ayrıca sınansın |
| coklu_bulgu | 20 | |
| coklu_olcu | 20 | |

---

## Sıra — bozulmamalı

1. **A · kör listeleme önce.** İkisi de kendi `TESTV2_A_*.csv` dosyasını doldurur.
2. **Sonra B · yargılama.**

⚠ B'yi görmüş bir göz sistemin **kaçırdığını** artık fark edemez. Duyarlılık
yalnızca kör listelemeden ölçülebilir ve bu, tek atışlık kümede telafi edilemez.

⚠ İki işaretleyici **birbirinin dosyasına bakmaz**. Uyum (kappa) ölçümü buna
dayanıyor.

---

## Prompt · Codex

```
docs/12_pilot_rehberi.md dosyasındaki kuralları oku. Kurallar donduruldu;
bu ölçümün sonucu raporlanacak sayıdır.

İKİ AŞAMA, SIRAYLA:

1) data/processed/TESTV2_A_codex.csv — 295 cümle, kör listeleme.
   Her cümle için `bulgular` ve `anatomiler` kolonlarını doldur:
   cümlede geçen bulguları ve anatomik yapıları metinde geçtiği hâliyle,
   virgülle ayırarak yaz. Bulgunun YOK olması onu listeden çıkarmaz.

2) A'YI BİTİRDİKTEN SONRA data/processed/TESTV2_B_codex.csv — 1.105 aday.
   Kolonlar: dogru_varlik_mi (E/H), dogru_kavram_mi (E/H),
   kesinlik_ne_olmali (mevcut/yok/belirsiz), zaman_ne_olmali
   (guncel/onceki/bilinmiyor).

A'yı bitirmeden B'ye bakma. B'yi gördükten sonra A'ya dönersen duyarlılık
ölçümü geçersiz olur ve bu küme bir kez açılıyor.

HATIRLA — sonradan eklenen üç kural:
- ANATOMİ OLUMSUZLANMAZ: "No mass in both lungs" -> mass YOK, lungs MEVCUT.
  Belirsizlik için de geçerli: "lesion (cyst?) in the liver" -> liver MEVCUT.
  İstisna: yapı gerçekten yoksa ("breast not observed secondary to the
  operation") -> YOK.
- TEKNİK YETERSİZLİK kesinliği DEĞİŞTİRMEZ: "could not be evaluated
  optimally" -> MEVCUT. ("cannot be excluded" farklıdır -> BELİRSİZ)
- Cümle başındaki ? veya ?? biçim artığıdır, yok say.

MEVCUT: "compatible with", "in favor of", "suspicious", "probably"
BELİRSİZ yalnızca: "cannot be excluded", parantez içi soru "(cyst?)",
"cannot be characterized", "ayırıcı tanı"

KURALLAR:
- task13_B_anahtar_test-v2.csv dosyasını AÇMA.
- *_gemini.csv dosyalarına BAKMA.
- Listede kasıtlı yanlış adaylar var (267 tane, %24).
- Emin olamazsan BOŞ BIRAK ve nota yaz. Tahmin etme.

Bitirince bildir: kaç satır boş bıraktın, nerede zorlandın, süre,
ve A'yı B'den önce doldurduğunun teyidi.
```

**Gemini için:** aynı metin, `codex` → `gemini`, ve *"`*_codex.csv` dosyalarına
bakma"*.

---

## İşaretleme dönünce yapılacaklar (kod tarafı)

1. Çeldirici kapısı — %80 altındaysa **ölçüm geçersiz**, o işaretleyici dışlanır
2. İşaretleyiciler arası kappa
3. `scripts/18_score_ayar.py` mantığıyla puanlama — K4, K5, K6, K7
4. Rastgele ve hedefli skorlar **AYRI** raporlanır (D26/6)
5. `reports/cikarim_dogruluk_raporu.md` yazılır

⚠ **Kırmızı çizgi:** sonucu görüp herhangi bir kural, sözlük veya desen
değiştirilirse bu sürüm **iptal** edilir, `--surum test-v3` çekilir ve raporda
eski skorun geçersiz olduğu yazar (D26/5, D31).

Ayrışma çıkarsa yapılabilecek **tek** şey: kural boşluğu mu diye bakmak ve
**kılavuzu** düzeltip yeniden yargılatmak — sistemi değil. Ayar kümesinde bu iki
kez oldu ve ikisi de meşruydu, çünkü hedef önceden yazılıydı.

---

## Beklenen sonuç ve okunuşu

Ayar kümesinde ölçülenler (geliştirme gözlemi):

| ölçüt | A | B |
|---|---|---|
| K5 duyarlılık | %93,0 | %89,7 |
| K4 kesinlik | %99,0 / %100 | %85,8 / %100 |
| K6 present / absent F1 | %98 / %93 | %97 / %95 |

`test-v2`de bunlardan **düşük** çıkması normaldir ve beklenir — ayar kümesinde
düzeltme yaptık, test kümesinde yapmadık. Aradaki fark **iyimserlik payıdır** ve
raporda ayrıca yazılır.

`uncertain` ilk kez ölçülebilir olacak (destek ~50 hedefleniyor).
