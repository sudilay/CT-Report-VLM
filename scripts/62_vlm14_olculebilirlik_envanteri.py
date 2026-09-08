"""SUDE-VLM-14 · Adim 3 · Olculebilirlik envanteri (`train`).

Lung-RADS kolonu URETILMIYOR (karar 2026-09-08). Bu adim Astra raporlarinin
klinik kilavuz uygulamaya ne kadar elverdigini OLCER.

Uc olcum:
  (a) Olcu-lezyon bagi — uretim boyutu YALNIZ L1 (`measured_by`, ayni cumle).
      L2/L3/L4 yalniz ortak-bulunma istatistigi olarak raporlanir.
  (b) Kilavuz ekseni envanteri — nodul tipi, buyume, lob, benign kalsifikasyon.
  (c) Negatif beyan analizi — PID duzeyi birincil, hasta-kumeli bootstrap.

⛔ KAPSAM: yalniz `train`. (c) icin etiket okunur - bu AYRI bir analiz
   betigidir, cikarim hatti degildir (docs/39 §6).

Kullanim:
    python scripts/62_vlm14_olculebilirlik_envanteri.py
"""
from __future__ import annotations

import importlib.util
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.extraction import astra as A  # noqa: E402
from radyovlm.extraction import entities as E  # noqa: E402

CUMLELER = KOK / "data/processed/astra_sentences.parquet"
VARLIKLAR = KOK / "data/processed/astra_entities_train.parquet"
KAYNAK = KOK / "astra_radiology_reports_with_labels_all.xlsx"
CIKTI = KOK / "reports/vlm14_olculebilirlik_envanteri.json"

TOHUM = 20260908
BOOTSTRAP = 2000


def _olcu_modulu():
    """scripts/07'nin desenlerini BIREBIR kullan - kopyalayip kaydirmayalim."""
    yol = KOK / "scripts/07_extract_measurements.py"
    spec = importlib.util.spec_from_file_location("_olcu07", yol)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_olcu07"] = mod
    spec.loader.exec_module(mod)
    return mod


# --- (b) Kilavuz eksenleri --------------------------------------------------
EKSENLER = {
    "nodul_ifadesi": r"nodul",
    "tip_solid": r"\bsolid\b",
    "tip_part_solid": r"part.?solid|subsolid|semi.?solid",
    "tip_ground_glass": r"ground.?glass|\bGGN\b",
    "buyume": r"\bgrowth\b|enlarg|increase in size|interval (?:growth|change)",
    "lob": r"(upper|middle|lower)\s+lobe",
    "spikulasyon": r"spicul",
    "benign_kalsifikasyon": r"popcorn|laminated|central calcification|centrally calcified",
    "kalsifikasyon": r"calcif",
}

NEGATIF_NODUL = re.compile(
    r"no (?:pulmonary |lung |significant )?nodul|without nodul"
    r"|nodule[s]? (?:are|is|was|were) not", re.I)


def bootstrap_fark_ci(a: list[str], b: list[str], pid_pozitif: dict[str, int],
                      n: int = BOOTSTRAP) -> tuple[float, float, float]:
    """Iki grup arasindaki FARKIN hasta-kumeli bootstrap guven araligi.

    ⚠ Iki ayri guven araliginin ORTUSMESI istatistiksel esitlik testi DEGILDIR.
    Karsilastirma icin farkin kendi araligi hesaplanir. Gruplar ayriktir:
    negatif beyan tasiyan PID'ler ile tasimayanlar.
    """
    rnd = random.Random(TOHUM)
    farklar = []
    na, nb = len(a), len(b)
    if na == 0 or nb == 0:
        return (float("nan"),) * 3
    for _ in range(n):
        oa = sum(pid_pozitif[a[rnd.randrange(na)]] for _ in range(na)) / na
        ob = sum(pid_pozitif[b[rnd.randrange(nb)]] for _ in range(nb)) / nb
        farklar.append(100 * (oa - ob))
    farklar.sort()
    nokta = 100 * (sum(pid_pozitif[p] for p in a) / na
                   - sum(pid_pozitif[p] for p in b) / nb)
    return (round(nokta, 2), round(farklar[int(0.025 * n)], 2),
            round(farklar[int(0.975 * n)], 2))


def bootstrap_ci(pidler: list[str], pid_pozitif: dict[str, int],
                 n: int = BOOTSTRAP) -> tuple[float, float]:
    """Hasta-kumeli bootstrap: PID'ler yeniden ornekleniyor, seriler degil."""
    rnd = random.Random(TOHUM)
    oranlar = []
    m = len(pidler)
    if m == 0:
        return (float("nan"), float("nan"))
    for _ in range(n):
        ornek = [pidler[rnd.randrange(m)] for _ in range(m)]
        oranlar.append(sum(pid_pozitif[p] for p in ornek) / m)
    oranlar.sort()
    return (round(100 * oranlar[int(0.025 * n)], 2),
            round(100 * oranlar[int(0.975 * n)], 2))


def main() -> None:
    olcu07 = _olcu_modulu()

    d = pd.read_parquet(CUMLELER, filters=[("split", "==", "train")])
    train = d[d["included_in_evaluation"]].copy()
    varlik = pd.read_parquet(VARLIKLAR)

    kavramlar, _ = E.sozlukleri_yukle()
    matcher, indeks = E.matcher_kur(kavramlar)

    anahtar = ["seri_anahtari", "bolum_ham", "cumle_idx"]

    # ---------- (a) Olcu-lezyon bagi ----------------------------------------
    l1_cumle: set[tuple] = set()
    teknik_olcu = 0
    teknik_baglandi = 0
    olculu_cumle: set[tuple] = set()
    nodul_cumle: set[tuple] = set()

    NODUL = {"nodule", "nodular_lesion", "mass", "lesion",
             "space_occupying_lesion"}

    for r in train.itertuples(index=False):
        metin = r.cumle_metni
        ak = (r.seri_anahtari, r.bolum_ham, r.cumle_idx)

        olculer = []
        for m in olcu07.OLCU.finditer(metin):
            teknik = A.olcu_teknik_mi(metin, m.start(), m.end())   # TEK KAYNAK (K5.1)
            if teknik:
                teknik_olcu += 1
                continue                      # teknik olcu ASLA baglanmaz
            olculer.append({"bas": m.start(), "son": m.end(),
                            "metin": m.group(0)})
        if olculer:
            olculu_cumle.add(ak)

        varliklar = E.cumleden_varliklar(metin, matcher, indeks)
        nod = [v for v in varliklar if v["kavram"].ad in NODUL]
        if nod:
            nodul_cumle.add(ak)
        if nod and olculer:
            l1_cumle.add(ak)

    # Negatif kontrol: teknik olcu iceren cumlede nodul VARSA bile
    # o olcu baglanmamis olmali (yukarida `continue` ile garanti).
    for r in train.itertuples(index=False):
        metin = r.cumle_metni
        for m in olcu07.OLCU.finditer(metin):
            if A.olcu_teknik_mi(metin, m.start(), m.end()):        # TEK KAYNAK (K5.1)
                if re.search(r"nodul", metin, re.I):
                    teknik_baglandi += 1      # sadece SAYILIR, baglanmaz

    # Seri duzeyi ortak-bulunma (L2-L4 yerine: bolum ve rapor duzeyi)
    tr_ser = train.set_index(anahtar)
    seri_nodul = {a[0] for a in nodul_cumle}
    seri_olcu = {a[0] for a in olculu_cumle}
    bolum_nodul = {(a[0], a[1]) for a in nodul_cumle}
    bolum_olcu = {(a[0], a[1]) for a in olculu_cumle}

    bag = {
        "L1_ayni_cumle_seri": len({a[0] for a in l1_cumle}),
        "L3_ayni_bolum_seri": len({b[0] for b in (bolum_nodul & bolum_olcu)}),
        "L4_ayni_rapor_seri": len(seri_nodul & seri_olcu),
        "nodul_gecen_seri": len(seri_nodul),
        "olcu_gecen_seri": len(seri_olcu),
        "teknik_olcu_sayisi": teknik_olcu,
        "teknik_olcu_nodullu_cumlede": teknik_baglandi,
        "teknik_olcu_baglandi": 0,       # sozlesme geregi HER ZAMAN 0
    }

    # ---------- (b) Kilavuz ekseni envanteri --------------------------------
    n_seri = train["seri_anahtari"].nunique()
    eksen_kapsam = {}
    for ad, desen in EKSENLER.items():
        p = re.compile(desen, re.I)
        seriler = {r.seri_anahtari for r in train.itertuples(index=False)
                   if p.search(r.cumle_metni)}
        eksen_kapsam[ad] = {"seri": len(seriler),
                            "oran_yuzde": round(100 * len(seriler) / n_seri, 2)}

    # ---------- (c) Negatif beyan analizi (T4) ------------------------------
    # ⚠ Bu blok ETIKET okur. Cikarim hatti degil, ayri analiz.
    et = pd.read_excel(KAYNAK, usecols=["PID", "Seri_Anahtari",
                                        "Kanser_Etiketi_y"])
    et["PID"] = et["PID"].astype(str)
    et["Seri_Anahtari"] = et["Seri_Anahtari"].astype(str)

    neg_seri = {r.seri_anahtari for r in train.itertuples(index=False)
                if NEGATIF_NODUL.search(r.cumle_metni)}
    tr_pidler = train[["seri_anahtari", "pid"]].drop_duplicates()
    e = tr_pidler.merge(et, left_on="seri_anahtari", right_on="Seri_Anahtari",
                        how="left")

    # PID duzeyi: PID pozitif = en az bir serisi pozitif (VLM-12 kurali)
    pid_poz = e.groupby("pid")["Kanser_Etiketi_y"].max().fillna(0).astype(int)
    pid_neg_beyan = (e.assign(neg=e["seri_anahtari"].isin(neg_seri))
                     .groupby("pid")["neg"].max())

    taban_pid = pid_poz.index.tolist()
    beyanli_pid = pid_neg_beyan[pid_neg_beyan].index.tolist()
    pid_poz_d = pid_poz.to_dict()

    taban_oran = round(100 * sum(pid_poz_d.values()) / len(taban_pid), 2)
    beyan_oran = round(100 * sum(pid_poz_d[p] for p in beyanli_pid)
                       / max(len(beyanli_pid), 1), 2)

    beyansiz_pid = [p for p in taban_pid if p not in set(beyanli_pid)]
    fark, fark_alt, fark_ust = bootstrap_fark_ci(beyanli_pid, beyansiz_pid,
                                                 pid_poz_d)
    beyansiz_oran = round(100 * sum(pid_poz_d[p] for p in beyansiz_pid)
                          / max(len(beyansiz_pid), 1), 2)

    negatif = {
        "birincil_estimand": "PID duzeyi",
        "taban_pid": len(taban_pid),
        "taban_pozitif_pid": int(sum(pid_poz_d.values())),
        "taban_oran_yuzde": taban_oran,
        "taban_ci95": bootstrap_ci(taban_pidler := taban_pid, pid_poz_d),
        "negatif_beyanli_pid": len(beyanli_pid),
        "negatif_beyanli_pozitif_pid": int(sum(pid_poz_d[p] for p in beyanli_pid)),
        "negatif_beyanli_oran_yuzde": beyan_oran,
        "negatif_beyanli_ci95": bootstrap_ci(beyanli_pid, pid_poz_d),
        "seri_duzeyi_ikincil": {
            "negatif_beyanli_seri": len(neg_seri),
            "bunlarin_pozitifi": int(e[e["seri_anahtari"].isin(neg_seri)]
                                     ["Kanser_Etiketi_y"].sum()),
        },
        "beyansiz_pid": len(beyansiz_pid),
        "beyansiz_oran_yuzde": beyansiz_oran,
        "FARK_yuzde_puan": fark,
        "FARK_ci95": [fark_alt, fark_ust],
        "fark_yorumu": ("Iki ayri guven araliginin ortusmesi esitlik testi "
                        "DEGILDIR; farkin kendi araligi hesaplandi. Aralik "
                        "sifiri iceriyorsa fark gosterilememis demektir."),
        "yorum": ("NPV degil: dogru ifade 'negatif beyan, kanser riskini taban "
                  "orana gore azaltmiyor'. Guven araliklari hasta-kumeli "
                  "bootstrap ile uretildi (tohum %d, %d yineleme)."
                  % (TOHUM, BOOTSTRAP)),
    }

    sonuc = {
        "gorev": "SUDE-VLM-14 · Adim 3",
        "kapsam": "yalniz train (838 PID / 2.050 seri)",
        "train_seri": int(n_seri),
        "olcu_lezyon_bagi": bag,
        "kilavuz_ekseni_envanteri": eksen_kapsam,
        "negatif_beyan_analizi": negatif,
        "ilan_edilen_sinir": (
            "Uretim boyutu YALNIZ L1'den alinir. L3/L4 ortak-bulunma "
            "istatistigidir, olcu-lezyon bagi DEGILDIR ve boyut_mm'e girmez."),
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1,
                                default=str), encoding="utf-8")

    print(f"train seri: {n_seri:,}")
    print(f"\n(a) olcu-lezyon bagi")
    for k, v in bag.items():
        print(f"    {k:34s} {v:>7,}")
    print(f"\n(b) kilavuz ekseni kapsami")
    for k, v in eksen_kapsam.items():
        print(f"    {k:24s} {v['seri']:>6,}  %{v['oran_yuzde']}")
    print(f"\n(c) negatif beyan (PID duzeyi)")
    print(f"    taban          : %{taban_oran}  CI95 {negatif['taban_ci95']}")
    print(f"    negatif beyanli: %{beyan_oran}  CI95 "
          f"{negatif['negatif_beyanli_ci95']}")
    print(f"\nyazildi: {CIKTI.relative_to(KOK)}")


if __name__ == "__main__":
    main()
