"""NLST kohortu · uc sistem icin kor degerlendirme paketi.

CT-RATE'ten farkli olarak NLST'de INSAN YAZIMI REFERANS RAPOR YOKTUR.
Uc kaynak da model ciktisidir. Bu yuzden kor paket "hangisi hekim" degil,
"uc sistemden hangisi hangi bulguyu bildiriyor" sorusunu sorar.

KORLUK UC KATMANLI:
  1. Paket otomatik cikarim etiketlerini ICERMEZ.
  2. Sistem adlari gizlidir: her vakada uc metin `Sistem-A/B/C` olarak,
     sirasi VAKA BASINA rastgele verilir. Ayni sistem farkli vakalarda
     farkli harfe dusar, boylece degerlendirici harften ogrenemez.
  3. KANSER ETIKETI verilmez. Degerlendirici hangi hastanin kanser
     oldugunu bilmez, yoksa metni ona gore okumaya egilim duyar.

Ornekleme: kanser pozitif PID'ler seyrek oldugu icin katmanli secim yapilir;
tani <= 1 yil olan pozitiflerin tamami havuza girer.

⛔ KAPSAM: yalniz train + dev.

Kullanim:
    python scripts/81_nlst_kor_paket.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
DIZIN = KOK / "outputs/btb3d_nlst"
BULGU = DIZIN / "nlst_uclu_bulgular.parquet"
BTB3D = KOK / "data/raw/btb3d-nlst-2965-reports/generated_reports_nlst_2965.csv"
ASTRA = KOK / "astra_radiology_reports_with_labels_all.xlsx"
MEDMO = KOK / "medmo_radiology_reports_with_labels.xlsx"

TOHUM = 20260910
N_POZ_ERKEN = 15     # tani <= 1 yil
N_POZ_GEC = 5        # tani > 1 yil
N_NEG = 20

KIS = ["MM", "AWC", "CM", "PCE", "CAWC", "HH", "LAP", "EMP", "ATL",
       "LN", "LO", "PFS", "PLE", "MAP", "PBT", "CONS", "BRE", "IST"]

TANIM = [
    ("MM", "Tibbi materyal", "Kateter, stent, pacemaker, cerrahi klips, protez, dren"),
    ("AWC", "Arteryel duvar kalsifikasyonu", "Aort / pulmoner arter duvarinda kalsifikasyon veya ateroma (koroner HARIC)"),
    ("CM", "Kardiyomegali", "Kalp buyuklugu ARTMIS denmis. 'Kalp boyutu normal' NEGATIFTIR"),
    ("PCE", "Perikardiyal efuzyon", "Perikardiyal efuzyon veya kalinlasma"),
    ("CAWC", "Koroner duvar kalsifikasyonu", "KORONER arterlerde kalsifikasyon / ateroma"),
    ("HH", "Hiatal herni", "Hiatal herni"),
    ("LAP", "Lenfadenopati", "PATOLOJIK boyutta lenf nodu. 'Patolojik boyutta saptanmadi' NEGATIFTIR"),
    ("EMP", "Amfizem", "Amfizem, amfizematoz degisiklik, bul"),
    ("ATL", "Atelektazi", "Atelektazi (bant, lineer, subsegmental, kompresyon)"),
    ("LN", "Akciger nodulu", "AKCIGERDE nodul veya kitle. Karaciger/tiroid/bobrek nodulu SAYILMAZ"),
    ("LO", "Akciger opasitesi", "Buzlu cam, infiltrasyon, konsolidasyon, dansite artisi"),
    ("PFS", "Pulmoner fibrotik sekel", "Fibrozis, sekel degisiklik, retikulasyon, bal petegi"),
    ("PLE", "Plevral efuzyon", "PLEVRAL efuzyon veya kalinlasma (perikardiyal DEGIL)"),
    ("MAP", "Mozaik atenuasyon", "Mozaik atenuasyon / mozaik dansite farki"),
    ("PBT", "Peribronsiyal kalinlasma", "Peribronsiyal veya bronsiyal duvar kalinlasmasi"),
    ("CONS", "Konsolidasyon", "Konsolidasyon"),
    ("BRE", "Bronsektazi", "Bronsektazi"),
    ("IST", "Interlobuler septal kalinlasma", "Interlobuler septal kalinlasma"),
]

TALIMAT = """# Kör değerlendirici talimatı · NLST akciğer kanseri tarama kohortu

Elinizde **120 göğüs BT raporu metni** var (40 vaka × 3 metin). Her vaka için
üç metin verilmiştir: `Sistem-A`, `Sistem-B`, `Sistem-C`.

Üç metnin **üçü de aynı BT görüntüsü için yazılmıştır**. Hangi metnin hangi
sistemden geldiği size söylenmemiştir ve harf sırası her vakada yeniden
karıştırılmıştır: bir vakadaki `Sistem-A` ile başka bir vakadaki `Sistem-A`
aynı sistem olmak zorunda değildir. Harflerden çıkarım yapmaya çalışmayın.

Ayrıca hastaların kanser durumu size verilmemiştir. Bu bilinçlidir.

## Görev bağlamı

Bu bir **akciğer kanseri tarama** kohortudur: düşük doz BT ile taranan,
çoğu sağlıklı olan yüksek riskli hastalar. Tanısal bir toraks BT'sinden farklı
olarak burada asıl soru şüpheli bir pulmoner lezyon bulunup bulunmadığıdır.

## Göreviniz

Her satır için 18 bulgu sütununu **0** veya **1** ile doldurun:

- **1** = bu metin, o bulgunun hastada **var olduğunu** söylüyor
- **0** = söylemiyor, ya da **yok olduğunu** söylüyor

## En önemli kural: negasyon

Bir kelimenin metinde geçmesi o bulgunun var olduğu anlamına **gelmez.**

| Cümle | Doğru etiket |
| :-- | :-- |
| "Her iki akciğerde nodül izlenmedi" | LN = **0** |
| "Sağ üst lobda 6 mm nodül izlenmektedir" | LN = **1** |
| "Patolojik boyutta lenf nodu saptanmadı" | LAP = **0** |
| "Plevral efüzyon saptanmadı" | PLE = **0** |

**Belirsiz ifadeler 0 sayılır**: "ekarte edilemez", "şüphelidir", "olabilir".

**Anatomik kapsam toraks**: karaciğerde kitle, tiroidde nodül, böbrekte kist
gibi bulgular ilgili akciğer sınıfını **1 yapmaz**.

## Ek alanlar

**`malignite`** (tek değer):

| Değer | Ne zaman |
| :-- | :-- |
| `yok` | Malignite/kitle/nodül hiç geçmiyor ya da tamamı olumsuzlanmış |
| `benign` | Lezyon var ama açıkça benign nitelenmiş (kalsifik granülom, kist) |
| `belirsiz` | Toraksta nodül/kitle var, malignite dili yok |
| `supheli` | Şüpheli nitelenmiş (spiküle, düzensiz kontur, "malignite açısından") |
| `malign` | Malignite/metastaz açıkça tarif edilmiş |
| `oykude` | Malignite yalnız öykü cümlesinde; güncel lezyon tarif edilmemiş |

**`takip_gerekir`** (tek değer): bu metni okuyan bir hekim hastayı ileri
tetkike veya kısa aralıklı takibe çağırır mıydı? `evet` / `hayir`.

**`anlamsiz_icerik`** (tek değer): metinde toraks BT'sinde karşılığı olmayan,
uydurma ya da anlamsız ifade var mı? `evet` / `hayir`. Varsa `not` sütununa
kısaca yazın.

## Yasaklar

- Bu kohorta ait **başka hiçbir dosyaya bakmayın**: etiket tabloları, çıkarım
  çıktıları, metrik dosyaları, değerlendirme raporları.
- Üç metni **birbirine göre** değil, her birini **kendi başına** etiketleyin.
  Bir metinde bulgu görmeniz diğerlerini etkilememelidir.
- Hangi sistemin hangisi olduğunu tahmin etmeye çalışmayın; bu görevin parçası
  değildir ve yargınızı bozar.

## Teslim

Doldurduğunuz tabloyu `KOR_paket_nlst_<isim>.csv` olarak kaydedin. Sütun
adlarını ve satır sırasını değiştirmeyin, hiçbir hücreyi boş bırakmayın.
"""


def main() -> None:
    d = pd.read_parquet(BULGU)
    rng = np.random.default_rng(TOHUM)

    # --- katmanli PID secimi ------------------------------------------------
    pid = d.groupby("pid").agg({"label": "max", "followup_yil": "min"})
    erken = pid[(pid.label == 1) & (pid.followup_yil <= 1)].index.to_numpy()
    gec = pid[(pid.label == 1) & (pid.followup_yil > 1)].index.to_numpy()
    neg = pid[pid.label == 0].index.to_numpy()
    sec = np.concatenate([
        rng.choice(erken, min(N_POZ_ERKEN, len(erken)), replace=False),
        rng.choice(gec, min(N_POZ_GEC, len(gec)), replace=False),
        rng.choice(neg, N_NEG, replace=False)])

    # Her PID'den TEK seri. Kanserli PID'de kanser ETIKETLI seri secilir:
    # PID etiketi max kuraliyla verildigi icin ayni hastanin bazi serileri
    # negatif olabilir; korlemede hastaligin gorunur oldugu seri istenir.
    havuz = d[d.pid.isin(sec)].sort_values(["pid", "label", "key"],
                                           ascending=[True, False, True])
    alt = havuz.groupby("pid").head(1)
    alt = alt.sample(frac=1.0, random_state=TOHUM).reset_index(drop=True)

    b = pd.read_csv(BTB3D).set_index("key")
    a = pd.read_excel(ASTRA, usecols=["Seri_Anahtari", "Radyoloji_Raporu"])
    m = pd.read_excel(MEDMO, usecols=["series_key", "full_report"])
    A = dict(zip(a.Seri_Anahtari.astype(str), a.Radyoloji_Raporu.fillna("")))
    M = dict(zip(m.series_key.astype(str), m.full_report.fillna("")))

    # Sistem harflerini DENGELI dagit: alti olasi siralamanin her biri
    # esit sayida kullanilir, sonra karistirilir. Rastgele atama 40 vakada
    # belirgin dengesizlik uretebiliyordu (olculdu: 20/11/9).
    import itertools
    perm = list(itertools.permutations(["BTB3D", "ASTRA", "MEDMO"]))
    siralar = [list(perm[j % 6]) for j in range(len(alt))]
    rng.shuffle(siralar)

    paket, anahtar = [], []
    for i, r in enumerate(alt.itertuples(index=False), 1):
        vid = f"N{i:02d}"
        metinler = {"BTB3D": str(b.loc[r.key, "Generated_Report"]),
                    "ASTRA": str(A[r.key]), "MEDMO": str(M[r.key])}
        sira = siralar[i - 1]
        for harf, sistem in zip("ABC", sira):
            paket.append({"vaka_id": vid, "sistem_kod": f"Sistem-{harf}",
                          "metin": re.sub(r"\s+", " ", metinler[sistem]).strip(),
                          **{k: "" for k in KIS},
                          "malignite": "", "takip_gerekir": "",
                          "anlamsiz_icerik": "", "not": ""})
            anahtar.append({"vaka_id": vid, "sistem_kod": f"Sistem-{harf}",
                            "gercek_sistem": sistem, "key": r.key,
                            "kanser": int(r.label),
                            "followup_yil": int(r.followup_yil)})

    p = pd.DataFrame(paket)
    yol = DIZIN / "KOR_paket_nlst.csv"
    DIZIN.mkdir(parents=True, exist_ok=True)
    p.to_csv(yol, index=False, encoding="utf-8")
    pd.DataFrame(anahtar).to_csv(DIZIN / ".KOR_anahtar_nlst.csv", index=False,
                                 encoding="utf-8")
    (DIZIN / "KOR_TALIMAT_nlst.md").write_text(
        TALIMAT + "\n\n## Sınıf tanımları\n\n"
        "| Kod | Sınıf | Ne zaman 1 |\n| :-- | :-- | :-- |\n"
        + "\n".join(f"| `{k}` | {ad} | {ac} |" for k, ad, ac in TANIM) + "\n",
        encoding="utf-8")

    ank = pd.DataFrame(anahtar)
    sha = hashlib.sha256(yol.read_bytes()).hexdigest()
    (DIZIN / "KOR_paket_nlst_kilidi.json").write_text(json.dumps({
        "tohum": TOHUM, "vaka": len(alt), "satir": len(p), "sha256_paket": sha,
        "katman": {"pozitif_tani_1yil": int((ank.groupby('vaka_id').first().kanser.eq(1)
                                             & ank.groupby('vaka_id').first().followup_yil.le(1)).sum()),
                   "pozitif_gec": int((ank.groupby('vaka_id').first().kanser.eq(1)
                                       & ank.groupby('vaka_id').first().followup_yil.gt(1)).sum()),
                   "negatif": int(ank.groupby('vaka_id').first().kanser.eq(0).sum())},
        "korluk": ["cikarim etiketleri yok", "sistem adlari gizli ve vaka basina karisik",
                   "kanser etiketi verilmiyor"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    ilk = ank.groupby("vaka_id").first()
    print(f"paket   : {yol}")
    print(f"satir   : {len(p)} ({len(alt)} vaka x 3 sistem)")
    print(f"katman  : {int((ilk.kanser==1).sum())} kanser pozitif "
          f"({int(((ilk.kanser==1)&(ilk.followup_yil<=1)).sum())} tanisi <=1 yil), "
          f"{int((ilk.kanser==0).sum())} negatif")
    print("  Sistem-A dagilimi:",
          dict(ank[ank.sistem_kod == "Sistem-A"].gercek_sistem.value_counts()))
    print(f"sha256  : {sha}")
    print(f"talimat : {DIZIN / 'KOR_TALIMAT_nlst.md'}")
    print(f"anahtar : {DIZIN / '.KOR_anahtar_nlst.csv'}  (KAPALI)")


if __name__ == "__main__":
    main()
