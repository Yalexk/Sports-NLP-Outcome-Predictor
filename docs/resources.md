# Resources

## Text sources

| Source | What it gives you | Notes |
|---|---|---|
| [Guardian Open Platform](https://open-platform.theguardian.com/) | Full article `bodyText` with publication timestamps, searchable by date range and section | Already used. Free developer key with a daily request cap; the Guardian forum has threads on temporary research increases. Best coverage is the Premier League. |
| [Football Events (Kaggle, secareanualin)](https://www.kaggle.com/datasets/secareanualin/football-events) | ~9k top-5-league matches, roughly 2011/12–2016/17, with minute-level commentary text scraped from BBC/ESPN/onefootball (`events.csv`, `ginf.csv`) | Overlaps the European Soccer DB period. Could provide in-match injury timing ("delay … because of an injury") — check the data card for the exact event types first. |
| [SoccerNet-Echoes](https://arxiv.org/abs/2405.07354) | Whisper-transcribed audio commentary for SoccerNet games | Research/educational use only. Noisy ASR text; good for in-match "went down injured" moments. |
| [SOCCER (Zhang & Eickhoff, NAACL 2021)](https://arxiv.org/abs/2106.01972) | Commentary paired with game-state tracking | A related task framing (tracking events from sparse commentary) worth citing. |
| Club sites / BBC "team news" previews | Dense, structured injury statements | Scraping only: check terms of service, cache aggressively, respect robots.txt. |

## Injury ground truth (for evaluating the dates you extract)

- **Transfermarkt injury histories:** per player, injury type, `from`/`until`, days and
  games missed. No official API; people scrape it. Examples of derived data:
  the [StatsBomb + Transfermarkt figshare dataset](https://figshare.com/articles/dataset/Multidimensional_match_performance_dataset_-_StatsBomb_Transfermarkt/25648770)
  has `Injury_from` / `Injury_until` / `Days` / `Games_missed` fields, and the R
  [`injurytools`](https://cran.r-project.org/web/packages/injurytools/vignettes/visualize-injury-data.html)
  package ships a Transfermarkt-derived sample. Use it to check `occurred.value`
  against `from` on a sample of players. It's noisy too, so report agreement, not "accuracy".
- **Lineup gaps in the European Soccer DB:** a regular starter disappearing from the XI is a
  weak, free signal. It mixes in rotation and suspensions, so it can't serve as gold.

## Reading list

### Event extraction
- **ACE 2005** (LDC2006T06) has a `Life:Injure` event type. Its annotation guidelines
  (triggers, arguments, the time argument) are the template these guidelines follow.
- Du & Cardie, 2020. [Event Extraction by Answering (Almost) Natural Questions](https://arxiv.org/abs/2004.13625). EMNLP. *QA framing ("Who was injured?"), good for low data.*
- Li, Ji & Han, 2021. [Document-Level Event Argument Extraction by Conditional Generation](https://arxiv.org/abs/2104.05919). NAACL. *Arguments outside the trigger sentence, which is exactly the "He limped off" problem. Introduces WikiEvents.*
- Hsu et al., 2022. [DEGREE: A Data-Efficient Generation-Based Event Extraction Model](https://arxiv.org/abs/2108.12724). NAACL. *Strong with few hundred examples, which is your gold-set size.*
- Paolini et al., 2021. [Structured Prediction as Translation between Augmented Natural Languages (TANL)](https://arxiv.org/abs/2101.05779). ICLR.
- Lu et al., 2022. [Unified Structure Generation for Universal Information Extraction (UIE)](https://arxiv.org/abs/2203.12277). ACL.
- Gao et al., 2023. [Exploring the Feasibility of ChatGPT for Event Extraction](https://arxiv.org/abs/2303.03836). *Zero-shot ChatGPT reached about half of a task-specific model on ACE and was sensitive to prompt style. That's the reason to evaluate the LLM extractor rigorously rather than trust it.*

### Temporal information extraction (the "when")
- **TimeML / TimeBank** (Pustejovsky et al., 2003): the standard markup for time expressions (TIMEX3) and their normalised values.
- **TempEval-3** (UzZaman et al., SemEval 2013): shared task on timex normalisation and event–time relations, including relations to the *document creation time*, which is your `report_date`.
- **HeidelTime** (Strötgen & Gertz, SemEval 2010; LRE 2013): rule-based temporal tagger with a news-specific mode. A strong baseline for `normalise_expression`.
- **SUTime** (Chang & Manning, LREC 2012): Stanford's rule-based temporal tagger.
- Ning, Wu & Roth, 2018. [A Multi-Axis Annotation Scheme for Event Temporal Relations (MATRES)](https://arxiv.org/abs/1804.07828). ACL. *Read for how to make temporal annotation reliable.*
- **Clinical analogue:** the i2b2 2012 temporal relations challenge and the THYME corpus extract medical events and when they happened relative to the note date. This is structurally the same problem as yours and a good comparison for the related-work section.

### Sports and news-specific work
- Kuptabut & Netisopakul, 2016. *Event extraction using ontology directed semantic grammar*, J. Information Science and Engineering. Football events from news pages into frames ([record](https://dspace.kmitl.ac.th/items/4262065d-eecb-4e1d-9152-ddff80f5d69b/full)).
- Hassan et al., 2020. [Injury prevalence, types and mechanisms in football: a media-based approach](https://eprints.unisza.edu.my/6751). *Manual content analysis of news, showing the question matters; your pipeline automates it.*
- NewsReader project (VU Amsterdam, 2013–2015): event-centric knowledge graphs from news, including a World Cup 2014 hackathon that suggested injury prediction as a use case.

## Tools
- **spaCy**: sentence splitting, dependency parses for the rule extractor.
- **dateparser** (`RELATIVE_BASE`, `PREFER_DATES_FROM='past'`) or **HeidelTime** (Python wrappers exist): temporal normalisation.
- **fastcoref**: pronoun resolution before linking.
- **rapidfuzz**: name linking (already a dependency).
- **Label Studio** / **doccano**: annotation UIs for the gold set.
