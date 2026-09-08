"""SUDE-VLM-14 · Astra seri duzeyi toplama ve kolon sozlesmesi.

Sozlesme: `docs/38_vlm14_calisma_plani.md` §4 (iki tablo).
Adaptor : `src/radyovlm/extraction/astra.py` (`astra-sozlesme-1.0`).
Sema    : `sema-1.0` (Faz A'da donduruldu).

BAGLAYICI KISITLAR
  * Surekli olasilik URETILMEZ - o VLM-20'nin lojistik regresyonudur.
  * `boyut_mm` YALNIZ L1'den (ayni cumlede `measured_by`) alinir.
  * `boyut_mm` teknik parametre satirindan ASLA alinmaz.
  * Akciger disi organ bolumleri kapsam DISIDIR; elenen malignite kaniti
    `qf_ekstratorasik_malignite_elendi` ile SAYILIR - sessiz kayip yok.
"""
from __future__ import annotations

import re

import pandas as pd

from radyovlm.evaluation import sema
from radyovlm.extraction import astra as A

VLM14_SURUMU = "astra-adaptor-1.2"

# 1.1 -> 1.2 · yeniden denetimin bulgulari (R1, R3, R5):
#   * `iliskiler=None` sessizce bos iliski sayilmiyor; ValueError
#   * Anatomi filtresi DARALTILDI - tek `located_at` bagina dayanip acik
#     toraks kanitini (`pulmonary nodules`) eleyemez
#   * Kilit hangi evreni (degerlendirmeye dahil / tum train) kullandigini ilan
#     eder; uretim girisi ayni evreni kullanir
#
# 1.0 -> 1.1 · bagimsiz sozlesme uyum denetiminin bulgulari (K1, K5.1-K5.3):
#   * Eksik zenginlestirme alaninda sessiz `False` yerine HATA verilir
#   * Teknik olcu tanimi TEKILLESTIRILDI (`astra.olcu_teknik_mi`)
#   * Ozet bolumlerinde ekstratorasik kanit ANATOMI duzeyinde elenir
#   * `qf_mediastinum_kaynakli` uretilir (sozlesmede vaat edilmisti)
#   * `measurement_available` sessiz varsayilani kaldirildi

# D4: sablon esigi = K farkli TRAIN hastasi. Sablon istatistigi YALNIZ
# train'den hesaplanir (AGENTS §4 baglayici kural: valid'den on islemeye
# sizinti olmaz).
SABLON_ESIGI = 10

LOB_DESENI = re.compile(
    r"\b(right|left)\s+(upper|middle|lower)\s+lobe"
    r"|\b(upper|middle|lower)\s+lobe\s+of\s+the\s+(right|left)", re.I)

LOB_KODU = {
    ("right", "upper"): "RUL", ("right", "middle"): "RML",
    ("right", "lower"): "RLL", ("left", "upper"): "LUL",
    ("left", "lower"): "LLL", ("left", "middle"): "LUL",  # lingula -> LUL
}

NODUL_KAVRAMLARI = frozenset({
    "nodule", "nodular_lesion", "mass", "space_occupying_lesion",
})

BENIGN_KAVRAMLARI = frozenset(sema.BENIGN_KAVRAMLARI) | {
    "calcification", "calcified", "fibrosis",
}

TIP_DESENI = re.compile(r"\bsolid\b|part.?solid|subsolid|ground.?glass|\bGGN\b",
                        re.I)

# Kesin olarak akciger disi organlar (`anat-1.1` kavramlari).
# Bu kume bolum duzeyi kapsam listesinden DAR tutulmustur: yalniz POZITIF
# tanimlanmis batin/boyun/meme organlari. Gerekce - karisik organli cumlede
# TORAKS kanitini korumak. Kemik yapilar BILEREK disarida: sinir takimi
# C5-03 ("metastatic masses in T1 and L1 vertebrae") hedefi
# `known_malignancy`dir, yani sema onlari sayar.
EKSTRATORASIK_ANATOMI = frozenset({
    "abdomen", "adrenal_gland", "breast", "esophagus", "gallbladder",
    "kidney", "liver", "pancreas", "spleen", "thyroid",
})

# Kesin torasik anatomi. Ayni cumlede hem bu kumeden hem EKSTRATORASIK'ten
# varlik varsa tekil `located_at` bagi GUVENILMEZDIR (R3).
TORASIK_ANATOMI = frozenset({
    "lung", "lung_parenchyma", "lung_apex", "pleura", "pleuroparenchymal",
    "bronchus", "trachea", "airway", "mediastinum", "hilum", "fissure",
    "upper_lobe", "middle_lobe", "lower_lobe", "lingula", "hemithorax",
    "pulmonary_artery", "pulmonary_conus", "anatomic_segment",
})

# Varligin KENDI span'inda torasik isaret. `pulmonary nodules` en yakin
# anatomi olarak `liver`a baglansa bile elenmemelidir (R3, iki gercek vaka).
TORAKS_ISARETI = re.compile(
    r"pulmonar|lung|pleural|bronch|thorac|mediastin|lobe\b", re.I)

# `pulmonary nodules` varliginin `raw_text`i yalniz "nodules"tur - "pulmonary"
# span DISINDA kalir. Bu yuzden span oncesindeki kisa pencere de taranir
# (R3, gercek vaka: "biopsy of the liver lesions and pulmonary nodules").
TORAKS_ONEK_PENCERESI = 25


def _iliski_zorunlu(iliskiler, cagiran: str) -> None:
    """R1: `None` sessizce bos iliski sayilamaz.

    `None` verildiginde supheli niteleyicilerin tamami False, anatomik eleme
    kumesi bos ve butun olculer eksik kabul edilirdi - hata vermeden, uc
    girdiyi ayni anda susturarak.
    """
    if iliskiler is None:
        raise ValueError(
            f"{cagiran}: `iliskiler` None olamaz. Iliski katmani uretilmeden "
            "cagrilirsa uc girdi (supheli_niteleyici, boyut_mm, anatomi "
            "elemesi) sessizce susar.")


def _norm(metin: str) -> str:
    return re.sub(r"\s+", " ", metin.strip().lower())


def sablon_kolonu_ekle(cumleler: pd.DataFrame) -> pd.DataFrame:
    """`sablon_cumle` kolonunu ekler - istatistik YALNIZ train'den (D4).

    Sema `sablon_cumle` bekler. Hesaplanmazsa C#nodul-kalip kurali SESSIZCE
    OLU KALIR; bu nedenle False birakmak yerine hesaplanir.
    """
    c = cumleler.copy()
    c["_norm"] = c["cumle_metni"].map(_norm)
    tr = c[c["split"].eq("train")]
    hasta_sayisi = tr.groupby("_norm")["pid"].nunique()
    sablonlar = set(hasta_sayisi[hasta_sayisi >= SABLON_ESIGI].index)
    c["sablon_cumle"] = c["_norm"].isin(sablonlar)
    c["n_patients_train"] = c["_norm"].map(hasta_sayisi).fillna(0).astype(int)
    return c.drop(columns=["_norm"])


def lob_coz(metin: str) -> str | None:
    m = LOB_DESENI.search(metin)
    if not m:
        return None
    g = [x.lower() for x in m.groups() if x]
    taraf = next((x for x in g if x in ("right", "left")), None)
    seviye = next((x for x in g if x in ("upper", "middle", "lower")), None)
    return LOB_KODU.get((taraf, seviye)) if taraf and seviye else None


def supheli_niteleyici_ekle(varliklar: pd.DataFrame,
                            iliskiler: pd.DataFrame) -> pd.DataFrame:
    """`supheli_niteleyici` kolonunu `modify` iliskilerinden uretir.

    ⚠ `modify` YONU: head = NITELEYICI, tail = GOZLEM (D80 alet hatasi).
    Bu kolon hesaplanmazsa C#nodul-kalip kuralinin bir dali SESSIZCE OLU
    KALIR; `False` sabitlemek yerine uretilir.
    """
    _iliski_zorunlu(iliskiler, "supheli_niteleyici_ekle")
    v = varliklar.copy()
    if len(iliskiler) == 0:
        v["supheli_niteleyici"] = False
        return v
    kavram = dict(zip(v["entity_id"], v["normalized_concept"]))
    mod = iliskiler[iliskiler["relation_type"].eq("modify")]
    supheli_head = mod["head_id"].map(kavram).isin(sema.NODUL_SUPHELI_NITELEYICI)
    hedefler = set(mod.loc[supheli_head, "tail_id"])
    v["supheli_niteleyici"] = v["entity_id"].isin(hedefler)
    return v


def boyut_ekle(kanit: pd.DataFrame, iliskiler: pd.DataFrame) -> pd.DataFrame:
    """`boyut_mm` — YALNIZ L1 (`measured_by`, ayni cumle) kaynagindan.

    Teknik parametre satirlarindaki olculer iliski katmanina HIC girmez
    (scripts/61, `teknik_mi` ile dislanir), dolayisiyla buraya sizamaz.
    """
    _iliski_zorunlu(iliskiler, "boyut_ekle")
    b = kanit.copy()
    if len(iliskiler) == 0:
        return b
    mb = iliskiler[iliskiler["relation_type"].eq("measured_by")]
    olcu = dict(zip(mb["head_id"], mb["tail_metin"]))

    def _mm(ham: str | None) -> float | None:
        if not ham:
            return None
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(mm|cm)", str(ham), re.I)
        if not m:
            return None
        d = float(m.group(1).replace(",", "."))
        return round(d * 10, 2) if m.group(2).lower() == "cm" else d

    b["boyut_mm"] = b["varlik_id"].map(olcu).map(_mm)
    b["boyut_bag_duzeyi"] = b["boyut_mm"].notna().map({True: "L1", False: "yok"})
    return b


ZORUNLU_ZENGINLESTIRME = ("sablon_cumle", "supheli_niteleyici")


def _sema_girdisi(varliklar: pd.DataFrame) -> pd.DataFrame:
    """Astra varlik tablosunu semanin girdi sozlesmesine cevirir.

    Denetim bulgusu K1: eksik zenginlestirme alani SESSIZCE `False`
    atanmamalidir. Alan yoklugunu normal deger saymak bu projede IKI KEZ
    kural dalinin sessizce olmesine yol acti. Artik hata verilir.
    """
    eksik = [k for k in ZORUNLU_ZENGINLESTIRME if k not in varliklar.columns]
    if eksik:
        raise ValueError(
            f"zenginlestirme alani eksik: {eksik}. `sablon_kolonu_ekle` ve "
            "`supheli_niteleyici_ekle` seri_ozeti'nden ONCE cagrilmalidir; "
            "eksik alan sessizce False sayilmaz.")
    return varliklar.rename(columns={"bolum_ham": "section",
                                     "cumle_idx": "sent_idx",
                                     "seri_anahtari": "study_id"}).copy()


def ekstratorasik_varliklar(varliklar: pd.DataFrame,
                            iliskiler: pd.DataFrame) -> set:
    """`located_at` ile akciger disi organa baglanan gozlem kimlikleri.

    Denetim bulgusu K5.2: bolum duzeyi kapsam TEK BASINA YETMEZ. Ozet
    bolumleri kapsam icindedir ve icinde karaciger metastazi gecebilir. Eleme
    ANATOMI duzeyinde yapilir ki ayni cumledeki TORAKS kaniti korunsun.

    Yon: `located_at` head = gozlem, tail = anatomi (entities.py:368).
    """
    _iliski_zorunlu(iliskiler, "ekstratorasik_varliklar")
    if len(iliskiler) == 0:
        return set()

    kavram = dict(zip(varliklar["entity_id"], varliklar["normalized_concept"]))
    ham_metin = dict(zip(varliklar["entity_id"], varliklar["raw_text"]))

    la = iliskiler[iliskiler["relation_type"].eq("located_at")]
    aday = set(la.loc[la["tail_id"].map(kavram).isin(EKSTRATORASIK_ANATOMI),
                      "head_id"])
    if not aday:
        return set()

    # --- KORUMA 1: varligin span'i VEYA onundeki pencere torasik isaret
    #     tasiyorsa elenmez. Yalniz `raw_text` yetmez (bkz. TORAKS_ISARETI). ---
    bas = dict(zip(varliklar["entity_id"], varliklar["char_start"]))
    son = dict(zip(varliklar["entity_id"], varliklar["char_end"]))
    cumle_m = dict(zip(varliklar["entity_id"], varliklar["cumle_metni"]))

    def _toraks_isaretli(eid: str) -> bool:
        if TORAKS_ISARETI.search(str(ham_metin.get(eid, ""))):
            return True
        t = str(cumle_m.get(eid, ""))
        b = int(bas.get(eid, 0)), int(son.get(eid, 0))
        return bool(TORAKS_ISARETI.search(
            t[max(0, b[0] - TORAKS_ONEK_PENCERESI): b[1]]))

    aday = {e for e in aday if not _toraks_isaretli(e)}

    # --- KORUMA 2: cumlede hem torasik hem ekstratorasik anatomi varsa
    #     tekil `located_at` bagi guvenilmez; eleme yapilmaz ---
    anahtar = ["seri_anahtari", "bolum_ham", "cumle_idx"]
    v = varliklar.set_index("entity_id")
    kar = varliklar.assign(
        _tor=varliklar["normalized_concept"].isin(TORASIK_ANATOMI),
        _eks=varliklar["normalized_concept"].isin(EKSTRATORASIK_ANATOMI))
    cumle = kar.groupby(anahtar)[["_tor", "_eks"]].any()
    belirsiz = set(cumle.index[cumle["_tor"] & cumle["_eks"]])

    def _belirsiz_mi(eid: str) -> bool:
        try:
            r = v.loc[eid]
        except KeyError:
            return False
        return (r["seri_anahtari"], r["bolum_ham"], r["cumle_idx"]) in belirsiz

    return {e for e in aday if not _belirsiz_mi(e)}


def seri_ozeti(varliklar: pd.DataFrame, cumleler: pd.DataFrame,
               boyutlu_seriler: set, iliskiler: pd.DataFrame) -> pd.DataFrame:
    """A tablosu - seri duzeyi ozet.

    `boyutlu_seriler` ve `iliskiler` ZORUNLUDUR (denetim bulgusu K1/K5.5):
    sessiz varsayilan `measurement_available`i her seride False yapiyordu.
    """
    boyutlu = boyutlu_seriler
    v = _sema_girdisi(varliklar)

    # K5.2 - anatomi duzeyi eleme, kapsam ici bolumlerde de uygulanir.
    ekst = ekstratorasik_varliklar(varliklar, iliskiler)
    v["_ekstratorasik"] = v["entity_id"].isin(ekst)

    kapsam = v[v["kapsam_ici"] & ~v["_ekstratorasik"]]
    disi = v[(~v["kapsam_ici"]) | v["_ekstratorasik"]]

    mal_disi = disi[disi["normalized_concept"].isin(sema.MALIGNITE_KAVRAMLARI)
                    & disi["assertion"].eq("present")]

    # K5.2 - bayrak AYRISTIRILDI: organ kaynakli eleme ile bilinmeyen/meta
    # bolum kaybi ayni bayrakta toplaniyordu.
    ekst_seri = set(mal_disi.loc[
        mal_disi["bolum_eslenmis"].eq("dis_organ")
        | mal_disi["_ekstratorasik"], "study_id"])
    bilinmeyen_seri = set(mal_disi.loc[
        mal_disi["bolum_eslenmis"].isin({"bilinmeyen", "meta"}), "study_id"])

    # K5.3 - mediastinum katkisi ayristirilabilsin (sozlesmede vaat edildi).
    med_seri = set(kapsam.loc[kapsam["bolum_eslenmis"].eq("mediasten")
                              & kapsam["assertion"].eq("present"), "study_id"])
    elenen_seri = ekst_seri

    satirlar = []
    for sid, g in kapsam.groupby("study_id", sort=False):
        g = g.reset_index(drop=True)
        bulgular = sema.bulgulari_hesapla(g) if not g.empty else []
        sonuc = sema.rapora_topla(sid, bulgular)

        nod = g[g["normalized_concept"].isin(NODUL_KAVRAMLARI)]
        nod_present = nod[nod["assertion"].eq("present")]
        nod_absent = nod[nod["assertion"].eq("absent")]
        if len(nod_present):
            nodul = "true"
        elif len(nod_absent):
            nodul = "false"
        else:
            nodul = "not_assessable"

        loblar = sorted({lob for lob in
                         (lob_coz(t) for t in g["cumle_metni"].unique())
                         if lob})
        benign = bool(len(g[g["normalized_concept"].isin(BENIGN_KAVRAMLARI)
                            & g["assertion"].eq("present")]))
        tip_var = bool(any(TIP_DESENI.search(t) for t in
                           g["cumle_metni"].unique()))

        satirlar.append({
            "seri_anahtari": sid,
            "nodul_var_mi": nodul,
            "loblar": loblar,
            "report_derived_malignancy_label": sonuc.olcek_duzeyi,
            "belirleyici_kaynak": sonuc.belirleyici_kaynak,
            "benign_evidence_present": benign,
            "evidence_count": int(len(g)),
            "nodule_type_available": tip_var,
            "measurement_available": sid in boyutlu,
            "qf_ekstratorasik_malignite_elendi": sid in elenen_seri,
            "qf_bilinmeyen_bolum_malignite": sid in bilinmeyen_seri,
            "qf_mediastinum_kaynakli": sid in med_seri,
        })

    a = pd.DataFrame(satirlar)

    # Seri meta bilgisi cumle tablosundan (etiket DEGIL)
    meta = (cumleler.groupby("seri_anahtari")
            .agg(pid=("pid", "first"),
                 split=("split", "first"),
                 included_in_evaluation=("included_in_evaluation", "first"),
                 qf_placeholder=("has_placeholder", "any"))
            .reset_index())
    a = meta.merge(a, on="seri_anahtari", how="left")
    a["nodul_var_mi"] = a["nodul_var_mi"].fillna("not_assessable")
    # Kapsam ici bolumu olmayan seride `loblar` NaN kalir - bos liste olmali.
    a["loblar"] = a["loblar"].map(lambda x: x if isinstance(x, list) else [])
    a["report_derived_malignancy_label"] = (
        a["report_derived_malignancy_label"].fillna("not_mentioned"))
    for kol, vars_ in (("benign_evidence_present", False),
                       ("measurement_available", False),
                       ("nodule_type_available", False),
                       ("qf_ekstratorasik_malignite_elendi", False),
                       ("qf_bilinmeyen_bolum_malignite", False),
                       ("qf_mediastinum_kaynakli", False)):
        a[kol] = a[kol].fillna(vars_).astype(bool)
    a["evidence_count"] = a["evidence_count"].fillna(0).astype(int)

    # Kapsam ici bolumu hic olmayan seriler
    kapsamli = set(kapsam["study_id"])
    a["qf_bolum_eksik"] = ~a["seri_anahtari"].isin(kapsamli)

    a["sema_surumu"] = sema.SEMA_SURUMU
    a["adaptor_surumu"] = VLM14_SURUMU
    a["sozlesme_surumu"] = A.SOZLESME_SURUMU
    return a


def kanit_tablosu(varliklar: pd.DataFrame) -> pd.DataFrame:
    """B tablosu - kanit duzeyi uzun tablo."""
    b = varliklar.copy()
    b["lob"] = b["cumle_metni"].map(lob_coz)
    b["kanit_id"] = [f"kanit-{i:08d}" for i in range(len(b))]
    b["boyut_bag_duzeyi"] = "yok"
    b["boyut_mm"] = pd.NA
    return b[[
        "kanit_id", "seri_anahtari", "bolum_ham", "bolum_eslenmis",
        "kapsam_ici", "cumle_idx", "entity_id", "normalized_concept",
        "assertion", "assertion_rule", "temporality", "lob",
        "boyut_mm", "boyut_bag_duzeyi", "cumle_metni",
    ]].rename(columns={"bolum_ham": "kaynak_bolum", "entity_id": "varlik_id",
                       "cumle_metni": "kanit_metni"})
