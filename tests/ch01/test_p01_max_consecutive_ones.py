"""Spec for 485. Max Consecutive Ones."""

import random
from itertools import groupby

import pytest

from arrays101.ch01.p01_max_consecutive_ones import Solution


def solve(nums: list[int]) -> int:
    return Solution().findMaxConsecutiveOnes(nums)


def oracle(nums: list[int]) -> int:
    """Obviously-correct reference: longest run of 1s, via groupby."""
    runs = [len(list(g)) for k, g in groupby(nums) if k == 1]
    return max(runs, default=0)


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
    ],
)
def test_examples_and_edges(nums: list[int], expected: int) -> None:
    original = list(nums)
    assert solve(nums) == expected
    assert nums == original, "this problem is read-only; don't mutate the input"


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    rng = random.Random(485)
    for _ in range(2000):
        n = rng.randint(1, 40)
        # Vary the density of 1s so we cover sparse, balanced, and dense arrays.
        p = rng.choice([0.1, 0.3, 0.5, 0.7, 0.9])
        nums = [1 if rng.random() < p else 0 for _ in range(n)]
        assert solve(nums) == oracle(nums), f"disagreed on {nums}"


@pytest.mark.slow
def test_large_input() -> None:
    """n = 10^5, the constraint ceiling.

    All 1s is the worst case for a solution that restarts the count at every index.
    If this test hangs rather than fails, your solution is O(n^2) — that is exactly
    what a LeetCode "Time Limit Exceeded" would be telling you.
    """
    assert solve([1] * 100_000) == 100_000

    rng = random.Random(0)
    nums = [rng.randint(0, 1) for _ in range(100_000)]
    assert solve(nums) == oracle(nums)
