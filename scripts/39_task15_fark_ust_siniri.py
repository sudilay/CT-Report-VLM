"""TASK-15 · Altin-bagimsiz A1 fark ust siniri.

Soru: kanonik altin uretilemedi. HERHANGI bir altin standarda karsi
puanlansaydi, TR ve EN-genel kollarinin A1 F1 farki EN FAZLA ne olabilirdi?

Mantik: iki kol AYNI altina karsi puanlanir. Ayrismadiklari her belge-kavramda
puanlari da aynidir; dolayisiyla F1 farki ayrisma miktariyla matematiksel
olarak sinirlidir - altinin ne oldugu bilinmeden.

Altin G'nin elemanlari dort kumeye ayrilir:
    c = ortak kesisimden dogru olanlar      (0 <= c <= ORTAK)
    a = yalniz-TR'den dogru olanlar         (0 <= a <= YALNIZ_TR)
    b = yalniz-EN'den dogru olanlar         (0 <= b <= YALNIZ_EN)
    m = iki sistemin de kacirdigi           (m >= 0)
    |G| = c + a + b + m

    TP_TR = c + a        TP_EN = c + b

Altin BILINMIYOR, o yuzden butun uygun (c, a, b, m) taranir ve azami fark alinir.

Girdi sayilari `scripts/31_task15_kol_karsilastirma.py` ciktisindandir
(dev, 46 belge, dondurulmus sozluk). Rapor: `reports/task15_dondurma.md` §3.

Bu betik veri okumaz, model calistirmaz, `test` bolumune dokunmaz.
"""

from __future__ import annotations

# scripts/31 ciktisi - dev, 46 belge, dondurulmus sozluk (2026-09-03)
ORTAK = 1039
YALNIZ_TR = 18
YALNIZ_EN = 22
P_TR = ORTAK + YALNIZ_TR  # 1057
P_EN = ORTAK + YALNIZ_EN  # 1061

KABUL_MARJI = 5.0  # docs/19 §5


def f1(tp: int, tahmin: int, altin: int) -> float:
    if tp == 0 or tahmin == 0 or altin == 0:
        return 0.0
    kesinlik = tp / tahmin
    duyarlilik = tp / altin
    return 2 * kesinlik * duyarlilik / (kesinlik + duyarlilik)


def azami_fark(c_araligi, m_araligi) -> tuple[float, tuple[int, int, int, int, int]]:
    """Verilen aralikta azami |F1_TR - F1_EN| ve onu ureten parametreler."""
    en_iyi = (0.0, (0, 0, 0, 0, 0))
    for c in c_araligi:
        for a in (0, YALNIZ_TR):
            for b in (0, YALNIZ_EN):
                for m in m_araligi:
                    g = c + a + b + m
                    if g == 0:
                        continue
                    fark = abs(f1(c + a, P_TR, g) - f1(c + b, P_EN, g))
                    if fark > en_iyi[0]:
                        en_iyi = (fark, (c, a, b, m, g))
    return en_iyi


def main() -> None:
    print("=" * 68)
    print("A1 - TR vs EN-genel - altin-bagimsiz F1 farki ust siniri")
    print("=" * 68)
    print(
        f"ortak {ORTAK} - yalniz TR {YALNIZ_TR} - yalniz EN {YALNIZ_EN}"
        f" - simetrik fark {YALNIZ_TR + YALNIZ_EN}"
    )
    print(f"kabul marji (docs/19 §5): {KABUL_MARJI:.1f} puan\n")

    print("--- 1. Gercekci bolge (ortak kesinlik %70-100, kacirma <= %25) ---")
    for kesinlik in (1.00, 0.90, 0.80, 0.70):
        c = round(ORTAK * kesinlik)
        m_ust = round((c + YALNIZ_TR + YALNIZ_EN) * 0.25)
        adim = max(1, m_ust // 20)
        fark, _ = azami_fark([c], range(0, m_ust + 1, adim))
        print(f"  ortak kesinlik %{kesinlik * 100:3.0f} (c={c:4})"
              f"  ->  azami fark = {fark * 100:.2f} puan")

    print("\n--- 2. Mutlak en kotu hal (hicbir varsayim yok) ---")
    fark, (c, a, b, m, g) = azami_fark(range(0, ORTAK + 1, 10), range(0, 400, 20))
    print(f"  azami fark = {fark * 100:.2f} puan"
          f"   (c={c}, a={a}, b={b}, m={m}, |G|={g})")
    print("  not: bu nokta altinin ortak bulgularin neredeyse tamamini")
    print("       reddettigi, yani IKI sistemin de coktugu senaryodur.")

    print("\n--- 3. Kaba analitik sinir ---")
    for g in (800, 900, 1000, 1100, 1200):
        print(f"  |G|={g:5}  ->  duyarlilik farki <= "
              f"{max(YALNIZ_TR, YALNIZ_EN) / g * 100:.2f} puan")
    print(f"\n  kesinlik farki <= ~{max(YALNIZ_TR, YALNIZ_EN) / P_TR * 100:.2f}"
          f" puan  (tahmin buyuklugu ~{P_TR}-{P_EN})")

    print(f"\nHUKUM: azami fark {fark * 100:.2f} puan < kabul marji"
          f" {KABUL_MARJI:.1f} puan  ->  KARAR OLCUTU ALTIN OLMADAN SAGLANDI")


if __name__ == "__main__":
    main()
