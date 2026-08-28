# TASK-13 / C1 — Yapısal Değişmezler

**Altın açıklama gerektirmez.** Bu ölçütler *"cevap doğru mu"* diye sormaz, *"sistem kendi kuralına uyuyor mu"* diye sorar. Geçmeleri sistemin doğru olduğunu **göstermez**; geçmemeleri sistemin kendi tasarımına uymadığını gösterir — o kesin hatadır.

Kesinlik, duyarlılık ve F1 (K4–K10) insan işaretlemesi bekliyor.

| Kod | Ölçüt | Eşik | Sonuç | Payda | İhlal | Durum |
|---|---|---|---|---|---|---|
| **K11** | 'cannot be excluded' kapsamindaki varlik 'absent' DEGIL | 100% | **100.0%** | 843 | 0 | gecti |
| **K12** | teknik cekince TEK BASINA 'absent' uretmiyor (bagimsiz negasyon yokken) | 100% | **100.0%** | 37,659 | 0 | gecti |
| **K13** | 'no X or Y' -> ikinci gozlem de 'absent' | 90% | **99.6%** | 10,826 | 43 | gecti |
| **K14** | 'absent'/'uncertain' satirlarda assertion_cue dolu | 100% | **100.0%** | 188,520 | 0 | gecti |
| **K15** | YALNIZCA ardil ipuclu cumlede 'absent' yakalandi | 85% | **98.9%** | 25,606 | 279 | gecti |

**K12 ek:** ayni cumlede bagimsiz negasyon calisan: 2,700 cumle

**K13 — ihlal örnekleri:**

> In the upper abdominal sections within the image, hypodense lesions belonging to multiple metastases are obser
> Mosaic attenuation pattern in both lungs (small airway disease? small vessel disease?) No mass or infiltrative
> Sequelae parenchymal changes in both lungs, diffuse mild ectasia and minimal peribronchial thickness increases

**K15 — ihlal örnekleri:**

> As far as can be observed in the sections, the right lobe of the liver was not observed (operated).
> In the sections passing through the upper abdomen, the gallbladder was not observed in the lodge.
> Contrast material given to the patient by lymphangiography was not detected to pass into the right effusion.

**Sonuç: tüm değişmezler geçti**
