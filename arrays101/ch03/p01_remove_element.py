"""27. Remove Element  (Easy)

https://leetcode.com/problems/remove-element/

Given an integer array nums and an integer val, remove all occurrences of val in nums in-place.
The order of the elements may be changed. Then return the number of elements in nums which are
not equal to val.

Consider the number of elements in nums which are not equal to val to be k. To get accepted:
change the array nums such that the first k elements contain the elements which are not equal to
val; the remaining elements are not important, as is the size of nums; and return k.

Example 1:
    Input:  nums = [3,2,2,3], val = 3
    Output: 2, nums = [2,2,_,_]

Example 2:
    Input:  nums = [0,1,2,2,3,0,4,2], val = 2
    Output: 5, nums = [0,1,4,0,3,_,_,_]
    Explanation: the five elements can be in any order.

Constraints:
    0 <= nums.length <= 100
    0 <= nums[i] <= 50
    0 <= val <= 100

Target: O(n) time — a fixed amount of work per element, whatever val is and however often it
occurs. The problem itself states no complexity requirement and n stops at 100, so a slow answer
is accepted there; the suite holds you to linear anyway, because a pass per removed element is
the wrong shape and 100 elements is far too few for a clock to tell you so.

Constant extra space is the better answer to reach for, and chapter 5 makes it the subject. It is
not what this problem requires and nothing here measures it.

IN PLACE — read this part twice:
    - k is the count of elements not equal to val, and k is what you return. An int, not a list.
    - The first k slots of nums must hold exactly those elements, IN ANY ORDER. The judge sorts
      the first k slots before comparing them, so for example 2 both [0,1,4,0,3] and [0,0,1,3,4]
      are accepted, and so is every other arrangement of those five values.
    - Everything from index k onwards is irrelevant. Not "should be zeroed", not "should be left
      as it was": irrelevant. Any values at all, and nothing reads them.
    - len(nums) is irrelevant too, so long as it is at least k. The problem says so outright: the
      size of nums is not important. It may shrink, and it may stay exactly as long as it was.
    - nums is modified in place. The caller keeps a reference to the list it handed you and reads
      the front of it when you return, so rebinding the name nums to a fresh list puts the answer
      somewhere nobody looks.
    - Both halves are graded together. The right k with nums untouched fails, and the right first
      k slots with the wrong k fails.
    - nums.length may be 0. The empty list is legal input here, and the answer to it is 0.

Removing every occurrence of a value sounds like it has to make the list shorter, and here it does
not: what gets read back is the front of the list and the number you return, and those two have to
agree with each other. The trap is that lifting an element out of a list where it stands moves
every element that follows it, so one removal per occurrence is one pass per occurrence — and an
index walked forward through a list that is shrinking underneath it steps straight over whatever
slid into the gap.
"""


class Solution:
    def removeElement(self, nums: list[int], val: int) -> int:
        raise NotImplementedError("your turn")
