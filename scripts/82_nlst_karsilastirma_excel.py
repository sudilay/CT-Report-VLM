"""NLST kohortu · yan yana inceleme calisma kitabi.

CT-RATE kitabindan FARKI: NLST'de insan yazimi referans rapor YOKTUR.
Orada karsilastirma "model raporu ile hekim raporu" idi; burada dis gercek
dogrulanmis KANSER TANISIDIR. Uc sistemin raporlari yan yana konur ve her
biri kanser sonucuna karsi isaretlenir.

Sayfalar:
    OKUBENI        sutunlarin anlami ve okuma uyarilari
    Karsilastirma  her satir bir seri: uc sistemin raporu + cikarim etiketleri
    Kanser_hasta   hasta duzeyi TP/FP/FN/TN, malignite paneli
    Etiketler      metinsiz etiket matrisi (pivot icin)
    Ozet           sistem basina bildirim oranlari ve metrikler

Kullanim:
    python scripts/82_nlst_karsilastirma_excel.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
DIZIN = KOK / "outputs/btb3d_nlst"
BULGU = DIZIN / "nlst_uclu_bulgular.parquet"
BTB3D = KOK / "data/raw/btb3d-nlst-2965-reports/generated_reports_nlst_2965.csv"
ASTRA = KOK / "astra_radiology_reports_with_labels_all.xlsx"
MEDMO = KOK / "medmo_radiology_reports_with_labels.xlsx"
CIKTI = DIZIN / "btb3d_nlst_karsilastirma.xlsx"

SISTEMLER = ["BTB3D", "ASTRA", "MEDMO"]
PANEL = ["Malignite", "Nodul", "Supheli morfoloji", "Kitle"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    m = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, m - h), min(1.0, m + h)


def main() -> None:
    d = pd.read_parquet(BULGU)
    on18 = [c.split("::", 1)[1] for c in d.columns
            if c.startswith("BTB3D::")]
    on18 = [s for s in on18 if s not in PANEL]

    b = pd.read_csv(BTB3D).set_index("key")
    a = pd.read_excel(ASTRA, usecols=["Seri_Anahtari", "Radyoloji_Raporu"])
    m = pd.read_excel(MEDMO, usecols=["series_key", "full_report"])
    A = dict(zip(a.Seri_Anahtari.astype(str), a.Radyoloji_Raporu.fillna("")))
    M = dict(zip(m.series_key.astype(str), m.full_report.fillna("")))

    # ---------------------------------------------------- Karsilastirma
    k = pd.DataFrame({
        "seri_anahtari": d.key,
        "hasta": d.pid,
        "KANSER": d.label,
        "tani_yili": d.followup_yil,
        "BTB3D_raporu": [str(b.loc[x, "Generated_Report"]) for x in d.key],
        "ASTRA_raporu": [str(A[x]) for x in d.key],
        "MEDMO_raporu": [str(M[x]) for x in d.key],
    })
    for s in PANEL:
        for x in SISTEMLER:
            k[f"{x} · {s}"] = d[f"{x}::{s}"].values
    # kanser sonucuna karsi isaret (malignite gostergesi uzerinden)
    for x in SISTEMLER:
        k[f"± {x} malignite"] = [
            "TP" if (y and p) else "FN" if (y and not p)
            else "FP" if (not y and p) else "TN"
            for y, p in zip(d.label, d[f"{x}::Malignite"])]
    for x in SISTEMLER:
        k[f"{x} · bulgu sayisi"] = d[[f"{x}::{s}" for s in on18]].sum(axis=1).values
        k[f"{x} · kelime"] = d[f"{x}__kelime"].values

    # ---------------------------------------------------- Kanser_hasta
    pid = d.groupby("pid").agg(
        {**{f"{x}::{s}": "max" for x in SISTEMLER for s in PANEL},
         "label": "max", "followup_yil": "min", "key": "count"})
    pid = pid.rename(columns={"key": "seri_sayisi"}).reset_index()
    for x in SISTEMLER:
        pid[f"± {x} malignite"] = [
            "TP" if (y and p) else "FN" if (y and not p)
            else "FP" if (not y and p) else "TN"
            for y, p in zip(pid.label, pid[f"{x}::Malignite"])]

    # ---------------------------------------------------- Ozet
    y_tum = pid.label.values
    erken = ((pid.label == 0) | (pid.followup_yil <= 1)).values
    ozet = []
    for kad, mask in [("tanisi <= 1 yil", erken),
                      ("tum hastalar", np.ones(len(pid), dtype=bool))]:
        y = y_tum[mask]
        for s in ["Malignite", "Nodul", "Supheli morfoloji"]:
            for x in SISTEMLER:
                p = pid[f"{x}::{s}"].values[mask]
                tp = int(((y == 1) & (p == 1)).sum())
                fp = int(((y == 0) & (p == 1)).sum())
                fn = int(((y == 1) & (p == 0)).sum())
                tn = int(((y == 0) & (p == 0)).sum())
                duy = tp / (tp + fn) if tp + fn else 0.0
                ozg = tn / (tn + fp) if tn + fp else 0.0
                lo, hi = wilson(tp, tp + fn)
                ozet.append({
                    "Katman": kad, "Sistem": x, "Gosterge": s,
                    "TP": tp, "FP": fp, "FN": fn, "TN": tn,
                    "Duyarlilik": duy, "GA alt": lo, "GA ust": hi,
                    "Ozgulluk": ozg, "Youden J": duy + ozg - 1})
    ozet = pd.DataFrame(ozet)

    okubeni = pd.DataFrame({"Alan": [
        "Kapsam", "Dis gercek", "!!! ONEMLI",
        "KANSER sutunu", "tani_yili sutunu",
        "'Sistem · Bulgu' sutunlari", "'± Sistem malignite' sutunu",
        "TP", "FP", "FN", "TN",
        "Pozitif kurali", "Hasta duzeyi kurali", "Tarama uyarisi"],
        "Aciklama": [
        "2.500 seri · 1.018 hasta · dondurulmus bolunmenin train+dev kismi",
        "Dogrulanmis akciger kanseri tanisi (takip verisinden)",
        "NLST'de INSAN YAZIMI REFERANS RAPOR YOKTUR. Uc sutundaki raporlarin "
        "UCU DE yapay zeka ciktisidir. Aralarindaki uyum 'dogruluk' degil "
        "'tutarlilik' olarak okunmalidir.",
        "1 = hasta takip suresinde akciger kanseri tanisi almis",
        "Tani konan yil (pozitiflerde); 1 = ilk yil icinde",
        "O sistemin raporundan cikarilan bulgu (1 = bildirilmis)",
        "O sistemin MALIGNITE bildirimi ile gercek kanser durumunun kesisimi",
        "Kanserli hastada malignite bildirilmis (dogru yakalama)",
        "Kanser olmayan hastada malignite bildirilmis (yanlis alarm)",
        "Kanserli hastada malignite BILDIRILMEMIS (kacirma - en tehlikeli)",
        "Kanser olmayan hastada bildirilmemis (dogru sessizlik)",
        "Olumsuzlanmis ifade pozitif SAYILMAZ; toraks disi anatomi elenir",
        "Hastanin herhangi bir serisinde bildirilmisse hasta pozitif sayilir",
        "NLST bir TARAMA kohortudur. Kanser etiketi GELECEKTEKI bir sonuctur; "
        "tarama aninda gorunur lezyon olmayabilir. Bu yuzden dusuk duyarlilik "
        "kusursuz bir okuyucu icin bile beklenir. Asil olcum 'tanisi <= 1 yil' "
        "katmanindadir."]})

    DIZIN.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(CIKTI, engine="openpyxl") as w:
        okubeni.to_excel(w, sheet_name="OKUBENI", index=False)
        ozet.to_excel(w, sheet_name="Ozet", index=False)
        pid.to_excel(w, sheet_name="Kanser_hasta", index=False)
        k.to_excel(w, sheet_name="Karsilastirma", index=False)
        d.drop(columns=[c for c in d.columns if c.endswith("__kelime")]
               ).to_excel(w, sheet_name="Etiketler", index=False)

        ws = w.sheets["Karsilastirma"]
        ws.freeze_panes = "E2"
        for kol, en in (("A", 30), ("B", 10), ("C", 8), ("D", 9),
                        ("E", 70), ("F", 70), ("G", 60)):
            ws.column_dimensions[kol].width = en
        w.sheets["OKUBENI"].column_dimensions["A"].width = 28
        w.sheets["OKUBENI"].column_dimensions["B"].width = 95

    mb = CIKTI.stat().st_size / 1e6
    print(f"yazildi: {CIKTI}  ({mb:.1f} MB)")
    print(f"  Karsilastirma : {len(k)} seri")
    print(f"  Kanser_hasta  : {len(pid)} hasta, {int(pid.label.sum())} kanser")
    print(f"  Ozet          : {len(ozet)} satir")
    print("\nMalignite gostergesi, tanisi <= 1 yil katmani:")
    alt = ozet[(ozet.Katman == "tanisi <= 1 yil") & (ozet.Gosterge == "Malignite")]
    print(alt[["Sistem", "TP", "FP", "FN", "TN", "Duyarlilik", "Ozgulluk",
               "Youden J"]].to_string(index=False))


if __name__ == "__main__":
    main()
