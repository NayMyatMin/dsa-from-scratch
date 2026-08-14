# 26. Remove Duplicates from Sorted Array — Tier 2 (observation)

The list arrives sorted, and that buys one thing, but it is a large thing: **equal values are
neighbours.** A value cannot appear, be interrupted by something different, and appear again — that
would put a larger value before a smaller one, and the input is non-decreasing. So the question
"have I seen this value already?", which in general is a question about every element you have
walked past, is here a question about one slot. Over every non-decreasing list of length 1 to 8
drawn from four values — 494 lists, 3,168 elements — 1,848 elements had appeared earlier in their
own list, and every one of the 1,848 was equal to the element immediately before it.

The second observation is in the contract rather than the input. Nothing past index `k - 1` is ever
read, and `len(nums)` is free above `k`: `tests/ch03/test_p02_remove_duplicates.py` slices `nums[:k]`
and never looks further, and accepts a list shortened to exactly `k` as readily as one left as long
as it arrived. **So nothing has to come out of the list at all.** "Remove" describes the state of the
front of the list when you return; it does not name an operation you are obliged to perform.

That distinction is worth money, because lifting an element out of a list where it stands moves every
element after it (chapter 1, section 8). The by-hand procedure in Tier 1 slides 23 values to delete
five from a list of ten, and at the top of the constraints that is no rounding error: one deletion
per duplicate over 30,000 identical values moves 449,955,001 elements, costing 115.6 ms a pass
against 0.374 ms for an accepted solution that deletes nothing. The growth matters more than the
figure — doubling the length multiplied the deleting version by 3.90, 3.96 and 3.97 from n = 5,000
to 40,000, which is quadratic, while a single pass multiplied by 2.00, 2.01 and 1.98.

It is also easy to get wrong in a way that has nothing to do with speed. A list shrinking underneath
a forward-walking index steps over whatever slid into the gap:

```python
readings = [11, 11, 11, 14, 18, 18]
for i, r in enumerate(readings):
    if i and r == readings[i - 1]:
        del readings[i]
print(readings)
# -> [11, 11, 14, 18]
```

Two 11s survive, because deleting the second one moved the third into the slot the loop had just
finished with. Drive the same test with `for i in range(len(readings))`, reading `readings[i]`
directly, and it reaches that same wrong list and then raises `IndexError: list index out of range`.

> **The official hint, verbatim:** "In this problem, the key point to focus on is the input array
> being sorted. As far as duplicate elements are concerned, what is their positioning in the array
> when the given array is sorted? If we know the position of one of the elements, do we also know the
> positioning of all the duplicate elements?"
>
> That is this tier's first paragraph, asked instead of stated, and it is a fair hint. It says nothing
> about the second — that the contract never asks you to take anything out — which is the half that
> decides what your loop is allowed to do.

---

Close this file and go back to the code. Only if a real attempt fails:
**[Tier 3 — approach](26-tier3.md)**

[Chapter 3 hints index](../ch03.md)
