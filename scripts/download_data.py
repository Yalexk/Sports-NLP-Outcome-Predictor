#!/usr/bin/env python3
"""Download the European Soccer Database from Kaggle.

The dataset is published by Hugo Mathien on Kaggle:
    https://www.kaggle.com/datasets/hugomathien/soccer

It ships as a single SQLite file (``database.sqlite``) with tables covering
~25,000 matches across 11 European leagues (2008-2016), plus team and player
attributes sourced from the FIFA video-game series and bookmaker odds.

Usage
-----
    python scripts/download_data.py                # defaults to ./data
    python scripts/download_data.py --data-dir /tmp/soccer
    python scripts/download_data.py --force        # re-download even if present

Prerequisites
-------------
1. ``pip install kaggle`` (or ``pip install -r requirements.txt``).
2. Create a Kaggle API token: https://www.kaggle.com/settings/account
   Save the resulting ``kaggle.json`` to ``~/.kaggle/kaggle.json`` and
   ``chmod 600`` it.
3. Accept the dataset's terms once by visiting the URL above while logged in.
"""
from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path

DATASET = "hugomathien/soccer"
SQLITE_FILENAME = "database.sqlite"


def _ensure_kaggle_available() -> None:
    try:
        import kaggle  # noqa: F401
    except ImportError:
        sys.exit(
            "The 'kaggle' package is not installed. Install it with:\n"
            "    pip install kaggle\n"
            "or:\n"
            "    pip install -r requirements.txt"
        )
    cred_path = Path.home() / ".kaggle" / "kaggle.json"
    if not cred_path.exists() and not (
        os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")
    ):
        sys.exit(
            f"Kaggle credentials not found.\n"
            f"Expected {cred_path} or KAGGLE_USERNAME / KAGGLE_KEY env vars.\n"
            f"See https://www.kaggle.com/settings/account to create an API token."
        )


def _extract_any_zips(data_dir: Path) -> None:
    """Some Kaggle CLI versions leave a zip behind; unpack it if so."""
    for zip_path in data_dir.glob("*.zip"):
        print(f"Extracting {zip_path.name}...")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(data_dir)
        zip_path.unlink()


def download(data_dir: Path, *, force: bool = False) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = data_dir / SQLITE_FILENAME

    if sqlite_path.exists() and not force:
        size_mb = sqlite_path.stat().st_size / (1024 * 1024)
        print(f"[skip] {sqlite_path} already exists ({size_mb:.1f} MB). "
              f"Use --force to re-download.")
        return sqlite_path

    _ensure_kaggle_available()

    # Imported lazily so the credential check above runs first with a clear error.
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    print(f"Downloading dataset '{DATASET}' to {data_dir} ...")
    api.dataset_download_files(DATASET, path=str(data_dir), unzip=True, quiet=False)
    _extract_any_zips(data_dir)

    if not sqlite_path.exists():
        sys.exit(
            f"Download finished but {sqlite_path} is missing. "
            f"Contents of {data_dir}: {sorted(p.name for p in data_dir.iterdir())}"
        )

    size_mb = sqlite_path.stat().st_size / (1024 * 1024)
    print(f"Done. Wrote {sqlite_path} ({size_mb:.1f} MB).")
    return sqlite_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
        help="Directory to write the SQLite file into (default: ./data).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the database file already exists.",
    )
    args = parser.parse_args(argv)
    download(args.data_dir, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
