# Dil Ablasyon Protokolü — TASK-15

**Sorulan soru:** Türkçe veri seti gerekli mi?

Bu belge, o soruyu **ölçülebilir** hâle getirir. Ölçüm başlamadan yazıldı;
sonucu görüp değiştirilirse sürüm iptal edilir (D26/5, D31).

---

## 1. Soruyu ölçülebilir hâle getirmek

Ham hâliyle *"Türkçe veri önemli mi"* bir ölçüm sorusu değil. Ölçülebilir hâli:

> **Aynı belge Türkçe okunduğunda mı, İngilizceye çevrilip okunduğunda mı
> daha doğru çıkarım üretiyor? Fark varsa hangi eksende ve ne kadar?**

### ⚠ Ölçüm olmayan tasarım — ve neden

Bir modele hem Türkçesini hem İngilizcesini verip *"yorumla"* demek **ölçüm
değildir**:

| sorun | sonucu |
|---|---|
| Modelin kendi yanlılığı sonuca karışır | Ölçtüğümüz şey dil değil, model olur |
| Tekrarlanabilir değil | Aynı girdi farklı cevap verir |
| Karşılaştırılabilir sayı üretmez | Raporda "şu kadar kayıp" yazılamaz |

Model yorumu **atılmıyor** — hata analizinde niteliksel destek olarak kalıyor
(bölüm 7). Yalnızca *sonuç* hanesine yazılmıyor.

---

## 2. Tek değişkenli tasarım — bağlayıcı

| sabit | değişen |
|---|---|
| aynı belgeler (RadTr test · 56) | **girdinin dili** |
| aynı görev (varlık + kesinlik çıkarımı) | |
| aynı altın açıklama | |
| aynı ölçütler ve eşikler | |

Üç kol:

| kol | girdi | kullanılan sözlük |
|---|---|---|
| **TR** | Türkçe asıl | Türkçe yüzeyler (`tr-0.2+`) |
| **EN-çeviri** | genel amaçlı çeviri | mevcut İngilizce sözlük |
| **EN-tıbbi** | tıbbi metinde eğitilmiş model çevirisi | mevcut İngilizce sözlük |

Çeviriyi **iki yoldan** üretmek, çeviriyi de bir değişken yapar ve kaybın
**çeviriden mi dilden mi** geldiğini ayrıştırır. Tek çeviriyle bu ayrım
yapılamaz.

---

## 3. Puanlama — **belge düzeyinde**, span düzeyinde değil

### Sorun

RadTr'nin altın etiketleri Türkçe metnin **karakter konumlarına** bağlı. Belge
İngilizceye çevrilince o konumlar anlamsızlaşır; İngilizce çıktı neye karşı
puanlanacak?

### Çözüm

Span değil, **belge düzeyinde kavram kümesi** karşılaştırılır:

```
altın(belge)     = { (kavram, kesinlik), ... }
TR-çıktı(belge)  = { (kavram, kesinlik), ... }
EN-çıktı(belge)  = { (kavram, kesinlik), ... }
```

Üçü de **çeviriden bağımsızdır** — karakter konumu yok, yalnızca kavram ve
kesinlik. Böylece fazladan altın açıklama üretmeye gerek kalmaz.

**Bedeli açıkça yazılır:** span sınırı doğruluğu ölçülmez. Ablasyonun sorusu o
olmadığı için kabul edilebilir; ama rapora "bu ölçüm span sınırı hakkında bir
şey söylemez" diye yazılır.

### Ölçütler

| kod | ne | nasıl |
|---|---|---|
| **A1** | kavram çıkarımı | belge düzeyinde P / R / F1 |
| **A2** | kesinlik ataması | eşleşen kavramlarda makro-F1 (`present`/`absent`/`uncertain`) |
| **A3** | eksen kırılımı | A2 sınıf başına ayrı — çevirinin etkisi eksenlere **eşit değil** |

⚠ **A3 zorunlu.** Tek bir ortalama, çevirinin nerede kırıldığını gizler.
İngilizce ölçümde `absent` neredeyse kusursuzken `uncertain` zayıftı; çevirinin
en çok belirsizliği bozması beklenir ve bu **sınanabilir bir tahmindir**.

---

## 4. Ölçüm kümesi

| | |
|---|---|
| belge | **56** (RadTr `test`) |
| kelime | 7.784 |
| varlık | 1.817 |
| kesinlik desteği | present 613 · absent 86 · **uncertain 128** |

Bölünme ve kilit: `reports/turkce_bolunme_dondurma.md`

`uncertain` desteği İngilizce `test-v2`dekinden (69/82) **yüksek** — belirsizlik
ekseni Türkçede daha iyi ölçülebilir.

⚠ Varlıkların %54'ü kesinlik eksenine eşlenmiyor (RadTr `Obs_Anatomy` etiketine
kesinlik vermiyor). A2/A3 yalnızca eşlenen alt kümede ölçülür ve payda yazılır.

---

## 5. Ek kontrol — geri çeviri

Türkçe metin İngilizceye çevrilip **tekrar** Türkçeye çevrildiğinde çıkarımın ne
kadar saptığı ölçülür. Bu, çeviri kaybının **üst sınırını** verir: iki çeviriden
geçmiş metin, bir çeviriden geçmişten daha kötü olmalıdır. Olmuyorsa ölçüm
düzeneğinde bir sorun var demektir.

---

## 6. Yayımlanmış tabanla karşılaştırma

Türkçe varlık çıkarımında yayımlanmış bir taban skoru **bu bölünmede**
ölçülmüştür ve karşılaştırma yapılabilir.

⚠ İki uyarı:

1. **Taban öğrenen bir model, bizimki kural tabanlı.** Bu adil bir yarış değil,
   **farklı bir soru**. Sorulacak soru *"bizimki daha iyi mi"* değil,
   *"kural tabanlı katman öğrenen bir tabanla aynı bantta mı"*.
2. Bölünme birebir devralınamazsa yayımlanmış skorla **doğrudan** karşılaştırma
   yapılamaz; kendi bölünmemizde yeniden koşulur. Bu da mümkün değilse taban
   referans değil yalnızca **büyüklük mertebesi göstergesi** olarak anılır.

---

## 7. Modelin yorumu — nerede kullanılır

Sonuç sayıları çıktıktan **sonra**, ayrışan belgeler bir modele hem Türkçe hem
İngilizce hâliyle verilir ve *"burada ne kaybolmuş"* diye sorulur.

| | |
|---|---|
| ✅ kullanılır | hata taksonomisi kurmak, hipotez üretmek |
| ⛔ kullanılmaz | skor üretmek, sonuç iddia etmek |

---

## 8. Sonuç bir sayı değil, bir **karar**

Ablasyonun çıktısı şu sorunun cevabıdır:

> **Faz 3 altın standart etiketlemesi hangi dilde yapılacak?**

Karar tablosu — ölçümden **önce** yazıldı:

| bulgu | karar |
|---|---|
| TR ≈ EN (fark küçük, eksenler tutarlı) | İngilizce devam; Türkçe veri **kritik değil**, gerekçesi kayıtlı |
| TR belirgin **üstün** | Türkçe etiketlemeye geçilir; CT-RATE Türkçe aslı öncelikli hedef olur |
| TR belirgin **düşük** ama sebep desen zayıflığı | Uzman onaylı sözlükle **tekrar** ölçülür; karar ertelenir |
| Eksenler **çelişiyor** (biri lehte biri aleyhte) | Tek karar verilmez; eksen bazlı rapor edilir |

⚠ Üçüncü satır önemli: Türkçe tarafın düşük çıkması tek başına *"Türkçe veri
gereksiz"* demek **değildir**. Desenler uzman onayından geçmediği sürece
düşüklüğün dilden mi araçtan mı geldiği ayrılamaz.

---

## 9. Bu ölçümü geçersiz kılacak şeyler

1. `test` bölümüne desen geliştirirken bakmak
2. Sonucu görüp desen/sözlük/kural değiştirmek → sürüm iptal, yeni bölünme
3. Türkçe ve İngilizce kolların **farklı** altın veriye karşı puanlanması
4. Model yorumunun sonuç hanesine yazılması

---

## 10. Bilinen sınırlar — rapora aynen geçer

| sınır | etkisi |
|---|---|
| RadTr **sentetik** (radyolog yazımı, gerçek hasta değil) | Sonuç *"RadTr benzeri Türkçe metinlerde"* diye yazılır |
| **56 belge** | Güven aralığı geniş; tek nokta tahmini sunulmaz |
| Türkçe yüzeyler **uzman onaysız** | Düşüklük dilden mi desenden mi ayrılamaz |
| Span sınırı ölçülmüyor | Belge düzeyi puanlamanın bilinen bedeli |
| **Hizalı çift yok** | RadTr'de aynı raporun insan yazımı Türkçe *ve* İngilizce hâli yok; İngilizce kol **makine çevirisi**. Çeviri hatası ile dil etkisi tam ayrılamaz — CT-RATE Türkçe aslı bu sınırı kaldırırdı |
