"""Frozen text backbones for ranking experiments."""

from __future__ import annotations

import hashlib
import math
from typing import Protocol

from .normalization import normalize_text


Vector = list[float]


class TextBackbone(Protocol):
    def encode_texts(self, texts: list[str]) -> list[Vector]:
        """Return one L2-normalized embedding vector per input text."""


def dot_product(left: Vector, right: Vector) -> float:
    return sum(l * r for l, r in zip(left, right, strict=True))


def l2_normalize(values: Vector) -> Vector:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        return values
    return [value / norm for value in values]


class HashTextBackbone:
    """Deterministic lexical baseline for scaffold validation."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def encode_texts(self, texts: list[str]) -> list[Vector]:
        return [self._encode_one(text) for text in texts]

    def _encode_one(self, text: str) -> Vector:
        vector = [0.0] * self.dim
        tokens = normalize_text(text).split()
        if not tokens:
            tokens = ["empty"]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            sign = -1.0 if digest[4] % 2 else 1.0
            vector[index] += sign
        return l2_normalize(vector)


class PolyTAOBackbone:
    """Optional frozen encoder view over the public PolyTAO checkpoint."""

    def __init__(
        self,
        model_name: str = "hkqiu/PolymerGenerationPretrainedModel",
        device: str = "cpu",
        max_length: int = 256,
    ) -> None:
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "PolyTAOBackbone requires torch and transformers. "
                'Install them with: pip install -e ".[ml]"'
            ) from exc

        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self._model.eval()
        self._model.to(device)
        self._device = device
        self._max_length = max_length

    def encode_texts(self, texts: list[str]) -> list[Vector]:
        vectors: list[Vector] = []
        torch = self._torch
        encoder = self._model.get_encoder()
        with torch.no_grad():
            for start in range(0, len(texts), 8):
                batch_texts = texts[start : start + 8]
                tokenized = self._tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=self._max_length,
                    return_tensors="pt",
                )
                tokenized = {
                    key: value.to(self._device)
                    for key, value in tokenized.items()
                }
                outputs = encoder(
                    input_ids=tokenized["input_ids"],
                    attention_mask=tokenized["attention_mask"],
                )
                hidden = outputs.last_hidden_state
                mask = tokenized["attention_mask"].unsqueeze(-1)
                pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
                for row in pooled.detach().cpu().tolist():
                    vectors.append(l2_normalize([float(value) for value in row]))
        return vectors


def create_backbone(
    backbone_name: str,
    model_name: str = "hkqiu/PolymerGenerationPretrainedModel",
    device: str = "cpu",
) -> TextBackbone:
    if backbone_name == "hash":
        return HashTextBackbone()
    if backbone_name == "polytao":
        return PolyTAOBackbone(model_name=model_name, device=device)
    raise ValueError(f"unknown backbone: {backbone_name}")
