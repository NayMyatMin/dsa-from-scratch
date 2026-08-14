# 88. Merge Sorted Array — Tier 4 (full strategy)

Keep three indices. `i` marks the last unplaced element of `nums1`'s data and starts at `m - 1`;
`j` marks the last unplaced element of `nums2` and starts at `n - 1`; `w` is the slot being filled
and starts at `m + n - 1`. Each step compares `nums1[i]` against `nums2[j]`, writes the larger into
`nums1[w]`, steps that source index back one, and steps `w` back one. Drive the loop off `j`: it
runs while `j >= 0`.

## Why a write can never destroy a value you still need

`w` begins at `i + j + 1`, and every step decrements `w` and exactly one of `i` or `j`, so
**`w == i + j + 1` holds for the entire run**. While there is anything left in `nums2`, `j >= 0`,
so `w >= i + 1`: the slot you are about to overwrite is always at least one position to the right
of the last unread element of `nums1`. Checked by asserting the invariant at every step of every
merge over all 960 shapes with `0 <= m, n <= 30` and `m + n >= 1`, three random fillings each —
2,880 merges, 80,797 steps, zero violations, and the closest `w` ever came to `i` was exactly one
slot.

That invariant is also why the loop ends on `j`. When `j` drops below zero, `w == i`, and
`nums1[0..i]` is sorted and already sitting in its final position — the remaining work is exactly
zero. The other exhaustion case is not symmetric: when `i` drops below zero first, `nums2` still
holds values that are nowhere in `nums1`, and they must be moved. Guarding the comparison with
`i >= 0` folds that case into the same loop, because once `i < 0` the guard short-circuits and
every remaining step takes from `nums2`.

Ties can break either way. With `int` values, equal elements are indistinguishable once written,
so strict and non-strict comparison are both correct — confirmed over 3,360 duplicate-heavy cases
(every shape from `m, n = 0` through `12`, values drawn from `0..3` so ties are everywhere, 20
fillings each). Both forms matched the oracle on all of them.

## Complexity

One write per slot filled, at most one comparison per write. **O(m + n) time, O(1) extra space**,
which is the follow-up answered. The comparison ceiling is `m + n - 1`, not `m + n`: reaching
`m + n` would need every `nums2` element taken while `i >= 0` *and* every `nums1` element moved,
and those cannot both happen. Counted at `m = n = 100`, the top of this problem's constraints:

| input shape | comparisons |
|---|---|
| random values on both sides, 10,000 trials | 188–199, mean 198.0 |
| perfectly interleaved | 199 |
| every `nums2` value above every `nums1` value | 100 |
| every `nums2` value below every `nums1` value | 100 |
| `m = 0`, or `n = 0` | 0 |

## The approaches not taken

**Splice and sort.** Assign `nums2` over the tail slice of `nums1`, then call `nums1.sort()`. Two
statements, in place, length preserved, correct — over 3,825 random cases (every shape from
`m, n = 0` through `15`, 15 fillings each) checked against a brute-force oracle it agrees with the
backward merge on every one. It is also, measured, the fastest thing here.

Best of 40, 20 and 11 rounds on CPython 3.14.4 — of 20,000, 2,000 and 50 merges respectively —
with the cost of copying the input list (0.24 us, 1.9 us and 141 us at the three sizes) measured
separately and subtracted out:

| m = n | splice + sort | backward merge | copy + forward merge | `heapq.merge` |
|---|---|---|---|---|
| 100 | 0.77 us | 5.84 us | 5.85 us | 14.39 us |
| 1,000 | 7.00 us | 71.52 us | 71.06 us | 138.19 us |
| 50,000 | 815 us | 4,158 us | 4,132 us | 7,092 us |

Absolute microseconds move between runs; a second run of the whole benchmark shifted every figure
by a few percent and reordered nothing. Splice-and-sort came out 7.5x, 10.2x and 5.1x faster than
the hand-written merge at the three sizes — the gap widest in the middle.

Two things produce that. First, `list.sort` is not paying `n log n` here — it detects runs of
already-ordered data and merges them, so a list that is exactly two sorted runs costs it about
`2(m + n)` comparisons. Counted directly with an `int` subclass that increments a counter in its
comparison method, at `m = n = 1000`, over five trials: 4,000–4,002 comparisons for the spliced
list, against 19,309–19,342 for the same 2,000 values shuffled. Same length, same sort, 4.8x the
work when the runs are absent. Second, those comparisons run at C speed inside `list.sort`, while
yours run one bytecode at a time; a single `nums1[w] = nums1[i]` in a Python `while` loop costs
more than a whole compare-and-move down there.

That is the honest tension in this problem: **the algorithmically inferior solution wins on the
clock at every size measured.** What the backward merge buys is the guarantee — linear regardless
of input shape, no reliance on the sort recognising the runs, constant extra space.

**Copy the first `m` elements out, then merge forward.** With `nums1[:m]` safe in its own list,
nothing is at risk and you can fill from slot 0 in the natural direction. Correct, same O(m + n),
measured within 2% of the backward merge at every size in the table — sometimes just ahead of it,
sometimes just behind — and O(m) extra space.

Be clear about the standing of that last one, because it is easy to over-read this section. The
follow-up asks for O(m + n) **time**, and this solution delivers it. It is accepted by the judge
and it passes this repo's tests, which police the contract and the running time and deliberately
say nothing about how much scratch space you use. The backward merge is the better answer and it
is the one worth carrying forward, but preferring it is a matter of craft here, not of meeting
the stated requirement. Constant extra space becomes the actual subject in chapter 5.

**`heapq.merge`.** Lazily merges any number of sorted iterables. Right idea, wrong scale: 2.5x,
1.9x and 1.7x slower than the hand loop at the three sizes above, and it yields an iterator you
still have to land somewhere. Save it for merging k sorted streams, where it genuinely is the
right tool.

## Before you call it done

Check `m = 0`, `n = 0`, values duplicated across both arrays, and that `nums2` comes back
untouched. Then re-read chapter 1 section 9: rebinding the name `nums1` inside the method is
invisible to the caller, and the caller's list is the only thing the tests look at.

---

[Chapter 2 hints index](../ch02.md)
