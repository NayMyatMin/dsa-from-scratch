"""Reference answer used to grade 27. Remove Element.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem, and this function settles the part of 27 that is worth thinking about -- not
how many survivors there are, but what the survivors are and where the graded ones sit. Nothing in
`arrays101/` imports this module; it exists only so the tests have something to disagree with.

Open it if you like. Just know that you are opening the answer.
"""


def oracle(nums: list[int], val: int) -> list[int]:
    """The multiset the first k slots of `nums` must hold, in sorted order.

    Sorted because the judge sorts: it compares the first k slots against the expected answer only
    after putting both in order, so the arrangement a solution leaves behind is its own business.
    len(oracle(...)) is therefore also the k that must be returned.

    Returns a new list rather than mutating, so the tests can compute the answer key from a
    pristine snapshot and compare it against whatever the solution did to the real input.
    """
    return sorted(x for x in nums if x != val)
