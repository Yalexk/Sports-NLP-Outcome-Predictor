"""Stage 4 — entity linking: player mention -> ``player_api_id`` and ``team_api_id``.

The archived NER notebooks fuzzy-matched every PERSON against all ~11k players,
which confused namesakes and couldn't handle "he" / "the striker". Here linking
has much more context to work with:
  - the article is already associated with a team and a date (from the cache key),
    so candidates can be restricted to players in that team's recent lineups
    (``home_player_X`` / ``away_player_X`` columns in Match);
  - surnames alone ("Kane") become unambiguous within one squad;
  - pronouns should be resolved *before* linking — either by the LLM extractor
    returning the antecedent name, or by a coreference model (e.g. fastcoref).
"""
from __future__ import annotations

from datetime import date

import pandas as pd


def squad_on(team_api_id: int, on: date, matches: pd.DataFrame, lookback_matches: int = 10) -> set[int]:
    """Player ids who started for ``team_api_id`` in its last N matches before ``on``.

    TODO: filter matches by team and date, melt the 11 player columns for the right side.
    """
    raise NotImplementedError


def link_player(
    mention: str,
    candidate_ids: set[int],
    players: pd.DataFrame,
    threshold: int = 85,
) -> int | None:
    """Best fuzzy match of ``mention`` among the candidate squad, or None.

    TODO: rapidfuzz ``token_set_ratio`` against ``players.player_name`` restricted to
    ``candidate_ids``; also try surname-only matching for single-token mentions.
    """
    raise NotImplementedError
