"""Spec for 1295. Find Numbers with Even Number of Digits."""

import random
import time

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
    result = solve(nums)
    # `type(...) is int`, not isinstance: bool is a subclass of int, and True == 1,
    # so an isinstance check would wave through a returned True on the ([10], 1) case.
    assert type(result) is int, (
        f"findNumbers must return an int, got {type(result).__name__} ({result!r}). "
        "A float or a bool compares equal to the right answer but is the wrong type."
    )
    assert result == expected
    assert nums == original, "this problem is read-only; don't mutate the input"


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    rng = random.Random(1295)
    for _ in range(2000):
        n = rng.randint(1, 60)
        nums = [rng.randint(1, 100_000) for _ in range(n)]
        original = list(nums)
        expected = oracle(original)  # from the pristine copy, so a mutating
        assert solve(nums) == expected, f"disagreed on {original}"  # solution can't
        assert nums == original, (  # rewrite its own answer key
            f"this problem is read-only; don't mutate the input. Was {original}, "
            f"became {nums}"
        )


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
        original = list(nums)
        expected = oracle(original)
        assert solve(nums) == expected, f"disagreed on {original}"
        assert nums == original, (
            f"this problem is read-only; don't mutate the input. Was {original}, "
            f"became {nums}"
        )


@pytest.mark.slow
def test_full_domain() -> None:
    """Every legal value of nums[i], 1 through 10^5, checked at once.

    Shuffled rather than ascending, for two reasons: an ordered domain groups the
    digit lengths into six contiguous blocks, and it is already sorted, which would
    make an in-place ``sort()`` by the solution invisible to the read-only check.
    """
    domain = list(range(1, 100_001))
    random.Random(100_000).shuffle(domain)
    original = list(domain)
    expected = oracle(original)

    start = time.perf_counter()
    result = solve(domain)
    elapsed = time.perf_counter() - start

    assert type(result) is int, (
        f"findNumbers must return an int, got {type(result).__name__} ({result!r})."
    )
    assert result == expected
    assert domain == original, "this problem is read-only; don't mutate the input"
    # This is what the `slow` marker is actually for. A single pass over the domain
    # costs well under a tenth of a second; the ceiling is hundreds of times that, so
    # it cannot fire on a linear solution however loaded the machine is. It fires on a
    # quadratic one, which needs tens of seconds here.
    assert elapsed < 5.0, (
        f"correct, but took {elapsed:.1f}s on {len(original):,} values. One pass should "
        "take a small fraction of a second. Something is re-scanning the whole array for "
        "each element -- .index(), `x in nums`, .count(), or a nested loop -- which makes "
        "the whole thing quadratic."
    )
