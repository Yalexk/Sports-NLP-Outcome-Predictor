"""Fetch and cache pre-match articles from the Guardian Open Platform API.

Lifted from ``notebooks/04_fetch_articles.ipynb`` so the extraction pipeline and
the long-running fetch script share one implementation. Cache keys are unchanged
(``"<team>|<from>|<to>"``), so an existing ``data/articles_cache.json`` still works.
"""
from __future__ import annotations

import json
import os
import time
import unicodedata
from datetime import timedelta
from itertools import cycle
from pathlib import Path

import pandas as pd
import requests

from sportsnlp.paths import ARTICLES_CACHE_PATH

GUARDIAN_BASE_URL = "https://content.guardianapis.com/search"
LOOKBACK_DAYS = 7
RATE_LIMIT_DELAY = 0.15


def load_api_keys() -> cycle:
    from dotenv import load_dotenv

    load_dotenv()
    keys = [k for k in (os.getenv(f"GUARDIAN_API_KEY_{i}") for i in (1, 2, 3)) if k]
    if not keys:
        raise RuntimeError("No GUARDIAN_API_KEY_* keys found — add them to your .env file")
    return cycle(keys)


def load_cache(path: Path = ARTICLES_CACHE_PATH) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict, path: Path = ARTICLES_CACHE_PATH) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    tmp.rename(path)


def clean_team_name(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").strip()


def window(match_date: pd.Timestamp, lookback_days: int = LOOKBACK_DAYS) -> tuple[str, str]:
    """Search window ending the day *before* kick-off, so no post-match text leaks in."""
    from_date = (match_date - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    to_date = (match_date - timedelta(days=1)).strftime("%Y-%m-%d")
    return from_date, to_date


def cache_key(team_name: str, match_date: pd.Timestamp) -> str:
    from_date, to_date = window(match_date)
    return f"{team_name}|{from_date}|{to_date}"


def get_cached_articles(team_name: str, match_date: pd.Timestamp, cache: dict) -> list[dict]:
    return cache.get(cache_key(team_name, match_date), [])


def fetch_articles(team_name: str, match_date: pd.Timestamp, cache: dict, key_pool: cycle) -> list[dict]:
    key = cache_key(team_name, match_date)
    if key in cache:
        return cache[key]

    from_date, to_date = window(match_date)
    try:
        response = requests.get(
            GUARDIAN_BASE_URL,
            params={
                "q":           clean_team_name(team_name),
                "section":     "football",
                "from-date":   from_date,
                "to-date":     to_date,
                "show-fields": "headline,bodyText",
                "page-size":   10,
                "api-key":     next(key_pool),
            },
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()["response"]["results"]
        articles = [
            {
                "headline": r["fields"].get("headline", ""),
                "body":     r["fields"].get("bodyText", ""),
                "date":     r["webPublicationDate"],
            }
            for r in results
        ]
    except Exception as e:
        # Don't cache failures, otherwise a transient error becomes a permanent "no coverage".
        print(f"  ERROR fetching {team_name} {from_date}: {e}")
        return []

    cache[key] = articles
    time.sleep(RATE_LIMIT_DELAY)
    return articles


def iter_unique_articles(cache: dict):
    """Yield each cached article once. The same article is often cached under several
    (team, window) keys, so the extraction pipeline should de-duplicate before running."""
    seen = set()
    for articles in cache.values():
        for article in articles:
            ident = (article.get("date"), article.get("headline"))
            if ident in seen:
                continue
            seen.add(ident)
            yield article
