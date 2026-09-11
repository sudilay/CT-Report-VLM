# Diyagramlar

CT-Report-VLM devir diyagramları. Depo kökündeki `README.md` bunların SVG sürümlerini
gösterir; burada kaynaklar ve nasıl güncellenecekleri vardır.

Her diyagram iki dosyadır:

- `.html` — kaynak. Tek dosyalık, bağımsız, açık tema. Tarayıcıda açılır; sunucu,
  kurulum veya derleme gerekmez. Değişiklikler burada yapılır.
- `.svg` — yalnız çizim. Markdown içine gömülen sürüm, `.html` dosyasından dışa aktarılır.

## Dosyalar

| Konu | Kaynak | Çizim | İçerik |
|---|---|---|---|
| Metin işleme hattı | `metin_hatti.html` | `metin_hatti.svg` | 9 düğüm, üç bölge, özet |
| Metin işleme hattı, ayrıntılı | `metin_isleme_hatti.html` | `metin_isleme_hatti.svg` | 15 düğüm, beş aşama, rehberli görünümler |
| Veri açmazı | `veri_acmazi.html` | `veri_acmazi.svg` | kohort ve gereksinim matrisi |
| Karar aşamaları | `karar_asamalari.html` | `karar_asamalari.svg` | beş aşamanın zaman çizgisi |
| Denenen yollar | `denenen_yollar.html` | `denenen_yollar.svg` | yedi dal, on dört kapanan yol, bir açık yol |

## Nasıl üretildi

Ayrıntılı hat [archify](https://github.com/tt-a1i/archify) ile üretildi; kaynağı
`metin_isleme_hatti.dataflow.json` dosyasıdır ve `archify deliver` ile yeniden
derlenebilir. Diğer dördü
[diagram-design](https://github.com/cathrynlavery/diagram-design) grameriyle elle
yazılmış SVG'dir ve derleme adımı yoktur.

## Bilinmesi gerekenler

**Ayrıntılı hattın SVG'si gömülmez.** Bütün renklerini tek bir `<style>` bloğundan alır;
o blok temizlenirse diyagram boş render eder. Diğer dört SVG renkleri öğe üstünde taşır
ve güvenle gömülür.

**Font.** Gömülü SVG'ler dış font yükleyemediğinde sistem yazı tipine düşer. Ölçüldü:
yerleşim bozulmuyor, hiçbir yazı kutusundan taşmıyor.

**Denenen yollar diyagramı geniştir** (1760 birim). Dar bir sütunda etiketleri küçülür;
tam boyutta görmek için çizimi ayrı açın.

## Doğrulama

Her dosya `diagram-design` paketinin `self_check.py` ve `verify-geometry.py` betikleriyle
denetlendi: erişilebilirlik sözleşmesi (`role="img"`, `<title>`, `<desc>`) ve etiket
geometrisi kuralları sağlanıyor.

Diyagramlardaki sayılar `DONDURMA_RAPORU.md` bölüm 2, 4 ve 5 ile
`reports/` altındaki değerlendirme raporlarından alınmıştır.
