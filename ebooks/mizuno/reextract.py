#!/usr/bin/env python3
"""Re-extract every downloaded PDF with the -raw mode (which turned out to give
correct reading order for these vertically-typeset Japanese scans) and rewrite
txt/ + md/ without re-downloading anything.
"""
import json
import re
import subprocess
import unicodedata

BASE = "/home/webadmin/mizuno"
DIR_PDF = f"{BASE}/pdf"
DIR_TXT = f"{BASE}/txt"
DIR_MD = f"{BASE}/md"


def is_cjk(c):
    try:
        return unicodedata.name(c).startswith(("CJK", "HIRAGANA", "KATAKANA"))
    except ValueError:
        return False


def normalize(raw):
    """These are scans of vertically-typeset Japanese pages, so pdftotext emits
    one glyph per line for some files. Rebuild continuous sentences, then break
    after 。 to keep paragraphs readable.
    """
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        return ""
    if sum(1 for ln in lines if len(ln) <= 2) / len(lines) > 0.6:
        body = "".join(lines)
    else:
        body = []
        for ln in lines:
            prev = body[-1] if body else ""
            if prev and is_cjk(prev[-1]) and is_cjk(ln[0]):
                body[-1] = prev + ln
            else:
                body.append(ln)
        body = "\n".join(body)
    paragraphs = []
    for chunk in body.split("\n"):
        sentences = re.split(r"(?<=。)", chunk)
        for s in sentences:
            if s.strip():
                paragraphs.append(s.strip())
    return "\n\n".join(paragraphs)


def extract(pdf, txt_path):
    subprocess.run(["pdftotext", "-raw", "-enc", "UTF-8", pdf, txt_path],
                   check=True, capture_output=True)
    raw = open(txt_path, encoding="utf-8", errors="replace").read()
    return normalize(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw))


def write_md(rec, body, md_path):
    lines = [
        f"# {rec['title_ja'] or rec['title_en']}",
        "",
        f"- 著者: {', '.join(rec['authors']) or '水野弘元'}",
        f"- 掲載誌: {rec['journal_ja'] or rec['journal_en']} "
        f"{rec['volume']}({rec['number']}) pp.{rec['pages']} ({rec['year']})",
        f"- DOI: {rec.get('doi', '')}",
        f"- URL: {rec['link']}",
        "",
        "---",
        "",
        body,
        "",
    ]
    open(md_path, "w", encoding="utf-8").write("\n".join(lines))


manifest = json.load(open(f"{BASE}/manifest.json"))
ok, bad = 0, []
for m in manifest:
    pdf = f"{DIR_PDF}/{m['slug']}.pdf"
    try:
        body = extract(pdf, f"{DIR_TXT}/{m['slug']}.txt")
    except subprocess.CalledProcessError as exc:
        bad.append((m["slug"], str(exc)))
        continue
    write_md(m, body, f"{DIR_MD}/{m['slug']}.md")
    m["chars"] = len(body)
    m["status"] = "needs_ocr" if len(body) < 300 else "ok"
    ok += 1

json.dump(manifest, open(f"{BASE}/manifest.json", "w"), ensure_ascii=False, indent=2)
print(f"re-extracted {ok} articles; failures: {bad}")
