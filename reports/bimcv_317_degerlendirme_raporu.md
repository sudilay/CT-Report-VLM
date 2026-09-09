# BIMCV-R 317 Serilik Kohortta Model Çıktılarının Radyoloji Raporlarıyla Değerlendirilmesi

**Tarih:** 9 Eylül 2026 · **Kohort:** 317 seri / 315 hasta
**Veri:** `bimcv-analysis/BIMCV_Sybil_Pillar_Astra_317_Clean_Results.xlsx`
**Kod:** `scripts/66_bimcv_rapor_uyumu.py`, `scripts/67_astra_rapor_karsilastirma.py`,
`scripts/68_uclu_sistem_uyumu.py`

| | Deney | Durum |
| :-- | :-- | :-- |
| **1** | Sybil ve Pillar risk skorlarının rapordaki torasik bulgularla ilişkisi | Tamamlandı |
| **2** | Astra'nın ürettiği raporların İspanyolca raporlarla karşılaştırılması | Tamamlandı |
| **3** | Üç sistemin birbiriyle ve raporla uyumu | Tamamlandı |
| **4** | Astra'nın Sybil ve Pillar kaçırmaları üzerindeki etkisi | Tamamlandı |
| **5** | İngilizce çeviride bulgu kaybı | Tamamlandı |

Kohortta patoloji, biyopsi veya takip verisi yok. İspanyolca rapor bir kanser
referans standardı değildir. Buradaki sayılar klinik duyarlılık, özgüllük veya
model geçerliliği olarak okunamaz; ölçülen şey rapor uyumudur.

---

## Ortak zemin

**Kohort.** 500 serilik havuzda 183 seride BT dosya adı ile metadata kimliği
eşleşmedi, bunlar çıkarıldı. Kalan 317 seri 315 hastaya ait; iki hastanın ikişer
serisi var. Güven aralıkları hasta düzeyinde kümeli bootstrap ile hesaplandı
(4000 tekrar, tohum 20260909).

Bu bir tarama kohortu değil, COVID döneminde toplanmış hastane kohortu.
Raporların çoğu torako-abdomino-pelvik BT ve baskın bulgu COVID pnömonisi.

**Raporlar gerçek.** 93 raporda `fecha`, 36 raporda `name` gibi de-identifikasyon
yer tutucuları, 48 raporda dikte tekrarları ve yaygın yazım hataları var; 317
raporun tamamı benzersiz. Excel'deki İngilizce sütun makine çevirisi ve hatalı
(16 raporda `metástasis` sözcüğü "goalstasis" olmuş). Bütün çıkarım İspanyolca
metinden yapıldı.

**Sınıflama.** Her rapor cümle cümle tarandı: malignite ve nodül sözlükleri,
olumsuzlama kapsamı, anatomik bölge ve zamansallık. Bölge, terime en yakın
anatomik sözcükten atandı.

*Malignite düzeyi:* not_mentioned 160, none 81, indeterminate 47, intermediate 10,
high 9, known_malignancy 6, low 4.

*Bulgusal bağlam* (bir seri birden fazla etiket alabilir):

| Bağlam | n |
| :-- | --: |
| Maligniteyle ilişkili kanıt yok | 260 |
| Toraks dışı malignite | 34 |
| Yalnız geçmiş öykü veya klinik endikasyon | 11 |
| Güncel primer akciğer kanseri kanıtı | 5 |
| Şüpheli primer pulmoner lezyon | 5 |
| Pulmoner metastaz | 5 |
| Mediastinal veya plevral malignite | 5 |
| Toraks kemik metastazı | 5 |

*Zamansallık:* 55 seride güncel bulgu, 30 seride takip, 10 seride öykü, 5 seride
klinik endikasyon.

Sybil ve Pillar gelecekteki akciğer kanseri riskini hedefler. Timoma, toraks
iskelet metastazı, başka primerden akciğer metastazı ve lobektomi öyküsü ayrı
katmanlarda tutuldu, tek hedefte birleştirilmedi.

Otomatik sınıflama tek başına kullanılmadı. Onkoloji sözcüğü geçip kanser kanıtı
bulunmadığı değerlendirilen raporların tamamı elle okundu ve
`bimcv_317_adjudikasyon.csv` dosyasına kaydedildi.

---

# 1. Sybil ve Pillar risk skorlarının rapor bulgularıyla ilişkisi

Soru: 0,20 eşiğinin altında ve üstünde kalan serilerde İspanyolca raporda hangi
torasik malignite kanıtı var? Eşik analiz öncesinde sabitlendi ve korundu.

## 1.1 Eşik tabloları

Hücreler rapor kanıtı ile skor konumunu birlikte adlandırır, tanısal doğruluk
tablosu değildir.

**Dar hedef: güncel primer akciğer kanseri veya şüpheli primer pulmoner lezyon (n = 8)**

| | Sybil | Pillar |
| :-- | --: | --: |
| Rapor kanıtı var / skor ≥ 0,20 | 3 | 3 |
| Rapor kanıtı var / skor < 0,20 | 5 | 5 |
| Rapor kanıtı yok / skor ≥ 0,20 | 13 | 91 |
| Rapor kanıtı yok / skor < 0,20 | 296 | 218 |

**Geniş torasik malignite (akciğer, mediasten/plevra, toraks kemiği; n = 21)**

| | Sybil | Pillar |
| :-- | --: | --: |
| Rapor kanıtı var / skor ≥ 0,20 | 5 | 4 |
| Rapor kanıtı var / skor < 0,20 | 16 | 17 |
| Rapor kanıtı yok / skor ≥ 0,20 | 11 | 90 |
| Rapor kanıtı yok / skor < 0,20 | 285 | 206 |

Sybil serilerin %5,0'ini (16 seri), Pillar %29,7'sini (94 seri) eşiğin üzerinde
skorladı. İki modelin sıra korelasyonu 0,437 (Spearman).

## 1.2 Sıralama ilişkisi

| Hedef | Model | n+ | AUC | %95 GA (hasta kümeli) |
| :-- | :-- | --: | --: | :-- |
| Dar hedef | Sybil 1 yıl | 8 | 0,690 | 0,431 – 0,921 |
| Dar hedef | Pillar 1 yıl | 8 | 0,685 | 0,526 – 0,843 |
| Geniş torasik | Sybil 1 yıl | 21 | 0,588 | 0,434 – 0,737 |
| Geniş torasik | Pillar 1 yıl | 21 | 0,454 | 0,329 – 0,587 |

Dört tahminden üçünde güven aralığı 0,5 değerini içeriyor. Aynı skorlar, hedef
kümesi değiştikçe 0,454 ile 0,690 arasında AUC veriyor.

1 ve 6 yıllık skorlar birbirine çok yakın AUC üretiyor. Bu, uygulanan izotonik
kalibrasyonun beklenen davranışı; veri veya eşleme hatası göstergesi değil.

## 1.3 Hekim etiketleriyle keşif analizi

Excel'deki 95 bulgu etiketi bağımsız uzman değerlendirmesi değil, raporlardan
otomatik türetilmiş zayıf etiketler. En az 10 pozitifi olan etiketler alındı,
88 etiket-model çifti sınandı, Benjamini-Hochberg düzeltmesi uygulandı. 12 çift
q < 0,05 eşiğini geçti.

| Etiket | n | Model | AUC | %95 GA | q |
| :-- | --: | :-- | --: | :-- | --: |
| Buzlu cam paterni | 120 | Pillar | 0,657 | 0,596 – 0,716 | <0,001 |
| Pnömoni | 101 | Sybil | 0,642 | 0,575 – 0,707 | 0,002 |
| Cerrahi | 25 | Pillar | 0,275 | 0,175 – 0,383 | 0,005 |
| Değişmemiş | 60 | Pillar | 0,353 | 0,275 – 0,438 | 0,009 |
| COVID-19 | 88 | Sybil | 0,624 | 0,558 – 0,691 | 0,011 |
| Konsolidasyon | 37 | Sybil | 0,666 | 0,571 – 0,756 | 0,015 |

Pillar skoru bazı yaygın kardiyopulmoner bulgularla, Sybil skoru pnömoni ve
konsolidasyon etiketleriyle ilişkili çıktı. Bu ilişkinin modelin bu bulgulara
odaklanmasından mı, yoksa hasta seçimi ve protokol gibi karıştırıcılardan mı
kaynaklandığı bu analizle belirlenemez.

## 1.4 Örnek seriler

Düşük skor, modelin lezyonu görmediğini tek başına göstermez.

| # | Sybil | Pillar | Rapordaki ifade |
| --: | --: | --: | :-- |
| 192 | 0,002 | 0,089 | LSD'de 23 × 11 mm tümöral kitle devam ediyor |
| 90 | 0,011 | 0,054 | Akciğer neoplazisinde radyolojik kötüleşme, spiküle nodül 1,8 → 2,1 cm |
| 16 | 0,011 | 0,150 | LID'de spiküle nodül 6 × 5 → 14 × 12 mm, ayrıca D11 ve D8'de litik lezyon |
| 25 | 0,043 | 0,465 | Sol alt lob apikal segmentte 8 × 6 cm heterojen kitle |
| 63 | 0,442 | 0,672 | Sağ üst lobda 4,8 × 3 cm spiküle konturlu kitle |
| 134 | 0,256 | 0,190 | LID üst segmentte 4,2 cm tümöral görünümlü kitle |

Rapor kanıtı olmadığı halde eşik üstü skor alan serilerde Sybil tarafında COVID
ve pnömoni etiketleri, Pillar tarafında sternotomi, kateter, kardiyomegali ve
amfizem etiketleri yoğunlaşıyor.

## 1.5 Hüküm

0,20 eşiğinde Sybil ve Pillar skorları, rapordan türetilen malignite kanıtıyla
sınırlı uyum gösterdi. Pozitif seri sayısı model karşılaştırmasına elvermiyor.

---

# 2. Astra raporlarının İspanyolca raporlarla karşılaştırılması

Her iki tarafa aynı bulgu ontolojisi ve aynı olumsuzlama mantığı uygulandı.
Astra çıktısı organ başlıklarına ayrıştırıldı, yalnız torasik bölümler alındı,
toraks dışı organdan söz edip hiçbir torasik yapıya değinmeyen cümleler elendi.
Astra'nın metni şablon olduğu için bu adım gerekli: ham metinde "mass" 306
raporda, "effusion" 314 raporda geçiyor ve çoğu olumsuz ifade.

Sayılar tek başına kullanılmadı. Her uyuşmazlık kategorisinden örnekler ve odak
lezyon karşılaştırmasının tamamı iki dilde elle okundu.

## 2.1 Bulgu düzeyi uyum

Son iki sütun, İspanyolca raporun pozitif ve negatif olduğu serilerde Astra'nın
aynı yönde olma oranı.

| Bulgu | İsp. + | Astra + | İkisi + | Yalnız İsp. | Yalnız Astra | Poz. uyum | Neg. uyum |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| Plevral efüzyon | 47 | 86 | 37 | 10 | 49 | %78,7 | %81,9 |
| Buzlu cam | 93 | 137 | 64 | 29 | 73 | %68,8 | %67,4 |
| Konsolidasyon | 64 | 82 | 35 | 29 | 47 | %54,7 | %81,4 |
| Fibrozis | 25 | 53 | 10 | 15 | 43 | %40,0 | %85,3 |
| Kitle | 18 | 29 | 7 | 11 | 22 | %38,9 | %92,6 |
| Kardiyomegali | 26 | 14 | 8 | 18 | 6 | %30,8 | %97,9 |
| Amfizem | 26 | 21 | 6 | 20 | 15 | %23,1 | %94,8 |
| Adenopati | 66 | 24 | 12 | 54 | 12 | %18,2 | %95,2 |
| Nodül | 56 | 20 | 8 | 48 | 12 | %14,3 | %95,4 |
| Atelektazi | 65 | 24 | 11 | 54 | 13 | %16,9 | %94,8 |
| Plevral kalınlaşma | 6 | 21 | 1 | 5 | 20 | %16,7 | %93,6 |
| Bronşektazi | 38 | 10 | 6 | 32 | 4 | %15,8 | %98,6 |
| Pnömotoraks | 0 | 0 | 0 | 0 | 0 | yok | %100 |

Yaygın ve göze çarpan bulgularda uyum daha yüksek: plevral efüzyon %78,7, buzlu
cam %68,8, konsolidasyon %54,7. Sayılabilir ve konum gerektiren bulgularda
düşük: nodül %14,3, bronşektazi %15,8, plevral kalınlaşma %16,7, atelektazi
%17,9, adenopati %18,2.

Astra buzlu cam, fibrozis, plevral kalınlaşma ve efüzyonu, İspanyolca raporun
söylemediği serilerde de bildiriyor.

## 2.2 Odak lezyon: taraf, boyut, nitelik

İspanyolca raporda 68 seride nodül veya kitle var, Astra'da 46 seride var,
ikisinin kesiştiği seri sayısı 21.

Her iki tarafın da lezyon tarafını belirttiği 10 seri elle okundu: 6 seride
taraf uyuşuyor, 3 seride taraf ters, 1 seride yaygınlık farklı (rapor iki
taraflı diyor, Astra tek taraf).

| # | İspanyolca rapor | Astra | Fark |
| --: | :-- | :-- | :-- |
| 63 | Sağ üst lobda 4,8 × 3 cm **spiküle** kitle | Sol üst lobda 4 × 3 cm **iyi sınırlı, lobüle** kitle | Taraf ters, morfoloji ters yönde |
| 114 | **Sol** üst lobda 13 mm kaviter nodül | **Sağ** akciğerde çok sayıda nodüler opasite | Taraf ters |
| 11 | **Sol** üst lobda milimetrik nodüller | **Sağ** akciğer ve mediastende geniş kitle | Taraf ters, lezyon raporda yok |
| 204 | Sağ alt lobda **4 mm** solid nodül | Sağ plevral boşlukta **geniş** lobüle kitle | Boyut ve nitelik uyumsuz |
| 25 | Sol alt lobda 8 × 6 cm kitle | Sol alt lobda 5 × 4 cm kitle | Taraf ve lob doğru, boyut düşük |
| 90 | Sol segment 6'da spiküle nodül, 2,1 cm | Sol alt lobda kitle | Taraf ve lob doğru |

Seri 63'te spiküle kontur malignite göstergesi; Astra'nın yazdığı "iyi sınırlı,
lobüle" ters yönde okunur.

İki tarafın da ölçü verdiği 4 seride medyan mutlak fark 10 mm. Ayrı olarak 3
seride rapor 10 mm veya altında lezyon tarif ederken Astra "geniş kitle" demiş
(seri 204: 4 mm, seri 307: 7 mm, seri 217: 10 mm).

## 2.3 Raporda karşılığı olmayan lezyon bildirimleri

Astra'nın kitle bildirdiği 29 serinin 7'sinde rapor da kitle, 8'inde nodül
tarif ediyor. Kalan 14 seride raporda hiçbir odak lezyon yok.

| # | Astra | İspanyolca rapor |
| --: | :-- | :-- |
| 34 | Sol üst lobda 4 × 3 cm iyi sınırlı kitle | Pulmoner emboli, orta lob atelektazisi, sağ üst lobda konsolidasyon |
| 100 | Sağ alt lobda iyi sınırlı homojen kitle | Akciğer parankiminde metastaz şüpheli lezyon görülmedi |
| 129 | Arka mediastende yumuşak doku kitlesi | Amfizem, hava boşluğu konsolidasyonu yok |
| 65 | Sol üst lobda 3,5 × 2,8 cm nekrozlu lobüle kitle | Lingula ve orta lobda iki milimetrik nodül, değişmemiş |

Ters yönde: seri 33'te rapor sol üst lob ön segmentte 12 × 10 mm soliter solid
nodül tarif ederken Astra "buzlu cam alanı veya nodül yok" yazmış.

## 2.4 Kapsam ve şablon

Astra, göğüs BT'sinden göremeyeceği organlar için de bölüm yazıyor ve
çoğunlukla "normal" diyor.

| | Seri | Oran |
| :-- | --: | --: |
| Abdomen bölümü yazılmış | 317 | %100 |
| Meme bölümü yazılmış | 317 | %100 |
| Tiroid bölümü yazılmış | 313 | %98,7 |
| `[Insert ...]` yer tutucusu kalmış | 119 | %37,5 |
| "Prepared by" imza satırı | 113 | %35,6 |
| `[Your Name]` yer tutucusu | 43 | %13,6 |
| "informational purposes only" feragati | 38 | %12,0 |

## 2.5 Hüküm

Uyum bulgu tipine göre değişiyor: yaygın parankim ve plevra bulgularında orta,
sayılabilir ve konum gerektiren bulgularda düşük.

Odak lezyonlarda iki tekrarlayan fark elle doğrulandı: lezyonun tarafının ters
verilmesi, lezyon boyutu ile niteliğinin raporla uyuşmaması. Fark iki yönlü;
Astra hem raporda bulunan lezyonu atlıyor hem de raporda bulunmayan lezyon
tarif ediyor.

Taraf karşılaştırması 10 seriye dayanıyor, tek başına oran olarak sunulamaz.
Tarafın uyuşması aynı lezyonun tarif edildiği anlamına da gelmez: seri 204'te
iki rapor da sağ diyor, biri 4 mm nodül diğeri geniş kitle tarif ediyor.

---

# 3. Üç sistemin birbiriyle ve raporla uyumu

Bu bölüm Astra'nın metin bulgusunu, Sybil ve Pillar'ın eşik üstü skorunu ve
İspanyolca raporu aynı tabloda karşılaştırır. Karar birimi ortaktır: seride
odak akciğer lezyonu (nodül veya kitle) işaret edilmiş mi?

Sybil ve Pillar gelecekteki kanser riskini tahmin eder, Astra ve rapor güncel
bulguyu yazar. Bu ikisinin birebir örtüşmesi baştan beklenmez; aşağıdaki sayılar
betimleyicidir.

## 3.1 Her sistem kaç seride lezyon işaret ediyor

| Sistem | Seri | Oran |
| :-- | --: | --: |
| İspanyolca rapor (nodül/kitle) | 68 | %21,5 |
| Astra (nodül/kitle) | 46 | %14,5 |
| Pillar (skor ≥ 0,20) | 94 | %29,7 |
| Sybil (skor ≥ 0,20) | 16 | %5,0 |

## 3.2 İkili uyum

Ham örtüşme oranı yanıltıcıdır: iki sistem de nadiren "var" diyorsa, ikisi de
"yok" dediği için oran yükselir. Şansa düşen uyum çıkarıldığında kalan değer
kappadır. Kappa 0 ise uyum şans düzeyindedir, 1 ise tam uyumdur.

| Çift | İkisi "var" | Yalnız 1. | Yalnız 2. | Ham örtüşme | Kappa | %95 GA |
| :-- | --: | --: | --: | --: | --: | :-- |
| Rapor – Astra | 21 | 47 | 25 | %77,3 | **0,236** | 0,108 – 0,360 |
| Sybil – Pillar | 11 | 5 | 83 | %72,2 | **0,124** | 0,041 – 0,215 |
| Astra – Sybil | 6 | 40 | 10 | %84,2 | 0,128 | 0,000 – 0,261 |
| Rapor – Sybil | 7 | 61 | 9 | %77,9 | 0,093 | −0,005 – 0,200 |
| Rapor – Pillar | 25 | 43 | 69 | %64,7 | 0,079 | −0,031 – 0,191 |
| Astra – Pillar | 18 | 28 | 76 | %67,2 | 0,077 | −0,026 – 0,181 |

Ham örtüşmenin neden kullanılamayacağı Astra–Sybil satırında görünüyor: listenin
en yüksek ham örtüşmesi (%84,2) burada, çünkü Sybil serilerin yalnız %5'ine
"var" diyor ve iki sistem çoğunlukla "yok" konusunda birleşiyor. Şans düzeltmesi
yapılınca kappa 0,128'e iniyor ve güven aralığının alt sınırı sıfıra dayanıyor.

Altı çiftten yalnız ikisinde güven aralığı sıfırın üstünde kalıyor:

- **Rapor – Astra: kappa 0,236.** Zayıf ama şans düzeyinin üstünde. Raporla
  gerçekten ilişkili tek çıktı Astra'nın metni.
- **Sybil – Pillar: kappa 0,124.** Sıfırın hemen üstünde. İki model aynı hedefi
  paylaşmasına rağmen aynı hastaları işaretlemiyor.

Kalan dört çiftte (Astra–Sybil, Rapor–Sybil, Rapor–Pillar, Astra–Pillar) güven
aralığı sıfıra dayanıyor veya sıfırı içeriyor; bu verilerle şans düzeyinden
ayırt edilemiyorlar.

## 3.3 Sürekli skorlarla bakıldığında

Eşiği kaldırıp ham skorlara bakınca tablo değişmiyor.

| Ölçüm | Değer |
| :-- | --: |
| Sybil – Pillar skor korelasyonu (Spearman) | 0,437 |
| Astra'nın lezyon dediği serilerde Sybil skorunun ayırt etme gücü (AUC) | 0,591 |
| Astra'nın lezyon dediği serilerde Pillar skorunun ayırt etme gücü (AUC) | 0,554 |
| Rapor lezyonu için Sybil AUC | 0,557 |
| Rapor lezyonu için Pillar AUC | 0,542 |

Skor medyanları, Astra'nın lezyon dediği ve demediği seriler arasında ayrışmıyor:

| Model | Astra "lezyon var" | Astra "lezyon yok" |
| :-- | --: | --: |
| Sybil | 0,0115 | 0,0109 |
| Pillar | 0,1149 | 0,1013 |

## 3.4 Raporda lezyon olan serilerde kaç sistem işaret ediyor

Raporda odak lezyon tarif edilen 68 seri:

| Kaç sistem işaretledi | Seri | Oran |
| :-- | --: | --: |
| Hiçbiri | 31 | %45,6 |
| Yalnız biri | 25 | %36,8 |
| İkisi | 8 | %11,8 |
| Üçü birden | 4 | %5,9 |

Raporda odak lezyon tarif edilmeyen 249 seri:

| Kaç sistem işaretledi | Seri | Oran |
| :-- | --: | --: |
| Hiçbiri | 161 | %64,7 |
| Yalnız biri | 73 | %29,3 |
| İkisi | 15 | %6,0 |
| Üçü birden | 0 | %0 |

Sistem başına dağılım:

| Sistem | Raporda lezyon olan 68 seride işaretlediği | Raporda lezyon olmayan seride işaretlediği |
| :-- | --: | --: |
| Pillar | 25 | 69 |
| Astra | 21 | 25 |
| Sybil | 7 | 9 |

## 3.5 Bu tablodan çıkan anlam

**Sistemler aynı hastaları işaretlemiyor.** Altı ikili karşılaştırmanın dördünde
uyum şans düzeyinden ayırt edilemiyor. Uyumun şans üstünde kaldığı iki yer var
ve ikisi de zayıf: Astra ile rapor (0,236), Sybil ile Pillar (0,124).

**Aynı hedefi paylaşan iki model bile birbirini tutmuyor.** Sybil ve Pillar aynı
soruyu yanıtlamak üzere geliştirilmiş olmasına rağmen 0,20 eşiğinde 11 seride
birleşiyor; Sybil'in işaretlediği 16 serinin 11'ini Pillar da işaretliyor, ama
Pillar'ın işaretlediği 94 serinin 83'ünü Sybil işaretlemiyor. Skor düzeyinde
korelasyon 0,437 ile orta düzeyde; yani iki model bir miktar aynı yöne bakıyor,
fakat eşik konulduğunda aynı hastalara varmıyor.

**Rapordaki lezyonların yaklaşık yarısını hiçbir sistem işaretlemiyor.** 68
serinin 31'inde (%45,6) üç sistem de sessiz kalıyor. Üçünün birden işaretlediği
seri sayısı 4.

**Uzlaşıya dayalı bir kullanım bu kohortta işlemiyor.** Üç sistemin ortak
kararını almak 4 seri bırakır; hepsini birleştirmek ise raporda lezyon olmayan
88 seriyi de listeye sokar. Sistemler birbirini doğrulayacak biçimde
davranmıyor.

**Astra ile skorlar farklı şeyler ölçüyor gibi davranıyor.** Astra'nın lezyon
dediği serilerde Sybil skorunun medyanı 0,0115, demediği serilerde 0,0109.
Astra'nın metin çıktısı ile risk skorları arasında bu veride kullanılabilir bir
bağ görünmüyor.

---

# 4. Astra'nın Sybil ve Pillar kaçırmaları üzerindeki etkisi

Soru: skorun eşiği geçemediği ama raporda lezyon tarif edilen serilerde Astra
devreye girse fayda sağlar mı? Referans, İspanyolca raporda odak lezyon (nodül
veya kitle) bulunan 68 seri.

## 4.1 Kaçırılanlarda kazanç ve bedeli

| | Sybil | Pillar |
| :-- | --: | --: |
| Raporda lezyon var, skor eşiğin altında | 61 | 43 |
| Bunlardan Astra'nın işaretlediği | 16 (%26,2) | 11 (%25,6) |
| Skorun doğru olarak sessiz kaldığı seri | 240 | 180 |
| Bunlardan Astra'nın işaretlediği | 24 (%10,0) | 17 (%9,4) |

Sistem birleştirilirse:

| | Yalnız skor | Skor veya Astra |
| :-- | :-- | :-- |
| Sybil: yakalanan / yanlış işaret | 7/68 · 9 | 23/68 · 33 |
| Pillar: yakalanan / yanlış işaret | 25/68 · 69 | 36/68 · 86 |

Sybil için yakalama 7'den 23'e çıkıyor, yanlış işaret 9'dan 33'e. Pillar için
yakalama 25'ten 36'ya, yanlış işaret 69'dan 86'ya çıkıyor.

## 4.2 Kurtarılan seriler aynı lezyonu mu tarif ediyor

Ham sayı tek başına yeterli değil: iki sistemin aynı seride "lezyon var" demesi,
aynı lezyondan söz ettikleri anlamına gelmiyor. Sybil'in kaçırıp Astra'nın
işaretlediği 16 serinin tamamı iki dilde okundu.

| Değerlendirme | Seri | Hangileri |
| :-- | --: | :-- |
| Aynı lezyon, taraf ve boyut uyumlu | 5 | 25, 28, 90, 120, 184 |
| Farklı lezyon tarif edilmiş | 5 | 11, 65, 204, 217, 307 |
| Belirsiz, eşleştirilemedi | 6 | 43, 60, 81, 102, 105, 182 |

Farklı lezyon örnekleri:

| # | İspanyolca rapor | Astra |
| --: | :-- | :-- |
| 11 | Sol üst lobda milimetrik nodüller, değişmemiş | Sağ akciğer ve mediastende geniş kitle |
| 65 | Lingula ve orta lobda iki milimetrik nodül | Sol üst lobda 3,5 × 2,8 cm nekrozlu kitle |
| 204 | Sağ alt lobda 4 mm solid nodül | Sağ plevral boşlukta geniş lobüle kitle |
| 217 | Retrokaval pretrakeal mediastinal kitle 5,1 × 4,1 cm | Sol hemitoraksı dolduran geniş kitle |
| 307 | Bilateral küçük nodüller, en belirgini 6 mm | Sol akciğerde geniş kitle |

## 4.3 Hüküm

Astra, skorun kaçırdığı serilerin dörtte birinde lezyon bildiriyor. Elle
doğrulandığında bu 16 serinin 5'inde iki rapor aynı lezyonu tarif ediyor,
5'inde farklı lezyon tarif ediliyor, 6'sı eşleştirilemiyor.

Bedel tarafında, skorun doğru olarak sessiz kaldığı serilerin yaklaşık %10'unda
Astra lezyon bildiriyor. Sybil için oran şöyle: 16 ek işaret karşılığında 24 ek
yanlış işaret.

Bu veriyle Astra'nın bir kurtarma katmanı olarak yararı gösterilemiyor. Ek
yakalamaların çoğunluğu doğrulanamıyor ve ek yanlış işaret sayısı ek doğru
işaret sayısından fazla.

---

# 5. İngilizce çeviride bulgu kaybı

Excel'deki İngilizce sütun, İspanyolca raporun makine çevirisidir. İki sütun
aynı içeriği taşıdığı için aradaki fark doğrudan çeviri kaybını verir.

## 5.1 Terimlerin ne kadarı doğru çevrilmiş

Yirmi radyoloji terimi seçildi. Terimin geçtiği her rapor için İngilizce
karşılığın durumu dört kategoriye ayrıldı:

- **Doğru çevrilmiş:** yerleşik İngilizce terim metinde var (`ground-glass`,
  `pleural effusion`, `adenopathy`).
- **İspanyolca kalmış:** sözcük hiç çevrilmemiş, olduğu gibi bırakılmış
  (`nodulo`, `hiliar`, `parenquima`).
- **Bozuk terime çevrilmiş:** bir karşılık üretilmiş ama doğru terim değil
  (`tangled glass`, `pleural spill`, `hiliary`, `goalstasis`).
- **Karşılığı yok:** kavram İngilizce metinde hiçbir biçimde geçmiyor.

Raporda doğru terim bir kez bile geçiyorsa o rapor "doğru" sayıldı.

**Toplam 1.380 terim geçişi:**

| Durum | Geçiş | Oran |
| :-- | --: | --: |
| Doğru çevrilmiş | 856 | **%62,0** |
| Bozuk terime çevrilmiş | 357 | **%25,9** |
| Karşılığı yok | 119 | %8,6 |
| İspanyolca kalmış | 48 | %3,5 |

Yani terimlerin yaklaşık üçte biri (%25,9 + %8,6 + %3,5 = %38,0) İngilizce
metinde doğru biçimde bulunamıyor. Bunun büyük kısmı bilginin kaybolması değil,
**yanlış sözcükle yazılması**.

## 5.2 Terim bazında döküm

| Terim | İspanyolca | Rapor | Doğru | Bozuk | İsp. kalmış | Yok | Doğru oranı |
| :-- | :-- | --: | --: | --: | --: | --: | --: |
| Buzlu cam | vidrio deslustrado | 110 | 0 | 99 | 0 | 11 | **%0** |
| Perikardiyal efüzyon | derrame pericárdico | 38 | 1 | 37 | 0 | 0 | **%3** |
| Hiler bölge | hiliar / hilio | 112 | 8 | 57 | 21 | 26 | **%7** |
| Plevral efüzyon | derrame pleural | 185 | 49 | 133 | 0 | 3 | **%26** |
| Metastaz | metástasis | 26 | 8 | 18 | 0 | 0 | **%31** |
| Apeks | vértice | 9 | 3 | 0 | 5 | 1 | %33 |
| Nodül | nódulo | 124 | 64 | 13 | 19 | 28 | %52 |
| Fissür | cisura | 23 | 16 | 0 | 2 | 5 | %70 |
| Amfizem | enfisema | 45 | 37 | 0 | 0 | 8 | %82 |
| Granülom | granuloma | 19 | 16 | 0 | 0 | 3 | %84 |
| Parankim | parénquima | 136 | 119 | 0 | 1 | 16 | %88 |
| Kalınlaşma | engrosamiento | 84 | 77 | 0 | 0 | 7 | %92 |
| Bronşektazi | bronquiectasias | 48 | 45 | 0 | 0 | 3 | %94 |
| Konsolidasyon | consolidación | 69 | 67 | 0 | 0 | 2 | %97 |
| Konsolidasyon | condensación | 38 | 37 | 0 | 0 | 1 | %97 |
| Kitle | masa | 41 | 40 | 0 | 0 | 1 | %98 |
| Adenopati | adenopatías | 172 | 169 | 0 | 0 | 3 | %98 |
| Atelektazi | atelectasia | 74 | 73 | 0 | 0 | 1 | %99 |
| Neoplazi | neoplasia | 22 | 22 | 0 | 0 | 0 | %100 |
| Spiküle | espiculado | 5 | 5 | 0 | 0 | 0 | %100 |

Bozulma seçici: 12 terim raporların %80'inden fazlasında doğru çevrilmiş, beş
terim yarısından azında. Kötü çevrilenlerin dördü bu kohortun en sık bulguları.

## 5.3 Bozuk çeviriler nasıl görünüyor

**Buzlu cam (110 rapor, doğru çeviri 0).** Çeviri tek terim için 29 farklı biçim
üretmiş: tangled glass 41, ranting glass 14, tired glass 6, rant glass 4,
frosted glass 4, rantless glass 2, grazed glass 2, peripheral glass 2, glass
areas 2; tenstled, shed, nodulous, tensforted, grated, sliced, tuning, mild gibi
19 biçim birer kez. 11 raporda "glass" sözcüğü hiç geçmiyor. En sık kullanılan
karşılık bile (tangled glass) doğru terim değil.

**Plevral efüzyon (185 rapor, doğru çeviri 49).** "derrame" ağırlıklı olarak
**"spill"** (dökülme) diye çevrilmiş: 153 raporda "spill", 49 raporda
"effusion". En sık kalıp "pleural spill" (74 rapor).

**Hiler bölge (112 rapor, doğru çeviri 8).** Baskın karşılık uydurma bir sözcük:
"hiliary" 54 rapor. 26 raporda karşılık hiç yok, 21 raporda İspanyolca kök
çevrilmeden kalmış ("hiliomediastinicas", "hilio").

**Perikardiyal efüzyon (38 rapor, doğru çeviri 1).** Sıfat bozulmuş:
"pericardial" yerine "pericardic".

**Metastaz (26 rapor, doğru çeviri 8).** Terim yedi ayrı uydurma biçime
dönüşmüş: goalstasis 11, goalstastosis, goalstasic, goalstatic, goalstase,
goalstastis, tastasis.

**Nodül (124 rapor, doğru çeviri 64).** 19 raporda sözcük İspanyolca kalmış,
13 raporda uydurma veya yanlış terim kullanılmış ("nodulous", "nodulum" ve dört
raporda "nodes", yani lenf düğümü), 28 raporda karşılık yok.

317 raporun **148'inde** (%46,7) en az bir İspanyolca sözcük çevrilmeden kalmış;
en sık `lobulo` (100 rapor), `toracico` (23), `nodulo` (21).

## 5.4 Bunun çıkarıma etkisi

Terim bozulmasının pratik sonucu, İngilizce metin üzerinden bulgu çıkarmaya
çalışıldığında görülüyor. Aynı bulgu ontolojisi üç ayrı sözlükle uygulandı:

① standart İngilizce radyoloji terimleri · ② çevirinin ürettiği bozuk terimler
de eklenmiş hali · ③ kavramı işaret eden herhangi bir sözcük

| Sözlük | Bulunamayan bulgu | Oran |
| :-- | --: | --: |
| ① Standart terim | 293 / 619 | %47,3 |
| ② Bozuk terimler eklenince | 116 / 619 | %18,7 |
| ③ En geniş arama | 61 / 619 | %9,9 |

Okunuşu: standart terimlerle çalışan bir çıkarım bulguların **%47,3'ünü**
göremez. Çevirinin ürettiği bozuk sözcükler sözlüğe elle eklenirse kayıp
%18,7'ye iner. Kavramın metinde hiçbir biçimde bulunmadığı, yani bilginin
gerçekten yok olduğu oran **%9,9**.

## 5.5 Hüküm

Terimlerin %62'si doğru çevrilmiş, %26'sı yanlış sözcükle yazılmış, %9'unun
karşılığı yok, %3'ü İspanyolca kalmış.

Çevirinin ürettiği hata üç türlü: sözcüğü İspanyolca bırakmak, var olmayan bir
sözcük uydurmak (hiliary, goalstasis, tangled glass), ve doğru görünen ama
yanlış olan bir terime çevirmek (derrame → spill, pericárdico → pericardic,
nódulo → nodes). Üçüncüsü en tehlikelisi: metin akıcı İngilizce görünüyor ama
klinik içerik yanlış.

İngilizce sütun bu haliyle çıkarım için kullanılamaz. Bu raporun bütün çıkarımı
İspanyolca metinden yapılmıştır.

---

## Sınırlılıklar

Kohortta patoloji, biyopsi veya takip verisi yok. Radyoloğun görmediği veya
yazmadığı bir bulgu bu analizde de yok görünür.

Pozitif seri sayısı dar hedefte 8, geniş hedefte 21. AUC değerleri betimleyici.

Hekim etiket matrisi olumsuzlamaya duyarsız görünüyor: raporunda "no se observan
nódulos" yazan serilerde `nodule` etiketi işaretlenmiş. Etiketler yalnız keşif
amacıyla kullanıldı.

Modeller asemptomatik düşük doz tarama BT'si için geliştirildi; buradaki seriler
semptomatik hastane hastalarına ait. Sonuçlar tarama performansı hakkında bilgi
vermez.

Deney 3'te Sybil ve Pillar gelecekteki risk, Astra ve rapor güncel bulgu
bildirir. Bu iki tür çıktının birebir örtüşmesi beklenmez; düşük uyum tek
başına herhangi bir sistemin kusuru sayılamaz. Kappa değerleri 0,20 eşiğine
bağlıdır, başka eşikte değişir.

Deney 2 iki metin arasındaki karşılaştırmadır, görüntüyle doğrulama yapılmadı:
bir uyuşmazlıkta hangi tarafın haklı olduğu belirlenemez. İspanyolca raporlar
önceki tetkike gönderme yapan ifadeler ve klinik öykü içeriyor; Astra bunları
göremez, bu tür farklar model hatası sayılamaz. Odak lezyon karşılaştırması 23,
taraf karşılaştırması 10 seriye dayanıyor. Bulgu sözlükleri iki dilde eşdeğer
kabul edildi; "condensación" ile "consolidation" gibi eşleştirmeler tam
örtüşmeyen kullanımlar içerebilir.

---

## Genel değerlendirme

**Kohort.** 317 seri, 315 hasta. Raporlarda odak akciğer lezyonu 68 seride tarif
edilmiş. Malignite olarak nitelenenler dar tanımla 8, geniş torasik tanımla 21
hasta. Ayrıca 34 hastada malignite toraks dışında, 11 hastada yalnız öyküde.

**Sybil ve Pillar.** 0,20 eşiğinde rapor bulgusuyla uyum sınırlı. Sybil 16,
Pillar 94 seriyi eşik üstü skorladı. AUC'ler 0,45 ile 0,69 arasında ve dört
tahminden üçünde güven aralığı 0,5'i içeriyor.

**Astra.** Uyum bulgu tipine göre değişiyor: plevral efüzyon %78,7 ve buzlu cam
%68,8 iken nodül %14,3, atelektazi %16,9. Odak lezyonlarda taraf hatası ile
boyut ve nitelik uyumsuzluğu var; kitle bildirdiği 29 serinin 14'ünde raporda
hiç odak lezyon yok. Göremeyeceği organlar için bölüm yazıyor (abdomen %100) ve
raporların %37,5'inde şablon yer tutucusu doldurulmadan kalmış.

**Üç sistem birlikte.** Altı ikili karşılaştırmanın dördünde uyum şans
düzeyinden ayırt edilemiyor; şansın üstündeki ikisi de zayıf (Astra ile rapor
0,236, Sybil ile Pillar 0,124). Raporda lezyon olan 68 serinin 31'inde (%45,6)
üç sistem de sessiz, üçünün birden işaretlediği seri 4.

**Astra kurtarma katmanı olarak.** Skorun kaçırdığı serilerin dörtte birinde
lezyon bildiriyor, ancak elle okunan 16 kurtarmanın yalnız 5'inde iki rapor aynı
lezyonu tarif ediyor. Karşılığında 24 ek yanlış işaret geliyor.

**İngilizce çeviri.** Standart radyoloji terimleriyle bulguların %47,3'ü
bulunamıyor; kavramın metinde hiç geçmediği oran %9,9. Buzlu cam 110 raporda
tarif edilmiş, doğru terim hiçbirinde yok.

**Ana çıkarım.** Bu kohortta üç sistemin çıktıları ne raporla ne birbirleriyle
kullanılabilir düzeyde örtüşüyor. Bu, modellerin geçerliliği hakkında bir hüküm
değildir: patoloji ve takip verisi yok, pozitif seri sayısı 8 ile 21 arasında,
kohort tarama dışı bir hastane kohortu.

Doğrudan kullanılabilir üç sonuç: İngilizce çeviri sütunu çıkarımda
kullanılmamalı; Astra'nın taraf hatası, uydurma lezyon, kapsam dışı organ ve
şablon sızıntısı düzeltilebilir üretim kusurlarıdır; üç sistemi birleştirerek
kullanmak bu kohortta fayda üretmiyor.

**İşletim maliyeti.** Seri başına medyan süre: Pillar 1,8 sn, Sybil 8,3 sn,
Astra 28,9 sn.

---

## Yeniden üretilebilirlik

```
python scripts/66_bimcv_rapor_uyumu.py            # Deney 1
python scripts/67_astra_rapor_karsilastirma.py    # Deney 2
python scripts/68_uclu_sistem_uyumu.py            # Deney 3
python scripts/71_ceviri_terim_denetimi.py        # Deney 5, terim denetimi
```

Rapordaki bütün tablolar, AUC değerleri, bootstrap güven aralıkları ve etiket
keşif analizi bu iki betikten üretilir.

Deney 1 çıktıları: `bimcv_317_siniflama.json`, `bimcv_317_adjudikasyon.csv`,
`bimcv_317_etiket_kesif.csv`, `bimcv_317_tablolar.txt`.

Deney 2 çıktıları: `astra_bulgu_matrisi.csv`, `astra_uyum_tablosu.csv`,
`astra_lezyon_karsilastirma.csv`, `astra_karsilastirma_ciktisi.txt`.

Deney 3 çıktıları: `uclu_uyum_ikili.csv`, `uclu_uyum_uclu_capraz.csv`,
`uclu_uyum_tablolari.txt`.

Deney 5 çıktısı: `ceviri_terim_denetimi.csv`.
