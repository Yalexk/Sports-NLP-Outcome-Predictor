"""Stage 3 — temporal grounding: *when* did the injury happen?

This is the part NER could never do, and the core of the professor's suggestion.
Given an extracted time expression and the article's publication date, produce
a ``TimeAnchor`` with a calendar date and a precision.

Three sources of evidence, roughly in order of reliability:
  1. Fixture references — "in Saturday's 2-1 defeat at Stoke", "against Chelsea".
     Resolve against the Match table: the most recent match before ``report_date``
     involving the player's team (and the named opponent, if any). Gives an exact
     day and a ``match_api_id``.
  2. Explicit / relative dates — "on 14 March", "last weekend", "on Tuesday",
     "a fortnight ago". Normalise relative to ``report_date`` (dateparser with
     ``RELATIVE_BASE`` and ``PREFER_DATES_FROM='past'`` is a reasonable start;
     HeidelTime is the stronger, news-specific option).
  3. No expression at all — fall back to the event type: an INJURY report with no
     time is usually within the last few days; RULED_OUT/DOUBTFUL say nothing about
     occurrence. Return precision="UNKNOWN" rather than inventing a date.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from sportsnlp.events.schema import TimeAnchor


def normalise_expression(text: str, report_date: date) -> TimeAnchor:
    """Map a surface time expression to a date relative to ``report_date``.

    Must never return a date after ``report_date`` for an INJURY event; that would
    leak future information into the outcome model.

    TODO: handle weekday names ("on Saturday" = most recent Saturday before
    report_date), "last week/weekend/month", explicit dates without a year, and
    set ``precision`` accordingly.
    """
    raise NotImplementedError


def resolve_fixture(
    text: str,
    report_date: date,
    team_api_id: int | None,
    matches: pd.DataFrame,
) -> TimeAnchor | None:
    """If ``text`` refers to a match ("against Arsenal", "in the derby"), find it.

    TODO: fuzzy-match opponent names against ``matches`` team names, restrict to the
    team's matches in the ~3 weeks before ``report_date``, take the most recent.
    """
    raise NotImplementedError


def ground(
    occurred_text: str | None,
    report_date: date,
    team_api_id: int | None,
    matches: pd.DataFrame,
) -> TimeAnchor:
    """Try fixture resolution, then expression normalisation, else UNKNOWN."""
    if not occurred_text:
        return TimeAnchor()
    anchor = resolve_fixture(occurred_text, report_date, team_api_id, matches)
    if anchor is not None:
        return anchor
    return normalise_expression(occurred_text, report_date)
