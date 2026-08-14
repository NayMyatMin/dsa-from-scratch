# 27. Remove Element — Tier 3 (approach)

Three families. All three are accepted; they are not equally good, and the differences are not
where you would expect.

## Build the survivors somewhere safe, then put them where the caller reads

Filter into a fresh list, then write that list into the front of `nums`. Reads and writes never
touch the same storage, so nothing can be clobbered and one left-to-right pass does it. O(n) time,
O(n) extra space, and in place in the sense that matters: the object the caller handed you is the
object holding the answer. Two Python details decide whether it works at all:

```python
def rebind(nums):
    nums = [4, 9, 7]

readings = [4, 5, 9, 5, 7]
rebind(readings)
print(readings)
# -> [4, 5, 9, 5, 7]

prices = [4, 5, 9, 5, 7]
same = id(prices)
prices[:3] = [4, 9, 7]
print(id(prices) == same, len(prices), prices)
# -> True 5 [4, 9, 7, 5, 7]
```

Assigning to the bare name changes nothing the caller can see (chapter 1 section 9). Assigning to
a slice mutates the list they are holding — and note the second line: three values went into the
front, the length stayed at 5, and the stale `5, 7` behind them is not a defect.

Be clear about this family's standing before you talk yourself out of it. **Constant extra space is
the better answer to reach for, and it is not what this problem requires.** "In place" says where
the answer is read from; it does not forbid scratch space. `tests/ch03/test_p01_remove_element.py`
does not measure memory at all and says so, the judge accepts it, and chapter 5 is where the space
bound becomes the subject.

## One pass, no second list

You may write into `nums` while reading it, and the licence comes from the shape of the answer
rather than from any trick. After reading the first `i + 1` elements you have met at most `i + 1`
survivors, so the front region they need is one you have already passed over — nothing still unread
lives there.

That gives you two positions moving through one list at different speeds: where you are reading,
and where the next survivor belongs. Left for you:

- Which position advances on a survivor, which on an occurrence of `val`, and which on every
  element; and what the second position holds when the walk ends, which is the number you return.
- The empty list and a `val` that never occurs are both legal inputs. Neither should need a branch
  of its own — check that yours doesn't before you add one.

## Fill the hole from the far end

The other direction. On meeting an occurrence of `val` you need not slide anything: the element at
the back of the region you still care about has to be accounted for anyway, and moving it into the
hole costs one write instead of a shift.

This family has a trap with teeth, which is why it is worth attempting. The value you pull in from
the back has not been examined yet, so decide what happens when it is itself `val` before writing
the loop. A version that steps the read position on after every swap is wrong on 1,584 of the 2,046
cases formed by every binary list of length 0 to 9 against both values of `val` — and its smallest
failure is two elements long: `[5, 5]` with `val = 5` comes back claiming one survivor, a 5 still
sitting in slot 0.

> **The second and third official hints, verbatim:** "We can move all the occurrences of this
> element to the end of the array. Use two pointers!" and "Yet another direction of thought is to
> consider the elements to be removed as non-existent. In a single pass, if we keep copying the
> visible elements in-place, that should also solve this problem for us."
>
> Those are this tier's third and second families, in that order. The third is good, and close to a
> full answer already. The second is misleading as written: the swap walk does *not* end with all
> the occurrences at the end — it overwrites some of them with survivors on the way past, and over
> every binary list of length 1 to 8 the tail held every occurrence in only 44 of 510 cases. The
> tail is unspecified junk, and code written to make that sentence true does work nobody asked for.

---

Close this file and go back to the code. Tier 4 is the full algorithm — it ends the problem.
Only if a real attempt fails: **[Tier 4 — full strategy](27-tier4.md)**

[Chapter 3 hints index](../ch03.md)
