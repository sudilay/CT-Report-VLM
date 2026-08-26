# -*- coding: utf-8 -*-
"""A3 / TASK-08: Sablon kimliklerini ve istatistiklerini cumle tablosuna isler.

Kararlar:
  D3  - Yalnizca sayilar maskelenir; anatomi ve taraf korunur (klinik olarak anlamli).
  D4  - Esik K = 10 farkli TRAIN hastasi (20.000 hasta icinde). Birlikte secildi.
  D11 - Katalog YALNIZCA train'den hesaplanir, valid'e uygulanir. Train katalogunda
        karsilik bulamayan valid cumlesi -> is_stock_phrasing = False.
  D9  - Faz 1 yalnizca YAPISAL bilgi kaydeder.
  D12 - template_type dortlu siniflandirmasi (negatif_ifade / normal_beyan /
        pozitif_bulgu / serbest) Faz 2'ye TASINDI. Dort tipin ucu negasyon analizi
        gerektiriyordu; bunu Faz 1'de regex ile yapmak hem D9'a aykiriydi hem de
        Faz 2'de medspaCy ConText ile yapilacak dogru analizin kotu bir kopyasi
        olurdu. Faz 1'de kalan tek yapisal ozellik: has_technical_caveat.

Uretilen kolonlar:
  template_id_exact     birebir ayni cumlelerin kimligi
  template_id_norm      sayilar maskelendikten sonraki kimlik
  n_patients_train      kalibin kac FARKLI TRAIN HASTASINDA gectigi (surekli deger;
                        bayrak degisse de bu sayi korunur, sonraki fazlar kendi
                        esigini secebilir)
  is_stock_phrasing     n_patients_train >= K_ESIK

                        !! Bu bayrak "bu ifade standart kaliptir" demektir,
                        "bu cumle onemsizdir" DEMEZ. FILTRELEME ICIN KULLANILMAZ.
                        Tek kelimelik tanilar (Cholelithiasis, Cardiomegaly,
                        Hepatosteatosis) en kesin sekilde kalip isaretlenir cunku
                        yazmanin tek bir yolu vardir - ama bilgi yogunlugu en
                        yuksek cumlelerdir. "Bu cumle bilgi tasiyor mu" sorusunun
                        cevabi Faz 2'den, bulgu (entity) cikarimindan gelir;
                        frekanstan degil. Onceki adi is_boilerplate idi;
                        "onemsiz" cagrisimi yaptigi icin degistirildi.

  has_technical_caveat  cumle tetkik sinirliligi bildiriyor mu ("as far as can be
                        seen", "could not be evaluated", "unenhanced"). Negasyondan
                        BAGIMSIZ bir eksendir; bir cumle hem klinik icerik hem
                        teknik cekince tasiyabilir.

Sira: 04_segment_sentences.py -> 06_apply_templates.py
Kullanim: .venv/Scripts/python.exe scripts/06_apply_templates.py
"""
import hashlib
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SENT = ROOT / "data" / "processed" / "sentences.parquet"
REPS = ROOT / "data" / "processed" / "reports_study_level.parquet"
OUTD = ROOT / "reports"

PIPELINE_VERSION = "tmpl-1.0"
K_ESIK = 10          # D4
ELLE_ETIKET_N = 350  # kabul olcutu: ilk 200 %46,2 kapsadi (<%50), sayi artirildi

# 04_segment_sentences.py'nin urettigi taban kolonlar. Bu scriptin ciktisi
# tekrar calistirildiginda eski kolonlar birikmesin diye acikca listelenir.
TABAN_KOLONLAR = ["study_id", "section", "sent_idx", "text",
                  "char_start", "char_end", "n_char"]

SAYI = re.compile(r"\d+(?:\.\d+)?")
BOSLUK = re.compile(r"\s+")

# --- Teknik cekince tespiti -------------------------------------------------
# Cumlenin tetkikin kendisi veya sinirliliklari hakkinda bir sey soyleyip
# soylemedigi. NEGASYON TESPITI DEGILDIR - o Faz 2'nin isi (D12).
TEKNIK = re.compile(
    r"\b(?:unenhanced|non[- ]?contrast|without contrast|contrast (?:agent|material)|"
    r"suboptimal|artifact|as far as (?:can|could) be|"
    r"within the (?:examination|study|image) (?:limits|borders)|"
    r"within the borders of|(?:can|could)not be (?:evaluated|assessed|distinguished)|"
    r"sections? (?:were |was )?(?:taken|obtained)|thick sections?|"
    r"reconstruct\w*|axial plane|workstation)\b", re.I)


def normalize(metin: str) -> str:
    """D3: sayilari maskele, bosluklari sadelestir, kucuk harfe indir."""
    return BOSLUK.sub(" ", SAYI.sub("<NUM>", metin.lower())).strip()


def kimlik(metin: str) -> str:
    return hashlib.sha1(metin.encode("utf-8")).hexdigest()[:12]


def teknik_cekince(metin: str) -> bool:
    """Cumle tetkikin kendisi veya sinirliliklari hakkinda bir sey soyluyor mu."""
    return bool(TEKNIK.search(metin))


def main() -> None:
    OUTD.mkdir(exist_ok=True)

    sent = pd.read_parquet(SENT)
    eksik = [c for c in TABAN_KOLONLAR if c not in sent.columns]
    if eksik:
        raise SystemExit(f"Taban kolonlar eksik: {eksik} - once 04_segment_sentences.py")
    atilan = [c for c in sent.columns if c not in TABAN_KOLONLAR]
    if atilan:
        print(f"onceki kosudan kalan kolonlar atiliyor: {atilan}")
    sent = sent[TABAN_KOLONLAR].copy()

    reps = pd.read_parquet(REPS, columns=["study_id", "patient_id", "split"])
    sent = sent.merge(reps, on="study_id", how="left")

    sent["norm"] = sent.text.map(normalize)
    sent["template_id_exact"] = sent.text.map(kimlik)
    sent["template_id_norm"] = sent.norm.map(kimlik)

    # --- D11: katalog YALNIZCA train'den ---
    train = sent[sent.split == "train"]
    katalog = train.groupby("norm")["patient_id"].nunique()
    print(f"train cumle          : {len(train):,}  ({train.patient_id.nunique():,} hasta)")
    print(f"train sablon ailesi  : {len(katalog):,}")

    # --- valid'e UYGULA; eslesmeyen -> 0 (sablon degil) ---
    sent["n_patients_train"] = sent.norm.map(katalog).fillna(0).astype(int)
    sent["is_stock_phrasing"] = sent.n_patients_train >= K_ESIK
    sent["has_technical_caveat"] = sent.text.map(teknik_cekince)
    sent["pipeline_version"] = PIPELINE_VERSION

    valid = sent[sent.split == "valid"]
    eslesmeyen = (valid.n_patients_train == 0).sum()
    print(f"valid'de eslesmeyen  : {eslesmeyen:,} / {len(valid):,} "
          f"(%{100*eslesmeyen/len(valid):.1f}) -> is_stock_phrasing=False")

    print(f"\nESIK K={K_ESIK}")
    print(f"  sablon isaretli cumle : {sent.is_stock_phrasing.sum():,} "
          f"(%{100*sent.is_stock_phrasing.mean():.1f})")
    print(f"  sablon ailesi         : {(katalog >= K_ESIK).sum():,}")

    tc = sent.has_technical_caveat
    print(f"\nTEKNIK CEKINCE (negasyondan bagimsiz eksen)")
    print(f"  cekince iceren cumle  : {tc.sum():,} (%{100*tc.mean():.1f})")
    print(f"  bunlarin sablon olani : {(tc & sent.is_stock_phrasing).sum():,}")
    print(f"  cekince iceren aile   : {sent[tc].template_id_norm.nunique():,}")

    kolonlar = [c for c in sent.columns if c not in ("norm", "patient_id", "split")]
    sent[kolonlar].to_parquet(SENT, index=False)
    print(f"\nyazildi: {SENT.name}  ({len(sent):,} satir, {len(kolonlar)} kolon)")

    # --- Elle dogrulama listesi (D4: esik manuel ornekle dogrulanacak) ---
    ust = katalog[katalog >= K_ESIK].sort_values(ascending=False).head(ELLE_ETIKET_N)
    ornek = train.drop_duplicates("norm").set_index("norm")["text"]
    liste = pd.DataFrame({
        "sira": range(1, len(ust) + 1),
        "n_hasta": ust.values,
        "teknik_cekince": [teknik_cekince(ornek[n]) for n in ust.index],
        "sablon_mu_onay": "",
        "ornek_cumle": [ornek[n] for n in ust.index],
    })
    yol = OUTD / "sablon_dogrulama.csv"
    liste.to_csv(yol, index=False, encoding="utf-8-sig")
    kaps = 100 * train[train.norm.isin(ust.index)].shape[0] / len(train)
    print(f"elle dogrulama listesi: reports/{yol.name} "
          f"(ilk {ELLE_ETIKET_N} sablon, train cumlelerinin %{kaps:.1f}'i)")


if __name__ == "__main__":
    main()
