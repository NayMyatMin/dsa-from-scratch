"""Spec for 27. Remove Element.

Chapter 2's problems returned nothing and left their answer in the list. This one does both at
once: it writes into `nums` *and* returns a number, and the two have to agree with each other.
Five contracts are enforced here.

1. `removeElement` returns k, an int -- the count of elements not equal to `val`. A list is not
   an int, a float is not an int, and neither is True: bool is a subclass of int in Python, so
   `isinstance(k, int)` alone would let `True` through as 1, and this suite rejects it explicitly.
2. The first k slots of `nums` hold exactly the elements not equal to `val`, IN ANY ORDER. The
   judge sorts the first k before it compares them, so this suite sorts too. Any arrangement of
   the right values passes; a right-looking arrangement of the wrong values does not.
3. `nums` itself is what gets read. Returning the right k while leaving `nums` alone fails, and
   so does building the right list somewhere else and handing it back.
4. len(nums) >= k, and that is the whole of the length contract. The problem says outright that
   the size of `nums` is not important, so this suite lets it be anything with room for the
   answer. Shrinking the list until only the survivors are left and returning how many there are
   is a legitimate way to solve this, and it MUST pass here; so is leaving the list exactly as
   long as it arrived. Only k slots are ever read.
5. n = 100, the constraint ceiling, and the shape of the work below it.

What this suite deliberately does NOT police, because the problem deliberately does not ask:

  the tail        Nothing past index k - 1 is ever read. Not by the judge, not here. Leave
                  copies of the removed value there, leave the original values, leave anything --
                  `_check` slices `nums[:k]` and never looks further.
  the order       Within the first k, every arrangement is equally right. `_check` sorts before
                  comparing, exactly as the judge does. `test_the_grader_matches_the_judge`
                  below pins that down by feeding the grader legal and illegal after-states
                  directly, so the contract is checked rather than described.
  the length      See contract 4. The problem calls the size of `nums` unimportant in as many
                  words, so a solution may shrink it to k, leave it as long as it arrived, or
                  land anywhere between, and nothing here prefers one over another.
  extra space     Not measured at all. "In place" says where the answer is read from; it does
                  not forbid scratch space. A solution that builds the survivors as a separate
                  list and then puts them where the caller will read them is accepted. Chapter 5
                  is where constant extra space becomes the subject.

Time is policed, and the reason is worth explaining. The problem states no complexity requirement,
and with n <= 100 nothing the constraints allow is slow enough to fail on the submission page:
measured on this repo's interpreter, CPython 3.14.4, the quickest solutions measured here cost
1.16 us per call at n = 100 and the slowest quadratic shape costs 8.71 us, and both of those are
instant. A wall-clock budget at that size separates nothing, so the timing comes in two parts:
`test_constraint_ceiling` holds the real ceiling to a budget that only a catastrophe fails, and
`test_does_not_grow_quadratically` runs the same code at sizes this test picked for itself, where
the two shapes are unmistakable. The measured numbers behind both are in their docstrings.
"""

import random
import time
from collections.abc import Callable
from itertools import product

import pytest

from arrays101.ch03.p01_remove_element import Solution
from tests._reference.p01_remove_element import oracle


def solve(nums: list[int], val: int) -> object:
    """Run the solution and hand back its return value, which must be k."""
    return Solution().removeElement(nums, val)


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


def _check(probes: str, original: list[int], val: int, nums: list[int], returned: object) -> None:
    """Assert the whole contract for one call, exactly as the judge would.

    `original` is a pristine snapshot taken before the call; `nums` is the list the solution was
    handed. The answer key is computed from the snapshot, so a solution cannot rewrite its own
    answer key.
    """
    expected = oracle(original, val)
    where = f"{probes}: removeElement({_render(original)}, {val})"

    if isinstance(returned, bool) or not isinstance(returned, int):
        raise AssertionError(
            f"{where} returned {_render(returned)}. It must return k, the number of elements "
            f"not equal to {val} -- an int, and the count itself, not the values, not a float "
            f"and not a truth value. The values go in the front of nums; the count comes back."
        )
    if returned != len(expected):
        detail = ""
        if returned == len(original) - len(expected):
            detail = (
                ". That is how many elements were removed. k is the number of elements that "
                "survive -- what is left, not what went"
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

    got = sorted(nums[:k])
    if got != expected:
        detail = ""
        if nums == original:
            detail = (
                ". nums came back exactly as it was handed over, so nothing was written into it "
                "at all. This problem is in place: the caller keeps a reference to this very "
                "list and reads the front of it, and a new list built somewhere else never "
                "reaches them"
            )
        elif sorted(x for x in nums if x != val) == expected:
            detail = (
                ". Every surviving value is still somewhere in nums -- they are just not in the "
                f"first {k} slots, which is the only region anyone reads"
            )
        elif val in nums[:k]:
            detail = f". nums[:{k}] still contains {val}"
        raise AssertionError(
            f"{where} returned {k} and left nums[:{k}] = {_render(nums[:k])}, want some "
            f"arrangement of {_render(expected)}{detail}. (Sorted before comparing, both here "
            f"and by the judge, so the order inside the first {k} slots is your business. The "
            f"full list afterwards was {_render(nums)}, and nothing past index {k - 1} is read.)"
        )


def _run(probes: str, nums: list[int], val: int) -> None:
    """Snapshot, call, check. The snapshot is the answer key; the solution never touches it."""
    original = list(nums)
    returned = solve(nums, val)
    _check(probes, original, val, nums, returned)


# ======================================================================================
# The grader itself, against the judge's rules.
# ======================================================================================


def test_the_grader_matches_the_judge() -> None:
    """What `_check` accepts and rejects, pinned down rather than asserted in a docstring.

    Every after-state below is one a solution could plausibly leave behind. The accepted ones
    are what "the first k in any order, the rest not important" actually permits, and it is
    worth seeing how much that is: the tail may hold the removed value itself, the list may keep
    its original length or lose it, and the survivors may be in any order at all.
    """
    original, val = [0, 1, 2, 2, 3, 0, 4, 2], 2  # five survivors: 0, 0, 1, 3, 4

    accepted: list[tuple[str, list[int], int]] = [
        ("survivors in their original order, tail untouched", [0, 1, 3, 0, 4, 0, 4, 2], 5),
        ("survivors in some other order, tail untouched", [4, 0, 3, 1, 0, 0, 4, 2], 5),
        ("survivors sorted", [0, 0, 1, 3, 4, 0, 4, 2], 5),
        ("tail full of the removed value", [0, 1, 3, 0, 4, 2, 2, 2], 5),
        ("tail full of junk", [0, 1, 3, 0, 4, 99, -7, 1000], 5),
        ("list shortened to exactly k", [0, 1, 3, 0, 4], 5),
        ("list shortened past the tail but not past k", [0, 1, 3, 0, 4, 2], 5),
    ]
    for probe, after, k in accepted:
        _check(f"grader self-test, accepted: {probe}", original, val, after, k)

    rejected: list[tuple[str, list[int], object]] = [
        ("k too small", [0, 1, 3, 0, 4, 2, 2, 2], 4),
        ("k too large", [0, 1, 3, 0, 4, 2, 2, 2], 6),
        ("count of what was removed", [0, 1, 3, 0, 4, 2, 2, 2], 3),
        ("nothing written into nums", list(original), 5),
        ("survivors pushed to the back", [2, 2, 2, 0, 1, 3, 0, 4], 5),
        ("a removed value left inside the first k", [0, 1, 2, 3, 0, 4, 2, 2], 5),
        ("a survivor duplicated inside the first k", [0, 1, 3, 0, 0, 4, 4, 2], 5),
        ("the list left shorter than k", [0, 1, 3, 0], 5),
        ("the answer returned instead of counted", [0, 1, 3, 0, 4, 2, 2, 2], [0, 1, 3, 0, 4]),
        ("k as a float", [0, 1, 3, 0, 4, 2, 2, 2], 5.0),
    ]
    for probe, after, k in rejected:
        with pytest.raises(AssertionError):
            _check(f"grader self-test, rejected: {probe}", original, val, after, k)

    # The bool rule needs an input of its own to be tested at all. bool is a subclass of int in
    # Python, so True would pass `isinstance(k, int)`; graded against the eight-element case above
    # it would also be the wrong count, and a case that fails for two reasons does not establish
    # either. This one has exactly one survivor, so 1 is the right answer and True is rejected
    # only for being a truth value where a count belongs.
    one, one_val, one_after = [1, 2, 2, 2], 2, [1, 2, 2, 2]
    _check("grader self-test, accepted: 1 for a single survivor", one, one_val, one_after, 1)
    with pytest.raises(AssertionError):
        _check("grader self-test, rejected: True in place of 1", one, one_val, one_after, True)


# ======================================================================================
# Hand-written cases. Each is (probe, nums, val, expected survivors sorted).
# ======================================================================================

Case = tuple[str, list[int], int, list[int]]

CASES: list[Case] = [
    # --- LeetCode's own examples ------------------------------------------------------------
    ("example 1", [3, 2, 2, 3], 3, [2, 2]),
    ("example 2", [0, 1, 2, 2, 3, 0, 4, 2], 2, [0, 0, 1, 3, 4]),
    # --- the empty list, which the constraints allow --------------------------------------
    ("empty list, val present nowhere", [], 0, []),
    ("empty list, val at the top of its range", [], 100, []),
    # --- single element ---------------------------------------------------------------------
    ("single element, removed", [7], 7, []),
    ("single element, kept", [7], 3, [7]),
    ("single element, val above every legal element", [50], 100, [50]),
    # --- everything goes ---------------------------------------------------------------------
    ("every element removed, length 2", [4, 4], 4, []),
    ("every element removed, length 8", [9] * 8, 9, []),
    ("every element removed, zeros", [0, 0, 0], 0, []),
    # --- nothing goes -------------------------------------------------------------------------
    ("val absent, distinct values", [1, 2, 3, 4, 5], 6, [1, 2, 3, 4, 5]),
    ("val absent, all identical", [8, 8, 8], 1, [8, 8, 8]),
    ("val absent and above the value range", [0, 25, 50], 51, [0, 25, 50]),
    # --- where the removed values sit ---------------------------------------------------------
    ("removed value only at the front", [5, 5, 1, 2, 3], 5, [1, 2, 3]),
    ("removed value only at the back", [1, 2, 3, 5, 5], 5, [1, 2, 3]),
    ("removed value only in the middle", [1, 5, 5, 2], 5, [1, 2]),
    ("removed value at both ends", [5, 1, 2, 5], 5, [1, 2]),
    ("removed value at every other index", [5, 1, 5, 2, 5, 3], 5, [1, 2, 3]),
    ("survivor at every other index", [1, 5, 2, 5, 3, 5], 5, [1, 2, 3]),
    # --- the survivor is the last thing the scan meets -----------------------------------------
    ("one survivor, at the very end", [2, 2, 2, 2, 7], 2, [7]),
    ("one survivor, at the very front", [7, 2, 2, 2, 2], 2, [7]),
    ("one survivor, in the middle", [2, 2, 7, 2, 2], 2, [7]),
    # --- duplicates among the survivors, which stay ---------------------------------------------
    ("survivors repeat", [1, 3, 1, 3, 1], 3, [1, 1, 1]),
    ("survivors all identical", [4, 4, 9, 4, 4], 9, [4, 4, 4, 4]),
    ("one value survives many times", [0, 1, 0, 1, 0, 1, 0], 1, [0, 0, 0, 0]),
    # --- long runs, where an index walked through a shrinking list goes wrong --------------------
    ("a run of two", [1, 5, 5, 2, 3], 5, [1, 2, 3]),
    ("a run of three", [1, 5, 5, 5, 2], 5, [1, 2]),
    ("two runs of two", [5, 5, 1, 5, 5, 2], 5, [1, 2]),
    ("a run at the end", [1, 2, 5, 5, 5, 5], 5, [1, 2]),
    ("runs on both sides of one survivor", [5, 5, 5, 1, 5, 5, 5], 5, [1]),
    # --- constraint extremes on the values -------------------------------------------------------
    ("value range, 0 removed", [0, 50, 0, 50], 0, [50, 50]),
    ("value range, 50 removed", [0, 50, 0, 50], 50, [0, 0]),
    ("val at the top of its own range", [0, 50, 25], 100, [0, 25, 50]),
    # --- long enough that an off-by-one at either end cannot hide --------------------------------
    ("24 elements, every third removed", [1, 2, 6] * 8, 6, [1] * 8 + [2] * 8),
    ("24 elements, only the first survives", [3] + [6] * 23, 6, [3]),
    ("24 elements, only the last survives", [6] * 23 + [3], 6, [3]),
    ("n = 100, the ceiling, alternating", [(i % 2) * 6 for i in range(100)], 6, [0] * 50),
    ("n = 100, the ceiling, nothing removed", [i % 51 for i in range(100)], 100,
     sorted(i % 51 for i in range(100))),
    ("n = 100, the ceiling, everything removed", [6] * 100, 6, []),
]


@pytest.mark.parametrize("probe,nums,val,expected", CASES)
def test_examples_and_edges(probe: str, nums: list[int], val: int, expected: list[int]) -> None:
    # The table's expected values are asserted against the reference as well, so a typo in a
    # hand-written case shows up as a broken test rather than as a wrong requirement.
    assert expected == oracle(nums, val), (
        f"the test case {probe!r} disagrees with the reference answer -- fix the table, "
        f"not the solution"
    )
    _run(probe, list(nums), val)


def test_cases_obey_the_stated_constraints() -> None:
    """The fixtures are held to the same contract the solution is.

    A case outside the constraints would demand something never asked for, and a solution that
    failed it would be right to. Checked rather than assumed: these cases are hand-written.
    """
    for probe, nums, val, expected in CASES:
        assert 0 <= len(nums) <= 100, f"[{probe}]: 0 <= nums.length <= 100"
        assert all(0 <= x <= 50 for x in nums), f"[{probe}]: 0 <= nums[i] <= 50"
        assert 0 <= val <= 100, f"[{probe}]: 0 <= val <= 100"
        assert expected == sorted(expected), f"[{probe}]: the answer key is kept sorted"


@pytest.mark.property
def test_every_small_arrangement() -> None:
    """Every list of length 0 to 6 over a three-value alphabet, against four values of val.

    Exhaustive, so nothing here is left to chance: the empty list, lists with no occurrence of
    val, lists that are nothing but val, every position and every run length in between, and a
    val that never appears in the alphabet at all.
    """
    for n in range(7):
        for tup in product((0, 1, 2), repeat=n):
            for val in (0, 1, 2, 3):
                nums = list(tup)
                _run(f"exhaustive n={n}, nums={nums}, val={val}", nums, val)


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    """Random lists, graded against the reference, inside the stated constraints.

    The two ranges are not the same: nums[i] stops at 50 while val runs to 100, so a val above
    50 is one that cannot occur in nums at all. That is a legal input and a different case from a
    val that is merely absent by chance, and both are generated here. Neither is allowed to put an
    out-of-range value into nums, which is why the planted value is drawn separately: a solution is
    entitled to rely on 0 <= nums[i] <= 50, and one that indexes a 51-slot table by element would
    be broken by a fixture that ignored the constraint, not by anything the problem asks of it.
    """
    rng = random.Random(27)
    for _ in range(2000):
        n = rng.randint(0, 100)
        val = rng.randint(0, 50) if rng.random() < 0.85 else rng.randint(51, 100)
        planted = val if val <= 50 else rng.randint(0, 50)
        # Vary how common the planted value is, so untouched, half-eaten and wholly-eaten lists
        # all get covered. The alphabet is narrow so that survivors repeat often.
        p = rng.choice([0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0])
        nums = [planted if rng.random() < p else rng.randint(0, 50) for _ in range(n)]
        assert all(0 <= x <= 50 for x in nums), "the generator itself must obey the constraints"
        _run(f"random n={n}, val={val}, density {p}", nums, val)


@pytest.mark.property
def test_every_length_up_to_the_ceiling() -> None:
    """All 101 legal lengths, in six shapes each.

    The exhaustive test above stops at 6 and the timing guards below start at 100, and a gap
    like that is somewhere for a bug to live: a solution that handles a leftover tail separately
    can be right on every tiny length, right again on a round 100, and wrong on 37. There are
    only 101 legal lengths here, so there is no reason to sample them -- take all of them.
    """
    rng = random.Random(2727)
    for n in range(101):
        _run(f"n={n}, every element removed", [6] * n, 6)
        _run(f"n={n}, nothing removed", [(i % 50) + 1 for i in range(n)], 0)
        _run(f"n={n}, alternating, removed first", [6 if i % 2 == 0 else 1 for i in range(n)], 6)
        _run(f"n={n}, alternating, removed last", [6 if i % 2 else 1 for i in range(n)], 6)
        _run(f"n={n}, removed only in the last tenth",
             [6 if i >= n - n // 10 else 1 for i in range(n)], 6)
        _run(f"n={n}, random", [rng.choice([6, 6, rng.randint(0, 50)]) for _ in range(n)], 6)


# ======================================================================================
# Timing guards.
# ======================================================================================

CEILING = 100  # the constraint ceiling: 0 <= nums.length <= 100

VAL = 5  # the value the timed shapes below remove


def _all_val(n: int, seed: int) -> list[int]:
    """The shape where every element goes. Nothing survives, so nothing has to be kept."""
    return [VAL] * n


def _half_val(n: int, seed: int) -> list[int]:
    """Half the elements go, so every removal has survivors sitting behind it."""
    rng = random.Random(seed)
    return [VAL if rng.random() < 0.5 else rng.randint(0, 50) for _ in range(n)]


def _no_val(n: int, seed: int) -> list[int]:
    """The shape where nothing goes. val never occurs, so every element is a survivor.

    Legal input, and not a corner case: 0 <= val <= 100 while 0 <= nums[i] <= 50, so any val
    above 50 removes nothing by construction. The two shapes above are both built with val
    present, which leaves a solution whose cost depends on val being there measured entirely on
    its other branch.
    """
    rng = random.Random(seed)
    pool = [x for x in range(51) if x != VAL]
    return [rng.choice(pool) for _ in range(n)]


TIMED_SHAPES: tuple[tuple[str, Callable[[int, int], list[int]]], ...] = (
    ("every element equal to val", _all_val),
    ("half the elements equal to val", _half_val),
    ("no element equal to val", _no_val),
)


@pytest.mark.slow
def test_constraint_ceiling() -> None:
    """n = 100, the largest input the constraints allow, against a wall-clock budget.

    A single call at the ceiling is over in a microsecond or two, far too quick to measure
    against machine noise, so the budget covers 2,000 of them. Measured on this repo's
    interpreter, CPython 3.14.4, best of five rounds over the 2,000 cases below. The first row is
    eight solutions that never move the tail of the list once per occurrence, spread across the
    range shown; the rest each do:

        the eight, as a band                    2.32 - 6.52 ms    1.16 - 3.26 us per call
        one list-level deletion per occurrence,
          scanning backwards                            3.29 ms          1.65 us per call
        taking elements off the front one at a time     5.65 ms          2.83 us per call
        searching out each occurrence with .index()
          and lifting it out where it stands           11.55 ms          5.77 us per call
        calling .remove(val) until it raises           17.42 ms          8.71 us per call
        ------------------------------------------------------------------ budget: 150 ms

    Every one of those is under the budget, and that is the honest situation: with n <= 100 the
    whole field fits inside a factor of eight, and no wall-clock budget can be tight enough to
    separate them and loose enough to be reliable. The budget is a floor, not a filter -- work
    that is not merely quadratic but catastrophic lands far outside it. It sits at 23x the
    slowest of the eight, and that margin is deliberate: the same measurement taken with eight
    processes running it at once, on a ten-core machine with nothing left to give, put that
    solution between 6.67 ms and 9.54 ms -- still 16x inside the budget. The guard that sees
    algorithm shape is the next one, and it has to invent its own sizes.

    The correctness half of this test is not a formality. It runs 2,000 cases at the ceiling in
    shapes the random test does not weight towards, and a wrong answer here is reported as a
    wrong answer rather than as a slow one.
    """
    rng = random.Random(127)
    cases: list[tuple[list[int], int]] = []
    for i in range(2_000):
        n = CEILING if i % 4 else rng.randint(90, CEILING)
        val = rng.randint(0, 50)
        p = rng.choice([0.0, 0.25, 0.5, 0.75, 1.0])
        cases.append(([val if rng.random() < p else rng.randint(0, 50) for _ in range(n)], val))

    for i, (nums, val) in enumerate(cases):
        _run(f"ceiling case {i}, n={len(nums)}, val={val}", list(nums), val)

    budget = 0.150
    fastest = float("inf")
    for _ in range(5):
        fresh = [(list(nums), val) for nums, val in cases]
        remove_element = Solution().removeElement
        start = time.perf_counter()
        for nums, val in fresh:
            remove_element(nums, val)
        fastest = min(fastest, time.perf_counter() - start)

    assert fastest < budget, (
        f"{len(cases):,} calls at the ceiling (n = {CEILING}) took {fastest * 1e3:.0f}ms, over "
        f"the {budget * 1e3:.0f}ms budget: {fastest / len(cases) * 1e6:.1f}us per call, against "
        f"the 1.2us a single pass over 100 elements costs here. Something inside the loop is "
        f"doing work that grows with the length of the list rather than a fixed amount."
    )


# --- the growth guard's measuring apparatus -------------------------------------------------
#
# Every call needs a list of its own, since the solution rewrites what it is given, so the copy
# is made inside the measured region. That is deliberate, and it cannot bend the result: list(data)
# measured 4.13 us at n = 4,000 and 28.95 us at n = 32,000, which is 7.02x for eight times the
# data -- itself linear, and if anything flattening slightly at the larger size. It is at most 21%
# of a sample here (20.6% at n = 4,000 and 18.3% at n = 32,000 for the quickest solution measured,
# and under 10% for most of them). A term that is itself linear cannot disguise growth in the term
# beside it. What the copy buys is that memory stays at two lists however many repetitions get
# taken, and that a solution is never timed against a list some earlier call already emptied.

GROWTH_CEILING = 25.0  # the ratio a solution may not exceed; see test_does_not_grow_quadratically
SMALL_N, FACTOR = 4_000, 8
BATCH_TARGET = 0.003  # seconds; how long one timed sample must last


def _seconds_per_call(data: list[int], batch: int) -> float:
    """Seconds per call, averaged over `batch` calls, each on a fresh copy of `data`."""
    start = time.perf_counter()
    for _ in range(batch):
        c = list(data)
        solve(c, VAL)
    return (time.perf_counter() - start) / batch


def _batch_size(data: list[int]) -> int:
    """The smallest power-of-two batch whose run lasts at least BATCH_TARGET seconds.

    One call at n = 4,000 takes tens of microseconds, and a sample that short is not a
    measurement of the code -- it is a measurement of what else the machine was doing during it.
    Timing a batch and dividing is what makes the number hold up when the machine is busy.
    Measured on this interpreter, twenty rounds of a best-of-nine floor for one correct solution
    on the all-val shape at n = 4,000, on a quiet machine and then with seven copies of the same
    measurement competing for ten cores (140 rounds pooled across the seven):

                                   quiet machine              seven at once
        one call per sample        18.38 - 18.50 us  1.01x    17.54 - 58.75 us   3.35x
        a batch of 128 per sample  20.50 - 20.52 us  1.00x    19.52 - 30.05 us   1.54x

    All four rows measure the same code, and on an idle machine the batch buys nothing at all --
    a single call is already steady to within 1%. The column that matters is the second. A single
    call is short enough to be swallowed whole by one scheduling burst, and once that happens the
    floor is 3.3x the truth; spread over a batch the same burst is diluted to 1.5x. A ratio is
    built from two of these numbers, so whatever the noise can do to one of them, it can do twice.
    """
    batch = 1
    while batch < 8192 and _seconds_per_call(data, batch) * batch < BATCH_TARGET:
        batch *= 2
    return batch


def _growth_ratio(small: list[int], big: list[int], reps: int = 9) -> float:
    """How much more one call costs at 8n than at n, as the ratio of two floor measurements.

    Both sides get the same number of repetitions and the two are interleaved, and both of those
    matter. A best-of-N time is a floor -- interference only ever makes a run slower, so the
    fastest run is the closest thing to a clean measurement -- and a side sampled fewer times can
    miss its floor and inflate the ratio all by itself. Interleaving handles the slower drift the
    repetitions cannot: this machine has four performance cores and six efficiency ones and moves
    a process between them, and a side measured entirely inside one of those windows is measuring
    the core rather than the code. Measured on five correct solutions across both shapes, 300
    readings of each arrangement on a quiet machine:

                                                                  median    worst
        one call per sample, sides measured one after the other     7.97x   17.63x
        batched samples, sides measured one after the other         8.11x   16.51x
        batched samples, sides interleaved                          8.03x    9.50x

    All three agree on the median, near 8x. Only the third has a tail that stays there, and the
    tail is the whole question: a ceiling has to clear the worst reading a correct solution
    produces, not its typical one. Under load the third widens without coming apart -- 320
    interleaved readings taken with eight processes competing for ten cores reached 15.30x, and
    336 taken with twelve produced nothing above 11.76x, with no reading in either run over 25x.
    Against that, the lowest reading any tail-moving solution produced anywhere was 55.29x. The
    ceiling below sits in that gap, and a reading over it is taken again rather than believed.

    The early exit keeps nine repetitions from being slow to fail. Once three pairs are in and
    the big side is past the ceiling with 50 ms of headroom on top, more repetitions cannot bring
    it back. The 50 ms is flat rather than proportional so that a verdict is never reached on the
    strength of microseconds of interference between two sub-millisecond numbers: the slowest
    correct solution measured 1.41 ms per sample at n = 32,000, against a threshold that starts at
    50 ms, so it never trips. What trips it is a call costing a tenth of a second.
    """
    small_batch, big_batch = _batch_size(small), _batch_size(big)
    best_small = best_big = float("inf")
    for taken in range(1, reps + 1):
        best_small = min(best_small, _seconds_per_call(small, small_batch))
        best_big = min(best_big, _seconds_per_call(big, big_batch))
        if taken >= 3 and best_big > GROWTH_CEILING * best_small + 0.050:
            break
    return best_big / best_small


@pytest.mark.slow
def test_does_not_grow_quadratically() -> None:
    """Eight times the input should cost about eight times the work, on three shapes.

    These sizes run far past the stated n <= 100, on purpose. A hundred elements is simply too
    few for a clock to tell one shape from another -- see the budget above, where the whole field
    fits inside a factor of eight. The code under test does not change with the size, so running
    it larger makes the same shape visible with no ambiguity left in it.

    Measured on this repo's interpreter, CPython 3.14.4, n = 4,000 then 32,000, fifteen readings
    of each solution on each shape. Eight solutions that never move the tail of the list once per
    occurrence are given as a band, since what matters about them is that they land together; the
    ones that do move it are named, because those are the shapes this guard exists to catch.
    Medians, with the full range of the fifteen readings in brackets:

        every element equal to val
            the eight, as a band                 7.90x - 8.03x   [ 7.55x -   8.31x]
            one list-level deletion per
              occurrence, scanning backwards              8.08x  [ 8.00x -   8.11x]  <- see below
            ---------------------------------------------------------- ceiling: 25x
            .index() each occurrence, then delete it     65.71x  [61.80x -  81.93x]
            taking elements off the front one at a time  89.36x  [89.22x - 102.91x]
            calling .remove(val) until it raises        116.56x  [107.15x - 164.12x]

        half the elements equal to val
            seven of the eight                   7.80x - 9.06x   [ 7.71x -   9.26x]
            the eighth, which sorts the list
              before keeping the survivors               10.68x  [10.38x -  10.95x]
            ---------------------------------------------------------- ceiling: 25x
            one list-level deletion per
              occurrence, scanning backwards             55.47x  [55.29x -  55.57x]
            calling .remove(val) until it raises         69.07x  [68.29x -  70.11x]
            .index() each occurrence, then delete it     85.19x  [84.56x -  89.17x]
            taking elements off the front one at a time 153.50x  [95.24x - 163.48x]

        no element equal to val
            four solutions, as a band            7.66x - 8.09x   [ 7.61x -   8.21x]
            the one that sorts the list
              before keeping the survivors               11.75x  [11.05x -  12.12x]
            ---------------------------------------------------------- ceiling: 25x
            growing the kept list by rebinding it
              once per element                           70.45x  [65.22x -  89.51x]

    A quadratic solution lands near 64x and most of the ones above land higher still, because the
    pass they make per element is a C-level move of the whole tail on top of the Python-level loop
    they were already paying for. Across every reading taken here, the lowest any of them produced
    was 55.29x, and the highest any correct solution produced was 15.30x -- that one under an
    eight-way load, 10.95x being the worst on a quiet machine. The ceiling sits between those,
    nearer the bottom of the gap than the middle, because a correct solution being failed is a
    worse outcome here than a slow one being let through -- and a slow one still has the budget
    above, and a submission page, to get past.

    The second shape is not decoration, and the arrow above says why. Deleting the *last* element
    of a list is cheap -- there is nothing behind it to move up -- so a solution that deletes one
    element at a time, scanning backwards, measured 8.08x on the array where everything goes,
    right inside the band the correct solutions occupy, and 55.47x as soon as the elements it
    removes have survivors sitting behind them. A list of a single repeated value is the easiest
    input in the world to be accidentally fast on.

    The third shape removes nothing at all, and it is there for the mirror image of that argument.
    The first two shapes both contain val -- at 100% and at 50% -- so a solution that takes one
    path when val is present and another when it is not is only ever measured on the first path.
    Every quadratic shape named above collapses to between 7.9x and 8.1x here, because with
    nothing to remove there is nothing quadratic left for them to do; what this shape catches
    instead is quadratic work done per *survivor*, which is at its worst exactly where the other
    two are at their weakest. Growing the kept list by rebinding it once per element measures
    8.04x where every element goes and 8.23x where half do -- inside the band, on both -- and
    70.45x here. A val that never occurs is not a corner case either: 0 <= val <= 100 while
    0 <= nums[i] <= 50, so every val above 50 is one of these, and "a fixed amount of work per
    element, whatever val is and however often it occurs" includes occurring zero times.

    Sorting the list before keeping the survivors is the one correct shape that separates the
    measurements in the other direction: 7.91x where every element is equal, 10.68x where half
    are and 11.75x where none are, since sorting has real work to do in proportion to how much
    of the list survives. It is n log n rather than n, it is well inside the ceiling at all three
    sizes, and nothing here asks it to be anything else. It is also the closest any correct
    solution comes to the ceiling on the third shape, and 12.12x was the worst of fifteen
    readings there against a ceiling of 25x.

    A ratio over the ceiling is measured again before it is reported, up to three times in all,
    and only fails if every attempt agrees. The re-measurement is for the machine's benefit, not
    the solution's: the excursions above are rare and uncorrelated, so three in a row is not
    something a correct solution runs into, while a genuinely quadratic one is over the ceiling
    every single time. A ratio past twice the ceiling is not re-measured at all -- nothing that
    far out is noise -- which is what keeps the slowest solutions from taking three times as long
    to be told they are slow.
    """
    attempts = 3
    for name, make in TIMED_SHAPES:
        small, big = make(SMALL_N, 1), make(SMALL_N * FACTOR, 2)

        # Correctness at the larger of the two timed sizes, checked once and outside the timing.
        # A wrong answer should say it is wrong, not that it is slow.
        _run(f"n={SMALL_N * FACTOR:,}, {name}", list(big), VAL)

        seen: list[float] = []
        for _ in range(attempts):
            seen.append(_growth_ratio(small, big))
            if seen[-1] < GROWTH_CEILING or seen[-1] > 2 * GROWTH_CEILING:
                break

        readings = ", ".join(f"{r:.0f}x" for r in seen)
        assert min(seen) < GROWTH_CEILING, (
            f"{FACTOR}x the input cost {min(seen):.0f}x the time (n={SMALL_N:,} -> "
            f"{SMALL_N * FACTOR:,}, {name}; measured {readings}). A single pass lands near "
            f"{FACTOR}x; {min(seen):.0f}x means the work done per element grows with the length "
            f"of the list. The algorithm may well be right -- look instead for a step inside the "
            f"loop that is not O(1). del nums[i], nums.pop(i), nums.remove(x) and nums.insert("
            f"i, x) all move every element past the position they touch; `in`, .index() and "
            f".count() walk the list; slicing copies it. Each of those is O(n) on its own, and "
            f"doing one per element is the entire cost."
        )
