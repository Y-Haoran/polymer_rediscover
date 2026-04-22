"""Assemble Stage 4 ranking benchmarks from normalized FDA IID and DailyMed tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import load_candidates
from .normalization import SynonymIndex, is_oral_solid_context
from .tabular import read_delimited_rows, write_tsv

DEFAULT_FDA_POLYMER_ROWS = Path("data/fda_iid/processed/iid_polymer_records.tsv")
DEFAULT_DAILYMED_PRODUCTS = Path("data/dailymed/processed/dailymed_products.tsv")
DEFAULT_DAILYMED_INGREDIENTS = Path("data/dailymed/processed/dailymed_ingredients.tsv")
DEFAULT_CANDIDATES = Path("data/schema/candidate_polymers_seed.tsv")
DEFAULT_SYNONYMS = Path("data/schema/polymer_synonyms_seed.tsv")
DEFAULT_BENCHMARK = Path("data/benchmark/oral_polymer_ranking.jsonl")
DEFAULT_RESOLVED = Path("data/benchmark/resolved_polymer_product_records.tsv")


def build_candidate_contexts(fda_polymer_rows: list[dict[str, str]]) -> dict[tuple[str, str], set[str]]:
    contexts: dict[tuple[str, str], set[str]] = {}
    for row in fda_polymer_rows:
        key = (row.get("route_normalized", ""), row.get("dosage_form_category", ""))
        contexts.setdefault(key, set()).add(row["canonical_polymer_id"])
    return contexts


def build_benchmark_records(
    fda_polymer_rows: list[dict[str, str]],
    dailymed_products: list[dict[str, str]],
    dailymed_ingredients: list[dict[str, str]],
    candidate_path: Path,
    synonyms_path: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    candidates = load_candidates(candidate_path)
    candidate_contexts = build_candidate_contexts(fda_polymer_rows)
    synonym_index = SynonymIndex.from_tsv(synonyms_path)

    products_by_setid = {row["setid"]: row for row in dailymed_products}
    ingredients_by_setid: dict[str, list[dict[str, str]]] = {}
    for ingredient in dailymed_ingredients:
        ingredients_by_setid.setdefault(ingredient["setid"], []).append(ingredient)

    benchmark_rows: list[dict[str, object]] = []
    resolved_rows: list[dict[str, object]] = []

    for setid, product in sorted(products_by_setid.items()):
        route = product.get("route_normalized", "")
        dosage_category = product.get("dosage_form_category", "")
        if not is_oral_solid_context(route, dosage_category):
            continue

        product_ingredients = ingredients_by_setid.get(setid, [])
        active_ingredients = sorted(
            {
                ingredient["ingredient_name"]
                for ingredient in product_ingredients
                if ingredient.get("ingredient_role") == "active" and ingredient.get("ingredient_name")
            }
        )
        inactive_polymer_ids = sorted(
            {
                canonical_id
                for ingredient in product_ingredients
                if ingredient.get("ingredient_role") == "inactive"
                for canonical_id in [synonym_index.resolve(ingredient.get("ingredient_name", ""))]
                if canonical_id and canonical_id in candidates
            }
        )
        if not active_ingredients or not inactive_polymer_ids:
            continue

        candidate_ids = sorted(candidate_contexts.get((route, dosage_category), set()))
        if not candidate_ids:
            continue

        for polymer_id in inactive_polymer_ids:
            resolved_rows.append(
                {
                    "setid": setid,
                    "title": product.get("title", ""),
                    "product_name": product.get("product_name", ""),
                    "api_names": active_ingredients,
                    "route": route,
                    "dosage_form_category": dosage_category,
                    "canonical_polymer_id": polymer_id,
                    "canonical_polymer_name": candidates[polymer_id].canonical_name,
                }
            )

        benchmark_rows.append(
            {
                "example_id": setid,
                "api_name": "; ".join(active_ingredients),
                "route": route,
                "dosage_form": dosage_category,
                "query_text": (
                    f"api {' ; '.join(active_ingredients)} "
                    f"route {route} dosage form {dosage_category}"
                ),
                "candidate_ids": candidate_ids,
                "positive_candidate_ids": inactive_polymer_ids,
                "metadata": {
                    "title": product.get("title", ""),
                    "product_name": product.get("product_name", ""),
                    "source_file": product.get("source_file", ""),
                },
            }
        )

    return benchmark_rows, resolved_rows


def write_benchmark_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row))
            handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the oral polymer ranking benchmark.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser("build-benchmark", help="Assemble benchmark JSONL.")
    build_parser_.add_argument("--fda-polymer-rows", default=str(DEFAULT_FDA_POLYMER_ROWS))
    build_parser_.add_argument("--dailymed-products", default=str(DEFAULT_DAILYMED_PRODUCTS))
    build_parser_.add_argument("--dailymed-ingredients", default=str(DEFAULT_DAILYMED_INGREDIENTS))
    build_parser_.add_argument("--candidates", default=str(DEFAULT_CANDIDATES))
    build_parser_.add_argument("--synonyms", default=str(DEFAULT_SYNONYMS))
    build_parser_.add_argument("--benchmark-out", default=str(DEFAULT_BENCHMARK))
    build_parser_.add_argument("--resolved-out", default=str(DEFAULT_RESOLVED))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    fda_polymer_rows = read_delimited_rows(Path(args.fda_polymer_rows))
    dailymed_products = read_delimited_rows(Path(args.dailymed_products))
    dailymed_ingredients = read_delimited_rows(Path(args.dailymed_ingredients))

    benchmark_rows, resolved_rows = build_benchmark_records(
        fda_polymer_rows=fda_polymer_rows,
        dailymed_products=dailymed_products,
        dailymed_ingredients=dailymed_ingredients,
        candidate_path=Path(args.candidates),
        synonyms_path=Path(args.synonyms),
    )
    write_benchmark_jsonl(Path(args.benchmark_out), benchmark_rows)
    write_tsv(
        Path(args.resolved_out),
        resolved_rows,
        [
            "setid",
            "title",
            "product_name",
            "api_names",
            "route",
            "dosage_form_category",
            "canonical_polymer_id",
            "canonical_polymer_name",
        ],
    )
    print(f"benchmark_rows={len(benchmark_rows)}")
    print(f"benchmark_out={args.benchmark_out}")
    print(f"resolved_out={args.resolved_out}")


if __name__ == "__main__":
    main()
