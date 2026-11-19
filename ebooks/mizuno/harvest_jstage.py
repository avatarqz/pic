#!/usr/bin/env python3
"""Harvest open-access articles authored by 水野弘元 (Mizuno Kogen) from J-STAGE.

Only open-access PDFs are downloaded: a candidate URL is kept only when the
response Content-Type is application/pdf. paywalled articles are skipped and
recorded in the manifest as "skipped".
"""
import csv
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path("/home/webadmin/mizuno")
DIR_PDF = BASE / "pdf"
DIR_TXT = BASE / "txt"
DIR_MD = BASE / "md"
API = "https://api.jstage.jst.go.jp/searchapi/do"
UA = "Mozilla/5.0 (compatible; MizunoResearchHarvest/0.1)"
NS = {
    "a": "http://www.w3.org/2005/Atom",
    "p": "http://prismstandard.org/namespaces/basic/2.0/",
    "o": "http://a9.com/-/spec/opensearch/1.1/",
}
TARGET_JA = "水野弘元"
TARGET_EN = "kogenmizuno"
SLEEP = 1.0


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def txt(node, path):
    n = node.find(path, NS)
    return (n.text or "").strip() if n is not None else ""


def collect_entries():
    entries, start = [], 1
    total = None
    while True:
        q = urllib.parse.urlencode(
            {"service": "3", "text": TARGET_JA, "count": "100", "start": str(start)}
        )
        data, _ = fetch(f"{API}?{q}")
        root = ET.fromstring(data)
        got = root.findall("a:entry", NS)
        if total is None:
            t = root.find("o:totalResults", NS)
            total = int(t.text) if t is not None else 0
        entries.extend(got)
        start += len(got)
        print(f"  fetched {len(entries)}/{total}")
        if not got or (total and len(entries) >= total):
            break
        time.sleep(SLEEP)
    return entries


def parse_entry(e):
    link_ja = txt(e, "a:article_link/a:ja") or txt(e, "a:id")
    authors = [re.sub(r"\s+", "", (n.text or "")) for n in e.findall("a:author/a:ja/a:name", NS)]
    authors_en = [re.sub(r"\s+", "", (n.text or "")).lower() for n in e.findall("a:author/a:en/a:name", NS)]
    return {
        "title_ja": txt(e, "a:article_title/a:ja"),
        "title_en": txt(e, "a:article_title/a:en"),
        "authors": authors,
        "journal_ja": txt(e, "a:material_title/a:ja"),
        "journal_en": txt(e, "a:material_title/a:en"),
        "year": txt(e, "a:pubyear"),
        "volume": txt(e, "p:volume"),
        "number": txt(e, "p:number"),
        "pages": f'{txt(e, "p:startingPage")}-{txt(e, "p:endingPage")}',
        "doi": txt(e, "p:doi"),
        "link": link_ja,
        "_authors_en": authors_en,
    }


def is_target(rec):
    return any(TARGET_JA in a for a in rec["authors"]) or any(
        TARGET_EN in a.replace(" ", "") for a in rec["_authors_en"]
    )


def slug(rec, i):
    year = rec["year"] or "0000"
    base = re.sub(r"[^\w一-鿿]+", "-", (rec["title_ja"] or rec["title_en"] or "untitled")).strip("-")
    return f"{year}-{i:03d}-{base[:40]}"


def pdf_candidates(link):
    link = link.rstrip("/")
    base = re.sub(r"/_article(/.*)?$", "", link)
    return [f"{base}/_pdf", base.replace("/_article", "/_pdf") + "/_pdf", link + "/_pdf"]


def try_download(link, dest):
    seen = set()
    for url in pdf_candidates(link):
        if url in seen:
            continue
        seen.add(url)
        try:
            data, ctype = fetch(url, timeout=90)
        except Exception as exc:
            print(f"    ! {url} -> {exc}")
            continue
        if "application/pdf" in ctype and data[:4] == b"%PDF":
            dest.write_bytes(data)
            return url
        print(f"    x {url} -> {ctype[:40] or 'no content-type'}")
        time.sleep(0.5)
    return None


def to_text(pdf_path, txt_path):
    subprocess.run(
        ["pdftotext", "-enc", "UTF-8", "-layout", str(pdf_path), str(txt_path)],
        check=True, capture_output=True,
    )
    raw = txt_path.read_text(encoding="utf-8", errors="replace")
    body = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw)
    return body.strip()


def write_md(rec, body, md_path):
    title = rec["title_ja"] or rec["title_en"]
    meta = [
        f"# {title}",
        "",
        f"- 著者: {', '.join(rec['authors']) or '水野弘元'}",
        f"- 掲載誌: {rec['journal_ja'] or rec['journal_en']} {rec['volume']}({rec['number']}) pp.{rec['pages']} ({rec['year']})",
        f"- DOI: {rec['doi']}",
        f"- URL: {rec['link']}",
        "",
        "---",
        "",
        body,
    ]
    md_path.write_text("\n".join(meta), encoding="utf-8")


def main():
    for d in (DIR_PDF, DIR_TXT, DIR_MD):
        d.mkdir(parents=True, exist_ok=True)

    print("[1] searching J-STAGE ...")
    entries = collect_entries()
    recs = [parse_entry(e) for e in entries]
    mine = [r for r in recs if is_target(r)]

    seen, unique = set(), []
    for r in mine:
        key = r["link"]
        if key not in seen:
            seen.add(key)
            unique.append(r)
    unique.sort(key=lambda r: (r["year"] or "", r["journal_ja"]))
    print(f"[2] {len(recs)} raw hits -> {len(unique)} authored by {TARGET_JA}")

    manifest = []
    for i, rec in enumerate(unique, 1):
        s = slug(rec, i)
        print(f"  [{i}/{len(unique)}] {rec['year']} {rec['title_ja'][:40]}")
        status, source = "skipped_paywalled", ""
        try:
            source = try_download(rec["link"], DIR_PDF / f"{s}.pdf")
        except Exception as exc:
            print(f"    ! {exc}")
        if source:
            body = to_text(DIR_PDF / f"{s}.pdf", DIR_TXT / f"{s}.txt")
            write_md(rec, body, DIR_MD / f"{s}.md")
            status = "needs_ocr" if len(body) < 300 else "ok"
            print(f"    saved {len(body)} chars ({status})")
        rec_out = {k: v for k, v in rec.items() if not k.startswith("_")}
        rec_out.update({"slug": s, "status": status, "pdf_source": source})
        manifest.append(rec_out)
        time.sleep(SLEEP)

    (BASE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (BASE / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "title_ja", "journal_ja", "vol", "no", "pages", "doi", "status", "file"])
        for m in manifest:
            w.writerow([m["year"], m["title_ja"], m["journal_ja"], m["volume"], m["number"],
                        m["pages"], m["doi"], m["status"], f"md/{m['slug']}.md"])

    ok = sum(1 for m in manifest if m["status"] == "ok")
    print(f"[3] done: {len(manifest)} articles listed, {ok} open-access full texts downloaded")


if __name__ == "__main__":
    main()
