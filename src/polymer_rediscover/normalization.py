"""Utilities for candidate-name normalization and synonym lookup."""

from __future__ import annotations

import csv
from pathlib import Path
import re


def normalize_text(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


class SynonymIndex:
    """Maps free-text names onto canonical polymer identifiers."""

    def __init__(self, mapping: dict[str, str], canonical_names: dict[str, str]) -> None:
        self._mapping = mapping
        self._canonical_names = canonical_names

    @classmethod
    def from_tsv(cls, path: str | Path) -> "SynonymIndex":
        mapping: dict[str, str] = {}
        canonical_names: dict[str, str] = {}
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                canonical_id = row["canonical_polymer_id"].strip()
                canonical_name = row["canonical_name"].strip()
                synonym = normalize_text(row["synonym"])
                canonical_names[canonical_id] = canonical_name
                if synonym:
                    mapping[synonym] = canonical_id
                normalized_canonical = normalize_text(canonical_name)
                if normalized_canonical:
                    mapping[normalized_canonical] = canonical_id
        return cls(mapping, canonical_names)

    def resolve(self, raw_name: str) -> str | None:
        return self._mapping.get(normalize_text(raw_name))

    def canonical_name_for(self, canonical_id: str) -> str | None:
        return self._canonical_names.get(canonical_id)
