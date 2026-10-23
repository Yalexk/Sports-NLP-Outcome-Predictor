"""Baseline extractor: trigger lexicon + dependency patterns.

This is the floor every learned extractor must beat. It's also cheap enough to
run over the whole cache, so it doubles as a silver-label generator.

Suggested approach (spaCy):
  1. Match a trigger from ``TRIGGERS`` -> sets ``event_type``.
  2. Player = nominal subject (``nsubj`` / ``nsubjpass``) of the trigger's head
     verb, falling back to the nearest PERSON entity in the passage.
  3. Body part / injury type = noun chunks containing ``BODY_PARTS`` / ``INJURY_TYPES``
     attached to the trigger (e.g. "a *hamstring* *strain*").
  4. Modality = SPECULATED if a hedge ("could", "may", "fears", "doubt") governs the
     trigger, NEGATED if there's a ``neg`` dependent.
  5. Time = DATE/TIME entities, or "against <team>" / "in the <x> win" phrases.
"""
from __future__ import annotations

from sportsnlp.events.extractors.base import Extractor
from sportsnlp.events.preprocess import Passage
from sportsnlp.events.schema import EventType, InjuryEvent

TRIGGERS: dict[EventType, list[str]] = {
    "INJURY": ["injured", "suffered", "sustained", "tore", "pulled", "limped off",
               "stretchered off", "went off injured", "picked up", "hurt"],
    "RULED_OUT": ["ruled out", "will miss", "sidelined", "out for", "faces", "unavailable"],
    "DOUBTFUL": ["doubt", "doubtful", "fitness test", "race against time", "touch and go"],
    "RETURN": ["returns", "back in training", "fit again", "recovered", "made his comeback"],
}

BODY_PARTS = ["hamstring", "knee", "ankle", "groin", "calf", "thigh", "foot", "metatarsal",
              "achilles", "hip", "back", "shoulder", "head", "rib", "wrist", "ligament"]
INJURY_TYPES = ["strain", "tear", "rupture", "fracture", "break", "sprain", "concussion",
                "knock", "bruising", "problem", "complaint"]


class RuleExtractor(Extractor):
    name = "rules"

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        # TODO: load spaCy lazily here and build a PhraseMatcher over TRIGGERS.
        self.spacy_model = spacy_model

    def extract(self, passage: Passage) -> list[InjuryEvent]:
        raise NotImplementedError
