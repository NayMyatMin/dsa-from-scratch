# 26. Remove Duplicates from Sorted Array — Tier 3 (approach)

Two families, and unusually both of them are accepted here. Decide which one you are writing before
you write it.

## Build the survivors somewhere else, then put them at the front

Filter into a new list — keep an element when it differs from the one before it — then assign that
list over the front of `nums` and return its length. Reads and writes never touch the same storage,
so nothing can be clobbered and one left-to-right pass works. O(n) time, O(k) extra space, and it is
in place in the sense the problem means: the object handed to you is the one holding the answer.
`dict.fromkeys` gets you the same list in one call, since a dict keeps its keys in first-insertion
order.

Nothing in `tests/ch03/test_p02_remove_duplicates.py` measures extra space, and the note at its foot
says so outright. This family passes, and it is not a loophole. **Constant extra space is the better
answer to reach for, and chapter 5 makes it the subject — it is not what this problem requires.**

Two details decide whether it works, and neither is the filtering. First, the slice you assign to
sets both the length and the memory:

```python
nums = sorted((i % 201) - 100 for i in range(30_000))
kept = list(range(-100, 101))        # the 201 survivors

nums[:len(kept)] = kept              # the front of nums, overwritten
print(len(nums))
# -> 30000
```

Assigning to `nums[:]` instead would leave `len(nums) == 201`. Both are accepted and both mutate the
caller's list, but the full-slice form allocates a buffer as large as the list it discards, so it
costs O(n) extra space however small `kept` is. Traced with `tracemalloc` on exactly these lists,
seven runs of each and identical every time: **241,856 bytes** for `nums[:] = kept`, **1,608** for
the front-slice form above.

Second, `set` is not an ordering, and order is graded on this problem: `list(set([12, 19, 25]))`
comes back as `[25, 19, 12]`. `sorted(set(nums))` fixes that and is accepted — but it pays
O(k log k) to recover an ordering the input already handed you, which is the one advantage this
problem gives away for free. And rebinding the name `nums` inside the method is invisible to the
caller: chapter 1, section 9.

## Never take anything out: decide, then place

The other family writes into `nums` and moves nothing. One left-to-right pass, and two positions in
the same list: where you are reading, and where the next survivor belongs. The second trails the first
and never overtakes it, and **that gap is the entire safety argument — every slot you write into is
one you have already read.**

Left for you:

- What the survivor test compares against. There are two defensible choices, and they are not
  obviously the same thing; work out why they agree before picking one.
- Where both positions start, and how many survivors you have before the loop runs at all. The
  constraint `1 <= nums.length` is what makes that answerable.
- What you return: something you counted, or something you read off the list afterwards. Only one of
  those survives a solution that leaves the length alone.

> **The official hints, verbatim:** "We need to modify the array in-place and the size of the final
> array would potentially be smaller than the size of the input array. So, we ought to use a
> two-pointer approach here. One, that would keep track of the current element in the original array
> and another one for just the unique elements." and "Essentially, once an element is encountered, you
> simply need to *bypass* its duplicates and move on to the next unique element."
>
> The first is this section's opening paragraph with a wrong clause in the middle: the size of the
> list need not change at all, and the solution this family is aiming at leaves it exactly as long as
> it arrived. Read as a requirement, it sends you hunting for a shrink you do not need — and "we
> ought to" overstates the rest, since the first family above uses no second position and is
> accepted. The second hint is weaker than it sounds: bypassing duplicates is the easy half, and
> skipping alone puts nothing into the front slots, which is what actually gets graded.

---

Close this file and go back to the code. Tier 4 is the full algorithm — it ends the problem.
Only if a real attempt fails: **[Tier 4 — full strategy](26-tier4.md)**

[Chapter 3 hints index](../ch03.md)
