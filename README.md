# Arrays 101 — in Python 3

The nineteen problems of LeetCode's Arrays 101 syllabus, worked in Python 3.14, with the theory
rewritten from scratch as a standalone Python course.

`notes/` owes nothing to any website. Chapter 1 is ~50,000 words on what a `list` actually is —
object layout, slicing semantics in full, the iterator protocol, over-allocation and amortized
cost, the complete operation cost model, aliasing, the other container types, and how to measure
all of it yourself. Chapter 2 is ~20,200 more on insertion: every form of it Python offers, what
each one moves, which of them can change a length, and the bugs that appear when a length changes
underneath code that recorded it. Chapter 3 is ~22,200 on deletion: every way an element leaves,
why the front is the expensive end, the one form that has to find its own target and what that
search costs, what a removal does to an index or an iterator recorded before it, and the case where
the length may not change at all. Chapter 4 is ~21,100 on search, the third of the three
fundamental operations and the one that moves nothing: every spelling of the scan and what each
refuses to tell you, why one O(n) row spans almost five orders of magnitude on a single list, `set`
and `dict` as lookup structures and when a second copy of your data pays for itself, halving a
sorted sequence and the precondition nothing enforces, searching for a description instead of a
value, and the disagreement between all of them about how to say "not there". Every claim in all
four was verified by execution: 271, 93, 96 and 85 runnable Python blocks, every `# -> value` a
real observed result on this machine — 646, 238, 240 and 244 of them.

You should never need to visit a website to use this repo.

## Layout

```
notes/          The course. Read this first. Standalone — no external reading required.
arrays101/      Your solutions. Stubs raise NotImplementedError.
tests/          The spec. Edge cases + randomized property tests.
hints/          Tiered hints, one file per tier. Open one when stuck, and only one.
dashboard.py    Generates the study dashboard from live repo state.
PROGRESS.md     Tracker for the 19 problems.
```

## Start here

```bash
uv run python dashboard.py --serve
```

Opens a dashboard that tells you the single next thing to do. It reads real state — the section
list comes from `notes/`, and problem status comes from actually running the test suite — so it
cannot drift from reality. Reading progress is ticked off in the browser and persists.

Regenerate any time with `uv run python dashboard.py`. Use `--fast` to skip the test run.

`--serve` uses port 8765, and walks up to the next free port if that one is busy — usually
because a dashboard from an earlier run is still serving. `--port N` pins it to a port you pick.

## Running

One problem, stopping at the first failure — the command you will use most:

```bash
uv run pytest tests/ch01/test_p01_max_consecutive_ones.py -x
```

Add `-vv` for a line per test instead of progress characters. It has to be `-vv`, not `-v`:
the config sets `-q`, pytest sums verbosity levels, and `-q -v` cancels back out to normal.

```bash
uv run pytest tests/ch01/test_p01_max_consecutive_ones.py -vv
```

Everything, once you have solutions to check:

```bash
uv run pytest
```

Expect this to be loud on a fresh clone — hundreds of lines, every failure the identical
`NotImplementedError` from an untouched stub. `uv run pytest --tb=no` gives you just the one-line
summary. None of the twelve `passed` in that summary is a solved problem.
`test_p03_squares_of_sorted_array.py::test_linear_does_not_sort` only asserts that `sortedSquares`
never calls `sorted()` — vacuously true while the body is still `raise NotImplementedError` — and
the other eleven never call your code at all. `test_cases_obey_the_stated_constraints`, in chapters
2, 3 and 4, checks the suite's own fixtures against the problem's stated constraints.
`test_the_grader_matches_the_judge`, in chapter 3's two suites, and
`test_the_grader_holds_the_contract_it_describes`, in chapter 4's two, check that the grader those
suites score you with agrees with the judge it is imitating. And
`test_the_shape_builders_are_what_they_claim`, also in chapter 4's two suites, checks that a fixture
built for a named shape really has that shape.

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
