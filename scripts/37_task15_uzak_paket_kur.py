# -*- coding: utf-8 -*-
"""TASK-15 · UZAK GPU paketini kurar - kendi kendine yeten, tekrar uretilebilir.

NEDEN BETIK: Paket elle kopyalanirsa neyin girdigi/girmedigi kayitsiz kalir.
Bu betik paketi HER SEFERINDE ayni sekilde uretir ve icindekilerin SHA-256'sini
yazar; uzak makinedeki dosyanin yerel dosyayla ayni oldugu kanitlanabilir.

PAKETE GIREN:
  * uc kolun `dev` metinleri, {document_id, order, text} bicimine NORMALLESTIRILMIS
  * kapali 144'luk kavram ENVANTERI - YALNIZ KIMLIKLER
  * dondurulmus istem
  * sozlesme dogrulayici kod (task15.py) + ikincil model adaptoru
  * kosu betigi, gereksinimler, OKU_BENI, SOZLESME

PAKETE GIRMEYEN - ve neden:
  * ALTIN ETIKETLER      -> docs/19 §4.2; model altin gormez
  * `test` bolumu        -> kilitli
  * SOZLUK DESENLERI     -> model sozlugu gormemeli; gorsse birincil sistemi
                            taklit eder ve ikincil dogrulama anlamini yitirir
  * birincil sistem cikti -> ayni sebep
  * MedGemma kodu/istemi  -> aday degil (docs/19 §2) ve kol dusuruldu (D63)
  * Google/Opus-MT ceviri kodu -> ceviri BITTI; uzak makinede ceviri yapilmaz

Kullanim:
  .venv/Scripts/python.exe scripts/37_task15_uzak_paket_kur.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

import yaml  # noqa: E402

HEDEF = KOK / "outputs" / "task15" / "TASK15_Model_Paketi"
MODEL_REVIZYONLARI = {
    "Qwen/Qwen3.5-4B": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
    "CohereLabs/aya-expanse-8b": "5062468bf9bc0c6035fd64e06274333ec127d980",
}

# kol -> (kaynak dosya, metin alani)
KOLLAR = {
    "tr": (KOK / "outputs/task15/dev_packages_v2/translation_dev.jsonl", "text_tr"),
    "en_genel": (KOK / "outputs/task15/ceviri_dev/en_genel_dev.jsonl", "text"),
    "en_ucuz": (KOK / "outputs/task15/ceviri_dev/en_ucuz_dev.jsonl", "text"),
}


def sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with yol.open("rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def kollari_normallestir(hedef: Path) -> dict:
    """Uc kolu ayni sozlesmeye getirir ve KIMLIK/SIRA esligini DOGRULAR.

    Kritik: uc kol ayni belgeleri ayni sirada icermezse kollar arasi
    karsilastirma anlamsizlasir. Esitsizlik burada durdurulur.
    """
    hedef.mkdir(parents=True, exist_ok=True)
    kimlikler: dict[str, list[str]] = {}
    bilgi = {}
    for kol, (kaynak, alan) in KOLLAR.items():
        if not kaynak.exists():
            raise SystemExit(f"DURDU: kaynak yok: {kaynak}")
        kayitlar = [json.loads(s) for s in kaynak.open(encoding="utf-8") if s.strip()]
        cikti = hedef / f"{kol}_dev.jsonl"
        with cikti.open("w", encoding="utf-8", newline="\n") as f:
            for sira, k in enumerate(kayitlar):
                if k["order"] != sira:
                    raise SystemExit(f"DURDU: {kol} sirasi kesintisiz degil")
                metin = k[alan]
                if not isinstance(metin, str) or not metin.strip():
                    raise SystemExit(f"DURDU: {kol}/{k['document_id']} bos metin")
                f.write(
                    json.dumps(
                        {
                            "document_id": k["document_id"],
                            "order": sira,
                            "text": metin,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        kimlikler[kol] = [k["document_id"] for k in kayitlar]
        bilgi[kol] = {
            "dosya": cikti.name,
            "belge_sayisi": len(kayitlar),
            "sha256": sha256(cikti),
            "kaynak": str(kaynak.relative_to(KOK)).replace("\\", "/"),
            "kaynak_sha256": sha256(kaynak),
        }
        print(f"  {kol:<9} {len(kayitlar):>3} belge -> {cikti.name}")

    ilk = kimlikler["tr"]
    for kol, liste in kimlikler.items():
        if liste != ilk:
            raise SystemExit(
                f"DURDU: {kol} kolunun belge kimlikleri/sirasi TR kolundan farkli. "
                "Kollar arasi karsilastirma bu haliyle gecersiz olur."
            )
    print(f"  OK - uc kol da ayni {len(ilk)} belgeyi ayni sirada iceriyor")
    return bilgi


def envanteri_yaz(hedef: Path) -> dict:
    """144 kavram KIMLIGINI yazar - DESENLER GIRMEZ.

    `load_inventory` `yuzeyler` anahtarini bekledigi icin ayni sekil korunur,
    ama her kavramin degeri BOS nesnedir. Boylece model envanteri gorur,
    sozlugu gormez.
    """
    hedef.mkdir(parents=True, exist_ok=True)
    kaynak = KOK / "configs" / "turkce_yuzeyler_taslak.yaml"
    kavramlar = sorted(
        yaml.safe_load(kaynak.read_text(encoding="utf-8"))["yuzeyler"]
    )
    if len(kavramlar) != 144:
        raise SystemExit(f"DURDU: envanter 144 olmali, bulunan {len(kavramlar)}")
    # Ingilizce sozlukle kimlik esligini DOGRULA - iki taraf ayni envanteri
    # kullanmiyorsa ikincil model hangi tarafi taklit ettigi belirsiz kalir.
    en: set[str] = set()
    for dosya in ("anatomi_sozlugu.yaml", "bulgu_sozlugu.yaml"):
        en |= set(
            yaml.safe_load(
                (KOK / "configs" / dosya).read_text(encoding="utf-8")
            )["kavramlar"]
        )
    if en != set(kavramlar):
        raise SystemExit(
            "DURDU: TR ve EN sozlukleri ayni kavram kumesini icermiyor: "
            f"yalniz TR={sorted(set(kavramlar)-en)} yalniz EN={sorted(en-set(kavramlar))}"
        )
    satirlar = [
        "# TASK-15 · IKINCIL MODEL kapali kavram envanteri - 144 kimlik",
        "#",
        "# ⚠ Bu dosyada YUZEY DESENI YOKTUR ve olmamalidir. Ikincil model",
        "#   birincil sistemin sozlugunu gormeden calisir; gorsse onu taklit",
        "#   eder ve bagimsiz dogrulama olmaktan cikar (docs/19 §3).",
        "#",
        "# Uretildi: scripts/37_task15_uzak_paket_kur.py",
        "",
        "yuzeyler:",
    ]
    satirlar += [f"  {k}: {{}}" for k in kavramlar]
    yol = hedef / "envanter_144.yaml"
    yol.write_text("\n".join(satirlar) + "\n", encoding="utf-8", newline="\n")
    print(f"  envanter  144 kavram -> {yol.name} (desen YOK)")
    return {"dosya": yol.name, "kavram_sayisi": 144, "sha256": sha256(yol)}


def kodu_kopyala(hedef: Path) -> dict:
    esleme = [
        (KOK / "src/radyovlm/__init__.py", hedef / "src/radyovlm/__init__.py"),
        (
            KOK / "src/radyovlm/evaluation/__init__.py",
            hedef / "src/radyovlm/evaluation/__init__.py",
        ),
        (
            KOK / "src/radyovlm/evaluation/task15.py",
            hedef / "src/radyovlm/evaluation/task15.py",
        ),
        (
            KOK / "src/radyovlm/evaluation/ikincil_model.py",
            hedef / "src/radyovlm/evaluation/ikincil_model.py",
        ),
        (
            KOK / "scripts/36_task15_ikincil_model.py",
            hedef / "scripts/36_task15_ikincil_model.py",
        ),
        (
            KOK / "configs/istem_ikincil_model_v2.txt",
            hedef / "istem/ikincil_model_v2.txt",
        ),
        # Belgeler: insan icin OKU_BENI, ajan icin baglayici talimat, sozlesme
        (KOK / "docs/uzak_paket/OKU_BENI.md", hedef / "OKU_BENI.md"),
        (KOK / "docs/uzak_paket/AJAN_TALIMATI.md", hedef / "AJAN_TALIMATI.md"),
        (KOK / "docs/uzak_paket/SOZLESME.md", hedef / "SOZLESME.md"),
    ]
    out = {}
    for kaynak, varis in esleme:
        varis.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(kaynak, varis)
        out[str(varis.relative_to(hedef)).replace("\\", "/")] = sha256(varis)
        print(f"  {'belge' if varis.suffix == '.md' else 'kod  '}     {varis.relative_to(hedef)}")
    return out


def main() -> None:
    if HEDEF.exists():
        shutil.rmtree(HEDEF)
    HEDEF.mkdir(parents=True)
    print(f"paket: {HEDEF.relative_to(KOK)}\n")
    girdi = kollari_normallestir(HEDEF / "girdi")
    envanter = envanteri_yaz(HEDEF / "envanter")
    kod = kodu_kopyala(HEDEF)
    (HEDEF / "cikti").mkdir(exist_ok=True)
    (HEDEF / "cikti" / ".gitkeep").write_text("", encoding="utf-8")

    (HEDEF / "gereksinimler.txt").write_text(
        "# TASK-15 ikincil model kosusu - uzak GPU\n"
        "# torch surumunu KENDI CUDA surumune gore kur:\n"
        "#   https://pytorch.org/get-started/locally/\n"
        "# Dogrulanmis Python kutuphane surumleri (2026-09-02):\n"
        "transformers==5.16.1\n"
        "accelerate==1.14.0\n"
        "huggingface_hub==1.28.0\n"
        "PyYAML==6.0.3\n"
        "sentencepiece==0.2.2\n"
        "# yalniz --dort-bit kullanilacaksa gerekli:\n"
        "# bitsandbytes>=0.45.0\n",
        encoding="utf-8",
        newline="\n",
    )

    kod["gereksinimler.txt"] = sha256(HEDEF / "gereksinimler.txt")
    manifest = {
        "uretildi_utc": datetime.now(timezone.utc).isoformat(),
        "uretici": "scripts/37_task15_uzak_paket_kur.py",
        "amac": "TASK-15 ikincil model dev secim kosusu (Qwen3.5-4B, Aya Expanse 8B)",
        "bolum": "dev",
        "model_revizyonlari": MODEL_REVIZYONLARI,
        "girdi": girdi,
        "envanter": envanter,
        "dosya_sha256": kod,
        "pakete_girmeyen": [
            "altin etiketler (docs/19 §4.2)",
            "test bolumu (kilitli)",
            "sozluk yuzey desenleri (ikincil model birincil sistemi gormemeli)",
            "birincil sistem ciktilari",
            "MedGemma kodu/istemi (aday degil, kol dusuruldu - D63)",
            "ceviri kodu (ceviri tamamlandi, uzak makinede ceviri yapilmaz)",
        ],
    }
    (HEDEF / "paket_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    print(f"\n  manifest  paket_manifest.json")
    # __pycache__ TEMIZLIGI - zip'ten HEMEN once.
    # Neden: paketten bir kez import edilirse (denetim, kuru kosu, ajanin
    # denemesi) Python .pyc birakir. Bayat bytecode uzak makineye giderse
    # kaynak dosyayla ORTUSMEYEN kod calisabilir ve manifest hash'i de
    # tutmaz. Kurucu bunu her seferinde temizler.
    for onbellek in HEDEF.rglob("__pycache__"):
        shutil.rmtree(onbellek, ignore_errors=True)
    artik = [x for x in HEDEF.rglob("*") if x.is_file() and x.suffix == ".pyc"]
    if artik:
        raise SystemExit(f"DURDU: .pyc temizlenemedi: {artik}")

    zip_yolu = Path(
        shutil.make_archive(
            str(HEDEF), "zip", root_dir=HEDEF.parent, base_dir=HEDEF.name
        )
    )
    print(f"  zip       {zip_yolu.name} ({sha256(zip_yolu)})")
    print(f"\nHAZIR. Uzak makineye gonder: {zip_yolu.name}")


if __name__ == "__main__":
    main()
