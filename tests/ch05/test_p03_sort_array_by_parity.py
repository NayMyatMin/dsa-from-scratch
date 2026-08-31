"""Spec for 905. Sort Array By Parity.

Every other problem in this chapter has exactly one accepted answer. This one has as many as the
even values can be ordered times the ways the odd ones can, and grading it is therefore a different
job: nothing here compares against a list, because there is no list to compare against. Four
contracts are enforced, and the fourth is the interesting one.

1. `sortArrayByParity` returns a list. Not None -- this is not 283's contract, and a solution that
   rearranges `nums` beautifully and returns nothing fails. Not a tuple and not an iterator: the
   signature says list[int].
2. What comes back is a rearrangement of `nums`: the same length, the same values, each appearing
   as many times as it did. Nothing added, dropped or altered.
3. Every even value comes before every odd one.
4. Nothing else. In particular the order inside the evens and the order inside the odds are not
   checked, in either direction: `_check` will accept the evens in their arrival order, in reverse,
   sorted, or shuffled, and it accepts all four of the answers the statement lists for [3,1,2,4].
   `test_the_grader_accepts_every_arrangement_the_statement_does` pins that down by feeding the
   grader all 24 permutations of that input and requiring exactly 4 of them through.

What this suite deliberately does NOT police, because the problem deliberately does not ask:

  what happens to nums   Not looked at after the call, at all. Returning a newly built list and
                         never writing into `nums` is a correct answer to this problem, on the
                         submission page and here, and so is rearranging `nums` where it stands and
                         returning it. `_check` grades the value that comes back and takes the
                         answer key from a snapshot made beforehand, so both routes are graded the
                         same way. This is the one place in the chapter where in-place is the
                         better exercise rather than the requirement, and inventing the requirement
                         here would be inventing it.

  the order within a
  parity group           See contract 4. Sorting the evens is accepted, reversing them is accepted,
                         and so is leaving them exactly as they arrived. None of the three is more
                         right than the others. 283 earlier in this chapter is the problem where
                         relative order is the whole difficulty; the contrast is why the two sit in
                         one chapter.

  extra space            Not measured. Contract 2 says what the answer has to contain, not where it
                         was assembled.

  which route            No static check on any name, and none on the route either. Whatever
                         comes back satisfying the three rules above is accepted.

Time is policed, and the reason is the same one chapter 3's 27 gives. The problem states no
complexity requirement, and n = 5000 is small enough that being wrong about this costs you very
little: measured on this repo's interpreter, CPython 3.14.4, the eleven quickest correct solutions
measured for this file cost 0.120 - 0.383 ms a call at the ceiling, and the quadratic shapes that
move a run of elements once per element cost 2.079 - 288.043 ms a call, which for most of them is
still a small fraction of a second. The suite holds you to linear anyway, because that cost comes
from an operation that moves everything behind the position it touches, which is the mistake this
chapter exists to catch.

Two guards do it, and they see genuinely different things, which is why both are here rather than
one being a weaker copy of the other. `test_does_not_grow_quadratically` compares the cost at n
against the cost at 8n and cares only about the ratio, so it is immune to how fast this machine is
-- and blind to any cost that grows linearly in n while still being enormous. The other one,
`test_constraint_ceiling`, puts a wall clock on the real ceiling, so it sees exactly that and
nothing about shape. Each catches solutions the other lets through, and both docstrings name the
ones measured.
"""

import random
import time
from collections.abc import Callable
from itertools import permutations, product

import pytest

from arrays101.ch05.p03_sort_array_by_parity import Solution
from tests._reference.p03_sort_array_by_parity import oracle


def solve(nums: list[int]) -> object:
    """Run the solution and hand back its return value, which is the answer."""
    return Solution().sortArrayByParity(nums)


# ======================================================================================
# Contract checking, shared by every test below.
# ======================================================================================

CEILING = 5_000  # the constraint ceiling: 1 <= nums.length <= 5000
MAX_VALUE = 5_000  # 0 <= nums[i] <= 5000


def _render(value: object, limit: int = 24) -> str:
    """A repr that stays readable when the list has thousands of elements in it."""
    if not isinstance(value, list) or len(value) <= limit:
        return repr(value)
    head = ", ".join(str(x) for x in value[:12])
    tail = ", ".join(str(x) for x in value[-4:])
    return f"[{head}, ..., {tail}] ({len(value)} elements)"


def _parities(a: list[int]) -> str:
    """The parity pattern as a string of E and O, truncated so it stays readable."""
    s = "".join("E" if x % 2 == 0 else "O" for x in a)
    return s if len(s) <= 60 else s[:40] + "..." + s[-8:]


def _check(probe: str, original: list[int], returned: object) -> None:
    """Assert the whole contract for one call.

    `original` is a pristine snapshot taken before the call, and it is the only thing the answer is
    graded against -- the list the solution was handed is never looked at again, because a solution
    is free to rewrite it or to ignore it.
    """
    evens, odds = oracle(original)
    where = f"{probe}: sortArrayByParity({_render(original)})"

    if not isinstance(returned, list):
        extra = ""
        if returned is None:
            extra = (
                ". None is 283's contract, not this one: there the caller reads the list it handed "
                "over, and here it reads what comes back. If nums is already arranged correctly, "
                "the fix is one `return nums`"
            )
        elif isinstance(returned, tuple):
            extra = ". A tuple is not a list, and the signature says list[int]"
        raise AssertionError(
            f"{where} returned {_render(returned)}, of type {type(returned).__name__}. It must "
            f"return a list{extra}."
        )

    if len(returned) != len(original):
        detail = ""
        if sorted(returned) == evens:
            detail = ". Those are the even values on their own. The odd ones are part of the "\
                     "answer too, behind them"
        elif sorted(returned) == odds:
            detail = ". Those are the odd values on their own. The even ones are part of the "\
                     "answer too, in front of them"
        elif len(returned) == len(set(original)):
            detail = ". That is how many distinct values there were -- duplicates are kept, not "\
                     "collapsed"
        raise AssertionError(
            f"{where} returned {len(returned)} elements, want {len(original)}{detail}. Every "
            f"element of nums appears in the answer as many times as it did in the input. What "
            f"came back was {_render(returned)}."
        )

    if sorted(returned) != sorted(original):
        raise AssertionError(
            f"{where} returned {_render(returned)}, which is not a rearrangement of the input. "
            f"The same values have to come back, each as many times as it went in; this problem "
            f"only ever moves what is already there."
        )

    k = len(evens)
    if sorted(returned[:k]) != evens:
        # There is always such an index once the multiset matches and the front k are not the
        # evens: some odd sits inside the first k, and some even sits behind it.
        bad = next(i for i, x in enumerate(returned) if x % 2 and any(
            y % 2 == 0 for y in returned[i + 1:]))
        detail = ""
        if returned == sorted(original):
            detail = (
                ". The list came back sorted by value, which is a different question: 3 is less "
                "than 4 and it is still odd. What has to come first is every even value, in any "
                "order at all"
            )
        raise AssertionError(
            f"{where} returned {_render(returned)}, whose parities run {_parities(returned)}. "
            f"The odd value {returned[bad]} at index {bad} still has an even value behind it, and "
            f"every even value has to come before every odd one. The answer holds {k} even values "
            f"and {len(odds)} odd ones, so the parities have to read E {k} times and then O "
            f"{len(odds)} times. Which even goes where is your business{detail}."
        )


def _run(probe: str, nums: list[int]) -> None:
    """Snapshot, call, check. The snapshot is the answer key; the solution never touches it."""
    original = list(nums)
    returned = solve(nums)
    _check(probe, original, returned)


# ======================================================================================
# The grader itself, against the judge's rules.
# ======================================================================================


def test_the_grader_accepts_every_arrangement_the_statement_does() -> None:
    """All 24 permutations of example 1, of which exactly 4 must be accepted.

    The statement gives [2,4,3,1] as its output and names [4,2,3,1], [2,4,1,3] and [4,2,1,3] as
    equally accepted. That is a rule about grading, not a remark, so it is checked as one: every
    ordering of the four values is fed to `_check`, and if the number that get through is ever
    anything other than those four this test fails rather than some solution being quietly held to
    a stricter or looser rule than the problem states.
    """
    original = [3, 1, 2, 4]
    accepted = set()
    for p in permutations(original):
        try:
            _check("grader self-test, permutation", original, list(p))
        except AssertionError:
            continue
        accepted.add(p)

    assert accepted == {(2, 4, 3, 1), (4, 2, 3, 1), (2, 4, 1, 3), (4, 2, 1, 3)}, (
        f"the grader accepts {sorted(accepted)} for [3,1,2,4]; the statement accepts exactly "
        f"[2,4,3,1], [4,2,3,1], [2,4,1,3] and [4,2,1,3]"
    )


def test_the_grader_holds_the_contract_it_describes() -> None:
    """What `_check` accepts and rejects beyond the permutation rule above."""
    original = [0, 2, 4, 1, 3, 5]  # three evens, three odds, already in the answer's shape

    accepted: list[tuple[str, list[int]]] = [
        ("the input unchanged, which already satisfies it", [0, 2, 4, 1, 3, 5]),
        ("evens reversed", [4, 2, 0, 1, 3, 5]),
        ("odds reversed", [0, 2, 4, 5, 3, 1]),
        ("both groups shuffled", [2, 4, 0, 5, 1, 3]),
    ]
    for probe, value in accepted:
        _check(f"grader self-test, accepted: {probe}", original, value)

    # A duplicated value has to come back the same number of times, and the count is what is
    # checked rather than the set.
    _check("grader self-test, accepted: duplicates kept", [2, 2, 1], [2, 2, 1])

    rejected: list[tuple[str, object]] = [
        ("None", None),
        ("a tuple of the right values", (0, 2, 4, 1, 3, 5)),
        ("a string", "024135"),
        ("an int", 3),
        ("one odd left in front", [0, 1, 2, 4, 3, 5]),
        ("the last even at the back", [0, 2, 1, 3, 5, 4]),
        ("odds first", [1, 3, 5, 0, 2, 4]),
        ("the evens dropped", [1, 3, 5]),
        ("the odds dropped", [0, 2, 4]),
        ("an element missing", [0, 2, 4, 1, 3]),
        ("an element added", [0, 2, 4, 1, 3, 5, 6]),
        ("a value changed", [0, 2, 6, 1, 3, 5]),
    ]
    for probe, value in rejected:
        with pytest.raises(AssertionError):
            _check(f"grader self-test, rejected: {probe}", original, value)

    # Sorting by value is the wrong question, and on this input it is visibly wrong: 3 < 4.
    with pytest.raises(AssertionError):
        _check("grader self-test, rejected: sorted by value", [3, 1, 2, 4], [1, 2, 3, 4])
    # A duplicate dropped is caught by the multiset rule rather than by the length rule.
    with pytest.raises(AssertionError):
        _check("grader self-test, rejected: duplicate replaced", [2, 2, 1], [2, 4, 1])
    # 0 is even, and a solution that treats it as odd is wrong rather than merely unusual.
    with pytest.raises(AssertionError):
        _check("grader self-test, rejected: zero pushed to the back", [0, 1], [1, 0])


# ======================================================================================
# Hand-written cases. Each is (probe, nums).
# ======================================================================================

Case = tuple[str, list[int]]

CASES: list[Case] = [
    # --- the statement's own examples ------------------------------------------------------
    ("example 1", [3, 1, 2, 4]),
    ("example 2, a single zero", [0]),
    # --- one element, the shortest legal input -------------------------------------------------
    ("a single even", [2]),
    ("a single odd", [1]),
    ("a single value at the top of the range", [5000]),
    ("a single odd at the top of the range", [4999]),
    # --- nothing to do -------------------------------------------------------------------------
    ("every value even", [2, 4, 6, 8]),
    ("every value odd", [1, 3, 5, 7]),
    ("already evens then odds", [2, 4, 1, 3]),
    ("exactly reversed: odds then evens", [1, 3, 2, 4]),
    # --- two elements, where every ordering question is visible ---------------------------------
    ("even then odd", [2, 1]),
    ("odd then even", [1, 2]),
    ("two evens", [4, 2]),
    ("two odds", [3, 1]),
    # --- zero, which is even and is the value most often mishandled -----------------------------
    ("zero among odds", [1, 0, 3]),
    ("zero at the back", [1, 3, 0]),
    ("zero at the front", [0, 1, 3]),
    ("several zeros", [1, 0, 0, 3, 0]),
    ("zero and the largest even", [1, 0, 5000]),
    ("zero on its own with one odd", [0, 1]),
    # --- one of a kind ---------------------------------------------------------------------
    ("one even among odds", [1, 3, 2, 5, 7]),
    ("one odd among evens", [2, 4, 3, 6, 8]),
    ("one even, at the very back", [1, 3, 5, 2]),
    ("one odd, at the very front", [1, 2, 4, 6]),
    # --- alternating and repeated ---------------------------------------------------------------
    ("alternating, starting even", [2, 1, 4, 3, 6, 5]),
    ("alternating, starting odd", [1, 2, 3, 4, 5, 6]),
    ("one value repeated, even", [4, 4, 4, 4]),
    ("one value repeated, odd", [5, 5, 5, 5]),
    ("duplicates of both parities", [2, 1, 2, 1, 2, 1]),
    # --- the extremes the constraints allow -----------------------------------------------------
    ("both ends of the value range", [5000, 0]),
    ("the largest odd and the largest even", [4999, 5000]),
    ("the full range with an odd between", [0, 4999, 5000]),
    # --- descending values, so a sort by value is visibly the wrong question --------------------
    ("descending, evens and odds mixed", [9, 8, 7, 6, 5, 4]),
    ("descending odds after descending evens", [8, 6, 4, 9, 7, 5]),
    # --- long enough that an off-by-one at either end cannot hide -------------------------------
    ("24 elements, alternating", list(range(24))),
    ("24 elements, all even", [2 * i for i in range(24)]),
    ("24 elements, all odd", [2 * i + 1 for i in range(24)]),
    ("24 elements, one odd at index 12", [2] * 12 + [3] + [4] * 11),
    # --- the constraint ceiling, in the tier that runs by default -------------------------------
    ("the ceiling, alternating", list(range(CEILING))),
    ("the ceiling, every value even", [2 * (i % 2500) for i in range(CEILING)]),
    ("the ceiling, one odd in the middle", [2] * 2500 + [3] + [2] * 2499),
]


@pytest.mark.parametrize("probe,nums", CASES)
def test_examples_and_edges(probe: str, nums: list[int]) -> None:
    _run(probe, list(nums))


def test_cases_obey_the_stated_constraints() -> None:
    """The fixtures are held to the same contract the solution is.

    A case outside the constraints would demand something never asked for, and a solution that
    failed it would be right to. Checked rather than assumed: these cases are hand-written.
    """
    for probe, nums in CASES:
        assert 1 <= len(nums) <= CEILING, f"[{probe}]: 1 <= nums.length <= 5000"
        assert all(0 <= x <= MAX_VALUE for x in nums), f"[{probe}]: 0 <= nums[i] <= 5000"


@pytest.mark.property
def test_every_small_arrangement() -> None:
    """Every list of length 1 to 6 over a four-value alphabet, exhaustively. 5,460 lists.

    The alphabet is (0, 1, 2, 3): two even values one of which is zero, and two odd ones, so every
    list carries duplicates of a parity as well as both parities. Exhaustive, so every count of
    evens, every count of odds and every interleaving of them is covered rather than sampled.
    """
    total = 0
    for n in range(1, 7):
        for tup in product((0, 1, 2, 3), repeat=n):
            _run(f"exhaustive n={n}, nums={list(tup)}", list(tup))
            total += 1
    assert total == sum(4 ** n for n in range(1, 7)) == 5460


@pytest.mark.property
def test_matches_oracle_on_random_inputs() -> None:
    """Random lists, graded against the reference, inside the stated constraints.

    The proportion of evens is varied on purpose: a list that is all one parity and a list with a
    single element of the other ask the same question and break different solutions. One run in
    six uses only the two extreme values, 0 and 5000, both of which are even, so that a solution
    which reaches for the ends of the value range rather than for parity has somewhere to go wrong.
    """
    rng = random.Random(905)
    for i in range(2000):
        n = rng.randint(1, 40)
        style = i % 6
        if style == 5:
            nums = [rng.choice([0, 5000, 4999]) for _ in range(n)]
        else:
            share = (0.0, 0.1, 0.5, 0.9, 1.0)[style]
            nums = [2 * rng.randint(0, 2500) if rng.random() < share
                    else 2 * rng.randint(0, 2499) + 1 for _ in range(n)]
        assert 1 <= len(nums) <= CEILING, "the generator must obey the constraints"
        assert all(0 <= x <= MAX_VALUE for x in nums), "the generator must obey the constraints"
        _run(f"random n={n}, style {style}", nums)


# ======================================================================================
# Shapes, used by the sweep, the ceiling and the growth guard.
#
# Every one of them stays inside 0 <= nums[i] <= 5000 at any length, including the lengths the
# growth guard invents for itself, so no measurement here is taken on a value the problem does not
# allow.
# ======================================================================================


def _all_even(n: int, seed: int = 1) -> list[int]:
    """Nothing has to move. Every solution's answer is some arrangement of the whole input."""
    rng = random.Random(seed)
    return [2 * rng.randint(0, MAX_VALUE // 2) for _ in range(n)]


def _all_odd(n: int, seed: int = 2) -> list[int]:
    """The mirror image, and not a corner case: nothing promises an even value anywhere.

    A solution whose cost is paid per even value does no work at all here, which makes this the
    shape that catches cost paid per odd value instead. See `test_does_not_grow_quadratically`.
    """
    rng = random.Random(seed)
    return [2 * rng.randint(0, (MAX_VALUE - 1) // 2) + 1 for _ in range(n)]


def _random_mix(n: int, seed: int = 3) -> list[int]:
    """Both parities, in no pattern, over the whole legal value range."""
    rng = random.Random(seed)
    return [rng.randint(0, MAX_VALUE) for _ in range(n)]


def _odds_then_evens(n: int, seed: int = 4) -> list[int]:
    """Exactly backwards: every odd value first. Every element is on the wrong side of the list."""
    rng = random.Random(seed)
    return ([2 * rng.randint(0, 2499) + 1 for _ in range(n // 2)]
            + [2 * rng.randint(0, 2500) for _ in range(n - n // 2)])


def _evens_then_odds(n: int, seed: int = 5) -> list[int]:
    """Already an accepted answer. It still has to come back as one."""
    rng = random.Random(seed)
    return ([2 * rng.randint(0, 2500) for _ in range(n // 2)]
            + [2 * rng.randint(0, 2499) + 1 for _ in range(n - n // 2)])


def _alternating_even_first(n: int, seed: int = 6) -> list[int]:
    """Even, odd, even, odd. No two of a parity adjacent.

    The values run 0, 1, 2, ... and start again at 0 once they reach 5000, which is the largest
    value allowed. The wrap keeps the parities alternating because the period is even, so this is
    list(range(n)) for every length the constraints permit and stays legal past them.
    """
    return [i % 5000 for i in range(n)]


def _alternating_odd_first(n: int, seed: int = 7) -> list[int]:
    """Odd, even, odd, even. The same list shifted by one, which flips every parity."""
    return [i % 5000 + 1 for i in range(n)]


def _one_odd_at_the_front(n: int, seed: int = 8) -> list[int]:
    """A single odd value, at index 0, which has to end up behind everything."""
    a = [2] * n
    a[0] = 3
    return a


def _one_even_at_the_back(n: int, seed: int = 9) -> list[int]:
    """A single even value, at the last index, which has to end up in front of everything."""
    a = [3] * n
    a[-1] = 2
    return a


def _one_odd_in_the_middle(n: int, seed: int = 10) -> list[int]:
    """A single odd value, away from both ends, where a solution that special-cases edges sees it.

    Every shape above plants what it is about at index 0, at index n - 1, or everywhere at once.
    This is the interior case at every length the sweep visits.
    """
    a = [2] * n
    a[n // 2] = 3
    return a


def _extremes(n: int, seed: int = 11) -> list[int]:
    """Only the ends of the legal value range and their neighbours. 0 and 5000 are both even."""
    rng = random.Random(seed)
    return [rng.choice([0, 5000, 4999, 1]) for _ in range(n)]


SHAPES: tuple[tuple[str, Callable[..., list[int]]], ...] = (
    ("every value even", _all_even),
    ("every value odd", _all_odd),
    ("a random mix", _random_mix),
    ("odds first, then evens", _odds_then_evens),
    ("evens first, then odds", _evens_then_odds),
    ("alternating, even first", _alternating_even_first),
    ("alternating, odd first", _alternating_odd_first),
    ("one odd, at the front", _one_odd_at_the_front),
    ("one even, at the back", _one_even_at_the_back),
    ("one odd, in the middle", _one_odd_in_the_middle),
    ("the extremes of the value range", _extremes),
)


def test_the_shape_builders_are_what_they_claim() -> None:
    """Each builder produces a legal input of the length asked for, in the shape it is named for.

    Nothing here needs an answer known by construction, since the reference is cheap and grades
    every input in this file directly. What does have to be checked is that the builders stay
    inside the constraints and keep their shape, because a shape that quietly stopped containing
    even values would weaken a timing guard without failing anything. The two largest lengths
    checked are the two the growth guard measures at, where the value range is the thing most
    easily lost: a builder that counted upwards without wrapping would leave the legal range at
    5,001 elements and nobody would notice.
    """
    expectations = {
        "every value even": lambda a: all(x % 2 == 0 for x in a),
        "every value odd": lambda a: all(x % 2 for x in a),
        "a random mix": lambda a: True,
        "odds first, then evens": lambda a: len(a) < 2 or a[-1] % 2 == 0,
        "evens first, then odds": lambda a: len(a) < 2 or a[-1] % 2 == 1,
        "alternating, even first": lambda a: all((x % 2 == 0) == (i % 2 == 0)
                                                 for i, x in enumerate(a)),
        "alternating, odd first": lambda a: all((x % 2 == 1) == (i % 2 == 0)
                                                for i, x in enumerate(a)),
        "one odd, at the front": lambda a: sum(x % 2 for x in a) == 1 and a[0] % 2 == 1,
        "one even, at the back": lambda a: sum(x % 2 == 0 for x in a) == 1 and a[-1] % 2 == 0,
        "one odd, in the middle": lambda a: sum(x % 2 for x in a) == 1,
        "the extremes of the value range": lambda a: set(a) <= {0, 1, 4999, 5000},
    }
    for name, make in SHAPES:
        for n in (1, 2, 3, 7, 8, 64, 999, 1000, CEILING, SMALL_N, SMALL_N * FACTOR):
            a = make(n)
            assert len(a) == n, f"{name}: builder returned {len(a)} elements, wanted {n}"
            assert all(0 <= x <= MAX_VALUE for x in a), f"{name} at n={n}: value out of range"
            assert expectations[name](a), (
                f"the builder {name!r} at n={n} produced {_render(a)}, which is not the shape its "
                f"name promises -- fix the builder, not the solution"
            )


SWEEP_BUDGET = 30.0  # seconds; see test_every_length_up_to_the_ceiling


@pytest.mark.property
def test_every_length_up_to_the_ceiling() -> None:
    """A sweep over the legal lengths, in every shape above, from 1 to the ceiling.

    The tests above stop at 40 elements and the ceiling test below runs only at 5000, and a gap
    like that is somewhere for a bug to live: a solution that handles the last element separately,
    or walks the list in fixed-size chunks, can be right on every tiny length, right again on a
    round 5000, and wrong on 37. The lengths where two converging positions meet -- odd lengths,
    even lengths, and both sides of each -- are all in here for the same reason. 188 lengths are
    taken in all, every one from 1 to 120 and then no gap anywhere below the ceiling wider than
    125, in each of the eleven shapes: 2,068 calls.

    The whole sweep is held to a wall clock, and that is not a speed requirement: the guards below
    are where speed is graded, and this one is a diagnosis instead of a silence. Two thousand calls
    land here, many of them near the ceiling, so a solution whose cost per element grows with the
    length of the list can sit in a test that has nothing to say about speed for a very long time.
    Measured on this repo's interpreter, CPython 3.14.4, the twelve correct solutions measured for
    this file get through the entire sweep in 0.43 - 0.84 s. The budget is 30 s, some thirty-six
    times the slowest of them. Two of the ten rejected solutions measured for this file trip it --
    the one that walks the list swapping neighbours until nothing is out of place, and the one that
    passes over the whole list once per value the constraints allow -- and both get 1,953 and 1,957
    of the 2,068 calls done before they do, so even they are barely caught here. Everything else is
    left to the guards below, which say the same thing with a number attached.
    """
    started = time.perf_counter()
    done = 0

    lengths = list(range(1, 121))
    for base in (128, 200, 256, 500, 512, 1000, 1024, 2048, 4096, CEILING):
        lengths += [base - 1, base, base + 1]
    lengths += list(range(120, CEILING, 125))
    lengths = sorted({n for n in lengths if 1 <= n <= CEILING})
    planned = len(lengths) * len(SHAPES)

    for n in lengths:
        for name, make in SHAPES:
            _run(f"n={n}, {name}", make(n))
            done += 1
            elapsed = time.perf_counter() - started
            assert elapsed < SWEEP_BUDGET, (
                f"the length sweep was abandoned after {elapsed:.0f}s and {done} of {planned} "
                f"calls, the last of them n={n}, {name}. This test grades answers, not speed, and "
                f"it is stopping only because it cannot finish: the correct solutions measured "
                f"for this file get through the whole sweep in 0.43 - 0.84 s. The two guards "
                f"below are the ones that grade speed, and they will say the same thing with "
                f"numbers attached -- run them with `uv run pytest -m slow`."
            )

    assert done == planned, f"the sweep made {done} calls, not the {planned} it planned"


# ======================================================================================
# Timing guards.
# ======================================================================================


def _ceiling_cases(count: int = 500, n: int = CEILING, seed: int = 905) -> list[list[int]]:
    """`count` lists at the constraint ceiling, cycling through every shape above."""
    return [SHAPES[i % len(SHAPES)][1](n, seed + i) for i in range(count)]


CEILING_BUDGET = 4.000  # seconds for 500 calls at n = 5000; see test_constraint_ceiling
GRADED_BUDGET = 45.0  # seconds for the 500 graded calls that come first


@pytest.mark.slow
def test_constraint_ceiling() -> None:
    """n = 5000, the largest input the constraints allow, against a wall-clock budget.

    A single call at the ceiling is over in a fraction of a millisecond, too quick to measure
    against machine noise, so the budget covers 500 of them, cycling every shape above. Measured on
    this repo's interpreter, CPython 3.14.4, best of three rounds over those 500 cases. The slowest
    rows were measured with the round cut short at 20 seconds and their totals extrapolated from
    the calls that did finish; those are marked with the count that was reached.

        eleven correct solutions                    60.0 - 191.3 ms   0.120 - 0.383 ms a call
        a sort whose comparison runs in Python             662.5 ms           1.325 ms a call
        --------------------------------------------------- budget: 4,000 ms
        move only the misplaced evens, in place          1,039.5 ms     2.079 ms a call
        pop each even and insert it at the front         1,535.8 ms     3.072 ms a call
        grow the answer by rebinding it per element      5,554.3 ms    11.109 ms a call
        rebuild the list out of slices per swap         11,295.9 ms    22.592 ms a call
        find the next even and lift it out              17,929.3 ms    35.859 ms a call
        carry each odd to the back                      24,761.7 ms    49.523 ms a call  (425)
        carry each even to the front                    32,673.0 ms    65.346 ms a call  (325)
        one list scan per distinct value                34,322.7 ms    68.645 ms a call  (300)
        one pass over the list per legal value          71,235.9 ms   142.472 ms a call  (150)
        adjacent swaps until nothing is misplaced      144,021.5 ms   288.043 ms a call   (75)

    The bottom two rows never actually reach this budget: at 71.30 s and 143.67 s they run out of
    the graded clock below first, and get told so there.

    Two rows sit below the budget and are meant to. This ceiling is small enough that no wall clock
    can separate the whole field: the slowest correct solution measured costs 662.5 ms and the
    quickest rejected one costs 1,039.5 ms, a gap of 1.6x, and a budget inside a gap that narrow
    would fail correct solutions on a busy machine. Both of those rows are quadratic and both are
    caught by the ratio below, at 62.33x and 62.53x. This budget is a floor, not a filter.

    What it catches that the ratio cannot is the two rows that count values rather than move them,
    and they are the reason it exists rather than an accident of where it landed. Both are correct
    answers whose cost is a count of values times n. The constraints cap nums[i] at 5000, so that
    first factor saturates and both are honestly linear in n: measured at n = 4,000 against
    n = 32,000 they grow by 7.90x - 14.98x and 7.82x - 8.94x respectively across all eleven shapes,
    well inside the ratio's ceiling of 25x on every one of them. Nothing about their shape is
    wrong. They are simply enormous, and only a clock at the real ceiling says so.

    The budget sits at 21x the slowest of the eleven and 6.0x the sort whose comparison runs in
    Python, which is the slowest correct route measured and is entitled to pass. That last margin
    was chosen against a measurement rather than a guess: the same 500-call round, best of three
    exactly as this test takes it, was run in competing processes on this ten-core machine -- four
    performance cores and six efficiency ones -- and gave 682 - 686 ms alone, 768 - 798 ms with
    four at once, 953 - 1,058 ms with eight, and 1,292 - 1,455 ms with twelve, 36 statistics at
    that last level. The budget clears the worst of those by 2.7x.

    The correctness half of this test is not a formality. It runs 500 cases at the ceiling across
    every shape in the file, and a wrong answer here is reported as a wrong answer, not a slow one.
    Those 500 graded calls -- which include building the answer key and checking it -- cost
    0.47 - 1.01 s for the correct solutions measured, so they get their own clock at 45 s. That
    number is not arbitrary either: of the solutions measured for this file the slowest to get
    through the graded half took 33.96 s, and the next two took 71.30 s and 143.67 s, so 45 s sits
    inside a gap of better than 2x and which failure a given solution gets is stable rather than a
    coin flip.
    """
    cases = _ceiling_cases()
    started = time.perf_counter()
    for i, nums in enumerate(cases):
        assert len(nums) == CEILING, f"ceiling case {i}: built {len(nums)} elements, want {CEILING}"
        assert all(0 <= x <= MAX_VALUE for x in nums), f"ceiling case {i}: value out of range"
        _run(f"ceiling case {i}, n={CEILING}", list(nums))
        graded = time.perf_counter() - started
        assert graded < GRADED_BUDGET, (
            f"the {len(cases)} graded calls at the ceiling were abandoned after {graded:.0f}s, "
            f"with {i + 1} of them done. Nothing was wrong with the answers -- this part of the "
            f"test grades answers, not speed, and it is stopping only because a solution this slow "
            f"makes it look like a hang. The correct solutions measured for this file get through "
            f"all {len(cases)}, answer key and all, in 0.47 to 1.01 s. The budget below is the one "
            f"that grades speed, and it never got to run."
        )

    sort_by_parity = Solution().sortArrayByParity
    readings: list[tuple[float, int]] = []
    for _ in range(3):
        fresh = [list(nums) for nums in cases]
        done = 0
        start = time.perf_counter()
        for nums in fresh:
            sort_by_parity(nums)
            done += 1
            # Checked every 25 calls rather than every call, so that the clock stays out of the
            # measurement while a hopeless run is still cut short inside a second of the budget.
            if done % 25 == 0 and time.perf_counter() - start >= CEILING_BUDGET:
                break
        readings.append((time.perf_counter() - start, done))
        if readings[-1][0] < CEILING_BUDGET:
            break

    best, done = min(readings)
    taken = ", ".join(f"{r * 1e3:.0f}ms" for r, _ in readings)
    assert best < CEILING_BUDGET, (
        f"{done} of {len(cases)} calls at the ceiling (n = {CEILING:,}) already cost "
        f"{best * 1e3:.0f}ms, over the {CEILING_BUDGET * 1e3:.0f}ms budget for all "
        f"{len(cases)} (measured {taken}), and the run was cut short the moment the budget went, "
        f"so the real figure is worse: {best / done * 1e6:.0f}us per call, against the 120 - 383us "
        f"a single pass over 5000 elements costs here. Two things land a solution here. One is "
        f"work that moves a run of elements once per element, which the growth guard below will "
        f"also report. The other is work the growth guard cannot see at all: a scan of the whole "
        f"list done once per distinct value, or once per value the constraints allow, is linear in "
        f"the length of the list and still costs a hundred times what one pass costs, because "
        f"0 <= nums[i] <= 5000 caps the number of values but not the size of that constant."
    )


# --- the growth guard's measuring apparatus -------------------------------------------------
#
# Every call needs a list of its own, since a solution is free to rewrite what it is given, so the
# copy is made inside the measured region. That is deliberate, and the arithmetic says it cannot
# bend the verdict. Measured on this interpreter, best of nine, list(data) costs 5.89 us at
# n = 4,000 and 63.96 us at n = 32,000 -- 10.87x for eight times the data, so the copy is very
# slightly worse than linear at these sizes rather than better. That is the direction that could
# hurt, so it is worth bounding rather than waving at: a sample here is the copy plus the call, the
# copy is at most 7.8% of it at the small size and at most 10.3% at the large one across the twelve
# correct solutions measured, and a blend of a term growing at 8x with a term growing at 10.87x
# cannot land above 10.87x whatever the weights are. The ceiling below is 25x. What the copy buys
# is that memory stays at two lists however many repetitions get taken, and that a solution is
# never timed against a list some earlier call already partitioned -- which for this problem would
# be a list that is already an accepted answer.

GROWTH_CEILING = 25.0  # the ratio a solution may not exceed; see test_does_not_grow_quadratically
SMALL_N, FACTOR = 4_000, 8
BATCH_TARGET = 0.003  # seconds; how long one timed sample must last
HOPELESS = 0.010  # seconds for one call at the small size; past this, report rather than measure


def _seconds_per_call(data: list[int], batch: int) -> float:
    """Seconds per call, averaged over `batch` calls, each on a fresh copy of `data`."""
    start = time.perf_counter()
    for _ in range(batch):
        c = list(data)
        solve(c)
    return (time.perf_counter() - start) / batch


def _batch_size(data: list[int]) -> int:
    """The smallest power-of-two batch whose run lasts at least BATCH_TARGET seconds.

    One call at n = 4,000 takes a fraction of a millisecond, and a sample that short is not a
    measurement of the code -- it is a measurement of what else the machine was doing during it.
    Timing a batch and dividing is what makes the number hold up when the machine is busy.
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

    Nine a side rather than three is cheap insurance, and the honest version of why is that at
    these sizes it buys very little. Sixty readings of the twelve correct solutions on the five
    timed shapes gave 7.10x - 11.93x with three repetitions a side and 7.60x - 11.75x with nine, so
    the two agree. What nine protects against is the tail that opens up as samples get shorter: the
    same twelve measured at n = 1,000 against n = 8,000, where a sample is a tenth as long, threw
    single readings of 21.4x and 22.9x with three a side, against a ceiling of 25x. A guard is
    sized by its worst reading and not its typical one.

    The early exit keeps nine repetitions from being slow to fail. Once three pairs are in and the
    big side is past the ceiling with 50 ms of headroom on top, more repetitions cannot bring it
    back. The 50 ms is flat rather than proportional so that a verdict is never reached on the
    strength of microseconds of interference between two small numbers: the slowest sample any
    correct solution produced at n = 32,000 on these shapes was 9.68 ms, so the headroom alone
    keeps it clear. What trips it is a call costing a tenth of a second.
    """
    small_batch, big_batch = _batch_size(small), _batch_size(big)
    best_small = best_big = float("inf")
    for taken in range(1, reps + 1):
        best_small = min(best_small, _seconds_per_call(small, small_batch))
        best_big = min(best_big, _seconds_per_call(big, big_batch))
        if taken >= 3 and best_big > GROWTH_CEILING * best_small + 0.050:
            break
    return best_big / best_small


TIMED_SHAPES: tuple[tuple[str, Callable[..., list[int]]], ...] = (
    ("every value even", _all_even),
    ("every value odd", _all_odd),
    ("a random mix", _random_mix),
    ("odds first, then evens", _odds_then_evens),
    ("alternating, even first", _alternating_even_first),
)


@pytest.mark.slow
def test_does_not_grow_quadratically() -> None:
    """Eight times the input should cost about eight times the work, on five shapes.

    These sizes run past the stated n <= 5000, on purpose. The code under test does not change with
    the size, so running it larger makes the same shape visible with no ambiguity left in it, and
    the budget above has already shown that ambiguity is what the real ceiling offers. The values
    stay inside 0 <= nums[i] <= 5000 at both sizes; it is only the length that grows.

    Measured on this repo's interpreter, CPython 3.14.4, n = 4,000 then 32,000, nine repetitions
    a side. Twelve correct solutions, seven rejected ones and the two value-counting solutions
    named in the budget above were measured on all eleven shapes in this file -- 231 readings --
    and the five columns below are the shapes this guard actually times. Ten of the correct
    solutions are given as a band, since what matters about them is that they land together; the
    two that are not linear are named, and so is every rejected one.

                                                 even      odd      mix backwrds  alt'ing
        ten linear correct solutions        7.56x - 8.68x over all fifty readings
        a sort with a Python comparison         7.51x   10.67x    8.07x    8.38x    9.06x
        sorted evens then sorted odds          11.12x   11.34x   11.12x   11.86x    8.45x
        ------------------------------------------------------------------ ceiling: 25x
        carry each even to the front             8.12     8.07    68.23    65.73    63.97
        carry each odd to the back               8.15     8.29    68.12    64.43    65.50
        rebuild the list out of slices           8.04     8.07    78.41    70.23    74.63
        move only the misplaced evens            8.11     8.16    62.77    62.33    63.82
        pop each even, insert at the front      62.93     8.15    62.85    62.53    63.88
        find the next even and lift it out      48.75     8.19    69.47    65.75    65.60
        grow the answer by rebinding it        104.25   104.77   112.23   125.13   105.92

    Across all 132 readings of the twelve correct solutions on all eleven shapes the worst was
    11.88x; the lowest any rejected solution produced on a shape that gives it work to do was
    46.46x. The ceiling sits in that gap, nearer the bottom of it than the middle, because failing
    a correct solution is a worse outcome here than letting a slow one through -- and a slow one
    still has the budget above, and a submission page, to get past.

    Read the columns before reading the rows. This problem is symmetrical: it has a group that has
    to end up in front and a group that has to end up behind, and a solution that carries the wrong
    group across the list is quadratic in the size of that group and costs nothing when that group
    is empty. On a list of nothing but odd values, six of the seven rejected solutions measure
    between 8.07x and 8.29x; on a list of nothing but even values, four of them measure between
    8.04x and 8.15x. Those are inside the band the correct ones occupy: invisible,
    indistinguishable. A guard built only from pure shapes would pass every one of them. The three
    mixed columns are what catch them, and no rejected solution measured here gets under 62.33x on
    any of the three.

    So why keep the two pure columns at all. Because "the mixed shapes are the ones that catch" is
    a claim about this field of solutions and not a law, and a guard that never measures the input
    on which a parity-specific cost disappears has no way to notice when that stops being true.
    They also cost almost nothing: most of the rejected solutions are linear on those two shapes,
    so the samples come back quickly.

    The three mixed columns are not interchangeable either, and the reason is displacement rather
    than count. All three hold both parities in quantity, but they place them very differently: in
    the random mix the two are interleaved in no pattern, in the backwards arrangement every
    single element is on the wrong side of the list and has the length of it to travel, and in the
    alternating one no two neighbours share a parity yet nothing has far to go. A cost that tracks
    how far things move rather than how many of them do would read differently across those three.
    On the seven measured it does not -- they agree to within 20% -- which is a measured result and
    not an assumption, and it is worth
    keeping all three so that it stays one.

    Two solutions this guard cannot see are named in `test_constraint_ceiling` above, and they are
    the reason that guard is not redundant with this one: work proportional to the number of
    distinct values, or to the number of values the constraints allow, is genuinely linear in n
    once that factor saturates, and lands at 7.90x - 14.98x and 7.82x - 8.94x here while costing
    68.6 and 142.5 ms a call at the ceiling. A ratio cannot see a constant, however large it is.

    A ratio over the ceiling is measured again before it is reported, up to three times in all, and
    only fails if every attempt agrees. The re-measurement is for the machine's benefit, not the
    solution's: the readings above are tight and uncorrelated, so three excursions in a row is not
    something a correct solution runs into, while a genuinely quadratic one is over the ceiling
    every single time. A ratio past twice the ceiling is not re-measured at all -- nothing that far
    out is noise -- which is what keeps the slowest solutions from taking three times as long to be
    told they are slow.
    """
    attempts = 3
    for name, make in TIMED_SHAPES:
        small, big = make(SMALL_N, 1), make(SMALL_N * FACTOR, 2)

        # Correctness at the smaller of the two timed sizes, checked before anything is timed. A
        # wrong answer should say it is wrong, not that it is slow.
        _run(f"n={SMALL_N:,}, {name}", list(small))

        # A cheap look before committing to the full measurement. One call at this size cost
        # between 0.079 and 1.170 ms across the twelve correct solutions measured on these five
        # shapes, the top of that range being the sort whose comparison runs in Python; 10 ms sits
        # 8.5x above it. This is not the guard -- the ratio below is -- and most of the rejected
        # solutions sail through it, including the one that grows the answer by rebinding it, at
        # 3.7 to 9.3 ms. It is here so that something costing a third of a second a call is told so
        # in a moment, rather than being timed nine times over at eight times the size.
        probe = min(_seconds_per_call(small, 1) for _ in range(3))
        assert probe < HOPELESS, (
            f"one call over {SMALL_N:,} elements ({name}) took {probe * 1e3:.1f} ms, so the growth "
            f"measurement was not attempted: at eight times the length, nine repetitions a side "
            f"would take minutes. The twelve correct solutions measured for this file cost 0.079 "
            f"to 1.170 ms here, and the solution that walks the list swapping neighbours until "
            f"nothing is out of place costs 342 ms. test_constraint_ceiling above has reported "
            f"this with a per-call number attached; the shape of the growth is not the interesting "
            f"question until the size of it is."
        )

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
            f"{FACTOR}x; {min(seen):.0f}x means the work done per element grows with the length "
            f"of the list. The algorithm may well be right -- look instead for a step inside the "
            f"loop that is not O(1). nums.insert(i, x), nums.pop(i) and del nums[i] all move "
            f"every element past the position they touch, and inserting at the front moves all of "
            f"them; `in`, .index() and .count() walk the list; slicing copies it. Note which shape "
            f"this is -- {name!r}: the problem is symmetrical, so a solution can be quick on one "
            f"parity and quadratic on the other, and quick on both when the list holds only one "
            f"of them."
        )


# ---------------------------------------------------------------------------------------
# What this suite does NOT check, and why none of it is an oversight.
#
# WHAT HAPPENS TO nums. Never looked at after the call. "Return any array that satisfies this
# condition" makes the returned value the answer, so a solution that builds a new list and leaves
# nums exactly as it arrived is correct here and correct on the submission page -- the two-pass
# [x for x in nums if x % 2 == 0] + [x for x in nums if x % 2] passes this file as it stands, and
# it was run against every test here to make sure of it. Requiring the rearrangement to happen in
# place would be this suite inventing a rule the problem does not have, and it is the one rule 1299
# in this chapter does invent -- deliberately, and only there, because there the statement already
# says the array comes back. The stub says plainly that the in-place version is the better exercise
# and is not the spec.
#
# THE ORDER WITHIN EACH PARITY GROUP. Not checked, in either direction. Sorted, reversed, arrival
# order and shuffled are all equally accepted, which is what
# `test_the_grader_accepts_every_arrangement_the_statement_does` exists to hold the grader to, and
# solutions taking each of those four routes were run against this file to confirm it. A suite that
# quietly preferred one of them would turn this into a harder problem than it is, and would erase
# the contrast with 283 that is the reason both are in this chapter.
#
# EXTRA SPACE. Not measured. Nothing here counts allocations or objects.
#
# WHICH ROUTE THE SOLUTION TOOK. No static check on any name.
# ---------------------------------------------------------------------------------------
