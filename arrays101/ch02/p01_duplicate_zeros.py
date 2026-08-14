"""1089. Duplicate Zeros  (Easy)

https://leetcode.com/problems/duplicate-zeros/

Given a fixed-length integer array arr, duplicate each occurrence of zero, shifting the remaining
elements to the right.

Note that elements beyond the length of the original array are not written. Do the above
modifications to the input array in place and do not return anything.

Example 1:
    Input:  arr = [1,0,2,3,0,4,5,0]
    Output: arr becomes [1,0,0,2,3,0,0,4]

Example 2:
    Input:  arr = [1,2,3]
    Output: arr becomes [1,2,3]

Constraints:
    1 <= arr.length <= 10^4
    0 <= arr[i] <= 9

Target: O(n) time, O(1) extra space.

IN PLACE — read this part twice:
    - The list object handed to you is the answer. Mutate arr itself.
    - len(arr) must not change. Same length going out as coming in: no append, no insert, no
      pop, no del, and no rebinding the name arr to a fresh list.
    - Elements pushed past the last index are discarded, not kept. Example 1 loses the trailing
      5 and 0 entirely.
    - The return value is ignored. The method returns None; the tests inspect arr afterwards.

Duplicating one zero means every element to its right slides one slot along and whatever falls
off the end is gone. The hazard is the sliding: a slot you write into may still hold a value you
have not read yet, and once you have overwritten it the rest of the array is wrong. Before you
write a single element, be sure you know how you are keeping that from happening.
"""


class Solution:
    def duplicateZeros(self, arr: list[int]) -> None:
        raise NotImplementedError("your turn")
