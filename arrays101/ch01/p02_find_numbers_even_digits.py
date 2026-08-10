"""1295. Find Numbers with Even Number of Digits  (Easy)

https://leetcode.com/problems/find-numbers-with-even-number-of-digits/

Given an array nums of integers, return how many of them contain an even number of digits.

Example 1:
    Input:  nums = [12,345,2,6,7896]
    Output: 2
    Explanation:
        12 contains 2 digits (even number of digits).
        345 contains 3 digits (odd number of digits).
        2 contains 1 digit (odd number of digits).
        6 contains 1 digit (odd number of digits).
        7896 contains 4 digits (even number of digits).
        Therefore only 12 and 7896 contain an even number of digits.

Example 2:
    Input:  nums = [555,901,482,1771]
    Output: 1
    Explanation: Only 1771 contains an even number of digits.

Constraints:
    1 <= nums.length <= 500
    1 <= nums[i] <= 10^5

Target: O(n * d) time where d is the digit count, O(1) extra space.

There are at least three ways to count a number's digits in Python, and they differ in speed,
in allocation behaviour, and in how they handle edge cases. Write whichever one you think of
first, get it green, then come back and find the other two — comparing them is the point of
this problem, not the counting.
"""


class Solution:
    def findNumbers(self, nums: list[int]) -> int:
        raise NotImplementedError("your turn")
