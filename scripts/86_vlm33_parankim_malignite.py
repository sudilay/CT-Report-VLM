# -*- coding: utf-8 -*-
"""SUDE-VLM-33: BIMCV-R'de akciger parankiminde malignite bulgusu olan vakalarda Sybil ve
3B BT modellerinin karsilastirilmasi (rapor bolum 6.3).

Hedef: raporda guncel primer akciger tumoru, supheli primer pulmoner lezyon ya da pulmoner
metastaz tanimlanan seriler (13/317). Etiket raporlardan kural tabanli turetildi, ikinci
degerlendiriciyle dogrulanmadi.
Model skoru: 5 tohum ortalamasi OOF olasiliklarinda max(nodule, pulmonary mass); yeni
siniflandirici egitilmez.

Girdi:  scripts/84_vlm33_benchmark_degerlendirme.py (OOF uretimi), reports/bimcv_317_siniflama.json
Cikti:  outputs/vlm33/parankim_malignite.json, outputs/vlm33/bimcv317_parankim_malignite_etiket.csv
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom

KOK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("b84", KOK / "scripts" / "84_vlm33_benchmark_degerlendirme.py")
b84 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b84)

HEDEF_BAGLAM = ["guncel_primer_akciger", "supheli_primer_pulmoner", "pulmoner_metastaz"]
ETIKET_CSV = KOK / "outputs" / "vlm33" / "bimcv317_parankim_malignite_etiket.csv"
SINIFLAMA = KOK / "reports" / "bimcv_317_siniflama.json"


def etiketler():
    if SINIFLAMA.exists():
        d = pd.DataFrame(json.load(open(SINIFLAMA, encoding="utf-8")))
        df = pd.DataFrame({"seri": d.seri, "sybil1": d.sybil1})
        for b in HEDEF_BAGLAM:
            df[b] = d.baglam.apply(lambda x, b=b: b in x)
        df["parankim_malignite"] = df[HEDEF_BAGLAM].any(axis=1)
        df.to_csv(ETIKET_CSV, index=False)
    return pd.read_csv(ETIKET_CSV).set_index("seri")


def main():
    e = etiketler()
    rng = np.random.default_rng(b84.RNG_SEED)
    skor = {}
    for m in ["spectre", "m3d", "mg3d"]:
        O, vols, pids = b84.oof_hesapla(m, "bimcv")
        skor[m] = np.max([np.mean(O["nodule"][1], axis=0), np.mean(O["pulmonary mass"][1], axis=0)], axis=0)
    vols, pids = np.array(vols), np.array(pids)
    y = e.loc[vols, "parankim_malignite"].values.astype(int)
    sy = e.loc[vols, "sybil1"].values
    alarm = sy >= 0.20
    boots = b84.bootstrap_indeksleri(pids, rng)
    neg = np.where(~alarm)[0]
    N, K, ka = len(neg), int(y[neg].sum()), int(alarm.sum())
    sonuc = {"pozitif": int(y.sum()), "sybil_yakalanan": int((alarm & (y == 1)).sum()),
             "sybil_kacirilan": int((~alarm & (y == 1)).sum()), "sybil_alarm": ka,
             "sybil_auc": round(float(b84.auc(y, sy)), 4),
             "sybil_auc_ga": b84.ga([b84.auc(y[i], sy[i]) for i in boots]),
             "rastgele_beklenen": round(ka * K / N, 2), "modeller": {}}
    ust20 = int(round(0.20 * N))
    for m, s in skor.items():
        sira = np.argsort(-s[neg], kind="stable")
        kurt = int(y[neg][sira[:ka]].sum())
        sonuc["modeller"][m] = {
            "auc": round(float(b84.auc(y, s)), 4), "auc_ga": b84.ga([b84.auc(y[i], s[i]) for i in boots]),
            "sybil_negatif_auc": round(float(b84.auc(y[neg], s[neg])), 4),
            "ek_alarmda_yakalanan": kurt, "p_rastgele": round(float(hypergeom.sf(kurt - 1, N, K, ka)), 3),
            "ust_yuzde20_seri": ust20, "ust_yuzde20_yakalanan": int(y[neg][sira[:ust20]].sum()),
        }
    (KOK / "outputs" / "vlm33" / "parankim_malignite.json").write_text(
        json.dumps(sonuc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(sonuc, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
