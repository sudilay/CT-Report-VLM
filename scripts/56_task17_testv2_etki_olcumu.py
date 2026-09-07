"""TASK-17 madde 9 - `test-v2` ETKI OLCUMU. ⛔ TEK ATIS.

Protokol: docs/36_task17_testv2_olcum_protokolu.md (SONUC GORULMEDEN yazildi)
Karar kaydi: D90

NE OLCER: K5 duyarlilik - kor listelemede isaretleyicinin YAZDIGI ogelerin
kaci sistem ciktisinda bulunuyor. A dosyasi SERBEST METINDIR ve sozlukten
BAGIMSIZDIR; bu yuzden herhangi bir sistem ciktisina karsi yeniden olculebilir.

⚠ NE OLCMEZ: kesinlik (K4/K6). B dosyasi paket uretilirken gosterilen ADAY
LISTESINE baglidir; yeni kavramlari kimse yargilamamistir. Bu sinir protokolde
ILAN EDILMISTIR ve burada da yazilidir.

⚠ NEDEN `scripts/21` KULLANILMIYOR: o betik sistem ciktisini paket
uretilirken DONDURULMUS kolonlardan okur (`_gizli_*`), yani `ent-1.0`
donemindeki ciktiyi puanlar. Kosulsaydi eski sayiyi aynen uretir, sozluk
degisikliginin etkisini OLCMEZDI.

UC YONLU (D88 yuzunden zorunlu):
  ent-1.0  (bayat)          - TASK-13'un raporladigi sayinin uredigi tablo
  ent-1.0r (temiz referans) - bulgu-1.1'in DOGRU hali
  ent-1.1  (bizim)          - TASK-17 sozluk genisletmesi
Iki fark AYRI raporlanir; karistirilirsa baskasinin onarimi TASK-17'ye yazilir.

Kullanim:
    .venv/Scripts/python.exe scripts/56_task17_testv2_etki_olcumu.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

P = KOK / "data/processed"
A_DOSYA = P / "task13_A_kor_listeleme_test-v2.csv"
ISARETCILER = {"codex": P / "TESTV2_A_codex.csv", "gemini": P / "TESTV2_A_gemini.csv"}
CIKTI = KOK / "reports/task17_testv2_etki_olcumu.json"

S = "C:/Users/PC_7820/AppData/Local/Temp/claude/c--Users-PC-7820-Desktop-radyo-vlm/b66eca5b-b3d6-4691-b744-fac9d6ba560e/scratchpad"
TABLOLAR = {
    "ent-1.0_bayat": Path(S) / "ent10_yedek/entities.parquet",
    "ent-1.0r_temiz_referans": Path(S) / "ent10r/entities.parquet",
    "ent-1.1_bizim": P / "entities.parquet",
}


def _normalize(s: str) -> str:
    """Isaretleyici serbest metni ile kavram adini karsilastirilabilir kilar."""
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _ogeler(hucre) -> list[str]:
    """Bir hucredeki serbest listeyi ogelere ayirir."""
    if pd.isna(hucre) or not str(hucre).strip():
        return []
    parcalar = re.split(r"[;,\n|]+", str(hucre))
    return [p for p in (_normalize(x) for x in parcalar) if p]


def _bulundu_mu(oge: str, sistem: set[str]) -> bool:
    """Isaretleyicinin yazdigi oge sistem ciktisinda var mi?

    Gevsek eslesme: oge sistem kavramlarindan/metinlerinden birinin icinde
    ya da tersi. TASK-13 raporunun 'kati okuma alt sinirdir' notuyla ayni
    ruh - burada da ALT SINIR olculur, sisirilmez.
    """
    if oge in sistem:
        return True
    for s in sistem:
        if oge and s and (oge in s or s in oge):
            return True
    return False


def main() -> int:
    for y in [A_DOSYA, *ISARETCILER.values(), *TABLOLAR.values()]:
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    a = pd.read_csv(A_DOSYA)
    print(f"test-v2 kor listeleme: {len(a)} cumle / "
          f"{a['study_id'].nunique()} calisma\n")

    # --- sistem ciktilarini uc tablodan cikar (yalniz test-v2 cumleleri) ---
    anahtar = set(zip(a["study_id"], a["section"], a["sent_idx"]))
    sistem: dict[str, dict] = {}
    for ad, yol in TABLOLAR.items():
        e = pd.read_parquet(yol, columns=[
            "study_id", "section", "sent_idx", "normalized_concept", "raw_text"])
        e = e[[t in anahtar for t in zip(e["study_id"], e["section"], e["sent_idx"])]]
        d: dict = {}
        for (sid, sec, si), g in e.groupby(["study_id", "section", "sent_idx"]):
            d[(sid, sec, si)] = (
                {_normalize(x) for x in g["normalized_concept"]}
                | {_normalize(x) for x in g["raw_text"]}
            )
        sistem[ad] = d
        print(f"  {ad:26} test-v2'de {len(e):>6,} varlik / {len(d)} cumle")

    # --- K5: her isaretleyici x her tablo ---
    print("\n" + "=" * 74)
    print("K5 · DUYARLILIK - kor listelemede yazilan ogelerin kaci bulundu")
    print("=" * 74)
    sonuc: dict = {}
    for isim, yol in ISARETCILER.items():
        m = pd.read_csv(yol)
        birlesik = m.merge(a[["study_id", "section", "sent_idx"]].drop_duplicates(),
                           on=["study_id", "section", "sent_idx"], how="inner") \
            if {"study_id", "section", "sent_idx"}.issubset(m.columns) else m
        sonuc[isim] = {}
        print(f"\n  --- isaretleyici: {isim} ---")
        print(f"  {'tablo':28}{'listelenen':>11}{'bulunan':>9}{'kacan':>7}{'K5':>9}")
        for tad in TABLOLAR:
            top = bul = 0
            kacan_ornek = []
            for _, s in birlesik.iterrows():
                k = (s.get("study_id"), s.get("section"), s.get("sent_idx"))
                sis = sistem[tad].get(k, set())
                for kol in ("bulgular", "anatomiler"):
                    for o in _ogeler(s.get(kol)):
                        top += 1
                        if _bulundu_mu(o, sis):
                            bul += 1
                        elif len(kacan_ornek) < 12:
                            kacan_ornek.append(o)
            k5 = bul / top * 100 if top else 0.0
            sonuc[isim][tad] = {"listelenen": top, "bulunan": bul,
                                "kacan": top - bul, "K5_yuzde": round(k5, 1),
                                "kacan_ornek": kacan_ornek}
            print(f"  {tad:28}{top:>11,}{bul:>9,}{top-bul:>7,}{k5:>8.1f}%")

    # --- iki fark AYRI ---
    print("\n" + "=" * 74)
    print("IKI FARK AYRI - hangisi kimin?")
    print("=" * 74)
    for isim in sonuc:
        b = sonuc[isim]["ent-1.0_bayat"]["K5_yuzde"]
        r = sonuc[isim]["ent-1.0r_temiz_referans"]["K5_yuzde"]
        y = sonuc[isim]["ent-1.1_bizim"]["K5_yuzde"]
        print(f"  {isim:10} bayat {b:5.1f}%  ->  temiz ref {r:5.1f}%  "
              f"({r-b:+.1f} = BASKASININ ONARIMI)  ->  bizim {y:5.1f}%  "
              f"({y-r:+.1f} = TASK-17)")

    rapor = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "protokol": "docs/36_task17_testv2_olcum_protokolu.md (sonuc gorulmeden yazildi)",
        "tek_atis": True,
        "olculen": "K5 duyarlilik (kor listeleme, sozlukten bagimsiz)",
        "olculmeyen": {
            "K4_K6_kesinlik": ("B dosyasi paket uretilirken gosterilen aday listesine "
                               "baglidir; yeni kavramlari kimse yargilamamistir"),
            "klinik_dogruluk": "ground truth yok (D71)",
        },
        "test_v2": {"cumle": int(len(a)), "calisma": int(a["study_id"].nunique())},
        "sonuc": sonuc,
        "baglayici_kural": ("Sonuc ne olursa olsun sozluge/desene/kurala DOKUNULMAZ. "
                            "Dusus kusur olarak ilan edilir. Duzeltme istenirse "
                            "test-v3 zorunludur."),
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
