"""485. Max Consecutive Ones  (Easy)

https://leetcode.com/problems/max-consecutive-ones/

Given a binary array nums, return the maximum number of consecutive 1's in the array.

Example 1:
    Input:  nums = [1,1,0,1,1,1]
    Output: 3
    Explanation: The first two digits or the last three digits are consecutive 1s.
                 The maximum number of consecutive 1s is 3.

Example 2:
    Input:  nums = [1,0,1,1,0,1]
    Output: 2

Constraints:
    1 <= nums.length <= 10^5
    nums[i] is either 0 or 1.

Target: O(n) time, O(1) extra space, in a single pass.

Note the upper bound on n. An O(n^2) solution — say, starting a fresh count at every index —
is 10^10 operations and will time out. Get the single pass.
"""


class Solution:
    def findMaxConsecutiveOnes(self, nums: list[int]) -> int:
        raise NotImplementedError("your turn")
