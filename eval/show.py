"""Print the paragraphs around a location, with indices, for reading context.

Usage: python eval/show.py <source_id> <chapter> <start> <end>
"""

import json
import sys
from pathlib import Path


def show(source_id: str, chapter: int, start: int, end: int):
    book = json.loads(Path(f"data/parsed/standard_ebooks/{source_id}.json").read_text())
    ch = next(c for c in book["chapters"] if c["num"] == chapter)
    for i in range(max(0, start), min(end + 1, len(ch["paragraphs"]))):
        print(f"[{chapter}, {i}]  {ch['paragraphs'][i]}\n")


if __name__ == "__main__":
    sid, ch, s, e = sys.argv[1], *map(int, sys.argv[2:5])
    show(sid, ch, s, e)
