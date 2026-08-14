# Chapter 3 — after you pass: where each of these goes next

Nothing here is needed to finish the chapter. It assumes you have already solved **both of chapter
3's problems: 27 Remove Element and 26 Remove Duplicates from Sorted Array** — those two by name,
and nothing else. It's here so the lineage of each is on hand when you want more of the same shape.

<!-- Maintenance note: the gate above names the two problems it is gated on, and it means those
     two only. Naming later problems as lineage is the point of this page; what it must never do
     is say how any problem outside chapter 3 is built — not the ones scaffolded in other chapters
     of this repo, and not the off-syllabus ones named below — because a reader can legitimately
     arrive here with any of them still open. 27 and 26 themselves return in chapter 5 under the
     same statement, so their own technique is not restated here either: a reader who has solved
     them does not need it, and the page has no way to tell how far into chapter 5 they are.
     Shape claims about someone else's problem belong on whichever after-you-pass page is gated
     on that problem being solved. -->

**27 Remove Element** — tagged *Array* and *Two Pointers*. The detail that makes it a family of its
own is the judge: it takes your `k`, sorts the first `k` elements, and only then compares them, so
the order the survivors end up in is genuinely not part of what you promised. That is section 6 of
the notes made concrete — the `ordered=False` half of the `matches` predicate, which most exercises
never give you an excuse to use. Off the syllabus, *Remove Linked List Elements* (Easy) asks the
identical question of a structure that has no indexes and no length to return, and *Remove Element*
itself is one of the small set of problems whose entire difficulty is the output contract rather
than the computation.

**26 Remove Duplicates from Sorted Array** — tagged *Array* and *Two Pointers*, and the mirror of
27 on exactly the point above: here order *is* part of the contract, the first `k` elements are
compared position by position, and `ordered=True` is the only reading of the answer that is
correct. The direct sequel is *Remove Duplicates from Sorted Array II* (Medium), the same statement
with each value allowed to survive twice instead of once. *Remove Duplicates from Sorted List*
(Easy) and its sequel (Medium) ask it of linked nodes, where the sorted input is the same gift and
nothing else about the setting is.

**Both of them come back in chapter 5**, re-framed as in-place exercises rather than as deletions —
26 with an explicit O(n) time requirement attached. Same statements, same constraints, a different
question asked about them, and there is nothing new to solve when you get there. What chapter 5
adds is the constraint that the chapter 3 notes deliberately left standing at the edge of section 5:
extra space that has to stay constant however long the input grows, which is stricter than "a copy
is affordable" and is a subject of its own.

Both problems also have a Pythonic non-answer worth writing out once, purely to see why it is
disqualified: build the survivors with a comprehension and publish them with `nums[:] = kept`. It
is correct, it passes, it is two lines, and section 5 of the notes measures exactly what it spends
to avoid the difficulty each problem exists to teach — a pointer per surviving element, briefly two
when the last resize has to move the block. Section 9 of chapter 1 explains why that assignment is
not the same statement as `nums = kept`, and why the difference is the whole reason the caller ever
sees your work. Knowing precisely what you gave up is the point of having written it.

What comes next in the notes is search — chapter 4 — which is the third of the three operations
chapter 2 section 1 named, and the one both of this chapter's forms have been quietly paying for
whenever they had to find something before they could touch it.

---

[Chapter 3 hints index](../ch03.md)
