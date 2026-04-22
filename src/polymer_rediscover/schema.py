"""Core data structures for normalized records and benchmark inputs."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any


@dataclass(frozen=True)
class FdaIidRecord:
    ingredient_name: str
    canonical_polymer_id: str
    route: str
    dosage_form: str
    unii: str = ""
    cas: str = ""
    potency_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DailyMedRecord:
    product_id: str
    api_name: str
    inactive_ingredient_name: str
    route: str
    dosage_form: str
    label_date: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolymerCandidate:
    candidate_id: str
    canonical_name: str
    candidate_text: str
    family: str = ""
    unii: str = ""
    cas: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "PolymerCandidate":
        metadata_text = (row.get("metadata_json") or "").strip()
        metadata = json.loads(metadata_text) if metadata_text else {}
        return cls(
            candidate_id=row["candidate_id"].strip(),
            canonical_name=row["canonical_name"].strip(),
            candidate_text=row["candidate_text"].strip(),
            family=(row.get("family") or "").strip(),
            unii=(row.get("unii") or "").strip(),
            cas=(row.get("cas") or "").strip(),
            metadata=metadata,
        )


@dataclass(frozen=True)
class RankingExample:
    example_id: str
    candidate_ids: tuple[str, ...]
    positive_candidate_ids: frozenset[str]
    api_name: str = ""
    route: str = ""
    dosage_form: str = ""
    query_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RankingExample":
        positive_ids = frozenset(str(value) for value in payload["positive_candidate_ids"])
        candidate_ids = tuple(str(value) for value in payload["candidate_ids"])
        return cls(
            example_id=str(payload["example_id"]),
            candidate_ids=candidate_ids,
            positive_candidate_ids=positive_ids,
            api_name=str(payload.get("api_name", "")),
            route=str(payload.get("route", "")),
            dosage_form=str(payload.get("dosage_form", "")),
            query_text=str(payload.get("query_text", "")),
            metadata=dict(payload.get("metadata", {})),
        )
