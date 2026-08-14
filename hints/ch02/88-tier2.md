# 88. Merge Sorted Array — Tier 2 (observation)

Both inputs arrive sorted, and that buys exactly one thing: **you never have to weigh more than
two values against each other.** The smallest value still unplaced anywhere is one of two
candidates — the front of what remains of `nums1`, or the front of what remains of `nums2`.
Nothing further along either array can undercut them, because each array is already in order. So
the interleaving is decided one local comparison at a time. No lookahead, no sorting.

That would be routine if you were building a fresh list. You are not. `nums1` is the destination
*and* one of the two sources, and they collide:

```python
nums1 = [1, 2, 3, 0, 0, 0]   # m = 3; the three 0s are reserved room, not data
nums2 = [2, 5, 6]            # n = 3
# The finished array is [1, 2, 2, 3, 5, 6], so slot 2 has to end up holding nums2's 2.
nums1[2] = 2
print(nums1)                 # -> [1, 2, 2, 0, 0, 0]
```

The 3 is gone, and you had not placed it yet. Anything that fills `nums1` starting from slot 0
hits this the first time a value in `nums2` is smaller than a value still sitting in the first `m`
slots. That is not a corner case. A front-to-back fill that is in every other respect a correct
merge comes out wrong on 9,843 of 10,000 random inputs here — every shape from `m, n = 1` through
`20`, values drawn from `0..49` — and on 1,998 of 2,000 when both sides are the same length (5,
10, 50 and 100 a side, 500 cases each).

So this problem asks two questions, not one: which value comes next, and **which slots are safe to
write into right now**. The second one is what lifts it above a warm-up.

To see which shapes your current attempt actually fails on:

```bash
uv run pytest tests/ch02 -k merge -v
```

> **If you go looking for published hints on this one, here is what you will find.** There are two
> of them, and between them they get no further than the first paragraph above: stop thinking about
> two whole arrays, take one element from each, decide locally which goes next, and keep going.
> That is the merge, and it is the easy half.
>
> Neither one says a word about the destination also being a source, which is the whole of the
> difficulty here. Worse, *keep going* taken at face value means keep advancing from the front,
> which walks you straight into the overwrite you just watched happen.

---

Close this file and go back to the code. Only if a real attempt fails:
**[Tier 3 — approach](88-tier3.md)**

[Chapter 2 hints index](../ch02.md)
