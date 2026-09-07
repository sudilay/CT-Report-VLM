# -*- coding: utf-8 -*-
"""TASK-11: Varlik, iliski ve olcu baglarinin cikarimi.

D15 geregi DETERMINISTIK: sozluk + kural. Ayni girdi her zaman ayni ciktiyi verir
ve her cikarimin hangi kuraldan geldigi `extraction_rule` / `attachment_rule`
alanlarinda kayitlidir. LLM kullanilmaz - Faz 4 LLM'leri degerlendirecek, Faz 2'yi
LLM'e yaptirmak dongusellik olurdu.

Sozlukler:
  configs/anatomi_sozlugu.yaml   anatomi kavramlari + taraf sozlugu
  configs/bulgu_sozlugu.yaml     gozlem, niteleyici, cihaz

EN UZUN ESLESME KAZANIR. Alternatifler ESLESEBILECEKLERI AZAMI METIN uzunluguna gore
siralanir - desen metninin uzunluguna gore DEGIL (bkz. azami_eslesme_uzunlugu); boylece
  "upper lobe"            -> upper_lobe      ("lobe" degil)
  "hilar-axillary"        -> station_hilar_axillary  ("hilar" degil)
  "space-occupying lesion"-> space_occupying_lesion  ("lesion" degil)
  "effusion-thickening"   -> effusion_thickening     ("effusion" degil)
  "atheromatous plaques"  -> TEK anma           (iki ayri anma degil)
Bu beslisi test edilir (tests/test_entities.py).

Bilinen sinirlar - gizlenmiyor, olculup TASK-13'e birakiliyor:
  * Bir gozlem EN FAZLA BIR located_at alir. "nodules in both lungs and liver"
    gibi cumlelerde yalnizca en yakin anatomi baglanir.
  * Cumleler arasi gonderme ("It is stable.") cozulmez; is_cross_sentence hep False.
  * Esit uzaklikta iki aday olmasi:
      - located_at'te BAG KURULMAZ (gozlem-anatomi arasinda yon kurali yoktur)
      - modify ve measured_by'da SAGDAKI secilir (D20) - Ingilizce isim obeginde
        niteleyici bas isimden once gelir
  * Kurulamayan hicbir bag DUSURULMEZ; sebebiyle unresolved_attachments'a yazilir
    (D22). Butunluk testi: her olcu ya baglanir ya kaydedilir.
  * Baglarin DOGRULUGU bu modulde olculmez - bu kurallar sezgiseldir ve dogruluk
    TASK-13'te altin aciklama setiyle olculecektir.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
CONF = ROOT / "configs"

# TASK-17 madde 8 (D88): sozluk `bulgu-1.1` -> `bulgu-1.2` genisledi
# (88 -> 106 kavram), bu yuzden varlik tablosu YENIDEN URETILDI.
# `ent-1.0` dondurmasi (reports/task13_dondurma.md) KIRILDI - kod
# degismedi, GIRDI SOZLUGU degisti; sayilar yeniden ifade edilmelidir.
ENTITY_VERSION = "ent-1.1"
RELATION_VERSION = "rel-1.0"
MEASUREMENT_VERSION_YENI = "meas-1.1"

TARAF_PENCERE = 60      # karakter: taraf ipucu bu uzakliga kadar aranir
EN_BUYUGU = re.compile(r"largest of which|the largest|biggest of which", re.I)


# --------------------------------------------------------------- sozluk

@dataclass
class Kavram:
    ad: str
    tip: str                 # observation | anatomy | qualifier | device
    desenler: list[str]
    grup: str | None = None  # niteleyici grubu
    ust_kavram: str | None = None
    taraf_alir: bool = False
    korpus: int = 0


def _yukle_yaml(ad: str) -> dict:
    with open(CONF / ad, encoding="utf-8") as f:
        return yaml.safe_load(f)


def sozlukleri_yukle() -> tuple[list[Kavram], dict[str, list[str]]]:
    anat = _yukle_yaml("anatomi_sozlugu.yaml")
    bulgu = _yukle_yaml("bulgu_sozlugu.yaml")

    kavramlar: list[Kavram] = []
    for ad, t in anat["kavramlar"].items():
        kavramlar.append(Kavram(ad, "anatomy", t["desenler"],
                                ust_kavram=t.get("ust_kavram"),
                                taraf_alir=bool(t.get("taraf_alir")),
                                korpus=t.get("korpus", 0)))
    for ad, t in bulgu["kavramlar"].items():
        kavramlar.append(Kavram(ad, t["tip"], t["desenler"], grup=t.get("grup"),
                                taraf_alir=t["tip"] in ("observation",),
                                korpus=t.get("korpus", 0)))
    return kavramlar, anat["taraf"]


def _yakalayan_grup_var_mi(desen: str) -> bool:
    """Lexicon desenleri YAKALAYAN grup icermemeli - birlesik regex'te grup
    numaralarini kaydirir ve eslesmeyi sessizce bozar."""
    return bool(re.search(r"\((?!\?)", desen))


def azami_eslesme_uzunlugu(desen: str) -> int:
    """Bir regex deseninin eslestirebilecegi AZAMI metin uzunlugunu kestirir.

    NEDEN GEREKLI - inceleme sirasinda bulunan kok kusur:
      Ilk surumde alternatifler DESEN METNININ uzunluguna gore siralaniyordu.
      Ama desen uzunlugu ile eslesen metnin uzunlugu ayni sey degil:
        "athero(?:sclerosis|sclerotic|matous)"  desen 36 kr, eslesme en fazla 15 kr
        "atheromatous plaques?"                 desen 21 kr, eslesme en fazla 20 kr
      Uzun DESEN once denendigi icin "atheromatous plaques" iki ayri anmaya
      bolunuyordu (2.021 vaka). "En uzun eslesme kazanir" iddiasi bu yuzden
      yalnizca YAKLASIK dogruydu. Artik eslesme uzunlugu kestiriliyor.
    """
    i, n, toplam = 0, len(desen), 0
    while i < n:
        c = desen[i]
        if c == "\\":                                  # \w \d \s -> 1 karakter
            i += 2
            uzunluk = 1
        elif c == "[":                                 # karakter sinifi -> 1
            j = i + 1
            while j < n and (desen[j] != "]" or desen[j - 1] == "\\"):
                j += 1
            i = j + 1
            uzunluk = 1
        elif c == "(":                                 # grup -> en uzun dal
            derinlik, j = 1, i + 1
            while j < n and derinlik:
                if desen[j] == "\\":
                    j += 2
                    continue
                derinlik += (desen[j] == "(") - (desen[j] == ")")
                j += 1
            ic = desen[i + 1:j - 1]
            ic = ic[3:] if ic.startswith("?:") is False and ic.startswith("?") else ic
            ic = ic[2:] if ic.startswith("?:") else ic
            uzunluk = max((azami_eslesme_uzunlugu(d) for d in _dallar(ic)),
                          default=0)
            i = j
        else:
            i += 1
            uzunluk = 1
        # niceleyici
        if i < n and desen[i] in "?*+":
            if desen[i] == "*":
                uzunluk = uzunluk * 3          # sinirsiz - olculu bir kestirim
            elif desen[i] == "+":
                uzunluk = uzunluk * 3
            i += 1
        toplam += uzunluk
    return toplam


def _dallar(ic: str) -> list[str]:
    """Ust duzey '|' ile ayrilmis dallar (ic gruplar sayilmaz)."""
    out, derinlik, son = [], 0, 0
    for i, c in enumerate(ic):
        if c == "(":
            derinlik += 1
        elif c == ")":
            derinlik -= 1
        elif c == "|" and derinlik == 0:
            out.append(ic[son:i])
            son = i + 1
    out.append(ic[son:])
    return out


def matcher_kur(kavramlar: list[Kavram]) -> tuple[re.Pattern, dict[str, Kavram]]:
    """Tum kavramlari TEK bir regex'te birlestirir.

    Alternatifler ESLESEBILECEKLERI AZAMI METIN UZUNLUGUNA gore azalan siralanir.
    Python alternasyonu soldan-ilk eslesir (en-uzun degil); siralama en uzun
    eslesmeyi saglar. Desen metninin uzunluguna gore siralamak yanlisti
    (bkz. azami_eslesme_uzunlugu).
    """
    parcalar, indeks = [], {}
    adaylar: list[tuple[int, str, Kavram]] = []
    for k in kavramlar:
        for d in k.desenler:
            if _yakalayan_grup_var_mi(d):
                raise ValueError(f"{k.ad}: desen yakalayan grup iceriyor -> {d}")
            adaylar.append((azami_eslesme_uzunlugu(d), d, k))

    adaylar.sort(key=lambda x: (-x[0], -len(x[1])))
    for i, (_, d, k) in enumerate(adaylar):
        g = f"m{i}"
        parcalar.append(f"(?P<{g}>{d})")
        indeks[g] = k
    return re.compile(r"\b(?:" + "|".join(parcalar) + r")\b", re.I), indeks


# --------------------------------------------------------------- kimlik

def _kimlik(*parcalar) -> str:
    ham = "|".join(str(p) for p in parcalar)
    return hashlib.sha1(ham.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------- taraf

def taraf_matcher(taraf_sozluk: dict[str, list[str]]) -> tuple[re.Pattern, dict]:
    alt = []
    for etiket, kelimeler in taraf_sozluk.items():
        for w in kelimeler:
            alt.append((len(w), w, etiket))
    alt.sort(key=lambda x: -x[0])
    desen = re.compile(r"\b(?:" + "|".join(
        f"(?P<t{i}>{w})" for i, (_, w, _) in enumerate(alt)) + r")\b", re.I)
    return desen, {f"t{i}": e for i, (_, _, e) in enumerate(alt)}


def taraf_bul(metin: str, desen: re.Pattern, indeks: dict) -> list[tuple[int, int, str]]:
    out = []
    for m in desen.finditer(metin):
        g = m.lastgroup
        if g in indeks:
            out.append((m.start(), m.end(), indeks[g]))
    return out


def taraf_ata(taraflar: list[tuple[int, int, str]],
              bas: int, son: int) -> str | None:
    """Varliga en yakin taraf ipucunu atar; esitlikte SOL tercih edilir.

    Radyoloji dilinde taraf isimden once gelir ("right lung", "both lungs"),
    o yuzden soldaki ipucu once gelir. TARAF_PENCERE karakterden uzaktaki
    ipucu atanmaz - o baska bir varliga aittir.
    """
    en_iyi, en_yakin, en_iyi_sol = None, TARAF_PENCERE + 1, False
    for tb, ts, etiket in taraflar:
        if ts <= bas:
            d, sol = bas - ts, True
        elif tb >= son:
            d, sol = tb - son, False
        else:
            d, sol = 0, True                      # ic ice: "both lungs"
        if d > TARAF_PENCERE:
            continue
        if d < en_yakin or (d == en_yakin and sol and not en_iyi_sol):
            en_iyi, en_yakin, en_iyi_sol = etiket, d, sol
    return en_iyi


# --------------------------------------------------------------- cikarim

def cumleden_varliklar(metin: str, matcher: re.Pattern, indeks: dict) -> list[dict]:
    """Bir cumleden varliklari cikarir. Ofsetler CUMLE ICINDE gorelidir."""
    out = []
    for m in matcher.finditer(metin):
        g = m.lastgroup
        # lastgroup ic ice gruplarda yaniltabilir; dolu olan grubu bul
        if g is None or m.group(g) is None:
            g = next((k for k, v in m.groupdict().items() if v is not None), None)
        if g is None:
            continue
        k = indeks[g]
        out.append({"kavram": k, "bas": m.start(), "son": m.end(),
                    "metin": m.group(0)})
    return _bitisikleri_birlestir(out, metin)


def _bitisikleri_birlestir(varliklar: list[dict], metin: str) -> list[dict]:
    """Ayni kavramin bitisik iki anmasini TEK anmaya indirir.

    "atheromatous plaques" -> desen siralamasi yanlis oldugunda iki ayri
    atheroma_plaque anmasi uretiyordu (2.021 vaka). Siralama duzeltildi ama
    baska desen ciftlerinde de olabilecegi icin bu gecis savunma katmanidir.
    Yalnizca aradaki bosluk TEK bir bosluk veya tire ise birlestirilir;
    virgulle ayrilmis iki anma AYRI kalir.
    """
    if len(varliklar) < 2:
        return varliklar
    out = [varliklar[0]]
    for v in varliklar[1:]:
        o = out[-1]
        ara = metin[o["son"]:v["bas"]]
        if o["kavram"] is v["kavram"] and ara in (" ", "-", ""):
            o["son"] = v["son"]
            o["metin"] = metin[o["bas"]:v["son"]]
        else:
            out.append(v)
    return out


def _en_yakin(kaynak_bas: int, kaynak_son: int, adaylar: list[dict], *,
              esitlikte_sag: bool = False) -> tuple[dict | None, str]:
    """En yakin adayi ve hangi kuralla secildigini dondurur.

    esitlikte_sag=False (located_at): esit uzaklikta iki aday varsa BAG KURULMAZ.
      Gozlem ile anatomi arasinda bir yon kurali yoktur; tahmin edilmez (D18).

    esitlikte_sag=True (modify, measured_by): esitlikte SAGDAKI secilir.
      Gerekce dil bilgiseldir: Ingilizce isim obeginde NITELEYICI BAS ISIMDEN
      ONCE gelir, yani niteleyicinin sagindaki aday bas isimdir.
        "Mediastinal millimetric lymph nodes"
         ^anatomi(sol,1)  ^olcu  ^anatomi(sag,1)  -> esit, ama bas isim SAGDA
      Ilk surumde bu vaka 'belirsiz' sayilip baglanmiyordu; elle inceleme
      sirasinda goruldu ve kural eklendi. Ayri kural adiyla kaydedilir ki
      esitlikten gelen bag, kesin bagdan ayirt edilebilsin.
    """
    if not adaylar:
        return None, "yok"
    if len(adaylar) == 1:
        return adaylar[0], "tek_aday"

    olculu = []
    for a in adaylar:
        if a["son"] <= kaynak_bas:
            olculu.append((kaynak_bas - a["son"], 1, "en_yakin_sol", a))
        elif a["bas"] >= kaynak_son:
            olculu.append((a["bas"] - kaynak_son, 0, "en_yakin_sag", a))
        else:
            olculu.append((0, 0, "ayni_oge", a))

    # sirala: once uzaklik, sonra (esitlikte_sag ise) sagdakini one al
    olculu.sort(key=lambda x: (x[0], x[1] if esitlikte_sag else 0))
    if len(olculu) > 1 and olculu[0][0] == olculu[1][0]:
        if not esitlikte_sag or olculu[0][1] == olculu[1][1]:
            return None, "belirsiz"
        return olculu[0][3], "esitlikte_sag"
    return olculu[0][3], olculu[0][2]


# Konum edati: ardindaki anatomi bulgunun YERIDIR, olculen sey degil.
# Araya giren kelimelere izin verilir: "in the RIGHT lung", "in both UPPER lobes".
# Ilk surumde yalnizca "in the " gibi bitisik bicim yakalaniyordu; taraf kelimesi
# araya girdiginde eleme calismiyordu ve "in the right lung" elenmiyordu.
KONUM_EDATI = re.compile(r"\b(?:in|within|at|on|into)\s+(?:\w+[\s-]+){0,3}$", re.I)


def _konum_mu(metin: str, varlik: dict) -> bool:
    return bool(KONUM_EDATI.search(metin[:varlik["bas"]]))


def _uzaklik(kaynak: dict, adaylar: list[dict]) -> int:
    """Kaynaga en yakin adayin karakter uzakligi."""
    return min((kaynak["bas"] - a["son"] if a["son"] <= kaynak["bas"]
                else a["bas"] - kaynak["son"] if a["bas"] >= kaynak["son"] else 0)
               for a in adaylar)


def iliskileri_kur(varliklar: list[dict], olculer: list[dict],
                   cumle_metni: str) -> tuple[list[dict], list[dict]]:
    """located_at · modify · measured_by iliskilerini kurar.

    Doner: (iliskiler, cozulemeyenler). Cozulemeyenler DUSURULMEZ - kaydedilir,
    cunku K9 kabul olcutunun 'belirsiz alt kume'si onlardan uretilir (sema-1.1).
    """
    gozlem = [v for v in varliklar if v["kavram"].tip == "observation"]
    anatomi = [v for v in varliklar if v["kavram"].tip == "anatomy"]
    nitel = [v for v in varliklar if v["kavram"].tip == "qualifier"]
    cihaz = [v for v in varliklar if v["kavram"].tip == "device"]

    rel, cozulemeyen = [], []

    def _kaydet(kaynak, tip, sebep, n_aday, olcu_mu=False):
        cozulemeyen.append({"kaynak": kaynak, "olcu_mu": olcu_mu,
                            "tip": tip, "sebep": sebep, "n_aday": n_aday})

    # --- located_at: gozlem/cihaz -> anatomi ---
    for g in gozlem + cihaz:
        if not anatomi:
            continue                       # anatomi yoksa bag beklenmiyor
        hedef, kural = _en_yakin(g["bas"], g["son"], anatomi)
        if hedef is None:
            _kaydet(g, "located_at", "belirsiz", len(anatomi))
            continue
        rel.append({"head": g, "tail": hedef, "tip": "located_at", "kural": kural})

    # --- modify: niteleyici -> gozlem (yoksa anatomi) ---
    for n in nitel:
        adaylar = gozlem or anatomi
        if not adaylar:
            continue
        hedef, kural = _en_yakin(n["bas"], n["son"], adaylar, esitlikte_sag=True)
        if hedef is None:
            _kaydet(n, "modify", "belirsiz", len(adaylar))
            continue
        rel.append({"head": n, "tail": hedef, "tip": "modify", "kural": kural})

    # --- measured_by ---
    # Iki eleme, sirayla. Inceleme gosterdi ki duz "en yakin" kurali sistematik
    # olarak yaniliyor: "The pleural effusion in the right lung reaches 10 cm"
    # cumlesinde olcu 'lung'a baglaniyordu, oysa olculen sey EFUZYON.
    en_buyugu = bool(EN_BUYUGU.search(cumle_metni))
    tum_aday = gozlem + anatomi + cihaz
    for o in olculer:
        if not tum_aday:
            _kaydet(o, "measured_by", "aday_yok", 0, olcu_mu=True)
            continue
        ham_hedef, _ = _en_yakin(o["bas"], o["son"], tum_aday, esitlikte_sag=True)

        # 1) Konum edatinin ardindaki anatomi olculen sey degildir
        elenmis = [a for a in tum_aday
                   if not (a["kavram"].tip == "anatomy" and _konum_mu(cumle_metni, a))]
        konum_elendi = len(elenmis) < len(tum_aday)
        adaylar = elenmis or tum_aday

        # 2) Olcu bir BULGUYU olcer, organi degil - gozlem varsa o secilir.
        #    AMA kosulsuz degil. Ilk denemede kosulsuzdu ve bir gerilemeye yol
        #    acti: "The ascending aorta is 39 mm and ectatic" cumlesinde olcu
        #    aorta yerine 'ectatic'e baglandi - oysa olculen sey AORT.
        #    Kural daraltildi: gozlem onceligi ancak
        #      (a) konum eleme bir anatomiyi cikardiysa   -> "in the right lung"
        #      (b) veya gozlem anatomiden DAHA YAKINSA
        #    gecerlidir. Aksi hâlde en yakin aday kazanir.
        gozlem_aday = [a for a in adaylar if a["kavram"].tip in ("observation", "device")]
        anat_aday = [a for a in adaylar if a["kavram"].tip == "anatomy"]
        gozlem_secildi = False
        if gozlem_aday and anat_aday:
            if konum_elendi or _uzaklik(o, gozlem_aday) <= _uzaklik(o, anat_aday):
                adaylar, gozlem_secildi = gozlem_aday, True
        elif gozlem_aday:
            adaylar = gozlem_aday

        hedef, kural = _en_yakin(o["bas"], o["son"], adaylar, esitlikte_sag=True)
        if hedef is None:
            _kaydet(o, "measured_by", "belirsiz", len(adaylar), olcu_mu=True)
            continue

        if en_buyugu and kural != "tek_aday":
            kural = "en_buyugu_ifadesi"
        elif hedef is not ham_hedef:
            kural = "gozlem_onceligi" if gozlem_secildi else (
                "konum_edati_atlandi" if konum_elendi else kural)
        rel.append({"head": hedef, "tail": o, "tip": "measured_by",
                    "kural": kural, "tail_olcu": True})
    return rel, cozulemeyen
