# Benchmark Schema

The benchmark code uses two normalized inputs:

1. Candidate polymers in TSV format
2. Ranking examples in JSONL format

## Candidate table

Required columns:

- `candidate_id`
- `canonical_name`
- `candidate_text`

Optional columns:

- `family`
- `unii`
- `cas`
- `metadata_json`

`candidate_text` is the backbone-facing representation for the polymer. For toy experiments it can be plain text. For real frozen PolyTAO experiments it should be replaced with a more meaningful structure-aware prompt.

## Synonym table

Required columns:

- `canonical_polymer_id`
- `canonical_name`
- `synonym`

Optional columns:

- `source`
- `unii`
- `cas`

## Ranking example JSONL

Required fields:

- `example_id`
- `candidate_ids`
- `positive_candidate_ids`

Recommended fields:

- `api_name`
- `route`
- `dosage_form`
- `query_text`
- `metadata`

If `query_text` is absent, the loader constructs one from the API and context fields.
