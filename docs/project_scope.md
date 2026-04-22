# Project Scope

## Core question

Can a polymer foundation model, anchored to FDA approved-use context, rank plausible polymer excipients for poorly soluble oral small molecules better than standard chemistry baselines?

## Disciplined claims

- FDA IID is used as approved-use context, not as a universal safety label.
- DailyMed provides product-level evidence of marketed API and excipient co-occurrence.
- Role-specific claims such as "best ASD carrier" require either curated functional labels or prospective lab validation.

## Suggested first paper

- Primary retrospective task: retrieve held-out marketed polymer excipients for an API in a defined oral dosage-form context
- Baselines: fingerprint similarity, nearest-neighbor polymer embeddings, and simple frequency priors
- Primary metric: ranking quality such as recall at k and mean reciprocal rank
- Prospective study: test top-ranked polymers on a small number of hard APIs

## Data model

Minimal entities to normalize:

- polymer excipient
- API
- route
- dosage form
- potency or concentration range when available
- product identifier

## Immediate next steps

1. Download FDA IID and DailyMed exports into the repo data layout.
2. Expand the polymer candidate list and synonym normalization rules beyond the toy examples.
3. Implement train, validation, and family-aware split logic on normalized product tables.
4. Benchmark frozen backbones before attempting any PolyTAO adaptation.
