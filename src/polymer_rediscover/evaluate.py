"""Evaluate frozen backbones on a polymer ranking benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backbones import create_backbone, dot_product
from .benchmark import load_candidates, load_ranking_examples, validate_examples


def reciprocal_rank(ranked_ids: list[str], positive_ids: frozenset[str]) -> float:
    for index, candidate_id in enumerate(ranked_ids, start=1):
        if candidate_id in positive_ids:
            return 1.0 / index
    return 0.0


def recall_at_k(ranked_ids: list[str], positive_ids: frozenset[str], k: int) -> float:
    top_ids = set(ranked_ids[:k])
    if not positive_ids:
        return 0.0
    return len(top_ids & positive_ids) / len(positive_ids)


def evaluate_benchmark(
    benchmark_path: str | Path,
    candidate_path: str | Path,
    backbone_name: str,
    ks: tuple[int, ...],
    model_name: str,
    device: str,
) -> dict[str, object]:
    candidates = load_candidates(candidate_path)
    examples = load_ranking_examples(benchmark_path)
    validate_examples(examples, candidates)

    backbone = create_backbone(backbone_name, model_name=model_name, device=device)
    candidate_texts = [candidates[candidate_id].candidate_text for candidate_id in candidates]
    candidate_vectors = backbone.encode_texts(candidate_texts)
    candidate_vector_map = {
        candidate_id: candidate_vectors[index]
        for index, candidate_id in enumerate(candidates)
    }

    per_example: list[dict[str, object]] = []
    mrr_values: list[float] = []
    recall_values = {k: [] for k in ks}

    for example in examples:
        query_vector = backbone.encode_texts([example.query_text])[0]
        ranked = sorted(
            example.candidate_ids,
            key=lambda candidate_id: dot_product(
                query_vector, candidate_vector_map[candidate_id]
            ),
            reverse=True,
        )
        rr = reciprocal_rank(ranked, example.positive_candidate_ids)
        mrr_values.append(rr)
        per_result = {
            "example_id": example.example_id,
            "top_predictions": ranked[: max(ks)],
            "positive_candidate_ids": sorted(example.positive_candidate_ids),
            "reciprocal_rank": rr,
        }
        for k in ks:
            recall = recall_at_k(ranked, example.positive_candidate_ids, k)
            per_result[f"recall@{k}"] = recall
            recall_values[k].append(recall)
        per_example.append(per_result)

    summary = {
        "backbone": backbone_name,
        "num_examples": len(examples),
        "mrr": sum(mrr_values) / len(mrr_values) if mrr_values else 0.0,
        "metrics": {
            f"recall@{k}": (
                sum(recall_values[k]) / len(recall_values[k]) if recall_values[k] else 0.0
            )
            for k in ks
        },
        "per_example": per_example,
    }
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate a frozen backbone on a polymer excipient ranking benchmark."
    )
    parser.add_argument("--benchmark", required=True, help="Path to JSONL benchmark file.")
    parser.add_argument("--candidates", required=True, help="Path to candidate TSV or CSV file.")
    parser.add_argument(
        "--backbone",
        choices=("hash", "polytao"),
        default="hash",
        help="Frozen backbone used to embed query and candidate text.",
    )
    parser.add_argument(
        "--top-k",
        nargs="+",
        type=int,
        default=[1, 3, 5],
        help="Top-k values used for recall metrics.",
    )
    parser.add_argument(
        "--model-name",
        default="hkqiu/PolymerGenerationPretrainedModel",
        help="Model identifier used when backbone=polytao.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Torch device used when backbone=polytao.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path for writing the full evaluation summary as JSON.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    ks = tuple(sorted(set(args.top_k)))
    summary = evaluate_benchmark(
        benchmark_path=args.benchmark,
        candidate_path=args.candidates,
        backbone_name=args.backbone,
        ks=ks,
        model_name=args.model_name,
        device=args.device,
    )
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
