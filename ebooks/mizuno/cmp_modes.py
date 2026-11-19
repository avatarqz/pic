#!/usr/bin/env python3
import re
import subprocess
import unicodedata

PDFS = [
    "/home/webadmin/mizuno/pdf/1952-001-Arthapada-Sutra-義足經-について.pdf",
    "/home/webadmin/mizuno/pdf/1942-901-心心所思想の発生過程に就て.pdf",
    "/home/webadmin/mizuno/pdf/1971-020-原始仏教における教育思想.pdf",
]


def run(pdf, mode):
    out = "/tmp/cmp.txt"
    cmd = ["pdftotext", "-f", "1", "-l", "1", "-enc", "UTF-8"]
    if mode:
        cmd.append(mode)
    cmd += [pdf, out]
    subprocess.run(cmd, check=True, capture_output=True)
    return open(out, encoding="utf-8", errors="replace").read()


def is_cjk(c):
    try:
        return unicodedata.name(c).startswith(("CJK", "HIRAGANA", "KATAKANA"))
    except ValueError:
        return False


def normalize(raw):
    lines = [re.sub(r"\s+", " ", l).strip() for l in raw.splitlines()]
    lines = [l for l in lines if l]
    if not lines:
        return ""
    short = sum(1 for l in lines if len(l) <= 2)
    vertical = short / len(lines) > 0.6
    if vertical:
        text = "".join(lines)
    else:
        text = []
        for l in lines:
            prev = text[-1] if text else ""
            if prev and is_cjk(prev[-1]) and is_cjk(l[0]):
                text[-1] = prev + l
            else:
                text.append(l)
        text = "\n".join(text)
    return re.sub(r"\n{3,}", "\n\n", text)


for pdf in PDFS:
    print("=" * 20, pdf.split("/")[-1])
    for mode in ["-raw", "", "-layout"]:
        try:
            n = normalize(run(pdf, mode))
        except subprocess.CalledProcessError:
            continue
        print(f"-- mode={mode or 'default'} len={len(n)}")
        print(n[:260].replace("\n", " / "))
        print()
