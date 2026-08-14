"""Spec for 26. Remove Duplicates from Sorted Array.

Problem 27's suite sorts the first k slots before it compares them, because 27's judge does.
This one does not, and that is the single most important line in this file. Five contracts are
enforced here.

1. `removeDuplicates` returns k, an int -- the number of distinct values in `nums`. bool is a
   subclass of int in Python, so `isinstance(k, int)` alone would let `True` through as 1; this
   suite rejects it explicitly.
2. The first k slots of `nums` hold the distinct values IN SORTED ORDER, compared one slot at a
   time. Order is graded here. The same values in a different arrangement is a wrong answer,
   where in 27 it was an equally right one.
3. `nums` itself is what gets read. Returning the right k while leaving `nums` alone fails, and
   so does building the right list somewhere else and handing it back.
4. len(nums) >= k, and that is the whole of the length contract. Everything beyond index k - 1
   can be ignored, so this suite ignores it: shrink the list, leave it exactly as long as it
   arrived, either is accepted.
5. n = 3 * 10^4, the constraint ceiling, inside a wall-clock budget, and a fixed amount of work
   per element as the list grows past it.

What this suite deliberately does NOT police, because the problem deliberately does not ask:

  the tail        Nothing past index k - 1 is ever read. `_check` slices `nums[:k]` and never
                  looks further. Leave the duplicates there, leave anything there.
  the length      len(nums) is free above k. Shrinking the list to exactly k is accepted and so
                  is leaving it as long as it arrived.
  extra space     Not measured at all. Chapter 5 is where constant extra space becomes the
                  subject; here a solution that allocates is as accepted as one that does not.

The note at the foot of this file says what each of those would cost if it were policed, and
names the accepted solutions a stricter suite would wrongly fail.

Time is policed, and here -- unlike in 27, whose ceiling of 100 elements is too small for a
clock to say anything -- the constraint ceiling itself is large enough to show the difference.
Over 3 * 10^4 identical values the eight accepted solutions measured for this file cost between
0.11 ms and 0.68 ms a pass, while one list-level deletion per duplicate cost 116 ms on the same
input: a factor of at least 170, on an input the constraints actually allow. So
`test_constraint_ceiling` measures the real ceiling, and
`test_does_not_grow_quadratically` confirms the shape with a ratio, which is the measurement that
does not care how fast the machine underneath it is. Those two both time the same pair of shapes,
and that pair is the two ends of the range k can occupy -- k = 1 and k = 201 -- so
`test_does_not_grow_quadratically_between_the_two_extremes` takes the same ratio on two shapes
from the middle of it, where a wall clock has too little to separate with. The numbers behind
every budget are in the docstring of the test that spends them, and every one of them was set
from measurements of solutions that are accepted rather than from what looked like a reasonable
round number.

Every test here that can run your solution on a long list is bounded. None of them will sit in
silence for ten minutes while a slow solution grinds through; each stops and says what it stopped
for. The bounds are sized so that only a solution which has already failed a timing guard can
reach one.

Every input this suite hands over arrives sorted non-decreasing with values in -100..100, and
`test_cases_obey_the_stated_constraints` holds the hand-written table to that. A solution is
entitled to assume it.
"""

import random
import time
from collections.abc import Callable
from itertools import combinations_with_replacement

import pytest

from arrays101.ch03.p02_remove_duplicates import Solution
from tests._reference.p02_remove_duplicates import oracle


def solve(nums: list[int]) -> object:
    """Run the solution and hand back its return value, which must be k."""
    return Solution().removeDuplicates(nums)


# ======================================================================================
# Contract checking, shared by every test below.
# ======================================================================================


def _render(value: object, limit: int = 24) -> str:
    """A repr that stays readable when the list has tens of thousands of elements in it."""
    if not isinstance(value, list) or len(value) <= limit:
        return repr(value)
    head = ", ".join(str(x) for x in value[:12])
    tail = ", ".join(str(x) for x in value[-4:])
    return f"[{head}, ..., {tail}] ({len(value)} elements)"


def _first_difference(got: list[int], want: list[int]) -> int | None:
    for i, (a, b) in enumerate(zip(got, want)):
        if a != b:
            return i
    return None


def _check(probes: str, original: list[int], nums: list[int], returned: object) -> None:
    """Assert the whole contract for one call, exactly as the judge would.

    `original` is a pristine snapshot taken before the call; `nums` is the list the solution was
    handed. The answer key is computed from the snapshot, so a solution cannot rewrite its own
    answer key.
    """
    expected = oracle(original)
    where = f"{probes}: removeDuplicates({_render(original)})"

    if isinstance(returned, bool) or not isinstance(returned, int):
        raise AssertionError(
            f"{where} returned {_render(returned)}. It must return k, the number of distinct "
            f"values -- an int, and the count itself, not the values and not a truth value. The "
            f"values go in the front of nums; the count comes back."
        )
    if returned != len(expected):
        detail = ""
        if returned == len(original) - len(expected):
            detail = (
                ". That is how many duplicates there were. k is how many values survive -- what "
                "is left, not what went"
            )
        elif returned == len(nums) and len(nums) != len(expected):
            detail = (
                ". That is len(nums) after the call. The two are only the same if the list was "
                "shortened to exactly k, and nothing requires that; k has to be counted, not "
                "read off the length"
            )
        raise AssertionError(f"{where} returned {returned}, want {len(expected)}{detail}")

    k = returned
    if len(nums) < k:
        raise AssertionError(
            f"{where} returned {k} but left only {len(nums)} elements in nums: {_render(nums)}. "
            f"The first k slots are the answer, so there have to be k of them. len(nums) is free "
            f"above that -- it may shrink to exactly k or stay as long as it arrived -- but it "
            f"cannot go below it."
        )

    got = nums[:k]
    if got != expected:
        i = _first_difference(got, expected)
        detail = f"first difference at index {i}: nums[{i}] = {got[i]}, want {expected[i]}"
        if nums == original:
            detail += (
                ". nums came back exactly as it was handed over, so nothing was written into it "
                "at all. This problem is in place: the caller keeps a reference to this very "
                "list and reads the front of it, and a new list built somewhere else never "
                "reaches them"
            )
        elif sorted(got) == expected:
            detail += (
                ". The right values are in the first k slots, in the wrong order. This is where "
                "26 and 27 differ: 27's judge sorts the first k before comparing, and this one "
                "does not -- it walks the slots one at a time"
            )
        elif len(set(got)) != len(got):
            detail += ". nums[:k] still contains a repeated value"
        raise AssertionError(
            f"{where} returned {k} and left nums[:{k}] = {_render(got)}, want {_render(expected)}"
            f"; {detail}. (The full list afterwards was {_render(nums)}, and nothing past index "
            f"{k - 1} is read.)"
        )


def _run(probes: str, nums: list[int]) -> None:
    """Snapshot, call, check. The snapshot is the answer key; the solution never touches it."""
    original = list(nums)
    returned = solve(nums)
    _check(probes, original, nums, returned)


# ======================================================================================
# Shapes and sizes used by more than one test below.
# ======================================================================================

CEILING = 30_000  # the constraint ceiling: 1 <= nums.length <= 3 * 10^4


def _one_value(n: int) -> list[int]:
    """One value repeated n times: every element after the first is a duplicate."""
    return [7] * n


def _equal_runs(n: int) -> list[int]:
    """The 201 values the constraints allow, in equal runs. k is as large as it can get."""
    return sorted((i % 201) - 100 for i in range(n))


def _pairs(n: int) -> list[int]:
    """101 values in equal runs. k is in the middle of its range instead of at either end."""
    return sorted([(i % 101) - 50 for i in range((n + 1) // 2)] * 2)[:n]


def _eleven_runs(n: int) -> list[int]:
    """11 values in equal runs. Long runs, and still nowhere near either end of k's range."""
    return sorted((i % 11) - 5 for i in range(n))


# ======================================================================================
# The grader itself, against the judge's rules.
# ======================================================================================


def test_the_grader_matches_the_judge() -> None:
    """What `_check` accepts and rejects, pinned down rather than asserted in a docstring.

    Every after-state below is one a solution could plausibly leave behind. The accepted ones
    show how little the tail matters; the rejected ones include the case that separates this
    problem from 27, which is the same values in the first k slots in a different order.
    """
    original = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]  # five distinct values: 0, 1, 2, 3, 4

    accepted: list[tuple[str, list[int], int]] = [
        ("tail left as it was", [0, 1, 2, 3, 4, 2, 2, 3, 3, 4], 5),
        ("tail full of junk", [0, 1, 2, 3, 4, 99, -7, 1000, 0, 0], 5),
        ("tail zeroed", [0, 1, 2, 3, 4, 0, 0, 0, 0, 0], 5),
        ("list shortened to exactly k", [0, 1, 2, 3, 4], 5),
        ("list shortened part of the way", [0, 1, 2, 3, 4, 3, 3], 5),
    ]
    for probe, after, k in accepted:
        _check(f"grader self-test, accepted: {probe}", original, after, k)

    rejected: list[tuple[str, list[int], object]] = [
        ("the right values in the wrong order", [1, 0, 2, 4, 3, 2, 2, 3, 3, 4], 5),
        ("the right values reversed", [4, 3, 2, 1, 0, 2, 2, 3, 3, 4], 5),
        ("k too small", [0, 1, 2, 3, 4, 2, 2, 3, 3, 4], 4),
        ("k too large", [0, 1, 2, 3, 4, 2, 2, 3, 3, 4], 6),
        ("nothing written into nums", list(original), 5),
        ("distinct values pushed to the back", [0, 0, 1, 1, 1, 0, 1, 2, 3, 4], 5),
        ("a duplicate left inside the first k", [0, 0, 1, 2, 3, 4, 2, 3, 3, 4], 5),
        ("the list left shorter than k", [0, 1, 2, 3], 5),
        ("the answer returned instead of counted", [0, 1, 2, 3, 4], [0, 1, 2, 3, 4]),
        ("True instead of 1", [7, 7], True),
    ]
    for probe, after, k in rejected:
        with pytest.raises(AssertionError):
            _check(f"grader self-test, rejected: {probe}", original, after, k)

    # Returning the number of duplicates removed instead of the number kept. `original` above
    # has five of each, so it cannot tell the two apart; this input has one duplicate and three
    # values that stay.
    with pytest.raises(AssertionError):
        _check("grader self-test, rejected: count of duplicates", [0, 0, 1, 2], [0, 1, 2, 2], 1)

    # And True is only rejected because bool is not int here: 1 in its place is the right answer.
    _check("grader self-test, accepted: 1 for a single distinct value", [7, 7], [7, 7], 1)


# ======================================================================================
# Hand-written cases. Each is (probe, nums, expected distinct values in order).
# ======================================================================================

Case = tuple[str, list[int], list[int]]

CASES: list[Case] = [
    # --- LeetCode's own examples ------------------------------------------------------------
    ("example 1", [1, 1, 2], [1, 2]),
    ("example 2", [0, 0, 1, 1, 1, 2, 2, 3, 3, 4], [0, 1, 2, 3, 4]),
    # --- the smallest legal input -------------------------------------------------------------
    ("single element", [7], [7]),
    ("single element, most negative legal value", [-100], [-100]),
    ("single element, largest legal value", [100], [100]),
    # --- nothing to remove ----------------------------------------------------------------------
    ("already distinct, length 2", [1, 2], [1, 2]),
    ("already distinct, length 5", [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2]),
    ("already distinct, adjacent values", [4, 5, 6, 7], [4, 5, 6, 7]),
    # --- everything is a duplicate of one value --------------------------------------------------
    ("all identical, length 2", [3, 3], [3]),
    ("all identical, length 8", [-5] * 8, [-5]),
    ("all identical zeros", [0, 0, 0], [0]),
    # --- where the run sits ----------------------------------------------------------------------
    ("run at the front", [1, 1, 1, 2, 3], [1, 2, 3]),
    ("run at the back", [1, 2, 3, 3, 3], [1, 2, 3]),
    ("run in the middle", [1, 2, 2, 2, 3], [1, 2, 3]),
    ("runs at both ends", [1, 1, 2, 3, 3], [1, 2, 3]),
    ("every value doubled", [1, 1, 2, 2, 3, 3], [1, 2, 3]),
    ("every value tripled", [1, 1, 1, 2, 2, 2], [1, 2]),
    # --- the last element decides, which is where off-by-ones live -------------------------------
    ("last element new", [1, 1, 1, 2], [1, 2]),
    ("last element a duplicate", [1, 2, 2], [1, 2]),
    ("last two elements new", [1, 1, 2, 3], [1, 2, 3]),
    ("only the first element is distinct", [5, 6, 6, 6, 6], [5, 6]),
    # --- negatives, and values that straddle zero ------------------------------------------------
    ("negatives only", [-3, -3, -2, -1, -1], [-3, -2, -1]),
    ("straddling zero", [-1, -1, 0, 0, 1, 1], [-1, 0, 1]),
    ("zeros in the middle of a run", [-1, 0, 0, 0, 1], [-1, 0, 1]),
    # --- constraint extremes on the values -------------------------------------------------------
    ("both ends of the value range", [-100, -100, 100, 100], [-100, 100]),
    ("the whole value range, once each", list(range(-100, 101)), list(range(-100, 101))),
    ("the whole value range, twice each",
     sorted(list(range(-100, 101)) * 2), list(range(-100, 101))),
    # --- longer, so that a mistake in one run cannot hide in the noise ---------------------------
    ("24 elements, three runs of eight", [1] * 8 + [2] * 8 + [3] * 8, [1, 2, 3]),
    ("24 elements, twelve pairs", sorted(list(range(12)) * 2), list(range(12))),
    ("25 elements, one long run then singles", [0] * 20 + [1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5]),
    ("25 elements, singles then one long run", [1, 2, 3, 4, 5] + [6] * 20, [1, 2, 3, 4, 5, 6]),
]


@pytest.mark.parametrize("probe,nums,expected", CASES)
def test_examples_and_edges(probe: str, nums: list[int], expected: list[int]) -> None:
    # The table's expected values are asserted against the reference as well, so a typo in a
    # hand-written case shows up as a broken test rather than as a wrong requirement.
    assert expected == oracle(nums), (
        f"the test case {probe!r} disagrees with the reference answer -- fix the table, "
        f"not the solution"
    )
    _run(probe, list(nums))


def test_cases_obey_the_stated_constraints() -> None:
    """The fixtures are held to the same contract the solution is.

    A case outside the constraints would demand something never asked for, and a solution that
    failed it would be right to. Checked rather than assumed: these cases are hand-written.
    """
    for probe, nums, expected in CASES:
        assert 1 <= len(nums) <= 30_000, f"[{probe}]: 1 <= nums.length <= 3 * 10^4"
        assert all(-100 <= x <= 100 for x in nums), f"[{probe}]: -100 <= nums[i] <= 100"
        assert nums == sorted(nums), f"[{probe}]: nums arrives sorted in non-decreasing order"
        assert expected == sorted(set(nums)), f"[{probe}]: the answer key is the distinct values"


@pytest.mark.property
def test_every_small_sorted_pattern() -> None:
    """Every non-decreasing list of length 1 to 8 over a four-value alphabet, exhaustively.

    494 lists. Only the run lengths matter, so enumerating every combination with repetition
    covers the whole shape of the problem at small sizes: runs at the front, at the back, in the
    middle, single elements between long runs, and every list that is one repeated value.
    """
    for n in range(1, 9):
        for tup in combinations_with_replacement((-1, 0, 1, 2), n):
            nums = list(tup)
            _run(f"exhaustive n={n}, nums={nums}", nums)


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    rng = random.Random(26)
    for _ in range(2000):
        n = rng.randint(1, 60)
        # Narrow alphabets force long runs; the widest is the constraint range itself, where
        # most values appear once. Both extremes matter.
        lo, hi = rng.choice([(0, 0), (0, 1), (-1, 1), (-3, 3), (-20, 20), (-100, 100)])
        nums = sorted(rng.randint(lo, hi) for _ in range(n))
        _run(f"random n={n}, values in {lo}..{hi}", nums)


@pytest.mark.property
def test_mid_size_lengths() -> None:
    """Every length between the small exhaustive sizes and the constraint ceiling is fair game.

    The tests above stop at n = 60 and the timing guards below start at n = 3 * 10^4, all round
    numbers. A gap like that is somewhere for a bug to live: a solution that walks the list in
    fixed-size chunks, or that handles a leftover tail separately, can be right on every length
    up to 60, right again on a round 30,000, and wrong on 101 or 29,999.

    The lengths worth naming come first: every one just above where the random test stops, both
    sides of each power of two, both sides of each round number, 201 and its neighbours -- the
    number of distinct values the constraints allow -- and 29,999, one short of the longest
    input there can be. Each is tried in five shapes.

    Naming lengths only covers the ones somebody thought of, so the rest of the range is then
    walked with a stride of 500 in two shapes. That leaves no window of 500 consecutive lengths
    anywhere below the ceiling untested, which is what makes this a statement about all lengths
    rather than about a lucky handful.

    The whole sweep is held to a wall clock, and that is not a speed requirement -- it is a
    diagnosis instead of a silence. 575 calls land here, some of them near the constraint ceiling,
    so a solution whose cost grows with the length of the list can spend a very long time in a test
    that has nothing to say about speed: one that calls .count() over the whole list for every
    element reached call 528 of the 575 in 61 s, and was still going. Measured on this repo's
    interpreter, CPython 3.14.4: the sweep costs the quickest accepted solution 0.28 s and the
    slowest of them -- the one that checks each element against the values it has kept so far --
    2.06 s. The budget is 60 s, twenty-nine times the slowest, and nothing can trip it without
    having already failed `test_constraint_ceiling` below, which reports the same problem with a
    per-pass number attached.
    """
    rng = random.Random(2626)
    sweep_budget = 60.0
    started = time.perf_counter()
    done = 0

    def run(probe: str, nums: list[int]) -> None:
        nonlocal done
        _run(probe, nums)
        done += 1
        elapsed = time.perf_counter() - started
        assert elapsed < sweep_budget, (
            f"the length sweep was abandoned after {elapsed:.0f}s and {done} of {planned} calls, "
            f"the last of them {probe}. This test grades answers, not speed, and it is stopping "
            f"only because it cannot finish: the accepted solutions measured for this file get "
            f"through the whole sweep in 0.28 to 2.06 s. The timing guards at the foot of this "
            f"file are the ones that grade speed, and they will tell you the same thing with "
            f"numbers -- run them with `uv run pytest -m slow`."
        )

    def all_distinct(n: int) -> list[int]:
        """As many distinct values as -100..100 allows, then a run to make up the length."""
        head = list(range(-100, min(101, -100 + n)))
        return head + [100] * (n - len(head))

    def pairs(n: int) -> list[int]:
        return sorted([(i % 101) - 50 for i in range((n + 1) // 2)] * 2)[:n]

    def sprinkled(n: int) -> list[int]:
        return sorted(rng.randint(-100, 100) for _ in range(n))

    lengths = list(range(61, 121))
    for base in (128, 256, 1024, 4096, 16384):
        lengths += [base - 1, base, base + 1]
    for base in (100, 201, 500, 1000, 10_000):
        lengths += [base - 1, base, base + 1]
    lengths.append(CEILING - 1)
    strided = list(range(201, CEILING, 500))
    # 575, counted rather than quoted, so the abandonment message above stays true if either
    # loop below is ever widened.
    planned = len(lengths) * 5 + len(strided) * 2

    for n in lengths:
        run(f"n={n}, one value repeated", _one_value(n))
        run(f"n={n}, every distinct value the range allows", all_distinct(n))
        run(f"n={n}, 201 values in equal runs", _equal_runs(n))
        run(f"n={n}, every value in a pair", pairs(n))
        run(f"n={n}, random sorted", sprinkled(n))

    for n in strided:
        run(f"n={n}, 201 values in equal runs", _equal_runs(n))
        run(f"n={n}, random sorted", sprinkled(n))

    assert done == planned, f"the sweep made {done} calls, not the {planned} it planned"


# ======================================================================================
# Timing guards.
# ======================================================================================

# The two shapes both timing guards measure, as (name, builder, ceiling budget). The budget is
# the wall clock `test_constraint_ceiling` allows for REPEATS passes at n = 3 * 10^4, and the two
# differ by a factor of 24 for a reason its docstring sets out: the constraints cap the number of
# distinct values at 201, so the cost of an accepted solution can depend heavily on the shape,
# while the cost of one whose work grows with the length of the list barely moves between them.
TIMED_SHAPES: tuple[tuple[str, Callable[[int], list[int]], float], ...] = (
    ("one value repeated", _one_value, 0.5),
    ("201 values in equal runs", _equal_runs, 12.0),
)

REPEATS = 25  # passes at the ceiling, per shape, in test_constraint_ceiling


@pytest.mark.slow
def test_constraint_ceiling() -> None:
    """n = 3 * 10^4, the largest input the constraints allow, against a wall-clock budget.

    A single pass at the ceiling takes well under a millisecond, too quick to measure against
    machine noise, so each budget covers 25 of them, and every figure below is a measured total
    for 25 passes with the mean per pass beside it. Measured on this repo's interpreter, CPython
    3.14.4. Eight accepted solutions were measured: a write cursor, a slice assignment from a set,
    a front-slice assignment from a comprehension, dict.fromkeys, one key per run from
    itertools.groupby, a scan against the values kept so far, one that writes the distinct values
    over the front of the list one at a time, and one that deletes backwards from the end.

        one value repeated                            25 passes      per pass
            eight accepted solutions              0.003 - 0.020 s   0.12 -  0.80 ms
            ---------------------------------------------------------- budget: 0.5 s
            one .pop() per duplicate                      1.58 s          63.2 ms
            .remove() per duplicate                       1.82 s          73.0 ms
            one del per duplicate                         3.72 s         148.8 ms
            .count() per element                         15.38 s         615.1 ms

        201 values in equal runs                      25 passes      per pass
            eight accepted solutions              0.006 - 0.688 s   0.24 - 27.5 ms
            one .pop() per duplicate                      2.19 s          87.5 ms
            .remove() per duplicate                       3.66 s         146.6 ms
            one del per duplicate                         4.16 s         166.5 ms
            --------------------------------------------------------- budget: 12.0 s
            .count() per element                         94.91 s        3796.6 ms

    The two budgets differ by a factor of 24, and the reason is the most interesting thing on
    this page. The constraints cap the distinct values at 201, so a solution that checks each
    element against the values it has kept so far does at most 201 comparisons per element: a
    fixed amount, whatever n is, which makes it linear in n and accepted. But that fixed amount is
    two hundred times larger on the 201-value shape than on the single-value one, and that one
    solution costs 0.005 s on the first table and 0.688 s on the second, a factor of 138. A
    solution whose work grows with the length of the list barely moves between them -- one del per
    duplicate goes 3.72 s to 4.16 s -- because its cost is set by n, and both shapes have the same
    n.

    So the two bands are 79x apart on the single-value shape (0.020 s against 1.58 s) and 3.2x
    apart on the 201-value one (0.688 s against 2.19 s). A factor of three is not a gap a wall
    clock can be trusted inside, and the budgets are placed accordingly: 0.5 s on the first shape,
    25x above the slowest accepted solution and still rejecting all four of the others, and 12.0 s
    on the second, 17x above the slowest accepted solution and catching only the catastrophe.
    Note what that means -- on the 201-value shape three of the four rejected solutions come in
    under the budget, and none of them escapes, because the first shape has already failed them.
    `test_does_not_grow_quadratically` then separates the bands on both shapes at once, without
    depending on the speed of the machine to do it.

    Correctness comes first, on six shapes: a wrong answer should say it is wrong, not that it is
    slow. Those six are not timed, but they are bounded, so that a solution slow enough to make
    them look like a hang gets a sentence instead of silence; the eight accepted solutions get
    through all six in 0.003 s to 0.083 s, against a bound of 30 s. Then the timed passes, which
    give up the moment the budget is blown rather than sitting through all 25 of something
    pathological -- the last row above would take a minute and a half to finish them.
    """
    rng = random.Random(126)
    shapes: list[tuple[str, list[int]]] = [
        ("one value repeated", _one_value(CEILING)),
        ("201 values in equal runs", _equal_runs(CEILING)),
        ("random sorted, full value range",
         sorted(rng.randint(-100, 100) for _ in range(CEILING))),
        ("every value in a pair", sorted([(i % 101) - 50 for i in range(CEILING // 2)] * 2)),
        ("one long run then the rest distinct", [-100] * (CEILING - 200) + list(range(-99, 101))),
        ("the rest distinct then one long run", list(range(-100, 100)) + [100] * (CEILING - 200)),
    ]
    started = time.perf_counter()
    for i, (name, data) in enumerate(shapes, start=1):
        _run(f"n=3x10^4, {name}", list(data))
        elapsed = time.perf_counter() - started
        assert elapsed < 30.0, (
            f"the six correctness shapes at the ceiling were abandoned after {elapsed:.0f}s, with "
            f"{i} of them done and the last being {name}. Nothing was wrong with the answers -- "
            f"this part of the test grades answers, not speed, and it is stopping only because a "
            f"solution this slow makes it look like a hang. The accepted solutions measured for "
            f"this file get through all six in 0.003 to 0.083 s. The budgets below are the ones "
            f"that grade speed, and they never got to run."
        )

    for name, make, budget in TIMED_SHAPES:
        data = make(CEILING)
        elapsed, passes = 0.0, 0
        for _ in range(REPEATS):
            c = list(data)  # a fresh copy each pass, made before the clock starts
            start = time.perf_counter()
            solve(c)
            elapsed += time.perf_counter() - start
            passes += 1
            if elapsed >= budget:
                break
        assert elapsed < budget, (
            f"{passes} of {REPEATS} passes over 3x10^4 elements ({name}) already cost "
            f"{elapsed:.1f}s -- {elapsed / passes * 1e3:.0f} ms a pass -- against a budget of "
            f"{budget}s for all {REPEATS}, and the run was cut short the moment the budget went, "
            f"so the real figure is worse. The accepted solutions measured for this budget cost "
            f"between 0.12 and 27.5 ms a pass on these two shapes. Something inside the loop is "
            f"doing work proportional to the length of the list rather than a fixed amount, "
            f"which makes the whole thing quadratic -- and quadratic is what a Time Limit "
            f"Exceeded on the submission page means."
        )


def _timed_best_of(data: list[int], reps: int, beyond_doubt: float | None = None) -> float:
    """Fastest of up to `reps` runs, in seconds, timing only the call.

    Every run needs its own copy, since the solution rewrites what it is given. The copy is made
    immediately before the clock starts and dropped immediately after, so the copying is never
    inside the measurement and only one copy is ever alive.

    The repetitions are noise rejection, not sampling. Interference from other processes only
    ever makes a run slower, so the fastest of several is the closest thing to a clean
    measurement of the code itself, and both sides of a ratio have to get the same number of
    tries or the ratio measures the sampling rather than the code. Nine is what both sides get.
    Measured on this interpreter: 200 runs of one correct pass at n = 10^4 ranged from 0.123 ms to
    3.447 ms, and 100 runs at n = 8x10^4 from 0.983 ms to 10.486 ms. The same code, the same
    input, a spread of 28x at the smaller size -- so a single sample says very little, and a side
    sampled only a few times can miss its floor entirely and inflate the ratio all by itself.

    `beyond_doubt` keeps nine repetitions from being slow to fail. The measurement stops early
    once the fastest run so far is past a threshold that repetition cannot rescue it from: after
    three runs at all, or immediately if it is more than a second past. The largest single burst
    of interference in the runs above was 9.5 ms, so a full second clear of the threshold is not
    noise -- it is a measurement failing on its own merits. Without that second clause a solution
    taking half a minute per pass would be timed nine times over.
    """
    fastest = float("inf")
    for taken in range(1, reps + 1):
        c = list(data)
        start = time.perf_counter()
        solve(c)
        fastest = min(fastest, time.perf_counter() - start)
        if beyond_doubt is not None and fastest > beyond_doubt:
            if taken >= 3 or fastest > beyond_doubt + 1.0:
                break
    return fastest


@pytest.mark.slow
def test_does_not_grow_quadratically() -> None:
    """Eight times the input should cost about eight times the work, on two shapes.

    The budgets above separate a single pass from a pass per duplicate at the real ceiling, and
    on one of the two shapes they cannot do it cleanly. This is the guard that says which of the
    two you wrote in a way that does not depend on how fast this machine is: a ratio is the same
    number on a slow machine and a fast one, and it stays the same number when the wall clock is
    busy with something else.

    The statistic is the best of three rounds, each round the best of nine runs on each side.
    Both sides get the same nine, and the reason for the three rounds is measured rather than
    assumed. A single round of best-of-nine reached 23.40x for a correct solution on the
    single-value shape and 17.01x on the 201-value one: the first of those is past the 20x ceiling,
    so one round would have failed a right answer outright. Interference only ever inflates a
    ratio, so the best of three rounds is the cleanest of the three, and across 144 such statistics
    -- eight accepted solutions, both shapes, nine statistics each -- the worst was 9.09x.

        one value repeated                                        n = 10^4 -> 8x10^4
            eight accepted solutions, 72 statistics                2.25x -  8.17x
            ------------------------------------------------------------ ceiling: 20x
            one del per duplicate                                         89.3x
            .count() per element                                         127.7x
            .remove() per duplicate                                      149.9x
            one .pop() per duplicate                                     163.0x

        201 values in equal runs                                  n = 10^4 -> 8x10^4
            eight accepted solutions, 72 statistics                2.42x -  9.09x
            ------------------------------------------------------------ ceiling: 20x
            .remove() per duplicate                                       58.4x
            one del per duplicate                                        106.1x
            one .pop() per duplicate                                     186.8x
            .count() per element                                 stopped by the probe

    The accepted rows are the statistic this test computes; the rejected rows are single rounds,
    taken because a full three rounds of a quadratic solution at 8x10^4 costs minutes to restate
    what one round has already settled. Three rounds can only lower a ratio, and even so the
    nearest any of them came to the ceiling was 58.4x.

    The last row is worth a word. On the 201-value shape a single pass costs that solution 0.45 s
    at n = 10^4, and the probe below stops it there rather than spending a minute on one run at
    8x10^4 to confirm what the ceiling budget has already said with a number.

    A solution whose cost grows with the length of the list lands at 58x or beyond, so the 20x
    ceiling sits in a wide empty gap with the accepted band nowhere near the other side of it.

    Two shapes rather than one, for the same reason as everywhere else in this repo: a list of a
    single repeated value is the easiest input in the world to be accidentally fast on, and the
    second shape is the one where the answer really has 201 values in it.
    """
    small_n, factor, ceiling, rounds, reps = 10_000, 8, 20.0, 3, 9
    big_n = small_n * factor
    # One pass at the small size costs an accepted solution between 0.036 ms and 5.55 ms, the
    # slowest being the scan against the values kept so far on the 201-value shape. A solution
    # 36 times slower than that has already blown the ceiling budget above, and timing it at
    # 8x10^4 would mean a single run of a minute or more, so it is stopped here instead.
    hopeless = 0.200

    for name, make, _budget in TIMED_SHAPES:
        small = make(small_n)

        probe = _timed_best_of(small, 1)
        assert probe < hopeless, (
            f"one pass over {small_n:,} elements ({name}) took {probe:.2f}s, so the growth "
            f"measurement was not attempted: at eight times the length it would take a minute or "
            f"more for a single run. An accepted solution costs between 0.036 ms and 5.55 ms "
            f"here. test_constraint_ceiling above has already reported this with a per-pass "
            f"number; the shape of the growth is not the interesting question until the size of "
            f"it is fixed."
        )

        big = make(big_n)
        # Correctness at the larger size, checked once, outside the timing. This size is past
        # the stated ceiling of 3 * 10^4, so it is a bonus rather than part of the contract.
        _run(f"n={big_n:,}, {name}", list(big))

        ratios = []
        for _ in range(rounds):
            small_time = _timed_best_of(small, reps)
            # Past this the ratio is already over the ceiling and no number of further runs at
            # this size can bring it back, so stop paying for them.
            big_time = _timed_best_of(big, reps, beyond_doubt=ceiling * small_time + 0.050)
            ratios.append(big_time / small_time)
        ratio = min(ratios)

        assert ratio < ceiling, (
            f"{factor}x the input cost {ratio:.0f}x the time (n={small_n:,} -> {big_n:,}, "
            f"{name}, the best of {rounds} rounds of {reps} runs a side). A single pass lands "
            f"near {factor}x; {ratio:.0f}x means the work done per element grows with the length "
            f"of the list. The algorithm may well be right -- look instead for a step inside the "
            f"loop that is not O(1). del nums[i], nums.pop(i), nums.remove(x) and "
            f"nums.insert(i, x) all move every element past the position they touch; `in`, "
            f".index() and .count() walk the list; slicing copies it. Each of those is O(n) on "
            f"its own, and doing one per element is the entire cost."
        )


# The shapes `test_does_not_grow_quadratically_between_the_two_extremes` measures. Both timing
# guards above use TIMED_SHAPES, whose two entries sit at the two ends of k's range: k = 1 and
# k = 201, the smallest and largest the constraints allow. These two sit in between.
MIDDLE_SHAPES: tuple[tuple[str, Callable[[int], list[int]]], ...] = (
    ("every value in a pair", _pairs),               # k = 101, runs of two at n = 202
    ("eleven values in equal runs", _eleven_runs),   # k = 11, and every run is long
)


@pytest.mark.slow
def test_does_not_grow_quadratically_between_the_two_extremes() -> None:
    """The same growth measurement, on shapes where k is neither 1 nor 201.

    Every timed input above is one of two shapes, and both are extremes: `_one_value` has k = 1,
    the smallest k the constraints allow, and `_equal_runs` has k = 201, the largest. Nothing
    above ever puts a clock on an input between them, and `test_constraint_ceiling` cannot be
    asked to -- on `_pairs` at the ceiling an accepted solution costs between 0.01 and 10.02 ms a
    pass while one del per duplicate costs 135.75 ms, a gap of 13x, and a budget that fits inside
    a gap that narrow is either failing right answers or letting the wrong one through. It cannot
    do both: 20x clear of the slowest accepted solution puts the budget at 5.0 s for 25 passes,
    and one del per duplicate finishes those 25 in 3.4 s.

    So this is a ratio, for the reason the test above gives: a ratio is the same number on a slow
    machine and a fast one. Measured on this repo's interpreter, CPython 3.14.4, as the best of
    three rounds of nine runs a side -- the same statistic, on the same two sizes:

        every value in a pair (k = 101)                           n = 10^4 -> 8x10^4
            twelve accepted solutions                             1.22x -  7.94x
            ------------------------------------------------------------ ceiling: 20x
            one del per duplicate                                        68.49x

        eleven values in equal runs (k = 11)                      n = 10^4 -> 8x10^4
            twelve accepted solutions                             1.16x -  8.06x
            ------------------------------------------------------------ ceiling: 20x
            one del per duplicate                                        65.05x

    What this catches that the guards above do not: a solution whose cost is linear on the two
    shapes they measure and quadratic everywhere else. One written by hand to do exactly that --
    the write cursor when the distinct count is 1 or 201, a del per duplicate otherwise -- passes
    every other test in this file, including all six correctness shapes at the ceiling, because
    those six are held to 30 s between them and it spends 0.13 s. Here it lands at 67.40x and
    66.72x.

    The two sizes and the accepted band are the same as above, so the same `hopeless` probe
    applies: an accepted solution costs between 0.001 ms and 3.257 ms for one pass at n = 10^4 on
    these shapes, and anything past 0.200 s is reported rather than timed at eight times the size.
    """
    small_n, factor, ceiling, rounds, reps = 10_000, 8, 20.0, 3, 9
    big_n = small_n * factor
    hopeless = 0.200

    for name, make in MIDDLE_SHAPES:
        small = make(small_n)

        probe = _timed_best_of(small, 1)
        assert probe < hopeless, (
            f"one pass over {small_n:,} elements ({name}) took {probe:.2f}s, so the growth "
            f"measurement was not attempted: at eight times the length it would take a minute or "
            f"more for a single run. An accepted solution costs between 0.001 ms and 3.257 ms "
            f"here."
        )

        big = make(big_n)
        _run(f"n={big_n:,}, {name}", list(big))

        ratios = []
        for _ in range(rounds):
            small_time = _timed_best_of(small, reps)
            big_time = _timed_best_of(big, reps, beyond_doubt=ceiling * small_time + 0.050)
            ratios.append(big_time / small_time)
        ratio = min(ratios)

        assert ratio < ceiling, (
            f"{factor}x the input cost {ratio:.0f}x the time (n={small_n:,} -> {big_n:,}, "
            f"{name}, the best of {rounds} rounds of {reps} runs a side). The two timed shapes "
            f"above have k = 1 and k = 201, the two ends of the range the constraints allow; this "
            f"one has k = {len(set(small))}, and the work done per element grows with the length "
            f"of the list on it. If the guards above passed and this one did not, the loop has a "
            f"step that is O(1) only when the runs are all the same length or all one value -- "
            f"look for del nums[i], nums.pop(i), nums.remove(x), `in`, .index() or .count() on a "
            f"path that a run of length one or a single distinct value happens to skip."
        )


# ---------------------------------------------------------------------------------------
# What this suite does NOT check, and why none of it is an oversight.
#
# len(nums) AFTER THE CALL. Only `len(nums) >= k` is enforced. The problem asks for k and for the
# first k slots, and says the elements beyond index k - 1 can be ignored; it says nothing at all
# about how long the list ends up. Both of these are accepted, and both must stay accepted:
#
#     nums[:] = sorted(set(nums)); return len(nums)      -- shrinks nums to exactly k
#     a write cursor over nums, returning the cursor     -- leaves len(nums) as it arrived
#
# Requiring the length to be unchanged would fail the first, which is a perfectly good answer,
# and requiring it to equal k would fail the second, which is the one the chapter is aiming at.
# The suite therefore checks the only thing the problem needs: that the first k slots exist and
# hold the right values. The sibling suite for 27 reaches the same conclusion from a statement
# that spells it out ("the size of nums is not important"); the wording here is quieter, but it
# grants exactly as much.
#
# THE TAIL. `_check` slices nums[:k] and never looks past it, because nothing reads past it.
#
# EXTRA SPACE. Not measured at all. Nothing in the problem constrains it, and a suite that
# demanded O(1) here would fail the slice assignment above for a property nobody asked for.
# Chapter 2's suite for 88 carries a longer note about the version of that mistake it had to
# have removed. Chapter 5 is where constant extra space becomes the actual subject.
#
# WHICH ROUTE THE SOLUTION TOOK. There is no static check on set(), sorted(), dict.fromkeys or a
# comprehension, and there should not be. The contract is the answer, not the method; the timing
# guards reject the shapes that are too slow, and the shapes that are fast enough are all
# accepted whatever they are made of.
#
# TIME is checked, and that one IS an addition: the problem states no complexity requirement, and
# at n = 3 * 10^4 a del per duplicate finishes a single call in 149 ms, which no judge would
# reject. The spec file the reader works from states the O(n) target outright, so it is a
# published requirement of this exercise rather than a hidden one, and it is the whole point of
# the chapter. The suite for 27 holds the same line for the same reason.
# ---------------------------------------------------------------------------------------
