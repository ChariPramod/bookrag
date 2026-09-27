"""Locate paragraphs matching a pattern, to build eval gold references.

Usage: python eval/find.py <source_id> "<regex>"
source_id is a Standard Ebooks slug, e.g. joseph-conrad_heart-of-darkness.
"""

import json
import re
import sys
from pathlib import Path


def find(source_id: str, pattern: str):
    book = json.loads(Path(f"data/parsed/standard_ebooks/{source_id}.json").read_text())
    rx = re.compile(pattern, re.I)
    for ch in book["chapters"]:
        for i, p in enumerate(ch["paragraphs"]):
            if rx.search(p):
                print(f"[{ch['num']}, {i}]  {p[:150]}...")


if __name__ == "__main__":
    find(sys.argv[1], sys.argv[2])
