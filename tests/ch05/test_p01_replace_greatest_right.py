"""Spec for 1299. Replace Elements with Greatest Element on Right Side.

Chapter 2 wrote its answer into the list and returned nothing. Chapter 4 returned a value and left
the list alone. This one does both halves at once, and neither is optional. Five contracts are
enforced here.

1. `arr` itself is rewritten. The caller keeps a reference to the list it handed over, and that
   list has to hold the answer when the call returns.
2. The value that comes back IS that same list. `_check` tests identity, not equality: a fresh
   list with perfect contents fails, however right it looks, and so does `None`. `arr[:] = ...`
   rewrites the list where it stands and returns nothing, so a solution is free to work the answer
   out somewhere else and then put it where it belongs.
3. `len(arr)` is unchanged. n elements in, n elements out.
4. The contents are exact. Every position holds the greatest of the values that were to its right
   when the call started, and the last position holds -1. There is one right answer per input.
5. n = 10^4, the constraint ceiling, and the shape of the work below it.

Contract 2 is this file's own addition, and it is worth saying so plainly rather than leaving it
as a surprise. The judge reads the array that comes back and never looks at the one it handed
over, so a solution that builds a new list and returns it is accepted there. It fails here. The
chapter is about rewriting a list where it stands, this problem is the gentlest place in it to
practise that, and a suite that accepted a fresh list would let the whole exercise be skipped.
The stub says so in as many words.

What this suite deliberately does NOT police:

  extra space         Not measured at all. Nothing counts allocations, and a solution that works
                      the answer out in a list of its own and then writes it into `arr` is
                      accepted -- that is the point of contract 2 being about where the answer
                      ends up rather than about how it was reached. Three of the six correct
                      solutions measured for this file's numbers do exactly that, and the quickest
                      of the six is one of them.

  which route         No static check on any name, and none on the route either. Whatever leaves
                      the right contents in `arr` and hands `arr` back is accepted.

  the tail            There is no tail. Unlike chapter 3's problems, every one of the n slots is
                      read, so nothing here is "not important".

Time is policed three times, and the three guards see different things. `test_constraint_ceiling`
holds 20 calls at n = 10^4 to a wall-clock budget, and at this ceiling that budget genuinely
separates the field: measured on this repo's interpreter, CPython 3.14.4, six correct solutions took
2.73 - 5.30 ms for all 20, and seven that go and look for each answer separately took between 1.1
and 22.8 seconds. `test_does_not_grow_quadratically` times the same code at n and 8n on five shapes,
where the shape of the growth is unmistakable and no wall clock is involved.
`test_cost_per_element_holds_across_the_length_range` takes the per-element cost at five sizes from
1,000 to the ceiling and asks that it be the same number at all of them. No guard is redundant: one
solution measured is invisible to the ratio on all five shapes and is caught only by the budget,
three more are invisible to the ratio AND to the budget -- their extra work begins and ends between
the sizes those two sample -- and are caught only by the ladder. The numbers for all of them are in
the docstrings below along with everything else measured here.
"""

import random
import time
from collections.abc import Callable
from itertools import product

import pytest

from arrays101.ch05.p01_replace_greatest_right import Solution
from tests._reference.p01_replace_greatest_right import oracle


def solve(arr: list[int]) -> object:
    """Run the solution and hand back its return value, which must be `arr` itself."""
    return Solution().replaceElements(arr)


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


def _excerpt(values: list[int], i: int, radius: int = 3) -> str:
    """A few elements either side of index i.

    `_render` shows the two ends of a long list, which is exactly the wrong window when the
    disagreement is in the middle: two lists that differ at index 4,000 render identically, and the
    report then looks like it is complaining about nothing. This shows the neighbourhood instead.
    """
    lo, hi = max(0, i - radius), min(len(values), i + radius + 1)
    body = ", ".join(str(x) for x in values[lo:hi])
    return f"[{'..., ' if lo else ''}{body}{', ...' if hi < len(values) else ''}]"


def _first_difference(got: list[int], want: list[int]) -> int | None:
    for i, (a, b) in enumerate(zip(got, want)):
        if a != b:
            return i
    return None


def _inclusive(original: list[int]) -> list[int]:
    """What the answer becomes if a position is allowed to count itself.

    The single most common wrong answer to this problem, and worth naming rather than reporting as
    an anonymous mismatch at index 0.
    """
    n = len(original)
    return [max(original[i:]) if i + 1 < n else -1 for i in range(n)]


def _check(probe: str, original: list[int], arr: list[int], returned: object) -> None:
    """Assert the whole contract for one call.

    `original` is a pristine snapshot taken before the call; `arr` is the list the solution was
    handed. The answer key is computed from the snapshot, so a solution cannot rewrite its own
    answer key.
    """
    expected = oracle(original)
    where = f"{probe}: replaceElements({_render(original)})"

    # Identity, not equality. `returned is arr` is the whole of contract 2, and the diagnostics
    # below exist because "wrong object" is an unhelpful thing to be told on its own.
    if returned is not arr:
        if returned is None:
            detail = (
                "It returned None. This problem is not chapter 2's contract: the statement says "
                "to return the array after modifying it, and the signature says list[int]. If arr "
                "is already right, the fix is one `return arr`"
            )
        elif isinstance(returned, list) and returned == expected and arr == original:
            detail = (
                "It returned a correct list -- but a different one, and arr came back exactly as "
                "it was handed over. On the judge this is ACCEPTED: it reads what you return and "
                "never looks at the array it handed over, so this is not a bug and you have not "
                "misunderstood the problem. This repo asks for more, on purpose and only here, "
                "because rewriting a list where it stands is the whole subject of this chapter "
                "and 1299 is where you first meet it. The caller keeps a reference to arr, and "
                "this chapter is about rewriting that list where it stands. `arr[:] = your_answer` "
                "writes your list into the caller's; rebinding the name arr only points your local variable "
                "somewhere else"
            )
        elif isinstance(returned, list):
            detail = (
                f"It returned a list, but not this one. What came back was {_render(returned)} "
                f"and arr itself holds {_render(arr)}. Both halves are read: arr has to be "
                f"rewritten, and arr is what has to come back"
            )
        else:
            detail = (
                f"It returned {_render(returned)}, of type {type(returned).__name__}. The answer "
                f"is the array itself, handed back"
            )
        raise AssertionError(f"{where} did not return arr. {detail}.")

    if len(arr) != len(original):
        raise AssertionError(
            f"{where} changed the length of arr: {len(original)} elements went in and "
            f"{len(arr)} came out. Every position gets an answer, so there are exactly as many "
            f"answers as there were elements. Afterwards arr was {_render(arr)}."
        )

    if arr != expected:
        i = _first_difference(arr, expected)
        detail = f"first difference at index {i}: arr[{i}] is {arr[i]}, want {expected[i]}"
        n = len(original)
        if arr == original:
            detail = (
                "nothing was written into arr at all -- it came back exactly as it was handed "
                "over. `arr` is where the answer goes"
            )
        elif arr == _inclusive(original):
            detail = (
                f"every position took the greatest element from itself onwards instead of from "
                f"the next one onwards. The elements to the right of index i start at i + 1; "
                f"arr[i] never counts towards its own answer. At index {i} that is the difference "
                f"between {arr[i]} and {expected[i]}"
            )
        elif n > 1 and all(x == -1 for x in arr):
            detail = (
                "every position ended up as -1. That is what happens when each answer is worked "
                "out from values that have already been replaced: the -1 written at the last "
                "index becomes the greatest element to the left of it, and then spreads. The "
                "values that decide arr[i] are the ones arr held when the call started"
            )
        elif arr[-1] != -1 and arr[:-1] == expected[:-1]:
            detail = (
                f"every position but the last is right, and the last one is {arr[-1]} rather than "
                f"-1. Index {n - 1} has nothing to its right, and the statement fixes its answer "
                f"at -1 outright"
            )
        elif n > 1 and arr[1:] == expected[:-1]:
            detail = (
                "the answers are all present and all one position too far right. Each is sitting "
                "at the index after the one that asked for it"
            )
        elif sorted(arr) == sorted(expected):
            detail += ". The right values are all there, in the wrong places"
        if i is not None and n > 24:
            detail += (
                f". Around index {i} arr holds {_excerpt(arr, i)} where the answer is "
                f"{_excerpt(expected, i)}"
            )
        raise AssertionError(
            f"{where} left arr = {_render(arr)}, want {_render(expected)} -- {detail}."
        )


def _run(probe: str, arr: list[int]) -> None:
    """Snapshot, call, check. The snapshot is the answer key; the solution never touches it."""
    original = list(arr)
    returned = solve(arr)
    _check(probe, original, arr, returned)


def _run_known(probe: str, arr: list[int], expected: list[int]) -> None:
    """The same, for lists too long to hand to a quadratic reference.

    The reference is O(n^2) on purpose -- it is the statement transcribed, and being obviously
    right matters more there than being quick. It costs 0.42 s on a single list of 10^4 elements,
    measured on this interpreter, which is affordable a handful of times and not hundreds. So the
    long inputs in this file mostly come from the shape builders below, whose answers are known by
    construction, and `test_the_shape_builders_are_what_they_claim` holds those constructions to
    the reference at sizes where the reference is cheap.
    """
    original = list(arr)
    returned = solve(arr)
    if returned is not arr or len(arr) != len(original) or arr != expected:
        # Fall through to the full reporting path, which recomputes the answer key from the
        # reference and produces a diagnosis. Only reached when something is already wrong, so
        # the quadratic cost of doing that never lands on a passing run.
        _check(probe, original, arr, returned)
        # `_check` graded against the reference and was satisfied, so what the solution produced
        # is right and `expected` is not. That is a broken builder, not a broken solution, and
        # saying so is the difference between a useful failure and a baffling one.
        raise AssertionError(
            f"{probe}: the solution matches the reference, but the shape builder promised "
            f"{_render(expected)} -- fix the builder, not the solution"
        )


# ======================================================================================
# Shapes used by more than one test below, each carrying the answer it was built to have.
#
# Two rules make these answers known without solving the problem. For a NON-INCREASING list the
# greatest element to the right of position i is simply the element at i + 1, so the answer is the
# list shifted one place left with -1 appended. For a NON-DECREASING list every suffix has its
# maximum at the very end, so the answer is the last element repeated, with -1 in the final slot.
# The shapes that are neither get their answers written out longhand.
#
# Between them the nine vary the two properties this problem's cost can depend on, which is what
# the comment on TIMED_SHAPES is about: how often the running answer CHANGES as you move right to
# left, and how often values are EQUAL to one another.
# ======================================================================================

CEILING = 10_000  # the constraint ceiling: 1 <= arr.length <= 10^4
MAX_VALUE = 100_000  # 1 <= arr[i] <= 10^5

Shape = tuple[list[int], list[int]]  # (arr, the answer it is built to have)


def _from_non_increasing(a: list[int]) -> Shape:
    return a, a[1:] + [-1]


def _from_non_decreasing(a: list[int]) -> Shape:
    return a, [a[-1]] * (len(a) - 1) + [-1]


def _strictly_descending(n: int, seed: int = 1) -> Shape:
    """Every element is the greatest of everything to its right. The answer changes at every step.

    No two elements are equal, so this is also the shape on which a solution that recomputes its
    answer whenever it meets a tie never meets one. See `test_does_not_grow_quadratically`.
    """
    return _from_non_increasing(list(range(n, 0, -1)))


def _strictly_ascending(n: int, seed: int = 2) -> Shape:
    """The greatest element is the last one, so almost every position has the same answer.

    The mirror of the shape above on both properties: the answer never changes after the first
    step, and again no two elements are equal.
    """
    return _from_non_decreasing(list(range(1, n + 1)))


def _all_equal(n: int, seed: int = 3) -> Shape:
    """One value throughout. A repeated value is still to the right of every copy but the last.

    Every pair of neighbours is a tie, which is the property the two monotone shapes above cannot
    show at all.
    """
    return _from_non_increasing([7] * n)


def _non_increasing_with_ties(n: int, seed: int = 4) -> Shape:
    """Descending in random-sized steps, with plateaus, so ties and changes are both constant."""
    rng = random.Random(seed)
    a, v = [], MAX_VALUE
    for _ in range(n):
        a.append(v)
        v = max(1, v - rng.choice([0, 0, 1, 3, 17]))
    return _from_non_increasing(a)


def _non_decreasing_with_ties(n: int, seed: int = 5) -> Shape:
    """The mirror image: rising in random-sized steps, with plateaus."""
    rng = random.Random(seed)
    a, v = [], 1
    for _ in range(n):
        a.append(v)
        v = min(MAX_VALUE, v + rng.choice([0, 0, 1, 3, 17]))
    return _from_non_decreasing(a)


def _spike_at(n: int, m: int) -> Shape:
    """A list of 1s with the largest legal value planted at index m, for any 0 <= m < n.

    Everything before m sees that value to its right and answers with it; everything from m to
    n - 2 sees only 1s; the last position answers -1 like every other list here.
    """
    a = [1] * n
    a[m] = MAX_VALUE
    if m == 0:
        return a, [1] * (n - 1) + [-1]
    return a, [MAX_VALUE] * m + [1] * (n - 1 - m) + [-1]


def _spike_at_the_front(n: int, seed: int = 6) -> Shape:
    """The largest value is at index 0, where it decides nothing at all."""
    return _spike_at(n, 0)


def _spike_at_the_back(n: int, seed: int = 7) -> Shape:
    """The largest value is at the last index, where it decides every other answer."""
    return _spike_at(n, n - 1)


def _spike_in_the_middle(n: int, seed: int = 8) -> Shape:
    """The largest value sits a third of the way in, so the answer changes once, in the interior.

    Every other shape here plants what it is about at index 0 or at index n - 1, which between
    them say nothing about a solution that treats the middle of a long list differently from its
    edges. On lists too short to have a strict interior the spike falls back to index 0 and this
    becomes the front-spike shape, which costs nothing: the answer is still known either way.
    """
    return _spike_at(n, n // 3)


def _plateau_then_step_up(n: int, seed: int = 9) -> Shape:
    """A long run of one value followed by a run of a larger one."""
    return _from_non_decreasing([1] * (n // 2) + [9] * (n - n // 2))


SHAPES: tuple[tuple[str, Callable[[int], Shape]], ...] = (
    ("strictly descending", _strictly_descending),
    ("strictly ascending", _strictly_ascending),
    ("every element equal", _all_equal),
    ("non-increasing with ties", _non_increasing_with_ties),
    ("non-decreasing with ties", _non_decreasing_with_ties),
    ("the largest value at the front", _spike_at_the_front),
    ("the largest value at the back", _spike_at_the_back),
    ("the largest value in the middle", _spike_in_the_middle),
    ("a plateau then a step up", _plateau_then_step_up),
)


def test_the_shape_builders_are_what_they_claim() -> None:
    """Every builder above, at every length the reference can afford, against the reference.

    The long inputs in this file are graded against the answer the builder promises rather than
    against the reference, because the reference is quadratic and the ceiling is 10^4 elements. So
    the promise itself is checked here, at sizes where checking is cheap: if a builder ever stops
    producing what it says on the label, this test fails rather than some unrelated test quietly
    grading against the wrong answer.

    The constraints are checked here too, at every one of these lengths and again at the ceiling,
    because the guards below build their inputs from these same functions and a fixture that broke
    1 <= arr[i] <= 10^5 would be demanding something the problem never asked for.
    """
    for name, make in SHAPES:
        for n in list(range(1, 61)) + [CEILING]:
            arr, expected = make(n)
            assert len(arr) == n, f"{name}: builder returned {len(arr)} elements, wanted {n}"
            assert all(1 <= x <= MAX_VALUE for x in arr), f"{name} at n={n}: 1 <= arr[i] <= 10^5"
            assert len(expected) == n, f"{name} at n={n}: the promised answer is the wrong length"
            if n <= 60:
                assert expected == oracle(arr), (
                    f"the builder {name!r} at n={n} produced {_render(arr)} and promises "
                    f"{_render(expected)}, but the real answer is {_render(oracle(arr))} -- fix "
                    f"the builder, not the solution"
                )


# ======================================================================================
# The grader itself, against the contract.
# ======================================================================================


def test_the_grader_holds_the_contract_it_describes() -> None:
    """What `_check` accepts and rejects, pinned down rather than asserted in a docstring."""
    original = [17, 18, 5, 4, 6, 1]  # example 1
    answer = [18, 6, 6, 6, 1, -1]

    # Accepted: arr rewritten to the right contents, and arr itself handed back.
    arr = list(original)
    arr[:] = answer
    _check("grader self-test, accepted: rewritten and returned", original, arr, arr)

    # A solution may build its answer anywhere it likes, so long as it lands in arr.
    arr = list(original)
    elsewhere = list(answer)
    arr[:] = elsewhere
    _check("grader self-test, accepted: built elsewhere, written back", original, arr, arr)

    # The one-element case, where the answer is entirely the special case.
    one = [400]
    one[:] = [-1]
    _check("grader self-test, accepted: the single-element answer", [400], one, one)

    # SELF in the third column means "the solution returned arr itself", which is how the content
    # rules get tested in isolation from the identity rule. Anything else is returned literally.
    SELF = object()

    rejected: list[tuple[str, list[int], object]] = [
        # --- the identity rule, with arr in every state it could plausibly be left in ----------
        ("None returned, arr right", list(answer), None),
        ("None returned, arr untouched", list(original), None),
        ("a correct but different list, arr untouched", list(original), list(answer)),
        ("a correct but different list, arr also right", list(answer), list(answer)),
        ("the answer as a tuple", list(answer), tuple(answer)),
        ("an int returned", list(answer), 18),
        # --- the content rules, with arr itself handed back ------------------------------------
        ("arr untouched", list(original), SELF),
        ("every position counting itself", [18, 18, 6, 6, 6, -1], SELF),
        ("the last element left alone", [18, 6, 6, 6, 1, 1], SELF),
        ("the last element made 0 instead of -1", [18, 6, 6, 6, 1, 0], SELF),
        ("everything -1", [-1] * 6, SELF),
        ("the answers shifted one place right", [-1, 18, 6, 6, 6, 1], SELF),
        ("one element wrong", [18, 6, 6, 6, 2, -1], SELF),
        ("the list shortened", [18, 6, 6, 6, 1], SELF),
        ("the list lengthened", [18, 6, 6, 6, 1, -1, -1], SELF),
        ("the right values in the wrong order", [6, 18, 6, 6, 1, -1], SELF),
    ]
    for probe, after, returned in rejected:
        with pytest.raises(AssertionError):
            value = after if returned is SELF else returned
            _check(f"grader self-test, rejected: {probe}", original, after, value)


def test_the_grader_names_what_went_wrong() -> None:
    """The diagnoses in `_check` fire on the after-states they were written for.

    A branch that can never be reached is worse than no branch at all: it reads like a promise the
    file does not keep, and nothing fails when it stops being true. Each row below is the shape of
    a real mistake, paired with a phrase the report has to contain.
    """
    original = [17, 18, 5, 4, 6, 1]
    diagnosed: list[tuple[str, list[int], str]] = [
        ("arr untouched", list(original), "nothing was written into arr at all"),
        ("every position counting itself", [18, 18, 6, 6, 6, -1], "instead of from the next one"),
        ("everything -1", [-1] * 6, "every position ended up as -1"),
        ("the last element left alone", [18, 6, 6, 6, 1, 1], "every position but the last"),
        ("shifted one place right", [-1, 18, 6, 6, 6, 1], "one position too far right"),
        ("the right values shuffled", [6, 18, 6, 6, 1, -1], "in the wrong places"),
    ]
    for probe, after, phrase in diagnosed:
        with pytest.raises(AssertionError, match=phrase.replace(" ", r"\s+")):
            _check(f"grader self-test, diagnosis: {probe}", original, after, after)

    # The neighbourhood excerpt, which is the half of the report that survives a long list. A
    # mismatch in the middle of 10,000 elements renders identically at both ends, so without this
    # the failure reads as a complaint about two lists that look the same.
    long_original = list(range(CEILING, 0, -1))
    long_answer = long_original[1:] + [-1]
    broken = list(long_answer)
    broken[5000] = 1
    with pytest.raises(AssertionError, match=r"Around index 5000 arr holds"):
        _check("grader self-test, diagnosis: wrong deep inside", long_original, broken, broken)


# ======================================================================================
# Hand-written cases. Each is (probe, arr).
# ======================================================================================

Case = tuple[str, list[int]]

CASES: list[Case] = [
    # --- the statement's own examples ------------------------------------------------------
    ("example 1", [17, 18, 5, 4, 6, 1]),
    ("example 2, the shortest legal input", [400]),
    # --- one element, which is legal and is entirely the special case --------------------------
    ("a single 1", [1]),
    ("a single element at the top of the value range", [100000]),
    # --- two elements, the smallest input with anything to the right ---------------------------
    ("two elements, rising", [1, 2]),
    ("two elements, falling", [2, 1]),
    ("two elements, equal", [5, 5]),
    # --- monotone runs, where the answer is either the neighbour or the far end ----------------
    ("strictly descending", [5, 4, 3]),
    ("strictly ascending", [1, 2, 3]),
    ("descending over more elements", [9, 7, 5, 3, 1]),
    ("ascending over more elements", [1, 3, 5, 7, 9]),
    # --- ties, which are the quiet half of the definition --------------------------------------
    ("every element equal", [7, 7, 7]),
    ("every element equal, longer", [4, 4, 4, 4, 4, 4]),
    ("the maximum appears twice, at both ends", [9, 1, 2, 9]),
    ("the maximum appears twice, adjacent", [1, 9, 9, 1]),
    ("a plateau at the maximum in the middle", [1, 8, 8, 8, 2]),
    # --- where the largest value sits ----------------------------------------------------------
    ("the largest value first, and it decides nothing", [100, 1, 2, 3]),
    ("the largest value last, and it decides everything", [1, 2, 3, 100]),
    ("the largest value in the middle", [1, 2, 100, 3, 4]),
    ("the largest value one from the end", [1, 2, 100, 4]),
    # --- shapes that rise and fall -------------------------------------------------------------
    ("a single peak", [1, 5, 9, 4, 2]),
    ("a single valley", [9, 4, 1, 5, 8]),
    ("a sawtooth", [1, 9, 2, 8, 3, 7]),
    ("alternating two values", [1, 2, 1, 2, 1, 2]),
    # --- the extremes the constraints allow ----------------------------------------------------
    ("the top of the value range at the back", [1, 100000]),
    ("the top of the value range at the front", [100000, 1]),
    ("the bottom of the value range throughout", [1, 1, 1, 1]),
    ("both ends of the value range, repeated", [1, 100000, 1, 100000, 1]),
    # --- long enough that an off-by-one at either end cannot hide ------------------------------
    ("24 elements, descending", list(range(24, 0, -1))),
    ("24 elements, ascending", list(range(1, 25))),
    ("24 elements, all equal", [3] * 24),
    ("24 elements, the maximum at index 12", [1] * 12 + [500] + [1] * 11),
]


@pytest.mark.parametrize("probe,arr", CASES)
def test_examples_and_edges(probe: str, arr: list[int]) -> None:
    _run(probe, list(arr))


def test_the_examples_answers_are_what_the_statement_says() -> None:
    """The two published examples, against the reference, before anything is run.

    A reference that disagreed with the statement would fail every solution in this file for the
    wrong reason, and it would do it quietly. These two lines are cheap insurance.
    """
    assert oracle([17, 18, 5, 4, 6, 1]) == [18, 6, 6, 6, 1, -1]
    assert oracle([400]) == [-1]


def test_cases_obey_the_stated_constraints() -> None:
    """The fixtures are held to the same contract the solution is.

    A case outside the constraints would demand something never asked for, and a solution that
    failed it would be right to. Checked rather than assumed: these cases are hand-written.
    """
    for probe, arr in CASES:
        assert 1 <= len(arr) <= CEILING, f"[{probe}]: 1 <= arr.length <= 10^4"
        assert all(1 <= x <= MAX_VALUE for x in arr), f"[{probe}]: 1 <= arr[i] <= 10^5"


def test_the_constraint_ceiling_is_legal_input() -> None:
    """n = 10^4 in all nine shapes, unmarked and unconditional.

    The ceiling is the largest input the problem allows, so it belongs among the edge cases and
    not only among the timed ones. The sweep and the budget below both reach it, but both carry
    markers, and a run that deselects those should still put the largest legal input through. The
    answers are known by construction, so nine calls at the ceiling are cheap: measured on this
    repo's interpreter, CPython 3.14.4, the six correct solutions measured for this file get
    through all nine in 1.33 to 2.84 ms.

    The wall clock here grades nothing. It is a diagnosis instead of a silence, for a solution slow
    enough that nine calls look like a hang, and it is set where nothing measured for this file
    reaches it -- the slowest thing measured, one that rebuilds every answer with a generator over
    the elements to the right, gets through the nine in 10.4 s against a bound of 30 s.
    """
    started = time.perf_counter()
    for i, (name, make) in enumerate(SHAPES, start=1):
        arr, expected = make(CEILING)
        _run_known(f"n=10^4, {name}", arr, expected)
        elapsed = time.perf_counter() - started
        assert elapsed < 30.0, (
            f"the nine shapes at the ceiling were abandoned after {elapsed:.0f}s, with {i} of them "
            f"done and the last being {name}. Nothing was wrong with the answers -- this test "
            f"grades answers, not speed, and it is stopping only because a solution this slow "
            f"makes it look like a hang. The six correct solutions measured for this file get "
            f"through all nine in 1.33 to 2.84 ms. The guards further down are the ones that grade "
            f"speed, and they will say the same thing with numbers -- `uv run pytest -m slow`."
        )


@pytest.mark.property
def test_every_small_arrangement() -> None:
    """Every list of length 1 to 6 over a three-value alphabet, exhaustively. 1,092 lists.

    Three values is enough for every relationship this problem can be about -- a value larger than
    what follows it, a value smaller, and a value equal -- and going exhaustive means no
    arrangement of them is left to chance. Every position for the maximum, every length of
    plateau, every place a tie can fall, and every list where the answer changes at every step.
    """
    total = 0
    for n in range(1, 7):
        for tup in product((1, 2, 3), repeat=n):
            _run(f"exhaustive n={n}, arr={list(tup)}", list(tup))
            total += 1
    assert total == sum(3 ** n for n in range(1, 7)) == 1092


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    """Random lists, graded against the reference, inside the stated constraints.

    The value range is varied on purpose. Over the full 1..10^5 range a random list has a new
    maximum only a handful of times and holds essentially no ties, so those lists say very little
    about what happens when the answer changes often or when values repeat; the narrow ranges make
    both constant. All of it matters, so all of it is generated, along with runs that are already
    sorted one way or the other.
    """
    rng = random.Random(1299)
    for i in range(2000):
        n = rng.randint(1, 40)
        style = i % 4
        if style == 0:
            arr = [rng.randint(1, 3) for _ in range(n)]  # ties everywhere
        elif style == 1:
            arr = [rng.randint(1, MAX_VALUE) for _ in range(n)]  # ties almost never
        elif style == 2:
            arr = sorted((rng.randint(1, 50) for _ in range(n)), reverse=True)
        else:
            arr = sorted(rng.randint(1, 50) for _ in range(n))
        assert all(1 <= x <= MAX_VALUE for x in arr), "the generator must obey the constraints"
        _run(f"random n={n}, style {style}", arr)


SWEEP_BUDGET = 30.0  # seconds; see test_every_length_up_to_the_ceiling


@pytest.mark.property
def test_every_length_up_to_the_ceiling() -> None:
    """A sweep over the legal lengths, in every shape above, from 1 to the ceiling.

    The tests above stop at 40 elements and the guards below run at 1,000, 8,000 and 10,000, and
    the gaps between them are somewhere for a bug to live: a solution that handles the last element
    separately, or that walks the list in fixed-size chunks, or that treats the interior of a long
    list differently from its ends, can be right on every tiny length, right again on a round
    10,000, and wrong on 37 or on 4,097. That last one is not hypothetical. A solution correct
    everywhere except one interior index, and only on lists of 40 elements or more, passes every
    hand-written case in this file -- the longest is 24 elements -- and is caught here.

    Every length from 1 to 120 is taken, then both sides of the round numbers and the powers of two
    above that, then a stride of 250 to the ceiling so that no window of 250 consecutive lengths
    anywhere below 10^4 goes untested. 191 lengths, 1,719 calls over 2,527,263 elements in all.

    The whole sweep is held to a wall clock, and that is not a speed requirement -- it is a
    diagnosis instead of a silence. A solution whose cost grows with the length of the list can
    spend a very long time in a test that has nothing to say about speed, and it is the guards
    below, not this one, that are equipped to explain why. Measured on this repo's interpreter,
    CPython 3.14.4, the six correct solutions measured for this file get through the whole sweep in
    0.043 s to 0.077 s, while four of the slow ones took 12.0 s, 24.4 s, 74.9 s and 188.4 s. The
    budget is 30 s, 390 times the slowest right answer measured, and nothing can trip it without
    having already failed a guard below.
    """
    started = time.perf_counter()
    done = 0

    lengths = list(range(1, 121))
    for base in (128, 200, 256, 500, 512, 1000, 1024, 2048, 4096, 8192, CEILING):
        lengths += [base - 1, base, base + 1]
    lengths += list(range(120, CEILING, 250))
    lengths = sorted({n for n in lengths if 1 <= n <= CEILING})
    planned = len(lengths) * len(SHAPES)

    for n in lengths:
        for name, make in SHAPES:
            arr, expected = make(n)
            _run_known(f"n={n}, {name}", arr, expected)
            done += 1
            elapsed = time.perf_counter() - started
            assert elapsed < SWEEP_BUDGET, (
                f"the length sweep was abandoned after {elapsed:.0f}s and {done} of {planned} "
                f"calls, the last of them n={n}, {name}. This test grades answers, not speed, and "
                f"it is stopping only because it cannot finish: the solutions measured for this "
                f"file get through the whole sweep in 0.043 to 0.077 s. The guards below are the "
                f"ones that grade speed, and they will tell you the same thing with numbers -- "
                f"run them with `uv run pytest -m slow`."
            )

    assert done == planned, f"the sweep made {done} calls, not the {planned} it planned"


# ======================================================================================
# Timing guards.
# ======================================================================================


def _ceiling_cases() -> list[Shape]:
    """Twenty lists at the constraint ceiling: the nine shapes above, plus eleven more.

    Two of the eleven hold 10^4 random values, and they are the only full-size lists anywhere in
    this file whose answer is not known by construction. They are graded against the quadratic
    reference, which costs 0.42 s a call at this size -- a fair price twice over for a shape no
    builder can produce, and not a price worth paying twenty times. The other nine are cheap
    constructions covering the top of the value range, the two spikes one place in from each end,
    and four lists of a single repeated value.
    """
    cases = [make(CEILING) for _, make in SHAPES]

    rng = random.Random(1299)
    for _ in range(2):
        arr = [rng.randint(1, MAX_VALUE) for _ in range(CEILING)]
        cases.append((arr, oracle(arr)))

    top = MAX_VALUE - CEILING
    cases.append(_from_non_increasing(list(range(MAX_VALUE, top, -1))))
    cases.append(_from_non_decreasing(list(range(top + 1, MAX_VALUE + 1))))
    cases.append(_spike_at(CEILING, 1))
    cases.append(_spike_at(CEILING, CEILING - 2))
    cases.append(_from_non_decreasing([1] * (CEILING // 2) + [MAX_VALUE] * (CEILING // 2)))
    for value in (11, 13, 17, MAX_VALUE):
        cases.append(_from_non_increasing([value] * CEILING))

    assert len(cases) == 20, f"the ceiling builder made {len(cases)} cases, not 20"
    return cases


CEILING_BUDGET = 0.250  # seconds for 20 calls at n = 10^4; see test_constraint_ceiling


@pytest.mark.slow
def test_constraint_ceiling() -> None:
    """n = 10^4, the largest input the constraints allow, against a wall-clock budget.

    This is the one guard in the chapter where a wall clock genuinely separates the field, and it
    is worth knowing why: at this ceiling the gap between a solution that answers each position
    from what it already knows and one that goes and looks is not a factor of two, it is three
    orders of magnitude. Measured on this repo's interpreter, CPython 3.14.4, over the 20 cases
    this function builds, total for all 20, best of five rounds for the correct band and of one to
    three for the rest:

        six correct solutions, as a band                          2.73 -     5.30 ms
        -------------------------------------------------------------- budget: 250 ms
        rescanning whenever the carried maximum is passed              1,117 ms
        rescanning across the middle third of the list                 2,926 ms
        rescanning whenever an equal value turns up                    3,467 ms
        max() over a slice of the elements to the right,
          taken once per position                             8,434 -     8,537 ms
        a carried maximum below 9,000 elements, a rescan above         9,046 ms
        max() over a generator, once per position                     22,791 ms

    The budget sits at 47x the slowest of the correct band and 4.5x inside the quickest of the
    others, and that margin is deliberate rather than lucky: the same measurement taken with eight
    processes running it at once, on a ten-core machine with nothing left to give, put the correct
    band at 2.83 - 12.85 ms over 48 readings, still 19x inside the budget.

    The six correct solutions spent 0.121 to 0.320 ms on a single pass over 10^4 elements, measured
    across all nine shapes above plus a list of random values. The band is wide because it includes
    solutions that allocate a second list and copy it back, which nothing here objects to -- the
    quickest of the six is one of them.

    The second-to-last row is why this guard is not redundant with the ratio below. That solution
    carries a maximum on any list of 9,000 elements or fewer and rescans the whole suffix on a
    longer one, so it is linear at both sizes the growth guard measures and lands between 8.16x and
    8.78x on all five of its shapes -- invisible there, and 36x over the budget here. A ratio taken
    below the ceiling cannot see work that only starts at the ceiling; a clock pointed at the
    ceiling can.

    A reading over budget is taken again, up to three times in all, and only fails if every attempt
    agrees -- unless the first reading is more than ten times the budget, in which case nothing is
    gained by watching a quadratic solution be slow twice more.

    The correctness half of this test is not a formality. These are the only full-size inputs in
    the file whose answers come from the reference rather than from a construction: two lists of
    10^4 random values, a shape no builder can produce.
    """
    cases = _ceiling_cases()
    for i, (arr, expected) in enumerate(cases):
        assert len(arr) == CEILING, f"ceiling case {i}: built {len(arr)} elements, want {CEILING}"
        assert all(1 <= x <= MAX_VALUE for x in arr), f"ceiling case {i}: 1 <= arr[i] <= 10^5"
        _run_known(f"ceiling case {i}, n={CEILING}", list(arr), expected)

    replace_elements = Solution().replaceElements
    readings: list[float] = []
    for _ in range(3):
        fresh = [list(arr) for arr, _ in cases]
        start = time.perf_counter()
        for arr in fresh:
            replace_elements(arr)
        readings.append(time.perf_counter() - start)
        if readings[-1] < CEILING_BUDGET or readings[-1] > 10 * CEILING_BUDGET:
            break

    taken = ", ".join(f"{r * 1e3:.0f}ms" for r in readings)
    assert min(readings) < CEILING_BUDGET, (
        f"{len(cases)} calls at the ceiling (n = {CEILING:,}) took {min(readings) * 1e3:.0f}ms, "
        f"over the {CEILING_BUDGET * 1e3:.0f}ms budget (measured {taken}): "
        f"{min(readings) / len(cases) * 1e3:.1f}ms per call, against the 0.12 - 0.32ms a single "
        f"pass over 10^4 elements costs here. Something inside the loop is doing work that grows "
        f"with the length of the list rather than a fixed amount -- max() over a slice, a nested "
        f"loop, or a search that starts again at some of the positions."
    )


# --- the growth guard's measuring apparatus -------------------------------------------------
#
# Every call needs a list of its own, since the solution rewrites what it is given, so the copy is
# made inside the measured region. That is deliberate, and it cannot bend the result: list(data)
# measured 0.91 - 1.10 us at n = 1,000 and 8.66 - 15.13 us at n = 8,000 across the five shapes
# below, which came to between 2.8% and 12.7% of a sample over the six correct solutions at both
# sizes. A term that small cannot lift a ratio near 8x anywhere near a ceiling of 25x, and it is
# itself linear in any case; the measured end-to-end ratios below already include it. What the copy
# buys is that memory stays at two lists however many repetitions get taken, and that a solution is
# never timed against a list some earlier call already rewrote.

GROWTH_CEILING = 25.0  # the ratio a solution may not exceed; see test_does_not_grow_quadratically
SMALL_N, FACTOR = 1_000, 8
BATCH_TARGET = 0.003  # seconds; how long one timed sample must last


def _seconds_per_call(data: list[int], batch: int) -> float:
    """Seconds per call, averaged over `batch` calls, each on a fresh copy of `data`."""
    start = time.perf_counter()
    for _ in range(batch):
        c = list(data)
        solve(c)
    return (time.perf_counter() - start) / batch


def _batch_size(data: list[int]) -> int:
    """The smallest power-of-two batch whose run lasts at least BATCH_TARGET seconds.

    One call at n = 1,000 costs between 14.4 and 34.0 microseconds for the correct solutions
    measured here, and a sample that short is not a measurement of the code -- it is a measurement
    of what else the machine was doing during it. Timing a batch and dividing is what makes the
    number hold up when the machine is busy. At those costs this settles on batches of 64 to 256
    at the small size and 8 to 32 at the large one.
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
    repetitions cannot: this machine has four performance cores and six efficiency ones and moves a
    process between them, and a side measured entirely inside one of those windows is measuring the
    core rather than the code.

    The early exit keeps nine repetitions from being slow to fail. Once three pairs are in and the
    big side is past the ceiling with 50 ms of headroom on top, more repetitions cannot bring it
    back. The 50 ms is flat rather than proportional so that a verdict is never reached on the
    strength of microseconds of interference between two sub-millisecond numbers: the slowest
    correct solution measured 0.284 ms per sample at n = 8,000, against a threshold that starts at
    50 ms, so it never trips. What trips it is a call costing a quarter of a second.
    """
    small_batch, big_batch = _batch_size(small), _batch_size(big)
    best_small = best_big = float("inf")
    for taken in range(1, reps + 1):
        best_small = min(best_small, _seconds_per_call(small, small_batch))
        best_big = min(best_big, _seconds_per_call(big, big_batch))
        if taken >= 3 and best_big > GROWTH_CEILING * best_small + 0.050:
            break
    return best_big / best_small


def _random_values(n: int, seed: int = 10) -> Shape:
    """n values drawn uniformly from the whole legal range, and no answer.

    The empty second element says "not known by construction". It is the one timed shape whose
    answer has to come from the reference, which is affordable because the correctness check runs
    once, outside the timing.
    """
    rng = random.Random(seed)
    return [rng.randint(1, MAX_VALUE) for _ in range(n)], []


# The five shapes the growth guard measures, and none of them is decoration. A solution can be
# linear on one of these lists and quadratic on another, and two properties of the input decide
# which: how often the running answer CHANGES as you move right to left, and how often values are
# EQUAL to one another. The five span both.
#
#                                       answer changes         ties
#     strictly descending               at every position      never
#     strictly ascending                never after the first  never
#     every element equal               never after the first  at every position
#     non-increasing with ties          often                  often
#     random values over 1..10^5        a handful of times     almost never
#
# Six slow solutions were measured against all five, and four of the five have a hole in them.
# Timing any single shape alone would give a confident and wrong answer:
#
#     a solution that recomputes its carried maximum
#       whenever the value it was carrying is PASSED     invisible on ascending, on all-equal,
#                                                        and on random values
#     a solution that recomputes its carried maximum
#       whenever an EQUAL value turns up                 invisible on descending, on ascending,
#                                                        and on random values
#
# On the shapes that miss them both sit between 0.140 and 0.202 ms a call at n = 10^4, inside the
# 0.121 to 0.320 ms band the correct solutions occupy, and on the shapes that catch them they cost
# 164 to 409 ms a call. Of the six, only "non-increasing with ties" catches all of them on its own,
# and it is in the list for that reason rather than trusted with the job.
TIMED_SHAPES: tuple[tuple[str, Callable[[int], Shape]], ...] = (
    ("strictly descending", _strictly_descending),
    ("strictly ascending", _strictly_ascending),
    ("every element equal", _all_equal),
    ("non-increasing with ties", _non_increasing_with_ties),
    ("random values", _random_values),
)


@pytest.mark.slow
def test_does_not_grow_quadratically() -> None:
    """Eight times the input should cost about eight times the work, on five shapes.

    The budget above already separates the two bands at the ceiling, and this is the guard that
    says the same thing without depending on how fast this machine is: a ratio is the same number
    on a slow machine and a fast one, and it stays the same number when the wall clock is busy with
    something else.

    Measured on this repo's interpreter, CPython 3.14.4, n = 1,000 then 8,000. Six correct
    solutions, three readings of each on each shape, are given as a band, since what matters about
    them is that they land together; the slow ones are named, two readings each, because what they
    do is the subject. Two slice-based solutions were measured and they land together, so they
    share a row and its range covers both. Arrows mark a shape a solution is invisible on.

        strictly descending
            the six correct, 18 readings                    8.13x -  9.21x
            rescanning when an equal value turns up          8.66x -  8.73x  <- invisible here
            ------------------------------------------------------------ ceiling: 25x
            rescanning when the carried maximum is passed  62.66x - 64.33x
            max() over a generator, per position           64.17x - 64.29x
            max() over a slice, per position               64.02x - 66.36x
            rescanning across the middle third             65.14x - 66.06x

        strictly ascending
            the six correct, 18 readings                    7.58x -  8.90x
            rescanning when an equal value turns up          8.38x -  8.48x  <- invisible here
            rescanning when the carried maximum is passed    8.49x -  8.67x  <- invisible here
            ------------------------------------------------------------ ceiling: 25x
            rescanning across the middle third             64.05x - 65.11x
            max() over a generator, per position           64.61x - 64.64x
            max() over a slice, per position               64.80x - 69.14x

        every element equal
            the six correct, 18 readings                    7.33x -  8.37x
            rescanning when the carried maximum is passed    8.33x -  8.35x  <- invisible here
            ------------------------------------------------------------ ceiling: 25x
            max() over a slice, per position               59.54x - 63.76x
            rescanning when an equal value turns up        60.49x - 62.32x
            rescanning across the middle third             62.31x - 63.28x
            max() over a generator, per position           62.99x - 63.42x

        non-increasing with ties
            the six correct, 18 readings                    7.97x -  8.86x
            ------------------------------------------------------------ ceiling: 25x
            rescanning when an equal value turns up        62.23x - 62.23x
            rescanning across the middle third             63.11x - 64.81x
            max() over a generator, per position           63.64x - 65.86x
            rescanning when the carried maximum is passed  64.37x - 65.79x
            max() over a slice, per position               64.94x - 65.67x

        random values over the full 1..10^5 range
            the six correct, 18 readings                    7.75x -  8.90x
            rescanning when the carried maximum is passed    7.87x -  7.95x  <- invisible here
            rescanning when an equal value turns up          9.04x -  9.15x  <- invisible here
            ------------------------------------------------------------ ceiling: 25x
            max() over a generator, per position           63.13x - 63.98x
            rescanning across the middle third             64.52x - 65.40x
            max() over a slice, per position               65.09x - 66.20x

    A quadratic solution lands near 64x, because the pass it makes per position is a C-level scan
    of the whole remaining list on top of the Python-level loop it was already paying for. Across
    all 90 correct readings the highest was 9.21x; across the slow readings, on the shapes that see
    them, the lowest was 59.54x. Under load the correct spread widens without coming apart: 480
    readings taken with eight processes competing for ten cores ran from 5.82x to 13.62x with a
    median of 8.30x, and not one of them reached the ceiling. The ceiling sits in that gap, nearer
    the bottom of it than the middle, because failing a correct solution is a worse outcome here
    than letting a slow one through -- and a slow one still has the budget above, and a submission
    page, to get past.

    Two things this guard cannot see, and does not pretend to. A solution that is merely WRONG in
    the interior of a long list is not a timing question at all; that is what the length sweep above
    is for, and it is why the sweep runs all nine shapes at every length rather than only at the two
    sizes measured here. And a solution whose extra work only begins above 8,000 elements is linear
    at both sizes measured here whatever the shape; that is what the budget above is for, and its
    docstring has the numbers for one.

    A ratio over the ceiling is measured again before it is reported, up to three times in all, and
    only fails if every attempt agrees. The re-measurement is for the machine's benefit, not the
    solution's: an excursion that far out is not something a correct solution produces three times
    running, while a quadratic one is over the ceiling every single time. A ratio past twice the
    ceiling is not re-measured at all -- nothing that far out is noise.
    """
    attempts = 3
    for name, make in TIMED_SHAPES:
        small, _ = make(SMALL_N)
        big, big_expected = make(SMALL_N * FACTOR)

        # Correctness at the larger of the two timed sizes, checked once and outside the timing.
        # A wrong answer should say it is wrong, not that it is slow.
        if big_expected:
            _run_known(f"n={SMALL_N * FACTOR:,}, {name}", list(big), big_expected)
        else:
            _run(f"n={SMALL_N * FACTOR:,}, {name}", list(big))

        seen: list[float] = []
        for _ in range(attempts):
            seen.append(_growth_ratio(small, big))
            if seen[-1] < GROWTH_CEILING or seen[-1] > 2 * GROWTH_CEILING:
                break

        readings = ", ".join(f"{r:.0f}x" for r in seen)
        assert min(seen) < GROWTH_CEILING, (
            f"{FACTOR}x the input cost {min(seen):.0f}x the time (n={SMALL_N:,} -> "
            f"{SMALL_N * FACTOR:,}, {name}; measured {readings}). A single pass lands near "
            f"{FACTOR}x; {min(seen):.0f}x means the work done per position grows with the length "
            f"of the list. The algorithm may well be right -- look instead for a step inside the "
            f"loop that is not O(1). max() over a slice walks and copies that slice; slicing "
            f"copies; a nested loop is a nested loop. Note that this shape is {name!r}: a solution "
            f"that rescans only sometimes -- when it passes the value it was carrying, or when it "
            f"meets one equal to it -- can pass on one shape and fail on another, and the fix is "
            f"the same either way."
        )



# --- the flat-cost guard's ladder ---------------------------------------------------------------
#
# Between them the two guards above sample three sizes: the ratio measures n = 1,000 and n = 8,000,
# the budget measures n = 10,000. Work that begins anywhere else is invisible to both, and not by a
# narrow margin. A ratio can only see cost that GROWS between the two sizes it takes, so a solution
# that walks a slice per position below some threshold and carries a maximum above it produces a
# ratio UNDER one and sails through; and a clock pointed at the ceiling sees only the ceiling, so a
# solution quadratic between the two measured sizes and linear at both of them never trips it.
# Three solutions of exactly those shapes were written for this file -- quadratic below 5,000,
# quadratic between 1,000 and 8,000, and quadratic between 2,000 and 3,000 -- and every one of them
# passed every other test here, including both guards above.
#
# What catches all three is the measurement the ratio already takes, read as an absolute rather than
# as a pair: seconds per element, at a ladder of sizes across the legal range. For a solution doing
# a fixed amount of work per position that number is very nearly a constant, and very nearly the
# same constant at every size. It is not a speed limit -- nothing here says how many nanoseconds an
# element may cost -- only a statement that whatever an element costs, it costs about that much
# wherever in the range it is measured.

COST_LADDER = (1_000, 2_500, 5_000, 7_500, 10_000)
COST_SPREAD_CEILING = 25.0  # how much the per-element cost may vary across the ladder

COST_SHAPES: tuple[tuple[str, Callable[[int], Shape]], ...] = (
    ("strictly descending", _strictly_descending),
    ("non-increasing with ties", _non_increasing_with_ties),
    ("random values", _random_values),
)


def _seconds_per_element(data: list[int], reps: int = 3) -> float:
    """The floor of `reps` batched samples on one list, divided by its length.

    Batched and floored for the same reasons `_growth_ratio` is: a single sample at n = 1,000 is
    over in microseconds and measures the machine rather than the code, and interference only ever
    makes a reading slower, so the fastest of several is the closest thing to a clean one.
    """
    batch = _batch_size(data)
    return min(_seconds_per_call(data, batch) for _ in range(reps)) / len(data)


@pytest.mark.slow
def test_cost_per_element_holds_across_the_length_range() -> None:
    """One element should cost the same whether the list has 1,000 of them or 10,000.

    Measured on this repo's interpreter, CPython 3.14.4, as the spread between the dearest and the
    cheapest element on the ladder above -- five sizes from 1,000 to the ceiling -- taken on three
    shapes, best of three batched samples at each size:

        six correct solutions, 18 readings                       1.05x -     1.17x
        a correct O(n log n) solution built on a heap             1.09x -     1.30x
        --------------------------------------------------------------- ceiling: 25x
        quadratic between 2,000 and 3,000, linear elsewhere        488x -      592x
        quadratic below 5,000, linear above it                     898x -    1,148x
        quadratic between 1,000 and 8,000, linear at both ends   1,538x -    1,941x

    The correct band is that tight because the quantity being compared is a rate rather than a
    time: a solution that allocates a second list and copies it back pays for that at every size,
    so it shows up in the constant and not in the spread. The heap solution is in the table on
    purpose. It is genuinely slower than the others at every size -- 73 to 128 ns an element
    against their 16 to 38 -- and this guard has nothing to say about that, which is the point.
    O(n log n) is not the target this problem sets, but it is not work that grows with the length
    of the list either, and the submission page takes it.

    The ceiling sits at 25x, which is very nearly the geometric middle of a gap running from 1.30x
    to 488x: 19 times above the worst correct reading and 19 times below the best slow one. Under
    load the correct spread widens without coming apart. Seven solutions -- the six correct ones and
    the heap -- measured on all three shapes by eight processes competing for ten cores gave 168
    readings between 1.02x and 2.95x, median 1.36x, the worst of them still 8 times inside the
    ceiling.

    This is not the quadratic guard and does not try to be. A solution that walks a slice at every
    position at every size has a per-element cost that RISES along the ladder rather than jumping
    on it, and rises only as far as the ladder is long: one measured 10.00x to 10.48x here, because
    1,000 to 10,000 is a factor of ten in n. It passes this guard and fails both of the others,
    which is the right division of labour. What this one sees is a per-element cost that is not the
    same at both ends of the range, whichever end is the dear one, and it looks where the other two
    do not.

    A spread over the ceiling is measured again, up to three times in all, and only fails if every
    attempt agrees. A spread past twice the ceiling is not re-measured -- nothing that far out is
    noise, and there is nothing to learn from watching it happen twice more.
    """
    for name, make in COST_SHAPES:
        costs: dict[int, float] = {}
        seen: list[float] = []
        for _ in range(3):
            costs = {n: _seconds_per_element(make(n)[0]) for n in COST_LADDER}
            seen.append(max(costs.values()) / min(costs.values()))
            if seen[-1] < COST_SPREAD_CEILING or seen[-1] > 2 * COST_SPREAD_CEILING:
                break

        ladder = ", ".join(f"n={n:,}: {costs[n] * 1e9:,.0f}ns" for n in COST_LADDER)
        cheapest = min(costs, key=lambda n: costs[n])
        dearest = max(costs, key=lambda n: costs[n])
        readings = ", ".join(f"{r:,.0f}x" for r in seen)
        assert min(seen) < COST_SPREAD_CEILING, (
            f"one element cost {min(seen):,.0f}x as much at n={dearest:,} as it did at "
            f"n={cheapest:,} ({name}; measured {readings}). Per element, across the ladder: "
            f"{ladder}. A solution doing a fixed amount of work per position lands inside 1.3x "
            f"here, because what is being compared is a rate and not a time -- allocating a second "
            f"list and copying it back costs the same per element at every size. A spread this "
            f"wide means the work done per element depends on how long the list is. The guards "
            f"above sample n=1,000, n=8,000 and n=10,000 only, so a slice walked per position "
            f"below some size, or between two sizes, or only above one, can pass both of them and "
            f"still be caught here: look for a branch on len(arr), and for a step inside the loop "
            f"that is not O(1) on one side of it."
        )


# ---------------------------------------------------------------------------------------
# What this suite does NOT check, and why none of it is an oversight.
#
# EXTRA SPACE. Not measured. Nothing counts allocations, and a solution that assembles the answer
# in a list of its own before writing it into `arr` is accepted -- three of the six correct
# solutions measured for the numbers above do exactly that, and the quickest of the six is one of
# them. The rule here is about where the answer ends up, not about how it was arrived at.
#
# WHICH ROUTE THE SOLUTION TOOK. No static check on any name.
#
# THE ORDER THE LIST IS VISITED IN. Not checked either. Right to left is the route that makes this
# problem one pass, but a solution that goes left to right over a reversed copy, or that reverses
# `arr` where it stands and reverses it back, is doing a fixed amount of work per element and is
# accepted. Both were measured for the numbers above.
#
# THE IDENTITY RULE *IS* an addition, and it is the one thing here the judge does not grade. The
# judge reads the array that comes back and never looks at the one it handed over, so returning a
# freshly built list is accepted there. It fails here on purpose. This chapter is about rewriting a
# list where it stands, and 1299 is the gentlest problem in it to practise on -- there is no order
# to preserve, no length to hold, and nothing sliding past anything else. Skipping the practice
# here would leave nothing but the harder problems to learn it on. The stub says so.
# ---------------------------------------------------------------------------------------
