"""Download and normalize FDA Inactive Ingredient Database releases."""

from __future__ import annotations

import argparse
from html import unescape
import re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import zipfile

from .benchmark import load_candidates
from .normalization import (
    SynonymIndex,
    dosage_form_category,
    normalize_dosage_form,
    normalize_route,
    normalize_text,
)
from .tabular import read_delimited_rows, write_tsv

FDA_IID_PAGE = (
    "https://www.fda.gov/drugs/drug-approvals-and-databases/"
    "inactive-ingredients-database-download"
)
DEFAULT_RAW_DIR = Path("data/fda_iid/raw/releases")
DEFAULT_PROCESSED_DIR = Path("data/fda_iid/processed")
DEFAULT_CANDIDATES = Path("data/schema/candidate_polymers_seed.tsv")
DEFAULT_SYNONYMS = Path("data/schema/polymer_synonyms_seed.tsv")


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=120) as response:
        payload = response.read()
        filename = parse_filename_from_headers(response.headers.get("Content-Disposition", ""))
        return payload, filename


def parse_filename_from_headers(content_disposition: str) -> str:
    match = re.search(r'filename="?([^";]+)"?', content_disposition)
    return match.group(1) if match else ""


def resolve_current_download_url(page_html: str) -> str:
    for href, label in extract_anchor_pairs(page_html):
        if label == "Inactive Ingredients Database Download File":
            return urljoin(FDA_IID_PAGE, href)
    raise ValueError("could not find current FDA IID download link")


def extract_anchor_pairs(page_html: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for match in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page_html, re.I | re.S):
        href = unescape(match.group(1))
        inner_html = re.sub(r"<[^>]+>", " ", match.group(2))
        label = " ".join(unescape(inner_html).split())
        pairs.append((href, label))
    return pairs


def download_current_release(raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    page_html = fetch_text(FDA_IID_PAGE)
    download_url = resolve_current_download_url(page_html)
    payload, filename = fetch_bytes(download_url)
    if not filename:
        filename = Path(download_url).name or "fda_iid_current.zip"
    zip_path = raw_dir / filename
    zip_path.write_bytes(payload)
    return zip_path


def extract_release(zip_path: Path, destination_dir: Path | None = None) -> Path:
    target_dir = destination_dir or zip_path.with_suffix("")
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(target_dir)
    return target_dir


def find_primary_csv(search_dir: Path) -> Path:
    candidates = sorted(search_dir.rglob("IIR_OCOMM.csv"))
    if candidates:
        return candidates[0]
    fallback = sorted(search_dir.rglob("*.csv"))
    if not fallback:
        raise FileNotFoundError(f"no CSV file found under {search_dir}")
    return fallback[0]


def normalize_iid_row(row: dict[str, str]) -> dict[str, str]:
    route = row.get("ROUTE", "").strip()
    dosage_form = row.get("DOSAGE_FORM", "").strip()
    return {
        "ingredient_name": row.get("INGREDIENT_NAME", "").strip(),
        "ingredient_name_normalized": normalize_text(row.get("INGREDIENT_NAME", "")),
        "route": route,
        "route_normalized": normalize_route(route),
        "dosage_form": dosage_form,
        "dosage_form_normalized": normalize_dosage_form(dosage_form),
        "dosage_form_category": dosage_form_category(dosage_form),
        "cas_number": row.get("CAS_NUMBER", "").strip(),
        "unii": row.get("UNII", "").strip(),
        "potency_amount": row.get("POTENCY_AMOUNT", "").strip(),
        "potency_unit": row.get("POTENCY_UNIT", "").strip(),
        "maximum_daily_exposure": row.get("MAXIMUM_DAILY_EXPOSURE", "").strip(),
        "maximum_daily_exposure_unit": row.get("MAXIMUM_DAILY_EXPOSURE_UNIT", "").strip(),
        "record_updated": row.get("RECORD_UPDATED", "").strip(),
    }


def build_polymer_subset(
    normalized_rows: list[dict[str, str]],
    synonym_index: SynonymIndex,
    candidate_table_path: Path,
) -> list[dict[str, str]]:
    candidates = load_candidates(candidate_table_path)
    polymer_rows: list[dict[str, str]] = []
    for row in normalized_rows:
        canonical_id = synonym_index.resolve(row["ingredient_name"])
        if not canonical_id:
            continue
        candidate = candidates.get(canonical_id)
        polymer_rows.append(
            {
                **row,
                "canonical_polymer_id": canonical_id,
                "canonical_name": synonym_index.canonical_name_for(canonical_id) or "",
                "candidate_family": candidate.family if candidate else "",
            }
        )
    return polymer_rows


def normalize_release_to_tables(
    csv_path: Path,
    processed_dir: Path,
    synonyms_path: Path,
    candidate_table_path: Path,
) -> tuple[Path, Path]:
    rows = [normalize_iid_row(row) for row in read_delimited_rows(csv_path)]
    synonym_index = SynonymIndex.from_tsv(synonyms_path)
    polymer_rows = build_polymer_subset(rows, synonym_index, candidate_table_path)

    all_rows_path = processed_dir / "iid_all_normalized.tsv"
    polymer_rows_path = processed_dir / "iid_polymer_records.tsv"
    write_tsv(
        all_rows_path,
        rows,
        [
            "ingredient_name",
            "ingredient_name_normalized",
            "route",
            "route_normalized",
            "dosage_form",
            "dosage_form_normalized",
            "dosage_form_category",
            "cas_number",
            "unii",
            "potency_amount",
            "potency_unit",
            "maximum_daily_exposure",
            "maximum_daily_exposure_unit",
            "record_updated",
        ],
    )
    write_tsv(
        polymer_rows_path,
        polymer_rows,
        [
            "ingredient_name",
            "ingredient_name_normalized",
            "canonical_polymer_id",
            "canonical_name",
            "candidate_family",
            "route",
            "route_normalized",
            "dosage_form",
            "dosage_form_normalized",
            "dosage_form_category",
            "cas_number",
            "unii",
            "potency_amount",
            "potency_unit",
            "maximum_daily_exposure",
            "maximum_daily_exposure_unit",
            "record_updated",
        ],
    )
    return all_rows_path, polymer_rows_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FDA IID download and normalization tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download the current FDA IID release.")
    download_parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))

    normalize_parser = subparsers.add_parser("normalize", help="Normalize an FDA IID CSV into TSV tables.")
    normalize_parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))
    normalize_parser.add_argument("--csv-path", default="")
    normalize_parser.add_argument("--processed-dir", default=str(DEFAULT_PROCESSED_DIR))
    normalize_parser.add_argument("--synonyms", default=str(DEFAULT_SYNONYMS))
    normalize_parser.add_argument("--candidates", default=str(DEFAULT_CANDIDATES))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "download":
        raw_dir = Path(args.raw_dir)
        zip_path = download_current_release(raw_dir)
        extract_dir = extract_release(zip_path)
        print(f"downloaded={zip_path}")
        print(f"extracted={extract_dir}")
        return

    raw_dir = Path(args.raw_dir)
    processed_dir = Path(args.processed_dir)
    csv_path = Path(args.csv_path) if args.csv_path else find_primary_csv(raw_dir)
    all_rows_path, polymer_rows_path = normalize_release_to_tables(
        csv_path=csv_path,
        processed_dir=processed_dir,
        synonyms_path=Path(args.synonyms),
        candidate_table_path=Path(args.candidates),
    )
    print(f"all_rows={all_rows_path}")
    print(f"polymer_rows={polymer_rows_path}")


if __name__ == "__main__":
    main()
