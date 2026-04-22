"""Small TSV and CSV helpers used by the pipeline scripts."""

from __future__ import annotations

import csv
from pathlib import Path


def read_delimited_rows(path: str | Path) -> list[dict[str, str]]:
    file_path = Path(path)
    delimiter = "\t" if file_path.suffix.lower() == ".tsv" else ","
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        return [dict(row) for row in reader]


def write_tsv(path: str | Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: _coerce_cell(row.get(field, ""))
                    for field in fieldnames
                }
            )


def _coerce_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    return str(value)
