# -*- coding: utf-8 -*-
"""TASK-12: Negasyon, belirsizlik ve zamansallik cozumlemesi.

D15 geregi DETERMINISTIK. Her atama, onu ureten IPUCU ve KURAL ile birlikte
kaydedilir (`assertion_cue`/`assertion_rule`/`temporality_*`/`change_*`) - bir
hata bulundugunda hangi kuralin urettigi gorulebilsin diye.

Sozluk: configs/ipucu_sozlugu.yaml  (korpustan turetildi, D16)

KAPSAM HESABI - ipucu duzeyinde, CUMLE duzeyinde DEGIL:
  Her ipucunun bir kapsami vardir; bir varlik yalnizca kendisini KAPSAYAN
  ipuclarindan etkilenir. Ayni cumlede birden cok ipucu olabilir ve farkli
  varliklar farkli sonuc alabilir.

    ileri : ipucunun sonundan, bir sonlandiriciya veya cumle sonuna kadar
    geri  : ipucunun basindan geriye, bir sonlandiriciya veya cumle basina kadar
    cift  : iki yon

KARAR ONCELIGI (bolum 6, plan):
  1. cannot be excluded ailesi kapsiyorsa -> uncertain
  2. negasyon ipucu kapsiyorsa            -> absent
  3. belirsizlik ipucu kapsiyorsa         -> uncertain
  4. cikarim ifadesi kapsiyorsa           -> present (ipucu kaydedilir)
  4. hicbiri                              -> present

  Teknik cekince bu listede YOKTUR: hicbir varliga 'absent' yazdirmaz, yalnizca
  negasyon tetikleyicisi olarak SAYILMAZ. Cumleyi susturmaz - olculdu, teknik
  cekince isaretli cumlelerin %42'sinde bagimsiz gercek negasyon var.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SOZLUK = ROOT / "configs" / "ipucu_sozlugu.yaml"

CONTEXT_VERSION = "ctx-1.1"

# 'increase' gibi ifadeler icin ACIK zamansal referans sarti (plan 4.11).
# Olculdu: increas* 25.522 cumlede ama yalnizca %3,4'unde zamansal referans var.
# Konum edati: ardindaki anatomi BAKILAN YERDIR, olumsuzlanan sey degil.
KONUM_EDATI_ONCE = re.compile(r"\b(?:in|within|at|on|into|inside)\b", re.I)

ZAMANSAL_REFERANS = re.compile(
    r"\bprevious(?:ly)?\b|\bprior\b|\bformer\b|\bcontrol\b|follow-?up|"
    r"compared (?:to|with)|current examination|old (?:CT|examination)|"
    r"\bnewly\b|in comparison", re.I)


@dataclass
class Ipucu:
    ad: str
    bolum: str
    desen: re.Pattern
    yon: str
    sonuc: str | None = None
    zamansal_referans_gerekir: bool = False


@dataclass
class Bulunan:
    ipucu: Ipucu
    bas: int
    son: int
    metin: str
    kapsam_bas: int
    kapsam_son: int

    def kapsiyor(self, b: int, s: int) -> bool:
        return self.kapsam_bas <= b and s <= self.kapsam_son


# ------------------------------------------------------------------ yukleme

def yukle(yol: Path | None = None) -> dict:
    with open(yol or SOZLUK, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ipuclarini_kur(sz: dict | None = None) -> tuple[list[Ipucu], re.Pattern]:
    sz = sz or yukle()
    out: list[Ipucu] = []
    for bolum, girdiler in sz.items():
        if not isinstance(girdiler, dict) or bolum.endswith("_olculup_alinmayan"):
            continue
        for ad, t in girdiler.items():
            if not isinstance(t, dict) or "desenler" not in t:
                continue
            pat = "|".join(f"(?:{p})" for p in t["desenler"])
            out.append(Ipucu(
                ad=ad, bolum=bolum, desen=re.compile(pat, re.I),
                yon=t.get("yon", "ileri"), sonuc=t.get("sonuc"),
                zamansal_referans_gerekir=bool(t.get("zamansal_referans_gerekir"))))
    sonl = sz["sonlandirici"]
    pat = "|".join(f"(?:{p})" for g in sonl.values() for p in g["desenler"])
    return out, re.compile(pat, re.I)


# ------------------------------------------------------------------- kapsam

def _kapsam(metin: str, bas: int, son: int, yon: str,
            sonlandirici: re.Pattern) -> tuple[int, int]:
    """Ipucunun kapsami - sonlandiriciya veya cumle sinirina kadar."""
    if yon == "yapisik":
        return bas, son
    sol, sag = 0, len(metin)
    if yon in ("ileri", "cift"):
        m = sonlandirici.search(metin, son)
        sag = m.start() if m else len(metin)
    else:
        sag = son
    if yon in ("geri", "cift"):
        sol = 0
        for m in sonlandirici.finditer(metin[:bas]):
            sol = m.end()
    else:
        sol = bas
    return sol, sag


def ipuclari_bul(metin: str, ipuclari: list[Ipucu],
                 sonlandirici: re.Pattern) -> list[Bulunan]:
    out = []
    for ip in ipuclari:
        for m in ip.desen.finditer(metin):
            kb, ks = _kapsam(metin, m.start(), m.end(), ip.yon, sonlandirici)
            out.append(Bulunan(ip, m.start(), m.end(), m.group(0), kb, ks))
    return out


def _ortusen(a: Bulunan, b: Bulunan) -> bool:
    return a.bas < b.son and b.bas < a.son


def _tip(v: dict) -> str:
    """Varlik tipini esnek okur - sozluk nesnesi veya duz alan."""
    if "tip" in v:
        return v["tip"]
    k = v.get("kavram")
    return getattr(k, "tip", "") if k is not None else ""


def _anatomi_korunur(metin: str, kapsam: "Bulunan", v: dict,
                     varliklar: list[dict]) -> bool:
    """Bu ANATOMI varligi olumsuzlamadan/belirsizlikten KORUNMALI mi?

    PILOT BULGUSU (2026-08-28): negasyon anatomiye siciriyordu.
      "No mass was detected in both LUNGS." -> akcigerler DURUYOR; yok olan KITLE.
    Olculdu: 177.922 anatomi 'absent', 24.416 'uncertain' - tum varliklarin %17,1'i.
    RadGraph tasariminda da ANAT-DP ayri etikettir; olumsuz cumledeki anatomi yine
    DP'dir. ANAT-DA yalnizca anatominin GERCEKTEN yok oldugu durumdur
    ("The right breast was not observed secondary to the operation").

    Iki korunma kosulu (biri yeterse korunur):
      1. Kapsamda bir GOZLEM/niteleyici de var -> olumsuzlanan odur, anatomi degil
         "Pleural effusion-thickening was not detected" -> plevra DURUYOR
      2. Anatomi bir KONUM EDATININ ardinda -> bakilan yerdir
         "no lymph nodes are observed IN THE mediastinum" -> mediasten DURUYOR

    Ikisi de yoksa anatomi olumsuzlanabilir - gercekten yok olma durumu.
    """
    if _tip(v) != "anatomy":
        return False
    # 1. kapsamda gozlem/niteleyici/cihaz var mi
    for x in varliklar:
        if _tip(x) in ("observation", "qualifier", "device") and                 kapsam.kapsiyor(x["bas"], x["son"]):
            return True
    # 2. kapsam basindan varliga kadar konum edati var mi
    onceki = metin[max(kapsam.kapsam_bas, 0):v["bas"]]
    return bool(KONUM_EDATI_ONCE.search(onceki))


def _teknik_kapsaminda(b: Bulunan, teknikler: list[Bulunan]) -> bool:
    """Bir negasyon ipucu bir teknik cekince ifadesinin ICINDE mi.

    'could not be evaluated' icindeki 'not' bagimsiz bir negasyon degildir.
    AMA ayni cumledeki BASKA bir 'no ...' etkilenmez - cumle susturulmaz.
    """
    return any(t.bas <= b.bas and b.son <= t.son for t in teknikler)


# ------------------------------------------------------------------- karar

def kesinlik_ata(metin: str, varliklar: list[dict], ipuclari: list[Ipucu],
                 sonlandirici: re.Pattern) -> list[dict]:
    """Her varliga assertion + ureten ipucu/kural. Varliklar {'bas','son'} tasir."""
    bulunan = ipuclari_bul(metin, ipuclari, sonlandirici)
    teknik = [b for b in bulunan if b.ipucu.bolum == "teknik_cekince"]
    sahte = [b for b in bulunan if b.ipucu.bolum == "sahte_negasyon"]

    oncelikli = [b for b in bulunan if b.ipucu.bolum == "belirsizlik_oncelikli"]
    negasyon = [b for b in bulunan
                if b.ipucu.bolum == "negasyon"
                and not _teknik_kapsaminda(b, teknik)
                and not any(_ortusen(b, s) for s in sahte)
                and not any(_ortusen(b, o) for o in oncelikli)]
    belirsiz = [b for b in bulunan if b.ipucu.bolum == "belirsizlik"]
    # CIKARIM IFADESI (ctx-1.1): 'ile uyumlu', 'lehine', 'supheli', 'olasilikla'
    # ALAN SOZLUGU BELGESI §12.2 bunlari PRESENT sayar - bulgu vardir, yalnizca
    # dayanagi cikarimdir. ctx-1.0'da belirsizlik altindaydilar ve 20.587 varligi
    # yanlislikla uncertain yapiyorlardi. Ipucu kaydedilir, sonuc present kalir.
    cikarim = [b for b in bulunan if b.ipucu.bolum == "cikarim_ifadesi"]

    out = []
    for v in varliklar:
        b, s = v["bas"], v["son"]
        kaynak, kural, sonuc = None, "varsayilan", "present"

        for k in oncelikli:
            if k.kapsiyor(b, s):
                kaynak, kural, sonuc = k, "belirsizlik_oncelikli", "uncertain"
                break
        if kaynak is None:
            for k in negasyon:
                if k.ipucu.yon == "yapisik":
                    # onek yalnizca YAPISIK oldugu varliga uygulanir (plan 4.2)
                    if k.son != b:
                        continue
                elif not k.kapsiyor(b, s):
                    continue
                if _anatomi_korunur(metin, k, v, varliklar):
                    continue          # anatomi bakilan yerdir, olumsuzlanan degil
                kaynak, kural = k, f"negasyon_{k.ipucu.yon}"
                sonuc = "absent"
                break
        if kaynak is None:
            for k in belirsiz:
                if k.kapsiyor(b, s):
                    if _anatomi_korunur(metin, k, v, varliklar):
                        continue
                    kaynak, kural, sonuc = k, "belirsizlik", "uncertain"
                    break
        if kaynak is None:
            for k in cikarim:
                if k.kapsiyor(b, s):
                    kaynak, kural, sonuc = k, "cikarim", "present"
                    break

        out.append({**v, "assertion": sonuc,
                    "assertion_cue": kaynak.metin if kaynak else None,
                    "assertion_rule": (f"{kural}:{kaynak.ipucu.ad}"
                                       if kaynak else "varsayilan_present")})
    return out


def zaman_ata(metin: str, varliklar: list[dict], ipuclari: list[Ipucu],
              sonlandirici: re.Pattern) -> list[dict]:
    """temporality + change_type ve ureten ipucu/kural (plan 4-B karar tablosu)."""
    bulunan = ipuclari_bul(metin, ipuclari, sonlandirici)
    zaman = [b for b in bulunan if b.ipucu.bolum == "zamansal"]
    degisim = [b for b in bulunan if b.ipucu.bolum == "degisim"]
    sahte = [b for b in bulunan if b.ipucu.bolum == "sahte_negasyon"]
    zref = bool(ZAMANSAL_REFERANS.search(metin))
    yon_veren = [z for z in zaman if z.ipucu.sonuc in ("prior", "current")]

    out = []
    for v in varliklar:
        b, s = v["bas"], v["son"]
        # --- temporality ---
        # DUZELTME (deneme sirasinda bulundu): ilk halde "cumlede tek zaman
        # ipucu varsa onun zamanini al" kurali vardi ve
        #   "The nodule has increased compared to THE PREVIOUS examination."
        # cumlesinde nodulu 'prior' yapiyordu - oysa nodul SIMDIKI, 'previous'
        # yalnizca KARSILASTIRMA REFERANSI. Kural daraltildi:
        # bir varlik ancak bir 'prior' ipucunun KAPSAMINDA ise prior olur.
        kapsayan = [z for z in yon_veren if z.kapsiyor(b, s)]
        if kapsayan:
            en_yakin = min(kapsayan, key=lambda z: abs(z.bas - b))
            t_sonuc, t_cue, t_kural = en_yakin.ipucu.sonuc, en_yakin.metin, "kapsam_ici"
        else:
            t_sonuc, t_cue, t_kural = "current", None, "varsayilan_current"

        # --- change_type ---
        c_sonuc, c_cue, c_kural = "none", None, "karsilastirma_yok"
        if any(x.kapsiyor(b, s) for x in sahte):
            x = next(x for x in sahte if x.kapsiyor(b, s))
            c_sonuc, c_cue, c_kural = "stable", x.metin, "sahte_negasyon_degisim_yok"
        else:
            for d in degisim:
                if not d.kapsiyor(b, s):
                    continue
                if d.ipucu.zamansal_referans_gerekir and not zref:
                    # 'increase' tek basina degisim kaniti degil (plan 4.11)
                    continue
                c_sonuc, c_cue, c_kural = d.ipucu.sonuc, d.metin, f"degisim:{d.ipucu.ad}"
                break
            else:
                if zaman:
                    c_sonuc, c_kural = "unknown", "karsilastirma_var_yon_yok"

        out.append({**v, "temporality": t_sonuc, "temporality_cue": t_cue,
                    "temporality_rule": t_kural, "change_type": c_sonuc,
                    "change_cue": c_cue, "change_rule": c_kural})
    return out
