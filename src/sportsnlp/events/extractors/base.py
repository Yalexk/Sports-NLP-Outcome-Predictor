"""Stage 2 — the common interface every extractor implements.

Keeping one interface means the rule baseline, the LLM extractor and any
fine-tuned model are scored by the same ``events.evaluate`` code against the
same gold set, which is what makes the comparison in your write-up meaningful.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sportsnlp.events.preprocess import Passage
from sportsnlp.events.schema import InjuryEvent


class Extractor(ABC):
    name: str = "base"

    @abstractmethod
    def extract(self, passage: Passage) -> list[InjuryEvent]:
        """Return every injury event mentioned in the passage (possibly none).

        Extractors fill trigger, event_type, modality, the argument fields and the
        *surface* time expression (``occurred.text``). Normalising that text to a
        date is ``events.temporal``'s job, and linking names to ``player_api_id``
        is ``events.linking``'s, so extractors stay comparable.
        """

    def extract_many(self, passages: list[Passage]) -> list[InjuryEvent]:
        return [event for p in passages for event in self.extract(p)]
