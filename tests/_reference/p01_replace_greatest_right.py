"""Reference answer used to grade 1299. Replace Elements with Greatest Element on Right Side.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem, and this function is a complete, working answer: the statement transcribed
one position at a time, slow and obviously right rather than quick. Nothing in `arrays101/`
imports this module; it exists only so the tests have something to disagree with.

Open it if you like. Just know that you are opening an answer.
"""


def oracle(arr: list[int]) -> list[int]:
    """The exact contents `arr` must hold when the call returns.

    Straight off the statement: every position takes the greatest of the elements to its right,
    and the last position, which has none, takes -1. `max()` over a fresh slice each time, which
    is the words and no more.

    Returns a new list and never touches `arr`, so the tests can compute the answer key from a
    pristine snapshot and compare it against whatever the solution did to the real input.

    O(n^2), which is why the tests keep it to short lists and grade the long ones against inputs
    whose answer is known by construction.
    """
    n = len(arr)
    return [max(arr[i + 1:]) if i + 1 < n else -1 for i in range(n)]
