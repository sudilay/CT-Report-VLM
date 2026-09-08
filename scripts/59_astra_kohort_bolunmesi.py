"""SUDE-VLM-12 - ASTRA/NLST KOHORTUNUN PID BAZINDA BOLUNME KILIDI.

Devir notu: outputs/vlm12/DEVIR_PROMPT.md · Gerekce: docs/kararlar.md D70

Neden simdi: SUDE-VLM-14 `sema-0.9` motorunu 2.965 raporun TAMAMINA uygulamak
istiyor. Bolunme once dondurulmazsa held-out test kumesi motor yazilirken
gorulmus olur ve olculen dogruluk sisik cikar. D70'in kurali aynen gecerli:
"bolunme sozluk kurulmadan ONCE yapilmali; sonra yapmak ise yaramaz."

Ayirma PID (hasta) duzeyindedir: bir hastanin 3 serisi var, ikisi iki tarafa
dusersse sinav sizar.

BU BETIK GERI DONUSSUZDUR: mevcut kilit dosyasinin uzerine YAZMAZ.

Kullanim:
    python scripts/59_astra_kohort_bolunmesi.py
    python scripts/59_astra_kohort_bolunmesi.py --dogrula   # yeniden uret ve karsilastir
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
KAYNAK = KOK / "astra_radiology_reports_with_labels_all.xlsx"
KILIT = KOK / "configs/splits_astra.json"

TOHUM = 20260907        # gorevin baslangic tarihi; scripts/40'in 20260903 oruntusu
DEV_ORANI = 0.15
TEST_ORANI = 0.15
SURUM = "astra-split-1.0"


def sha(kimlikler) -> str:
    """Sirali kimlik listesinin kararli saglama toplami (scripts/40 ile ayni)."""
    h = hashlib.sha256()
    for m in sorted(kimlikler):
        h.update(str(m).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def filtrele(ham: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Gorev filtresi: `Censor_Time < 1` olan KANSER-DISI satirlar cikarilir.

    Kanserli satirlar Censor_Time'dan bagimsiz olarak KALIR - bir vakanin
    kanser oldugu biliniyorsa kisa takip suresi onu gecersiz kilmaz.
    """
    dis = (ham["Censor_Time"] < 1) & (ham["Kanser_Etiketi_y"] == 0)
    dislanan = sorted(str(s) for s in ham.loc[dis, "Seri_Anahtari"])
    return ham.loc[~dis].copy(), dislanan


def pid_etiketleri(d: pd.DataFrame) -> pd.Series:
    """PID duzeyi etiket = seri etiketlerinin MAKSIMUMU (D98).

    3 karma PID var (bir hastada hem kanserli hem kansersiz seri). `max`
    kurali: PID'de tek kanserli seri varsa PID kanserlidir.
    """
    return d.groupby("PID")["Kanser_Etiketi_y"].max()


def bolunmeyi_uret(d: pd.DataFrame, dislanan: list[str]) -> dict:
    """Deterministik: ayni kaynak + ayni tohum -> ayni bolunme.

    Katmanlama: her etiket katmani (pozitif / negatif) KENDI ICINDE
    %70/%15/%15'e bolunur, sonra birlestirilir. Boylece held-out'a dusen
    pozitif PID sayisi tesadufe birakilmaz.
    """
    etiket = pid_etiketleri(d)
    rng = random.Random(TOHUM)
    kumeler: dict[str, list[str]] = {"train": [], "dev": [], "held_out": []}

    for deger in (0, 1):  # sabit sira - determinizm icin sart
        havuz = sorted(str(p) for p in etiket[etiket == deger].index)
        karisik = rng.sample(havuz, len(havuz))  # tam permutasyon
        n_test = round(len(havuz) * TEST_ORANI)
        n_dev = round(len(havuz) * DEV_ORANI)
        kumeler["held_out"] += karisik[:n_test]
        kumeler["dev"] += karisik[n_test:n_test + n_dev]
        kumeler["train"] += karisik[n_test + n_dev:]

    pid_str = d["PID"].astype(str)

    def ozet(pidler: list[str]) -> dict:
        pidler = sorted(pidler)
        kume = set(pidler)
        satirlar = d[pid_str.isin(kume)]
        return {
            "pid": len(pidler),
            "seri": int(len(satirlar)),
            "pozitif_pid": int(etiket[etiket.index.astype(str).isin(kume)].sum()),
            "pozitif_seri": int(satirlar["Kanser_Etiketi_y"].sum()),
            "sha256": sha(pidler),
            "pid_listesi": pidler,
        }

    return {
        "surum": SURUM,
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "tohum": TOHUM,
        "oranlar": {"train": 0.70, "dev": DEV_ORANI, "held_out": TEST_ORANI},
        "kaynak": {
            "dosya": KAYNAK.name,
            "ham_seri": 2965,
            "ham_pid": 1201,
            "filtre_sonrasi_seri": int(len(d)),
            "filtre_sonrasi_pid": int(d["PID"].nunique()),
        },
        "filtre": {
            "kural": "Censor_Time < 1 VE Kanser_Etiketi_y == 0 olan seriler cikarilir",
            "aciklama": "Kanserli seriler Censor_Time'dan bagimsiz olarak KALIR.",
            "dislanan_seri": len(dislanan),
            "dislanan_seri_anahtarlari": dislanan,
        },
        "karma_pid_kurali": {
            "kural": "max - PID'de tek kanserli seri varsa PID kanserlidir",
            "etkilenen_pid": ["101907", "134575", "205393"],
            "karar": "D98",
        },
        "katmanlama": {
            "degisken": "PID duzeyi Kanser_Etiketi_y (max kuraliyla)",
            "yontem": "her katman KENDI ICINDE %70/%15/%15; round() ile yuvarlanir",
            "karar": "D99",
        },
        "onceden_ilan": {
            "aciklama": "Bolunme KOSULMADAN once yazildi; sonuca bakilarak degistirilmedi.",
            "birincil_estimand": "PID duzeyi duyarlilik",
            "beklenen_held_out_pozitif_pid": 11,
            "esik_sinanabilir_mi": False,
            "gerekce": "11 pozitif PID ile kusursuz sonucta bile (11/11) Wilson %95 "
                       "guven araliginin alt siniri %74,1'dir; %80'lik bir duyarlilik "
                       "esigi HICBIR sonucta gecilemez. Held-out yalniz nokta tahmin "
                       "ve guven araligi raporlar, esik SINAMAZ.",
            "ulasilabilir_kesinlik_wilson95": {
                "11/11": "[%74,1 - %100,0]",
                "10/11": "[%62,3 - %98,4]",
                "9/11": "[%52,3 - %94,9]",
            },
            "seri_duzeyi_not": "Seri duzeyi (n~21) ikincil ve TANIMLAYICIDIR; ayni "
                               "hastanin 3 serisi bagimsiz gozlem degildir, seri "
                               "duzeyi guven araligi iyimserdir.",
            "karar": "D100",
        },
        "bolunme": {
            "aciklama": "held_out SUDE-VLM-12'den sonra DOKUNULMAZ (D70). Sema, "
                        "sozluk ve esik gelistirmesi YALNIZ train + dev uzerinde yapilir.",
            "train": ozet(kumeler["train"]),
            "dev": ozet(kumeler["dev"]),
            "held_out": ozet(kumeler["held_out"]),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dogrula", action="store_true",
                    help="Kilidi yeniden uretip mevcut dosyayla karsilastirir, yazmaz.")
    a = ap.parse_args()

    if not KAYNAK.exists():
        print(f"HATA: kaynak yok: {KAYNAK}")
        return 1

    ham = pd.read_excel(KAYNAK)
    d, dislanan = filtrele(ham)
    yeni = bolunmeyi_uret(d, dislanan)

    if a.dogrula:
        if not KILIT.exists():
            print(f"HATA: dogrulanacak kilit yok: {KILIT}")
            return 1
        eski = json.loads(KILIT.read_text(encoding="utf-8"))
        tamam = True
        for ad in ("train", "dev", "held_out"):
            e = eski["bolunme"][ad]["sha256"]
            y = yeni["bolunme"][ad]["sha256"]
            if e != y:
                tamam = False
            print(f"  [{'OK ' if e == y else 'FARK'}] {ad}: {e[:16]}")
        print("\nKILIT YENIDEN URETILEBILIR" if tamam else "\n!!! KILIT YENIDEN URETILEMIYOR !!!")
        return 0 if tamam else 1

    if KILIT.exists():
        print(f"HATA: kilit ZATEN VAR ve uzerine yazilmaz: {KILIT}")
        print("      Bu bilincli bir tasarimdir (D70 - geri donussuz).")
        print("      Yeniden uretmek icin dosyayi ELLE silin ve kararinizi kaydedin.")
        print("      Dogrulama icin: --dogrula")
        return 1

    KILIT.parent.mkdir(parents=True, exist_ok=True)
    KILIT.write_text(json.dumps(yeni, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"YAZILDI: {KILIT.relative_to(KOK)}  (surum {SURUM}, tohum {TOHUM})\n")
    print(f"  filtre: {yeni['filtre']['dislanan_seri']} seri dislandi -> "
          f"{yeni['kaynak']['filtre_sonrasi_seri']} seri / {yeni['kaynak']['filtre_sonrasi_pid']} PID\n")
    for ad in ("train", "dev", "held_out"):
        b = yeni["bolunme"][ad]
        print(f"  {ad:<9}: {b['pid']:>5} PID / {b['seri']:>5} seri  "
              f"poz {b['pozitif_pid']:>3} PID / {b['pozitif_seri']:>3} seri  {b['sha256'][:16]}")
    print(f"\n  dosya sha256: {hashlib.sha256(KILIT.read_bytes()).hexdigest()[:32]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
