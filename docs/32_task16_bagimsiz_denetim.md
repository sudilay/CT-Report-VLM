# TASK-16 · Planın Bağımsız Denetimi ve Karara Bağlanması

**Tarih:** 2026-09-03 · **Denetleyen:** Gemini (bağımsız, depoya erişimsiz)
**Denetlenen:** `docs/29_task16_calisma_plani.md` v1 (691 satır)
**Sonuç:** plan **v2**'ye revize edildi · v1 uygulanmadı

> TASK-15'te `docs/24` ile aynı işlevi görür: planı yazan taraf dışında bir gözün
> kusur araması. Denetleyiciye depo, korpus, karar defteri ve önceki raporlar
> **verilmedi** — yalnız plan metni ve bir bağlam özeti verildi. Bu, bazı
> itirazların bilgi eksikliğinden doğmasına yol açtı; öyle olanlar aşağıda
> **reddedildi** ve gerekçesi yazıldı.

---

## 1 · Denetimin hükmü

> *"Bu plan mevcut haliyle uygulamaya hazır DEĞİLDİR; çünkü kural içermeyen bir
> alan sözlüğünden türetilen ~40 kararı 'aktarılan (A)' sayarak klinik denetimden
> kaçırmakta, döngüsel/biçimsel kabul ölçütlerine dayanmakta ve projenin ana
> misyonu olan yanlış pozitifleri baskılamayı denetleyecek hiçbir koruma kapısı
> içermemektedir."*

**Bu hüküm kabul edildi.** Plan v1 uygulanmadı; v2 yazıldı.

---

## 2 · Üç bulgu planı yapısal olarak değiştirdi

### 2.1 Faz 2'nin çıkarım hatalarının çarpan etkisi *(KRİTİK)*

Denetim, şemanın **girdi katmanının bilinen kusurlarını** hesaba katmadığını
buldu. Bu, projenin **kendi ölçümleriyle** doğrulanıyor:

| ölçüm | değer | kaynak |
|---|---|---|
| K7 · `prior` F1 | **%36,4** — eşiği geçemedi | `test-v2`, D39 |
| `uncertain` duyarlılığı | **%71 / %46** | `test-v2` |
| sebebi | D29 belirsizlik ipuçlarını `cikarim_ifadesi` → `present` yapmıştı | kayıtlı |

Çıkarım katmanı **geçmiş bir nodülü `present` verme eğiliminde** ve şemanın
*"en yüksek şüphe kazanır"* mantığı bunu doğrudan maligniteye yükseltir —
projenin ana hedefi olan **yanlış pozitif azaltmanın tam tersi.**

Denetleyici bu sayıları görmeden bulguyu buldu. → **v2 §7 girdi kalite filtresi**

### 2.2 Yanlış pozitif koruma kapısı yok *(KRİTİK)*

Projenin ayırt edici vurgusu *"malignite yakalamak değil yanlış pozitifleri
azaltmak"*. v1'in kabul ölçütlerinde bunu sınayan **tek bir ölçüt yoktu.**
→ **v2 §8.3 Negatif/Benign Koruma Kapısı**

### 2.3 A/C sınıflaması otorite modelini sakatlıyordu *(KRİTİK)*

v1 §1.1'de *"belge NE çıkarılacağını söyler, NASIL karar verileceğini söylemez"*
yazıp, v1 §2.2'de belgeden **~40 kuralı "A · aktarılan, onay gerekmez"** diye
sınıflamıştı. **Kendi içinde çelişki.** Öncelik, eşik ve ağırlık kuralları plan
yazarının kurgusudur → **C**.

**Kabul edilen sonuç dürüstçe kaydedilir: C listesi şişer.** v1'in "15-25 madde" tahmini geçersizdir. → **v2 §2 katmanlı C listesi**

---

## 3 · Bütün bulguların karara bağlanması

| # | bölüm | bulgu | önem | karar |
|---|---|---|---|---|
| 1 | §9-B.5 | "beklenen prevalans"ın dış kaynağı yok, kural sübjektif beklentiye göre bükülüyor | KRİTİK | ✅ kabul |
| 2 | §8/4 | kurallar yazılmadan sınıf prevalansı ölçülemez | ÖNEMLİ | ✅ kabul |
| 3 | §8/6 | "her cümle tam bir sınıfa düşer" yalnız **kapsamayı** sınıyor; her şeyi `indeterminate` diyen naif kural da geçer | KRİTİK | ✅ kabul |
| 4 | §4.3 | boyutu/kotası belirsiz held-out havuz metodolojik olarak geçersiz | KRİTİK | ✅ kabul |
| 5 | §6.1-2 | örnek cümleler bölünme ayrılmadan tüm korpustan çekildi | ÖNEMLİ | ✅ kabul |
| 6 | §2.2 | "15-25 C maddesi" ampirik değil temenni | ÖNEMLİ | ✅ kabul |
| 7 | §8/3 | 40 kural / 6 saat gerçekçi değil | KÜÇÜK | ✅ kabul |
| 8 | §8/3 | "bölüm numarası yazılmış" ölçütü türetmeyi denetlemiyor | ÖNEMLİ | ✅ kabul |
| 9 | §8/8-9 | biçimsel kabul ölçütleri kalite kapısı sanılıyor | KÜÇÜK | ✅ kabul |
| 10 | §9-B | Faz 2 çıkarım hatalarının çarpan etkisi için yedek yok | KRİTİK | ✅ kabul — §2.1 |
| 11 | §9-B | kılavuzlar çatışınca öncelik hiyerarşisi yok | ÖNEMLİ | ✅ kabul ⚠ önceliğin **kendisi C maddesidir**, plan yazarı belirleyemez |
| 12 | §9-B.1 | alan sözlüğünün kullanılamaz hâle gelme ihtimali atlanmış | ÖNEMLİ | ✅ kabul |
| 13 | §2.2/§1.1 | ~40 kuralın A sayılması | KRİTİK | ✅ kabul — §2.3 |
| 14 | §5.1 | 6→4 eşlemesi klinik karardır, mühendislik seçimi değil | ÖNEMLİ | ✅ kabul |
| 15 | §2.2 | `sequela` sıklığı (B) benignliği kanıtlamaz | ÖNEMLİ | ✅ kabul — ince ve doğru |
| 16 | §3.5 vs §3.6 | NLST erişimi hakkında iki çelişkili ifade | ÖNEMLİ | ✅ kabul |
| 17 | §2.4 vs §2.5 | "belge onaylı bir çerçeve sayılır" ↔ "onay izi yok, varsayılamaz" | ÖNEMLİ | ✅ kabul, §2.4 geri çekildi |
| 18 | §5.1 | "bilgi kaybı" ↔ "kayıpsızdır" | KÜÇÜK | ⚠ ifade düzeltildi; tasarım (6+1 sakla, 4 raporla) korundu |
| 19 | §4.3 | "T-13" yanlış atıf | KÜÇÜK | ❌ **reddedildi** — §4 |
| 20 | §8/8 | HTML tezgah 25-30 vaka için aşırı | ÖNEMLİ | ⚠ **kısmen** — §5.1 |
| 21 | §7.2 | Sybil'in 27 alanı TASK-16'yı şişiriyor | ÖNEMLİ | ✅ kabul, kapsam dışına alındı |
| 22 | §8/7 | Codex kör yargılaması yapay | KÜÇÜK | ⚠ **kısmen** — §5.2 |
| 23 | §7.2/§3.3 | tarama kohortu kılavuzu ≠ genel/akut toraks BT | KRİTİK | ✅ kabul |
| 24 | §8/6 | FP koruma kapısı yok | KRİTİK | ✅ kabul — §2.2 |
| 25 | §6.2 | karaciğeri "kapsam dışı organ" saymak | ÖNEMLİ | ✅ kabul |

**Toplam:** 25 bulgu · **21 tam kabul** · **3 kısmi** · **1 red**

---

## 4 · Reddedilen bulgu ve gerekçesi

**#19 — "T-13 yanlış atıf" (§4.3).**

Denetleyici, planın *"T-13'te ölçülen doğruluk şişkin çıkar"* ifadesini hatalı
sayıp *"T-03/T-04 veya TASK-19"* ile değiştirilmesini önerdi. **Bu bir bilgi
eksikliğidir:** projede **iki ayrı numaralandırma** vardır.

| sistem | ne | örnek |
|---|---|---|
| `T-nn` | kaynak listedeki **14 madde** (`radyoloji_raporu_degerlendirme_tasklari.xlsx`) | **T-13** = *"AUROC, duyarlılık, özgüllük, F1, NPV, PPV… ground truth üzerinden karşılaştırma"* — Faz 5 |
| `TASK-nn` | plandaki **47 görev** (`RADYOLOJI_VLM_TASK_LISTESI.xlsx`) | **TASK-13** = elle doğrulama, **tamamlandı** |

Plandaki kullanım **doğruydu**: bölünme kirlenirse şişecek olan şey Faz 5'in
değerlendirme sayılarıdır.

⚠ **Ama altta yatan gözlem haklıdır:** iki sistem karıştırılabilir. v2'ye
**numaralandırma uyarısı** eklendi (v2 §0).

---

## 5 · Kısmen kabul edilen ikisi

### 5.1 HTML inceleme tezgâhı *(#20)*

Denetleyici 25-30 vaka için özel HTML sayfası geliştirmeyi aşırı buldu ve
CSV/Markdown önerdi. **Teknik olarak haklı.**

**Ama yürütücü kararı bunun aksine:** TASK-15'in inceleme tezgâhı gözle
denetimde işe yaramıştı ve yürütücü aynısını açıkça istedi. Bu bir **inceleme
ergonomisi** tercihidir, metodolojik bir kusur değil.

**Karar: tezgâh kalıyor.** Ama kanonik kayıt CSV'dir; tezgâh o CSV'den **üretilir**
ve kendi başına veri kaynağı değildir.

### 5.2 Codex bağımsız yargılaması *(#22)*

Denetleyici *"iki dil modelinin uzlaşması altın standart üretmez"* dedi —
**doğru, ama adımın amacı o değildi.** Amaç **ayrışmayı teşhis olarak
kullanmaktı**: TASK-13'te kappa **0,479** çıkmış, sebebi kılavuz boşluğu
olduğu anlaşılmış, kural yazılınca **0,845** olmuştu (D37). Bu, bu projede
**ölçülmüş** bir faydadır ve denetleyici o geçmişi bilmiyordu.

**Karar: adım kalıyor, iddiası küçülüyor.** Codex artık *"altın üretici"* değil,
**C kaydında hangi vakaların öncelikli işaretleneceğini belirleyen ayrışma dedektörü**.
Uyuştukları vakalar kayıtta alta iner; ayrıştıkları üste çıkar.

---

## 6 · Denetimin görebildikleri ve göremedikleri

**Göremedi** (depo verilmediği için): karar defteri D1–D69 · korpus ölçümleri ·
önceki raporlar · iki numaralandırma sistemi · TASK-13/14/15'in ölçülmüş
sonuçları.

**Buna rağmen bulduğu en güçlü iki şey** (§2.1, §2.2) bu bilgilerin
**hiçbirini gerektirmiyordu** — planın kendi iç tutarlılığından ve projenin
ilan edilmiş misyonundan çıkarılabiliyordu. Denetimin değeri buradadır.

**Çıkarılan ders:** planı yazan taraf, kendi planının misyonla çelişen yerini
göremiyor. Bu denetim TASK-17 ve TASK-18 planları için de tekrarlanacaktır.
