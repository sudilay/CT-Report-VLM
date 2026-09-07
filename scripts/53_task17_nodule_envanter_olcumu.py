"""TASK-17 Madde 4 - `nodule` KAVRAMININ ENVANTER OLCUMU.

Plan: docs/34_task17_calisma_plani.md v2 §4.3 (Karar 3, kullanici onayli;
denetim B6 ile DARALTILDI) · Karar kaydi: D80

SORU
----
Ciplak `nodule` bir MALIGNITE GOSTERGESI midir?

Bugun semanin `MALIGNITE_KAVRAMLARI` listesinde ve dolayisiyla rapor sinifini
yukseltebiliyor. Ama kontrol takiminin 6/23'u present malignite kavrami
tasiyor ve cogu sablon "nonspecific nodules" cumlesi; onlari sessiz tutan TEK
sey F2 girdi filtresi (docs/34 §4.3). Yani dogru sonuc YANLIS gerekceyle
uretiliyor olabilir.

⚠ KAPSAM DENETIM TARAFINDAN DARALTILDI (B6, docs/35 §7)
-------------------------------------------------------
v1 dort kavrami (`nodule`, `mass`, `space_occupying_lesion`,
`lytic_destructive_lesion`) niteleyici sikligiyla olcup KADEMELENDIRMEYI
oneriyordu. Denetim hakli olarak reddetti: **ground truth olmayan bir
korpusta niteleyici sikligi bir kavramin gosterge niteligini DUSURMEYE
YETMEZ.** Siklik kapsam belirler, klinik agirlik vermez (docs/29 §2.2/B) -
v1 kendi onerisinde bu kurali ihlal ediyordu. Denetimin somut ornegi:
"sag alt lobda 3 cm kitle" cumlesinde niteleyici YOKTUR ama bulgu ACIKTIR.

Bu yuzden:
  `mass`, `lytic_destructive_lesion`, `space_occupying_lesion`
      -> DOGRUDAN GOSTERGE KALIR, INCELENMEZ
  `nodule`
      -> TEK incelenen kavram, ve YALNIZ sablon / "nonspecific" ekseninde

⚠ BU BETIK KARAR VERMEZ, OLCER. Kural yazilip yazilmayacagi olcume ve
kullanici onayina baglidir.

KAPSAM: yalniz GELISTIRME HAVUZU. Degerlendirme kilidi okunmaz.

Kullanim:
    .venv/Scripts/python.exe scripts/53_task17_nodule_envanter_olcumu.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from radyovlm.evaluation import envanter as env  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
VARLIKLAR = KOK / "data/processed/entities.parquet"
CUMLELER = KOK / "data/processed/sentences.parquet"
ILISKILER = KOK / "data/processed/relations.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
KONTROL = KOK / "data/processed/sema_negatif_kontrol.csv"
CIKTI = KOK / "reports/task17_nodule_envanter_olcumu.json"

ORNEK = 6
TOHUM = 20260907

# "Supheli" morfoloji/dansite niteleyicileri - kavram duzeyinde, `modify`
# iliskisiyle nodule'e bagli olanlar. Kaynak: bulgu_sozlugu.yaml
# niteleyici gruplari `margin` ve `density`.
SUPHELI_NITELEYICI = frozenset({
    "spiculated", "irregular", "lobulated", "indistinct", "halo",
    "part_solid", "ground_glass", "solid", "necrotic",
})
# Aksi yonde: benign/rastlantisal niteleyiciler
BENIGN_NITELEYICI = frozenset({
    "calcific", "sequela", "granulomatous", "punctate", "smooth",
    "well_defined", "fat_containing",
})

# METIN duzeyi kaliplar - bunlar sozlukte KAVRAM DEGIL (olculdu 2026-09-07),
# o yuzden cumle metninden okunur.
NONSPECIFIC = r"non-?specific"
MILLIMETRIC = r"millimetric|milimetric"


def _ornekler(seri: pd.Series, n: int = ORNEK) -> list[str]:
    if seri.empty:
        return []
    return [t[:200] for t in seri.sample(min(n, len(seri)), random_state=TOHUM)]


def main() -> int:
    for y in (VARLIKLAR, CUMLELER, ILISKILER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])
    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    gelistirme = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])

    v = pd.read_parquet(VARLIKLAR, columns=[
        "entity_id", "study_id", "sent_idx", "section", "normalized_concept",
        "assertion", "assertion_rule", "raw_text"])
    v = v[v["study_id"].isin(gelistirme)]

    c = pd.read_parquet(CUMLELER, columns=[
        "study_id", "section", "sent_idx", "text", "is_stock_phrasing"])
    c = c[c["study_id"].isin(gelistirme)]

    print(f"kapsam: gelistirme havuzu · {len(gelistirme):,} calisma "
          f"· {len(v):,} varlik  (kilit OKUNMADI)\n")

    rapor: dict = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit["surum"],
        "ornek_tohumu": TOHUM,
        "incelenen_kavram": "nodule",
        "incelenmeyen_kavramlar": {
            "liste": ["mass", "lytic_destructive_lesion", "space_occupying_lesion"],
            "gerekce": "denetim B6 (docs/35 §7) - dogrudan gosterge kalir",
        },
    }

    # --- cumle metnini varliga bagla ---
    v = v.merge(c, on=["study_id", "section", "sent_idx"], how="left")
    v["text"] = v["text"].fillna("")

    nod = v[v["normalized_concept"] == "nodule"]
    print("=" * 72)
    print("1 · `nodule` VARLIKLARI")
    print("=" * 72)
    print(f"  toplam                : {len(nod):>8,} varlik / "
          f"{nod['study_id'].nunique():,} calisma")
    for a, n in nod["assertion"].value_counts().items():
        print(f"    assertion={a:<10} {n:>8,}  (%{n/len(nod)*100:5.1f})")

    pres = nod[nod["assertion"] == "present"]
    print(f"\n  present               : {len(pres):>8,} varlik / "
          f"{pres['study_id'].nunique():,} calisma")
    ipucusuz = pres[pres["assertion_rule"] == "varsayilan_present"]
    print(f"    ipucusuz (F2 adayi) : {len(ipucusuz):>8,}  "
          f"(%{len(ipucusuz)/max(len(pres),1)*100:5.1f})")

    rapor["nodule_varlik"] = {
        "toplam": int(len(nod)), "calisma": int(nod["study_id"].nunique()),
        "assertion_dagilimi": {str(a): int(n) for a, n in nod["assertion"].value_counts().items()},
        "present": int(len(pres)),
        "present_calisma": int(pres["study_id"].nunique()),
        "present_ipucusuz": int(len(ipucusuz)),
    }

    # --- 2 · sablon ve "nonspecific" ekseni ---
    print("\n" + "=" * 72)
    print("2 · SABLON ve `nonspecific` EKSENI  (present nodule uzerinde)")
    print("=" * 72)
    sablon = pres["is_stock_phrasing"].fillna(False).astype(bool)
    nonspec = pres["text"].str.contains(NONSPECIFIC, case=False, regex=True, na=False)
    millim = pres["text"].str.contains(MILLIMETRIC, case=False, regex=True, na=False)

    for ad, m in (("sablon cumlede", sablon), ("`nonspecific` iceren", nonspec),
                  ("`millimetric` iceren", millim),
                  ("sablon VEYA nonspecific", sablon | nonspec)):
        print(f"  {ad:26} {int(m.sum()):>8,}  (%{m.mean()*100:5.1f})")

    print("\n  ornek - sablon VE nonspecific:")
    for t in _ornekler(pres.loc[sablon & nonspec, "text"]):
        print(f"    · {t}")

    rapor["sablon_ekseni"] = {
        "present_sablon": int(sablon.sum()),
        "present_nonspecific": int(nonspec.sum()),
        "present_millimetric": int(millim.sum()),
        "present_sablon_veya_nonspecific": int((sablon | nonspec).sum()),
        "ornek_sablon_ve_nonspecific": _ornekler(pres.loc[sablon & nonspec, "text"]),
    }

    # --- 3 · niteleyici bagi (KADEMELENDIRME ICIN DEGIL, KARSITLIK ICIN) ---
    print("\n" + "=" * 72)
    print("3 · NITELEYICI BAGI  (`modify` iliskisiyle nodule'e bagli)")
    print("=" * 72)
    print("  ⚠ Bu sayilar bir kavramin gosterge niteligini DUSURMEK icin")
    print("    kullanilamaz (denetim B6). Yalniz sablon ekseninin ne kadar")
    print("    AYRISTIRICI oldugunu gostermek icin olculuyor.")
    # ⚠ ALET DENETIMI (D60) - ilk surumde YON TERS VARSAYILMISTI ve olcum
    # 20.259 varligin %100'unde "niteleyici yok" diyordu. Bu bir bulgu degil,
    # KIRIK BIR ALETTI. Olculdu (2026-09-07): `modify` iliskisinde
    # head = NITELEYICI (qualifier), tail = GOZLEM (observation).
    # Kanit: head/tail entity_type dagilimi qualifier->observation 66.760,
    # qualifier->anatomy 7.784; baska kombinasyon YOK. `nodule` HEAD olarak
    # 0, TAIL olarak 11.838 kez geciyor.
    r = pd.read_parquet(ILISKILER, columns=["study_id", "head_id", "tail_id", "relation_type"])
    r = r[(r["relation_type"] == "modify") & (r["study_id"].isin(gelistirme))]
    kavram = dict(zip(v["entity_id"], v["normalized_concept"]))
    r["head_kavram"] = r["head_id"].map(kavram)   # head = NITELEYICI

    supheli_ids = set(r.loc[r["head_kavram"].isin(SUPHELI_NITELEYICI), "tail_id"])
    benign_ids = set(r.loc[r["head_kavram"].isin(BENIGN_NITELEYICI), "tail_id"])
    s_bayrak = pres["entity_id"].isin(supheli_ids)
    b_bayrak = pres["entity_id"].isin(benign_ids)
    print(f"\n  supheli niteleyici bagli : {int(s_bayrak.sum()):>8,}  (%{s_bayrak.mean()*100:5.1f})")
    print(f"  benign  niteleyici bagli : {int(b_bayrak.sum()):>8,}  (%{b_bayrak.mean()*100:5.1f})")
    print(f"  hicbir niteleyici yok    : {int((~s_bayrak & ~b_bayrak).sum()):>8,}  "
          f"(%{(~s_bayrak & ~b_bayrak).mean()*100:5.1f})")

    # ⭐ Kritik capraz: sablon/nonspecific olan nodule'lerin kaci supheli?
    kalip = sablon | nonspec
    print(f"\n  ⭐ KALIP (sablon|nonspecific) icinde supheli niteleyici: "
          f"{int((kalip & s_bayrak).sum()):,} / {int(kalip.sum()):,} "
          f"(%{(s_bayrak[kalip].mean()*100 if kalip.any() else 0):.2f})")
    print(f"     KALIP DISINDA supheli niteleyici: "
          f"{int((~kalip & s_bayrak).sum()):,} / {int((~kalip).sum()):,} "
          f"(%{(s_bayrak[~kalip].mean()*100 if (~kalip).any() else 0):.2f})")

    rapor["niteleyici_bagi"] = {
        "supheli_bagli": int(s_bayrak.sum()), "benign_bagli": int(b_bayrak.sum()),
        "niteleyicisiz": int((~s_bayrak & ~b_bayrak).sum()),
        "kalip_icinde_supheli": int((kalip & s_bayrak).sum()),
        "kalip_toplam": int(kalip.sum()),
        "kalip_disinda_supheli": int((~kalip & s_bayrak).sum()),
        "kalip_disi_toplam": int((~kalip).sum()),
        "supheli_niteleyici_listesi": sorted(SUPHELI_NITELEYICI),
    }

    # --- 4 · DUYARLILIK MALIYETI: risk altindaki populasyon ---
    print("\n" + "=" * 72)
    print("4 · DUYARLILIK MALIYETI - risk altindaki populasyon")
    print("=" * 72)
    print("  Soru: bir kalip kurali yazilirsa KAC CALISMA etkilenebilir?")
    print("  Olculen: tek malignite kaniti KALIP nodule olan calismalar.")

    mal = v[v["normalized_concept"].isin(env.MALIGNITE_KAVRAMLARI)
            & v["assertion"].eq("present")]
    mal_calisma = set(mal["study_id"])
    # nodule DISI present malignite kavrami tasiyan calismalar
    baska_kanit = set(mal.loc[mal["normalized_concept"] != "nodule", "study_id"])
    # kalip nodule tasiyan calismalar
    kalip_calisma = set(pres.loc[kalip, "study_id"])
    # sadece-kalip-nodule: baska hicbir malignite kaniti yok
    yalniz_kalip = kalip_calisma - baska_kanit
    # kalip DISI nodule tasiyanlar bundan cikarilmali
    kalip_disi_nodule_calisma = set(pres.loc[~kalip, "study_id"])
    yalniz_kalip_saf = yalniz_kalip - kalip_disi_nodule_calisma

    print(f"\n  present malignite kavrami tasiyan calisma : {len(mal_calisma):>7,}")
    print(f"  nodule DISI kaniti da olan                : {len(baska_kanit):>7,}")
    print(f"  KALIP nodule tasiyan                      : {len(kalip_calisma):>7,}")
    print(f"  ⭐ TEK kaniti KALIP nodule olan (risk altindaki populasyon)"
          f"\n     = {len(yalniz_kalip_saf):,} calisma "
          f"(gelistirme havuzunun %{len(yalniz_kalip_saf)/len(gelistirme)*100:.2f}'i)")
    print("\n  ⚠ Bu bir UST SINIRDIR: bu calismalarin sinifi kuralla")
    print("    degisebilir, ama hepsi degismek ZORUNDA degil - F2 zaten")
    print("    bir kismini bastiriyor. Kesin sayi madde 13'te sema")
    print("    yeniden kosuldugunda olculecek.")

    rapor["duyarlilik_maliyeti"] = {
        "present_malignite_calisma": len(mal_calisma),
        "nodule_disi_kaniti_olan": len(baska_kanit),
        "kalip_nodule_calisma": len(kalip_calisma),
        "risk_altindaki_populasyon": len(yalniz_kalip_saf),
        "gelistirme_havuzu_orani_yuzde": round(len(yalniz_kalip_saf) / len(gelistirme) * 100, 3),
        "not": "UST SINIR - F2 zaten bir kismini bastiriyor; kesin sayi madde 13'te",
    }

    # --- 5 · kontrol takimi ---
    if KONTROL.exists():
        print("\n" + "=" * 72)
        print("5 · KONTROL TAKIMI  (docs/34 §4.3'un cikis noktasi)")
        print("=" * 72)
        # ⚠ ALET DENETIMI (D60) - ilk surumde CALISMA duzeyinde sayilmisti
        # ve 11/23 veriyordu; D77 ise 6/23 demisti. Sebep: bir kontrol
        # VAKASI bir CUMLEDIR (`cumle` kolonu), tum calisma degil. Ayni
        # calismanin BASKA cumlesindeki nodule vakaya YAZILAMAZ.
        kt = pd.read_csv(KONTROL)
        vaka_kayit = []
        for _, satir in kt.iterrows():
            vaka_metni = str(satir.get("cumle", "") or "")
            aday = pres[pres["study_id"] == satir["study_id"]]
            # bos aday -> apply() object dtype dondurur ve bool maske sayilmaz
            if aday.empty:
                icinde = aday
            else:
                maske = aday["text"].apply(
                    lambda s: bool(s) and s.strip() in vaka_metni).astype(bool)
                icinde = aday[maske]
            if icinde.empty:
                kalip_m = pd.Series([], dtype=bool)
            else:
                kalip_m = (icinde["is_stock_phrasing"].fillna(False).astype(bool)
                           | icinde["text"].str.contains(NONSPECIFIC, case=False, na=False))
            vaka_kayit.append({
                "vaka_id": satir["vaka_id"],
                "present_nodule": int(len(icinde)),
                "kalip_nodule": int(kalip_m.sum()),
                "ornek": icinde.loc[kalip_m, "text"].head(1).tolist(),
            })
        nod_vaka = [x for x in vaka_kayit if x["present_nodule"] > 0]
        kalip_vaka = [x for x in vaka_kayit if x["kalip_nodule"] > 0]
        print(f"  kontrol vakasi                       : {len(kt):>3}")
        print(f"  KENDI cumlesinde present nodule olan : {len(nod_vaka):>3}")
        print(f"  bunlarin KALIP (sablon|nonspecific)  : {len(kalip_vaka):>3}")
        print()
        print("  KALIP vakalar:")
        for x in kalip_vaka:
            ok = x["ornek"][0][:110] if x["ornek"] else ""
            print(f"    · {x['vaka_id']:26} {ok}")
        rapor["kontrol_takimi"] = {
            "vaka": int(len(kt)),
            "kendi_cumlesinde_present_nodule": len(nod_vaka),
            "kalip_vaka": len(kalip_vaka),
            "vaka_detay": vaka_kayit,
        }

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    print("\n⚠ BU BETIK KARAR VERMEZ. Kalip kurali yazilip yazilmayacagi")
    print("  bu sayilara ve kullanici onayina baglidir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
