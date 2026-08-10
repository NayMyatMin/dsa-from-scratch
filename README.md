# Arrays 101 — in Python 3

Working through LeetCode's [Arrays 101 explore
card](https://leetcode.com/explore/fun-with-arrays/card/fun-with-arrays/), translated from its
Java originals into Python 3.14.

The card teaches *Java* arrays: fixed size, explicit capacity, manual element shifting. Python has
none of that at the surface. Rather than skip the mismatch, `notes/` makes it the subject —
because "why does Python not need `capacity`?" has a real answer involving how CPython's `list`
actually works, and knowing it changes the code you write.

## Layout

```
notes/       Theory, one file per chapter. Read this first.
arrays101/   Your solutions. Stubs raise NotImplementedError.
tests/       The spec. Edge cases + randomized property tests.
hints/       Tiered hints. Open only when stuck, one tier at a time.
PROGRESS.md  Tracker for the 19 problems in the card.
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
