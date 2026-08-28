# TASK-13 · Pilot İşaretleme Raporu

**30 cümle · 112 aday (86 gerçek + 26 çeldirici) · ayar kümesi · 2026-08-28**

> ⚠ **Bu bir sonuç raporu değildir.** Pilot **ayar kümesinden** gelir (D26).
> Aşağıdaki değerler üzerinde düzeltme yapıldığı için tarafsız tahmin değil,
> **geliştirme gözlemidir**. Raporlanacak doğruluk `test-v1`den gelecek —
> kurallar donduktan sonra **bir kez** açılacak.

---

## 1. Ölçüm aygıtı önce doğrulandı

Sistem puanına bakmadan önce **işaretlemenin kendisi** denetlendi.

| Denetim | Değer | Eşik | Durum |
|---|---|---|---|
| Çeldirici ret oranı | **%100** (26/26) | %80 | geçti |
| Boş bırakılan satır | 0 | — | — |

26 çeldirici, sistemin **üretmediği** sahte adaylardır: cümleden rastgele seçilmiş
kelimelere rastgele kavram atanır. İşaretleyen kişi her şeye *"doğru"* diyorsa
burada yakalanır.

**Neden önce bu:** ret oranı düşük çıksaydı diğer hiçbir sayı yorumlanamazdı.
%100 çıktığı için, kesinlik atamasındaki düşüklüğün **işaretleyicinin değil
sistemin** sorunu olduğu söylenebildi.

---

## 2. İlk puanlama — bir ölçüt kaldı

| Ölçüt | Değer | Eşik | Durum |
|---|---|---|---|
| K4 · varlık kesinliği | %96,5 (83/86) | %90 | geçti |
| **K6 · kesinlik ataması** | **makro-F1 %63,5** · doğruluk %72,3 | %85 | **KALDI** |

Hata tipe göre eşit dağılmıyordu — **bu asimetri hatayı adresledi**:

| tip | hata oranı |
|---|---|
| anatomy | **%43** |
| observation | %6 |
| qualifier | %17 |

---

## 3. Hata 1 — negasyon anatomiye sıçrıyordu

> *"No nodule was detected in the right lung"*

Sistem **`lung`'u da** `absent` işaretliyordu. Akciğer yerinde duruyor; yok olan nodül.

**Sebep:** kapsam temelli atama, kapsamdaki **her** varlığa uygulanıyordu.

**Düzeltme (D28):** anatomi iki koşuldan **biri** sağlanırsa korunur —
(1) kapsamda bir gözlem/niteleyici de var, veya
(2) anatomi bir konum edatının (`in`/`within`/`at`/`on`/`into`) ardında.

Gerçek organ yokluğu korunmaz:

| cümle | sonuç |
|---|---|
| *"No lymph nodes are observed **in** the mediastinum"* | `lymph_node` **absent** · `mediastinum` present |
| *"The right breast was not observed secondary to the operation"* | `breast` **absent** ✓ |

| | önce | sonra |
|---|---|---|
| anatomi `absent` | 177.922 | **11.117** |
| anatomi `uncertain` | 24.416 | **5.887** |
| **gözlem (3 sınıf)** | 166.899 / 181.013 / 20.103 | **birebir aynı** |

Gözlem sayılarının değişmemesi düzeltmenin **hedefli** olduğunun kanıtıdır.

---

## 4. Hata 2 — çıkarım ifadeleri belirsiz sayılıyordu

Sistem *"ile uyumlu"*, *"lehine"*, *"şüpheli"*, *"olasılıkla"* ifadelerini
`uncertain` üretiyordu.

**Alan sözlüğü belgesi §12.2 bunları `present` sayar**: bulgu vardır, yalnızca
dayanağı çıkarımdır; tereddüt ayrı bir `certainty` alanının işidir.

İşaretleme kılavuzu bu belgeden **ölçümden önce** yazılmıştı ve `compatible with
→ mevcut` diyordu. **Hedef sabitti, sistem ona uymuyordu.**

**Düzeltme (D29):** `ipucu_sozlugu.yaml`'a `cikarim_ifadesi` bölümü (9 ipucu);
`context.py` ctx-1.1 karar zinciri:

```
1. belirsizlik_oncelikli  -> uncertain    ("dışlanamaz")
2. negasyon               -> absent
3. belirsizlik            -> uncertain    (parantez-soru, ayırıcı tanı)
4. cikarim_ifadesi        -> present      ipucu KAYDEDİLİR
```

İpucu `assertion_cue`/`assertion_rule`'da tutulur — ileride `certainty` alanı
eklenirse bu kayıt olmadan geri üretilemez.

Öncelik korunuyor: *"**No** findings **compatible with** pneumonia"* → **absent**.

**Etki:** 20.587 varlık — belirsiz işaretlenenlerin **%70'i**.

---

## 5. Düzeltme sonrası — iki türlü raporlanır

| | K6 makro-F1 | doğruluk | eşik %85 |
|---|---|---|---|
| İlk puanlama | %63,5 | %72,3 | KALDI |
| **A · yalnızca sistem düzeltmeleri** | **%87,8** | %95,2 | **GEÇTİ** |
| B · kılavuz düzeltmesi de uygulanınca | %90,1 | %96,4 | geçti |

**Kazanç hanesine yazılan A'dır.** B, teknik çekince kuralının (D30) düzeltilmesini
içerir — bu **hedefi değiştirir**, sistemi iyileştirmez. Sistem düzeltmeleri
eşiği **kılavuz düzeltmesi olmadan da** geçmiştir.

### A · sınıf bazında

| sınıf | destek | P | R | F1 |
|---|---|---|---|---|
| present | 61 | %94 | %100 | **%97** |
| absent | 14 | %100 | %100 | **%100** |
| uncertain | 8 | %100 | %50 | %67 |

`uncertain` duyarlılığı düşük ve **destek yalnızca 8** — bu sınıf hakkında pilotla
karar verilemez. Kalan 4 hatanın tamamı teknik çekince vakasıdır (D30).

K4 varlık kesinliği **%96,5'te değişmedi** — düzeltmeler kesinlik atamasına
dokundu, varlık çıkarımına dokunmadı.

---

## 6. Değişmezler — düzeltme sonrası

| kod | eşik | sonuç | payda | ihlal | durum |
|---|---|---|---|---|---|
| K11 | %100 | %100,0 | 725 | 0 | geçti |
| K12 | %100 | %100,0 | 37.689 | 0 | geçti |
| K13 | %90 | %99,6 | 10.825 | 41 | geçti |
| K14 | %100 | %100,0 | 187.752 | 0 | geçti |
| K15 | %85 | %98,9 | 25.604 | 285 | geçti |

Şema kapısı (sema-1.2, K1–K3g) geçti. Test paketi: **240 + 5 yeni = 245 geçiyor.**

---

## 7. Korpus düzeyi son durum

| | değer |
|---|---|
| toplam varlık | 1.180.408 |
| present | 992.656 (%84,1) |
| absent | 179.898 (%15,2) |
| uncertain | **7.854 (%0,7)** |

`uncertain` artık **yalnızca gerçek belirsizlikte**: parantez-soru (6.620),
*"dışlanamaz"* (725), ayırıcı tanı. Çıkarım dayanağı `assertion_rule`'da
izlenebilir kalıyor (`cikarim:uyumlu` 19.533 · `cikarim:lehine` 10.411).

---

## 8. Pilotun cevapladığı üç soru

| soru | cevap |
|---|---|
| Kılavuz anlaşılır mı? | **Evet** — bir iç çelişki çıktı (teknik çekince), düzeltildi |
| Doktor olmayan biri yapabilir mi? | **Evet** — %100 çeldirici reddi, 0 boş satır |
| Sistemde büyük bir bozukluk var mı? | **Evet, iki tane** — ikisi de bulundu ve düzeltildi |

**Pilot amacına ulaştı.** Tam kümeye geçilebilir.

---

## 9. Açık uçlar

- `uncertain` sınıfı desteği 8 — tam kümede yeterli örnek gerekiyor
- 4 teknik çekince vakası kılavuz düzeltmesiyle çözüldü, sistemde iş yok
- Pilot **tek işaretleyici** ile yapıldı; işaretleyiciler arası uyum ölçülmedi
- Bu değerlerin hiçbiri sonuç olarak raporlanamaz — `test-v1` bekliyor
