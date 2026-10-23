#!/usr/bin/env python3
"""Sample candidate passages from the article cache for gold annotation.

Writes data/annotations/to_annotate.jsonl: one passage per line with article_id,
report_date, headline and text. Annotate them following docs/injury_event_schema.md
and save the events to data/annotations/gold_events.jsonl (InjuryEvent format).

Usage
-----
    python scripts/sample_for_annotation.py --n 300 --seed 13
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict

from sportsnlp.data import guardian
from sportsnlp.events import preprocess
from sportsnlp.paths import ANNOTATIONS_DIR


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=300)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--negatives", type=float, default=0.1,
                        help="Fraction of non-candidate passages to include, to measure filter recall.")
    args = parser.parse_args(argv)

    articles = list(guardian.iter_unique_articles(guardian.load_cache()))
    rng = random.Random(args.seed)
    rng.shuffle(articles)

    # TODO: also draw ~args.negatives * n random non-candidate sentences, so you can
    # estimate how many injury mentions preprocess.CANDIDATE_RE misses.
    passages = []
    for article in articles:
        passages.extend(preprocess.candidate_passages(article))
        if len(passages) >= args.n:
            break

    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    out = ANNOTATIONS_DIR / "to_annotate.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for p in passages[: args.n]:
            f.write(json.dumps(asdict(p), default=str, ensure_ascii=False) + "\n")
    print(f"Wrote {min(len(passages), args.n)} passages to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
