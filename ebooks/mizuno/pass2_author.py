#!/usr/bin/env python3
"""Second pass: use the author index (author='水野   弘元') to catch anything
the free-text search missed, then report the diff against the first-pass manifest.
"""
import json
import sys
import urllib.parse

sys.path.insert(0, "/home/webadmin/mizuno")
from harvest_jstage import API, NS, TARGET_JA, fetch, parse_entry, is_target  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402


def query(params):
    q = urllib.parse.urlencode({"service": "3", "count": "100", **params})
    data, _ = fetch(f"{API}?{q}")
    return ET.fromstring(data)


known = {m["link"].rstrip("/") for m in json.load(open("/home/webadmin/mizuno/manifest.json"))}
found = {}
for params in ({"author": "水野   弘元"}, {"text": "Mizuno Kogen"}, {"text": "MIZUNO Kōgen"}):
    root = query(params)
    tot = root.find("o:totalResults", NS)
    n_root = len(root.findall("a:entry", NS))
    print(f"{params}: server total={tot.text if tot is not None else '?'} returned={n_root}")
    for e in root.findall("a:entry", NS):
        rec = parse_entry(e)
        if is_target(rec):
            found[rec["link"].rstrip("/")] = rec

new = [r for link, r in found.items() if link not in known]
print(f"author-index hits by {TARGET_JA}: {len(found)}; not yet in manifest: {len(new)}")
for r in new:
    print("  NEW:", r["year"], r["title_ja"][:60], "|", r["link"])
json.dump(list(found.values()), open("/home/webadmin/mizuno/.pass2.json", "w"),
          ensure_ascii=False, indent=2)
