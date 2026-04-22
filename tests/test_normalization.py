from pathlib import Path
import unittest

from polymer_rediscover.normalization import SynonymIndex, normalize_text


class NormalizationTests(unittest.TestCase):
    def test_normalize_text_collapses_case_and_punctuation(self) -> None:
        self.assertEqual(normalize_text(" Povidone, USP "), "povidone usp")

    def test_synonym_index_resolves_example_entries(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "schema"
            / "polymer_synonyms_example.tsv"
        )
        index = SynonymIndex.from_tsv(path)
        self.assertEqual(index.resolve("Polyvinylpyrrolidone"), "pvp")
        self.assertEqual(
            index.canonical_name_for("hpmcas"),
            "Hydroxypropyl methylcellulose acetate succinate",
        )


if __name__ == "__main__":
    unittest.main()
