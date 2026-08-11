# Arrays 101 — in Python 3

The nineteen problems of LeetCode's Arrays 101 syllabus, worked in Python 3.14, with the theory
rewritten from scratch as a standalone Python course.

`notes/` owes nothing to any website. Chapter 1 is ~49,000 words on what a `list` actually is —
object layout, slicing semantics in full, the iterator protocol, over-allocation and amortized
cost, the complete operation cost model, aliasing, the other container types, and how to measure
all of it yourself. Every claim in it was verified by execution: 273 runnable code blocks, every
`# -> value` a real observed result on this machine.

You should never need to open a browser to use this repo.

## Layout

```
notes/             The course. Read this first. Standalone — no external reading required.
arrays101/         Your solutions. Stubs raise NotImplementedError.
tests/             The spec. Edge cases + randomized property tests.
hints/             Tiered hints. Open only when stuck, one tier at a time.
PROGRESS.md        Tracker for the 19 problems.
.leetcode-source/  Raw source capture. Authoring input, spoiler-dense — not for reading.
```

## Running

Everything:

```bash
uv run pytest
```

One problem, verbose:

```bash
uv run pytest tests/ch01/test_p01_max_consecutive_ones.py -v
```

Stop at the first failure and drop into a debugger:

```bash
uv run pytest -x --pdb
```

Just the fast hand-written cases, skipping the randomized property tests:

```bash
uv run pytest -m "not property"
```

## The loop

1. Read the chapter note in `notes/`.
2. Open the stub in `arrays101/`, read the docstring — it has the full problem statement and
   constraints, taken verbatim from LeetCode.
3. Write the solution. Run the tests.
4. Stuck? Take **one** tier from `hints/`, then go back to step 3.
5. Green? Ask for a review. That conversation is where most of the learning is — complexity,
   idiom, and the approaches you didn't take.
6. Paste into LeetCode to confirm, and tick `PROGRESS.md`.

`class Solution` and the camelCase method names are LeetCode's convention, kept so solutions paste
in unedited. Real Python code would use module-level `snake_case` functions.
