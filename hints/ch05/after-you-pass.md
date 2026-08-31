# Chapter 5 — after you pass: where each of these goes next

Nothing here is needed to finish the chapter. It assumes you have already solved **all five of
chapter 5's entries: 1299 Replace Elements with Greatest Element on Right Side, 283 Move Zeroes,
905 Sort Array By Parity, and the two the chapter revisits under its own framing — 27 Remove
Element and 26 Remove Duplicates from Sorted Array** — those five by name, and nothing else. It's
here so the lineage of each is on hand when you want more of the same shape.

<!-- Maintenance note: the gate above names the five problems it is gated on, and it means those
     five only. Naming later problems as lineage is the point of this page; what it must never do
     is say how any problem outside chapter 5 is built — not the ones scaffolded in other chapters
     of this repo, and not the off-syllabus ones named below. A reader can legitimately arrive
     here with any of those still open, and a shape claim landing right after Tier 3 and Tier 4
     material hands over their middle tiers unearned. Say what question another problem asks;
     never say what it does about it. In particular this page must not describe: duplicating
     values in place, writing a fixed-length buffer from its far end backwards, or combining two
     already-sorted sequences into one — those are chapter 2's two problems, and a reader here has
     not solved either. Chapter 2's own version of this page failed in this direction once, by
     describing in one clause the technique shared by problems the reader had not reached. Do not
     repeat the sentence in order to warn about it. Shape claims about someone else's problem
     belong on whichever after-you-pass page is gated on that problem being solved. -->

**1299 Replace Elements with Greatest Element on Right Side** — tagged *Array*, and nothing else.
That bare tag is accurate rather than lazy: there is no structure to reach for and no second
sequence involved, only a definition applied at every position at once. What makes it a family is
that the definition is *a summary of everything on one side of you*, and every relative changes one
word of that phrase. *Running Sum of 1d Array* (Easy) changes the side and the summary — everything
to the left, added rather than maximised. *Best Time to Buy and Sell Stock* (Easy) keeps the two
sides and asks for the best pairing of an earlier position with a later one instead of for a value
per position. *Product of Array Except Self* (Medium) asks each position for a summary of both sides
at once, and then forbids the arithmetic that would let you get the second side from the first.
*Daily Temperatures* (Medium) asks each position not for the extreme value later in the list but for
the distance to the nearest later position meeting a condition, which is a different question with
the same silhouette. *Next Greater Element I* (Easy) asks that one across two sequences rather than
within one.

Space is scored on none of the three, and 1299's stub says so most bluntly: nothing in the suite
counts allocations, and a solution that computes the whole answer somewhere else and then writes it
into `arr` is accepted. Now that you have a passing version, the exercise worth doing is the one no
grader here could ask for. Run your solution under section 1's `peak_extra` harness at `n = 10**4`,
then at `n = 10**5`, and see whether the figure it reports moves. Both answers are legal. Knowing
which one you shipped is the point, and it takes about a minute to find out.

**283 Move Zeroes** — tagged *Array* and *Two Pointers*. The two you have just revisited, 27 and 26,
are its immediate family: all three hand you one list, ask a yes-or-no question of every element in
it, and want the elements that answered one way gathered at the front of that same list. They differ
in what the question is and in whether a count or the length carries how many answered it. Off the
syllabus, *Remove Duplicates from Sorted Array II* (Medium) is 26 with each value allowed to appear
twice instead of once, which is the smallest interesting change you can make to a keep-or-drop rule.
*Sort Colors* (Medium) asks the partition question with three groups where 905 asked it with two.
*Rearrange Array Elements by Sign* (Medium) asks for the two groups interleaved rather than
separated, with each group's own order preserved.

Its follow-up is the one question in the chapter nothing here scores: *could you minimise the total
number of operations done?* Section 6 of the notes is where that gets a number — it counts exchanges
for both shapes and gives each a closed form, and the honest subtraction at the end of that
subsection (the writes where the two indices sit on the same slot and a value is stored over itself)
is exactly the operation the follow-up is asking you to eliminate. Section 5 weighed guarding those
away and measured it as a wash on this interpreter, at 0.87 to 1.15 times the unguarded form across
six runs, with which side of 1 it lands on decided by how much of the input gets dropped. That is
worth re-reading with a passing solution in hand, because the follow-up is a question about
instruction counts and the measurement is a question about wall clock, and they do not have to
agree.

**905 Sort Array By Parity** — tagged *Array*, *Two Pointers* and *Sorting*, and the third tag is
the interesting one, because sorting is not what the problem needs and is what most people reach
for. Its family is the family of partitions. *Sort Array By Parity II* (Easy) is the same two groups
with the positions they must land in specified exactly, which removes the freedom this one gave you.
*Sort Colors* (Medium) asks for three groups instead of two. *Partition Array According to Given
Pivot* (Medium) asks for three groups around a value you are handed, with the relative order inside
each group required — which is exactly the clause 905 left out, and section 6 of the notes measured
what putting it back would cost you: over every permutation of a list of seven or fewer, the
converging shape left the kept group out of its original order in 4,980 of 5,913 arrangements.

You had written a converging pair before this chapter, and it is worth going back to look at.
Chapter 1's 977 starts one index at each end of the input and walks the two towards each other,
which is the skeleton 905 uses, asked a different question. Reading your two loops side by side is
five minutes well spent.

The Pythonic non-answers are worth writing out once each, now that you have real solutions to
compare them against. Both are one line, both are in place under the practical reading, and both
were checked here against a reference implementation on 20,000 random inputs apiece:

```python
nums.sort(key=bool, reverse=True)   # 283: zeros last, non-zeros in their original order
nums.sort(key=lambda x: x % 2)      # 905: evens first, odds after — then return nums
```

They work for one reason, and it is the reason chapter 1 section 8 gives: the sort is **stable**, so
elements that compare equal keep the order they were in, and `reverse=True` reverses the ordering
without breaking that. For 283 the whole difficulty of the problem — the relative order of the
non-zero elements — is being handled by a property of `list.sort` rather than by anything you wrote.
What you gave up is in the stub's own table: a sort with a key measured 0.208 to 0.293 ms per call
against 0.083 to 0.221 ms for the linear solutions on 283, and 0.164 to 0.166 against 0.110 to 0.188
on 905. The space is the sharper cost, and it is invisible from the call site. On a 10,000-element
list built half of zeros, `nums.sort(key=bool, reverse=True)` peaks at 120,176 bytes of extra
allocation — the list of computed keys plus the merge buffer — reproducing to the byte across three
runs, against the flat zero section 5 measures for a cursor pass over 200,000 elements. 283's
statement asks
for the move "without making a copy of the array"; nothing enforces that clause, and this line is
where it quietly goes.

What carries forward from this chapter is the habit rather than any one loop. Chapter 5 is the only
one so far where the answer's *address* was part of the specification, and the three stubs disagreed
with each other about it on purpose. Section 7 of the notes is the general form: **before you
overwrite anything, be able to say who else holds a name for it, and what they will read after you
return.** Chapter 6 closes the syllabus and revisits 977 — a problem you have already solved, which
is the point of putting it there.

---

[Chapter 5 hints index](../ch05.md)
