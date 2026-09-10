# BTB3D Modelinin Akciğer Kanseri Taramasında Malignite Tespiti

### Doğrulanmış kanser sonucuna karşı değerlendirme, iki karşılaştırma sistemiyle

**Tarih:** 2026-09-10 · **Model:** BTB3D · **Veri:** NLST düşük doz BT tarama kohortundan 2.500 seri

---

## Özet

Bu çalışmada BTB3D'nin akciğer kanseri tarama tomografilerinden ürettiği raporlar, hastaların **doğrulanmış kanser tanısıyla** karşılaştırıldı. Önceki bir çalışmada aynı model tanısal toraks tomografilerinde değerlendirilmişti; oradaki referans hekim raporlarıydı. Burada referans daha güçlüdür: hastanın gerçekten kanser olup olmadığı takip verisinden bilinmektedir.

Sorulan soru şudur: **model, sonradan akciğer kanseri tanısı alan hastaların tarama raporlarında bir şüphe dile getirebiliyor mu?**

Cevap hayırdır. Bir yıl içinde kanser tanısı alan 34 hastanın 33'ünde model raporunda pulmoner malignite bildirilmemiş, Youden J değeri sıfırın altında kalmıştır. Nodül bildirimleri ise ayırt edici değildir çünkü model hastaların yaklaşık beşte dördüne nodül yazmaktadır.

Bir ölçüt kusuru çözümleme sırasında saptanmış ve düzeltilmiştir; buradaki tüm sayılar düzeltilmiş ölçüte dayanmaktadır. Düzeltme sonrası, ilk çözümlemede bulunan "ters yönlü ilişki" istatistiksel anlamlılığını yitirmiştir ve bu bulgu geri alınmıştır.

Karşılaştırma için aynı serilerde iki sistem daha değerlendirildi. Ortaya çıkan tablo tek yönlü değildir: BTB3D, karşılaştırma sistemlerinden birinde bol miktarda bulunan şablon artıklarını hiç taşımamaktadır. Buna karşılık klinik içerik açısından ölçülebilir sinyali üreten tek sistem Astra olmuştur.

Sonuçlar hem otomatik çıkarımla hem de kaynağı bilmeyen bağımsız bir ikincil yapay zekâ değerlendirmesiyle elde edilmiş, iki yol aynı yönü vermiştir.

---

## 1. Bu çalışma öncekinden neden farklı

Tanısal toraks tomografisi çalışmasında model raporu hekim raporuyla karşılaştırılmıştı. O tasarımın bilinen bir zayıflığı vardır: hekim raporu da bir metindir, hekimin yazmadığı bir bulgu orada "yok" sayılır ve gerçekte görüntüde ne olduğu bilinmez.

NLST kohortu bu zayıflığı kapatır. Burada her hastanın **takip süresi boyunca akciğer kanseri tanısı alıp almadığı** kayıtlıdır. Bu, metinden bağımsız bir dış gerçektir.

Buna karşılık NLST'de bir eksiklik vardır: **insan yazımı referans rapor yoktur.** Kohortta bulunan diğer iki rapor kümesi de yapay zekâ çıktısıdır. Bu nedenle burada "model raporu hekim raporuyla uyuşuyor mu" sorusu sorulamaz; sorulabilecek soru, raporun kanser sonucuyla ilişkili olup olmadığıdır.

Bir noktanın baştan belirtilmesi gerekir. NLST bir **tarama** kohortudur: hastaların çoğu sağlıklıdır ve kanser tanısı alanların bir kısmında tarama anında henüz görünür bir hastalık yoktur. Bu nedenle tanıya kadar geçen süreye göre katmanlama zorunludur. Tanısı bir yıl içinde konan hastalar, hastalığın taramada görülebilir olma olasılığının en yüksek olduğu gruptur ve asıl ölçüm bu grupta yapılmıştır.

---

## 2. Yöntem

Değerlendirme, önceden dondurulmuş bir hasta bölünmesinin eğitim ve geliştirme kümeleriyle sınırlandırılmıştır. Nihai test kümesi bu çalışmada açılmamıştır.

| | |
|---|---:|
| Seri | 2.500 |
| Hasta | 1.018 |
| Kanser tanısı almış hasta | 61 (%6,0) |
| Tanısı bir yıl içinde konan hasta | 34 |

Üç sistemin raporları da aynı çıkarım hattından geçirilerek standart toraks patolojilerine ve bir malignite paneline indirgendi. Aynı hat kullanıldığı için sistemler arasındaki fark yöntemden değil rapor içeriğinden gelmektedir. Bu hat, olumsuzlanmış ifadeleri pozitif saymaz ve toraks dışı anatomiye bağlanan bulguları eler; bir raporda "kitle" kelimesinin geçmesi tek başına pozitif sayılmaz.

Ölçümler hasta düzeyinde yapılmıştır: bir hastanın herhangi bir serisinde bulgu bildirilmişse o hasta pozitif kabul edilmiştir.

### Kullanılan ölçütler

**Duyarlılık**, kanser tanısı almış hastaların ne kadarında raporda ilgili bulgunun bildirildiğini gösterir. **Özgüllük**, kanser olmayan hastaların ne kadarında bulgunun bildirilmediğini gösterir.

Bu iki değere ayrı ayrı bakmak yanıltıcıdır. Her hastaya "kanser var" diyen bir sistem tam duyarlılık, hiç kimseye demeyen bir sistem tam özgüllük elde eder. Bu nedenle ikisi **Youden J indeksinde** birleştirilmiştir:

> J = duyarlılık + özgüllük − 1

Yazı tura atan bir sistem J = 0 alır. J > 0 sistemin bilgi taşıdığını, J < 0 ise şanstan kötü performansı gösterir.

Duyarlılık güven aralıkları Wilson yöntemiyle, J güven aralıkları 2.000 tekrarlı bootstrap ile hesaplanmıştır. Yön farkının rastlantı olup olmadığı Fisher kesin testiyle sınanmıştır.

---

## 3. BTB3D'nin kanser tespitindeki başarısı

### 3.1 Ölçütün tanımı ve bir düzeltme

İlk çözümlemede malignite ölçütü bir **kara liste** ile kurulmuştu: karaciğer, tiroid, böbrek gibi bilinen toraks dışı yapılara bağlanan ifadeler eleniyordu. Bu tanımın bir açığı bulunduğu sonradan görülmüştür. Anatomi sözlüğünde hiç bulunmayan yapılar (vokal kord, prostat, larinks) boş bir anatomi bağlamı ürettiği için elenmemekte, dolayısıyla *"sağ vokal kord üzerinde 4 cm kitle"* gibi ifadeler pulmoner malignite sayılabilmekteydi.

Ölçüt **beyaz listeye** çevrilerek tüm çözümleme yinelenmiştir: bir malignite ifadesinin sayılabilmesi için cümlesinde akciğer, lob, parankim, plevra veya bronş gibi bir **pulmoner anatominin bulunması zorunludur**. Anatomi belirtmeyen ifadeler artık elenmektedir. Aynı düzeltme üç sisteme de simetrik olarak uygulanmıştır.

Düzeltmenin etkisi küçük değildir:

| Sistem | Eski ölçüt | Torasik | **Pulmoner** |
|---|---:|---:|---:|
| BTB3D | %8,8 | %6,4 | **%4,8** |
| Astra | %17,8 | %16,0 | %11,6 |
| MedMo | %0,6 | %0,3 | %0,2 |

Aşağıdaki sonuçlar düzeltilmiş pulmoner ölçüte dayanmaktadır. Nodül ve şüpheli morfoloji göstergeleri ilk tanımla hesaplanmış olup aynı çekince onlar için de geçerlidir.

### 3.2 Kanser sonucuna karşı sonuçlar

**Analiz kümesi ve payda.** Kohorttaki 1.018 hastanın 991'i bu analize girmektedir: 957 kanser tanısı almamış hasta ile tanısı bir yıl içinde konan 34 hasta. Tanısı bir yıldan sonra konan **27 hasta analiz dışında bırakılmıştır**, çünkü bu hastalarda tarama anında görünür hastalık bulunma olasılığı düşüktür.

| Sistem | TP | FP | FN | TN | Duyarlılık | Özgüllük | Youden J |
|---|---:|---:|---:|---:|---:|---:|---|
| **BTB3D** | 1 | 108 | 33 | 849 | 0,029 | 0,887 | **−0,083** [−0,128, −0,013] |
| Astra | 13 | 240 | 21 | 717 | 0,382 | 0,749 | +0,132 [−0,036, +0,303] |
| MedMo | 0 | 6 | 34 | 951 | 0,000 | 0,994 | −0,006 [−0,012, −0,002] |

BTB3D, bir yıl içinde kanser tanısı alan 34 hastanın **33'ünde** pulmoner malignite bildirmemiştir. Youden J değeri sıfırın altındadır ve güven aralığı sıfırı içermemektedir: model, bu ölçütle rastgele tahminden daha kötü performans göstermektedir.

**Astra için sonuç, önceki çözümlemeye göre zayıflamıştır.** Düzeltilmiş ölçütte güven aralığı sıfırı içermektedir; yani tek başına bakıldığında Astra'nın da şanstan ayırt edilebilir bir sinyal ürettiği söylenemez.

**Buna karşılık sistemler arasındaki fark sağlamdır.** Üç sistem aynı hastalara uygulandığı için karşılaştırma, ayrı güven aralıklarına bakarak değil **eşleştirilmiş bootstrap** ile yapılmıştır:

| Karşılaştırma | ΔJ | %95 GA |
|---|---:|---|
| Astra ile BTB3D | +0,215 | [+0,026, +0,405] |
| BTB3D ile MedMo | −0,077 | [−0,121, −0,005] |
| Astra ile MedMo | +0,138 | [−0,024, +0,304] |

Astra ile BTB3D arasındaki fark, dört farklı çözümleme kurgusunda da (pulmoner ve torasik tanım, hasta düzeyi ve tek indeks tarama) sıfırı içermeyen bir aralık vermektedir. Bu, en sağlam sonuçtur: **BTB3D bu görevde Astra'nın gerisindedir.**

### 3.3 Ters yönlü ilişki iddiası geri alınmıştır

Önceki çözümlemede modelin malignite ifadesini kanser hastalarında anlamlı biçimde daha seyrek kullandığı bulunmuştu. Düzeltilmiş ölçütle bu bulgu **istatistiksel anlamlılığını yitirmektedir**:

| Ölçüt | Kanserli | Kanser olmayan | Odds | *p* |
|---|---:|---:|---:|---:|
| Eski (kara liste) | %3,3 | %20,2 | 0,13 | 0,0003 |
| Pulmoner (düzeltilmiş) | %4,9 | %11,3 | 0,41 | **0,1406** |
| Torasik (düzeltilmiş) | %6,6 | %15,2 | 0,39 | **0,0897** |

Nokta tahmini hâlâ ters yöndedir, ancak fark rastlantıdan ayırt edilememektedir. **Önceki anlamlı sonuç, büyük ölçüde ölçüt kusurundan kaynaklanmıştır.**

İkinci bir karıştırıcı da saptanmıştır. Ölçümler hasta düzeyinde ve "herhangi bir seride bildirim yeterlidir" kuralıyla yapılmaktadır. Ancak kanser tanısı almış hastaların ortalama seri sayısı **2,00**, kanser tanısı almamışlarınki **2,48**'dir. Daha çok görüntülenen hastaların yanlış pozitif alma olasılığı otomatik olarak yükselir; bu, gözlenen ters yönü kısmen açıklamaktadır.

Bu etkiyi denetlemek için hasta başına **tek indeks tarama** ile çözümleme yinelenmiştir. Orada BTB3D'nin doğru yakalama sayısı 23 hastada **sıfıra** düşmekte, Youden J −0,051 [−0,065, −0,038] olmaktadır. Yani düşük performans bu kuralın bir yan etkisi değildir; ancak ters yönün istatistiksel anlamlılığı ona bağlıdır.

### 3.4 Rapor içeriği hastanın durumundan bağımsız

Bir tarama sisteminin en temel davranışı, hasta olan ve olmayan kişiler için farklı raporlar üretmesidir. Bu, referans gerektirmeden ölçülebilir.

| Ölçülen | Kanser hastaları | Kanser olmayanlar |
|---|---:|---:|
| Vaka başına bildirilen bulgu | 2,31 | 2,45 |
| Rapor uzunluğu (kelime) | 201,9 | 205,2 |
| Sayısal ölçü içeren rapor | %57,1 | %63,9 |

Üç ölçütün üçünde de fark ya yok denecek kadar küçüktür ya da ters yöndedir.

Bu ölçütler klinik kalite ölçüsü değildir: küçük bir malign nodül kısa ve doğru biçimde raporlanabilir. Buradaki değerleri, çıktının hasta durumuyla herhangi bir ilişki gösterip göstermediğine dair kaba göstergelerdir. Üçünün de ilişkisiz çıkması, tek başına kanıt olmasa da diğer ölçümlerle aynı yöne işaret etmektedir.

Buna ek olarak, kanser tanısı almış **26 seri**, kanser tanısı almamış bir hastaya da yazılan birebir aynı rapor metnini almıştır. Aynı normal rapor iki sağlıklı hasta için doğru olabilir; sorun, ayrıntılı ve bulgu içeren şablonların farklı hastalarda birebir tekrarlanmasıdır. Bu durumda metin, o hastanın görüntüsünden türetilmiş olamaz.

### 3.5 Hatalı ve anlamsız içerik

Yukarıdaki sayılar modelin doğru bulguyu bulamadığını gösterir. Bu bölüm, ürettiği içeriğin niteliğini gösterir.

**Rapor kendi içinde çelişiyor.** Modelin raporlarının **%4,8'inde**, aynı metinde hem akciğerde nodül bulunmadığı hem de ölçüsü verilmiş bir akciğer nodülü yazılıdır. Örnekler:

> *"Her iki akciğer parankiminde nodüler lezyon saptanmadı."* … *"Tarif edilen nodüllerin en büyüğü sağ akciğer alt lob superior segmentte 5 mm boyutundadır."*

> *"Her iki akciğerde kitle, nodül, infiltrasyon saptanmadı."* … *"Sol akciğer üst lob apikoposterior segmentte, düzgün konturlu 5 mm çapında parankimal nodül izlenmektedir."*

Bir rapor, kendi içinde bu şekilde çelişiyorsa doğru bulguyu içerse bile klinik olarak kullanılamaz. Aynı ölçüm tanıdık veride %3,0'tür; yabancı veride artmaktadır.

**Tümüyle başka bir organın raporu yazılabiliyor.** Aşağıdaki metin, bir akciğer kanseri tarama tomografisi için üretilmiştir. Kanser tanısı almamış bir hastaya aittir ve olduğu gibi aktarılmıştır:

> *"Please examine my pet for the most accurate diagnosis of prostate cancer. Nodular hypodense lesions with a diameter of 45 mm are observed in the left lobe of the prostate. Another hypodense nodular lesion is observed in the right lobe inferior. Bula and linear calcifications are observed in the left lobe of the prostate. The described appearances are the most accurate diagnostic findings for prostate cancer. […] Impression: No signs of infection were detected in the examination area. The appearances described above in the thyroid gland and prostate are the most accurate findings for prostate cancer. Further testing is recommended."*

Bu metinde üç ayrı sorun bir aradadır. Prostat, göğüs tomografisinin görüntüleme alanında **bulunmaz**; oradaki 45 mm'lik lezyon ve kalsifikasyonlar tümüyle uydurmadır. Rapor bir istek cümlesiyle başlamaktadır; buradaki "pet" büyük olasılıkla PET-BT kısaltmasının bozulmuş halidir ve cümle yapısı eğitim verisindeki sohbet metinlerinden bir kalıntı izlenimi vermektedir. Ve sonuç bölümü, hiç görüntülenmemiş bir organ için **prostat kanseri tanısı** koymakta ve ileri tetkik önermektedir.

Metnin geri kalanı normal bir toraks raporu gibi devam etmektedir: trakea açık, mediastende patolojik lenf nodu yok, akciğer parankimi normal. Yani uydurma bölüm, gerçekçi bir raporun içine yerleşmiştir.

**Bağımsız değerlendirme de aynı sonucu vermiştir.** Kaynağı bilmeyen ikincil değerlendirici, kırk BTB3D raporunun **on ikisinde** anlamsız veya uydurma içerik işaretlemiştir. İşaretlerin gerekçeleri arasında şunlar bulunmaktadır: *"23 mm nodül ile nodül yok ifadeleri çelişkili"*, *"adrenal bezler doğal denip ardından sağ adrenal kitle yazılmış"*, *"kalp hem büyük hem normal denmiş"*, *"toraks değerlendirmesi yerine yalnız böbrek bulguları verilmiş"*.

Bu hataların ortak özelliği, metnin akıcı ve profesyonel görünmeye devam etmesidir. Çelişki iki ayrı paragrafta durduğu için tek okuyuşta fark edilmeyebilir.

---

## 4. İki karşılaştırma sistemi

Aynı 2.500 seride iki sistemin raporları da değerlendirilmiştir. Bu bölümün amacı BTB3D'nin sonuçlarını bir bağlama oturtmaktır: ölçülen düşük performans göreve mi özgüdür, yoksa bu görevde daha iyisi mümkün müdür?

### 4.1 Klinik sinyal ve farkın sağlamlığı

Düzeltilmiş ölçütle **hiçbir sistemin tek başına** şanstan ayırt edilebilir bir sinyal ürettiği gösterilememiştir (§3.2): Astra'nın güven aralığı sıfırı içermekte, BTB3D ve MedMo'nunki sıfırın altında kalmaktadır.

Sağlam olan bulgu, sistemler arasındaki **eşleştirilmiş farktır**. Üç sistem aynı hastalara uygulandığı için karşılaştırma, ayrı güven aralıklarını yan yana koyarak değil, hasta düzeyinde eşleştirilmiş bootstrap ile yapılmıştır. Sonucun bir çözümleme tercihine bağlı olmadığını görmek için dört ayrı kurgu denenmiştir:

| Kurgu | ΔJ (Astra − BTB3D) | %95 GA |
|---|---:|---|
| Pulmoner tanım, hasta düzeyi | +0,215 | [+0,026, +0,405] |
| Pulmoner tanım, tek indeks tarama | +0,195 | [+0,017, +0,397] |
| Torasik tanım, hasta düzeyi | +0,229 | [+0,033, +0,414] |
| Torasik tanım, tek indeks tarama | +0,288 | [+0,083, +0,496] |

Dördünde de aralık sıfırı içermemektedir. **BTB3D bu görevde Astra'nın gerisindedir** ve bu, raporun en sağlam karşılaştırmalı bulgusudur.

MedMo ise malignite bildirimini neredeyse hiç kullanmamakta (hastaların %0,6'sı), dolayısıyla yüksek özgüllükle birlikte sıfır duyarlılık üretmektedir. BTB3D ile MedMo arasındaki fark da BTB3D aleyhinedir (ΔJ −0,077 [−0,121, −0,005]).

### 4.2 Sistemler birbirini doğrulamıyor

Üç sistemin aynı görüntü için bildirdiği bulgular karşılaştırıldığında uyum şans düzeyindedir.

| Sistem çifti | 18 patoloji | Malignite paneli |
|---|---:|---:|
| BTB3D ile Astra | +0,075 | +0,008 |
| BTB3D ile MedMo | +0,035 | −0,013 |
| Astra ile MedMo | +0,036 | −0,030 |

Değerler Cohen kappa katsayısıdır ve sıfır şans düzeyini gösterir. Aynı tomografiye bakan üç sistem, birbirinden bağımsız denebilecek bulgular üretmektedir. Bu, dış referans olmadan da bir sonuç verir: **üç sistemin çıktıları birbirinin yerine kullanılamaz.** Düşük uyum tek başına hangisinin doğru olduğunu göstermez; yalnızca en az ikisinin aynı görüntü için farklı şeyler bildirdiğini gösterir.

Nodül bildirim oranlarındaki fark bunu somutlaştırır: seri düzeyinde BTB3D taramaların %52,1'inde, Astra %13,6'sında, MedMo %3,7'sinde nodül bildirmektedir. Hasta düzeyinde BTB3D için bu oran %79,8'e çıkmaktadır.

### 4.3 Rapor biçimi: şablon artıkları

Karşılaştırma tek yönlü değildir. Rapor metinlerinin biçimsel kalitesi incelendiğinde tablo kısmen tersine dönmektedir.

| Yapay zekâ şablon artığı | BTB3D | Astra | MedMo |
|---|---:|---:|---:|
| `[Insert ...]` türü doldurulmamış yer tutucu | %0,0 | **%41,6** | %0,0 |
| Markdown biçimlendirme işaretleri | %0,0 | **%96,8** | %0,0 |
| "Chest CT Report" türü başlık | %0,0 | %54,7 | %0,0 |
| "Patient Information" bölümü | %0,0 | %45,8 | %0,0 |

Astra raporlarının önemli bir kısmı klinik rapor biçiminde değildir: doldurulmamış hasta adı ve tarih alanları, madde işaretli listeler ve sohbet üslubu içermektedir. Bu haliyle bir rapor sistemine doğrudan aktarılamaz.

BTB3D bu şablon artıklarının hiçbirini taşımamaktadır. Ürettiği metinler radyoloji rapor biçimine, bölüm sırasına ve üslubuna uygundur. Ancak bu tablo yalnızca şablon artıklarını ölçmektedir; üçüncü sistem de aynı ölçütlerde temizdir.

### 4.4 BTB3D'nin biçim disiplini yabancı veride korunuyor mu

Tanısal tomografi çalışmasında modelin en güçlü yönü rapor biçimiydi. Bu üstünlüğün yabancı veride de sürüp sürmediği ayrıca ölçülmüştür.

| Biçim ölçütü | Tanıdık veri | Yabancı veri |
|---|---:|---:|
| "Impression" sonuç bölümü içeriyor | %95,2 | %95,2 |
| Yapay zekâ yer tutucusu (`[Insert…]`) | %0,0 | %0,0 |
| Sohbet üslubu ifadeler | %0,0 | %0,5 |
| Markdown biçimlendirme artığı | %5,4 | %3,0 |
| Bozuk başlangıç ("Find the…") | %12,8 | **%20,2** |
| Cümle ortasında kesilen rapor | %22,6 | %25,1 |
| Benzersiz metin oranı | %95,6 | **%85,1** |

Sonuç ikiye ayrılır.

**Rapor mimarisi korunmaktadır.** Sonuç bölümü içerme oranı iki kohortta birebir aynıdır. Karşılaştırma sisteminde görülen doldurulmamış alanlar ve sohbet üslubu BTB3D'de yabancı veride de yok denecek kadar azdır. Model, radyoloji rapor iskeletini kohorttan bağımsız olarak kurabilmektedir.

**Metin üretim düzeyinde bozulma artmaktadır.** Bozuk başlangıç oranı yaklaşık iki katına çıkmakta, kesilen rapor oranı yükselmekte ve şablon tekrarı belirgin biçimde artmaktadır. Bozuk başlangıçların içeriği de bunu göstermektedir:

> *"Find the parenchymal tissue in the **supraclious** showing no extension towards the vertebral apex…"*

> *"Find the triangular soft tissue density in the **supraclirus** extends to the anterior mediastinal area."*

Her iki cümlede de anatomik terim bozulmuştur; "supraklaviküler" sözcüğü var olmayan biçimlere dönüşmüştür. Bu tür bozulmalar tanıdık veride de görülmekte, yabancı veride sıklaşmaktadır.

Özetle BTB3D, gösterilen şablon artıkları bakımından karşılaştırma sistemlerinden birinden belirgin biçimde temizdir. Üçüncü sistem bu ölçütlerde BTB3D ile eşittir ve bağımsız değerlendirmede anlamsız içerik açısından ondan daha iyidir; dolayısıyla genel bir biçim üstünlüğü iddia edilmemektedir. BTB3D'nin biçim disiplini yabancı veride korunmakta, ancak kendi tanıdık verisine göre ölçülebilir biçimde gerilemektedir.

## 5. Bağımsız ikincil değerlendirme

Otomatik çıkarım hattının çıktısına tek başına güvenilmemesi için bağımsız bir ikincil değerlendirme yapılmıştır. Kırk vaka için üç sistemin raporu da, **OpenAI Codex** adlı yapay zekâ değerlendiricisine kör olarak verilmiştir.

Körlük üç katmanlıdır: otomatik çıkarım etiketleri paylaşılmamış, hangi metnin hangi sistemden geldiği gizlenmiş (metinler vaka içinde karıştırılarak `Sistem-A/B/C` olarak sunulmuş) ve hastaların kanser durumu bildirilmemiştir. Değerlendirici 120 metnin her biri için on sekiz patolojiyi işaretlemiş, ayrıca üç ek yargı vermiştir.

Bu bir yapay zekâ değerlendirmesidir, radyolog görüşü değildir. Sonuçlar otomatik hattın tekrarlanabilirliğini sınamak için kullanılmış, klinik uzman görüş birliği olarak yorumlanmamıştır.

### 5.1 Otomatik hat ile uyum

| Sistem raporları üzerinde | Karar sayısı | Uyum | Kappa |
|---|---:|---:|---:|
| BTB3D | 720 | %97,6 | +0,895 |
| MedMo | 720 | %99,7 | +0,955 |
| Astra | 720 | %93,6 | **+0,624** |
| Tümü | 2.160 | %97,0 | +0,806 |

BTB3D ve MedMo raporlarında uyum çok yüksektir. **Astra raporlarında ise belirgin biçimde düşüktür.** Bunun nedeni Astra metinlerinin madde işaretli listeler, başlıklar ve açıklayıcı cümleler içermesidir; cümle temelli çalışan otomatik hat bu yapıda daha çok hata yapmaktadır.

Bu, raporda Astra ile ilgili sayıların BTB3D sayılarından **daha az kesin** olduğu anlamına gelir ve o bölümler bu sınırla birlikte okunmalıdır.

### 5.2 Anlamsız içerik oranı

Değerlendiriciden, her metinde toraks tomografisinde karşılığı olmayan veya uydurma ifade bulunup bulunmadığını işaretlemesi istenmiştir. Bu, halüsinasyonun otomatik desen taramasından bağımsız ilk ölçümüdür.

| Sistem | Anlamsız içerik işaretlenen rapor |
|---|---:|
| Astra | 25 / 40 (%62,5) |
| **BTB3D** | 12 / 40 (%30,0) |
| MedMo | 0 / 40 (%0,0) |

Kaynağı bilmeyen bir değerlendirici, Astra raporlarını BTB3D raporlarından **iki kat daha sık** anlamsız içerik taşıyor diye işaretlemiştir. Bu bulgu, biçim ekseninde BTB3D'nin üstün olduğu yönündeki ölçümü bağımsız olarak doğrulamaktadır.

Buna karşılık BTB3D raporlarının da yaklaşık üçte biri bu şekilde işaretlenmiştir; oran düşük değildir.

### 5.3 "Bu rapor hastayı geri çağırtır mı"

Değerlendiriciden ayrıca, her metni okuyan bir hekimin hastayı ileri tetkike çağırıp çağırmayacağını yargılaması istenmiştir. Bu yargı, klinik sonucu doğrudan ölçen bir vekildir ve kanser sonucuyla karşılaştırılabilir.

| Sistem | TP | FP | FN | TN | Duyarlılık | Özgüllük | J |
|---|---:|---:|---:|---:|---:|---:|---:|
| Astra | 15 | 13 | 5 | 7 | 0,750 | 0,350 | **+0,100** |
| BTB3D | 11 | 15 | 9 | 5 | 0,550 | 0,250 | **−0,200** |
| MedMo | 3 | 4 | 17 | 16 | 0,150 | 0,800 | −0,050 |

Yön, otomatik ölçümle aynıdır: Astra sıfırın üzerinde, BTB3D altındadır. BTB3D raporlarını okuyan bir hekim, kanser hastalarının yarısını geri çağırırdı; ancak sağlıklı hastaların dörtte üçünü de çağırırdı.

### 5.4 Malignite yargısı

Değerlendirici, altı düzeyli ölçekte üç sistemin de raporlarında **malignite şüphesini neredeyse hiç bulmamıştır**: BTB3D için 40 vakanın 3'ünde, Astra için 1'inde, MedMo için hiçbirinde "şüpheli" veya "malign" düzeyi verilmiştir.

Bu, otomatik hattın bildirdiği oranlardan çok daha düşüktür ve önemli bir uyarıdır: otomatik hattın "malignite" kavramı, dikkatli bir okuyucunun malignite şüphesi sayacağından daha geniştir. Otomatik ölçümlerdeki mutlak oranlar bu nedenle şüpheyle karşılanmalı, sistemler arası **karşılaştırma** ise geçerliliğini korumaktadır çünkü aynı hat üç sisteme de uygulanmıştır.

Değerlendiricinin bildirdiği bulgu sayıları da otomatik ölçümle aynı sıralamayı vermektedir: BTB3D vaka başına 2,42, Astra 1,25, MedMo 0,57 bulgu.

İkincil değerlendirme ayrıca bir ölçüm hatasını yakalamıştır. Karşılaştırma sistemlerinden birinin raporlarında, hastaya dair bulgu bildirmeyen açıklayıcı cümleler bulunduğu (*"göğüs tomografisinde tipik olarak kitle, büyümüş lenf nodu gibi anormallikler değerlendirilir"*) ve otomatik hattın buradaki terimleri bulgu sayabildiği görülmüştür. Bu gözlem, malignite ölçütünün anatomik olarak sıkılaştırılmasına yol açan iki bulgudan biri olmuştur (§3.1). Bu tür kontroller, otomatik ölçümün tek başına bırakılmaması gerektiğini göstermektedir.

---

## 6. Tanısal tomografi çalışmasıyla karşılaştırma

### 6.1 Neden bu karşılaştırma önemli

Bu iki çalışma arasında, sonucun yorumunu belirleyen kritik bir asimetri vardır: **model CT-RATE üzerinde eğitilmiştir.**

Tanısal tomografi çalışmasının verisi, modelin eğitildiği veri kümesinin ayrılmış bir bölümüdür. Aynı hastaneden, aynı görüntüleme protokolüyle, aynı raporlama geleneğiyle gelen tomografilerdir. Model açısından bu **tanıdık dağılımdır**.

NLST ise farklı bir dünyadır: farklı bir ülkede, farklı bir dönemde, farklı cihazlarla ve düşük doz tarama protokolüyle çekilmiş görüntülerdir. Hasta profili de farklıdır; burada çoğu kişi sağlıklıdır ve incelemenin amacı tanı koymak değil şüpheli lezyon aramaktır. Model açısından bu **yabancı dağılımdır**.

Bu ayrım, olağan beklentiyi belirler: bir modelin tanıdık dağılımda iyi, yabancı dağılımda daha kötü olması normaldir. Asıl soru, gözlenen tablonun bu beklentiyle açıklanıp açıklanamayacağıdır.

### 6.2 Hangisinde daha başarılı

Doğrudan karşılaştırılabilecek tek grup, **referans gerektirmeyen ölçütlerdir**. Bunlar iki kohortta aynı tanımla hesaplanmıştır. Klinik başarı sayıları ise karşılaştırılamaz, çünkü referanslar farklıdır: biri hekim raporu, diğeri doğrulanmış kanser sonucudur.

| Ölçüt | Tanısal tomografi (tanıdık veri) | Tarama tomografisi (yabancı veri) |
|---|---:|---:|
| Benzersiz metin oranı | %95,6 | %85,1 |
| En sık şablonun kaç hastaya yazıldığı | 13 | 50 |
| Cümle ortasında kesilen rapor | %22,6 | %25,1 |
| Bozuk başlangıçla ("Find the…") başlayan rapor | %12,8 | %20,2 |
| Kendi içinde çelişen rapor (akciğer nodülü) | %3,0 | %4,8 |
| Bulgu sayısı, hasta ağırlığına göre | fark yok | ters yön |

Metin üretim kalitesi yabancı veride **ölçülebilir biçimde bozulmaktadır**. Aynı şablonun kaç hastaya yazıldığı on üçten elliye çıkmakta, bozuk başlangıç oranı neredeyse iki katına ulaşmaktadır.

Klinik içerik açısından ise iki kohortta da başarı gösterilememiştir. Tanıdık veride bulgu uyumu rastgele tahminin çok az üzerinde kalmış, yabancı veride kanser sonucuyla ilişki sıfırın altına düşmüştür.

Kısa cevap şudur: **model yabancı veride bir miktar daha kötüdür, ama tanıdık veride de başarılı değildir.** Bu ikinci kısım daha önemlidir, çünkü dağılım farkının başarısızlığı açıklamadığını gösterir.

### 6.3 Sebep ne olabilir

Gözlenen tablo, iki gözlemle birlikte okunduğunda tutarlı bir açıklamaya işaret etmektedir.

**Birincisi, model nodül bildirim oranını kohorttan bağımsız olarak taşımaktadır.**

| | Oran |
|---|---:|
| Eğitim verisindeki gerçek nodül sıklığı | %47,8 |
| Modelin tanıdık veride nodül bildirme oranı | %45,6 |
| Modelin yabancı veride nodül bildirme oranı | **%52,1** |
| Karşılaştırma sistemlerinin yabancı veride bildirme oranı | %13,6 ve %3,7 |

Tanıdık veride model, gerçek sıklığa çok yakın bir oranda nodül bildirmektedir. Bu ilk bakışta iyi kalibrasyon gibi görünür. Ancak yabancı veride de yaklaşık aynı oranı üretmektedir. İki kohortta benzer oran üretmesi, bu oranın görüntüden çok eğitim dağılımından geldiği hipotezini desteklemektedir. Tek başına kanıt değildir; ancak aynı kohortta çalışan diğer iki sistemin çok daha düşük oranlar bildirmesi bu yorumu güçlendirmektedir.

Bir başka deyişle, tanıdık verideki "doğru" nodül oranı bir başarı değil, tesadüftür: model her koşulda taramaların yarısına nodül yazmaktadır ve eğitim verisinde bu oran gerçekten yarıya yakın olduğu için isabetli görünmüştür.

**İkincisi, model yabancı veriye eğitim döneminin içeriğini taşımaktadır.**

NLST tarama raporlarının **%18,1'inde Covid-19 pnömonisinden söz edilmektedir.**

NLST taraması Covid-19 salgınından yıllar önce tamamlanmıştır. Bu görüntülerde Covid pnömonisi bulunması mümkün değildir. Model, eğitim verisinin yazıldığı dönemin baskın klinik gündemini, o gündemle hiçbir ilgisi olmayan görüntülere aktarmaktadır.

Aynı şekilde tiroid, meme ve kafa içi yapılardan söz etme oranları iki kohortta neredeyse aynıdır. Model, hangi görüntüye baktığından bağımsız olarak benzer içerikte metin üretmektedir.

**Bu iki gözlem birlikte şunu söyler:** modelin ürettiği rapor, önündeki tomografiden çok eğitim verisindeki raporların ortalamasına benzemektedir. Tanıdık veride bu ortalama gerçeğe yakın düştüğü için model kalibre görünmekte, yabancı veride ise aynı ortalama açıkça yanlış hale gelmektedir.

### 6.4 Eğitim verisinden taşınan içeriğe örnekler

Aşağıdaki ifadeler yabancı verideki raporlarda geçmektedir ve bu görüntülerde bulunmaları mümkün değildir. Sayılar 2.500 rapor içindeki sıklıklarıdır.

İçerikler iki gruba ayrılmalıdır. Bir kısmı bu görüntülerde **fiziksel olarak bulunamaz**; bir kısmı ise mümkündür ama tarama raporunun amacı dışındadır.

| Taşınan içerik | Rapor | Değerlendirme |
|---|---:|---|
| Covid-19 pnömonisi | 452 (%18,1) | **Anakronik.** Tarama salgından yıllar önce yapıldı |
| "Pandemi süreci" vurgusu | 54 (%2,2) | **Anakronik.** Aynı gerekçe |
| Beyin ve kafa içi yapılar | 19 (%0,8) | **Alan dışı.** Görüntüleme kapsamında bulunmaz |
| Meme protezi ve jinekomasti | 59 (%2,4) | Amaç dışı. Meme dokusu kesitlerde kısmen görülebilir |
| Tiroid ultrason önerisi | 87 (%3,5) | Amaç dışı. Tiroid alt ucu kesitlere girebilir |
| PET-BT önerisi | 18 (%0,7) | Amaç dışı. Şüpheli bulgu sonrası klinik olarak mümkündür |

İlk üç satır kesin hatadır. Son üç satır ise tarama protokolünün kapsamı dışında kalan ama tomografi kesitlerinde kısmen görülebilen yapılara ilişkindir; bunlar tek başına yanlışlık kanıtı değildir, modelin tarama görevine odaklanmadığını gösterir.

Örnek cümleler:

> *"However, during the pandemic process, Covid-19 pneumonia cannot be ruled out definitively."*

> *"Since the study was performed in the parenchyma of the opposite, bilateral gynecomasty was observed in both retroareolar regions."*

Birinci cümle, modelin eğitim verisinin yazıldığı dönemin klinik gündemini doğrudan taşımaktadır. İkinci cümlenin ilk yarısı ise anlamsızdır ve bunu takip eden bulgu, tarama protokolünde değerlendirilmeyen bir yapıya aittir.

Bu ifadeler tek tek nadir görünebilir, ancak toplandığında raporların dörtte birinden fazlasını etkilemektedir. Daha önemlisi, hepsi aynı yöne işaret etmektedir: metin, önündeki görüntüden değil eğitim verisinin dilinden üretilmektedir.

Dağılım farkı, metin üretimindeki bozulmayı açıklamaktadır. Ancak klinik içerikteki başarısızlığı açıklamamaktadır, çünkü bu başarısızlık modelin kendi eğitim dağılımında da gözlenmiştir. Eksik olan, görüntüden hastaya özgü bilgi çıkarma yeteneğidir; bu yetenek yabancı veride kaybolmuş değildir, tanıdık veride de gösterilememiştir.

---

## 7. Değerlendirme

Bu çalışmanın güvenle gösterdiği şudur: **mevcut rapor üretimi ile otomatik çıkarım hattının birleşimi, tarama triyajı için kullanılamaz durumdadır.**

Model, bir yıl içinde kanser tanısı alan 34 hastanın 33'ünde pulmoner malignite bildirmemiş, buna karşılık kanser tanısı almamış 108 hastada bildirmiştir. Nodül bildirimi ayırt edici değildir çünkü model hastaların beşte dördüne nodül yazmaktadır. Youden J değeri sıfırın altındadır ve bu, hem hasta düzeyinde hem tek indeks tarama kurgusunda korunmaktadır.

Bu sonucun tümüyle BTB3D görüntü modeline atfedilemeyeceği belirtilmelidir. Ölçüm zinciri iki halkadan oluşmaktadır: modelin ürettiği rapor ve o rapordan bulgu çıkaran otomatik hat. İkinci halkanın hataları çözümleme sırasında saptanmış ve düzeltilmiştir, ancak tümüyle giderildiği iddia edilemez. Görüntü modelinin malignite tespit yeteneği hakkında kesin bir hüküm için, çıkarım hattından bağımsız bir değerlendirme gerekir.

Modelin kaydedilmesi gereken bir üstünlüğü vardır: karşılaştırma sistemlerinden birinde bol miktarda bulunan şablon artıkları ve doldurulmamış alanlar BTB3D'de hiç görülmemektedir. Bu genel bir biçim üstünlüğü değildir; üçüncü sistem aynı ölçütlerde temiz olup bağımsız değerlendirmede anlamsız içerik oranı daha düşüktür. Her durumda bir tarama raporunun değeri biçiminden değil, doğru hastayı işaret edebilmesinden gelir.

Karşılaştırma sistemlerinin sonuçları, ölçülen başarısızlığın görevin doğasından kaynaklanmadığını düşündürmektedir. Düzeltilmiş ölçütle hiçbir sistem tek başına şanstan ayırt edilebilir bir sinyal üretememiştir; ancak Astra ile BTB3D arasındaki eşleştirilmiş fark, denenen dört çözümleme kurgusunun dördünde de sıfırı içermeyen bir aralık vermiştir. Yani aynı veride, aynı ölçüm hattıyla daha iyi bir sonuç elde edilebilmektedir.

Başarısızlık, veri kümesinin yabancılığıyla da açıklanamaz. Model kendi eğitim verisinin ayrılmış bölümünde de hastaya özgü bilgi üretememiştir. Yabancı veride ek olarak gözlenen şey, metin üretim kalitesinin bozulması ve eğitim dönemine ait içeriğin ilgisiz görüntülere taşınmasıdır; tarama raporlarının %18,1'inde, o görüntülerin çekildiği dönemde var olmayan bir hastalıktan söz edilmektedir.

Üç sistemin birbiriyle şans düzeyinde uyuşması ayrıca önemlidir. Bu tür sistemlerin çıktıları, aralarındaki tutarlılık sınanmadan güvenilir kabul edilmemelidir.

---

## 8. Çalışmanın sınırları

**Tarama kohortunda kanser etiketi gelecekteki bir sonuçtur.** Bir hastanın takip süresinde kanser tanısı alması, tarama anında görünür bir lezyon bulunduğu anlamına gelmez. Bu nedenle kusursuz bir okuyucu için bile duyarlılık düşük çıkabilir. Tanısı bir yıl içinde konan hastalarla yapılan katmanlama bu etkiyi azaltır ama tümüyle ortadan kaldırmaz.

**İnsan yazımı referans rapor yoktur.** Karşılaştırma sistemlerinin çıktıları da yapay zekâ üretimidir. Bunlar arasındaki uyum "doğruluk" değil "tutarlılık" olarak yorumlanmalıdır.

**Ters yön bulgusunun mekanizması açıklanamamıştır.** İstatistiksel olarak gösterilmiş bir ilişkidir; nedensel bir yorum yapılmamaktadır ve bağımsız bir kohortta doğrulanması gerekir.

**Değerlendirme geliştirme kümeleriyle sınırlıdır ve bir dış geçerlilik iddiası taşımaz.** Nihai test kümesi bu çalışmada kullanılmamıştır. Ancak bu küme, proje kayıtlarına göre daha önce etiketli çözümlemeye ve eşik denemelerine maruz kalmıştır; dolayısıyla "hiç görülmemiş bağımsız test kümesi" olarak sunulamaz. Temiz bir dış geçerlilik için ayrı bir kohort gerekir.

**Çıkarım hattı otomatiktir ve sistemlere göre farklı güvenilirlikte çalışmaktadır.** Bağımsız ikincil değerlendirmeyle uyum BTB3D raporlarında kappa 0,895, MedMo'da 0,955, Astra'da ise yalnızca 0,624'tür. Astra ile ilgili sayılar bu nedenle daha az kesindir.

**Malignite kavramının otomatik tanımı geniştir.** İkincil değerlendirme, üç sistemin de raporlarında malignite şüphesini otomatik hattın bildirdiğinden çok daha seyrek bulmuştur. Mutlak oranlar bu sınırla okunmalı; sistemler arası karşılaştırma ise aynı hat hepsine uygulandığı için geçerlidir.

**Ölçüm hatası sistemlere göre farklıdır.** Otomatik hattın bağımsız değerlendirmeyle uyumu BTB3D'de kappa 0,895, MedMo'da 0,955, Astra'da 0,624'tür. Aynı hattın üç sisteme uygulanmış olması eşit hata anlamına gelmez; Astra ile ilgili sayılar daha az kesindir ve sistemler arası fark için elle doğrulanmış ortak bir alt küme gerekir.

**Bildirilen p değerleri keşifseldir.** Birden çok gösterge, iki anatomik tanım ve iki toplama kuralı denenmiştir; hangisinin önceden birincil sonlanım olduğu ilan edilmemiştir. Çoklu karşılaştırma düzeltmesi uygulanmamıştır.

**Kırk vakalık ikincil değerlendirme yönü desteklemekte, doğrulamamaktadır.** Örneklem 20 kanserli ve 20 kanser olmayan hastadan katmanlı olarak seçilmiştir (sabit tohum). Bu büyüklükte duyarlılık ve Youden J tahminlerinin belirsizliği geniştir; sonuçlar tanımlayıcıdır.

**Tarama zamanlaması tam denetlenememiştir.** Serilerin tanı tarihine göre konumu veri kümesinde doğrudan verilmemektedir; tanı sonrası görüntülerin dışlandığı kesin olarak gösterilememiştir. Tek indeks tarama çözümlemesi bu etkiyi azaltmaktadır.

**İkincil değerlendirici bir dil modelidir**, radyolog değildir. Sonuçları otomatik hattın tekrarlanabilirliğini destekler, klinik uzman görüş birliği yerine geçmez.

**Karşılaştırma sistemlerinin görev tanımları farklı olabilir.** Üç sistem aynı amaçla eğitilmemiş olabilir; özellikle çok kısa raporlar üreten sistemin farklı bir kullanım senaryosu bulunabilir. Bu bölüm bir sıralama değil, bağlam sağlama amacı taşımaktadır.
