"""Reference answer used to grade 1346. Check If N and Its Double Exist.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem, and this function is a complete, working answer: the statement transcribed
one comparison at a time, slow and obviously right rather than quick. Nothing in `arrays101/`
imports this module; it exists only so the tests have something to disagree with.

Open it if you like. Just know that you are opening an answer.
"""


def oracle(arr: list[int]) -> bool:
    """True iff two distinct positions i, j exist with arr[i] == 2 * arr[j].

    Every ordered pair of distinct indices, checked one at a time, straight off the statement --
    including the `i != j` clause, which is the only thing standing between this and a wrong
    answer on a list holding exactly one zero.

    O(n^2), which is why the tests keep it to short lists and grade the long ones against inputs
    whose answer is known by construction.
    """
    n = len(arr)
    return any(arr[i] == 2 * arr[j] for i in range(n) for j in range(n) if i != j)
