#!/usr/bin/env python3
"""Run the injury event pipeline over the article cache.

    cache -> candidate passages -> extractor -> linking -> temporal grounding
          -> data/processed/events_<extractor>.jsonl

Usage
-----
    python scripts/extract_events.py --extractor rules
    python scripts/extract_events.py --extractor llm --limit 200
"""
from __future__ import annotations

import argparse
from contextlib import closing

from sportsnlp.data import guardian, soccer_db
from sportsnlp.events import preprocess, temporal
from sportsnlp.events.schema import write_jsonl
from sportsnlp.paths import DATA_DIR


def build_extractor(name: str):
    if name == "rules":
        from sportsnlp.events.extractors.rules import RuleExtractor
        return RuleExtractor()
    if name == "llm":
        # TODO: construct a complete(prompt) -> str callable for your LLM provider.
        raise NotImplementedError("wire up an LLM client in scripts/extract_events.py")
    raise ValueError(f"Unknown extractor {name!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--extractor", choices=["rules", "llm"], default="rules")
    parser.add_argument("--limit", type=int, default=None, help="Max articles (for dev runs).")
    args = parser.parse_args(argv)

    with closing(soccer_db.connect()) as conn:
        matches = soccer_db.load_matches(conn)

    extractor = build_extractor(args.extractor)
    events = []
    for i, article in enumerate(guardian.iter_unique_articles(guardian.load_cache())):
        if args.limit is not None and i >= args.limit:
            break
        for event in extractor.extract_many(preprocess.candidate_passages(article)):
            # TODO: link player/team before grounding (events.linking), so fixture
            # resolution can use the team.
            event.occurred = temporal.ground(event.occurred.text, event.report_date,
                                             event.team_api_id, matches)
            events.append(event)

    out_dir = DATA_DIR / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"events_{extractor.name}.jsonl"
    write_jsonl(events, out)
    print(f"Wrote {len(events):,} events to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
