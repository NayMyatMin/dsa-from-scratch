# Chapter 4 — Searching a List

Chapter 1 built the container: one contiguous block of pointers, an index that names a place rather
than a value, and a cost model that follows from those two facts. Chapter 2 took the operations that
put values in, chapter 3 the ones that take them out, and found the second was the first run
backwards over the same slots. This chapter takes the third of the three operations chapter 2
section 1 named, and completes the set: insert, delete, search. It is the one that is nobody's
mirror image. The two edits are told where to act and are billed for the tail they move; **search
moves nothing at all, and its whole job is to produce the position the other two were handed.**

That difference decides the shape of everything here. A search is asked far more often than the
edits it serves, so the question stops being what one call costs and becomes what a structure costs
across a day of questions — which makes this the chapter where the answer is sometimes to stop using
a list at all. It is also the first chapter where every tool has two answers rather than one, a hit
and a miss, and the misses disagree with each other about how to report themselves, so choosing a
spelling is choosing how absence will reach your code. And it is the chapter where a precondition
can be false with nothing raising: sortedness buys twenty comparisons in place of a million, and
nothing whatsoever checks that the input is sorted.

It leans on the first three chapters rather than repeating them. The operation cost table and the
measured case for membership testing are chapter 1 section 8; the other containers, `set` and `dict`
among them, are section 10; the iterator protocol is section 6; and the timing method every
measurement below uses is section 11. Chapter 2 section 6 introduced `bisect` for insertion, and
section 5 here extends it rather than restating it — the same halving probe, asked a different
question, and needing a guard that insertion never needed. Chapter 3 section 4 priced the search
hidden inside `remove`, and more than one section here starts from that figure.

## How to read this

**Run the code.** Every block is executable exactly as written — there are 85 of them, carrying 244
`# -> value` comments — and every one of those comments is a real observed result rather than an
illustration. Open a session next to this document and paste as you go:

```bash
uv run python
```

Some blocks continue the one before them within a section, reusing a variable set up earlier. Some
deliberately end in an exception and say so on the offending line; those are demonstrations, and the
exception is the point.

**Predict before you run.** Section 8 is ten drills and an answer key, and it is the honest test of
whether the rest of the chapter landed. The three subjects it goes after hardest — what each search
returns when it succeeds, what it does when it fails, and which of those failures can be mistaken
for a result — are the three that decide correctness rather than style.

**Measurements come from this machine.** Every number was measured on CPython 3.14.4, the
interpreter in this repository's virtual environment, on a 64-bit build. Deterministic values —
object sizes, probe counts, printed output — will reproduce exactly for you. Timings will not; they
depend on your hardware and on what else is running. What reproduces is the shape: the ratios, the
orderings, and the way a figure moves when the input doubles. Where a number is a timing, the
surrounding prose says what about it is meant to hold.

**It is about the length of chapter 2.** Around 20,000 words, roughly two and a half hours at the
pace of prose you stop and run rather than skim, against chapter 1's six and a quarter. One long
sitting or two; the natural break is the end of section 3, which closes the account of the scan
before the two ways out of it.

## The sections

| | Section | What it settles | Size |
|---|---|---|---:|
| 1 | [The two questions a search answers](#1-the-two-questions-a-search-answers) | Presence against position, and the three strategies with their preconditions | 1,900 w · 14 min |
| 2 | [Linear search, and the tools Python gives you](#2-linear-search-and-the-tools-python-gives-you) | `in`, `index`, `count`, the loop you write yourself, and the early exit | 2,600 w · 20 min |
| 3 | [What linear search costs](#3-what-linear-search-costs) | Why one O(n) row is a range, and the scans that do not look like loops | 2,600 w · 20 min |
| 4 | [Searching by hashing](#4-searching-by-hashing) | `set` and `dict` as lookup structures, and what the second copy costs | 2,800 w · 21 min |
| 5 | [Searching a sorted sequence](#5-searching-a-sorted-sequence) | `bisect` as a search, and the precondition nothing enforces | 2,700 w · 21 min |
| 6 | [Searching by predicate](#6-searching-by-predicate) | `next`, `any`, `all`, `min`, `max`, and targets you cannot name | 2,500 w · 19 min |
| 7 | [When the answer is "not there"](#7-when-the-answer-is-not-there) | Sentinel, exception or `None`, and the miss that reads as a hit | 2,400 w · 18 min |
| 8 | [Drills](#8-drills) | Ten predictions, an answer key, and a readiness check | 2,500 w · 20 min |

Sections 1 through 3 are the spine and are best read in order: what a search is asked to return,
every spelling of the scan, and what the scan actually costs. Sections 4 and 5 are the only two ways
out of that cost, and each is a bargain rather than an upgrade — read them as a pair, because
choosing between them is the interesting part. Section 6 is the case where the target has no name to
look up. Section 7 is the one to read before writing any search whose failure matters, which is all
of them. Nothing in sections 1 to 7 is optional here. Section 8 is the exit exam.

When you finish, the two problems in `arrays101/ch04/` are waiting. Sections 3 and 7 are the two
nearest to them, and neither is a hint: section 3 is what a scan costs and how much of that depends
on where the answer sits, and section 7 is what each of these tools does when there is no answer at
all — something both problems make you decide before they will accept anything.

---

## 1. The two questions a search answers

Chapter 2 section 1 named the three operations a data structure exists to answer — insert, delete,
search — and made the point that the differences between structures are differences in what those
three cost. Chapter 2 took the first. Chapter 3 took the second, and found it was the first run
backwards over the same slots. This chapter takes the third, and it is not anybody's mirror image.
Insertion and deletion are both edits: you are told where, and the bill is the tail you have to
shift. Search is the operation that has to work out the where, and nothing it does moves an element
at all.

It is also the one that most often decides a design. A job is submitted once and cancelled at most
once, but the status page behind it is refreshed by every engineer waiting on a build. Chapter 2
flagged that asymmetry in passing while introducing the queue; it is the whole reason this chapter
matters. **You pay for insertion once per element and for search once per question, and the
questions outnumber the elements** — which is why a structure that makes lookups instant is worth
a great deal of up-front cost, and why the rest of this chapter is largely about what that cost is
and when to accept it.

### The status page, refreshed all day

Keep the render farm from chapters 2 and 3. A worker takes jobs off the front of a queue, and every
engineer who submitted one has a page open that refreshes every few seconds. That page shows two
things, and they are not the same thing.

There is a badge at the top: *still queued*, or *no longer queued*. It is a yes-or-no, it is the
only part that a job which has already started rendering can still answer sensibly, and it is what
the "cancel" button greys itself out on.

Underneath it is a line that says *3 jobs ahead of you*. That is a position, and it only exists if
the answer to the first question was yes.

```python
queue = ["hotfix-9002", "render-4471", "index-rebuild", "thumbs-2210", "backup-nightly"]
mine = "index-rebuild"

print(mine in queue)                       # the badge: still waiting?
# -> True
print(queue.index(mine))                   # the position: how many are ahead?
# -> 2
print(len(queue) - queue.index(mine) - 1)  # and how many behind
# -> 2

finished = "render-0001"
print(finished in queue)
# -> False
try:
    queue.index(finished)
except ValueError as e:
    print(e)
# -> list.index(x): x not in list
```

**"Is it there" and "where is it" are different questions, and Python gives them different
operators, different return types, and different behaviour when the answer is nothing.** `in` hands
back a `bool` in both cases and never raises. `index` hands back an `int` in one case and raises
`ValueError` in the other, because there is no integer that means "nowhere" — every integer,
including `-1`, is a position some list could really have. `index` also answers a narrower question
than it looks like it does: it reports the *first* match and stops there, so a value sitting in
three places has three positions and one `index`. First, last, and all of them are three different
searches, and section 2 writes each one.

```python
queue = ["hotfix-9002", "render-4471", "index-rebuild", "thumbs-2210", "backup-nightly"]

present = "index-rebuild" in queue
where = queue.index("index-rebuild")
print(type(present).__name__, type(where).__name__)
# -> bool int
print(queue.count("index-rebuild"), queue.count("render-0001"))
# -> 1 0

queued = set(queue)
print("index-rebuild" in queued)
# -> True
try:
    queued.index("index-rebuild")
except AttributeError as e:
    print(e)
# -> 'set' object has no attribute 'index'
```

`count` is a third shape of answer: an `int` that is allowed to be zero, so it reports absence with
a value rather than an exception, and it reports multiplicity, which neither of the others can. The
last three lines are the point that the two questions really are separable. A `set` answers the
first question and cannot answer the second at all — it has no positions to report. That is not a
missing feature; it is the trade section 4 is built on.

The consequence for your code is that the failure mode is chosen when you choose the spelling. `in`
inside an `if` is total: it has an answer for every input and you handle both branches in the
obvious place. `index` is partial, so either you know the value is present or you write the `try`.
Section 7 is entirely about that choice — every form of search in this chapter reports "not there"
differently, and picking a form is picking how the absent case will reach you.

### If you already know the index, there is nothing to search

Search only exists because you do not have the position. When you do have it, the operation is a
read, and chapter 1 section 8 prices that read at O(1): one bounds check and one pointer offset,
the same cost on a list of five elements and a list of five million. There is no algorithm to
choose and no chapter to write.

```python
import timeit

setup = "queue = [f'job-{i}' for i in range(200_000)]"
known = min(timeit.repeat("queue[150_000]",
                          setup=setup, number=1_000_000, repeat=7))
found = min(timeit.repeat("queue.index('job-150000')",
                          setup=setup, number=200, repeat=7))
print(round(known / 1_000_000 * 1e9, 1), "ns to read the index you were given")
# -> 5.1 ns to read the index you were given
print(round(found / 200 * 1e6, 1), "us to work out what that index is")
# -> 848.9 us to work out what that index is
print(round(found / 200 / (known / 1_000_000)), "x")
# -> 167248 x
```

Both lines end up holding the same element. One of them was told where it was. Repeated runs on
this machine hold the read at five-odd nanoseconds and the search just short of a millisecond,
putting the multiplier between about 155,000x and 170,000x; your own figures will differ, and the
ordering will not. Note also what the second measurement depends on that the first does not — the
target sits three quarters of the way along, and moving it moves the number. Searching for
`job-10000` instead, a twentieth of the way in, measured 63.6 us against 975.2 us for the target
three quarters along, on the same list in the same run. Section 3 is where that dependence gets
taken apart.

So the useful reading of "if you know the index, it is free" is the contrapositive: **the reason
search is a subject at all is that a position is the one thing a list will not hand you, and the
one thing it stops being true about the moment the list is edited.** Chapter 3 section 1 made that
concrete — an index is a position, not a handle, so a position you recorded before a removal names
a different element afterwards, and says nothing about it. A stored index is only as good as the
promise that nothing has shifted underneath it. On a queue that is being drained all day, that
promise is worth very little, and re-deriving the position is a search.

### Three strategies, and what each one demands first

Everything in this chapter is one of three answers to "where is it", and they differ less in how
they work than in what they require to be true before they are allowed to run.

| Strategy | The spellings | What must already be true | Per search | Section |
|---|---|---|---|---|
| Scan every element | `x in nums`, `nums.index(x)`, `nums.count(x)`, a hand-written loop with an early exit, `next(...)`, `any` / `all` | nothing at all | O(n) | 2, 3, 6 |
| Hash the values | `x in lookup` on a `set`; `k in d` and `d[k]` on a `dict` | every value hashable, and a second structure built beforehand at O(n) and kept in step | O(1) average | 4 |
| Exploit an existing order | `bisect_left`, `bisect_right`, plus a guard you write | the sequence sorted already — and nothing checks | O(log n) | 5 |

The third column is the decision, and the fourth is mostly a distraction until the third is
satisfied. The scan is the only row that asks for nothing, which is why it is the default and why
it is never wrong. The other two are faster per question and charge an entry fee: a set costs a
linear pass and a second copy of the data before its first lookup, and sorting costs O(n log n)
before its first probe. **One search on data you know nothing about is a scan, every time — you
cannot amortise a preparation you only benefit from once.** The moment the same collection is
questioned repeatedly, the arithmetic inverts and the entry fee is the cheapest thing you will pay
all day.

All three answer the same question, and it is worth seeing them agree before seeing them argue:

```python
from bisect import bisect_left

sensors = [11, 14, 19, 23, 31]      # sorted, and known to be sorted
by_hash = set(sensors)

print(19 in sensors)                            # scan
# -> True
print(19 in by_hash)                            # hash
# -> True
i = bisect_left(sensors, 19)
print(i < len(sensors) and sensors[i] == 19)    # order
# -> True

print(20 in sensors, 20 in by_hash)
# -> False False
j = bisect_left(sensors, 20)
print(j, j < len(sensors) and sensors[j] == 20)
# -> 3 False
```

The third form needs two lines where the others need one, and the second of those lines is not
optional. `bisect_left` returns an insertion point whether or not the value is present, so 20 comes
back as 3 — a perfectly valid index into a list that does not contain 20. Chapter 2 section 6
established that for insertion, where the index was the answer you wanted; here it is the trap,
because the number looks exactly like a search result. Section 5 is where the guard gets written
properly.

Chapter 1 has the background all three lean on and this chapter does not re-derive: section 8 for
the cost table and the measured case for membership testing, section 10 for what `set` and `dict`
are and what they will not accept, and section 11 for how the timings here were taken.

### What this chapter settles

Section 2 is the scan in every spelling Python offers, including the loop you write by hand and
what it buys over the built-ins. Section 3 prices it, including the part the O(n) row hides —
where in the list the answer sits, and what happens when the scan sits inside a loop of its own.
Section 4 is hashing: `set` and `dict` as lookup structures, what building one costs, and when the
second copy of your data pays for itself. Section 5 is `bisect` used for searching rather than
inserting, and the precondition that nothing enforces. Section 6 is searching by a predicate
rather than a value — `next`, `any`, `all`, and generator expressions — the case where "equal to
x" is not the question. Section 7 collects every way this chapter's tools say "not there", because
they disagree, and the disagreement is where the bugs are. Section 8 is drills.

---

## 2. Linear search, and the tools Python gives you

The simplest search is the one you would invent unprompted: start at index 0, compare, stop when you
find the element or run out of list. Python ships three spellings of that scan as built-ins, each
stopping at a different point, and leaves you the raw loop for everything they do not cover — all
of them below, along with the one line that separates a search from a survey.

### `in` answers presence, and nothing else

```python
temps = [18, 21, 19, 23, 21, 20]
print(21 in temps)        # -> True
print(25 in temps)        # -> False
print(25 not in temps)    # -> True
print(21 in [])           # -> False
```

`in` walks from index 0 and stops the moment an element matches, so its cost is set by how far in
the first match sits — chapter 1, section 8 has the row, section 3 below takes it apart. What it
will never tell you is *where*. If the next thing you write after `if v in nums` is `nums.index(v)`,
you have scanned the same prefix twice; chapter 3, section 4 priced that mistake in its `remove`
form. The empty list needs no guard: every value is absent from it, and `in` says so without a
special case. Matching is identity first and equality second — chapter 1, section 8's rule for
every scanning operation, and why an element finds itself even when its `__eq__` would refuse.

### `index` answers where, and takes a window

```python
temps = [18, 21, 19, 23, 21, 20]
print(temps.index(21))         # -> 1
print(temps.index(21, 2))      # -> 4
print(temps.index(21, 2, 6))   # -> 4
print(temps.index(21, -3))     # -> 4    a negative bound counts back from the end
print(temps.index(21, 0, 99))  # -> 1    an out-of-range bound is clamped, not an error
```

The optional second and third arguments are a start and a stop: the same half-open interval as a
slice from chapter 1, section 5, resolved the same way, except that no copy is made and the number
handed back is an index into the *original* list.

```python
temps = [18, 21, 19, 23, 21, 20]
print(temps[2:].index(21))     # -> 2
print(temps.index(21, 2))      # -> 4
```

Both found the same element. The slice built a four-element copy and reported a position inside it,
which you would then have to add 2 to; `index` with a start reported the answer you wanted and
allocated nothing. Absence is an exception, not a value, and the message is fixed text:

```python
temps = [18, 21, 19, 23, 21, 20]
try:
    temps.index(25)            # not in the list at all
except ValueError as e:
    print(type(e).__name__, "|", str(e))
    # -> ValueError | list.index(x): x not in list
try:
    temps.index(21, 2, 4)      # 21 sits at 1 and at 4; the window is [2, 4)
except ValueError as e:
    print(str(e))              # -> list.index(x): x not in list
```

It never names the value you looked for, and when the search failed only because your window
excluded the match, it does not mention the window either. Nor is there a sentinel-returning
sibling: a `str` has both `index` and `find`, and `find` answers `-1` rather than raising, but
`hasattr(list, "find")` is `False`. Raising is the only behaviour a list offers, and section 7 is
about what to do with that.

### `count` answers how many, and cannot stop early

```python
temps = [18, 21, 19, 23, 21, 20]
print(temps.count(21))    # -> 2
print(temps.count(25))    # -> 0
print([].count(21))       # -> 0
```

`count` never raises: zero occurrences is a number, and an empty list is the case where every count
is zero. It takes no start and stop — the window arguments belong to `index` alone. The price of a
total is that there is nothing to stop for. Chapter 3, section 4 measured `count` flat at 110
microseconds on a 20,000-element list whether the value sat at index 0 or index 19,999, against 6.3
nanoseconds for an `in` answered at the front. **Use `count` when the number is the answer; never
write `count(v) > 0` to ask whether something is there.**

### Writing the scan yourself

The three built-ins ask one fixed question: does this element match that value. The moment your
test is anything else — the first reading above a threshold, the position *and* the value
together — you write the scan yourself, and `enumerate` from chapter 1, section 6 keeps the index
for you. Python has an expression form for both of those examples, which section 6 takes up; the
loop below is the mechanism underneath it rather than the spelling to reach for.

```python
def first_above(readings, limit):
    for i, r in enumerate(readings):
        if r > limit:
            return i
    return -1

def no_fallthrough(readings, limit):    # the same loop, minus the last line
    for i, r in enumerate(readings):
        if r > limit:
            return i

print(first_above([18.2, 19.6, 21.4, 23.9], 21.0))   # -> 2
print(first_above([], 30.0))                         # -> -1
print(no_fallthrough([18.2, 19.6], 30.0))            # -> None
```

No length check appears anywhere and none is needed: an empty list runs the body zero times and
falls through to the same last line a non-empty list with no match reaches. The guard you *do*
need is that fall-through. Drop it and the function still runs, still passes every test where the
value is present, and answers by default rather than by decision when it is not — the `None` in
that third `print` was never chosen by anyone. It is supplied by the compiler, which ends every
function that runs off its own end the same way:

```python
import dis

def no_fallthrough(readings, limit):
    for i, r in enumerate(readings):
        if r > limit:
            return i

print([i.opname for i in dis.get_instructions(no_fallthrough)][-2:])
# -> ['LOAD_CONST', 'RETURN_VALUE']      the constant loaded is None
```

**A search has to answer on no match, and the answer has to be picked deliberately rather than
left to the end of the function.** Which value to pick is a good deal less obvious than it looks,
and it is section 7's subject; `-1` stands here only to make the fall-through visible, not because
it is the right choice.

Writing the loop is not free. On a 100,000-element list with the target at the very end, so that
both spellings examine every element:

```python
import timeit

def per_call(fn, repeat=25):
    t = timeit.Timer(fn)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

nums = list(range(100_000))
target = 99_999

def builtin_in():
    return target in nums

def loop_in():
    for x in nums:
        if x == target:
            return True
    return False

def builtin_index():
    return nums.index(target)

def loop_index():
    for i, x in enumerate(nums):
        if x == target:
            return i
    return -1

a, b = per_call(builtin_in), per_call(loop_in)
c, d = per_call(builtin_index), per_call(loop_index)
print(f"in    {a:10.1f} ns   loop {b:10.1f} ns   {b / a:5.2f}x")
print(f"index {c:10.1f} ns   loop {d:10.1f} ns   {d / c:5.2f}x")
# -> in     550108.3 ns   loop  524900.0 ns    0.95x
# -> index  560829.2 ns   loop 1355552.2 ns    2.42x
```

The two presence tests swap order from one run to the next — five sittings here put that first
ratio anywhere from 0.91x to 1.55x — so it is noise, and `in` earns its place on clarity rather
than on speed. The position search is a different story. `index` came in between two and three
times quicker than the `enumerate` loop
doing identical work, in every run, because its scan stays inside CPython's C implementation while
the loop pays the interpreter per element: a call into the iterator, an unpack in the loop header,
and a fresh integer for the index once the counter climbs past the small ints CPython keeps cached
— chapter 1, section 6 measured that bill and established that a fresh *tuple* is not part of it.
That factor is what it costs to ask a question `index` cannot ask — worth paying, but not when
`index` already answers you.

### The early exit is what makes it a search

Two functions differing by one keyword. One returns at the first match; the other walks to the end
remembering the last thing it saw. Same list, same target, three positions.

```python
import timeit

def per_call(fn, repeat=25):
    t = timeit.Timer(fn)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

def search(readings, target):
    for i, r in enumerate(readings):
        if r == target:
            return i
    return -1

def survey(readings, target):
    found = -1
    for i, r in enumerate(readings):
        if r == target:
            found = i
    return found

readings = list(range(100_000))
for target in (50, 25_000, 99_999):
    a = per_call(lambda t=target: search(readings, t))
    b = per_call(lambda t=target: survey(readings, t))
    print(f"target at {target:>6}   search {a:11.1f} ns   survey {b:11.1f} ns   {b / a:9.1f}x")
# -> target at     50   search       603.5 ns   survey   1431812.5 ns      2372.5x
# -> target at  25000   search    361079.1 ns   survey   1485750.0 ns         4.1x
# -> target at  99999   search   1437073.0 ns   survey   1504250.0 ns         1.0x
```

The survey column is flat: it always visits every element, so the input cannot change its work. The
search column tracks the position of the match, and with the target near the front it comes in
roughly two thousand times quicker on the same list. Both are O(n) — section 3 reconciles that
notation with this table. **A scan without a `return` inside the `if` is a survey of the whole list;
the `return` is the entire difference between the two columns.** `count` is a survey and is right
to be one; a membership test written as one is just a slow membership test.

### Absent, empty, and more than once

Three edge cases decide whether a search is correct, and none needs a length guard in Python.
Absence is `False` from `in`, `0` from `count`, a `ValueError` from `index`, and whatever your loop
falls through to; an empty list is the case where the value is absent and the body never runs. The
third changes the answer rather than the control flow: **`index` gives you the first match, and no
argument makes it give you the last.**

```python
temps = [18, 21, 19, 23, 21, 20, 21]
print(temps.index(21))                                # -> 1
print(len(temps) - 1 - temps[::-1].index(21))         # -> 6
print([i for i, t in enumerate(temps) if t == 21])    # -> [1, 4, 6]
print(temps.count(21))                                # -> 3
```

A list has no `rindex`, so the last position has to be built. The reversed-slice spelling reads
well and copies the entire list to do it; a backwards `range` scan copies nothing and keeps the
early exit, which matters exactly when the match is near the end. On `list(range(200_000))` asked
for 199,995, the same `per_call` harness gives 424,725 ns for the reversed copy against 126.4 ns
for `for i in range(len(nums) - 1, -1, -1)`, which settles it on its fifth comparison — three
thousand-fold, and timing the reversal on its own accounts for all but a few percent of that.

Every position is a survey by nature: the comprehension must finish to know it has them all, which
is why its length agrees with `count`. To take them one at a time instead, `index`'s start argument
is the mechanism — each call resumes one past the previous hit, and the `ValueError` is the stop
condition rather than an accident:

```python
temps = [18, 21, 19, 23, 21, 20, 21]
i, found = -1, []
while True:
    try:
        i = temps.index(21, i + 1)     # resume just past the previous hit
    except ValueError:                 # no further occurrence: the scan is done
        break
    found.append(i)
print(found)                           # -> [1, 4, 6]
```

That version can stop as soon as it has seen enough, which the comprehension cannot, and it never
re-examines an element the previous call already rejected. It costs one `try` to say so.

### A record instead of a value

`in`, `index` and `count` compare a whole element against a whole value. When the test looks at one
*field* of an element, none of them applies, and the idiom is `next()` over a generator expression:

```python
records = [{"sku": "sku-0", "stock": 3},
           {"sku": "sku-1", "stock": 0},
           {"sku": "sku-2", "stock": 7}]

print(next((r for r in records if r["sku"] == "sku-2"), None))
# -> {'sku': 'sku-2', 'stock': 7}
print(next((r for r in records if r["sku"] == "sku-9"), None))
# -> None
try:
    next(r for r in records if r["sku"] == "sku-9")     # no default
except StopIteration as e:
    print(type(e).__name__, "|", repr(str(e)))          # -> StopIteration | ''
```

The generator produces nothing until something asks. `next` asks exactly once, the scan advances
only far enough to satisfy that one request, and stops — the previous subsection's early exit,
without a loop to write. The second argument is the answer when the scan runs out, and without it
running out raises `StopIteration` carrying an empty message, a poor thing to let escape a function.

The alternative you will be tempted by is a comprehension that filters and then takes element zero.
It returns the same record and pays for the whole list to get it. Two hundred thousand records, the
one you want first in line:

```python
import sys, timeit, tracemalloc

def per_call(fn, repeat=25):
    t = timeit.Timer(fn)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

records = [{"sku": f"sku-{i}", "stock": i % 7} for i in range(200_000)]

def lazy():
    return next((r for r in records if r["stock"] == 0), None)

def eager():
    matches = [r for r in records if r["stock"] == 0]
    return matches[0] if matches else None

print(lazy() is eager())                       # -> True

tracemalloc.start()                            # what each holds once it has the answer
scan = (r for r in records if r["stock"] == 0)
held = next(scan, None)
lazy_bytes = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

tracemalloc.start()
matches = [r for r in records if r["stock"] == 0]
eager_bytes = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

print(lazy_bytes, eager_bytes, len(matches), sys.getsizeof(matches))
# -> 376 246544 28572 246488
print(f"lazy {per_call(lazy):11.1f} ns   eager {per_call(eager):11.1f} ns")
# -> lazy       114.6 ns   eager   3425834.0 ns
```

Literally the same record — `is`, not merely `==` — four orders of magnitude apart in time, and
655 times apart in what each one is still holding once it has that record. The eager version
scanned all 200,000 records and assembled a 28,572-element list of matches only to discard all but
the first. `sys.getsizeof` puts that list at 246,488 bytes, and that is the figure here fixed by
the language rather than by your session: `tracemalloc` is chapter 1, section 11's tool, and that
section's warning applies in full — it charges only what your session had not already allocated,
so its total lands within one object header of `getsizeof`, on either side. Read the factor, never
the last digits. Double the input and the generator's few hundred bytes stay a few hundred bytes
while the list of matches goes from 246,488 to 499,960: one of these costs is a constant and the
other is the size of your data. **`next()` over a generator is a linear search with the early exit
built in; a filtering comprehension is a survey that happens to keep what matched.**

One field of a record is still one element examined on its own, which is why this belongs here
rather than under a heading of its own; section 6 generalises it from a named field to any
predicate, and adds `any` and `all` for when the yes-or-no is all you wanted. Section 3 prices the
scan every spelling in this section shares.

---

## 3. What linear search costs

Every spelling in section 2 costs the same thing, because underneath they all do the same thing:
compare the target against elements, one after another, until something matches or the list runs
out. The price of a linear search is therefore not a single number. It is a number that depends on
where the answer is.

### Three cases, and only one of them is about the algorithm

Put 200,000 user ids in a list and ask for one at the front, one in the middle, one at the back,
and one that is not there at all.

```python
import timeit

def per_call(stmt, setup, repeat=25):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

n = 200_000
setup = f"ids = list(range(1000, 1000 + {n}))"
for label, target in (("first", 1000), ("middle", 1000 + n // 2),
                      ("last", 1000 + n - 1), ("absent", -1)):
    ns = per_call(f"{target} in ids", setup)
    print(f"{label:>7} {ns:12.1f} ns")
# ->   first         12.5 ns
# ->  middle     492870.8 ns
# ->    last     982771.0 ns
# ->  absent     986073.0 ns
```

Almost five orders of magnitude between the first row and the last, on one list, from one
operation. The best case is O(1): the target sat at index 0, one comparison settled it, and 12.5 ns
is essentially the cost of the call itself. That row does not move when the list grows — the same
harness on lists of 1,000, 100,000 and 10,000,000 elements gave 8.6, 8.5 and 8.9 ns, flat across
four orders of magnitude of `n`.

The middle row is almost exactly half the last row, because it examines half as many elements, and
dividing either by the number of elements it walked gives the same figure: 492,870.8 ns over 100,000
elements is 4.93 ns apiece, and 982,771.0 ns over 200,000 is 4.91. That constant is the whole cost
model. A linear search is a per-element price times the number of elements you reach, and it is in
the same neighbourhood as the 5.53 ns per element chapter 3, section 4 measured for `index` on a
different list — because it is the same work.

The last two rows are the worst case, O(n), and they are worth looking at together. Finding the
final element and finding nothing at all cost the same, because both examine every element. **A
scan that fails has paid the full price of a scan that succeeds; absence is never cheap.** Section
7 takes up what to do with that answer once you have it.

Sortedness does not rescue the failing case either, and `ids` happens to be sorted. The absent
target `-1` is smaller than every element in it, so the first comparison could in principle settle
the question — and it does not: `-1 in ids` measured 984.1 µs against 983.9 µs for `999_999 in
ids`, which is larger than every element. Both walk the entire list. **The scan has no idea the
elements are ordered**, so it cannot stop early. That order is information nobody is spending, and
section 5 spends it.

Between the extremes sits the case usually labelled "average", and the label is misleading. There
is no average built into the algorithm. There is only the distribution of the targets you actually
ask about.

```python
import random, timeit

n = 200_000
ids = list(range(1000, 1000 + n))
rng = random.Random(7)
workloads = {
    "uniform over the list": [rng.choice(ids) for _ in range(500)],
    "the first 1% only":     [rng.choice(ids[:n // 100]) for _ in range(500)],
    "always the last id":    [ids[-1]] * 500,
    "always absent":         [-1] * 500,
}
for label, targets in workloads.items():
    t = timeit.Timer(lambda: [x in ids for x in targets])
    per = min(t.repeat(number=1, repeat=9)) / len(targets) * 1e6
    print(f"{label:<22} {per:9.2f} us per lookup")
# -> uniform over the list     666.50 us per lookup
# -> the first 1% only           5.68 us per lookup
# -> always the last id       1228.57 us per lookup
# -> always absent            1239.33 us per lookup
```

Same list, same operation, same 500 lookups each time. Only the *choice of targets* changed, and
the per-lookup cost moved by more than a factor of 200. Targets drawn uniformly cost about half the
worst case, which is the textbook n/2 comparisons. Targets concentrated in the first 1% cost about
a two-hundredth of it, because their mean depth is half of one percent of the list. When someone
says linear search is O(n) on average, they mean: assuming every position is equally likely. If
your lookups are mostly hits near the front, your average is far better than that; if your lookups
are mostly misses, your average *is* the worst case. All three cases are still O(n) as a class —
the distribution moves the constant, not the exponent.

### One search is cheap; n of them are not

A single millisecond scan over 200,000 elements is invisible. Nobody profiles it, nobody notices
it, and there is nothing wrong with it. The problem starts when that scan sits inside a loop over
the same collection, because then you are paying it once per element.

```python
import timeit

def ms(fn, number=1, repeat=9):
    return min(timeit.repeat(fn, number=number, repeat=repeat)) / number * 1000

prev_scan = prev_hash = None
for n in (4_000, 8_000, 16_000, 32_000):
    ids = list(range(n))
    flagged = list(range(0, n, 2))

    def by_scan():
        return sum(1 for x in ids if x in flagged)

    def by_hash():
        blocked = set(flagged)
        return sum(1 for x in ids if x in blocked)

    assert by_scan() == by_hash()
    a, b = ms(by_scan), ms(by_hash, number=20)
    ga = f"x{a / prev_scan:.1f}" if prev_scan else "-"
    gb = f"x{b / prev_hash:.1f}" if prev_hash else "-"
    print(f"{n:>6}  scan {a:9.2f} ms {ga:>5}   set {b:7.3f} ms {gb:>5}")
    prev_scan, prev_hash = a, b
# ->   4000  scan     29.37 ms     -   set   0.085 ms     -
# ->   8000  scan    119.49 ms  x4.1   set   0.177 ms  x2.1
# ->  16000  scan    480.71 ms  x4.0   set   0.345 ms  x1.9
# ->  32000  scan   1939.00 ms  x4.0   set   0.686 ms  x2.0
```

The growth columns are the whole point. Double the input and the scanning version quadruples, which
is the signature of O(n²); the set version doubles, which is O(n). Every individual `in` in the
left column is one of the cheap operations from the first table — the bottom row divided by its
32,000 lookups is 60.6 microseconds each, far too small to feel on its own — and there are `n` of
them, so the cost of the whole is `n` times a cost that itself grows with `n`. By 32,000 elements,
which is a small list, the two columns are more than two thousand times apart, and every doubling
from here widens that by another factor of two. Chapter 1, section 8 showed the same shape from the
container's side; the reading to carry away here is about your own code. **The `in` is not the bug.
The `in` inside a loop over the collection it searches is the bug.**

That is the shape to learn to recognise in source rather than in a profile, because at the sizes
you test with it does not hurt. At 4,000 elements the scanning version takes 29 ms and looks
perfectly healthy.

### Where a set starts paying for itself

Chapter 1, section 8's membership row already gives the fix: hoist the collection into a `set`
before the loop, and each test becomes an O(1) hash-and-probe instead of an O(n) walk. Section 4
takes that apart properly. The question that row does not answer is when it is worth doing at all —
building the set is itself a full linear pass, so for a small number of lookups you are better off
just scanning.

Measure the break-even directly. For each `k`, the targets are spread so their mean depth is n/2
whatever `k` is, which keeps the scan column honest.

```python
import timeit

def us(fn, number, repeat=11):
    return min(timeit.repeat(fn, number=number, repeat=repeat)) / number * 1e6

for n, number in ((10_000, 500), (100_000, 100), (1_000_000, 10)):
    ids = list(range(n))
    print(f"n = {n:,}")
    for k in (1, 2, 3, 4):
        targets = [(2 * j + 1) * n // (2 * k) for j in range(k)]   # mean depth n/2 for every k

        def by_scan():
            return sum(t in ids for t in targets)

        def by_hash():
            known = set(ids)
            return sum(t in known for t in targets)

        a, b = us(by_scan, number), us(by_hash, number)
        print(f"   {k} lookup(s)  scan {a:9.1f} us   build+probe {b:9.1f} us"
              f"   {'set' if b < a else 'scan':>4} wins")
# -> n = 10,000
# ->    1 lookup(s)  scan      24.4 us   build+probe      50.6 us   scan wins
# ->    2 lookup(s)  scan      48.9 us   build+probe      50.7 us   scan wins
# ->    3 lookup(s)  scan      73.0 us   build+probe      50.8 us    set wins
# ->    4 lookup(s)  scan      97.4 us   build+probe      50.8 us    set wins
# -> n = 100,000
# ->    1 lookup(s)  scan     244.1 us   build+probe     588.6 us   scan wins
# ->    2 lookup(s)  scan     489.6 us   build+probe     596.4 us   scan wins
# ->    3 lookup(s)  scan     735.8 us   build+probe     582.8 us    set wins
# ->    4 lookup(s)  scan     978.2 us   build+probe     592.4 us    set wins
# -> n = 1,000,000
# ->    1 lookup(s)  scan    2482.4 us   build+probe    7332.2 us   scan wins
# ->    2 lookup(s)  scan    4976.2 us   build+probe    7508.7 us   scan wins
# ->    3 lookup(s)  scan    7473.4 us   build+probe    7862.5 us   scan wins
# ->    4 lookup(s)  scan   10041.8 us   build+probe    7650.6 us    set wins
```

**Three lookups.** The set overtakes the scan at the third one, and it does so at all three sizes —
at a million the two columns land close enough together at `k = 3` that repeated runs put the
crossing at three or four, but never higher. The break-even does not climb with `n` across a
hundredfold range of it, and that is not luck: building the set and scanning the list are both one
pass over `n` elements, so their ratio is a constant and the break-even is that constant. On this
machine one build costs between two and three scans.

The two columns read differently down each block. Build+probe is flat, because the probes cost
nothing next to the build — the same reason chapter 1, section 8 could report one build costing
about what a hundred thousand queries cost. Scan is a straight multiple of `k`, because nothing is
being reused between lookups; the fourth search redoes every comparison the first one already did.

Three is a small enough number to turn into a habit. Ask more than a couple of membership questions
about the same collection and building the lookup structure first is already the cheaper program.
Ask exactly one and it is not worth the allocation.

### The searches you did not write down

The `in` above is visible. Several other operations run the same scan without the word appearing.

```python
import timeit

def ms(fn, number=1, repeat=7):
    return min(timeit.repeat(fn, number=number, repeat=repeat)) / number * 1000

for n in (2_000, 4_000, 8_000):
    users = [f"user-{i}" for i in range(n)]
    leaving = users[::2]
    gone = set(leaving)

    def by_remove():
        keep = users.copy()
        for name in leaving:
            keep.remove(name)
        return keep

    def by_filter():
        return [name for name in users if name not in gone]

    def by_index():
        return {name: users.index(name) for name in users}

    def by_enumerate():
        return {name: i for i, name in enumerate(users)}

    assert by_remove() == by_filter() and by_index() == by_enumerate()
    print(f"{n:>6}  remove-loop {ms(by_remove):7.2f} ms   filter {ms(by_filter, number=100):6.3f} ms"
          f"   |   index {ms(by_index):8.2f} ms   enumerate {ms(by_enumerate, number=100):6.3f} ms")
# ->   2000  remove-loop    3.38 ms   filter  0.037 ms   |   index    13.47 ms   enumerate  0.063 ms
# ->   4000  remove-loop   14.39 ms   filter  0.070 ms   |   index    56.65 ms   enumerate  0.131 ms
# ->   8000  remove-loop   61.44 ms   filter  0.173 ms   |   index   239.40 ms   enumerate  0.272 ms
```

Both left-hand columns quadruple per doubling; both right-hand columns double. `remove` is a search
followed by a shift, and chapter 3, section 4 priced its two halves twenty-fold apart, with the
search the expensive one — so a loop of `remove` calls is a loop of scans, and it is quadratic even
though no comparison appears in the source. `index` inside a comprehension over the same list is
the same trap with the deletion taken away: it re-derives from scratch, once per element, a
position `enumerate` was already handing you for free.

`count` is the one that does not vary at all. Section 2 gave you the rule — never write
`count(v) > 0` to ask whether something is there — and chapter 3, section 4 gave you the reason:
`count` has no early exit, so it must reach the end to know it has seen every occurrence. What the
rule *costs* is the number neither of them puts a figure on, and it is a ratio rather than a time.

```python
import timeit

def per_call(stmt, setup, repeat=25):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

setup = "readings = list(range(50_000))"
for label, target in (("at the front", 0), ("in the middle", 25_000), ("at the back", 49_999)):
    asked = per_call(f"{target} in readings", setup)
    tallied = per_call(f"readings.count({target}) > 0", setup)
    print(f"{label:<14} in {asked:10.1f} ns   count > 0 {tallied:10.1f} ns"
          f"   {tallied / asked:9.1f}x")
# -> at the front   in        8.6 ns   count > 0   298618.8 ns     34686.1x
# -> in the middle  in   123156.2 ns   count > 0   296964.6 ns         2.4x
# -> at the back    in   247345.8 ns   count > 0   297766.7 ns         1.2x
```

The `count` column barely moves; the ratio column moves by four and a half orders of magnitude, and
its shape is exactly `n` over the depth of the target. Half way in, `count` walks twice as far as
the `in` did and the measured ratio is 2.4. At the back it walks the same distance and the ratio is
1.2. At the front it walks 50,000 elements against a single comparison. **The penalty for asking
with `count` is not a constant factor: it is the whole list divided by how deep the answer was, so
the cheaper the search should have been, the more the mistake costs you.** That is why the habit
survives testing — on the inputs where `in` was going to be slow anyway, `count` looks fine.

`remove`, `index`, `count`, and an `in` buried in a comprehension are the same mistake wearing four
faces. Each reaches for a position or a tally the list does not store, so it reconstructs it by
walking. That is fine once. It stops being fine the moment it happens per element — and not one of
those four spellings looks like a loop.

### The two ways out

Every cost on this page comes from one fact: an unordered list gives the scan no information, so it
has no choice but to look at everything. There are exactly two ways to escape that, and the rest of
the chapter is those two.

Change the structure. A `set` or `dict` computes where a value would live instead of hunting for
it, which is what the break-even table was buying. Chapter 1, section 10 covered these as
containers; section 4 covers them as search.

Or exploit an order the data already has. A sorted list *does* carry information, and halving
spends it: chapter 2, section 6 used `bisect` to find where a value should be inserted, and section
5 turns the same probe into a search that answers whether it is there — twenty comparisons on a
million elements, with no second copy of the data.

---

## 4. Searching by hashing

Sections 2 and 3 leave you with one shape and one price. To answer a question about an unsorted
list you walk it, and the walk is O(n) whichever spelling you reach for. No rearrangement of that
loop escapes it, because a list stores *positions* and you are asking about *values*. The way out
is not a cleverer scan. It is to spend one pass building a different structure — one that answers
the value question directly — and then interrogate that structure instead.

### Build once, then query

`set(iterable)` is that structure. You hand it a collection, it hashes every element as it goes,
and from then on `in` is a lookup rather than a walk.

```python
ids = [4102, 1877, 9330, 2604, 1877]
allowed = set(ids)

print(len(ids), len(allowed))   # -> 5 4      the duplicate collapsed
print(9330 in allowed)          # -> True
print(5555 in allowed)          # -> False
```

`x in ids` compares `x` against elements one after another until something matches or the list runs
out. `x in allowed` computes `hash(x)`, uses that number to pick the one table slot the value could
be living in, and compares only what it finds there. **A set is not a faster scan; it is a
structure that makes the scan unnecessary.** Chapter 1, section 8 gives the cost model this sits
inside, and section 10 of that chapter compares the containers themselves; what matters here is the
two-step shape. Build the structure first, from data you already have. Query it afterwards.

Those two steps stay separate, and the order is the whole technique. A build inside the loop you
were trying to speed up costs more than the scan it replaced.

### The lookup does not notice how big the set is

Take a list of random user ids at four sizes and, in each, ask about an id that was never issued.
Absence is the list's worst case: it has to look at everything before it can answer.

```python
import timeit

def per_call(stmt, setup, repeat=20):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

for n in (1_000, 10_000, 100_000, 1_000_000):
    setup = f"import random; random.seed(3)\nids = random.sample(range(10**7), {n})\nallowed = set(ids)"
    scan = per_call("-1 in ids", setup)
    probe = per_call("-1 in allowed", setup)
    print(f"{n:>9}  list {scan / 1000:9.1f} us   set {probe:5.1f} ns")
# ->      1000  list       6.4 us   set   8.9 ns
# ->     10000  list      58.9 us   set   8.9 ns
# ->    100000  list     693.3 us   set   7.7 ns
# ->   1000000  list    7227.6 us   set   6.8 ns
```

Every tenfold increase in `n` multiplies the list column by roughly ten, which is what O(n) looks
like when you plot it; the factor drifts above ten at the top end, where a list of a million
elements has stopped fitting in cache and every step of the walk pays for that. The set column
stays under ten nanoseconds at every size and shows no upward trend across a thousandfold range of
`n` — the small wobble it does show is run-to-run noise, and reruns move it in both directions. By
the last row one answer costs about a millionth of the other. That flatness is the whole product —
the cost of a membership test stops being a function of how much data you have.

The harness is chapter 1, section 11's: construction lives in `setup` so it is not timed, and the
minimum of the repeats is quoted because interference only ever adds.

### Constant on average, not in the worst case

The guarantee is weaker than the table makes it look, and the reason is worth holding onto. Two
different values can hash to the same slot. When they do, the second one goes to another slot, and
a later lookup has to follow that same trail, comparing as it goes — a small linear scan hidden
inside the constant. With well-spread hashes the trail is one or two slots long, so the average
stays flat. If every element hashes to the same number, the trail is the whole set and you are back
to the walk you were escaping.

You can build that pathological case deliberately. `__hash__` returning a constant is legal — the
one rule you must not break is that equal objects hash equally.

```python
import timeit

class Sensor:
    __slots__ = ("sid",)
    def __init__(self, sid):
        self.sid = sid
    def __eq__(self, other):
        return self.sid == other.sid
    def __hash__(self):
        return 0                        # legal, and catastrophic

class Spread(Sensor):
    def __hash__(self):
        return hash(self.sid)

for n in (1_000, 2_000, 4_000):
    collide = {Sensor(i) for i in range(n)}
    spread = {Spread(i) for i in range(n)}
    probe_c, probe_s = Sensor(n - 1), Spread(n - 1)
    one = min(timeit.repeat("probe_c in collide", globals=globals(), number=200, repeat=10))
    many = min(timeit.repeat("probe_s in spread", globals=globals(), number=200, repeat=10))
    print(f"{n:>5}  one hash {one / 200 * 1e9:10.1f} ns   spread hashes {many / 200 * 1e9:6.1f} ns")
# ->  1000  one hash    45083.8 ns   spread hashes   86.0 ns
# ->  2000  one hash    77780.6 ns   spread hashes   71.2 ns
# ->  4000  one hash   178859.6 ns   spread hashes   71.2 ns
```

The left column roughly doubles when `n` doubles. The right column sits still. Both are sets; only
the hash function differs. You have to work to produce the left column — `int`, `str`, `tuple` and
the rest of the built-in types spread their hashes well, and chapter 1, section 8 measures how mild
the effect is even for integers chosen to collide. But "O(1) membership" is an average, and this is
what it is averaging over.

### What the structure costs

**Building it is a full linear pass, and the pass has a real constant on it.** Section 3 priced
that constant against the scan it replaces and located the break-even, which turns out to be a
small number of lookups rather than a large one. What one machine's table cannot show is that
**the constant is not a single number.** A hash table writes each element into the slot its hash
picks, so consecutive keys land in neighbouring slots and scattered keys land all over the table.
Same linear pass, very different walk through memory.

```python
import timeit

def us(stmt, setup, number=20, repeat=15):
    t = timeit.Timer(stmt, setup=setup)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e6

for label, make in (("consecutive", "ids = list(range(100_000))"),
                    ("scattered  ", "import random; random.seed(3)\n"
                                    "ids = random.sample(range(10**7), 100_000)")):
    setup = make + "\nallowed = set(ids)"
    scan = us("-1 in ids", setup)
    build = us("set(ids)", setup)
    print(f"{label}  scan {scan:7.1f} us   build {build:7.1f} us   build = {build / scan:4.1f} scans")
# -> consecutive  scan   543.9 us   build   659.9 us   build =  1.2 scans
# -> scattered    scan   563.6 us   build  2580.0 us   build =  4.6 scans
```

Both rows hold 100,000 integers, and the two scans land within a few per cent of each other,
because a scan reads the list in the order it was laid out either way. Only the build differs. The
top row is stable at close to one scan across reruns; the bottom row is not, and repeated runs put
it anywhere between four and nine. That instability is itself the finding — what varies is the
memory system, not the algorithm. Section 3 measured on consecutive integers, and against searches
that stop halfway because the value is present; both choices put its constant at the cheap end of
this range.

None of it changes the shape. The build is O(n) once, each query is O(1) after, and the question to
ask before reaching for a set is still section 3's. It changes how much slack you have when the
answer is close.

The memory is the second cost. A hash table deliberately leaves a large fraction of its slots empty
so that collisions stay rare, and you pay for the empty slots. Chapter 1, section 10 priced a list,
a set and a dict of 100,000 integers side by side; the part worth adding here is that the factor it
quotes is not a constant.

```python
import sys
for n in (60_000, 100_000, 160_000, 200_000):
    ids = list(range(n))
    allowed = set(ids)
    print(n, sys.getsizeof(ids), sys.getsizeof(allowed),
          round(sys.getsizeof(allowed) / sys.getsizeof(ids), 2))
# -> 60000 480056 2097368 4.37
# -> 100000 800056 4194520 5.24
# -> 160000 1280056 8388824 6.55
# -> 200000 1600056 8388824 5.24
```

The list grows eight bytes per element, smoothly. The set grows in doublings and then sits on the
new size: the last two rows are the *same* table, so 40,000 further elements were absorbed for
nothing while the ratio fell from 6.55 back to 5.24. Budget for the peak, which is the row before a
doubling, not for the average. All of these figures are container overhead only — the same integer
objects sit behind the list and the set — so none of them is a total, but the ratio between two
containers holding the same objects is honest.

The third cost is a restriction on what you may store. Every element must be hashable, which rules
out lists.

```python
palette = {(255, 0, 0), (0, 128, 0)}
try:
    palette.add([0, 0, 255])
except TypeError as e:
    print(type(e).__name__, e)
    # -> TypeError cannot use 'list' as a set element (unhashable type: 'list')

palette.add((0, 0, 255))
print((0, 0, 255) in palette)   # -> True
```

The tuple is the fix whenever the thing you want to look up is a small fixed group of values.

The rule reaches your own types too. Defining `__eq__` and leaving `__hash__` alone makes a class
unhashable, because a type is not allowed to declare two objects equal while inheriting a hash that
would file them in different slots.

```python
class Reading:
    def __init__(self, celsius):
        self.celsius = celsius
    def __eq__(self, other):
        return self.celsius == other.celsius

print(Reading(21.5) == Reading(21.5))   # -> True
try:
    {Reading(21.5)}
except TypeError as e:
    print(type(e).__name__, e)
    # -> TypeError cannot use 'Reading' as a set element (unhashable type: 'Reading')
```

Write a `__hash__` that agrees with the `__eq__`, the way `Spread` does above, and the type becomes
something you can look up.

The fourth is that **membership is not limited to the object you handed it, and equality has
whatever meaning the type gives it.** After the identity check chapter 1, section 8 established —
the hash finds the slot, and an occupant that is the very same object matches without any
comparison at all — a set confirms a candidate with `==`, so anything that compares equal to a
stored element is "in" the set.

```python
print(1.0 in {1}, True in {1})   # -> True True
print("10" in {10})              # -> False
```

`1 == 1.0 == True`, and they hash alike, so one entry answers for all three. A string never equals
an integer, so the last line is `False` rather than an error. A linear scan has exactly these
semantics too — identity first, then equality. The set does not change the rule, it just applies
it in one step instead of `n`.

### When you want something back, not just yes or no

A search often has to return a payload: not "is this station id known" but "which station is it".
`dict` is the same hash table with a value attached to each key, at the same lookup cost.

```python
records = [(4102, "oslo"), (1877, "cairo"), (9330, "lima"), (2604, "perth")]
station = dict(records)

print(9330 in station)                  # -> True       membership tests the key
print(station[9330])                    # -> lima
try:
    station[5555]
except KeyError as e:
    print(type(e).__name__, e)          # -> KeyError 5555
print(station.get(5555))                # -> None
print(station.get(5555, "unassigned"))  # -> unassigned
print(5555 in station)                  # -> False      and .get did not insert it
```

`dict[key]` raises on a miss; `dict.get(key)` returns `None`; `dict.get(key, default)` returns
whatever you nominate. Section 7 takes up which of those three a search should hand back. Against a
scan of the pairs, the payoff is the same shape as the set's:

```python
import timeit

def per_call(stmt, setup, repeat=20):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

setup = """
import random; random.seed(3)
ids = random.sample(range(10**7), 100_000)
records = [(i, f"city-{i}") for i in ids]
by_id = dict(records)
wanted = ids[70_000]
city = by_id[wanted]
"""
print(round(per_call("next(name for k, name in records if k == wanted)", setup) / 1000, 1))
print(round(per_call("by_id[wanted]", setup), 1))
print(round(per_call("city in by_id.values()", setup) / 1000, 1))
# -> 744.8
# -> 7.1
# -> 746.5
```

Three quarters of a millisecond to walk the pairs, 7.1 nanoseconds to ask the dict — better than a
hundred thousandfold, once the dict exists. The third line is the one to sit with. **A hash table
answers the question you keyed it on, and only that one.** There is no table to go through for a
city name, so `.values()` walks, and the walk lands in the same hundreds-of-microseconds league as
the pair scan it was supposed to replace. The two are the same linear work over the same 100,000
entries, close enough that which of them prints the larger number changes from run to run; against
the keyed lookup they are the same answer. If what you keep looking up is the name, the name is
what has to be the key.

### Dicts remember the order; sets do not

This is a real difference between the two, and it is easy to check rather than take on faith. Build
the same five keys in two different orders, as a dict and as a set:

```python
first = dict.fromkeys([507, 12, 883, 44, 291])
second = dict.fromkeys([291, 44, 883, 12, 507])
print(list(first))     # -> [507, 12, 883, 44, 291]
print(list(second))    # -> [291, 44, 883, 12, 507]

third = set([507, 12, 883, 44, 291])
fourth = set([291, 44, 883, 12, 507])
print(list(third))     # -> [291, 12, 44, 883, 507]
print(list(fourth))    # -> [291, 44, 12, 883, 507]
print(third == fourth) # -> True
```

`dict.fromkeys(seq)` above is a dict built from those keys with `None` under each one — the
shortest spelling when only the keys matter. Each dict hands back exactly the sequence it was
given. Neither set does, and the two sets do not even agree with each other although they compare
equal, because a set's order falls out of where the hashes landed and how the collisions were
resolved, which depends on insertion history you were not thinking about. Treat it as unspecified.
The consequence for a search is narrow but sharp: **the moment an answer depends on which matching
element comes first, a set cannot be the thing you iterate.** Sort it, or keep the list.

### Set operations are searches in bulk

`&`, `-`, `^` and `<=` ask a whole collection's worth of membership questions in one call.

```python
catalogue = {4102, 1877, 9330, 2604}
recalled = {9330, 7001}

print(catalogue & recalled)         # -> {9330}                    in both
print(catalogue - recalled)         # -> {2604, 1877, 4102}        in the first only
print(catalogue ^ recalled)         # -> {4102, 2604, 1877, 7001}  in exactly one
print({9330, 2604} <= catalogue)    # -> True                      every one present
```

The operators require sets on both sides; the method spellings take any iterable, which saves a
conversion when the right-hand side arrives as a list.

```python
catalogue = {4102, 1877, 9330, 2604}
try:
    catalogue & [9330, 7001]
except TypeError as e:
    print(type(e).__name__, e)
    # -> TypeError unsupported operand type(s) for &: 'set' and 'list'
print(catalogue.intersection([9330, 7001]))   # -> {9330}
```

Against a hand-written loop the win is not the hashing — the loop hashes too — but that `&` walks
the smaller collection and probes the larger, whichever way round you wrote it. A loop searches
whatever you told it to iterate.

```python
import timeit

def per_call(stmt, setup, repeat=15):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e6

setup = """
import random; random.seed(11)
catalogue = set(random.sample(range(1_000_000), 200_000))
recalled = set(random.sample(range(1_000_000), 200))
cat_list, rec_list = list(catalogue), list(recalled)
"""
print(round(per_call("catalogue & recalled", setup), 2))
print(round(per_call("{x for x in cat_list if x in recalled}", setup), 2))
print(round(per_call("{x for x in rec_list if x in catalogue}", setup), 2))
# -> 1.28
# -> 2847.96
# -> 2.74
```

All three compute the same 40 ids. The middle line iterates 200,000 elements to find them and costs
more than two thousand times what the operator costs; the last line iterates 200 and lands within
two or three times it. The operator gets the good version without your having to notice which
collection is the smaller one — and when the two are comparable in size it and the loop converge,
because there is no smaller side left to pick.

---

## 5. Searching a sorted sequence

Every search up to here knew nothing about the sequence it walked, so it had no choice but to look
at everything until it found a reason to stop. Order is information, and a search told that its
input is sorted can spend that information instead of comparisons: in a sorted sequence, every
element you look at tells you something about every element you did not look at.

### Halving instead of walking

Look at the middle element. Either it is smaller than the value you want — in which case nothing at
that position or before it can be your target, and the whole first half is gone — or it is not, in
which case nothing after it can be, and the whole second half is gone. One comparison eliminates
half of what was left. Repeat on what remains.

```python
temps = [11, 14, 17, 19, 23, 26, 31, 34, 38]

def locate(nums, target):
    lo, hi = 0, len(nums)                 # the live window is nums[lo:hi]
    while lo < hi:
        mid = (lo + hi) // 2
        print(f"window {nums[lo:hi]!s:<38} probe nums[{mid}] = {nums[mid]}")
        if nums[mid] < target:
            lo = mid + 1                  # target cannot be at mid or before it
        else:
            hi = mid                      # target cannot be after mid
    return lo

print(locate(temps, 26))
# -> window [11, 14, 17, 19, 23, 26, 31, 34, 38]   probe nums[4] = 23
# -> window [26, 31, 34, 38]                       probe nums[7] = 34
# -> window [26, 31]                               probe nums[6] = 31
# -> window [26]                                   probe nums[5] = 26
# -> 5
```

Nine elements, four probes, and the window loses at least half its width every round. The bounds
are half-open — `lo` included, `hi` excluded — which is the same convention slicing uses (chapter 1
section 5) and is why `nums[lo:hi]` prints the live window without any adjustment. **The number of
rounds is the number of times you can halve n before nothing is left, and that is what makes the
work logarithmic rather than linear.**

### What halving costs

Count probes rather than nanoseconds. A count is a property of the procedure, so it reproduces
exactly, where a timing carries the machine along with it — the distinction chapter 1 section 11
draws between measuring growth and measuring time. Run the same loop over a sweep of targets —
every one of them up to n = 100,000, every seventh above that — and keep the worst case:

```python
import math

def probes(n, target):
    lo, hi, count = 0, n, 0
    while lo < hi:
        mid = (lo + hi) // 2
        count += 1
        if mid < target:                  # the sequence is range(n), so nums[mid] is mid
            lo = mid + 1
        else:
            hi = mid
    return count

for n in (10, 100, 1_000, 10_000, 100_000, 1_000_000):
    step = 1 if n <= 100_000 else 7
    worst = max(probes(n, t) for t in range(0, n + 1, step))
    print(f"n = {n:>9}   probes {worst:>2}   ceil(log2(n+1)) = {math.ceil(math.log2(n + 1)):>2}"
          f"   scan {n:>9}")
# -> n =        10   probes  4   ceil(log2(n+1)) =  4   scan        10
# -> n =       100   probes  7   ceil(log2(n+1)) =  7   scan       100
# -> n =      1000   probes 10   ceil(log2(n+1)) = 10   scan      1000
# -> n =     10000   probes 14   ceil(log2(n+1)) = 14   scan     10000
# -> n =    100000   probes 17   ceil(log2(n+1)) = 17   scan    100000
# -> n =   1000000   probes 20   ceil(log2(n+1)) = 20   scan   1000000
```

Every row is exactly `ceil(log2(n + 1))`. Read the last two columns together: twenty questions
against a million, where the scan of section 3 asks a million. Multiply the size by a thousand and
the halving search adds ten probes, while the scan adds three zeroes. Chapter 2 section 6 counted
this same halving from the other side, by instrumenting `__lt__` and watching `bisect_left` probe a
list, and got the same figures — it is the same procedure, priced there as the cheap half of an
insertion and here as the entire job.

### The precondition, and what it costs to buy

None of this survives if the sequence is not sorted. Chapter 2 section 6 showed what happens when
you break that precondition: no exception, no warning, a confident and meaningless index. The
useful question is not whether the rule exists but what it costs to satisfy.

```python
import random, timeit
from bisect import bisect_left

random.seed(11)
n = 200_000
ids = random.sample(range(10_000_000), n)      # unsorted user ids
ordered = sorted(ids)
missing = 10_000_001                           # absent, so nothing short-circuits early

scan  = min(timeit.repeat(lambda: missing in ids, number=20, repeat=7)) / 20
srt   = min(timeit.repeat(lambda: sorted(ids), number=5, repeat=7)) / 5
probe = min(timeit.repeat(lambda: bisect_left(ordered, missing),
                          number=200_000, repeat=7)) / 200_000

print(f"one linear scan    {scan * 1e6:9.1f} us")
print(f"one sort           {srt * 1e6:9.1f} us")
print(f"one bisect probe   {probe * 1e6:9.3f} us")
print(f"crossover at k =   {srt / (scan - probe):9.1f} searches")
# -> one linear scan       1218.9 us
# -> one sort             26108.5 us
# -> one bisect probe        0.090 us
# -> crossover at k =        21.4 searches
```

The probe is roughly four orders of magnitude cheaper than the scan, and the sort costs about
twenty scans. **If you are going to search once, sorting first is the slowest thing you can do: you
pay twenty linear searches to avoid one.** The sort is O(n log n) and the scan it replaces is O(n),
so the setup is asymptotically worse than the work it saves, and it only pays back when spread over
enough queries. Confirm the crossover by running both routes end to end at several query counts:

```python
import random, timeit
from bisect import bisect_left

random.seed(11)
ids = random.sample(range(10_000_000), 200_000)
targets = [random.randrange(10_000_000, 20_000_000) for _ in range(80)]   # all absent

def by_scan(k):
    return [q in ids for q in targets[:k]]

def by_search(k):
    s = sorted(ids)
    out = []
    for q in targets[:k]:
        i = bisect_left(s, q)
        out.append(i < len(s) and s[i] == q)
    return out

for k in (1, 5, 10, 20, 40, 80):
    assert by_scan(k) == by_search(k) and len(targets[:k]) == k
    a = min(timeit.repeat(lambda: by_scan(k), number=1, repeat=9)) * 1000
    b = min(timeit.repeat(lambda: by_search(k), number=1, repeat=9)) * 1000
    print(f"k = {k:>3}   scan {a:7.1f} ms   sort + bisect {b:7.1f} ms   ratio {a / b:5.2f}")
# -> k =   1   scan     1.1 ms   sort + bisect    27.2 ms   ratio  0.04
# -> k =   5   scan     5.6 ms   sort + bisect    27.4 ms   ratio  0.20
# -> k =  10   scan    11.1 ms   sort + bisect    27.5 ms   ratio  0.40
# -> k =  20   scan    22.8 ms   sort + bisect    29.1 ms   ratio  0.78
# -> k =  40   scan    46.6 ms   sort + bisect    26.8 ms   ratio  1.74
# -> k =  80   scan    94.5 ms   sort + bisect    22.6 ms   ratio  4.19
```

The `targets` list has exactly 80 entries and the largest `k` asks for all of them, which is what
keeps the scan column readable: it is a straight multiple of `k`, because nothing is reused between
one lookup and the next. The search column is almost entirely the one sort and barely notices `k`
at all. The ratio is therefore a straight line through the origin, and where it crosses 1.00 is the
crossover — here between twenty and forty queries, which is what the unit costs above predicted.
The `k = 20` row sits close enough to 1.00 that repeated runs land on either side of it; that is
what being at a crossover looks like. The exact figure is a property of the machine and will move
on yours; the shape will not. **So binary search pays when the data arrives already ordered, or
when you will query the same data enough times to amortize the ordering.**

If membership is all you want, ordering is not even the cheapest way to buy it. On the same 200,000
ids, `set(ids)` measured 9.3 ms against the sort's 25.1 ms, and one `in` test on the set took
16.0 ns against the probe's 87.5 ns — cheaper to build and cheaper to ask. What it costs is memory:
`sys.getsizeof` reports 1,600,056 bytes for the sorted list and 8,388,824 for the set. So the sorted
sequence earns its place when the data is already in order, when the memory matters, or when the
question is one a hash table cannot answer at all — where does this value belong, what is the
nearest value below it, which values fall in this range. Chapter 1 section 10 sets the two
containers side by side on those terms.

### bisect answers "where", not "whether"

Reach for `bisect` rather than the loop above. Chapter 2 section 6 introduced the module for
insertion and covered the parts that carry over unchanged: what `bisect_left` and `bisect_right`
return, the `lo` and `hi` window arguments, `insort`, and the fact that `bisect` is a second name
for `bisect_right`. What matters for searching is that the answer is an *insertion point*.

```python
from bisect import bisect_left, bisect_right

stock = [0, 2, 5, 5, 5, 9, 12]                             # inventory counts, in order
print(bisect_left(stock, 5), bisect_right(stock, 5))       # -> 2 5    present, three times
print(bisect_left(stock, 7), bisect_right(stock, 7))       # -> 5 5    absent, inside
print(bisect_left(stock, 20), bisect_right(stock, 20))     # -> 7 7    absent, past the end
```

Every one of those six numbers is an index at which the value could be inserted with the order
preserved, which is the point: an insertion point exists for values that are in the sequence and for
values that are not, and nothing in the return type tells you which case you are in. **The return
value is an index whether or not the value is there, so it is never by itself a membership answer**
— 5 came back for the absent 7, 7 came back for the absent 20, and 7 is not even a valid subscript
into a sequence of seven elements. The first row is the left/right distinction chapter 2 section 6
already drew, seen from the searching side: the two straddle the run of equal values, `bisect_left`
returning the first position holding the value and `bisect_right` the position just past the last
one, so `bisect_left` is the one whose answer is a position you can actually read the value out of.

The standard idiom turns "where" into "whether" in two steps, a range check and an equality check:

```python
from bisect import bisect_left

stock = [0, 2, 5, 5, 5, 9, 12]

def contains(ordered, value):
    i = bisect_left(ordered, value)
    return i < len(ordered) and ordered[i] == value

def index_of(ordered, value):
    i = bisect_left(ordered, value)
    return i if i < len(ordered) and ordered[i] == value else -1

print(contains(stock, 5), contains(stock, 7), contains(stock, 20))
# -> True False False
print(index_of(stock, 9), index_of(stock, 7))
# -> 5 -1
```

Both halves are load-bearing. Drop the range check and a value past the end raises `IndexError`.
Reach for `bisect_right` out of habit and the guard reads the slot after the run, which is a
different value or off the end:

```python
from bisect import bisect_right

stock = [0, 2, 5, 5, 5, 9, 12]
i = bisect_right(stock, 5)
print(i, i < len(stock) and stock[i] == 5)   # -> 5 False
```

5 is in the list three times and that says it is not there. `bisect_left` is the one that pairs
with an equality guard. Note also that `contains` never assumed a list — the search half of the
module reads any sorted sequence, and copies nothing:

```python
from bisect import bisect_left

def contains(ordered, value):
    i = bisect_left(ordered, value)
    return i < len(ordered) and ordered[i] == value

names = ("Ada", "Grace", "Hedy", "Karen", "Radia")
print(contains(names, "Hedy"), contains(names, "Hopper"))                 # -> True False
print(contains(range(0, 1_000_000, 2), 999_998),
      contains(range(0, 1_000_000, 2), 999_999))                          # -> True False
```

### Searching by a key

`key` behaves for the search functions exactly as chapter 2 section 6 established it for insertion.
What searching adds is a generalized guard: check the range, then compare the *key* of what you
found against the key you asked for — `ordered[i] == value` was only ever the special case where
the key is the element itself. And "sorted by that key" stops being a rule about where a value
would be placed and becomes a rule about whether the answer coming back is true. Break it and the
guard does not rescue you; it compares the key at whatever index it was handed.

```python
from bisect import bisect_left

sensors = [(3, "attic"), (7, "cellar"), (12, "porch"), (19, "shed")]
sensor_id = lambda rec: rec[0]

i = bisect_left(sensors, 12, key=sensor_id)
print(i, sensors[i])                                        # -> 2 (12, 'porch')
i = bisect_left(sensors, 13, key=sensor_id)
print(i, i < len(sensors) and sensor_id(sensors[i]) == 13)  # -> 3 False

scrambled = [(3, "attic"), (7, "cellar"), (19, "shed"), (12, "porch")]   # not sorted by id
i = bisect_left(scrambled, 12, key=sensor_id)
print(i, scrambled[i], i < len(scrambled) and sensor_id(scrambled[i]) == 12)
# -> 2 (19, 'shed') False
```

Only the last two records are out of order by id, and a sensor sitting in the list reports absent.
**A guard can only tell you that the position it was given does not hold your value; it cannot tell
you the search looked in the right place.**

### Do not write it yourself

The loop at the top of this section exists to show the mechanism, not to be copied. Binary search is
notorious for correct-looking variants that are wrong at one boundary, and the failures hide in
exactly the inputs a hand-written test list forgets. Here is `hi` initialized to a last index rather
than to a bound, checked against `bisect_left` on every sorted sequence from a small universe:

```python
from bisect import bisect_left
from itertools import combinations_with_replacement

def find(nums, target):
    lo, hi = 0, len(nums) - 1        # a last index, where a bound was meant
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo

cases = [(list(v), t)
         for size in range(1, 7)
         for v in combinations_with_replacement(range(5), size)
         for t in range(0, 6)]
bad = [(n, t) for n, t in cases if find(n, t) != bisect_left(n, t)]
print(len(cases) - len(bad), "agreements,", len(bad), "disagreements")
# -> 1980 agreements, 786 disagreements
print(min(bad, key=lambda c: (len(c[0]), c[0], c[1])))
# -> ([0], 1)
print(find([11, 14, 19], 23), bisect_left([11, 14, 19], 23))
# -> 2 3
```

It agrees on 1,980 cases and every one of the 786 failures has the same shape: a target larger than
everything present, where the correct answer is `len(nums)` and this version can never return it.
A test set that only ever searches for values inside the range passes it completely. **`bisect_left`
and `bisect_right` are the ones to reach for: they are correct at the boundaries, and the halving
loop itself lives in the C accelerator module `_bisect`, so the window arithmetic and the branching
cost no bytecode.**

That is a claim about the loop, not about the comparisons. Each probe still calls back into the
interpreter whenever the thing being compared is defined in Python, and `sys.setprofile` will count
those entries:

```python
import sys
from bisect import bisect_left

python_calls = 0
def note(frame, event, arg):
    global python_calls
    if event == "call":
        python_calls += 1

plain = list(range(1000))
records = [(i, "x") for i in range(1000)]
sensor_id = lambda rec: rec[0]

python_calls = 0
sys.setprofile(note); bisect_left(plain, 500); sys.setprofile(None)
print(python_calls)                                     # -> 0

python_calls = 0
sys.setprofile(note); bisect_left(records, 500, key=sensor_id); sys.setprofile(None)
print(python_calls)                                     # -> 9
```

Zero against nine. Searching a list of plain integers runs start to finish without executing a line
of Python, while the same search with a `key` stops at the lambda once per probe. Nine, not the ten
the table above gives for a thousand elements, because this block searches for one particular
target and 500 is a target that settles a probe early; ten is the worst case over all of them.
Chapter 2, section 6 watched the same per-probe callback from the other side, instrumenting `__lt__`
and counting comparisons rather than frames. That is the mechanism its comparison counts depended
on: instrumenting `__lt__` could only produce a number because `bisect_left` was calling a Python
method on every probe. It is the same reason `key` is charged per probe and not per element. Write
the loop by hand when you are learning what it does, or when the decision at each step is something
`key` cannot express — and then test it differentially against `bisect`, the way the block above
does.

---

## 6. Searching by predicate

Almost every search so far began with a value you could write down. `in`, `index` and `count` take
the thing itself (section 2); a set or dict lookup hashes it (section 4); `bisect` compares against
it (section 5). Often you cannot write it down. You know the reading was above the alarm threshold,
or the inventory count fell under the reorder point, or the user has the owner role — you have a
*description* of the target rather than the target, and the only way to learn which element fits it
is to ask each one. Section 2 met the first case of this, a record matched on one of its fields,
and used `next` over a generator expression to answer it. This section takes that spelling as far
as it goes and adds the tools that share its shape.

**A description gives a search nothing to exploit: hashing needs the value and halving needs the
order, and a predicate supplies neither.** Everything in this section is therefore the linear scan
of section 2, and what separates the tools is where each one is permitted to stop.

### `next` over a generator expression

A generator expression is a scan that has not run yet, and `next` pulls exactly one element out of
it. Together they are how Python spells *the first element satisfying a condition*.

```python
readings = [18.0, 21.5, 19.2, 34.6, 22.1, 40.3]
print(next((r for r in readings if r > 30.0), None))     # -> 34.6
print(next((r for r in readings if r > 90.0), None))     # -> None
```

The second argument is the default — what `next` evaluates to when the generator has nothing left to
give. Section 2 showed what leaving it out costs: a bare `StopIteration` carrying an empty message,
raised from a line that reads like a lookup. One pair of parentheses is enough when the generator
expression is the sole argument, which is why the no-default form looks lighter than it is. Section
7 takes the no-match case apart properly; for now, treat the default as load-bearing rather than as
punctuation.

### The bracket decides whether the scan stops

The obvious alternative is to build the list of everything that matches and take element zero. It
gives the same answer and it cannot stop early, because a list comprehension is finished before its
first element is available to anyone. Section 2 priced that with the match at the front. The figure
it reported is not a property of `next`, and the way to see so is to move the match: put one
qualifying reading into a 200,000-element list and walk it down the list.

```python
import timeit

loop = """
hit = None
for r in readings:
    if r > 50:
        hit = r
        break
"""
for pos in (5, 100_000, 199_999):
    setup = f"readings = [3.0] * 200_000\nreadings[{pos}] = 97.4"
    n = 20_000 if pos < 100 else 200
    lazy = min(timeit.repeat("next((r for r in readings if r > 50), None)",
                             setup=setup, number=n, repeat=9)) / n * 1e6
    eager = min(timeit.repeat("[r for r in readings if r > 50][0]",
                              setup=setup, number=200, repeat=9)) / 200 * 1e6
    scan = min(timeit.repeat(loop, setup=setup, number=n, repeat=9)) / n * 1e6
    print(f"match at {pos:>6}   next {lazy:9.2f} us   for/break {scan:9.2f} us"
          f"   list {eager:9.2f} us   {eager / lazy:8.1f}x")
# -> match at      5   next      0.16 us   for/break      0.09 us   list   2394.07 us    15033.4x
# -> match at 100000   next   1122.04 us   for/break   1089.23 us   list   2169.02 us        1.9x
# -> match at 199999   next   2122.58 us   for/break   2116.61 us   list   2145.73 us        1.0x
```

The right-hand column is the whole argument. When the match is near the front, `next` costs about a
sixth of a microsecond and the comprehension costs two milliseconds — a factor that stayed above ten
thousand across every rerun, and which is not a property of `next` at all but of how far into the
list the answer lives. Halfway along, the ratio collapses to about 2, exactly as you would predict
from one scan against half a scan; reruns put it between 1.9 and 2.6. At the last element the two
are indistinguishable, and reruns swapped their order.
**The early exit is worth the entire distance it saves and nothing more, so `next` never loses and
usually wins by however much of the list it did not have to look at.**

The middle column is the hand-written scan from section 2, and it is the honest control. Building
the generator object costs 0.065 µs on its own, which is why the loop leads on the first row; past
that the two run within a few percent on a quiet machine and trade places between sittings, the loop
ahead in some runs and behind in others. `next` is not faster than a `for` with a `break` — it is
the same algorithm as one expression, and that is the reason to prefer it.

### `any` and `all` stop where the answer is settled

When you want the yes-or-no rather than the element, `any` is the same scan with the value thrown
away, and `all` is the same scan looking for the first counterexample. Chapter 1 section 6 priced
the short circuit; what it looks like from the search side is best seen by counting how far the
scan actually got, with a generator that reports on its own progress:

```python
examined = 0

def watched(values):
    global examined
    for v in values:
        examined += 1
        yield v

temps = [18, 21, 34, 19, 22, 40, 17]

examined = 0
print(any(t > 30 for t in watched(temps)), "elements examined:", examined)
# -> True elements examined: 3
examined = 0
print(all(t > 20 for t in watched(temps)), "elements examined:", examined)
# -> False elements examined: 1
examined = 0
print(any(t > 90 for t in watched(temps)), "elements examined:", examined)
# -> False elements examined: 7
examined = 0
print(all(t > 15 for t in watched(temps)), "elements examined:", examined)
# -> True elements examined: 7
examined = 0
print(any([t > 30 for t in watched(temps)]), "elements examined:", examined)
# -> True elements examined: 7
```

Three elements to say yes, one to say no, and the full seven whenever the answer needs every element
to agree. **A `True` from `any` and a `False` from `all` are both witnessed by a single element, so
both stop at it; the opposite answers are claims about the whole sequence and cost the whole
sequence.** The last line is chapter 1's bracket trap in the same units: the list is built in full
before `any` is called at all, so the short circuit is gone and seven elements are examined to learn
what three would have settled. On the 200,000-element list above, with the one qualifying reading at
index 5, adding those two brackets took the same call from 0.195 to 2,130 microseconds, and reruns
held the factor between ten and eleven thousand.

Note also `any([])` is `False` and `all([])` is `True`, which is chapter 1 section 6's pair, and it
is the reason `all` over an empty result is so often the answer that surprises.

### Asking for the position instead of the value

`index` finds a position, but only for a value you can name. To get the position of the first
element matching a *predicate*, put `enumerate` inside the generator and yield the index rather than
the element — chapter 1 section 6 introduced `enumerate`; this is the shape it is most useful in.

```python
readings = [18.0, 21.5, 19.2, 34.6, 22.1, 40.3]
print(next((i for i, r in enumerate(readings) if r > 30.0), -1))   # -> 3
print(next((i for i, r in enumerate(readings) if r > 90.0), -1))   # -> -1
```

The sentinel changes because the return type did: `-1` is the reflex not-found for something that
is otherwise an index, the way `None` was the reflex for something that was otherwise a reading.
Treat the first of those as contested rather than settled — a sentinel that is itself a legal
index has a failure mode the reading case does not, and section 7 is where that argument is had.

Paying for the index is not free, and neither is the obvious alternative of finding the value and
then looking up where it was:

```python
import timeit

setup = "readings = [3.0] * 200_000\nreadings[199_999] = 97.4"
for label, stmt in (
    ("the value", "next((r for r in readings if r > 50), None)"),
    ("its index", "next((i for i, r in enumerate(readings) if r > 50), -1)"),
    ("value, then index", "readings.index(next((r for r in readings if r > 50), None))"),
):
    t = min(timeit.repeat(stmt, setup=setup, number=200, repeat=9)) / 200 * 1e6
    print(f"{label:<20}{t:9.2f} us")
# -> the value             2445.44 us
# -> its index             3819.66 us
# -> value, then index     3217.91 us
```

Both index-producing spellings landed between 1.25x and 1.85x the value-only figure across reruns,
and the two-pass version came in the quicker of the two every time — unpacking a tuple per element
is real work, and a second scan running at C speed is cheap enough to undercut it. That margin is
not a reason to choose it, and the reason to avoid it survives the margin: it asks a second
question, *where is the first element equal to this value*, which is not the question you asked. The
two answers agree only because a predicate over one element depends on nothing but that element's
value, so no earlier element could have held that same value and failed the test. **You are relying
on a property of the predicate to make a second search stand in for the first**, and the `enumerate`
spelling is what it costs to stop relying on it.

### `min` and `max` are searches too

`min` and `max` also find an element by description — the smallest, the largest, or with `key`, the
element scoring best on something computed from it. They belong in this section, and they have one
property none of the tools above shares.

```python
palette = [(200, 30, 30), (10, 10, 200), (250, 250, 40), (0, 0, 0)]
print(max(palette, key=sum))                        # -> (250, 250, 40)
print(min(palette, key=lambda c: c[1]))             # -> (0, 0, 0)

names = ["ada", "grace", "bo", "katherine"]
print(max(names, key=len), min(names, key=len))     # -> katherine bo

print(max([], key=len, default=None))               # -> None
try:
    max([], key=len)
except ValueError as e:
    print(type(e).__name__, str(e))                 # -> ValueError max() iterable argument is empty
```

`default=` is the same idea as `next`'s second argument and fills the same hole. On a tie both
functions keep the first element they met, so `max` and `min` are stable in the direction you would
hope.

The property is that neither can stop:

```python
import timeit

for pos in (0, 100_000, 199_999):
    setup = f"prices = [50] * 200_000\nprices[{pos}] = 1"
    t = min(timeit.repeat("min(prices)", setup=setup, number=200, repeat=9)) / 200 * 1e6
    print(f"smallest at {pos:>6}   min(prices) {t:8.2f} us")
# -> smallest at      0   min(prices)  1347.17 us
# -> smallest at 100000   min(prices)  1378.10 us
# -> smallest at 199999   min(prices)  1371.60 us
```

A few percent between the first row and the last — reruns held the spread between 2% and 9% — while
the answer's position moved across the entire list, and `next` on that same shape of input moved by
a factor above ten thousand. **No element can prove it is the smallest, so there is no witness to
stop at and `min` is O(n) on every input there is**, which is what chapter 1 section 8's table means
by describing it as one pass. `in` and `index` carry the same O(n) row and are the operations that
sometimes do far less than it.

`key` is charged per element, because it is a call per element. On `list(range(200_000))`,
`min(prices)` measured 1,394 to 1,495 µs across four sittings, `min(prices, key=abs)` 2,115 to
2,231 µs, and `min(prices, key=lambda p: -p)` 4,941 to 5,010 µs. A built-in as the key cost about
half again as much as no key at all, and a `lambda` about three and a half times as much. The
ordering held every time; treat the ratios as the finding and the figures as one machine's.

### Where the walrus earns its place

A predicate search hands back two things at once: whether there was a match, and what it was. An
`if` wants the first and the body wants the second, and `:=` is what lets one line supply both.

```python
readings = [18.0, 21.5, 19.2, 34.6, 22.1, 40.3]
if (hot := next((r for r in readings if r > 30.0), None)) is not None:
    print(f"first above 30: {hot}")
else:
    print("nothing above 30")
# -> first above 30: 34.6
```

The version without it needs a separate assignment line, which is a small loss on its own and a real
one in a ladder, where each branch is a different search and no plain assignment can be placed
between an `elif` and its condition:

```python
users = [{"id": 7, "role": "editor"}, {"id": 12, "role": "owner"}, {"id": 3, "role": "editor"}]
if (who := next((u for u in users if u["role"] == "admin"), None)) is not None:
    print("admin", who["id"])
elif (who := next((u for u in users if u["role"] == "owner"), None)) is not None:
    print("owner", who["id"])
else:
    print("nobody in charge")
# -> owner 12
```

Both examples spell out `is not None`, and that is not ceremony. Write the condition as a truth test
and the search reports failure whenever it succeeds on a falsy element:

```python
counts = [7, 0, 4]
if low := next((c for c in counts if c < 5), None):
    print("restock", low)
else:
    print("looks fine")
# -> looks fine
print(next((c for c in counts if c < 5), None))     # -> 0
```

The search found the element at index 1 and the `if` threw the answer away. Zero inventory, an empty
name, an RGB channel at black — **a sentinel is only a sentinel if you compare against it, and
`if x:` compares against something else entirely.** The walrus is what makes the mistake easy,
because `if low := ...` reads so much better than the version that is correct. Section 7 is where
the choice of sentinel and the alternatives to having one get decided.

### What the predicate is handed

Every predicate in this section is a test one element can answer by itself: is this reading above
the threshold, is this role the owner, is this count under the reorder point. That is what makes
the scan work — it can decide on the element it is holding and forget everything before it, which
is exactly what lets `next` and `any` stop where they do. Even `min` and `max`, which cannot stop,
score each element on its own and keep only a running best.

That is a property of the predicates written above, not a limit inside the tools. `next`, `any`,
`all`, `min` and `max` never reach into a list themselves; each one takes an iterable and decides on
whatever that iterable hands it, one item at a time. **The unit a predicate gets to see is settled
by what you iterate over, not by which of these functions you call.**

---

## 7. When the answer is "not there"

Every tool in this chapter has a second answer, and it is the one that gets code wrong. `in` says
`False`, `index` raises, `bisect_left` hands back a position nothing occupies, `next` either raises
or returns the default you supplied. Chapter 3, section 4 met the first version of this problem —
`remove` on a value that is not present — and settled it with a single exception. Searching has
more ways to say no, and they are not interchangeable.

### The three conventions

The standard library picks between three, and each is a different bargain.

```python
label = "sensor-07:temp"
settings = {"gain": 2.0}

print(label.find("="))                  # -> -1          a sentinel value
try:
    label.index("=")                    #                an exception
except ValueError as e:
    print(type(e).__name__, e)          # -> ValueError substring not found
try:
    settings["offset"]                  #                and so is a missing key
except KeyError as e:
    print(type(e).__name__, e)          # -> KeyError 'offset'
print(settings.get("offset"))           # -> None        a null result
```

Raising is the loud one. Nothing downstream runs on a bad value, and the traceback points at the
search itself. The price is that every caller who can survive a miss has to write a `try` — and a
`try` is a region, not a line, so it catches whatever else inside it raises the same class:

```python
labels = ["gain", "offset", "trim"]
raw = {"gain": "2.0", "offset": "n/a"}

try:
    i = labels.index("offset")
    print(float(raw[labels[i]]))
except ValueError:
    print("no such label")              # -> no such label
```

`offset` is at index 1; the search succeeded. The `ValueError` came from `float`, and the handler
reported the only failure it was written for. **Wrap the search, not the work that follows it.**

A sentinel is the quiet one. The miss comes back as a value of the same type a hit would produce,
chosen so that no hit could produce it. Execution continues, so the caller has to remember to look.

`None` is the third, and it is a sentinel with a type of its own. `NoneType` shares almost no
operations with the result you wanted, so a forgotten check usually fails a step or two later:

```python
directory = {"ada": 3}
n = directory.get("bob")
try:
    print(n + 1)
except TypeError as e:
    print(type(e).__name__, e)
# -> TypeError unsupported operand type(s) for +: 'NoneType' and 'int'
```

Loud, but *late*: the traceback names the addition, not the lookup that produced the `None`.

You do not get the choice everywhere. The sentinel spelling exists on the text types and nowhere
else:

```python
for t in (str, bytes, list, tuple):
    print(t.__name__, hasattr(t, "find"), hasattr(t, "index"))
# -> str True True
# -> bytes True True
# -> list False True
# -> tuple False True
```

Every sequence has `index`, and it raises on all of them. Search a list and raising is the only
convention handed to you; a sentinel is yours to pick. The next subsection is the pick almost
everyone makes first.

### −1 is a legal index

Write the sentinel convention yourself over a list and the result is a value that reads as a bug
report and behaves as a position:

```python
names = ["ada", "grace", "alan", "edsger"]

def find(seq, target):
    for i, x in enumerate(seq):
        if x == target:
            return i
    return -1

i = find(names, "linus")
print(i)                    # -> -1
print(repr(names[i]))       # -> 'edsger'
names[i] = "linus"
print(names)                # -> ['ada', 'grace', 'alan', 'linus']
```

The search failed, and the failure value read the last element and then overwrote it. No exception,
no warning, and the corrupted list looks entirely plausible. Chapter 1, section 4 introduced
negative indexing as the convenience it is; here it is the mechanism by which a failed search
becomes a successful write. **A sentinel is only a sentinel if it lies outside the range of valid
answers, and −1 is inside the range of valid indices.**

Slicing makes it quieter still, because a slice bound is never checked at all:

```python
label = "sensor-07:temp"
cut = label.find("=")
print(cut, repr(label[:cut]))       # -> -1 'sensor-07:tem'
```

`label[:-1]` is a legal, silent request for everything but the last character. Chapter 1, section 5
covers the clamping that buys that silence. The rule that follows: if you call `find`, compare the
result against −1 on the very next line, and never let the value reach an index or a slice bound.

### `None`, and data that legally contains `None`

`None` is only unambiguous while it cannot appear as a real result. The moment it can, the sentinel
and the answer are the same object:

```python
overrides = {"gain": 2.0, "offset": None}
print(overrides.get("offset"))      # -> None
print(overrides.get("trim"))        # -> None
```

Two different questions, one answer. Both repairs are one line:

```python
overrides = {"gain": 2.0, "offset": None}
_MISSING = object()
print(overrides.get("offset", _MISSING) is _MISSING)   # -> False
print(overrides.get("trim", _MISSING) is _MISSING)     # -> True
print("offset" in overrides, "trim" in overrides)      # -> True False
```

A bare `object()` has no equality beyond identity and no way into the data, so `is` against it
cannot be fooled. **A sentinel you constructed is the only one guaranteed absent from data you did
not construct.**

The related failure is testing the result for truth instead of for the sentinel. A hit that happens
to be falsy then reports itself as a miss:

```python
counts = [5, 0, 7]
first_even = next((c for c in counts if c % 2 == 0), None)
print(first_even)                   # -> 0
print(bool(first_even))             # -> False
print(first_even is not None)       # -> True
```

Indices have the same shape, because index 0 is falsy too. Section 5 built the range-then-equality
guard that turns an insertion point into a membership answer, and had its `index_of` return `-1` for
the miss. That spelling is safe exactly as long as the result is compared and never subscripted.
Returning `None` retires the question, and gives the guard a second job — collapsing every kind of
miss, absent value and empty sequence alike, into one agreed answer:

```python
from bisect import bisect_left

prices = [12, 19, 25, 31]

def found_at(seq, x):
    i = bisect_left(seq, x)
    return i if i < len(seq) and seq[i] == x else None

idx = found_at(prices, 12)
print(idx, bool(idx), idx is not None)          # -> 0 False True
print(found_at(prices, 20), found_at([], 5))    # -> None None
```

`if idx:` would report the cheapest price as absent. `if idx is not None:` is the test.

### Ask first, or apologise afterwards

Two spellings guard a search that may fail: check membership before calling `index`, or call it and
catch the `ValueError`. They have names — *look before you leap*, LBYL, and *easier to ask
forgiveness than permission*, EAFP. The library has settled one of the two questions here: how a
miss is *reported*. `index`, `remove`, `d[key]` and a defaultless `next` all raise rather than
return a flag, which is what makes EAFP available on `index` in the first place — there is an
exception to catch. That is a vote about signalling, not about guarding. A default is not a verdict.
Which guard you write is the separate question, and it is settled by measurement. Chapter 3,
section 4 priced the pair for `remove` on a 20,000-element list and found that checking first buys a
second scan; `index` behaves the same way, and length decides the miss:

```python
import timeit

def per_call(stmt, setup, repeat=25):
    t = timeit.Timer(stmt, setup=setup)
    number, _ = t.autorange()
    number = max(1, number // 50)
    return min(t.repeat(number=number, repeat=repeat)) / number * 1e9

check = "if {v} in nums: nums.index({v})"
catch = "try:\n    nums.index({v})\nexcept ValueError:\n    pass"

for n in (8, 20_000):
    setup = f"nums = list(range({n}))"
    for label, v in (("hit", n // 2), ("miss", -1)):
        print(f"n={n:<6} {label:5}  in+index {per_call(check.format(v=v), setup):10.1f} ns"
              f"   try {per_call(catch.format(v=v), setup):10.1f} ns")
# -> n=8      hit    in+index       58.2 ns   try       32.4 ns
# -> n=8      miss   in+index       47.3 ns   try      116.5 ns
# -> n=20000  hit    in+index   113087.5 ns   try    57812.5 ns
# -> n=20000  miss   in+index   109664.6 ns   try   128816.7 ns
```

On a hit, catching wins at both sizes by the factor you would predict: `in` scans to the match and
`index` scans to it again, so checking first does the work twice. On a miss the ordering reverses,
and by how much depends on length. Raising and catching an exception has a fixed cost that does not
shrink; over eight elements it more than doubles the price of the miss, while over 20,000 it is a
small surcharge on a scan that dominates everything. **Neither spelling is the idiom; the common
case is.** If misses are frequent and the sequence is short, check. If hits are frequent, or the
sequence is long enough that a second scan is real work, catch.

### `get` with a default, and `setdefault`

`get` is the non-raising lookup, and it never writes:

```python
inventory = {"widget": 4, "gasket": 0}
print(inventory.get("widget"), inventory.get("bolt"), inventory.get("bolt", 0))  # -> 4 None 0
print(inventory)                        # -> {'widget': 4, 'gasket': 0}
print(bool(inventory.get("gasket")), bool(inventory.get("bolt")))   # -> False False
```

The last line is the falsy trap again: a stocked-out part and a part you do not carry are different
facts, and truth-testing the lookup erases the difference.

`setdefault` is the writing sibling: it returns the existing value if the key is there and inserts
the default if it is not, making "look it up, creating it if needed" one expression:

```python
palette = {}
palette.setdefault("red", []).append((255, 0, 0))
palette.setdefault("red", []).append((250, 10, 10))
print(palette)                          # -> {'red': [(255, 0, 0), (250, 10, 10)]}
```

Its cost is that the default is an ordinary argument, so it is built on every call, hit or miss:

```python
calls = 0
def fresh():
    global calls
    calls += 1
    return []

palette = {"red": [(255, 0, 0)]}
palette.setdefault("red", fresh())
print(calls)                            # -> 1
palette.setdefault("blue", fresh())
print(calls)                            # -> 2
```

The first call constructed a list and discarded it unused. An empty list is cheap enough to ignore;
a default that opens a file or runs a query is not. The same applies to `get`'s second argument.

### The empty sequence is the search that always misses

Section 2 made the point that absence needs no length guard in Python. That is true, and it is not
the same as the tools agreeing about what an empty container means:

```python
from bisect import bisect_left

empty = []
print(3 in empty)                       # -> False
print(empty.count(3))                   # -> 0
print(bisect_left(empty, 3))            # -> 0
print(next(iter(empty), "none"))        # -> none
print(max(empty, default=None))         # -> None
print(any(empty), all(empty))           # -> False True
for name, call in (("index", lambda: empty.index(3)), ("min", lambda: min(empty))):
    try:
        call()
    except ValueError as e:
        print(name, type(e).__name__, e)
# -> index ValueError list.index(x): x not in list
# -> min ValueError min() iterable argument is empty
```

Two deserve marking. `bisect_left` returns `0`, a correct insertion point and an invalid index at
once — the confusion the guard above exists to prevent, and the one case where its range check
does all the work. And section 6's pair lands here as a decision: **`all([])` is `True` and
`any([])` is `False`**, so an accidental emptiness is accepted by one validation and rejected by the
other. Write the empty case down and test it, whichever answer you meant.

Every one of those searches got an answer, and every answer was right. What the tools cannot
survive is the sequence *not being there at all* — a `nums` that is `None` because the caller had
nothing to hand you. There is then nothing to scan, and none of them fall back to "absent":

```python
missing = None
for name, call in (("in", lambda: 3 in missing),
                   ("len", lambda: len(missing)),
                   ("next", lambda: next(iter(missing), "none"))):
    try:
        print(name, "->", call())
    except TypeError as e:
        print(name, type(e).__name__, e)
# -> in TypeError argument of type 'NoneType' is not a container or iterable
# -> len TypeError object of type 'NoneType' has no len()
# -> next TypeError 'NoneType' object is not iterable
```

The default in `next(iter(missing), "none")` never gets its chance: `iter` raises before there is a
search to come up empty. **An empty sequence answers every search correctly and needs no guard; an
absent sequence answers nothing, and is the one case `if nums is None` exists for.** The rule from
section 2 survives intact — no *length* guard is needed, at any size — and this is the one guard
that is about the container itself rather than about how much is in it.

Which is why `if not nums:` is the wrong spelling whenever the two cases mean different things:

```python
def summarise(nums):
    if nums is None:
        return "no readings taken"
    return f"{len(nums)} readings, 21 seen: {21 in nums}"

print(summarise([]))            # -> 0 readings, 21 seen: False
print(summarise([18, 21]))      # -> 2 readings, 21 seen: True
print(summarise(None))          # -> no readings taken
print(not [], not None)         # -> True True
```

`not []` and `not None` are both `True`, so a single truth test folds "you measured nothing" into
"you never measured" and reports one of them as the other. It is the falsy trap from earlier in
this section moved up a level: applied to the container instead of to the result.

### Decide before you write the search

The tools are fine. The bugs come from deciding what a miss means after the search is already
written, and from a miss that can be mistaken for a hit. Three questions settle it in advance.

*Can the caller do anything sensible without a result?* If not, raise — `index`, `remove`,
`d[key]` and `min` all take that position, and a `ValueError` or `KeyError` at the point of failure
is worth more than a clean-looking value that corrupts something later.

*If it returns a value instead, is that value impossible as a success?* `None` qualifies only while
`None` cannot appear in the data; `-1` never qualifies for an index. When neither holds, a private
`object()` is always available, as is returning two things, `(True, value)` and `(False, None)`, so
the answer and the verdict cannot be confused.

*How is the caller made to check?* A sentinel that is easy to ignore will be ignored. Test it with
`is` against the exact sentinel, never with `if result:`, and keep the check adjacent to the search
so no expression can carry a miss away from the line that produced it.

---

## 8. Drills

Ten snippets, and the procedure from chapters 2 and 3 unchanged: predict in writing, then run, then
read the key — in that order and no other. A prediction has to be exact, down to the returned
integer, the exception type with its message text, and the order the lines come out in, because
"it finds it" and "it raises something" cannot be wrong in the way that teaches you anything. Every
output in the key was produced by running the snippet on CPython 3.14.4. Nothing here is timed;
this chapter's cost claims and the timings behind them live in the sections before it, and what you
are being tested on is what each search *returns* when it succeeds and what it does when it fails.

### The drills

**Drill 1.**

```python
prices = [199, 249, 99, 349]
print(199 in prices)                     # ?
print(200 in prices)                     # ?

lookup = set(prices)
print(199 in lookup)                     # ?
print(200 in lookup)                     # ?

by_sku = {"bolt": 199, "nut": 249}
print("bolt" in by_sku)                  # ?
print(199 in by_sku)                     # ?

label = "washer-42"
print("ash" in label)                    # ?
print("ash" in ["washer-42", "bolt"])    # ?
print("washer-42" in ["washer-42", "bolt"])   # ?
```

**Drill 2.**

```python
temps = [12, 15, 19, 15]
print(temps.index(15))                   # ?

try:
    temps.index(99)
except ValueError as e:
    print(type(e).__name__, e)           # ?

label = "sensor-15"
print(label.find("15"))                  # ?
print(label.find("99"))                  # ?

try:
    label.index("99")
except ValueError as e:
    print(type(e).__name__, e)           # ?

print(temps.count(15), temps.count(99), [].count(99))   # ?
```

**Drill 3.**

```python
def position_of(readings, target):
    for i, r in enumerate(readings):
        if r == target:
            return i
    return -1


readings = [21, 19, 23, 20]
print(position_of(readings, 23))         # ?
print(position_of(readings, 99))         # ?

i = position_of(readings, 99)
print(readings[i])                       # ?

print("found" if position_of(readings, 99) else "not found")   # ?
print("found" if position_of(readings, 21) else "not found")   # ?

j = position_of(readings, 20)
print(readings[j], j == len(readings) - 1)    # ?
```

**Drill 4.**

```python
temps = [12, 15, 19, 15, 12, 15]
print(temps.index(15))                   # ?
print(temps.index(15, 2))                # ?
print(temps.index(15, 2, 4))             # ?

try:
    temps.index(15, 2, 3)
except ValueError as e:
    print(type(e).__name__, e)           # ?

print(temps.index(15, -2))               # ?

try:
    temps.index(12, 99)
except ValueError as e:
    print(type(e).__name__, e)           # ?

print(temps.count(15), temps[2:4].index(15))   # ?
```

**Drill 5.**

```python
prices = [199, 249, 99, 349]

print(next(i for i, p in enumerate(prices) if p > 200))         # ?
print(next((i for i, p in enumerate(prices) if p > 400), -1))   # ?

try:
    next(i for i, p in enumerate(prices) if p > 400)
except StopIteration as e:
    print(type(e).__name__, repr(str(e)))    # ?

print(next((p for p in prices if p > 400), None))    # ?

gen = (p for p in prices if p > 200)
print(next(gen), next(gen))              # ?
print(next(gen, "exhausted"))            # ?

try:
    compile("next(p for p in prices if p > 400, -1)", "<drill>", "exec")
except SyntaxError as e:
    print(type(e).__name__, e.msg)       # ?
```

**Drill 6.** Predict the printed lines in order, including the ones `log` produces.

```python
def log(x):
    print("checked", x)
    return x > 20


readings = [21, 19, 23]
print(any(log(r) for r in readings))     # ?
print(all(log(r) for r in readings))     # ?

print(any([]), all([]))                  # ?
print(any(r > 99 for r in []), all(r > 99 for r in []))   # ?

print(any([0, "", None]), all(["ok", 3.0, [0]]))          # ?

prices = [199, 249, 99, 349]
print(any(p > 200 for p in prices), next((p for p in prices if p > 200), None))   # ?
```

**Drill 7.**

```python
from bisect import bisect_left, bisect_right

temps = [12, 15, 15, 15, 19]
print(bisect_left(temps, 15), bisect_right(temps, 15))    # ?
print(bisect_left(temps, 16), bisect_right(temps, 16))    # ?
print(bisect_left(temps, 0), bisect_right(temps, 99))     # ?
print(bisect_right(temps, 15) - bisect_left(temps, 15))   # ?

i = bisect_left(temps, 15)
print(i, i < len(temps) and temps[i] == 15)               # ?

j = bisect_left(temps, 16)
print(j, j < len(temps) and temps[j] == 16)               # ?

k = bisect_left(temps, 99)
print(k, k < len(temps))                                  # ?
```

**Drill 8.**

```python
from bisect import bisect_left

prices = [349, 99, 199, 249]
print(349 in prices, prices.index(349))       # ?

i = bisect_left(prices, 349)
print(i, i < len(prices))                     # ?

for target in (99, 199, 249, 349):
    i = bisect_left(prices, target)
    found = i < len(prices) and prices[i] == target
    print(target, i, found, target in prices)    # ?

ordered = sorted(prices)
print(ordered)                                # ?
j = bisect_left(ordered, 349)
print(j, ordered[j] == 349)                   # ?
print(prices)                                 # ?
```

**Drill 9.**

```python
names = ["ana", "bo", "cy"]
print("bo" in names)                     # ?
lookup = set(names)
print("bo" in lookup)                    # ?

groups = [["ana", "bo"], ["cy"]]
print(["cy"] in groups)                  # ?

try:
    set(groups)
except TypeError as e:
    print(type(e).__name__, e)           # ?

try:
    print(["cy"] in lookup)
except TypeError as e:
    print(type(e).__name__, e)           # ?

pairs = {("ana", "bo"), ("cy", "dee")}
print(("cy", "dee") in pairs)            # ?
print(1 in {1.0, 2}, len({1, 1.0}), True in {1})   # ?
```

**Drill 10.**

```python
stock = {"bolt": 40, "nut": 12}
print(stock["bolt"])                     # ?

try:
    stock["washer"]
except KeyError as e:
    print(type(e).__name__, e)           # ?

print(stock.get("washer"))               # ?
print(stock.get("washer", 0))            # ?
print(stock.get("bolt", 0))              # ?
print("washer" in stock, len(stock))     # ?

counts = {"bolt": 0, "nut": 12}
print(counts.get("bolt") or "missing")   # ?
print(counts.get("washer") or "missing")  # ?
print(counts.get("bolt", "missing"))     # ?
print(counts.get("bolt") is None, counts.get("washer") is None)   # ?
```

### The answer key

**1.** `True` / `False` / `True` / `False` / `True` / `False` / `True` / `False` / `True`. The
`in` operator asks each container the question that container is built to answer: a list compares
against every element until one matches, a set hashes the value and looks in one place, a dict
answers about its *keys*, so `199 in by_sku` is `False` even though 199 is a value in it, and a
string answers about substrings — which is why `"ash"` is in `"washer-42"` but is not an element
of a list containing it. **The spelling is identical and the work behind it is not**, which is the
whole of sections 2 and 4. (Sections 2 and 4; chapter 1 sections 8 and 10.)

**2.** `1` / `ValueError list.index(x): x not in list` / `7` / `-1` /
`ValueError substring not found` / `2 0 0`. `index` returns the position of the *first* match and
raises when there is none; `count` returns 0 for an absent value and never raises, so it answers
presence without a guard. `str` carries both conventions side by side: `find` reports absence as
`-1` and `index` raises on the same input, on the same object. **A sentinel and an exception are
two answers to one question, and only the exception cannot be mistaken for a result.** The
`ValueError` is the same shape chapter 3 section 4 met from `remove`. (Sections 2 and 7; chapter 3
section 4.)

**3.** `2` / `-1` / `20` / `found` / `not found` / `20 True`. The scan returns at the first match,
so absent values fall out of the loop to the `return -1`. Both failures follow from that sentinel:
`readings[-1]` is a legal index that quietly hands back the last element, so the "not found" answer
reads as a successful lookup of 20 — the value a genuine hit at the last position also returns —
and `-1` is truthy while a genuine hit at position 0 is falsy, so the truth test gets both cases
exactly backwards. **Python indexes from the end with `-1`, which makes `-1` the one integer a
position-returning search must never use to mean nothing.** Compare `None`, which is neither an
index nor truthy. (Sections 1, 2 and 7.)

**4.** `1` / `3` / `3` / `ValueError list.index(x): x not in list` / `5` /
`ValueError list.index(x): x not in list` / `3 1`. `index(x, start, stop)` searches the half-open
window `[start, stop)`, so `(15, 2, 4)` reaches position 3 and `(15, 2, 3)` looks only at position
2; a negative `start` counts back from the end, and a `start` past the end selects an empty window
that matches nothing rather than raising an `IndexError`. **The bounds are clamped like a slice's,
and the failure is still the value-not-found `ValueError`.** The last line is the reason to use the
window instead of slicing: `temps[2:4]` copies, and `.index` on the copy returns 1, a position in
the copy that is not a position in `temps`. (Section 2; chapter 1 sections 5 and 8.)

**5.** `1` / `-1` / `StopIteration ''` / `None` / `249 349` / `exhausted` /
`SyntaxError Generator expression must be parenthesized`. `next` pulls one value from the
generator, which stops at the first element satisfying the condition, so nothing past it is
examined. With no second argument, exhaustion is `StopIteration`, carrying an empty message, which
is why an accidental bare `next` fails uninformatively; with a default, exhaustion returns that
default and the search reads as an expression. The generator is a live cursor, so successive
`next` calls resume where the last one stopped and then report exhaustion. **The parentheses are
mandatory as soon as there is a default**, because a bare generator expression is only allowed as a
sole argument. (Sections 6 and 7.)

**6.** `checked 21` / `True` / `checked 21` / `checked 19` / `False` / `False True` /
`False True` / `False True` / `True 249`. `any` stops at the first truthy result and `all` at the
first falsy one, which the `log` lines make visible: `any` evaluated one element, `all` evaluated
two. On an empty sequence `any` is `False` and `all` is `True` — `all` is asserting that no
counterexample exists, and an empty sequence has none — and that holds for an empty list and for a
generator that yields nothing. Both test truthiness rather than equality, so `0`, `""` and `None`
are all false while `"ok"`, `3.0` and `[0]` are all true. **`any` tells you whether something
matched and `next` tells you what matched**, which is the choice section 6 turns on. (Section 6.)

**7.** `1 4` / `4 4` / `0 5` / `3` / `1 True` / `4 False` / `5 False`. On a run of equal values
`bisect_left` returns the position before the run and `bisect_right` the position after it, so the
two coincide exactly when the value is absent (`16` gives `4` from both), and their difference is
the length of the run, here 3. That is the test: **`bisect_left` always returns a valid insertion
point, never a verdict, so a search is only complete once you check that the position is in range
and that the element sitting there is the one you wanted.** Skip either half and a value larger
than everything returns `len(temps)`, which is not a readable index. Chapter 2 section 6 used these
positions to insert; here you use the same number to decide whether to look. (Section 5; chapter 2
section 6.)

**8.** `True 0` / `4 False` / `99 0 False True` / `199 2 True True` / `249 3 True True` /
`349 4 False True` / `[99, 199, 249, 349]` / `3 True` / `[349, 99, 199, 249]`. Every value in the
loop is present, and the confirmed bisect reports two of the four as absent. Halving assumes that
nothing left of a probe is larger than it and nothing right of it is smaller; on an unsorted list
that assumption is false and the halves it discards may hold the target. **The failure is silent —
no exception, no warning, correct answers on some inputs and wrong ones on others**, which is worse
than an error and is the reason "sorted" is a precondition you check rather than hope for. Search
the `sorted` copy and 349 is found at 3, with the original list left in its own order, so a
read-only input survives. (Sections 5 and 7; chapter 1 section 8.)

**9.** `True` / `True` / `True` /
`TypeError cannot use 'list' as a set element (unhashable type: 'list')` / the same `TypeError` /
`True` / `True 1 True`. A list compares elements with `==`, so a list of lists can hold and find
`["cy"]`. A set locates a value by its hash, and a list has no hash because its contents can
change, so it can be neither stored in a set nor looked up in one: the membership test raises even
though the set is not empty and nothing would have had to change. **The speed comes from hashing,
and hashing is what the element type has to support.** Swap in the tuple and it works. Hash lookup
finishes with `==`, so `1`, `1.0` and `True` are one key: `{1, 1.0}` has length 1. (Section 4;
chapter 1 section 10.)

**10.** `40` / `KeyError 'washer'` / `None` / `0` / `40` / `False 2` / `missing` / `missing` / `0`
/ `False True`. Indexing a dict raises `KeyError` on a missing key; `.get` returns `None` instead,
or the default you supply, and unlike `setdefault` it never writes the default back, so
`len(stock)` is still 2 and `"washer" in stock` is still `False` after two lookups that missed.
The last block is the trap: `counts.get("bolt")` returns the stored `0`, which is falsy, so
`or "missing"` reports a present key as absent, while the default argument distinguishes them
correctly. **`or` tests truthiness and a lookup tests presence, and a legitimate
falsy value is exactly where the two come apart.** (Sections 4 and 7; chapter 1 section 10.)

### The readiness checklist

Chapter 1's scoring rule still holds: explanation rather than recognition, out loud, in under a
minute. Each statement names the section that carries it and the drill that tests it.

You should be able to explain, without looking it up, why:

1. `x in nums` and `x in lookup` are the same operator and not the same amount of work, and
   what has to be true of `x` before the second one is even legal. (Sections 2 and 4; drills 1
   and 9.)
2. `index` raises where `count` returns 0 and `str.find` returns `-1`, and which of those three you
   want when "absent" is an ordinary outcome rather than a bug. (Sections 2 and 7; drill 2.)
3. a search that returns `-1` for "not found" produces a wrong answer twice over in Python — once
   when the result is used as an index, once when it is used as a truth value. (Section 7;
   drill 3.)
4. `nums.index(x, start)` is preferable to `nums[start:].index(x)`, in both what it costs and what
   number it gives back. (Section 2; drill 4.)
5. `next(gen, default)` is a complete search and bare `next(gen)` is a bet, and what the
   parentheses have to do with it. (Sections 6 and 7; drill 5.)
6. `all([])` is `True`, `any([])` is `False`, and neither of them examines every element in the
   general case. (Section 6; drill 6.)
7. `bisect_left` returning `i` is not yet an answer to "is it there", and what the two checks are
   that turn it into one. (Section 5; drill 7.)
8. binary search on unsorted data returns confidently wrong positions without raising anything, and
   what that costs you compared with a linear scan that is merely slower. (Sections 3, 5 and 7;
   drill 8.)
9. `d.get(k)` and `d[k]` differ on a missing key, and why `d.get(k) or fallback` is not a safe
   shorthand for either. (Sections 4 and 7; drill 10.)
