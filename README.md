# Lexaitis

**Lexaitis** is an interactive educational tool that lets students explore
language generation as next-token prediction conditioned on prior context.
It is built around a simple n-gram / Markov-style language model and is
deliberately minimal: its pedagogical value lies in making the logic of
sequential text prediction *visible and manipulable*, not in replicating
the power of modern neural language models.

---

## Quick start

### 1. Prerequisites

- Python 3.9 or later
- `pip`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

---

## What students can do

| Control | What it does |
|---|---|
| **Source text** | Choose from six bundled public-domain texts, or paste your own |
| **n (order)** | Set the n-gram order (1 = unigram, 2 = bigram, …, 7 = 7-gram) |
| **Temperature** | 0.01 = nearly deterministic; 1.0 = proportional to frequency; 2.0 = very random |
| **Backoff** | Allow the model to fall back to shorter contexts when an exact n-gram is unseen |
| **Starting phrase** | Seed text; leave blank for a random start |
| **Tokens to generate** | How many tokens to produce (1–200) |

### Generate tab
Step through generation one token at a time with **Step ▶**, or generate the
full sequence with **Run all ⏩**. At every step:
- The **context window** (the last n−1 tokens) is highlighted in amber.
- The **chosen token** is highlighted in red-pink.
- A **probability bar chart** shows the top-15 candidate next tokens and their
  probabilities after temperature scaling.  The chosen token's bar is red-pink.
- If **backoff** fired, a note appears explaining the fallback order actually used.

### Compare tab
Run two independent generations side-by-side with different n, temperature, or
backoff settings.  Both panels share the same source text and starting phrase
from the sidebar.

### About tab
A concise in-app reference explaining how Lexaitis works, its key controls, and
what it does *not* do.

---

## Bundled texts

| Text | Author | Approx. tokens |
|---|---|---|
| Alice in Wonderland | Lewis Carroll | ~27 k |
| Pride and Prejudice | Jane Austen | 30 k (excerpt) |
| Moby-Dick | Herman Melville | 30 k (excerpt) |
| Hamlet | William Shakespeare | ~30 k |
| Gettysburg Address | Abraham Lincoln | ~272 words |
| Declaration of Independence | — | ~1,300 words |

All texts are in the public domain.

---

## Project structure

```
Laxaitis/
├── app.py                         Streamlit entry point
├── requirements.txt
├── README.md
└── lexaitis/
    ├── __init__.py
    ├── model.py                   NgramModel class
    └── texts/
        ├── __init__.py
        ├── library.py             Text registry and loader
        ├── alice_in_wonderland.txt
        ├── pride_and_prejudice.txt
        ├── moby_dick.txt
        ├── hamlet.txt
        ├── gettysburg_address.txt
        └── declaration_of_independence.txt
```

---

## Pedagogical notes

### What Lexaitis demonstrates
- Language generation as a sequence of probabilistic decisions
- How context length (n) trades off coherence against sparsity
- How temperature controls the sharpness of the probability distribution
- How backoff handles unseen n-grams

### What Lexaitis does NOT do
Lexaitis is deliberately simple.  It is **not** a neural network and does not:
- Learn distributed word representations
- Handle long-range dependencies beyond n−1 tokens
- Generalise to semantically similar but lexically different contexts
- Scale to the vocabulary or parameter counts of modern LLMs

These limitations are intentional.  Seeing *where* the simple model breaks down
(repetitive loops at high n, incoherence at low n, gibberish after unseen
contexts) is itself a learning objective.

---

## Suggested classroom exercises

1. **Effect of n**: Generate 100 tokens from the same starting phrase with
   n = 1, 3, 5, and 7. Describe how coherence and repetitiveness change.

2. **Effect of temperature**: Hold n = 3 and vary temperature from 0.1 to 2.0.
   At what temperature does the output seem most "readable"?

3. **Backoff in action**: Choose the Gettysburg Address (a short text), set
   n = 6, and observe how often backoff fires. Then repeat with n = 2.

4. **Sparsity vs. coherence**: Why does a 7-gram model on a short text almost
   reproduce the source verbatim? What does this reveal about the training data?

5. **Comparison**: Generate text with two very different temperature settings
   using the Compare tab. Which looks more like the source text? Why?
