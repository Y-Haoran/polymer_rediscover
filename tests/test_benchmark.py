from pathlib import Path
import unittest

from polymer_rediscover.benchmark import load_candidates, load_ranking_examples, validate_examples
from polymer_rediscover.evaluate import evaluate_benchmark


class BenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.candidates_path = root / "data" / "schema" / "candidate_polymers_example.tsv"
        self.benchmark_path = (
            root / "data" / "benchmark" / "example_oral_polymer_ranking.jsonl"
        )

    def test_load_and_validate_toy_benchmark(self) -> None:
        candidates = load_candidates(self.candidates_path)
        examples = load_ranking_examples(self.benchmark_path)
        validate_examples(examples, candidates)
        self.assertEqual(len(candidates), 4)
        self.assertEqual(len(examples), 3)

    def test_hash_backbone_scores_toy_benchmark(self) -> None:
        result = evaluate_benchmark(
            benchmark_path=self.benchmark_path,
            candidate_path=self.candidates_path,
            backbone_name="hash",
            ks=(1, 3),
            model_name="unused",
            device="cpu",
        )
        self.assertEqual(result["num_examples"], 3)
        self.assertGreaterEqual(result["mrr"], 0.99)
        self.assertEqual(result["metrics"]["recall@1"], 1.0)


if __name__ == "__main__":
    unittest.main()
