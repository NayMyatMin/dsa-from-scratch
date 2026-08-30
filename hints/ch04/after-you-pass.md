# Chapter 4 — after you pass: where each of these goes next

Nothing here is needed to finish the chapter. It assumes you have already solved **both of chapter
4's problems: 1346 Check If N and Its Double Exist and 941 Valid Mountain Array** — those two by
name, and nothing else. It's here so the lineage of each is on hand when you want more of the same
shape.

<!-- Maintenance note: the gate above names the two problems it is gated on, and it means those
     two only. Naming later problems as lineage is the point of this page; what it must never do
     is say how any problem outside chapter 4 is built — not the ones scaffolded in other chapters
     of this repo, and not the off-syllabus ones named below. A reader can legitimately arrive
     here with any of those still open, and a shape claim landing right after Tier 3 and Tier 4
     material hands over their middle tiers unearned. Say what question another problem asks;
     never say what it does about it. Chapter 2's version of this page failed exactly here: it
     described, in one clause, the technique shared by the problems scaffolded in chapters 3 and
     5, none of which the reader of that page had solved. Do not repeat the sentence in order to
     warn about it. Shape claims about someone else's problem belong on whichever after-you-pass
     page is gated on that problem being solved. -->

**1346 Check If N and Its Double Exist** — tagged *Array*, *Hash Table*, *Two Pointers*, *Binary
Search* and *Sorting*, and that tag list is the most interesting thing about it. Five tags for one
Easy problem is not indecision: three separate strategies from chapter 4 all reach the answer here,
and the constraints — `arr.length` capped at 500 — are deliberately small enough that the judge
accepts every one of them, including the plainest nested scan. That makes it an unusually good
problem to solve more than once. Section 3 of the notes has the arithmetic for deciding which of
them you would actually want at a size where it mattered, and section 5 has the reason the
sorted route needs a guard the other two do not.

Off the syllabus, *Two Sum* (Easy) is the ancestor of this whole family and asks the closest
question: two distinct positions whose values stand in a fixed arithmetic relation. *Contains
Duplicate* (Easy) and *Contains Duplicate II* (Easy) ask the same yes-or-no about a relation
between two positions with the arithmetic taken away and, in II, a bound on how far apart they may
be. *Intersection of Two Arrays* (Easy) asks it across two sequences instead of within one. All of
them are the question of chapter 4 wearing different clothes: *does a value I can describe exist
somewhere in here*, asked often enough that how you ask decides the runtime.

The Pythonic non-answer worth writing out once, now that you have a real solution to compare it
against, is the one-liner `any(a == 2 * b for a, b in permutations(arr, 2))`, with `permutations`
taken from `itertools`. It is one line, it leaves `arr` alone, and it agrees with the reference
oracle on every one of the 20,008 inputs it was checked against here. What it is, though, is
exactly the pass over every ordered pair of distinct positions that the stub's own docstring lists
as the slowest of the routes it measured — the whole of the O(n²) it prices, with the pairs handed
to you rather than written out. It is accepted only because the constraints stop at 500 elements.
Knowing precisely what you gave up is the point of having written it.

**941 Valid Mountain Array** — tagged *Array* and nothing else, which is the opposite signal:
there is no structure to reach for and no ordering to exploit, only the sequence and the definition.
What makes it a family is that the definition is a *shape*, so every relative of it is a different
question asked about the same shape. *Peak Index in a Mountain Array* (Medium) is handed the
guarantee this problem makes you check, and asks where the summit is instead of whether there is
one. *Find in Mountain Array* (Hard) takes that same guarantee and asks for an ordinary search
inside it, with the number of reads you are allowed capped. *Longest Mountain in Array* (Medium)
drops the guarantee and asks for the longest stretch that qualifies rather than a verdict on the
whole. *Minimum Number of Removals to Make Mountain Array* (Hard) asks what it would cost to make
the answer yes. *Monotonic Array* (Easy) is the same kind of verdict with one phase instead of two.

Neither of these two comes back later in the syllabus — chapter 5 revisits 26 and 27 and chapter 6
revisits 977, and 1346 and 941 are done when you finish them. What does carry forward is the
read-only contract they share, which is chapter 1's: the answer is the value you return, the input
comes back untouched, and nothing you write into `arr` can be an answer because nobody reads it
again. Chapter 5 takes the syllabus back to problems where that is not true and the list itself is
the answer, under a constraint on space rather than on time.

Both problems are also worth re-reading for what they did to your edge cases. Neither has an
interesting algorithm; both have an input that the obvious version of the answer gets wrong — a
lone zero for one, a plateau or a missing side for the other — and in both the wrong answer is a
confident `True` or `False` rather than a crash. Section 7 of the notes is the general form of that
lesson, and it applies well beyond these two: **a search that fails quietly is worse than one that
raises, and both of these were built to make you find that out.**

---

[Chapter 4 hints index](../ch04.md)
