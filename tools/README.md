# Ölçüm araçları

Sözlüklerdeki `korpus` sayılarını **ölçen** ve YAML'a geri yazan araçlar.
Sayım yalnızca **train**'de yapılır (D11/D16).

| Araç | Ne yapar |
|---|---|
| `olc_sozluk.py <dosya>` | `anatomi_sozlugu.yaml` / `bulgu_sozlugu.yaml` sayılarını ölçer. Desenleri `\b…\b` ile sarar |
| `olc_ipucu.py` | `ipucu_sozlugu.yaml` sayılarını ölçer. Desenler kendi sınırlarını taşır, sarılmaz |
| `terim_madeni.py` | Aday terim madeni — frekans ve kapsama |
| `negex_tara.py` | İthal NegEx listesinin korpustaki karşılığını ölçer |

Belge araçları:

| Araç | Ne yapar |
|---|---|
| `diyagram_svg_disa_aktar.py` | `docs/diagrams/*.html` içindeki çizimi gömülebilir SVG olarak dışa aktarır. `--tumu` hepsini yeniler |

## ⚠ Kullanmadan önce

**Bu araçlar YAML'ı ÜZERİNE YAZAR.** Çalıştırmadan önce `git status` temiz olsun
ki hatalı bir sonuç `git checkout` ile geri alınabilsin.

**Bilinen tuzak — kelime sınırı.** `anatomi`/`bulgu` desenleri çıplak terimlerdir ve
`\b` ile sarılmalıdır; sarılmazsa `stent` ifadesi `consistent` içinde eşleşir ve sayı
812 yerine 6.435 çıkar. `ipucu` desenleri ise `";"` gibi noktalama içerdiğinden
sarılamaz. İki aracın ayrı durmasının sebebi budur.

Bu ikisini tek araçta birleştirme denemesi 2026-08-27'de yapıldı ve sözlükleri
bozdu (önce şişmiş sayılar, sonra sıfırlar); araç kaldırıldı, sözlükler
`git checkout` ile geri alındı. Birleştirmeden önce **bilinen bir değere karşı
kendini sınayan** bir kontrol eklenmelidir.
