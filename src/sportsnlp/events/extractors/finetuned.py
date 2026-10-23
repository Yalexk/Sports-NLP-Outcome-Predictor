"""Optional, later: a fine-tuned extractor trained on gold + silver labels.

Two framings that fit this schema well (see docs/resources.md):
  - QA-style (Du & Cardie 2020): one question per argument, e.g. "Who was injured?",
    "When did the injury happen?" — reuses extractive QA models, handles multi-word spans.
  - Generative (TANL / DEGREE): a seq2seq model (e.g. flan-t5) emits a linearised
    event string that you parse back into ``InjuryEvent``.

Only worth doing once the rule and LLM extractors are evaluated, so you know
what a fine-tuned model has to beat.
"""
from __future__ import annotations

from sportsnlp.events.extractors.base import Extractor
from sportsnlp.events.preprocess import Passage
from sportsnlp.events.schema import InjuryEvent


class FinetunedExtractor(Extractor):
    name = "finetuned"

    def __init__(self, model_dir: str):
        self.model_dir = model_dir

    def extract(self, passage: Passage) -> list[InjuryEvent]:
        raise NotImplementedError
