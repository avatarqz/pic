#!/usr/bin/env python3
"""Build index.md / manifest.csv from the current manifest.json."""
import csv
import json

BASE = "/home/webadmin/mizuno"

manifest = json.load(open(f"{BASE}/manifest.json"))
manifest.sort(key=lambda m: (m["year"] or "", m["title_ja"] or m["title_en"]))

lines = [
    "# 水野弘元 著作（J-STAGE 开放获取全文）",
    "",
    "来源：J-STAGE 官方检索 API（service=3）。仅收录版权允许开放获取的学术论文，"
    "共 {} 篇，约 {} 万字。单行本・译本仍有著作权（保护至 2076 年），不在本目录中。".format(
        len(manifest), round(sum(m.get("chars", 0) for m in manifest) / 10000)
    ),
    "",
    "| 年 | 标题 | 刊物 | 卷(号) | 页码 | txt | md | DOI |",
    "|---|---|---|---|---|---|---|---|",
]
for m in manifest:
    title = m["title_ja"] or m["title_en"] or "（无标题）"
    lines.append(
        "| {} | {} | {} | {}({}) | {} | [txt](txt/{}.txt) | [md](md/{}.md) | {} |".format(
            m["year"], title, m["journal_ja"] or m["journal_en"], m["volume"], m["number"],
            m["pages"], m["slug"], m["slug"], m["doi"],
        )
    )
open(f"{BASE}/index.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")

with open(f"{BASE}/manifest.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "title_ja", "title_en", "journal", "vol", "no", "pages", "doi",
                "chars", "status", "md", "txt", "pdf"])
    for m in manifest:
        w.writerow([m["year"], m["title_ja"], m["title_en"], m["journal_ja"] or m["journal_en"],
                    m["volume"], m["number"], m["pages"], m["doi"], m.get("chars", ""),
                    m["status"], f"md/{m['slug']}.md", f"txt/{m['slug']}.txt", f"pdf/{m['slug']}.pdf"])
print("wrote index.md and manifest.csv for", len(manifest), "articles")
