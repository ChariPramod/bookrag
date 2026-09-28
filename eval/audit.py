"""Print every question next to its gold paragraphs, for a one-sitting audit.

Usage: python eval/audit.py > eval/audit.txt
"""

import json
from pathlib import Path

questions = [json.loads(l) for l in Path("eval/questions.jsonl").read_text().splitlines() if l.strip()]
books = {}
for q in questions:
    sid = q["source_id"]
    books.setdefault(sid, json.loads(Path(f"data/parsed/standard_ebooks/{sid}.json").read_text()))
    chapters = {c["num"]: c for c in books[sid]["chapters"]}
    print("=" * 100)
    print(f"{q['id']} [{q['type']}]  Q: {q['question']}")
    print(f"A: {q['answer']}\n")
    for ch, p in q["gold"]:
        print(f"  [{ch}, {p}] {chapters[ch]['paragraphs'][p][:400]}\n")
