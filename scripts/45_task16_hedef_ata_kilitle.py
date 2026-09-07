"""TASK-16 Adim 4b - HEDEF SINIFLARIN ATANMASI ve TAKIMLARIN KILITLENMESI.

Plan: docs/29 §8.1

Hedefler KURALLAR YAZILMADAN ONCE atanir. Her hedef, dayanagini (A<n> kurali ya
da C#<n> varsayilani) ve gerekcesini tasir.

⚠ ARTIK SINIR: hedefleri atayan taraf ile kurallari yazacak taraf AYNIDIR. Bunun
tam bagimsiz bir sinav olmadigi kayitlidir. Azaltici uc onlem:
  1. Vakalar ILAN EDILMIS yordamla ornekLendi (scripts/44), elle secilmedi
  2. Hedefler kurallardan ONCE atanip HASH'lenip KILITLENIYOR
  3. Hedefin dayanagi A ise sinav gercek bir disaridan denetimdir; C ise
     yalnizca ic tutarlilik kontroludur - ikisi ayri raporlanir

Kilitten sonra vaka eklenemez/cikarilamaz. Kural takimi gecemezse KURAL degisir.

Kullanim:
    python scripts/45_task16_hedef_ata_kilitle.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from radyovlm.evaluation import envanter as env  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
SINIR = KOK / "data/processed/sema_sinir_vakalari.csv"
KONTROL = KOK / "data/processed/sema_negatif_kontrol.csv"
MANIFEST = KOK / "configs/sema_takim_kilidi.json"

# vaka_id -> (hedef_sinif, hedef_kaynagi, gerekce)
HEDEF_SINIR = {
    "C1-negasyon-kapsami-01": ("None", "A1+A19", "Metastaz negasyon KAPSAMI icinde: 'No metastases ... were observed'"),
    "C1-negasyon-kapsami-02": ("intermediate", "C#1+C#4", "Negasyon INCELEMEYE ait ('could not be characterized'), metastaza degil; bulgu 'might belong to metastasis' = orta derece"),
    "C1-negasyon-kapsami-03": ("None", "A1", "'no significant tumoral wall thickening was detected' - tumoral kapsam icinde"),
    "C4-derece-yuksek-01": ("known_malignancy", "C#4", "'metastatic masses in the liver' HUKUM olarak yaziliyor, cekince yok"),
    "C4-derece-yuksek-02": ("high", "C#4", "'highly suspicious ... in favor of malignancy' - yuksek derece ama patoloji yok; 'histopathological diagnosis will be appropriate'"),
    "C4-derece-orta-01": ("intermediate", "C#4", "'may be compatible with capsular metastasis' - orta derece"),
    "C4-derece-orta-02": ("indeterminate", "C#16", "'may be of fungal infection OR metastasis' - ayirici tani, taraf tutulmaz"),
    "C4-derece-dislanamaz-01": ("indeterminate", "A3+A18", "'metastasis cannot be excluded' - Kritik kural 1: present degil"),
    "C4-derece-dislanamaz-02": ("indeterminate", "A3+A18", "'malignancy cannot be excluded'"),
    "C5-stabil-malignite-01": ("known_malignancy", "C#5", "'regressed primary malignancy' bilinen; 'stable' tanıyı degistirmez"),
    "C5-stabil-malignite-02": ("high", "A8+C#5", "'evaluated in favor of metastasis' = present (A8); patoloji yok, 'stable' dusurmez"),
    "C5-stabil-malignite-03": ("known_malignancy", "C#5", "'metastatic masses observed in T1 and L1' HUKUM; 'no significant change' yalniz degisimi olumsuzluyor"),
    "C6-malignite-benign-01": ("intermediate", "C#4", "Nodullar sekel arasinda ama 'may be compatible with metastasis' - orta derece"),
    "C6-malignite-benign-02": ("low", "C#6+A8", "'spiculated' malignite gostergesi VAR ama radyolog 'in favor of sequela' diye HUKUM vermis; hukum gecerli, gosterge kayitli"),
    "C6-malignite-benign-03": ("indeterminate", "A3+A18", "Sekel degisiklikler + 'underlying malignancy cannot be excluded'"),
    "C11-olumsuz-belirsiz-01": ("None", "A1", "'No suspicious nodular or mass-occupying lesion ... was detected' - supheyi olumsuzluyor"),
    "C11-olumsuz-belirsiz-02": ("indeterminate", "A16", "Teknik kisitlilik: 'not possible to comment' + karaciger lezyonlari VAR ama karakterize edilemiyor"),
    "C12-benign-belirsiz-01": ("low", "C#12+A26", "'hilar fat contents' = A26 benign ozellik; 'possibly benign' hukmu"),
    "C12-benign-belirsiz-02": ("low", "C#12+A26", "Ayni icerik, farkli ifade (ornekleme artefakti - kayitli)"),
    "C12-benign-belirsiz-03": ("low", "C#12", "'nodule developed on the subpleural possible sequelae' - benign zemin, kucuk nodul"),
    "C13-ekstratorasik-01": ("known_malignancy", "C#13", "'newly emerged metastases in the liver and spleen' HUKUM; ekstratorasik ELENMEZ"),
    "C13-ekstratorasik-02": ("indeterminate", "C#10", "Yeni karaciger lezyonlari + '(metastasis?)' - soru isareti epistemik belirsizlik"),
    "C13-ekstratorasik-03": ("known_malignancy", "C#13", "'Bladder ca' bilinen + 'liver metastases' + lenfanjitis karsinomatoza"),
    "C16-malignite-enf-01": ("known_malignancy", "C#13", "'patient's known primary and lung metastasis' asserted; enfeksiyon ayirici tanida ama malignite BILINEN"),
    "C16-malignite-enf-02": ("indeterminate", "C#16", "'may belong to infection, metastasis could not be excluded' - ayirici tani"),
    "C16-malignite-enf-03": ("low", "A17+A20", "'control for neoplasia is recommended' bir ONERIDIR, status degil (Kritik kural 3); bulgu enfeksiyon"),
    "A8-cikarim-ifadesi-01": ("not_mentioned", "A7", "'compatible with COPD' - malignite ekseninde ifade YOK"),
    "A8-cikarim-ifadesi-02": ("not_mentioned", "A7", "Sekel + enfektif alan; malignite ekseninde ifade YOK"),
    "A26-kalsifikasyon-01": ("intermediate", "A26+C#7", "'spiculated contours CONTAINING CALCIFICATIONS' - kalsifikasyon A26 benign listesinde degil, spikulasyon supheli"),
    "A26-kalsifikasyon-02": ("intermediate", "A26+C#5+C#7", "'AMORPHOUS calcification' A26 listesinde YOK; 'spicular contour' supheli; 'stable' dusurmez"),
}

HEDEF_KONTROL = {
    "K-olumsuz-kitle-01": ("None", "A1", "'no solid mass was detected'"),
    "K-olumsuz-kitle-02": ("None", "A1", "'does not give a subpleural mass contour'"),
    "K-olumsuz-kitle-03": ("None", "A1", "'no mass with distinguishable borders'"),
    "K-olumsuz-kitle-04": ("None", "A1", "'No mass or nodule was detected'"),
    "K-sekel-benign-01": ("not_mentioned", "A10", "Sekel + nonspesifik nodul; malignite ifadesi yok"),
    "K-sekel-benign-02": ("not_mentioned", "A10", "Sekel + kalsifiye nonspesifik nodul; malignite ifadesi yok"),
    "K-sekel-benign-03": ("not_mentioned", "A10", "Sekel + nonspesifik nodul"),
    "K-sekel-benign-04": ("not_mentioned", "A10", "Plevroparankimal sekel + dansite artisi"),
    "K-enfeksiyon-01": ("not_mentioned", "A10", "Bronsektazi, atelektazi, kalsifikasyon; malignite ifadesi yok"),
    "K-enfeksiyon-02": ("not_mentioned", "A27", "'viral pneumonia cannot be excluded' - belirsizlik ENFEKSIYONA dair, malignite eksenine GIRMEZ"),
    "K-enfeksiyon-03": ("not_mentioned", "A10", "Sekel + pnomonik infiltrasyon"),
    "K-stabil-benign-01": ("not_mentioned", "A10", "Sekel fibroatelektazi + kalsifiye plevral plak"),
    "K-stabil-benign-02": ("not_mentioned", "A10+A11", "'Possible postoperative sequelae ... are stable'"),
    "K-teknik-01": ("not_mentioned", "A16", "'could not be optimally evaluated' - teknik cekince"),
    "K-teknik-02": ("not_mentioned", "A16", "Artefakttan ayirt edilemeyen tiroid hipodansitesi; malignite ekseni disi"),
}

# v1.1 DUZELTME (2. denetim, bulgu 3.1): `indeterminate` YONLU bir malignite
# supheti degil, epistemik/teknik belirsizliktir (docs/31 #8: 4 sinifli semada
# "belirsiz"e gider, ama "belirsiz" ile "supheli" ayni sey degildir - burada
# koruma kapisinin amaci semanin YONLU suphe URETMEMESIDIR). indeterminate
# disarida birakildi.
# TASK-17 madde 3 (D79): kilitli takimin KENDI gecerliligi - kontrol
# vakasina malignite HEDEFI yazilamaz. Motorun CIKTISINI sinayan kapi
# AYRI bir kumedir (env.KAPI_MALIGNITE_SINIFLARI) ve Karar 2 yalniz
# ONA uygulandi. Bu kume DEGISMEDI.
MALIGN_URETIR = env.HEDEF_MALIGNITE_SINIFLARI


def sha(y: Path) -> str:
    return hashlib.sha256(y.read_bytes()).hexdigest()


def doldur(yol: Path, hedefler: dict, ad: str) -> pd.DataFrame:
    d = pd.read_csv(yol, keep_default_na=False)
    eksik = set(d["vaka_id"]) - set(hedefler)
    fazla = set(hedefler) - set(d["vaka_id"])
    if eksik or fazla:
        print(f"HATA [{ad}]: hedefsiz vaka {sorted(eksik)} · karsiliksiz hedef {sorted(fazla)}")
        sys.exit(1)
    d["hedef_sinif"] = d["vaka_id"].map(lambda v: hedefler[v][0])
    d["hedef_kaynagi"] = d["vaka_id"].map(lambda v: hedefler[v][1])
    d["hedef_gerekcesi"] = d["vaka_id"].map(lambda v: hedefler[v][2])
    d.to_csv(yol, index=False, encoding="utf-8")
    return d


def main() -> int:
    if MANIFEST.exists():
        print(f"HATA: takim ZATEN KILITLI: {MANIFEST}")
        print("      Kilitli takim degistirilemez (docs/29 §8.1/4).")
        return 1
    for y in (SINIR, KONTROL):
        if not y.exists():
            print(f"HATA: once scripts/44 kosulmali: {y}")
            return 1

    ds = doldur(SINIR, HEDEF_SINIR, "sinir")
    dk = doldur(KONTROL, HEDEF_KONTROL, "kontrol")

    # kontrol takiminin degismezi: hicbiri malignite uretmemeli
    ihlal = dk[dk["hedef_sinif"].isin(MALIGN_URETIR)]
    if not ihlal.empty:
        print(f"HATA: kontrol takiminda malignite ureten hedef var: {ihlal['vaka_id'].tolist()}")
        return 1

    print("SINIR TAKIMI - hedef dagilimi")
    for k, v in ds["hedef_sinif"].value_counts().items():
        print(f"  {k:20} {v:>3}")
    a_dayanakli = int(ds["hedef_kaynagi"].str.startswith("A").sum())
    print(f"\n  hedefi A kuraline dayanan  : {a_dayanakli:>3} / {len(ds)}  (gercek dis denetim)")
    print(f"  hedefi C varsayilanina dayanan: {len(ds)-a_dayanakli:>3} / {len(ds)}  (ic tutarlilik)")

    print("\nKONTROL TAKIMI")
    for k, v in dk["hedef_sinif"].value_counts().items():
        print(f"  {k:20} {v:>3}")
    print(f"  hicbiri malignite uretmiyor: OK ({len(dk)} vaka)")

    manifest = {
        "surum": "takim-1.0",
        "kilit_utc": datetime.now(timezone.utc).isoformat(),
        "ornekleme_tohumu": 20260904,
        "kural": "Kilitten sonra vaka EKLENEMEZ/CIKARILAMAZ. Kural takimi gecemezse "
                 "KURAL degisir, takim degil (docs/29 §8.1/4).",
        "artik_sinir": "Hedefleri atayan taraf ile kurallari yazacak taraf ayni. "
                       "Hedefi A kuraline dayanan vakalar gercek dis denetimdir; C'ye "
                       "dayananlar ic tutarlilik kontroludur. Ikisi ayri raporlanir.",
        "sinir_takimi": {
            "dosya": "data/processed/sema_sinir_vakalari.csv",
            "vaka": len(ds), "sha256": sha(SINIR),
            "hedef_dagilimi": ds["hedef_sinif"].value_counts().to_dict(),
            "A_dayanakli_hedef": a_dayanakli,
            "C_dayanakli_hedef": len(ds) - a_dayanakli,
        },
        "kontrol_takimi": {
            "dosya": "data/processed/sema_negatif_kontrol.csv",
            "vaka": len(dk), "sha256": sha(KONTROL),
            "kapi": "Sema bu vakalarin HICBIRINDE malignite uretmeyecek. Tolerans YOK (%100).",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nKILITLENDI: {MANIFEST.relative_to(KOK)}")
    print(f"  sinir   sha256 {manifest['sinir_takimi']['sha256'][:16]}")
    print(f"  kontrol sha256 {manifest['kontrol_takimi']['sha256'][:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
