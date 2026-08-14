"""Spec for 1089. Duplicate Zeros.

Chapter 1's problems were read-only, and their suites checked that the input came back
untouched. This one inverts that. The input is the output, so four contracts are enforced here:

1. `duplicateZeros` returns None. The answer is whatever `arr` holds afterwards, so returning
   the right list without writing into `arr` fails, and so does writing into `arr` correctly and
   then handing the list back as a return value.
2. `arr` itself holds the duplicated contents, exactly.
3. `len(arr)` is unchanged. Elements pushed past the last index are discarded, not appended.
4. n = 10^4 finishes inside a wall-clock budget.

Two independent timing guards sit at the bottom, and the reason for the second one is worth
knowing. The constraint ceiling here is 10^4, which is small: measured on this repo's
interpreter (CPython 3.14.4), a single correct pass over 10^4 elements takes about 0.35 ms,
while a solution whose per-element cost grows with n can still get through the same input in
7 ms when the moving is done by the list object itself at C speed. Milliseconds against
milliseconds is not a gap a wall clock can call, so:

  budget guard   `test_large_input` repeats the worst case at the ceiling and holds the total to
                 a wall-clock budget. This catches per-element work done in Python, which is the
                 expensive kind -- the same input measured 8.5 s that way, against 8.9 ms for a
                 single pass.

  growth guard   `test_does_not_grow_quadratically` times the solution at n and 8n and rejects
                 super-linear growth. Eight times the input costs about eight times the work for
                 a single pass (measured 8.05x and 7.44x for two different correct solutions)
                 and about sixty-four times for one whose per-element cost grows with the array
                 (measured 62.9x and 66.1x). This one sees the costs the budget cannot, because
                 a ratio does not care how fast the machine underneath it is.

Both guards measure two shapes: an array of all zeros, and one where every other element is a
zero. An array of a single repeated value is the easiest thing in the world to special-case, so
timing only that one leaves a solution free to be fast on the shape being measured and slow on
every other.
"""

import random
import time
from collections.abc import Callable

import pytest

from arrays101.ch02.p01_duplicate_zeros import Solution
from tests._reference.p01_duplicate_zeros import oracle


def solve(arr: list[int]) -> object:
    """Run the solution and hand back its return value, which must be None."""
    return Solution().duplicateZeros(arr)


# ======================================================================================
# Contract checking, shared by every test below.
# ======================================================================================


def _render(value: object, limit: int = 24) -> str:
    """A repr that stays readable when the list has ten thousand elements in it."""
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


def _check(probes: str, original: list[int], arr: list[int], returned: object) -> None:
    """Assert the whole in-place contract for one call.

    `original` is a pristine snapshot taken before the call; `arr` is the list the solution was
    handed. The expected contents are computed from the snapshot, so a solution cannot rewrite
    its own answer key.
    """
    expected = oracle(original)

    assert returned is None, (
        f"{probes}: duplicateZeros must return None and leave its answer in arr, but it "
        f"returned {_render(returned)}. The list handed to you is the output: the caller keeps "
        f"a reference to it and reads it once you are done, and ignores what you return."
    )
    assert len(arr) == len(original), (
        f"{probes}: len(arr) must still be {len(original)}, but duplicateZeros left "
        f"{len(arr)} elements: {_render(arr)}. The array is fixed-length -- elements pushed "
        f"past the last index are discarded, not stored."
    )
    if arr != expected:
        i = _first_difference(arr, expected)
        detail = f"first difference at index {i}: arr[{i}] = {arr[i]}, want {expected[i]}"
        if arr == original and expected != original:
            detail += (
                ". arr came back exactly as it was handed over, so nothing was written into it "
                "at all. This problem is in place: the caller keeps a reference to this very "
                "list, and a new list built somewhere else never reaches them"
            )
        raise AssertionError(
            f"{probes}: duplicateZeros({_render(original)}) left arr = {_render(arr)}, "
            f"want {_render(expected)}; {detail}"
        )


# ======================================================================================
# Shapes and sizes used by more than one test below.
# ======================================================================================

CEILING = 10_000  # the constraint ceiling: 1 <= arr.length <= 10^4


def _all_zeros(n: int) -> list[int]:
    """The worst case for a correct solution: every element has somewhere to move."""
    return [0] * n


def _alternating_zeros(n: int) -> list[int]:
    """Every other element a zero, so half the array moves and half of it stays put.

    The second shape both timing guards are measured on. An all-zero array is uniform, and
    uniform is exactly what a solution can recognise cheaply and hand back untouched; this one
    cannot be disposed of that way, because the answer really does differ from the input.
    """
    return [0 if i % 2 else 7 for i in range(n)]


# ======================================================================================
# Hand-written cases. Third field names what the case is probing.
# ======================================================================================

CASES: list[tuple[list[int], list[int], str]] = [
    # --- LeetCode's own examples ---------------------------------------------------------
    ([1, 0, 2, 3, 0, 4, 5, 0], [1, 0, 0, 2, 3, 0, 0, 4], "example 1"),
    ([1, 2, 3], [1, 2, 3], "example 2"),
    # --- single element --------------------------------------------------------------------
    ([0], [0], "single zero, nowhere for the copy to go"),
    ([7], [7], "single non-zero"),
    # --- every pattern of length 2 ---------------------------------------------------------
    ([0, 0], [0, 0], "two zeros, both copies fall off"),
    ([0, 1], [0, 0], "leading zero pushes the 1 off the end"),
    ([1, 0], [1, 0], "trailing zero, copy discarded"),
    ([1, 2], [1, 2], "no zeros, length 2"),
    # --- no zeros at all: nothing may move -------------------------------------------------
    ([1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], "no zeros, every value 1-9"),
    ([9, 9, 9], [9, 9, 9], "no zeros, all identical"),
    # --- all zeros: every copy but the first n falls off ------------------------------------
    ([0, 0, 0, 0], [0, 0, 0, 0], "all zeros, length 4"),
    ([0] * 7, [0] * 7, "all zeros, odd length"),
    # --- a zero in the final position: the truncation boundary ------------------------------
    ([1, 2, 3, 0], [1, 2, 3, 0], "zero at the last index, its copy is discarded"),
    ([4, 0], [4, 0], "zero at the last index, length 2"),
    ([1, 2, 0, 0], [1, 2, 0, 0], "two zeros at the end, both copies discarded"),
    ([1, 2, 3, 4, 5, 0, 0, 0, 0, 0], [1, 2, 3, 4, 5, 0, 0, 0, 0, 0], "zeros fill the tail"),
    # --- a zero landing exactly at the boundary, so only one copy fits ----------------------
    ([1, 0, 3, 0, 5], [1, 0, 0, 3, 0], "shifted zero lands on the last index, copy discarded"),
    ([8, 4, 5, 0, 0, 0, 0, 7], [8, 4, 5, 0, 0, 0, 0, 0], "run of zeros overruns the end"),
    ([0, 0, 1], [0, 0, 0], "second zero's first copy is the last surviving element"),
    # --- a zero whose pair fits exactly, pushing the next value off -------------------------
    ([1, 2, 0, 3], [1, 2, 0, 0], "pair lands exactly on the last two slots"),
    ([1, 2, 3, 0, 4], [1, 2, 3, 0, 0], "pair fits exactly, the 4 is pushed out"),
    # --- a leading zero shifts the whole array ---------------------------------------------
    ([0, 1, 2, 3], [0, 0, 1, 2], "zero at index 0"),
    ([0, 0, 1, 2, 3], [0, 0, 0, 0, 1], "two leading zeros, one value survives"),
    ([0] * 5 + [1, 2, 3, 4, 5], [0] * 10, "leading zeros push out every non-zero value"),
    # --- adjacent zeros in the middle -------------------------------------------------------
    ([1, 0, 0, 2], [1, 0, 0, 0], "adjacent zeros mid-array"),
    ([1, 2, 0, 3, 4], [1, 2, 0, 0, 3], "one zero mid-array"),
    # --- one zero, at each end of a longer array ---------------------------------------------
    ([1, 2, 3, 4, 5, 6, 0, 7, 8, 9], [1, 2, 3, 4, 5, 6, 0, 0, 7, 8], "one zero, late"),
    ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [0, 0, 1, 2, 3, 4, 5, 6, 7, 8], "one zero, first index"),
    # --- alternating, starting from each side --------------------------------------------------
    ([0, 1, 0, 1, 0, 1], [0, 0, 1, 0, 0, 1], "alternating, zero first"),
    ([1, 0, 1, 0, 1, 0], [1, 0, 0, 1, 0, 0], "alternating, zero second"),
    # --- long enough that an off-by-one at the tail cannot hide -----------------------------
    (
        [1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0],
        [1, 0, 0, 2, 0, 0, 3, 0, 0, 4, 0, 0],
        "12 elements, every other one a zero",
    ),
    (
        [1, 1, 1, 0] * 6,
        [1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0],
        "24 elements, six identical groups",
    ),
    (
        [0] + [5] * 22 + [0],
        [0, 0] + [5] * 22,
        "24 elements, a zero at each end",
    ),
]


@pytest.mark.parametrize("arr,expected,probes", CASES)
def test_examples_and_edges(arr: list[int], expected: list[int], probes: str) -> None:
    # The table's expected values are asserted against the reference as well, so a typo in a
    # hand-written case shows up as a broken test rather than as a wrong requirement.
    original = list(arr)
    assert expected == oracle(original), (
        f"the test case {probes!r} disagrees with the reference answer -- fix the table, "
        f"not the solution"
    )
    returned = solve(arr)
    _check(probes, original, arr, returned)


@pytest.mark.property
def test_every_small_pattern() -> None:
    """All 8,190 zero/non-zero patterns of length 1 through 12, exhaustively.

    Only the positions of the zeros matter, so enumerating every subset of positions covers the
    whole shape of the problem at small sizes: zeros at both ends, runs of them, a copy landing
    on the last index, a copy falling off it. Nothing here is left to chance.
    """
    for n in range(1, 13):
        for mask in range(1 << n):
            arr = [0 if (mask >> i) & 1 else (i % 9) + 1 for i in range(n)]
            original = list(arr)
            returned = solve(arr)
            _check(f"exhaustive n={n}, zero pattern {mask:0{n}b}", original, arr, returned)


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    rng = random.Random(1089)
    for _ in range(2000):
        n = rng.randint(1, 60)
        # Vary how common zeros are, so sparse, balanced and all-zero arrays all get covered.
        p = rng.choice([0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0])
        arr = [0 if rng.random() < p else rng.randint(1, 9) for _ in range(n)]
        # Snapshot first. The answer key is computed from this copy inside _check, never from
        # the list the solution was handed -- that list is about to be overwritten by design.
        original = list(arr)
        returned = solve(arr)
        _check(f"random n={n}, zero density {p}", original, arr, returned)


@pytest.mark.property
def test_mid_size_lengths() -> None:
    """Every length between the small exhaustive sizes and the constraint ceiling is fair game.

    The tests above stop at n = 60 and the timing guards below start at n = 10^4, both of them
    round numbers. A gap like that is somewhere for a bug to live: a solution that walks the
    array in fixed-size chunks, or that handles a leftover tail separately, can be right on
    every length up to 60, right again on a round 10,000, and wrong on 101 or 9,999. Nothing in
    the constraints says the length will be convenient.

    The lengths worth naming come first: every one just above where the random test stops, both
    sides of each power of two, both sides of each round number, and 9,999 -- one short of the
    longest input allowed. Each is tried in six shapes, including both alignments of an
    alternating pattern, since a tail bug can easily depend on whether the last element is a
    zero.

    Naming lengths only covers the ones somebody thought of, so the rest of the range is then
    walked with a stride of 250 in two shapes. That leaves no window of 250 consecutive lengths
    anywhere below the ceiling untested, which is what makes this a statement about all lengths
    rather than about a lucky handful.
    """
    rng = random.Random(20891089)

    def run(n: int, name: str, data: list[int]) -> None:
        arr = list(data)
        original = list(data)
        returned = solve(arr)
        _check(f"n={n}, {name}", original, arr, returned)

    def no_zeros(n: int) -> list[int]:
        return [(i % 9) + 1 for i in range(n)]

    def zero_first(n: int) -> list[int]:
        return [0 if i % 2 == 0 else 7 for i in range(n)]

    def zero_last(n: int) -> list[int]:
        return [0 if (n - 1 - i) % 2 == 0 else 7 for i in range(n)]

    def zeros_in_the_tail(n: int) -> list[int]:
        return [0 if i >= n - n // 10 else 7 for i in range(n)]

    def sprinkled(n: int, p: float) -> list[int]:
        return [0 if rng.random() < p else rng.randint(1, 9) for _ in range(n)]

    lengths = list(range(61, 201))
    for base in (256, 512, 1024, 4096):
        lengths += [base - 1, base, base + 1]
    for base in (100, 500, 1000, 5000):
        lengths += [base - 1, base, base + 1]
    lengths.append(CEILING - 1)

    for n in lengths:
        run(n, "all zeros", _all_zeros(n))
        run(n, "no zeros", no_zeros(n))
        run(n, "alternating, first element a zero", zero_first(n))
        run(n, "alternating, last element a zero", zero_last(n))
        run(n, "zeros only in the last tenth", zeros_in_the_tail(n))
        run(n, "random, zeros one time in three", sprinkled(n, 1 / 3))

    for n in range(201, CEILING, 250):
        run(n, "alternating, last element a zero", zero_last(n))
        run(n, "random, zeros one time in five", sprinkled(n, 0.2))


# ======================================================================================
# Timing guards.
# ======================================================================================

# The shapes both timing guards measure, as (name, builder) pairs so each guard can build them
# at whatever length it needs.
TIMED_SHAPES: tuple[tuple[str, Callable[[int], list[int]]], ...] = (
    ("all zeros", _all_zeros),
    ("every other element a zero", _alternating_zeros),
)


def _timed_best_of(data: list[int], reps: int) -> float:
    """Fastest of `reps` runs, in seconds, timing only the call.

    Every run needs its own copy, since the solution destroys what it is given. The copies are
    made up front so that copying is not inside the measurement.
    """
    copies = [list(data) for _ in range(reps)]
    fastest = float("inf")
    for c in copies:
        start = time.perf_counter()
        solve(c)
        fastest = min(fastest, time.perf_counter() - start)
    return fastest


@pytest.mark.slow
def test_large_input() -> None:
    """n = 10^4, the constraint ceiling, in the shapes that stress it hardest.

    The budget covers REPEATS passes over an all-zero array, which is the worst case: every
    element has to move. A single such pass measured 0.35 ms on this repo's interpreter, so the
    25 of them below come to roughly 9 ms; the budget of 2.0 s is over two hundred times that,
    which no amount of interference from other processes will close. What does close it is
    doing per-element work in Python inside a loop that already visits every element -- the same
    25 passes measured 8.5 s that way, four times over the budget.

    The same budget is then applied to an array whose zeros alternate with non-zeros, where only
    half the elements move. That one costs a correct solution nothing extra -- 25 passes measured
    0.008 s and 0.005 s for two correct solutions, the same as those two measured on the all-zero
    array -- while it costs a solution doing per-element work in Python 6.6 s, three times over
    the budget. Two shapes rather than one, because an array of a single repeated value is the
    easiest input there is to recognise and skip.
    """
    rng = random.Random(1089)
    shapes: list[tuple[str, list[int]]] = [
        ("all zeros", [0] * CEILING),
        ("no zeros", [rng.randint(1, 9) for _ in range(CEILING)]),
        ("random digits 0-9", [rng.randint(0, 9) for _ in range(CEILING)]),
        ("every other element a zero", [0 if i % 2 else rng.randint(1, 9) for i in range(CEILING)]),
        ("one zero, at the last index", [rng.randint(1, 9) for _ in range(CEILING - 1)] + [0]),
        ("one zero, at index 0", [0] + [rng.randint(1, 9) for _ in range(CEILING - 1)]),
        ("zeros only in the last tenth", [0 if i >= CEILING - 1000 else 7 for i in range(CEILING)]),
    ]
    for name, data in shapes:
        arr = list(data)
        original = list(data)
        returned = solve(arr)
        _check(f"n=10^4, {name}", original, arr, returned)

    repeats, budget = 25, 2.0
    for name, make in TIMED_SHAPES:
        data = make(CEILING)
        copies = [list(data) for _ in range(repeats)]
        start = time.perf_counter()
        for c in copies:
            solve(c)
        elapsed = time.perf_counter() - start
        assert elapsed < budget, (
            f"{repeats} passes over 10^4 elements ({name}) took {elapsed:.1f}s, over the "
            f"{budget}s budget. One pass should cost a fraction of a millisecond. Something "
            f"inside the loop is doing work proportional to the length of the array rather than "
            f"a fixed amount, which makes the whole thing quadratic -- and quadratic is what a "
            f"Time Limit Exceeded on the submission page means."
        )


@pytest.mark.slow
def test_does_not_grow_quadratically() -> None:
    """Eight times the input should cost about eight times the work, on two shapes.

    A solution whose per-element cost grows with the array costs about sixty-four times as much
    instead, so the two are far enough apart that ordinary machine noise cannot confuse them.
    Measured here at 10^4 -> 8x10^4 on an all-zero array, where every element moves: 8.05x and
    7.44x for two different single-pass solutions, against 62.9x and 66.1x for two whose
    per-element cost grows. The ceiling below sits between those bands with room on both sides.

    This is the guard the budget above cannot be: whole-list operations run at C speed, so on a
    ceiling of only 10^4 a quadratic solution can still finish in single-digit milliseconds and
    slip under any wall-clock budget loose enough to be reliable. A ratio catches it anyway,
    because the shape of the growth does not depend on how fast the machine is.

    The second shape is not decoration. An array of one repeated value is trivial to recognise
    and hand straight back, and a solution that does so is being timed doing nothing: one that
    shifts by an insert per zero, but returns early when the array is all zeros or has none,
    measured 7.9x here on the all-zero array -- inside the correct band -- and 62.2x once every
    other element is a zero. The correct solutions measure 8.1x and 7.9x on that same
    interleaved shape, so it costs them nothing to be asked.

    Times are the best of several runs, which throws away interference from other processes.
    """
    factor, ceiling = 8, 20.0
    for name, make in TIMED_SHAPES:
        small, big = make(CEILING), make(CEILING * factor)

        # Correctness at 8x the constraint ceiling, checked once, outside the timing.
        arr = list(big)
        returned = solve(arr)
        _check(f"n=8x10^4, {name}", list(big), arr, returned)

        ratio = _timed_best_of(big, 3) / _timed_best_of(small, 9)
        assert ratio < ceiling, (
            f"{factor}x the input cost {ratio:.0f}x the time (n={CEILING:,} -> "
            f"{CEILING * factor:,}, {name}). A single pass lands near {factor}x; "
            f"{ratio:.0f}x means the work done per element grows with the length of the array. "
            f"The algorithm may well be right -- look instead for a step inside the loop that "
            f"is not O(1). Inserting into a list, deleting from one, slicing it, searching it "
            f"with `in`, .index() or .count(): each of those touches the whole list, and doing "
            f"it once per zero is the entire cost."
        )
