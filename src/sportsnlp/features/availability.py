"""Bridge to the outcome model: injury spells -> per-match availability features.

Leakage rule: a spell may only affect a match if ``spell.first_reported`` is
strictly before the match date. Using ``start`` alone would let a model "know"
about injuries that were only reported after kick-off.

Note the Match table's lineups are the players who *actually* started, so the
injured players are by definition absent from them. Measure absence against an
*expected* XI instead (e.g. each team's most-used starters over its last N matches).
"""
from __future__ import annotations

import pandas as pd

AVAILABILITY_COLS = [
    "home_n_injured", "away_n_injured",                      # spells active at kick-off
    "home_n_injured_regulars", "away_n_injured_regulars",    # ... among the expected XI
    "home_missing_rating", "away_missing_rating",            # summed overall_rating of injured regulars
    "home_new_injuries_7d", "away_new_injuries_7d",          # spells first reported in the prior week
]


def expected_xi(matches: pd.DataFrame, lookback_matches: int = 5) -> pd.DataFrame:
    """Per (match_api_id, side): the team's most frequent starters over its prior N matches.

    TODO: build from the PLAYER_COLS lineups, shifted so the current match is excluded.
    """
    raise NotImplementedError


def build_availability_features(
    matches: pd.DataFrame,
    spells: pd.DataFrame,
    player_ratings: pd.DataFrame,
) -> pd.DataFrame:
    """One row per match_api_id with ``AVAILABILITY_COLS``.

    ``spells`` is a DataFrame of ``events.aggregate.InjurySpell`` rows.

    TODO: a spell is active for a match if first_reported < date and
    (end is null or end >= date). Matches with no article coverage should get NaN
    (not 0) plus a coverage flag — "no news" is different from "no injuries".
    """
    raise NotImplementedError
