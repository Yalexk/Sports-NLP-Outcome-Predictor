# Sports-NLP-Outcome-Predictor

Predicting soccer match outcomes from structured data **plus injury events extracted
from pre-match news**: who got injured, how, and *when it happened*.

The first iteration used keyword counts and NER tags as injury signals; they didn't
improve the model (see [`notebooks/archive/ner_approach/`](notebooks/archive/ner_approach/README.md)).
This version treats injuries as **events** with typed arguments and a time anchor,
then turns them into leak-free player-availability features.

- **Plan / roadmap:** [`docs/PLAN.md`](docs/PLAN.md)
- **Event schema & annotation guidelines:** [`docs/injury_event_schema.md`](docs/injury_event_schema.md)
- **Data sources & reading list:** [`docs/resources.md`](docs/resources.md)

## Pipeline

```
Guardian articles ─► passages ─► InjuryEvent ─► player link ─► date ─► injury spells ─► availability features ─► outcome model
                     preprocess   extractors     linking        temporal  aggregate       features/availability    models/outcome
```

## Layout

```
.
├── data/                       # gitignored, except annotations/
│   ├── database.sqlite         #   European Soccer Database (scripts/download_data.py)
│   ├── articles_cache.json     #   Guardian articles (scripts/fetch_articles.py)
│   ├── annotations/            #   gold injury events — committed
│   └── processed/              #   extractor output
├── docs/                       # plan, schema, resources
├── notebooks/
│   ├── 01_explore_soccer_db.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_baseline_models.ipynb
│   ├── 04_fetch_articles.ipynb
│   └── archive/ner_approach/   # keyword + NER attempt, kept for reference
├── scripts/
│   ├── download_data.py        # Kaggle → data/database.sqlite
│   ├── fetch_articles.py       # Guardian → data/articles_cache.json (resumable)
│   ├── sample_for_annotation.py
│   └── extract_events.py       # run an extractor over the cache
├── src/sportsnlp/
│   ├── paths.py
│   ├── data/                   # soccer_db.py, guardian.py
│   ├── features/               # match_features.py (structured), availability.py (from events)
│   ├── events/                 # schema, preprocess, extractors/, temporal, linking, aggregate, evaluate
│   └── models/                 # outcome.py — ablation runner
└── tests/
```

Modules marked as skeletons raise `NotImplementedError` with a TODO describing what to build.

## Dataset: European Soccer Database

[European Soccer Database](https://www.kaggle.com/datasets/hugomathien/soccer) by Hugo Mathien:
one SQLite file with ~25,000 matches across 11 European leagues, 2008/09–2015/16.

- `Country`, `League`: lookup tables.
- `Match`: date, teams, score, starting XIs (`home_player_1..11`, `away_player_1..11`),
  event XML (shots, fouls, cards, …), and bookmaker odds (B365, BW, IW, …).
- `Team`, `Team_Attributes`: FIFA-derived tactical ratings, versioned by date.
- `Player`, `Player_Attributes`: FIFA-derived player ratings, versioned by date.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .                 # makes `import sportsnlp` work in notebooks/scripts

cp .env.example .env             # add Guardian API keys (and Kaggle, if not using ~/.kaggle)

# Kaggle: create a token at https://www.kaggle.com/settings/account, put it in
# ~/.kaggle/kaggle.json (chmod 600), and accept the dataset terms once on its page.
python scripts/download_data.py
python scripts/fetch_articles.py --leagues "England Premier League"

pytest                           # xfail = spec for a stage you haven't implemented yet
```

## Using the shared code

```python
from sportsnlp.data.soccer_db import load_all
from sportsnlp.features.match_features import build_match_dataset
from sportsnlp.models.outcome import fit_and_score

db = load_all()
dataset = build_match_dataset(db["matches"], db["player_ratings"], db["team_attributes"])
fit_and_score(dataset)   # structured-only baseline on the pre/post-2014 split
```

The notebooks still contain their original inline code (with outputs) as a record;
new work should import from `sportsnlp` instead.
