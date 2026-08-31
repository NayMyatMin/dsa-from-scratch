"""Reference used to grade 905. Sort Array By Parity.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem. Nothing in `arrays101/` imports this module; it exists only so the tests
have something to disagree with.

Unlike the other references in this directory, this one is not an answer, and opening it gives
nothing away. 905 accepts any arrangement with the evens in front, so there is no single list to
compare against and nothing here computes one. What it produces instead is the pair of multisets
any accepted answer has to be built from -- which is a restatement of the question, not a route
to it.
"""


def oracle(nums: list[int]) -> tuple[list[int], list[int]]:
    """The evens and the odds of `nums`, each sorted, as two lists.

    Sorted so that they can be compared against the two halves of a returned answer without
    caring about the order inside either half, which is exactly the latitude the problem grants.
    An answer is accepted when its first len(evens) elements are some arrangement of `evens` and
    the rest are some arrangement of `odds`; those two conditions together also force it to be
    the right length and to hold the right values the right number of times.

    Returns new lists and never touches `nums`, so the tests can build the answer key from a
    pristine snapshot and compare it against what came back from a call that may well have
    rewritten the input.

    O(n log n), so the tests can afford to grade the largest inputs the constraints allow.
    """
    return sorted(x for x in nums if x % 2 == 0), sorted(x for x in nums if x % 2)
