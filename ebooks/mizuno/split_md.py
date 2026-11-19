#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 mizuno/md 下「整段成一行」的 md 重新按句斷行, 便於閱讀/翻譯。
用法: python3 split_md.py <in.md> <out.txt>
- 保留頂部 metadata(- 開頭)與 '---' 分隔不動
- 其後正文按 。(ASCII .) ！？ ︒ ︑ 等切句, 每行一句; 過長句再按 、 或 120 字兜底斷行
"""
import re, sys

inp, outp = sys.argv[1], sys.argv[2]
text = open(inp, encoding="utf-8").read()

lines = text.split("\n")
head, body_lines = [], []
flushed = False
for ln in lines:
    if not flushed and (ln.startswith("- ") or ln.strip() == "---" or ln.startswith("#")):
        head.append(ln)
        if ln.strip() == "---":
            flushed = True
        continue
    if not flushed:
        head.append(ln)
        continue
    body_lines.append(ln)

body = "\n".join(body_lines)

# 先按句末標點切
parts = re.split(r"(?<=[\u3002\uFF0E\uFF61\uFF09\uFF01\uFF1F\.\!\?])", body)
out = []
for p in parts:
    p = p.strip()
    if not p:
        continue
    # 過長句子兜底: 按 、 或 逗號 或每 120 字斷
    while len(p) > 120:
        cut = p.rfind("、", 0, 120)
        if cut < 0:
            cut = p.rfind("，", 0, 120)
        if cut < 0:
            cut = 119
        out.append(p[:cut + 1])
        p = p[cut + 1:]
    out.append(p)

with open(outp, "w", encoding="utf-8") as f:
    f.write("\n".join(head) + "\n\n" + "\n".join(out) + "\n")
print("wrote", outp, "body lines:", len(out))
