"""LLM extractor: few-shot prompt -> JSON matching ``InjuryEvent``.

Likely your strongest extractor out of the box, and useful two other ways:
  - pre-annotating passages so you only *correct* labels instead of writing them
    (much faster gold-set construction; report agreement on a hand-only subset)
  - generating silver training data for a smaller fine-tuned model

Provider-agnostic on purpose: pass in any ``complete(prompt) -> str`` callable.
Cache responses on disk keyed by (model, prompt hash) so reruns are free and
results are reproducible.
"""
from __future__ import annotations

from collections.abc import Callable

from sportsnlp.events.extractors.base import Extractor
from sportsnlp.events.preprocess import Passage
from sportsnlp.events.schema import InjuryEvent

PROMPT_TEMPLATE = """\
You extract football injury events from news text.

Article published: {report_date}
Passage:
\"\"\"{text}\"\"\"

Return a JSON list. Each item has: trigger, event_type (INJURY | RULED_OUT | DOUBTFUL | RETURN),
modality (ASSERTED | SPECULATED | NEGATED), player_mention, body_part, injury_type,
occurred_text (the exact words saying when the injury happened, or null),
expected_duration. Use null for anything not stated. Do not guess. Return [] if none.

{examples}
"""


class LLMExtractor(Extractor):
    name = "llm"

    def __init__(self, complete: Callable[[str], str], examples: str = ""):
        self.complete = complete
        self.examples = examples  # TODO: 3–5 worked examples from docs/injury_event_schema.md

    def build_prompt(self, passage: Passage) -> str:
        return PROMPT_TEMPLATE.format(
            report_date=passage.report_date.isoformat(),
            text=passage.text,
            examples=self.examples,
        )

    def parse(self, raw: str, passage: Passage) -> list[InjuryEvent]:
        """TODO: json-decode ``raw``, validate each item, map ``occurred_text`` into
        ``TimeAnchor(text=...)``, and drop (but log) malformed items."""
        raise NotImplementedError

    def extract(self, passage: Passage) -> list[InjuryEvent]:
        return self.parse(self.complete(self.build_prompt(passage)), passage)
