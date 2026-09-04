"""TASK-16 adim 7 - UC YARGININ AYRISMA TABLOSU.

Plan: docs/29 §8.5 adim 7 · Kor paket: outputs/task16/adim7_codex/

Karsilastirilan uc yargi:
  hedef  - adim 4'te KILITLENEN sinif (kurallardan once atandi)
  codex  - bagimsiz kor yargilama
  gemini - bagimsiz kor yargilama (ikinci)
ve referans olarak `motor` (semanin ciktisi).

⚠ NE OLCER: kilitli HEDEFLERIN savunulabilirligini. Adim 6 hedefleri atayan
taraf ile kurallari yazan tarafin AYNI oldugunu gostermisti (D75); iki
bagimsiz yargicin AYNI ANDA hedeften ayrildigi vaka, hedefin supheli
oldugunun en guclu isaretidir.

⚠ NE OLCMEZ: semanin genel dogrulugunu. 30 vaka CELISEN GOSTERGE taramasindan
zenginlestirilerek secildi (adim 1/4), rastgele ornek DEGILDIR. Bu tablodan
korpus geneline dogruluk cikarilamaz.

Kullanim:
    python scripts/51_task16_adim7_ayrisma.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
DIZIN = KOK / "outputs/task16/adim7_codex"
HEDEF = KOK / "data/processed/sema_sinir_vakalari.csv"
SINAV = KOK / "reports/task16_sema_sinavi.json"
CIKTI = KOK / "reports/task16_adim7_ayrisma.json"


def main() -> int:
    h = pd.read_csv(HEDEF, keep_default_na=False)[["vaka_id", "hedef_sinif"]]
    c = pd.read_csv(DIZIN / "CODEX_yargisi.csv", keep_default_na=False)
    g = pd.read_csv(DIZIN / "GEMINI_yargisi.csv", keep_default_na=False)
    k = pd.read_csv(DIZIN / "KOR_sinir_vakalari.csv", keep_default_na=False)
    sinav = json.loads(SINAV.read_text(encoding="utf-8"))["sinir"]["detay"]

    d = (h.merge(c[["vaka_id", "atanan_duzey", "gerekce"]]
                 .rename(columns={"atanan_duzey": "codex", "gerekce": "codex_gerekce"}),
                 on="vaka_id")
         .merge(g[["vaka_id", "atanan_duzey", "gerekce"]]
                .rename(columns={"atanan_duzey": "gemini", "gerekce": "gemini_gerekce"}),
                on="vaka_id")
         .merge(pd.DataFrame([{"vaka_id": x["vaka_id"], "motor": x["motor_ciktisi"]}
                              for x in sinav]), on="vaka_id")
         .merge(k, on="vaka_id"))
    d = d.rename(columns={"hedef_sinif": "hedef"})

    n = len(d)
    ozet = {
        "codex_hedefle_uyum": int((d.codex == d.hedef).sum()),
        "gemini_hedefle_uyum": int((d.gemini == d.hedef).sum()),
        "codex_gemini_uyum": int((d.codex == d.gemini).sum()),
        "ucu_de_ayni": int(((d.codex == d.hedef) & (d.gemini == d.hedef)).sum()),
        "toplam": n,
    }
    print(f"=== UYUM ({n} vaka) ===")
    for k_, v in ozet.items():
        if k_ != "toplam":
            print(f"  {k_:22} {v}/{n}  (%{v/n*100:.1f})")

    # --- Hedefin SUPHELI oldugu vakalar: iki bagimsiz yargi da ayriliyor ---
    supheli = d[(d.codex != d.hedef) & (d.gemini != d.hedef)]
    print(f"\n=== HEDEF SUPHELI ({len(supheli)} vaka) - iki bagimsiz yargi da ayriliyor ===")
    for _, r in supheli.iterrows():
        hemfikir = "IKISI DE AYNI SEYI SOYLUYOR" if r.codex == r.gemini else "birbirleriyle de ayrisiyorlar"
        print(f"\n  {r.vaka_id}")
        print(f"    hedef={r.hedef}  codex={r.codex}  gemini={r.gemini}  motor={r.motor}")
        print(f"    -> {hemfikir}")

    # --- Tek yargicin ayrildigi vakalar (daha zayif sinyal) ---
    tek = d[((d.codex != d.hedef) ^ (d.gemini != d.hedef))]
    print(f"\n=== TEK YARGIC AYRILIYOR ({len(tek)} vaka) - zayif sinyal ===")
    for _, r in tek.iterrows():
        ayrilan = "codex" if r.codex != r.hedef else "gemini"
        print(f"  {r.vaka_id:28} hedef={r.hedef:16} {ayrilan}={getattr(r, ayrilan)}")

    cikti = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ne_olcer": "Kilitli HEDEFLERIN savunulabilirligi (D75'in acigi)",
        "ne_olcmez": "Semanin korpus genelindeki dogrulugu. 30 vaka celisen "
                     "gosterge taramasindan ZENGINLESTIRILEREK secildi, rastgele "
                     "ornek DEGILDIR.",
        "ozet": ozet,
        "hedef_supheli": supheli.drop(columns=["cumle"]).to_dict("records"),
        "tek_yargic_ayriliyor": tek[["vaka_id", "hedef", "codex", "gemini", "motor"]]
            .to_dict("records"),
        "tam_tablo": d.drop(columns=["cumle"]).to_dict("records"),
    }
    CIKTI.write_text(json.dumps(cikti, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
