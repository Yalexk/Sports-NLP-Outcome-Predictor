"""Score extractor output against the gold annotations in ``data/annotations/``.

Report these separately; they fail for different reasons and your write-up
should show which stage is the bottleneck:
  - event detection: precision/recall/F1 of (article, player, event_type)
  - argument F1: body_part, injury_type, modality, given a matched event
  - temporal: of matched INJURY events with a gold date, % exactly right and
    % within ±1 / ±3 days; plus accuracy of the precision label
"""
from __future__ import annotations

from datetime import date

from sportsnlp.events.schema import InjuryEvent


def _f1(tp: int, n_pred: int, n_gold: int) -> dict[str, float]:
    p = tp / n_pred if n_pred else 0.0
    r = tp / n_gold if n_gold else 0.0
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0}


def event_key(e: InjuryEvent) -> tuple:
    """Identity of an event for matching. Uses the mention text until linking exists."""
    who = e.player_api_id if e.player_api_id is not None else (e.player_name or e.player_mention or "").lower()
    return (e.article_id, who, e.event_type)


def detection_scores(pred: list[InjuryEvent], gold: list[InjuryEvent]) -> dict[str, float]:
    pred_keys, gold_keys = {event_key(e) for e in pred}, {event_key(e) for e in gold}
    return _f1(len(pred_keys & gold_keys), len(pred_keys), len(gold_keys))


def temporal_scores(pred: list[InjuryEvent], gold: list[InjuryEvent], tolerances=(0, 1, 3)) -> dict[str, float]:
    """TODO: pair matched INJURY events by ``event_key`` where gold has ``occurred.value``;
    compute the share with |pred - gold| <= t days for each t (missing pred date = miss)."""
    raise NotImplementedError


def day_error(pred: date | None, gold: date) -> int | None:
    return None if pred is None else abs((pred - gold).days)
