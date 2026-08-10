"""Spec for 1295. Find Numbers with Even Number of Digits."""

import random

import pytest

from arrays101.ch01.p02_find_numbers_even_digits import Solution


def solve(nums: list[int]) -> int:
    return Solution().findNumbers(nums)


def oracle(nums: list[int]) -> int:
    return sum(1 for x in nums if len(str(x)) % 2 == 0)


@pytest.mark.parametrize(
    "nums,expected",
    [
        # --- LeetCode's own examples -------------------------------------------------
        ([12, 345, 2, 6, 7896], 2),
        ([555, 901, 482, 1771], 1),
        # --- single element, each digit count ----------------------------------------
        ([1], 0),  # 1 digit  -> odd
        ([10], 1),  # 2 digits -> even
        ([100], 0),  # 3 digits -> odd
        ([1000], 1),  # 4 digits -> even
        ([10000], 0),  # 5 digits -> odd
        ([100000], 1),  # 6 digits -> even, and the constraint ceiling (10^5)
        # --- every power-of-ten boundary, from both sides ----------------------------
        ([9, 10], 1),
        ([99, 100], 1),
        ([999, 1000], 1),
        ([9999, 10000], 1),
        ([99999, 100000], 1),
        # --- all even / all odd ------------------------------------------------------
        ([10, 11, 1000, 9999], 4),
        ([1, 9, 100, 99999], 0),
        # --- duplicates count separately ---------------------------------------------
        ([12, 12, 12], 3),
        # --- a full sweep of digit lengths in one array ------------------------------
        ([1, 12, 123, 1234, 12345, 100000], 3),
    ],
)
def test_examples_and_edges(nums: list[int], expected: int) -> None:
    original = list(nums)
    assert solve(nums) == expected
    assert nums == original, "this problem is read-only; don't mutate the input"


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    rng = random.Random(1295)
    for _ in range(2000):
        n = rng.randint(1, 60)
        nums = [rng.randint(1, 100_000) for _ in range(n)]
        assert solve(nums) == oracle(nums), f"disagreed on {nums}"


@pytest.mark.property
def test_clusters_around_boundaries() -> None:
    """Random values are almost never near a power of ten. Force the issue."""
    rng = random.Random(7)
    boundaries = [10**k for k in range(6)]
    for _ in range(2000):
        nums = []
        for _ in range(rng.randint(1, 30)):
            b = rng.choice(boundaries)
            nums.append(max(1, min(100_000, b + rng.randint(-2, 2))))
        assert solve(nums) == oracle(nums), f"disagreed on {nums}"


@pytest.mark.slow
def test_full_domain() -> None:
    """Every legal value of nums[i], 1 through 10^5, checked at once."""
    domain = list(range(1, 100_001))
    assert solve(domain) == oracle(domain)
