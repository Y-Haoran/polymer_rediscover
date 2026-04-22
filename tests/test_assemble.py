from pathlib import Path
import tempfile
import unittest

from polymer_rediscover.assemble import build_benchmark_records
from polymer_rediscover.tabular import write_tsv


class AssembleTests(unittest.TestCase):
    def test_build_benchmark_records(self) -> None:
        root = Path(__file__).resolve().parents[1]
        candidates = root / "data" / "schema" / "candidate_polymers_seed.tsv"
        synonyms = root / "data" / "schema" / "polymer_synonyms_seed.tsv"

        fda_polymer_rows = [
            {
                "canonical_polymer_id": "povidone",
                "route_normalized": "oral",
                "dosage_form_category": "tablet",
            },
            {
                "canonical_polymer_id": "hypromellose",
                "route_normalized": "oral",
                "dosage_form_category": "tablet",
            },
        ]
        dailymed_products = [
            {
                "setid": "set-1",
                "title": "Demo",
                "product_name": "Demo Product",
                "route_normalized": "oral",
                "dosage_form_category": "tablet",
                "source_file": "demo.xml",
            }
        ]
        dailymed_ingredients = [
            {
                "setid": "set-1",
                "ingredient_role": "active",
                "ingredient_name": "Demo API",
            },
            {
                "setid": "set-1",
                "ingredient_role": "inactive",
                "ingredient_name": "POVIDONE",
            },
        ]
        benchmark_rows, resolved_rows = build_benchmark_records(
            fda_polymer_rows=fda_polymer_rows,
            dailymed_products=dailymed_products,
            dailymed_ingredients=dailymed_ingredients,
            candidate_path=candidates,
            synonyms_path=synonyms,
        )
        self.assertEqual(len(benchmark_rows), 1)
        self.assertEqual(benchmark_rows[0]["positive_candidate_ids"], ["povidone"])
        self.assertEqual(len(resolved_rows), 1)


if __name__ == "__main__":
    unittest.main()
