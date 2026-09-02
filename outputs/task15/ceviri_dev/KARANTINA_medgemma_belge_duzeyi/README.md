# KARANTINA · MedGemma belge düzeyi post-edit — kullanılamaz

2026-09-01, uzak 8 GB makine, 46 `dev` belgesi, 22 dakika. Provenance zinciri
doğru (girdi hash'i bizim Google çıktımızla birebir). Sorun teknik değil,
**davranışsal**: MedGemma post-edit yapmadı, raporu yeniden yazdı.

| ölçüm | sonuç |
|---|---|
| sayıları koruyan **ve** Markdown'sız belge | **0 / 46** |
| Markdown (`**`, `*`, `#`) içeren çıktı | 37 / 46 (%80) |
| ölçüm düşen | 21 / 46 |
| ölçüm uydurulan / değiştirilen | 2 / 46 |
| `TECHNIQUE` bölümü kaybolan | 13 / 44 |
| en çok kısalan belge | asıl uzunluğun **%13'ü** |

En açık örnek `_59_140`: girdide kot kırıkları, 2 cm pnömotoraks ve 30x25 mm
pnömatosel ölçülü olarak yazılı. Çıktı:

```
**IMPRESSION:**
RIGHT-SIDED RIB FRACTURES WITH PNEUMOTHORAX AND PNEUMATOCOLE.
RIGHT-SIDED THYROID NODULE.
ASCENDING AORTA ANEURYSM.
```

Bütün ölçümler yok, rapor bir **impression** özetine dönüşmüş. Bu, `docs/19`
§4/4'ün ("bulgu silemez, sayısal değeri değiştiremez, özetleyemez") doğrudan
ihlali.

**Sebep:** istem "Rewrite the English radiology report" diyordu — bu bir yeniden
yazma daveti. Markdown ve impression üretimi ayrıca yasaklanmamıştı. Model
varsayılan "yardımcı radyoloji asistanı" davranışına düştü.

Bu artefakt hiçbir ölçüme girmeyecek. `dev`in işi tam olarak buydu: hatayı
`test` açılmadan yakaladık.
