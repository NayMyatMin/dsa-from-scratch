# 26. Remove Duplicates from Sorted Array — Tier 4 (full strategy)

## The rule

`k` does two jobs at once: it is how many distinct values you have kept so far, and it is the index
the next one belongs at. The first element is always kept and the constraints guarantee there is one,
so `k` starts at 1. Walk a read index `i` from 1 to `len(nums) - 1`. At each step compare `nums[i]`
against `nums[k - 1]`, the last value you kept. Equal means `nums[i]` is another copy of a value
already sitting in the front, so do nothing at all and step on. Different means `nums[i]` is the first
element of a new run, so write it into `nums[k]` and add one to `k`. When the walk ends, `nums[:k]`
holds the distinct values in the order they occurred — which, for a non-decreasing input, is sorted
order — and `k` is what you return. Nothing is deleted, and the length never changes.

## Why writing into the list you are reading is safe

`k` starts equal to `i` and rises by at most one per step while `i` rises by exactly one, so
**`k <= i` holds for the entire run**: the slot you write is at or behind the slot you have just read,
never ahead of it. Checked at every step of every non-decreasing list of length 1 to 10 over a
four-value alphabet — 7,008 steps — the write index was never once ahead of the read index.

That also settles the choice Tier 3 left open. Comparing against `nums[i - 1]` works just as well as
comparing against `nums[k - 1]`, and it is not luck: slot `i - 1` can only ever be written on step
`i - 1` itself, and the value written there on that step is the one already in it. Over the same
7,008 predecessor reads the slot never held a value different from the one it arrived with, and both
forms agreed with the reference answer on all 494 non-decreasing lists of length 1 to 8.

## Complexity

**O(n) time, O(1) extra space.** Exactly `n - 1` comparisons on every input whatever its shape —
counted at n = 30,000, 29,999 on a list of one repeated value and 29,999 on 201 equal runs — and
exactly `k - 1` writes: none at all when the list is one value repeated, 200 when `k` is at its
ceiling. The constraints cap the distinct values at 201, so the writes are capped at 200 however long
the list is, and the loop's cost is essentially its comparisons. `tracemalloc` over the whole routine
at n = 30,000, seven traced runs each: 0 bytes peak on the single-value shape, and 0 on six of seven
runs with 32 on the other for the 201-value shape.

Guarding the write with `if k != i`, to skip a slot writing to itself, is not worth buying. Measured
over three rounds it came out 0.88x–0.93x on a 201-element list of entirely distinct values, where
every write is a self-write, and 1.00x–1.02x at n = 30,000 on both timed shapes, where at most 200
writes happen at all.

## The stopwatch does not agree with the complexity

All four rows below are accepted — the suite grades the answer, not the route, and it does not measure
extra space at all. Best of nine runs per cell at n = 30,000, three rounds, the ordering identical in
all three; peaks from `tracemalloc` over seven traced runs. The two slice-assigning rows write over
the front of `nums` only. The `sorted(set(nums))` row assigns over the whole of it, which is where
almost all of its memory goes — that one assignment costs 241,856 bytes on its own, as Tier 3
measures.

| solution | one value repeated | 201 values in equal runs | peak extra bytes |
|---|---|---|---|
| `sorted(set(nums))` | 0.158–0.168 ms | 0.238–0.251 ms | 240,064 / 243,488 |
| `dict.fromkeys` + front slice | 0.206 ms | 0.296–0.303 ms | 312 / 13,928 |
| the write cursor above | 0.372–0.374 ms | 0.418–0.424 ms | 0 / 0–32 |
| comprehension + front slice | 0.638–0.651 ms | 0.671–0.674 ms | 104 / 3,464–3,496 |

The routine with the best bound is third of four on the clock, 1.7x to 2.4x behind the one that
discards the ordering and sorts it back. The cursor's comparisons and writes cost a bytecode apiece,
while `set`, `sorted` and `dict.fromkeys` do the equivalent work at C speed — and the constraints cap
`k` at 201, so the sort is over at most 201 values however long the list is. Lift that cap and the
order reverses: on 300,000 sorted values with 299,964 of them distinct, the cursor takes 8.97 ms and
`sorted(set(nums))` takes 35.81 ms, while on 300,000 values with `k = 200` the same pair measures
3.78 ms and 1.59 ms. **Choose the cursor because it is linear on every input shape and allocates
nothing, not because it wins a stopwatch.** The tension between the bound and the clock is not
peculiar to this problem, and the bound is the half that survives a change of input.

## Before you call it done

- Return the count you kept, not `len(nums)`. The two agree only if you shortened the list, and this
  routine does not shorten it at all.
- Starting at `k = 1` is correct only because `1 <= nums.length` is a constraint. Handed `[]` it
  returns 1 without reading anything — a silent wrong answer rather than an `IndexError`. Out of
  constraints here, so not a bug; worth remembering the next time this shape comes without that
  guarantee.
- The first `k` slots are compared one at a time, so the right values in a different arrangement is
  a wrong answer on this problem.

## The published hints

All three are spent by Tiers 2 and 3 — one on the sortedness, two on the two-position shape. None of
them mentions the invariant that makes the writing safe, none states a complexity, and the one that
comes closest to the algorithm asserts that the list gets shorter, which this solution never does.

---

[Chapter 3 hints index](../ch03.md)
