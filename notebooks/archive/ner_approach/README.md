# Archived: keyword and NER-based injury signals

Kept for reference and for the write-up's "what we tried first" section. Not maintained.

| Notebook | What it did |
|---|---|
| `01_keyword_features.ipynb` | Regex counts of injury / suspension / return keywords per team, merged into the baseline models. |
| `02_initial_generation.ipynb` | `dslim/bert-large-NER` PERSON spans → fuzzy-matched against the Player table → keyword-proximity BIO tags (PLAYER / INJURY / STATUS). |
| `03_active_learning.ipynb` | Flagged sentences where keywords fired but no tag did; manual correction loop into `gold_labels.jsonl`. |
| `04_finetune_sportsbert.ipynb` | Fine-tuned `microsoft/SportsBERT` for token classification on the silver labels. |

## Why it was dropped

- **Keyword counts didn't move accuracy** (GBC ≈ 0.51 with or without). One injury is
  reported many times, previews mention both teams, and counts can't say *whose* injury.
- **NER labels spans, not events.** A `B-INJURY` on "hamstring" doesn't say whether the
  player was injured, is returning, or isn't injured at all. There's no time attached.
- **Sentence-level only:** "He limped off after 20 minutes" loses the player, who was named a sentence earlier.
- **Silver labels came from the same heuristics** the model was meant to improve on, so
  fine-tuning mostly learned the keyword-proximity rule back.
- **Linking against all ~11k players** with fuzzy matching confused namesakes and non-players.

These map directly onto the design of the new pipeline: event types + modality,
passage windows, squad-restricted linking, temporal grounding, and spell aggregation.
See [`docs/PLAN.md`](../../../docs/PLAN.md).

Paths in these notebooks were updated to find the repo root, but they still expect
`data/initial_labels.jsonl` etc. from the original runs.
