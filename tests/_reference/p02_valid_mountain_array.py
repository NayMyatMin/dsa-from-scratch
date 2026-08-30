"""Reference answer used to grade 941. Valid Mountain Array.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem, and this function is a complete, working answer: the definition transcribed
literally, one candidate summit at a time, slow and obviously right rather than quick. Nothing in
`arrays101/` imports this module; it exists only so the tests have something to disagree with.

Open it if you like. Just know that you are opening an answer.
"""


def oracle(arr: list[int]) -> bool:
    """True iff arr is a mountain array, by the definition and nothing else.

    The definition says: length at least 3, and some index i strictly inside the list such that
    everything up to i strictly rises and everything from i on strictly falls. So this tries every
    index strictly inside the list and checks both halves from scratch, which is exactly what the
    words say and no more.

    O(n^2), which is why the tests keep it to short lists and grade the long ones against inputs
    whose answer is known by construction.
    """
    n = len(arr)
    if n < 3:
        return False
    for i in range(1, n - 1):
        rises = all(arr[k] < arr[k + 1] for k in range(i))
        falls = all(arr[k] > arr[k + 1] for k in range(i, n - 1))
        if rises and falls:
            return True
    return False
