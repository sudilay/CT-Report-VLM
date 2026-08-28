# -*- coding: utf-8 -*-
"""TASK-13: Ayar kumesi puanlamasi - iki isaretleyici, duzeltmeli/duzeltmesiz.

KONUMSAL KIMLIK (2026-08-28 duzeltmesi):
  Ilk surum satirlari (study_id, section, sent_idx, aday_metin, aday_kavram)
  uzerinden birlestiriyordu. Bu anahtar YETERSIZ: ayni cumlede ayni kavram iki
  kez gecebiliyor ("lung parenchyma ... lung parenchyma") ve anahtarda karakter
  ofseti yok. 513 satirin tekil anahtari 493; birlestirme satirlari 527'ye
  sisiriyor ve skorlari bozuyordu.

  Cozum: SATIR SIRASI kimliktir.
    - Iki isaretleyici AYNI uretilmis dosyayi doldurdu -> satir i = satir i.
    - Sisteme eslerken ayni anahtarin n'inci anmasi, entities'te char_start'a
      gore siralanmis n'inci anmaya baglanir.

OLCUTLER (docs/10, sonuc gorulmeden sabitlendi)
  K4 varlik kesinligi   esik %90
  K6 kesinlik atamasi   esik %85 (makro-F1)

Kullanim: .venv/Scripts/python.exe scripts/18_score_ayar.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from radyovlm.evaluation import score as S   # noqa: E402

P = ROOT / "data" / "processed"
K = ["study_id", "section", "sent_idx", "aday_metin", "aday_kavram"]
KESINLIK = {"mevcut": "present", "yok": "absent", "belirsiz": "uncertain"}
ISARETLEYICI = ("codex", "gemini")


def anma_sirasi(d: pd.DataFrame) -> pd.Series:
    """Ayni anahtarin kacinci anmasi oldugu (0,1,2...)."""
    return d.groupby(K).cumcount()


def sistem_esle(b: pd.DataFrame) -> pd.DataFrame:
    """Her aday satirini sistemin AYNI SIRADAKI anmasina baglar."""
    e = pd.read_parquet(P / "entities.parquet")
    e = e.sort_values(["study_id", "section", "sent_idx", "char_start"])
    e = e.rename(columns={"raw_text": "aday_metin",
                          "normalized_concept": "aday_kavram"})
    e["_n"] = anma_sirasi(e)
    b = b.copy()
    b["_n"] = anma_sirasi(b)
    return b.merge(e[K + ["_n", "assertion"]], on=K + ["_n"], how="left")


def yukle(m: str, duzelt: bool) -> pd.DataFrame:
    d = pd.read_csv(P / f"KALAN_B_{m}.csv", encoding="utf-8-sig")
    d["_satir"] = range(len(d))
    if duzelt:
        y = pd.read_csv(P / f"YENIDEN_{m}.csv", encoding="utf-8-sig")
        # YENIDEN, B'den ayni sirayla suzuldu -> konumsal hizalama gecerli.
        secili = d[d._satir.isin(_etkilenen_satirlar(d))]
        if len(secili) != len(y):
            sys.exit(f"hizalama bozuk: {len(secili)} != {len(y)}")
        d.loc[secili._satir.values, "kesinlik_ne_olmali"] = \
            y.kesinlik_ne_olmali.values
    anahtar = pd.read_csv(P / "task13_B_anahtar_ayar.csv", encoding="utf-8-sig")
    anahtar["_n"] = anma_sirasi(anahtar)
    d["_n"] = anma_sirasi(d)
    d = d.merge(anahtar[K + ["_n", "_gizli_sahte"]], on=K + ["_n"], how="left")
    d["sahte"] = d._gizli_sahte.fillna(0).astype(int)
    return d


def _etkilenen_satirlar(d: pd.DataFrame):
    """17_build_rejudge.py ile AYNI olcut - kopyasi degil, ithali."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib
    mod = importlib.import_module("17_build_rejudge".replace("17_", "_17_")
                                  if False else "17_build_rejudge")
    m = mod.KAPSAM
    return d[(d.sahte == 0) if "sahte" in d else (d.aday_tip == d.aday_tip)][
        (d.aday_tip == "anatomy") & d.cumle.astype(str).str.contains(m)]._satir


def kappa(a, b):
    a, b = list(a), list(b)
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(x) / n) * (b.count(x) / n) for x in set(a) | set(b))
    return ((po - pe) / (1 - pe) if pe < 1 else float("nan")), po


def main() -> None:
    for duzelt, ad in [(False, "A · DUZELTMESIZ"),
                       (True, "B · DUZELTMELI (anatomi kurali yazildiktan sonra)")]:
        print(f"\n{'='*64}\n{ad}\n{'='*64}")
        t = {m: yukle(m, duzelt) for m in ISARETLEYICI}
        for m in ISARETLEYICI:
            assert len(t[m]) == 513, f"{m} satir sayisi bozuldu: {len(t[m])}"

        c, g = t["codex"], t["gemini"]
        print("\nISARETLEYICILER ARASI UYUM  (konumsal - satir i = satir i)")
        for etiket, kol, yalniz_gercek in [
                ("varlik (E/H)", "dogru_varlik_mi", False),
                ("kavram (E/H)", "dogru_kavram_mi", False),
                ("KESINLIK", "kesinlik_ne_olmali", True)]:
            gecerli = (c.sahte == 0) if yalniz_gercek else pd.Series(True, index=c.index)
            gecerli &= c[kol].notna() & g[kol].notna()
            A = c.loc[gecerli, kol].astype(str).str.strip().str.lower()
            B = g.loc[gecerli, kol].astype(str).str.strip().str.lower()
            k, po = kappa(A, B)
            yorum = ("neredeyse tam" if k >= .8 else "guclu" if k >= .6
                     else "orta" if k >= .4 else "zayif")
            print(f"  {etiket:<16}n={len(A):>4}  uyum %{100*po:>5.1f}  "
                  f"kappa {k:.3f}  ({yorum})")

        print("\nSISTEM SKORU")
        for m in ISARETLEYICI:
            d = sistem_esle(t[m][t[m].sahte == 0])
            for kol in ("dogru_varlik_mi", "dogru_kavram_mi"):
                d[kol] = d[kol].astype(str).str.strip().str.upper()
            n = len(d)
            ok = int(((d.dogru_varlik_mi == "E") & (d.dogru_kavram_mi == "E")).sum())
            x = d[(d.dogru_varlik_mi == "E") & (d.dogru_kavram_mi == "E")].copy()
            x["altin"] = (x.kesinlik_ne_olmali.astype(str).str.strip()
                          .str.lower().map(KESINLIK))
            x = x[x.altin.notna() & x.assertion.notna()]
            r = S.makro_f1([(S.Span(0, 1, "x", {"a": a}), S.Span(0, 1, "x", {"a": y}))
                            for a, y in zip(x.altin, x.assertion)],
                           "a", ["present", "absent", "uncertain"])
            print(f"  --- {m} ---  n={n}")
            print(f"    K4 varlik kesinligi %{100*ok/n:>5.1f}  esik %90 -> "
                  f"{S.olcut_durumu(ok/n, .90)}")
            print(f"    K6 kesinlik atamasi %{100*r['makro_f1']:>5.1f}  esik %85 -> "
                  f"{S.olcut_durumu(r['makro_f1'], .85)}"
                  f"   (dogruluk %{100*r['dogruluk']:.1f}, n={r['n']})")
            for cl, v in r["sinif"].items():
                f = lambda z: f"{100*z:.0f}%" if z == z else "-"      # noqa: E731
                uyari = "  <- DESTEK YETERSIZ" if v["destek"] < 20 else ""
                print(f"       {cl:<10}destek{v['destek']:>4}  P{f(v['p']):>6} "
                      f"R{f(v['r']):>6} F1{f(v['f1']):>6}{uyari}")


if __name__ == "__main__":
    main()
