# 27. Remove Element — Tier 4 (full strategy)

## Two positions, one list

Keep one extra integer, `w`: the index where the next survivor belongs, starting at 0. Walk `nums`
from the front. If the element equals `val`, do nothing whatever — no write, no shift, `w` does not
move; it simply is not carried forward, and that is the whole of "removing" it. Otherwise write it
into `nums[w]` and step `w` on by one. When the walk ends, `w` is the number of survivors and they
are sitting in `nums[0:w]` in their original relative order. Return `w`.

There is no separate counting pass: `w` counts as a side effect of placing, because it advances
exactly once per survivor. Iterate the elements directly rather than by index — the element in hand
is what gets written, and `w` is the only position you need.

## Why the write never lands on something unread

At the moment you are reading index `i`, **`w` equals `i` minus the number of occurrences of `val`
already passed.** That quantity starts at 0, only ever increases, and increases only when an
occurrence goes by, so `w <= i` always. Checked over every binary list of length 0 through 11 —
4,095 lists, 40,962 individual steps — `w > i` never happened, and `i - w` was the count of
already-passed occurrences at every step.

That inequality is the correctness argument, and it is the whole of it: the write lands at or
behind the element just read, and everything at or behind the read position has already been read.
When `w == i`, which is every step until the first occurrence of `val`, the write is a slot copying
to itself — harmless, and not worth a branch to avoid. Neither edge case needs code either: on the
empty list the walk takes zero steps and `w` is still 0, and with a `val` above 50 — legal, and so
absent from `nums` by construction — every element is a survivor and `w` finishes at `len(nums)`.

## Complexity, and what it actually costs

One comparison per element, at most one write per element, one integer of state: **O(n) time, O(1)
extra space.** `tracemalloc` over the whole routine at n = 10,000 with half the elements equal to
`val`, five traced runs and identical every time: **0 bytes** peak.

The number of writes is not `n`. It is the number of survivors, which makes this shape cheapest
exactly where Tier 3's third family is dearest. Counted at n = 10,000:

| occurrences of `val` | survivors | writes, one pass | writes, swap from the far end |
|---|---|---|---|
| 0 | 10,000 | 10,000 (all slot-to-itself) | 0 |
| 989 | 9,011 | 9,011 (11 slot-to-itself) | 989 |
| 5,011 | 4,989 | 4,989 | 5,011 |
| 9,015 | 985 | 985 | 9,015 |
| 10,000 | 0 | 0 | 10,000 |

They cross at half, and neither ever does more than one write per element, which is why choosing
between them is not a complexity question. Growth from n = 4,000 to n = 32,000, best of nine with
the sides interleaved, on the three shapes the suite uses: **7.91x** where every element is
removed, **8.41x** where half are, **8.05x** where none are.

## The approaches not taken

**Filter into a new list, then slice-assign it into the front.** At the constraint ceiling this is
not slower — it is sometimes quicker. At n = 100, best of nine rounds of 20,000 calls, cost of
copying the input subtracted:

| density of `val` | one pass | `nums[:k] = keep` | `nums[:] = keep` |
|---|---|---|---|
| 0.00 | 1.08 us | 1.13 us | 1.18 us |
| 0.25 | 1.16 us | 1.00 us | 1.01 us |
| 0.50 | 0.89 us | 0.79 us | 0.78 us |
| 0.75 | 0.73 us | 0.69 us | 0.80 us |
| 1.00 | 0.50 us | 0.54 us | 0.52 us |

Absolute microseconds drift between runs and each row is genuinely close. What separates them is
memory. At n = 10,000 with 4,901 survivors the comprehension alone peaked at 41,824 bytes, and the
slice assignment costs a temporary of its own on top, sized by the number of slots being replaced
rather than by `k`: `nums[:k] = keep` measured exactly 39,208 bytes, 8 x 4,901, confirmed to the
byte at four sizes, while `nums[:] = keep` replaces all 10,000 slots and measured 124,128. Prefer
the single pass because 0 bytes is the better habit, not because the clock demands it.

**Swap in from the far end.** Fewer writes when `val` is common, O(1) space like the single pass,
growth of 7.96x to 8.04x — and slower at every density measured at n = 100, between 1.19 and
1.87 us against the single pass's 0.50 to 1.16, because a `while` loop indexing both ends costs
more per element than a `for` loop that hands you elements. It also scrambles the survivors' order,
which this problem permits; that is a property of the technique, not a free lunch.

**One list-level removal per occurrence.** `nums.remove(val)` until it raises, `.index()` then
`del`, `pop(0)` off the front. Each slides the tail at C speed, which is fast enough to feel
harmless and quadratic anyway:

```python
import random
import timeit

rng = random.Random(27)
data = [5 if rng.random() < 0.5 else rng.randint(0, 4) for _ in range(10_000)]


def strip_by_removal(values):
    while True:
        try:
            values.remove(5)
        except ValueError:
            return values


loop = min(timeit.repeat("strip_by_removal(list(data))", globals=globals(),
                         number=5, repeat=5)) / 5
once = min(timeit.repeat("sum(1 for x in list(data) if x != 5)", globals=globals(),
                         number=200, repeat=5)) / 200
print(round(loop * 1e3, 1), "ms to call remove(5) until it raises")
print(round(once * 1e3, 3), "ms for one pass that touches every element")
# -> 66.3 ms to call remove(5) until it raises
# -> 0.151 ms for one pass that touches every element
```

Across seven runs of that block the ratio stayed between 426x and 476x. Doubling n with half the
elements equal to `val` multiplied the removal loop's time by 3.92, 3.97, 4.26 and 4.22 from
n = 2,500 to 40,000 — the 4x of a quadratic — while the single pass multiplied by 2.06, 2.07, 2.03
and 2.00. In the growth guard's terms, eight times the input cost the removal loop 92.04x and
68.50x on the two shapes where `val` is present.

**One `del` per occurrence, scanning backwards.** Worth naming because it is what the timing guard
exists to catch. Deleting the *last* element is free — nothing behind it to slide — so on a list
where every element goes it measured 8.06x, inside the band the correct solutions occupy, and
56.10x as soon as survivors sit behind what is being removed. A list of a single repeated value is
the easiest input in the world to be accidentally fast on.

The honest footnote: at n = 100 the removal loop measured 0.64 us where `val` never occurs — faster
than every column of the table above — and 9.59 us where half the elements are `val`. A hundred
elements is far too few for a wall clock to referee this, which is why
`test_does_not_grow_quadratically` invents its own sizes.

## Before you call it done

Run `uv run pytest tests/ch03/test_p01_remove_element.py`, then check by hand: the empty list, a
`val` above 50, every element equal to `val`, and one survivor at each of the front, middle and
back. Confirm you return a count rather than `len(nums)` — the two agree only if you also shortened
the list, and nothing asks you to. Resist tidying the tail: those slots are not read, and zeroing
them is work the contract explicitly does not want.

---

[Chapter 3 hints index](../ch03.md)
