"""Read-only access to the European Soccer Database (``data/database.sqlite``)."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd

from sportsnlp.paths import DB_PATH

PLAYER_COLS = [f"home_player_{i}" for i in range(1, 12)] + \
              [f"away_player_{i}" for i in range(1, 12)]

RESULT_CODES = {"Defeat": 0, "Draw": 1, "Win": 2}


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Missing {db_path}. Run `python scripts/download_data.py` from the repo root."
        )
    return sqlite3.connect(db_path)


def add_result_labels(matches: pd.DataFrame) -> pd.DataFrame:
    """Add ``result`` (Win/Draw/Defeat, home perspective) and integer ``result_code``."""
    matches = matches.copy()
    conditions = [
        matches["home_team_goal"] > matches["away_team_goal"],
        matches["home_team_goal"] == matches["away_team_goal"],
        matches["home_team_goal"] < matches["away_team_goal"],
    ]
    matches["result"] = np.select(conditions, ["Win", "Draw", "Defeat"], default="")
    matches["result_code"] = matches["result"].map(RESULT_CODES)
    return matches


def load_matches(conn: sqlite3.Connection) -> pd.DataFrame:
    """One row per match with goals, starting XIs, team/league names and result labels."""
    matches = pd.read_sql(
        f"""
        SELECT m.match_api_id, m.date, m.season,
               l.name AS league_name,
               m.home_team_api_id, m.away_team_api_id,
               ht.team_long_name AS home_team_name,
               at.team_long_name AS away_team_name,
               m.home_team_goal, m.away_team_goal,
               {', '.join(f'm.{c}' for c in PLAYER_COLS)}
        FROM Match m
        JOIN Team ht ON ht.team_api_id = m.home_team_api_id
        JOIN Team at ON at.team_api_id = m.away_team_api_id
        JOIN League l ON l.id = m.league_id
        ORDER BY m.date
        """,
        conn,
    )
    matches["date"] = pd.to_datetime(matches["date"])
    return add_result_labels(matches)


def load_players(conn: sqlite3.Connection) -> pd.DataFrame:
    """Player lookup table, used to link extracted player mentions to ``player_api_id``."""
    return pd.read_sql(
        "SELECT player_api_id, player_name, birthday FROM Player", conn
    )


def load_player_ratings(conn: sqlite3.Connection) -> pd.DataFrame:
    ratings = pd.read_sql(
        "SELECT player_api_id, date, overall_rating FROM Player_Attributes", conn
    )
    ratings["date"] = pd.to_datetime(ratings["date"])
    return ratings


def load_team_attributes(conn: sqlite3.Connection, columns: list[str]) -> pd.DataFrame:
    attrs = pd.read_sql(
        f"SELECT team_api_id, date, {', '.join(columns)} FROM Team_Attributes", conn
    )
    attrs["date"] = pd.to_datetime(attrs["date"])
    return attrs


def load_all(db_path: Path = DB_PATH) -> dict[str, pd.DataFrame]:
    """Convenience loader for everything ``features.match_features`` needs."""
    from sportsnlp.features.match_features import TACTICAL_COLS

    with closing(connect(db_path)) as conn:
        return {
            "matches": load_matches(conn),
            "players": load_players(conn),
            "player_ratings": load_player_ratings(conn),
            "team_attributes": load_team_attributes(conn, TACTICAL_COLS),
        }
