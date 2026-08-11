"""Reference answer used to grade 485. Max Consecutive Ones.

This lives away from the spec on purpose. The spec file is meant to be read
while you are still solving the problem — an obviously-correct implementation
sitting three lines above the test cases is a solution in plain sight. Nothing
in `arrays101/` imports this module; it exists only so the tests have something
to disagree with.

Open it if you like. Just know that you are opening the answer.
"""

from itertools import groupby


def oracle(nums: list[int]) -> int:
    """Longest run of 1s. Slow and allocation-happy, but obviously correct."""
    runs = [len(list(g)) for k, g in groupby(nums) if k == 1]
    return max(runs, default=0)
