"""Reference answer used to grade 26. Remove Duplicates from Sorted Array.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem, and the one line below is a complete answer to the question "what should be
in the front of the array" -- which is most of the problem. Nothing in `arrays101/` imports this
module; it exists only so the tests have something to disagree with.

Open it if you like. Just know that you are opening the answer.
"""


def oracle(nums: list[int]) -> list[int]:
    """The values the first k slots of `nums` must hold, in the order they must hold them.

    The input arrives sorted non-decreasing, so the distinct values in sorted order are exactly
    the distinct values in their original relative order. len(oracle(...)) is the k that must be
    returned. Nothing sorts on the solution's behalf here: the judge compares the first k slots
    one at a time, so this list is positional, not a multiset.

    Returns a new list rather than mutating, so the tests can compute the answer key from a
    pristine snapshot and compare it against whatever the solution did to the real input.
    """
    return sorted(set(nums))
