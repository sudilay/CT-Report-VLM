"""BTB3D degerlendirmesi · kor ikinci degerlendirici paketi.

Elle okuma (`el_yargisi.csv`) TEK degerlendiricilidir. Bu betik, o yargiyi
bagimsiz olarak sinamak icin kor bir paket uretir.

KORLUK IKI KATMANLI:
  1. Paket, benim etiketlerimi ICERMEZ (anahtar ayri ve kapali dosyada).
  2. Her vakada hangi metnin HEKIM hangisinin BTB3D oldugu GIZLIDIR -
     iki metin `Metin-1` / `Metin-2` olarak rastgele sirayla verilir.
     Boylece degerlendirici "bu makine ciktisi" onyargisiyla etiketleyemez.

Cikti (karantina dizinine):
  KOR_paket.csv        doldurulacak tablo (80 satir = 40 vaka x 2 metin)
  KOR_TALIMAT.md       etiketleme talimati
  .KOR_anahtar.csv     hangi metin hangi kaynak + benim etiketlerim (KAPALI)

Kullanim:
    python scripts/77_btb3d_kor_paket.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
KARANTINA = KOK / "outputs/btb3d_ctrate_muhurlu"
HAM = KOK / "data/raw/btb3d-ctrate-500-reports/generated_reports_500.csv"
ORNEK = KARANTINA / "el_ornekleme.json"
EL = KARANTINA / "el_yargisi.csv"

TOHUM = 20260910

KIS = ["MM", "AWC", "CM", "PCE", "CAWC", "HH", "LAP", "EMP", "ATL",
       "LN", "LO", "PFS", "PLE", "MAP", "PBT", "CONS", "BRE", "IST"]

TANIM = [
    ("MM", "Medical material", "Kateter, stent, pacemaker, cerrahi klips, protez, dren"),
    ("AWC", "Arterial wall calcification", "Aort / pulmoner arter / vena kava duvarinda kalsifikasyon veya ateroma plagi (koroner HARIC)"),
    ("CM", "Cardiomegaly", "Kalp buyuklugu ARTMIS denmis. 'Kalp boyutu normal' NEGATIFTIR"),
    ("PCE", "Pericardial effusion", "Perikardiyal efuzyon veya kalinlasma"),
    ("CAWC", "Coronary artery wall calcification", "KORONER arterlerde kalsifikasyon / ateroma plagi"),
    ("HH", "Hiatal hernia", "Hiatal herni (kayici, mikst)"),
    ("LAP", "Lymphadenopathy", "PATOLOJIK boyutta / buyumus lenf nodu. 'Patolojik boyutta lenf nodu saptanmadi' NEGATIFTIR"),
    ("EMP", "Emphysema", "Amfizem, amfizematoz degisiklik, bul"),
    ("ATL", "Atelectasis", "Atelektazi (bant, lineer, subsegmental, kompresyon)"),
    ("LN", "Lung nodule", "AKCIGERDE nodul veya kitle. Karaciger/tiroid/bobrek/meme nodulu SAYILMAZ"),
    ("LO", "Lung opacity", "Buzlu cam, infiltrasyon, konsolidasyon, dansite artisi - akcigerde"),
    ("PFS", "Pulmonary fibrotic sequela", "Fibrozis, sekel degisiklik, retikulasyon, plevroparankimal sekel, bal petegi"),
    ("PLE", "Pleural effusion", "PLEVRAL efuzyon veya kalinlasma (perikardiyal DEGIL)"),
    ("MAP", "Mosaic attenuation pattern", "Mozaik atenuasyon / mozaik dansite farki"),
    ("PBT", "Peribronchial thickening", "Peribronsiyal veya bronsiyal duvar kalinlasmasi"),
    ("CONS", "Consolidation", "Konsolidasyon (hava bronkogrami olsun olmasin)"),
    ("BRE", "Bronchiectasis", "Bronsektazi (silindirik, kistik, traksiyonel)"),
    ("IST", "Interlobular septal thickening", "Interlobuler septal kalinlasma"),
]

TALIMAT = """# Kör değerlendirici talimatı · BTB3D / CT-RATE

Elinizde **80 göğüs BT raporu metni** var (40 vaka × 2 metin). Her vaka için
iki metin verilmiştir: `Metin-1` ve `Metin-2`. **Hangisinin hekim tarafından
yazıldığı, hangisinin bir model tarafından üretildiği size söylenmemiştir ve
sıraları rastgeledir.** Bu bilinçlidir — iki metni de aynı ölçütle
değerlendirmenizi istiyoruz.

## Göreviniz

Her satır için 18 sütunu **0** veya **1** ile doldurun:

- **1** = bu metin, o bulgunun hastada **var olduğunu** söylüyor
- **0** = söylemiyor, ya da **yok olduğunu** söylüyor

## En önemli kural: negasyon

Bir kelimenin metinde geçmesi, o bulgunun var olduğu anlamına **gelmez.**
Radyoloji raporlarının çoğu cümlesi olumsuzdur.

| Cümle | Doğru etiket |
| :-- | :-- |
| "Plevral efüzyon saptanmadı" | PLE = **0** |
| "Her iki akciğerde nodül izlenmedi" | LN = **0** |
| "Sağ üst lobda 6 mm nodül izlenmektedir" | LN = **1** |
| "Patolojik boyutta lenf nodu saptanmadı" | LAP = **0** |
| "Mediastende 15 mm kısa aksli lenf nodu" | LAP = **1** |

**Belirsiz ifadeler 0 sayılır**: "ekarte edilemez", "şüphelidir", "olabilir".
Bulgu açıkça tarif edilmişse 1, yalnızca ihtimal olarak anılmışsa 0.

**Anatomik kapsam**: sınıflar toraksa ilişkindir. Karaciğerde kitle, tiroidde
nodül, böbrekte kist → ilgili akciğer/toraks sınıfı **0**.

## Ek alan: `malignite`

Her metin için ayrıca tek bir değer:

| Değer | Ne zaman |
| :-- | :-- |
| `yok` | Malignite/kitle/tümör hiç geçmiyor ya da tamamı olumsuzlanmış |
| `benign` | Lezyon var ama açıkça benign nitelenmiş (kalsifik granülom, kist) |
| `belirsiz` | Toraksta nodül/kitle var, malignite dili yok |
| `supheli` | Şüpheli nitelenmiş (spiküle, düzensiz kontur, "malignite açısından") |
| `malign` | Güncel tetkikte malignite/metastaz açıkça tarif edilmiş |
| `oykude` | Malignite yalnız öykü cümlesinde; güncel lezyon tarif edilmemiş |

## Yasaklar

- Bu kohort için üretilmiş **başka hiçbir dosyaya bakmayın**: etiket tabloları,
  çıkarım çıktıları, metrik dosyaları, değerlendirme raporu.
- İki metni **birbirine göre** değil, her birini **kendi başına** etiketleyin.
  Metin-1'de bir bulgu görmeniz Metin-2'yi etkilememelidir.
- Emin olamadığınız satırı boş bırakmayın; en iyi yargınızı yazın.

## ⛔ İçerik mührü

Bu paketteki rapor metinleri mühürlü bir değerlendirme havuzundan gelmektedir.
Yalnızca bu tabloyu doldurmak için kullanın; **şema, sözlük, kural veya eşik
geliştirmesine yansıtmayın** ve başka bir göreve taşımayın.

## Teslim

`KOR_paket.csv` dosyasını doldurup aynı adla kaydedin. Sütun adlarını ve satır
sırasını değiştirmeyin.
"""


def main() -> None:
    ham = pd.read_csv(HAM).set_index("VolumeName")
    orn = json.loads(ORNEK.read_text(encoding="utf-8"))
    el = pd.read_csv(EL)

    vakalar = [("R", v) for v in orn["rastgele30"]] + \
              [("M", v) for v in orn["malignite10"]]
    rng = np.random.default_rng(TOHUM)

    paket, anahtar = [], []
    for i, (kume, vol) in enumerate(vakalar, 1):
        vid = f"{kume}{i if kume == 'R' else i - 30:02d}"
        r = ham.loc[vol]
        metinler = {
            "HEKIM": re.sub(r"\s+", " ",
                            f"{r.Ground_Truth_Findings} {r.Ground_Truth_Impressions}").strip(),
            "BTB3D": re.sub(r"\s+", " ", str(r.Generated_Report)).strip(),
        }
        sira = ["HEKIM", "BTB3D"]
        if rng.random() < 0.5:
            sira.reverse()

        for slot, kaynak in enumerate(sira, 1):
            paket.append({"vaka_id": vid, "metin_no": f"Metin-{slot}",
                          "metin": metinler[kaynak],
                          **{k: "" for k in KIS}, "malignite": ""})
            benim = el[(el.rapor == vid) &
                       (el.kaynak == ("GT" if kaynak == "HEKIM" else "GEN"))]
            anahtar.append({
                "vaka_id": vid, "metin_no": f"Metin-{slot}",
                "gercek_kaynak": kaynak, "VolumeName": vol,
                **({k: int(benim.iloc[0][k]) for k in KIS}
                   if len(benim) else {k: "" for k in KIS}),
            })

    p = pd.DataFrame(paket)
    a = pd.DataFrame(anahtar)

    KARANTINA.mkdir(parents=True, exist_ok=True)
    yol = KARANTINA / "KOR_paket.csv"
    p.to_csv(yol, index=False, encoding="utf-8")
    a.to_csv(KARANTINA / ".KOR_anahtar.csv", index=False, encoding="utf-8")
    (KARANTINA / "KOR_TALIMAT.md").write_text(
        TALIMAT + "\n\n## Sınıf tanımları\n\n"
        "| Kod | Sınıf | Ne zaman 1 |\n| :-- | :-- | :-- |\n"
        + "\n".join(f"| `{k}` | {ad} | {aciklama} |" for k, ad, aciklama in TANIM)
        + "\n", encoding="utf-8")

    sha = hashlib.sha256(yol.read_bytes()).hexdigest()
    (KARANTINA / "KOR_paket_kilidi.json").write_text(json.dumps({
        "tohum": TOHUM, "vaka": len(vakalar), "satir": len(p),
        "sha256_paket": sha,
        "korluk": ["anahtar ayri dosyada", "kaynak sirasi vaka basina rastgele"],
        "sinif": KIS,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    hekim_once = sum(1 for i in range(0, len(a), 2)
                     if a.iloc[i].gercek_kaynak == "HEKIM")
    print(f"paket   : {yol}")
    print(f"satir   : {len(p)} ({len(vakalar)} vaka x 2 metin)")
    print(f"korluk  : Metin-1 {hekim_once}/{len(vakalar)} vakada hekim "
          f"({100*hekim_once/len(vakalar):.0f}% - dengeli olmali)")
    print(f"sha256  : {sha}")
    print(f"talimat : {KARANTINA / 'KOR_TALIMAT.md'}")
    print(f"anahtar : {KARANTINA / '.KOR_anahtar.csv'}  (KAPALI - paylasilmaz)")


if __name__ == "__main__":
    main()
