# Injury event annotation guidelines

The code version of this schema is `src/sportsnlp/events/schema.py`. Gold annotations
go in `data/annotations/gold_events.jsonl`, one `InjuryEvent` per line.

## What counts as an event

Annotate one event per **(player, event type)** stated in the passage. Event types:

| `event_type` | Meaning | Typical triggers |
|---|---|---|
| `INJURY` | The injury itself occurred | *suffered, sustained, tore, pulled, limped off, went off injured, picked up a knock* |
| `RULED_OUT` | Player will definitely miss upcoming match(es) | *ruled out, will miss, sidelined, out for six weeks* |
| `DOUBTFUL` | Availability uncertain | *doubt, faces a fitness test, race against time* |
| `RETURN` | Player is fit / back | *returns, back in training, fit again, made his comeback* |

Suspensions are **not** injury events (they're already derivable from card data).

One sentence can hold several events: *"Kane, who tore his hamstring against Chelsea,
will miss the derby"* → one `INJURY` and one `RULED_OUT`.

## Fields

- **trigger** — the minimal word/phrase that evokes the event, copied exactly.
- **modality**
  - `ASSERTED`: stated as fact ("has been ruled out").
  - `SPECULATED`: hedged ("could miss", "fears he has", "is likely to be out").
  - `NEGATED`: explicitly denied ("is not injured", "has been passed fit" for `INJURY`).
- **player_mention** — as written, even if a pronoun. **player_name** — full name of
  the referent, resolved from context (fill this even when the mention is "he").
- **body_part / injury_type** — only if stated. "Hamstring strain" → `hamstring` / `strain`.
  "Knock" is an `injury_type`.
- **occurred** (for `INJURY` only):
  - `text`: the exact words that say when, e.g. "on Saturday", "in the 2-1 win at Stoke",
    "during training on Tuesday". `null` if not stated — don't infer from report date.
  - `value`: the calendar date you determine (use the match date for fixture references).
  - `precision`: `DAY` / `WEEK` ("last week") / `MONTH` / `SEASON` / `UNKNOWN`.
  - `match_api_id`: if the text names a specific fixture and you can find it.
- **expected_duration** — as written: "three weeks", "rest of the season".
- **expected_return** — for `RULED_OUT`, if a date/match is given ("until after Christmas").

## Worked examples

Report date for all: **Wednesday 2012-03-07**.

> *"Harry Kane limped off in Saturday's 2-1 defeat at Stoke and is expected to miss three weeks with a hamstring strain."*

```json
[
 {"event_type": "INJURY", "trigger": "limped off", "modality": "ASSERTED",
  "player_mention": "Harry Kane", "player_name": "Harry Kane",
  "body_part": "hamstring", "injury_type": "strain",
  "occurred": {"text": "in Saturday's 2-1 defeat at Stoke", "value": "2012-03-03", "precision": "DAY", "match_api_id": null}},
 {"event_type": "RULED_OUT", "trigger": "expected to miss", "modality": "SPECULATED",
  "player_mention": "Harry Kane", "player_name": "Harry Kane",
  "expected_duration": "three weeks"}
]
```

> *"Walker trained on Tuesday and is no longer a doubt."*

→ one `DOUBTFUL` event with `modality: NEGATED` (and optionally a `RETURN`).

> *"The manager refused to rule out Modric, who has been nursing an ankle problem."*

→ `DOUBTFUL` (`trigger: "refused to rule out"`, ASSERTED) and `INJURY`
(`trigger: "nursing"`, `body_part: ankle`, `injury_type: problem`, `occurred.text: null`, `precision: UNKNOWN`).

> *"Injuries have plagued United this season."*

→ no event (no specific player).

## Edge cases
- **Past-season injuries** mentioned as background ("since his knee injury in 2010"):
  annotate the `INJURY` with `precision: SEASON` or `MONTH`. `aggregate` will discard old spells.
- **Same event twice in one passage**: annotate once.
- **Non-players** (managers, referees): skip.
