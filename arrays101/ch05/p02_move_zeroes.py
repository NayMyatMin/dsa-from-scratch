"""283. Move Zeroes  (Easy)

https://leetcode.com/problems/move-zeroes/

Given an integer array nums, move all 0's to the end of it while maintaining the relative order
of the non-zero elements.

Note that you must do this in-place without making a copy of the array.

Example 1:
    Input:  nums = [0,1,0,3,12]
    Output: nums becomes [1,3,12,0,0]

Example 2:
    Input:  nums = [0]
    Output: nums becomes [0]

Constraints:
    1 <= nums.length <= 10^4
    -2^31 <= nums[i] <= 2^31 - 1

Follow up: Could you minimize the total number of operations done?

Target: O(n) time — a fixed amount of work per element, whatever the zeros are doing.

The scale does not force that, and it is worth being clear about which of the two guards you are
under. Measured on this repo's interpreter, CPython 3.14.4, at the constraint ceiling n = 10^4,
best of three rounds over two hundred full-size lists spread across the eleven zero patterns the
suite uses:

    solutions doing a fixed amount of work per element    0.083 - 0.221 ms per call
    a sort with a key                                     0.208 - 0.293 ms per call
    lifting each zero out where it stands and putting
      one back on the end                                   2.4 - 45.4 ms per call

Forty-five milliseconds a call is slow, and it is not slow enough to be rejected on the submission
page. The suite holds you to linear anyway, for the same reason chapter 3's 27 does: the cost in
that last row comes from an operation that moves the whole tail of the list every time it is used,
and that is the mistake this chapter exists to catch rather than an honest reading of the
statement. Ratios and orderings only, since those reproduce; and the ordering above depends on
there being zeros to move. On a list with no zeros in it at all every shape measured lands in
the same band as the first row, which is why the suite times more than one pattern.

Extra space is not measured, and the statement's "without making a copy" is the one requirement
here that nothing can enforce. The caller reads nums when you return and has no way to see what
you allocated on the way, so a solution that assembles the answer in a list of its own and then
writes it into nums is accepted on the submission page and accepted here. Constant extra space is
the better answer to reach for, and it is the subject of this chapter; it is not what this problem
checks.

IN PLACE — read this part twice:
    - The list object handed to you is the answer. Mutate nums itself. The caller keeps a
      reference to this very list and reads it when you return, so rebinding the name nums to a
      fresh list puts the answer somewhere nobody looks.
    - The return value must be None. The signature says so and the suite checks it: a correct
      rewrite of nums followed by `return nums` fails here. This is chapter 2's contract, not the
      one 1299 next door uses.
    - len(nums) must not change. Same length going out as coming in: no append, no insert, no pop,
      no del, no slice assignment that changes the length.
    - There is exactly one right answer, and the order is half of it. The non-zero elements must
      come out in the order they went in, and every 0 must sit behind all of them. That is why
      example 1 is [1,3,12,0,0] and nothing else. This is the opposite of what 905 later in this
      chapter allows, and the difference between the two is the point of having both.
    - A zero is the int 0 and nothing else. It is the only int that is falsy, and there is no
      separate negative zero for a solution to miss.
    - nums[i] runs from -2147483648 to 2147483647. Those bounds cost nothing here: a Python int
      is not a fixed-width machine word, so nothing overflows and no value in that range needs
      handling of its own. Negative values are ordinary non-zero elements.
    - nums.length is at least 1. The empty list is not legal input; a single element is, and
      example 2 is one.

Two things have to be true when you return and only one of them is about zeros. Getting every 0
behind every non-zero is the easy half, and the cheapest-looking way to do it is also the way that
breaks the other half: pull each zero out and swap something from the far end into the hole it
leaves, and [0,1,0,3,12] comes out as [12,1,3,0,0] — zeros in the right place, 3 and 12 in the
wrong order, and a test suite that only checked where the zeros were would call it correct.
Preserving relative order is the whole difficulty of this problem. The follow-up above asks you to
do it in as few operations as possible; nothing here counts them, and it is a question worth
coming back to once the suite is green.
"""


class Solution:
    def moveZeroes(self, nums: list[int]) -> None:
        raise NotImplementedError("your turn")
