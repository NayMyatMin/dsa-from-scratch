# 27. Remove Element — Tier 2 (observation)

Read the contract as a list of what it does *not* pin down. The values that have to end up at the
front are fixed — every element not equal to `val`, duplicates and all. Everything else is yours:
their order inside the first `k` slots, every slot from index `k` onward, and the length of the
list, so long as it still has room for `k`.

**"Remove" describes the result, not the mechanism.** Nothing is obliged to leave the list. Some
things are obliged to arrive at the front of it.

That is worth real money, because taking an element out where it stands is the expensive move in
this chapter. `del nums[i]` closes the gap by sliding every element behind `i` one slot to its
left, so the price is set by how much list lies to the right of the cut:

```python
import timeit

setup = "b = [0] * 10_001"
front = min(timeit.repeat("del b[0]; b.append(0)", setup, number=20_000, repeat=9)) / 20_000
back = min(timeit.repeat("del b[9_999]; b.append(0)", setup, number=20_000, repeat=9)) / 20_000
print(round(front * 1e6, 2), "us to delete at the front")
print(round(back * 1e6, 3), "us to delete one slot from the back")
# -> 2.56 us to delete at the front
# -> 0.012 us to delete one slot from the back
```

Two orders of magnitude, and the ordering does not wobble: over six runs the ratio landed between
209x and 215x. Cutting in the middle costs half of cutting at the front, 1.29 us against 2.56 us,
and the front price doubles as the list doubles — 0.658 us at n = 2,500, 10.207 us at n = 40,000.

The second hazard has nothing to do with speed. A list that shrinks under a forward walk moves the
elements you have not read yet:

```python
readings = [1, 5, 5, 2, 3]
i = 0
while i < len(readings):
    if readings[i] == 5:
        del readings[i]
    i += 1
print(readings, len(readings))
# -> [1, 5, 2, 3] 4

prices = [1, 5, 5, 2, 3]
for x in prices:
    if x == 5:
        prices.remove(x)
print(prices, len(prices))
# -> [1, 5, 2, 3] 4
```

A 5 survives both. The deletion at index 1 pulls the second 5 down into index 1, and the index
moves on to 2 without looking back; the `for` loop fails the same way, because iterating advances a
position counter that knows nothing about the list changing length underneath it (chapter 1
section 6). Neither form is wrong merely occasionally: over every list of length 0 to 8 drawn from
`{0, 1, 2}`, against each `val` in `{0, 1, 2, 3}`, both are wrong on 13,701 of 39,364 cases — and
on exactly the same set, the ones where two occurrences of `val` sit next to each other. No input
with an adjacent pair came out right, and none without one came out wrong.

One deletion per occurrence is therefore both too slow and, walked naively, too fragile.

> **The first official hint, verbatim:** "The problem statement clearly asks us to modify the array
> in-place and it also says that the element beyond the new length of the array can be anything.
> Given an element, we need to remove all the occurrences of it from the array. We don't
> technically need to *remove* that element per se, right?"
>
> That is the second paragraph above, reached from the same direction, and it is a fair hint. It
> stops short of both hazards, which is where this problem's difficulty lives — and the docstring
> in `arrays101/ch03/p01_remove_element.py` names both, so you had already been told more.

---

Close this file and go back to the code. Only if a real attempt fails:
**[Tier 3 — approach](27-tier3.md)**

[Chapter 3 hints index](../ch03.md)
