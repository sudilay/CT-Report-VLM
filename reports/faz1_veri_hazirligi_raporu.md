# Faz 1 — Veri Hazırlığı Raporu

**Kapsam:** Kaynak görev listesindeki **T-01** maddesi (CT-RATE kohortundan Findings ve Impression bölümlerinin ayrıştırılması ve analiz için standartlaştırılması).

**Durum:** Tamamlandı. Doğrulama takımı 89 test ile geçiyor.

---

## 1. Amaç

Serbest metin radyoloji raporlarını, üzerinde güvenilir ölçüm yapılabilecek yapılandırılmış bir korpusa dönüştürmek. Bu faz malignite değerlendirmesi yapmaz; sonraki fazların üzerine kurulacağı zemini hazırlar.

Fazın çıkış noktası şu gözlemdir: **bir kelimenin raporda geçmesi, o bulgunun hastada bulunduğu anlamına gelmez.** Korpusta `tumoral` kelimesinin geçtiği cümlelerin tamamı olumsuzdur (*"no significant tumoral wall thickening was detected"*), `mass` kelimesinin geçtiği cümlelerin %93'ü olumsuzdur. Anahtar kelime sayımına dayanan bir yaklaşım bu kohortta sistematik olarak yanlış pozitif üretir.

## 2. Veri kaynağı

CT-RATE, kontrastsız toraks BT görüntüleri ve eşleşen radyoloji raporlarından oluşur (CC-BY-NC-SA-4.0, erişim onayı gerektirir). Bu fazda yalnızca metin varlıkları kullanılmıştır; görüntü verisi indirilmemiştir.

Kohort bir tarama popülasyonu değil, genel hastane popülasyonudur: hasta yaş medyanı 46, raporların yarısında klinik endikasyon alanı boş. Bu, klinik değerlendirme çerçevesi seçimini doğrudan etkiler (bkz. §5).

## 3. Yapılan işler

### 3.1 Rapor korpusunun kurulması

Ham veri hacim (rekonstrüksiyon) düzeyindedir. Bir BT çekiminin farklı ayarlarla üretilmiş birden çok rekonstrüksiyonu ayrı kayıt olarak durur ve **hepsi birebir aynı rapor metnini taşır**. Metni farklılaşan çalışma sayısı sıfırdır.

Bu tespit üzerine korpus **çalışma düzeyinde** tekilleştirilmiştir. Tekilleştirme yapılmadan yürütülen bir çalışmada aynı rapor hem eğitim hem test kümesine düşer ve başarım ölçümleri yapay olarak yükselir.

Ayrıca veri setinde göğüs BT'si olmayan (beyin) taramalar bulunmaktadır; bunlar veri setinin resmi düzeltme listeleriyle çıkarılmıştır. Dikkat çeken nokta: bu taramaların hiçbiri tek başına bir çalışmayı oluşturmuyor — hepsi kafa ve toraksın birlikte çekildiği protokollerin parçası. Görüntü fazında doğru rekonstrüksiyonun seçilmesi kritik olacaktır.

Sonuç: **25.692 çalışma / 21.304 hasta**. Bu değerler, veri setinin kendi yayınında bildirilen sayılarla birebir örtüşmektedir; tekilleştirme mantığı böylece dış kaynakla doğrulanmıştır.

### 3.2 Cümle bölütleme

Analiz cümle düzeyinde yapılacağından raporlar cümlelere ayrılmıştır. Klinik metin için geliştirilmiş bir bölütleyici kullanılmıştır; noktadan körü körüne bölen bir yaklaşım ondalıklı ölçüleri (`1.5 mm`) parçalardı.

Impression bölümünün yapısı Findings'ten farklıdır: maddeler kimi zaman noktalama olmadan, yalnızca boşlukla ayrılmıştır. Üç aday bölütleme kuralı korpusun tamamında karşılaştırılmış ve seçim ölçümle yapılmıştır. Belirleyici bulgu: **çift boşlukla ayrılmış madde sınırlarının %14,1'inde öncesinde noktalama yoktur**; yalnızca cümle bölütleyici kullanmak bu maddeleri birleştirip bilgi kaybına yol açmaktadır.

Örnek: *"Metastatic breast Ca  Findings compatible with Covid pneumonia  Bilateral supraclavicular lymph nodes"* — üç ayrı klinik madde, hiç nokta yok. Tek cümle sayıldığında *"Metastatic breast Ca"* ifadesi alakasız bir bulgunun içine gömülür.

Her cümle, orijinal metindeki karakter konumuyla birlikte kaydedilmiştir. Bu izlenebilirlik, sonraki fazlarda model çıktısının rapora dayanıp dayanmadığını denetleyebilmek için gereklidir.

### 3.3 Şablon cümlelerin karakterize edilmesi

Radyolog her raporu sıfırdan yazmaz; hazır kalıpları kullanıp içindeki sayıyı değiştirir. Bölütlenmiş korpusta cümle oluşumlarının **%71'i** birden fazla kez geçen bir cümleye aittir; yalnızca Findings bölümüne bakıldığında bu oran **%74,8**'e çıkar. En sık cümle sekiz binden fazla hastada birebir aynıdır.

Sayılar maskelenerek kalıp aileleri çıkarılmış ve her kalıbın **kaç farklı hastada** geçtiği sayılmıştır. Sayım hasta üzerinden yapılır: bir hastanın birden çok çekimi olması cümleyi yapay olarak sık göstermemelidir.

İstatistik **yalnızca eğitim kümesinden** hesaplanmış, doğrulama kümesine uygulanmıştır. Doğrulama kümesini de saymak, test verisinden ön işlemeye bilgi sızması anlamına gelirdi.

Bu tasarımın ölçülebilir bir sonucu vardır: doğrulama kümesindeki cümlelerin **%29,27'si** (8.542 / 29.183) eğitim kataloğunda karşılık bulmamakta ve tanım gereği kalıp sayılmamaktadır. Bu oran, kalıp bayrağına dayanan sonraki analizlerde doğrulama kümesinin eğitim kümesinden farklı davranacağını gösterir ve raporlanmalıdır.

Frekans dağılımında beklenen keskin kırılma noktası çıkmamıştır; dağılım düzgün bir güç yasası izler. Bu nedenle eşik niteliksel olarak, her seviyeden örnek cümleler incelenerek belirlenmiştir. Eşik iki bağımsız incelemeyle doğrulanmıştır: eşiğin hemen üstündeki (en düşük frekanslı) ailelerden sabit tohumla yüz örnek çekilmiş, tamamı standart kalıp bulunmuştur. Üçünde hastaya özgü ayrıntı (ölçü ve lokalizasyon) bulunmakla birlikte cümle iskeleti kalıptır; bu, kalıp bayrağının bilgi değeri hakkında iddia taşımadığını gösteren örnektir.

### 3.4 Ölçü ifadelerinin normalize edilmesi

Lezyon boyutu, klinik değerlendirmede doğrudan kriterdir. Ölçü ifadelerinin hangi biçimlerde geçtiği tahmin edilmemiş, korpustan ölçülmüştür. Tek eksenli, çok eksenli (`5x3 mm`), aralık (`2-3 mm`) ve birimi bitişik (`7mm`) biçimlerin tamamı yakalanmıştır.

**Raporların yaklaşık %40'ı boyutu sayısız, niteliksel olarak vermektedir** (*"A few millimetric nodules"*). Bu ifadeler ne yok sayılmış ne de kendilerine sayı atanmıştır; ayrı bir niteliksel kategori olarak kaydedilmişlerdir. Sayı atamak uydurma veri üretmek, yok saymak ise raporların büyük bir kısmında boyut bilgisini kaybetmek olurdu.

Santimetre değerleri milimetreye çevrilmiş, ham birim korunmuştur. Aralıklarda alt ve üst sınır **birlikte** tutulmuştur; "üst sınırı al" bir karar kuralıdır ve karar kuralları değerlendirme katmanına aittir.

Sonuç: **50.513 ölçü kaydı** (33.787 sayısal, 16.726 niteliksel).

## 4. Öne çıkan bulgular

**Kaynak veri setinde malignite ground truth'u yoktur.** Veri setinin 18 anormallik etiketi arasında malignite, kanser, kitle veya tümör etiketi bulunmamaktadır; en yakını `Lung nodule`'dür. Ayrıca bu etiketler raporlardan otomatik üretilmiştir, radyolog doğrulaması değildir. Rapordan çıkarılan hiçbir sınıf hastanın gerçek sonucu sayılamaz. Bu nedenle kolon adlandırmasında `report_derived_*` ön eki benimsenmiştir ve "ground truth" adı yalnızca patoloji doğrulama fazına saklanmıştır.

**Sık geçmek, bilgisiz olmak demek değildir.** Tek kelimelik tanılar (`Cholelithiasis`, `Cardiomegaly`, `Hepatosteatosis`) en kesin biçimde "kalıp ifade" olarak işaretlenir, çünkü bunları yazmanın tek bir yolu vardır — oysa bilgi yoğunluğu en yüksek cümlelerdir. Bu nedenle ilgili bayrak `is_stock_phrasing` olarak adlandırılmış ve **filtreleme için kullanılmaması** belgelenmiştir.

**Bazı raporlarda kaynak veri hataları vardır.** Ölçü çıkarımı sırasında fiziksel olarak imkânsız değerler tespit edilmiştir: 34 cm çıkan aorta (normal aralık 25–35 mm), 40 cm safra taşı, 36 cm aksesuar dalak. Bir kayıtta iç çelişki açıktır: aynı cümlede pulmoner trunkus 33 mm, sağ pulmoner arter 29 mm yazarken sol pulmoner arter 311 mm görünmektedir. Bunlar çıkarım hatası değil kaynak rapor hatasıdır; ham değer korunmuş, düzeltilmemiş, insan değerlendirmesi ayrı bir dosyada kayda geçirilmiştir.

**Yaklaşık sekiz yüz çalışmada radyolog kanaati yoktur** — Impression bölümü boş veya "Not given." yazmaktadır. Bu çalışmalar işaretlenmiştir; sonraki fazlarda "bu rapordan kanaat çıkarılamaz" demek için kullanılacaktır.

## 5. Metodolojik kararlar

**Klinik çerçeve.** Lung-RADS akciğer kanseri taraması için, Fleischner kılavuzu insidental nodüller için tasarlanmıştır. Bu kohort bir tarama kohortu olmadığından bağlam insidentaldir. Boyut ve morfoloji eşikleri gösterge referansı olarak kullanılacak, ancak **Lung-RADS kategorisi üretilmeyecektir**; klinik bağlam bilinmeden otomatik kategori atamak yanlış olur.

**Üç kavramın ayrılması.** Negasyon (bulgu var mı deniyor), şablon (ifade kalıp mı) ve malignite ilgisi (bulgu malignite ile ilgili mi) **bağımsız eksenlerdir**. *"Pericardial effusion was not observed"* cümlesi hem olumsuz hem kalıptır ama malignite ile ilgisizdir; *"No enlarged lymph nodes were detected"* ise üçünü birden taşır. Olumsuz bir bulguyu otomatik olarak "malignite aleyhine kanıt" saymak değerlendirmeyi sistematik olarak çarpıtır.

Bu ayrım gereği Faz 1 yalnızca yapısal bilgi kaydeder. Negasyon çözümlemesi Faz 2'ye, malignite ilgisi atanması Faz 3'e bırakılmıştır.

**Veri hazırlığı korur, karar vermez.** Aralıklarda üst sınırı seçmek, şüpheli değerleri elemek veya niteliksel ifadelere sayı atamak birer karar kuralıdır ve değerlendirme katmanına aittir. Bu fazda hiçbir dönüşüm geri döndürülemez yapılmamış, ham metin her kayıtta korunmuştur.

**Kabul ölçütleri sonuç görülmeden yazılmıştır.** Bir ölçüt tutmadığında ölçüt gevşetilmemiş, gereği yapılmıştır: elle doğrulanacak şablon sayısı kapsama ölçütü sağlanana kadar artırılmıştır.

## 6. Doğrulama

Doğrulama iki katmanlıdır.

**Sınır örneklemleri.** Kabul ölçütlerinin gerektirdiği iki örneklem üretilmiş ve değerlendirilmiştir: bölütleme kuralının uygulandığı madde sınırlarından yüz örnek (risk taşıyan noktalamasız sınırlar ağırlıklı) ve kalıp eşiğinin hemen üstündeki ailelerden yüz örnek. Değerlendirme sonuçları ilgili dosyalarda kayıtlıdır.

**Zor vaka takımı.** Elle seçilmiş zorlayıcı örnekler sabit bir dosyada tutulur ve her değişiklikten sonra çalıştırılır: ondalıklı ölçüler, aralıklar, çok eksenli ölçüler, aynı cümlede birden çok ölçü, negasyon, belirsizlik ifadeleri, madde işaretleri, bozuk noktalama, teknik ile klinik ölçü ayrımı.

**Tam sayım.** Mekanik özellikler örneklemeyle değil, kayıtların tamamında denetlenmiştir: karakter konumlarının metne birebir oturması, birim çevriminin doğruluğu, türetilmiş alanların kaynak alanlarla tutarlılığı. Elli binden fazla kayıtta sıfır hata bulunmuştur.

Ayrıca hasta düzeyinde veri sızıntısı, tekilleştirmenin bilgi kaybetmemesi ve kaynak dosyalarla sadakat ayrı testlerle bağlanmıştır.

## 7. Bilinen sınırlar

**Önceki tetkik ölçüleri ayrıştırılmamıştır.** Sekiz yüzden fazla cümlede güncel ve önceki tetkik ölçüleri birlikte geçmektedir (*"51x42 mm in the current examination and 46x36 mm in the previous PET-CT"*). Şu an ikisi de aynı biçimde kaydedilmektedir. Hangisinin güncel olduğunu ayırmak zamansal çözümleme gerektirir ve Faz 2'ye bırakılmıştır. **Büyüme değerlendirmesi için kritik olacaktır.**

**Aynı lezyona ait çoklu ölçü anmaları birleştirilmemiştir.** Yedi yüzden fazla cümlede hem niteliksel hem sayısal ölçü aynı lezyonu tarif etmektedir. İkisi de metinde geçen ayrı anmalar olduğu için ikisi de kaydedilmiştir; aynı lezyona ait olduklarını belirlemek bulgu düzeyi bir iştir.

**Metin çeviri kaynaklıdır.** Raporlar aslen Türkçe yazılıp İngilizceye çevrilmiştir. Şablon oranının yüksekliği kısmen bundan kaynaklanabilir ve bulgular Türkçe kurum verisine doğrudan genellenemeyebilir.

**Teknik ölçü ayrımının kapsamı beklenenden küçüktür.** Kesit kalınlığı gibi teknik ölçüler ayrı bir alanda tutulduğundan, Findings ve Impression içinde yalnızca birkaç örnek bulunmuştur. Ayrım uygulanmıştır ancak pratikte etkisi sınırlıdır.

## 8. Sonraki faz

Faz 2, bu korpus üzerinde yapılandırılmış çıkarıma geçer: bulgu ve anatomik bölge varlıklarının çıkarılması, negasyon ve belirsizlik kapsamının doğru algoritmayla belirlenmesi, zamansal ifadelerin çözümlenmesi ve çıkarım doğruluğunun manuel örneklemle ölçülmesi.

Faz 2 ve Faz 3 tamamlanmadan model karşılaştırma fazlarına geçilmeyecektir; değerlendirme şeması olmadan hiçbir başarım ölçümü anlamlı olmaz.
