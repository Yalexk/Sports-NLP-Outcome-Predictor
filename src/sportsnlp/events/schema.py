"""Target representation for injury event extraction.

See ``docs/injury_event_schema.md`` for the annotation guidelines and worked
examples. Every extractor (rules, fine-tuned model, LLM) should emit
``InjuryEvent`` records so they can be scored against the same gold annotations
in ``data/annotations/`` and consumed by the same availability features.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

# What happened. INJURY is the occurrence itself ("tore his hamstring against Spurs");
# the others are later reports about the same underlying injury.
EventType = Literal["INJURY", "RULED_OUT", "DOUBTFUL", "RETURN"]

# Factuality of the event as stated in the text. Without this, "could be out"
# and "has been ruled out" look identical to the outcome model.
Modality = Literal["ASSERTED", "SPECULATED", "NEGATED"]

# How precisely the time expression pins down the date.
TimePrecision = Literal["DAY", "WEEK", "MONTH", "SEASON", "UNKNOWN"]


@dataclass
class TimeAnchor:
    """When the event happened, grounded against the article's publication date."""

    text: str | None = None              # surface form: "on Saturday", "in the 2-1 win at Stoke"
    value: date | None = None            # normalised date (earliest plausible day)
    precision: TimePrecision = "UNKNOWN"
    match_api_id: int | None = None      # set when the text ties the injury to a specific fixture


@dataclass
class InjuryEvent:
    # Provenance
    article_id: str
    report_date: date                    # document creation time; anchor for relative expressions
    evidence: str                        # sentence(s) the event was read from
    trigger: str                         # word/phrase that evokes the event: "limped off", "ruled out"

    event_type: EventType
    modality: Modality = "ASSERTED"

    # Arguments
    player_mention: str | None = None    # as written; may be a pronoun resolved to a name below
    player_name: str | None = None       # canonical name after coreference / linking
    player_api_id: int | None = None     # link into the Player table
    team_api_id: int | None = None
    body_part: str | None = None         # "hamstring", "knee"
    injury_type: str | None = None       # "strain", "fracture", "concussion"

    occurred: TimeAnchor = field(default_factory=TimeAnchor)
    expected_duration: str | None = None  # "three weeks", "rest of the season"
    expected_return: TimeAnchor | None = None

    extractor: str = "gold"              # which system produced this record

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=_json_default, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "InjuryEvent":
        d = dict(d)
        d["report_date"] = date.fromisoformat(d["report_date"])
        d["occurred"] = _anchor_from_dict(d.get("occurred") or {})
        if d.get("expected_return"):
            d["expected_return"] = _anchor_from_dict(d["expected_return"])
        return cls(**d)


def _anchor_from_dict(d: dict) -> TimeAnchor:
    d = dict(d)
    if d.get("value"):
        d["value"] = date.fromisoformat(d["value"])
    return TimeAnchor(**d)


def _json_default(o):
    if isinstance(o, date):
        return o.isoformat()
    raise TypeError(f"Not JSON serialisable: {type(o).__name__}")


def write_jsonl(events: list[InjuryEvent], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(e.to_json() + "\n")


def read_jsonl(path: Path) -> list[InjuryEvent]:
    with open(path, encoding="utf-8") as f:
        return [InjuryEvent.from_dict(json.loads(line)) for line in f if line.strip()]
