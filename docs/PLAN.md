# Implementation plan

**Goal:** extract *injury events* — who got injured, how, and **when it happened** —
from pre-match news, turn them into leak-free player-availability features, and
measure whether they improve match outcome prediction over structured features.

**Why the pivot from NER:** NER tags spans ("hamstring" = INJURY) but has no notion
of an *event*: it can't tell "injured on Saturday" from "returns from injury", can't
link a pronoun to a player, and gives no date. Counting tags reproduced the same
double-counting problem as the keyword counts (see
[`notebooks/archive/ner_approach/README.md`](../notebooks/archive/ner_approach/README.md)).
Event extraction makes the event itself the unit, with typed arguments and a time anchor.

```
Guardian cache ─► preprocess ─► extractor ─► linking ─► temporal ─► aggregate ─► availability ─► outcome model
 (data/)          passages      InjuryEvent  player_id   date        spells       features         ablation
                                    ▲
                     gold annotations (data/annotations/) ─► evaluate
```

Each box is one module under `src/sportsnlp/`. Skeletons raise `NotImplementedError`;
`tests/test_events.py` has `xfail` specs that start passing as you implement them.

---

## Phase 0 — Setup ✅ (done in this restructure)
- [x] Package layout (`src/sportsnlp`), `pip install -e .`, tests run with `pytest`
- [x] Structured features deduplicated into `features/match_features.py` (tested against the notebook version)
- [x] Guardian fetching as a module + resumable `scripts/fetch_articles.py`
- [x] NER work archived with a retrospective
- [x] `InjuryEvent` schema (`events/schema.py`) + annotation guidelines (`docs/injury_event_schema.md`)

## Phase 1 — Data and gold set (do this before any modelling)
1. Re-populate `data/articles_cache.json` (or copy your old one back in; keys are unchanged).
   Restrict to the leagues the coverage check showed are well-covered (mainly the EPL).
2. Implement `events/preprocess.py` (`split_sentences`, `candidate_passages`) → passes the xfail spec.
3. `python scripts/sample_for_annotation.py --n 300`.
4. Annotate ~200–300 passages into `data/annotations/gold_events.jsonl` following
   `docs/injury_event_schema.md`. Have a second person do ~50 so you can report
   inter-annotator agreement. Split into dev (tune prompts/rules) and test (touch once).
   - Tip: annotate in Label Studio / doccano, or pre-fill with the LLM extractor and correct.
5. Include ~10% random non-candidate passages to measure the recall of `CANDIDATE_RE`.

**Deliverable:** a frozen gold test set. Everything after this is measured against it.

## Phase 2 — Extractors
1. `extractors/rules.py` — trigger lexicon + spaCy dependency patterns. This is your baseline.
2. `extractors/llm.py` — few-shot JSON extraction. Cache responses to disk.
3. Implement `evaluate.temporal_scores`; compare both on the dev set, then once on test:
   detection F1, argument F1, modality accuracy.
4. *(Optional)* `extractors/finetuned.py` — QA-style or seq2seq model trained on gold + LLM silver labels.

## Phase 3 — Temporal grounding (the core contribution)
1. `temporal.normalise_expression` — weekdays, "last weekend", explicit dates; never after `report_date`.
2. `temporal.resolve_fixture` — "against Arsenal" → most recent matching row in `Match`.
3. Score: % of gold INJURY dates exact / ±1 / ±3 days; break down by expression type
   (fixture reference vs weekday vs none). This table is likely the most interesting
   result in the write-up.
4. External check: compare inferred start dates against Transfermarkt injury histories
   for a sample of players (see `docs/resources.md`).

## Phase 4 — Linking and aggregation
1. `linking.squad_on` + `linking.link_player` — restrict candidates to the team's recent lineups.
2. `aggregate.build_spells` — collapse repeated reports into one spell per injury.
3. Sanity check: spells for well-known injuries you can verify by hand.

## Phase 5 — Outcome model (your next focus)
1. `features/availability.py` — expected XI, injured regulars, missing rating; NaN + flag when no coverage.
2. `models/outcome.run_ablation` — structured vs +keywords vs +availability; add the bookmaker baseline.
3. Report accuracy **and** log-loss/Brier, on covered matches only as well as overall.
4. Error analysis: matches where availability features moved the prediction most.

## Risks to keep in mind
- **Coverage:** Guardian coverage outside England is thin; the effect can only show where there's text.
- **Leakage:** only events with `report_date < match date`; the fetch window already ends the day before kick-off.
- **Odds already price in injuries:** beating structured features is realistic, beating bookmakers is a stretch goal.
- **Lineups are post-hoc:** the injured player isn't in the recorded XI, so compare against an *expected* XI.
