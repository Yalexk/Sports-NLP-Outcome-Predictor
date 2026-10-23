"""Stage 5 — merge many reports into injury *spells*.

One hamstring injury produces a dozen articles over three weeks ("injured",
"ruled out", "doubtful", "returns"). The outcome model needs one spell per
injury: (player, start, expected/observed end), not a dozen mentions. This is
exactly the double-counting that sank the keyword-count features.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sportsnlp.events.schema import InjuryEvent


@dataclass
class InjurySpell:
    player_api_id: int
    team_api_id: int | None
    start: date | None           # best estimate of when the injury occurred
    first_reported: date         # earliest report_date — what a model could know, and when
    end: date | None             # RETURN event date, or start + expected duration
    body_part: str | None
    events: list[InjuryEvent]    # supporting evidence


def build_spells(events: list[InjuryEvent], gap_days: int = 21) -> list[InjurySpell]:
    """Group linked events by player into spells.

    TODO:
      - drop events with no ``player_api_id`` or modality NEGATED
      - sort by report_date; start a new spell after a RETURN or a gap > ``gap_days``
      - ``start`` = earliest grounded ``occurred.value``; ``first_reported`` = min report_date
      - ``end`` = first RETURN report_date, else parse ``expected_duration``
    """
    raise NotImplementedError
