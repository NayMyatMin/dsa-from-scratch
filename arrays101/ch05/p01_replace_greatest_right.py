"""1299. Replace Elements with Greatest Element on Right Side  (Easy)

https://leetcode.com/problems/replace-elements-with-greatest-element-on-right-side/

Given an array arr, replace every element in that array with the greatest element among the
elements to its right, and replace the last element with -1. After doing so, return the array.

Example 1:
    Input:  arr = [17,18,5,4,6,1]
    Output: [18,6,6,6,1,-1]

Example 2:
    Input:  arr = [400]
    Output: [-1]

Constraints:
    1 <= arr.length <= 10^4
    1 <= arr[i] <= 10^5

Target: O(n) time, in one pass, with the rewrite landing in arr itself.

The time half is forced by the scale, and it is forced hard. n reaches 10^4, and a solution that
goes looking for the greatest element to the right of each position separately does that search n
times. Measured on this repo's interpreter, CPython 3.14.4, at n = 10^4, best of three rounds
over twenty full-size lists:

    solutions doing a fixed amount of work per element    0.146 - 0.257 ms per call
    max() over a slice of the elements to the right,
      taken once per position                                  425 - 441 ms per call
    max() over a generator, once per position                        1,159 ms per call

The slowest of the linear group is more than 1,600x quicker than the quickest of the others, and
the widest gap measured is around 8,000x. Those are ratios rather than absolute times, because
ratios are what reproduce from one run to the next; the ordering held on every shape measured, on
a strictly descending list, a strictly ascending one, a random one and a list of one repeated
value alike. A quarter of a second per call is what a Time Limit Exceeded looks like from the
inside.

The space half is not measured. Nothing in the suite counts allocations, and a solution that
works out the whole answer somewhere else and then writes it into arr is accepted. What *is*
enforced is where the answer ends up, which is the next paragraph and is a different thing.

IN PLACE, AND RETURNED — read this part twice:
    - The list object handed to you is where the answer goes. Rewrite arr itself.
    - AND hand it back. The signature says list[int], not None: this is not chapter 2's contract,
      where the answer lived in the list and the return value was ignored. Here both halves are
      read, and returning None fails even when arr is perfect.
    - What comes back must be arr, the same object. The suite checks identity, not equality, so
      building a fresh list and returning it fails however right its contents are. Writing that
      fresh list back over arr and returning arr passes: arr[:] = whatever rewrites the list where
      it stands rather than making a new one.
    - len(arr) must not change. n elements in, n elements out.
    - The last element becomes -1, always, whatever was there. -1 is outside the range the
      constraints allow for input values, so it is a value arr could never have arrived holding.
    - "Greatest element among the elements to its right" means the values arr held when the call
      started, not the ones you have put there since. arr[i] is decided by the original arr[i+1:]
      and never by arr[i] itself.
    - arr.length may be 1. Example 2 is that case: one element, nothing to its right, answer
      [-1].

Every position is asked the same question and one position cannot answer it. Index n - 1 has
nothing to its right, so rather than leave it alone or invent a maximum for an empty collection
the statement fixes its answer at -1 outright, and a solution that gets the other n - 1 positions
perfect and forgets that one is wrong on every input there is. The other place wrong answers come
from is the word right. Nothing at position i counts towards position i, so [5,4,3] becomes
[4,3,-1] and not [5,4,-1]. A value that appears more than once is not exempt from that: the copies
still sit to the right of one another, so [7,7,7] becomes [7,7,-1] and the 7 only runs out at the
position where none are left.
"""


class Solution:
    def replaceElements(self, arr: list[int]) -> list[int]:
        raise NotImplementedError("your turn")
