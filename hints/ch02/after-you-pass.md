# Chapter 2 — after you pass: where each of these goes next

Nothing here is needed to finish the chapter, and it assumes you have already solved both.
It's here so the lineage of each problem is on hand when you want more of the same shape.

**1089 Duplicate Zeros** — tagged *Array* and *Two Pointers*, and the second tag is the whole
family. The direct sequels are all on your own syllabus: *Remove Element* and *Remove Duplicates
from Sorted Array* (both Easy) in Chapter 3, then *Move Zeroes*, *Sort Array By Parity* and both of
those two again (all Easy) in Chapter 5. Every one of them is the same bargain — a length you may
not change, a write position and a read position, and a rule for when each advances. Off the
syllabus, *Sort Colors* (Medium) runs three regions at once instead of two, and *Rotate Array*
(Medium) is the purest form of the question this problem asked you: move every element by a fixed
offset inside a list you are not allowed to grow. If any of those feel like a fresh problem rather
than a variation, the thing to reread is section 5 of the notes, not the hint tiers.

**88 Merge Sorted Array** — tagged *Array*, *Two Pointers* and *Sorting*, and the follow-up
("O(m + n)") is the whole exercise. This is the merge step that `list.sort` performs internally, so
the shape recurs everywhere: *Merge Two Sorted Lists* (Easy) does it over linked nodes, where there
is no destination to overwrite and no back end to start from; *Intersection of Two Arrays II*
(Easy) walks two sorted inputs the same way but emits only what both hold; *Merge k Sorted Lists*
(Hard) generalises to any number of inputs and is what `heapq.merge` does for you in one call; and
*Median of Two Sorted Arrays* (Hard) is the one that refuses to let you merge at all, since
producing the answer in logarithmic time means never walking the inputs. Your own Chapter 1
*Squares of a Sorted Array* is the same skeleton wearing a disguise, which is why Chapter 6 has you
revisit it — if you solved that one first, compare the two solutions side by side before you move
on.

Both problems also have a Pythonic non-answer worth writing out once, purely to see why it is
disqualified: build the result as a fresh list and then publish it with `nums[:] = result`. It is
correct, it passes, it is three lines, and it spends O(n) extra memory to avoid the exact
difficulty the problem exists to teach. Section 9 of chapter 1 explains why that assignment is not
the same statement as `nums = result`; section 4 of chapter 2 prices it. Knowing precisely what you
gave up is the point of having written it.

What comes next in the notes is deletion — chapter 3 — which is this same physical shifting run in
the opposite direction, and reuses every cost you measured here.

---

[Chapter 2 hints index](../ch02.md)
