# -*- coding: utf-8 -*-
"""A1 / TASK-08: Raporlari cumlelere bolup ofsetli sentences.parquet uretir.

Bolutleme kurali (D2 - olcumle secildi):
  Findings   : blok bolme + PyRuSH
  Impression : blok bolme + PyRuSH

  "Blok bolme" = 2+ ardisik bosluktan on bolme. Gerekcesi olculdu:
  Impression'daki 27.985 cift bosluk sinirinin %14,1'inde (3.939 sinir)
  oncesinde noktalama YOK; PyRuSH tek basina bunlari birlestirip kaciriyor.
  Madde isareti / numaralandirma adayi elendi - veride 1-3 raporda geciyor.

Ofsetler (D10): report_text alanina goredir. report_text degistirilmemelidir.

Kullanim:
  .venv/Scripts/python.exe scripts/04_segment_sentences.py            # tam kosu
  .venv/Scripts/python.exe scripts/04_segment_sentences.py --sample 300
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
from loguru import logger  # noqa: E402

logger.remove()  # PyRuSH DEBUG loglari cikti akisini bogar

import medspacy  # noqa: E402,F401  - spaCy fabrikalarini kaydeder (medspacy_pyrush)
import pandas as pd  # noqa: E402
import spacy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "processed" / "reports_study_level.parquet"
OUT = ROOT / "data" / "processed" / "sentences.parquet"

SEGMENTATION_VERSION = "seg-1.1"

# Blok siniri: 2+ bosluk VEYA madde isareti.
# Orta nokta (U+00B7) ilk taramada kacirilmisti: 238 raporda (%0,93), yalnizca
# Impression'da, rapor basina ort. 3,2 madde. Elle inceleme sirasinda bulundu.
BLOK = re.compile(r" {2,}|[·•]+")

# En az bir harf/rakam icermeyen "cumle"ler atilir (238 adet: ',' '.' '?' ';').
HARF = re.compile(r"\w")


def bolum_ofsetleri(findings: str, impressions: str) -> tuple[int | None, int | None]:
    """report_text = (Findings + '\\n\\n' + Impressions).strip() olarak uretilmisti.
    Her bolumun report_text icindeki baslangic ofsetini dondurur."""
    f, i = bool(findings), bool(impressions)
    if f and i:
        return 0, len(findings) + 2
    if f:
        return 0, None
    if i:
        return None, 0
    return None, None


def bloklar(metin: str, taban: int):
    """Metni 2+ bosluktan bloklara ayirir; (blok_metni, mutlak_ofset) uretir."""
    son = 0
    for m in BLOK.finditer(metin):
        parca = metin[son:m.start()]
        if parca.strip():
            yield parca, taban + son
        son = m.end()
    parca = metin[son:]
    if parca.strip():
        yield parca, taban + son


def isleri_hazirla(df: pd.DataFrame):
    """Her (calisma, bolum, blok) icin bolutlenecek is birimi uretir."""
    for satir in df.itertuples(index=False):
        fs, ims = bolum_ofsetleri(satir.Findings_EN, satir.Impressions_EN)
        for bolum, metin, taban in (("findings", satir.Findings_EN, fs),
                                    ("impression", satir.Impressions_EN, ims)):
            if taban is None or not metin:
                continue
            for blok_metni, ofset in bloklar(metin, taban):
                yield blok_metni, (satir.study_id, bolum, ofset)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, help="yalnizca ilk N rapor")
    args = ap.parse_args()

    df = pd.read_parquet(SRC)
    if args.sample:
        df = df.head(args.sample)
    print(f"kaynak: {len(df):,} calisma")

    nlp = spacy.blank("en")
    nlp.add_pipe("medspacy_pyrush")

    # report_text'i dogrulama icin sozluge al
    metinler = dict(zip(df.study_id, df.report_text))

    kayitlar = []
    sayac: dict[tuple[str, str], int] = {}
    t0 = time.time()

    for doc, (sid, bolum, ofset) in nlp.pipe(isleri_hazirla(df), as_tuples=True, batch_size=64):
        for sent in doc.sents:
            ham = sent.text
            if not HARF.search(ham):
                continue  # yalnizca noktalamadan ibaret
            # Bosluklari kirp ve ofsetleri buna gore duzelt (D10: tam esitlik sarti)
            sol = len(ham) - len(ham.lstrip())
            sag = len(ham) - len(ham.rstrip())
            bas = ofset + sent.start_char + sol
            son = ofset + sent.end_char - sag
            metin = ham.strip()

            idx = sayac.get((sid, bolum), 0)
            sayac[(sid, bolum)] = idx + 1
            kayitlar.append((sid, bolum, idx, metin, bas, son, len(metin)))

    dt = time.time() - t0
    out = pd.DataFrame(kayitlar, columns=[
        "study_id", "section", "sent_idx", "text", "char_start", "char_end", "n_char"])
    out["segmentation_version"] = SEGMENTATION_VERSION

    # --- Ofset dogrulamasi: text, report_text'ten birebir kesilebilmeli ---
    hatali = 0
    for r in out.itertuples(index=False):
        if metinler[r.study_id][r.char_start:r.char_end] != r.text:
            hatali += 1
    print(f"\nOFSET DOGRULAMASI: {len(out) - hatali:,}/{len(out):,} dogru", end="")
    print("  [TAMAM]" if hatali == 0 else f"  [HATA: {hatali}]")
    if hatali:
        sys.exit("Ofset dogrulamasi basarisiz - yazma iptal edildi")

    out.to_parquet(OUT, index=False)

    print(f"\nyazildi: {OUT.name}")
    print(f"  cumle sayisi   : {len(out):,}")
    print(f"  sure           : {dt/60:.1f} dakika ({dt/len(df)*1000:.1f} ms/rapor)")
    print(f"  bolum dagilimi :")
    for b, n in out.section.value_counts().items():
        c = out[out.section == b]
        print(f"    {b:<11} {n:>7,} cumle | calisma basina medyan "
              f"{c.groupby('study_id').size().median():.0f} | medyan uzunluk {c.n_char.median():.0f}")
    print(f"  benzersiz cumle: {out.text.nunique():,} ({100*out.text.nunique()/len(out):.1f}%)")


if __name__ == "__main__":
    main()
