"""Tests for the structured features, on a tiny synthetic league (no DB needed)."""
import numpy as np
import pandas as pd
import pytest

from sportsnlp.data.soccer_db import PLAYER_COLS, add_result_labels
from sportsnlp.features import match_features as mf


@pytest.fixture
def matches():
    # Teams 1, 2, 3. Fixture (1, 2) is played three times, alternating venue.
    rows = [
        (101, "2010-01-01", 1, 2, 2, 0),
        (102, "2010-01-08", 2, 3, 1, 1),
        (103, "2010-01-15", 2, 1, 3, 1),
        (104, "2010-01-22", 3, 1, 0, 2),
        (105, "2010-01-29", 1, 2, 0, 0),
    ]
    df = pd.DataFrame(rows, columns=["match_api_id", "date", "home_team_api_id",
                                     "away_team_api_id", "home_team_goal", "away_team_goal"])
    df["date"] = pd.to_datetime(df["date"])
    for i, col in enumerate(PLAYER_COLS):
        df[col] = 1000 + i  # same 22 players every match is fine for these tests
    return add_result_labels(df)


def test_result_labels(matches):
    assert matches.set_index("match_api_id")["result"].to_dict() == {
        101: "Win", 102: "Draw", 103: "Win", 104: "Defeat", 105: "Draw"
    }


def test_team_form_excludes_current_match(matches):
    form = mf.compute_team_form(matches).set_index("match_api_id")
    # Team 1's first match has no history.
    assert np.isnan(form.loc[101, "home_rolling_gf"])
    # Before match 104, team 1 (away) scored 2 (m101) and 1 (m103).
    assert form.loc[104, "away_rolling_gf"] == pytest.approx(1.5)
    assert form.loc[104, "away_rolling_pts"] == pytest.approx(1.5)  # 3 + 0


def test_h2h_home_perspective(matches):
    h2h = mf.compute_h2h(matches).set_index("match_api_id")
    assert h2h.loc[101, "h2h_n_matches"] == 0
    # Match 103 (home=2): prior meeting m101 was a 2-0 loss for team 2.
    assert h2h.loc[103, "h2h_home_win_rate"] == 0
    assert h2h.loc[103, "h2h_avg_goal_diff"] == -2
    # Match 105 (home=1): team 1 won m101 by 2, lost m103 by 2.
    assert h2h.loc[105, "h2h_home_win_rate"] == 0.5
    assert h2h.loc[105, "h2h_avg_goal_diff"] == 0


def _h2h_reference(df, n=mf.H2H_WINDOW):
    """The original O(n^2) implementation from 02_feature_engineering.ipynb."""
    df_sorted = df.sort_values("date").reset_index(drop=True)
    df_sorted["_t1"] = np.minimum(df_sorted["home_team_api_id"], df_sorted["away_team_api_id"])
    df_sorted["_t2"] = np.maximum(df_sorted["home_team_api_id"], df_sorted["away_team_api_id"])
    records = []
    for idx, row in df_sorted.iterrows():
        prior = df_sorted.iloc[:idx]
        prior = prior[(prior["_t1"] == row["_t1"]) & (prior["_t2"] == row["_t2"])].tail(n)
        if prior.empty:
            records.append({"match_api_id": row["match_api_id"], "h2h_home_win_rate": np.nan,
                            "h2h_avg_goal_diff": np.nan, "h2h_n_matches": 0})
            continue
        diff = np.where(prior["home_team_api_id"] == row["home_team_api_id"],
                        prior["home_team_goal"] - prior["away_team_goal"],
                        prior["away_team_goal"] - prior["home_team_goal"])
        records.append({"match_api_id": row["match_api_id"],
                        "h2h_home_win_rate": (diff > 0).sum() / len(prior),
                        "h2h_avg_goal_diff": diff.mean(), "h2h_n_matches": len(prior)})
    return pd.DataFrame(records)


def test_h2h_matches_original_notebook_implementation():
    rng = np.random.default_rng(0)
    n = 300
    home = rng.integers(1, 7, n)
    away = (home + rng.integers(1, 6, n) - 1) % 6 + 1  # never equal to home
    df = pd.DataFrame({
        "match_api_id": np.arange(n),
        "date": pd.date_range("2010-01-01", periods=n, freq="D"),
        "home_team_api_id": home, "away_team_api_id": away,
        "home_team_goal": rng.integers(0, 4, n), "away_team_goal": rng.integers(0, 4, n),
    })
    ours = mf.compute_h2h(df).sort_values("match_api_id").reset_index(drop=True)
    ref = _h2h_reference(df).sort_values("match_api_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(ours, ref, check_dtype=False)


def test_build_match_dataset_uses_ratings_before_kickoff(matches):
    ratings = pd.DataFrame({
        "player_api_id": [1000 + i for i in range(22)] * 2,
        "date": pd.to_datetime(["2009-12-01"] * 22 + ["2010-01-20"] * 22),
        "overall_rating": [60] * 22 + [80] * 22,
    })
    team_attrs = pd.DataFrame({"team_api_id": [1, 2, 3], "date": pd.to_datetime(["2009-06-01"] * 3)})
    for c in mf.TACTICAL_COLS:
        team_attrs[c] = 50

    ds = mf.build_match_dataset(matches, ratings, team_attrs).set_index("match_api_id")
    assert ds.loc[103, "home_avg_rating"] == 60   # 15 Jan: only the December rating exists
    assert ds.loc[104, "home_avg_rating"] == 80   # 22 Jan: picks up the 20 Jan rating
    assert set(mf.FEATURE_COLS) <= set(ds.columns)


def test_temporal_split(matches):
    train, test = mf.temporal_split(matches, cutoff="2010-01-20")
    assert train["match_api_id"].tolist() == [101, 102, 103]
    assert test["match_api_id"].tolist() == [104, 105]
