"""Turkce kavram yuzeylerini tek birlesik regex ile eslestirir (D61)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from radyovlm.extraction.entities import (
    _yakalayan_grup_var_mi,
    azami_eslesme_uzunlugu,
)

ROOT = Path(__file__).resolve().parents[3]
VARSAYILAN_SOZLUK = ROOT / "configs" / "turkce_yuzeyler_taslak.yaml"


def turkce_sozlugu_yukle(yol: Path = VARSAYILAN_SOZLUK) -> dict[str, str]:
    """Turkce yuzey YAML'ini ``{kavram: desen}`` olarak yukle."""
    veri = yaml.safe_load(yol.read_text(encoding="utf-8"))
    return {kavram: kayit["desen"] for kavram, kayit in veri["yuzeyler"].items()}


def tr_matcher_kur(yuzeyler: dict[str, str]) -> tuple[re.Pattern, dict[str, str]]:
    """Turkce kavramlari EN matcher ile ayni mimaride derle.

    Tek dil farki sag kelime siniridir: Turkce sondan eklemeli oldugu icin
    ``nod[uü]l`` deseni ``nodulde`` ve ``noduler`` bicimlerini de yakalar.
    Soldaki sinir, ``ektazi`` deseninin ``atelektazi`` icine dusmesini onler.
    """
    adaylar: list[tuple[int, str, str]] = []
    for kavram, desen in yuzeyler.items():
        # entities._yakalayan_grup_var_mi yalniz sozluk desenleri icin yazildi;
        # kacirilmis ham parantezi de grup sanir. Once \( / \) literallerini
        # ayir, kalan gercek yakalayan gruplari ayni ortak denetimle reddet.
        grup_kontrolu = re.sub(r"\\[()]", "", desen)
        if _yakalayan_grup_var_mi(grup_kontrolu):
            raise ValueError(f"{kavram}: desen yakalayan grup iceriyor -> {desen}")
        adaylar.append((azami_eslesme_uzunlugu(desen), desen, kavram))

    adaylar.sort(key=lambda x: (-x[0], -len(x[1])))
    parcalar, indeks = [], {}
    for i, (_, desen, kavram) in enumerate(adaylar):
        grup = f"m{i}"
        parcalar.append(f"(?P<{grup}>{desen})")
        indeks[grup] = kavram

    # scripts/23.derle ile ayni gelecek korumasi: ham parantez deseni eklenirse
    # sol kelime siniri onu sessizce erisilmez yapmasin. Bugun boyle desen yok.
    if any(desen.startswith(r"\(") for _, desen, _ in adaylar):
        parcalar = [
            parca if desen.startswith(r"\(") else r"\b" + parca
            for parca, (_, desen, _) in zip(parcalar, adaylar)
        ]
        return re.compile(r"(?:" + "|".join(parcalar) + r")", re.I), indeks

    return re.compile(r"\b(?:" + "|".join(parcalar) + r")", re.I), indeks


def kavramlari_bul(
    metin: str, matcher: re.Pattern, indeks: dict[str, str]
) -> set[str]:
    """Birlesik matcher eslesmelerini belge duzeyi kavram kumesine indir."""
    return {indeks[m.lastgroup] for m in matcher.finditer(metin)}
