"""Reference answer used to grade 283. Move Zeroes.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem, and this function is a complete, working answer: the statement transcribed,
built somewhere else rather than in place, because being obviously right matters here and being
in place does not. Nothing in `arrays101/` imports this module; it exists only so the tests have
something to disagree with.

Open it if you like. Just know that you are opening an answer.
"""


def oracle(nums: list[int]) -> list[int]:
    """The exact contents `nums` must hold when the call returns.

    The statement asks for two things and this is both of them written out: the non-zero elements
    in the relative order they arrived in, then as many zeros as there were, so that the length
    comes out unchanged. There is only ever one list that satisfies that, which is what makes this
    problem's grading exact rather than a check on some property of the answer.

    Returns a new list and never touches `nums`, so the tests can compute the answer key from a
    pristine snapshot and compare it against whatever the solution did to the real input. That is
    also the one thing this function is not allowed to be a model of: the problem says to do it
    in place, and this does not.

    O(n), so the tests can afford to grade the largest inputs the constraints allow against it.
    """
    kept = [x for x in nums if x != 0]
    return kept + [0] * (len(nums) - len(kept))
