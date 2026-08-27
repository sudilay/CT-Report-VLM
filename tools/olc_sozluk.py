# -*- coding: utf-8 -*-
"""Sozlukteki her kavramin korpus destegini OLCER ve YAML'a geri yazar.

Amac: 'korpus' alanindaki hicbir sayi tahmin olmasin. Elle yazilmis bir sayi
olcumle celisiyorsa olcum kazanir.
Sayim YALNIZCA train'de (D11).
"""
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(".")
YOL = ROOT / "configs" / sys.argv[1]
ALAN = sys.argv[2] if len(sys.argv) > 2 else "kavramlar"

sent = pd.read_parquet(ROOT / "data/processed/sentences.parquet")
reps = pd.read_parquet(ROOT / "data/processed/reports_study_level.parquet",
                       columns=["study_id", "split"])
train = sent.merge(reps, on="study_id", how="left").query("split == 'train'")
T = train.text
print(f"train cumle: {len(T):,}")

ham = YOL.read_text(encoding="utf-8")
veri = yaml.safe_load(ham)

sonuc = {}
for kavram, t in veri[ALAN].items():
    pat = "|".join(f"(?:{p})" for p in t["desenler"])
    n = int(T.str.contains(rf"\b(?:{pat})\b", case=False, regex=True).sum())
    sonuc[kavram] = n

print(f"\n{'kavram':<28} {'yazili':>8} {'olculen':>8}  durum")
degisen = 0
for kavram, n in sorted(sonuc.items(), key=lambda x: -x[1]):
    yazili = veri[ALAN][kavram].get("korpus")
    if yazili is None:
        durum = "YENI"
    elif yazili == n:
        durum = "ok"
    else:
        durum = f"DUZELTILDI ({yazili} -> {n})"
        degisen += 1
    isaret = "  <-- ZAYIF" if n < 100 else ""
    print(f"{kavram:<28} {str(yazili):>8} {n:>8}  {durum}{isaret}")

print(f"\ntoplam kavram: {len(sonuc)} · duzeltilen: {degisen}")
print(f"100 cumleden az destekli: {sum(1 for n in sonuc.values() if n < 100)}")
print(f"sifir destekli          : {sum(1 for n in sonuc.values() if n == 0)}")

# YAML'i satir bazli guncelle (yorumlar ve sira korunsun)
satirlar = ham.split("\n")
aktif = None
for i, s in enumerate(satirlar):
    m = re.match(r"^  ([a-z_0-9]+):\s*$", s)
    if m and m.group(1) in sonuc:
        aktif = m.group(1)
        continue
    if aktif and re.match(r"^    korpus:", s):
        satirlar[i] = re.sub(r"(korpus:\s*)\d+", rf"\g<1>{sonuc[aktif]}", s)
        aktif = None
    elif aktif and re.match(r"^  \S", s):
        aktif = None

YOL.write_text("\n".join(satirlar), encoding="utf-8")
print(f"yazildi: {YOL}")
