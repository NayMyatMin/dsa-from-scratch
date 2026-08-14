"""Reference answer used to grade 1089. Duplicate Zeros.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem, and this function gives the whole game away: it is a complete, working
answer that happens to be written with a second list instead of inside the one you were handed.
Nothing in `arrays101/` imports this module; it exists only so the tests have something to
disagree with.

Open it if you like. Just know that you are opening the answer.
"""


def oracle(arr: list[int]) -> list[int]:
    """The contents `arr` must hold once the zeros have been duplicated.

    Returns a new list rather than mutating, so the tests can compute the answer key from a
    pristine snapshot and compare it against whatever the solution did to the real input.
    """
    out: list[int] = []
    for x in arr:
        out.append(x)
        if x == 0:
            out.append(0)
    return out[: len(arr)]
