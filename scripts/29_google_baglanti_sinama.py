"""Google Cloud Translation baglantisini TEK cumleyle sinar.

NEDEN AYRI BETIK: kimlik dogrulama, proje kimligi, API etkinligi ve faturalandirma
dort ayri sebeple patlar. Bunlari 46 belgelik gercek kosuda ogrenmek yerine tek
cumlede ogreniriz. Gonderilen metin RadTr'den DEGILDIR - notr bir sinama cumlesi.

Kimlik dogrulama iki yoldan biriyle bulunur:
  1. GOOGLE_APPLICATION_CREDENTIALS -> servis hesabi JSON anahtari (gcloud gerekmez)
  2. gcloud auth application-default login -> ADC dosyasi

Kullanim:
  set GOOGLE_APPLICATION_CREDENTIALS=C:\\yol\\anahtar.json
  .venv/Scripts/python.exe scripts/29_google_baglanti_sinama.py
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SINAMA = "Sağ akciğer üst lobda 12 mm çapında nodül izlenmektedir."


def proje_kimligi() -> str:
    """Proje kimligini once anahtar dosyasindan, sonra ortamdan bul."""
    anahtar = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if anahtar:
        yol = Path(anahtar)
        if not yol.exists():
            sys.exit(f"DURDU: GOOGLE_APPLICATION_CREDENTIALS var ama dosya yok: {yol}")
        veri = json.loads(yol.read_text(encoding="utf-8"))
        pid = veri.get("project_id")
        if not pid:
            sys.exit("DURDU: anahtar dosyasinda 'project_id' yok; yanlis dosya olabilir")
        print(f"kimlik kaynagi : servis hesabi anahtari ({yol.name})")
        print(f"hesap          : {veri.get('client_email', '?')}")
        return pid
    pid = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if pid:
        print("kimlik kaynagi : ADC (gcloud auth application-default login)")
        return pid
    sys.exit(
        "DURDU: kimlik bulunamadi.\n"
        "  Ya GOOGLE_APPLICATION_CREDENTIALS'i servis hesabi JSON'una isaret ettir,\n"
        "  ya da gcloud ADC kurup GOOGLE_CLOUD_PROJECT ver."
    )


def main() -> None:
    try:
        from google.cloud import translate  # noqa: F401
    except ImportError:
        sys.exit(
            "DURDU: google-cloud-translate kurulu degil.\n"
            "  .venv/Scripts/python.exe -m pip install google-cloud-translate"
        )

    pid = proje_kimligi()
    print(f"proje kimligi  : {pid}")
    print(f"\ngonderilen (notr sinama cumlesi, RadTr'den DEGIL):\n  {SINAMA}")

    from radyovlm.evaluation.translation import GoogleNmtAdapter

    adapter = GoogleNmtAdapter(project_id=pid)
    try:
        sonuc = adapter.translate(SINAMA, "tr", "en")
    except Exception as hata:  # noqa: BLE001 - tanisi kullaniciya gosterilecek
        print(f"\n❌ BASARISIZ: {type(hata).__name__}: {hata}\n")
        print("Sik sebepler:")
        print("  PermissionDenied / 403  -> servis hesabinda 'Cloud Translation API")
        print("                             User' rolu yok, ya da API etkin degil")
        print("  NotFound / 404          -> proje kimligi yanlis (ad degil, ID olmali)")
        print("  Unauthenticated / 401   -> anahtar dosyasi bozuk veya suresi gecmis")
        print("  billing                 -> projeye faturalandirma hesabi bagli degil")
        sys.exit(1)

    print(f"\n✅ BAGLANTI CALISIYOR\ngelen:\n  {sonuc}")
    print(f"\nharcanan: {len(SINAMA)} karakter (aylik ucretsiz katman 500.000)")
    print("Sonraki adim: scripts/28_task15_ceviri.py --kol en-genel")


if __name__ == "__main__":
    main()
