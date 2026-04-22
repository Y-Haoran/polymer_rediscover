"""Utilities for candidate-name normalization and synonym lookup."""

from __future__ import annotations

import csv
from pathlib import Path
import re


def normalize_text(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def normalize_route(value: str) -> str:
    return normalize_text(value)


def normalize_dosage_form(value: str) -> str:
    return normalize_text(value)


def dosage_form_category(value: str) -> str:
    text = normalize_dosage_form(value)
    if not text:
        return "unknown"
    if "tablet" in text:
        return "tablet"
    if "capsule" in text:
        return "capsule"
    if "film" in text:
        return "film"
    if "granule" in text:
        return "granule"
    if "powder" in text:
        return "powder"
    if "pellet" in text:
        return "pellet"
    if "solution" in text:
        return "solution"
    if "suspension" in text:
        return "suspension"
    return text


def is_oral_solid_context(route: str, dosage_form: str) -> bool:
    return normalize_route(route) == "oral" and dosage_form_category(dosage_form) in {
        "tablet",
        "capsule",
    }


class SynonymIndex:
    """Maps free-text names onto canonical polymer identifiers."""

    def __init__(self, mapping: dict[str, str], canonical_names: dict[str, str]) -> None:
        self._mapping = mapping
        self._canonical_names = canonical_names
        self._ordered_synonyms = sorted(mapping, key=len, reverse=True)

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
        normalized = normalize_text(raw_name)
        exact = self._mapping.get(normalized)
        if exact:
            return exact
        padded = f" {normalized} "
        for synonym in self._ordered_synonyms:
            if len(synonym) < 4:
                continue
            if f" {synonym} " in padded:
                return self._mapping[synonym]
        return None

    def canonical_name_for(self, canonical_id: str) -> str | None:
        return self._canonical_names.get(canonical_id)
