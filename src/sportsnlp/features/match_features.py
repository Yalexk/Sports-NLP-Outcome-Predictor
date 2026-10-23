"""Structured (non-text) match features.

Single source of truth for the pipeline that was previously copy-pasted across
``02_feature_engineering``, ``03_baseline_models`` and the archived keyword notebook:
player ratings, rolling form, head-to-head and FIFA tactical attributes. Every
feature only uses information dated strictly before the match.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from sportsnlp.data.soccer_db import PLAYER_COLS

FORM_WINDOW = 5
H2H_WINDOW = 5

TACTICAL_COLS = [
    "buildUpPlaySpeed", "buildUpPlayPassing",
    "chanceCreationPassing", "chanceCreationCrossing", "chanceCreationShooting",
    "defencePressure", "defenceAggression", "defenceTeamWidth",
]

RATING_COLS = [
    "home_avg_rating", "away_avg_rating",
    "home_min_rating", "away_min_rating",
    "home_max_rating", "away_max_rating",
    "home_std_rating", "away_std_rating",
]
FORM_COLS = [
    "home_rolling_gf", "home_rolling_ga", "home_rolling_pts",
    "away_rolling_gf", "away_rolling_ga", "away_rolling_pts",
]
H2H_COLS = ["h2h_home_win_rate", "h2h_avg_goal_diff"]
HOME_TACTICAL_COLS = [f"home_{c}" for c in TACTICAL_COLS]
AWAY_TACTICAL_COLS = [f"away_{c}" for c in TACTICAL_COLS]

FEATURE_COLS = RATING_COLS + FORM_COLS + H2H_COLS + HOME_TACTICAL_COLS + AWAY_TACTICAL_COLS


def compute_player_ratings(matches: pd.DataFrame, player_ratings: pd.DataFrame) -> pd.DataFrame:
    """Long table: one row per (match, lineup slot) with the latest rating before kick-off."""
    match_players = (
        matches[["match_api_id", "date"] + PLAYER_COLS]
        .melt(id_vars=["match_api_id", "date"], value_vars=PLAYER_COLS, value_name="player_api_id")
        .dropna(subset=["player_api_id"])
        .astype({"player_api_id": int})
        .sort_values("date")
    )
    rated = pd.merge_asof(
        match_players,
        player_ratings.sort_values("date"),
        on="date",
        by="player_api_id",
        direction="backward",
    )
    rated["side"] = rated["variable"].str.split("_player_").str[0]
    return rated


def compute_team_ratings(rated: pd.DataFrame) -> pd.DataFrame:
    stats = (
        rated.groupby(["match_api_id", "side"])["overall_rating"]
        .agg(avg_rating="mean", min_rating="min", max_rating="max", std_rating="std")
        .unstack("side")
    )
    # (avg_rating, home) -> home_avg_rating
    stats.columns = [f"{side}_{stat}" for stat, side in stats.columns]
    return stats.reset_index()


def compute_team_form(df: pd.DataFrame, n: int = FORM_WINDOW) -> pd.DataFrame:
    """Rolling per-team form stats, leak-free (shift 1 before rolling mean)."""
    home = df[["match_api_id", "date", "home_team_api_id", "home_team_goal", "away_team_goal"]].copy()
    home.columns = ["match_api_id", "date", "team_id", "goals_for", "goals_against"]
    home["is_home"] = True

    away = df[["match_api_id", "date", "away_team_api_id", "away_team_goal", "home_team_goal"]].copy()
    away.columns = ["match_api_id", "date", "team_id", "goals_for", "goals_against"]
    away["is_home"] = False

    timeline = pd.concat([home, away], ignore_index=True).sort_values(["team_id", "date"])
    timeline["points"] = np.select(
        [timeline["goals_for"] > timeline["goals_against"],
         timeline["goals_for"] == timeline["goals_against"]],
        [3, 1], default=0
    )

    for stat in ["goals_for", "goals_against", "points"]:
        timeline[f"rolling_{stat}"] = (
            timeline.groupby("team_id")[stat]
            .transform(lambda x: x.shift(1).rolling(n, min_periods=1).mean())
        )

    renames = {
        side: {"rolling_goals_for": f"{side}_rolling_gf",
               "rolling_goals_against": f"{side}_rolling_ga",
               "rolling_points": f"{side}_rolling_pts"}
        for side in ("home", "away")
    }
    home_form = (timeline[timeline["is_home"]]
                 .rename(columns=renames["home"])
                 [["match_api_id"] + FORM_COLS[:3]])
    away_form = (timeline[~timeline["is_home"]]
                 .rename(columns=renames["away"])
                 [["match_api_id"] + FORM_COLS[3:]])
    return home_form.merge(away_form, on="match_api_id")


def compute_h2h(df: pd.DataFrame, n: int = H2H_WINDOW) -> pd.DataFrame:
    """Per-match H2H win rate and avg goal diff from the home team's perspective."""
    df_sorted = df.sort_values("date").reset_index(drop=True)

    # Canonical pair key so (A,B) and (B,A) are treated as the same fixture
    df_sorted["_t1"] = np.minimum(df_sorted["home_team_api_id"], df_sorted["away_team_api_id"])
    df_sorted["_t2"] = np.maximum(df_sorted["home_team_api_id"], df_sorted["away_team_api_id"])

    records = []
    for _, fixture in df_sorted.groupby(["_t1", "_t2"], sort=False):
        for i, row in enumerate(fixture.itertuples()):
            prior = fixture.iloc[max(0, i - n):i]
            if prior.empty:
                records.append({"match_api_id": row.match_api_id,
                                "h2h_home_win_rate": np.nan,
                                "h2h_avg_goal_diff": np.nan,
                                "h2h_n_matches": 0})
                continue

            home_perspective_diff = np.where(
                prior["home_team_api_id"] == row.home_team_api_id,
                prior["home_team_goal"] - prior["away_team_goal"],
                prior["away_team_goal"] - prior["home_team_goal"],
            )
            records.append({"match_api_id": row.match_api_id,
                            "h2h_home_win_rate": (home_perspective_diff > 0).sum() / len(prior),
                            "h2h_avg_goal_diff": home_perspective_diff.mean(),
                            "h2h_n_matches": len(prior)})

    return pd.DataFrame(records)


def compute_tactical(matches: pd.DataFrame, team_attributes: pd.DataFrame) -> pd.DataFrame:
    """Most recent FIFA tactical snapshot before kick-off, for both sides."""
    team_attributes = team_attributes.sort_values("date")
    matches_sorted = matches.sort_values("date")

    def merge_side(team_id_col: str, prefix: str) -> pd.DataFrame:
        merged = pd.merge_asof(
            matches_sorted[["match_api_id", "date", team_id_col]],
            team_attributes,
            on="date",
            left_by=team_id_col,
            right_by="team_api_id",
            direction="backward",
        ).drop(columns=["team_api_id", team_id_col, "date"])
        return merged.rename(columns={c: f"{prefix}_{c}" for c in TACTICAL_COLS})

    return merge_side("home_team_api_id", "home").merge(
        merge_side("away_team_api_id", "away"), on="match_api_id"
    )


def build_match_dataset(
    matches: pd.DataFrame,
    player_ratings: pd.DataFrame,
    team_attributes: pd.DataFrame,
) -> pd.DataFrame:
    """Full structured feature table, one row per match with a known lineup."""
    team_ratings = compute_team_ratings(compute_player_ratings(matches, player_ratings))
    matches = matches.merge(team_ratings, on="match_api_id", how="left")
    # Some matches have no lineup recorded, so they get no ratings and are dropped.
    matches = matches.dropna(subset=["home_avg_rating", "away_avg_rating"])

    id_cols = ["match_api_id", "date", "home_team_api_id", "away_team_api_id", "result", "result_code"]
    return (
        matches[id_cols + RATING_COLS]
        .merge(compute_team_form(matches), on="match_api_id", how="left")
        .merge(compute_h2h(matches), on="match_api_id", how="left")
        .merge(compute_tactical(matches, team_attributes), on="match_api_id", how="left")
        .sort_values("date")
        .reset_index(drop=True)
    )


def temporal_split(dataset: pd.DataFrame, cutoff: str = "2014-01-01") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pre-cutoff train / post-cutoff test, matching the split used in 03_baseline_models."""
    return dataset[dataset["date"] < cutoff].copy(), dataset[dataset["date"] >= cutoff].copy()
