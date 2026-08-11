"""Spec for 485. Max Consecutive Ones.

Three contracts are enforced here, not one:

1. the returned value is the length of the longest run of 1s;
2. `nums` comes back exactly as it was handed over — this problem is read-only;
3. n = 10^5 finishes inside a wall-clock budget, so a quadratic scan fails here
   rather than on the submission page.
"""

import random
import time

import pytest

from arrays101.ch01.p01_max_consecutive_ones import Solution
from tests._reference.p01_max_consecutive_ones import oracle


def solve(nums: list[int]) -> int:
    return Solution().findMaxConsecutiveOnes(nums)


@pytest.mark.parametrize(
    "nums,expected",
    [
        # --- LeetCode's own examples -------------------------------------------------
        ([1, 1, 0, 1, 1, 1], 3),
        ([1, 0, 1, 1, 0, 1], 2),
        # --- single element ----------------------------------------------------------
        ([1], 1),
        ([0], 0),
        # --- degenerate arrays -------------------------------------------------------
        ([1, 1, 1, 1, 1], 5),
        ([0, 0, 0, 0, 0], 0),
        # --- where the winning run sits ----------------------------------------------
        ([1, 1, 1, 0, 1], 3),  # at the start
        ([1, 0, 1, 1, 1], 3),  # at the end  <- the classic off-by-one lives here
        ([0, 1, 1, 1, 0], 3),  # in the middle
        ([0, 0, 1], 1),  # at the very end, length 1
        ([1, 0, 0, 0], 1),  # at the very start, length 1
        # --- ties: two runs of equal length ------------------------------------------
        ([1, 1, 0, 1, 1], 2),
        # --- alternating -------------------------------------------------------------
        ([1, 0, 1, 0, 1, 0], 1),
        ([0, 1, 0, 1, 0, 1], 1),
        # --- a later run beats an earlier one, and vice versa ------------------------
        ([1, 1, 0, 1, 1, 1, 1], 4),
        ([1, 1, 1, 1, 0, 1, 1], 4),
        # --- long enough that a length-gated shortcut cannot hide behind them --------
        ([1, 1, 1, 0] * 6, 3),  # 24 elements, six identical runs
        ([0] * 20 + [1] * 5, 5),  # 25 elements, winning run at the very end
    ],
)
def test_examples_and_edges(nums: list[int], expected: int) -> None:
    original = list(nums)
    got = solve(nums)
    assert nums == original, f"this problem is read-only; {original} came back as {nums}"
    assert got == expected, f"{original} -> got {got}, want {expected}"


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    rng = random.Random(485)
    for _ in range(2000):
        n = rng.randint(1, 40)
        # Vary the density of 1s so we cover sparse, balanced, and dense arrays.
        p = rng.choice([0.1, 0.3, 0.5, 0.7, 0.9])
        nums = [1 if rng.random() < p else 0 for _ in range(n)]
        # Grade against a snapshot, never against the list the solution was
        # handed. A solution that rewrites `nums` must not get to be marked
        # against the array it just rewrote.
        original = list(nums)
        got = solve(nums)
        assert nums == original, f"this problem is read-only; mutated {original}"
        assert got == oracle(original), f"disagreed on {original}"


@pytest.mark.slow
def test_large_input() -> None:
    """n = 10^5, the constraint ceiling.

    All 1s is the worst case for a solution that restarts the count at every
    index. A single pass gets through it in hundredths of a second, so the
    budget below is generous by two orders of magnitude. Blow it and the shape
    of your solution is quadratic — which is exactly what a LeetCode "Time
    Limit Exceeded" would be telling you.
    """
    ones = [1] * 100_000
    original = list(ones)
    start = time.perf_counter()
    got = solve(ones)
    elapsed = time.perf_counter() - start
    assert ones == original, "this problem is read-only; don't mutate the input"
    assert got == 100_000, f"all 1s, n=10^5 -> got {got}, want 100000"
    assert elapsed < 2.0, (
        f"n=10^5 of all 1s took {elapsed:.1f}s. A single pass does this in "
        "hundredths of a second; this is the shape of a Time Limit Exceeded."
    )

    rng = random.Random(0)
    nums = [rng.randint(0, 1) for _ in range(100_000)]
    original = list(nums)
    got = solve(nums)
    assert nums == original, "this problem is read-only; don't mutate the input"
    assert got == oracle(original), f"n=10^5 random -> got {got}, want {oracle(original)}"
