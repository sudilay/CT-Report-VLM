# İş Emri · `known_malignancy` Kör Metin Puanlaması (v2)

**Tarih:** 2026-09-08 · **İsteyen:** Claude · **Yürüten:** bağımsız yargıç
**Faz A · A4** · Protokol: `docs/37_task17_known_malignancy_kor_dogrulama.md`

---

## ⛔ ÖNCE BUNU OKU — geçen sefer burada hata yapıldı

Bu doğrulamanın v1 turu, yargıç bir tutarsızlığı araştırırken **anahtar
dosyasını açtığı** için resmî sonuç sayılamadı. Anahtar hedef içermiyordu ama
katı *"yalnız cümle"* koşulu bozuldu ve gelen yargı ancak gayriresmî geri
bildirim olarak işlenebildi.

**Bu turda:**

- ❌ `configs/task17_km_kor_anahtar_v2.json` **açılmayacak**
- ❌ `src/radyovlm/evaluation/sema.py` **açılmayacak**
- ❌ `configs/degerlendirme_semasi.json` **açılmayacak**
- ❌ `docs/40_sema_dondurma_protokol_degisikligi.md` **açılmayacak**
- ❌ Kural, kavram listesi, desen, `study_id` **aranmayacak**

Bir şey tuhaf görünürse **araştırma — sor.** Tutarsızlığı kendin çözmeye
çalışman bu turu da geçersiz kılar.

Okuyabileceğin tek şeyler: bu iş emri, `docs/37` (protokol) ve kör paket CSV.

---

## 1. Paket

```
outputs/task17/km_kor_v2/KOR_known_malignancy_v2.csv
```

**Doğrula (zorunlu):**

```
SHA-256 = 16411428b04a359faf6765249f12c307dd1fbabecb9d74715608746c5e56a4ed
```

Tutmuyorsa **dur ve bildir.**

40 satır · kolonlar: `vaka_id`, `cumle`, `yargi_E_H_SORU`, `gerekce`.
Son iki kolon boştur; senin dolduracağın yerdir.

**Paketin geçerliliği doğrulanmıştır:** güncel kodla yeniden üretildiğinde
popülasyon (156 çalışma) ve 40 vakalık örneklem eşlemesi **birebir aynı**
çıkmaktadır. Tohum `20260908`, örneklem büyüklüğü 40; ikisi de koşumdan önce
ilan edilmiştir.

---

## 2. Sorulan tek soru

Her cümle için:

> Bu cümle, hastada **daha önceden bilinen / belgelenmiş** bir kanser olduğunu
> söylüyor mu?

| Yanıt | Anlamı | Örnek |
|---|---|---|
| **E** | Evet — raporda yazılı bir kanser öyküsü/tanısı var | *"followed up for lung cancer"* · *"known primary"* · *"operated for breast ca"* |
| **H** | Hayır — yalnız **radyolojik yorum** var, ya da kanserle ilgili hiçbir öykü yok | *"highly suspicious for malignancy"* · *"metastasis cannot be excluded"* |
| **?** | Cümleden anlaşılmıyor | — |

`gerekce` kolonuna kısa bir not yaz; **`H` ve `?` için zorunlu.**

**Ayrımın özü:** *belgelenmiş öykü* ile *radyolojik nedensellik/olasılık*
arasındaki fark. *"due to malignant infiltration"* bir öykü değil, bir yorumdur.

---

## 3. Kabul ölçütü — sonuç görülmeden yazıldı, değiştirilmeyecek

```
Kesinlik = E / (E + H)   ≥ %85
```

`?` yanıtları paydadan çıkarılır **ve sayısı ayrıca raporlanır.**

⚠ Bağımsız denetim, `?`'yi paydadan çıkarmanın **iyimser** olduğunu belirtmişti
ve bu itiraz kayda geçmiştir. Bu nedenle **iki oranı da** raporla:

- Protokol hesabı: `E / (E + H)`
- Duyarlılık kontrolü: `E / 40` (yani `?` = `H` sayılırsa)

Ayrıca `E/(E+H)` için **%95 binom güven aralığı** ver.

---

## 4. Ne ölçülüyor, ne ölçülmüyor

**Ölçülen:** Tetikleyicinin `known_malignancy` ürettiği cümlelerde, cümlenin
gerçekten yazılı bir kanser öyküsü bildirip bildirmediği.

**Ölçülmeyen ve iddia edilmeyecek:**

| Ölçülmeyen | Neden |
|---|---|
| Hastanın gerçekten kanseri olup olmadığı | Patoloji ground truth yok (D71) |
| Klinik doğruluk | Aynı sebep |
| Duyarlılık (kaçırılanlar) | Örneklem yalnız **tetiklenen** vakalardan çekildi; kaçanlar ayrı örneklem ister — **ilan edilmiş sınırdır** |

---

## 5. Sonucun bağlayıcı etkisi

| Kesinlik | Sonuç |
|---|---|
| **≥ %85** | Kural ayakta kalır — yalnız *"raporda yazılı öyküyü yakalama"* ekseninde. Klinik doğruluk iddiası **yok** |
| **< %85** | ⚠ Kural **geri alınır**, `known_malignancy` yeniden ölü basamak olur ve şemanın hedef uyumu **daha da düşer** |

Eşik sonuç görüldükten sonra **değiştirilmez.** Hatalı bulunan vakalar
incelenip desen daraltılırsa bu **yeni bir sürümdür** ve bu doğrulama geçersiz
sayılır, yeni örneklem çekilir.

---

## 6. Çıktı

`reports/km_kor_v2_yargi.md` — ve doldurulmuş CSV'yi
`outputs/task17/km_kor_v2/KOR_known_malignancy_v2_yargi.csv` olarak kaydet
(orijinali **üzerine yazma**).

Raporda bulunsun:

1. Bağımsızlık beyanı — hangi dosyaları açtın, SHA doğrulaması tuttu mu
2. `E` / `H` / `?` sayıları
3. İki oran + %95 güven aralığı
4. `H` verdiğin her vakanın `vaka_id`'si ve gerekçesi
5. `?` verdiğin vakalar ve neden karar veremediğin
6. Desende bir örüntü görüyorsan (ör. `H`'lerin çoğu aynı kalıptan geliyorsa)
   bunu belirt — **ama kuralı arama, yalnız cümlelerde gördüğünü yaz**

---

## 7. Bu denetim neden isteniyor

`known_malignancy` ölçeğin **en üst** basamağıdır ve rapor düzeyini doğrudan
malignite-pozitif yapar. Yanlış pozitifi azaltmak bu projenin ayırt edici
önceliğidir, dolayısıyla en üst basamağın kesinliği yüksek olmalıdır.

Bu, `docs/41`'deki gibi bir "sayı doğrulama" değil, **bir kural sürümünün
kabul kapısıdır** — sonucu şemanın dondurulup dondurulamayacağını etkiler.
