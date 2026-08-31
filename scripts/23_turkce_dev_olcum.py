# -*- coding: utf-8 -*-
"""Turkce cikarimi RadTr `dev` uzerinde olcer (TASK-14 / adim 6).

`dev` AYAR KUMESIDIR: sinirsiz bakilir, duzeltme serbesttir. `test`in 56 belgesi
bu betikten erisilemez.

IKI OLCUM - ayri sorular, ayri paydalar:

  D1 · SOZLUK KAPSAMASI (duyarlilik yaklasimi)
     RadTr'nin isaretledigi her altin span icin: bizim Turkce yuzeylerimizden
     biri o span'i yakaliyor mu? "Sozlugumuz uzmanin gordugunu goruyor mu"
     sorusudur. Altin span'in KAVRAMI RadTr'de yok - yalnizca tipi ve kesinligi
     var - bu yuzden kavram dogrulugu burada olculemez, KAPSAMA olculur.

  D2 · KESINLIK ATAMASI  ← ipucu sozlugunun gercek sinavi
     Altin kesinlik RadTr'nin KENDI etiketinden gelir (Obs_Present / Obs_Absent /
     Obs_Uncertain) ve bizim sozlugumuzden BAGIMSIZDIR. Dolayisiyla bu olcum
     dairesel degildir.

     Bizim atamamiz: span'in bulundugu cumleye Turkce ipuclari uygulanir,
     kapsam icindeyse ipucunun sonucu atanir, degilse `present`.

⚠ YON: Turkcede negasyon ipuclarinin %97'si cumlenin SONUNDA (Ingilizcede
   %19,9). Bu yuzden kapsam GERI yonlu kurulur: ipucu, kendisinden ONCEKI
   varliklari olumsuzlar. Ileri yonlu bir kurulum Turkcede negasyonun neredeyse
   tamamini kacirir.

⚠ D30: teknik cekince kesinligi DEGISTIRMEZ. Turkcede bu daha da kritik -
   teknik cekince (961 anma) gercek negasyondan (843) BUYUK ve hepsi -ma/-me
   eki tasiyor.

Kullanim: .venv/Scripts/python.exe scripts/23_turkce_dev_olcum.py
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
BS = chr(92)
CUMLE = re.compile(r"(?<=[.;])\s+")


def derle(desen: str) -> re.Pattern:
    """Turkce sondan eklemeli -> desen BASTA sinirli, sonda serbest."""
    if desen.startswith("\\("):          # parantez-soru gibi ham desenler
        return re.compile(desen, re.I)
    return re.compile(BS + "b(?:" + desen + ")", re.I)


def yukle():
    y = yaml.safe_load((ROOT / "configs" / "turkce_yuzeyler_taslak.yaml")
                       .read_text(encoding="utf-8"))
    i = yaml.safe_load((ROOT / "configs" / "turkce_ipuclari_taslak.yaml")
                       .read_text(encoding="utf-8"))
    yuzey = {k: derle(v["desen"]) for k, v in y["yuzeyler"].items()
             if v["radtr"] > 0}
    ipucu = {}
    for bolum, girdiler in i["bolumler"].items():
        if bolum == "negasyon_olculup_alinmayan":
            continue                      # destegi sifir - alinmadi
        for ad, g in girdiler.items():
            if g["korpus"] == 0:
                continue
            ipucu.setdefault(bolum, []).append((ad, derle(g["desen"]),
                                                g.get("sonuc")))
    return yuzey, ipucu


def kesinlik_ata(cumle: str, span_bas: int, ipucu: dict) -> tuple[str, str]:
    """Bir span'in kesinligini cumledeki ipuclarindan belirler.

    ONCELIK SIRASI - Ingilizce ctx-1.1 ile ayni:
      belirsizlik_oncelikli -> teknik_cekince(etkisiz) -> negasyon -> belirsizlik
      -> cikarim_ifadesi -> varsayilan present
    """
    def bulunanlar(bolum):
        return [(ad, m) for ad, r, _ in ipucu.get(bolum, [])
                for m in r.finditer(cumle)]

    # 1) "ekarte edilemez" - icinde olumsuzluk eki var, negasyondan ONCE bakilir
    for ad, m in bulunanlar("belirsizlik_oncelikli"):
        return "uncertain", ad

    # 2) TEKNIK CEKINCE (D30): kesinligi DEGISTIRMEZ ama negasyon ipucunun
    #    kendi kapsamini da tuketir - "yapilamamistir" bir bulgu yoklugu degil.
    teknik = [m.span() for _, m in bulunanlar("teknik_cekince")]

    # 3) NEGASYON - GERI yonlu (%97 sonda). Ipucu, kendisinden ONCEKI span'i
    #    olumsuzlar. Teknik cekince kapsamindaki ipucular sayilmaz.
    for ad, m in bulunanlar("negasyon"):
        if any(tb <= m.start() <= ts for tb, ts in teknik):
            continue
        if span_bas < m.start():
            return "absent", ad

    # 4) BELIRSIZLIK - KAPSAMLI, cumle geneline yayilmaz.
    #    Ilk surum cumlede parantez-soru gorunce TUM varliklari 'uncertain'
    #    yapiyordu. Olculdu: altin 'present' span'larin 41/450'sinin cumlesinde
    #    parantez-soru var ve hatamiz TAM 41 satirdi - birebir bu sebepti.
    #
    #    Radyoloji Turkcesinde parantez bir AYIRICI TANI onerisidir:
    #      "Mozaik atenuasyon paterni (kucuk hava yolu hastaligi?)"
    #      -> mozaik atenuasyon MEVCUT, kucuk hava yolu hastaligi BELIRSIZ
    #    Belirsizlik parantezin ICINDEDIR, cumlenin tamaminda degil.
    #    Ayni kapsam kurali PARANTEZSIZ soru icin de gecerli: "PTE? PNOMONI?"
    #    yalnizca kendi terimini belirsiz yapar, cumledeki her seyi degil.
    for ad, m in bulunanlar("belirsizlik"):
        if ad in ("parantez_soru", "soru_isareti"):
            if m.start() <= span_bas <= m.end():
                return "uncertain", ad
            continue
        return "uncertain", ad
    for ad, m in bulunanlar("cikarim_ifadesi"):
        return "present", ad
    return "present", "varsayilan"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", default="dev", help="train | dev  (test KAPALI)")
    a = ap.parse_args()
    if a.bolum not in ("train", "dev"):
        sys.exit("DURDU: test bolumu ablasyon icin dokunulmazdir.\n"
                 "  Gerekce: reports/turkce_bolunme_dondurma.md")

    yuzey, ipucu = yukle()
    belgeler = [json.loads(l) for l in
                (PROC / "radtr_toraks.jsonl").open(encoding="utf-8")
                if json.loads(l)["kaynak_bolum"] == a.bolum]
    print(f"olcum: {a.bolum} · {len(belgeler)} belge · "
          f"{len(yuzey)} kavram yuzeyi · "
          f"{sum(len(v) for v in ipucu.values())} ipucu\n")

    # ---------------- D1 · sozluk kapsamasi ----------------
    tut = Counter()
    kacan = Counter()
    for b in belgeler:
        for v in b["varliklar"]:
            if v["bizim_tip"] is None:        # Obs_Technical / Obs_Advice
                continue
            s = v["metin"]
            tut["toplam"] += 1
            if any(r.search(s) for r in yuzey.values()):
                tut["yakalandi"] += 1
            else:
                kacan[s.lower().strip()] += 1

    print("=" * 62)
    print("D1 · SOZLUK KAPSAMASI  (altin span'i yuzeylerimiz yakaliyor mu)")
    print("=" * 62)
    print(f"  altin span {tut['toplam']}  yakalanan {tut['yakalandi']}  "
          f"KAPSAMA %{100*tut['yakalandi']/tut['toplam']:.1f}")
    print(f"\n  en sik kacanlar:")
    for s, n in kacan.most_common(15):
        print(f"    {n:>3}  {s[:66]}")

    # ---------------- D2 · kesinlik atamasi ----------------
    kars = Counter()
    hata_ornek = []
    for b in belgeler:
        cumleler = [c for c in CUMLE.split(b["metin"]) if c.strip()]
        for v in b["varliklar"]:
            altin = v["bizim_kesinlik"]
            if altin is None:
                continue
            s = v["metin"].strip()
            c = next((c for c in cumleler if s and s[:24] in c), None)
            if c is None:
                kars["cumle_bulunamadi"] += 1
                continue
            bizim, ad = kesinlik_ata(c, c.find(s[:24]), ipucu)
            kars[(altin, bizim)] += 1
            if altin != bizim and len(hata_ornek) < 8:
                hata_ornek.append((altin, bizim, ad, c[:96]))

    print("\n" + "=" * 62)
    print("D2 · KESINLIK ATAMASI  (altin RadTr'nin KENDI etiketinden)")
    print("=" * 62)
    siniflar = ["present", "absent", "uncertain"]
    baslik = "altin -> bizim"
    print(f"  {baslik:<16}" + "".join(f"{c:>11}" for c in siniflar))
    for al in siniflar:
        print(f"  {al:<16}" + "".join(f"{kars[(al,bz)]:>11}" for bz in siniflar))

    print()
    for cl in siniflar:
        tp = kars[(cl, cl)]
        fn = sum(kars[(cl, x)] for x in siniflar if x != cl)
        fp = sum(kars[(x, cl)] for x in siniflar if x != cl)
        p = tp / (tp + fp) if tp + fp else 0
        r = tp / (tp + fn) if tp + fn else 0
        f = 2 * p * r / (p + r) if p + r else 0
        print(f"  {cl:<11}destek{tp+fn:>5}  P %{100*p:>5.1f}  R %{100*r:>5.1f}  "
              f"F1 %{100*f:>5.1f}")
    top = sum(kars[(x, y)] for x in siniflar for y in siniflar)
    dg = sum(kars[(x, x)] for x in siniflar)
    print(f"\n  dogruluk %{100*dg/top:.1f}  (n={top})")
    if kars["cumle_bulunamadi"]:
        print(f"  UYARI cumlesi bulunamayan span: {kars['cumle_bulunamadi']}")

    print("\n  hata ornekleri (altin -> bizim · ipucu):")
    for al, bz, ad, c in hata_ornek:
        print(f"    {al:>9} -> {bz:<9} [{ad}]  {c}")


if __name__ == "__main__":
    main()
