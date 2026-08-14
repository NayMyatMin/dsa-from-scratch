# 88. Merge Sorted Array — Tier 3 (approach)

The reserved room is not scattered through `nums1`. It is `n` slots in one contiguous block at the
**end**. That is where there is nothing to lose.

So fill the answer from the last slot of `nums1` and work down toward slot 0. The local comparison
is the same one, taken from the other end: the two candidates are now the **largest** unplaced
value on each side — the back of `nums1`'s first `m` elements, and the back of `nums2`. Take the
bigger of the two, write it into the slot you are currently filling, and step that side's pointer
back by one.

Three indices, all travelling right to left: one into `nums1`'s data, one into `nums2`, one for
the slot being written.

Left for you:

- Convince yourself a write can never land on a value you still need. Do it on the *worst* case —
  the moment the destination slot gets as close as it ever gets to the last unread element of
  `nums1`. How close is that, and why can it get no closer?
- Decide what happens when a side runs out. There are two such cases and they are not symmetric:
  one needs a copy, the other needs nothing at all. Work out which is which before writing either,
  because getting it backwards produces code that passes the examples and fails the suite.
- `m = 0` and `n = 0` are both legal inputs. Neither should need a special case.

---

Close this file and go back to the code. Tier 4 is the full algorithm — it ends the problem.
Only if a real attempt fails: **[Tier 4 — full strategy](88-tier4.md)**

[Chapter 2 hints index](../ch02.md)
