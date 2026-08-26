"""T-01 kontrol araci: uretilen korpusu her acidan gozle dogrulamani saglar.

Kullanim:
  .venv/Scripts/python.exe scripts/02_inspect_corpus.py            # ozet
  .venv/Scripts/python.exe scripts/02_inspect_corpus.py --report 5 # 5. raporu tam goster
  .venv/Scripts/python.exe scripts/02_inspect_corpus.py --search spiculat  # kelime ara
"""
import sys, argparse
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
DF = pd.read_parquet(ROOT / "data" / "processed" / "reports_study_level.parquet")

LABELS = ['Medical material', 'Arterial wall calcification', 'Cardiomegaly', 'Pericardial effusion',
          'Coronary artery wall calcification', 'Hiatal hernia', 'Lymphadenopathy', 'Emphysema',
          'Atelectasis', 'Lung nodule', 'Lung opacity', 'Pulmonary fibrotic sequela', 'Pleural effusion',
          'Mosaic attenuation pattern', 'Peribronchial thickening', 'Consolidation', 'Bronchiectasis',
          'Interlobular septal thickening']


def line(t=""):
    print(f"\n{'='*72}\n{t}\n{'='*72}" if t else "")


def summary():
    line("1. KORPUS BUYUKLUGU")
    print(f"  calisma (satir)     : {len(DF):,}")
    print(f"  benzersiz hasta     : {DF['patient_id'].nunique():,}")
    print(f"  calisma/hasta orani : {len(DF)/DF['patient_id'].nunique():.2f}")
    print(f"\n  split dagilimi:")
    print(DF['split'].value_counts().to_string().replace('\n', '\n    '))

    line("2. KOLONLAR (ne elimizde var)")
    for c in DF.columns:
        nn = DF[c].notna().sum()
        print(f"  {c:<38} dolu={nn:>6,} ({100*nn/len(DF):5.1f}%)  {DF[c].dtype}")

    line("3. HASTA DEMOGRAFISI")
    print(f"  cinsiyet:\n{DF['PatientSex'].value_counts(dropna=False).to_string()}")
    age = pd.to_numeric(DF['PatientAge'].astype(str).str.extract(r'(\d+)')[0], errors='coerce')
    print(f"\n  yas: medyan={age.median():.0f}  min={age.min():.0f}  max={age.max():.0f}  bos={age.isna().sum()}")

    line("4. RAPOR UZUNLUKLARI (karakter)")
    for c in ['Findings_EN', 'Impressions_EN', 'ClinicalInformation_EN']:
        s = DF[c].str.len()
        print(f"  {c:<24} medyan={s.median():>6.0f}  p95={s.quantile(.95):>6.0f}  max={s.max():>6.0f}  bos={(s==0).sum():>4}")
    print(f"\n  >> Impression, Findings'in ~{DF['Impressions_EN'].str.len().median()/DF['Findings_EN'].str.len().median()*100:.0f}%'i kadar. Yani radyolog ciddi bir eleme yapiyor.")

    line("5. CT-RATE'IN 18 OTOMATIK ETIKETI (prevalans)")
    print("  NOT: bunlar raporlardan otomatik uretildi, radyolog dogrulamasi DEGIL.")
    prev = DF[LABELS].mean().sort_values(ascending=False)
    for k, v in prev.items():
        bar = '#' * int(v * 50)
        print(f"  {k:<36} {100*v:5.1f}%  {bar}")
    print(f"\n  >> Icinde malignite/kanser/kitle etiketi YOK. En yakini 'Lung nodule'.")

    line("6. KLINIK BILGI ALANI NE KADAR DOLU?")
    ci = DF['ClinicalInformation_EN'].str.strip().str.lower()
    empty = ci.isin(['', 'not given.', 'not given', 'none.', 'none'])
    print(f"  bos/'not given' : {empty.sum():,} ({100*empty.mean():.1f}%)")
    print(f"  gercek icerik   : {(~empty).sum():,} ({100*(~empty).mean():.1f}%)")
    print("\n  gercek icerik ornekleri:")
    for t in DF.loc[~empty, 'ClinicalInformation_EN'].drop_duplicates().head(6):
        print(f"    - {t[:100]}")

    line("7. SABLON CUMLE SORUNU (T-01'in kalan iSi)")
    sents = DF['Findings_EN'].str.split(r'(?<=[.])\s+').explode().str.strip()
    sents = sents[sents.str.len() > 15]
    vc = sents.value_counts()
    tekrar = vc[vc > 1].sum()
    print(f"  toplam cumle          : {len(sents):,}")
    print(f"  benzersiz cumle       : {len(vc):,}")
    print(f"  >1 kez tekrar eden    : {tekrar:,} ({100*tekrar/len(sents):.1f}%)  <-- sablon yuku")
    print("\n  EN COK TEKRAR EDEN 12 CUMLE:")
    for s, n in vc.head(12).items():
        print(f"    {n:>6,}x  {s[:95]}")


def show_report(i):
    r = DF.iloc[i]
    line(f"RAPOR #{i}  |  {r['VolumeName']}  |  hasta={r['patient_id']}  split={r['split']}")
    print(f"\n[YAS/CINSIYET] {r['PatientAge']} / {r['PatientSex']}")
    for c in ['ClinicalInformation_EN', 'Technique_EN', 'Findings_EN', 'Impressions_EN']:
        print(f"\n--- {c} ---\n{r[c]}")
    pos = [l for l in LABELS if r[l] == 1]
    print(f"\n--- OTOMATIK ETIKETLER (pozitif) ---\n{pos if pos else 'hicbiri'}")


def search(kw, n=8):
    m = DF['report_text'].str.contains(kw, case=False, na=False)
    line(f"'{kw}' ARAMASI  ->  {m.sum():,} calisma (%{100*m.mean():.2f})")
    import re
    for _, r in DF[m].head(n).iterrows():
        for s in re.split(r'(?<=[.])\s+', r['report_text']):
            if kw.lower() in s.lower():
                print(f"  [{r['VolumeName']}] {s.strip()[:160]}")
                break


def show_sentences(i):
    """Bir raporun cumlelere nasil bolundugunu ofsetleriyle birlikte gosterir."""
    sp = ROOT / "data" / "processed" / "sentences.parquet"
    if not sp.exists():
        print("sentences.parquet yok - once scripts/04_segment_sentences.py calistir")
        return
    r = DF.iloc[i]
    s = pd.read_parquet(sp)
    s = s[s.study_id == r["study_id"]].sort_values(["section", "sent_idx"])
    line(f"RAPOR #{i}  {r['study_id']}  ->  {len(s)} cumle")
    for bolum in ["findings", "impression"]:
        alt = s[s.section == bolum]
        if not len(alt):
            continue
        print(f"\n--- {bolum.upper()} ({len(alt)} cumle) ---")
        for x in alt.itertuples(index=False):
            # ofsetin gercekten oturdugunu goster
            ok = "ok" if r["report_text"][x.char_start:x.char_end] == x.text else "HATA"
            print(f"  {x.sent_idx:>2}. [{x.char_start:>5}-{x.char_end:<5} {ok}] {x.text}")


def uc_noktalar(n=6):
    """En uzun ve en kisa cumleler - bolutlemenin uc durumlarini gozle gormek icin."""
    sp = ROOT / "data" / "processed" / "sentences.parquet"
    if not sp.exists():
        print("sentences.parquet yok"); return
    s = pd.read_parquet(sp)
    line(f"EN UZUN {n} CUMLE  (bolunememis madde olabilir mi?)")
    for x in s.nlargest(n, "n_char").itertuples(index=False):
        print(f"  [{x.n_char:>4} krk · {x.section}] {x.text[:300]}")
    line(f"EN KISA {n} CUMLE  (asiri bolunme olabilir mi?)")
    for x in s.nsmallest(n, "n_char").itertuples(index=False):
        print(f"  [{x.n_char:>4} krk · {x.section}] {x.text!r}")
    line("UZUNLUK DAGILIMI")
    q = s.n_char.quantile([.5, .9, .99, 1.0])
    print(f"  medyan={q[.5]:.0f}  p90={q[.9]:.0f}  p99={q[.99]:.0f}  max={q[1.0]:.0f}")
    print(f"  400 karakterden uzun: {(s.n_char > 400).sum()} (%{100*(s.n_char > 400).mean():.2f})")
    print(f"  20 karakterden kisa : {(s.n_char < 20).sum()} (%{100*(s.n_char < 20).mean():.2f})")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=int, help="raporu tam metin olarak goster")
    p.add_argument("--sents", type=int, help="raporun cumlelere bolunmusunu goster")
    p.add_argument("--uc", action="store_true", help="en uzun/kisa cumleler")
    p.add_argument("--search", type=str)
    a = p.parse_args()
    if a.report is not None: show_report(a.report)
    elif a.sents is not None: show_sentences(a.sents)
    elif a.uc: uc_noktalar()
    elif a.search: search(a.search)
    else: summary()
