"""Spec for 1346. Check If N and Its Double Exist.

Chapters 2 and 3 wrote their answers into the list they were handed. This one does not touch it.
`arr` is input, the answer is the value that comes back, and the list must be exactly as it
arrived when the call returns. That is chapter 1's contract again, and three things are enforced
here.

1. `checkIfExist` returns a real `bool` -- True or False, not 1, not 0, not None, not the pair it
   found. bool is a subclass of int in Python and the relationship runs one way: isinstance(True,
   int) is True while isinstance(1, bool) is False, and 1 == True either way. This suite checks
   the type rather than the truthiness, so 1 in place of True is rejected.
2. The value is right. The answer key comes from the reference in `tests/_reference/`, which is
   the statement transcribed literally, and it is computed from a pristine snapshot taken before
   the call -- so a solution cannot rewrite its own answer key.
3. `arr` comes back untouched. Same length, same elements, same order. This one is checked on
   every single call in this file, not in a test of its own, because there is no call on which it
   is allowed to fail.

What this suite deliberately does NOT police:

  speed, at all           There is no timing guard anywhere in this file, and no growth guard
                          either. Not a loose one, not a generous one, not one dressed up as a
                          diagnostic. The reason is the whole shape of this problem: arr.length
                          stops at 500, so a nested loop over every pair of positions is about
                          250,000 comparisons, and it is an accepted answer on the submission
                          page. Measured on this repo's interpreter, CPython 3.14.4, over the 60
                          calls at n = 500 that `test_constraint_ceiling` makes, a third of them
                          holding no pair at all so the search has to run to the end, that nested
                          loop costs single-digit milliseconds a call. There is no wall clock
                          that fails it without also being noise, and a suite that failed it
                          would be inventing a requirement the problem does not have. Note that
                          the ceiling is not what settles this. The sibling suite for 27 in
                          chapter 3 polices shape at a ceiling of 100, which is lower than this
                          one, and it is right to: there the quadratic cost comes from an
                          operation that moves the whole tail of the list once per element, and
                          that is the mistake the chapter is about. Here it comes from reading
                          the statement literally and comparing every pair, which is not a
                          mistake. The stub's Target line points at O(n) because it is worth
                          finding, not because anything here will fail you for missing it.

  extra space             Not measured at all. Read-only says where the answer is read from; it
                          does not forbid scratch space, and a solution that builds a structure
                          the size of `arr` alongside it is as accepted as one that does not.
                          Chapter 5 is where constant extra space becomes the subject.

  which route was taken   No static check on `sorted`, on `set`, on `in`, on `bisect` or on
                          anything else. The contract is the answer, not the method.

Reading `arr` is unrestricted. What is banned is *writing* to it, and the difference is worth
being precise about, because the read-only rule is easy to over-read: `sorted(arr)` builds a new
list and leaves `arr` alone, so it passes; `arr.sort()` rewrites `arr` where it stands, so it
fails. A solution is free to copy the input and do anything at all to the copy.
"""

import random
from itertools import product

import pytest

from arrays101.ch04.p01_check_double_exists import Solution
from tests._reference.p01_check_double_exists import oracle


def solve(arr: list[int]) -> object:
    """Run the solution and hand back its return value, which must be a bool."""
    return Solution().checkIfExist(arr)


# ======================================================================================
# Contract checking, shared by every test below.
# ======================================================================================


def _render(value: object, limit: int = 24) -> str:
    """A repr that stays readable when the list has hundreds of elements in it."""
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


def _check(probe: str, original: list[int], arr: list[int], returned: object,
           expected: bool) -> None:
    """Assert the whole contract for one call.

    `original` is a pristine snapshot taken before the call; `arr` is the list the solution was
    handed. `expected` is graded against the snapshot, never against whatever came back.
    """
    where = f"{probe}: checkIfExist({_render(original)})"

    # `type(returned) is bool` rather than isinstance, and the exactness is the point: bool is a
    # subclass of int, so a check for int would let True and 1 both through. The two spellings
    # happen to agree here -- bool cannot be subclassed, `class B(bool)` raises TypeError: type
    # 'bool' is not an acceptable base type on this interpreter -- and the identity check is used
    # anyway, because it says what is meant without resting on that.
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
        elif isinstance(returned, tuple | list):
            extra = ". The question is whether such a pair exists, not which pair it is"
        raise AssertionError(
            f"{where} returned {_render(returned)}, of type {type(returned).__name__}. It must "
            f"return True or False{extra}."
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
                    "sorted or reversed arr where it stands. sorted(arr) and arr[:] hand back new "
                    "lists and leave arr alone; arr.sort() and arr.reverse() do not"
                )
        raise AssertionError(
            f"{where} modified arr. This problem is read-only: arr is input, the answer is the "
            f"value you return, and nobody reads arr again afterwards. {detail}. Afterwards arr "
            f"was {_render(arr)}. Copy it and rewrite the copy if you need to."
        )

    if returned != expected:
        detail = ""
        if expected is False and original.count(0) == 1:
            detail = (
                ". arr holds exactly one zero. 0 == 2 * 0, so a single zero looks like a pair to "
                "any check that lets i and j land on the same position -- and i != j says they "
                "cannot. Two zeros would be a genuine pair; one is not"
            )
        elif expected is True and original.count(0) >= 2:
            detail = (
                ". arr holds two or more zeros, and that is a genuine pair: two different "
                "positions i and j with arr[i] == 2 * arr[j], both values being 0"
            )
        elif expected is True and any(x < 0 for x in original):
            detail = (
                ". The pair here involves negative values, where the double of an element is "
                "smaller than the element rather than larger"
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

    The reference is O(n^2) on purpose -- it is the statement transcribed, and being obviously
    right matters more there than being quick. That makes it the wrong tool at the constraint
    ceiling, so the long inputs in this file are built by the shape functions below, whose answers
    are known by construction. `test_the_shape_builders_are_what_they_claim` holds those
    constructions to the reference at sizes where the reference is cheap, so nothing here rests on
    a builder being trusted rather than checked.
    """
    original = list(arr)
    returned = solve(arr)
    _check(probe, original, arr, returned, expected)


# ======================================================================================
# Shapes used by more than one test below, all with answers known by construction.
# ======================================================================================

CEILING = 500  # the constraint ceiling: 2 <= arr.length <= 500

# Odd values from 501 to 999. One fact makes this pool a guaranteed no-pair list on its own: every
# value in it is odd, and 2 * anything is even, so no element here can equal the double of any
# other. Twice the smallest of them is 1002, past the largest value the constraints allow, which
# is a second reason for the same thing. Every shape below starts from this pool and then plants
# exactly the pair, or exactly the near-miss, that it is named for.
_ODD_POOL = tuple(range(501, 1000, 2))


def _odds(n: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.choice(_ODD_POOL) for _ in range(n)]


def _no_pair(n: int, seed: int = 1) -> list[int]:
    """Nothing doubles anything. The search has to run to the end to find that out."""
    return _odds(n, seed)


def _pair_at_the_end(n: int, seed: int = 2) -> list[int]:
    """The only pair is the last two elements: the latest a scan can possibly find one."""
    a = _odds(n, seed)
    a[-2], a[-1] = 4, 8
    return a


def _pair_at_the_front(n: int, seed: int = 3) -> list[int]:
    """The only pair is the first two elements: the earliest a scan can find one."""
    a = _odds(n, seed)
    a[0], a[1] = 4, 8
    return a


def _pair_at_the_two_ends(n: int, seed: int = 4) -> list[int]:
    """The two halves of the pair are as far apart as the list allows."""
    a = _odds(n, seed)
    a[0], a[-1] = 4, 8
    return a


def _double_before_its_half(n: int, seed: int = 8) -> list[int]:
    """The double comes first and its half comes last, so the pair only reads backwards.

    Every shape above this one can be found by a scan that, standing on an element, looks ahead
    for twice that element. This one cannot: the 8 is at the front and the 4 it doubles is at the
    back, so the only way to see the pair is to look behind you, or to look for halves as well as
    doubles, or not to care about direction at all.
    """
    a = _odds(n, seed)
    a[0], a[-1] = 8, 4
    return a


def _interior(n: int) -> tuple[int, int]:
    """Two distinct positions a third and two thirds of the way in, for any legal length.

    From n = 4 up these are both strictly inside the list, which is the point of the shapes that
    use them. On the two shortest legal lengths there is no strict interior to reach for and they
    fall back to whatever positions exist, which costs nothing: the shapes stay valid, they just
    stop being about the interior at a size where nothing has one.
    """
    return n // 3, (2 * n) // 3


def _pair_in_the_middle(n: int, seed: int = 9) -> list[int]:
    """The only pair sits away from both ends.

    Every shape above plants what it is about at index 0, 1, n - 2 or n - 1, so between them they
    say nothing about a solution that treats the middle of a long list differently from its edges
    -- one that scans a window, or splits the list in half, or takes a shortcut once the input is
    bigger than the cases it was tried on. This shape is the interior case, at every length the
    sweep visits.
    """
    a = _odds(n, seed)
    lo, hi = _interior(n)
    a[lo], a[hi] = 4, 8
    return a


def _negative_double_before_its_half_in_the_middle(n: int, seed: int = 10) -> list[int]:
    """The interior positions again, with a negative pair that also reads backwards.

    Three things at once, all of which the shapes above test only at the ends: the pair is in the
    middle, the double comes before its half, and both values are negative so the double is the
    smaller of the two.
    """
    a = _odds(n, seed)
    lo, hi = _interior(n)
    a[lo], a[hi] = -600, -300
    return a


def _one_zero(n: int, seed: int = 5) -> list[int]:
    """Exactly one zero, and no pair. The i != j trap, at whatever size is asked for."""
    a = _odds(n, seed)
    a[-1] = 0
    return a


def _one_zero_in_the_middle(n: int, seed: int = 11) -> list[int]:
    """The same trap, with the zero away from either end rather than at the last index."""
    a = _odds(n, seed)
    a[n // 2] = 0
    return a


def _two_zeros(n: int, seed: int = 6) -> list[int]:
    """Two zeros, which are a genuine pair, and nothing else that is."""
    a = _odds(n, seed)
    a[-2] = a[-1] = 0
    return a


def _negative_pair(n: int, seed: int = 7) -> list[int]:
    """The only pair is negative, so the double is the smaller of the two values."""
    a = _odds(n, seed)
    a[-2], a[-1] = -300, -600
    return a


# (name, builder, the answer it is built to have)
SHAPES: tuple[tuple[str, object, bool], ...] = (
    ("no pair anywhere", _no_pair, False),
    ("the pair is the last two elements", _pair_at_the_end, True),
    ("the pair is the first two elements", _pair_at_the_front, True),
    ("the pair sits at the two ends", _pair_at_the_two_ends, True),
    ("the double sits before its half", _double_before_its_half, True),
    ("the pair sits in the middle", _pair_in_the_middle, True),
    ("a negative double before its half, both in the middle",
     _negative_double_before_its_half_in_the_middle, True),
    ("exactly one zero, and no pair", _one_zero, False),
    ("exactly one zero in the middle, and no pair", _one_zero_in_the_middle, False),
    ("two zeros", _two_zeros, True),
    ("the only pair is negative", _negative_pair, True),
)


def test_the_shape_builders_are_what_they_claim() -> None:
    """Every builder above, at every length the reference can afford, against the reference.

    The long inputs in this file are graded against the answer the builder promises rather than
    against the reference, because the reference is quadratic and the ceiling is 500 elements. So
    the promise itself is checked here, at sizes where checking is cheap: if a builder ever stops
    producing what it says on the label, this test fails rather than some unrelated test quietly
    grading against the wrong answer.
    """
    for name, make, expected in SHAPES:
        for n in range(2, 61):
            arr = make(n, 99)
            assert len(arr) == n, f"{name}: builder returned {len(arr)} elements, wanted {n}"
            assert all(-1000 <= x <= 1000 for x in arr), f"{name} at n={n}: -10^3 <= arr[i] <= 10^3"
            assert oracle(arr) is expected, (
                f"the builder {name!r} at n={n} produced {_render(arr)}, whose real answer is "
                f"{oracle(arr)} and not the {expected} it promises -- fix the builder, not the "
                f"solution"
            )


# ======================================================================================
# The grader itself, against the contract.
# ======================================================================================


def test_the_grader_holds_the_contract_it_describes() -> None:
    """What `_check` accepts and rejects, pinned down rather than asserted in a docstring."""
    original = [10, 2, 5, 3]  # example 1: True

    # Accepted: the right bool, with arr handed back exactly as it arrived.
    _check("grader self-test, accepted: True", original, list(original), True, True)
    _check("grader self-test, accepted: False", [3, 1, 7, 11], [3, 1, 7, 11], False, False)

    rejected: list[tuple[str, list[int], object, bool]] = [
        ("the wrong answer", list(original), False, True),
        ("1 in place of True", list(original), 1, True),
        ("0 in place of False", list(original), 0, False),
        ("None, from a path with no return", list(original), None, True),
        ("the pair itself instead of a verdict", list(original), [10, 5], True),
        ("a count instead of a verdict", list(original), 2, True),
        ("a string", list(original), "true", True),
        ("the list sorted in place", [2, 3, 5, 10], True, True),
        ("the list reversed in place", [3, 5, 2, 10], True, True),
        ("one element overwritten", [10, 2, 5, 99], True, True),
        ("the list emptied", [], True, True),
        ("an element appended", [10, 2, 5, 3, 0], True, True),
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
    ("example 1", [10, 2, 5, 3], True),
    ("example 2", [3, 1, 7, 11], False),
    # --- the smallest legal input, which is two elements ----------------------------------------
    ("two elements, the value then its double", [1, 2], True),
    ("two elements, the double then the value", [2, 1], True),
    ("two elements, unrelated", [3, 5], False),
    ("two elements, equal and non-zero", [4, 4], False),
    ("two elements, one is three times the other", [3, 9], False),
    # --- zero, which is the whole reason i != j is in the statement -----------------------------
    ("two elements, a lone zero and an odd value", [0, 1], False),
    ("a single zero and nothing else to pair with", [0, 3], False),
    ("a single zero in the middle of a longer list", [1, 0, 5, 7], False),
    ("a single zero at the front", [0, 1, 3, 5], False),
    ("a single zero at the back", [1, 3, 5, 0], False),
    ("two zeros", [0, 0], True),
    ("two zeros and an odd value", [0, 0, 1], True),
    ("two zeros at opposite ends", [0, 3, 5, 7, 0], True),
    ("three zeros", [0, 0, 0], True),
    ("a zero and an even value, which is still no pair", [0, 2], False),
    ("a single zero alongside a genuine pair elsewhere", [0, 3, 6], True),
    # --- negatives, where the double is the smaller value ---------------------------------------
    ("a negative pair", [-2, -4], True),
    ("a negative pair, the double first", [-4, -2], True),
    ("a negative pair, minus ten and minus five", [-10, -5], True),
    ("negatives with no pair", [-3, -5, -7], False),
    ("opposite signs, no pair", [-2, 4], False),
    ("opposite signs, no pair, other order", [2, -4], False),
    ("a negative pair among positives", [7, -3, 11, -6], True),
    # --- where the pair sits, and which way round it reads --------------------------------------
    ("the pair is the first two elements", [3, 6, 7, 9, 11], True),
    ("the pair is the last two elements", [7, 9, 11, 3, 6], True),
    ("the pair straddles the whole list", [3, 7, 9, 11, 6], True),
    ("the pair is in the middle", [7, 3, 6, 9, 11], True),
    ("the double comes before its half", [11, 9, 6, 7, 3], True),
    ("the double comes first, its half comes last", [6, 9, 11, 7, 3], True),
    ("the half comes first, its double comes last", [3, 9, 11, 7, 6], True),
    # --- values that are near misses ------------------------------------------------------------
    ("every element odd, so no element can be a double", [1, 3, 5, 7, 9], False),
    ("every element the same, non-zero", [5, 5, 5], False),
    ("a value repeated alongside its double", [2, 4, 4], True),
    ("a chain of doublings", [1, 2, 4, 8], True),
    ("halves present but doubles absent", [1, 3, 5, 11], False),
    ("off by one from a pair", [4, 9], False),
    # --- constraint extremes on the values -------------------------------------------------------
    ("the top of the value range, paired", [500, 1000], True),
    ("the bottom of the value range, paired", [-1000, -500], True),
    ("both ends of the value range, unpaired", [-1000, 1000], False),
    ("values whose doubles fall outside the legal range", [600, 700, 1000], False),
    ("the largest and smallest legal values with a zero", [-1000, 0, 1000], False),
    # --- long enough that an off-by-one at either end cannot hide --------------------------------
    ("24 elements, no pair", list(range(1, 48, 2)), False),
    ("24 elements, the pair is the last two", list(range(1, 44, 2)) + [4, 8], True),
    ("24 elements, the pair is the first two", [4, 8] + list(range(1, 44, 2)), True),
    ("24 elements, the double first and its half last", [8] + list(range(1, 44, 2)) + [4], True),
    ("24 elements, a lone zero at the end", list(range(1, 46, 2)) + [0], False),
    ("24 elements, a lone zero at the front", [0] + list(range(1, 46, 2)), False),
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
        assert 2 <= len(arr) <= CEILING, f"[{probe}]: 2 <= arr.length <= 500"
        assert all(-1000 <= x <= 1000 for x in arr), f"[{probe}]: -10^3 <= arr[i] <= 10^3"


@pytest.mark.property
def test_every_small_arrangement() -> None:
    """Every list of length 2 to 5 over a five-value alphabet, exhaustively. 3,900 lists.

    The alphabet is (-2, -1, 0, 1, 2), which is small but carries every relationship the problem
    can be about: a pair going up (1 and 2), a pair going down in magnitude (-1 and -2), zero on
    its own, zero repeated, and values that pair with nothing. Exhaustive, so no arrangement of
    them is left to chance -- every position for the zero, every position for each half of a pair,
    every ordering of the two halves, and every list that contains neither.
    """
    for n in range(2, 6):
        for tup in product((-2, -1, 0, 1, 2), repeat=n):
            _run(f"exhaustive n={n}, arr={list(tup)}", list(tup))


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    """Random lists, graded against the reference, inside the stated constraints.

    The value range is varied on purpose. Over the full -1000..1000 range a random list almost
    never contains a pair, so most of these would be Falses that prove very little; the narrow
    ranges make pairs common, and the zero-heavy ones make the i != j question come up over and
    over. All three matter, so all three are generated.
    """
    rng = random.Random(1346)
    for _ in range(2000):
        n = rng.randint(2, 40)
        style = rng.random()
        if style < 0.30:
            # Narrow, so doubles land inside the list often.
            arr = [rng.randint(-4, 4) for _ in range(n)]
        elif style < 0.55:
            # Zero-heavy: the trap comes up with one zero and with several.
            arr = [0 if rng.random() < 0.4 else rng.randint(-6, 6) for _ in range(n)]
        elif style < 0.75:
            # Powers of two, where chains of doublings are everywhere.
            arr = [rng.choice([1, 2, 4, 8, 16, 32, -1, -2, -4, -8]) for _ in range(n)]
        else:
            # The full legal range, where a pair is a rare accident.
            arr = [rng.randint(-1000, 1000) for _ in range(n)]
        assert all(-1000 <= x <= 1000 for x in arr), "the generator must obey the constraints"
        _run(f"random n={n}, style {style:.2f}", arr)


@pytest.mark.property
def test_every_length_up_to_the_ceiling() -> None:
    """A sweep over the legal lengths, in every shape above, from 2 to the ceiling.

    The tests above stop at 40 elements and the ceiling test below runs only at 500, and a gap
    like that is somewhere for a bug to live: a solution that handles the last element separately,
    or that walks the list in fixed-size chunks, can be right on every tiny length, right again on
    a round 500, and wrong on 37.

    Every length from 2 to 120 is taken, then both sides of the round numbers and the powers of
    two above that, then a stride of 20 to the ceiling so that no window of twenty consecutive
    lengths anywhere below 500 goes untested. Nothing here is timed. This test grades answers.

    Both halves of that matter, the shapes as much as the lengths, and the shapes are the half
    that is easy to leave thin: the pair, the lone zero and the negatives are each planted in the
    middle of the list as well as at its ends, so a length in this range is never tested only with
    the interesting element sitting at index 0, 1, n - 2 or n - 1.
    """
    done = 0

    lengths = list(range(2, 121))
    for base in (128, 200, 250, 256, 300, 400, 500):
        lengths += [base - 1, base, base + 1]
    lengths += list(range(120, CEILING, 20))
    lengths = sorted({n for n in lengths if 2 <= n <= CEILING})
    planned = len(lengths) * len(SHAPES)

    for n in lengths:
        for name, make, expected in SHAPES:
            _run_known(f"n={n}, {name}", make(n), expected)
            done += 1

    assert done == planned, f"the sweep made {done} calls, not the {planned} it planned"


# ======================================================================================
# The constraint ceiling. Correctness at full size, and nothing about speed.
# ======================================================================================


def _ceiling_cases(count: int = 60, n: int = CEILING,
                   seed: int = 1346) -> list[tuple[list[int], bool]]:
    """`count` lists at the constraint ceiling, cycling through six shapes.

    Two of the six have no pair in them, which is what makes the search run all the way to the end
    rather than stopping the moment it gets lucky. One of those two is the lone-zero shape, so the
    trap is exercised at full size as well as in the small cases above. Where a shape plants two
    values, it plants them at two positions drawn at random rather than at the end every time, so
    the pair is not always in the same place and a solution cannot be accidentally right by only
    ever looking there.

    Every shape starts from the odd pool, which holds no pair of its own, so whatever is planted
    is the only pair there is and the answer is known by construction.
    """
    rng = random.Random(seed)
    out: list[tuple[list[int], bool]] = []
    for i in range(count):
        arr = [rng.choice(_ODD_POOL) for _ in range(n)]
        lo, hi = sorted(rng.sample(range(n), 2))
        kind = i % 6
        if kind == 1:
            arr[lo], arr[hi] = 4, 8  # the half first, then its double
        elif kind == 2:
            arr[lo], arr[hi] = 8, 4  # the double first, then its half
        elif kind == 3:
            arr[lo] = arr[hi] = 0  # two zeros, a genuine pair
        elif kind == 4:
            arr[lo], arr[hi] = -300, -600  # a negative pair
        elif kind == 5:
            arr[lo] = 0  # exactly one zero, and no pair
        out.append((arr, kind in (1, 2, 3, 4)))
    return out


@pytest.mark.slow
def test_constraint_ceiling() -> None:
    """n = 500, the largest input the constraints allow. Answers only -- there is no clock here.

    Read this before reading the code, because a test named after the constraint ceiling usually
    comes with a budget attached and this one deliberately does not. arr.length stops at 500. A
    nested loop over every pair of positions is 250,000 comparisons, it is an accepted answer on
    the submission page, and it must pass here unchanged. Measured on this repo's interpreter,
    CPython 3.14.4, over the 60 cases this function builds -- all at n = 500, a third of them
    holding no pair at all, so that a third of the calls cannot stop early at any point -- the
    shapes measured for this file order like this per call, four rounds of best-of-five:

        a nested loop over every ordered pair       the slowest measured, a few ms per call
        a nested loop over every unordered pair     three quarters to nine tenths of that
        one scan of the whole list per element      between a fifth and a third of it
        the quickest single-pass shapes measured    around two hundred times quicker, and more

    Only the ordering and the ratios are quoted, because those are what reproduced across the four
    rounds. All four rows are milliseconds or less per call, and no wall-clock number can separate
    the top of that list from the bottom without also being a measurement of what else the machine
    was doing. So none is asserted. The gap in the last row is a reason to go looking for a better
    answer; it is not a threat from the grader, and this file will never fail you for being
    quadratic.

    What is checked is what the problem actually asks: the right bool, on the largest inputs it
    allows, with `arr` handed back untouched. These are the only full-size inputs in the file, and
    the shapes are the ones a smaller test cannot reach -- 500 elements with a single pair buried
    at two random positions in them, and 500 elements with no pair at all.
    """
    cases = _ceiling_cases()
    for i, (arr, expected) in enumerate(cases):
        assert len(arr) == CEILING, f"ceiling case {i}: built {len(arr)} elements, wanted {CEILING}"
        assert all(-1000 <= x <= 1000 for x in arr), f"ceiling case {i}: -10^3 <= arr[i] <= 10^3"
        _run_known(f"ceiling case {i}, n={CEILING}", list(arr), expected)


# ---------------------------------------------------------------------------------------
# What this suite does NOT check, and why none of it is an oversight.
#
# SPEED. There is no timing guard and no growth guard in this file, and adding one would be a bug
# in the suite rather than an improvement to it. n <= 500 and the problem states no complexity
# requirement, so a nested loop over every pair of positions is accepted by the judge, and a suite
# that failed it would be inventing a requirement the problem does not have. The size of the
# ceiling is not what settles this: chapter 3's suite for 27 polices shape at a ceiling of 100,
# lower than this one. What differs is where the quadratic cost comes from. There it comes from an
# operation that moves the whole tail of the list once per element, which is the mistake that
# chapter exists to catch; here it comes from taking the statement at its word and comparing every
# pair, which is not a mistake, and the honest thing is to leave that answer alone. The stub's
# Target line says O(n) is available and worth finding, and stops there on purpose.
#
# EXTRA SPACE. Not measured. Read-only constrains what happens to `arr`, not how much memory a
# solution allocates beside it. Chapter 5 is where constant extra space becomes the subject.
#
# WHICH ROUTE THE SOLUTION TOOK. No static check on any name. Whatever produces the right bool
# without writing into `arr` is accepted.
#
# READ-ONLY *IS* an addition, and it is the one thing here the judge does not grade. LeetCode
# hands this method a list, reads the boolean that comes back, and never looks at the list again,
# so a solution that sorts `arr` in place is accepted there. It fails here, and the reason is
# worth saying out loud rather than leaving as a surprise: chapters 2 and 3 spent their whole
# length on writing into the caller's list, and the discipline that makes those problems work is
# knowing exactly when you are allowed to. This problem is a place to practise not doing it. The
# stub says so in as many words, twice.
# ---------------------------------------------------------------------------------------
