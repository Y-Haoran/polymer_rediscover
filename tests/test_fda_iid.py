from pathlib import Path
import tempfile
import unittest

from polymer_rediscover.fda_iid import normalize_release_to_tables, normalize_iid_row, resolve_current_download_url
from polymer_rediscover.tabular import read_delimited_rows


class FdaIidTests(unittest.TestCase):
    def test_resolve_current_download_url(self) -> None:
        html = """
        <html><body>
        <a href="/media/191970/download?attachment">Inactive Ingredients Database Download File</a>
        </body></html>
        """
        self.assertEqual(
            resolve_current_download_url(html),
            "https://www.fda.gov/media/191970/download?attachment",
        )

    def test_normalize_iid_row_derives_context_fields(self) -> None:
        row = normalize_iid_row(
            {
                "INGREDIENT_NAME": "POVIDONE",
                "ROUTE": "ORAL",
                "DOSAGE_FORM": "TABLET, CHEWABLE",
            }
        )
        self.assertEqual(row["route_normalized"], "oral")
        self.assertEqual(row["dosage_form_category"], "tablet")

    def test_normalize_release_writes_polymer_subset(self) -> None:
        root = Path(__file__).resolve().parents[1]
        candidates = root / "data" / "schema" / "candidate_polymers_seed.tsv"
        synonyms = root / "data" / "schema" / "polymer_synonyms_seed.tsv"
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            csv_path = tmp_dir / "IIR_OCOMM.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "INGREDIENT_NAME,ROUTE,DOSAGE_FORM,CAS_NUMBER,UNII,POTENCY_AMOUNT,POTENCY_UNIT,MAXIMUM_DAILY_EXPOSURE,MAXIMUM_DAILY_EXPOSURE_UNIT,RECORD_UPDATED",
                        "POVIDONE,ORAL,TABLET,,,5,mg,,,",
                        "GLYCERIN,TOPICAL,LOTION,,,11,%w/w,,,",
                    ]
                ),
                encoding="utf-8",
            )
            processed_dir = tmp_dir / "processed"
            _, polymer_path = normalize_release_to_tables(
                csv_path=csv_path,
                processed_dir=processed_dir,
                synonyms_path=synonyms,
                candidate_table_path=candidates,
            )
            rows = read_delimited_rows(polymer_path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["canonical_polymer_id"], "povidone")


if __name__ == "__main__":
    unittest.main()
