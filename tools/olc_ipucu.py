# -*- coding: utf-8 -*-
"""Ipucu sozlugundeki her girdinin korpus destegini OLCER ve YAML'a geri yazar."""
import re
import pandas as pd, yaml
from pathlib import Path

YOL = Path("configs/ipucu_sozlugu.yaml")
s = pd.read_parquet("data/processed/sentences.parquet")
r = pd.read_parquet("data/processed/reports_study_level.parquet",
                    columns=["study_id", "split"])
T = s.merge(r, on="study_id").query("split=='train'").text
print(f"train cumle: {len(T):,}\n")

ham = YOL.read_text(encoding="utf-8")
veri = yaml.safe_load(ham)
sonuc, sifir = {}, []
for bolum, girdiler in veri.items():
    if not isinstance(girdiler, dict):
        continue
    print(f"--- {bolum} ---")
    for ad, t in girdiler.items():
        if not isinstance(t, dict) or "desenler" not in t:
            continue
        pat = "|".join(f"(?:{p})" for p in t["desenler"])
        try:
            n = int(T.str.contains(pat, case=False, regex=True).sum())
        except re.error as e:
            print(f"    !! {ad}: REGEX HATASI {e}"); continue
        sonuc[ad] = n
        isaret = "  <-- SIFIR" if n == 0 else ("  <-- zayif" if n < 100 else "")
        print(f"    {ad:<26} {n:>8,}{isaret}")
        if n == 0:
            sifir.append(f"{bolum}.{ad}")

print(f"\ntoplam girdi: {len(sonuc)} · sifir destekli: {len(sifir)}")
if sifir:
    print("SIFIR DESTEKLILER:", sifir)

sat = ham.split("\n"); aktif = None
for i, x in enumerate(sat):
    m = re.match(r"^  ([a-z_0-9]+):\s*$", x)
    if m and m.group(1) in sonuc:
        aktif = m.group(1); continue
    if aktif and re.match(r"^    korpus:", x):
        sat[i] = re.sub(r"(korpus:\s*)\d+", rf"\g<1>{sonuc[aktif]}", x); aktif = None
    elif aktif and re.match(r"^  \S", x):
        aktif = None
YOL.write_text("\n".join(sat), encoding="utf-8")
print(f"yazildi: {YOL}")
