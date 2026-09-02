"""TASK-15 ceviri kollarini kosar; ciktiyi ve provenance'i kilitler.

KOLLAR (D52):
  en-genel  Turkce paket -> Google Cloud NMT `general/nmt`
  en-tibbi  en-genel CIKTISI -> MedGemma 1.5 4B tibbi post-edit
  en-ucuz   Turkce paket -> Helsinki-NLP opus-mt-tc-big-tr-en (Apache 2.0)

`en-tibbi` girdisi Turkce paket DEGIL, `en-genel` ciktisidir: iki EN kolu
arasindaki tek degisken tibbi post-edittir.

GUVENLIK:
  - Cikti dosyasi varsa DURUR; kilitli artefaktin uzerine yazilmaz.
  - Her kosu icin ayri provenance dosyasi yazilir (model, revizyon, decoding,
    girdi/cikti SHA-256, zaman). Saglayici revizyon aciklamiyorsa uydurulmaz.
  - Bu betik RadTr `test` bolumunu ACMAZ; ne verilirse onu cevirir.

Kullanim:
  .venv/Scripts/python.exe scripts/28_task15_ceviri.py ^
    --kol en-ucuz ^
    --girdi outputs/task15/dev_packages_v2/translation_dev.jsonl ^
    --cikti outputs/task15/ceviri_dev/en_ucuz_dev.jsonl
"""

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation.task15 import (
    ContractError,
    run_translation,
    sha256_file,
    write_jsonl,
)
from radyovlm.evaluation.translation import (
    CumleDuzeyiAdapter,
    CumleDuzeyiPostEdit,
    GoogleNmtAdapter,
    MedGemmaPostEditAdapter,
    OpusMtAdapter,
    run_post_edit,
)


def gorunur_yol(yol: Path) -> str:
    """Depo icindeyse goreli, disindaysa mutlak yol. `relative_to` tek basina
    goreli argumanlarda ValueError atiyordu (2026-09-01'de ilk kosuda patladi)."""
    mutlak = yol.resolve()
    try:
        return str(mutlak.relative_to(ROOT))
    except ValueError:
        return str(mutlak)


def satirlar(yol: Path) -> list[dict]:
    if not yol.exists():
        sys.exit(f"DURDU: girdi yok: {yol}")
    with yol.open(encoding="utf-8") as f:
        return [json.loads(s) for s in f if s.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kol", choices=("en-genel", "en-tibbi", "en-ucuz"), required=True)
    ap.add_argument("--girdi", type=Path, required=True)
    ap.add_argument("--cikti", type=Path, required=True)
    ap.add_argument("--google-proje", help="en-genel icin Google Cloud proje kimligi")
    ap.add_argument("--revizyon", default="main", help="HF model revizyonu (sabitle)")
    ap.add_argument(
        "--belge-duzeyi",
        action="store_true",
        help="en-tibbi'yi cumle yerine BELGE duzeyinde kosar (kosu 2'de basarisiz oldu)",
    )
    ap.add_argument(
        "--gevsek-sayi",
        action="store_true",
        help="yalniz dev: sayi/birim ihlalinde durma, profilini olc",
    )
    args = ap.parse_args()

    if args.cikti.exists():
        sys.exit(f"DURDU: kilitli ciktinin uzerine yazilmaz: {args.cikti}")
    if args.kol == "en-genel" and not args.google_proje:
        sys.exit("DURDU: en-genel icin --google-proje zorunlu")
    if args.gevsek_sayi and args.kol != "en-tibbi":
        sys.exit("DURDU: --gevsek-sayi yalniz en-tibbi kolunda anlamlidir")

    kayitlar = satirlar(args.girdi)
    print(f"kol {args.kol} · girdi {args.girdi.name} · {len(kayitlar)} belge")

    baslangic = datetime.now(timezone.utc).isoformat()
    if args.kol == "en-tibbi":
        # Cumle duzeyi VARSAYILAN: belge duzeyinde model rapor yeniden yaziyor
        # (kosu 2: 20/46 Markdown, 8/46 dusunme izi). --belge-duzeyi ile kapanir.
        ic = MedGemmaPostEditAdapter(
            revision=args.revizyon,
            max_new_tokens=1024 if args.belge_duzeyi else 320,
        )
        adapter = ic if args.belge_duzeyi else CumleDuzeyiPostEdit(ic)
        cikti = run_post_edit(
            kayitlar, adapter, strict_numbers=not args.gevsek_sayi
        )
        ihlalli = [r["document_id"] for r in cikti if r["number_violations"]]
        if ihlalli:
            print(f"  ⚠ sayi/birim ihlali olan belge: {len(ihlalli)}/{len(cikti)}")
    else:
        # Ucuz kol CUMLE duzeyinde kosar (D54): Opus-MT bir cumle cevirmenidir,
        # belge verilince dagiliyor. Sarmalayici kayipsiz boler ve birlestirir.
        adapter = (
            GoogleNmtAdapter(project_id=args.google_proje)
            if args.kol == "en-genel"
            else CumleDuzeyiAdapter(OpusMtAdapter(revision=args.revizyon))
        )
        cikti = run_translation(kayitlar, adapter)
    bitis = datetime.now(timezone.utc).isoformat()

    write_jsonl(args.cikti, cikti)
    provenance = {
        "kol": args.kol,
        "adapter": adapter.name,
        "model_id": getattr(adapter, "model_id", None)
        or getattr(getattr(adapter, "ic_adapter", None), "model_id", None),
        "ceviri_birimi": "belge"
        if (args.kol == "en-genel" or args.belge_duzeyi)
        else "cumle",
        # Yonetilen saglayici kesin revizyon vermiyorsa UYDURULMAZ.
        "revision": getattr(adapter, "revision", "saglayici tarafindan aciklanmadi"),
        "decoding": {
            "do_sample": False,
            "num_beams": getattr(adapter, "num_beams", 1),
            "max_new_tokens": getattr(adapter, "max_new_tokens", None),
        },
        "istem_hash": None
        if args.kol != "en-tibbi"
        else sha256_metin(MedGemmaPostEditAdapter.ISTEM),
        "girdi_dosya": gorunur_yol(args.girdi),
        "girdi_sha256": sha256_file(args.girdi),
        "cikti_dosya": gorunur_yol(args.cikti),
        "cikti_sha256": sha256_file(args.cikti),
        "belge_sayisi": len(cikti),
        "baslangic_utc": baslangic,
        "bitis_utc": bitis,
        "ortam": {"python": platform.python_version(), "platform": platform.platform()},
        "sayi_korunumu_zorlandi": args.kol == "en-tibbi" and not args.gevsek_sayi,
    }
    prov_yolu = args.cikti.with_suffix(args.cikti.suffix + ".provenance.json")
    prov_yolu.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"\nyazildi: {args.cikti}")
    print(f"  cikti SHA-256 {provenance['cikti_sha256']}")
    print(f"  provenance    {prov_yolu.name}")


def sha256_metin(metin: str) -> str:
    import hashlib

    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    try:
        main()
    except ContractError as hata:
        sys.exit(f"SOZLESME HATASI: {hata}")
