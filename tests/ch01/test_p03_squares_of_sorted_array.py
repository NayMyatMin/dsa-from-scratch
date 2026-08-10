"""Spec for 977. Squares of a Sorted Array.

Both methods are held to the same correctness bar. `sortedSquares` is additionally held to the
follow-up's constraint: no sorting.
"""

import ast
import inspect
import random
import textwrap

import pytest

from arrays101.ch01.p03_squares_of_sorted_array import Solution

CASES: list[tuple[list[int], list[int]]] = [
    # --- LeetCode's own examples ---------------------------------------------------
    ([-4, -1, 0, 3, 10], [0, 1, 9, 16, 100]),
    ([-7, -3, 2, 3, 11], [4, 9, 9, 49, 121]),
    # --- single element --------------------------------------------------------------
    ([0], [0]),
    ([5], [25]),
    ([-5], [25]),
    # --- entirely one sign -----------------------------------------------------------
    ([1, 2, 3, 4], [1, 4, 9, 16]),  # all positive: already in order
    ([-4, -3, -2, -1], [1, 4, 9, 16]),  # all negative: exactly reversed
    # --- zeros -----------------------------------------------------------------------
    ([0, 0, 0], [0, 0, 0]),
    ([-2, 0, 2], [0, 4, 4]),
    ([-1, 0], [0, 1]),
    ([0, 1], [0, 1]),
    # --- symmetric: every square appears twice ---------------------------------------
    ([-3, -3, 3, 3], [9, 9, 9, 9]),
    ([-2, -1, 1, 2], [1, 1, 4, 4]),
    # --- the crossover sits at each possible position --------------------------------
    ([-1, 2, 3, 4], [1, 4, 9, 16]),
    ([-3, -2, -1, 4], [1, 4, 9, 16]),
    ([-4, -3, 2, 3], [4, 9, 9, 16]),
    # --- lopsided magnitudes: the big value is on the left ----------------------------
    ([-100, 1, 2], [1, 4, 10000]),
    ([-1, 2, 100], [1, 4, 10000]),
    # --- duplicates ------------------------------------------------------------------
    ([-2, -2, -2], [4, 4, 4]),
    ([1, 1, 1], [1, 1, 1]),
    # --- constraint extremes ----------------------------------------------------------
    ([-10_000, 10_000], [100_000_000, 100_000_000]),
]


def _sorting_call_in(fn) -> str | None:
    """Return the name of a sorting call in fn's body, or None.

    Walks the AST rather than grepping the text, so comments and docstrings that merely
    mention sorted() don't trip the guard.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "sorted":
            return f"{func.id}()"
        if isinstance(func, ast.Attribute) and func.attr in {"sort", "sortedSquaresNaive"}:
            return f".{func.attr}()"
    return None


@pytest.mark.parametrize("nums,expected", CASES)
def test_naive(nums: list[int], expected: list[int]) -> None:
    original = list(nums)
    assert Solution().sortedSquaresNaive(nums) == expected
    assert nums == original, "return a new list; don't mutate the input"


@pytest.mark.parametrize("nums,expected", CASES)
def test_linear(nums: list[int], expected: list[int]) -> None:
    original = list(nums)
    assert Solution().sortedSquares(nums) == expected
    assert nums == original, "return a new list; don't mutate the input"


def test_linear_does_not_sort() -> None:
    """The follow-up asks for O(n). Sorting is O(n log n), so it is off the table.

    min()/max() on two scalars stay legal — that's O(1) and shows up in a perfectly good
    linear solution. Only sorting the collection is banned.
    """
    found = _sorting_call_in(Solution.sortedSquares)
    assert found is None, (
        f"sortedSquares uses {found}. That's the naive approach — put it in "
        f"sortedSquaresNaive instead. The input is already sorted; the O(n) solution "
        f"exploits that ordering directly."
    )


@pytest.mark.property
@pytest.mark.parametrize("method", ["sortedSquaresNaive", "sortedSquares"])
def test_matches_oracle_on_random_inputs(method: str) -> None:
    solve = getattr(Solution(), method)
    rng = random.Random(977)
    for _ in range(2000):
        n = rng.randint(1, 40)
        # Narrow ranges force ties; wide ranges force big crossovers.
        lo = rng.choice([-10_000, -50, -5, 0])
        hi = rng.choice([0, 5, 50, 10_000])
        nums = sorted(rng.randint(lo, max(lo, hi)) for _ in range(n))
        assert solve(nums) == sorted(x * x for x in nums), f"disagreed on {nums}"


@pytest.mark.slow
@pytest.mark.parametrize("method", ["sortedSquaresNaive", "sortedSquares"])
def test_large_input(method: str) -> None:
    solve = getattr(Solution(), method)
    rng = random.Random(1)
    nums = sorted(rng.randint(-10_000, 10_000) for _ in range(10_000))
    assert solve(nums) == sorted(x * x for x in nums)
