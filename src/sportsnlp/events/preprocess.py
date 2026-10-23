"""Stage 1 — turn raw cached articles into candidate passages worth extracting from.

Most Guardian football articles don't mention an injury at all, and running an
expensive extractor (LLM / fine-tuned model) over every sentence is wasteful. This
stage segments articles and keeps a high-recall subset of passages.

Unlike the archived NER approach, keep a *window of sentences* rather than single
sentences: "He limped off after 20 minutes" only makes sense with the previous
sentence that names the player.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date

# Deliberately broad: this is a recall filter, precision comes from the extractor.
# TODO: grow this from false negatives you find while annotating.
CANDIDATE_RE = re.compile(
    r"\b(injur\w*|hamstring|knee|ankle|groin|calf|thigh|ligament|achilles|metatarsal|"
    r"concussion|fractur\w*|strain\w*|tear|tore|torn|limp\w*|stretcher\w*|"
    r"ruled out|sidelined|doubt\w*|fitness|surgery|scan|knock|"
    r"returns?|returned|back in training|comeback)\b",
    re.IGNORECASE,
)


@dataclass
class Passage:
    article_id: str
    report_date: date
    headline: str
    text: str            # the sentence window
    sentence_start: int  # index of the first sentence in the window


def article_id(article: dict) -> str:
    """Stable id for a cached article (the cache has no Guardian id field)."""
    raw = f"{article.get('date', '')}|{article.get('headline', '')}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def report_date(article: dict) -> date:
    """Publication date (document creation time) — the anchor for relative time expressions."""
    return date.fromisoformat(article["date"][:10])


def split_sentences(text: str) -> list[str]:
    """Sentence-split an article body.

    TODO: pick a splitter (nltk ``sent_tokenize`` as in the archived notebooks, or
    spaCy if you also want dependency parses for the rule-based extractor).
    """
    raise NotImplementedError


def candidate_passages(article: dict, window: int = 1) -> list[Passage]:
    """Return passages of ``2 * window + 1`` sentences centred on each candidate sentence.

    TODO:
      - split the body, find sentences matching ``CANDIDATE_RE``
      - expand each hit by ``window`` sentences either side, merging overlapping windows
      - consider also including the headline, which often carries the key fact
        ("Kane faces six weeks out with ankle injury")
    """
    raise NotImplementedError
