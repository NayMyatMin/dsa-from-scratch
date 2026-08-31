"""905. Sort Array By Parity  (Easy)

https://leetcode.com/problems/sort-array-by-parity/

Given an integer array nums, move all the even integers at the beginning of the array followed by
all the odd integers.

Return any array that satisfies this condition.

Example 1:
    Input:  nums = [3,1,2,4]
    Output: [2,4,3,1]
    Explanation: [4,2,3,1], [2,4,1,3] and [4,2,1,3] would also be accepted.

Example 2:
    Input:  nums = [0]
    Output: [0]

Constraints:
    1 <= nums.length <= 5000
    0 <= nums[i] <= 5000

Target: O(n) time. That is the whole of it, and the rest of this paragraph is about what the
target deliberately does not include. Rearranging nums where it stands, without a second list
anywhere, is the better exercise and the reason this problem sits in this chapter — but it is not
what the problem asks for. "Return any array" means the array you return is the answer, and a
solution that never writes into nums at all and hands back something it built from scratch is a
correct answer to this problem, on the submission page and in this suite. Reach for the in-place
rearrangement because it is the harder and more interesting answer, not because anything is
checking.

Nor does the scale force the O(n). Measured on this repo's interpreter, CPython 3.14.4, at the
constraint ceiling n = 5000, best of three rounds over five hundred full-size lists spread across
the eleven parity patterns the suite uses:

    solutions doing a fixed amount of work per element    0.110 - 0.188 ms per call
    a sort with a key                                     0.164 - 0.166 ms per call
    carrying one parity group across the list an
      element at a time                                   0.881 - 3.112 ms per call

Three milliseconds a call is comfortably accepted on the submission page. The suite holds you to
linear anyway, for the same reason chapter 3's 27 does: the last row is slow because it moves
everything behind each element it touches, which is the mistake this chapter exists to catch.
Ratios and orderings only, since those are what reproduce; and this ordering depends on which
parity the input is made of, because the problem is symmetrical. Measured at n = 5000, one shape
at a time: on a list of nothing but even values, carrying the evens forwards costs 3.7 - 4.9 ms a
call while carrying the odds backwards costs 0.14 ms; on a list of nothing but odd values the two
swap places, at 0.09 ms and 2.0 ms. Either input on its own would call one of those mistakes
free, which is why the suite times more than one pattern.

WHAT COUNTS AS RIGHT — read this part twice:
    - The answer is the list you return. That is what gets graded, and nums afterwards is not.
    - Any arrangement with every even value in front of every odd one is accepted. The order
      within the evens is your business and so is the order within the odds. Example 1 has four
      accepted answers and lists all of them.
    - This is the opposite of 283 earlier in the chapter, where the relative order of what you
      moved was the entire difficulty. Here the statement drops that clause on purpose.
    - What you return has to be a rearrangement of nums: the same length and the same values,
      each appearing as many times as it did. Nothing added, nothing dropped, nothing altered.
    - A new list is accepted, and so is nums itself after you have rewritten it. The suite grades
      whatever comes back and does not care which of the two it is. Returning None fails: unlike
      283, this problem's answer is the return value.
    - Even means x % 2 == 0, and 0 is even. Example 2 is the single-element list [0], whose only
      accepted answer is [0].
    - Every value is at or above 0, so no negative ever reaches you and parity here is never
      ambiguous.
    - nums.length is at least 1. The empty list is not legal input.

The freedom is the whole of this problem and it is easy to read straight past. 1299 and 283 each
have exactly one right answer; this one has as many as the evens can be ordered times the ways
the odds can, and [3,1,2,4] admits four of them, each worth as much as any other. The trap is
inventing a requirement nobody stated: a solution that carefully keeps 2 ahead of 4 because that
is how they arrived, or that produces the evens in sorted order because sorted looks tidier, is
doing work the problem did not ask for and paying for it. Read the sentence "return any array
that satisfies this condition" and decide what you are allowed to stop caring about before you
write anything.
"""


class Solution:
    def sortArrayByParity(self, nums: list[int]) -> list[int]:
        raise NotImplementedError("your turn")
