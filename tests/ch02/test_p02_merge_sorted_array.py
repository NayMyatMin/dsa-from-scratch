"""Spec for 88. Merge Sorted Array.

Chapter 1's problems were read-only, and every suite there asserted that the input came back
untouched. This one inverts that. `nums1` *is* the answer, so the input must change, and five
separate things have to be pinned down instead of one.

1. `merge` returns None. The caller reads `nums1` when the call comes back and never looks at
   the return value, so a solution that computes the right list and hands it over has not
   solved the problem. Together with (2) this cuts both ways: returning the answer without
   writing it into `nums1` fails, and so does writing it into `nums1` but returning it too.
2. `nums1` holds exactly the expected contents afterwards.
3. `len(nums1)` is still m + n. The trailing zeros are reserved room, not slack: a solution
   that appends and never trims, or deletes and never restores, fails here even when the
   values it leaves behind are in the right order.
4. `nums2` is untouched. It is an input, not scratch space.
5. `m` and `n` are the arguments, not something to be recovered from the lists. Zero is a legal
   value, so no amount of looking at the contents identifies the reserved room, and the traps
   below make that concrete.

The randomized tests grade against a pristine snapshot taken before the call, never against the
list the solution was handed. A solution that rewrites `nums1` must not get to be marked
against the array it has just rewritten.

The follow-up asks for O(m + n). A ceiling of m + n <= 200 is far too small for a clock to tell
one algorithm shape from another, so the timing comes in two parts: `test_constraint_ceiling`
holds the real ceiling to a wall-clock budget, and `test_does_not_grow_quadratically` runs the
same code at sizes where the shapes are unmistakable. The measured numbers behind both budgets
are in their docstrings.

What this suite deliberately does NOT police is how much scratch space you use. Merging into a
list of your own and copying it over is linear in time, correct, and accepted — the follow-up
asks about time, and "stored inside nums1" says where the answer goes, not what you may allocate
getting there. Solving it with no scratch array at all is a better answer and the tier-4 hint
says why, but it is an ambition rather than the spec, and chapter 5 is where constant extra
space becomes the actual subject. The comment at the foot of this file records an earlier
version of this suite that got that wrong.
"""

import random
import time

import pytest

from arrays101.ch02.p02_merge_sorted_array import Solution
from tests._reference.p02_merge_sorted_array import oracle

# A case is (probe, nums1, m, nums2, n, expected). `probe` says what the case is testing, and it
# is what names the case in a failure.
Case = tuple[str, list[int], int, list[int], int, list[int]]

BILLION = 10**9

CASES: list[Case] = [
    # --- LeetCode's own examples ---------------------------------------------------
    ("example 1, three and three", [1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3, [1, 2, 2, 3, 5, 6]),
    ("example 2, n = 0", [1], 1, [], 0, [1]),
    ("example 3, m = 0", [0], 0, [1], 1, [1]),
    # --- n = 0: nums1 already holds the answer, and must be left holding it ---------
    ("n = 0, several values in place", [4, 5, 6], 3, [], 0, [4, 5, 6]),
    ("n = 0, a real 0 in the data", [-9, -9, 0, 7], 4, [], 0, [-9, -9, 0, 7]),
    # --- m = 0: every slot in nums1 is reserved room --------------------------------
    ("m = 0, all values from nums2", [0, 0, 0], 0, [-1, 2, 2], 3, [-1, 2, 2]),
    ("m = 0 at the smallest legal size", [0], 0, [-BILLION], 1, [-BILLION]),
    # --- one element on each side ---------------------------------------------------
    ("one each, nums2 value smaller", [2, 0], 1, [1], 1, [1, 2]),
    ("one each, nums2 value larger", [1, 0], 1, [2], 1, [1, 2]),
    ("one each, values equal", [3, 0], 1, [3], 1, [3, 3]),
    # --- disjoint ranges, in both directions ----------------------------------------
    # Above: nothing already in place has to move. Below: all of it does.
    ("disjoint, nums2 entirely above", [1, 2, 3, 0, 0, 0], 3, [7, 8, 9], 3, [1, 2, 3, 7, 8, 9]),
    ("disjoint, nums2 entirely below", [7, 8, 9, 0, 0, 0], 3, [1, 2, 3], 3, [1, 2, 3, 7, 8, 9]),
    ("disjoint lopsided, nums1 largest", [9, 0, 0, 0], 1, [1, 2, 3], 3, [1, 2, 3, 9]),
    ("disjoint lopsided, nums1 smallest", [1, 0, 0, 0], 1, [7, 8, 9], 3, [1, 7, 8, 9]),
    ("ranges touch at a shared value", [1, 2, 5, 0, 0, 0], 3, [5, 6, 7], 3, [1, 2, 5, 5, 6, 7]),
    # --- fully interleaved: the answer alternates between the two sources ------------
    (
        "interleaved, nums1 supplies the first",
        [1, 3, 5, 7, 0, 0, 0, 0], 4, [2, 4, 6, 8], 4, [1, 2, 3, 4, 5, 6, 7, 8],
    ),
    (
        "interleaved, nums2 supplies the first",
        [2, 4, 6, 8, 0, 0, 0, 0], 4, [1, 3, 5, 7], 4, [1, 2, 3, 4, 5, 6, 7, 8],
    ),
    # --- duplicates ------------------------------------------------------------------
    ("every value identical", [5, 5, 5, 0, 0, 0], 3, [5, 5, 5], 3, [5, 5, 5, 5, 5, 5]),
    ("ties straddling both arrays", [2, 2, 0, 0], 2, [1, 2], 2, [1, 2, 2, 2]),
    ("duplicates, lopsided sizes", [1, 1, 1, 0, 0], 3, [1, 1], 2, [1, 1, 1, 1, 1]),
    # --- negative values ---------------------------------------------------------------
    ("all negative", [-9, -5, -1, 0, 0, 0], 3, [-8, -4, -2], 3, [-9, -8, -5, -4, -2, -1]),
    ("negatives, one at each end", [-3, -2, -1, 0, 0], 3, [-9, 9], 2, [-9, -3, -2, -1, 9]),
    ("signs mixed, real zeros", [-4, 0, 6, 0, 0, 0], 3, [-7, 0, 9], 3, [-7, -4, 0, 0, 6, 9]),
    # --- constraint extremes -------------------------------------------------------------
    ("value range, smaller on the left", [-BILLION, 0], 1, [BILLION], 1, [-BILLION, BILLION]),
    ("value range, smaller on the right", [BILLION, 0], 1, [-BILLION], 1, [-BILLION, BILLION]),
    (
        "value range end to end",
        [-BILLION, 0, 0, 0], 1, [-BILLION, 0, BILLION], 3, [-BILLION, -BILLION, 0, BILLION],
    ),
    ("m + n = 200, n = 0", list(range(200)), 200, [], 0, list(range(200))),
    ("m + n = 200, m = 0", [0] * 200, 0, list(range(-100, 100)), 200, list(range(-100, 100))),
    (
        "m + n = 200, interleaved",
        list(range(0, 200, 2)) + [0] * 100, 100, list(range(1, 200, 2)), 100, list(range(200)),
    ),
]

# m and n are arguments. A solution that recovers them from the lists instead -- counting zeros
# at the end of nums1, filtering zeros out of nums2, taking nums1.index(0) as the boundary --
# agrees with the arguments on most inputs and disagrees on exactly these. Zero is a legal
# value: -10^9 <= nums1[i] <= 10^9 includes it, and nothing distinguishes a stored 0 that is
# data from a stored 0 that is room.
INFERENCE_TRAPS: list[Case] = [
    ("a real 0 at index m-1", [-3, 0, 0, 0], 2, [-1, 5], 2, [-3, -1, 0, 5]),
    ("the data region is all zeros", [0, 0, 0, 0, 0, 0], 3, [1, 2, 3], 3, [0, 0, 0, 1, 2, 3]),
    ("data ends in 0, nums2 all below", [-5, 0, 0, 0], 2, [-9, -7], 2, [-9, -7, -5, 0]),
    ("every slot is 0, only m are data", [0, 0, 0, 0], 2, [5, 6], 2, [0, 0, 5, 6]),
    ("nums2 is all zeros, all real", [1, 2, 3, 0, 0, 0], 3, [0, 0, 0], 3, [0, 0, 0, 1, 2, 3]),
    ("zeros in both roles", [-1, 0, 0, 0, 0, 0], 3, [0, 0, 4], 3, [-1, 0, 0, 0, 0, 4]),
    ("data ends in zeros, room is shorter", [-2, 0, 0, 0, 0], 4, [3], 1, [-2, 0, 0, 0, 3]),
]

ALL_CASES = CASES + INFERENCE_TRAPS


def run_case(
    probe: str, nums1: list[int], m: int, nums2: list[int], n: int, expected: list[int]
) -> None:
    """Call `merge` once and enforce all five contracts, naming the probe in every failure.

    Hands the solution its own copies. The cases are module-level lists shared by every test
    here, and merge writes into what it is given: handing over a case itself would leave the
    next test reading one that has already been merged. Aliasing, in the harness rather than
    in the solution.

    Which also means the case is left untouched and can be compared against directly below.
    """
    where = f"[{probe}] nums1={list(nums1)}, m={m}, nums2={list(nums2)}, n={n}"
    given1, given2 = list(nums1), list(nums2)

    result = Solution().merge(given1, m, given2, n)

    assert result is None, (
        f"{where}: merge must return None, but returned {result!r}. The merged values belong "
        f"in nums1 itself -- the caller reads nums1 when the call comes back, and never looks "
        f"at what merge handed over."
    )
    assert len(given1) == m + n, (
        f"{where}: nums1 must still be {m + n} long, and it is now {len(given1)} long "
        f"({given1}). It arrives at exactly the length of the answer; the trailing zeros are "
        f"reserved room, and there is no slack to add to or take away from."
    )
    assert given1 == expected, f"{where}: nums1 came out as {given1}, want {expected}"
    assert given2 == nums2, (
        f"{where}: nums2 is an input, not scratch space, and it came back as {given2}. Only "
        f"nums1 may be written to."
    )


@pytest.mark.parametrize("probe,nums1,m,nums2,n,expected", CASES)
def test_examples_and_edges(
    probe: str, nums1: list[int], m: int, nums2: list[int], n: int, expected: list[int]
) -> None:
    run_case(probe, nums1, m, nums2, n, expected)


@pytest.mark.parametrize("probe,nums1,m,nums2,n,expected", INFERENCE_TRAPS)
def test_m_and_n_are_arguments_not_guesses(
    probe: str, nums1: list[int], m: int, nums2: list[int], n: int, expected: list[int]
) -> None:
    """Where the data ends and the reserved room begins is m, and only m says so.

    Every case here is one where reading that boundary off the values themselves gives a
    different answer from the one the arguments describe.
    """
    run_case(probe, nums1, m, nums2, n, expected)


def test_cases_obey_the_stated_constraints() -> None:
    """The fixtures are held to the same contract the solution is.

    A case that broke the constraints would demand something never asked for, and a solution
    that failed it would be right to. Checked rather than assumed, because these cases are
    hand-written and a typo in one is invisible until it fails a correct solution.
    """
    for probe, nums1, m, nums2, n, expected in ALL_CASES:
        assert len(nums1) == m + n, f"[{probe}]: nums1 must be m + n long"
        assert len(nums2) == n, f"[{probe}]: nums2 must be n long"
        assert 0 <= m <= 200 and 0 <= n <= 200, f"[{probe}]: 0 <= m, n <= 200"
        assert 1 <= m + n <= 200, f"[{probe}]: 1 <= m + n <= 200"
        assert nums1[m:] == [0] * n, f"[{probe}]: the last n slots of nums1 are set to 0"
        assert nums1[:m] == sorted(nums1[:m]), f"[{probe}]: the data in nums1 arrives sorted"
        assert nums2 == sorted(nums2), f"[{probe}]: nums2 arrives sorted"
        assert all(abs(v) <= BILLION for v in nums1 + nums2), f"[{probe}]: |value| <= 10^9"
        assert len(expected) == m + n, f"[{probe}]: the answer is m + n long"
        assert expected == sorted(expected), f"[{probe}]: the answer is sorted"


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    rng = random.Random(88)
    for _ in range(2000):
        total = rng.randint(1, 24)
        m = rng.randint(0, total)
        n = total - m
        # Narrow ranges force ties and repeated values; the widest is the constraint range
        # itself. All but one straddle 0, so real zeros land among the data often.
        lo, hi = rng.choice([(-3, 3), (0, 2), (-1, 1), (5, 5), (-BILLION, BILLION)])
        nums1 = sorted(rng.randint(lo, hi) for _ in range(m)) + [0] * n
        nums2 = sorted(rng.randint(lo, hi) for _ in range(n))
        # Snapshot first, and grade against the snapshot. The list the solution is handed is
        # the one it is about to rewrite; it cannot also be the answer key.
        before1, before2 = list(nums1), list(nums2)
        expected = oracle(before1, m, before2, n)
        run_case(f"random m={m}, n={n}", nums1, m, nums2, n, expected)


@pytest.mark.property
def test_matches_oracle_when_zeros_are_everywhere() -> None:
    """Random values are almost never 0. Force the issue.

    Half the pool is 0, so the data region, the reserved room and nums2 all fill up with
    zeros, and no rule that works by spotting them survives the run.
    """
    pool = [0, 0, 0, 0, -1, 1, -2, 2]
    rng = random.Random(1088)
    for _ in range(2000):
        total = rng.randint(1, 16)
        m = rng.randint(0, total)
        n = total - m
        nums1 = sorted(rng.choice(pool) for _ in range(m)) + [0] * n
        nums2 = sorted(rng.choice(pool) for _ in range(n))
        before1, before2 = list(nums1), list(nums2)
        expected = oracle(before1, m, before2, n)
        run_case(f"zero-heavy m={m}, n={n}", nums1, m, nums2, n, expected)


# A template is an immutable case at the constraint ceiling: (nums1, m, nums2, n).
Template = tuple[tuple[int, ...], int, tuple[int, ...], int]


def _ceiling_templates(count: int, seed: int = 88) -> list[Template]:
    """`count` distinct cases at m + n = 200, values spanning the whole +/-10^9 range.

    Immutable, so that one round of timing cannot damage the inputs the next round reuses. The
    first two cases are the extremes of the split: everything already in place, and nothing.
    """
    rng = random.Random(seed)
    cases: list[Template] = []
    for i in range(count):
        m = 200 if i == 0 else 0 if i == 1 else rng.randint(0, 200)
        n = 200 - m
        head = sorted(rng.randint(-BILLION, BILLION) for _ in range(m))
        tail = sorted(rng.randint(-BILLION, BILLION) for _ in range(n))
        cases.append((tuple(head + [0] * n), m, tuple(tail), n))
    return cases


@pytest.mark.slow
def test_constraint_ceiling() -> None:
    """m + n = 200, the largest input the constraints allow, against a wall-clock budget.

    A single merge at the ceiling is over in microseconds, far too quick to measure against
    machine noise, so the budget covers 2,000 of them.

    Measured on this repo's interpreter, CPython 3.14.4, best of three rounds:

        one pass, each value placed once             12.5 ms      6.3 us per merge
        ------------------------------------------------------ budget: 150 ms
        re-scanning what is left for the next value 162.8 ms     81.4 us per merge
        selecting the smallest of everything left   402.0 ms    201.0 us per merge

    The budget is about a dozen times what a correct solution costs. That margin is a decade,
    not the hundredfold slack chapter 1's suites could afford, and deliberately so: at 200
    elements a quadratic scan is only around thirty times slower than a single pass, and a
    looser budget would wave one through. It is also why this is not the only timing guard.
    test_does_not_grow_quadratically separates the two shapes with room to spare, and sees the
    quadratic costs that hide inside C-speed list operations rather than in Python-level loops.
    """
    reps = 2_000
    budget = 0.150
    templates = _ceiling_templates(reps)
    expected = [oracle(list(a), m, list(b), n) for a, m, b, n in templates]

    fastest = float("inf")
    for _ in range(3):
        cases = [(list(a), m, list(b), n) for a, m, b, n in templates]
        merge = Solution().merge
        start = time.perf_counter()
        for nums1, m, nums2, n in cases:
            merge(nums1, m, nums2, n)
        fastest = min(fastest, time.perf_counter() - start)
        # Correctness before speed: a wrong answer should say it is wrong, not that it is slow.
        graded = zip(cases, templates, expected)
        for (nums1, m, nums2, n), (before1, _, before2, _), want in graded:
            assert len(nums1) == 200, (
                f"[ceiling m={m}, n={n}] nums1 is {len(nums1)} long, want 200"
            )
            assert nums1 == want, (
                f"[ceiling m={m}, n={n}] nums1 came out as {nums1}, want {want} "
                f"(from nums1={list(before1)}, nums2={list(before2)})"
            )
            assert tuple(nums2) == before2, (
                f"[ceiling m={m}, n={n}] nums2 is read-only, and it came back as {nums2}"
            )

    assert fastest < budget, (
        f"{reps:,} merges at the ceiling (m + n = 200) took {fastest * 1e3:.0f}ms, over the "
        f"{budget * 1e3:.0f}ms budget: {fastest / reps * 1e6:.0f}us per merge, against the 6us "
        f"a single pass costs here. Something inside the loop is looking at more than a "
        f"constant number of elements per step."
    )


def _growth_case(total: int, seed: int) -> tuple[list[int], int, list[int], int]:
    rng = random.Random(seed)
    m = total // 2
    n = total - m
    head = sorted(rng.randint(-BILLION, BILLION) for _ in range(m))
    tail = sorted(rng.randint(-BILLION, BILLION) for _ in range(n))
    return head + [0] * n, m, tail, n


@pytest.mark.slow
def test_does_not_grow_quadratically() -> None:
    """Eight times the input should cost about eight times the work.

    These sizes run far past the stated m + n <= 200, on purpose. The follow-up asks for
    O(m + n), and 200 elements is simply too few for a clock to tell O(m + n) from
    O((m + n)^2): the two are only about thirty times apart there, which is inside the range
    ordinary machine noise can cover. The code under test does not change with the size, so
    running it larger makes the same shape visible with no ambiguity left in it.

    Measured on this repo's interpreter, CPython 3.14.4, m + n = 4,000 then 32,000:

        one pass, each value placed once             0.15 ms ->    1.31 ms      8.5x
        ------------------------------------------------------------ ceiling: 20x
        repeated insert into the merged part         0.75 ms ->   37.77 ms     50.7x
        popping the front of a list each step        0.45 ms ->   24.88 ms     54.8x
        scanning for each insertion point           41.72 ms -> 2848.23 ms     68.3x

    A quadratic solution lands near 64x, so the 20x ceiling sits in a wide empty gap. Note the
    first two offenders: each spends one comparison per element, so any count of comparisons
    would call them linear, and each is quadratic anyway because the list operation it performs
    every step touches the whole tail. This is the guard that sees those.

    Times are the best of several runs, which throws away interference from other processes.
    """
    total, factor, ceiling = 4_000, 8, 20.0

    def best_of(size: int, reps: int, seed: int) -> float:
        # Every repetition needs its own case: the first call leaves nums1 merged, and merging
        # an already-merged list is a different problem. Building them is not timed.
        cases = [_growth_case(size, seed) for _ in range(reps)]
        merge = Solution().merge
        fastest = float("inf")
        for nums1, m, nums2, n in cases:
            start = time.perf_counter()
            merge(nums1, m, nums2, n)
            fastest = min(fastest, time.perf_counter() - start)
        return fastest

    def timed(size: int, reps: int, seed: int) -> float:
        try:
            return best_of(size, reps, seed)
        except RecursionError:
            pass  # reported below, outside the handler, so the traceback stays readable
        pytest.fail(
            f"merge ran out of stack at m + n = {size:,}. These sizes run past the stated "
            f"ceiling of 200 deliberately (see the docstring), but a recursion that deep is "
            f"worth knowing about anyway: one stack frame per element is O(m + n) extra "
            f"space, and the target here is O(1)."
        )

    small_time = timed(total, 9, 1)
    big_time = timed(total * factor, 3, 2)

    ratio = big_time / small_time
    assert ratio < ceiling, (
        f"{factor}x the input cost {ratio:.0f}x the time (m + n = {total:,} -> "
        f"{total * factor:,}). An O(m + n) solution lands near {factor}x; {ratio:.0f}x means "
        f"the work per element grows with the input. The algorithm may well be right -- look "
        f"instead for a step inside the loop that is not O(1): insert() and pop(0) both shift "
        f"every element past the position they touch, `in` and .index() walk the list, and "
        f"slicing copies it. Each is O(m + n) on its own, and doing one per element is the "
        f"whole cost."
    )


# ---------------------------------------------------------------------------------------
# There is deliberately NO auxiliary-space guard here.
#
# An earlier version of this suite measured peak allocation with tracemalloc and rejected any
# solution whose extra space grew with the input. That was wrong, and it is worth recording
# why so it does not come back.
#
# This problem's follow-up asks for one thing: "Can you come up with an algorithm that runs in
# O(m + n) time?" Time. It never constrains space, and "stored inside the array nums1" is a
# statement about where the ANSWER goes, not about what you may allocate on the way there.
# Two solutions the guard rejected are entirely correct by that statement:
#
#   * copy nums1[:m] aside, then merge the two sorted runs forward into nums1  -- O(m) space
#   * merge both runs into a new list, then nums1[:] = it                      -- O(m+n) space
#
# Both are linear in time and both are accepted. Failing them would be inventing a requirement
# and then marking the reader wrong for not guessing it.
#
# The guard also ran at m + n = 50_000, which is 250x this problem's stated ceiling of 200 --
# so it was enforcing an invented rule at a scale the problem never reaches.
#
# The genuinely wrong shapes are still caught, by the tests that remain: anything quadratic
# fails the wall-clock budgets above, and anything that gets the contract wrong fails the
# correctness and immutability tests.
#
# O(1) extra space IS worth reaching for here, and the tier-4 hint says so. It is an ambition,
# not the spec. Chapter 5 is where in-place-with-constant-space becomes the actual subject.
# ---------------------------------------------------------------------------------------
