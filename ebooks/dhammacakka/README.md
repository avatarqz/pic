# 轉法輪經 巴利 ⇄ 漢 平行對齊

## 對齊對象
- **巴利**: SN 56.11 《Dhammacakkappavattanasuttaṃ》(CSCD / Chaṭṭha Saṅgāyana, 編號 1081)
  來源: `/home/webadmin/.buddha/tipitaka-xml/romn/s0305m.mul.xml` (Saṃyuttanikāyo Mahāvagga)
  清洗後逐句: `sn56.11_pali.txt` (33 句)
- **漢譯**: T02n0109 《佛說轉法輪經》(東漢·安世高) — 自由意譯本
  逐句: `t0109_zh_sent.txt` (31 句)

## 對齊方法
`align_interlinear.py` — 純標準庫實現的 Gale-Church 句級統計對齊
(跨文字體句長規一化: CJK/藏/梵按「字」計, 拉丁按「詞」計; 本機無法訪問
HuggingFace, 故 embedding 類對齊器無法使用)。

```
python3 align_interlinear.py sn56.11_pali.txt t0109_zh_sent.txt \
        --src-lang pi --tgt-lang lzh --format text  --out alignment_dhammacakka.txt
python3 align_interlinear.py sn56.11_pali.txt t0109_zh_sent.txt \
        --src-lang pi --tgt-lang lzh --format tsv   --out alignment_dhammacakka.tsv
python3 align_interlinear.py sn56.11_pali.txt t0109_zh_sent.txt \
        --src-lang pi --tgt-lang lzh --format html  --out alignment_dhammacakka.html
```

## 產出
- `alignment_dhammacakka.txt` — 終端/閱讀用逐行對照
- `alignment_dhammacakka.tsv` — 檢索用 (巴利句群 \t 漢譯句群)
- `alignment_dhammacakka.html` — 瀏覽器檢視的 interlinear 頁面

## 重要說明 (對齊品質)
安世高本為**自由意譯 + 增刪**, 並非逐句直譯:
- 開頭新增「自然法輪飛來當佛前轉 / 佛以手撫輪曰止」的情節 (巴利無對應)。
- 四聖諦的「三轉十二行」(tiparivaṭṭaṃ dvādasākāraṃ) 在漢譯中被壓縮,
  故若干巴利句(尤其 "cakkhuṃ udapādi" 一系列)在漢譯裡找不到一一對應句。
- 因此本對齊為**段落級 / 大意對應**, 標記為「(无对应)」的區塊屬正常,
  多為上述增刪處, 而非工具錯誤。

若需要**逐句嚴格對應**的平行本, 建議改用結構貼近巴利的漢譯平行本,
例如《雜阿含經》(T02n0099, 對應 SA 379) 或《別譯雜阿含經》(T02n0100),
二者皆保留「四諦 + 三轉」結構, 可得到近 1:1 的乾淨對齊。需要時可經
buddha/fojin MCP 抓取。
