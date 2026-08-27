# -*- coding: utf-8 -*-
"""TASK-11 adim 1: aday terim madeni.

Sozluk ders kitabindan degil KORPUSTAN cikarilir (D16'nin mantigi).
Sayim YALNIZCA train'de yapilir (D11) - valid'den on islemeye sizinti olmasin.
"""
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(".")
sent = pd.read_parquet(ROOT / "data/processed/sentences.parquet")
reps = pd.read_parquet(ROOT / "data/processed/reports_study_level.parquet",
                       columns=["study_id", "patient_id", "split"])
sent = sent.merge(reps, on="study_id", how="left")
train = sent[sent.split == "train"]
print(f"train cumle: {len(train):,}  hasta: {train.patient_id.nunique():,}")

DURAK = set("""a an the of in on at to and or is are was were be been being with without
for from by as that this these those it its there here which who whom whose what when
where how not no nor but if then than so such both each any all some more most other
another same very can could may might will would shall should must have has had do does
did done being were been at into onto upon within between among during about above below
under over after before again further once only own too s t just now also seen observed
detected noted evaluated identified distinguished appearance appearances area areas
level levels part parts side sides right left bilateral anterior posterior superior
inferior lateral medial cm mm findings finding impression examination examinations
study studies patient present significant compatible consistent normal""".split())

KELIME = re.compile(r"[a-z][a-z\-]{2,}")


def kelimeler(t: str):
    return [w for w in KELIME.findall(t.lower()) if w not in DURAK]


tek = Counter()
ikili = Counter()
for t in train.text:
    ws = kelimeler(t)
    tek.update(ws)
    ikili.update(f"{a} {b}" for a, b in zip(ws, ws[1:]))

print(f"\nbenzersiz tek kelime : {len(tek):,}")
print(f"benzersiz ikili      : {len(ikili):,}")

# Kapsama: ilk N terim train cumlelerinin yuzde kacina dokunuyor?
print("\n--- TEK KELIME KAPSAMASI ---")
for N in (100, 200, 300, 500, 1000):
    ust = {w for w, _ in tek.most_common(N)}
    kaps = train.text.map(lambda t: bool(ust & set(kelimeler(t)))).mean()
    print(f"  ilk {N:>4} terim -> train cumlelerinin %{100*kaps:.1f}'ine dokunuyor")

out = Path("_terimler.txt")
with out.open("w", encoding="utf-8") as f:
    f.write("===== EN SIK 400 TEK KELIME =====\n")
    for w, n in tek.most_common(400):
        f.write(f"{n:>7}  {w}\n")
    f.write("\n\n===== EN SIK 250 IKILI =====\n")
    for w, n in ikili.most_common(250):
        f.write(f"{n:>7}  {w}\n")
print(f"\nyazildi: {out}")
