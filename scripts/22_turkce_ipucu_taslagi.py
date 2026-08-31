# -*- coding: utf-8 -*-
"""TURKCE ipucu sozlugunu KORPUSTAN turetir ve olcer (TASK-14 / adim 5).

NEDEN EN KRITIK ADIM:
  Sistemin en guclu yani negasyon: test-v2'de `absent` 73/73. Ama bu tamamen
  Ingilizce ipuclarina dayaniyor ("no", "not observed", "was not detected").
  Cevrilmezse Turkcede negasyon TAMAMEN COKER.

ITHAL EDILMEZ, OLCULUR - Ingilizce tarafta oldugu gibi (D16):
  Ders kitabi bir Turkce olumsuzlama listesi "gorulmedi", "rastlanmadi",
  "tespit edilmedi", "mevcut degil" icerirdi. OLCULDU: DORDU DE SIFIRA YAKIN.
  Bu korpusta olumsuzlamayi IKI bicim tasiyor: saptanma- (583) ve izlenme- (260).

  Ingilizce tarafta ithal NegEx listesinin 272 tetikleyicisinin 220'si hic
  gecmiyordu. Ayni sonuc, ayni sebep: sozluk korpustan turetilir.

⚠ TURKCEYE OZGU IKI BULGU - mimariyi dogrudan etkiler:

  1) YON. Turkce fiil-sonlu bir dil; olumsuzluk AYRI KELIME degil SON EKtir
     (-ma/-me). Olculdu: negasyon ipucu tasiyan 843 cumlenin %97'sinde ipucu
     cumlenin SONUNDA. Ingilizcede bu oran %19,9'du.
     -> Ingilizceye gore ayarlanmis ILERI yonlu bir kurulum Turkcede negasyonun
        NEREDEYSE TAMAMINI kacirir. Varsayilan yon 'geri' olmalidir.

  2) TEKNIK CEKINCE NEGASYONDAN BUYUK. "verilmedigi/yapilamamistir/optimal
     degerlendirilemedi" kaliplari 900+ anma veriyor - gercek negasyondan fazla.
     Bunlar da -ma/-me eki tasir. Genel bir "-ma/-me olumsuzluk demektir" kurali
     bu 900+ anmayi da olumsuzlama sayar ve KITLESEL yanlis 'absent' uretir.
     D30 (teknik cekince kesinligi degistirmez) Turkcede daha da kritiktir.

Kullanim: .venv/Scripts/python.exe scripts/22_turkce_ipucu_taslagi.py
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
BS = chr(92)
GELISTIRME = ("train", "dev")

# bolum -> ipucu adi -> (desen, sonuc)
# Desenler BASTA sinirlidir (Turkce sondan eklemeli, bkz. 20_turkce_yuzey_taslagi).
IPUCU = {
    "belirsizlik_oncelikli": {
        # Ingilizcedeki "cannot be excluded" karsiligi. Icinde olumsuzluk eki
        # tasir ve naif bir negasyon kurali bunu 'absent' yazar - ANLAMIN TERSI.
        "ekarte_edilemez": ("ekarte edileme|d[ıi][şs]lanama", "uncertain"),
        "ayirt_edilemedi": ("ay[ıi]rt edileme", "uncertain"),
    },
    "teknik_cekince": {
        # ⚠ NEGASYON DEGIL. Tetkikin sinirindan bahseder, bulgunun yoklugundan degil.
        "kontrast_verilmedi": ("kontrast.{0,20}verilme|verilmedi[gğ]in", None),
        "yapilamadi": ("yap[ıi]lama", None),
        "degerlendirilemedi": ("de[gğ]erlendirileme|se[çc]ileme", None),
        "optimal_degil": ("optimal|yeterince", None),
    },
    "negasyon": {
        # Korpustan turetildi. Ders kitabi listesindeki gorulmedi/rastlanmadi/
        # tespit edilmedi/mevcut degil ODCULDU ve SIFIRA YAKIN cikti - alinmadi.
        "saptanmadi": ("saptanma(?:d|m)", "absent"),
        "izlenmedi": ("izlenme(?:d|m)", "absent"),
    },
    "negasyon_olculup_alinmayan": {
        # Alinmadi cunku destegi yok. Kayitta durur ki baska korpusta yeniden
        # olculebilsin - "denenmedi" ile "denendi, cikmadi" ayri seylerdir.
        "gorulmedi": ("g[oö]r[uü]lme(?:d|m)", "absent"),
        "rastlanmadi": ("rastlanm|rastlanmad", "absent"),
        "tespit_edilmedi": ("tespit edilme", "absent"),
        "mevcut_degil": ("mevcut de[gğ]il", "absent"),
        "bulunmamaktadir": ("bulunma(?:d|m)", "absent"),
        "negatif": ("negatif", "absent"),
    },
    "belirsizlik": {
        "parantez_soru": (r"\([^)]{2,40}\?\s*\)", "uncertain"),
        # PARANTEZSIZ SORU (dev olcumunde bulundu): Turkce raporlar ayirici
        # taniyi parantezsiz de yaziyor - "KLINIK BILGI: PTE? PNOMONI?",
        # "nodul? metastaz?". Parantezli bicimin 4 KATI kadar geciyor
        # (461'e 117). Kapsam: soru isaretinin ONUNDEKI terim.
        "soru_isareti": (r"[A-Za-zİıŞşĞğÜüÖöÇç]{3,}\s*\?", "uncertain"),
        "ayirici_tani": ("ay[ıi]r[ıi]c[ıi] tan[ıi]", "uncertain"),
    },
    "cikarim_ifadesi": {
        # D29: bunlar BELIRSIZ DEGIL, MEVCUT. Ingilizce tarafta olculmustu;
        # Turkce karsiliklari da tasiniyor.
        "uyumlu": ("uyumlu", "present"),
        "lehine": ("lehine", "present"),
        "olasi": ("olas[ıi]|olabil", "present"),
        "oncelikle": ("[oö]ncelikle", "present"),
        "dusunuldu": ("d[uü][şs][uü]n[uü]l", "present"),
        "supheli": ("[şs][uü]pheli", "present"),
    },
    "zamansal": {
        "onceki_tetkik": ("[oö]nceki tetkik|[oö]nceki incelem|eski tetkik", "prior"),
        "karsilastirma": ("kar[şs][ıi]la[şs]t[ıi]r|g[oö]re", "prior"),
    },
    "degisim": {
        # ⚠ Tek basina zamansal kanit DEGIL - Ingilizce tarafta olculmustu:
        # artis bildiren 25.522 cumlenin yalnizca %3,4'unde acik zaman referansi var.
        "artis": ("artm[ıi][şs]|art[ıi][şs]", None),
        "gerileme": ("gerile|azalm", None),
        "stabil": ("stabil|sebat|de[gğ]i[şs]iklik yok", None),
    },
}

# Cumleyi bolen kalip - yon olcumu icin
CUMLE = re.compile(r"(?<=[.;])\s+")


def metinler(bolumler) -> tuple[str, list[str]]:
    yol = PROC / "radtr_toraks.jsonl"
    if not yol.exists():
        sys.exit("once scripts/16_extract_radtr_thorax.py calistirilmali")
    belgeler = [json.loads(l) for l in yol.open(encoding="utf-8")]
    secili = [b for b in belgeler if b["kaynak_bolum"] in bolumler]
    cumleler = [c.strip() for b in secili
                for c in CUMLE.split(b["metin"]) if c.strip()]
    return " ".join(b["metin"] for b in secili), cumleler, len(secili), len(belgeler)


def yon_olc(cumleler: list[str], desen: str) -> dict:
    """Ipucu cumlenin neresinde duruyor? Turkcede bu 'geri' cikmali."""
    r = re.compile(BS + "b(?:" + desen + ")", re.I)
    n = son = bas = 0
    for c in cumleler:
        m = r.search(c)
        if not m:
            continue
        n += 1
        oran = m.start() / max(1, len(c))
        son += oran > 0.6
        bas += oran < 0.3
    return {"cumle": n, "sonda": son, "basta": bas,
            "yon": ("geri" if n and son / n > 0.7
                    else "ileri" if n and bas / n > 0.7 else "cift")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", default="gelistirme")
    a = ap.parse_args()
    if a.bolum != "gelistirme":
        sys.exit("DURDU: yalnizca train+dev. test dokunulmazdir.\n"
                 "  Gerekce: reports/turkce_bolunme_dondurma.md")

    metin, cumleler, n_sec, n_hep = metinler(GELISTIRME)
    print(f"olcum tabani: {n_sec}/{n_hep} belge (train+dev) · "
          f"{len(metin.split())} kelime · {len(cumleler)} cumle")
    print(f"DISARIDA: {n_hep - n_sec} test belgesi\n")

    cikti, alinmayan = {}, []
    for bolum, ipuclari in IPUCU.items():
        cikti[bolum] = {}
        print(f"=== {bolum}")
        for ad, (desen, sonuc) in ipuclari.items():
            n = len(re.findall(
                desen if desen.startswith("\\(") else BS + "b(?:" + desen + ")",
                metin, re.I))
            kayit = {"desen": desen, "korpus": n, "uzman_onayi": False}
            if sonuc:
                kayit["sonuc"] = sonuc
            if bolum in ("negasyon", "belirsizlik_oncelikli"):
                kayit.update(yon_olc(cumleler, desen))
            cikti[bolum][ad] = kayit
            bayrak = "  <- DESTEK YOK, ALINMADI" if n == 0 else ""
            if n == 0:
                alinmayan.append(f"{bolum}/{ad}")
            yon = f"  yon={kayit['yon']}" if "yon" in kayit else ""
            print(f"   {ad:<24}{n:>5}{yon}{bayrak}")
        print()

    # --- Turkceye ozgu iki olcum, rapora girecek ---
    neg = "|".join(v[0] for v in IPUCU["negasyon"].values())
    y = yon_olc(cumleler, neg)
    tek = sum(cikti["teknik_cekince"][k]["korpus"] for k in cikti["teknik_cekince"])
    gercek_neg = sum(cikti["negasyon"][k]["korpus"] for k in cikti["negasyon"])

    print("=" * 62)
    print("TURKCEYE OZGU OLCUMLER")
    print("=" * 62)
    print(f"1) YON: negasyon ipucu tasiyan {y['cumle']} cumlenin "
          f"%{100*y['sonda']/max(1,y['cumle']):.0f}'inde ipucu SONDA, "
          f"%{100*y['basta']/max(1,y['cumle']):.0f}'inde BASTA.")
    print(f"   Ingilizce tarafta SONDA orani %19,9 idi. Ileri yonlu bir kurulum")
    print(f"   Turkcede negasyonun neredeyse TAMAMINI kacirir.")
    print(f"\n2) TEKNIK CEKINCE {tek} anma · GERCEK NEGASYON {gercek_neg} anma")
    print(f"   Teknik cekince negasyondan {tek/max(1,gercek_neg):.1f} kat BUYUK.")
    print(f"   Genel bir '-ma/-me olumsuzluktur' kurali bu {tek} anmayi da")
    print(f"   olumsuzlama sayar -> kitlesel yanlis 'absent'. D30 kritiktir.")
    print(f"\nDestegi sifir oldugu icin ALINMAYAN: {len(alinmayan)}")
    for x in alinmayan:
        print(f"   {x}")

    yol = ROOT / "configs" / "turkce_ipuclari_taslak.yaml"
    with yol.open("w", encoding="utf-8") as f:
        f.write(
            "# TURKCE IPUCU TASLAGI - surum: tr-ipucu-0.1 (TASLAK)\n"
            "#\n"
            "# ⚠ HICBIR IPUCU UZMAN ONAYINDAN GECMEDI.\n"
            "#\n"
            f"# KORPUSTAN TURETILDI: RadTr train+dev ({n_sec} belge · "
            f"{len(cumleler)} cumle). Ithal liste alinmadi.\n"
            "#\n"
            "# TURKCEYE OZGU IKI BULGU:\n"
            f"#  1) YON: negasyon ipuclarinin %{100*y['sonda']/max(1,y['cumle']):.0f}'i"
            " cumle SONUNDA (Ingilizcede %19,9).\n"
            "#     Turkce fiil-sonlu; olumsuzluk ayri kelime degil SON EKtir.\n"
            f"#  2) Teknik cekince ({tek}) gercek negasyondan ({gercek_neg}) "
            f"{tek/max(1,gercek_neg):.1f} kat BUYUK.\n"
            "#     Genel '-ma/-me' kurali kitlesel yanlis 'absent' uretir.\n"
            "#\n"
            "# 'korpus: 0' olan ipuclari ALINMADI; kayitta durur ki baska bir\n"
            "# korpusta yeniden olculebilsin.\n\n")
        yaml.safe_dump({"surum": "tr-ipucu-0.1", "durum": "taslak",
                        "kaynak": f"RadTr train+dev ({n_sec} belge) - test HARIC",
                        "bolumler": cikti},
                       f, allow_unicode=True, sort_keys=False, width=100)
    print(f"\nyazildi: {yol.name}")


if __name__ == "__main__":
    main()
