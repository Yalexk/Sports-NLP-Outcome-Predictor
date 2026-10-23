"""Event schema tests, plus executable specs for the stages you still have to build.

Tests marked ``xfail(raises=NotImplementedError)`` describe the expected behaviour
of a skeleton function. Once you implement it they start passing and pytest
reports them as XPASS — then delete the marker.
"""
from datetime import date

import pandas as pd
import pytest

from sportsnlp.events import evaluate, preprocess, temporal
from sportsnlp.events.schema import InjuryEvent, TimeAnchor, read_jsonl, write_jsonl

todo = pytest.mark.xfail(raises=NotImplementedError, reason="not implemented yet", strict=False)

REPORT = date(2012, 3, 7)  # a Wednesday


def make_event(**kw):
    base = dict(article_id="a1", report_date=REPORT, evidence="...", trigger="limped off",
                event_type="INJURY", player_mention="Kane")
    return InjuryEvent(**{**base, **kw})


def test_schema_jsonl_roundtrip(tmp_path):
    events = [
        make_event(occurred=TimeAnchor("on Saturday", date(2012, 3, 3), "DAY", 1234)),
        make_event(event_type="RULED_OUT", trigger="ruled out", expected_duration="three weeks",
                   expected_return=TimeAnchor("three weeks", date(2012, 3, 28), "WEEK")),
    ]
    path = tmp_path / "events.jsonl"
    write_jsonl(events, path)
    assert read_jsonl(path) == events


def test_detection_scores_by_player_and_type():
    gold = [make_event(), make_event(event_type="RULED_OUT")]
    pred = [make_event(player_mention="kane"), make_event(player_mention="Walker")]
    scores = evaluate.detection_scores(pred, gold)
    assert scores["precision"] == 0.5
    assert scores["recall"] == 0.5


def test_ground_without_expression_is_unknown():
    anchor = temporal.ground(None, REPORT, None, pd.DataFrame())
    assert anchor.precision == "UNKNOWN" and anchor.value is None


# --- Specs for skeleton functions --------------------------------------------

@todo
def test_weekday_resolves_to_most_recent_past_day():
    anchor = temporal.normalise_expression("on Saturday", REPORT)
    assert anchor.value == date(2012, 3, 3)
    assert anchor.precision == "DAY"


@todo
def test_injury_date_never_after_report_date():
    anchor = temporal.normalise_expression("on Wednesday", REPORT)
    assert anchor.value <= REPORT


@todo
def test_last_month_has_month_precision():
    anchor = temporal.normalise_expression("last month", REPORT)
    assert anchor.precision == "MONTH"
    assert anchor.value.month == 2


@todo
def test_candidate_passages_keep_context_sentence():
    article = {
        "date": "2012-03-07T10:00:00Z",
        "headline": "Spurs news",
        "body": "Harry Kane started brightly. He limped off after 20 minutes. Spurs won 2-0.",
    }
    passages = preprocess.candidate_passages(article, window=1)
    assert len(passages) == 1
    assert "Harry Kane" in passages[0].text  # antecedent of "He" is kept
