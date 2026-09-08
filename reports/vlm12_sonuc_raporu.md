# Astra/NLST Kohortunun Hasta Düzeyinde Bölünmesi ve Dondurulması

- **Rapor tarihi:** 8 Eylül 2026
- **Kaynak kohort:** 2.965 seri, 1.201 hasta
- **Bölünme sürümü:** `astra-split-1.0`

## Yönetici özeti

Astra/NLST kohortu, aynı hastaya ait serilerin farklı veri kümelerine düşmesini
engellemek amacıyla hasta kimliği (PID) düzeyinde bölünmüştür. Kanser etiketi
korunarak yapılan filtreleme sonrasında 2.940 seri ve 1.198 PID kalmıştır. Bu
kohort, kanser durumuna göre katmanlı biçimde train, dev ve held-out kümelerine
ayrılmıştır.

| Küme | PID | Seri | Pozitif PID | Pozitif seri | PID oranı |
|---|---:|---:|---:|---:|---:|
| Train | 838 | 2.050 | 50 | 99 | %69,9 |
| Dev | 180 | 450 | 11 | 20 | %15,0 |
| Held-out | 180 | 440 | 11 | 21 | %15,0 |
| **Toplam** | **1.198** | **2.940** | **72** | **140** | **%100,0** |

Kümeler arasında ortak PID bulunmamaktadır. Çok serili 1.016 PID'nin bütün
serileri aynı kümede tutulmuştur. Filtre sonrası hiçbir PID veya seri açıkta
kalmamıştır. Bölünme sabit tohumla yeniden üretilebilmekte ve PID listeleri
SHA-256 özetleriyle doğrulanmaktadır.

Held-out kümesinde yalnız 11 pozitif PID bulunduğundan bu veriyle duyarlılık
için bir kabul eşiği sınanamaz. Kusursuz bir sonuçta bile, 11/11 duyarlılığın
Wilson %95 güven aralığı alt sınırı %74,1'dir. Bu nedenle held-out sonuçları
nokta tahmini ve güven aralığıyla raporlanmalı, eşik temelli kabul veya ret
kararı için kullanılmamalıdır.

## 1. Amaç

Bir hastanın birden fazla görüntü serisi bulunabilir. Seriler birbirinden
bağımsızmış gibi farklı veri kümelerine dağıtılırsa aynı hastaya ait bilgiler
hem geliştirme hem değerlendirme tarafında yer alabilir. Bu durum veri
sızıntısına ve performansın olduğundan yüksek görünmesine yol açar.

Bu çalışmanın amacı:

1. kohortu tanımlı uygunluk ölçütüne göre filtrelemek,
2. aynı PID'ye ait tüm serileri tek kümede tutmak,
3. kanserli hastaların üç kümedeki dağılımını korumak,
4. held-out kümesini değişmez PID listeleriyle dondurmak,
5. bölünmenin yeniden üretilebilirliğini ve sızıntısızlığını doğrulamaktır.

## 2. Veri kaynağı ve kapsam

Kaynak dosya `astra_radiology_reports_with_labels_all.xlsx` olup 2.965 seri ve
1.201 PID içermektedir. Bölünmede yalnızca aşağıdaki alanlar kullanılmıştır:

| Alan | Kullanım amacı |
|---|---|
| `PID` | Hasta düzeyinde gruplama |
| `Seri_Anahtari` | Seri kapsamının ve benzersizliğinin denetimi |
| `Kanser_Etiketi_y` | PID düzeyi etiket ve katmanlama |
| `Censor_Time` | Uygunluk filtresi |

Rapor metni bölünme kararına dahil edilmemiştir. Metindeki bulgular, biçimsel
özellikler veya herhangi bir çıkarım sonucu örnek seçimini etkilememiştir.

## 3. Yöntem

### 3.1 Uygunluk filtresi

Aşağıdaki iki koşulu birlikte sağlayan seriler kohorttan çıkarılmıştır:

```text
Censor_Time < 1 ve Kanser_Etiketi_y = 0
```

Bu kuralla 25 kanser dışı, kısa takip süreli seri elenmiştir. Kanser etiketi 1
olan seriler takip süresinden bağımsız olarak korunmuştur. Böylece kanserli
seri sayısı filtreleme öncesinde ve sonrasında 140 olarak kalmıştır.

Filtreleme sonucu:

| Aşama | Seri | PID |
|---|---:|---:|
| Ham kohort | 2.965 | 1.201 |
| Filtre koşulunu sağlayan | 25 | 20 |
| Analize alınan | 2.940 | 1.198 |

Filtre 20 PID'ye ait 25 seriyi etkilemiş, bu PID'lerin 3'ü kohorttan tamamen
çıkmıştır. Diğer 17 PID, analize uygun en az bir serisi bulunduğu için kohortta
kalmıştır.

### 3.2 Karma etiketli PID'ler

Üç PID'de aynı hastaya ait seriler farklı kanser etiketleri taşımaktadır:
`101907`, `134575` ve `205393`.

PID düzeyi kanser etiketi, o hastaya ait seri etiketlerinin maksimumu olarak
tanımlanmıştır. Başka bir ifadeyle, hastanın en az bir serisi kanserli olarak
etiketlenmişse PID pozitif kabul edilmiştir. Bu yaklaşım belgelenmiş pozitif
bilgiyi korur. Karma etiketli PID'lerin tamamen çıkarılması pozitif PID
sayısını 72'den 69'a, held-out pozitif PID sayısını ise 11'den 10'a
düşüreceğinden tercih edilmemiştir.

### 3.3 Katmanlı hasta bölünmesi

Pozitif ve negatif PID havuzları ayrı ayrı yüzde 70 train, yüzde 15 dev ve
yüzde 15 held-out oranlarıyla bölünmüştür. Katmanlama, düşük prevalanslı
pozitif sınıfın kümeler arasındaki dağılımını korumaktadır.

| Özellik | Değer |
|---|---|
| Bölünme birimi | PID |
| Katmanlama değişkeni | PID düzeyi kanser etiketi |
| PID etiket kuralı | Seri etiketlerinin maksimumu |
| Train, dev, held-out oranı | %70, %15, %15 |
| Rastgelelik tohumu | `20260907` |
| Rastgeleleştirme | `random.Random` ile tam permütasyon |
| Yuvarlama | Python `round()` |

Sabit tohum ve sabit katman sırası kullanıldığı için aynı kaynak dosya ve aynı
kurallarla PID listeleri yeniden üretilebilir.

## 4. Sonuçlar

### 4.1 Dondurulan kümeler

| Küme | PID | Seri | Pozitif PID | Pozitif seri | SHA-256 ilk 16 karakter |
|---|---:|---:|---:|---:|---|
| Train | 838 | 2.050 | 50 | 99 | `3b6577bc816017ce` |
| Dev | 180 | 450 | 11 | 20 | `6ef7618a7e23f50e` |
| Held-out | 180 | 440 | 11 | 21 | `ed1d8faf89219530` |

Held-out kümesindeki pozitif PID prevalansı %6,1, filtrelenmiş kohortun genel
pozitif PID prevalansı %6,0'dır. Bu yakınlık katmanlamanın amaçlanan dağılımı
koruduğunu göstermektedir.

### 4.2 Veri sızıntısı denetimi

Kaynak Excel ile bölünme kilidi birbirinden bağımsız olarak karşılaştırılmıştır.

| Denetim | Sonuç |
|---|---:|
| Train ile dev ortak PID | 0 |
| Train ile held-out ortak PID | 0 |
| Dev ile held-out ortak PID | 0 |
| Birden fazla kümeye düşen PID | 0 |
| Birden fazla kümeye düşen seri | 0 |
| Atanmamış seri | 0 |
| Eksik PID | 0 |
| Fazladan PID | 0 |
| Çok serili PID | 1.016 |
| Bir PID'deki azami seri sayısı | 3 |

Aynı hastaya ait hiçbir seri farklı kümelere ayrılmamış ve filtre sonrası
kohortun tamamı tekil biçimde kapsanmıştır.

### 4.3 Yeniden üretilebilirlik

Üretim betiğinin doğrulama modu, kaynak dosyadan PID listelerini tekrar
oluşturmuş ve üç kümenin SHA-256 özetlerini dondurulan dosyayla
karşılaştırmıştır. Üç özetin tamamı eşleşmiştir.

Kilit dosyası mevcutken betik yeni çıktı yazmayı reddetmektedir. Bu koruma,
held-out üyeliğinin yanlışlıkla değiştirilmesini önlemektedir. Bölünmeye ilişkin
12 gerileme testi ile proje test takımındaki toplam 462 test başarıyla
tamamlanmıştır.

## 5. İstatistiksel değerlendirme sınırı

Birincil değerlendirme birimi PID'dir. Held-out kümesindeki 11 pozitif PID için
olası duyarlılık sonuçlarının Wilson %95 güven aralıkları aşağıdadır.

| Doğru bulunan pozitif PID | Duyarlılık | Wilson %95 güven aralığı |
|---:|---:|---:|
| 11/11 | %100,0 | %74,1 ile %100,0 |
| 10/11 | %90,9 | %62,3 ile %98,4 |
| 9/11 | %81,8 | %52,3 ile %94,9 |

Kusursuz sonuçta dahi alt sınır %80'in altında kaldığı için bu held-out kümesi
duyarlılık eşiğini doğrulamak için yeterli istatistiksel güce sahip değildir.
Duyarlılık, nokta tahmini ve güven aralığıyla birlikte verilmelidir.

Held-out kümesinde 21 pozitif seri bulunması, seri düzeyinde daha dar bir güven
aralığı izlenimi oluşturabilir. Ancak aynı hastaya ait seriler bağımsız gözlem
değildir. Seri düzeyi değerlendirme bu nedenle ikincil ve tanımlayıcı olmalı,
PID düzeyi sonucun yerine kullanılmamalıdır.

## 6. Kaynak raporların niteliği

Kohorttaki metinler rutin klinik raporlar değil, Astra tarafından NLST
görüntülerinden üretilmiş raporlardır. Bu özellik PID bölünmesini etkilemez;
çünkü bölünme metin kullanılmadan gerçekleştirilmiştir. Bununla birlikte,
raporlardan çıkarılacak bulguların yorumlanmasında veri kaynağının niteliği
dikkate alınmalıdır.

| Biçimsel gösterge | Rapor oranı |
|---|---:|
| Markdown kalın başlık | %96,8 |
| Doldurulmamış yer tutucu | %41,7 |
| `Findings` bölümü | %18,8 |
| `Impression` bölümü | %0,8 |
| `spicul*` ifadesi | %0,3 (8 rapor) |

Bu dağılım, metinlerin insan yazımı klinik raporlardan farklı bir yapıya sahip
olduğunu göstermektedir. Özellikle boş yer tutucuların yüksek,
`Impression` bölümünün ve spikülasyon ifadelerinin düşük olması, metin tabanlı
çıkarım sonuçlarının genellenebilirliği değerlendirilirken göz önünde
bulundurulmalıdır.

## 7. Sonuç ve kullanım koşulları

Astra/NLST kohortu hasta düzeyinde, kanser etiketine göre katmanlı ve yeniden
üretilebilir biçimde bölünmüş; PID listeleri `astra-split-1.0` sürümüyle
dondurulmuştur.

Held-out kümesi 180 PID ve 440 seriden oluşmaktadır. Bu kümedeki üyelik
değiştirilmemeli; model, sözlük, eşik ve istem geliştirmesi yalnız train ile dev
kümelerinde yürütülmelidir. Held-out değerlendirmesi, yöntemi ve raporlanacak
ölçütleri yazılı olarak belirlenmiş tek bir değerlendirme çalışmasında
kullanılmalıdır.

## 8. Teknik artefaktlar

| Bileşen | Dosya veya değer |
|---|---|
| Bölünme kilidi | `configs/splits_astra.json` |
| Bölünme sürümü | `astra-split-1.0` |
| Üretim ve doğrulama betiği | `scripts/59_astra_kohort_bolunmesi.py` |
| Gerileme testleri | `tests/test_vlm12_astra_bolunme.py` |
| Kaynak dosya | `astra_radiology_reports_with_labels_all.xlsx` |
| Rastgelelik tohumu | `20260907` |
| Test sonucu | 462/462 başarılı |
