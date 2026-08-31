# Chapter 5 — Changing a List in Place

Chapter 1 settled what a list is. Chapters 2, 3 and 4 took the three operations one at a time and
priced them: insert, delete, search. This chapter takes something that is not an operation at all.
**In place is a promise about which object the caller reads the answer out of** — not an algorithm,
not a data structure, and not, on its own, a claim about how much memory you used. It cuts across
all three operations, and it changes what counts as a finished answer.

The promise is looser than the phrase sounds. Two readings of it are in circulation and people use
them interchangeably, and they come apart the moment anything is measured. One is about delivery:
the object you were handed carries the result. The other is about space: whatever you allocate on
the way must not grow with the input. A single statement can satisfy the first exactly while
allocating a second full copy of the list, and `sort` — the method everyone calls in place —
satisfies the second or fails it depending on the data rather than on the method.

That gap is most of the chapter. The first half is about rewrites that need nothing clever, because
what goes into a position is decided by what was already sitting there or by values you have
finished with; those are free, and the only thing to get right is the direction you walk. The second
half is the case where the answer is shorter than the input, the destination has to be worked out
rather than read off, and two indices moving over one list at different speeds buy linear time and
constant space at once. The last section is the argument on the other side, because every technique
here destroys its input, and the input usually belongs to somebody who was not in the conversation.

It leans on chapter 1 rather than repeating it. Aliasing, and what "in place" means to a name, is
chapter 1 section 9; the operation cost table — the price of a copy, the sort's merge buffer, what
`reverse` does and does not allocate — is section 8; and the `tracemalloc` and `timeit` harnesses
every measurement below is cut down from are section 11. Section 10, on reaching for a different
container, is the one piece of chapter 1 this chapter never uses: these problems hand you a list and
read that same list when you return. Chapter 3 section 6 is the one to keep in mind throughout. It
set up the convention that delivers an answer shorter than its input through the caller's own
object, and then stopped deliberately, before saying how the surviving values get there. Section 4
below is where that stop is lifted.

---

**STOP AT THE END OF SECTION 3 IF YOU HAVE NOT SOLVED 27 AND 26.**

**Sections 1, 2 and 3 are safe for anyone. Section 4 onward is not.** Section 4 opens by handing
over the technique behind two problems that are not this chapter's and that you have not solved, and
it names them outright: **27. Remove Element** and **26. Remove Duplicates from Sorted Array**, the
two waiting in `arrays101/ch03/`. It then works the second of them through by name, and sections 5
and 6 build the technique in full. If either of those two is still open, read to the end of section
3, close this file, and go and solve them. Being stuck on them is the exercise this chapter is about
to spend.

Nothing in sections 1 to 3 touches either problem. Those three are also enough on their own for
**1299. Replace Elements with Greatest Element on Right Side**, the first of this chapter's own
three: it wants a direction and a carried variable, which section 3 builds, and nothing from past
the gate. Sections 5 and 6 then finish **283. Move Zeroes** and **905. Sort Array By Parity**
outright, and each of them says so where it is about to.

---

## How to read this

**Run the code.** Every block is executable exactly as written — there are 80 of them, carrying 187
`# -> value` comments — and every one of those comments is a real observed result rather than an
illustration. Open a session next to this document and paste as you go:

```bash
uv run python
```

Some blocks continue the one before them within a section, reusing a function or a variable set up
earlier. Four of them raise an exception on purpose, catch it and print what it said; those are
demonstrations, and the exception is the result being reported.

**Predict before you run.** Section 8 is ten drills and an answer key, and it is the honest test of
whether the rest of the chapter landed. The three subjects it goes after hardest — which object a
statement actually changed, what a list is holding once a rewrite has finished with it, and how much
of what it holds is the answer — are the three that decide correctness rather than style.

**Measurements come from this machine.** Every number was measured on CPython 3.14.4, the
interpreter in this repository's virtual environment, on a 64-bit build. Deterministic values —
byte counts, move counts, printed output — will reproduce exactly for you. Timings will not; they
depend on your hardware and on what else is running. What reproduces is the shape: the ratios, the
orderings, and the way a figure moves when the input doubles. Where a number is a timing, the
surrounding prose says what about it is meant to hold, and where an ordering depends on a property
of the input it says which property.

**It is the longest chapter after the first.** Around 24,600 words, a little over three hours at the
pace of prose you stop and run rather than skim, against chapter 1's six and a quarter. Two sittings
rather than one, and the natural break is the gate itself: the end of section 3.

## The sections

| | Section | What it settles | Gate | Size |
|---|---|---|---|---:|
| 1 | [What in place actually means](#1-what-in-place-actually-means) | The two readings of the phrase, and where they come apart | safe | 2,500 w · 19 min |
| 2 | [What the copy costs](#2-what-the-copy-costs) | The size of the second list, and why time is a separate question | safe | 2,700 w · 20 min |
| 3 | [In-place rewrites that need no cleverness](#3-in-place-rewrites-that-need-no-cleverness) | Same length in as out, and the direction that keeps it correct | safe | 2,800 w · 21 min |
| 4 | [When the answer is shorter than the input](#4-when-the-answer-is-shorter-than-the-input) | The trade between a shifted tail and a second list, stated exactly | **past the gate** | 2,700 w · 21 min |
| 5 | [The read cursor and the write cursor](#5-the-read-cursor-and-the-write-cursor) | The invariant, why overwriting is safe, and the count that is the answer | **past the gate** | 4,000 w · 31 min |
| 6 | [Two indices from opposite ends](#6-two-indices-from-opposite-ends) | The converging shape, what it scrambles, and which shape a statement wants | **past the gate** | 3,000 w · 23 min |
| 7 | [When not to do it in place](#7-when-not-to-do-it-in-place) | The caller you damaged, and the five questions before you overwrite | **past the gate** | 2,700 w · 21 min |
| 8 | [Drills](#8-drills) | Ten predictions, an answer key, and a readiness check | **past the gate** | 2,700 w · 21 min |

Sections 1 through 3 are the safe half and are best read in order: what the phrase promises, what
the alternative costs in bytes, and the whole family of rewrites that needs no technique at all.
They are self-contained, and stopping after section 3 leaves you with something complete rather than
half an idea.

Section 4 is the hinge. It states the problem the rest of the chapter exists to solve — an answer
shorter than its input, delivered through the caller's object — and proves that the two obvious
algorithms each fail on the axis the other wins. Sections 5 and 6 are the two arrangements of the
answer, and they are a pair: two indices in convoy, and two indices converging from the ends. Read
them together, because choosing between them is the part a problem statement decides for you.
Section 7 is the case against everything the four sections before it built, and it is the one to
read before writing an in-place helper anybody else will call. Section 8 is the exit exam.

When you finish, the three problems in `arrays101/ch05/` are waiting. Sections 3, 5 and 6 are the
three nearest to them, and section 7 is the one that explains why their contracts disagree with each
other about what to return.

---

## 1. What in place actually means

Chapters 2, 3 and 4 each took one operation and asked what it costs. This chapter takes a constraint
that cuts across all three, and it constrains the answer's address rather than the work. **In place
is not an algorithm and not a data structure; it is a promise about which object the caller reads
the answer out of.** The promise is looser than the phrase sounds, and the looseness is worth
pinning down before any technique gets built on top of it.

### The same transformation, reached twice

Take a transformation small enough to hold in your head. Given a list of integers, produce one in
which every element at an even index has been replaced by its square, and every element at an odd
index is left alone.

The obvious implementation builds a second list and fills it.

```python
readings = [3, 5, 2, 8, 4, 1]

squares = []
for i, value in enumerate(readings):
    squares.append(value * value if i % 2 == 0 else value)

print(squares)               # -> [9, 5, 4, 8, 16, 1]
print(readings)              # -> [3, 5, 2, 8, 4, 1]
print(squares is readings)   # -> False
```

Six values in, six values out, and the two lists sit side by side afterwards. `readings` still holds
what it arrived holding, `squares` holds the answer, and `is` reports two objects.

The second implementation never mentions a second list. It walks the even indices of the list it was
handed and overwrites each one.

```python
readings = [3, 5, 2, 8, 4, 1]
audit = readings

for i in range(0, len(readings), 2):
    readings[i] = readings[i] * readings[i]

print(readings)                   # -> [9, 5, 4, 8, 16, 1]
print(audit, audit is readings)   # -> [9, 5, 4, 8, 16, 1] True
```

The printed answer is identical. Everything else about the situation differs. Nothing was allocated
for a second list, because there is no second list. There is also no list anywhere holding
`[3, 5, 2, 8, 4, 1]` any more: the three values at even positions are gone rather than moved. And
`audit`, a second name bound to that same object before the loop ran, shows the new contents without
having been mentioned — chapter 1 section 9 establishes that behaviour, and the last
subsection here is about what it costs you.

**It is the second shape — the object you were handed carrying the answer — that "in place"
names.**

### Two definitions, and they come apart

There are two readings of the phrase in circulation, and people use them interchangeably as though
they were one requirement.

The strict reading is a statement about space complexity: an algorithm is in place when the extra
space it needs, beyond the input itself, does not grow with the input. O(1) auxiliary. A fixed
number of loose integers, and nothing whose size tracks the length.

The practical reading, and the one nearly every problem statement means, is a statement about
delivery: the input object carries the answer. The caller hands you a list and reads that same
object when you return. What you allocated on the way is not part of the contract, and the caller
usually has no way to observe it.

Which of the two a problem means is written into its signature and its extra words, never into the
phrase itself. A function declared to return `None` can only be scored on the object it was handed,
so the shape of the call has already chosen the practical reading. A signature that returns a list
does not lift the requirement: what comes back may still have to *be* the list you were given,
compared with `is` rather than `==`, which is how this chapter's `replaceElements` is checked. Where
the strict reading is wanted on top of either, it has to be written out, because no shape of call
implies it and no caller can confirm it: this chapter's `moveZeroes` asks for the move "without
making a copy of the array", a clause that would say nothing at all if "in place" already meant O(1)
auxiliary.

One line separates them. Chapter 1 section 9 already flagged this spelling: the right-hand side
is fully built before anything is written, so the result is in place while the work is not.

```python
nums = [3, 5, 2, 8, 4, 1]
holder = nums

nums[:] = [v * v if i % 2 == 0 else v for i, v in enumerate(nums)]

print(nums, holder is nums)   # -> [9, 5, 4, 8, 16, 1] True
```

The caller sees the answer in its own object, so the practical reading is satisfied exactly. Peak
memory says the strict reading is not. One harness answers every memory question in this chapter,
and it is chapter 1 section 11's `tracemalloc` pair narrowed to a single number: start the meter,
build the input, reset the peak, run the work, subtract the bytes already resident when the work
began.

```python
import tracemalloc


def peak_extra(build, work):
    """Bytes allocated above the resident data while `work` runs."""
    tracemalloc.start()
    nums = build()
    tracemalloc.reset_peak()
    base = tracemalloc.get_traced_memory()[0]
    work(nums)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak - base
```

It reports bytes, and it reports what the operation asked for rather than what the input already
cost. Building inside the traced region is the load-bearing choice: an object the work releases is
credited back to an account that was charged for it, so the figure is net rather than gross. Paste
it once; it is the memory harness for the rest of the chapter. Here it runs the three spellings
against two 200,000-element inputs differing in one respect — whether the squares they compute are
integers CPython already has.

```python
def returns_new(nums):
    return [v * v if i % 2 == 0 else v for i, v in enumerate(nums)]


def rewrites_by_slice(nums):
    nums[:] = [v * v if i % 2 == 0 else v for i, v in enumerate(nums)]


def rewrites_by_index(nums):
    for i in range(0, len(nums), 2):
        nums[i] = nums[i] * nums[i]


n = 200_000
fresh = lambda: list(range(n))                # squaring 0..199_999 makes new objects
cached = lambda: [i % 16 for i in range(n)]   # every square of 0..15 already exists

for fn in (returns_new, rewrites_by_slice, rewrites_by_index):
    print(f"{fn.__name__:18} fresh {peak_extra(fresh, fn):>9}   cached {peak_extra(cached, fn):>9}")
# -> returns_new        fresh   4823848   cached   1624072
# -> rewrites_by_slice  fresh   6423776   cached   3224000
# -> rewrites_by_index  fresh      7104   cached         0
```

Read the cached column first, because it prices containers and nothing else: every value and every
square there is one of the integers the interpreter keeps permanently, so only list structure
reaches the meter. The two copying spellings pay 1,624,072 and 3,224,000 bytes for their second
list. The indexed rewrite pays zero, and **that zero is the figure to carry forward — it is what a
write into a slot that already exists costs, at any length.**

The fresh column adds the new integers that squaring 0 through 199,999 requires, and it charges the
three rows very differently. Both copying rows rise by exactly 3,199,776 bytes, because a copy keeps
every square it builds. The indexed row rises by 7,104, under a tenth of a byte per write, because a
write releases what was in the slot as it stores what replaces it — each new integer is paid for out
of the space its predecessor vacates. Hold a second list of the originals so that nothing can be
released and the same loop charges that same 3,199,776.

The gap between the two copying rows is 1,599,928 bytes, the same on both inputs for the identical
comprehension: that is what the slice assignment costs on top of the list the comprehension had
already made. Priced on its own, with elements that already exist so that only list allocation
reaches the meter:

```python
n = 200_000
elements = [object() for _ in range(n)]   # every element already exists
source = elements[::-1]


def by_slice(target):
    target[:] = source


def by_index(target):
    for i in range(len(target)):
        target[i] = source[i]


print(peak_extra(lambda: elements[:], by_slice))   # -> 1600000
print(peak_extra(lambda: elements[:], by_index))   # -> 0
print(n * 8)                                       # -> 1600000
```

1,600,000 bytes is exactly 200,000 pointers at 8 bytes apiece, and the equality is not a coincidence
of this length: at 50,000 and 100,000 elements the same pair of calls returns 400,000 and 800,000
against a zero that never moves. The slice assignment allocates a full list's worth even though the
right-hand side was already a list, because the old contents have to be held somewhere until the new
ones are safely installed. **A rewrite that satisfies every in-place check the caller can perform
can still allocate a second copy of the input.**

The strict reading fails in a more surprising place too. `sort` is the method everyone calls in
place, and chapter 1 section 8 priced its merge buffer at 399,832 bytes on a shuffled
100,000-element list. The same harness reproduces that figure, and hands back something else
entirely for three inputs that are already ordered in some way:

```python
import random

m = 100_000


def shuffled():
    data = list(range(m))
    random.seed(7)
    random.shuffle(data)
    return data


def do_sort(data):
    data.sort()


print(peak_extra(shuffled, do_sort))                      # -> 399832
print(peak_extra(lambda: list(range(m)), do_sort))        # -> 32
print(peak_extra(lambda: list(range(m))[::-1], do_sort))  # -> 32
print(peak_extra(lambda: [0] * m, do_sort))               # -> 0
```

Same method, same length, and the extra space is 399,832 bytes or a flat 32. The buffer is scratch
space for combining the ordered stretches the sort finds, and each of the last three inputs is a
single such stretch from end to end: ascending, descending, and all one value. The 32 bytes the two
ordered ones still pay is the shape the strict reading asks about: it reads 32 at m = 1,000 and 32
at m = 1,000,000, so it never grows. The shuffled row's buffer does, doubling as m doubles — 199,920
at 50,000 and 799,920 at 200,000. **Whether `sort` is in place under the strict reading is a
fact about the data, not about the method**, which is a good reason not to carry the strict reading
as your only definition.

### Rebinding is not mutating

Between the two readings there is a failure that belongs to neither, because it delivers nothing at
all. Chapter 1 section 9 has the mechanism in full and it is not worth re-deriving; what matters
here is that one line decides it.

```python
def square_even_rebound(values):
    values = [v * v if i % 2 == 0 else v for i, v in enumerate(values)]

def square_even_in_place(values):
    values[:] = [v * v if i % 2 == 0 else v for i, v in enumerate(values)]

for fn in (square_even_rebound, square_even_in_place):
    data = [3, 5, 2, 8, 4, 1]
    fn(data)
    print(f"{fn.__name__:22} {data}")
# -> square_even_rebound    [3, 5, 2, 8, 4, 1]
# -> square_even_in_place   [9, 5, 4, 8, 16, 1]
```

Same body, same arithmetic, same comprehension. `square_even_rebound` computed the right six values
and bound a local name to them; the name went away when the function returned and took the answer
with it. `square_even_in_place` stored into the object. **`nums = something` can never satisfy an
in-place contract, and `nums[:] = something` always can**, however correct the arithmetic in
between. The check is chapter 1 section 9's: discard the return value, look only at the list you
passed in, and if it is unchanged the function did nothing.

### Why the constraint is worth asking for

Two reasons, and only one of them is about your program.

The first is that space is scored. A solution is judged on time and on memory, and the time half
announces itself, because a solution that is too slow visibly takes too long. The space half is
silent, so it is the half that gets conceded without anyone noticing, and an interviewer who asks
for in place is asking you to spend the same care on it.

The second is that the input is usually the largest thing in the room. At `n = 10**4`, the highest
length any of this chapter's problems allows, the list alone is most of what exists:

```python
import sys

arr = list(range(10_000))
print(sys.getsizeof(arr))                          # -> 80056
print(sys.getsizeof(arr) + sys.getsizeof(arr[:]))  # -> 160112
print(sys.getsizeof(0), sys.getsizeof(9_999))      # -> 28 28
print(sys.getsizeof(2 ** 30 - 1), sys.getsizeof(2 ** 30))  # -> 28 32
```

A second list of the same length costs the 80,056 over again, because a copy duplicates the
pointers and shares the elements they point at. A solution that instead keeps a handful of its own
counters and indices beside the input is holding 28-byte objects — every index into a list this
size sits far below the boundary at `2 ** 30` where an integer needs a second digit and grows to
32. The two quantities are not merely far apart, they are different shapes: one grows with the
length and the other never does, so the gap widens with every element added. Chapter 3 section 6
measured the same fact from the other side, running two hundred thousand indexed writes over a list
and finding its block byte-for-byte the size it started.

### What the caller gives up

The bargain has a second half, and it is charged to somebody who was not in the conversation. When
the input carries the answer, the input is no longer available.

```python
def square_even(values):
    for i in range(0, len(values), 2):
        values[i] = values[i] * values[i]

readings = [3, 5, 2, 8, 4, 1]
baseline = sum(readings)
audit = readings

square_even(readings)

print(baseline, sum(audit))   # -> 23 43
print(audit)                  # -> [9, 5, 4, 8, 16, 1]
```

`baseline` was captured before the call and is now the only surviving trace of what the list held.
`audit` was never passed to `square_even` and never mentioned inside it, and it reports the new
contents anyway, because it is a second name for the one object. Nothing raised and nothing looked
wrong; a later read simply answers a different question than it did an hour ago. In code you did not
write, the other holder of that name may be several frames away and may have captured its reference
long before your function existed.

When you need both the answer and the original, the copy is the remedy and taking it is a decision
rather than a reflex:

```python
def square_even(values):
    for i in range(0, len(values), 2):
        values[i] = values[i] * values[i]

readings = [3, 5, 2, 8, 4, 1]
audit = readings
working = readings[:]
square_even(working)

print(working)   # -> [9, 5, 4, 8, 16, 1]
print(audit)     # -> [3, 5, 2, 8, 4, 1]
```

Chapter 1 section 9 states the two rules that collide here: copy what you do not own, and do not
copy what you must change. An in-place contract is the second rule; a caller who still needs the
original values is the first. Nothing in the language arbitrates between them, so the copy becomes
the caller's decision rather than yours, and the requirement gets written into the problem instead
of assumed. What that copy actually costs, when you do take it, is section 2.

---

## 2. What the copy costs

"It uses extra space" is the reason usually given for preferring the rewrite, and as stated it is
not a reason at all — it is a claim with no size attached. This section attaches the sizes. The
transformation throughout is one line long: square every element sitting at an even index, leave
the rest alone.

### Peak, not total

`tracemalloc` reports two numbers, the bytes held at the moment you ask and the high-water mark
reached on the way there. Chapter 1 section 11 introduced the pair and made the case for reading
them against each other; a temporary that has already been freed is invisible in the first number
and unmissable in the second, so **the peak is the figure that prices a copy.**

```python
import tracemalloc


def peak_extra(build, work):
    """Bytes allocated above the resident data while `work` runs."""
    tracemalloc.start()
    nums = build()
    tracemalloc.reset_peak()
    base = tracemalloc.get_traced_memory()[0]
    work(nums)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak - base


def rebuilt(nums):
    out = [x * x if i % 2 == 0 else x for i, x in enumerate(nums)]


def in_place(nums):
    for i in range(0, len(nums), 2):
        nums[i] = nums[i] * nums[i]


for n in (10_000, 100_000, 1_000_000):
    build = lambda: [i % 16 for i in range(n)]
    a, b = peak_extra(build, rebuilt), peak_extra(build, in_place)
    print(f"n = {n:<9} rebuilt {a:>9} bytes ({a / n:5.2f} per element)   in place {b} bytes")

# -> n = 10000     rebuilt     85192 bytes ( 8.52 per element)   in place 0 bytes
# -> n = 100000    rebuilt    801000 bytes ( 8.01 per element)   in place 0 bytes
# -> n = 1000000   rebuilt   8448744 bytes ( 8.45 per element)   in place 0 bytes
```

Those six figures reproduce exactly, run after run. Two decisions in the harness are load-bearing.
The input is built inside the traced region, so that objects the transformation releases are
subtracted from an account that was charged for them. And the values are `i % 16`, which keeps
every element and every square inside chapter 1 section 2's window of shared integer objects, -5 to
256 — so no integer is allocated by either version, and what the meter reports is the list
structure alone.

The rebuilt column is one pointer per element plus the slack a list collects while growing without
a known final length, which is chapter 1 section 7's over-allocation showing up as a bill. Nothing
else is in there: at each of the three sizes the peak is `sys.getsizeof` of the finished list plus
sixteen bytes. The in-place column is a literal zero at every size, including the largest. A write
to a slot that already exists asks the allocator for nothing at all.

**The copy's peak is proportional to n and the rewrite's is a constant that happens to be zero** —
that is the whole space argument, and at a million elements it is worth 8,448,744 bytes.

### What eight bytes buys, and what it does not

Eight bytes is a pointer. It is not the value, and the distinction decides whether the copy costs
eight bytes an element or four times that. Above, both lists point at integers that already
existed. Change the transformation so each result is a fresh object and the per-element figure
changes with it:

```python
def rebuilt(nums):
    out = [x + 1.0 for x in nums]


def in_place(nums):
    for i in range(len(nums)):
        nums[i] = nums[i] + 1.0


for n in (10_000, 100_000, 1_000_000):
    build = lambda: [i * 0.5 for i in range(n)]
    a, b = peak_extra(build, rebuilt), peak_extra(build, in_place)
    print(f"n = {n:<9} rebuilt {a:>9} ({a / n:5.2f} per element)   in place {b} bytes")

# -> n = 10000     rebuilt    325120 (32.51 per element)   in place 24 bytes
# -> n = 100000    rebuilt   3200928 (32.01 per element)   in place 24 bytes
# -> n = 1000000   rebuilt  32448672 (32.45 per element)   in place 24 bytes
```

Thirty-two bytes an element: eight for the pointer and twenty-four for the float it points at,
which `sys.getsizeof(1.5)` will confirm. The in-place column is 24 bytes — one float — at all
three sizes, because each replacement value is built, stored, and the value it displaced released
before the next iteration starts. The rewrite holds one new object at a time; the copy holds n of
them and the original n as well.

Seen from the other side, the same fact is that two blocks are alive at once:

```python
import sys

nums = [i % 16 for i in range(100_000)]
before = sys.getsizeof(nums)
out = [x * x if i % 2 == 0 else x for i, x in enumerate(nums)]
print(before, sys.getsizeof(out))          # -> 800984 800984

for i in range(0, len(nums), 2):
    nums[i] = nums[i] * nums[i]
print(sys.getsizeof(nums) == before)       # -> True
```

Two identical 800,984-byte blocks where there was one, against a hundred thousand writes that leave
the block byte-for-byte the size it was. (Both lists report the same size because both were built by
a comprehension — chapter 1 section 11's warning that a size comparison is only a comparison of
contents when both structures were built the same way.)

### The idiom that pays both bills

`nums[:] = ...` looks like the best of both: the caller's object survives, and the transformation is
still written as an expression. In memory it is the most expensive of the three.

```python
def splice(nums):
    nums[:] = [x * x if i % 2 == 0 else x for i, x in enumerate(nums)]


for n in (10_000, 100_000, 1_000_000):
    build = lambda: [i % 16 for i in range(n)]
    c = peak_extra(build, splice)
    print(f"n = {n:<9} nums[:] = ...  {c:>9} bytes ({c / n:5.2f} per element)")

# -> n = 10000     nums[:] = ...     165120 bytes (16.51 per element)
# -> n = 100000    nums[:] = ...    1600928 bytes (16.01 per element)
# -> n = 1000000   nums[:] = ...   16448672 bytes (16.45 per element)
```

Sixteen bytes an element, twice the plain copy, and chapter 3 section 5 already took both halves
apart: the right-hand side is consumed into a list before the target is touched, which is why
spelling it as a generator expression saves nothing, and the assignment then holds the references it
displaces at eight bytes each. Eight bytes for the incoming reference and eight for the outgoing
one. It buys the caller's object back, and the price is the copy plus a copy.

### Time is a separate question, with a separate answer

The space argument does not carry a time argument with it. Five ways to spell the same job, one
input, each execution on data the setup has just rebuilt:

```python
import timeit


def bench_fresh(stmt, setup, repeat=15):
    """Best of `repeat` single executions. `setup` runs once per repeat, so each gets fresh data."""
    return min(timeit.repeat(stmt, setup, number=1, repeat=repeat))


setup = "nums = [i % 16 for i in range(100_000)]"
cases = {
    "plain comprehension":  "out = [x * x for x in nums]",
    "comp + enumerate":     "out = [x * x for i, x in enumerate(nums)]",
    "comp + enum + choice": "out = [x * x if i % 2 == 0 else x for i, x in enumerate(nums)]",
    "in place, every slot": "for i in range(len(nums)):\n    nums[i] = nums[i] * nums[i]",
    "in place, even slots": "for i in range(0, len(nums), 2):\n    nums[i] = nums[i] * nums[i]",
}
for name, stmt in cases.items():
    print(f"{name:<22}{bench_fresh(stmt, setup) * 1e3:7.3f} ms")

# -> plain comprehension     0.502 ms
# -> comp + enumerate        1.353 ms
# -> comp + enum + choice    2.211 ms
# -> in place, every slot    1.443 ms
# -> in place, even slots    0.708 ms
```

`number=1` is not decoration. Chapter 1 section 11 showed that `setup` runs once per repeat rather
than once per execution, so a mutating statement timed with `number=10` spends nine of its ten
executions on the output of the first. One execution per repeat is the honest arrangement for
anything that rewrites its input.

Read the first and fourth rows against each other and the copy wins by 2.87x. Read the third and
fifth and the rewrite wins by 3.12x. Both orderings held on every rerun, at 2.7x to 2.9x and 3.1x
give or take — on this input, and a third property below moves those factors a long way without
disturbing either ordering. The property that separates the rows is visible in their labels:
**whether the transformation needs to know the index.** When it does not, the copy is a plain
comprehension, which chapter 2 section 2 counted at four bytecode instructions per item against
the indexed loop's seven — and measured, on a fill rather than a rewrite, at 2.42x when the body
only moves a pointer, collapsing to 1.35x once each item carries real arithmetic. When the
transformation does need the index, the comprehension has to carry `enumerate` and then a
conditional, at 2.7x and a further 1.6x here, and it gives the advantage straight back.

The second property is how much of the list actually changes. The copy visits every element whatever
the answer; the rewrite visits only the slots it means to touch:

```python
for k in (1, 2, 4, 8):
    new = bench_fresh(f"out = [x * x if i % {k} == 0 else x for i, x in enumerate(nums)]", setup)
    old = bench_fresh(f"for i in range(0, len(nums), {k}):\n    nums[i] = nums[i] * nums[i]", setup)
    print(f"1 slot in {k:<3}rebuilt {new * 1e3:6.3f} ms   in place {old * 1e3:6.3f} ms"
          f"   {new / old:5.2f}x")

# -> 1 slot in 1  rebuilt  2.336 ms   in place  1.432 ms    1.63x
# -> 1 slot in 2  rebuilt  2.212 ms   in place  0.708 ms    3.12x
# -> 1 slot in 4  rebuilt  2.656 ms   in place  0.357 ms    7.44x
# -> 1 slot in 8  rebuilt  2.336 ms   in place  0.183 ms   12.79x
```

The right-hand column halves every time `k` doubles: a factor of 7.8 from top to bottom, tracking
the factor of 8 in slots touched. The left-hand column does not track it at all — it wanders
inside about ten percent of its own value, because the comprehension is producing a hundred
thousand elements no matter how few of them differ from their input. That is the shape to carry
away rather than any single ratio: rebuilding costs O(n) in time and space regardless, while an
in-place pass costs what it touches.

The third property is one the harness has been quietly supplying all along. Every value in `setup`
is `i % 16`, and the square of one is at most 225, so both columns run entirely on integers the
interpreter already had and neither allocates anything to do its arithmetic — the same choice that
made the memory figures readable is also inflating the time ratios. Take it away and the margin
narrows:

```python
inputs = {
    "i % 16, squares cached": "nums = [i % 16 for i in range(100_000)]",
    "i, squares allocated":   "nums = [i for i in range(100_000)]",
    "i + 10**18, big ints":   "nums = [i + 10**18 for i in range(100_000)]",
}
for name, s in inputs.items():
    comp = bench_fresh("out = [x * x for x in nums]", s)
    slot = bench_fresh("for i in range(len(nums)):\n    nums[i] = nums[i] * nums[i]", s)
    print(f"{name:<24}comprehension {comp * 1e3:6.3f} ms   in place {slot * 1e3:6.3f} ms"
          f"   {slot / comp:5.2f}x")

# -> i % 16, squares cached  comprehension  0.515 ms   in place  1.441 ms    2.80x
# -> i, squares allocated    comprehension  1.166 ms   in place  2.056 ms    1.76x
# -> i + 10**18, big ints    comprehension  2.106 ms   in place  3.356 ms    1.59x
```

The comprehension wins every row, and that ordering held on every rerun of all three inputs. Its
margin does not hold: it falls from roughly 2.8x to roughly 1.6x as each element's arithmetic starts
costing real work, because that work is charged identically to both spellings and only the fixed
per-item overhead differs. This is chapter 2 section 2's collapse from 2.42x to 1.35x, reproduced on
a rewrite instead of a fill. **Quote the ordering; do not quote the factor.** The factor belongs to
your values as much as to your loop.

**Do not reach for the rewrite expecting it to be faster.** It is reliably smaller. Whether it is
also quicker depends on the three properties above — whether the transformation needs the index,
how much of the list it changes, and how much each element's arithmetic costs — and on the
cached-integer input used here the plain comprehension beat the every-slot rewrite by nearly 3x.

### When the copy is the right answer

*The original is still needed.* Chapter 1 section 9 states the rule as copy what you do not own, and
the caller is not the only party who might need the old values — the transformation itself often
does. A pass whose result at each position reads its neighbours has already destroyed one of its own
inputs by the time it needs it:

```python
readings = [4, 10, 4, 10, 4]
print([readings[i - 1] + readings[i] + readings[i + 1] for i in range(1, len(readings) - 1)])
# -> [18, 24, 18]

for i in range(1, len(readings) - 1):
    readings[i] = readings[i - 1] + readings[i] + readings[i + 1]
print(readings[1:-1])
# -> [18, 32, 46]
```

Same arithmetic, different answers, and only the first one is the smoothing that was asked for. When
a position's new value depends on positions the pass has already rewritten, the second list is not
overhead — it is what makes the transformation mean what it says.

*The length changes.* Keeping an unknown subset produces an answer shorter than the input, and a
list cannot report a length its own contents do not have. The comprehension is the plain way to say
it, and chapter 3 section 5 priced it: a pointer per survivor, briefly two, and it called the second
list a cost to price rather than a rule to obey. Section 4 takes up what to do when a caller refuses
to pay it.

*Clarity is worth more than the constant.* An expression that produces a value can be read in one
sitting; a loop that mutates has to be read with a model of what the list holds at each step. On a
list of a few hundred elements the entire saving measured above is a few kilobytes and some
microseconds. Chapter 2 section 2's advice generalises cleanly here: prefer the form that says what
you mean, and do not restructure code for a speedup you cannot feel.

### Measuring your own case

The two harnesses in this section are the whole toolkit, and both are cut down from chapter 1
section 11. `peak_extra` answers "what does this cost in memory" — build the input inside the
traced region, reset the peak, run the work, subtract the base. `bench_fresh` answers "what does
it cost in time" — quote the minimum, never the mean, since interference can only make code look
slower; keep construction in `setup`, out of the clock; and use `number=1` whenever the statement
changes its input.

One caution before you generalise from a label. In place is a claim about the object, not a promise
of zero allocation: `nums.sort()` rewrites the list you already have, and on the 100,000-element
input used throughout this section `peak_extra` charges it 374,848 bytes for the merge buffer
chapter 1 section 8's table describes. That is not the 399,832 bytes section 1 reports for a
100,000-element sort, and neither figure is wrong. The buffer is sized by the ordered stretches the
sort finds, which section 1 demonstrates at that same length with inputs paying anything from the
full 399,832 down to nothing — and this section's `i % 16` is not the shuffle that produced its
headline number. If the memory matters enough to argue about, measure the operation you are
actually going to run, on the data you are going to run it on.

---

## 3. In-place rewrites that need no cleverness

A rewrite is dangerous only when it destroys something it still needs. That is the whole of the
difficulty, and it means a large family of in-place work carries no difficulty at all. If the value
you write into position `i` is decided entirely by the value that was in position `i` — or by values
you have already finished with — then there is nothing to lose by writing early, and the order you
visit the positions in cannot make you wrong. **Test a rewrite by asking what it still needs after
it has written; when the answer is nothing, in place is free.**

### The rewrites with no order to get wrong

Take the narrowest case first: what goes into a position is a function of what was in that same
position and of nothing else. Square every element sitting at an even index and leave the odd ones
alone.

```python
readings = [3, 5, 2, 7, 4, 9]
for i in range(0, len(readings), 2):
    readings[i] = readings[i] * readings[i]
print(readings)     # -> [9, 5, 4, 7, 16, 9]
```

The step of 2 walks 0, 2, 4 and never visits the others, so the untouched positions cost not just no
allocation but no write. Chapter 1 section 6 is the reason the loop is written over indices rather
than values: `for x in readings` binds `x` to whatever is in a slot, and rebinding `x` moves a name,
not an element. When you need the position *and* the old value, `enumerate` gives you both:

```python
readings = [3, 5, 2, 7, 4, 9]
for i, x in enumerate(readings):
    if i % 2 == 0:
        readings[i] = x * x
print(readings)     # -> [9, 5, 4, 7, 16, 9]
```

`enumerate` is safe here for a reason worth naming rather than assuming. It yields the pair for
position `i` before the body runs, so `x` is always what was in the slot before your write, and in
this family the body writes only the slot it was just handed — every read still lands ahead of every
write. The length never moves either, which is what keeps the iterator's idea of the list and the
list's own idea of itself in agreement; chapter 3 section 7 is the case where they stop agreeing.

Because the positions are independent, the direction is yours. Forwards, backwards with chapter 1
section 6's `reversed(range(len(readings)))`, or in any order you can enumerate the even positions
in: same answer. That freedom is what the rest of this section spends.

### The same rewrite as one store

Chapter 1 section 5 established slice assignment, and its length rule decides which spellings are
available: a contiguous slice may resize, an extended slice may not, and `readings[:] = ...`
overwrites the object every other name is still pointing at. Both of the loops above have a
slice-assignment spelling.

```python
readings = [3, 5, 2, 7, 4, 9]
readings[::2] = [x * x for x in readings[::2]]
print(readings)     # -> [9, 5, 4, 7, 16, 9]

readings = [3, 5, 2, 7, 4, 9]
readings[:] = (x * x if i % 2 == 0 else x for i, x in enumerate(readings))
print(readings)     # -> [9, 5, 4, 7, 16, 9]
```

The second is reading the very list it is writing, and that is not a hazard: the right-hand side is
consumed into a temporary sequence before a single slot is touched, which is chapter 1 section 5's
`nums[:0] = nums`. A generator expression buys no laziness against a slice assignment.

The copy itself runs at C speed, and that part is worth seeing on its own, with no transform in the
way. Chapter 1 section 11's method throughout — `timeit.repeat`, minimum of the repeats:

```python
import timeit

setup = "src = list(range(200_000)); nums = [None] * 200_000"
for stmt in ("nums[:] = src",
             "for i in range(len(src)): nums[i] = src[i]",
             "for i, x in enumerate(src): nums[i] = x"):
    t = min(timeit.repeat(stmt, setup, number=1, repeat=200))
    print(f"{stmt:<44}{t * 1e3:7.3f} ms")

# -> nums[:] = src                                 0.359 ms
# -> for i in range(len(src)): nums[i] = src[i]    2.268 ms
# -> for i, x in enumerate(src): nums[i] = x       3.019 ms
```

Six times the cost for the indexed loop, eight for the `enumerate` one. Across sittings the multiple
wandered between four and eleven, holding its ordering on distinct ints, on one int repeated, on
floats and on strings alike. The slice assignment moves pointers in bulk at C speed; each loop pays
the interpreter per element for a subscript store it cannot avoid.

Put a transform back in and the copy stops being the story, because the transform is bytecode in
both spellings and only the copy was ever cheap. Time `nums[:] = [x * 2 for x in nums]` against the
matching indexed loop at n = 200,000 and there is still an ordering, but it belongs to the values
rather than to the spelling. On `[7] * 200_000`, where every result is one of the small integers the
interpreter keeps and so neither spelling allocates an element at all, the slice assignment finished
about 1.65 times faster across three sittings. On 200,000 distinct ints it loses, by about 1.2
times, and it loses on floats by a little less. Each ordering is steady on its own input, never came
out the other way round on it, and inverts on the other. **An ordering you can invert by
changing the values is not a reason to prefer a spelling, so do not choose between these two on
speed.** Memory does have an answer, and it is not close. The input below is picked so the meter
reads the containers rather than the values: `7 * 2` is `14`, one of the small integers the
interpreter keeps permanently, so not a single element object is created by any of the three.

```python
import tracemalloc

def peak(rewrite):
    nums = [7] * 200_000
    tracemalloc.start()
    tracemalloc.reset_peak()
    base = tracemalloc.get_traced_memory()[0]
    rewrite(nums)
    top = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return (top - base) / 1024

def indexed(nums):
    for i in range(len(nums)):
        nums[i] = nums[i] * 2

def published(nums):
    nums[:] = [x * 2 for x in nums]

def lazily(nums):
    nums[:] = (x * 2 for x in nums)

for label, fn in (("indexed loop", indexed), ("nums[:] = [...]", published),
                  ("nums[:] = (...)", lazily)):
    print(f"{label:<18}peak +{peak(fn):8.1f} KiB")

# -> indexed loop      peak +     0.0 KiB
# -> nums[:] = [...]   peak +  3148.4 KiB
# -> nums[:] = (...)   peak +  3148.6 KiB
```

Zero. The indexed loop asks the allocator for nothing whatsoever: it stores into slots that already
exist, the length never moves, and the values it stores already existed too. Section 2 priced the
other two at sixteen bytes an element, eight for the incoming reference and eight for the outgoing
one, and 3148.4 KiB is 3,224,000 bytes — 3,200,000 of them that doubling. The remaining 24,000 are
chapter 1 section 7's over-allocation, which only the byte-exact figure makes visible:
`sys.getsizeof` reports 1,624,056 for the right-hand side, a 56-byte header on a 1,624,000-byte
block where the pointers alone need 1,600,000, and that slack is still held when the assignment
allocates the second block. The generator expression lands within 0.2 KiB of it, because a slice
assignment consumes its right-hand side whole before writing anything and there is no laziness left
to spend.

**No slice assignment across a whole list is constant extra space.** Even the pure copy of `src`
above peaks at 1562.5 KiB, eight bytes a slot, for the outgoing pointers alone; chapter 3 section 5
priced the same temporary from the deletion side. Choose between these spellings on the memory
column, which is stable, and never on the timing column, which is not.

### The whole-list rewrites Python already has

Two rewrites are common enough that the list does them for you, reordering the object you already
hold rather than handing back a second one. Both follow chapter 1 section 9's convention, the one
chapter 3 section 2 restates: a list method that edits the list in place evaluates to `None`, and
`pop` is the single exception.

```python
readings = [3, 5, 2, 7, 4, 9]
print(readings.reverse())   # -> None
print(readings)             # -> [9, 4, 7, 2, 5, 3]
```

`reverse()` swaps pointers within the existing block, which chapter 1 section 8's table prices at
O(n) time and O(1) space. The copying spelling is not close:

```python
import timeit

setup = "nums = list(range(200_000))"
for stmt in ("nums.reverse()", "nums[:] = nums[::-1]"):
    t = min(timeit.repeat(stmt, setup, number=1, repeat=200))
    print(f"{stmt:<24}{t * 1e3:7.3f} ms")

# -> nums.reverse()            0.037 ms
# -> nums[:] = nums[::-1]      0.705 ms
```

Around twenty times on ints across sittings, and further apart still on floats and on strings, since
`nums[::-1]` builds a full reversed list before the assignment copies it back. Memory says the same
thing without the caveats: `reverse()` peaked at 0.0 KiB, the copying spelling at 3125.0 KiB — the
reversed list and the outgoing pointers, 1,600,000 bytes of each.

Sorting splits the same way, and the split is the entire difference between the two names:

```python
readings = [3, 5, 2, 7, 4, 9]
print(readings.sort(), readings)     # -> None [2, 3, 4, 5, 7, 9]

readings = [3, 5, 2, 7, 4, 9]
print(sorted(readings), readings)    # -> [2, 3, 4, 5, 7, 9] [3, 5, 2, 7, 4, 9]
```

`sort()` reorders the object and returns nothing; `sorted()` leaves the object alone and returns a
new list. Neither is free of a temporary — chapter 1 section 8's table prices `sort()` at a working
buffer of up to n/2 pointers — but they are not the same bill, and the bill is set by the input as
much as by the call. On 200,000 ints in random order, `data.sort()` peaked at 781.2 KiB, just under
those n/2 pointers, and `sorted(data)` at 2343.7 KiB, the same buffer plus a full copy of the list.
Hand both calls a list that is already ascending and the buffer vanishes: `sort()` peaked at 0.0 KiB
and `sorted()` at 1562.5 KiB, the copy on its own — the whole list is one ordered stretch already,
chapter 1 section 8's O(n) best case, so no buffer is asked for. **Quote a sort's memory with the
order of its input attached, or not at all.**

The third tool is one statement rather than a method. `a, b = b, a` swaps two names, the same
statement with slots as its targets swaps two elements, and chapter 1 section 4 established why both
are safe: the whole right-hand side is evaluated before any assignment happens, so both reads
complete before either write starts.

```python
readings = [3, 5, 2, 7, 4, 9]
readings[0], readings[5] = readings[5], readings[0]
print(readings)     # -> [9, 5, 2, 7, 4, 3]
```

Two statements would need a temporary name, because the first store would destroy a value the second
still wants. The statement above needs no name and, for two targets, no tuple object either — the
compiler pushes both reads onto the evaluation stack and reorders them there:

```python
import dis

def held(source):
    ops = [i.opname for i in dis.get_instructions(source)]
    return [op for op in ops if op in
            ("BINARY_OP", "SWAP", "STORE_SUBSCR", "BUILD_TUPLE", "UNPACK_SEQUENCE")]

print(held("readings[0], readings[5] = readings[5], readings[0]"))
# -> ['BINARY_OP', 'BINARY_OP', 'SWAP', 'STORE_SUBSCR', 'STORE_SUBSCR']

print(held("a, b, c, d = d, c, b, a"))
# -> ['BUILD_TUPLE', 'UNPACK_SEQUENCE']
```

Both subscript reads, then one `SWAP`, then both stores, and no `BUILD_TUPLE`. That refines chapter
1 section 4, which called the held right-hand side a tuple: at two targets, and at three, the
compiler keeps the values in stack slots and builds no object at all, and one appears only once
there are more of them than it will juggle there — four, on the second line. The guarantee survives
the refinement, because it never rested on the tuple. It is about the reads only, though, and the
targets are still assigned left to right:

```python
i = 0
readings = [10, 20, 30]
i, readings[i] = 2, 99
print(i, readings)     # -> 2 [10, 20, 99]
```

The second target used the `i` the first target had just changed. Swapping two slots is safe because
neither target's *address* depends on the other; make one target's index depend on the other and the
statement stops meaning what it looks like.

### When each position depends on one side

Now the case where order is everything. Rewrite each reading as the sum of itself and the one before
it, keeping the first as it stands. Each position depends on a value to its left, and the obvious
loop is wrong:

```python
temps = [18, 21, 19, 24, 17, 22, 20]
for i in range(1, len(temps)):
    temps[i] = temps[i] + temps[i - 1]
print(temps)     # -> [18, 39, 58, 82, 99, 121, 141]
```

That is not the pair sums. It is the running total, because by the time position `i` read position
`i - 1`, position `i - 1` was no longer holding its input — it was holding *its* answer. Nothing
raised, the numbers rise the way a plausible answer would, and the wanted result was
`[18, 39, 40, 43, 41, 39, 42]`.

There are two repairs and they are not equally general. This window is one element deep, so walking
from the far end instead leaves both values it needs untouched, and the identical loop body run over
`reversed(range(1, len(temps)))` produces `[18, 39, 40, 43, 41, 39, 42]` — the wanted answer. That
escape closes as soon as a position depends on more than a fixed handful of neighbours. The repair
that does not close is to stop asking the list for a value the list no longer has, and carry it
yourself:

```python
temps = [18, 21, 19, 24, 17, 22, 20]
previous = temps[0]
for i in range(1, len(temps)):
    current = temps[i]
    temps[i] = current + previous
    previous = current
print(temps)     # -> [18, 39, 40, 43, 41, 39, 42]
```

**A rewrite whose positions all depend on one side can be done in place by walking from that side,
carrying everything you still need in ordinary variables — because then every slot ahead of you is
untouched input and every slot behind you has already been summarised into what you carry.** One
variable buys one element of history. The interesting version is when a single variable buys the
whole side:

```python
temps = [18, 21, 19, 24, 17, 22, 20]
best = temps[0]
for i in range(len(temps)):
    if temps[i] > best:
        best = temps[i]
    temps[i] = best
print(temps)     # -> [18, 21, 21, 24, 24, 24, 24]

original = [18, 21, 19, 24, 17, 22, 20]
print(temps == [max(original[:i + 1]) for i in range(len(original))])   # -> True
```

Each position now holds the highest reading up to and including itself, and the check underneath is
that sentence written out as slices. `best` is a complete summary of everything to the left, so
overwriting the left costs nothing — one variable, whatever the length.

The direction and the summary are separate choices, worth seeing come apart. Start the walk at the
far end and the carried variable summarises everything to the *right*; make it a total rather than a
maximum and the argument is unchanged:

```python
temps = [18, 21, 19, 24, 17, 22, 20]
total = 0
for i in reversed(range(len(temps))):
    total = total + temps[i]
    temps[i] = total
print(temps)     # -> [141, 123, 102, 83, 59, 42, 20]

original = [18, 21, 19, 24, 17, 22, 20]
print(temps == [sum(original[i:]) for i in range(len(original))])   # -> True
```

The loop that opened this subsection produced a running total too — by accident, from the left, when
the question wanted something else. This one produces one deliberately, from the right, carrying it
rather than reading it back out of a slot it has already overwritten. Both checks cost a copied
slice and a full scan per position; both loops get the same answer in one pass and allocate nothing
at all. Walking from the right means the untouched input is always ahead of you and the overwritten
slots behind you are already summarised into what you carry — which is the whole argument, and worth
making out loud before you write the loop rather than after.

Every rewrite so far has produced exactly as many elements as it consumed, which is why none of them
needed anything cleverer than a direction and a variable. Section 4 takes the case where that stops
being true.

---

## 4. When the answer is shorter than the input

---

**STOP. Everything from here to the end of the chapter gives away four problems you have not
solved.**

**This section hands over the technique behind the two problems sitting in `arrays101/ch03/`: 27.
Remove Element, and 26. Remove Duplicates from Sorted Array. Not a hint towards it — the technique
itself, worked through on the second of those two problems by name. Go and solve both of them
before you read another paragraph.**

**Sections 5 and 6 then give away two more, and these are this chapter's own: 283. Move Zeroes and
905. Sort Array By Parity, both sitting unattempted in `arrays101/ch05/`. Section 5 finishes the
first outright and section 6 the second, and section 6 closes by naming both by number and
prescribing which shape each one wants. This section touches neither, so the place to stop for
those two is the end of it, where it tells you again.**

**Sections 1 to 3 above are clear of all of this, and nothing in them will spoil anything. 1299,
the first problem of this chapter, is solvable from those three sections alone; you do not need
this one for it.**

---

Every rewrite in section 3 had one shape. Position `i` received the answer for position `i`, and
the number of positions never moved. What varied between them was only what a position's answer
depended on — the value already sitting there, or everything to one side of it — and that decided
which direction you walked, never where a value went. No loop in that section had to work out a
destination. That is the easy half of working in place, and it is easy for a reason worth naming:
**the answer was exactly as long as the question.**

Now change that one thing.

> Given a list sorted in non-decreasing order, remove the duplicates so that each value appears
> only once.

The input has `n` elements. The answer has `k`, and `k` is at most `n`, and you do not know `k`
until you have looked at everything. Section 3's discipline has nothing to say here, because from
the first duplicate onwards the answer for position `i` is not built from position `i` at all: it
comes from somewhere further along, and how much further depends on how many duplicates you have
already passed. The destination has become something you have to work out.

### The algorithm chapter 3 already built

You have already read most of this loop. Chapter 3 section 7 arrived at it while fixing a different
bug — walk by index, and advance the index only on the steps where you kept the element, because
after a deletion the next element has already slid into `i`. Point that loop at a sorted list and
compare each element with the one before it, and the duplicates come out.

```python
def dedupe_by_deleting(nums):
    i = 1
    while i < len(nums):
        if nums[i] == nums[i - 1]:
            del nums[i]
        else:
            i += 1
    return len(nums)

readings = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
print(dedupe_by_deleting(readings), readings)   # -> 5 [0, 1, 2, 3, 4]

for case in ([], [5], [7, 7, 7, 7], [1, 2, 3]):
    buf = list(case)
    print(case, dedupe_by_deleting(buf), buf)
# -> [] 0 []
# -> [5] 1 [5]
# -> [7, 7, 7, 7] 1 [7]
# -> [1, 2, 3] 3 [1, 2, 3]
```

It is correct, including on the inputs that usually break a neighbour comparison. The empty list
never enters the loop, so `nums[i - 1]` is never evaluated on a list with nothing before it. A
single element is the same story. Four identical values collapse to one, the case that does the
most deleting, and a list with no duplicates at all comes back untouched. Sortedness is what makes
the neighbour test sufficient: equal values in a sorted list are adjacent, so a value that has been
seen before is a value sitting next to itself, and no memory of what came earlier is required.

### Its space bill really is zero

Section 1 separated two readings of in place — the practical one, where the caller reads the answer
out of the object it handed you, and the strict one, where the extra space does not grow with the
input — and this algorithm satisfies both at once. `del` removes a slot from the block the list
already owns. Nothing is allocated, and the caller's object is the object that changes:

```python
import tracemalloc

readings = [i // 2 for i in range(200_000)]
held = readings

tracemalloc.start()
tracemalloc.reset_peak()
base = tracemalloc.get_traced_memory()[0]
k = dedupe_by_deleting(readings)
peak = tracemalloc.get_traced_memory()[1]
tracemalloc.stop()

print(k, peak - base)                   # -> 100000 32
print(held is readings, len(held))      # -> True 100000
```

Thirty-two bytes at peak, to collapse two hundred thousand elements down to a hundred thousand.
That figure is not a small fraction of the input, it is unrelated to the input: the same block run
at 20,000 and at 400,000 elements reports 32 both times, so a twentyfold change in `n` moved it by
nothing. Those 32 bytes are the measuring harness, not the algorithm. **The extra space is O(1),
and it is the kind of O(1) you can point at.** `held is readings` is chapter 1 section 9's test,
confirming that the name the caller still holds sees the shortened list without rebinding anything.

So the space column is already the best it can be. Every remaining objection has to be about time.

### And the time is quadratic

Each `del` closes the gap it opens by sliding the whole tail one slot to the left — chapter 3
section 3's `n − i − 1`. Do that once per duplicate and the bill is a sum of tail lengths. That sum
is the entire cost model, and the exact number of relocated slots can be counted rather than
guessed:

```python
import timeit

SETUP = """
def dedupe_by_deleting(nums):
    i = 1
    while i < len(nums):
        if nums[i] == nums[i - 1]:
            del nums[i]
        else:
            i += 1
    return len(nums)
src = %s
"""

def moves_for(src):
    nums, i, moved = list(src), 1, 0
    while i < len(nums):
        if nums[i] == nums[i - 1]:
            moved += len(nums) - i - 1
            del nums[i]
        else:
            i += 1
    return moved

n = 20_000
for label, expr in (("every value distinct", "list(range(20_000))"),
                    ("each value twice", "[i // 2 for i in range(20_000)]"),
                    ("each value ten times", "[i // 10 for i in range(20_000)]"),
                    ("one value throughout", "[0] * 20_000")):
    setup = SETUP % expr
    moved = moves_for(eval(expr))
    t = min(timeit.repeat("dedupe_by_deleting(src.copy())", setup, number=3, repeat=7)) / 3 * 1000
    each = f"{t * 1e6 / moved:.3f} ns each" if moved else "nothing moved"
    print(f"{label:<22}{moved:>12,} moves {t:8.1f} ms   {each}")
print(f"n squared over two is {n * n // 2:,}")
# -> every value distinct             0 moves      0.6 ms   nothing moved
# -> each value twice        99,990,000 moves     25.9 ms   0.259 ns each
# -> each value ten times   179,982,000 moves     46.2 ms   0.257 ns each
# -> one value throughout   199,970,001 moves     51.2 ms   0.256 ns each
# -> n squared over two is 200,000,000
```

The move counts are exact and reproduce to the digit, and the right-hand column is what they buy:
divide the time by the moves and the same quarter of a nanosecond comes back on every row. What
reproduces there is the evenness rather than the digits — sittings landed anywhere from 0.255 to
0.281 ns, and the three rows moved together every time, never apart — against the 0.255 ns chapter
3 section 3 charged for the identical relocation. **The running time is one constant multiplied by
a number of moved slots, and that constant is already as low as CPython can make it, because none
of the move is interpreted.**

Read the left column before drawing any conclusion about speed, because it, not the algorithm,
decides which row you land on. **This loop's cost is governed by how many duplicates the input
contains, and the range is the full distance from linear to quadratic.** A sorted list with no
duplicates does no deletions at all and finishes in 0.6 ms — a plain scan, linear, nothing to
complain about. A list of 20,000 identical values relocates 199,970,001 slots, which is the
200,000,000 of `n²/2` to within 0.015%, and takes close to ninety times as long — the table's
rounding of the top row understates it, and timed head to head those two inputs came out between
88.6 and 91.0 times apart on five sittings. Quoting a single figure for "the delete loop" without
saying what was in the list is quoting a number that moves by a factor of ninety across the four
rows above.

Fix the duplicate density and grow `n`, and the shape is unmistakable. Below, every value appears
exactly twice, so half the elements are duplicates at every size:

```python
import timeit

SETUP = """
def dedupe_by_deleting(nums):
    i = 1
    while i < len(nums):
        if nums[i] == nums[i - 1]:
            del nums[i]
        else:
            i += 1
    return len(nums)

def dedupe_into_new(nums):
    out = []
    for i, x in enumerate(nums):
        if i == 0 or x != nums[i - 1]:
            out.append(x)
    return out

src = [i // 2 for i in range(%d)]
"""

prev_a = prev_b = None
for n in (5_000, 10_000, 20_000, 40_000):
    setup = SETUP % n
    a = min(timeit.repeat("dedupe_by_deleting(src.copy())", setup, number=3, repeat=7)) / 3 * 1000
    b = min(timeit.repeat("dedupe_into_new(src.copy())", setup, number=20, repeat=7)) / 20 * 1000
    ga = "-" if prev_a is None else f"x{a / prev_a:.2f}"
    gb = "-" if prev_b is None else f"x{b / prev_b:.2f}"
    print(f"n = {n:<7}del {a:8.2f} ms {ga:>6}    new list {b:6.3f} ms {gb:>6}    ratio {a / b:5.1f}x")
    prev_a, prev_b = a, b
# -> n = 5000   del     1.74 ms      -    new list  0.139 ms      -    ratio  12.6x
# -> n = 10000  del     6.62 ms  x3.81    new list  0.276 ms  x1.99    ratio  24.0x
# -> n = 20000  del    25.93 ms  x3.92    new list  0.554 ms  x2.01    ratio  46.8x
# -> n = 40000  del   102.32 ms  x3.95    new list  1.120 ms  x2.02    ratio  91.4x
```

Double the input and the `del` loop takes not twice as long but very nearly four times. Eight
sittings put its three factors between 3.64 and 4.14, scattered around the 4 that squared growth
predicts and never once near 2. The second algorithm in that table doubles when the input doubles —
1.87 to 2.19 across the same sittings — and it is the subject of the next heading. The column that
settles the argument is the last one: the gap between them is not a constant factor to be optimised
away, it doubles every time `n` doubles. About twelve times at 5,000, about ninety at 40,000, on
every sitting.

### The linear version, and what it costs to have

Give up on staying in place and the linear algorithm is immediate. Walk the input once, and append
each value that differs from the one before it.

```python
import sys, tracemalloc

def dedupe_into_new(nums):
    out = []
    for i, x in enumerate(nums):
        if i == 0 or x != nums[i - 1]:
            out.append(x)
    return out

print(dedupe_into_new([0, 0, 1, 1, 1, 2, 2, 3, 3, 4]))   # -> [0, 1, 2, 3, 4]

readings = [i // 2 for i in range(200_000)]
tracemalloc.start()
tracemalloc.reset_peak()
base = tracemalloc.get_traced_memory()[0]
out = dedupe_into_new(readings)
peak = tracemalloc.get_traced_memory()[1]
tracemalloc.stop()

print(len(out), peak - base)                    # -> 100000 801032
print(sys.getsizeof(out), 100_000 * 8 + 56)     # -> 800984 800056
```

Nothing is shifted, so no element is touched more than once, and the whole thing is one pass. It is
also the shortest code in this section, and shorter still written as a comprehension, or handed to
`itertools.groupby`, which exists to collapse exactly this kind of run:

```python
import itertools

readings = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
print([x for i, x in enumerate(readings) if i == 0 or x != readings[i - 1]])
# -> [0, 1, 2, 3, 4]
print([value for value, _ in itertools.groupby(readings)])
# -> [0, 1, 2, 3, 4]
print(sum(1 for i, x in enumerate(readings) if i == 0 or x != readings[i - 1]))
# -> 5
```

One detail in the measurement is worth reading closely, because it is where the destination's size
shows up. The peak was 801,032 bytes, of which 800,984 is the finished list and the few dozen bytes
left over are the harness. A list holding exactly 100,000 pointers with nothing spare would be
800,056 bytes, so 928 bytes — 116 slots — is capacity collected on the way up and never used. That
slack is the price of not knowing `k` in advance. **You never had to know it: `out = []` and
`append` size the destination as they go, chapter 1 section 7's over-allocation making the
amortized cost of each one constant.** The alternative is to decide the length before you create
the destination, and the only way to learn `k` before writing anything is to count first — the
last line of the block above, a complete extra pass over the input, run before a single element is
written, to buy back 928 bytes.

Either way, the bill is the one thing this algorithm cannot argue with. 800,984 bytes of fresh
pointers, next to 32. That is O(n) extra space, on a problem whose answer was already sitting in a
list the caller owned.

### The trade, stated exactly

Two algorithms, one problem, and each is the best available answer on one axis and, on the input
that suits it least, the worst on the other.

| | extra space | time | why |
|---|---|---|---|
| `dedupe_by_deleting` | 32 bytes, flat in `n` | up to `n²/2` slot moves | every deletion shifts the tail |
| `dedupe_into_new` | 800,984 bytes at `n` = 200,000 | one pass, `n` comparisons | nothing is ever moved twice |

Neither column is a defect of the code. The first algorithm pays in slot moves because it insists
on having only one list, and the only way to close a gap inside one list is to move everything
after it — which is why its cost is set by the input's duplicate density and reaches `n²/2` when
that density is highest. The second is linear on every input because it writes each survivor to a
position no one has read yet, and it can promise that only by having a second list to write into.
**Each algorithm's virtue is the direct cause of its vice.**

That framing is also what makes the trade look inevitable, and it is worth being explicit that
nothing has been proved. Chapter 3 section 6 stopped exactly here. It set up the convention that
lets an answer shorter than its input be delivered through the caller's own object — a count, and
the first `count` positions — and then declined to say how the surviving values get into those
positions, on the grounds that it was the exercise rather than the reading. This is where that
stop is lifted.

So: is there a third algorithm? One that touches each element a fixed number of times, like the
second, while allocating nothing at all, like the first — linear time and constant space, at once,
on the same problem?

**Stop here, before the answer.** Sections 5 and 6 build it, and building it solves 283. Move
Zeroes and 905. Sort Array By Parity outright — the two stubs waiting in `arrays101/ch05/`, each
of which asks for exactly the pair of conditions this section has just failed to satisfy together.
Go and attempt both of them now, holding yourself to those two conditions: the list you were handed
is the only place the answer may go, and no element may be touched more than a fixed number of
times. Come back to section 5 either way — with something passing, or having run out of ideas.
Having been stuck on it is what makes the next section land.

---

## 5. The read cursor and the write cursor

Section 4 left the problem stated and unsolved. The answer is shorter than the input, the input is
the only place the answer may go, and closing each gap where it opens charges you the whole tail
behind it. The way out is to stop thinking about one position at a time and carry two.

**One index reads and one index writes, and they move at different speeds.** The read cursor visits
every position in turn and never goes back. The write cursor marks the slot the next kept element
belongs in, and advances only when something is kept. Where nothing has been dropped they sit on
the same slot; every drop puts one more slot between them, and the gap between them is exactly the
number of elements discarded so far.

Carrying two indices over one list like this is the **two-pointer technique**, one of the main
techniques for in-place array work, and it is worth knowing under that name: the name is what the
idea travels under in a problem's tags, in a conversation with an interviewer, in somebody else's
description of a loop. It has more than one arrangement. This section's is the two indices in
convoy, both starting at the front and moving right, one trailing the other and never overtaking
it; section 6 builds the other common arrangement, two indices starting at opposite ends and
converging on the middle. **`read` and `write` stay this chapter's working vocabulary**, because
those names say what each index is *for*, which "first pointer" and "second pointer" do not.

### The invariant, stated before the loop

Write the loop last. Start with what has to be true at the top of every step — before the element
at `read` has been looked at, with `original` naming the list's contents when the call began:

1. `write <= read`.
2. `buf[:write]` holds exactly the elements of `original[:read]` that pass the test, in the order
   they were in.
3. `buf[read:]` is untouched: still exactly `original[read:]`.

Clause 2 says the answer so far is already assembled at the front. Clause 3 says the part not yet
examined is still intact. Clause 1 is the one that makes those two compatible, and everything else
in this section falls out of it.

Now ask what a single step must do to leave all three true again with `read` one larger. If the
element passes, clause 2 needs it appended to the prefix, which means writing it at index `write`
and advancing `write` by one. If it fails, clause 2 needs nothing at all, so `write` stays. Either
way `read` advances by one. That is the whole body, and it was derived rather than guessed. Assert
the three clauses and run it against twenty thousand random inputs:

```python
def keep_above_checked(buf, threshold):
    original = list(buf)
    write = 0
    for read in range(len(buf)):
        assert write <= read
        assert buf[:write] == [x for x in original[:read] if x > threshold]
        assert buf[read:] == original[read:]
        if buf[read] > threshold:
            buf[write] = buf[read]
            write += 1
    assert buf[:write] == [x for x in original if x > threshold]
    return write

import random
random.seed(5)
for _ in range(20_000):
    keep_above_checked([random.randrange(6) for _ in range(random.randrange(9))], 2)
print("every invariant held at every step")
# -> every invariant held at every step
```

### Why the write cursor cannot overtake

Clause 1 is not an extra requirement bolted on beside the other two; it is what clause 2 already
says, restated as a count. Clause 2 puts exactly those elements of `original[:read]` that passed
into `buf[:write]`, so `write` is the *number* of elements among the first `read` that passed. A
count of how many members of a group of `read` things have some property cannot come out larger than
`read`. **So `write <= read` is not a condition the loop has to be careful to maintain; it is an
arithmetic fact about a count of a subset, and it needs no checking at run time.**

The loop body confirms it from the other side, which is worth seeing because it is the argument you
can run in your head while writing the code. Both cursors start at 0, so it holds before the first
step. Within a step `read` always advances by exactly one, and `write` advances by one or by zero.
An index that never gains on another and starts level with it never gets ahead.

That is what makes the overwriting safe. The write lands at index `write`, and `write <= read`, so
the slot being clobbered is one the read cursor has already passed or the one it is standing on. By
clause 3 nothing at or beyond `read` has been disturbed, so the value in that slot is either an
element already copied into the prefix, or one already examined and discarded, or — when the two
cursors coincide — the very element being copied, which makes the write a no-op. In none of those
cases is anything lost:

```python
buf = [21, 19, 24, 18, 22, 17, 20, 23]
write = 0
for read in range(len(buf)):
    if buf[read] > 19:
        print(f"overwriting slot {write}, which holds {buf[write]};"
              f" already read: {write <= read}")
        buf[write] = buf[read]
        write += 1
# -> overwriting slot 0, which holds 21; already read: True
# -> overwriting slot 1, which holds 19; already read: True
# -> overwriting slot 2, which holds 24; already read: True
# -> overwriting slot 3, which holds 18; already read: True
# -> overwriting slot 4, which holds 22; already read: True
```

Break clause 1 and the algorithm destroys its own input. Start the write cursor one slot ahead and
every write lands on an element that has not been read yet, so each read finds the value the
previous write put there:

```python
buf = [21, 24, 18, 22]
write = 1                            # the invariant is false from the first step
try:
    for read in range(len(buf)):
        if buf[read] > 19:
            buf[write] = buf[read]
            write += 1
except IndexError as e:
    print(e, write - 1, buf)
# -> list assignment index out of range 3 [21, 21, 21, 21]
```

One value smeared across the list, 24 and 22 gone, and the run ending by reaching past the last
index — a `write` that has got ahead runs out of list before `read` does. That `IndexError` is the
*lucky* outcome of breaking clause 1, because it is the one version of the failure that tells you
anything, and it is not the version you are owed. Let the first element fail the test and `write`
never leaves the list:

```python
quiet = [17, 21, 24, 22]             # the first element fails, so write never leaves the list
write = 1
for read in range(len(quiet)):
    if quiet[read] > 19:
        quiet[write] = quiet[read]
        write += 1
print(write - 1, quiet[:write - 1])  # -> 3 [17, 21, 24]
```

Three kept, says the count, and three is the right count — but the prefix holds 17, which the test
rejected, and not 22, which passed. Nothing raised and nothing looked odd.

### The loop, and the count it returns

With the derivation done, the code is short. Keeping only the readings above a threshold:

```python
readings = [21, 19, 24, 18, 22, 17, 20, 23]

def keep_above(buf, threshold):
    write = 0
    for read in range(len(buf)):
        if buf[read] > threshold:
            buf[write] = buf[read]
            write += 1
    return write

count = keep_above(readings, 19)
print(count)                # -> 5
print(readings[:count])     # -> [21, 24, 22, 20, 23]
print(readings)             # -> [21, 24, 22, 20, 23, 17, 20, 23]
```

The second and third lines are the same object printed twice, and only the second one is an answer.
This is the count-and-prefix contract chapter 3 section 6 set up: the meaningful elements are the
first `count` of them, the count travels separately from the list because no list has ever tracked
it, and everything from index `count` onward is outside the answer altogether. That section stopped
short of how a result gets into that shape, and this loop is how. `len(readings)` is still 8,
`count` is 5, and neither number is wrong.

### The price of not shifting

Section 4 ended by asking for one algorithm that is linear in time and constant in space at once.
The space half takes one measurement. `tracemalloc` watches the whole compaction, with `keep_above`
still the function defined above:

```python
import tracemalloc

bulk = [21 if i % 2 else 17 for i in range(200_000)]
held = bulk

tracemalloc.start()
tracemalloc.reset_peak()
kept = keep_above(bulk, 19)
peak = tracemalloc.get_traced_memory()[1]
tracemalloc.stop()

print(kept, peak)                # -> 100000 0
print(held is bulk, len(held))   # -> True 200000
```

A peak of zero. Two hundred thousand elements reduced to a hundred thousand meaningful ones without
a single traced byte allocated, because every write went to a slot that already existed. `held is
bulk` is chapter 1 section 9's test: the object the caller kept a name on is the object that
changed, and it is still 200,000 long.

Now the time half, and only half of that needs measuring here. Section 4 timed its deleting
algorithm at these same four sizes, on an input that dropped every second element — half of them,
alternating, which is the workload below as well — and watched each doubling of `n` multiply the
time by 3.81, then 3.92, then 3.95: squared growth, one shifted tail charged per drop. The open
question is what the cursor version does over that range. With the same half of the readings
dropped and the timing method of chapter 1 section 11 — a paired measurement with the input copy
subtracted as a baseline:

```python
import timeit

setup = """
def keep_above(buf, threshold):
    write = 0
    for read in range(len(buf)):
        if buf[read] > threshold:
            buf[write] = buf[read]
            write += 1
    return write

src = [21 if i % 2 else 17 for i in range(SIZE)]
"""

def ms(stmt, s, number):
    return min(timeit.repeat(stmt, setup=s, number=number, repeat=7)) / number * 1000

prev = None
for n in (5_000, 10_000, 20_000, 40_000):
    s = setup.replace("SIZE", str(n))
    base = ms("src.copy()", s, 200)
    c = ms("keep_above(src.copy(), 19)", s, 60) - base
    factor = "-" if prev is None else f"x{c / prev:.2f}"
    print(f"n = {n:<6} cursor {c:6.3f} ms {factor:>6}   per element {c * 1e6 / n:5.1f} ns")
    prev = c
# -> n = 5000   cursor  0.079 ms      -   per element  15.8 ns
# -> n = 10000  cursor  0.164 ms  x2.08   per element  16.4 ns
# -> n = 20000  cursor  0.321 ms  x1.95   per element  16.0 ns
# -> n = 40000  cursor  0.658 ms  x2.05   per element  16.4 ns
```

The right-hand column is the claim, and it is the one a growth factor cannot fake. Eight times as
much input and the cost of an element does not move: over seven sittings every entry in that column
landed between 15.5 and 17.6 ns, with the doubling factors between 1.92 and 2.17. **Linear means
that column is flat, and a flat column is something to look at rather than something to argue.**
Set it beside section 4's 3.81, 3.92, 3.95 on the same sizes and the same workload, and the two
algorithms are separated by a growth rate rather than by a constant factor — whatever the gap
between them is at one size, the next size doubles it.

Both of those readings are for one input, though, and they depend on a property of it that has to
be stated rather than assumed: how much gets dropped, and where it sits. Count the work exactly,
which unlike a timing reproduces digit for digit:

```python
n = 20_000
shapes = {
    "nothing dropped": [21] * n,
    "half, alternating": [21 if i % 2 else 17 for i in range(n)],
    "half, all at the front": [17] * (n // 2) + [21] * (n // 2),
    "half, all at the back": [21] * (n // 2) + [17] * (n // 2),
    "everything dropped": [17] * n,
}
for label, src in shapes.items():
    work = list(src)
    shifted = i = 0
    while i < len(work):
        if work[i] > 19:
            i += 1
        else:
            shifted += len(work) - i - 1
            del work[i]
    written = sum(1 for x in src if x > 19)
    print(f"{label:<23} shifted {shifted:>12,}   written {written:>6,}")
# -> nothing dropped         shifted            0   written 20,000
# -> half, alternating       shifted  100,000,000   written 10,000
# -> half, all at the front  shifted  149,995,000   written 10,000
# -> half, all at the back   shifted   49,995,000   written 10,000
# -> everything dropped      shifted  199,990,000   written      0
```

Left column: the elements the deleting version relocates, which is the tail length of each deletion
summed, chapter 3 section 3's `n - i - 1` charged once per drop. Right column: the writes the
cursor version performs, which is the number of elements kept and can never exceed `n`. Section 4
varied *how much* was dropped and watched a count like the left one run from nothing up to `n²/2`.
The three middle rows here hold that fixed — exactly half dropped, every time — and vary only
*where* the dropped elements sit, and the left column still moves by a factor of three:
49,995,000 with the dropped half at the back against 149,995,000 with it at the front. **A drop
early in the list is the expensive kind, because the tail it has to close over is longer** — the
same `n - i - 1`, charged at a small `i`. The right column notices none of it: 10,000 writes on all
three rows, because the number of writes is the number of elements kept and nothing about where
they were.

The top row is the honest caveat. With nothing dropped the deleting version never deletes, its left
column is zero, and it is a linear scan like the other one. At 20,000 elements the two land on top
of each other: across six runs the deleting version measured 0.419 to 0.440 ms and the cursor
version 0.414 to 0.453 ms, bands that overlap and are separated by less than the spread inside
either one, so no ordering between them is being claimed. **The cursor version's guarantee is that
its work is bounded by `n` whatever the input does; the deleting version's cost is a property of the
data, and it is worst exactly when the most is being removed.**

### Nothing dropped, everything dropped, and no input at all

The three cases that usually need special handling need none. Continuing from `keep_above` above:

```python
for data, threshold in (([5, 6, 7], 0), ([5, 6, 7], 99), ([], 0)):
    buf = list(data)
    print(keep_above(buf, threshold), buf)
# -> 3 [5, 6, 7]
# -> 0 [5, 6, 7]
# -> 0 []
```

Keep everything and the two cursors never separate, so every write is `buf[read] = buf[read]` and
the list ends identical to how it arrived. Keep nothing and `write` never leaves 0, so no write
happens at all and the list is again untouched — the return value carries the entire answer. An
empty list runs the body zero times and hands back the 0 `write` started at. None of these is a
branch you wrote; they are the invariant holding vacuously. Guarding the redundant self-write with
`if write != read` trades a write for a comparison and measures as a wash: across six runs at 20,000
elements the guarded form came in between 0.87 and 1.15 times the plain one, and which side of 1 it
lands on is decided by the input, not the guard — ahead on every run where nothing was dropped and
every write was redundant, behind on every run where half was dropped and the comparison almost
never saved one.

### The tail is garbage on purpose

Past `count` the list holds whatever the algorithm happened to leave — here the untouched original
positions 5 through 7, which is a coincidence of this input rather than a promise. Three
implementations, each calling the `keep_above` above and differing only in what it does afterwards
— three different lists, one answer:

```python
def keep_above_blanked(buf, threshold):
    count = keep_above(buf, threshold)
    for i in range(count, len(buf)):
        buf[i] = 0
    return count

def keep_above_shortened(buf, threshold):
    count = keep_above(buf, threshold)
    del buf[count:]
    return count

for fn in (keep_above, keep_above_blanked, keep_above_shortened):
    data = [21, 19, 24, 18, 22, 17, 20, 23]
    k = fn(data, 19)
    print(k, data, data[:k])
# -> 5 [21, 24, 22, 20, 23, 17, 20, 23] [21, 24, 22, 20, 23]
# -> 5 [21, 24, 22, 20, 23, 0, 0, 0] [21, 24, 22, 20, 23]
# -> 5 [21, 24, 22, 20, 23] [21, 24, 22, 20, 23]
```

Chapter 3 section 6 already made the verification point — two solutions may leave completely
different garbage past the count and both be correct — and the reason is visible here from the
producing side. Cleaning the tail is not tidiness, it is a claim: `keep_above_blanked` asserts that
those positions hold zeros, and zero is a perfectly legal reading. Anything written there is
invented data placed where the contract says nobody may look, and it costs writes that buy nothing.
Leaving it alone is the cheaper and the more truthful of the two. `keep_above_shortened` is a third
thing again — it changes the length, which is available only when the caller permits it, and hands
back a `count` that `len` now duplicates.

### The read cursor you do not have to write

`read` exists only to fetch `buf[read]`, and a `for` loop over the list already does that. The
length never changes here, so none of chapter 1 section 6's hazards around iterating a list whose
size is moving apply, and clause 3 guarantees the iterator has not been overtaken by the writes
behind it:

```python
def keep_above_iter(buf, threshold):
    write = 0
    for value in buf:
        if value > threshold:
            buf[write] = value
            write += 1
    return write

readings = [21, 19, 24, 18, 22, 17, 20, 23]
count = keep_above_iter(readings, 19)
print(count, readings[:count])       # -> 5 [21, 24, 22, 20, 23]
```

One index instead of two, and it is faster for the plain reason that it never indexes the list to
read — the iterator hands the value over directly. At 20,000 elements, across six runs at each
shape, it came out 1.27 to 1.45 times faster with nothing dropped, 1.42 to 1.57 with half dropped
and 1.63 to 1.79 with everything dropped. The three bands do not overlap and they rise in that
order, which is the part that reproduces; the figures themselves drift with the machine. That
ordering is not a fact about the two loops on their own, it is a fact about how much the input
drops. The saving is the same size per element whatever happens, so the
fewer writes are left standing beside it, the larger a fraction of the total it becomes. **The read
cursor is still there; it is the iterator's position, and the invariant is unchanged.** That is
worth holding onto, because the moment the algorithm needs to look at the element *before* the one
it is reading, the explicit index comes back and the invariant is what tells you whether the new
version is still safe. Section 4's problem needs exactly that.

### Back to the duplicates

Section 4 left a question standing: a sorted list, the duplicates removed, linear time and constant
space at once. Every test in this section so far has looked at `buf[read]` and nothing else, and
duplicate removal cannot. A value is a duplicate only relative to something else, and that
something else is the last value *kept* — which sits in the prefix this loop has been rewriting, at
`write - 1`:

```python
def dedupe(nums):
    write = 0
    for read in range(len(nums)):
        if write == 0 or nums[read] != nums[write - 1]:
            nums[write] = nums[read]
            write += 1
    return write

readings = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
count = dedupe(readings)
print(count, readings[:count])   # -> 5 [0, 1, 2, 3, 4]
print(readings)                  # -> [0, 1, 2, 3, 4, 2, 2, 3, 3, 4]

for case in ([], [5], [7, 7, 7, 7], [1, 2, 3]):
    buf = list(case)
    k = dedupe(buf)
    print(case, k, buf[:k])
# -> [] 0 []
# -> [5] 1 [5]
# -> [7, 7, 7, 7] 1 [7]
# -> [1, 2, 3] 3 [1, 2, 3]
```

Clause 2 licenses that test with no new argument required — read `buf` for `nums`, since the
clauses are about whatever list the loop was handed. `buf[:write]` holds exactly the kept elements
of `original[:read]` in the order they were in, so `buf[write - 1]` *is* the last element kept,
which is all the comparison wants. `write == 0` is the same clause read at the start, with
nothing kept yet and therefore nothing to be a duplicate of — which is why the empty list and the
single element need no special case here. They are that branch and a loop body that runs zero
times, not two extra `if`s bolted on.

Now the spelling that looks tempting, and the reason clause 3 was worth stating. Section 4's
deleting loop compared each element with its *neighbour*, and sortedness was what made a neighbour
comparison sufficient. Carry that test across unchanged and it reads `nums[read - 1]` — a slot
*behind* the read cursor, inside the stretch this loop has spent the entire run overwriting. Clause
3 speaks only from `read` onward and says nothing about it.

It is safe, and clause 3 was understated. A write lands at index `write` and `write` then advances,
so the highest index ever written is one below the current `write`: **everything from `write`
onward is still the original, not merely everything from `read` onward.** That covers `read - 1`
whenever `read - 1 >= write`. The one case left over is `read - 1 < write`, which together with
`write <= read` forces `write == read` — nothing dropped yet, so the prefix is the original prefix
element for element, and the slot holds its original value that way instead. Either branch, the
neighbour test reads what the input had there. Assert the stronger clause, count the steps at which
the slot had in fact been rewritten, and run both spellings against `sorted(set(...))`:

```python
def dedupe_prev(nums):
    original = list(nums)
    write = 0
    stale = 0
    for read in range(len(nums)):
        assert nums[write:] == original[write:]       # stronger than clause 3
        if read and nums[read - 1] != original[read - 1]:
            stale += 1
        if read == 0 or nums[read] != nums[read - 1]:
            nums[write] = nums[read]
            write += 1
    return write, stale

import random
from itertools import combinations_with_replacement

random.seed(26)
cases = [sorted(random.randrange(5) for _ in range(random.randrange(10)))
         for _ in range(50_000)]
cases += [list(c) for n in range(13) for c in combinations_with_replacement((0, 1, 2, 3), n)]

stale_steps = 0
for src in cases:
    a, b = list(src), list(src)
    ka = dedupe(a)
    kb, stale = dedupe_prev(b)
    assert a[:ka] == b[:kb] == sorted(set(src)), src
    stale_steps += stale
print(len(cases), stale_steps)   # -> 51820 0
```

Fifty thousand random sorted lists, plus every sorted list of twelve or fewer elements drawn from
four values: both spellings agree with each other and with `sorted(set(...))` on all 51,820, the
stronger clause holds at every step of every one, and `stale_steps` finishes at 0 — not once did
`nums[read - 1]` hold anything but its original value. **That is what writing the invariant down
before the loop buys you.** The test grew from a function of one element into a function of two,
one of them sitting behind the write cursor, and settling whether the loop was still correct took
no experimenting. It took reading off which clause covered the slot being touched.

---

## 6. Two indices from opposite ends

Section 5's read cursor and write cursor both started at the front and both travelled right, one
trailing the other and never overtaking it. Call that pair **the collecting shape** from here on,
and call what it does compaction: the kept elements gather into the prefix the write cursor is
filling, and the rest of the list is left as it falls. Wherever this chapter says the cursor
version, the cursor loop or a compaction, it means that one loop.

There is a second arrangement, **the converging shape**, and almost everything about it is
inverted. One index starts at 0 and the other at the last position; they move towards each other
rather than in convoy; the run ends when they meet in the middle rather than when one reaches the
end. Nothing is collected in front of a cursor. Positions are traded across the middle, which is
why this shape rearranges rather than compacts.

You have already used it. `list.reverse()` is this pair of indices with the condition removed —
every step an exchange, unconditionally — and chapter 1 section 8's table prices it at O(n) time
and O(1) space, "swaps pointers in place":

```python
def reverse_in_place(values):
    lo, hi = 0, len(values) - 1
    while lo < hi:
        values[lo], values[hi] = values[hi], values[lo]
        lo += 1
        hi -= 1

temps = [21, 19, 24, 18, 22, 17, 20]
reverse_in_place(temps)
print(temps)                # -> [20, 17, 22, 18, 24, 19, 21]

builtin = [21, 19, 24, 18, 22, 17, 20]
builtin.reverse()
print(builtin == temps)     # -> True
```

The exchange line is chapter 1 section 4's tuple assignment doing load-bearing work: the whole
right-hand side is evaluated before either write happens, so both reads complete before the first
value is destroyed. Written as two statements it would need a temporary, because the first store
would destroy a value the second one still needs. Written as one it needs no storage at all, and
section 3 already disassembled a swap of exactly this form — two subscript targets in one
statement — and found two subscript reads, a `SWAP` and two stores, with no `BUILD_TUPLE`: the
pair being held is a pair of stack slots and never an object. Nothing is allocated in between, so
**an in-place exchange costs no extra space worth naming**, and every rearrangement in this section
is built out of it.

### The invariant, and why the run ends

Reversal exchanges every pair it meets. The general shape exchanges only pairs whose two elements
are both on the wrong side, so each index needs a rule for when to advance and the loop needs a
reason to stop. Both fall out of one invariant, stated the same way section 5's was:

> Everything at an index below `lo` is settled and belongs where it is. Everything at an index
> above `hi` is settled and belongs where it is. The elements from `lo` to `hi` inclusive are the
> unsettled region, and nothing outside it will be touched again.

At the start `lo` is 0 and `hi` is the last index, so the settled regions are both empty and
everything is unsettled — the invariant holds trivially. Each iteration then asks two questions.
If the element at `lo` already belongs on the left, `lo` moves up by one and the left settled
region grows. Otherwise, if the element at `hi` already belongs on the right, `hi` moves down by one
and the right settled region grows. Otherwise both are on the wrong side, one exchange puts each of
them where it belongs, and both indices move — two positions settled in a single write pair.

Termination is the same three cases read differently. **Every branch either raises `lo` or lowers
`hi`, so `hi - lo` strictly decreases on every iteration, and a loop guarded by `lo <= hi` cannot
run more times than there are elements.** No arrangement of values can prevent that. The bound is a
condition you wrote rather than a fixed count of iterations, so the movement in every branch is the
only thing enforcing it. A branch that examined an element and left both indices where they were
would spin forever.

### Partitioning readings around a threshold

Take a run of sensor readings and a threshold, and put every reading below the threshold in front of
every reading at or above it. Nothing says what order they come out in within each group, and that
permission is what the shape needs.

```python
def partition(values, limit):
    lo, hi = 0, len(values) - 1
    while lo <= hi:
        if values[lo] < limit:
            lo += 1
        elif values[hi] >= limit:
            hi -= 1
        else:
            values[lo], values[hi] = values[hi], values[lo]
            lo += 1
            hi -= 1
    return lo

readings = [21, 34, 19, 40, 22, 17, 36, 20]
boundary = partition(readings, 30)
print(boundary, readings)                        # -> 5 [21, 20, 19, 17, 22, 40, 36, 34]
print(readings[:boundary], readings[boundary:])  # -> [21, 20, 19, 17, 22] [40, 36, 34]
```

The returned `boundary` is `lo` where the loop stopped, and it is exactly the count of readings
below the threshold — chapter 3 section 6's count-and-prefix convention arriving unbidden, because a
partition is a list plus the index where one group ends and the other begins. Print the three
regions on every pass and the invariant is visible as a squeeze:

```python
def partition_traced(values, limit):
    lo, hi = 0, len(values) - 1
    while lo <= hi:
        print(values[:lo], "|", values[lo:hi + 1], "|", values[hi + 1:])
        if values[lo] < limit:
            lo += 1
        elif values[hi] >= limit:
            hi -= 1
        else:
            values[lo], values[hi] = values[hi], values[lo]
            lo += 1
            hi -= 1
    print(values[:lo], "|", values[lo:hi + 1], "|", values[hi + 1:])

partition_traced([21, 34, 19, 40, 22, 17, 36, 20], 30)
# -> [] | [21, 34, 19, 40, 22, 17, 36, 20] | []
# -> [21] | [34, 19, 40, 22, 17, 36, 20] | []
# -> [21, 20] | [19, 40, 22, 17, 36] | [34]
# -> [21, 20, 19] | [40, 22, 17, 36] | [34]
# -> [21, 20, 19] | [40, 22, 17] | [36, 34]
# -> [21, 20, 19, 17] | [22] | [40, 36, 34]
# -> [21, 20, 19, 17, 22] | [] | [40, 36, 34]
```

Seven lines with six steps between them, and the middle column shrinks at every step — by two where
an exchange happened, by one otherwise. The outer columns only ever grow, and once a position has
joined one of them nothing writes to it again: over twenty thousand random lists no position was
ever written more than once. When the middle empties, the answer is the two columns beside it.

Comparisons are a separate count and the two are easy to conflate. **Every position is settled
once; a position may be looked at more than once.** The trace above makes nine comparisons for
eight elements, and 40 is the element paying for it — it sits at `lo` while the fourth pass steps
`hi` down past 36, and the fifth pass has to ask about it again. That is the price of a branch that
retires only one end: the other end's element was examined for nothing.

The guard is `lo <= hi` and not `lo < hi`, and the invariant is what decides that. The loop may stop
only when the unsettled region is empty, and at `lo == hi` the region still holds one element that
nothing has classified. Stop there and that element is never asked about: it stays where it sits,
and the boundary comes back on the wrong side of it whenever it belonged on the left.

```python
def partition_early(values, limit):        # the same loop, guarded lo < hi
    lo, hi = 0, len(values) - 1
    while lo < hi:
        if values[lo] < limit:
            lo += 1
        elif values[hi] >= limit:
            hi -= 1
        else:
            values[lo], values[hi] = values[hi], values[lo]
            lo += 1
            hi -= 1
    return lo

from itertools import product

wrong = grouped_wrong = total = 0
for n in range(1, 13):
    for bits in product((0, 1), repeat=n):
        values = [10 if b else 40 for b in bits]
        want = sum(bits)
        got = partition_early(values, 30)
        total += 1
        wrong += got != want
        grouped_wrong += not (all(x < 30 for x in values[:want])
                              and all(x >= 30 for x in values[want:]))
print(total, wrong, grouped_wrong)   # -> 8190 2048 0
```

Over every list of twelve elements or fewer built from one value below the threshold and one above,
the early guard returns the wrong boundary on 2,048 of 8,190 — always low by exactly one, and only
when the element stranded at `lo == hi` belonged on the left. **The third count is the warning: the
arrangement is never wrong.** The list comes back correctly grouped in all 8,190 cases, so a check
that asks only whether the two groups ended up separated passes every one of them. The returned
index is the only place the missing step shows.

### The same job in the other shape

Section 5's cursors can partition too, with one change, and the change is the interesting part.
There the write was a plain overwrite, `buf[write] = buf[read]`, and it was allowed to be one
because the elements failing the test were being thrown away — whatever stood in the write slot was
expendable by construction. A partition throws nothing away. Both groups are part of the answer, so
the value sitting in the write slot has to survive, and the one position guaranteed to be free for
it is the slot the incoming element just vacated. **The overwrite becomes an exchange, and that is
the entire difference between compacting and partitioning in this shape.**

```python
def collect(values, limit):
    write = 0
    for read in range(len(values)):
        if values[read] < limit:
            values[write], values[read] = values[read], values[write]
            write += 1
    return write

start = [21, 34, 19, 40, 22, 17, 36, 20]
a, b = list(start), list(start)
print(collect(a, 30), a)             # -> 5 [21, 19, 22, 17, 20, 40, 36, 34]
print(partition(b, 30), b)           # -> 5 [21, 20, 19, 17, 22, 40, 36, 34]
print([x for x in start if x < 30])  # -> [21, 19, 22, 17, 20]
print([x for x in start if x >= 30]) # -> [34, 40, 36]
```

Same input, same boundary of 5, same two groups, two different lists. Read the third line against
the first two and the difference has a name. `collect` produced the below-threshold group in exactly
the order the readings arrived; `partition` produced 20 before 19 and 17 before 22, an order the
input never had. Neither preserved the above-threshold group, which is a limit worth stating:
**the collecting shape preserves the relative order of the group it is collecting, and of that
group only.**

That axis has a name you already have. Chapter 1 section 8 called a sort **stable** when elements
that compare equal keep the order they were in, and the same word does the same work here, with
"compare equal" meaning "land in the same group". The collecting shape is stable on the group it
collects and on nothing else; the converging shape guarantees stability on neither group, and the
5,913 arrangements below put a number on how thoroughly. So the collecting shape is right when the
order of what you keep is part of the answer — you are pulling a subsequence out of a sequence, and
a subsequence is by definition still in the sequence's order. The converging shape is right when
you are rearranging into groups and the question asks only which group each element lands in.
Decide which of those two sentences describes the problem in front of you and the shape follows.

How reliably does the converging shape scramble? Run both over every permutation of a small list:

```python
from itertools import permutations

out_of_order = {"partition": 0, "collect": 0}
cases = 0
for n in range(1, 8):
    for perm in permutations(range(n)):
        limit = n // 2
        kept = [x for x in perm if x < limit]
        for name, fn in (("partition", partition), ("collect", collect)):
            values = list(perm)
            fn(values, limit)
            if values[:len(kept)] != kept:
                out_of_order[name] += 1
        cases += 1
print(cases, out_of_order)
# -> 5913 {'partition': 4980, 'collect': 0}
```

Out of 5,913 arrangements, `partition` left the kept group out of its original order in 4,980 and
`collect` in none. Reordering is not a rare accident of the converging shape but its usual outcome,
and nothing in the loop protects the 933 that came through in order. They are the arrangements
where no exchange happened to carry a kept element in front of another kept element that started
ahead of it. Nine of the 933 had fewer than two kept elements and so had no order to lose, and in
200 of them the loop was never forced to exchange anything at all.

### Counting the exchanges

The order guarantee is paid for in writes, and the two differ in a way that does not depend on the
input. Instrument both and count, still on the `start` readings above:

```python
import random

def counted_partition(values, limit):
    lo, hi, swaps, steps = 0, len(values) - 1, 0, 0
    while lo <= hi:
        steps += 1
        if values[lo] < limit:
            lo += 1
        elif values[hi] >= limit:
            hi -= 1
        else:
            values[lo], values[hi] = values[hi], values[lo]
            swaps += 1
            lo += 1
            hi -= 1
    return swaps, steps

def counted_collect(values, limit):
    write, swaps = 0, 0
    for read in range(len(values)):
        if values[read] < limit:
            values[write], values[read] = values[read], values[write]
            swaps += 1
            write += 1
    return swaps, len(values)

print(counted_partition(list(start), 30), counted_collect(list(start), 30))
# -> (2, 6) (5, 8)

random.seed(2026)
big = [random.randrange(100) for _ in range(2000)]
for limit in (30, 50):
    below = sum(1 for x in big if x < limit)
    past = sum(1 for i, x in enumerate(big) if i >= below and x < limit)
    print(limit, below, past,
          counted_partition(list(big), limit), counted_collect(list(big), limit))
# -> 30 577 418 (418, 1582) (577, 2000)
# -> 50 977 515 (515, 1485) (977, 2000)
```

On the eight readings, 2 exchanges against 5, in 6 loop passes against 8. On 2,000 values with the
threshold at 30, 418 against 577; at 50, 515 against 977. The pattern is exact rather than
statistical, and both columns have closed forms. `collect` exchanges once for every element that
belongs on the left, since each is written into the write position — 577 and 977, the `below`
column, matching to the unit. `partition` exchanges once for every element that belongs on the left
*and started at or past the boundary* — the `past` column, 418 and 515, again to the unit. Those
are a subset of the same elements, so **the converging shape can never make more exchanges than the
collecting one, and makes fewer by exactly the number of left-group elements that already start
inside the stretch the left group will occupy** — 159 of the 577 at threshold 30, 462 of the 977 at
50. Elements that begin on the correct side of the eventual boundary are stepped over for free.
Over 30,000 randomly generated lists both identities held every time, as did both loop counts:
`collect` always runs `len(values)` passes and `partition` between half that and all of it,
depending on how many passes retire two positions instead of one.

One honest subtraction from `collect`'s column, since it is the one being counted against. Some of
its exchanges have `write` and `read` on the same slot, and swap a value with itself — the redundant
self-write section 5 weighed and left in. There is 1 of those in the 5 on the eight readings, 1 of
the 577 and 2 of the 977 on the two thousand. Striking them out does not disturb the conclusion:
across 50,000 random lists `partition`'s swap count never once exceeded `collect`'s with the
self-writes already removed.

---

**Notice: the subsection below is aimed straight at the problems in `arrays101/ch05/`.** It gives
you the criterion for choosing between the two shapes, not the verdict on any one problem — the
matching is left to you deliberately. If you would rather reach even the criterion yourself, stop
here, go and solve them, and come back to check your reasoning against this.

---

### Reading a statement for the shape it wants

None of this decides an implementation for you, but it narrows the choice to one line of reading in
the problem statement. Three questions, in order, each answered by a clause you either find in the
words you were given or fail to find.

*Does anything move position at all?* Some rewrites change only the value standing at each position
and never which position an element occupies. Neither shape applies to those — there is no pair to
exchange and no group to gather, and section 3's one-position-at-a-time discipline is the whole of
what is needed. Ask it first, because both shapes are machinery for moving elements and a statement
that moves none of them will accept the machinery anyway and be the worse for it.

*Is the relative order within a group part of the answer?* A statement saying the order of some
group must be maintained rules the converging shape out on sight; the 4,980 permutations above are
precisely what such a clause exists to forbid. The collecting shape preserves order for the group
it gathers and for no other, so check that the group named in the clause is the group you would be
gathering.

*Or is any arrangement meeting the condition accepted?* Wording that asks for any result satisfying
the condition, with no ordering clause anywhere, is a permission rather than an oversight, and that
permission is what the converging shape needs. **Where it is granted, both shapes are legal and the
choice stops being about correctness** — which is where the swap counts of the previous subsection
turn from a curiosity into the grounds to decide on.

Read each statement in `arrays101/ch05/` for those clauses before you write anything.

Section 7 takes the question this chapter has so far assumed away: when writing into the caller's
list is the wrong thing to do at all.

---

## 7. When not to do it in place

The cursor's whole advantage is that it allocates nothing. Its whole cost is that the input is gone
when it finishes. Sections 5 and 6 built the invariant that makes the overwriting correct; this one
is about the cases where correct overwriting is still the wrong thing to do.

### The damage does not surface where you caused it

Here is a compaction written as a helper, a name bound before it runs, and a second function that
reads that name afterwards.

```python
def keep_positive(nums):
    w = 0
    for r in range(len(nums)):
        if nums[r] > 0:
            nums[w] = nums[r]
            w += 1
    del nums[w:]

def mean_reading(archive):
    return sum(archive) / len(archive)

readings = [3, -1, 4, -1, 5]
archive = readings                      # kept for the end-of-run report

keep_positive(readings)
print(readings, archive)                # -> [3, 4, 5] [3, 4, 5]
print(mean_reading(archive))            # -> 4.0
```

`archive` was bound before the call and never passed to it, and it changed anyway. Chapter 1
section 9 is the mechanism in full: assignment binds a second name to the one list, a parameter is
a third, and **a name tells you nothing about how many other names are bound to the same object.**

The last line is the part that costs you a day. The mean of the readings is 2.0; `mean_reading`
prints 4.0, the mean of the survivors, and 4.0 is a perfectly ordinary number for sensor readings to
produce. Nothing raised, nothing looked odd, and the function that returns the wrong answer never
touched the list — it was handed a name that had been correct when it was bound. An in-place bug is
not usually a crash; it is a plausible answer computed somewhere you were not looking.

### Copy when the list is not yours

If you cannot establish that you own the object, take one:

```python
def positives(values):
    values = list(values)               # your own list from here on
    w = 0
    for r in range(len(values)):
        if values[r] > 0:
            values[w] = values[r]
            w += 1
    del values[w:]
    return values

log = [3, -1, 4, -1, 5]
print(positives(log), log)              # -> [3, 4, 5] [3, -1, 4, -1, 5]
```

Now be honest about what that bought. Chapter 1 section 8 rates `list(nums)` at O(n) time **and
space**, so the copy costs exactly the allocation the cursor existed to avoid: `positives` is O(n)
space, a comprehension's class, with four more lines and a mutable index to keep correct. **Once you
have decided to copy, the cursor has nothing left to offer, and the comprehension is the better
version of the same function** — `return [v for v in values if v > 0]`.

The copy is the right move when the loop in the middle is genuinely more than a filter, not a way to
keep the technique while dodging its consequences.

### Say so loudly when the list is yours

When mutating the argument *is* the contract, the docstring says it in the first line, and the name
helps. Python's own pairs are the model: `sorted(nums)` hands back a new list, `nums.sort()`
rewrites the one you have; `reversed(nums)` is a lazy iterator, `nums.reverse()` rewrites in place.
The participle builds, the imperative mutates. Put the warning in the name, the first line of the
docstring and the return type, all saying the same thing:

```python
def compact_positives(nums):
    """Rewrite nums in place; return how many entries at the front are the answer.

    MUTATES nums. The caller keeps the object it passed in and reads nums[:count].
    The original contents are not recoverable afterwards.
    """
    w = 0
    for r in range(len(nums)):
        if nums[r] > 0:
            nums[w] = nums[r]
            w += 1
    return w

log = [3, -1, 4, -1, 5]
count = compact_positives(log)
print(count, log[:count])               # -> 3 [3, 4, 5]
print(len(log))                         # -> 5
```

A docstring that buries "modifies its argument" in the third paragraph has not warned anybody.

### A mutator returns None

Of the eight list methods that mutate, seven return `None`:

```python
nums = [3, 1, 2]
print([nums.append(4), nums.insert(0, 0), nums.extend([5]),
       nums.sort(), nums.reverse(), nums.remove(5), nums.clear()])
# -> [None, None, None, None, None, None, None]

nums = [3, 1, 2]
print(nums.pop(), nums)                 # -> 2 [3, 1]
```

`pop` is the eighth, and what it hands back is the element it removed — available nowhere else once
it is gone. What no mutating list method returns is the list. That is a design decision, and what it
buys is that a call site misreading a mutation as a computation fails on the spot:

```python
scores = [7, 3, 9]
try:
    top = scores.sort()[:2]
except TypeError as e:
    print(e)            # -> 'NoneType' object is not subscriptable

try:
    scores.sort().reverse()
except AttributeError as e:
    print(e)            # -> 'NoneType' object has no attribute 'reverse'

print(sorted([5, 1, 4])[:2])   # -> [1, 4]   chaining is for the function that builds
```

`scores.sort()` reads as a statement because it *is* one, and `None` makes every attempt to use it
as an expression raise immediately. Now add the one line that throws that away:

```python
def keep_positive(nums):
    w = 0
    for r in range(len(nums)):
        if nums[r] > 0:
            nums[w] = nums[r]
            w += 1
    del nums[w:]
    return nums                         # the line that causes the trouble

raw = [3, -1, 4, -1, 5]
clean = keep_positive(raw)
print(clean, raw)                       # -> [3, 4, 5] [3, 4, 5]
print(clean is raw)                     # -> True

raw = [3, -1, 4, -1, 5]
print(keep_positive(raw)[:2])           # -> [3, 4]
print(raw)                              # -> [3, 4, 5]
```

`clean` is not a cleaned copy of `raw`. It is `raw` under a second name your own function handed
out, and every later `clean.append(...)` lands on the caller's list too. The last two lines are
worse: `keep_positive(raw)[:2]` is a subscripted function call — the shape of an expression that
reads its argument — and it destroyed its argument. Returning `None` would have made that line a
`TypeError` on the day it was written.

Returning a *count* is a different thing and stays fine, for exactly the reason `pop` is allowed a
return value: a count is information the list cannot carry about itself, which is the point of the
convention chapter 3 section 6 sets out. The value to refuse to return is the object the caller
already has.

One of this chapter's three problems demands the shape this subsection has just argued against, and
it is worth meeting that on purpose rather than as a surprise. 1299 in `arrays101/ch05/` requires
you to rewrite `arr` *and* hand `arr` back, and its suite checks identity rather than equality, so a
fresh list with perfect contents fails and so does `return None`. 283 next door requires the
opposite: rewrite `nums` and return `None`, and `return nums` after a flawless rewrite fails there.
Neither is a matter of taste. **A convention is what governs when the caller has not said; these
callers have said**, and question 3 below is the one they are answering. What does not change is
what the returned object *is* — 1299's caller is told in advance that what comes back is the list it
passed in, so the alias is the contract rather than a copy handed out under a misleading name.

### Do not rewrite what something else is walking

Chapter 1 section 6 covers this from the deletion side; compaction hits it harder, because it moves
elements *and* trims the length in one pass:

```python
nums = [3, 0, 5, 0, 7]
it = iter(nums)
print(next(it), next(it))               # -> 3 0

w = 0                                   # the same compaction, inline
for r in range(len(nums)):
    if nums[r] > 0:
        nums[w] = nums[r]
        w += 1
del nums[w:]

print(nums)                             # -> [3, 5, 7]
print(list(it))                         # -> [7]
```

The `5` is never delivered. It moved from index 2 to index 1 — behind an iterator whose position was
already 2 — and the trim then cut the length to 3, so the walk stopped one element later. The
consumer took three values out of a five-element list, two from before the rewrite and one from
after, and nothing raised.

There is a quieter version with no length change at all:

```python
temps = [18, 21, 19, 24]
seen = []
for t in temps:
    seen.append(t)
    if len(seen) == 1:
        for i in range(len(temps)):
            temps[i] = 0
print(seen, temps)                      # -> [18, 0, 0, 0] [0, 0, 0, 0]
```

Chapter 1 section 6 says reassigning existing slots during iteration is safe, and it is — safe means
the loop's arithmetic stays correct and no element is skipped. It does not mean the reader receives
the values it began reading. Section 3's rewrites are the safest thing in this chapter and they
still change what a concurrent walk observes.

### The space has to be worth the reader's time

The comprehension says what it produces; the cursor loop says how, in six lines, and a reader has to
carry two indices and a trim before the answer is visible as "the survivors, at the front". Everyone
who reads it afterwards pays that, so **a reviewer who asks why this is a loop is asking a fair
question, and the answer has to be a number.**

Section 2 ended with the opposite result — an in-place rewrite ahead of the comprehension by 12.79x
— so put the two side by side before the table below reads as a contradiction. The rewrite there
kept the length and touched one slot in eight, 12,500 slots against the 100,000 elements the
comprehension had to produce regardless, so its advantage was the slots it skipped and grew as that
fraction fell. A compaction has no fraction to shrink: it reads every element to decide and writes
on each survivor, more per element than the comprehension it replaces rather than less, and nothing
below inverts the ordering the way that row did.

Two properties of the input move that figure, so vary both: how much survives, and whether the
survivors sit together or are mixed through. Both statements start with the copy the cursor needs in
order to have something to destroy, timed separately and subtracted. The four rows at the end hold
the survival fraction at half and change nothing but the layout.

```python
import random, timeit

N = 100_000
COPY = "nums = list(base)\n"
COMP = COPY + "out = [v for v in nums if v > 0]"
CURSOR = COPY + """
w = 0
for r in range(len(nums)):
    if nums[r] > 0:
        nums[w] = nums[r]
        w += 1
del nums[w:]
"""

def ms(stmt, base, number=20):
    return min(timeit.repeat(stmt, globals={"base": base}, number=number, repeat=5)) / number * 1e3

def pair(base):                          # comprehension, cursor; the copy subtracted from both
    copy = ms(COPY, base, 200)
    return ms(COMP, base) - copy, ms(CURSOR, base) - copy

random.seed(7)
print("kept    one block      mixed through")
for pct in (0, 25, 50, 75, 100):
    block = [1] * (N * pct // 100) + [-1] * (N - N * pct // 100)
    print("%4d%%  %5.2f %5.2f    %5.2f %5.2f"
          % (pct, *pair(block), *pair(random.sample(block, N))))

half = [1] * (N // 2) + [-1] * (N // 2)
print("same 50,000 kept, four layouts")
for name, base in (("one block   ", half),
                   ("alternating ", [1 if i % 2 == 0 else -1 for i in range(N)]),
                   ("runs of four", [1 if (i // 4) % 2 == 0 else -1 for i in range(N)]),
                   ("mixed       ", random.sample(half, N))):
    print("  %s  kept %d   %5.2f %5.2f" % (name, sum(1 for v in base if v > 0), *pair(base)))
# -> kept    one block      mixed through
# ->    0%   0.45  0.94     0.43  0.93
# ->   25%   0.48  1.22     0.77  1.68
# ->   50%   0.52  1.44     1.04  2.29
# ->   75%   0.54  1.73     0.84  2.18
# ->  100%   0.60  1.97     0.58  1.95
# -> same 50,000 kept, four layouts
# ->   one block     kept 50000    0.56  1.47
# ->   alternating   kept 50000    0.56  1.49
# ->   runs of four  kept 50000    0.58  1.75
# ->   mixed         kept 50000    1.01  2.27
```

**The cursor loop was slower in every cell**, by a factor between roughly two and four, and that
held over six runs of the whole table. The ordering is the only reading here that does not move with
the input. Every other one does, and quoting any of them without saying what the input looked like
is how a benchmark becomes a lie.

Read down the one-block pair and both figures climb with the survival fraction, the cursor's the
faster of the two. The bytecode accounts for that much: the cursor subscripts and compares on every
element, then on each *survivor* pays a second subscript, a `STORE_SUBSCR` and an increment, against
one `LIST_APPEND` for the comprehension. More survivors, more work the cursor is doing and the
comprehension is not.

Read down the mixed pair and the climb is gone. Both figures peak at half and come back down, and by
100% the mixed column has fallen back onto the one-block column. So survival fraction is not the
property, and the last four rows isolate the one that is: the same 50,000 survivors, four layouts,
and the three regular arrangements all sit well below the random one in both columns. Measured
against the solid block, the random layout cost about 1.8x in the comprehension and about 1.5x in
the cursor. Strict alternation is the row that settles it — it splits the input exactly in half,
element by element, and it prices with the solid block rather than with the random one. **What costs
is how irregular the keep-or-drop decision is from one element to the next**, and 0% and 100% are
the two fractions no arrangement can make irregular, which is why the mixed column has to come back
down and meet the other one at both ends.

What survives all of that is the ordering and its cause. **The in-place compaction is not the fast
version — it is the version that does not allocate**, and those are not the same claim.

So price the allocation it avoids, exactly:

```python
import sys
for n in (20, 5_000, 10_000):
    print(n, sys.getsizeof(list(range(n))))
# -> 20 216
# -> 5000 40056
# -> 10000 80056
```

Eight bytes per slot plus a 56-byte header, and pointers only — a copied list shares the integer
objects with the original. So at the ceiling of this chapter's three problems the entire saving is
80,056 bytes: eighty kilobytes, once, transient. Worth having when the surrounding code holds a
hundred such lists, or when the problem statement says in so many words that no copy is allowed,
which one of the three in `arrays101/ch05/` does. Not worth having in a function that runs once on
twenty elements and will be read by somebody else on a Tuesday.

### Five questions before you overwrite

Chapter 3 section 7 asks five before you delete. These are the five for writing over what is there.

1. **Do I own this object?** A list that arrived as a parameter belongs to the caller. If the
   contract does not say you may rewrite it, copy or build a new one.
2. **Is the original still needed?** By you later in the function, by the caller after you return,
   by an aggregate somebody computes at the end of the run. Overwriting is not undoable.
3. **Does the caller read the return value, or the object?** Pick one and make the signature say
   so. Mutate and return `None`, or build and return the new list. Doing both hands out an alias
   dressed as a copy.
4. **Is the space saving real at this size?** Multiply it out before you defend the loop.
5. **Can I state the invariant that makes the overwriting safe?** Sections 5 and 6 each have one —
   the write index never passes the read index; everything outside the two ends is already settled
   and will not be touched again. If you cannot say yours in a sentence, you have not got one, and
   the loop is guesswork that happens to pass its tests.

Questions 1 and 2 are answered by the caller, and where they are uncertain the answer is the
comprehension. Question 5 is answered by you, and it is the only one no reviewer can check for you.

---

## 8. Drills

Ten snippets, and the procedure from the earlier chapters unchanged: predict in writing, then run,
then read the key — in that order and no other. A prediction has to be exact, down to the list
contents, the integer beside them, and the order the lines come out in, because "it changes the
list" is not a claim that can be wrong in the way that teaches you anything. Every output in the
key was produced by running the snippet on CPython 3.14.4. Nothing here is timed; the cost claims
live in the sections before this one. What you are being tested on is which object each line
touched, what is left in it afterwards, and how much of what is left is the answer.

### The drills

**Drill 1.**

```python
def zero_out_rebind(nums):
    nums = [0] * len(nums)

def zero_out_slice(nums):
    nums[:] = [0] * len(nums)

a = [3, 5, 8]
zero_out_rebind(a)
print(a)                       # ?

b = [3, 5, 8]
zero_out_slice(b)
print(b)                       # ?

c = [3, 5, 8]
held = c
c = [1, 2, 3]
print(held, c)                 # ?

d = [3, 5, 8]
held = d
d[:] = [1, 2, 3]
print(held, held is d)         # ?
```

**Drill 2.**

```python
def doubled(nums):
    for i in range(len(nums)):
        nums[i] *= 2
    return nums

original = [1, 2, 3]
result = doubled(original)
print(result)                  # ?
print(original)                # ?
print(result is original)      # ?

original.append(4)
print(result)                  # ?

snapshot = doubled(original[:])
print(snapshot, original)      # ?
```

**Drill 3.**

```python
nums = [10, 20, 30, 40]
nums[0], nums[3] = nums[3], nums[0]
print(nums)                    # ?

other = [10, 20, 30, 40]
other[0] = other[3]
other[3] = other[0]
print(other)                   # ?

xs = [7, 8, 9]
i = 1
xs[i], i = 99, 0
print(xs, i)                   # ?

ys = [7, 8, 9]
j = 1
j, ys[j] = 0, 99
print(ys, j)                   # ?
```

**Drill 4.**

```python
a = [1, 2, 3]
alias = a
a.reverse()
print(a, alias)                # ?
print(a.reverse())             # ?
print(a)                       # ?

b = [1, 2, 3]
alias = b
b = b[::-1]
print(b, alias)                # ?

c = [1, 2, 3]
alias = c
c[:] = c[::-1]
print(c, alias, c is alias)    # ?
```

**Drill 5.**

```python
nums = [1, 2, 3, 4, 5]
nums[1:3] = [9]
print(nums, len(nums))         # ?

nums = [1, 2, 3, 4, 5]
nums[1:3] = [7, 7, 7, 7]
print(nums, len(nums))         # ?

nums = [1, 2, 3, 4, 5]
nums[1:3] = []
print(nums)                    # ?

nums = [1, 2, 3, 4, 5]
nums[::2] = [0, 0, 0]
print(nums)                    # ?

nums = [1, 2, 3, 4, 5]
try:
    nums[::2] = [0, 0]
except ValueError as e:
    print(type(e).__name__, e)  # ?

nums = [1, 2, 3, 4, 5]
nums[1:3] = "ab"
print(nums)                    # ?
```

**Drill 6.** Each block is meant to replace every element from position 1 onward with the sum of it
and the element before it.

```python
nums = [1, 2, 3, 4]
for i in range(1, len(nums)):
    nums[i] = nums[i] + nums[i - 1]
print(nums)                    # ?

nums = [1, 2, 3, 4]
for i in range(len(nums) - 1, 0, -1):
    nums[i] = nums[i] + nums[i - 1]
print(nums)                    # ?

nums = [1, 2, 3, 4]
print([nums[i] + nums[i - 1] for i in range(1, len(nums))])   # ?
```

**Drill 7.**

```python
def compact(nums, unwanted):
    w = 0
    for r in range(len(nums)):
        if nums[r] != unwanted:
            nums[w] = nums[r]
            w += 1
    return w

nums = [4, 1, 7, 3]
print(compact(nums, 9), nums, len(nums))   # ?

nums = [4, 1, 7, 3]
print(compact(nums, 4), nums)              # ?

nums = []
print(compact(nums, 4), nums)              # ?

nums = [9, 9, 9]
print(compact(nums, 9), nums)              # ?
```

**Drill 8.**

```python
readings = [21, 5, 24, 3, 22]
w = 0
for r in range(len(readings)):
    if readings[r] >= 20:
        readings[w] = readings[r]
        w += 1
print(w, readings)                     # ?
print(readings[:w], readings[w:])      # ?
print(len(readings), 22 in readings[w:])   # ?

readings[w:] = []
print(readings, len(readings))         # ?
```

**Drill 9.**

```python
nums = [3, 1, 2]
print(nums.sort())             # ?
print(nums)                    # ?

nums = [3, 1, 2]
nums = nums.sort()
print(nums)                    # ?

nums = [3, 1, 2]
print(sorted(nums), nums)      # ?

nums = [3, 1, 2]
print(nums.append(4), nums)    # ?

try:
    [3, 1, 2].sort().reverse()
except AttributeError as e:
    print(type(e).__name__, e)  # ?
```

**Drill 10.**

```python
grid = [[0, 0], [0, 0]]
row = grid[0]
row[0] = 9
print(grid)                    # ?

rows = [[0, 0]] * 2
rows[0][0] = 9
print(rows)                    # ?

fresh = [[0, 0] for _ in range(2)]
fresh[0][0] = 9
print(fresh)                   # ?

nums = [1, 2, 3]
snap = nums
copy = nums[:]
nums[0] = 99
print(snap, copy)              # ?
print(snap is nums, copy is nums)   # ?
```

### The answer key

**1.** `[3, 5, 8]` / `[0, 0, 0]` / `[3, 5, 8] [1, 2, 3]` / `[1, 2, 3] True`. `nums = ...` binds the
local name to a new list and the caller's object is never touched; `nums[:] = ...` writes through
the name into the object every holder shares. The last two blocks are the same distinction with no
function in sight: rebinding `c` leaves `held` pointing at the old list, while the slice assignment
to `d` is seen through `held` because there is only one list. **Two spellings that differ by the
three characters of `[:]`, and only one of them is in place.** (Sections 1 and 3; chapter 1
sections 5 and 9.)

**2.** `[2, 4, 6]` / `[2, 4, 6]` / `True` / `[2, 4, 6, 4]` / `[4, 8, 12, 8] [2, 4, 6, 4]`. The
function rewrites the slots and hands the same object back, so `result` and `original` are two
names for one list — `is` says so, and appending through one name shows up through the other. The
shape reads like a before and an after and is nothing of the kind. Passing `original[:]` is what
actually produces a snapshot: a separate list to work on, leaving the input as the caller left it.
**A returned value proves nothing about whether a copy was made.** (Sections 1 and 7; chapter 1
section 9.)

**3.** `[40, 20, 30, 10]` / `[40, 20, 30, 40]` / `[7, 99, 9] 0` / `[99, 8, 9] 0`. The right-hand
side of an assignment is fully evaluated before any target is written — chapter 1 section 4's
rule — so the tuple form completes both reads before either store fires, and no temporary of your
own is needed. Nor is one built for you: section 3 disassembled this exact statement and found two
subscript loads, a `SWAP` and two stores, with no `BUILD_TUPLE` anywhere, so for two targets the
held pair is a pair of stack slots and never an object. The two-step version destroys `other[0]`
before it has been read, and the second line copies the value it just wrote — 10 is gone. The last
two blocks show the other half of the rule, which section 3 also states: **targets are assigned
left to right**, so `xs[i]` is computed with the old `i` while `ys[j]` is computed with the `j`
that the same statement has already changed. (Section 3; chapter 1 section 4.)

**4.** `[3, 2, 1] [3, 2, 1]` / `None` / `[1, 2, 3]` / `[3, 2, 1] [1, 2, 3]` /
`[3, 2, 1] [3, 2, 1] True`. `reverse()` rearranges the slots of the one list, so `alias` sees it,
and it returns `None` — printing the call reverses the list a second time and then prints `None`
rather than the list you were hoping to see, which is why the following line is back to
`[1, 2, 3]`. `b = b[::-1]` builds a reversed copy and rebinds, which costs a second list and
leaves `alias` on the original. `c[:] = c[::-1]` also builds the copy, but
then overwrites the slots with it, so it is visible through `alias` while still paying for the
temporary. **In place is a property of what the statement does to the object, not of whether the
list ends up looking right.** (Sections 1, 3 and 6; chapter 1 section 9.)

**5.** `[1, 9, 4, 5] 4` / `[1, 7, 7, 7, 7, 4, 5] 7` / `[1, 4, 5]` / `[0, 2, 0, 4, 0]` /
`ValueError attempt to assign sequence of size 2 to extended slice of size 3` /
`[1, 'a', 'b', 4, 5]`. A contiguous slice assignment replaces the selected run with whatever the
right-hand side yields and moves the tail to fit, so the length rises, falls, or stays as the two
counts happen to compare — an empty right-hand side is a deletion. An extended slice names
scattered positions with nothing between them to close up, so the counts must match exactly, which
chapter 2 section 4 established. The right-hand side only has to be iterable, which is why a string
splices in as single characters. **The contiguous form is the one that can resize, and resizing is
exactly what a length-preserving rewrite must not do.** (Sections 1 and 3; chapter 1 section 5;
chapter 2 section 4.)

**6.** `[1, 3, 6, 10]` / `[1, 3, 5, 7]` / `[3, 5, 7]`. Only the second block does what the
description says. Walking left to right, position `i - 1` has already been overwritten by the time
`i` reads it, so each element picks up a sum of everything before it instead of one neighbour, and
`[1, 3, 6, 10]` is a running total. Reversing the walk repairs it here, and the reason is a property
of this rewrite rather than a general law: every position reads only its left neighbour, so a walk
that runs right to left keeps all of its writes behind it and every slot it reads is still original
input. Section 3 repaired the same rewrite by carrying the displaced value in a variable instead;
both are correct, and the choice between them is yours. The comprehension gets the values right by
not writing into what it is reading, and gives back three elements rather than four. **When a
rewrite reads its neighbours, the direction of the walk is part of the algorithm, and choosing it
wrongly produces a plausible wrong answer rather than an error.** (Section 3.)

**7.** `4 [4, 1, 7, 3] 4` / `3 [1, 7, 3, 3]` / `0 []` / `0 [9, 9, 9]`. With nothing to remove the
write cursor never falls behind the read cursor, so every assignment is `nums[r] = nums[r]`, the
list is unchanged, and the cursor finishes at `len(nums)` — the highest it can reach, and the
signal that everything survived. That is the invariant made visible, and it is arguable from the
loop rather than observed: both cursors start at 0, `r` advances exactly once per iteration and `w`
advances at most once, so `w <= r` holds at every point. **The write cursor can never get ahead of
the read cursor, which is why writing into the list you are still reading is safe here.** The empty
list runs zero iterations and returns 0; a list where nothing survives returns 0 with every slot
untouched, because no write ever fired. In none of the four cases did `len(nums)` change.
(Sections 4 and 5.)

**8.** `3 [21, 24, 22, 3, 22]` / `[21, 24, 22] [3, 22]` / `5 True` / `[21, 24, 22] 3`. Three
readings survived and the answer is `readings[:3]`. The list is still five long, and the two
positions past the cursor hold neither the rejected values in order nor blanks. Neither slot was
written at all: `3` is a rejected reading the loop simply walked past, and `22` is the last
survivor's own source slot, still holding the value because copying it forward to position 2 never
erased where it came from. What the tail holds is a fact about this input, not a promise the
technique makes. That is chapter 3 section 6's debris, produced by a rewrite rather than by a
count. **The pair `(readings, w)` is the answer and `readings` alone is not**, which is why a
caller that only inspects the list will read two elements that mean nothing. Slice-deleting the
tail turns the pair back into a single self-describing list, at the cost of the length change the
technique existed to avoid. (Sections 4 and 5; chapter 3 section 6.)

**9.** `None` / `[1, 2, 3]` / `None` / `[1, 2, 3] [3, 1, 2]` / `None [3, 1, 2, 4]` /
`AttributeError 'NoneType' object has no attribute 'reverse'`. `sort()` sorted the list and
returned `None`; `nums = nums.sort()` therefore sorts and then throws the sorted list away by
rebinding the only name to `None`. The convention runs across the mutators — `append` returns
`None` too — and it is deliberate: a method that changes the list and returns nothing is the
language refusing to let a mutation be mistaken for an expression that produces a value. The one
exception chapter 1 section 9 names is `pop`, which hands back the element it removed, never the
list. `sorted()` is the other half of the pair, giving a new list and leaving the input alone.
Chaining exposes the convention loudly, since `None` has no list methods. **A missing return value
is the signal that the work was done to the object you already have.** (Sections 3 and 7; chapter 1
sections 8 and 9.)

**10.** `[[9, 0], [0, 0]]` / `[[9, 0], [9, 0]]` / `[[9, 0], [0, 0]]` / `[99, 2, 3] [1, 2, 3]` /
`True False`. `row` is a name for the inner list itself, not a copy of it, so writing through it is
writing into `grid`. Repetition copies references, so `[[0, 0]] * 2` produces two names for one
inner list and a single write appears in both rows; the comprehension evaluates its expression once
per iteration and builds two distinct lists. The last block is the same fact stated plainly: `snap`
is another name and sees the write, `copy` is a separate list and does not. **Every in-place
technique in this chapter is this property being used on purpose, and every bug it causes is the
same property being forgotten.** (Chapter 1 sections 3 and 9 are the source for all four blocks;
section 7 is where this chapter shows what forgetting it costs.)

### The readiness checklist

Chapter 1's scoring rule still holds: explanation rather than recognition, out loud, in under a
minute. Each statement names the section that carries it and the drill that tests it.

You should be able to explain, without looking it up, why:

1. `nums = [...]` and `nums[:] = [...]` differ in what every other holder of that list sees, and
   which of the two the word "in place" requires. (Sections 1 and 3; drills 1 and 10.)
2. `sort()` returns `None` while a hand-written in-place helper may return the list, and why the
   second one gives you a second name rather than a before-and-after. (Sections 1 and 7;
   drills 2 and 9.)
3. `a[i], a[j] = a[j], a[i]` needs no temporary while the same two writes on separate lines lose a
   value, and what the evaluation order of both sides has to do with it. (Section 3; drill 3.)
4. `nums.reverse()` and `nums = nums[::-1]` leave a second name bound to that list in opposite
   states, and which one allocates. (Sections 1, 3 and 6; drill 4.)
5. a contiguous slice assignment can change a list's length and an extended one cannot, and why
   that matters when the caller is holding the object. (Sections 1 and 3; drill 5.)
6. a rewrite that reads a neighbour gives a different answer depending on the direction of the
   walk, which property of the dependency decides that a safe direction exists at all, and when a
   carried variable is the repair instead. (Section 3; drill 6.)
7. the write cursor can never overtake the read cursor — as an invariant you can argue from the
   loop, not as something you observed on one input — and why that is precisely what makes writing
   into a list you are still reading safe. (Section 5; drills 7 and 8.)
8. the count a compaction returns is the answer and `len(nums)` is not, and what the positions
   past that count are actually holding. (Sections 4 and 5; drills 7 and 8.)
