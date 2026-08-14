"""26. Remove Duplicates from Sorted Array  (Easy)

https://leetcode.com/problems/remove-duplicates-from-sorted-array/

Given an integer array nums sorted in non-decreasing order, remove the duplicates in-place such
that each unique element appears only once. The relative order of the elements should be kept the
same.

Consider the number of unique elements in nums to be k. After removing duplicates, return k. The
first k elements of nums should contain the unique numbers in sorted order. The remaining elements
beyond index k - 1 can be ignored.

Example 1:
    Input:  nums = [1,1,2]
    Output: 2, nums = [1,2,_]

Example 2:
    Input:  nums = [0,0,1,1,1,2,2,3,3,4]
    Output: 5, nums = [0,1,2,3,4,_,_,_,_,_]

Constraints:
    1 <= nums.length <= 3 * 10^4
    -100 <= nums[i] <= 100
    nums is sorted in non-decreasing order.

Target: O(n) time — a fixed amount of work per element, however many duplicates there are. Unlike
problem 27, n reaches 3 * 10^4 here, which is enough that a pass per duplicate is measurable: a
single pass over an array of 3 * 10^4 identical values costs 0.69 ms on this repo's interpreter,
and one list-level deletion per duplicate costs 256 ms on the same input.

Constant extra space is the better answer to reach for, and chapter 5 makes it the subject. It is
not what this problem requires and nothing here measures it.

IN PLACE — read this part twice:
    - k is the number of distinct values in nums, and k is what you return. An int, not a list.
    - The first k slots of nums must hold those distinct values IN SORTED ORDER. This is the one
      place where 26 and 27 part company: the judge for 27 sorts the first k before comparing, so
      any arrangement passes there. Nothing sorts anything for you here. The judge walks the first
      k slots and compares them one at a time, so the order you leave them in is the answer.
    - Everything beyond index k - 1 is irrelevant. Not "should be zeroed", not "should be left as
      it was": irrelevant. Any values at all, and nothing reads them.
    - len(nums) is irrelevant too, so long as it is at least k. It may shrink, and it may stay
      exactly as long as it was.
    - nums is modified in place. The caller keeps a reference to the list it handed you and reads
      the front of it when you return, so rebinding the name nums to a fresh list puts the answer
      somewhere nobody looks.
    - Both halves are graded together. The right k with nums untouched fails, and the right first
      k slots with the wrong k fails.
    - nums.length is at least 1. Unlike 27, the empty list is not legal input here.

nums arrives sorted non-decreasing, and that ordering is the entire advantage you are handed —
it is the only thing separating this from the harder problem of removing duplicates from a list
in no particular order. A solution whose first move is to sort, or that puts the values somewhere
the ordering stops mattering, has thrown that advantage away and paid for a property it already
had. The trap is the same shape as in 27, and it bites harder because the input is three hundred
times longer: taking one element out of a list where it stands moves every element after it, so a
deletion per duplicate is a pass per duplicate, and an index walked forward through a list that is
shrinking underneath it steps over whatever slid into the gap.
"""


class Solution:
    def removeDuplicates(self, nums: list[int]) -> int:
        raise NotImplementedError("your turn")
