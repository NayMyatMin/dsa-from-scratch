"""Spec for 941. Valid Mountain Array.

Chapters 2 and 3 wrote their answers into the list they were handed. This one does not touch it.
`arr` is input, the answer is the value that comes back, and the list must be exactly as it
arrived when the call returns. That is chapter 1's contract again, and four things are enforced
here.

1. `validMountainArray` returns a real `bool` -- True or False, not 1, not 0, not None, not the
   index of the summit. bool is a subclass of int in Python, so 1 would pass a comparison against
   True; this suite compares types, not truthiness.
2. The value is right. The answer key comes from the reference in `tests/_reference/`, which is
   the definition transcribed literally, and it is computed from a pristine snapshot taken before
   the call -- so a solution cannot rewrite its own answer key.
3. `arr` comes back untouched. Same length, same elements, same order. This one is checked on
   every single call in this file, not in a test of its own, because there is no call on which it
   is allowed to fail.
4. n = 10^4, the constraint ceiling, inside a wall-clock budget, and a fixed amount of work per
   element as the list grows towards it.

Time is policed here, and it is the difference between this problem and 1346 next door. There n
stops at 500 and a nested loop over every pair is an accepted answer, so that suite has no growth
guard at all. Here n reaches 10^4, and a solution that verifies each candidate summit from scratch
costs 376 ms on one pass over a true mountain and 1,475 ms on one pass over a strictly rising
list, against 0.14 to 0.62 ms for the four linear solutions measured for this file. That is a
factor of between 600 and 10,800 on inputs the constraints actually allow, so the requirement is
real and both guards below enforce it: `test_constraint_ceiling` measures the ceiling against a
wall clock, and `test_does_not_grow_quadratically` measures the shape with a ratio, which is the
statistic that does not care how fast the machine underneath it is.

What this suite deliberately does NOT police, because the problem does not ask:

  extra space   Not measured at all. The stub names O(1) extra space as the target because that is
                the bar this problem is usually held to, but 10^4 elements is small enough that a
                solution which slices `arr` into two halves and checks each one is accepted by the
                judge, and it is accepted here. Chapter 5 is where constant extra space becomes
                the subject.

  which route   No static check on any name. Whatever produces the right bool inside the time
                budget, without writing into `arr`, is accepted.

Reading `arr` is unrestricted. What is banned is *writing* to it, and the difference is worth
being precise about, because the read-only rule is easy to over-read: `arr[:]`, `sorted(arr)` and
`list(reversed(arr))` all build new lists and leave `arr` alone, so they pass; `arr.sort()` and
`arr.reverse()` rewrite `arr` where it stands, so they fail. A solution is free to copy the input
and do anything at all to the copy.

Every input this file hands over obeys the stated constraints, including the ones the timing
guards build -- 1 <= len(arr) <= 10^4 and 0 <= arr[i] <= 10^4, at every size, right up to and
including the ceiling. Nothing here runs past the constraints to make a measurement work, so a
solution is entitled to assume them everywhere.
"""

import random
import time
from itertools import product

import pytest

from arrays101.ch04.p02_valid_mountain_array import Solution
from tests._reference.p02_valid_mountain_array import oracle


def solve(arr: list[int]) -> object:
    """Run the solution and hand back its return value, which must be a bool."""
    return Solution().validMountainArray(arr)


# ======================================================================================
# Contract checking, shared by every test below.
# ======================================================================================


def _render(value: object, limit: int = 24) -> str:
    """A repr that stays readable when the list has thousands of elements in it."""
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


def _flat_step(arr: list[int]) -> int | None:
    """The index of the first pair of equal neighbours, or None."""
    for i in range(len(arr) - 1):
        if arr[i] == arr[i + 1]:
            return i
    return None


def _check(probe: str, original: list[int], arr: list[int], returned: object,
           expected: bool) -> None:
    """Assert the whole contract for one call.

    `original` is a pristine snapshot taken before the call; `arr` is the list the solution was
    handed. `expected` is graded against the snapshot, never against whatever came back.
    """
    where = f"{probe}: validMountainArray({_render(original)})"

    # `type(...) is bool` rather than isinstance, and deliberately: bool is a subclass of int in
    # Python, and 1 == True, so a check written as `returned == expected` would accept 1 for True
    # and 0 for False, and one written as `isinstance(returned, int)` would accept them too.
    if type(returned) is not bool:
        extra = ""
        if returned in (0, 1):
            extra = (
                ". 1 and 0 are not True and False here. Python will treat them as truth values "
                "almost everywhere, and this is one of the places it does not: the signature "
                "says bool"
            )
        elif returned is None:
            extra = (
                ". None is what a function returns when it runs off the end without a return "
                "statement -- look for a path through your code that never reaches one"
            )
        raise AssertionError(
            f"{where} returned {_render(returned)}, of type {type(returned).__name__}. It must "
            f"return True or False -- the question is whether arr is a mountain, not where the "
            f"summit is{extra}."
        )

    if arr != original:
        if len(arr) != len(original):
            detail = f"it is now {len(arr)} elements long, was {len(original)}"
        else:
            i = _first_difference(arr, original)
            detail = f"first difference at index {i}: arr[{i}] is now {arr[i]}, was {original[i]}"
            if sorted(arr) == sorted(original):
                detail += (
                    ". The same values are all still there, in a different order -- something "
                    "sorted or reversed arr where it stands. arr[:], sorted(arr) and "
                    "list(reversed(arr)) hand back new lists and leave arr alone; arr.sort() and "
                    "arr.reverse() do not"
                )
        raise AssertionError(
            f"{where} modified arr. This problem is read-only: arr is input, the answer is the "
            f"value you return, and nobody reads arr again afterwards. {detail}. Afterwards arr "
            f"was {_render(arr)}. Copy it and rewrite the copy if you need to."
        )

    if returned != expected:
        detail = ""
        n = len(original)
        flat = _flat_step(original)
        if expected is False and n < 3:
            detail = (
                f". arr has {n} element{'s' if n != 1 else ''}, and the definition starts with "
                f"arr.length >= 3. A list this short has nowhere to put a summit with something "
                f"on both sides of it, so the answer is False whatever the values are"
            )
        elif expected is False and flat is not None:
            detail = (
                f". arr[{flat}] and arr[{flat + 1}] are both {original[flat]}. Every comparison "
                f"in the definition is strict, so a pair of equal neighbours is neither a climb "
                f"nor a fall and one of them anywhere is fatal"
            )
        elif expected is False and n >= 3 and all(
            a < b for a, b in zip(original, original[1:])
        ):
            detail = (
                ". arr climbs the whole way and never falls. The definition puts the summit at an "
                "index i with 0 < i < arr.length - 1, strictly inside the list, so the last "
                "element cannot be it"
            )
        elif expected is False and n >= 3 and all(
            a > b for a, b in zip(original, original[1:])
        ):
            detail = (
                ". arr falls the whole way and never climbs. The definition puts the summit at an "
                "index i with 0 < i < arr.length - 1, strictly inside the list, so the first "
                "element cannot be it"
            )
        raise AssertionError(f"{where} returned {returned}, want {expected}{detail}")


def _run(probe: str, arr: list[int]) -> None:
    """Snapshot, grade against the reference, call, check."""
    original = list(arr)
    expected = oracle(original)
    returned = solve(arr)
    _check(probe, original, arr, returned, expected)


def _run_known(probe: str, arr: list[int], expected: bool) -> None:
    """The same, for lists too long to hand to a quadratic reference.

    The reference is O(n^2) on purpose -- it is the definition transcribed, and being obviously
    right matters more there than being quick. That makes it the wrong tool at a ceiling of 10^4,
    so the long inputs in this file are built by the shape functions below, whose answers are
    known by construction. `test_the_shape_builders_are_what_they_claim` holds those constructions
    to the reference at sizes where the reference is cheap, so nothing here rests on a builder
    being trusted rather than checked.
    """
    original = list(arr)
    returned = solve(arr)
    _check(probe, original, arr, returned, expected)


# ======================================================================================
# Shapes used by more than one test below, all with answers known by construction.
#
# Every one of them keeps 0 <= arr[i] <= 10^4 for every length up to the ceiling, so the timing
# guards never have to step outside the constraints to get a measurement.
# ======================================================================================

CEILING = 10_000  # the constraint ceiling: 1 <= arr.length <= 10^4


def _mountain(n: int) -> list[int]:
    """A genuine mountain: strictly up to a summit near the middle, then strictly down.

    The summit value is max(left, right), which is about n / 2, so at the ceiling the largest
    element is 5,000 -- half of what the constraints allow.
    """
    left = n // 2
    right = n - left - 1
    peak = max(left, right)
    return (
        [peak - left + i for i in range(left)]
        + [peak]
        + [peak - 1 - i for i in range(right)]
    )


def _rising(n: int) -> list[int]:
    """Climbs the whole way and never falls. The summit would have to be the last element."""
    return list(range(n))


def _falling(n: int) -> list[int]:
    """Falls the whole way and never climbs. The summit would have to be the first element."""
    return list(range(n - 1, -1, -1))


def _flat_at_the_foot(n: int) -> list[int]:
    """A mountain whose first two elements are equal. The climb never starts."""
    a = _mountain(n)
    a[0] = a[1]
    return a


def _flat_at_the_peak(n: int) -> list[int]:
    """A mountain with a plateau at the summit -- the flat step that gets missed most often."""
    a = _mountain(n)
    p = a.index(max(a))
    a[p + 1] = a[p]
    return a


def _flat_at_the_end(n: int) -> list[int]:
    """A mountain whose last two elements are equal. Everything before the last step is right."""
    a = _mountain(n)
    a[-1] = a[-2]
    return a


def _two_peaks(n: int) -> list[int]:
    """Two mountains end to end. Up, down, up, down: one summit too many."""
    half = n // 2
    return _mountain(half) + _mountain(n - half)


def _valley(n: int) -> list[int]:
    """Down then up: the mirror image of a mountain, and not one."""
    left = n // 2
    right = n - left - 1
    return [left - i for i in range(left)] + [0] + [i + 1 for i in range(right)]


def _plateau(n: int) -> list[int]:
    """Every element the same. No climb, no fall, nothing but flat steps."""
    return [7] * n


# (name, builder, the answer it is built to have, the shortest length it makes sense at)
SHAPES: tuple[tuple[str, object, bool, int], ...] = (
    ("a true mountain", _mountain, True, 3),
    ("strictly rising, never falls", _rising, False, 1),
    ("strictly falling from the first element", _falling, False, 1),
    ("a mountain whose first step is flat", _flat_at_the_foot, False, 3),
    ("a mountain whose summit is a plateau", _flat_at_the_peak, False, 3),
    ("a mountain whose last step is flat", _flat_at_the_end, False, 3),
    ("two mountains end to end", _two_peaks, False, 6),
    ("a valley instead of a mountain", _valley, False, 3),
    ("every element equal", _plateau, False, 1),
)


def test_the_shape_builders_are_what_they_claim() -> None:
    """Every builder above, at every length the reference can afford, against the reference.

    The long inputs in this file are graded against the answer the builder promises rather than
    against the reference, because the reference is quadratic and the ceiling is 10,000 elements.
    So the promise itself is checked here, at sizes where checking is cheap: if a builder ever
    stops producing what it says on the label, this test fails rather than some unrelated test
    quietly grading against the wrong answer.

    The constraints are checked here too, at every one of these lengths and again at the ceiling,
    because the timing guards below build their inputs from these same functions and a fixture
    that broke 0 <= arr[i] <= 10^4 would be demanding something the problem never asked for.
    """
    for name, make, expected, floor in SHAPES:
        for n in list(range(floor, 61)) + [CEILING]:
            arr = make(n)
            assert len(arr) == n, f"{name}: builder returned {len(arr)} elements, wanted {n}"
            assert all(0 <= x <= CEILING for x in arr), f"{name} at n={n}: 0 <= arr[i] <= 10^4"
            if n <= 60:
                assert oracle(arr) is expected, (
                    f"the builder {name!r} at n={n} produced {_render(arr)}, whose real answer is "
                    f"{oracle(arr)} and not the {expected} it promises -- fix the builder, not "
                    f"the solution"
                )


# ======================================================================================
# The grader itself, against the contract.
# ======================================================================================


def test_the_grader_holds_the_contract_it_describes() -> None:
    """What `_check` accepts and rejects, pinned down rather than asserted in a docstring."""
    original = [0, 3, 2, 1]  # example 3: True

    _check("grader self-test, accepted: True", original, list(original), True, True)
    _check("grader self-test, accepted: False", [3, 5, 5], [3, 5, 5], False, False)

    rejected: list[tuple[str, list[int], object, bool]] = [
        ("the wrong answer", list(original), False, True),
        ("1 in place of True", list(original), 1, True),
        ("0 in place of False", list(original), 0, False),
        ("None, from a path with no return", list(original), None, True),
        ("the summit's index instead of a verdict", list(original), 1, True),
        ("a string", list(original), "true", True),
        ("the list sorted in place", [0, 1, 2, 3], True, True),
        ("the list reversed in place", [1, 2, 3, 0], True, True),
        ("one element overwritten", [0, 3, 2, 9], True, True),
        ("the list emptied", [], True, True),
        ("an element appended", [0, 3, 2, 1, 0], True, True),
    ]
    for probe, after, returned, expected in rejected:
        with pytest.raises(AssertionError):
            _check(f"grader self-test, rejected: {probe}", original, after, returned, expected)


# ======================================================================================
# Hand-written cases. Each is (probe, arr, expected).
# ======================================================================================

Case = tuple[str, list[int], bool]

CASES: list[Case] = [
    # --- LeetCode's own examples ---------------------------------------------------------------
    ("example 1", [2, 1], False),
    ("example 2", [3, 5, 5], False),
    ("example 3", [0, 3, 2, 1], True),
    # --- too short to be a mountain, and both lengths are legal input ----------------------------
    ("a single element", [7], False),
    ("a single element, the smallest legal value", [0], False),
    ("a single element, the largest legal value", [10000], False),
    ("two elements, rising", [1, 2], False),
    ("two elements, falling", [5, 4], False),
    ("two elements, equal", [3, 3], False),
    # --- the shortest mountain there can be, and its near misses ---------------------------------
    ("three elements, a mountain", [1, 2, 1], True),
    ("three elements, rising", [1, 2, 3], False),
    ("three elements, falling", [3, 2, 1], False),
    ("three elements, flat at the summit", [1, 2, 2], False),
    ("three elements, flat at the foot", [1, 1, 2], False),
    ("three elements, all equal", [2, 2, 2], False),
    ("three elements, a valley", [2, 1, 2], False),
    ("three elements, asymmetric", [0, 100, 99], True),
    # --- where the summit sits, which is the clause about the two ends ---------------------------
    ("the summit is the first element", [5, 4, 3, 2, 1], False),
    ("the summit is the last element", [1, 2, 3, 4, 5], False),
    ("the summit is one in from the front", [1, 9, 8, 7, 6], True),
    ("the summit is one in from the back", [1, 2, 3, 9, 4], True),
    ("the summit is in the middle", [1, 4, 9, 4, 1], True),
    # --- flat steps, one at a time, everywhere they can go ---------------------------------------
    ("flat step at the very start", [1, 1, 2, 3, 2], False),
    ("flat step on the way up", [1, 2, 2, 3, 1], False),
    ("flat step at the summit", [1, 2, 3, 3, 2, 1], False),
    ("flat step on the way down", [1, 2, 3, 2, 2], False),
    ("flat step at the very end", [1, 2, 3, 2, 1, 1], False),
    ("every element equal", [4, 4, 4, 4], False),
    ("two flat steps", [1, 1, 3, 2, 2], False),
    # --- more than one summit, or a summit in the wrong place ------------------------------------
    ("two summits", [1, 3, 2, 4, 1], False),
    ("a dip inside the descent", [1, 5, 3, 4, 2], False),
    ("it climbs again after the last fall", [1, 5, 3, 1, 2], False),
    ("a mountain with one extra step tacked on", [0, 2, 1, 3], False),
    # --- constraint extremes on the values --------------------------------------------------------
    ("zeros at both feet", [0, 1, 0], True),
    ("the whole value range in three elements", [0, 10000, 0], True),
    ("a dip between two maxima", [10000, 0, 10000], False),
    ("all zeros", [0, 0, 0], False),
    ("values at the top of the range, a mountain", [9998, 10000, 9999, 0], True),
    ("values at the top of the range, no fall", [9997, 9998, 9999, 10000], False),
    ("the summit is the largest legal value", [9998, 9999, 10000, 9999], True),
    # --- long enough that an off-by-one at either end cannot hide --------------------------------
    ("24 elements, a mountain", list(range(13)) + list(range(11, 0, -1)), True),
    ("24 elements, strictly rising", list(range(24)), False),
    ("24 elements, strictly falling", list(range(23, -1, -1)), False),
    ("24 elements, flat at the summit", list(range(13)) + [12] + list(range(11, 1, -1)), False),
    ("24 elements, flat at the very end", list(range(13)) + list(range(11, 1, -1)) + [2], False),
]


@pytest.mark.parametrize("probe,arr,expected", CASES)
def test_examples_and_edges(probe: str, arr: list[int], expected: bool) -> None:
    # The table's expected values are asserted against the reference as well, so a typo in a
    # hand-written case shows up as a broken test rather than as a wrong requirement.
    assert oracle(arr) is expected, (
        f"the test case {probe!r} disagrees with the reference answer -- fix the table, "
        f"not the solution"
    )
    _run(probe, list(arr))


def test_cases_obey_the_stated_constraints() -> None:
    """The fixtures are held to the same contract the solution is.

    A case outside the constraints would demand something never asked for, and a solution that
    failed it would be right to. Checked rather than assumed: these cases are hand-written.
    """
    for probe, arr, _expected in CASES:
        assert 1 <= len(arr) <= CEILING, f"[{probe}]: 1 <= arr.length <= 10^4"
        assert all(0 <= x <= CEILING for x in arr), f"[{probe}]: 0 <= arr[i] <= 10^4"


@pytest.mark.property
def test_every_small_arrangement() -> None:
    """Every list of length 1 to 6 over a four-value alphabet, exhaustively. 5,460 lists.

    Four values are enough to build every shape the problem cares about at these lengths: a
    mountain, a rise with no fall, a fall with no rise, a plateau anywhere in either, a valley,
    and two summits. Exhaustive, so none of them is left to chance -- every flat step at every
    index, and both of the lengths too short to be a mountain at all.
    """
    for n in range(1, 7):
        for tup in product((0, 1, 2, 3), repeat=n):
            _run(f"exhaustive n={n}, arr={list(tup)}", list(tup))


def _random_mountain(rng: random.Random, n: int) -> list[int]:
    """A genuine mountain of length n with a summit in a random place and random step sizes."""
    p = rng.randint(1, n - 2)
    up = [0]
    for _ in range(p):
        up.append(up[-1] + rng.randint(1, 5))
    down = [0]
    for _ in range(n - 2 - p):
        down.append(down[-1] + rng.randint(1, 5))
    down.reverse()
    peak = max(up[-1], down[0]) + rng.randint(1, 5)
    return up[:-1] + [peak] + down


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    """Random lists, graded against the reference, inside the stated constraints.

    A list of uniformly random values is essentially never a mountain, so a generator that only
    did that would be 2,000 Falses and would prove very little. Half of these are built to be
    mountains, and half of those then have a single element rewritten -- which is where the
    interesting near misses come from, because one changed value turns a mountain into a plateau,
    a second summit, a rise with no fall or nothing at all, depending on where it lands. The
    reference decides which; nothing here assumes.
    """
    rng = random.Random(941)
    for _ in range(2000):
        style = rng.random()
        if style < 0.25:
            n = rng.randint(1, 12)
            arr = [rng.randint(0, 3) for _ in range(n)]  # narrow: flat steps everywhere
        elif style < 0.50:
            n = rng.randint(3, 50)
            arr = _random_mountain(rng, n)
        elif style < 0.75:
            n = rng.randint(3, 50)
            arr = _random_mountain(rng, n)
            arr[rng.randrange(n)] = rng.randint(0, max(arr))
        else:
            n = rng.randint(1, 30)
            arr = [rng.randint(0, 10_000) for _ in range(n)]
        assert 1 <= len(arr) <= CEILING, "the generator itself must obey the constraints"
        assert all(0 <= x <= CEILING for x in arr), "the generator must obey the constraints"
        _run(f"random n={len(arr)}, style {style:.2f}", arr)


@pytest.mark.property
def test_every_length_up_to_the_ceiling() -> None:
    """A sweep over the legal lengths, in all nine shapes, from 1 to the ceiling.

    The tests above stop at 50 elements and the timing guards below run at 1,250 and 10,000, and
    the gap between them is somewhere for a bug to live: a solution that treats the last element
    separately, or that pairs elements up two at a time, can be right on every tiny length, right
    again on a round 10,000, and wrong on 4,097.

    Every length from 1 to 120 is taken, then both sides of the round numbers and the powers of
    two above that, then a stride of 250 to the ceiling so that no window of 250 consecutive
    lengths anywhere below 10^4 goes untested.

    The whole sweep is held to a wall clock, and that is not a speed requirement -- it is a
    diagnosis instead of a silence. 1,700-odd calls land here, many of them close to the ceiling,
    so a solution whose cost grows with the length of the list can spend a very long time in a
    test that has nothing to say about speed. Measured on this repo's interpreter, CPython 3.14.4,
    the four linear solutions measured for this file get through the whole sweep in 0.11 s to
    0.15 s. The budget is 60 s, four hundred times the slowest of them, and nothing can trip it
    without having already failed both guards below.
    """
    sweep_budget = 60.0
    started = time.perf_counter()
    done = 0

    lengths = list(range(1, 121))
    for base in (128, 256, 512, 1000, 1024, 2000, 2048, 4000, 4096, 5000, 8192, CEILING):
        lengths += [base - 1, base, base + 1]
    lengths += list(range(250, CEILING, 250))
    lengths = sorted({n for n in lengths if 1 <= n <= CEILING})
    planned = sum(1 for n in lengths for _name, _make, _exp, floor in SHAPES if n >= floor)

    for n in lengths:
        for name, make, expected, floor in SHAPES:
            if n < floor:
                continue
            _run_known(f"n={n}, {name}", make(n), expected)
            done += 1
            elapsed = time.perf_counter() - started
            assert elapsed < sweep_budget, (
                f"the length sweep was abandoned after {elapsed:.0f}s and {done} of {planned} "
                f"calls, the last of them n={n}, {name}. This test grades answers, not speed, and "
                f"it is stopping only because it cannot finish: the solutions measured for this "
                f"file get through the whole sweep in 0.11 to 0.15 s. The guards below are the "
                f"ones that grade speed, and they will tell you the same thing with numbers -- "
                f"run them with `uv run pytest -m slow`."
            )

    assert done == planned, f"the sweep made {done} calls, not the {planned} it planned"


# ======================================================================================
# Timing guards.
# ======================================================================================

# The five shapes both guards below measure. The first four force a correct solution to look at
# essentially the whole list: there is no early exit available on a true mountain, none on a list
# that climbs the whole way, and none on a mountain that goes wrong at its very last step or at
# its summit.
#
# The fifth is the opposite of all four, and it is here because a guard that only ever measures
# inputs it has to read to the end has a blind spot. A list that falls from its first element is a
# "no" that is available at the first comparison, and the argument for not timing it goes: a
# correct solution answers immediately and a quadratic one answers almost as quickly, so the shape
# separates nothing. Measured, the first half of that is true and the second half is not. At 10^4
# elements a solution that verifies every
# candidate summit from scratch does get through this shape in 1.4 ms -- but one that sorts both
# slices per candidate summit takes 655 ms on it, and one that walks the list once per element
# takes 282 ms, against at most 0.153 ms for any of the four accepted solutions measured here.
#
# What an input rejected at its first comparison catches is work that is not the summit search:
# work done per element whatever the answer turns out to be, and work done before the answer is
# looked for. A guard that only ever measures inputs it has to read to the end cannot see any of
# it. The demonstration is a solution that walks the list once and, when the very first step is
# not a climb, checks exhaustively before committing to a no: on the four shapes above it measures
# 8.3x to 8.9x and 0.13 to 0.70 ms a pass, inside the accepted band on both guards and invisible
# to either, and on this fifth shape it measures 73x and 817 ms a pass.
TIMED_SHAPES: tuple[tuple[str, object, bool], ...] = (
    ("a true mountain", _mountain, True),
    ("strictly rising, never falls", _rising, False),
    ("a mountain whose last step is flat", _flat_at_the_end, False),
    ("a mountain whose summit is a plateau", _flat_at_the_peak, False),
    ("strictly falling from the first element", _falling, False),
)

REPEATS = 25  # passes at the ceiling, per shape, in test_constraint_ceiling


@pytest.mark.slow
def test_constraint_ceiling() -> None:
    """n = 10^4, the largest input the constraints allow, against a wall-clock budget.

    A single pass at the ceiling is over in well under a millisecond, too quick to measure against
    machine noise, so the budget covers 25 of them per shape. Measured on this repo's interpreter,
    CPython 3.14.4, best of three rounds. Four accepted solutions were measured; they are given as
    a band rather than named, because naming them is naming the answer and this file is meant to
    be readable while you are still solving the problem. The three rejected ones are named, since
    what they do wrong is the whole subject:

                                                        25 passes         per pass
        a true mountain
            four accepted solutions                  8.358 - 15.570 ms   0.334 - 0.623 ms
            every candidate summit verified                375.6 ms/pass
            sorted() on both slices per candidate          727.7 ms/pass
            .index() once per element, then one pass       159.2 ms/pass
        strictly rising, never falls
            four accepted solutions                  3.402 -  7.670 ms   0.136 - 0.307 ms
            every candidate summit verified               1474.6 ms/pass
            sorted() on both slices per candidate         1236.8 ms/pass
            .index() once per element, then one pass       282.6 ms/pass
        a mountain whose last step is flat
            four accepted solutions                  6.072 -  8.802 ms   0.243 - 0.352 ms
            every candidate summit verified                909.3 ms/pass
            sorted() on both slices per candidate         1092.8 ms/pass
            .index() once per element, then one pass       140.8 ms/pass
        a mountain whose summit is a plateau
            four accepted solutions                  3.381 -  8.066 ms   0.135 - 0.323 ms
            every candidate summit verified               1106.7 ms/pass
            sorted() on both slices per candidate         1256.7 ms/pass
            .index() once per element, then one pass       161.7 ms/pass
        strictly falling from the first element
            four accepted solutions                  0.003 -  3.828 ms   0.000 - 0.153 ms
            every candidate summit verified                  1.4 ms/pass  <- the one exception
            sorted() on both slices per candidate          655.3 ms/pass
            .index() once per element, then one pass       281.7 ms/pass
        ---------------------------------------------------- budget: 1.0 s for 25 passes

    The budget sits 64x above the slowest accepted total, and every rejected row but one spends it
    inside eight of its twenty-five passes -- most of them inside one or two -- so there is nothing
    subtle about the separation and no need for a tight budget to find it. Which is also why the
    loop below stops the moment the budget is gone rather than finishing the 25: past that point it
    would only be measuring how much worse the news is. The exception is marked: on a list that
    falls from its first element, a
    solution that verifies every candidate summit really is quick, because every candidate's climb
    fails at the first comparison it makes. That shape is not there to catch that solution -- the
    four above it already have, at up to 1.5 s a pass -- and the comment on TIMED_SHAPES says what
    it is there for.

    Correctness comes first, on all nine shapes at the ceiling, because a wrong answer should say
    it is wrong rather than that it is slow; those nine are not timed but they are bounded, so a
    solution slow enough to make them look like a hang gets a sentence instead of silence.
    """
    started = time.perf_counter()
    for i, (name, make, expected, _floor) in enumerate(SHAPES, start=1):
        _run_known(f"n=10^4, {name}", make(CEILING), expected)
        elapsed = time.perf_counter() - started
        assert elapsed < 30.0, (
            f"the nine correctness shapes at the ceiling were abandoned after {elapsed:.0f}s, "
            f"with {i} of them done and the last being {name}. Nothing was wrong with the "
            f"answers -- this part of the test grades answers, not speed, and it is stopping only "
            f"because a solution this slow makes it look like a hang. The four accepted solutions "
            f"measured for this file get through all nine of them in 2.8 to 4.3 ms. "
            f"The budget below is the one that grades speed, and it never got to run."
        )

    budget = 1.0
    for name, make, _expected in TIMED_SHAPES:
        data = make(CEILING)
        valid_mountain_array = Solution().validMountainArray
        elapsed, passes = 0.0, 0
        for _ in range(REPEATS):
            start = time.perf_counter()
            valid_mountain_array(data)
            elapsed += time.perf_counter() - start
            passes += 1
            if elapsed >= budget:
                break
        assert elapsed < budget, (
            f"{passes} of {REPEATS} passes over 10^4 elements ({name}) already cost "
            f"{elapsed:.2f}s -- {elapsed / passes * 1e3:.0f} ms a pass -- against a budget of "
            f"{budget}s for all {REPEATS}, and the run was cut short the moment the budget went, "
            f"so the real figure is worse. The accepted solutions measured for this budget cost "
            f"between 0.135 and 0.623 ms a pass on these five shapes. Something inside the loop "
            f"is doing work proportional to the length of the list rather than a fixed amount, "
            f"which makes the whole thing quadratic -- and quadratic is what a Time Limit "
            f"Exceeded on the submission page means."
        )


# --- the growth guard's measuring apparatus ---------------------------------------------------
#
# This problem is read-only, which makes the measurement unusually clean: the solution never
# changes what it is given, so one list can be reused for every repetition and no copy has to be
# made inside the timed region. Nothing here is measuring `list(data)` by accident.

GROWTH_CEILING = 25.0  # the ratio a solution may not exceed; see test_does_not_grow_quadratically
SMALL_N, FACTOR = 1_250, 8  # so the large size is the constraint ceiling exactly
BATCH_TARGET = 0.003  # seconds; how long one timed sample must last
HOPELESS = 0.003  # seconds for one pass at the small size; past this, report rather than measure


def _seconds_per_call(data: list[int], batch: int) -> float:
    """Seconds per call, averaged over `batch` calls on the same list."""
    valid_mountain_array = Solution().validMountainArray
    start = time.perf_counter()
    for _ in range(batch):
        valid_mountain_array(data)
    return (time.perf_counter() - start) / batch


def _batch_size(data: list[int]) -> int:
    """The smallest power-of-two batch whose run lasts at least BATCH_TARGET seconds.

    One call at n = 1,250 takes tens of microseconds, and a sample that short is not a measurement
    of the code -- it is a measurement of what else the machine was doing during it. Timing a
    batch and dividing is what keeps the number steady when the machine is busy.
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
    repetitions cannot: a process moved between a fast core and a slow one mid-measurement, with
    one side of the ratio entirely inside one of those windows, is measuring the core rather than
    the code.

    The early exit keeps nine repetitions from being slow to fail. Once three pairs are in and the
    big side is past the ceiling with 50 ms of headroom on top, more repetitions cannot bring it
    back. The 50 ms is flat rather than proportional so that a verdict is never reached on the
    strength of microseconds of interference between two sub-millisecond numbers.
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
    """Eight times the input should cost about eight times the work, on five shapes.

    The budget above already separates the two bands at the ceiling, and this is the guard that
    says the same thing without depending on how fast this machine is: a ratio is the same number
    on a slow machine and a fast one, and it stays the same number when the wall clock is busy
    with something else. The two sizes are 1,250 and 10,000, and the larger of them is the
    constraint ceiling exactly -- nothing here has to run past what the problem allows to get a
    reading, and the largest value in any of these inputs is 9,999.

    Measured on this repo's interpreter, CPython 3.14.4, nine readings of each of four accepted
    solutions on each of the five shapes -- 180 statistics in all -- and two readings of each
    rejected solution, which is enough when the nearest of them sits at more than twice the
    ceiling:

                                                          n = 1,250 -> 10,000
        a true mountain
            four accepted solutions, 36 statistics           7.43x -  9.41x
            every candidate summit verified                 78.26x - 98.55x
            sorted() on both slices per candidate summit    78.12x - 78.82x
            .index() once per element, then a single pass   60.14x - 63.29x
        strictly rising, never falls
            four accepted solutions, 36 statistics           7.51x - 10.28x
            every candidate summit verified                 75.94x - 78.36x
            sorted() on both slices per candidate summit    70.82x - 86.61x
            .index() once per element, then a single pass   66.09x - 68.09x
        a mountain whose last step is flat
            four accepted solutions, 36 statistics           7.72x -  9.33x
            every candidate summit verified                 71.59x - 73.81x
            sorted() on both slices per candidate summit    75.78x - 76.80x
            .index() once per element, then a single pass   60.66x - 63.28x
        a mountain whose summit is a plateau
            four accepted solutions, 36 statistics           8.43x -  9.62x
            every candidate summit verified                 70.09x - 71.24x
            sorted() on both slices per candidate summit    75.42x - 76.58x
            .index() once per element, then a single pass   62.22x - 62.35x
        strictly falling from the first element
            four accepted solutions, 36 statistics           0.81x -  8.77x
            every candidate summit verified                  7.80x -  8.08x  <- the exception
            sorted() on both slices per candidate summit    75.24x - 76.48x
            .index() once per element, then a single pass   68.52x - 71.17x
        ---------------------------------------------------------- ceiling: 25x

    Across all 180 accepted readings the worst was 10.28x; across the rejected readings the best
    that is a real reading of quadratic work was 60.14x. The ceiling sits in that gap, nearer the
    bottom of it than the middle, because failing a correct solution is a worse outcome here than
    letting a slow one through -- and a slow one still has the ceiling budget above, and a
    submission page, to get past.

    Two rows in the last block need reading carefully, and neither is a hole. The accepted band
    starts at 0.81x there because one of the four answers the question at the first comparison and
    does the same fixed work at both sizes: 1x is what constant time looks like in this statistic,
    and it is a long way under a ceiling, not over it. The marked row is the per-candidate-summit
    solution, which is genuinely linear on this shape -- every candidate's climb fails at the first
    comparison it makes -- so this shape does not catch it. The four shapes above it do, at 70x and
    upwards, which is why the guard measures all five and not one.

    A ratio over the ceiling is measured again before it is reported, up to three times in all,
    and only fails if every attempt agrees. The re-measurement is for the machine's benefit, not
    the solution's: a quadratic solution is over the ceiling every single time, while an excursion
    that far out is not something a correct solution produces three times running. A ratio past
    twice the ceiling is not re-measured at all -- nothing that far out is noise.
    """
    attempts = 3
    for name, make, expected in TIMED_SHAPES:
        small, big = make(SMALL_N), make(SMALL_N * FACTOR)

        # Correctness at both timed sizes, checked once and outside the timing. A wrong answer
        # should say it is wrong, not that it is slow.
        _run_known(f"n={SMALL_N:,}, {name}", list(small), expected)
        _run_known(f"n={SMALL_N * FACTOR:,}, {name}", list(big), expected)

        # A cheap look before committing to the full measurement. Across all five shapes the four
        # accepted solutions cost between 0.0001 and 0.078 ms for one pass at this size, and the
        # rejected ones cost between 2.43 and 19.74 ms -- except on the shape they leave at the
        # first comparison, where the per-candidate-summit solution costs 0.16 ms and this probe
        # rightly says nothing about it. So 3 ms sits between the two bands with 38x of room above
        # the slowest right answer measured. This is not the guard -- the ratio below is, and it
        # catches what slips through here. It is here so that something spending a second a pass is
        # told so in a moment rather than timed nine times over at eight times the size.
        probe = min(_seconds_per_call(small, 1) for _ in range(3))
        assert probe < HOPELESS, (
            f"one pass over {SMALL_N:,} elements ({name}) took {probe * 1e3:.2f} ms, so the "
            f"growth measurement was not attempted: at eight times the length, nine repetitions "
            f"a side would take minutes. The four accepted solutions measured for this file cost "
            f"between 0.0001 and 0.078 ms here. test_constraint_ceiling above has already reported "
            f"this with a per-pass number attached; the shape of the growth is not the interesting "
            f"question until the size of it is fixed."
        )

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
            f"of the list, which at n = 10^4 is a Time Limit Exceeded. The algorithm may well be "
            f"right -- look instead for a step inside the loop that is not O(1). Re-checking a "
            f"stretch of the list you have already been over is the usual cause here; `in`, "
            f".index(), .count(), min(), max() and sorted() each walk the whole list on their "
            f"own, and slicing copies it."
        )


# ---------------------------------------------------------------------------------------
# What this suite does NOT check, and why none of it is an oversight.
#
# EXTRA SPACE. Not measured. The stub names O(1) extra space as the target because that is the bar
# this problem is usually held to, but the constraints do not force it: 10^4 elements is small
# enough that a solution which slices `arr` in two and checks each half is accepted by the judge,
# and both timing guards above accept it too -- one of the four solutions measured for them does
# exactly that. Chapter 5 is where constant extra space becomes the subject, and inventing the
# requirement here would fail a right answer for a property nobody asked for.
#
# WHICH ROUTE THE SOLUTION TOOK. No static check on any name. The contract is the answer, not the
# method; the guards reject what is too slow, and everything fast enough is accepted whatever it
# is made of.
#
# TIME *IS* checked, and unlike in 1346 next door that is not an addition -- it is what the
# constraints already require. n reaches 10^4 and a per-candidate-summit solution takes over a
# second on a single call at that size, so the judge rejects it too. The sibling suite for 1346
# has no growth guard at all, for the mirror-image reason: its ceiling is 500, where the same
# shape finishes in 4 ms and the judge accepts it.
#
# READ-ONLY *IS* an addition, and it is the one thing here the judge does not grade. LeetCode
# hands this method a list, reads the boolean that comes back, and never looks at the list again,
# so a solution that sorts `arr` in place is accepted there. It fails here, and the reason is
# worth saying out loud rather than leaving as a surprise: chapters 2 and 3 spent their whole
# length on writing into the caller's list, and the discipline that makes those problems work is
# knowing exactly when you are allowed to. This problem is a place to practise not doing it. The
# stub says so in as many words, twice.
# ---------------------------------------------------------------------------------------
