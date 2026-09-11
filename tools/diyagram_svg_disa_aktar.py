# -*- coding: utf-8 -*-
"""Diyagram HTML dosyasindan gomulebilir SVG cikarir.

`docs/diagrams/*.html` dosyalari tek dosyalik, bagimsiz diyagram kaynaklaridir.
Markdown icine gomulen `.svg` sureumleri bu betikle uretilir; elle duzenlenmez.

Yaptiklari:
  1. HTML icindeki ilk <svg> blogunu alir (editoryal basliklar ve kartlar disarida
     kalir, gomulen sey yalniz cizimdir).
  2. Google Fonts @import'unu <defs><style> icine ekler. Ayraclar &amp; olarak
     kacirilir; bagimsiz .svg kati XML olarak ayristirilir ve cıplak & dosyayi bozar.
  3. rgba() renklerini hex + -opacity ikilisine cevirir. Kati SVG 1.1 tuketicileri
     (ornegin PowerPoint) rgba'yi tanimaz ve opak siyah boyar.
  4. Basa XML bildirimi koyar.

Kullanim:
    python tools/diyagram_svg_disa_aktar.py docs/diagrams/metin_hatti.html
    python tools/diyagram_svg_disa_aktar.py --tumu        # docs/diagrams/*.html
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DIYAGRAM_DIZINI = KOK / "docs" / "diagrams"

# archify ciktisi haric tutulur: renklerini tek bir <style> blogundan alir,
# blok temizlenirse bos render eder. Onun SVG'si archify goruntuleyicisinden alinir.
HARIC = {"metin_isleme_hatti.html"}

FONTLAR = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Instrument+Serif:ital@0;1&amp;"
    "family=Geist:wght@400;500;600&amp;"
    "family=Geist+Mono:wght@400;500;600&amp;display=swap');"
)

RGBA = re.compile(
    r'(fill|stroke)="rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d*\.?\d+)\s*\)"'
)


def disa_aktar(html_yolu: Path) -> Path:
    html = io.open(html_yolu, encoding="utf-8").read()

    eslesme = re.search(r"<svg\b.*?</svg>", html, re.S)
    if not eslesme:
        raise SystemExit("HATA: %s icinde <svg> bulunamadi" % html_yolu.name)
    svg = eslesme.group(0)

    if 'xmlns="http://www.w3.org/2000/svg"' not in svg:
        svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    if "viewBox" not in svg:
        raise SystemExit("HATA: %s icinde viewBox yok, tahmin edilmez" % html_yolu.name)

    # Mevcut <defs> varsa icine birlestir; ikinci bir <defs> acma.
    if "<defs>" in svg:
        svg = svg.replace("<defs>", "<defs>\n          <style>%s</style>" % FONTLAR, 1)
    else:
        svg = re.sub(r"(<svg\b[^>]*>)",
                     r"\1\n<defs><style>%s</style></defs>" % FONTLAR, svg, count=1)

    svg = RGBA.sub(
        lambda m: '{0}="#{1:02x}{2:02x}{3:02x}" {0}-opacity="{4}"'.format(
            m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5)
        ),
        svg,
    )
    svg = re.sub(r'(fill|stroke)="transparent"', r'\1="none"', svg)

    hedef = html_yolu.with_suffix(".svg")
    io.open(hedef, "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n"
    )
    return hedef


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", nargs="*", type=Path, help="diyagram HTML dosyalari")
    ap.add_argument("--tumu", action="store_true",
                    help="docs/diagrams altindaki uygun butun HTML dosyalarini isle")
    a = ap.parse_args()

    if a.tumu:
        hedefler = sorted(y for y in DIYAGRAM_DIZINI.glob("*.html")
                          if y.name not in HARIC)
    else:
        hedefler = a.html
    if not hedefler:
        ap.error("dosya verin veya --tumu kullanin")

    for y in hedefler:
        if y.name in HARIC:
            print("atlandi (archify ciktisi):", y.name)
            continue
        cikti = disa_aktar(y)
        print("yazildi:", cikti.relative_to(KOK), "·", cikti.stat().st_size, "bayt")
    return 0


def _kendi_denetimi() -> None:
    """assert tabanli kucuk denetim: rgba cevrimi ve & kacirma."""
    ornek = '<fill="rgba(45,49,66,0.08)"'
    assert RGBA.sub(
        lambda m: '{0}="#{1:02x}{2:02x}{3:02x}" {0}-opacity="{4}"'.format(
            m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5)),
        'fill="rgba(45,49,66,0.08)"') == 'fill="#2d3142" fill-opacity="0.08"'
    assert "&amp;" in FONTLAR and "?family" in FONTLAR
    assert ornek  # kullanilmayan degisken uyarisini bastir
    print("kendi denetimi gecti")


if __name__ == "__main__":
    if "--kendi-denetimi" in sys.argv:
        _kendi_denetimi()
    else:
        raise SystemExit(main())
