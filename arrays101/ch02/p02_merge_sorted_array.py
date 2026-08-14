"""88. Merge Sorted Array  (Easy)

https://leetcode.com/problems/merge-sorted-array/

You are given two integer arrays nums1 and nums2, sorted in non-decreasing order, and two
integers m and n, representing the number of elements in nums1 and nums2 respectively.

Merge nums1 and nums2 into a single array sorted in non-decreasing order.

The final sorted array should not be returned by the function, but instead be stored inside the
array nums1. To accommodate this, nums1 has a length of m + n, where the first m elements denote
the elements that should be merged, and the last n elements are set to 0 and should be ignored.
nums2 has a length of n.

Example 1:
    Input:  nums1 = [1,2,3,0,0,0], m = 3, nums2 = [2,5,6], n = 3
    Output: nums1 becomes [1,2,2,3,5,6]

Example 2:
    Input:  nums1 = [1], m = 1, nums2 = [], n = 0
    Output: nums1 becomes [1]

Example 3:
    Input:  nums1 = [0], m = 0, nums2 = [1], n = 1
    Output: nums1 becomes [1]
    Explanation: Note that because m = 0 there are no elements in nums1; the 0 is only there to
                 ensure the merge result can fit.

Constraints:
    nums1.length == m + n
    nums2.length == n
    0 <= m, n <= 200
    1 <= m + n <= 200
    -10^9 <= nums1[i], nums2[j] <= 10^9

Follow up: Can you come up with an algorithm that runs in O(m + n) time?

Target: O(m + n) time. That is what the follow-up asks for and what the tests enforce.

Then, once it passes, go again for O(1) extra space — merging with no scratch array at all.
That second version is the better answer and it is the one worth understanding, but it is an
ambition here rather than the spec: a correct linear solution that copies part of the input
aside is accepted, both by the tests and by the judge.

IN PLACE — read this part twice:
    - nums1 is the output. Mutate it. Do not rebind the name nums1 to a fresh list, and do not
      return one.
    - len(nums1) is already m + n and must still be m + n when you finish. The n trailing zeros
      are reserved room, not data — never treat them as values to be merged.
    - nums2 is read-only. It must come out identical to how it went in; the tests check.
    - The return value is ignored. The method returns None; the tests inspect nums1 afterwards.

Both inputs arrive sorted, and that is the entire advantage you are handed — a solution whose
first move is to sort has thrown it away, and the follow-up's O(m + n) is out of reach. The
hazard is that nums1 is both a source and the destination at once: every slot you write into is
a slot that may still hold one of the m values you have not placed yet.
"""


class Solution:
    def merge(self, nums1: list[int], m: int, nums2: list[int], n: int) -> None:
        raise NotImplementedError("your turn")
