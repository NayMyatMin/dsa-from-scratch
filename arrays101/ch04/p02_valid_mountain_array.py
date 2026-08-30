"""941. Valid Mountain Array  (Easy)

https://leetcode.com/problems/valid-mountain-array/

Given an array of integers arr, return true if and only if it is a valid mountain array.

Recall that arr is a mountain array if and only if arr.length >= 3 and there exists some i with
0 < i < arr.length - 1 such that
    arr[0] < arr[1] < ... < arr[i - 1] < arr[i]
and
    arr[i] > arr[i + 1] > ... > arr[arr.length - 1].

Example 1:
    Input:  arr = [2,1]
    Output: false

Example 2:
    Input:  arr = [3,5,5]
    Output: false

Example 3:
    Input:  arr = [0,3,2,1]
    Output: true

Constraints:
    1 <= arr.length <= 10^4
    0 <= arr[i] <= 10^4

Target: O(n) time and O(1) extra space, in a single pass over arr.

The time half is forced by the scale, and this is the difference between this problem and 1346
next door. n reaches 10^4 here, and a solution that verifies each candidate summit from scratch
does on the order of n^2 comparisons. Measured on this repo's interpreter, CPython 3.14.4, at
n = 10^4, per pass:

    on a true mountain
        four linear solutions                          0.267 - 0.528 ms
        every candidate summit verified from scratch           315.5 ms
    on a strictly rising list, which never falls
        four linear solutions                          0.140 - 0.326 ms
        every candidate summit verified from scratch          1276.2 ms

Between 600x and 1,200x on the first shape and between 3,900x and 9,100x on the second, on inputs
the constraints allow. That is what a Time Limit Exceeded looks like from the inside.

The space half is the bar this problem is usually held to rather than something the constraints
force: 10^4 elements is small enough that a solution which slices arr into two halves and checks
each one is accepted, and it is accepted here. Nothing in this suite measures space. Chapter 5 is
where constant extra space becomes the subject.

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
      arr[:] and sorted(arr) hand back new lists and leave arr alone; arr.sort() and arr.reverse()
      rewrite arr where it stands, and those fail here.
    - True and False, not 1 and 0. The signature says bool, and bool is what the suite checks for.
      Python will let a truth value stand in for 1 almost anywhere; this is one of the places
      where the distinction is the point.
    - arr.length is at least 1. A list of one element and a list of two are both legal input, and
      the answer to both is always False, whatever is in them.

The definition above is doing more work than it looks. Two of its clauses are about the ends and
one is about ties, and wrong answers to this problem live in exactly those three places.

0 < i < arr.length - 1 puts the summit strictly inside the list, so a list that only climbs and a
list that only falls are both rejected however long and however orderly they are: [0,1,2,3] is
not a mountain and neither is [3,2,1,0]. arr.length >= 3 rejects [2,1] and [7] outright, and both
of those are legal input — the constraints allow a list of one.

Every comparison in the definition is strict. Equal neighbours are neither a climb nor a fall, so
a single repeated value anywhere is fatal, wherever it sits: [3,5,5] is one of the examples above
and it is false, and so are [1,1,2,1] and [1,2,3,3,1] and [1,2,3,2,2]. A plateau at the summit is
the one that gets missed most often, because from a distance the list still has the right shape.
"""


class Solution:
    def validMountainArray(self, arr: list[int]) -> bool:
        raise NotImplementedError("your turn")
