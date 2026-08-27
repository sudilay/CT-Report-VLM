# -*- coding: utf-8 -*-
"""Ithal NegEx listesinin bu korpusta ne kadar karsiligi var - OLCULUR."""
import re
from pathlib import Path
import pandas as pd

s = pd.read_parquet("data/processed/sentences.parquet")
r = pd.read_parquet("data/processed/reports_study_level.parquet",
                    columns=["study_id", "split"])
T = s.merge(r, on="study_id").query("split=='train'").text
print(f"train cumle: {len(T):,}\n")

kayit = []
for satir in Path("data/external/negex/negex_triggers.txt").read_text(
        encoding="utf-8", errors="ignore").splitlines():
    if not satir.strip():
        continue
    p = [x for x in satir.split("\t") if x.strip()]
    if len(p) < 2:
        continue
    tetik, kat = p[0].strip().lower(), p[-1].strip()
    n = int(T.str.contains(rf"\b{re.escape(tetik)}\b", case=False, regex=True).sum())
    kayit.append({"tetikleyici": tetik, "kategori": kat, "korpus": n})

d = pd.DataFrame(kayit)
print("KATEGORI BAZINDA ITHAL LISTENIN KARSILIGI")
print(f"{'kategori':<10} {'tetik':>6} {'sifir':>6} {'>=100':>6} {'toplam eslesme':>16}")
for k, g in d.groupby("kategori"):
    print(f"{k:<10} {len(g):>6} {int((g.korpus==0).sum()):>6} "
          f"{int((g.korpus>=100).sum()):>6} {g.korpus.sum():>16,}")
print(f"\nTOPLAM {len(d)} tetikleyicinin {int((d.korpus==0).sum())}'i korpusta HIC gecmiyor "
      f"(%{100*(d.korpus==0).mean():.0f})")
print(f"{int((d.korpus>=100).sum())}'i 100+ cumlede geciyor (%{100*(d.korpus>=100).mean():.0f})")

for k in ("PREN", "POSP", "PSEU", "CONJ"):
    g = d[d.kategori == f"[{k}]"].sort_values("korpus", ascending=False)
    print(f"\n--- {k}: en sik 12 ---")
    for x in g.head(12).itertuples():
        print(f"    {x.korpus:>7,}  {x.tetikleyici}")
    print(f"    ... {int((g.korpus==0).sum())} tanesi SIFIR")
d.to_csv("_negex_tarama.csv", index=False, encoding="utf-8-sig")
