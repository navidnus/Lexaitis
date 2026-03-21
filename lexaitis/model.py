"""
Core n-gram language model for Lexaitis.

An NgramModel learns token transition frequencies from a source text and can
generate new text one token at a time, conditioned on a fixed-length prior
context.  Temperature scaling controls sampling sharpness; optional backoff
lets the model fall back to shorter contexts when an exact n-gram is unseen.
"""

from __future__ import annotations

import re
import random
from collections import Counter, defaultdict
from typing import Generator, Iterator

import numpy as np


# ---------------------------------------------------------------------------
# Tokenisation
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\S+")


def tokenize(text: str) -> list[str]:
    """Split *text* into whitespace-delimited tokens, lowercased.

    Punctuation stays attached to its neighbouring word (e.g. "said," or
    "end.") so students see tokens that look like the source text, making the
    model's behaviour more transparent.
    """
    return _TOKEN_RE.findall(text.lower())


# ---------------------------------------------------------------------------
# Table construction
# ---------------------------------------------------------------------------

def build_tables(tokens: list[str], max_n: int) -> dict[int, dict[tuple, Counter]]:
    """Build frequency tables for all n-gram orders from 1 to *max_n*.

    Returns a dict  order → {context_tuple → Counter(next_token → count)}.
    For order 1 (unigram), the context tuple is always the empty tuple ().
    """
    tables: dict[int, dict[tuple, Counter]] = {}
    for n in range(1, max_n + 1):
        table: dict[tuple, Counter] = defaultdict(Counter)
        for i in range(len(tokens) - n + 1):
            context = tuple(tokens[i : i + n - 1])   # n-1 preceding tokens
            next_tok = tokens[i + n - 1]
            table[context][next_tok] += 1
        tables[n] = dict(table)
    return tables


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def _apply_temperature(counts: Counter, temperature: float) -> tuple[list[str], np.ndarray]:
    """Convert a Counter of counts to a probability array scaled by *temperature*.

    Returns (tokens_list, probs_array) where probs sums to 1.
    Very low temperature (< 0.05) is treated as greedy (argmax).
    """
    tokens = list(counts.keys())
    raw = np.array([counts[t] for t in tokens], dtype=float)

    if temperature < 0.05:
        probs = np.zeros(len(tokens))
        probs[int(np.argmax(raw))] = 1.0
        return tokens, probs

    log_counts = np.log(raw)
    scaled = log_counts / temperature
    shifted = scaled - scaled.max()          # numerical stability
    exp_vals = np.exp(shifted)
    probs = exp_vals / exp_vals.sum()
    return tokens, probs


# ---------------------------------------------------------------------------
# NgramModel
# ---------------------------------------------------------------------------

class NgramModel:
    """A simple n-gram language model backed by frequency tables.

    Parameters
    ----------
    text:
        Raw source text from which frequencies are learned.
    max_n:
        Highest n-gram order to pre-compute (default 7).  The model can
        use any order from 1 to max_n at generation time.
    token_limit:
        Maximum number of tokens to use from the source (guards against
        very large texts slowing the UI).
    """

    MAX_N_CAP = 7

    def __init__(self, text: str, max_n: int = 7, token_limit: int = 30_000) -> None:
        self.max_n = min(max_n, self.MAX_N_CAP)
        raw_tokens = tokenize(text)
        self.tokens = raw_tokens[:token_limit]
        self.vocab: list[str] = sorted(set(self.tokens))
        self.tables = build_tables(self.tokens, self.max_n)

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def _trim_context(self, context: tuple[str, ...], n: int) -> tuple[str, ...]:
        """Return the last n-1 tokens of *context* for order-n prediction."""
        want = n - 1
        return context[-want:] if want > 0 else ()

    # ------------------------------------------------------------------
    # Candidate retrieval (with optional backoff)
    # ------------------------------------------------------------------

    def get_candidates(
        self,
        context: tuple[str, ...],
        n: int,
        use_backoff: bool = True,
    ) -> tuple[Counter, int]:
        """Return (candidates Counter, actual_order_used).

        If *use_backoff* is True and the exact context is not found, the model
        progressively shortens the context until a match is found, down to a
        unigram distribution (order 1, empty context).

        If *use_backoff* is False and the context is not found, returns an
        empty Counter and order 0 to signal a generation failure.
        """
        orders_to_try = range(n, 0, -1) if use_backoff else [n]

        for order in orders_to_try:
            ctx = self._trim_context(context, order)
            table = self.tables.get(order, {})
            candidates = table.get(ctx)
            if candidates:
                return candidates, order

        return Counter(), 0

    # ------------------------------------------------------------------
    # Single-step prediction
    # ------------------------------------------------------------------

    def sample_next(
        self,
        context: tuple[str, ...],
        n: int,
        temperature: float = 1.0,
        use_backoff: bool = True,
    ) -> tuple[str | None, dict[str, float], dict[str, int], int]:
        """Sample one token given *context*.

        Returns
        -------
        next_token:
            The sampled token, or None if no candidates were found.
        prob_dict:
            Mapping from candidate token to its probability (after temperature
            scaling).  Sorted descending by probability.
        raw_counts:
            Mapping from candidate token to its raw frequency count in the
            training text.  Used for the temperature-effect visualisation.
        actual_order:
            The n-gram order that was actually used (may be < n if backoff
            fired, or 0 if no candidates were found at all).
        """
        candidates, actual_order = self.get_candidates(context, n, use_backoff)

        if not candidates:
            return None, {}, {}, 0

        tokens_list, probs = _apply_temperature(candidates, temperature)
        sampled_idx = int(np.random.choice(len(tokens_list), p=probs))
        next_token = tokens_list[sampled_idx]

        prob_dict = {t: float(p) for t, p in zip(tokens_list, probs)}
        prob_dict = dict(
            sorted(prob_dict.items(), key=lambda kv: kv[1], reverse=True)
        )
        raw_counts = dict(candidates)
        return next_token, prob_dict, raw_counts, actual_order

    # ------------------------------------------------------------------
    # Multi-step generation (generator)
    # ------------------------------------------------------------------

    def generate(
        self,
        start_tokens: list[str],
        n: int,
        length: int,
        temperature: float = 1.0,
        use_backoff: bool = True,
    ) -> Generator[tuple[str, dict[str, float], dict[str, int], int], None, None]:
        """Yield *(token, prob_dict, raw_counts, actual_order)* for each generated step.

        Parameters
        ----------
        start_tokens:
            Seed tokens providing the initial context.
        n:
            N-gram order to use.
        length:
            Number of tokens to generate.
        temperature:
            Sampling temperature.
        use_backoff:
            Whether to allow backoff to shorter contexts.
        """
        generated = list(start_tokens)

        for _ in range(length):
            context = tuple(generated[-(n - 1) :]) if n > 1 else ()
            next_token, prob_dict, raw_counts, actual_order = self.sample_next(
                context, n, temperature, use_backoff
            )
            if next_token is None:
                return
            generated.append(next_token)
            yield next_token, prob_dict, raw_counts, actual_order

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def parse_start_phrase(self, phrase: str) -> list[str]:
        """Tokenize *phrase* the same way the model tokenizes source text."""
        return tokenize(phrase)

    def random_start_token(self, rng: random.Random | None = None) -> str:
        """Return a random token from the source vocabulary."""
        r = rng or random
        return r.choice(self.tokens)

    def get_chart_probs(
        self,
        tokens: list[str],
        generation_n: int,
        temperature: float = 1.0,
    ) -> tuple[dict[str, float], int, int]:
        """Return the probability distribution used for the chart display.

        For *generation_n* >= 3 the chart always shows the **bigram**
        distribution (conditioned on the single token that immediately
        preceded the last generated word).  This guarantees the chart has
        multiple candidates with varying probabilities, making the sampling
        step visible and meaningful to students.

        For *generation_n* <= 2 the chart shows the actual distribution that
        was used for generation.

        Returns
        -------
        prob_dict : dict[str, float]
            Token → probability, sorted descending.
        display_order : int
            The n-gram order whose table was actually consulted.
        display_n : int
            The intended display order (2 for n>=3, else generation_n).
        """
        display_n = 2 if generation_n >= 3 else generation_n

        # Context for the display distribution is the (display_n - 1) tokens
        # that preceded the most recently generated token.
        # tokens[-1] is the last generated word; we want the context before it.
        context_len = display_n - 1
        if context_len == 0:
            context: tuple[str, ...] = ()
        elif len(tokens) > 1:
            context = tuple(tokens[-(context_len + 1) : -1])
        else:
            context = ()

        candidates, display_order = self.get_candidates(
            context, display_n, use_backoff=True
        )

        if not candidates:
            return {}, 0, display_n

        tokens_list, probs = _apply_temperature(candidates, temperature)
        prob_dict = {t: float(p) for t, p in zip(tokens_list, probs)}
        prob_dict = dict(
            sorted(prob_dict.items(), key=lambda kv: kv[1], reverse=True)
        )
        return prob_dict, display_order, display_n

    def __repr__(self) -> str:
        return (
            f"NgramModel(vocab={len(self.vocab)}, "
            f"tokens={len(self.tokens)}, max_n={self.max_n})"
        )
