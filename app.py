"""
Lexaitis — Interactive N-gram Language Model Explorer
Streamlit application entry point.
"""

from __future__ import annotations

import random
import textwrap

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from lexaitis.model import NgramModel
from lexaitis.texts.library import (
    CUSTOM_LABEL,
    all_display_names,
    description_for,
    load_text,
)

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Lexaitis",
    page_icon="🔤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Colour palette (used in HTML spans and Plotly)
# ──────────────────────────────────────────────────────────────────────────────

CONTEXT_BG = "#ffd166"      # amber highlight for context window
CHOSEN_BAR = "#ef476f"      # red-pink for selected token bar
DEFAULT_BAR = "#118ab2"     # steel blue for candidate bars
BACKOFF_COLOR = "#ff6b35"   # orange for backoff annotation

# ──────────────────────────────────────────────────────────────────────────────
# Cached model builder
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Building n-gram tables…")
def get_model(text_keys: tuple[str, ...], custom_text: str, max_n: int) -> NgramModel:
    """Build and cache an NgramModel from one or more source texts.

    All selected texts are concatenated before tokenisation.  The token limit
    is applied to the combined corpus so that adding more texts genuinely
    increases vocabulary and n-gram coverage.
    """
    parts: list[str] = []
    for key in text_keys:
        if key == CUSTOM_LABEL:
            if custom_text.strip():
                parts.append(custom_text)
        else:
            parts.append(load_text(key))

    source = "\n\n".join(parts) if parts else ""
    # Per-text limit of 30k × number of texts, capped at 150k tokens
    combined_limit = min(30_000 * max(len(text_keys), 1), 150_000)
    return NgramModel(source, max_n=max_n, token_limit=combined_limit)


# ──────────────────────────────────────────────────────────────────────────────
# Session-state helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ss_key(prefix: str, key: str) -> str:
    return f"{prefix}__{key}"


def init_gen_state(prefix: str, start_tokens: list[str]) -> None:
    """Initialise (or re-initialise) generation state for a panel."""
    st.session_state[_ss_key(prefix, "tokens")] = list(start_tokens)
    st.session_state[_ss_key(prefix, "prob_dicts")] = []   # list of prob_dict per step
    st.session_state[_ss_key(prefix, "orders")] = []       # actual order used per step
    st.session_state[_ss_key(prefix, "done")] = False


def get_gen_state(prefix: str) -> tuple[list, list, list, bool]:
    tokens = st.session_state.get(_ss_key(prefix, "tokens"), [])
    prob_dicts = st.session_state.get(_ss_key(prefix, "prob_dicts"), [])
    orders = st.session_state.get(_ss_key(prefix, "orders"), [])
    done = st.session_state.get(_ss_key(prefix, "done"), False)
    return tokens, prob_dicts, orders, done


def append_token(prefix: str, token: str, prob_dict: dict, order: int) -> None:
    st.session_state[_ss_key(prefix, "tokens")].append(token)
    st.session_state[_ss_key(prefix, "prob_dicts")].append(prob_dict)
    st.session_state[_ss_key(prefix, "orders")].append(order)


def set_done(prefix: str, done: bool) -> None:
    st.session_state[_ss_key(prefix, "done")] = done


# ──────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ──────────────────────────────────────────────────────────────────────────────

def render_generated_text(
    tokens: list[str],
    start_len: int,
    n: int,
) -> str:
    """Build an HTML string with the current context window highlighted.

    *start_len* is the number of seed tokens (not highlighted as generated).
    *n* controls the size of the context window = n-1 tokens.
    """
    if not tokens:
        return "<em style='color:grey'>No text generated yet.</em>"

    context_size = max(n - 1, 1)
    context_start = max(len(tokens) - context_size, start_len)

    parts: list[str] = []
    for i, tok in enumerate(tokens):
        escaped = tok.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if i < start_len:
            # seed tokens — shown in grey italics
            parts.append(f"<span style='color:#888;font-style:italic'>{escaped}</span>")
        elif context_start <= i < len(tokens) - 1:
            # context window (not the very last token)
            parts.append(
                f"<span style='background-color:{CONTEXT_BG};border-radius:3px;"
                f"padding:1px 3px'>{escaped}</span>"
            )
        elif i == len(tokens) - 1 and i >= start_len:
            # most recently generated token — bold
            parts.append(
                f"<span style='background-color:{CHOSEN_BAR};color:white;"
                f"border-radius:3px;padding:1px 4px;font-weight:bold'>{escaped}</span>"
            )
        else:
            parts.append(f"<span>{escaped}</span>")

    return " ".join(parts)


def render_prob_chart(
    prob_dict: dict[str, float],
    chosen_token: str,
    actual_order: int,
    requested_n: int,
    top_k: int = 15,
) -> go.Figure:
    """Return a horizontal Plotly bar chart of top-k candidate probabilities."""
    items = sorted(prob_dict.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    if not items:
        fig = go.Figure()
        fig.add_annotation(text="No candidates found.", x=0.5, y=0.5, showarrow=False)
        return fig

    labels = [t for t, _ in items]
    probs = [p for _, p in items]
    colors = [CHOSEN_BAR if t == chosen_token else DEFAULT_BAR for t in labels]

    fig = go.Figure(
        go.Bar(
            x=probs,
            y=labels,
            orientation="h",
            marker_color=colors,
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )

    if actual_order < requested_n and actual_order > 0:
        backoff_note = f"  ↓ backed off to {actual_order}-gram"
    elif actual_order == 0:
        backoff_note = "  ✗ no candidates found"
    else:
        backoff_note = ""

    title = (
        f"Next-token probabilities  ·  context = {actual_order}-gram"
        + backoff_note
    )

    fig.update_layout(
        title={"text": title, "x": 0, "font": {"size": 13}},
        xaxis_title="Probability",
        yaxis={"autorange": "reversed", "tickfont": {"size": 12}},
        height=max(280, 28 * len(items)),
        margin={"l": 10, "r": 10, "t": 50, "b": 30},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def context_info_box(tokens: list[str], n: int, start_len: int) -> str:
    """Return an HTML snippet describing the current context."""
    ctx_size = n - 1
    if ctx_size == 0:
        ctx_display = "(none — unigram model)"
    else:
        ctx_tokens = tokens[-ctx_size:] if len(tokens) >= ctx_size else tokens
        ctx_display = " &nbsp;›&nbsp; ".join(
            f"<code>{t}</code>" for t in ctx_tokens
        )
    generated_count = max(len(tokens) - start_len, 0)
    return (
        f"<small>"
        f"<b>Context window (n={n}, last {ctx_size} token{'s' if ctx_size!=1 else ''}):</b> "
        f"{ctx_display} &nbsp;&nbsp;"
        f"<b>Tokens generated:</b> {generated_count}"
        f"</small>"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Single-panel generation UI  (reused in both Generate tab and Compare tab)
# ──────────────────────────────────────────────────────────────────────────────

def generation_panel(
    prefix: str,
    model: NgramModel,
    n: int,
    temperature: float,
    use_backoff: bool,
    gen_length: int,
    start_phrase: str,
    show_chart: bool = True,
) -> None:
    """Render the full generation panel (text + controls + chart) inside a container."""

    # Parse start phrase into seed tokens
    seed_tokens = model.parse_start_phrase(start_phrase) if start_phrase.strip() else []
    if not seed_tokens:
        seed_tokens = [model.random_start_token()]

    # Initialise state on first visit or after reset
    state_key = _ss_key(prefix, "tokens")
    if state_key not in st.session_state:
        init_gen_state(prefix, seed_tokens)

    tokens, prob_dicts, orders, done = get_gen_state(prefix)
    start_len = len(tokens) - len(prob_dicts)  # number of seed tokens

    # ── Buttons ──────────────────────────────────────────────────────────────
    col_step, col_run, col_reset, col_spacer = st.columns([1, 1, 1, 5])

    with col_step:
        step_clicked = st.button(
            "Step ▶",
            key=f"{prefix}_step",
            disabled=done or (len(tokens) - start_len >= gen_length),
            help="Generate one token",
        )
    with col_run:
        run_clicked = st.button(
            "Run all ⏩",
            key=f"{prefix}_run",
            disabled=done or (len(tokens) - start_len >= gen_length),
            help="Generate all remaining tokens",
        )
    with col_reset:
        reset_clicked = st.button(
            "Reset ↺",
            key=f"{prefix}_reset",
            help="Clear generated text and start over",
        )

    # ── Handle button actions ─────────────────────────────────────────────────
    if reset_clicked:
        init_gen_state(prefix, seed_tokens)
        st.rerun()

    if step_clicked and not done:
        remaining = gen_length - (len(tokens) - start_len)
        if remaining > 0:
            ctx = tuple(tokens[-(n - 1) :]) if n > 1 else ()
            tok, prob_dict, actual_order = model.sample_next(
                ctx, n, temperature, use_backoff
            )
            if tok is None:
                set_done(prefix, True)
            else:
                append_token(prefix, tok, prob_dict, actual_order)
            remaining -= 1
            if remaining <= 0:
                set_done(prefix, True)
        st.rerun()

    if run_clicked and not done:
        remaining = gen_length - (len(tokens) - start_len)
        for tok, prob_dict, actual_order in model.generate(
            tokens, n, remaining, temperature, use_backoff
        ):
            append_token(prefix, tok, prob_dict, actual_order)
        set_done(prefix, True)
        st.rerun()

    # Reload state after possible mutations
    tokens, prob_dicts, orders, done = get_gen_state(prefix)
    start_len = len(tokens) - len(prob_dicts)

    # ── Generated text display ────────────────────────────────────────────────
    html_text = render_generated_text(tokens, start_len, n)
    st.markdown(
        f"<div style='background:#f8f9fa;border-radius:8px;padding:14px 18px;"
        f"font-size:1.05rem;line-height:1.8;min-height:80px'>{html_text}</div>",
        unsafe_allow_html=True,
    )

    # Context info
    if tokens:
        st.markdown(
            context_info_box(tokens, n, start_len),
            unsafe_allow_html=True,
        )
        if done and (len(tokens) - start_len) >= gen_length:
            st.success("Generation complete.")
        elif done:
            st.warning("Generation stopped: no candidates found for current context.")

    # ── Probability chart (last step) ─────────────────────────────────────────
    if show_chart and prob_dicts:
        last_prob = prob_dicts[-1]
        last_order = orders[-1]
        last_token = tokens[-1]
        fig = render_prob_chart(last_prob, last_token, last_order, n)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Backoff banner (if backoff fired on the last step)
        if last_order < n and last_order > 0:
            st.info(
                f"Backoff triggered: the {n}-gram context was not found in the training "
                f"text. The model fell back to a {last_order}-gram distribution."
            )
        elif last_order == 0:
            st.error(
                "No candidates found even after backoff (or backoff is disabled). "
                "Try enabling backoff, lowering n, or choosing a different start phrase."
            )
    elif show_chart:
        st.caption(
            "The probability chart will appear here after the first token is generated."
        )


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

def sidebar() -> tuple:
    """Render sidebar controls; return (model, n, temperature, use_backoff, gen_length, start_phrase)."""
    with st.sidebar:
        st.title("Lexaitis")
        st.caption("An interactive n-gram language model explorer.")
        st.divider()

        # ── Text selection ────────────────────────────────────────────────────
        st.subheader("Source texts")
        text_options = all_display_names() + [CUSTOM_LABEL]
        selected_texts = st.multiselect(
            "Choose one or more texts",
            options=text_options,
            default=[all_display_names()[0]],
            key="text_select",
            help=(
                "Combine texts to create a richer corpus. "
                "Each bundled text contributes up to 30 k tokens."
            ),
        )

        if not selected_texts:
            st.warning("Please select at least one text.")
            selected_texts = [all_display_names()[0]]

        custom_text = ""
        if CUSTOM_LABEL in selected_texts:
            custom_text = st.text_area(
                "Paste your custom text here",
                height=150,
                placeholder="Paste at least a few hundred words for meaningful results.",
                key="custom_text",
            )
            if len(custom_text.strip()) < 50:
                st.warning("Please paste a longer text (at least ~50 words).")

        # Show per-text descriptions and combined token estimate
        bundled_selected = [t for t in selected_texts if t != CUSTOM_LABEL]
        if len(bundled_selected) == 1:
            desc = description_for(bundled_selected[0])
            if desc:
                st.caption(desc)
        elif len(bundled_selected) > 1:
            st.caption(
                f"{len(selected_texts)} text(s) selected — n-gram tables will be "
                f"built from their combined corpus (up to "
                f"{min(30 * len(selected_texts), 150):,} k tokens)."
            )

        # ── Model settings ────────────────────────────────────────────────────
        st.divider()
        st.subheader("Model settings")

        n = st.slider(
            "n  (n-gram order)",
            min_value=1,
            max_value=7,
            value=3,
            step=1,
            key="n_slider",
            help=(
                "n=1: unigram (no context).  "
                "n=2: bigram (1 token context).  "
                "n=3: trigram (2 tokens context), etc."
            ),
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.01,
            max_value=2.0,
            value=1.0,
            step=0.05,
            key="temp_slider",
            help=(
                "Low (→ 0): nearly deterministic / repetitive.  "
                "1.0: sample proportional to frequency.  "
                "High (> 1): increasingly random."
            ),
        )

        use_backoff = st.toggle(
            "Enable backoff",
            value=True,
            key="backoff_toggle",
            help=(
                "When the exact context is not found, fall back to a shorter "
                "context rather than stopping."
            ),
        )

        # ── Generation settings ───────────────────────────────────────────────
        st.divider()
        st.subheader("Generation settings")

        start_phrase = st.text_input(
            "Starting phrase",
            value="",
            placeholder="Leave blank for a random start token",
            key="start_phrase",
        )

        gen_length = st.slider(
            "Tokens to generate",
            min_value=1,
            max_value=200,
            value=50,
            step=1,
            key="gen_length",
        )

        st.divider()
        st.caption(
            "Lexaitis uses a simple n-gram model, not a neural network. "
            "It illustrates how next-token prediction works, not how modern "
            "large language models (e.g. GPT, Claude) achieve their results."
        )

    # Build (or retrieve cached) model from the combined selected corpus
    cache_custom = custom_text if CUSTOM_LABEL in selected_texts else ""
    model = get_model(tuple(selected_texts), cache_custom, max_n=7)

    return model, n, temperature, use_backoff, gen_length, start_phrase


# ──────────────────────────────────────────────────────────────────────────────
# Compare tab helpers
# ──────────────────────────────────────────────────────────────────────────────

def compare_settings_column(col_label: str, prefix: str) -> tuple:
    """Render compact per-column settings overrides inside a column."""
    st.markdown(f"#### {col_label}")
    n = st.slider(
        "n (order)",
        min_value=1, max_value=7, value=3 if prefix == "cmpA" else 5,
        key=f"{prefix}_n",
    )
    temperature = st.slider(
        "Temperature",
        min_value=0.01, max_value=2.0, value=1.0,
        step=0.05,
        key=f"{prefix}_temp",
    )
    use_backoff = st.toggle("Backoff", value=True, key=f"{prefix}_backoff")
    return n, temperature, use_backoff


# ──────────────────────────────────────────────────────────────────────────────
# Main app
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    model, n, temperature, use_backoff, gen_length, start_phrase = sidebar()

    tab_generate, tab_compare, tab_about = st.tabs(
        ["Generate", "Compare", "About"]
    )

    # ── Tab 1: Generate ───────────────────────────────────────────────────────
    with tab_generate:
        st.header("Text generation")
        st.markdown(
            "Use the **Step** button to generate one token at a time and watch the "
            "probability chart update, or click **Run all** to generate everything at once. "
            "The <span style='background:#ffd166;padding:1px 4px;border-radius:3px'>"
            "highlighted</span> tokens show the current context window; the "
            "<span style='background:#ef476f;color:white;padding:1px 4px;border-radius:3px'>"
            "red</span> token is the one just chosen.",
            unsafe_allow_html=True,
        )
        generation_panel(
            prefix="main",
            model=model,
            n=n,
            temperature=temperature,
            use_backoff=use_backoff,
            gen_length=gen_length,
            start_phrase=start_phrase,
        )

    # ── Tab 2: Compare ────────────────────────────────────────────────────────
    with tab_compare:
        st.header("Compare two runs side-by-side")
        st.markdown(
            "Both panels use the same **source text** and **starting phrase** as the "
            "sidebar. Each panel has its own **n**, **temperature**, and **backoff** "
            "settings so you can directly compare the effect of changing one parameter."
        )

        col_a, col_divider, col_b = st.columns([10, 1, 10])

        with col_a:
            nA, tempA, backoffA = compare_settings_column("Run A", "cmpA")
            st.divider()
            generation_panel(
                prefix="cmpA",
                model=model,
                n=nA,
                temperature=tempA,
                use_backoff=backoffA,
                gen_length=gen_length,
                start_phrase=start_phrase,
            )

        with col_divider:
            st.markdown(
                "<div style='border-left:2px solid #dee2e6;height:100%;margin:auto'></div>",
                unsafe_allow_html=True,
            )

        with col_b:
            nB, tempB, backoffB = compare_settings_column("Run B", "cmpB")
            st.divider()
            generation_panel(
                prefix="cmpB",
                model=model,
                n=nB,
                temperature=tempB,
                use_backoff=backoffB,
                gen_length=gen_length,
                start_phrase=start_phrase,
            )

    # ── Tab 3: About ──────────────────────────────────────────────────────────
    with tab_about:
        st.header("About Lexaitis")
        st.markdown(
            textwrap.dedent("""\
            **Lexaitis** is an interactive educational tool designed to help students
            understand one of the central ideas behind modern language models:
            *language generation as next-token prediction conditioned on prior context.*

            ---

            ### How it works

            At its core, Lexaitis uses a simple **n-gram language model**.

            An n-gram model estimates the probability of the next token based on
            the previous *n − 1* tokens.

            | n | Context size | Example |
            |---|---|---|
            | 1 (unigram) | 0 tokens | Samples from overall word frequency |
            | 2 (bigram) | 1 token | P(next \| previous) |
            | 3 (trigram) | 2 tokens | P(next \| prev₁, prev₂) |
            | … | … | … |

            More context generally improves local **coherence**, but it also increases
            **sparsity**: longer exact sequences become harder to find in a finite text.

            ---

            ### Key controls

            - **n (order)** — How many prior tokens condition the next prediction.
            - **Temperature** — Controls sampling randomness.  Low values make output
              deterministic; high values make it more varied and surprising.
            - **Backoff** — When an exact context is unseen, the model falls back to a
              shorter context rather than failing.

            ---

            ### What Lexaitis is *not*

            Lexaitis deliberately omits the machinery that makes modern LLMs powerful:

            - It uses a **fixed, small context window** (n − 1 tokens), not a large
              attention-based context.
            - It has **no learned representations** — tokens are treated as atomic symbols.
            - It has **no semantic understanding** — it only knows which words tend to
              follow which other words in a specific training text.

            These limitations are pedagogically intentional: they make the underlying
            logic of sequential prediction transparent and manipulable.

            ---

            ### Learning objectives

            After using Lexaitis, you should be able to:

            1. Explain language generation as probabilistic next-token prediction.
            2. Describe how context length affects coherence and sparsity.
            3. Explain the role of temperature in controlling output randomness.
            4. Distinguish between simple n-gram models and modern large language models.
            """)
        )


if __name__ == "__main__":
    main()
