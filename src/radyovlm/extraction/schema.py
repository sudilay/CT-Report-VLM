# -*- coding: utf-8 -*-
"""TASK-10: Cikarim semasinin yuklenmesi ve tablolarin semaya karsi dogrulanmasi.

Sema verisi `configs/extraction_schema.json` icindedir; bu modul onu okur ve
uretilen tablolari ona karsi denetler. Sema JSON'da, kural burada: JSON elle
duzenlenebilsin, mantik tek yerde dursun.

Faz 1'in disiplini surer: DOGRULAMA GECMEZSE YAZILMAZ. 04_segment_sentences.py
ofset dogrulamasi basarisiz olursa ciktiyi yazmayi reddediyordu; ayni davranis
burada `dogrula_veya_dur` ile saglanir.

Kullanim:
    from radyovlm.extraction import schema
    s = schema.yukle()
    ihlaller = schema.dogrula_entities(ent, sentences=sent, reports=rep)
    schema.dogrula_veya_dur(ihlaller)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SEMA_YOLU = ROOT / "configs" / "extraction_schema.json"


class SemaHatasi(RuntimeError):
    """Zorunlu bir dogrulama kurali saglanmadi."""


@dataclass
class Ihlal:
    kod: str
    kural: str
    sayi: int
    ornekler: list = field(default_factory=list)

    def __str__(self) -> str:
        o = "; ".join(str(x)[:110] for x in self.ornekler[:3])
        return f"[{self.kod}] {self.kural}: {self.sayi} ihlal" + (f" -> {o}" if o else "")


# ---------------------------------------------------------------- yukleme

def yukle(yol: Path | None = None) -> dict:
    with open(yol or SEMA_YOLU, encoding="utf-8") as f:
        return json.load(f)


def _kume_degerleri(sema: dict, yol: str) -> set:
    """'kontrollu_degerler.assertion' veya 'varlik_tipleri' gibi bir kume yolunu
    izin verilen degerler kumesine cevirir."""
    if yol == "varlik_tipleri":
        return set(sema["varlik_tipleri"])
    if yol == "iliski_tipleri":
        return set(sema["iliski_tipleri"])
    if yol == "baglama_kurallari":
        return set(sema["baglama_kurallari"]["degerler"])
    if yol == "niteleyici_gruplari":
        return {k for k in sema["niteleyici_gruplari"] if not k.startswith("_")}
    if yol.startswith("kontrollu_degerler."):
        return set(sema["kontrollu_degerler"][yol.split(".", 1)[1]]["degerler"])
    raise KeyError(f"bilinmeyen kume yolu: {yol}")


def izinli_degerler(sema: dict, tablo: str, kolon: str) -> set:
    """Bir kolonun kabul ettigi degerler. Testler ve cikarim kodu bunu kullanir."""
    tanim = sema["tablolar"][tablo]["kolonlar"][kolon]
    if "degerler" in tanim:
        return set(tanim["degerler"])
    if "kume" in tanim:
        return _kume_degerleri(sema, tanim["kume"])
    raise KeyError(f"{tablo}.{kolon} kontrollu deger tasimiyor")


def niteleyici_degerleri(sema: dict, grup: str) -> set:
    """Bir niteleyici grubunun ALINAN degerleri. 'olculup_alinmayan' DAHIL DEGILDIR -
    onlar korpusta olcup yetersiz bulundugumuz, bilerek disarida biraktiklarimizdir."""
    return set(sema["niteleyici_gruplari"][grup]["degerler"])


# ---------------------------------------------------------------- yardimci

def _eksik_kolonlar(df: pd.DataFrame, sema: dict, tablo: str) -> list[str]:
    return [k for k in sema["tablolar"][tablo]["kolonlar"] if k not in df.columns]


def _bos_kontrolu(df: pd.DataFrame, sema: dict, tablo: str) -> list[Ihlal]:
    out = []
    for kol, tanim in sema["tablolar"][tablo]["kolonlar"].items():
        if tanim.get("bos_olabilir", True) or kol not in df.columns:
            continue
        bos = df[kol].isna()
        if tanim["tip"] == "str":
            bos = bos | (df[kol].astype("string").fillna("").str.strip() == "")
        if bos.any():
            out.append(Ihlal("K3", f"{tablo}.{kol} bos birakilamaz",
                             int(bos.sum()), df.loc[bos, kol].head(3).tolist()))
    return out


def _kume_kontrolu(df: pd.DataFrame, sema: dict, tablo: str) -> list[Ihlal]:
    out = []
    for kol, tanim in sema["tablolar"][tablo]["kolonlar"].items():
        if kol not in df.columns or not ({"degerler", "kume"} & set(tanim)):
            continue
        izinli = izinli_degerler(sema, tablo, kol)
        gecerli = df[kol].isin(izinli)
        if None in izinli or tanim.get("bos_olabilir"):
            gecerli = gecerli | df[kol].isna()
        if not gecerli.all():
            kotu = df.loc[~gecerli, kol]
            out.append(Ihlal("K3c", f"{tablo}.{kol} tanimsiz deger",
                             int((~gecerli).sum()), sorted(set(kotu))[:3]))
    return out


def _tekillik(df: pd.DataFrame, sema: dict, tablo: str) -> list[Ihlal]:
    out = []
    for kol, tanim in sema["tablolar"][tablo]["kolonlar"].items():
        if tanim.get("tekil") and kol in df.columns:
            yin = df[kol].duplicated()
            if yin.any():
                out.append(Ihlal("K3b", f"{tablo}.{kol} tekil degil",
                                 int(yin.sum()), df.loc[yin, kol].head(3).tolist()))
    return out


# ---------------------------------------------------------------- entities

def dogrula_entities(ent: pd.DataFrame, sema: dict | None = None, *,
                     sentences: pd.DataFrame | None = None,
                     reports: pd.DataFrame | None = None) -> list[Ihlal]:
    """K1, K1b, K1c, K3, K3b, K3c, K3d."""
    sema = sema or yukle()
    ihl: list[Ihlal] = []

    eksik = _eksik_kolonlar(ent, sema, "entities")
    if eksik:
        return [Ihlal("K0", "entities kolonlari eksik", len(eksik), eksik)]
    if ent.empty:
        return ihl

    ihl += _bos_kontrolu(ent, sema, "entities")
    ihl += _kume_kontrolu(ent, sema, "entities")
    ihl += _tekillik(ent, sema, "entities")

    # K1b - ofset araligi
    kotu = ent.char_end <= ent.char_start
    if kotu.any():
        ihl.append(Ihlal("K1b", "char_end <= char_start", int(kotu.sum()),
                         ent.loc[kotu, "entity_id"].head(3).tolist()))

    # K1 - ofset ham metne birebir oturuyor mu
    if reports is not None:
        metin = dict(zip(reports.study_id, reports.report_text))
        kotu = [(r.entity_id, r.raw_text)
                for r in ent.itertuples(index=False)
                if metin.get(r.study_id, "")[r.char_start:r.char_end] != r.raw_text]
        if kotu:
            ihl.append(Ihlal("K1", "raw_text report_text ofsetine oturmuyor",
                             len(kotu), kotu[:3]))

    # K1c - varlik kaynak cumlenin icinde mi
    if sentences is not None:
        anahtar = ["study_id", "section", "sent_idx"]
        s = sentences.set_index(anahtar)[["char_start", "char_end"]]
        birlesik = ent.join(s, on=anahtar, rsuffix="_cumle")
        disari = ((birlesik.char_start < birlesik.char_start_cumle) |
                  (birlesik.char_end > birlesik.char_end_cumle) |
                  birlesik.char_start_cumle.isna())
        if disari.any():
            ihl.append(Ihlal("K1c", "varlik kaynak cumlenin disina tasiyor",
                             int(disari.sum()),
                             birlesik.loc[disari, "entity_id"].head(3).tolist()))

    # K3d - kural alani bos birakilamaz (D18)
    bos = ent.extraction_rule.astype("string").fillna("").str.strip() == ""
    if bos.any():
        ihl.append(Ihlal("K3d", "extraction_rule bos (D18)", int(bos.sum()), []))

    # K3e - niteleyici kavrami ait oldugu grubun DEGERLERI arasinda olmali.
    # sema-1.0'da yalnizca grup ADI denetleniyordu; kavramin o gruba ait olup
    # olmadigi denetlenmiyordu ve sema ile sozluk sessizce ayrisabiliyordu.
    nitel = ent[ent.entity_type == "qualifier"]
    if not nitel.empty:
        kotu = []
        for grup, alt in nitel.groupby("qualifier_group"):
            if grup not in sema["niteleyici_gruplari"]:
                continue
            izinli = set(sema["niteleyici_gruplari"][grup]["degerler"])
            disari = set(alt.normalized_concept) - izinli
            if disari:
                kotu += [f"{grup}:{d}" for d in sorted(disari)]
        if kotu:
            ihl.append(Ihlal("K3e", "niteleyici kavrami grubunun degerlerinde yok",
                             len(kotu), kotu[:3]))

    # K3f - varsayilan disi her kesinlik atamasinin bir IPUCU dayanagi olmali.
    # sema-1.2: TASK-12 'absent'/'uncertain' yazdiysa neye dayandigi kayitli olmali.
    if "assertion_cue" in ent.columns:
        gerekli = ent.assertion.isin(["absent", "uncertain"])
        bos = gerekli & (ent.assertion_cue.astype("string").fillna("").str.strip() == "")
        if bos.any():
            ihl.append(Ihlal("K3f", "assertion 'absent'/'uncertain' ama assertion_cue bos",
                             int(bos.sum()),
                             ent.loc[bos, "raw_text"].head(3).tolist()))

    # K3g - 'increased'/'decreased' ACIK zamansal referans ister (olculdu: increas*
    # 25.522 cumlede ama yalnizca %3,4'unde zamansal referans var).
    if "change_cue" in ent.columns:
        gerekli = ent.change_type.isin(["increased", "decreased"])
        bos = gerekli & (ent.change_cue.astype("string").fillna("").str.strip() == "")
        if bos.any():
            ihl.append(Ihlal("K3g", "change_type 'increased'/'decreased' ama change_cue bos",
                             int(bos.sum()),
                             ent.loc[bos, "raw_text"].head(3).tolist()))

    # K3 - surum zinciri tekil olmali (katman basina tek surum)
    for kol in ("segmentation_version", "template_version", "entity_version"):
        if ent[kol].nunique(dropna=False) > 1:
            ihl.append(Ihlal("K3", f"entities.{kol} birden fazla surum tasiyor",
                             int(ent[kol].nunique()), sorted(set(ent[kol]))[:3]))
    return ihl


# --------------------------------------------------------------- relations

def dogrula_relations(rel: pd.DataFrame, sema: dict | None = None, *,
                      entities: pd.DataFrame | None = None,
                      measurements: pd.DataFrame | None = None) -> list[Ihlal]:
    """K2, K2b, K2c, K3, K3b, K3c, K3d."""
    sema = sema or yukle()
    ihl: list[Ihlal] = []

    eksik = _eksik_kolonlar(rel, sema, "relations")
    if eksik:
        return [Ihlal("K0", "relations kolonlari eksik", len(eksik), eksik)]
    if rel.empty:
        return ihl

    ihl += _bos_kontrolu(rel, sema, "relations")
    ihl += _kume_kontrolu(rel, sema, "relations")
    ihl += _tekillik(rel, sema, "relations")

    ent_tip: dict[str, str] = {}
    ent_cal: dict[str, str] = {}
    if entities is not None and not entities.empty:
        ent_tip = dict(zip(entities.entity_id, entities.entity_type))
        ent_cal = dict(zip(entities.entity_id, entities.study_id))
    olcu_cal: dict[str, str] = {}
    if measurements is not None and not measurements.empty and \
            "measurement_id" in measurements.columns:
        olcu_cal = dict(zip(measurements.measurement_id, measurements.study_id))

    def _tip(kimlik: str, cins: str) -> str | None:
        return ent_tip.get(kimlik) if cins == "entity" else (
            "measurement" if kimlik in olcu_cal else None)

    def _calisma(kimlik: str, cins: str) -> str | None:
        return ent_cal.get(kimlik) if cins == "entity" else olcu_cal.get(kimlik)

    tanim = sema["iliski_tipleri"]
    yok, tip_uymaz, farkli_calisma = [], [], []

    for r in rel.itertuples(index=False):
        ht, tt = _tip(r.head_id, r.head_kind), _tip(r.tail_id, r.tail_kind)
        if ht is None or tt is None:
            yok.append((r.relation_id, r.head_id if ht is None else r.tail_id))
            continue
        t = tanim.get(r.relation_type)
        if t and (ht not in t["head"] or tt not in t["tail"]):
            tip_uymaz.append((r.relation_id, f"{r.relation_type}({ht}->{tt})"))
        hc, tc = _calisma(r.head_id, r.head_kind), _calisma(r.tail_id, r.tail_kind)
        if hc != tc or hc != r.study_id:
            farkli_calisma.append((r.relation_id, hc, tc, r.study_id))

    if yok:
        ihl.append(Ihlal("K2", "iliski ucu var olmayan kimlige isaret ediyor",
                         len(yok), yok[:3]))
    if tip_uymaz:
        ihl.append(Ihlal("K2b", "iliski tip uyumsuzlugu", len(tip_uymaz), tip_uymaz[:3]))
    if farkli_calisma:
        ihl.append(Ihlal("K2c", "iliski uclari ayni calismada degil",
                         len(farkli_calisma), farkli_calisma[:3]))

    # D18 - belirsiz bag sessizce kurulmaz
    bos = rel.attachment_rule.astype("string").fillna("").str.strip() == ""
    if bos.any():
        ihl.append(Ihlal("K3d", "attachment_rule bos (D18)", int(bos.sum()), []))
    return ihl


# ------------------------------------------------------------------- kapi

def dogrula_veya_dur(ihlaller: Iterable[Ihlal], baglam: str = "") -> None:
    """Zorunlu kurallardan biri bile ihlal edilmisse yazmaya izin verme.

    Faz 1'de ofset dogrulamasi icin ayni sey yapilmisti: sessizce bozuk veri
    uretmektense hic uretmemek yeglenir.
    """
    ihlaller = list(ihlaller)
    if not ihlaller:
        return
    bas = f"Sema dogrulamasi basarisiz{(' - ' + baglam) if baglam else ''}:"
    raise SemaHatasi(bas + "\n  " + "\n  ".join(str(i) for i in ihlaller))


def ozet(sema: dict | None = None) -> str:
    """Semanin insan okunur ozeti - inceleme icin."""
    sema = sema or yukle()
    sat = [f"sema surumu   : {sema['schema_version']}",
           f"varlik tipleri: {', '.join(sema['varlik_tipleri'])}",
           f"iliski tipleri: {', '.join(sema['iliski_tipleri'])}"]
    for grup, t in sema["niteleyici_gruplari"].items():
        if grup.startswith("_"):
            continue
        alinan = t["degerler"]
        atilan = t.get("olculup_alinmayan", {})
        sat.append(f"  {grup:<22} {len(alinan)} deger"
                   + (f"  ({len(atilan)} olculup alinmadi)" if atilan else ""))
    sat.append(f"dogrulama kurali: {len(sema['dogrulama_kurallari'])}")
    return "\n".join(sat)


if __name__ == "__main__":
    print(ozet())
