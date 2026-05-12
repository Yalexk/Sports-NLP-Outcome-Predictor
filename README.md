# Sports-NLP-Outcome-Predictor

Predicting soccer match outcomes from structured data and (eventually) match-report text.

## Dataset: European Soccer Database

This project uses the [European Soccer Database](https://www.kaggle.com/datasets/hugomathien/soccer) published by Hugo Mathien on Kaggle. It is distributed as a single SQLite file (`database.sqlite`, ~36 MB compressed) covering roughly 25,000 matches across 11 European leagues from the 2008/2009 through 2015/2016 seasons.

Tables:

- `Country` and `League` — lookup tables (England Premier League, Spain La Liga, Italy Serie A, Germany Bundesliga, France Ligue 1, Netherlands Eredivisie, Belgium Jupiler League, Portugal Liga ZON Sagres, Switzerland Super League, Scotland Premier League, Poland Ekstraklasa).
- `Match` — one row per match with date, teams, final score, lineups (referenced by `player_X1..11`/`player_Y1..11` coordinates), event XML blobs (shots, fouls, cards, possession, cross), and pre-match bookmaker odds from B365, BW, IW, LB, PS, WH, SJ, VC, GB, BS.
- `Team` and `Team_Attributes` — FIFA-game-derived team ratings (buildup speed, chance creation, defensive pressure, etc.), versioned by date.
- `Player` and `Player_Attributes` — FIFA-game-derived player ratings (overall, potential, position-specific skills), versioned by date.

The raw SQLite file is not committed to the repo; you download it locally with the script below.

## Setup

```bash
# 1. Install dependencies (use a virtualenv if you like)
pip install -r requirements.txt

# 2. Configure Kaggle API credentials
#    - Go to https://www.kaggle.com/settings/account and click "Create New Token".
#    - Move the downloaded kaggle.json to ~/.kaggle/kaggle.json and chmod 600 it.
#    - Or set KAGGLE_USERNAME / KAGGLE_KEY environment variables.

# 3. Accept the dataset terms once at the dataset page while logged in:
#    https://www.kaggle.com/datasets/hugomathien/soccer

# 4. Download the database into ./data/
python scripts/download_data.py
```

The script is idempotent — re-running it is a no-op unless you pass `--force`.

## Exploring the data

Launch Jupyter from the repo root and open the exploration notebook:

```bash
jupyter notebook notebooks/explore_soccer_db.ipynb
```

It connects to `data/database.sqlite`, lists tables and row counts, prints the schema and a few rows of every table, and runs a couple of starter queries (matches per league/season, goal-difference distribution).

## Layout

```
.
├── data/                       # SQLite file lives here (gitignored)
├── notebooks/
│   └── explore_soccer_db.ipynb
├── scripts/
│   └── download_data.py
├── requirements.txt
└── README.md
```
