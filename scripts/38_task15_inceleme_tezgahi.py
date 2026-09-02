# -*- coding: utf-8 -*-
"""Rapor Inceleme Tezgahi - TAMAMEN STATIK HTML uretir.

Kullanim: .venv/Scripts/python.exe scripts/38_task15_inceleme_tezgahi.py
Cikti  : outputs/task15/inceleme_tezgahi.html

Icerik icin JS YOKTUR: her belge, her metin, her kavram ve her model ciktisi
sayfaya BASILI gelir. Kullanici yalnizca kaydirir.
"""
from __future__ import annotations
import html, json, pathlib, re, sys

sys.path.insert(0, "src")
import yaml
from radyovlm.extraction.turkce_varliklar import turkce_sozlugu_yukle, tr_matcher_kur
from radyovlm.extraction.entities import matcher_kur, sozlukleri_yukle

KOK = pathlib.Path(".")
CIK = KOK / "outputs" / "task15" / "inceleme_tezgahi.html"

BOLUM = re.compile(r"\b(KL[İI]N[İI]K B[İI]LG[İI]|TEKN[İI]K|BULGULAR|SONU[ÇC]|[ÖO]NER[İI]|"
                   r"CLINICAL INFORMATION|TECHNIQUE|FINDINGS|IMPRESSION|CONCLUSION)\s*:")

def jl(p, alan=None):
    out = {}
    for l in pathlib.Path(p).open(encoding="utf-8"):
        d = json.loads(l)
        out[d["document_id"]] = d[alan] if alan else d
    return out

tr  = jl("outputs/task15/dev_packages_v2/translation_dev.jsonl", "text_tr")
eng = jl("outputs/task15/ceviri_dev/en_genel_dev.jsonl", "text")
euc = jl("outputs/task15/ceviri_dev/en_ucuz_dev.jsonl", "text")

TRD = yaml.safe_load(pathlib.Path("configs/turkce_yuzeyler_taslak.yaml").read_text(encoding="utf-8"))["yuzeyler"]
END = {}
for f in ("anatomi_sozlugu.yaml", "bulgu_sozlugu.yaml"):
    for a, t in yaml.safe_load((pathlib.Path("configs") / f).read_text(encoding="utf-8"))["kavramlar"].items():
        END[a] = t["desenler"]
ENVANTER = set(TRD)

tp, ti = tr_matcher_kur(turkce_sozlugu_yukle())
K, _ = sozlukleri_yukle()
ep, ei = matcher_kur(K)

def sp_tr(m): return [(x.start(), x.end(), ti[x.lastgroup]) for x in tp.finditer(m) if x.lastgroup in ti]
def sp_en(m): return [(x.start(), x.end(), ei[x.lastgroup].ad) for x in ep.finditer(m) if x.lastgroup in ei]

# --- KESINLIK ATAYICILARI --------------------------------------------------
# ⚠ ON BAGLAMA: Turkce kesinlik atayici resmi olarak birlesik cikariciya HENUZ
#   baglanmadi (acik is). Burada YALNIZ GORSEL INCELEME icin gecici baglaniyor.
#   Ikisi de CUMLE duzeyinde kosuyor - uretimdeki gibi. Belge duzeyinde kosmak
#   negasyon kapsamini belge geneline yayip her seyi 'absent' yapar (olculdu).
import importlib.util as _iu
from radyovlm.extraction import context as CTX
_sp = _iu.spec_from_file_location("s23", "scripts/23_turkce_dev_olcum.py")
_s23 = _iu.module_from_spec(_sp); _sp.loader.exec_module(_s23)
_, TR_IPUCU = _s23.yukle()
EN_IPUCU, EN_SONL = CTX.ipuclarini_kur()
CUM = re.compile(r"(?<=[.;])\s+")

def tr_kesinlik(metin):
    """{kavram: kesinlik} - cumle duzeyinde."""
    out = {}
    for c in [x for x in CUM.split(metin) if x.strip()]:
        for m in tp.finditer(c):
            k = ti.get(m.lastgroup)
            if k and k not in out:
                out[k] = _s23.kesinlik_ata(c, m.start(), TR_IPUCU)[0]
    return out

def en_kesinlik(metin):
    out = {}
    for c in [x for x in CUM.split(metin) if x.strip()]:
        vs = [{"bas": m.start(), "son": m.end(), "kavram": ei[m.lastgroup].ad}
              for m in ep.finditer(c) if m.lastgroup in ei]
        if not vs:
            continue
        for v in CTX.kesinlik_ata(c, vs, EN_IPUCU, EN_SONL):
            out.setdefault(v["kavram"], v.get("assertion", "?"))
    return out

MODEL = {
    "Qwen3.5-4B":     ("kosu_v2_1", "qwen_{k}_dev.jsonl"),
    "Aya Expanse 8B": ("kosu_v2_1", "aya_{k}_dev.jsonl"),
    "Qwen3-8B":       ("kosu_v2_2", "qwen3_8b_{k}_dev.jsonl"),
}
mod = {}
for ad, (kok, dsn) in MODEL.items():
    mod[ad] = {}
    for kol in ("tr", "en_genel", "en_ucuz"):
        f = KOK / "outputs/task15/ikincil_model" / kok / dsn.format(k=kol)
        if not f.exists():
            continue
        for did, d in jl(f).items():
            mod[ad].setdefault(did, {})[kol] = d

E = html.escape

def isaretle(metin, spanlar, sinif):
    """Metni span'larla vurgula, bolum basliklarini one cikar."""
    out, i = [], 0
    for b, s, k in sorted(spanlar):
        if b < i:
            continue
        out.append(E(metin[i:b]))
        out.append(f'<mark class="{sinif(k)}" title="{E(k)}">{E(metin[b:s])}</mark>')
        i = s
    out.append(E(metin[i:]))
    g = "".join(out)
    g = BOLUM.sub(lambda m: f'<span class="bolum">{m.group(0)}</span>', g)
    return "".join(f"<p>{x}</p>" for x in re.split(r"\n+", g) if x.strip())

def model_kolu(d):
    if d is None:
        return '<div class="marm"><div class="lab">yok</div></div>'
    if not d["gecerli"]:
        ham_metin = d["raw_response"]
        # Ham yanittan kimlikleri ayikla: hangileri kapali listede YOK?
        kimlikler = re.findall(r'"concept_id"\s*:\s*"([^"]{1,60})"', ham_metin)
        gorulen, disarda, icerde = set(), [], 0
        for c in kimlikler:
            if c in gorulen:
                continue
            gorulen.add(c)
            (disarda.append(c) if c not in ENVANTER else None)
            icerde += (c in ENVANTER)
        rozet = ""
        if disarda:
            rozet = ('<div class="ok" style="color:var(--bad)">'
                     f'{len(disarda)} uydurulmuş kimlik · {icerde} geçerli</div>'
                     '<div class="chips">'
                     + "".join('<span class="chip bad" title="kapali listede yok">'
                                 + E(c) + '</span>'
                               for c in disarda[:24]) + '</div>')
        elif kimlikler:
            rozet = f'<div class="ok" style="color:var(--ink-3)">{icerde} kimlik, hepsi listede — sorun biçimde</div>'
        ham = E(ham_metin[:1400])
        return (f'<div class="viol">⛔ {E((d["ihlal"] or "")[:150])}</div>{rozet}'
                f'<details class="ham"><summary>ham yanıtı göster</summary><pre>{ham}</pre></details>')
    cl = {"present": "p", "absent": "a", "uncertain": "u"}
    ch = []
    for x in d["findings"]:
        dis = x["concept_id"] not in ENVANTER
        c = "bad" if dis else cl.get(x["assertion"], "u")
        t = x["assertion"] + (" · ENVANTER DIŞI" if dis else "")
        ch.append(f'<span class="chip {c}" title="{E(t)}">{E(x["concept_id"])}</span>')
    return (f'<div class="ok">✓ geçerli · {len(d["findings"])} bulgu</div>'
            f'<div class="chips">{"".join(ch) or "<span class=yok>boş</span>"}</div>')

parcalar = []
ozet = []          # belge bazinda
kav_tr, kav_en, kav_ort = {}, {}, {}   # kavram bazinda
sirali = sorted(tr, key=lambda x: x)
for n, did in enumerate(sirali, 1):
    st, se, su = sp_tr(tr[did]), sp_en(eng[did]), sp_en(euc[did])
    kesT, kesE = tr_kesinlik(tr[did]), en_kesinlik(eng[did])
    T, EN, U = {k for _, _, k in st}, {k for _, _, k in se}, {k for _, _, k in su}
    hepsi = sorted(T | EN | U)
    ayr = [k for k in hepsi if (k in T) != (k in EN)]
    ort = [k for k in hepsi if (k in T) == (k in EN)]

    def satir(k):
        inT, inE, inU = k in T, k in EN, k in U
        d = ('<span class="tag b">ikisi de</span>' if inT and inE else
             '<span class="tag t">yalnız TR</span>' if inT else
             '<span class="tag e">yalnız EN</span>')
        tick = lambda v: '<span class="tick y">✓</span>' if v else '<span class="tick n">·</span>'
        KIS = {"present": ("var", "kp"), "absent": ("yok", "ka"),
               "uncertain": ("belirsiz", "ku")}
        def kes(x):
            if x is None:
                return '<span class="kes yok">—</span>'
            ad, c = KIS.get(x, (x, "ku"))
            return f'<span class="kes {c}">{ad}</span>'
        a, b = kesT.get(k), kesE.get(k)
        ayrik = ' kfark' if (a and b and a != b) else ''
        return (f'<tr class="{ayrik.strip()}"><td class="k">{E(k)}'
                f'<span class="dsn"><i>TR</i> {E(TRD[k]["desen"])}</span>'
                f'<span class="dsn"><i>EN</i> {E("  ·  ".join(END.get(k, [])))}</span></td>'
                f'<td class="c">{tick(inT)}</td><td class="c">{tick(inE)}</td>'
                f'<td class="c">{tick(inU)}</td>'
                f'<td class="c kk">{kes(a)}</td><td class="c kk">{kes(b)}</td>'
                f'<td>{d}</td></tr>')

    yt = [k for k in hepsi if k in T and k not in EN]
    ye = [k for k in hepsi if k in EN and k not in T]
    # ipuclari: belgede ne gorecegim?
    bel = len(re.findall(r"\([^)]{0,60}\?\s*\)", tr[did]))          # ayirici tani
    neg = len(re.findall(r"saptanma|izlenme|goruilme|gorulme", tr[did], re.I))
    mq = mod["Qwen3.5-4B"].get(did, {})
    mgec = sum(1 for kk in ("tr","en_genel","en_ucuz") if mq.get(kk) and mq[kk]["gecerli"])
    ozet.append({"n": n, "id": did, "T": len(T), "E": len(EN), "U": len(U),
                 "ort": len(T & EN), "yt": yt, "ye": ye})
    for k in yt: kav_tr[k] = kav_tr.get(k, 0) + 1
    for k in ye: kav_en[k] = kav_en.get(k, 0) + 1
    for k in (T & EN): kav_ort[k] = kav_ort.get(k, 0) + 1

    mkart = []
    for ad in MODEL:
        m = mod[ad].get(did)
        if not m:
            mkart.append(f'<div class="mcard"><div class="mcard-h"><b>{E(ad)}</b>'
                         f'<span class="yok">bu belge koşulmadı — model ilk 8 belgede erken durdurmayla elendi</span>'
                         f'</div></div>')
            continue
        gec = sum(1 for k in ("tr", "en_genel", "en_ucuz") if m.get(k) and m[k]["gecerli"])
        top = sum(1 for k in ("tr", "en_genel", "en_ucuz") if m.get(k))
        rz = (f'<span class="tag b">{gec}/{top} kol geçerli</span>' if gec == top else
              f'<span class="tag bad">hiçbir kol geçerli değil</span>' if gec == 0 else
              f'<span class="tag t">{gec}/{top} kol geçerli</span>')
        kollar = "".join(
            f'<div class="marm"><div class="lab">{lab}</div>{model_kolu(m.get(kk))}</div>'
            for kk, lab in (("tr", "TR"), ("en_genel", "EN-genel"), ("en_ucuz", "EN-ucuz")))
        mkart.append(f'<div class="mcard"><div class="mcard-h"><b>{E(ad)}</b>{rz}</div>'
                     f'<div class="marms">{kollar}</div></div>')

    fk = len(ayr)
    sev = "yuk" if fk >= 6 else "orta" if fk >= 3 else "dus"
    ipuc = []
    if fk: ipuc.append('<span class="ip f">' + str(fk) + ' ayrışan</span>')
    for k in ayr[:4]:
        ipuc.append('<span class="ip ' + ("t" if k in T else "e") + '">' + E(k) + '</span>')
    if len(ayr) > 4: ipuc.append('<span class="ip s">+' + str(len(ayr)-4) + '</span>')
    if bel: ipuc.append('<span class="ip u">' + str(bel) + ' ayırıcı tanı</span>')
    if neg: ipuc.append('<span class="ip n">' + str(neg) + ' olumsuzlama</span>')
    ipuc.append('<span class="ip m">model ' + str(mgec) + '/3 geçerli</span>')

    parcalar.append(f"""
<details class="doc" id="d{n}">
  <summary>
    <span class="sno">{n}</span>
    <span class="sid">{E(did.split('#')[0])}</span>
    <span class="scnt">TR {len(T)} · EN {len(EN)} · ucuz {len(U)}</span>
    <span class="sfk {sev}">{fk}</span>
    <span class="sipuc">{"".join(ipuc)}</span>
  </summary>
  <div class="dhdr">
    <div><span class="no">{n} / {len(sirali)}</span>
      <h2>{E(did.split('#')[0])}</h2>
      <p class="sub">sözlük · TR <b>{len(T)}</b> · EN-genel <b>{len(EN)}</b> · EN-ucuz <b>{len(U)}</b> kavram
      &nbsp;·&nbsp; <b>{len(ayr)}</b> ayrışan, {len(ort)} uyuşan</p></div>
  </div>

  <div class="cols">
    <div class="panel"><div class="panel-h"><b>Türkçe aslı</b><span class="n">{len(st)} eşleşme</span></div>
      <div class="rapor">{isaretle(tr[did], st, lambda k: 'b' if k in EN else 't')}</div></div>
    <div class="panel"><div class="panel-h"><b>EN-genel · Google</b><span class="n">{len(se)} eşleşme</span></div>
      <div class="rapor">{isaretle(eng[did], se, lambda k: 'b' if k in T else 'e')}</div></div>
    <div class="panel"><div class="panel-h"><b>EN-ucuz · Opus-MT</b><span class="n">{len(su)} eşleşme</span></div>
      <div class="rapor">{isaretle(euc[did], su, lambda k: 'b' if k in T else 'e')}</div></div>
  </div>

  <h3 class="sec">Sözlük ne buldu — kavram ve kutuplaşma</h3>
  <p class="tnot">İlk üç sütun <b>kavram ekseni</b>: bu kavram o metinde konu ediliyor mu?
  Son iki sütun <b>kutuplaşma</b>: rapor "var" mı "yok" mu diyor?
  <span class="kes kp">var</span> <span class="kes ka">yok</span>
  <span class="kes ku">belirsiz</span> · İki tarafın kutbu farklıysa satır işaretlenir.
  <b>⚠ Kutuplaşma sütunları ön ölçümdür</b> — Türkçe kesinlik atayıcı çıkarıcıya geçici
  bağlandı, resmî hat henüz kurulmadı.</p>
  <p class="tnot" style="background:var(--bad-bg);border:1px solid var(--bad);border-radius:8px;padding:11px 14px">
  <b>⚠ Bilinen sınır — "normal" ifadeleri.</b> Kesinlik sistemi yalnız <b>açık olumsuzlama</b>
  tanıyor (<code>saptanmadı</code>, <code>izlenmedi</code> · İngilizcede <code>no</code>,
  <code>not detected</code>). <em>"Kalp boyutları normaldir"</em> gibi <b>normallik beyanları</b>
  ipucu listesinde yok, bu yüzden <span class="kes kp">var</span> sayılıyor — oysa rapor
  kardiyomegalinin <b>olmadığını</b> söylüyor. Ölçüldü: "normal" geçen ama olumsuzlama ipucu
  içermeyen cümlelerde <b>50 kavram anmasının 50'si</b> present sayılıyor.
  <b>İki tarafta da aynı</b> (İngilizce <em>"Heart dimensions are normal"</em> de present),
  yani TR/EN karşılaştırmasını bozmuyor — ama <code>present</code> ekseninin mutlak doğruluğunu
  etkiliyor ve kanonik altın üretilmeden önce kapatılması gereken bir açıktır.</p>
  <div class="tw"><table>
    <thead><tr><th>kavram ve sözlüğün aradığı desen</th>
      <th class="c">TR</th><th class="c">EN-genel</th><th class="c">EN-ucuz</th>
      <th class="c kk">TR<br><small>var/yok</small></th>
      <th class="c kk">EN<br><small>var/yok</small></th>
      <th>durum</th></tr></thead>
    <tbody>{"".join(satir(k) for k in ayr)}{"".join(satir(k) for k in ort)}</tbody>
  </table></div>

  <h3 class="sec">Modeller ne dedi</h3>
  <div class="mgrid">{"".join(mkart)}</div>
</details>""")


# ===================== GENEL KARSILASTIRMA TABLOLARI =====================
tT = sum(o["T"] for o in ozet); tE = sum(o["E"] for o in ozet)
tU = sum(o["U"] for o in ozet); tO = sum(o["ort"] for o in ozet)
tYT = sum(len(o["yt"]) for o in ozet); tYE = sum(len(o["ye"]) for o in ozet)
jac = tO / (tO + tYT + tYE) if (tO + tYT + tYE) else 0

def kis(lst, n=6):
    if not lst: return '<span class="bos">—</span>'
    g = "".join(f'<code>{E(k)}</code>' for k in lst[:n])
    return g + (f'<span class="bos"> +{len(lst)-n}</span>' if len(lst) > n else "")

satirlarA = []
for o in sorted(ozet, key=lambda x: -(len(x["yt"]) + len(x["ye"]))):
    f = len(o["yt"]) + len(o["ye"])
    sev = "yuk" if f >= 6 else "orta" if f >= 3 else "dus"
    satirlarA.append(
        f'<tr><td class="ix"><a href="#d{o["n"]}">{o["n"]}</a></td>'
        f'<td class="did"><a href="#d{o["n"]}">{E(o["id"].split("#")[0])}</a></td>'
        f'<td class="c">{o["T"]}</td><td class="c">{o["E"]}</td><td class="c">{o["U"]}</td>'
        f'<td class="c">{o["ort"]}</td>'
        f'<td class="c"><b class="fk {sev}">{f}</b></td>'
        f'<td class="lst t">{kis(o["yt"])}</td><td class="lst e">{kis(o["ye"])}</td></tr>')

kavlar = sorted(set(kav_tr) | set(kav_en),
                key=lambda k: -(kav_tr.get(k, 0) + kav_en.get(k, 0)))
satirlarB = []
for k in kavlar:
    a, b, c = kav_tr.get(k, 0), kav_en.get(k, 0), kav_ort.get(k, 0)
    yon = ('<span class="tag t">TR lehine</span>' if a > b * 2 else
           '<span class="tag e">EN lehine</span>' if b > a * 2 else
           '<span class="tag">dengeli</span>')
    bar = lambda v, cls: (f'<span class="bar {cls}" style="width:{min(v,20)*5}%"></span>'
                          if v else "")
    satirlarB.append(
        f'<tr><td class="k">{E(k)}'
        f'<span class="dsn"><i>TR</i> {E(TRD[k]["desen"])}</span>'
        f'<span class="dsn"><i>EN</i> {E("  ·  ".join(END.get(k, [])))}</span></td>'
        f'<td class="c">{a or ""}</td><td class="bars">{bar(a,"t")}{bar(b,"e")}</td>'
        f'<td class="c">{b or ""}</td><td class="c">{c or ""}</td><td>{yon}</td></tr>')

GENEL = f"""
<section class="genel" id="genel">
  <h3 class="sec">Genel tablo · 46 belgenin tamamı</h3>

  <div class="ozet">
    <div class="oz"><span class="lab">Türkçe sözlük</span><b>{tT:,}</b><span class="alt">belge-kavram</span></div>
    <div class="oz"><span class="lab">EN-genel</span><b>{tE:,}</b><span class="alt">belge-kavram</span></div>
    <div class="oz"><span class="lab">EN-ucuz</span><b>{tU:,}</b><span class="alt">belge-kavram</span></div>
    <div class="oz mid"><span class="lab">ikisi de buldu</span><b>{tO:,}</b><span class="alt">TR ∩ EN-genel</span></div>
    <div class="oz tr"><span class="lab">yalnız TR</span><b>{tYT:,}</b><span class="alt">EN kaçırdı</span></div>
    <div class="oz en"><span class="lab">yalnız EN</span><b>{tYE:,}</b><span class="alt">TR kaçırdı</span></div>
    <div class="oz mid"><span class="lab">örtüşme</span><b>{str(round(jac,3)).replace(chr(46),chr(44))}</b><span class="alt">toplu Jaccard</span></div>
  </div>
  <p class="ipucu">Bu sayılar bu sayfadaki <b>46 <code>dev</code> belgesine</b> aittir ve
  <b>onarılmış sözlüklerle</b>, iki tarafta da aynı birleşik eşleştiriciyle üretilmiştir.
  Onarımdan önce aynı 46 belgede yalnız-TR <b>116</b>, yalnız-EN <b>111</b>, örtüşme <b>0,795</b> idi —
  yani ayrışma <b>227'den 40'a</b> düştü.
  (Raporlarda geçen <b>152 / 167</b> ve <b>0,940</b> rakamları <code>train</code> bölümünün
  223 belgesine aittir; sözlük orada türetilip donduruldu.)
  Aşağıdaki iki tablo bu toplamın nereden geldiğini açar.</p>



  <div class="uyari">
    <b>⚠ Buradaki tik "hasta bu bulguya sahip" demek DEĞİL</b>
    <p>Sözlük bu katmanda tek bir soruyu cevaplıyor: <b>bu kavram raporda konu ediliyor mu?</b>
    Var mı yok mu sorusu <b>ayrı bir eksende</b> cevaplanıyor.</p>
    <p>Örnek: <em>"Kalp boyutları <b>normaldir</b>"</em> cümlesi <code>cardiomegaly</code> kavramını
    işaretler — çünkü rapor kardiyomegaliden <em>söz ediyor</em>, ve "yok" diyor.
    <code>dev</code>'deki 38 belgenin çoğunda cümle tam da böyle: kalp boyutları
    <em>normaldir / normal sınırlardadır</em>. Kavram <b>tikli</b>, bulgu <b>yok</b>.</p>
    <p><b>Neden böyle kurulu?</b> Çeviri iki ayrı şeyi kaybedebilir: (1) konunun kendisini —
    cümle hiç çevrilmemiştir; (2) kutuplaşmayı — <em>"yoktur"</em> düşmüş, cümle <em>"vardır"</em>a
    dönmüştür. Birincisi bu tablodaki <b>A1 · kavram çıkarımı</b> ekseni, ikincisi
    <b>kesinlik</b> ekseni. Önce kavramın hayatta kalıp kalmadığına bakılır; kutuplaşma ayrı ölçülür.</p>
    <p><b>Kutuplaşmayı görmek istersen</b> aşağıdaki model kartlarına bak: modeller her kavramı
    <span class="chip p" style="display:inline-block">present</span>
    <span class="chip a" style="display:inline-block">absent</span>
    <span class="chip u" style="display:inline-block">uncertain</span> olarak etiketliyor.
    Aynı 46 belgede Qwen'in <code>cardiomegaly</code> için dediği: 7 <em>present</em>, 2 <em>absent</em>.</p>
    <p class="acik"><b>Açık iş:</b> Türkçe tarafta kesinlik atayıcı var ama henüz birleşik
    çıkarıcının kendi span'larına bağlı değil. İngilizce tarafta bu hat kurulu. Skorlamadan
    önce tamamlanacak — bu yüzden sözlük tablosunda şimdilik yalnız kavram ekseni gösteriliyor.</p>
  </div>



    <div class="kimkarar">
      <b>Peki var/yok kararını kim veriyor?</b>
      <p><b>Ayrı bir sözlük ve ayrı bir kural sistemi</b> — yüzey sözlüğü değil.
      Yüzey sözlüğü kavramı <em>bulur</em>, ipucu sözlüğü kavrama <em>kutup verir.</em></p>
      <div class="ikili">
        <div class="ik"><span class="lab">Türkçe</span>
          <code>configs/turkce_ipuclari_taslak.yaml</code>
          <span class="d">22 ipucu · <code>saptanmadı</code> · <code>izlenmedi</code> ·
          <code>ekarte edilemez</code> · <code>parantez-soru</code> · <code>uyumlu</code></span></div>
        <div class="ik"><span class="lab">İngilizce</span>
          <code>configs/ipucu_sozlugu.yaml</code>
          <span class="d">9 negasyon + teknik çekince + belirsizlik ipucu ·
          <code>no</code> · <code>not detected</code> · <code>cannot be excluded</code></span></div>
      </div>
      <p><b>Karar sırası</b> — ilk eşleşen kazanır, sırayla:</p>
      <ol class="sira">
        <li><b>belirsizlik-öncelikli</b> — <em>"ekarte edilemez"</em>: içinde olumsuzluk eki var,
        negasyondan <b>önce</b> bakılır yoksa yanlışlıkla "yok" sayılır</li>
        <li><b>teknik çekince</b> — <em>"kontrast verilmediğinden değerlendirilemedi"</em>:
        kesinliği değiştirmez ama negasyon ipucunun kapsamını tüketir; bir bulgunun
        yokluğu <b>değildir</b></li>
        <li><b>negasyon</b> — <em>"saptanmadı"</em> → <span class="pz">absent</span>.
        Türkçede <b>geri yönlüdür</b>: ipucu cümlenin sonunda, kendinden <b>önceki</b>
        kavramı olumsuzlar. Ölçüldü: Türkçe negasyon ipuçlarının <b>%97'si cümle sonunda</b>;
        İngilizce mantığı doğrudan uygulansaydı negasyonun neredeyse tamamı kaçardı</li>
        <li><b>belirsizlik</b> — <em>"(metastaz?)"</em> → <span class="uz">uncertain</span>.
        <b>Kapsamlıdır</b>, cümle geneline yayılmaz: parantez radyolojide bir ayırıcı tanı
        önerisidir, yalnız kendi terimini belirsiz yapar</li>
        <li><b>çıkarım ifadesi</b> — <em>"ile uyumlu"</em>, <em>"lehine"</em> →
        <span class="pz">present</span></li>
        <li>hiçbiri yoksa → <span class="pz">present</span></li>
      </ol>
      <p class="acik"><b>Doğrulandı mı?</b> Evet — Türkçe kesinlik sistemi <code>dev</code>'de
      <b>altın etikete karşı</b> ölçüldü: <code>absent</code> için kesinlik %84,3 ·
      duyarlılık <b>%97,2</b> · F1 <b>%90,3</b>. Yani "yok" diyen cümlelerin %97'sini
      yakalıyor. Kaynak: <code>reports/turkce_dondurma.md</code></p>
    </div>

    <div class="olcum">
      <b>Peki kutuplaşma çeviride korunuyor mu? — ölçtük</b>
      <p>Türkçe ve İngilizce kesinlik atayıcıları aynı 46 belgede koşturulup karşılaştırıldı.
      İki tarafta da bulunan <b>1.039</b> kavramın <b>1.012'sinde kesinlik aynı</b>,
      <b>27'sinde (%2,6)</b> farklı.</p>
      <div class="kt3">
        <div class="k3"><span>uncertain → present</span><b>14</b></div>
        <div class="k3"><span>absent → present</span><b>10</b></div>
        <div class="k3"><span>present → uncertain</span><b>2</b></div>
        <div class="k3"><span>present → absent</span><b>1</b></div>
      </div>
      <p><b>Üç vaka tek tek açıldı ve üçünde de çeviri kusursuz</b> — fark iki kesinlik
      sisteminin kural farkından geliyor, çeviri kaybından değil:</p>
      <table class="ktbl"><tbody>
        <tr><td><code>heart</code></td><td class="a">absent</td><td class="o">→</td><td class="pz">present</td>
          <td><em>"IVKM verilmediğinden … değerlendirme yapılamamıştır"</em> — <b>teknik çekince</b>.
          Türkçe sistem bunu yok sayıyor, İngilizce saymıyor.</td></tr>
        <tr><td><code>gallbladder</code></td><td class="a">absent</td><td class="o">→</td><td class="pz">present</td>
          <td><em>"Safra kesesi izlenmedi (opere)."</em> → <em>"was not visualized"</em> —
          çeviri doğru, İngilizce tarafta negasyon kapsamı parantezde kopuyor.</td></tr>
        <tr><td><code>pneumonia</code></td><td class="a">uncertain</td><td class="o">→</td><td class="pz">present</td>
          <td><em>"KLİNİK BİLGİ: PNÖMONİ?"</em> → <em>"CLINICAL INFORMATION: PNEUMONIA?"</em> —
          çeviri doğru, soru işareti kapsamı iki tarafta farklı çözülüyor.</td></tr>
      </tbody></table>
      <p class="acik"><b>⚠ Bu bir ön ölçümdür, skor değildir.</b> Türkçe kesinlik atayıcı
      birleşik çıkarıcıya <b>geçici olarak</b> bağlanarak yapıldı; resmî hat henüz kurulmadı.
      Ayrıca burada iki sistem <b>birbiriyle</b> karşılaştırılıyor — altın etiketle değil.
      Türkçe negasyon sistemi ayrıca altına karşı ölçülmüştü: <code>absent</code> F1 <b>%90,3</b>,
      duyarlılık <b>%97,2</b>.</p>
    </div>

  <h4 class="alt2">Bu tablodan ne okunuyor</h4>
  <div class="okuma">
    <div class="ok1"><span class="k">1</span>
      <b>Türkçe ile iyi çeviri artık ayırt edilemiyor</b>
      <span>TR <b>1.057</b>, EN-genel <b>1.061</b> belge-kavram. Ayrışma <b>40</b> — yaklaşık 1.100 üzerinden.
      <b>46 belgenin 24'ünde hiç ayrışma yok</b>, 19'unda yalnız 1-2 kavram, 6 ve üzeri ayrışan
      <b>hiç yok.</b></span></div>
    <div class="ok1"><span class="k">2</span>
      <b>Kalan ayrışma dağınık, sistematik değil</b>
      <span>En çok ayrışan kavram bile 3-4 belgede ayrışıyor (<code>infiltration</code>,
      <code>dilatation</code>). Bir dili sistematik olarak kayıran bir örüntü <b>yok</b> —
      yalnız-TR 18, yalnız-EN 22.</span></div>
    <div class="ok1"><span class="k">3</span>
      <b>Asıl fark dilde değil, çeviri kalitesinde</b>
      <span>EN-ucuz yalnız <b>881</b> belge-kavram buluyor: iyi çeviriye göre <b>%17 daha az</b>.
      EN-genel'de bulunup EN-ucuz'da kaybolan <b>244</b> belge-kavram var —
      <code>hemithorax</code> 32, <code>cardiomegaly</code> 21, <code>lung_parenchyma</code> 21…
      Bu, Türkçe/İngilizce farkının <b>altı katı</b>.</span></div>
  </div>
  <p class="ipucu"><b>Ama bu ablasyon sonucu değildir</b> ve öyle sunulamaz. Üç sebeple:
  (a) burada sözlük <b>kendini</b> karşılaştırıyor — altın etiketle değil, birbiriyle;
  (b) bu <code>dev</code> bölümü ve Türkçe sözlük <code>dev</code>'i görerek türetildi, yani sayılar
  Türkçe lehine hafif yanlı; (c) ölçüm <code>test</code> üzerinde, kilitli altın veriyle yapılacak.
  Buradaki tablo <b>aletin ayarlandığını</b> gösterir, sorunun cevabını değil.</p>

  <h4 class="alt2">A · Belge bazında — en çok ayrışan üstte</h4>
  <div class="tw"><table class="genelA">
    <thead><tr><th>#</th><th>belge</th><th class="c">TR</th><th class="c">EN-genel</th>
      <th class="c">EN-ucuz</th><th class="c">ikisi de</th><th class="c">ayrışan</th>
      <th>yalnız TR</th><th>yalnız EN</th></tr></thead>
    <tbody>{"".join(satirlarA)}</tbody>
  </table></div>

  <h4 class="alt2">B · Kavram bazında — hangi kavram, kaç belgede, hangi yönde ayrışıyor</h4>
  <p class="ipucu" style="margin-top:0">Her kavramın altında iki sözlüğün aradığı desen var.
  Bir kavram tek yönde yığılıyorsa sebebi çoğu zaman desende görünür.</p>
  <div class="tw"><table class="genelB">
    <thead><tr><th>kavram ve sözlüğün aradığı desen</th><th class="c">yalnız TR</th>
      <th style="width:200px"></th><th class="c">yalnız EN</th><th class="c">ikisi de</th>
      <th>eğilim</th></tr></thead>
    <tbody>{"".join(satirlarB)}</tbody>
  </table></div>
</section>
"""

GIRIS = """
<header class="mast">
  <p class="eyebrow">TASK-15 · Dil Ablasyonu</p>
  <h1>Rapor İnceleme Tezgâhı</h1>
  <p class="standfirst">Aynı radyoloji raporunu <b>Türkçe okumakla, İngilizceye çevirip okumak</b> arasında bilgi farkı var mı? Bu sayfa 46 belgenin tamamını üç metin, iki okuyucu ve üç model çıktısıyla yan yana koyar.</p>
</header>

<div class="intro">
  <h2>Nasıl okunur</h2>
  <div class="steps">
    <div class="step"><span class="k">1 · METİN</span><b>Üç sütun</b>
      <span>Türkçe aslı, Google çevirisi, ucuz çeviri. Renkli vurgular sözlüğün bir kavramı <em>hangi kelimeden</em> tanıdığını gösterir.</span></div>
    <div class="step"><span class="k">2 · SÖZLÜK</span><b>Birincil ölçüm</b>
      <span>Kural tabanlı, deterministik okuyucu. <b>Dil kararını bu verir.</b> Tablo hangi kavramı hangi tarafın bulduğunu ve aradığı deseni açar; ayrışanlar üstte.</span></div>
    <div class="step"><span class="k">3 · MODEL</span><b>İkincil kontrol</b>
      <span>Üç açık dil modeli aynı işi sözlüğü hiç görmeden yapacaktı. <b>Üçü de seçim kapılarını geçemedi</b> — çıktıları ölçüme girmez, burada yalnız görmek için.</span></div>
  </div>

  <div class="lg">
    <span><i class="sw b"></i><b>yeşil</b> — iki tarafın da bulduğu kavram</span>
    <span><i class="sw t"></i><b>turuncu</b> — yalnız Türkçede bulunan</span>
    <span><i class="sw e"></i><b>mavi</b> — yalnız İngilizcede bulunan</span>
  </div>
  <p class="ipucu">Turuncu bir vurgu iki şeyden biri demektir: ya çeviri o bilgiyi <b>düşürmüştür</b> (ölçmek istediğimiz şey), ya da İngilizce sözlük o biçimi <b>tanımıyordur</b> (alet arızası). Hangisi olduğunu anlamak için karşı sütundaki aynı cümleye ve tablodaki desene bak.</p>
</div>



<div class="intro">
  <h2>Bu sayfadaki 46 belge nereden geliyor?</h2>
  <p class="ipucu" style="margin-top:0">Veri kümesi <b>RadTr</b> — uzman radyologlar tarafından
  Türkçe yazılmış toraks BT raporları. Üç bölüme ayrılmış ve <b>her bölüm farklı bir iş için</b>
  kullanılıyor. Bu sayfa <code>dev</code> bölümünü gösteriyor.</p>

  <div class="bolumler">
    <div class="bl">
      <span class="bad">train</span><b>223 belge</b>
      <span class="ne">Sözlüğün <b>yapıldığı</b> yer</span>
      <ul>
        <li>Türkçe yüzey desenleri buradan okunarak yazıldı</li>
        <li>Simetrik onarım burada yapıldı — <b>26 kavram</b></li>
        <li>Onarım sonrası: yalnız TR <b>152</b>, yalnız EN <b>167</b>, örtüşme <b>0,940</b></li>
        <li>Google çevirisi burada da üretildi (223 belge)</li>
      </ul>
    </div>
    <div class="bl akt">
      <span class="bad a">dev</span><b>46 belge</b>
      <span class="ne">Ayarların <b>denendiği</b> yer — <b>bu sayfa</b></span>
      <ul>
        <li>Üç çeviri kolu burada üretildi ve kalite kontrolü yapıldı</li>
        <li>Çevirinin deterministik olmadığı burada ölçüldü (%11 belge farklı çıktı)</li>
        <li>Tıbbi post-edit kolu burada denendi ve <b>düşürüldü</b></li>
        <li>Üç dil modeli burada sınandı, <b>üçü de elendi</b></li>
        <li>Türkçe negasyon sistemi burada altına karşı ölçüldü (<code>absent</code> F1 %90,3)</li>
      </ul>
    </div>
    <div class="bl kil">
      <span class="bad k">test</span><b>56 belge</b>
      <span class="ne">Asıl ölçüm — <b>henüz açılmadı</b></span>
      <ul>
        <li>Çevirisi <b>yapılmadı</b>, hiçbir skor hesaplanmadı</li>
        <li>Açılması için: kanonik altın üretilecek, radyolog onaylayacak, altın hash'lenip kilitlenecek</li>
        <li>Sonra <b>tek sefer</b> çevrilecek — ham çıktı değişmez artefakt (çeviri deterministik değil)</li>
        <li>Ablasyonun cevabı buradan çıkacak</li>
      </ul>
    </div>
  </div>

  <p class="ipucu"><b>⚠ Neden bu sayfadaki sayılar "sonuç" değil.</b> Üç sebep:
  (a) burada sözlük <b>kendini</b> karşılaştırıyor — altın etiketle değil;
  (b) Türkçe sözlük <code>dev</code>'i <b>görerek</b> türetildi (<code>train</code>+<code>dev</code>,
  269 belge), İngilizce sözlük görmedi — yani bu bölümdeki sayılar <b>Türkçe lehine hafif yanlı</b>;
  (c) ölçüm <code>test</code>te yapılacak ve orayı <b>iki sözlük de görmedi</b>.
  Buradaki tablolar <b>aletin ayarlandığını</b> gösterir, sorunun cevabını değil.</p>
</div>
<div class="intro">
  <h2>Sözlük sistemi nedir</h2>
  <p class="ipucu" style="margin-top:0">Bir <b>ölçü aletidir.</b> Ona bir rapor verirsin, sana o raporda
  geçen kavramların listesini verir. Deterministiktir: aynı metni iki kez versen aynı cevabı alırsın ve
  her kararın hangi kelimeden geldiğini gösterebilir.</p>

  <div class="sema">
    <div class="hub"><b>144 KAVRAM</b><span>ortak kimlik listesi</span>
      <code>cardiomegaly · effusion · rib …</code></div>
    <div class="oklar"><span>Türkçe metinde</span><span>İngilizce metinde</span></div>
    <div class="kutular">
      <div class="kt tr"><span class="lab">turkce_yuzeyler.yaml</span>
        <code>kardiyomegali|kalp boyut|kardiyak boyut</code>
        <span class="src">desenler RadTr korpusundan okunarak yazıldı</span></div>
      <div class="kt en"><span class="lab">bulgu_ + anatomi_sozlugu.yaml</span>
        <code>cardiomegaly · heart dimensions? · heart size</code>
        <span class="src">desenler CT-RATE korpusundan okunarak yazıldı</span></div>
    </div>
  </div>

  <p class="ipucu"><b>Çeviri sözlüğü değildir.</b> İki dosya birbirini görmez, birbirine bakarak yazılmadı.
  Öyle olsaydı deneyi yapamazdık: iki tarafı birbirine eşitleyip sonra <em>"ikisi de aynı şeyi buluyor"</em>
  diye ölçerdik — dairesel olurdu. Her iki dosya da <b>aynı 144 kimliğe</b> bakar ama kendi dilinin
  metnini kendi gözlemleriyle tanır.</p>

  <p class="ipucu"><b>Neden düz kelime listesi değil de desen?</b> Türkçe sondan eklemeli.
  <code>nodül</code> yazsan <em>nodüller, nodülde, nodüler</em> kaçar. Bu yüzden Türkçe desenler
  <b>kökten</b> yazılır. İngilizcede çekim az, bileşik terim çok; desenler öbek hâlinde listelenir.
  Üretimde her iki taraf da tek birleşik eşleştirici kullanır ve <b>en uzun eşleşme kazanır</b> —
  <em>"lung parenchyma"</em> tek bir kavrama gider, <code>lung</code> + <code>parenchyma</code> diye
  ikiye bölünmez.</p>

  <details class="ham" style="margin-top:16px">
    <summary>144 kavramı kim, nasıl, hangi veriden belirledi?</summary>
    <div style="margin-top:12px">
      <p class="ipucu" style="margin-top:0"><b>Kaynak:</b> CT-RATE korpusunun <code>train</code> bölümü —
      449.868 cümle, 20.000 hasta. Kavramlar bir ders kitabından ya da hazır bir ontolojiden
      <b>kopyalanmadı</b>; korpusta gerçekten geçen ifadelerin frekans madenciliğiyle çıkarıldı.
      İlke şuydu: <em>ithal sözlük başlangıç noktasıdır, bitiş noktası değil.</em></p>
      <p class="ipucu"><b>Dağılım:</b> 56 anatomi · 56 gözlem · 26 niteleyici · 6 cihaz.</p>
      <p class="ipucu"><b>"Dilsiz" ne demek, ne demek değil.</b> Kavramlar <b>kimlik</b> olarak kullanılır,
      kelime olarak değil: <code>cardiomegaly</code> bir İngilizce sözcük değil, "kalbin büyümüş olması"
      fikrinin adıdır ve her dil ona kendi yüzeylerini bağlar. Ama <b>seçimleri</b> İngilizce bir korpusun
      frekansına dayanır — yani köken olarak dilsiz değildir, kullanımda dilden bağımsızdır.
      Bu ayrım önemlidir ve gizlenmemelidir.</p>
      <p class="ipucu"><b>İlginç bir ayrıntı:</b> CT-RATE'in İngilizcesi de aslında Türkçe raporların
      Google Translate ile çevrilip iki dilli tıp öğrencilerince düzeltilmiş hâlidir. Yani zincir
      <em>Türkçe klinik yazı → çeviri + insan düzeltmesi → İngilizce → frekans madenciliği → 144 kavram</em>
      diye gider. Envanter, dolaylı da olsa Türkçe radyoloji pratiğinden doğmuştur.</p>
      <p class="ipucu"><b>⚠ Güvenilirlik sınırları — açıkça:</b></p>
      <ul class="sinir">
        <li><b>Uzman onayı yok.</b> 144 kavramın <b>144'ü de</b> <code>uzman_onayi: false</code> taşır.
        Sözlük bir ölçü aletidir, altın etiket değildir. Kanonik altın ayrı üretilecek ve
        <b>radyolog</b> nihai kararı verecek.</li>
        <li><b>RadLex eşlemesi yapılmadı.</b> Erişim sağlanamadı; uydurma kimlik yazmak yerine
        kimliksiz kalındı. Kavram kimlikleri <b>yereldir</b>, şemada RadLex alanı boş bekliyor.</li>
        <li><b>Kapsam toraks BT ile sınırlı.</b> Başka modalite ya da bölge için yeniden türetilmesi gerekir.</li>
        <li><b>Kapsam boşlukları var.</b> Bu sayfadaki modeller <code>pneumatocele</code>,
        <code>scoliosis</code>, <code>cavitary</code>, <code>suture</code> gibi gerçek bulgulara ad uydurdu —
        çünkü 144'lük listede karşılıkları yok. Bu, envanterin dışarıdan bir denetimi sayılır.</li>
      </ul>
    </div>
  </details>
</div>
<div class="intro">
  <h2>Modeller neden başarısız oldu</h2>
  <p class="ipucu" style="margin-top:0">Üç model, metni okuyup <b>kapalı 144 kavramlık listeden</b> hangilerinin geçtiğini katı JSON biçiminde söyleyecekti. Kapı 2 çıktıların %100'ünün ayrıştırılabilmesini, kapı 3 liste dışı kimlik oranının <b>sıfır</b> olmasını istiyordu.</p>
  <div class="neden">
    <div class="nk"><b>Tekrar döngüsü</b><span class="who">Qwen3.5-4B · 37/46 · 31/46 · 34/46</span>
      <span class="t">Kilitlenip bitiremiyor. Bir belgede 7.000 karakter, 118 kavram — ama yalnız 47 benzersiz; biri <b>72 kez</b> tekrarlanmış. Ayrıca JSON anahtar adını düşürüyor.</span></div>
    <div class="nk"><b>Markdown çiti</b><span class="who">Aya Expanse 8B · üç kolda da 0/8</span>
      <span class="t">Cevabını kod bloğuna sarıyor — istem bunu açıkça yasaklıyor. İçerideki JSON bozuk değil; ne bulduğunu hiç göremedik.</span></div>
    <div class="nk"><b>Envanteri yok sayma</b><span class="who">Qwen3-8B · 1/8 · 2/8 · 2/8</span>
      <span class="t">Büyük model JSON'u <b>daha iyi</b> yazıyor ama ihlallerinin neredeyse tamamı kimlik uydurma. Ölçek <em>biçim</em> sorununu çözüyor, <em>envanter</em> sorununu çözmüyor.</span></div>
  </div>
  <p class="ipucu"><b>Üç farklı arıza, tek ortak duvar:</b> hiçbiri kapalı listeye uymadı. İki tür uydurma var — <b>yeniden adlandırma</b> (<code>pleural_effusion</code>, oysa bizde <code>effusion</code>) ve <b>kapsam dışı</b> (<code>pneumatocele</code>, <code>scoliosis</code> — gerçek bulgular ama listemizde yoklar). İkincisi listemizin kapsam boşluklarını gösteriyor.</p>
  <p class="ipucu">Aşağıda sözleşmeyi bozan her kolun altında <span class="chip bad" style="display:inline-block">kırmızı</span> rozetlerle <b>o modelin uydurduğu kimlikler</b> listelenir; yanında kaç tanesinin listede olduğu yazar. Kimliklerin hepsi listedeyse sorun biçimdedir (kesilme, çit, bozuk JSON) — bunu da ayrıca belirtiyoruz. <b>Ham yanıtı</b> açıp modelin gerçekte ne yazdığını okuyabilirsin.</p>
</div>
"""

CSS = (KOK / "configs" / "tezgah.css").read_text(encoding="utf-8")

CIK.write_text(
    "<title>Rapor İnceleme Tezgâhı</title>\n"
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&'
    'family=Spectral:wght@400;500;600&display=swap">\n'
    f"<style>{CSS}</style>\n"
    f'<div class="wrap">{GIRIS}{GENEL}'
    '<h3 class="sec" style="margin-top:44px">Belgeler — başlığa tıkla, o belgenin tam dökümü açılır</h3>'
    '<p class="ipucu" style="margin:0 0 14px">Her satırda belgenin adı, kavram sayıları, kaç kavramda '
    'ayrıştığı ve içinde ne göreceğine dair ipuçları var: <b>ayrışan kavramların adları</b>, kaç '
    '<b>ayırıcı tanı</b> (parantez-soru) ve kaç <b>olumsuzlama</b> içerdiği, ve o belgede modellerin '
    'kaç kolda geçerli çıktı verdiği.</p>'
    f'{"".join(parcalar)}'
    '<div class="foot">'
    '<div>Kaynak · outputs/task15/{dev_packages_v2, ceviri_dev, ikincil_model}</div>'
    '<div>Sözlük · configs/{turkce_yuzeyler_taslak, anatomi_sozlugu, bulgu_sozlugu}.yaml</div>'
    '<div>Kapılar ve çıktı sözleşmesi · docs/19 · Kararlar · docs/kararlar.md</div>'
    "</div></div>\n",
    encoding="utf-8")
print(f"{len(sirali)} belge · {CIK.stat().st_size/1024/1024:.2f} MB · {CIK}")
