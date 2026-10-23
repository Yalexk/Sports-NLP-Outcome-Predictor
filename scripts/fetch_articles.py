#!/usr/bin/env python3
"""Fetch Guardian pre-match articles for every match into data/articles_cache.json.

Script version of the fetch loop in notebooks/04_fetch_articles.ipynb, so the
multi-hour run doesn't depend on a notebook kernel staying alive. Resumable:
already-cached (team, window) pairs are skipped.

Usage
-----
    python scripts/fetch_articles.py
    python scripts/fetch_articles.py --leagues "England Premier League" "Spain LIGA BBVA"
"""
from __future__ import annotations

import argparse
from contextlib import closing

from sportsnlp.data import guardian, soccer_db


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--leagues", nargs="*", default=None,
                        help="Restrict to these league names (default: all).")
    parser.add_argument("--save-every", type=int, default=500)
    args = parser.parse_args(argv)

    with closing(soccer_db.connect()) as conn:
        matches = soccer_db.load_matches(conn)
    if args.leagues:
        matches = matches[matches["league_name"].isin(args.leagues)]

    pairs = sorted({(team, date)
                    for row in matches.itertuples()
                    for team, date in ((row.home_team_name, row.date), (row.away_team_name, row.date))})

    cache = guardian.load_cache()
    todo = [(t, d) for t, d in pairs if guardian.cache_key(t, d) not in cache]
    print(f"{len(pairs):,} (team, window) pairs, {len(todo):,} to fetch")

    key_pool = guardian.load_api_keys()
    for i, (team, date) in enumerate(todo, 1):
        guardian.fetch_articles(team, date, cache, key_pool)
        if i % args.save_every == 0:
            guardian.save_cache(cache)
            print(f"  {i:,}/{len(todo):,} fetched — cache size {len(cache):,}")

    guardian.save_cache(cache)
    print(f"Done. Cache size {len(cache):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
