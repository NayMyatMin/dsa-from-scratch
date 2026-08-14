# Chapter 3 — Deleting From a List

Chapter 1 settled the format: one contiguous block of pointers, an index that names a place rather
than a value, a length that is stored rather than counted. Chapter 2 began the contract with the
operations that grow a list. This chapter finishes it with the ones that shrink it, and the physical
work is chapter 2's run backwards — the same unbroken run of slots, the same bulk move over the same
tail, the opposite direction. The cost model therefore arrives already paid for, which is what lets
this chapter spend itself on everything deletion has that insertion did not.

That turns out to be most of the chapter. Only one removal form has to find its own target, and the
search it pays for costs about twenty times what the shift costs. Only one hands the removed element
back, which decides when the memory comes back with it. An index that names no element raises where
the matching insertion clamped in silence, and a slice that names no element does not. A list that
shrinks under a walk skips elements rather than repeating them, and says nothing either way. And a
caller may forbid the length to change at all, which takes every form in this chapter off the table
in one stroke and leaves a convention standing in their place.

It leans on chapter 1 rather than repeating it. The operation cost table is chapter 1 section 8,
the iterator protocol is section 6, over-allocation and amortization are section 7, and aliasing and
in-place semantics are section 9; where this chapter needs one of those it names it and moves on.
Chapter 2 is cited the same way throughout — sections 3, 4, 5 and 7 of it are the four this chapter
mirrors most directly, and none of them is re-derived here. Read chapter 2 first if you have not:
half of what follows is priced against it.

## How to read this

**Run the code.** Every block is executable exactly as written — there are 96 of them, carrying 240
`# -> value` comments — and every one of those comments is a real observed result rather than an
illustration. Open a session next to this document and paste as you go:

```bash
uv run python
```

Some blocks continue the one before them within a section, reusing a variable set up earlier. Some
deliberately end in an exception and say so on the offending line; those are demonstrations, and the
exception is the point.

**Predict before you run.** Section 8 is ten drills and an answer key, and it is the honest test of
whether the rest of the chapter landed. The three subjects it goes after hardest — which spellings
raise and which go quiet, what a removal does to an index or an iterator recorded before it, and the
difference between one shift and many — are the three that decide correctness rather than style.

**Measurements come from this machine.** Every number was measured on CPython 3.14.4, the
interpreter in this repository's virtual environment, on a 64-bit build. Deterministic values —
object sizes, capacities, printed output — will reproduce exactly for you. Timings will not; they
depend on your hardware and on what else is running. What reproduces is the shape: the ratios, the
orderings, and the way a figure moves when the input doubles. Where a number is a timing, the
surrounding prose says what about it is meant to hold.

**It is a little longer than chapter 2.** About 22,200 words, just under three hours at the pace of
prose you stop and run rather than skim, against chapter 1's six and a quarter. One long sitting or
two; the natural break is the end of section 5, which closes the tour of the forms about two thirds
of the way in.

## The sections

| | Section | What it settles | Size |
|---|---|---|---:|
| 1 | [Deletion, and why it is insertion in reverse](#1-deletion-and-why-it-is-insertion-in-reverse) | The slide, the map of the forms, and why a list cannot hold a hole | 2,200 w · 17 min |
| 2 | [Removing from the end](#2-removing-from-the-end) | The one position that costs nothing, and where the block goes back | 2,200 w · 17 min |
| 3 | [Removing by position](#3-removing-by-position) | The shift measured against `i`, and `del` against `pop` | 3,100 w · 23 min |
| 4 | [Removing by value](#4-removing-by-value) | The only form that searches first, and what the search costs | 2,800 w · 21 min |
| 5 | [Removing many at once](#5-removing-many-at-once) | One shift instead of k, and building the survivors instead | 3,600 w · 28 min |
| 6 | [Deleting when the length cannot change](#6-deleting-when-the-length-cannot-change) | A count beside the list, and how a result of that shape is checked | 2,200 w · 17 min |
| 7 | [Deleting while iterating](#7-deleting-while-iterating) | The cursor that does not move when the elements do | 2,500 w · 19 min |
| 8 | [Drills](#8-drills) | Ten predictions, an answer key, and a readiness check | 2,600 w · 20 min |

Sections 1 through 6 are the spine and are best read in order: each one is a different answer to the
question of what leaves and how you name it, and section 6 is the case where the answer is forced —
nothing may leave at all, and the word has to mean something else. Section 7 is the one to read
before you edit a list while walking it. Section 8 is the exit exam.

When you finish, the two problems in `arrays101/ch03/` are waiting. Sections 6 and 7 are the two
written with them in mind, and neither of them is a hint: section 6 is the output contract both of
them use, and section 7 is the failure, described so you recognise it when you produce it.

---

## 1. Deletion, and why it is insertion in reverse

Chapter 2 took the half of a list's contract that puts values in. This chapter takes the half that
takes them out, and most of it is chapter 2 read backwards. Deletion arrives in the same three cases
— from the end, from the front, from an arbitrary position in between — for the same reason
insertion did, and that reason is the fact chapter 1 built everything on: the elements sit in one
unbroken run of slots, and slot `i` holds element `i`. Every edit has to leave that true, and
leaving it true is the entire bill.

Chapter 2 section 1 set out the three operations a data structure exists to answer — insert, delete,
search — and put insertion among them. That framing is not re-derived here. What is worth stating
twice is the shape of the answer, because deletion's is identical to insertion's: **once you know
where it is, the cost of a removal is not the size of the list, it is how much of the list is
standing to the right of the thing you removed.** Finding it is a separate bill, and only one of the
forms below pays it.

### The same queue, later in the day

Chapter 2 section 1 watched a render farm's job queue fill: jobs submitted onto the back, an
incident job jumping to the front. Now watch it empty. A job leaves that queue for several unrelated
reasons over a working day, and each reason reaches for a different call.

**The worker takes the next job.** Position 0 comes out and starts running, and every job behind it
moves one place closer to the front. This is the ordinary case and it happens all day.

**A submitter withdraws the job they just queued.** They notice the wrong branch seconds after
hitting the button, and the job they take back is the one at the very back of the queue.

**A job is cancelled by name.** Someone pastes an identifier into the cancel box. Nobody knows or
cares what position it currently occupies; the queue has to find it and take it out.

**A job is cancelled by position.** The status page lists the queue in order and the operator picks
a row off it, so the position is what arrives and the name never comes into it.

**A branch is abandoned and the batch queued for it comes out together.** Several queued jobs,
sitting next to each other because they were submitted in one go, removed in one action.

**A dashboard wants the queue without the test jobs.** Nothing is being cancelled here. The
scheduler needs a filtered view to render, and the queue itself has to be left exactly as it is.

**The queue is drained at shutdown.** Everything goes, at once.

Every one of those is spelled differently, and the whole day fits in one session:

```python
queue = ["hotfix-9002", "render-4471", "index-rebuild", "thumbs-2210",
         "test-smoke", "test-e2e", "test-perf", "backup-nightly", "gc-sweep"]

running = queue.pop(0)                  # the worker takes the next job
print(running)
# -> hotfix-9002

withdrawn = queue.pop()                 # the submitter takes back the newest job
print(withdrawn)
# -> gc-sweep

queue.remove("index-rebuild")           # cancelled by name; position unknown
print(queue)
# -> ['render-4471', 'thumbs-2210', 'test-smoke', 'test-e2e', 'test-perf', 'backup-nightly']

del queue[1]                            # cancelled by position
print(queue)
# -> ['render-4471', 'test-smoke', 'test-e2e', 'test-perf', 'backup-nightly']

del queue[1:3]                          # a contiguous band, in one action
print(queue)
# -> ['render-4471', 'test-perf', 'backup-nightly']

kept = [job for job in queue if not job.startswith("test-")]   # a new list, not an edit
print(kept)
# -> ['render-4471', 'backup-nightly']
print(queue)
# -> ['render-4471', 'test-perf', 'backup-nightly']

queue.clear()                           # drained at shutdown
print(queue, len(queue))
# -> [] 0
```

Seven removals, six of them edits to the queue itself and one of them a new list built beside it.
The printed output conceals what they cost, exactly as it did in chapter 2.

### The map, before the detail

| What you want gone | How you say it | What you get back | Settled in |
|---|---|---|---|
| the last element | `queue.pop()` | the removed element | section 2 |
| the element at a position | `queue.pop(i)`, `del queue[i]` | the element; nothing | section 3 |
| the first element equal to a value | `queue.remove(x)` | nothing | section 4 |
| a contiguous run | `del queue[a:b]`, `queue[a:b] = []` | nothing | section 5 |
| everything failing a test, scattered | `[x for x in queue if keep(x)]` | a new list | section 5 |
| every element | `queue.clear()`, `del queue[:]` | nothing | section 2 |

Four distinctions run through that table. `pop` is the only form that hands the element back, which
is the whole difference between it and `del` — chapter 1 section 4 made that point and it does not
change. `remove` is the only form that takes a value rather than a position, so it is the only one
that has to search first. The comprehension is the only form that leaves the original list
untouched, because it builds a second one. And `clear` is the only form that names no position at
all.

One case is missing from the table because it is not really deletion. When the list's length is not
allowed to change, nothing can come out of it, and the closest available act is writing a different
value over a slot that already exists. Section 6 is where that belongs.

### The person who joined last can leave without disturbing anyone

Think of the queue as a line of people rather than a list of strings. Somebody near the front leaves
and everyone behind them shuffles forward a place — the further forward they were standing, the more
people have to move. But the person who joined most recently, standing at the very back, can step
out at any moment and nobody in front of them notices. There is nobody behind them to move up.

That is the whole asymmetry, and it mirrors chapter 2's: appending was the cheap end for insertion,
and removing from the end is the cheap end for deletion, for the same reason in reverse. On a queue
of a hundred thousand jobs it is not a subtlety.

```python
import timeit

setup = "queue = [f'job-{i}' for i in range(100_000)]"
end = min(timeit.repeat("queue.append('rush'); queue.pop()",
                        setup=setup, number=10_000, repeat=7))
front = min(timeit.repeat("queue.append('rush'); queue.pop(0)",
                          setup=setup, number=10_000, repeat=7))
print(round(end / 10_000 * 1e9), "ns per add-and-remove at the back")
# -> 13 ns per add-and-remove at the back
print(round(front / 10_000 * 1e9), "ns per add-and-remove at the front")
# -> 12530 ns per add-and-remove at the front
print(round(front / end), "x")
# -> 976 x
```

Both rows run the same `append`, so what the clock is comparing is `pop()` against `pop(0)` and
nothing else, and the queue is the same length at the end of every iteration as it was at the start.
The only difference is which end the removal took from, and at this length it is worth close to a
factor of a thousand. The front is the stable half of that measurement: reruns on this machine hold
it between 12,400 and 13,300 ns while the back wanders between 12 and 16 ns, which puts the
multiplier anywhere from roughly 750x to 1050x. Your own figures will differ; the ordering will
not, and neither will the fact that the gap widens as the queue grows — the same measurement at
10,000 elements puts the front only about 60x behind, and at 400,000 elements several thousand
times behind.

### Deleting never makes a hole

Everything else in this chapter is a consequence of one fact: a list has no way to represent an
absent element. There is no blank, no gap, no tombstone; chapter 1 section 4 established that every
slot inside the length holds a real object and there is no such thing as an empty one to read. So
removing the element at position `i` cannot mean vacating slot `i` and walking away. It means the
element that was at `i + 1` has to become element `i`, the one at `i + 2` has to become element
`i + 1`, and so on to the end.

**"Delete" in a contiguous structure is not an erasure, it is a slide: everything after the gap
moves left by one, and the only question that decides the cost is how many elements that is.**

Nothing is copied and nothing is rebuilt. The objects that move are the same objects; only their
addresses change position within the block:

```python
queue = ["render-4471", "index-rebuild", "thumbs-2210", "backup-nightly"]
tail = queue[2:]
del queue[1]
print(queue)
# -> ['render-4471', 'thumbs-2210', 'backup-nightly']
print(queue[1] is tail[0], queue[2] is tail[1])
# -> True True
print(queue.index("thumbs-2210"))
# -> 1
```

`"thumbs-2210"` is the object it always was — it simply answers to index 1 now instead of 2. A run
of 8-byte pointers slid over by 8 bytes, which is chapter 2 section 3's shift running the other
direction.

Insertion at `i` moves the `n − i` elements standing at `i` and beyond one slot right to open a gap.
Deletion at `i` moves the `n − i − 1` elements standing after `i` one slot left to close one. One
element fewer, the same mechanism, opposite direction — which is why chapter 1 section 8's cost
table gives `insert(i, x)` and `pop(i)` the identical O(n − i) row, why removing the first element
is the worst case rather than a separate operation with rules of its own, and why removing the last
element moves nothing at all. That table is the reference; sections 2 through 5 are what the rows
mean in practice.

### The length falls; the block does not

A removal shortens the list on the spot, and there is no second number to maintain beside it.
`len()` reads a stored field rather than counting — chapter 1 section 7 — so length and occupancy
are one thing, and no bookkeeping of yours has to record where the live elements stop. **The list's
length is the only length there is, and it is correct the instant the removal returns.**

The block underneath is slower to react. `list(range(1000))` measures 8,056 bytes — 56 for the
header and 8,000 for a thousand pointer slots — and popping 500 elements off the end leaves that
figure at exactly 8,056, with half the slots now past the length and unreachable. Storage comes back
on a threshold rather than on every removal, which is chapter 1 section 7's over-allocation rule run
backwards and the reason `pop()` is amortized rather than flatly constant. Section 2 measures where
the threshold falls.

What deletion does to the element itself is drop one reference to it, and chapter 1 section 4
already settled what follows: an object is freed the moment its count reaches zero, so a removed
element survives exactly as long as something else still refers to it. That was stated there about
an overwrite; a removal is the same bookkeeping, and the `- 1` below is the same correction for
`getrefcount`'s own argument.

```python
import sys

job = "".join(["render-", "4471"])
queue = [job, "index-rebuild"]
print(sys.getrefcount(job) - 1)
# -> 2
del queue[0]                     # the list lets go; the name still holds it
print(sys.getrefcount(job) - 1)
# -> 1
```

`del queue[0]` and `del job` are one statement doing one thing at two kinds of target: unbind a
reference, and let the object's own count decide the rest. The list form has the extra job of
sliding the tail afterwards; the accounting is identical.

### An index is a position, not a handle

Chapter 1 section 4 stated the rule in one line while introducing `del`: an index names a position
in the list as it stands, not the element standing there. The slide is what makes that rule bite,
and it bites harder on the way out than on the way in. Every index you were holding onto that
pointed past the deletion point now means a different element, and it says so without raising.

```python
queue = ["hotfix-9002", "render-4471", "index-rebuild", "thumbs-2210", "backup-nightly"]
i = queue.index("thumbs-2210")
print(i)
# -> 3
del queue[0]
print(queue[i])                 # the same index, a different job
# -> backup-nightly
del queue[0]
try:
    print(queue[i])
except IndexError as e:
    print(e)
# -> list index out of range
```

The first read is the dangerous one. It raises nothing, returns a perfectly plausible job name, and
is wrong. Only the second read, once the queue has shrunk past the index entirely, fails loudly.
Chapter 2 section 7 catalogued this for a list growing underneath a stored index; a list shrinking
underneath one is the same bug with the sign flipped, and it fails in one way the growing case
cannot — a walk over a shrinking list steps over the elements that slide into the gaps, so it visits
fewer than it was given. Section 7 takes that apart, and it is the failure both of this chapter's
problems are shaped to invite.

---

## 2. Removing from the end

Section 1 priced a removal at the length of the tail it has to close up. At the last position that
tail is empty: no element changes index, no pointer is relocated, and the whole operation is
dropping one reference and lowering the stored length by one. Chapter 2 section 2 made the matching
claim about putting values in, and the two are one fact rather than two: **a position with nothing
after it has no arrangement left to repair, which is why the end of a list is the cheap end in both
directions.**

Section 1's line of people is the picture to keep: the person who joined most recently steps out of
the back and nobody in front notices. What follows is the measurement behind "nobody notices".

### `pop()` takes the element out and hands it back

Called with no argument, `pop` removes the last element and evaluates to it:

```python
queue = ["render-4471", "backup-nightly", "index-rebuild", "thumbs-2210"]
newest = queue[-1]
withdrawn = queue.pop()
print(withdrawn)              # -> thumbs-2210
print(withdrawn is newest)    # -> True
print(queue, len(queue))      # -> ['render-4471', 'backup-nightly', 'index-rebuild'] 3
```

What comes back is the object that was in the slot, not a copy of it.

That return value is the detail people read past. Every other list method that edits the list in
place evaluates to `None` — the in-place convention from chapter 1 section 9 — and `pop` is the
single exception to it:

```python
work = [3, 1, 2]
print(work.append(9), work.insert(0, 5), work.reverse(), work.sort())
# -> None None None None
print(work)         # -> [1, 2, 3, 5, 9]
print(work.pop())   # -> 9
print(work)         # -> [1, 2, 3, 5]
```

**`pop()` is a read and a removal in one statement, and that is precisely why the method is not
called `delete`: the element does not vanish, it comes back to you.**

Because it hands something back, `pop` invites the rebinding typo in a quieter form than the others
do:

```python
undo = ["typed", "pasted", "deleted"]
undo = undo.pop()
print(undo)         # -> deleted
```

`work = work.sort()` leaves a name bound to `None`, and the next line that treats it as a list
raises. This leaves a name bound to a perfectly ordinary string, nothing raises, and the list is
unreachable if nothing else named it. Write `last = undo.pop()` and leave the list where it is.

### `del nums[-1]` when the value is not wanted

When the element is going in the bin, `del` says so and offers you nothing back:

```python
readings = [18.2, 19.0, 21.4]
del readings[-1]
print(readings)     # -> [18.2, 19.0]
```

That is a difference of intent rather than of price. Four spellings name the last element, and they
separate only by how much interpreted work each does before the removal starts. Every row below
pairs one `append` with one removal, so the list ends each iteration as long as it started and both
calls are inside the figure. The extra `append` and `pop` in the setup buy spare capacity before the
clock starts: a list built from a range is allocated to exactly its length (chapter 1 section 7), so
without them the first `append` would enlarge the block once per repeat and smear that one
reallocation across every figure.

```python
import timeit

setup = "nums = list(range(1_000_000)); nums.append(0); nums.pop()"
for stmt in ("nums.pop()", "del nums[-1]", "nums.pop(-1)", "nums.pop(len(nums) - 1)"):
    t = min(timeit.repeat(f"nums.append(0); {stmt}", setup=setup,
                          number=100_000, repeat=7))
    print(f"{stmt:<26}{t * 1e9 / 100_000:6.1f} ns")

# -> nums.pop()                  15.2 ns
# -> del nums[-1]                14.0 ns
# -> nums.pop(-1)                16.1 ns
# -> nums.pop(len(nums) - 1)     27.2 ns
```

The top two sit within a nanosecond and a half of each other — a bytecode against a method
call — and which of them leads changes between sittings, so the gap is far too small to choose on.
The bottom two spell the index out and were consistently dearer for it in every run. `pop(-1)` pays
about a nanosecond to accept an argument and resolve a negative index against the length.
`pop(len(nums) - 1)` costs close to twice the bare call — an interpreted `len`, a subtraction and an
argument push, all to name the slot that empty parentheses find by themselves, the overhead
chapter 2 section 3 measured on `insert(len(nums), 0)`. If you mean the last element, write `pop()`
or `del nums[-1]`. Section 3 takes up the choice between `del` and `pop` where it has consequences,
at a position in the middle.

### The price does not move when the list does

Same pairing and the same bought capacity as above, so nothing inside the loop ever resizes the
block. The only thing that changes down the rows is how long the list is:

```python
import timeit

for n in (1_000, 10_000, 100_000, 1_000_000, 10_000_000):
    setup = f"nums = list(range({n})); nums.append(0); nums.pop()"
    t = min(timeit.repeat("nums.append(0); nums.pop()", setup=setup,
                          number=100_000, repeat=7))
    print(f"n = {n:<12}{t * 1e9 / 100_000:6.1f} ns per append-and-pop")

# -> n = 1000          14.8 ns per append-and-pop
# -> n = 10000         14.6 ns per append-and-pop
# -> n = 100000        15.0 ns per append-and-pop
# -> n = 1000000       15.3 ns per append-and-pop
# -> n = 10000000      15.1 ns per append-and-pop
```

Ten thousand times the length, and the column moves by less than a nanosecond. Anything proportional
to the length would have made the bottom row ten thousand times the top one. Reruns landed every
figure between 11.3 and 17.7 ns — the whole column drifting together with the state of the
machine — and never ordered them by size. **Removing the last element is constant time, because
what sets the price of a deletion is the number of elements to the right of it, and at the end
there are none.** That is chapter 1 section 8's `O(n − i)` row read at the largest `i` a list has.
Section 3 reads it at every other value.

Drop the setup's spare capacity and the same code says something else: the column rises down the
page and the ten-million row comes out at more than twice the top one, which reads exactly like a
cost that grows with length. It is not. `setup` runs once per repeat while the statement runs
100,000 times, so the one reallocation the first `append` forces is divided by 100,000 and charged
to every call — chapter 1 section 11's trap, in the shape that flatters a wrong conclusion.

Draining a list one `pop()` at a time holds the same rate. Timed as `while nums: nums.pop()` on a
fresh list per repeat, the best figure ran 13.2 to 14.7 nanoseconds a pop from a thousand elements
up to a million and 15.3 to 15.6 at ten million: a few percent across four orders of magnitude, not
a factor. What the largest size adds is only partly the popping — ten million pops drop the last
reference to ten million distinct integers, each reclaimed on the spot. `[None] * n`, where every
slot points at one shared object and nothing has to be freed, drained at 10.7 to 12.2 nanoseconds a
pop, 1.2x to 1.3x quicker, and that margin is what releasing costs.

The word chapter 1 section 8's table attaches to this row is *amortized*, for the same reason it
sits on `append`. Now and then a pop leaves the block too large to justify and the list is moved
into a smaller one. That pop can be caught in the act: on a million-element list drained to just
above half its length and then timed call by call, the pop that carried the length to 499,999
measured between 0.53 and 0.66 milliseconds across five runs, against 80 to 900 nanoseconds for the
pops either side of it. Three to four orders of magnitude, on one call in half a million.

### Popping an empty list

An empty list has no last element, and the two spellings complain in different words:

```python
jobs = []
try:
    jobs.pop()
except IndexError as e:
    print(e)          # -> pop from empty list

try:
    del jobs[-1]
except IndexError as e:
    print(e)          # -> list assignment index out of range
```

`pop` has a message written for the occasion. `del` falls back to the general complaint about an
index naming no slot, and its wording repays a second read: it says *assignment* although nothing
was assigned, because the removal reaches the same internal entry point writing to `nums[-1]` would.
Neither form returns a sentinel and neither returns `None` — the removal fails, and the code below
it does not run.

The guard is the list itself, which is falsy when empty:

```python
queue = ["compress", "upload", "verify"]
while queue:
    print(queue.pop())
# -> verify
# -> upload
# -> compress
print(queue, bool(queue))    # -> [] False
```

No length comparison, no counter. Note the order the work came back in: `pop()` returns the most
recently added element, so a list with `append` and `pop()` is how a stack is spelled in Python, and
it is a stack whose every operation is the constant-time case measured above.

### Three ways to empty a list, and one that only looks like it

`clear()`, `del nums[:]` and `nums[:] = []` all leave a list with nothing in it. They are one
operation under three spellings, indistinguishable on the clock — on a million elements they came
out at 3.97, 3.99 and 3.99 ms, and the ordering between them changed on every rerun. All three edit
the object every name for it can see. The last of the four groups below is the spelling that is not
in the family at all:

```python
inventory = [4, 7, 2]
same = inventory
inventory.clear()
print(inventory, same, same is inventory)     # -> [] [] True

inventory = [4, 7, 2]
same = inventory
del inventory[:]
print(inventory, same, same is inventory)     # -> [] [] True

inventory = [4, 7, 2]
same = inventory
inventory[:] = []
print(inventory, same, same is inventory)     # -> [] [] True

inventory = [4, 7, 2]
same = inventory
inventory = []
print(inventory, same, same is inventory)     # -> [] [4, 7, 2] False
```

**The first three empty the object; the fourth empties nothing and moves the name to a different
object.** That is `nums[:] = ...` against `nums = ...` with an empty right-hand side, which
chapter 1 section 9 derives in full where the difference decides whether a caller ever sees your
work. Prefer `clear()` on the reading — it names the operation, where the other two spell it as a
slice deletion and a slice assignment that happen to cover everything.

None of the three is free. Emptying is O(n) because every element is holding a reference that has to
be dropped, and the cost is in those references rather than in the block: clearing a million
distinct integers measured 3.97 ms against 0.51 ms for `[None] * 1_000_000`, where one shared object
absorbs every drop and nothing is freed. Both are linear, and the near-eightfold gap is what
releasing costs. The block, meanwhile, goes back in one piece:

```python
import sys

big = list(range(1_000))
print(sys.getsizeof(big))              # -> 8056
big.clear()
print(len(big), sys.getsizeof(big))    # -> 0 56
```

Fifty-six bytes is the bare header from chapter 1 section 7. The element block is gone, not merely
unused.

### The block does not shrink as fast as the length

Emptying in one call releases the storage immediately. Taking the same list down one element at a
time does not, and chapter 1 section 7 measured the rule: nothing is handed back until the length
falls *below half* the capacity, which is the slack that stops a loop alternating `append` and
`pop()` from copying the whole list on every call. Here is the same rule in bytes rather than slots:

```python
import sys

nums = list(range(1_000_000))
print(len(nums), sys.getsizeof(nums))    # -> 1000000 8000056

for _ in range(500_000):
    nums.pop()
print(len(nums), sys.getsizeof(nums))    # -> 500000 8000056

nums.pop()
print(len(nums), sys.getsizeof(nums))    # -> 499999 4500088
```

Half the elements gone and not one byte released: eight megabytes of block holding four megabytes of
live pointers. The next pop crosses the threshold and three and a half megabytes go back at once —
the expensive pop priced a few paragraphs above, seen from the memory side. **A list that grew large
and then shrank keeps its old capacity until it is less than half full**, so a peak in length is a
peak in memory that outlives the length by a long way. If a large list has finished its work and its
name stays in scope, `clear()` hands the block back in one call.

Every other position this chapter visits costs something. This one does not: no element changes
index, nothing is relocated, and the figure does not move when the list gets ten thousand times
longer. That is worth designing around rather than merely knowing. Where you control the order
things leave in — a stack of undo steps, a parser's stack of open brackets, a queue reversed once
before it is drained — arranging for the end to be the only place you delete from turns deletion
into bookkeeping. Section 3 is the bill when the position is not yours.

---

## 3. Removing by position

### What the call does

`del nums[i]` removes the element at position `i` and closes the gap by moving every element from
`i + 1` onward one slot to the left. The length drops by one. `nums.pop(i)` performs the same work
and additionally hands back the element it removed. Both are the exact mirror of chapter 2 section
3's `insert(i, x)`: the same run of pointers, the same distance, the opposite direction — and this
section is the mirror of that one, which measured the shift from the insertion side.

```python
readings = [12, 15, 19, 22, 25]
kept = readings[3]
del readings[1]
print(readings, len(readings))   # -> [12, 19, 22, 25] 4
print(readings[2] is kept)       # -> True

readings = [12, 15, 19, 22, 25]
gone = readings.pop(1)
print(gone, readings)            # -> 15 [12, 19, 22, 25]
```

No element was copied and none was rebuilt. `22` is the object it always was, and closing the gap
consisted entirely of writing its address one slot earlier — section 1's slide, seen at one
position. The storage underneath is untouched by it: deletion rearranges pointers inside a block the
list already owns, and section 2 measured the threshold where that block comes back. What this
section prices is the slide.

### The cost is n − i − 1, not n

Every element after the deletion point has to move, so the bill is the length of the tail. Fix the
list at 100,000 elements and walk the deletion point across it. Each measurement pairs the deletion
with an `append`, which restores the length at negligible cost, and subtracts a baseline that does
the same bookkeeping without any shift — chapter 1 section 11's method, and the harness chapter 2
section 3 used for `insert`.

```python
import timeit

n = 100_000
setup = f"nums = list(range({n}))"
base = min(timeit.repeat("nums.append(0); nums.pop()", setup=setup, number=1000, repeat=7))
for i in (0, 25_000, 50_000, 75_000, 90_000, 99_000, n - 1):
    stmt = f"del nums[{i}]; nums.append(0)"
    pair = min(timeit.repeat(stmt, setup=setup, number=1000, repeat=7))
    ns = (pair - base) * 1e9 / 1000
    moved = n - i - 1
    each = f"{ns / moved:.3f} ns each" if moved else "nothing to move"
    print(f"del at {i:>6}: {ns:9.1f} ns   {moved:>6} elements   {each}")
# -> del at      0:   25541.9 ns    99999 elements   0.255 ns each
# -> del at  25000:   19734.8 ns    74999 elements   0.263 ns each
# -> del at  50000:   12818.9 ns    49999 elements   0.256 ns each
# -> del at  75000:    6400.4 ns    24999 elements   0.256 ns each
# -> del at  90000:    2558.8 ns     9999 elements   0.256 ns each
# -> del at  99000:     268.5 ns      999 elements   0.269 ns each
# -> del at  99999:       0.1 ns        0 elements   nothing to move
```

The right-hand column is the finding, and it is the one chapter 2 section 3 reached from the other
direction: divide by the elements that had to move and the same quarter of a nanosecond comes back
every time. What reproduces is that flatness rather than the digits — a busy machine pushed the
whole column to 0.27 without disturbing its evenness. The descending middle column is not a property
of `del`; it is that constant multiplied by a tail that keeps getting shorter, and at the last
position there is no tail at all, which is section 2's subject.

The constant is small because none of the move is interpreted. One bytecode instruction reaches
CPython's own implementation, and the tail relocates inside a single bulk memory move at C speed
with no bytecode running per slot. Against chapter 1's reference cost of 5.6 ns to read one element
through the interpreter, you can relocate roughly twenty elements in the time it takes to read one.
`insert` was charged 0.278 ns per element for the identical work; timed head to head on a
million-element list, `nums.insert(0, 0)` measured 276.3 µs against `del nums[0]` at 282.9 µs, and
across reruns the two stayed within a third of each other while trading places for which was ahead.
**Insertion and deletion are the same shift at the same price, and neither direction is the cheap
one.**

### The parameter is the tail, not the list

Hold the tail length fixed and grow the list a hundredfold, and the cost does not move:

```python
import timeit

for n in (20_000, 200_000, 2_000_000):
    setup = f"nums = list(range({n}))"
    base = min(timeit.repeat("nums.append(0); nums.pop()", setup=setup, number=500, repeat=7))
    for label, i in (("i = 10_000", 10_000), ("i = n - 10_000", n - 10_000)):
        stmt = f"del nums[{i}]; nums.append(0)"
        pair = min(timeit.repeat(stmt, setup=setup, number=500, repeat=7))
        print(f"n = {n:<9} {label:<15} {(pair - base) * 1e6 / 500:8.2f} us")
# -> n = 20000     i = 10_000          2.54 us
# -> n = 20000     i = n - 10_000      2.53 us
# -> n = 200000    i = 10_000         48.44 us
# -> n = 200000    i = n - 10_000      2.56 us
# -> n = 2000000   i = 10_000        752.76 us
# -> n = 2000000   i = n - 10_000      2.56 us
```

Ten thousand elements from the end costs 2.56 µs whether the list holds twenty thousand or two
million; index 10,000 costs 2.54 µs on the first and 752.76 µs on the last. Written as a
complexity, the operation is O(n − i) — linear in what sits to the right of the deletion point,
and completely indifferent to what sits to the left. Deleting the first element is not a separate
rule; it is this one at `i = 0`, where the tail is the whole list.

The bottom-left figure is the one row that does not divide out to the same constant as the rest. It
works out at 0.378 ns per element, half again the figure the smaller tails produced — reruns of
that row put it between 0.32 and 0.38 — and the reason is the tail's size in bytes rather than
anything about `del`:

```python
import timeit

for tail in (1_000, 10_000, 100_000, 1_000_000, 4_000_000):
    n = tail + 10_000
    i = n - tail - 1
    setup = f"nums = list(range({n}))"
    base = min(timeit.repeat("nums.append(0); nums.pop()", setup=setup, number=200, repeat=7))
    pair = min(timeit.repeat(f"del nums[{i}]; nums.append(0)",
                             setup=setup, number=200, repeat=7))
    ns = (pair - base) * 1e9 / 200
    print(f"tail {tail:>9}  ({tail * 8 / 1024**2:7.2f} MiB)  {ns:11.1f} ns   {ns / tail:.3f} ns each")
# -> tail      1000  (   0.01 MiB)        267.9 ns   0.268 ns each
# -> tail     10000  (   0.08 MiB)       2559.2 ns   0.256 ns each
# -> tail    100000  (   0.76 MiB)      25461.2 ns   0.255 ns each
# -> tail   1000000  (   7.63 MiB)     255335.6 ns   0.255 ns each
# -> tail   4000000  (  30.52 MiB)    1410505.6 ns   0.353 ns each
```

Flat to within a few percent across four orders of magnitude of tail length, and dearer only on the
bottom row, where the tail has outgrown the caches and the move starts waiting on main memory. That
row is the least stable figure in this section — reruns put it between 0.31 and 0.48 ns per element,
always above whatever the shorter tails held in the same run — and it is still linear: the
right-hand column is a constant with an upward drift, not a growth term. Carry a quarter of a
nanosecond as the working number for tails that fit in cache, and remember the constant gets worse,
never better, as they stop fitting.

### Draining from the front is quadratic

`pop(0)` in a loop is the single most common way this cost is paid by accident. Each call shifts
what remains, so emptying a queue from the front is n calls whose costs sum to n²/2 pointer moves.

```python
import timeit

stmt = "queue = list(range(n))\nwhile queue:\n    queue.pop(0)"
prev = None
for n in (10_000, 20_000, 40_000, 80_000):
    t = min(timeit.repeat(stmt, f"n = {n}", number=5, repeat=9)) / 5 * 1000
    growth = "-" if prev is None else f"x{t / prev:.2f}"
    print(f"n = {n:<8}{t:9.2f} ms   {growth:>6}   {t * 1e6 / (n * n / 2):6.3f} ns per move")
    prev = t
# -> n = 10000        3.98 ms        -    0.080 ns per move
# -> n = 20000       25.35 ms    x6.36    0.127 ns per move
# -> n = 40000      151.28 ms    x5.97    0.189 ns per move
# -> n = 80000      662.64 ms    x4.38    0.207 ns per move
```

Eight times the input for 166 times the work in that run. Pure quadratic growth would predict 64
times, and every excess over 64 is in the last column: normalising by the move count leaves a
per-move cost that climbs as the working set grows, exactly the cache effect the previous table
isolated. Reruns put the total anywhere from 105x to 170x and the per-doubling factors between 3.4
and 7.5, never once approaching the 2 that a linear drain would give. The whole column sits below
the 0.255 ns `del` charges for the same relocation, because `pop` issues the move for less — a gap
the `del`-against-`pop` timings below measure directly. Chapter 1 section 8 traced this same curve
at other sizes, with a drain from the back running beside it as the linear control.

At n = 1,000 that loop takes 0.06 ms, so a test suite built on small inputs measures nothing and
complains about nothing. **Being a bulk memory move is exactly what makes this hard to catch: a
fraction of a nanosecond per element buys enough headroom that the loop stays comfortable through
two or three doublings, and then the squared term arrives all at once.** Between 10,000 and 80,000
elements — three doublings — the same loop went from unnoticeable to two-thirds of a second.
Chapter 2 section 3 arrives at the identical warning from the other side, by building a list from
the front rather than draining one.

### An index that does not exist

Here the mirror breaks. Chapter 2 section 3 measured `insert` clamping silently at both ends, and
deletion does no such thing: an index outside the current length raises. The reason is what the
index means. `insert` names a gap, and a list of length `n` has `n + 1` of them, so a request past
the end still has somewhere to land. Deletion names an *element*, and there are only `n` of those.

```python
prices = [10, 20, 30, 40]
for attempt in ("del prices[4]", "del prices[-5]", "prices.pop(4)", "prices.pop(-5)"):
    try:
        exec(attempt)
    except IndexError as e:
        print(f"{attempt:<18} IndexError: {e}")
# -> del prices[4]      IndexError: list assignment index out of range
# -> del prices[-5]     IndexError: list assignment index out of range
# -> prices.pop(4)      IndexError: pop index out of range
# -> prices.pop(-5)     IndexError: pop index out of range
```

The two spellings raise the same class with different wording — section 2 read that wording on the
empty list, where `del` falls back to a complaint about assignment although nothing was assigned —
and the difference is the first hint that they are not the same code path inside the interpreter. A
float index is a `TypeError` from both, again worded differently (`list indices must be integers or
slices, not float` for `del`, `'float' object cannot be interpreted as an integer` for `pop`), and
an index too large for the C integer that holds it gives `del` an `IndexError` reading `cannot fit
'int' into an index-sized integer` while `pop` raises `OverflowError: Python int too large to
convert to C ssize_t`. `sys.maxsize` is the last value that still fits, so both spellings answer it
with their ordinary out-of-range message and `sys.maxsize + 1` is where the two part company.

### A negative index

A negative index is resolved once, against the length at the moment of the call, and then treated as
a position like any other — so the price follows the position it lands on, not the sign it was
written with.

```python
import timeit

n = 200_000
setup = f"nums = list(range({n}))"
for name in ("del nums[-1]", "del nums[-2]", "del nums[-1000]",
             "del nums[-100_000]", "del nums[-200_000]", "del nums[0]"):
    t = min(timeit.repeat(f"{name}; nums.append(0)", setup=setup, number=2000, repeat=9))
    print(f"{name:<22}{t * 1e9 / 2000:11.1f} ns")
# -> del nums[-1]                 11.9 ns
# -> del nums[-2]                 11.6 ns
# -> del nums[-1000]             280.2 ns
# -> del nums[-100_000]        27785.3 ns
# -> del nums[-200_000]        61185.4 ns
# -> del nums[0]               61665.1 ns
```

`del nums[-1]` moves nothing and is the cheapest deletion available; `del nums[-1000]` moves 999
elements for 0.280 ns each; and the last two rows are one figure measured twice, because on a list
of this length they name the same slot. They landed 2% to 18% apart across runs and in both orders,
which is this harness's scatter at a tail that size rather than a cost of counting from the right.
**A negative index is a position, not a direction.**

### `del` or `pop`

They are not interchangeable in shape. `del` is a statement, so it evaluates to nothing and cannot
appear where a value is expected — `job = del queue[0]` is a `SyntaxError`, not a runtime error.
`pop` is an ordinary method call, so it is an expression and its result can be bound, passed, or
discarded. That is the whole of the difference at the language level, and it decides which one reads
better: use `pop` when the removed element is the point, and `del` when the removal is.

```python
queue = ["render-4471", "backup-nightly", "index-rebuild"]
running = queue.pop(0)          # the value is the point
print(running, queue)           # -> render-4471 ['backup-nightly', 'index-rebuild']

del queue[0]                    # the removal is the point
print(queue)                    # -> ['index-rebuild']
```

Section 1 watched a removal drop its reference and leave the object's own count to decide the rest,
and choosing between these two spellings is a choice about that count: `del` offers the element to
nobody, so one that nothing else names is freed on the spot, while `pop` hands it back and keeps it
alive as long as you hold what came out.

```python
class Frame:
    def __init__(self, tag): self.tag = tag
    def __del__(self): print(f"[{self.tag} freed]")


frames = [Frame("A"), Frame("B")]
del frames[0]                   # -> [A freed]   the slot held the only reference
held = frames.pop(0)            # nothing printed - `held` refers to it now
print(len(frames), held.tag)    # -> 0 B
# -> [B freed]                  printed at shutdown, when `held` finally goes away
```

On a list of large objects that is the difference between the memory coming back at the removal and
coming back whenever the name you bound it to expires.

Watch the target, too. `del queue[0]` and `del queue` are one statement pointed at different things,
as section 1 spelled out: the second removes the *name*, leaving the object for anything else that
still holds it.

```python
queue = ["render-4471"]
alias = queue
del queue
print("queue" in dir())         # -> False
print(alias)                    # -> ['render-4471']
```

The two do not cost the same either, and the ordering flips with size. `del nums[0]` compiles to
three instructions and `nums.pop(0)` to five, so on a short list `del` wins on interpreter overhead
— and on anything longer the bulk move dominates and `pop` wins, by a factor that reruns kept
between 1.4x and 3.6x:

```python
import timeit

for n in (10, 100, 1_000, 10_000, 100_000):
    setup = f"nums = list(range({n}))"
    d = min(timeit.repeat("del nums[0]; nums.append(0)",
                          setup=setup, number=2000, repeat=15)) * 1e9 / 2000
    p = min(timeit.repeat("nums.pop(0); nums.append(0)",
                          setup=setup, number=2000, repeat=15)) * 1e9 / 2000
    print(f"n = {n:<9} del {d:10.1f} ns   pop {p:10.1f} ns   {d / p:5.2f}x")
# -> n = 10        del       13.3 ns   pop       14.9 ns    0.89x
# -> n = 100       del       37.0 ns   pop       22.9 ns    1.62x
# -> n = 1000      del      276.7 ns   pop       90.8 ns    3.05x
# -> n = 10000     del     2564.5 ns   pop      769.4 ns    3.33x
# -> n = 100000    del    26925.4 ns   pop    14825.3 ns    1.82x
```

Both columns are linear in the tail; the gap is a constant factor in how the move is issued, and it
survives every harness it was measured in. It is still not a reason to choose between them: a
constant factor on an operation you should not be repeating is the wrong thing to optimise, and the
next subsection is the fix that matters. Write whichever of the two says what you mean.

### When both ends are the work

If elements genuinely have to leave from the front, the answer is a different container rather than
a cleverer call. `collections.deque` removes at either end in constant time, having no single
contiguous run of storage to close up.

```python
import timeit
from collections import deque

n = 200_000
env = {"d": deque(range(n)), "l": list(range(n))}
for name, stmt in (("deque  popleft + appendleft", "d.popleft(); d.appendleft(0)"),
                   ("list   del l[0] + insert", "del l[0]; l.insert(0, 0)"),
                   ("deque  del d[100_000] + insert", "del d[100_000]; d.insert(100_000, 0)"),
                   ("list   del l[100_000] + insert", "del l[100_000]; l.insert(100_000, 0)")):
    t = min(timeit.repeat(stmt, globals=env, number=2000, repeat=7))
    print(f"{name:<32}{t * 1e6 / 2000:11.3f} us")
# -> deque  popleft + appendleft           0.014 us
# -> list   del l[0] + insert            136.870 us
# -> deque  del d[100_000] + insert      189.389 us
# -> list   del l[100_000] + insert       75.916 us
```

The first row sits at the edge of what that loop count resolves; timed on its own with 100,000
iterations the pair comes out at 14.0 ns, which puts the front ratio at about 9,800x in that run and
between 7,000x and 10,000x across reruns. The exact multiplier is not the point: the front is
constant on a deque and linear on a list, so the gap widens with every element added.

**What you give up is the middle**, and the last two rows are the trade in miniature: the deque was
the slower of the two in every run, usually by about 2.4x and never by less than 1.3x. Both
containers are linear in the middle, so that gap stays a constant factor — but reaching the position
at all means walking a chain of blocks rather than jumping to it, which chapter 1 section 10 prices
on plain indexing, where the same walk costs thousands of times a list subscript. Slicing is refused
outright and each element carries a little more memory. Reach for a deque when the ends are the
whole story and no index ever lands in the middle.

---

## 4. Removing by value

Sections 2 and 3 both start from a position. `pop()` needs no argument because the position is
implied, and `del nums[i]` needs `i` spelled out. Often you do not have `i`. You have a sensor
reading that turned out to be a dropout marker, a cancelled job, a colour the palette no longer
allows — you have a *value*, and no idea where in the list it currently sits.

`remove` is the method for that case. It is the only deletion in this chapter that has to find its
own target, and that search is the whole subject of this section.

### A search, then a deletion

```python
temps = [18, 21, 19, 21, 20]
print(temps.remove(21))   # -> None
print(temps)              # -> [18, 19, 21, 20]
print(len(temps))         # -> 4
```

`remove` walks the list from index 0 until it meets an element equal to its argument, then deletes
at that position exactly as section 3's `del` does: everything to the right slides one slot left,
and the length drops by one. The `None` is the in-place convention from chapter 1, section 9 — the
list you already have is the one that changed.

**`nums.remove(v)` is `del nums[nums.index(v)]` written as a single call: a linear search to find
the position, followed by a linear shift to close the gap.** That sentence is the whole method, and
you should be able to produce it without looking anything up, because every cost below falls out of
it.

Two consequences of "walks from index 0" are visible immediately. The search stops at the first
match, so duplicates further along are untouched; and the elements themselves are never copied, only
their addresses moved, so an object that was in the list before is the same object afterwards. The
inventory counts below sit above the window of integers CPython shares, measured in chapter 1,
section 2, so the identity check is a question that could have gone either way.

```python
stock = [418, 902, 517, 902, 640]
last = stock[4]
print(stock.index(902))     # -> 1
stock.remove(902)
print(stock)                # -> [418, 517, 902, 640]
print(stock[3] is last)     # -> True
print(stock.count(902))     # -> 1
```

Chapter 2 had nothing to match this. To insert you always knew *where*, because you chose; section 6
of that chapter was the single case where an insertion had to search first, and it could halve its
way to the answer because the list was sorted. `remove` has no such luxury. An unsorted list gives a
search no structure to exploit, so it starts at the front and keeps going.

### The search is the expensive half

Take a 100,000-element list whose value at every slot is its own index, so naming a value and naming
a position pick out the same element, and remove four of them two ways: once by value, once by the
index you already know. Each call is paired with an `insert` that puts the element back, so both
rows do the identical delete-and-restore work and the list is unchanged at the end of every
iteration.

```python
import timeit

def per_call(stmt, setup, repeat=25):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)                       # about 4 ms per repeat
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

n = 100_000
setup = f"nums = list(range({n}))"
for i in (0, 25_000, 50_000, 75_000):
    by_value = per_call(f"nums.remove({i}); nums.insert({i}, {i})", setup)
    by_index = per_call(f"del nums[{i}]; nums.insert({i}, {i})", setup)
    print(f"{i:>6}  by value {by_value:9.1f} ns   by index {by_index:9.1f} ns   {by_value / by_index:6.2f}x")
# ->      0  by value   39007.1 ns   by index   52930.8 ns     0.74x
# ->  25000  by value  164935.4 ns   by index   39712.1 ns     4.15x
# ->  50000  by value  290416.7 ns   by index   26512.5 ns    10.95x
# ->  75000  by value  419195.8 ns   by index   13358.5 ns    31.38x
```

The two columns run in opposite directions. Told the position, the cost *falls* as the target moves
right, because the tail that has to shift keeps getting shorter — that is section 3's result. Told
only the value, the cost *rises* on the same inputs, against a shrinking shift. The rise can only be
the search, and by index 75,000 the by-value call costs thirty-one times the by-index one.

The first row is the control: with the target at index 0 there is no searching to do, and the
by-value column is not the more expensive one. The 13,900 ns separating the two columns there works
out at 0.14 ns for each of the 100,000 elements moved, and that per-element figure stayed between
0.13 and 0.16 on lists from 25,000 to 400,000 elements, so the gap is set by the size of the block
move and not by `i` — which means it shrinks as `i` grows, while the by-value column climbs. It is
the gap between two spellings reaching the same block move, which is section 3's business, and it is
not what that climb is made of.

Measure the search on its own with `index`, which does the scan and stops:

```python
import timeit

def per_call(stmt, setup, repeat=25):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

setup = "nums = list(range(20_000))"
for i in (0, 5_000, 10_000, 19_999):
    ns = per_call(f"nums.index({i})", setup)
    print(f"{i:>6} {ns:10.1f} ns   {(ns / i if i else 0):.3f} ns per element scanned")
# ->      0       10.2 ns   0.000 ns per element scanned
# ->   5000    27750.0 ns   5.550 ns per element scanned
# ->  10000    55269.8 ns   5.527 ns per element scanned
# ->  19999   110535.4 ns   5.527 ns per element scanned
```

Flat: 5.53 nanoseconds per element examined, whatever the distance. The same harness applied to
`insert`'s shift on this machine gives 0.281 nanoseconds per element moved, reproducing chapter 2,
section 3's constant. **Comparing an element costs about twenty times what relocating one costs**,
because a comparison is a call into the element's own type while a shift is a single block move at C
speed. So in `remove(v)`'s two phases — `i + 1` comparisons then `n − i − 1` pointer moves — the
comparisons dominate unless the value is very near the front. Written as a complexity the operation
is O(n) either way, and that notation hides the more useful fact that its two halves are priced
twenty-fold apart.

### A value that is not there raises

There is no "remove it if present" spelling. An absent value is a `ValueError`, and an empty list is
just the case where every value is absent.

```python
readings = [12.5, -1, 13.0, -1, 12.8]
try:
    readings.remove(99)
except ValueError as e:
    print(type(e).__name__, str(e))       # -> ValueError list.remove(x): x not in list
try:
    [].remove(-1)
except ValueError as e:
    print(str(e))                         # -> list.remove(x): x not in list
```

The message names the method and not the value, so it will not tell you *which* removal failed in a
loop that removes several things. Two guards are available, and they are not equally priced:

```python
import timeit

def per_call(stmt, setup, repeat=25):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

setup = "nums = list(range(20_000))"
check = "if {v} in nums: nums.remove({v})"
catch = "try:\n    nums.remove({v})\nexcept ValueError:\n    pass"

print("absent      ", f"{per_call(check.format(v=-1), setup):9.1f} ns",
                      f"{per_call(catch.format(v=-1), setup):9.1f} ns")
restore = "\nnums.insert(10_000, 10_000)"
print("present     ", f"{per_call(check.format(v=10_000) + restore, setup):9.1f} ns",
                      f"{per_call(catch.format(v=10_000) + restore, setup):9.1f} ns")
# -> absent        107326.1 ns  108240.6 ns
# -> present       111686.4 ns   58027.9 ns
```

When the value is absent the two cost the same: both scan the whole list once and find nothing, and
raising and catching the exception is lost in the noise of 20,000 comparisons. When the value is
present, checking first costs roughly twice as much, because `in` scans to the match and `remove`
then scans to the same match all over again. **Asking whether a value is there and then removing it
searches the list twice; catching the failure searches it once.** Choose the check when absence is
the common case and you want the code to read as a condition; choose the `try` when the value is
usually present, or when the list is long enough for a second scan to matter.

### Equal, not the same object

`remove` deletes the first element that *compares equal* to its argument. Equal is not the same
question as identical, and it is not the same question as same-type either.

```python
temps = [21.0, 20, 21, 20.0]
temps.remove(21)
print(temps)                                   # -> [20, 21, 20.0]
print([type(t).__name__ for t in temps])       # -> ['int', 'int', 'float']

flags = [0, False, 2, 1, True]
flags.remove(False)
print(flags)                                   # -> [False, 2, 1, True]
```

The float `21.0` went, because it came first and `21.0 == 21`. The integer `0` went, because
`0 == False`. If you were picturing `remove` as hunting for the object you handed it, both results
are surprises.

The reverse case is sharper. Put the very object you are about to remove *second* in the list,
behind an equal but distinct one:

```python
z = 0
target = z + 300
counts = [z + 300, target]
print(counts[0] is target, counts[0] == target)   # -> False True
counts.remove(target)
print(len(counts), counts[0] is target)           # -> 1 True
```

`remove(target)` deleted the element that was not `target` and left `target` behind. For a list of
small integers you would never see this: chapter 1, section 2 measured CPython's shared window at
exactly the 262 values from -5 to 256, so below 257 the equal object *is* the same object and the
two questions cannot disagree. That coincidence is why `is` versus `==` needs the deliberate
treatment chapter 1, section 9 gives it, and why the value above is 300.

Identity does still get asked, just not as the criterion. Chapter 1, section 8 establishes the rule
for every scanning operation: a container asks `is` first and only falls back to `==`, so an element
always matches itself regardless of what its `__eq__` would say. `remove` obeys it, and a float NaN
makes it audible, since NaN is unequal even to itself:

```python
n = float("nan")
readings = [18.5, n, 19.0]
try:
    readings.remove(float("nan"))
except ValueError as e:
    print(str(e))          # -> list.remove(x): x not in list
readings.remove(n)
print(readings)            # -> [18.5, 19.0]
```

A different NaN cannot be found by equality and is not found at all. The same NaN is found on
identity, before equality is ever consulted.

### `count` and `index`: the same scan without the deletion

These two are `remove`'s search, exposed on their own, and their costs follow from where each one is
allowed to stop.

```python
import timeit

def per_call(stmt, setup, repeat=25):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

setup = "nums = list(range(20_000))"
for i in (0, 5_000, 19_999):
    print(f"{i:>6}   in {per_call(f'{i} in nums', setup):9.1f} ns"
          f"   index {per_call(f'nums.index({i})', setup):9.1f} ns"
          f"   count {per_call(f'nums.count({i})', setup):9.1f} ns")
# ->      0   in       6.3 ns   index      10.2 ns   count  110241.7 ns
# ->   5000   in   26946.2 ns   index   27761.7 ns   count  110435.4 ns
# ->  19999   in  107479.2 ns   index  110412.5 ns   count  110285.4 ns
```

`in` and `index` stop at the first match, so their cost is set by where that match is — O(i), down
to 6.3 ns for an `in` answered at index 0, where nothing is left but the call itself. `count` is
flat at 110 microseconds across all three rows, because **`count` has no early exit: it must reach
the end to know it has seen every occurrence, so it is O(n) even when the value is at the front.**
A `count` used only to ask "is it there" therefore pays the worst case every time; `in` is the
operation for that question.

`index` also raises on absence, with its own message — `list.index(x): x not in list` — and takes
optional bounds that narrow the scan without building a slice. `nums.index(19_999, 19_000)` examines
the 1,000 elements from index 19,000 onwards and costs 5,522 ns against 110,602 ns for the unbounded
call: a factor of twenty for a search a twentieth as long, which is the 5.53 ns per element arriving
from a third direction. `count` takes no such bounds.

### Removing every occurrence, one call at a time

`remove` deletes one element. The obvious way to delete all copies of a value is to call it until it
runs out, and it is worth seeing both of the things that go wrong.

The first is a correctness problem. Walking the list with a `for` loop and removing as you go
produces answers that look right on some inputs and are wrong on others:

```python
readings = [12, -1, -1, 14, -1, 15]
for r in readings:
    if r == -1:
        readings.remove(r)
print(readings)          # -> [12, 14, -1, 15]

alternating = [0, -1, 2, -1, 4, -1, 6, -1]
for r in alternating:
    if r == -1:
        alternating.remove(r)
print(alternating)       # -> [0, 2, 4, 6]
```

The second list came out clean; the first kept a `-1`. Whether the bug shows depends on how the
targets happen to be arranged, which is the worst property a bug can have. There is a second defect
hiding in the same two lines: `readings.remove(r)` removes the *first* element equal to `r`, which
is not necessarily the one the loop is standing on. Section 7 takes the mechanism apart.

The second problem is cost, and it survives the fix. A loop that keeps removing until the value is
gone is correct:

```python
import time

def drain(nums, v):
    while v in nums:
        nums.remove(v)
    return nums

def timed(source):
    nums = source.copy()
    t = time.perf_counter()
    drain(nums, -1)
    return (time.perf_counter() - t) * 1000

previous = None
for n in (5_000, 10_000, 20_000, 40_000):
    source = [-1 if i % 3 == 0 else i for i in range(n)]
    best = min(timed(source) for _ in range(9))
    growth = "" if previous is None else f"{best / previous:5.2f}x"
    print(f"n = {n:>6}   dropped {source.count(-1):>6}   {best:9.1f} ms   {growth}")
    previous = best
# -> n =   5000   dropped   1667        31.5 ms
# -> n =  10000   dropped   3334       166.4 ms    5.29x
# -> n =  20000   dropped   6667       589.2 ms    3.54x
# -> n =  40000   dropped  13334      2569.1 ms    4.36x
```

Each doubling of `n` multiplies the cost by roughly four. The individual factors wobble around that
because the runs are short and the machine is shared; the eightfold increase in `n` across the table
multiplied the cost by 82. Counting the work instead of timing it removes the wobble entirely:

```python
def audit(n):
    nums = [-1 if i % 3 == 0 else i for i in range(n)]
    compared = moved = removals = 0
    while -1 in nums:
        i = nums.index(-1)
        compared += 2 * (i + 1)          # the `in` scan and the `remove` scan
        moved += len(nums) - i - 1
        nums.remove(-1)
        removals += 1
    return removals, compared, moved

for n in (6_000, 12_000, 24_000, 48_000):
    removals, compared, moved = audit(n)
    print(f"n = {n:>5}  removals {removals:>6}  compared {compared:>11}"
          f"  moved {moved:>10}   compared / n**2 = {compared / n ** 2:.4f}")
# -> n =  6000  removals   2000  compared     8000000  moved    6001000   compared / n**2 = 0.2222
# -> n = 12000  removals   4000  compared    32000000  moved   24002000   compared / n**2 = 0.2222
# -> n = 24000  removals   8000  compared   128000000  moved   96004000   compared / n**2 = 0.2222
# -> n = 48000  removals  16000  compared   512000000  moved  384008000   compared / n**2 = 0.2222
```

Exactly 2n²/9 comparisons across the removals, at every size, with no rounding left over, and the
arithmetic says why. The j-th marker starts at index 3j, and by the time the loop reaches it j
markers have already gone, so it is found at index 2j: the scans get *longer* as the list gets
shorter, because each one restarts at index 0 and re-examines every element the last one rejected.
Summing the 2(2j + 1) comparisons a removal costs over the n/3 markers gives 2n²/9 exactly. Removing
16,000 markers from a 48,000-element list examined half a billion elements to do it. The pointer
moves are quadratic too, but at 0.281 ns against 5.53 ns they are the cheaper half of a bill that is
quadratic on both sides.

**Repeated `remove` is quadratic because the search restarts at index 0 every time, and no amount
of care with the loop changes that.** The way out is not a better loop over the same list. It is to
stop deleting and start building: one pass that copies the values you are keeping into a new list
costs one scan and no shifting at all. Section 5 is where that is written and measured.

---

## 5. Removing many at once

Sections 3 and 4 priced a single element leaving a single position, and each one of those cost a
shift of everything to its right. Removing `k` elements one call at a time therefore costs `k`
shifts. Python will do the whole job in one, and this is the part of deletion where it is genuinely
good.

### A run of adjacent elements

`del` accepts a slice wherever it accepts an index.

```python
readings = [12, 15, 19, 22, 25, 31, 30]
del readings[2:5]
print(readings)          # -> [12, 15, 31, 30]
```

Three elements leave together, and the two survivors to their right move left once, by three
positions each. The same operation spelled as an assignment:

```python
readings = [12, 15, 19, 22, 25, 31, 30]
readings[2:5] = []
print(readings)          # -> [12, 15, 31, 30]
```

Chapter 2 section 4 built insertion out of assignment to an empty slice, `nums[i:i] = items`. This
is that statement with its two halves exchanged: a non-empty target, an empty replacement. Chapter 1
section 5 named the two spellings equivalent in a line; what this section adds is the price tag. The
bound-clamping established there carries over unchanged, so a slice deletion never raises for being
too ambitious — a target past the end simply names fewer elements, or none:

```python
prices = [3, 5, 8]
del prices[1:99]
print(prices)            # -> [3]
del prices[99:200]       # names nothing, so removes nothing
print(prices)            # -> [3]
```

The two spellings cost the same, because they reach the same C-level routine:

```python
import timeit

setup = "q = list(range(200_000))"
for stmt in ("del q[50_000:70_000]", "q[50_000:70_000] = []"):
    t = min(timeit.repeat(stmt, setup, number=1, repeat=200))
    print(f"{stmt:<26}{t * 1e6:8.1f} us")

# -> del q[50_000:70_000]          98.3 us
# -> q[50_000:70_000] = []        100.0 us
```

Write `del`. It says removal; the assignment says replacement and then hands you an empty
replacement to squint at.

### One shift instead of twenty thousand

This is the measurement to keep from this section. Deleting a run of 20,000 elements from a list of
200,000, once as a slice and once an element at a time:

```python
import time

n = 200_000
k = 20_000


def bulk(i):
    q = list(range(n))
    t = time.perf_counter()
    del q[i:i + k]
    return (time.perf_counter() - t) * 1e6, q


def one_at_a_time(i):
    q = list(range(n))
    t = time.perf_counter()
    for _ in range(k):
        del q[i]
    return (time.perf_counter() - t) * 1e6, q


for i in (0, n // 2):
    a = min(bulk(i)[0] for _ in range(20))
    b = min(one_at_a_time(i)[0] for _ in range(3))
    print(f'i={i:>6}  bulk {a:7.1f} us   one at a time {b:10.1f} us   ratio {b / a:6.0f}x')
print(bulk(0)[1] == one_at_a_time(0)[1])

# -> i=     0  bulk   103.9 us   one at a time  1631064.0 us   ratio  15702x
# -> i=100000  bulk    94.2 us   one at a time   775879.6 us   ratio   8239x
# -> True
```

Identical results, thousands of times apart — across five reruns the ratios ran from 5,200x to
15,700x and never left the thousands. The arithmetic is the same shape as chapter 2 section 4's: the
loop moves about `k · (n - i)` pointers and the slice deletion moves about `n - i`, so the ratio is
roughly `k`, plus the twenty thousand interpreted statements the loop pays and the slice does not.
**A loop whose body is `del`,
`pop(i)`, or `remove` is a loop that reshifts the tail on every pass; if the positions are adjacent,
one slice deletion replaces the whole loop.**

### A step other than one

An extended slice — step anything but 1 — can be deleted too, and it names scattered positions
rather than a run:

```python
temps = [12, 15, 19, 22, 25, 31]
del temps[::2]
print(temps)             # -> [15, 22, 31]

temps = [12, 15, 19, 22, 25, 31]
del temps[1::2]
print(temps)             # -> [12, 19, 25]

temps = [12, 15, 19, 22, 25, 31]
del temps[::-2]          # same positions, named from the back
print(temps)             # -> [12, 19, 25]
```

Chapter 2 section 4 established that extended slice *assignment* cannot resize a list: the number of
values you supply must equal the number of positions the slice names, exactly, or you get a
`ValueError`. Deletion has no such rule, and this is the asymmetry worth holding onto: you are not
supplying anything, so there is no count to disagree with.

```python
temps = [12, 15, 19, 22, 25, 31]
try:
    temps[::2] = []
except ValueError as e:
    print(e)             # -> attempt to assign sequence of size 0 to extended slice of size 3
del temps[::2]           # the deletion the assignment could not express
print(temps)             # -> [15, 22, 31]
```

So `del nums[::2]` is not `nums[::2] = []` in disguise. The assignment form is a scatter-write that
never changes a length; the deletion form is the only way an extended slice ever resizes a list.
What it costs is a run of small shifts rather than one big one — every surviving element between two
removed positions slides left, so the whole tail is still touched, just in pieces:

```python
import time

n = 1_000_000


def scattered(q):
    del q[::100]


def front(q):
    del q[:10_000]


def back(q):
    del q[-10_000:]


def half_scattered(q):
    del q[::2]


def half_front(q):
    del q[:500_000]


cases = {"del q[::100]": scattered, "del q[:10_000]": front, "del q[-10_000:]": back,
         "del q[::2]": half_scattered, "del q[:500_000]": half_front}
best = dict.fromkeys(cases, float('inf'))
for _ in range(15):                            # round robin, so no case runs only after another
    for label, fn in cases.items():
        q = list(range(n))
        t = time.perf_counter()
        fn(q)
        best[label] = min(best[label], (time.perf_counter() - t) * 1e6)

for label, t in best.items():
    print(f"{label:<18}{t:9.1f} us")

# -> del q[::100]          461.3 us
# -> del q[:10_000]        276.2 us
# -> del q[-10_000:]        45.0 us
# -> del q[::2]           3403.8 us
# -> del q[:500_000]      2496.1 us
```

The first three rows remove 10,000 elements each; the last two remove 500,000. The scattered form is
the slower of its group in every run, by about 1.7 times at the smaller count and about 1.4 times at
the larger — real, and nothing like the thousand-fold gap a loop would open. The round robin is what
holds those numbers still: run each case to completion in turn instead and `del q[:500_000]`, going
last, pays for the temporaries `del q[::2]` just churned — it reads about 1.4 times slower there,
enough on its own to make that pair look tied. The row that stands apart is `del q[-10_000:]`, five
to six times cheaper than the same count taken from the front: removing from the back shifts nothing
at all, which is section 2's point arriving in slice form.

### Removing everything that fails a test

When the elements to remove are picked out by a condition rather than by position, stop reaching for
deletion. **Build a new list containing what survives.** A comprehension does it in one linear pass,
and it is the idiomatic Python for "remove all elements satisfying a condition". Chapter 1 section 6
already named it the default; what the measurement below adds is how the gap grows.

```python
readings = [18, -1, 21, -1, 19]     # -1 marks a dropped sample
kept = [r for r in readings if r != -1]
print(kept)              # -> [18, 21, 19]
```

Against the two deletion loops that produce the same answer — `remove` called until the value is
gone, and `del` at each offending index — over a list where one reading in ten is a dropout:

```python
import time

DROP = -1


def make(n):
    return [DROP if i % 10 == 0 else i for i in range(n)]


def by_comprehension(src):
    q = src.copy()
    t = time.perf_counter()
    kept = [r for r in q if r != DROP]
    return (time.perf_counter() - t) * 1e3, kept


def by_repeated_remove(src):
    q = src.copy()
    t = time.perf_counter()
    while DROP in q:
        q.remove(DROP)
    return (time.perf_counter() - t) * 1e3, q


def by_repeated_del(src):
    q = src.copy()
    t = time.perf_counter()
    for i in range(len(q) - 1, -1, -1):
        if q[i] == DROP:
            del q[i]
    return (time.perf_counter() - t) * 1e3, q


warm = make(1_000)
for fn in (by_comprehension, by_repeated_remove, by_repeated_del):
    fn(warm)                                   # warm up before anything is timed

for n in (5_000, 10_000, 20_000, 40_000):
    src = make(n)
    a, ka = min((by_comprehension(src) for _ in range(30)), key=lambda p: p[0])
    b, kb = min((by_repeated_remove(src) for _ in range(3)), key=lambda p: p[0])
    c, kc = min((by_repeated_del(src) for _ in range(3)), key=lambda p: p[0])
    print(f"n={n:<6} comprehension {a:6.3f} ms   remove {b:8.2f} ms ({b / a:6.0f}x)"
          f"   del {c:7.2f} ms ({c / a:5.0f}x)  {ka == kb == kc}")

# -> n=5000   comprehension  0.055 ms   remove    11.93 ms (   216x)   del    0.38 ms (    7x)  True
# -> n=10000  comprehension  0.110 ms   remove    47.60 ms (   434x)   del    1.37 ms (   13x)  True
# -> n=20000  comprehension  0.223 ms   remove   190.60 ms (   853x)   del    5.23 ms (   23x)  True
# -> n=40000  comprehension  0.445 ms   remove  1019.70 ms (  2289x)   del   20.67 ms (   46x)  True
```

The warm-up line is not decoration. Without it the first timed case pays for machinery the later
ones find already built: on two runs in three with those three lines deleted, the comprehension's
5,000-element reading came out three times too slow, making the column *fall* between `n = 5000` and
`n = 10000` and inverting the trend the table exists to show.

Read down the columns, not across. The comprehension's column doubles when `n` doubles — 2.00, 2.03
and 2.00 times here, and between 1.90 and 2.09 across five runs — because it is one linear pass that
shifts nothing. The other two grow much faster than their input, because each removal shifts a tail
and there are `n / 10` of them; that is the quadratic, and it is why the two ratio columns climb
instead of holding steady. Across five runs the `remove` ratio grew by between ten and twelve times
between `n = 5000` and `n = 40000`, and the `del` ratio by between six and ten. Those two spreads
are the honest picture: the direction never once reversed, and no single step of either column is
worth quoting — one run put the `del` column at twice its usual for `n = 20000`, which moves a step
and not the trend. Read the trend, not the step.

`remove` is the worse of the two by a wide margin, and the loop around it is why: `DROP in q` scans
for the value and `q.remove(DROP)` scans for it again before the shift — the three linear passes per
removal that section 4 counts exactly and chapter 1 section 8 prices. The `del` loop already knows
the index, so it pays the shift alone. Both are the wrong shape.

The reverse index order in `by_repeated_del` is deliberate: deleting from the back leaves every
index still to be visited smaller than the one just removed, so none go stale. Section 7 is what
happens when you walk forwards instead.

### `filter`, and when it reads better

`filter(predicate, iterable)` expresses the same idea, lazily, in the sense chapter 1 section 6
described: it yields survivors on demand and builds no list until you ask for one.

```python
readings = [18, -1, 21, -1, 19]
print(list(filter(lambda r: r != -1, readings)))     # -> [18, 21, 19]
print(list(filter(None, [3, 0, 5, 0, 0, 8])))        # -> [3, 5, 8]
```

Those are the two cases worth distinguishing. With a predicate you had to write, `filter` is slower
than the comprehension, because the comprehension inlines its test while `filter` makes a real call
per element:

```python
import timeit

setup = ("readings = [-1 if i % 10 == 0 else i for i in range(100_000)]\n"
         "def live(r):\n    return r != -1\n")
cases = {
    "comprehension":        "kept = [r for r in readings if r != -1]",
    "filter + lambda":      "kept = list(filter(lambda r: r != -1, readings))",
    "filter + def":         "kept = list(filter(live, readings))",
    "comprehension + call": "kept = [r for r in readings if live(r)]",
}
times = {k: min(timeit.repeat(v, setup, number=20, repeat=7)) / 20 for k, v in cases.items()}
fastest = min(times.values())
for k, t in sorted(times.items(), key=lambda kv: kv[1]):
    print(f"{k:<22}{t * 1e3:7.3f} ms   {t / fastest:5.2f}x")

# -> comprehension           1.043 ms    1.00x
# -> filter + lambda         2.060 ms    1.97x
# -> filter + def            2.118 ms    2.03x
# -> comprehension + call    2.145 ms    2.06x
```

The plain comprehension won every one of eight runs, never by less than 1.9 times over whichever of
the other three came second. Those three landed within a few per cent of each other and swapped
places freely between runs, which is the finding worth taking: **what you are paying for is the call
per element, not the choice between `filter` and a comprehension.** A comprehension that calls a
function is no cheaper than `filter` calling the same function. Chapter 1 section 6 reached that
verdict for `map`, and `filter` differs only in how often the escape is available: a `map` and a
comprehension over the same named function both make the call, so they tie, while a predicate is
usually an expression the comprehension can inline and `filter` cannot.

`filter(None, ...)` is the exception, and it is the case where `filter` reads better as well as runs
faster. It means "keep the truthy ones", with no predicate to write and no call to make:

```python
import timeit

setup = "counts = [i % 5 for i in range(100_000)]"
cases = {"comprehension": "kept = [c for c in counts if c]",
         "filter(None, ...)": "kept = list(filter(None, counts))"}
times = {k: min(timeit.repeat(v, setup, number=20, repeat=7)) / 20 for k, v in cases.items()}
fastest = min(times.values())
for k, t in sorted(times.items(), key=lambda kv: kv[1]):
    print(f"{k:<20}{t * 1e3:7.3f} ms   {t / fastest:5.2f}x")

# -> filter(None, ...)     0.488 ms    1.00x
# -> comprehension         0.789 ms    1.62x
```

`filter(None, ...)` won every run, by about 1.6 times once the machine had settled and never by less
than 1.2 — the only arrangement in this section where `filter` is ahead. Reach for it when the test
is plain truthiness, and for `filter` generally when the predicate already exists under a good name
and naming it is what makes the line readable. Write the comprehension everywhere else.

### The second list, and what it costs

The comprehension allocates. That is the honest trade, and it is worth measuring rather than
worrying about. Filtering one dropout in ten out of a million readings:

```python
import tracemalloc

n = 1_000_000
DROP = -1
checksum = sum(i for i in range(n) if i % 10)      # an int, so the heap stays clean


def peak_of(fn):
    readings = [DROP if i % 10 == 0 else i for i in range(n)]
    tracemalloc.start()
    tracemalloc.reset_peak()
    base = tracemalloc.get_traced_memory()[0]
    out = fn(readings)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return (peak - base) / 1024, sum(out) == checksum


def new_list(readings):
    return [r for r in readings if r != DROP]


def publish(readings):
    readings[:] = [r for r in readings if r != DROP]
    return readings


def publish_lazily(readings):
    readings[:] = (r for r in readings if r != DROP)
    return readings


def reverse_del(readings):
    for i in range(len(readings) - 1, -1, -1):
        if readings[i] == DROP:
            del readings[i]
    return readings


for label, fn in (("new list", new_list), ("nums[:] = [comp]", publish),
                  ("nums[:] = (genexp)", publish_lazily), ("reverse del loop", reverse_del)):
    kib, ok = peak_of(fn)
    print(f"{label:<22}peak +{kib:9.1f} KiB   {ok}")

# -> new list              peak +  13852.9 KiB   True
# -> nums[:] = [comp]      peak +  15146.4 KiB   True
# -> nums[:] = (genexp)    peak +  15146.6 KiB   True
# -> reverse del loop      peak +      0.1 KiB   True
```

The 900,000 surviving pointers are 7031.2 KiB, and `sys.getsizeof` on the finished list reports
7333.9 KiB — the extra 302.7 KiB is the spare capacity chapter 1 section 7 describes for a list
grown without a known final size.

The first row is nearly twice that, and it is the one figure in this section that moved between
sittings: earlier runs on this same interpreter reported 7333.9 KiB, the finished block exactly, and
later ones reported 13852.9 KiB without a line of the code changing. The difference is neither noise
nor random. It is 6519.0 KiB, and that is a number you can go and find:

```python
import sys

kept = []
steps = []
for i in range(900_000):
    kept.append(i)
    cap = (sys.getsizeof(kept) - 56) // 8
    if not steps or cap != steps[-1]:
        steps.append(cap)

print(steps[-2:])                                   # -> [834428, 938736]
print(steps[-2] * 8 / 1024, sys.getsizeof(kept) / 1024)
# -> 6518.96875 7333.9296875
```

834,428 slots is the capacity the list held one growth step before its last, and 6519.0 plus 7333.9
is 13852.9 to the decimal. **A comprehension's last resize either stretches the block where it
stands, in which case the peak is the finished list, or it has to move it, in which case both blocks
are live for an instant and the peak is their sum.** Which one you get depends on the state of the
process's heap, not on anything you wrote, so budget for the larger figure: building a list of
unknown final length can momentarily cost about twice the list.

The publishing forms are unmoved by all this, at 15146.4 KiB in every run, because that number is
larger than either outcome above: it is 7333.9 for the comprehension plus 7812.5, eight bytes for
each of the million references the assignment displaces. And the generator expression saves nothing
at all — slice assignment consumes its right-hand side into a list before it touches the target, so
the temporary gets built either way.

A bulk deletion is not free of allocation either. It holds the outgoing references in a
temporary while it closes the gap, at eight bytes each, with a small fixed buffer covering the first
eight:

```python
import tracemalloc


def cost_of_removing(k):
    q = list(range(1_000_000))
    tracemalloc.start()
    tracemalloc.reset_peak()
    base = tracemalloc.get_traced_memory()[0]
    del q[:k]
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak - base


for k in (8, 9, 100, 100_000):
    print(f"del q[:{k:<7}] peak +{cost_of_removing(k):>8} bytes")

# -> del q[:8      ] peak +       0 bytes
# -> del q[:9      ] peak +      72 bytes
# -> del q[:100    ] peak +     800 bytes
# -> del q[:100000 ] peak +  800000 bytes
```

So the comprehension costs a pointer per *surviving* element — briefly up to two, when its last
resize has to move — and the bulk deletion costs one per *removed* element. Neither is free, and
only the element-at-a-time deletion loop is, which is the single argument in its favour. It is also
the loop the table earlier in this section shows falling further behind the comprehension at every
size, so the constant space is bought with quadratic time.

**The second list is a cost to price, not a rule to obey.** The figures above are here so you can
say what the allocation is, not so you will avoid it: a linear pass that allocates beats a quadratic
one that does not, at every size measured here, and the memory it wants is a copy of the survivors
rather than a copy of the process. Two things turn that cost into a prohibition, and both arrive
from outside the code you are writing. A caller may fix the length — you are free to rewrite the
contents, but the object has to stay the size it arrived, which leaves no shorter list to hand back
and no second one to build; that is section 6. Or the extra space may be budgeted rather than merely
paid for — a list already too large to duplicate, or a bound requiring the extra to stay constant
however long the input grows, which is stricter than either and a subject of its own in chapter 5.
Until one of those is on the table, building the survivors is the answer to "remove everything that
fails a test", and this subsection is the price of it, not an argument against it.

### Putting the result back into the original object

A comprehension gives you a new list. Rebinding the name to it leaves every other name pointing at
the unfiltered original, which chapter 1 section 9 is entirely about:

```python
readings = [18, -1, 21, -1, 19]
alias = readings
readings = [r for r in readings if r != -1]
print(readings, alias)   # -> [18, 21, 19] [18, -1, 21, -1, 19]

readings = [18, -1, 21, -1, 19]
alias = readings
readings[:] = [r for r in readings if r != -1]
print(readings, alias)   # -> [18, 21, 19] [18, 21, 19]
```

`nums[:] = [...]` overwrites the object's contents in place, so callers, aliases, and anything
holding the list see the filtered result. It is the linear-pass filter with the in-place semantics
of a deletion, and it costs one extra copy of the survivors:

```python
import timeit

setup = "readings = [-1 if i % 10 == 0 else i for i in range(200_000)]"
for stmt in ("kept = [r for r in readings if r != -1]",
             "readings[:] = [r for r in readings if r != -1]"):
    t = min(timeit.repeat(stmt, setup, number=1, repeat=200))
    print(f"{stmt:<50}{t * 1e3:7.3f} ms")

# -> kept = [r for r in readings if r != -1]             1.954 ms
# -> readings[:] = [r for r in readings if r != -1]      2.425 ms
```

About a quarter more here, for the 180,000 surviving pointers moved from the temporary into the
original block. The ratio is the wrong thing to memorize: across reruns the first row wandered
between 1.33 and 1.95 ms while the gap between the rows stayed between 0.46 and 0.50 ms every time.
It is an extra copy of the survivors, and it costs what one costs. Pay it when the object's identity
matters and skip it when it does not — but decide, rather than picking a spelling and finding out
later which one you chose.

---

## 6. Deleting when the length cannot change

Every form so far reaches its result by making the list shorter. `pop` hands back a value and drops
the length by one, `del` closes the gap it opens, a slice deletion closes a wider one, and each of
them leaves you holding a list whose `len()` is the count of what survived. That falling length is
deletion's ordinary shape, and it is why deletion runs insertion backwards.

Some callers do not permit it. They hand you a list, they keep their own name bound to that same
object, and the terms are that you may rewrite the contents but must not change the length. `del`,
`pop`, `remove` and slice deletion go off the table together, because every one of them is a length
change. The word "delete" then has to mean something other than "the list gets shorter", because
there is no shorter list to hand back.

What is left is the one length-preserving family chapter 2 section 5 isolated: indexed assignment,
and the equal-length slice assignment built out of it. Every edit still open to you writes over a
position that already exists, which is why the result has to be described rather than delivered —
the list on its own can no longer say where the answer ends.

### A count, and a prefix

The convention such an interface uses is the one chapter 2 section 5 already put on the table from
the other direction: **the meaningful elements are the first `count` of them, and `count` travels
separately from the list.** Everything from index `count` onward is explicitly not the caller's
business — not "should be blanked", not "should be left as you found it", but outside the answer
altogether.

```python
readings = [21, 19, 24, 18, 22, 17, 20, 23]
count = 5

print(len(readings), count)     # -> 8 5
print(readings[:count])         # -> [21, 19, 24, 18, 22]
print(readings[count:])         # -> [17, 20, 23]
```

The first line is the whole point. `len()` says eight and the answer has five elements in it, and
neither number is wrong — they are answers to different questions. `len()` reports how many
positions you can index, and the list maintains that number for itself. `count` reports how many of
those positions mean anything, which no list has ever tracked: chapter 1 section 7 settled that
length equals occupancy for a list built from its own contents and only for such a list, and this
one was not. The second line is the answer. The third is debris.

Chapter 2 section 5 met the same pair with the arrow pointing the other way: a preallocated buffer
where `count` started at 0 and rose as you filled positions, so the count marked how far the data
had got. Here the buffer arrives already full of data and the count marks how far the *surviving*
data reaches. Same two numbers, same relationship, opposite direction of travel — and the same
consequence, that nothing in the list will maintain the count for you and nothing will complain
when it is wrong.

The trivial case shows how little "deleting" now costs. Dropping the last meaningful element is
`count - 1` and no write at all. The value is still sitting in its slot, and it has stopped being
part of the answer purely because the count no longer reaches it. **Nothing is freed and nothing
moves: dropping the last element of the answer costs one decrement.** Nor does the slot want
clearing afterwards. Blanking it would be a write nobody is entitled to read, and the position is
available again regardless: a deletion of this kind returns no memory, because it never held any
of its own.

### Why an interface asks for this

Two reasons, and both of them are about the object rather than the values in it.

The first is that no memory is claimed. Building the survivors into a new list is a perfectly good
thing to do, and section 5 priced that second list as one option among several. Here the same
figure is the reason the interface exists at all, so it is worth seeing as bytes:

```python
import sys

readings = [i % 7 for i in range(200_000)]
before = sys.getsizeof(readings)

kept = [x for x in readings if x != 0]
print(len(kept), sys.getsizeof(kept))    # -> 171428 1443576
```

171,428 pointers at 8 bytes each is 1,371,424 bytes, and the 56-byte header the list carries
whatever its length brings that to 1,371,480. The block is holding 1,443,576, so 72,096 bytes —
9,012 slots — are spare capacity collected on the way up, chapter 1 section 7's over-allocation
turning up as a memory bill. In round numbers, 1.4 MB of fresh pointers, aimed at elements that
were already in the process.

Now the same volume of rewriting, done to slots that already exist:

```python
for i in range(len(readings)):
    readings[i] = readings[i] + 1

print(len(readings), sys.getsizeof(readings) == before)   # -> 200000 True
```

Two hundred thousand writes, and `getsizeof` reports the same block it reported before the first
one. A write to a position that already exists asks the allocator for nothing, which is the
length-preserving property chapter 2 section 5 established, doing real work here. **That is the
trade the interface is buying: the result costs one integer beside the data, instead of a second
copy of it.**

The second reason is that the caller keeps the object it already had. A name bound inside a
function is local to it, so rebuilding and returning gives the caller something new to hold, while
writing into the slots is visible through every name already pointing at that list — chapter 1
section 9 in one comparison:

```python
def scale_rebuilt(buf):
    buf = [x * 2 for x in buf]      # a local name, rebound
    return buf

def scale_in_place(buf):
    for i in range(len(buf)):
        buf[i] = buf[i] * 2

shelf = [3, 5, 8]
held = shelf

print(scale_rebuilt(shelf), held)   # -> [6, 10, 16] [3, 5, 8]
scale_in_place(shelf)
print(held, held is shelf)          # -> [6, 10, 16] True
```

Rebuilding is not broken; it is answering a different question. If the caller's contract says "the
list you were given will be read back when you return", then a fresh list is an answer delivered to
an address nobody is watching. The count-and-prefix convention exists precisely so that a result
can be delivered through an object the caller already holds, without the caller having to rebind
anything.

### Checking a result of this shape

The convention changes how you verify, and getting this wrong is how correct work gets reported as
broken. Three results, all of them right:

```python
answers = [
    ([21, 19, 24, 18, 22, 17, 20, 23], 5),   # tail left exactly as it was found
    ([21, 19, 24, 18, 22, 0, 0, 0], 5),      # tail overwritten with zeros
    ([21, 19, 24, 18, 22], 5),               # list shortened as well
]
for buf, count in answers:
    print(len(buf), count, buf[:count])
# -> 8 5 [21, 19, 24, 18, 22]
# -> 8 5 [21, 19, 24, 18, 22]
# -> 5 5 [21, 19, 24, 18, 22]
```

Three different buffers, two different lengths, one answer. **Two solutions may leave completely
different garbage past the count and both be correct, because the garbage was never part of what
either of them promised.** A check that compares whole lists therefore rejects correct work:

```python
expected = [21, 19, 24, 18, 22]
for buf, count in answers:
    print(buf == expected, count == len(expected) and buf[:count] == expected)
# -> False True
# -> False True
# -> True True
```

The left column is wrong twice, and it is wrong in the direction that wastes an afternoon: a
passing result reported as a failure, with a diff that points at values the specification said not
to look at. The right column is the check, and it is worth writing down as one predicate — the
count first, the prefix second, and nothing else ever. The prefix clause has two forms, and you do
not get to pick between them by taste: an interface that promised an order is checked position by
position, and one that promised only which elements survive is checked as a multiset, so the
predicate has to be told which promise it is enforcing.

```python
def matches(buf, count, expected, *, ordered):
    if not 0 <= count <= len(buf) or count != len(expected):
        return False
    prefix = buf[:count]
    return prefix == expected if ordered else sorted(prefix) == sorted(expected)

expected = [21, 19, 24, 18, 22]
print(matches([21, 19, 24, 18, 22, 17, 20, 23], 5, expected, ordered=True))   # -> True
print(matches([21, 19, 24, 18, 22, 0, 0, 0], 5, expected, ordered=True))      # -> True
print(matches([21, 19, 24, 18, 22], 5, expected, ordered=True))               # -> True
print(matches([21, 19, 24, 18, 22, 17, 20, 23], 6, expected, ordered=True))   # -> False
print(matches([19, 21, 24, 18, 22, 0, 0, 0], 5, expected, ordered=True))      # -> False
print(matches([19, 21, 24, 18, 22, 0, 0, 0], 5, expected, ordered=False))     # -> True
```

The count of 6 fails `count != len(expected)`: it claims a sixth element the answer does not have,
and no promise about ordering rescues it. The last two rows are one buffer read against the two
promises — the right five values with the first two swapped, rejected where position was part of
the contract and accepted where only membership was. Which verdict is correct is a fact about the
interface, not about the buffer. Leaving `ordered` out does not avoid that decision, it makes it
silently, and an unordered contract checked position by position rejects correct work exactly the
way the left column did.

The leading `0 <= count <= len(buf)` did no work in any of those rows, and it is in there
deliberately, because it is the one condition a slice will not report for you:

```python
short = [21, 19]
print(short[:5], len(short[:5]))   # -> [21, 19] 2
```

A count of 5 over a two-element buffer is a broken result, and slicing answers it by clamping
rather than raising — chapter 1 section 5's rule. Checking the shape before the values makes such
a result fail as an impossible count, which is what it is, rather than as a values mismatch, which
sends you looking in the wrong place.

### Reading one

The skill on the consuming side is small and worth doing once explicitly. You are handed a list and
a count; you produce the meaningful part and work from that alone.

```python
readings = [21, 19, 24, 18, 22, 17, 20, 23]

def summarise(buf, count):
    window = buf[:count]
    return len(window), sum(window), max(window)

print(summarise(readings, 5))                # -> (5, 104, 24)
print(summarise(readings, len(readings)))    # -> (8, 164, 24)
```

Same list, same function, and the second call is the bug this convention invites: reading `len()`
where the count belonged folds three stale values into the total and reports eight readings where
five were taken. Nothing raised, nothing looked odd, the maximum did not even move, and 164 is a
perfectly plausible total.

Two details on the reading itself. An empty answer is ordinary — `buf[:0]` is `[]`, and it is the
aggregation that has an opinion about it, not the slice:

```python
print(readings[:0], sum(readings[:0]))   # -> [] 0
try:
    max(readings[:0])
except ValueError as e:
    print(e)                             # -> max() iterable argument is empty
```

And `buf[:count]` copies, as everything about slicing in chapter 1 section 5 says it must. The copy
is exactly sized rather than over-allocated, which makes the bill easy to read:

```python
import sys, itertools

buf = list(range(200_000))
count = 150_000

print(sys.getsizeof(buf[:count]))                     # -> 1200056
print(sys.getsizeof(itertools.islice(buf, count)))    # -> 72
print(sum(buf[:count]) == sum(itertools.islice(buf, count)))   # -> True
```

1,200,056 bytes is 150,000 pointers and the 56-byte header, with no slack at all. That is fine for
inspecting a result and wrong inside anything hot, because it duplicates the very prefix the
convention went to the trouble of not duplicating. When you only need to *read* the prefix, walk it
with `range(count)` or wrap it in `itertools.islice(buf, count)` — the islice object is 72 bytes
whatever the count, since it holds a position rather than the elements.

### Where this section stops

Reading a counted prefix is the whole of the consuming side, and it is deliberately the inverse of
the producing side. Producing one is what each of the two problems in `arrays101/ch03/` asks for,
and each borrows this convention without borrowing the restriction that motivated it. What each of
them fixes is the output contract: you return a count, the first `count` positions of the list you
were handed have to hold the answer, and nothing past the count is ever read. The length is left
open above the count — a list as long as it arrived and a list that ends up shorter are both
acceptable. **What is pinned down is the object, not its size: the caller keeps the list it passed
in and reads the front of that same list when you return, which is the difference `scale_rebuilt`
and `scale_in_place` draw above.** How each problem gets the answer into those positions is the
exercise rather than the reading.

Section 7 takes the other hazard, the one that appears when the length *is* free to move: what
happens to a walk through a list that is being shortened underneath it.

---

## 7. Deleting while iterating

Every deletion does two things at once: it shortens the list, and it slides every element after the
gap one slot to the left. A `for` loop over that same list is holding a position it computed before
either of those happened. Chapter 2 section 7 is the mirror of this section — there the list grew
under the loop and elements got seen twice or the loop never ended. Here it shrinks, and elements
get missed.

### The loop that removes half of what it should

Drop every reading above 20 from a list of temperatures, the obvious way:

```python
readings = [18, 21, 21, 19]
for r in readings:
    if r > 20:
        readings.remove(r)
print(readings)          # -> [18, 21, 19]
```

One of the two 21s survived. Make every element qualify and exactly half of them survive:

```python
readings = [22, 22, 22, 22]
for r in readings:
    if r > 20:
        readings.remove(r)
print(readings)          # -> [22, 22]
```

Nothing raised. A list will not object to being resized while a loop is walking it — chapter 1
section 6 has the contrast with `dict` and `set`, which do object — so this arrives as a plausible
wrong answer rather than an error, and a test whose input happens to have no two removable elements
adjacent will pass.

### The cursor does not move when the elements do

Chapter 1 section 6 has the protocol: a list iterator is the live list plus one integer position,
which `next` reads at and then increments. Nothing in that arrangement is a snapshot, and nothing
in it is notified of anything. CPython will show you the integer:

```python
readings = [18, 21, 21, 19]
it = iter(readings)
print(next(it), next(it), it.__reduce__()[2])   # -> 18 21 2
readings.remove(21)                             # the tail slides left; the position does not
print(readings, it.__reduce__()[2])             # -> [18, 21, 19] 2
print(next(it))                                 # -> 19   the second 21 was never offered
```

After the removal the surviving 21 sits at index 1, which the cursor has already passed, and
index 2 now holds 19. **A loop misses exactly one element for every deletion made at an index the
cursor has already gone past** — so one `remove` per iteration skips one element per iteration,
which is why a list of identical values loses precisely half.

That rule prices the whole family. Cut two elements out from behind the cursor and two go unseen;
shrink the list from the other end and the finish line walks toward the cursor until they meet:

```python
readings = [10, 20, 30, 40, 50, 60]
seen = []
for r in readings:
    seen.append(r)
    if r == 30:
        del readings[0:2]        # two elements gone from behind the cursor
print(seen)                      # -> [10, 20, 30, 60]

readings = [18, 21, 19, 25, 30]
seen = []
for r in readings:
    seen.append(r)
    readings.pop()               # the end comes to meet the position
print(seen, readings)            # -> [18, 21, 19] [18, 21]
```

In the first, 40 and 50 were never offered. In the second, five elements produced three iterations,
because the length fell to 2 while the position climbed to 3. Neither raised anything.
`enumerate` and `zip` change none of this: over a list they wrap that same cursor and inherit its
position.

### The index loop people write instead

Told that `for` is the problem, the usual next attempt is to drive the walk by index. It is the same
bug with the cursor spelled out by hand, because `i += 1` runs whether or not something came out:

```python
readings = [18, 21, 21, 19]
i = 0
while i < len(readings):
    if readings[i] > 20:
        readings.pop(i)
    i += 1
print(readings)          # -> [18, 21, 19]
```

The repair is one word: advance only when you kept the element, because after a deletion the next
element is already at `i`.

```python
readings = [18, 21, 21, 19]
i = 0
while i < len(readings):
    if readings[i] > 20:
        readings.pop(i)
    else:
        i += 1
print(readings)          # -> [18, 19]
```

That is correct, and it is fragile in the way an invariant maintained by hand always is: the next
person to add a branch to the loop body has to rediscover why one path skips the increment.
`range(len(readings))` is worse than either, because the bound is computed once from a length that
is about to be wrong, so the loop both skips and runs off the end:

```python
readings = [18, 21, 21, 19]
seen = []
try:
    for i in range(len(readings)):
        seen.append(readings[i])
        if readings[i] > 20:
            del readings[i]
except IndexError as e:
    print(seen, readings, e)
# -> [18, 21, 19] [18, 21, 19] list index out of range
```

One 21 in `seen` where the input had two is the skip; the fourth step is the overrun.

### The two approaches that work, priced for deletion

Chapter 1 section 6 established both of them for iteration in general: build a new list with a
comprehension, which is the default, or walk a copy and mutate the original when the change has to
land on the caller's object as it happens. What this chapter adds is the bill from the deletion
side, which is where the choice between them is actually decided.

The comprehension deletes nothing. It decides what to keep and puts those elements somewhere else,
and there is no cursor into the list being written because that list did not exist when the walk
started:

```python
readings = [18, 21, 21, 19]
kept = [r for r in readings if r <= 20]
print(kept)              # -> [18, 19]
```

**This is the default, and the case for it is not only that it is correct — it is the one shape in
this section that is not quadratic.** One pass, nothing shifted, and every write is an append at
the end, which is amortized O(1) (chapter 1 section 7). Section 5 measures it against a deletion
loop that produces the same answer, and section 5 also has the caller-visible spelling: when the
change has to land on their object rather than on a new one, assign into the full slice,
`readings[:] = [r for r in readings if r <= 20]`. The right-hand side is fully built before anything
is stored, so no other holder ever sees a half-filtered list.

The copy form keeps the deletions on the original by handing the cursor a list that nothing is
shifting:

```python
readings = [18, 21, 21, 19]
for r in readings.copy():
    if r > 20:
        readings.remove(r)
print(readings)          # -> [18, 19]
```

`readings[:]`, `list(readings)` and `tuple(readings)` all do the same job. What they cost is a
second block the size of the list: 8 bytes a slot, so a copy of 200,000 elements is 1,600,056
bytes by `sys.getsizeof` — those 200,000 pointers plus a 56-byte header — and `tracemalloc` puts
the peak growth of making one at 1,600,000 bytes for the block alone. In time it is one more linear
pass before the loop starts, and that surcharge is flat: it does not care what the body of the loop
does, while the walk itself cares about very little else.

```python
import timeit

setup = "readings = list(range(100_000))"
for label, body in (("bare", "pass"), ("one compare", "if r > 20:\n        pass")):
    direct = min(timeit.repeat(f"for r in readings:\n    {body}",
                               setup, number=20, repeat=9)) / 20
    copied = min(timeit.repeat(f"for r in readings.copy():\n    {body}",
                               setup, number=20, repeat=9)) / 20
    print(f"{label:<12}{direct * 1e3:7.3f} ms   {copied * 1e3:7.3f} ms   "
          f"+{(copied - direct) * 1e3:6.3f} ms")

# -> bare          0.240 ms     0.412 ms   + 0.172 ms
# -> one compare   0.473 ms     0.650 ms   + 0.177 ms
```

One comparison in the body roughly doubles the walk and moves the surcharge by hundredths of a
millisecond. Across reruns the surcharge stayed between 0.15 and 0.19 ms whatever the body was, and
it is the same quantity chapter 1 section 6 reports for 100,000 elements, at about 0.19 ms. The
number worth carrying between the two chapters is that surcharge, not the walk time printed beside
it: the walk time is a fact about the work the loop was doing, and not about the copy. A copy stores
each pointer and bumps one reference count per element at C speed with no interpreted step in
between, so it buys you at most one more pass of the cheapest kind there is. It is affordable.

**The copy is not what makes this shape expensive. The deletions are.** Every `remove` is a scan for
the value plus a shift of everything after it, so a loop that takes out `m` elements pays `m` linear
passes: section 4 prices the scan, and section 5 puts a loop of them against the comprehension and
watches the quadratic open up. What the copy adds to that bill is the lost position. Walking a
snapshot throws away the index of every element it hands you, so `remove` has to find each one
again, where the hand-driven `while` gives `pop` an index and pays the shift alone. That is also
what chapter 1 section 6's third form buys — deleting by descending index, correct for the same
reason the copy is and quadratic like both of these, but paying only the shift and never the scan.
Move every removable element to the front, so each scan ends immediately, and the gap between the
copy and the `while` closes:

```python
import timeit

wh = ("i = 0\nwhile i < len(readings):\n    if not readings[i]:\n"
      "        readings.pop(i)\n    else:\n        i += 1")
cr = "for r in readings.copy():\n    if not r:\n        readings.remove(r)"
for label, src in (("spread out", "[i % 4 for i in range(20_000)]"),
                   ("front-loaded", "[0] * 5_000 + [1] * 15_000")):
    a = min(timeit.repeat("readings = src.copy()\n" + wh, f"src = {src}", number=1, repeat=25))
    b = min(timeit.repeat("readings = src.copy()\n" + cr, f"src = {src}", number=1, repeat=25))
    print(f"{label:<14}{a * 1e3:8.3f} ms   {b * 1e3:9.3f} ms   {b / a:6.1f}x")

# -> spread out       4.841 ms     199.523 ms     41.2x
# -> front-loaded     9.730 ms       7.897 ms      0.8x
```

In the second row both shapes delete at index 0 five thousand times, so they shift the same volume
of pointers — and with the search reduced to nothing the copy comes out slightly ahead of the loop
that never needed it. Across reruns the first row stayed between 40x and 45x and the second between
0.8x and 0.9x.

Reach for the copy when the mutations genuinely have to land on the original object as they happen,
and for the hand-driven `while` when you also need to avoid the second block of memory. Everywhere
else the comprehension is simpler and faster.

### The list may not be yours alone

Deletion through a parameter is deletion from the caller's list, because the parameter is another
name for the same object — chapter 1 section 9 in full:

```python
def drop_negatives(values):
    for v in values.copy():
        if v < 0:
            values.remove(v)

log = [3, -1, 4, -1]
archive = log
drop_negatives(log)
print(log, archive, archive is log)      # -> [3, 4] [3, 4] True
```

Chapter 2 section 7 lists what a co-owner may be holding besides the object itself, and deletion is
harder on every item of that list than insertion was: an index that an insertion merely misdirected
can now be out of range, a recorded length is now larger than the list, and a loop running somewhere
up the call stack you cannot see from here starts skipping. Copy before you filter and return the
copy, or mutate deliberately, say so in the docstring, and publish the finished result in one
statement.

### An index recorded before a deletion names the wrong element

Strip the loop away and the same bug remains. An index names a position, not an element (chapter 2
section 7), and a deletion changes what that position holds:

```python
prices = [10, 20, 30, 40]
i = prices.index(30)
print(i)                 # -> 2
del prices[0]            # an earlier entry is voided
print(prices)            # -> [20, 30, 40]
print(prices[i])         # -> 40   not 30
```

A deletion at position `p` leaves every index below `p` correct and makes every index at or above
`p` point one element too late — the exact opposite of chapter 2 section 7, where an insertion
made them point one too early. The indexes that were near the end fall off it, so the same
mistake sometimes raises and sometimes does not:

```python
prices = [10, 20, 30, 40]
i = prices.index(40)
del prices[0]
del prices[0]
print(prices[i])         # -> IndexError: list index out of range
```

Positions kept in another structure go stale in the same way, and are harder to notice because the
structure still looks well formed:

```python
names = ['ana', 'bo', 'cy', 'di']
where = {n: i for i, n in enumerate(names)}
names.remove('bo')
print(where)                                      # -> {'ana': 0, 'bo': 1, 'cy': 2, 'di': 3}
print(names[where['ana']], names[where['cy']])    # -> ana di
print(where['di'] < len(names))                   # -> False
```

Only `ana`, the one entry that sat before the removal, still points at itself. `cy` now names `di`,
and `di` names a position the list no longer has. Rebuild the index after the deletion, or key by
something that a deletion cannot move.

### Five questions before you delete from a list you were handed

Chapter 2 section 7's four questions, in the same order, and a fifth that only deletion raises.

1. **Is it mine to change?** A list that arrived as a parameter belongs to the caller. If the
   contract does not say you may edit it, build and return a new one.
2. **May its length change?** Some contracts fix it, and then `remove`, `pop`, `del` and every slice
   deletion are off the table, and the only edit left is a write into a slot that already exists.
   Section 6 draws that line.
3. **Is anything iterating it?** Including your own loop over the list you are deleting from, and
   including a loop further up the call stack that you cannot see.
4. **Does anyone else hold a reference?** Another name, another object's attribute, a container it
   was put into, a length recorded earlier, or an index computed before you started.
5. **Do I need the removed values?** `pop` hands the element back; `remove`, `del` and `clear`
   discard it. A comprehension keeps the survivors and drops the rest on the floor, so when both
   halves matter, name both halves:

```python
readings = [18, 21, 21, 19]
kept = [r for r in readings if r <= 20]
dropped = [r for r in readings if r > 20]
print(kept, dropped)     # -> [18, 19] [21, 21]
```

If question 1, 3 or 4 is uncertain, build a new list and return it. That answer is correct under all
three, and it is the cheaper one besides. Question 2 is the exception, and it is the one both of
this chapter's problems hand you.

---

## 8. Drills

Ten snippets, and the procedure from chapter 2 section 8 unchanged: predict in writing, then run,
then read the key — in that order and no other. A prediction has to be exact, down to the whole
list, the length, and the exception type with its message text, because "it gets shorter" and "it
raises something" cannot be wrong in the way that teaches you anything. Every output in the key
was produced by running the snippet on CPython 3.14.4. Drill 7 reports this machine's timings, so
there you predict which columns move with `n` and by what factor, never the digits.

### The drills

**Drill 1.**

```python
queue = ["render-4471", "backup-nightly", "index-rebuild", "thumbs-2210"]

last = queue.pop()
print(last, queue)                    # ?

first = queue.pop(0)
print(first, queue)                   # ?

print(queue.pop(-1), queue)           # ?

queue = queue.pop()
print(queue, type(queue).__name__)    # ?
```

**Drill 2.**

```python
temps = [12, 15, 19]
print(temps.pop(1), temps)      # ?

try:
    temps.pop(7)
except IndexError as e:
    print(type(e).__name__, e)  # ?

empty = []
try:
    empty.pop()
except IndexError as e:
    print(type(e).__name__, e)  # ?

try:
    empty.pop(0)
except IndexError as e:
    print(type(e).__name__, e)  # ?

del empty[0:9]
print(empty)                    # ?
```

**Drill 3.**

```python
prices = [199, 249, 99, 349]

taken = prices.pop(2)
print(taken, prices)      # ?

del prices[0]
print(prices)             # ?

try:
    compile("kept = del prices[0]", "<drill>", "exec")
except SyntaxError:
    print("SyntaxError")  # ?

slots = [21, 19, 23, 20]
slots[1] = None
print(slots, len(slots))  # ?
del slots[1]
print(slots, len(slots))  # ?

readings = [1, 2, 3]
alias = readings
del readings
print(alias)              # ?

try:
    readings
except NameError as e:
    print(type(e).__name__, e)   # ?
```

**Drill 4.**

```python
rgb = [255, 128, 64, 32, 16]

print(rgb.pop(-2), rgb)          # ?

del rgb[-1]
print(rgb)                       # ?

try:
    del rgb[9]
except IndexError as e:
    print(type(e).__name__, e)   # ?

del rgb[9:]
print(rgb)                       # ?

del rgb[-99:-98]
print(rgb)                       # ?

try:
    rgb.pop(-9)
except IndexError as e:
    print(type(e).__name__, e)   # ?
```

**Drill 5.**

```python
sensors = [21, 19, 21, 23, 21]

print(sensors.remove(21), sensors)   # ?

sensors.remove(21)
print(sensors)                       # ?

try:
    sensors.remove(99)
except ValueError as e:
    print(type(e).__name__, e)       # ?

flags = [0, 1, 2]
flags.remove(True)
print(flags)                         # ?

mixed = [3, 1.0, 1]
mixed.remove(1)
print(mixed)                         # ?
```

**Drill 6.**

```python
levels = [10, 20, 30, 40, 50, 60]
del levels[1:3]
print(levels)          # ?

del levels[3:1]
print(levels)          # ?

codes = [0, 1, 2, 3, 4, 5, 6]
del codes[::-3]
print(codes)           # ?

picks = [0, 1, 2, 3, 4, 5]
del picks[::2]
print(picks)           # ?

try:
    picks[::2] = []
except ValueError as e:
    print(type(e).__name__, e)   # ?

a = [10, 20, 30, 40]
b = [10, 20, 30, 40]
del a[1:3]
b[1:3] = []
print(a == b, a)       # ?
```

**Drill 7.** Predict the shape, not the digits. For the first line, say which of the two is faster
and by roughly what order of magnitude. For the table, say of each column whether doubling `n`
roughly doubles the time or leaves it flat, and where the middle column sits relative to the
first.

```python
import timeit


def ms(stmt, setup):
    return min(timeit.repeat(stmt, setup, number=1, repeat=15)) * 1000


setup = "data = list(range(200_000))"
bulk = ms("del data[100:2100]", setup)
singles = ms("for _ in range(2000): del data[100]", setup)
print(round(bulk, 4), round(singles, 3))     # ?

for n in (20_000, 40_000, 80_000):
    src = f"data = list(range({n}))"
    front = ms("for _ in range(2000): data.pop(0)", src)
    mid = ms("for _ in range(2000): data.pop(len(data) // 2)", src)
    end = ms("for _ in range(2000): data.pop()", src)
    print(n, round(front, 2), round(mid, 2), round(end, 3))   # ?
```

**Drill 8.**

```python
temps = [21, 40, 40, 19]
for t in temps:
    if t == 40:
        temps.remove(t)
print(temps)     # ?

seen = []
queue = ["a", "b", "c", "d"]
for i, job in enumerate(queue):
    seen.append((i, job))
    if job == "a":
        del queue[0]
print(seen)      # ?
print(queue)     # ?

safe = [21, 40, 40, 19]
for t in safe[:]:
    if t == 40:
        safe.remove(t)
print(safe)      # ?
```

**Drill 9.**

```python
import sys

inventory = ["bolt", "nut", "washer"]
alias = inventory
inventory.clear()
print(inventory, alias)                  # ?

inventory = ["bolt", "nut", "washer"]
alias = inventory
inventory = []
print(inventory, alias)                  # ?

stock = ["bolt", "nut"]
mirror = stock
del stock[:]
print(stock, mirror, stock is mirror)    # ?

print(["bolt"].clear())                  # ?

big = list(range(1000))
before = sys.getsizeof(big)
big.clear()
print(before, sys.getsizeof(big), sys.getsizeof([]))   # ?
```

**Drill 10.**

```python
def keep_positive_inplace(readings):
    readings[:] = [r for r in readings if r >= 0]


def keep_positive_rebind(readings):
    readings = [r for r in readings if r >= 0]


a = [12, -3, 19, -8, 22]
keep_positive_inplace(a)
print(a)              # ?

b = [12, -3, 19, -8, 22]
keep_positive_rebind(b)
print(b)              # ?

c = [12, -3, 19]
view = c
c[:] = [r for r in c if r >= 0]
print(c, view, c is view)     # ?

d = [12, -3, 19]
view = d
d = [r for r in d if r >= 0]
print(d, view, d is view)     # ?
```

### The answer key

**1.** `thumbs-2210 ['render-4471', 'backup-nightly', 'index-rebuild']` /
`render-4471 ['backup-nightly', 'index-rebuild']` / `index-rebuild ['backup-nightly']` /
`backup-nightly str`. `pop` shortens the list and hands back the element it took out — the last
one when called bare, which shifts nothing, and otherwise the one at the index you name, which
slides everything after it one slot left. **`pop` returns the element, not the list, so
`queue = queue.pop()` discards the list and leaves the name bound to a string**: the mirror of
chapter 2 drill 1, where `insert` returned `None`. (Sections 2 and 3.)

**2.** `15 [12, 19]` / `IndexError pop index out of range` / `IndexError pop from empty list` /
`IndexError pop from empty list` / `[]`. An index handed to `pop` has to name a slot that exists,
so it is bounds-checked on every call, and an empty list gets its own wording even when you pass
an explicit `0`. The last line is the contrast: a slice bound is clamped rather than checked, so
deleting `[0:9]` from an empty list removes nothing and says nothing. (Sections 2, 3 and 5.)

**3.** `99 [199, 249, 349]` / `[249, 349]` / `SyntaxError` / `[21, None, 23, 20] 4` /
`[21, 23, 20] 3` / `[1, 2, 3]` / `NameError name 'readings' is not defined`. `pop` is a method
call and therefore an expression with a value, while `del` is a statement and has no value at all,
so `kept = del prices[0]` is rejected before it runs. **When the removed element is wanted, that
is `pop`; when it only has to be gone, `del` says exactly that.** The middle pair is section 6 in
four lines — writing `None` into a slot holds the length at 4, and `del` on that slot takes it to
3 — and the last pair is about names rather than lists: `del readings` unbinds the name and leaves
the object alive under `alias`. (Sections 3 and 6; chapter 1 sections 4 and 9.)

**4.** `32 [255, 128, 64, 16]` / `[255, 128, 64]` /
`IndexError list assignment index out of range` / `[255, 128, 64]` / `[255, 128, 64]` /
`IndexError pop index out of range`. Both `pop` and `del` take one index, count a negative one
back from the end, and raise when the result lands outside the list; `del rgb[9]` even reports
itself in the wording of a subscript assignment, since it is resolving a single slot the same way.
Replace the index with a slice and the rule inverts. **An out-of-range index deletion raises; an
out-of-range slice deletion is a no-op that produces no evidence** — which is chapter 2 drill 2
read backwards, where `insert(99, x)` clamped its index while a plain subscript assignment past the
end raised. (Sections 3 and 5; chapter 2 section 3.)

**5.** `None [19, 21, 23, 21]` / `[19, 23, 21]` / `ValueError list.remove(x): x not in list` /
`[0, 2]` / `[3, 1]`. `remove` scans from index 0, deletes the first slot whose element is `==` to
the argument, and returns `None`, so the other 21s survive and the second call is a fresh scan.
Matching is equality, not identity and not type, which is how `True` finds the `1` and `1` finds
the `1.0`; an absent value is a `ValueError` rather than a silent nothing. The cost is a search
plus a shift, and the search is the larger half: on a 100,000-element list this machine measured
`data.remove(5)` at 12.6 µs, `data.remove(50_000)` at 277.6 µs and `data.remove(99_990)` at 545.1
µs. **The price tracks how deep the value sits, not how much has to move afterwards**, because the
shift is one block move at C speed while the search compares elements one at a time. (Section 4;
chapter 1 section 8.)

**6.** `[10, 40, 50, 60]` / `[10, 40, 50, 60]` / `[1, 2, 4, 5]` / `[1, 3, 5]` /
`ValueError attempt to assign sequence of size 0 to extended slice of size 2` / `True [10, 40]`. A
contiguous slice deletion removes the whole span and closes the gap in one move, and an inverted
span selects nothing, so `del levels[3:1]` is a legal no-op. A step selects scattered positions
and deletes each — `codes[::-3]` picks 6, 3 and 0, and the survivors close up in order.
**Extended-slice deletion has no length rule to satisfy, while extended-slice assignment must
supply exactly as many elements as it selected**, because deleting closes the gaps and assigning
has nowhere to put a mismatch. The last pair shows `del a[1:3]` and `b[1:3] = []` are two
spellings of one operation. (Section 5; chapter 1 section 5; chapter 2 section 4.)

**7.** This machine printed `0.0323 113.954`, then `20000 4.06 1.53 0.029` /
`40000 9.6 4.95 0.029` / `80000 19.8 9.93 0.029`. The digits are this machine's; the ratios are the
answer.

Both spellings remove the same 2,000 elements and produce the identical list, and the loop took
about 3,500 times longer — 113.954 ms against 0.0323 ms — a multiplier that repeated runs held in
the low thousands, between roughly 3,000x and 3,900x. **One slice deletion works out the surviving
length once and moves each surviving element at most once; the loop moves the entire tail again on
every iteration.** In the table, the `pop(0)` column climbs with `n` — 4.06, 9.6, 19.8, so each
doubling of `n` roughly doubles the time — because each call shifts everything that is left. The
middle column climbs the same way and holds at about half the front (0.38, 0.52 and 0.50 of it),
since deleting at the midpoint moves only what lies to its right, and half of O(n) is still O(n).
The `pop()` column does not respond to `n` at all — the same 0.029 ms at all three sizes here, and
about 0.03 ms across a fourfold range on any run — because removing the last element shifts
nothing. That flat column is why the helper takes fifteen samples and keeps the smallest: it is
reporting tens of microseconds alongside columns reporting tens of milliseconds, and a thinner
sample lets one scheduling hiccup invert the very shape you are being asked to read.
(Sections 2, 3 and 5; chapter 1 section 8.)

**8.** `[21, 40, 19]` / `[(0, 'a'), (1, 'c'), (2, 'd')]` / `['b', 'c', 'd']` / `[21, 19]`. All the
state an iterator carries is an integer position into the live list, so each step reads whatever
occupies the next slot at that moment (chapter 1 section 6). Delete an element and the tail slides
one place left while the position advances one place right, so whatever moves into the slot you
just left is stepped straight over: the second 40 is never examined, `'b'` never reaches `seen`,
and the loop ends early because the length it checks against has dropped. Chapter 2 section 7 had
a growing list re-reading elements; this is that mechanism run the other way. **Neither direction
raises anything — the loop simply visits the wrong elements and finishes.** The last block
iterates `safe[:]`, a snapshot that nothing mutates, so both 40s are visited and both `remove`
calls find a first match. (Section 7; chapter 1 section 6; chapter 2 section 7.)

**9.** `[] []` / `[] ['bolt', 'nut', 'washer']` / `[] [] True` / `None` / `8056 56 56`. `clear()`
empties the object, so every name bound to it sees an empty list, while rebinding to `[]` builds a
second object and leaves `alias` holding a full one; `del stock[:]` is a third spelling of the
emptying, and identity survives it. `clear` mutates and returns `None`, like the other mutators.
The size readings settle whether emptying is only a length reset: 1,000 slots occupy 8,056 bytes,
and after `clear()` the object is 56 bytes, exactly a fresh empty list, so the buffer is released.
(Section 2; chapter 1 sections 7 and 9.)

**10.** `[12, 19, 22]` / `[12, -3, 19, -8, 22]` / `[12, 19] [12, 19] True` /
`[12, 19] [12, -3, 19] False`. Both functions build the identical filtered list;
`readings[:] = ...` copies it into the existing object, so the caller and every other name see the
change, while plain assignment rebinds a local name and the caller's list is untouched. **The two
lines produce equal lists and differ only in whether anyone else can see the result.** The
in-place form is not free — the replacement list has to exist in full before the old contents can
go. Filtering a 200,000-element list this way peaks, on `tracemalloc`, at 3,224,000 bytes of extra
allocation beyond the list itself: 1,624,000 for the comprehension's result, and 1,600,000 more for
the block that holds the displaced elements until they can be released — 200,000 slots at 8 bytes,
exactly. **In-place is a statement about which object ends up holding the answer, not about how
little memory is in use while it is worked out.** (Section 5; chapter 1 sections 7 and 9; chapter 2
section 4.)

### The readiness checklist

Chapter 1's scoring rule still holds: explanation rather than recognition, out loud, in under a
minute. Each statement names the section that carries it and the drill that tests it.

You should be able to explain, without looking it up, why:

1. `pop()` costs the same at any length while `pop(0)` costs O(n), and exactly what that O(n) is
   spent on. (Sections 2 and 3; drills 1 and 7.)
2. `nums.pop(i)` can appear on the right of an `=` and `del nums[i]` cannot, and which one you
   reach for when the removed value is wanted. (Section 3; drill 3.)
3. `del nums[9]` raises on a short list while `del nums[9:]` is silent, and why that is chapter
   2's clamping rule seen from the other side. (Sections 3 and 5; drill 4.)
4. `remove` deletes exactly one element and which one, why two calls are two full scans, and why
   the search costs more than the shift it triggers. (Section 4; drill 5.)
5. one slice deletion beats a loop of single deletions by three orders of magnitude, and what has
   to be true of the positions before you are allowed to use it. (Section 5; drill 7.)
6. `del nums[::2]` is accepted and `nums[::2] = []` is refused. (Section 5; drill 6.)
7. deleting from a list inside a `for` loop over that same list skips elements and stops early
   without raising, and what iterating `nums[:]` changes. (Section 7; drill 8.)
8. `nums.clear()` and `nums = []` look alike until a second name is involved, and why
   `nums[:] = filtered` and `nums = filtered` split the same way. (Sections 2 and 5; drills 9
   and 10.)
9. `del`, `pop`, `remove` and slice deletion are all unavailable when the length must not change,
   and what that leaves you with. (Section 6; drill 3.)
