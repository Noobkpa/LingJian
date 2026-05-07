"""长文本按字分块，多块 logits 逐维取 max 聚合。"""
from __future__ import annotations

from typing import Iterable, List


def chunk_by_chars(text: str, max_chars: int = 512, overlap: int = 0) -> List[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    text = text.strip()
    if not text:
        return []
    if overlap >= max_chars:
        overlap = max(0, max_chars // 8)
    step = max_chars - overlap
    chunks: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        chunks.append(text[i : i + max_chars])
        i += step
    return chunks


def aggregate_logits_max(logits_list: Iterable["torch.Tensor"]) -> "torch.Tensor":
    import torch

    stacked = torch.stack(list(logits_list), dim=0)
    return stacked.max(dim=0).values
