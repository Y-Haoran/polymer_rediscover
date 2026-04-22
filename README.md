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
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m polymer_rediscover.cli
python -m unittest discover -s tests
```

## Current status

This is the initial scaffold. It does not yet include proprietary or downloaded FDA or DailyMed datasets.
