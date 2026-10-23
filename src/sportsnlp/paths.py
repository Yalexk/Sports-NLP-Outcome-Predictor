"""Canonical filesystem locations, resolved relative to the repo root."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

DB_PATH = DATA_DIR / "database.sqlite"
ARTICLES_CACHE_PATH = DATA_DIR / "articles_cache.json"

# Hand-annotated injury events. Unlike everything else in data/, this is committed.
ANNOTATIONS_DIR = DATA_DIR / "annotations"

MODELS_DIR = REPO_ROOT / "models"
