"""Deterministic stub backend for unit tests.

No torch, no model weights required.
StubModel produces reproducible token sequences so tests can assert on output shape.
"""
from __future__ import annotations

import hashlib


class StubTokenizer:
    """Minimal tokenizer that maps characters to ordinals and back."""

    def __init__(self, vocab_size: int = 256) -> None:
        self.vocab_size = vocab_size

    def encode(self, text: str) -> list[int]:
        return [ord(c) % self.vocab_size for c in text]

    def decode(self, ids: list[int]) -> str:
        return "".join(chr(i % 128) for i in ids)


class StubModel:
    """
    Deterministic pseudo-model.

    generate() returns *max_new_tokens* token IDs derived from a hash
    of the prompt, so results are reproducible and testable.
    """

    def __init__(self, vocab_size: int = 256) -> None:
        self.vocab_size = vocab_size

    def generate(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        seed = hashlib.sha256(bytes(prompt_ids)).digest()
        tokens: list[int] = []
        state = int.from_bytes(seed[:8], "little")
        for _ in range(max_new_tokens):
            state = (state * 6364136223846793005 + 1442695040888963407) & 0xFFFF_FFFF_FFFF_FFFF
            tokens.append(state % self.vocab_size)
        return tokens

    def eval(self) -> None:
        pass  # no-op for interface compatibility
