# -*- coding: utf-8 -*-
"""TASK-13 / C1: Yapisal degismezleri olcer (K11-K15).

NEDEN ALTIN ACIKLAMA GEREKMEZ:
  Bu olcutler "cevap dogru mu" diye sormuyor, "sistem kendi kuraluna uyuyor mu"
  diye soruyor. Ikisi farkli. Gecmeleri sistemin DOGRU oldugunu gostermez;
  GECMEMELERI sistemin kendi tasarimina uymadigini gosterir - o kesin hatadir.

  K4-K10 (kesinlik, duyarlilik, F1) insan isaretlemesi bekliyor - `14_score.py`.

Kullanim: .venv/Scripts/python.exe scripts/13_check_invariants.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction import context as C   # noqa: E402

PROC = ROOT / "data" / "processed"
OUTD = ROOT / "reports"
ANAHTAR = ["study_id", "section", "sent_idx"]


def yukle():
    ent = pd.read_parquet(PROC / "entities.parquet")
    sent = pd.read_parquet(PROC / "sentences.parquet")
    return ent, sent


def _kapsayan_varliklar(metin, cb, varliklar, ipucu_bulunanlar):
    """Bir ipucunun kapsamina dusen varliklarin indekslerini dondurur."""
    out = []
    for i, r in enumerate(varliklar):
        b, s = r[0] - cb, r[1] - cb
        if any(k.kapsiyor(b, s) for k in ipucu_bulunanlar):
            out.append(i)
    return out


def olc(ent: pd.DataFrame, sent: pd.DataFrame) -> list[dict]:
    ipuclari, sonlandirici = C.ipuclarini_kur()
    onc = [i for i in ipuclari if i.bolum == "belirsizlik_oncelikli"]
    tek = [i for i in ipuclari if i.bolum == "teknik_cekince"]
    ardil = [i for i in ipuclari if i.bolum == "negasyon" and i.yon == "geri"]

    ent_g = {k: v[["char_start", "char_end", "assertion", "entity_type"]].values
             for k, v in ent.groupby(ANAHTAR)}
    cum = {tuple(k): (t, cb) for k, t, cb
           in zip(sent[ANAHTAR].values, sent.text, sent.char_start)}

    # sayaclar
    k11 = {"kapsanan": 0, "absent": 0}
    k12 = {"kapsanan": 0, "absent": 0, "bagimsiz_negasyon_calisan": 0}
    k13 = {"cumle": 0, "ikinci_absent": 0}
    k15 = {"cumle": 0, "en_az_bir_absent": 0}
    ornek = {"k11": [], "k12": [], "k13": [], "k15": []}

    KOORD = re.compile(r"\bno\b[^.;]{0,60}\bor\b", re.I)

    for k, (metin, cb) in cum.items():
        v = ent_g.get(k)
        if v is None:
            continue
        bulunan = C.ipuclari_bul(metin, ipuclari, sonlandirici)

        # ---- K11: cannot be excluded kapsamindaki varlik 'absent' OLMAMALI ----
        b_onc = [x for x in bulunan if x.ipucu.bolum == "belirsizlik_oncelikli"]
        for i in _kapsayan_varliklar(metin, cb, v, b_onc):
            k11["kapsanan"] += 1
            if v[i][2] == "absent":
                k11["absent"] += 1
                if len(ornek["k11"]) < 3:
                    ornek["k11"].append(metin[:110])

        # ---- K12: teknik cekince TEK BASINA 'absent' uretmemeli ----
        # ILK OLCUM YANLISTI: "teknik ifadenin span'i icine dusen varlik" diye
        # sormustum, paydasi SIFIR cikti - teknik ifade bir FIIL obegi
        # ("could not be evaluated"), varliklar onun disinda durur.
        # Dogru soru: teknik cekince VAR ama bagimsiz negasyon YOK olan
        # cumlelerde hicbir varlik 'absent' olmamali.
        b_tek = [x for x in bulunan if x.ipucu.bolum == "teknik_cekince"]
        b_neg_hepsi = [x for x in bulunan if x.ipucu.bolum == "negasyon"]
        b_neg_bagimsiz = [x for x in b_neg_hepsi
                          if not any(t.bas <= x.bas and x.son <= t.son for t in b_tek)]
        if b_tek and not b_neg_bagimsiz:
            for r in v:
                k12["kapsanan"] += 1
                if r[2] == "absent":
                    k12["absent"] += 1
                    if len(ornek["k12"]) < 3:
                        ornek["k12"].append(metin[:110])
        if b_tek and b_neg_bagimsiz and any(r[2] == "absent" for r in v):
            k12["bagimsiz_negasyon_calisan"] += 1

        # ---- K13: 'no X or Y' -> IKINCI gozlem de absent olmali ----
        if KOORD.search(metin):
            goz = [r for r in v if r[3] == "observation"]
            if len(goz) >= 2:
                k13["cumle"] += 1
                ikinci = sorted(goz, key=lambda r: r[0])[1]
                if ikinci[2] == "absent":
                    k13["ikinci_absent"] += 1
                elif len(ornek["k13"]) < 3:
                    ornek["k13"].append(metin[:110])

        # ---- K15: YALNIZCA ardil ipucu tasiyan cumlede absent yakalandi mi ----
        b_ardil = [x for x in bulunan if x.ipucu.bolum == "negasyon"
                   and x.ipucu.yon == "geri"]
        b_ileri = [x for x in bulunan if x.ipucu.bolum == "negasyon"
                   and x.ipucu.yon == "ileri"]
        if b_ardil and not b_ileri:
            k15["cumle"] += 1
            if any(r[2] == "absent" for r in v):
                k15["en_az_bir_absent"] += 1
            elif len(ornek["k15"]) < 3:
                ornek["k15"].append(metin[:110])

    # ---- K14: assertion_cue dolu mu (tum korpus) ----
    g = ent[ent.assertion.isin(["absent", "uncertain"])]
    bos = int((g.assertion_cue.isna() |
               (g.assertion_cue.astype(str).str.strip() == "")).sum())

    def oran(pay, payda):
        return 100 * pay / payda if payda else float("nan")

    return [
        {"kod": "K11", "ad": "'cannot be excluded' kapsamindaki varlik 'absent' DEGIL",
         "esik": 100.0, "deger": oran(k11["kapsanan"] - k11["absent"], k11["kapsanan"]),
         "payda": k11["kapsanan"], "ihlal": k11["absent"], "ornek": ornek["k11"]},
        {"kod": "K12", "ad": "teknik cekince TEK BASINA 'absent' uretmiyor (bagimsiz negasyon yokken)",
         "esik": 100.0, "deger": oran(k12["kapsanan"] - k12["absent"], k12["kapsanan"]),
         "payda": k12["kapsanan"], "ihlal": k12["absent"], "ornek": ornek["k12"],
         "ek": f"ayni cumlede bagimsiz negasyon calisan: {k12['bagimsiz_negasyon_calisan']:,} cumle"},
        {"kod": "K13", "ad": "'no X or Y' -> ikinci gozlem de 'absent'",
         "esik": 90.0, "deger": oran(k13["ikinci_absent"], k13["cumle"]),
         "payda": k13["cumle"], "ihlal": k13["cumle"] - k13["ikinci_absent"],
         "ornek": ornek["k13"]},
        {"kod": "K14", "ad": "'absent'/'uncertain' satirlarda assertion_cue dolu",
         "esik": 100.0, "deger": oran(len(g) - bos, len(g)),
         "payda": len(g), "ihlal": bos, "ornek": []},
        {"kod": "K15", "ad": "YALNIZCA ardil ipuclu cumlede 'absent' yakalandi",
         "esik": 85.0, "deger": oran(k15["en_az_bir_absent"], k15["cumle"]),
         "payda": k15["cumle"], "ihlal": k15["cumle"] - k15["en_az_bir_absent"],
         "ornek": ornek["k15"]},
    ]


def main() -> None:
    OUTD.mkdir(exist_ok=True)
    ent, sent = yukle()
    print(f"girdi: {len(ent):,} varlik · {len(sent):,} cumle\n")
    sonuc = olc(ent, sent)

    sat = ["# TASK-13 / C1 — Yapısal Değişmezler", "",
           "**Altın açıklama gerektirmez.** Bu ölçütler *\"cevap doğru mu\"* diye "
           "sormaz, *\"sistem kendi kuralına uyuyor mu\"* diye sorar. Geçmeleri "
           "sistemin doğru olduğunu **göstermez**; geçmemeleri sistemin kendi "
           "tasarımına uymadığını gösterir — o kesin hatadır.", "",
           "Kesinlik, duyarlılık ve F1 (K4–K10) insan işaretlemesi bekliyor.", "",
           "| Kod | Ölçüt | Eşik | Sonuç | Payda | İhlal | Durum |",
           "|---|---|---|---|---|---|---|"]
    print(f"{'kod':<5} {'esik':>6} {'sonuc':>8} {'payda':>9} {'ihlal':>7}  durum")
    hepsi_gecti = True
    for s in sonuc:
        gecti = s["deger"] >= s["esik"] - 1e-9
        hepsi_gecti &= gecti
        d = "gecti" if gecti else "KALDI"
        d_md = "gecti" if gecti else "**KALDI**"
        print(f"{s['kod']:<5} {s['esik']:>5.0f}% {s['deger']:>7.1f}% "
              f"{s['payda']:>9,} {s['ihlal']:>7,}  {d}")
        sat.append(f"| **{s['kod']}** | {s['ad']} | {s['esik']:.0f}% | "
                   f"**{s['deger']:.1f}%** | {s['payda']:,} | {s['ihlal']:,} | {d_md} |")

    sat.append("")
    for s in sonuc:
        if s.get("ek"):
            sat.append(f"**{s['kod']} ek:** {s['ek']}")
        if s["ornek"]:
            sat.append(f"\n**{s['kod']} — ihlal örnekleri:**\n")
            for o in s["ornek"]:
                sat.append(f"> {o}")
    sat.append("")
    sat.append(f"**Sonuç: {'tüm değişmezler geçti' if hepsi_gecti else 'İHLAL VAR'}**")

    yol = OUTD / "task13_degismezler.md"
    yol.write_text("\n".join(sat) + "\n", encoding="utf-8")
    print(f"\nyazildi: reports/{yol.name}")
    if not hepsi_gecti:
        print("!! Ihlal var - kural seti duzeltilmeli (ayar kumesine bakarak).")


if __name__ == "__main__":
    main()
