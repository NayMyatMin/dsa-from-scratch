"""1346. Check If N and Its Double Exist  (Easy)

https://leetcode.com/problems/check-if-n-and-its-double-exist/

Given an array arr of integers, check if there exist two indices i and j such that i != j,
0 <= i, j < arr.length, and arr[i] == 2 * arr[j].

Example 1:
    Input:  arr = [10,2,5,3]
    Output: true
    Explanation: for i = 0 and j = 2, 10 == 2 * 5.

Example 2:
    Input:  arr = [3,1,7,11]
    Output: false

Constraints:
    2 <= arr.length <= 500
    -10^3 <= arr[i] <= 10^3

Target: O(n) time is available here, and it is worth finding. It is not required, and the test
file does not require it — there is no timing guard in it at all. n stops at 500, so a nested
loop over every pair of positions is about 250,000 comparisons and a legitimate accepted answer
to this problem, on the submission page and here. Measured on this repo's interpreter, CPython
3.14.4, over the 60 calls at the ceiling n = 500 that the test file makes, a third of them
holding no pair at all so the search has to run to the end:

    a nested loop over every ordered pair        the slowest measured, a few ms per call
    a nested loop over every unordered pair      three quarters to nine tenths of that
    the quickest single-pass shape measured      around two hundred times quicker, and more

Ratios rather than absolute times, because those are what reproduce from one run to the next.
Both loops are instant at this size and nothing in the test file is watching a clock. The last
row is the reason to go looking for it — a gap worth having, not a threat from the grader.

READ-ONLY — read this part twice:
    - The answer is the value you return, and nothing else. True or False.
    - arr must come back exactly as it was handed over: the same elements, in the same order, the
      same length. The suite snapshots arr before the call and compares it afterwards.
    - This is chapter 1's contract, and it is deliberately not the one chapters 2 and 3 used.
      There the answer lived in the list: you wrote into nums and the caller read the front of it
      after you returned. Here the list is input only. Nobody reads it again, so nothing you write
      into it can be an answer — it can only be damage.
    - Read-only is a rule about arr, not about you. Nothing stops you building your own structures
      alongside it, and nothing stops you copying arr and doing whatever you like to the copy.
      sorted(arr) hands back a new list and leaves arr alone; arr.sort() rewrites arr where it
      stands, and that fails here.
    - True and False, not 1 and 0. The signature says bool, and bool is what the suite checks for.
      Python will let a truth value stand in for 1 almost anywhere; this is one of the places
      where the distinction is the point.
    - arr.length is at least 2. A list of one element is not legal input, and neither is an empty
      one.

You are being asked a yes-or-no question about a pair of positions, and the interesting word in
it is indices. i != j requires the two positions to be different. It says nothing about the two
values being different, and for almost every value that costs nothing, because x == 2 * x has
exactly one solution. Zero is a legal element here. A lone 0 is its own double, so a check that
lets i and j land on the same position answers True to [0, 3] and to [1, 0, 5], where the answer
is False, while [0, 0] and [3, 0, 0] are genuinely True. One value in the whole legal range
behaves this way, which is why a test set that never puts a single zero on its own gives no sign
that anything is wrong. Negatives are legal too, so the double of an element is not necessarily
larger than it.
"""


class Solution:
    def checkIfExist(self, arr: list[int]) -> bool:
        raise NotImplementedError("your turn")
