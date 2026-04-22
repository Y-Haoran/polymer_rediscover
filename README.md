# polymer_rediscover

`polymer_rediscover` is a starter repository for an FDA-aware polymer excipient ranking project focused on oral solid dosage forms.

## Project focus

The initial scientific scope is intentionally narrow:

- Target: polymer excipients used in oral solid formulations
- Context: route and dosage form constrained by FDA approved-use history
- Task: rank plausible polymer excipients for a given API and formulation context
- Validation: retrospective retrieval on approved products, then prospective dissolution or supersaturation testing

This repository is set up so the project can grow in three directions without rewriting the foundation:

- polymer representation learning
- FDA IID and DailyMed data preparation
- ranking and prospective validation workflows

The current scaffold now includes:

- `data/fda_iid/` and `data/dailymed/` placeholders for raw and normalized regulatory data
- a normalization schema for polymer candidate and synonym tables
- a generic ranking benchmark loader
- a frozen-backbone evaluation entrypoint with a deterministic hash baseline and optional PolyTAO support

## Proposed data flow

1. Pretrain or adapt a polymer encoder on large polymer corpora.
2. Anchor candidate polymers to FDA Inactive Ingredient Database context.
3. Build API polymer co-occurrence tables from DailyMed SPL data.
4. Train context-aware retrieval and ranking models.
5. Validate shortlisted polymers in lab assays.

## Repository layout

- `src/polymer_rediscover/`: Python package
- `docs/`: project framing and study design notes
- `data/`: place for raw and processed dataset manifests
- `tests/`: small unit tests for starter utilities

## Quick start

```bash
cd git_repos/polymer_rediscover
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m polymer_rediscover.cli
python3 -m unittest discover -s tests
```

To try the toy ranking benchmark:

```bash
PYTHONPATH=src python3 -m polymer_rediscover.evaluate \
  --benchmark data/benchmark/example_oral_polymer_ranking.jsonl \
  --candidates data/schema/candidate_polymers_example.tsv \
  --backbone hash
```

To experiment with frozen PolyTAO embeddings later:

```bash
pip install -e ".[ml]"
PYTHONPATH=src python3 -m polymer_rediscover.evaluate \
  --benchmark data/benchmark/example_oral_polymer_ranking.jsonl \
  --candidates data/schema/candidate_polymers_example.tsv \
  --backbone polytao
```

## Current status

This scaffold does not include downloaded FDA IID or DailyMed data yet, but it now has the schema and code paths needed to normalize them into a first retrieval benchmark.
