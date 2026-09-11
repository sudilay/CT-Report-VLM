# Diyagramlar

CT-Report-VLM devir diyagramları. Depo kökündeki `README.md` bunların SVG sürümlerini
gösterir; burada kaynaklar ve bakım sözleşmesi vardır.

## Bakım sözleşmesi

Her diyagramın **tek bir kanonik kaynağı** vardır. Üretilen dosyalar elle düzenlenmez;
kaynak değişince yeniden üretilir.

| Diyagram | Kanonik kaynak | Üretilen | Üretim komutu |
|---|---|---|---|
| Metin işleme hattı | `metin_hatti.html` | `metin_hatti.svg` | `python tools/diyagram_svg_disa_aktar.py docs/diagrams/metin_hatti.html` |
| Veri açmazı | `veri_acmazi.html` | `veri_acmazi.svg` | `python tools/diyagram_svg_disa_aktar.py docs/diagrams/veri_acmazi.html` |
| Karar aşamaları | `karar_asamalari.html` | `karar_asamalari.svg` | `python tools/diyagram_svg_disa_aktar.py docs/diagrams/karar_asamalari.html` |
| Denenen yollar | `denenen_yollar.html` | `denenen_yollar.svg` | `python tools/diyagram_svg_disa_aktar.py docs/diagrams/denenen_yollar.html` |
| Metin işleme hattı, ayrıntılı | `metin_isleme_hatti.dataflow.json` | `metin_isleme_hatti.html` | `archify deliver dataflow docs/diagrams/metin_isleme_hatti.dataflow.json docs/diagrams/metin_isleme_hatti.html --quality showcase` |

Hepsini birden yenilemek için: `python tools/diyagram_svg_disa_aktar.py --tumu`

İlk dördünde kanonik kaynak HTML'dir: tek dosyalık, bağımsız, açık tema, elle yazılmış
SVG. Tarayıcıda açılır, doğrudan düzenlenir; derleme adımı yoktur. Beşincinin kanonik
kaynağı JSON'dur ve HTML ondan üretilir; HTML elle düzenlenmez.

## İçerik

| Diyagram | Ne gösterir |
|---|---|
| Metin işleme hattı | 9 düğüm, üç bölge, özet |
| Veri açmazı | üç kohortun, ana hipotez için gereken üç veri gereksinimini karşılama matrisi |
| Karar aşamaları | beş aşamanın sırası ve her aşamada kaç yolun kapandığı |
| Denenen yollar | yedi kategori, on dört kapanan yol ve her birini kapatan ölçüm, bir açık yol |
| Metin işleme hattı, ayrıntılı | 15 düğüm, beş aşama, rehberli görünümler |

Ayrıntılı sürüm [archify](https://github.com/tt-a1i/archify) ile, diğer dördü
[diagram-design](https://github.com/cathrynlavery/diagram-design) grameriyle üretildi.

## Bilinmesi gerekenler

**Ayrıntılı hattın SVG'si depoda tutulmaz.** archify çıktısı bütün renklerini tek bir
`<style>` bloğundan alır; o blok temizlenirse diyagram boş render eder, bu yüzden
gömülmez. Gerekirse archify görüntüleyicisinin Export menüsünden alınır.

**Font.** Gömülü SVG'ler dış font yükleyemediğinde sistem yazı tipine düşer. Ölçüldü:
yerleşim bozulmuyor, hiçbir yazı kutusundan taşmıyor.

**Denenen yollar diyagramı geniştir** (1760 birim). Dar bir sütunda etiketleri küçülür;
bu yüzden depo kökündeki README'ye gömülmez, burada tam boyutta durur.

## Doğrulama

Her HTML dosyası `diagram-design` paketinin `self_check.py` ve `verify-geometry.py`
betikleriyle denetlendi: erişilebilirlik sözleşmesi (`role="img"`, `<title>`, `<desc>`)
ve etiket geometrisi kuralları sağlanıyor. archify çıktısı kendi `validate --quality
showcase` kapısından geçti.

Diyagramlardaki sayılar `DONDURMA_RAPORU.md` bölüm 2, 4 ve 5 ile `reports/` altındaki
değerlendirme raporlarıyla karşılaştırılarak doğrulandı.
