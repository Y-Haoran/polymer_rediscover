# Data Setup

This project assumes a staged build of the first benchmark rather than direct model fine-tuning.

## Recommended directory use

- `data/fda_iid/raw/`: original FDA IID exports
- `data/dailymed/raw/`: original DailyMed label or SPL exports
- `data/schema/`: candidate polymer and synonym tables
- `data/benchmark/`: JSONL ranking examples

The code supports both:

- manual placement of raw FDA IID zip files and DailyMed XML or ZIP label files
- scripted download from official FDA and DailyMed sources

## Stage 2 normalization targets

From FDA IID, normalize at least:

- inactive ingredient name
- canonical polymer identifier
- route
- dosage form
- UNII
- CAS when available
- potency text and parsed numeric range when possible

## Stage 3 product join targets

From DailyMed, normalize at least:

- set ID or product identifier
- active ingredient or API name
- inactive ingredient names
- route
- dosage form
- label version or date when captured

## First benchmark shape

The initial benchmark should support the following question:

`Given an API and an oral dosage-form context, which polymer excipients are most plausible retrieval targets?`

Keep the first benchmark conservative:

- use product-level co-occurrence as supervision
- do not infer functional roles like ASD carrier unless explicitly curated
- keep route and dosage form explicit in the query context

## Model sequence

1. Start with frozen backbones and non-neural baselines.
2. Confirm signal on the retrospective benchmark.
3. Fine-tune only after the benchmark and leakage controls are stable.

## Suggested command sequence

```bash
PYTHONPATH=src python3 -m polymer_rediscover.fda_iid download
PYTHONPATH=src python3 -m polymer_rediscover.fda_iid normalize

PYTHONPATH=src python3 -m polymer_rediscover.dailymed download-metadata
# If you already have DailyMed ZIP or XML labels, put them in data/dailymed/raw/labels/
# Otherwise fetch specific current labels by setid:
PYTHONPATH=src python3 -m polymer_rediscover.dailymed fetch-setids --setid-file path/to/setids.txt
PYTHONPATH=src python3 -m polymer_rediscover.dailymed parse

PYTHONPATH=src python3 -m polymer_rediscover.assemble build-benchmark
```
