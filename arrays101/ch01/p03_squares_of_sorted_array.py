"""977. Squares of a Sorted Array  (Easy)

https://leetcode.com/problems/squares-of-a-sorted-array/

Given an integer array nums sorted in non-decreasing order, return an array of the squares of
each number sorted in non-decreasing order.

Example 1:
    Input:  nums = [-4,-1,0,3,10]
    Output: [0,1,9,16,100]
    Explanation: After squaring, the array becomes [16,1,0,9,100].
                 After sorting, it becomes [0,1,9,16,100].

Example 2:
    Input:  nums = [-7,-3,2,3,11]
    Output: [4,9,9,49,121]

Constraints:
    1 <= nums.length <= 10^4
    -10^4 <= nums[i] <= 10^4
    nums is sorted in non-decreasing order.

Follow up: Squaring each element and sorting the new array is very trivial, could you find an
O(n) solution using a different approach?

--------------------------------------------------------------------------------------------
This problem is split into two methods on purpose. Do them in order.

  sortedSquaresNaive  -- the trivial one. Square, sort, return. One line if you like.
                         O(n log n). Write it first so you have a correct reference.

  sortedSquares       -- the follow-up. O(n) time, no sorting.
                         The test suite reads this method's source and FAILS it if it finds
                         sorted() or .sort(), so you can't accidentally pass with the naive
                         version. That guard is deliberate: the O(n) approach here is the
                         first genuinely non-obvious technique in the card, and it reappears
                         in Chapter 5.

The input is already sorted. That fact is the entire problem — a solution that starts by
sorting has thrown away the only thing it was given.
"""


class Solution:
    def sortedSquaresNaive(self, nums: list[int]) -> list[int]:
        """The trivial O(n log n) version. Sorting is allowed and expected here."""
        raise NotImplementedError("your turn")

    def sortedSquares(self, nums: list[int]) -> list[int]:
        """The O(n) follow-up. No sorted(), no .sort()."""
        raise NotImplementedError("your turn")
