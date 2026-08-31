# -*- coding: utf-8 -*-
"""TASK-13 / son adim: test-v2 puanlamasi. TEK ATIS - sonuc raporlanan sayidir.

AYAR KUMESINDEN FARKI:
  Ayar kumesinde kilavuz boslugu bulunmus, kural yazilip ETKILENEN satirlar
  yeniden yargilanmisti (17_build_rejudge.py). test-v2'de kurallar DONDURULMUS
  durumda (reports/task13_dondurma.md) ve kilavuz eksiksizdi -> yeniden
  yargilama YOK, tek tur.

  Sonucu gorup kural/sozluk/desen degistirmek bu surumu IPTAL eder (D26/5, D31).

HIZALAMA:
  aday_no her uc dosyada (uretilen, codex, gemini) ayni sirada -> konumsal
  kimlik dogrudan gecerli. (Ayar kumesinde bu kimlik yoktu ve tekrarli anahtar
  513 satiri 527'ye sisirmisti; bkz. 14_build_gold_template.py satir 126.)

SISTEM CIKTISI anahtardan okunur (_gizli_assertion / _gizli_temporality):
  bunlar paket URETILIRKEN dondurulmustur, sonradan yeniden hesaplanmaz.

D26/6: rastgele ve hedefli skorlar AYRI raporlanir. Hedefli kume nadir siniflari
  olculebilir kilmak icin zenginlestirilmistir; birlestirilmis ortalama hicbir
  populasyonu temsil etmez.

Kullanim: .venv/Scripts/python.exe scripts/21_score_testv2.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from radyovlm.evaluation import score as S   # noqa: E402

P = ROOT / "data" / "processed"
KUME = "test-v2"
ISARETLEYICI = ("codex", "gemini")
KESINLIK = {"mevcut": "present", "yok": "absent", "belirsiz": "uncertain"}
ZAMAN = {"guncel": "current", "onceki": "prior", "bilinmiyor": "unknown"}
CELDIRICI_ESIK = 0.80
ESIK_K4, ESIK_K5, ESIK_K6, ESIK_K7 = 0.90, 0.80, 0.85, 0.85


def n(s) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).strip()


def kelimeler(s: str) -> set:
    return {w for w in n(s).split() if len(w) >= 4}


def ortusuyor(altin: str, sis: str) -> bool:
    """Dize duzeyinde GEVSEK eslesme: kapsama veya anlamli kelime ortusmesi.

    Isaretleyici serbest metin yazdigi icin kati kavram eslemesi mumkun degil.
    Bu duyarliligi OLDUGUNDAN YUKSEK gosterebilir - raporda sinir olarak okunur.
    """
    a, s = n(altin), n(sis)
    if not a or not s:
        return False
    if a in s or s in a:
        return True
    return bool(kelimeler(a) & kelimeler(s))


# ----------------------------------------------------------------- yukleme

def yukle_b(m: str) -> pd.DataFrame:
    d = pd.read_csv(P / f"TESTV2_B_{m}.csv", encoding="utf-8-sig")
    a = pd.read_csv(P / f"task13_B_anahtar_{KUME}.csv", encoding="utf-8-sig")
    if not (d.aday_no.values == a.aday_no.values).all():
        sys.exit(f"HIZALAMA BOZUK: {m} aday_no sirasi anahtardan farkli")
    d = d.merge(a[["aday_no", "_gizli_sahte", "_gizli_assertion",
                   "_gizli_temporality"]], on="aday_no")
    for k in ("dogru_varlik_mi", "dogru_kavram_mi"):
        d[k] = d[k].astype(str).str.strip().str.upper()
    for k in ("kesinlik_ne_olmali", "zaman_ne_olmali"):
        d[k] = d[k].astype(str).str.strip().str.lower()
    d["sahte"] = d._gizli_sahte.fillna(0).astype(int)
    return d


def kappa(a, b):
    a, b = list(a), list(b)
    if not a:
        return float("nan"), float("nan")
    N = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / N
    pe = sum((a.count(x) / N) * (b.count(x) / N) for x in set(a) | set(b))
    return ((po - pe) / (1 - pe) if pe < 1 else float("nan")), po


def yorum_k(k):
    return ("neredeyse tam" if k >= .8 else "guclu" if k >= .6
            else "orta" if k >= .4 else "zayif")


# ------------------------------------------------------------ K5 duyarlilik

def k5(m: str) -> dict:
    a = pd.read_csv(P / f"TESTV2_A_{m}.csv", encoding="utf-8-sig")
    e = pd.read_parquet(P / "entities.parquet")
    orn = pd.read_csv(P / f"task12_{KUME}.csv", encoding="utf-8-sig")
    anah = ["study_id", "section", "sent_idx"]
    e = e.merge(orn[anah].drop_duplicates(), on=anah)
    grup = {k: v for k, v in e.groupby(anah)}

    out = {}
    for etiket, kolon, tipler in [("bulgu", "bulgular", {"observation"}),
                                  ("anatomi", "anatomiler", {"anatomy"}),
                                  ("tip-bagimsiz", None, None)]:
        listelenen = bulundu = 0
        kacan = []
        for r in a.itertuples(index=False):
            v = grup.get((r.study_id, r.section, r.sent_idx))
            sis_hepsi = [] if v is None else list(zip(v.raw_text, v.entity_type))
            if kolon is None:
                kalemler = [(x, None) for k in ("bulgular", "anatomiler")
                            for x in str(getattr(r, k)).split(",")
                            if x.strip() and x.strip().lower() != "nan"]
            else:
                kalemler = [(x, tipler) for x in str(getattr(r, kolon)).split(",")
                            if x.strip() and x.strip().lower() != "nan"]
            for kalem, tip in kalemler:
                listelenen += 1
                aday = [t for t, ty in sis_hepsi if tip is None or ty in tip]
                if any(ortusuyor(kalem, t) for t in aday):
                    bulundu += 1
                else:
                    kacan.append(kalem.strip())
        out[etiket] = {"listelenen": listelenen, "bulundu": bulundu,
                       "k5": bulundu / listelenen if listelenen else float("nan"),
                       "kacan": kacan}
    return out


# ------------------------------------------------------------------- rapor

def blok(d: pd.DataFrame, baslik: str) -> None:
    g = d[d.sahte == 0]
    if not len(g):
        return
    ok = int(((g.dogru_varlik_mi == "E") & (g.dogru_kavram_mi == "E")).sum())
    print(f"    {baslik:<12} n={len(g):>4}  K4 %{100*ok/len(g):>5.1f}  "
          f"-> {S.olcut_durumu(ok/len(g), ESIK_K4)}")


def eksen(g: pd.DataFrame, kol: str, harita: dict, gizli: str,
          siniflar: list, ad: str, esik: float) -> None:
    x = g[(g.dogru_varlik_mi == "E") & (g.dogru_kavram_mi == "E")].copy()
    x["altin"] = x[kol].map(harita)
    x = x[x.altin.notna() & x[gizli].notna()]
    if not len(x):
        print(f"    {ad} olculemedi (n=0)")
        return
    r = S.makro_f1([(S.Span(0, 1, "x", {"a": p}), S.Span(0, 1, "x", {"a": q}))
                    for p, q in zip(x.altin, x[gizli])], "a", siniflar)
    print(f"    {ad} makro-F1 %{100*r['makro_f1']:>5.1f}  esik %{100*esik:.0f} -> "
          f"{S.olcut_durumu(r['makro_f1'], esik)}"
          f"   (dogruluk %{100*r['dogruluk']:.1f}, n={r['n']})")
    for cl, v in r["sinif"].items():
        f = lambda z: f"{100*z:.0f}%" if z == z else "-"          # noqa: E731
        uyari = "  <- DESTEK YETERSIZ" if v["destek"] < 20 else ""
        print(f"       {cl:<10}destek{v['destek']:>4}  P{f(v['p']):>6} "
              f"R{f(v['r']):>6} F1{f(v['f1']):>6}{uyari}")


def main() -> None:
    t = {m: yukle_b(m) for m in ISARETLEYICI}

    print("=" * 68)
    print("1 · CELDIRICI KAPISI   (gecemeyen isaretleyici olcumden DISLANIR)")
    print("=" * 68)
    # OLCUT: celdirici "yakalandi" sayilir ancak isaretleyici onu TAM kabul
    # etmediyse - yani (varlik=E VE kavram=E) DEGILSE.
    #
    #   Celdirici uretici (14_build_gold_template.py) cumleden GERCEK bir
    #   kelime secip ona RASTGELE bir kavram atar. Kelime cogu zaman gercekten
    #   bir varliktir ("trachea", "heart"); sahteligi KAVRAMDADIR. Kilavuz
    #   (docs/11 bolum 3) iki kolonu ayri tanimlar: varlik = "bu bir
    #   bulgu/anatomi mi", kavram = "atanan ad uygun mu". "trachea -> fracture"
    #   satirina E/H demek kilavuza UYAN ve celdiriciyi REDDEDEN cevaptir.
    #
    #   Bu betigin ilk surumu yalnizca (varlik==H) sayiyordu ve test-v2'yi
    #   %72/%63 ile dusuruyordu. Ayni olcut AYAR kumesinde %65,5 veriyor -
    #   oysa yayimlanmis ayar raporu %100 diyor. Celiski olcutun bende yanlis
    #   yazildigini gosterdi; asagidaki olcut ayar kumesinde de %100 verir.
    #   Yani esik test sonucu gorulup GEVSETILMEDI, onceden sabit olan olcute
    #   geri donuldu.
    gecen = []
    for m in ISARETLEYICI:
        s = t[m][t[m].sahte == 1]
        ret = int((~((s.dogru_varlik_mi == "E") & (s.dogru_kavram_mi == "E"))).sum())
        o = ret / len(s)
        durum = "GECTI" if o >= CELDIRICI_ESIK else "KALDI - DISLANIR"
        print(f"  {m:<8} {ret}/{len(s)} celdirici reddedildi  %{100*o:.1f}  "
              f"esik %{100*CELDIRICI_ESIK:.0f}  -> {durum}")
        if o >= CELDIRICI_ESIK:
            gecen.append(m)
    if not gecen:
        sys.exit("HIC ISARETLEYICI GECMEDI - olcum gecersiz")

    print("\n" + "=" * 68)
    print("2 · ISARETLEYICILER ARASI UYUM   (konumsal, aday_no uzerinden)")
    print("=" * 68)
    c, g = t["codex"], t["gemini"]
    for etiket, kol, yalniz_gercek in [
            ("varlik (E/H)", "dogru_varlik_mi", False),
            ("kavram (E/H)", "dogru_kavram_mi", False),
            ("KESINLIK", "kesinlik_ne_olmali", True),
            ("ZAMAN", "zaman_ne_olmali", True)]:
        ok = (c.sahte == 0) if yalniz_gercek else pd.Series(True, index=c.index)
        ok &= c[kol].ne("nan") & g[kol].ne("nan")
        A, B = c.loc[ok, kol], g.loc[ok, kol]
        k, po = kappa(A, B)
        print(f"  {etiket:<16}n={len(A):>4}  uyum %{100*po:>5.1f}  "
              f"kappa {k:.3f}  ({yorum_k(k)})")

    print("\n" + "=" * 68)
    print("3 · K5 DUYARLILIK   (kor listelemeden - sistem ciktisi gorulmeden)")
    print("=" * 68)
    k5_sonuc = {}
    for m in gecen:
        k5_sonuc[m] = k5(m)
        print(f"  --- {m} ---")
        for etiket, v in k5_sonuc[m].items():
            bayrak = (f"  esik %{100*ESIK_K5:.0f} -> "
                      f"{S.olcut_durumu(v['k5'], ESIK_K5)}"
                      if etiket == "tip-bagimsiz" else "")
            print(f"    {etiket:<14}listelenen {v['listelenen']:>4}  "
                  f"bulundu {v['bulundu']:>4}  kacan "
                  f"{v['listelenen']-v['bulundu']:>3}  "
                  f"K5 %{100*v['k5']:>5.1f}{bayrak}")

    if len(gecen) > 1:
        ortak = (set(map(str.lower, k5_sonuc[gecen[0]]["tip-bagimsiz"]["kacan"]))
                 & set(map(str.lower, k5_sonuc[gecen[-1]]["tip-bagimsiz"]["kacan"])))
        if ortak:
            print(f"\n  IKISININ DE KACIRDIGI ({len(ortak)} tekil) - gercek"
                  f" sozluk boslugu adaylari:")
            print("   " + " · ".join(sorted(ortak)[:40]))

    print("\n" + "=" * 68)
    print("4 · K4 / K6 / K7   (D26/6: rastgele ve hedefli AYRI)")
    print("=" * 68)
    for m in gecen:
        d = t[m]
        print(f"\n  --- {m} ---")
        print("   K4 VARLIK KESINLIGI")
        blok(d[d.grup == "rastgele"], "rastgele")
        blok(d[d.grup != "rastgele"], "hedefli")
        blok(d, "(hepsi)")
        for etiket, alt in [("rastgele", d[d.grup == "rastgele"]),
                            ("hedefli", d[d.grup != "rastgele"])]:
            gg = alt[alt.sahte == 0]
            print(f"\n   {etiket.upper()}")
            eksen(gg, "kesinlik_ne_olmali", KESINLIK, "_gizli_assertion",
                  ["present", "absent", "uncertain"], "K6 kesinlik", ESIK_K6)
            eksen(gg, "zaman_ne_olmali", ZAMAN, "_gizli_temporality",
                  ["current", "prior", "unknown"], "K7 zaman   ", ESIK_K7)


if __name__ == "__main__":
    main()
