"""Reference answer used to grade 88. Merge Sorted Array.

This lives away from the spec on purpose. The spec file is meant to be read while you are still
solving the problem, and the whole difficulty of 88 is *where* the answer goes -- so a function
that computes the right contents in one obvious line, sitting a few lines above the test cases,
gives away more than it looks like it does.

Nothing in `arrays101/` imports this module; it exists only so the tests have something to
disagree with.

Open it if you like. Just know that you are opening a solution -- not the one the follow-up is
asking for, but enough of one to stop you thinking.
"""


def oracle(nums1: list[int], m: int, nums2: list[int], n: int) -> list[int]:
    """The contents `nums1` should hold once `merge` has finished.

    Takes copies and returns a new list: the grader must never be able to disturb the input it
    is grading, and the tests compare this against the list the solution was handed.
    """
    return sorted(nums1[:m] + nums2[:n])
