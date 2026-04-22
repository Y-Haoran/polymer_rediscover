"""Benchmark loading utilities for polymer excipient ranking."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .schema import PolymerCandidate, RankingExample


def _delimiter_for(path: Path) -> str:
    return "\t" if path.suffix.lower() == ".tsv" else ","


def build_default_query_text(example: RankingExample) -> str:
    parts = []
    if example.api_name:
        parts.append(f"api {example.api_name}")
    if example.route:
        parts.append(f"route {example.route}")
    if example.dosage_form:
        parts.append(f"dosage form {example.dosage_form}")
    return " | ".join(parts)


def load_candidates(path: str | Path) -> dict[str, PolymerCandidate]:
    candidate_path = Path(path)
    with candidate_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=_delimiter_for(candidate_path))
        candidates = {
            candidate.candidate_id: candidate
            for candidate in (PolymerCandidate.from_row(row) for row in reader)
        }
    return candidates


def load_ranking_examples(path: str | Path) -> list[RankingExample]:
    examples: list[RankingExample] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            example = RankingExample.from_payload(payload)
            if not example.query_text:
                example = RankingExample(
                    example_id=example.example_id,
                    candidate_ids=example.candidate_ids,
                    positive_candidate_ids=example.positive_candidate_ids,
                    api_name=example.api_name,
                    route=example.route,
                    dosage_form=example.dosage_form,
                    query_text=build_default_query_text(example),
                    metadata=example.metadata,
                )
            examples.append(example)
    return examples


def validate_examples(
    examples: Iterable[RankingExample],
    candidates: dict[str, PolymerCandidate],
) -> None:
    candidate_ids = set(candidates)
    for example in examples:
        missing = set(example.candidate_ids) - candidate_ids
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(
                f"example {example.example_id} references unknown candidates: {missing_text}"
            )
        absent_positive = example.positive_candidate_ids - set(example.candidate_ids)
        if absent_positive:
            missing_text = ", ".join(sorted(absent_positive))
            raise ValueError(
                f"example {example.example_id} has positives outside candidate_ids: {missing_text}"
            )
