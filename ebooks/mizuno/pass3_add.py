#!/usr/bin/env python3
"""Download a specific list of article links and append them to the manifest."""
import json
import sys

sys.path.insert(0, "/home/webadmin/mizuno")
from harvest_jstage import (DIR_MD, DIR_PDF, DIR_TXT, SLEEP, slug,  # noqa: E402
                            to_text, try_download, write_md)
from pass2_author import found  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402

manifest = json.load(open("/home/webadmin/mizuno/manifest.json"))
known = {m["link"].rstrip("/") for m in manifest}

added = 0
for link, rec in found.items():
    if link in known:
        continue
    s = slug(rec, 900 + added)
    print(f"[+] {rec['year']} {rec['title_ja'][:50]}")
    status, source = "skipped_paywalled", ""
    source = try_download(rec["link"], DIR_PDF / f"{s}.pdf")
    body = ""
    if source:
        body = to_text(DIR_PDF / f"{s}.pdf", DIR_TXT / f"{s}.txt")
        write_md(rec, body, DIR_MD / f"{s}.md")
        status = "needs_ocr" if len(body) < 300 else "ok"
        print(f"    saved {len(body)} chars ({status})")
    out = {k: v for k, v in rec.items() if not k.startswith("_")}
    out.update({"slug": s, "status": status, "pdf_source": source})
    manifest.append(out)
    added += 1
    time.sleep(SLEEP)

manifest.sort(key=lambda m: (m["year"] or "", m["title_ja"]))
json.dump(manifest, open("/home/webadmin/mizuno/manifest.json", "w"), ensure_ascii=False, indent=2)
print(f"added {added}; total now {len(manifest)}")
