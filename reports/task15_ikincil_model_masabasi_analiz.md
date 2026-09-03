# TASK-15 · İkincil Model — Masabaşı Analiz

**Tarih:** 2026-09-03 · **Durum:** kapanış kanıtı · **GPU kullanılmadı, model koşulmadı, `test` açılmadı**

> Bu belge yeni bir koşu değildir. `kosu_v2_1`'in **kayıtlı ham yanıtları**
> yeniden okunmuştur. Hiçbir model indirilmedi, hiçbir dış servis çağrılmadı.

---

## 1 · Neden bu analiz yapıldı

`reports/task15_ikincil_model_raporu.md` §4, tekrar döngüsünü **modelin arızası**
olarak kaydediyordu. Ancak koşucunun üretim ayarları incelendiğinde
(`src/radyovlm/evaluation/ikincil_model.py:205-217`) şu görüldü:

```python
do_sample=False, num_beams=1, temperature=None, top_p=None, top_k=None
```

**Hiçbir tekrar kontrolü yok** — ne `repetition_penalty`, ne
`no_repeat_ngram_size`. Saf greedy çözümlemede tekrar döngüsü bilinen bir
artefakttır.

D64 şu kuralı kurmuştu: *koşucu ayarımızdan gelen ihlaller **bizimdir**, modele
yazılmaz.* `max_new_tokens=1024` bu kuralla düzeltilmişti. Tekrar kontrolünün
hiç olmaması **aynı sınıfta** bir eksikliktir.

Soru: **tekrar kontrolü eklenseydi kol kapı 2'yi geçer miydi?**

Bir belgenin tekrar kontrolüyle kurtulabilmesi için iki şart birlikte gerekir:
(a) tekrar döngüsü yüzünden düşmüş olmalı, **ve** (b) envanter dışı kimlik
**içermemeli** — çünkü tekrar kontrolü kapı 3'e dokunmaz.

---

## 2 · Ölçüm

`outputs/task15/ikincil_model/kosu_v2_1/qwen_{tr,en_genel,en_ucuz}_dev.jsonl`
· Qwen3.5-4B · 138 belge (46 × 3 kol) · envanter 144 kimlik

| kol | geçerli | geçersiz | envanter ihlali içeren | tekrar döngüsü görülen |
|---|---:|---:|---:|---:|
| tr | 37/46 | 9 | 5 | 1 |
| en-genel | 31/46 | 15 | 9 | 3 |
| en-ucuz | 34/46 | 12 | 11 | 0 |
| **toplam** | **102/138** | **36** | **25** | **4** |

### Hüküm

| | |
|---|---:|
| tekrar döngüsü görülen belge | **4** |
| bunlardan envanter ihlali **içermeyen** (yani kurtulabilecek) | **1** |
| tekrar kontrolünün kurtaramayacağı | **35** |
| şimdiki geçerli | 102/138 (%73,9) |
| **tekrar kontrolü sonrası ulaşılabilecek TAVAN** | **103/138 (%74,6)** |
| kapı 2 eşiği | 138/138 (%100) |
| **sonuç** | **GEÇMEZ** |

**Tekrar kontrolü eklenseydi de kol elenirdi.** Fark tek belgedir.

---

## 3 · Düzeltilen atıf

Rapordaki *"tekrar döngüsü modelin arızasıdır, ayarla çözülmez"* ifadesi
**eksikti**: koşucuda tekrar kontrolü yoktu, dolayısıyla döngünün ne kadarının
modele ait olduğu o koşudan okunamazdı.

Yerine geçen ve ölçülmüş hüküm:

> **Tekrar döngüsü 138 belgenin yalnız 4'ünde görüldü ve elenmenin belirleyici
> sebebi değildi. Koşucuya tekrar kontrolü eklenseydi tavan %74,6'da kalırdı;
> kapı 2'nin %100 eşiği yine geçilmezdi. Elenmenin belirleyici sebebi
> **envanter dışı kimlik** — 36 başarısızlığın 25'i.**

Bu, eski hükümden **daha güçlüdür**: kol artık "belki ayarımız yüzünden
düştü" şüphesi taşımıyor.

---

## 4 · Beklenmeyen bulgu — "uydurma" kimliklerin üçte ikisi uydurma değil

33 benzersiz envanter dışı kimlik tek tek katalogla karşılaştırıldı. Üç ayrı
sınıf çıktı ve dağılım beklenenden çok farklı:

| sınıf | sayı | örnek | envanterde karşılığı |
|---|---:|---|---|
| **1 · Yeniden adlandırma / çekim** | **15** | `bronchi`→`bronchus` · `pleural_effusion`→`effusion` · `thoracic_aorta`→`aorta` · `hiatal_hernia`→`hernia` · `cavitary`/`cavitaiton`→`cavitation` · `fibroatelectatic`→`atelectasis` | **VAR** |
| **2 · Çıplak niteleyici/parça** | **7** | `left` · `right` · `anterior` · `posterior` · `segment` · `artery` · `right_lobe` | kavram değil |
| **3 · Gerçek kapsam boşluğu** | **11** | `pneumatocele` · `scoliosis` · `suture` · `mucous_impaction` · `sequestration` · `mitral_valve` · `stomach` · `hiatal hernia dışı` | **YOK** |

**Sınıf 1 + 2 = 22/33 (%67).** Bunlar model uydurması değil, **adlandırma
uyuşmazlığı**. Kısıtlı çözümleme bunları mekanik olarak çözerdi.

### Ve bu, kısıtlı çözümleme kullanmama kararını haklı çıkarıyor — yeni bir sebeple

D65 kısıtlı çözümlemeyi *"kapalı listeye uymak kapı 3'ün sınavıdır"* diye
reddetmişti. Analiz daha güçlü bir sebep gösteriyor:

**Kısıtlı çözümleme sınıf 3'ü görünmez yapardı.** Model `pneumatocele` demek
isterken 144'ten *en yakın* kimliği seçmeye zorlanır; çıktı yapısal olarak
kusursuz görünür ama **11 gerçek bulgu sessizce yanlış kavrama eşlenirdi.**
Şimdiki hâlinde o 11 boşluk **görülebiliyor.**

Yani başarısız koşu, başarılı bir kısıtlı koşudan **daha bilgilendirici**.

---

## 5 · Adlandırılmamış dördüncü arıza: envanter dökümü

Analiz sırasında, önceki raporda ismi olmayan bir arıza türü görüldü:

| belge | kol | benzersiz kimlik | not |
|---|---|---:|---|
| `_107_263.txt` | tr | **127** | kesildi |
| `_56_193.txt` | tr | **120** | kesildi, envanter ihlali **yok** |
| `_93_38.txt` | tr | **116** | — |

Model 144'lük envanterin **neredeyse tamamını** tek rapor için listeliyor.
Sözlük sistemi belge başına ortalama **24,8** kavram buluyor; buradaki 120,
raporun söylemediği şeyleri de saymak demektir.

`_56_193` özellikle öğretici: envanter ihlali yok, yalnız token sınırında
kesilmiş. **Daha yüksek bir token tavanı bu belgeyi kapı 2'den geçirirdi** —
ama içerik yine klinik olarak anlamsız kalırdı. **Yapısal kapıyı geçmek, çıktının
kullanılabilir olduğunu göstermez.** Bu, kapı tasarımının bilinen bir sınırıdır
ve burada somut örneğiyle kaydedilmiştir.

---

## 6 · Sonuç

1. İkincil model kolunun düşürülmesi (D65) **doğruydu** ve şimdi ölçülmüş
   kanıta dayanıyor: tekrar kontrolü tavanı %73,9'dan %74,6'ya taşırdı, eşik
   %100'dü.
2. Rapordaki atıf düzeltildi; hüküm zayıflamadı, **güçlendi**.
3. Kısıtlı çözümleme kullanmama kararı, orijinal gerekçesinden **daha iyi** bir
   gerekçe kazandı: kısıt, 11 gerçek kapsam boşluğunu gizlerdi.
4. Sınıf 3'teki 11 kimlik envanterin **bedava dış denetimidir** ve gelecek sürüm
   için kapsam boşluğu adayı olarak kaydedilir. **Şimdi eklenmez** — sözlük
   donduruldu (D62/D67).
5. **Dördüncü model denenmez, dördüncü koşu yapılmaz.** Aday havuzu tükendi ve
   şimdi bunun ölçülmüş gerekçesi var.

**Üretilen dosya:** bu rapor. Hiçbir kilitli artefakt değiştirilmedi.
