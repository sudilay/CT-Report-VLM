# TASK-15 · RadTr Kanonik Kavram Altını Normalizasyon Protokolü

**Tarih:** 2026-09-01  
**Durum:** Protokol donduruldu; `train/dev` pilotu ve işaretleme paketleri henüz
üretilmedi; RadTr `test` açılmadı.

## 1. Neden gerekli

RadTr bağımsız radyolog span'ları ve genel NER etiketleri sağlar:
`Obs_Present`, `Obs_Absent`, `Obs_Uncertain`, `Obs_Anatomy`,
`Obs_Technical`, `Obs_Advice` ve `Differential Diagnosis`. Bunlar raporda bir
varlığın nerede olduğunu ve gözlemin kesinliğini verir; fakat span'a
`nodule`, `effusion` veya `cardiomegaly` gibi kanonik `concept_id` atamaz.

Bu nedenle RadTr yerel etiketinden doğrudan belge düzeyi A1 kavram F1
hesaplanamaz. Türkçe sözlüğün kendi eşlemesini altın kabul etmek dairesel;
bir değerlendirme modeline altın ürettirmek de bağımsız değildir.

TASK-15 A1 için RadTr span'ları, sistem tahminlerinden kör ve iki bağımsız
ön-işaretlemeden sonra radyolog tarafından onaylanan ortak kanonik envantere
eşlenecektir.

## 2. İddia sınırı

Üretilen altın şu soruyu yanıtlar:

> Rapor metninde hangi kanonik kavramlar hangi kesinlikle ileri sürülüyor?

Şunları yanıtlamaz:

- gerçek hastada bulgu var mı,
- kesin klinik tanı nedir,
- lezyon malign mi,
- patoloji sonucu nedir.

RadTr sentetiktir: metinler radyolog yazımıdır, fakat gerçek hasta, görüntü,
patoloji ve takip bağlantısı yoktur. Bu yüzden çıktı **rapor-anlamı altınıdır**,
hasta-tanısı ground truth'u değildir.

## 3. Dondurulan envanter ve birim

- Kanonik envanter TASK-15'in dondurulmuş **144 `concept_id`** listesidir.
- Yeni Türkçe yüzey yeni kavram demek değildir; mevcut kimliğe eşlenir.
- Testte yeni `concept_id` eklenmez. Karşılığı bulunmayan span `unmapped`
  olarak korunur ve oranı raporlanır.
- Birim RadTr'nin altın span'ıdır; nihai A1 puanında belge içindeki kanonik
  kimlikler tekilleştirilir.
- Bileşik bir span birden fazla açık kavram taşıyorsa `concept_ids` bir liste
  olabilir. Bu kural önce `train/dev` pilotunda örnekleriyle dondurulur.
- Aynı kavram belgede farklı kesinliklerle geçiyorsa `(belge, concept_id,
  assertion)` üçlüleri ayrı korunur.

İşaretleme kaydının asgari alanları:

| alan | anlamı |
|---|---|
| `document_id` | değişmez RadTr belge kimliği |
| `span_id` | belge içinde değişmez span kimliği |
| `sentence_text` | bağlam için Türkçe kaynak cümle |
| `span_text` | RadTr'nin altın span metni |
| `radtr_label` | özgün RadTr etiketi; değiştirilmez |
| `concept_ids` | yalnız kapalı 144 envanterden sıfır, bir veya birden çok kimlik |
| `mapping_status` | `mapped`, `unmapped`, `needs_adjudication` |
| `annotator_id` | bağımsız işaretleyici kimliği |
| `note` | yalnız belirsizlik/ayrışma gerekçesi |

`Obs_Technical` D30 gereği kesinliğe katılmaz; `Obs_Advice` kesinliği
değiştirmez. Hangi RadTr etiketlerinin A1/A2/A3 paydasına girdiği `train/dev`
pilotunda tablo olarak dondurulur. Bu kapsam test görüldükten sonra değişmez.

## 4. İşaretleyiciler ve bağımsızlık

1. **A işaretleyicisi:** Claude Opus; kesin model kimliği/revizyonu kaydedilir.
2. **B işaretleyicisi:** Codex; kesin model kimliği/revizyonu kaydedilir.
3. A ve B aynı kapalı envanter, aynı kılavuz ve aynı kör paketi kullanır.
4. İkisi birbirinin dosyasını, gerekçesini veya ara sonucunu görmeden paketi
   tamamlar ve çıktı hash'iyle kilitler.
5. Sistem tahminleri, Türkçe/İngilizce sözlük eşleşmeleri, Qwen/Aya çıktıları,
   çeviriler ve skorlar işaretleyici paketine girmez.
6. Tam eşleşmeler otomatik birleşir; ayrışmalar ayrı uzlaştırma tablosuna çıkar.
7. Radyolog yalnız ayrışmaları değil, birleşmiş nihai listenin **tamamını**
   belge bağlamında inceler ve onaylar/düzeltir.

Bu nedenle nihai veri “iki modelin ortak kararı” diye değil,
**radyolog-onaylı, iki bağımsız model ön-işaretlemeli kanonik kavram altını**
diye adlandırılır. Opus ve Codex maliyeti azaltan ön-işaretleyicilerdir; klinik
son karar radyoloğundur.

## 5. Train/dev pilotu — testten önce

Test paketinden önce yalnız `train/dev` üzerinde:

1. kapalı 144 kavramın iki dilli kısa kataloğu hazırlanır,
2. span→kavram kılavuzu örneklerle yazılır,
3. bileşik span, genel anatomi, betimleyici ifade ve envanter dışı vaka
   kuralları sınanır,
4. Opus ve Codex bağımsız pilot işaretlemesi yapılır,
5. tam eşleşme, `unmapped` oranı ve ayrışma türleri ölçülür,
6. radyolog pilot örnekleri üzerinden kılavuzu onaylar,
7. kılavuz, envanter, istemler, model sürümleri ve çıktı şeması dondurulur.

Pilot sonucu kılavuz değişikliği gerektirirse değişiklik yalnız `train/dev`de
yapılır ve yeni hash yazılır. Bunlar tamamlanmadan test açılmaz.

## 6. Test bir kez açıldığında üretilecek iki ayrı paket

Tek kontrollü paketleme komutu RadTr `test`in 56 belgesini bir kez okuyup aynı
anda iki fiziksel olarak ayrı artefakt üretir:

### A · Çeviri paketi

- yalnız `document_id`, sıra ve Türkçe rapor metni,
- altın span, RadTr etiketi ve kanonik kavram içermez.

### B · Kör kavram normalizasyon paketi

- `document_id`, `span_id`, Türkçe cümle/span ve özgün `radtr_label`,
- çeviri veya herhangi bir sistem/model tahmini içermez.

İki paketin ve manifestin SHA-256 değerleri aynı anda kaydedilir. Test metnini
yeniden paketlemek, örnek seçmek veya içeriğe göre kılavuz değiştirmek yasaktır.

## 7. Ground truth ne zaman tamamlanabilir?

Kod, adaptörler, puanlayıcı, `train/dev` çevirileri ve ikincil model seçimi
önceden tamamlanabilir. Opus erişimi daha sonra geldiğinde altın normalizasyon
en son test öncesi aşamada yapılabilir.

Zorunlu sıra:

1. tüm yöntem, envanter, kılavuz, istem ve modeller `train/dev`de dondurulur,
2. test tek komutla paketlenir,
3. Opus ve Codex kör ve bağımsız işaretler,
4. radyolog bütün nihai listeyi onaylar,
5. altın dosya hash'lenip salt okunur kilitlenir,
6. ancak sonra test tahminleri açılır ve skor hesaplanır.

Test çeviri/model koşuları teknik olarak altın işaretlemeyle paralel üretilecekse
çıktılar kapalı tutulur; hiç kimse tahminleri veya ara skorları altın kilitlenmeden
görmez. En temiz ve tercih edilen sıra, altını önce kilitleyip test çıkarımını
sonra çalıştırmaktır.

## 8. Kalite ve raporlama

Rapor en az şunları verir:

- A/B span düzeyi tam eşleşme oranı,
- ayrışan ve radyologca değiştirilen kayıt sayısı,
- `mapped` ve `unmapped` span/belge sayısı,
- kavram başına destek,
- RadTr yerel etiketine göre destek,
- bileşik span sayısı,
- nihai radyolog onay tarihi ve altın dosya SHA-256 değeri.

Nadir veya tek sınıflı dağılımda kappa tek başına yorumlanmaz; ham uyum ve sınıf
destekleri zorunludur (D36).

## 9. Ölçümde kullanım

- **A1:** radyolog-onaylı belge düzeyi `concept_id` kümesine karşı P/R/F1.
- **A2:** radyolog-onaylı kavram eşlemesi + RadTr'nin dondurulmuş assertion
  eşlemesiyle `(belge, concept_id, assertion)` değerlendirmesi.
- **A3:** `present`, `absent`, `uncertain` ayrı destek/P/R/F1.
- Anatomi A1'e girer; RadTr anatomiye kesinlik vermediği için A2/A3'e girmez.
- D30 şema farkı ham ve teknik çekince hariç iki görünümle raporlanır.

