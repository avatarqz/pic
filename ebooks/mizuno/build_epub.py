#!/usr/bin/env python3
"""Pack the extracted markdown into a single EPUB (one chapter per article)."""
import json
import re

from ebooklib import epub

BASE = "/home/webadmin/mizuno"

books = json.load(open(f"{BASE}/manifest.json"))
books.sort(key=lambda m: (m["year"] or "", m["title_ja"] or m["title_en"]))

book = epub.EpubBook()
book.set_identifier("mizuno-kogen-jstage-open-access")
book.set_title("水野弘元 論文集（J-STAGE 公開アクセス）")
book.set_language("ja")
book.add_author("水野弘元")

chapters, toc = [], []
for i, m in enumerate(books, 1):
    md_path = f"{BASE}/md/{m['slug']}.md"
    body = open(md_path, encoding="utf-8").read()
    body = body.split("---\n", 1)[-1]
    title = m["title_ja"] or m["title_en"] or m["slug"]
    html = "".join(
        f"<p>{re.sub(chr(10)+'+', '', p).strip()}</p>"
        for p in body.split("\n\n") if p.strip()
    )
    ch = epub.EpubHtml(title=title, file_name=f"chap_{i:02d}.xhtml", lang="ja")
    ch.content = f"<h1>{title}</h1>{html}"
    chapters.append(ch)
    toc.append(ch)

for ch in chapters:
    book.add_item(ch)
book.toc = tuple(toc)
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())
book.spine = ["nav"] + chapters

out = f"{BASE}/水野弘元論文集.epub"
epub.write_epub(out, book)
print(f"wrote {out} with {len(chapters)} chapters")
