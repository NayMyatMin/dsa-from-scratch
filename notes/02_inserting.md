# Chapter 2 — Inserting Into a List

Chapter 1 settled the format: one contiguous block of pointers, an index that names a place rather
than a value, a length that is stored rather than counted, and a block deliberately bigger than that
length so growth is usually free. A data structure is that format *plus* a contract — what you are
allowed to do to the arrangement, and what each of those things costs. This chapter is the first of
the three that describe the contract, and it takes the half of it that puts values in.

Insertion is the operation the layout is built around, and it is the one whose price swings hardest
on a single argument. The same value, into the same list, by the same call, costs nothing at one
position and moves the entire list at another. This chapter settles which forms of insertion Python
offers, what each of them moves, which of them can change a length and which cannot, what every one
of them costs measured rather than asserted, and the family of wrong answers that appears when a
length changes underneath code that had already recorded it.

It leans on chapter 1 rather than repeating it. Amortized append is chapter 1 section 7, the full
operation cost table is section 8, and aliasing and in-place semantics are section 9; where this
chapter needs one of those it names it and moves on. If you have not read those three, read them
before this — everything here is priced against them.

## How to read this

**Run the code.** Every block is executable exactly as written — there are 93 of them, carrying 239
`# -> value` comments — and every one of those comments is a real observed result rather than an
illustration. Open a session next to this document and paste as you go:

```bash
uv run python
```

Some blocks continue the one before them within a section, reusing a variable set up earlier. Some
deliberately end in an exception and say so on the offending line; those are demonstrations, and the
exception is the point.

**Predict before you run.** Section 8 is eleven drills and an answer key, and it is the honest test
of whether the rest of the chapter landed. The three subjects it goes after hardest — index rules,
what a length change does to code holding a position, and the difference between one shift and many
— are the three that decide correctness rather than style.

**Measurements come from this machine.** Every number was measured on CPython 3.14.4, the
interpreter in this repository's virtual environment, on a 64-bit build. Deterministic values —
object sizes, capacities, printed output — will reproduce exactly for you. Timings will not; they
depend on your hardware and on what else is running. What reproduces is the shape: the ratios, the
orderings, and the way a figure moves when the input doubles. Where a number is a timing, the
surrounding prose says what about it is meant to hold.

**It is shorter than chapter 1.** Just under 20,000 words, about two and a half hours at the pace of
prose you stop and run rather than skim, against chapter 1's six and a quarter. One long sitting or
two; the natural break is the end of section 4, which closes the tour of the forms.

## The sections

| | Section | What it settles | Size |
|---|---|---|---:|
| 1 | [Three operations, and where insertion sits](#1-three-operations-and-where-insertion-sits) | Insert, delete, search, and why position is the subject of all three | 1,700 w · 13 min |
| 2 | [Appending: the end is the cheap end](#2-appending-the-end-is-the-cheap-end) | Every way to grow at the end, and which of them is actually fastest | 2,500 w · 19 min |
| 3 | [insert(i, x): what it actually costs](#3-inserti-x-what-it-actually-costs) | The shift, measured against `i`, and the index rules that clamp | 2,300 w · 18 min |
| 4 | [Splicing: assignment as insertion](#4-splicing-assignment-as-insertion) | Many elements in one shift, and when the length may move | 2,300 w · 18 min |
| 5 | [Writing into a fixed-length list](#5-writing-into-a-fixed-length-list) | The only insertion left when the length cannot change | 2,000 w · 16 min |
| 6 | [Inserting in order](#6-inserting-in-order) | `bisect`, the halving search, and the O(n) it hands off to | 2,600 w · 20 min |
| 7 | [Hazards when the list changes size](#7-hazards-when-the-list-changes-size) | Stale indexes, live iterators, and lists that are not yours | 2,300 w · 18 min |
| 8 | [Drills](#8-drills) | Eleven predictions, an answer key, and a readiness check | 2,900 w · 23 min |

Sections 1 through 5 are the spine and are best read in order: each one is a different answer to the
question of where a value goes, and section 5 is the case where the answer is forced. Section 6 is a
specialised case you can take when you need it — a sorted list that must stay sorted — and nothing
after it depends on having read it. Section 7 is the one to read before you touch code that edits a
list while walking it. Section 8 is the exit exam.

When you finish, the two problems in `arrays101/ch02/` are waiting. Sections 5 and 7 are the two
written with them in mind, and neither of them is a hint: they are the hazards, described so you
recognise the failure when you produce it.

---

## 1. Three operations, and where insertion sits

A list is not merely somewhere to put values. It is somewhere to put values *in a particular
arrangement*, together with a set of operations that maintain that arrangement for you. That pairing
is the whole of what the phrase **data structure** means: a format for the data, plus a contract
about what you can do to it and what each of those things costs. Chapter 1 was about the format —
one contiguous block of pointers, an index that names a place rather than a value, a length that is
stored rather than counted. This chapter and the two after it are about the contract.

### A queue of jobs

Picture the software that runs a render farm. One worker machine processes jobs one at a time, and
the jobs that are waiting sit in order in a list:

```python
queue = ["render-4471", "backup-nightly", "index-rebuild"]
```

Order here is not decoration. Position 0 is the job that runs next, and a job at position 7 has
seven jobs ahead of it. The list is not a bag of jobs; it is a *sequence* of them, and every
operation the scheduler performs has to leave that meaning intact.

Now watch what the scheduler actually has to do over a working day.

**A job is submitted.** Someone hits the button, and a new job joins the back of the queue behind
everything already waiting. This is the ordinary case, and it happens all day.

**An incident job jumps the queue.** Production is down, the fix has to build now, and the job goes
to the front rather than the back — or, in a scheduler with three priority bands, into the middle,
just behind the other urgent work and ahead of everything routine.

**A job is cancelled.** The submitter realises the branch was wrong, or a duplicate got queued
twice, and it has to come out of the middle of the queue without disturbing the relative order of
everything else.

**Somebody asks where their job is.** This is the operation that runs most often by a wide margin.
A submitted job is submitted once and cancelled at most once, but the status page behind it is
refreshed by every engineer waiting on a build, and each refresh asks the same two questions: is
that job still queued at all, and how many jobs are ahead of it.

Insert, delete, search. **Those three are what almost every data structure that has ever been
designed exists to answer, and the differences between structures are differences in what those
three cost.** A structure that makes searching instant while making insertion expensive is a
different tool from one that reverses the trade, and choosing between them is most of what data
structure design is.

### The map, before the detail

Python spells all three on `list`, several ways each. The full cost of each form is the business of
the sections that follow; what matters right now is knowing the vocabulary exists.

| The question | How you ask it | Where it is settled |
|---|---|---|
| **Insertion** — get a value in | `append(x)`, `insert(i, x)`, `extend(other)`, `nums += other`, `nums[i:j] = other`, and plain `nums[i] = x` when the slot already exists | this chapter |
| **Deletion** — get a value out | `remove(x)`, `pop()`, `pop(i)`, `del nums[i]`, `del nums[i:j]`, `clear()` | chapter 3 |
| **Search** — find out whether, and where | `x in nums`, `nums.index(x)`, `nums.count(x)`, and `nums[i]` itself when you already know the index | chapter 4 |

The whole day's work fits in one session:

```python
queue = ["render-4471", "backup-nightly", "index-rebuild"]

queue.append("thumbs-2210")             # a job is submitted; it joins the back
print(queue)
# -> ['render-4471', 'backup-nightly', 'index-rebuild', 'thumbs-2210']

queue.insert(0, "hotfix-9002")          # an incident job jumps the whole queue
print(queue)
# -> ['hotfix-9002', 'render-4471', 'backup-nightly', 'index-rebuild', 'thumbs-2210']

queue.remove("backup-nightly")          # the submitter cancels it
print(queue)
# -> ['hotfix-9002', 'render-4471', 'index-rebuild', 'thumbs-2210']

print("index-rebuild" in queue)         # is that job still waiting?
# -> True
print(queue.index("index-rebuild"))     # how many jobs are ahead of it?
# -> 2

running = queue.pop(0)                  # the worker takes the next job
print(running, queue)
# -> hotfix-9002 ['render-4471', 'index-rebuild', 'thumbs-2210']
```

Six operations, and every one of them is an insertion, a deletion, or a search. Nothing in this
section is difficult; the difficulty is entirely in what those six cost, which the printed output
conceals completely.

### What this chapter settles

This chapter is insertion, in every form Python offers. Section 2 takes appending and the reason the
end of a list is privileged. Section 3 takes `insert(i, x)` and measures what it does to the
elements already sitting at `i` and beyond. Section 4 covers slice assignment, which is insertion
that can place a whole run of values at once and can change the list's length while doing it.
Section 5 handles the case where the length is fixed and must stay fixed, so the only insertion
available is writing over a slot that already exists. Section 6 covers placing a value so that a
sorted list stays sorted. Section 7 collects the ways a list changing size underneath you produces
wrong answers rather than errors. Section 8 is drills: predict the output, then run it.

Chapter 3 does the same for deletion, which turns out to be the same physical work in the opposite
direction. Chapter 4 does search: scanning when you know nothing about the arrangement, and the much
better option available when the values are in sorted order.

### Every one of these is a question about where

Look back at the three operations and notice what they have in common. Insertion has to be told
*where* the new value goes. Deletion has to be told *where* the departing value is. Search is
nothing but the question "where", asked when you do not already know the answer. Position is not
incidental to these operations — position is their subject.

That matters because of the one fact chapter 1 spent its first section establishing: a list keeps
its elements in one unbroken run of slots, and slot `i` holds element `i`. That invariant is what
makes `queue[7]` a jump instead of a walk. It is also a promise the list has to keep after every
edit, and keeping it is not free. Insertion at the end has no promise to repair:

```python
readings = [12, 15, 19, 22]
readings.append(25)
print(readings)
# -> [12, 15, 19, 22, 25]
```

No element had to change index to make room. The new value went to a position past the end, where
nothing was standing in its way. Now do it at the front:

```python
readings.insert(0, 9)
print(readings)
# -> [9, 12, 15, 19, 22, 25]
```

The printed result looks just as tidy, and the work behind it is not comparable at all. There was no
free slot at the front, so making one meant moving 12 from slot 0 to slot 1, 15 from slot 1 to slot
2, and so on for every element in the list. **Inserting at the end disturbs nothing; inserting at
the front moves everything.** The front is not even a special operation — it is `insert(i, x)`
with `i` at 0, simply the position that has the most of the list sitting to its right. That is the
asymmetry this chapter is built around, and on a queue of any real size it is not a subtlety:

```python
import timeit

setup = "queue = [f'job-{i}' for i in range(100_000)]"
back = min(timeit.repeat("queue.append('rush'); queue.pop()",
                         setup=setup, number=10_000, repeat=7))
front = min(timeit.repeat("queue.insert(0, 'rush'); queue.pop(0)",
                          setup=setup, number=10_000, repeat=7))
print(round(back / 10_000 * 1e9), "ns per add-and-remove at the back")
# -> 12 ns per add-and-remove at the back
print(round(front / 10_000 * 1e9), "ns per add-and-remove at the front")
# -> 38690 ns per add-and-remove at the front
print(round(front / back), "x")
# -> 3214 x
```

Same list, same two values in and out, same visible result. Three thousand times the cost, because
of *where*. Repeated runs on this machine put the multiplier between 3000 and 3250; your own figure
will differ, but the ordering and the rough scale will not, and the gap widens as the queue grows
rather than staying put.

Why the end specifically is the cheap end is already answered: chapter 1, section 7. A list holds a
block with room to spare beyond its current length, so appending usually writes into a slot that is
already allocated and does nothing else, and the occasional reallocation is rare enough to average
out to constant cost. That is the over-allocation story, and it is not re-derived here. Neither is
chapter 1 section 8's cost table, which prices the shift itself at a fraction of a nanosecond per
element moved — cheap enough that a linear insertion can sit inside a loop for a long time before
the wall clock ever complains about it. What this chapter is for is what you do with those two
facts: every form of insertion Python offers, which of them moves what, and how to place a value
when the back of the list is not where it belongs.

One further consequence of shifting is worth naming now, even though sections 5 and 7 are where it
gets taken apart. `insert` does the moving for you and loses nothing doing it. When the list is not
allowed to change length, the moving becomes yours, one write at a time — and then every slot you
write into already holds a value, which may be a value you have not read yet. Overwriting it
raises nothing: it leaves a list of exactly the right length holding plausible wrong values, the
kind of failure that survives a spot check. Section 5 takes that hazard apart; section 7 takes apart
the different set of bugs that appear when the length *is* free to change underneath you.

---

## 2. Appending: the end is the cheap end

Every list has one position where making room costs nothing: one past the last element. Writing
there disturbs nothing, because there is nothing after it to disturb. Chapter 1 section 7 worked out
why that survives growth — the block is over-allocated, so most appends drop a pointer into a slot
that already exists, and the rare reallocation averages out. **Appending is the insertion the whole
design is built around: opening a position anywhere but the end costs more, because everything after
it has to move.** Writing to a slot that already exists — `nums[i] = x` — matches an append on
price, but it opens no position at all, and section 5 takes up what that does and does not buy you.

### `append` adds exactly one item

`append` takes one argument and puts it at the end. It changes the list in place and evaluates to
nothing:

```python
readings = [12.5, 13.0]
readings.append(14.25)
print(readings, len(readings))   # -> [12.5, 13.0, 14.25] 3

print(readings.append(15.0))     # -> None
print(readings)                  # -> [12.5, 13.0, 14.25, 15.0]
```

Rebinding a name to that `None` — `queue = queue.append(job)` — throws the list away, and is the
standard way this method is misused.

The other word to take literally is *one*: the length goes up by exactly one whatever you hand it,
including a sequence:

```python
batch = [1, 2]
batch.append([3, 4])
print(batch, len(batch))         # -> [1, 2, [3, 4]] 3
```

### The cost does not depend on how long the list already is

Build lists at four sizes one `append` at a time, with chapter 1 section 11's harness cut down to
what this section needs, and divide by the appends:

```python
import timeit


def bench(stmt, setup="pass", *, number=None, repeat=7):
    t = timeit.Timer(stmt, setup)
    if number is None:
        number, _ = t.autorange()
    return min(t.repeat(repeat=repeat, number=number)) / number


for n in (1_000, 10_000, 100_000, 1_000_000):
    t = bench("out = []\nfor x in src:\n    out.append(x)",
              f"src = list(range({n}))", number=max(1, 2_000_000 // n))
    print(f"n = {n:<10}{t * 1e3:9.3f} ms total   {t / n * 1e9:5.1f} ns per append")

# -> n = 1000          0.008 ms total     8.3 ns per append
# -> n = 10000         0.069 ms total     6.9 ns per append
# -> n = 100000        0.638 ms total     6.4 ns per append
# -> n = 1000000       7.158 ms total     7.2 ns per append
```

Three orders of magnitude, and the per-append figure does not climb — it wanders inside a couple of
nanoseconds and ends below where it started. That is chapter 1 section 7's amortization argument as
a measurement rather than a proof.

The interpreter does more than decline to penalise this operation: it keeps an instruction for it.
Chapter 1 section 11 showed hot instructions rewriting themselves into specialised variants. Warm an
append loop and read the result:

```python
import dis


def build(src):
    out = []
    for x in src:
        out.append(x)


for _ in range(30):
    build(list(range(1000)))          # enough passes to make the loop hot

names = [i.opname for i in dis.get_instructions(build, adaptive=True)]
print([n for n in names if n.startswith(("FOR_ITER", "LOAD_ATTR", "CALL"))])

# -> ['FOR_ITER_LIST', 'LOAD_ATTR_METHOD_NO_DICT', 'CALL_LIST_APPEND']
```

`FOR_ITER_LIST` is the list-iteration specialisation chapter 1 met. The one to look at is
`CALL_LIST_APPEND`: not a general fast path for method calls, but an instruction that exists because
appending to a list in a loop is common enough to deserve its own case in the interpreter.

That inverts a folk optimisation. Hoisting the method out of the loop — `add = out.append`, then
`add(x)` — looks like it saves the attribute lookup, and instead defeats the specialisation: the
`LOAD_ATTR` now runs once, outside the loop, leaving nothing beside the call for the interpreter to
pair it with:

```python
setup = "src = list(range(100_000))"
plain = bench("out = []\nfor x in src:\n    out.append(x)", setup)
hoisted = bench("out = []\nadd = out.append\nfor x in src:\n    add(x)", setup)
print(f"{plain * 1e6:.1f} us   {hoisted * 1e6:.1f} us   {hoisted / plain:.2f}x")

# -> 637.7 us   770.5 us   1.21x
```

The hoisted body ends in `CALL_BUILTIN_O`, the generic path for calling a C function. The penalty
ran 1.21x to 1.24x across reruns and never once favoured the hoist. Write `out.append(x)`.

### `extend` appends every item of an iterable

`extend` is the bulk form: it appends each item its argument yields, in order, and also returns
`None`:

```python
inventory = [3, 5]
inventory.extend([7, 11])
inventory.extend((13, 17))
inventory.extend(range(19, 22))
print(inventory)       # -> [3, 5, 7, 11, 13, 17, 19, 20, 21]
```

Any iterable at all, which is where the hazard lives. A string is a sequence of characters:

```python
names = ["ada"]
names.extend("bob")
print(names)           # -> ['ada', 'b', 'o', 'b']

names = ["ada"]
names.append("bob")
print(names)           # -> ['ada', 'bob']
```

That is the whole difference: one item, or every item of one iterable. A generator works and is
consumed; a dict yields its keys; a non-iterable is an error rather than a single-item append:

```python
taxed = []
taxed.extend(round(p * 1.08, 2) for p in (4.99, 12.50, 30.00))
print(taxed)           # -> [5.39, 13.5, 32.4]

counts = {"red": 2, "green": 9}
keys = []
keys.extend(counts)
print(keys)            # -> ['red', 'green']

try:
    [1].extend(5)
except TypeError as e:
    print(e)           # -> 'int' object is not iterable
```

When you already hold the items, `extend` beats a loop of appends: one call into the C-level routine
replaces an interpreted iteration per item.

```python
for k in (1, 10, 1_000, 100_000):
    setup = f"src = list(range({k}))"
    loop = bench("out = []\nfor x in src:\n    out.append(x)", setup)
    bulk = bench("out = []\nout.extend(src)", setup)
    print(f"k={k:<8}{loop * 1e6:9.3f} us   {bulk * 1e6:9.3f} us   {loop / bulk:5.2f}x")

# -> k=1           0.029 us       0.021 us    1.34x
# -> k=10          0.093 us       0.027 us    3.39x
# -> k=1000        8.051 us       0.919 us    8.76x
# -> k=100000    636.199 us     179.903 us    3.54x
```

Both are linear in `k`. The gap is a constant factor and not a fixed one — small for a handful of
items, widest in the middle, narrower again at a hundred thousand. That last narrowing is the bulk
call slowing down per item rather than the loop speeding up: divide the two right-hand figures by
their `k` and `extend` costs 0.92 ns an item at a thousand against 1.80 ns at a hundred thousand.
No size favours the loop.

### `+=` extends; `+` builds a new list

Chapter 1 section 9 settled the semantics: `+=` runs `extend` on the existing object and rebinds the
name to that same object, so aliases see the change, while `a + b` builds a third list and leaves
both operands alone. That section also prices `out = out + [x]` in an accumulation loop and shows it
is quadratic. None of that changes here.

For insertion the practical point is that `+=` is not merely *like* `extend`, it is the same work at
essentially the same price. Timed against a 100,000-element source, ten runs in shuffled order put
`out += src` between 1.02x and 1.05x of `out.extend(src)` — consistently a shade behind, never far
enough behind to decide anything. Choose between them on reading: `out.extend(src)` says appending,
while `out += src` reads as arithmetic and is easy to misread as building something new.

### Three ways to fill a new list

Three loop shapes produce a list of `n` items, and they are all O(n). Chapter 1 section 3 ranked
them at one size and called the comprehension the winner; the question for an insertion chapter is
whether that ranking is a property of the code or of the size it was measured at. Against the same
source at two sizes, with the bulk form for scale:

```python
cases = {
    "append loop":   "out = []\nfor x in src:\n    out.append(x)",
    "comprehension": "out = [x for x in src]",
    "preallocated":  "out = [None] * len(src)\nfor i in range(len(src)):\n    out[i] = src[i]",
    "extend":        "out = []\nout.extend(src)",
}
for n in (1_000, 100_000):
    times = {k: bench(v, f"src = list(range({n}))") for k, v in cases.items()}
    fastest = min(times.values())
    print(f"--- n = {n}")
    for k, t in sorted(times.items(), key=lambda kv: kv[1]):
        print(f"{k:<16}{t * 1e6:9.2f} us   {t / fastest:5.2f}x")

# -> --- n = 1000
# -> extend               0.92 us    1.00x
# -> comprehension        5.57 us    6.04x
# -> append loop          8.11 us    8.80x
# -> preallocated         9.33 us   10.13x
# -> --- n = 100000
# -> extend             178.52 us    1.00x
# -> comprehension      410.74 us    2.30x
# -> append loop        635.12 us    3.56x
# -> preallocated       995.39 us    5.58x
```

That ranking held on every rerun at both sizes, including with the four cases measured in shuffled
order so that no one of them always ran first. Only the margins moved, and only by a few percent.
**The indexed fill comes last despite doing the fewest allocations of the three loops**, which is
the row worth understanding, because the explanation is not complexity — all three are linear — but
how much interpreted work one item costs. Part of that you can count:

```python
import dis
import textwrap


def by_comp(src):
    out = [x for x in src]


def by_index(src):
    out = [None] * len(src)
    for i in range(len(src)):
        out[i] = src[i]


def by_append(src):
    out = []
    for x in src:
        out.append(x)


def per_item(f):
    names = [i.opname for i in dis.get_instructions(f)]
    return names[names.index("FOR_ITER"):names.index("JUMP_BACKWARD") + 1]


for f in (by_comp, by_index, by_append):
    ops = per_item(f)
    print(textwrap.fill(" ".join(ops), 92,
                        initial_indent=f"{f.__name__:<11}{len(ops)}  ",
                        subsequent_indent=" " * 14))

# -> by_comp    4  FOR_ITER STORE_FAST_LOAD_FAST LIST_APPEND JUMP_BACKWARD
# -> by_index   7  FOR_ITER STORE_FAST LOAD_FAST_BORROW_LOAD_FAST_BORROW BINARY_OP
# ->               LOAD_FAST_BORROW_LOAD_FAST_BORROW STORE_SUBSCR JUMP_BACKWARD
# -> by_append  8  FOR_ITER STORE_FAST LOAD_FAST_BORROW LOAD_ATTR LOAD_FAST_BORROW CALL POP_TOP
# ->               JUMP_BACKWARD
```

Four against seven and eight explains the comprehension and nothing else. `LIST_APPEND` *is* the
append: one instruction reaching the same C-level routine, with no attribute lookup, no call, and no
returned `None` to discard. The other two rows run in the opposite order to their counts, because
instructions are not priced alike — the indexed fill's seven cost more than the append loop's eight.
Time the two loop headers with empty bodies and the ordering is already decided:

```python
for n in (1_000, 100_000):
    s = f"src = list(range({n}))"
    walk_list = bench("for x in src:\n    pass", s)
    walk_range = bench("for i in range(len(src)):\n    pass", s)
    print(f"n = {n:<8}{walk_list * 1e6:8.2f} us   {walk_range * 1e6:8.2f} us"
          f"   {walk_range / walk_list:5.2f}x")

# -> n = 1000        2.21 us       4.61 us    2.08x
# -> n = 100000    224.96 us     532.60 us    2.37x
```

Chapter 1 section 4 already charged the indexed form for the index object and the bounds-checked
subscript it pays on every pass. What the header timing adds is how much of the gap those account
for before a single element moves: walking the list hands back a reference to an object that already
exists, while walking `range` builds a fresh integer at each step. At 100,000 the header alone is
308 µs of the 360 µs by which the indexed fill trails the append loop.

**The comprehension's advantage is a fixed saving of interpreter overhead per item, not a better
algorithm** — so it shrinks the moment each item costs real work:

```python
setup = "celsius = [i * 0.1 for i in range(100_000)]"
work = {
    "append loop":   "out = []\nfor c in celsius:\n    out.append(c * 1.8 + 32)",
    "comprehension": "out = [c * 1.8 + 32 for c in celsius]",
    "preallocated":  ("out = [None] * len(celsius)\n"
                      "for i in range(len(celsius)):\n    out[i] = celsius[i] * 1.8 + 32"),
}
times = {k: bench(v, setup) for k, v in work.items()}
fastest = min(times.values())
for k, t in sorted(times.items(), key=lambda kv: kv[1]):
    print(f"{k:<16}{t * 1e6:9.1f} us   {t / fastest:5.2f}x")

# -> comprehension      1939.0 us    1.00x
# -> append loop        2093.3 us    1.08x
# -> preallocated       2626.4 us    1.35x
```

Same shapes, same length, the same order — and the spread across the three loop shapes has collapsed
from 2.42x to 1.35x, because the arithmetic each item now carries is charged identically to all
three. (2.42x is the same two rows in the table above, preallocated against comprehension; `extend`
is not a loop and has no row here, so its 5.58x is not the figure that collapses.) Prefer the
comprehension where it says what you mean; do not restructure a loop into one expecting a speedup
you can feel.

### Knowing the final size, and not knowing it

When the count is known before you start, hand the whole source over in one operation. Chapter 1
section 7 measured what that buys: `extend` on an empty list, from a source that can report its
length, sizes the block exactly in a single allocation with no slack. `list(src)` and `src.copy()`
do the same. That is a memory property, and it is worth having for its own sake — but it is not why
that row wins the table above by so much. The win is the one already measured at the top of this
section: one C-level call in place of interpreted work per item.

The two come apart cleanly, because the same bulk copy into a list that is *not* empty does the
identical work and loses the exact sizing:

```python
import sys
src = list(range(1_000))

out = []
out.extend(src)
print(len(out), sys.getsizeof(out))     # -> 1000 8056

out = [0]
out.extend(src)
print(len(out), sys.getsizeof(out))     # -> 1001 8088

out = [x for x in src]
print(len(out), sys.getsizeof(out))     # -> 1000 8856
```

Fifty-six bytes of header and eight per slot, so the empty start holds exactly 1000 slots, the
non-empty start rounds up to 1004, and the comprehension's repeated growth leaves it holding 1100
for 1000 items. Timed against each other, though, the two `extend` forms land within a few percent
either way at both 1,000 and 100,000 items, while the comprehension stays multiples behind. Losing
the exact allocation costs almost nothing; running the loop in the interpreter costs everything the
table showed.

Preallocating with `[None] * n` and writing by index is the other known-size form. The table above
prices it last, but that verdict has a size attached to it, and the crossing sits in the low
hundreds:

```python
for n in (100, 250, 500, 1_000, 10_000):
    s = f"src = list(range({n}))"
    grow = bench("out = []\nfor x in src:\n    out.append(x)", s)
    sized = bench("out = [None] * len(src)\nfor i in range(len(src)):\n    out[i] = src[i]", s)
    print(f"n = {n:<8}{grow * 1e6:8.3f} us   {sized * 1e6:8.3f} us   {sized / grow:5.2f}x")

# -> n = 100        0.984 us      0.791 us    0.80x
# -> n = 250        2.228 us      1.804 us    0.81x
# -> n = 500        4.141 us      4.392 us    1.06x
# -> n = 1000       8.093 us      9.322 us    1.15x
# -> n = 10000     68.692 us    100.639 us    1.47x
```

Below a few hundred the single allocation does win, and two small effects line up behind that.
Reaching 100 elements one append at a time takes 11 reallocations; reaching 10,000 takes 47, which
is 0.5 per hundred items instead of 11. And at that scale the loop counter is free — chapter 1
section 2 measured the window of shared integer objects as -5 to 256, and iterating two hundred
values inside that window timed 2.3x cheaper than two hundred outside it. Past a few hundred the
growth steps have thinned out, every index is a freshly built object, and the ratio never comes
back. **Preallocating is not the faster way to build a list at any size where speed is the
question** — chapter 1 section 3's verdict, holding across three orders of magnitude rather than at
the one size that produced it. Preallocate for shape: the position a value lands in stops being
decided by arrival order, which is a different job from accumulation — section 5's.

When the count is not known — you are keeping some inputs and dropping others, so the length is a
property of the data — appending is the natural fit, and the growth rule absorbs the uncertainty for
free. Filtering 100,000 readings with an append loop and a condition took 652.0 µs against 541.0 µs
for the equivalent comprehension, and the ratio stayed between 1.19x and 1.22x over six reruns: the
same fixed overhead per item, nothing more. Reach for the explicit loop when the decision to emit
depends on state a comprehension cannot see — a running total, a flag, anything carried between
iterations. That is a readability boundary, and a fifth is cheap.

---

## 3. insert(i, x): what it actually costs

### What the call does

`nums.insert(i, x)` makes room at position `i` by moving every element from `i` onward one slot to
the right, then writes `x` into the slot that has come free. Length grows by one, and the method
returns `None` because it changes the list you already have rather than building a new one — the
in-place convention from chapter 1, section 9.

```python
labels = ["red", "green", "blue"]
green = labels[1]
print(labels.insert(1, "amber"))   # -> None
print(labels)                      # -> ['red', 'amber', 'green', 'blue']
print(labels[2] is green)          # -> True
print(len(labels))                 # -> 4
```

Nothing was copied and nothing was lost. `"green"` is the same object it always was; only its
address moved one slot along, which is what the shift consists of — a run of 8-byte pointers sliding
over by 8 bytes. The block itself may have to grow to fit the extra pointer, and when it does,
`insert` uses the same over-allocation rule as `append`, measured in chapter 1, section 7:

```python
import sys
appended, inserted = [], []
for i in range(10):
    appended.append(i)
    inserted.insert(0, i)
    print(sys.getsizeof(appended), sys.getsizeof(inserted), end="   ")
# -> 88 88   88 88   88 88   88 88   120 120   120 120   120 120   120 120   184 184   184 184
```

Both containers pass through exactly the same sizes, because where you insert has nothing to do with
how the storage grows.

**`insert` never overwrites an element: the list gets longer instead.** Making room inside a list
whose length must not change is a different operation with a hazard of its own, and it is the
subject of section 5 below.

### The cost is n − i, not n

Every element after the insertion point has to move, so the bill is the length of the tail. Fix the
list at 100,000 elements and walk the insertion point across it. Each measurement pairs the insert
with a `pop()` from the end, which restores the length at negligible cost, and subtracts a baseline
that does the same bookkeeping without the shift — the method chapter 1, section 11 sets out.

```python
import timeit

n = 100_000
setup = f"nums = list(range({n}))"
base = min(timeit.repeat("nums.append(0); nums.pop()", setup=setup, number=1000, repeat=7))
for i in (0, 25_000, 50_000, 75_000, 90_000, 99_000, n):
    stmt = f"nums.insert({i}, 0); nums.pop()"
    pair = min(timeit.repeat(stmt, setup=setup, number=1000, repeat=7))
    ns = (pair - base) * 1e9 / 1000
    moved = n - i
    each = f"{ns / moved:.3f} ns each" if moved else "nothing to move"
    print(f"insert at {i:>6}: {ns:9.1f} ns   {moved:>6} elements   {each}")
# -> insert at      0:   27758.0 ns   100000 elements   0.278 ns each
# -> insert at  25000:   20843.2 ns    75000 elements   0.278 ns each
# -> insert at  50000:   13913.6 ns    50000 elements   0.278 ns each
# -> insert at  75000:    6951.6 ns    25000 elements   0.278 ns each
# -> insert at  90000:    2774.5 ns    10000 elements   0.277 ns each
# -> insert at  99000:     287.5 ns     1000 elements   0.287 ns each
# -> insert at 100000:       8.2 ns        0 elements   nothing to move
```

The right-hand column is the finding. Divide each cost by the number of elements that had to move
and you get the same 0.28 nanoseconds every time, which is chapter 1, section 8's per-element shift
constant arrived at from a different direction. The curve down the middle column is not a property
of `insert`; it is that column multiplied by a tail that keeps getting shorter.

So the parameter that sets the price is not the size of the list. Hold the tail length fixed and
grow the list a hundredfold, and the cost does not move:

```python
import timeit

for n in (20_000, 200_000, 2_000_000):
    setup = f"nums = list(range({n}))"
    base = min(timeit.repeat("nums.append(0); nums.pop()", setup=setup, number=500, repeat=7))
    for label, i in (("i = 10_000", 10_000), ("i = n - 10_000", n - 10_000)):
        stmt = f"nums.insert({i}, 0); nums.pop()"
        pair = min(timeit.repeat(stmt, setup=setup, number=500, repeat=7))
        print(f"n = {n:<9} {label:<15} {(pair - base) * 1e6 / 500:8.2f} us")
# -> n = 20000     i = 10_000          2.78 us
# -> n = 20000     i = n - 10_000      2.77 us
# -> n = 200000    i = 10_000         52.81 us
# -> n = 200000    i = n - 10_000      2.78 us
# -> n = 2000000   i = 10_000        541.77 us
# -> n = 2000000   i = n - 10_000      2.79 us
```

**Ten thousand elements from the end costs 2.78 µs on a list of twenty thousand and 2.78 µs on a
list of two million; index 10,000 costs 2.78 µs on the first and 541.77 µs on the last.** The two
rows are the same call with the same argument type, and only one of them cares how big the list is.
At n = 20,000 they are the same index by construction, and they land 0.01 µs apart, which is the
control: the harness is reading the shift and not the bookkeeping around it. Written as a
complexity, the operation is O(n − i) — linear in the number of elements to the right of the
insertion point, and independent of everything to the left.

Inserting at the front is therefore not a separate operation with a rule of its own. It is this one
at i = 0, the case where the tail is the entire list and the bill is the largest it can be.

The per-element constant is small because none of the shift is interpreted: `insert` is one call,
and the tail moves inside CPython's own implementation with no bytecode executing per slot. Chapter
1's reference cost for reading one element through the interpreter is 5.6 ns; the shift relocates an
element for 0.278 ns, about a twentieth of that. You can move twenty elements in the time it takes
to read one. The figure holds across scale as well as across tails — the three `i = 10_000` rows
above divide out to 0.278, 0.278 and 0.272 ns per element, for tails of 10,000, 190,000 and
1,990,000.

What 0.278 ns is not is the least a pointer can be moved for. It is what this particular call
charges to relocate one slot, and a different insertion form moves the identical tail for roughly
half of that. Section 4 measures that form and divides its constant out against this one. Carry
0.278 ns forward as `insert`'s constant rather than the machine's.

### A small constant is what makes the quadratic hard to see

Build a list of `n` items one at a time, inserting at the front, and compare it against building the
same list by appending.

```python
import time

def build(n, at_front):
    nums = []
    t = time.perf_counter()
    for x in range(n):
        nums.insert(0, x) if at_front else nums.append(x)
    return (time.perf_counter() - t) * 1000

for n in (25_000, 50_000, 100_000, 200_000):
    front = min(build(n, True) for _ in range(3))
    end = min(build(n, False) for _ in range(3))
    print(f"{n:>7}   front {front:9.2f} ms   end {end:6.2f} ms   {front / end:7.0f}x")
# ->   25000   front     86.26 ms   end   0.27 ms       325x
# ->   50000   front    347.34 ms   end   0.51 ms       677x
# ->  100000   front   1399.81 ms   end   1.13 ms      1240x
# ->  200000   front   5570.47 ms   end   2.36 ms      2363x
```

Each doubling of `n` multiplies the front-insertion column by 4.03, 4.03 and 3.98 — quadratic, with
no ambiguity — while the append column doubles. The loop runs `n` times and the `i`-th call shifts
`i` elements, so the total work is n²/2 pointer moves: the same curve chapter 1, section 8 traced by
emptying a list from the front, arrived at here by filling one. The separation between the two
columns is not a constant factor; it doubles every time the input does.

Now the part worth internalising. At n = 1,000 that same front-insertion loop takes 0.16 ms. At
n = 10,000 it takes 14.08 ms. Both are instant to a human, and a test suite built on small inputs
will never say a word. **The constant is 0.28 nanoseconds per element moved, which is exactly why
accidentally quadratic code survives review: it feels fast right up to the size where it stops
being fast, and it gets there suddenly.** Between 25,000 and 200,000 — an eightfold increase — the
cost went from a barely noticeable 86 ms to five and a half seconds.

If the only reason for inserting at the front was to end up with the items in the opposite order to
which they arrived, you do not need front insertion at all. Append them and reverse once: timed
side by side in a single run at n = 200,000, that produced the identical list in 2.02 ms against
5537.12 ms — a factor of about 2,700 — because it pays one linear pass rather than `n` of them.

### An index past the end

`insert` clamps rather than raising, the way slice bounds do. Any index at or beyond the current
length means "at the end", and no `IndexError` is available to this call at all:

```python
readings = [10, 20, 30]
readings.insert(99, 40)
print(readings)              # -> [10, 20, 30, 40]
empty = []
empty.insert(5, 7)
print(empty)                 # -> [7]
```

The clamp is on the value, not on the type: a float index is still a `TypeError`
(`'float' object cannot be interpreted as an integer`), and an index too large to fit the C integer
that holds it is an `OverflowError` (`Python int too large to convert to C ssize_t`), which
`sys.maxsize` reaches but does not exceed.

Clamped to the end means genuinely free of shifting, and the timings say so. Each row below is one
insert paired with one `pop()`, on a list of a million elements:

```python
import timeit

n = 1_000_000
setup = f"nums = list(range({n}))"
for name in ("nums.append(0)", "nums.insert(len(nums), 0)", "nums.insert(10**9, 0)",
             "nums.insert(-1, 0)", "nums.insert(-10**9, 0)", "nums.insert(0, 0)"):
    t = min(timeit.repeat(f"{name}; nums.pop()", setup=setup, number=1000, repeat=7))
    print(f"{name:<28}{t * 1e9 / 1000:12.1f} ns")
# -> nums.append(0)                      11.5 ns
# -> nums.insert(len(nums), 0)           25.4 ns
# -> nums.insert(10**9, 0)               18.7 ns
# -> nums.insert(-1, 0)                  18.8 ns
# -> nums.insert(-10**9, 0)          269847.3 ns
# -> nums.insert(0, 0)                269789.7 ns
```

Four of those six rows sit between 11 and 26 nanoseconds on a million-element list, which is
constant-time territory and nowhere near the linear one. `insert(len(nums), 0)` is the slowest of
the four only because it pays for an interpreted `len` call and the argument push before `insert`
throws the value away — the same effect chapter 1, section 8 found in `nums[len(nums) - 1]`. If you
mean the end, `append` says so in fewer instructions and reads better.

### A negative index

A negative index is resolved once, against the length at the moment of the call, and then treated as
a position like any other. That produces two results people do not expect.

```python
prices = [10, 20, 30]
prices.insert(-1, 25)
print(prices)                # -> [10, 20, 25, 30]
counts = [1, 2, 3]
counts.insert(-99, 0)
print(counts)                # -> [0, 1, 2, 3]
```

`insert(-1, x)` puts `x` *before* the last element, so it is never a way to append — it is the last
position that still shifts something. And an out-of-range negative index clamps to 0 rather than
raising, mirroring the clamp at the other end.

Both facts are visible in the timing table above. `insert(-1, 0)` costs 18.8 ns on a million
elements because exactly one element moves, while `insert(-10**9, 0)` costs 269,847 ns — within
noise of `insert(0, 0)`, because after clamping that is what it is. **A negative index here is a
position, not a direction, and the price follows the position it lands on.**

### When the front is where the work is

If insertions genuinely belong at the front, the fix is a different structure rather than a cleverer
call. `collections.deque` adds and removes at either end in constant time, having no single
contiguous run of storage to shift.

```python
import timeit
from collections import deque

n = 200_000
env = {"d": deque(range(n)), "l": list(range(n))}
for name, stmt in (("deque appendleft", "d.appendleft(0); d.pop()"),
                   ("list  insert(0, x)", "l.insert(0, 0); l.pop()"),
                   ("deque insert middle", "d.insert(100_000, 0); d.pop()"),
                   ("list  insert middle", "l.insert(100_000, 0); l.pop()")):
    t = min(timeit.repeat(stmt, globals=env, number=2000, repeat=7))
    print(f"{name:<22}{t * 1e6 / 2000:11.3f} us")
# -> deque appendleft            0.018 us
# -> list  insert(0, x)         54.014 us
# -> deque insert middle        57.098 us
# -> list  insert middle        28.140 us
```

Thousands of times faster at the front, and twice as slow in the middle. The `appendleft` row sits
at the edge of what that loop count resolves; timed on its own with 100,000 iterations the pair
comes out at 14.2 ns, which puts the front ratio nearer 3,800× than 3,000×. Either figure says the
same thing, because the two rows are not in the same complexity class: the front is constant on a
deque and linear on a list.

**What you trade for that is the middle**, and the trade is not subtle. Chapter 1, section 10 has
the full account; the short version is that reaching an arbitrary position means walking the block
chain, so `d[100_000]` on this container measured 9.563 µs against the list's 0.006 µs, slicing is
refused outright, and each element carries a little more memory. A deque is the right container when
the ends are the whole story and the middle is never reached by index.

If the finished result has to be a list, converting costs one linear pass — `list(d)` measured
541.90 µs at 200,000 elements, against 356.74 µs to copy the equivalent list. That is a real
overhead and worth knowing, and it is still nothing beside a quadratic.

---

## 4. Splicing: assignment as insertion

`insert(i, x)` puts one element in one place. There is a second insertion form that puts any number
of elements in one place, in a single statement, for a single shift. It is the least-used insertion
form and, at size, by far the most useful. Chapter 1 section 5 established what slice assignment
*means*; this section is about what it *costs*.

### An empty target is an insertion point

A slice with `start == stop` selects nothing. Assigning to it therefore removes nothing, and the
right-hand side lands at that position.

```python
temps = [12, 15, 19, 22]
temps[2:2] = [16, 17, 18]
print(temps, len(temps))    # -> [12, 15, 16, 17, 18, 19, 22] 7
```

**Read `nums[i:i] = items` as "insert all of `items` at index `i`", and it becomes the general
insertion statement, of which `insert` is the one-element special case.** The two agree exactly:

```python
prices = [100, 200, 300]
prices.insert(1, 150)
print(prices)               # -> [100, 150, 200, 300]

prices = [100, 200, 300]
prices[1:1] = [150]
print(prices)               # -> [100, 150, 200, 300]
```

The two useful extremes are the ends. `nums[:0] = items` is bulk insertion at the front, and
`nums[len(nums):] = items` is bulk insertion at the back:

```python
names = ['ada', 'bo']
names[:0] = ['zed', 'yan']
print(names)                # -> ['zed', 'yan', 'ada', 'bo']
names[len(names):] = ['cy']
print(names)                # -> ['zed', 'yan', 'ada', 'bo', 'cy']
```

### A non-empty target replaces a run with a run

Widen the target and the assignment removes what it covers before putting the right-hand side in
its place — the semantics chapter 1 section 5 sets out in full. The two counts are unrelated, so
the list's length changes by the difference:

```python
names = ['ada', 'bo', 'cy', 'di']
names[1:3] = ['xu']
print(names, len(names))    # -> ['ada', 'xu', 'di'] 3

names = ['ada', 'bo', 'cy', 'di']
names[1:3] = ['p', 'q', 'r', 's']
print(names, len(names))    # -> ['ada', 'p', 'q', 'r', 's', 'di'] 6
```

That length change is the whole cost story. The cost table in chapter 1 section 8 gives the row as
O(k) when `k == b - a` and O(k + n - b) otherwise, and the gap between the two cases is not subtle.
Replace ten elements of a million-element list with exactly ten and nothing after index 10 moves;
replace them with eleven and every one of the remaining elements slides one slot right:

```python
import time
n = 1_000_000
ten, eleven = list(range(10)), list(range(11))

def once(rhs):
    nums = list(range(n))
    t = time.perf_counter()
    nums[0:10] = rhs
    return (time.perf_counter() - t) * 1e6

print(round(min(once(ten) for _ in range(25)), 2), 'us')      # -> 0.12 us
print(round(min(once(eleven) for _ in range(25)), 1), 'us')   # -> 143.4 us
```

Ten slot overwrites against ten overwrites plus a bulk move of 999,990 pointers. One extra element
on the right-hand side is the difference between a constant-time edit and a linear one.

When the length does change, the cost tracks how much lives to the right of the edit — the same
`n - i` curve section 3 measured for `insert`, over the same tail and moved in bulk at C speed. The
curve is the same; the price per element, as the division below shows, is not:

```python
import time
n = 1_000_000
more = list(range(10))

def once(i):
    nums = list(range(n))
    t = time.perf_counter()
    nums[i:i] = more
    return (time.perf_counter() - t) * 1e6

for i in (0, 250_000, 500_000, 750_000, n):
    best = min(once(i) for _ in range(25))
    print(f'splice at {i:>7}: {best:7.1f} us   ({n - i:>7} elements after it)')
# -> splice at       0:   132.6 us   (1000000 elements after it)
# -> splice at  250000:    99.3 us   ( 750000 elements after it)
# -> splice at  500000:    62.2 us   ( 500000 elements after it)
# -> splice at  750000:    29.6 us   ( 250000 elements after it)
# -> splice at 1000000:     0.2 us   (      0 elements after it)
```

Divide each row by the tail it moved and the splice has a per-element constant of its own: 0.133,
0.132, 0.124 and 0.118 ns down the four rows that move anything, against `insert`'s 0.278 ns from
section 3. That is what section 3 sent you here for — the same shape of bill, `n - i` elements at a
fixed price each, but about half the price for the identical tail. Half is the figure to carry and
not a sharper one, because those two constants were arrived at by different harnesses; timed head to
head in a single one, the splice lands between roughly 0.45x and 0.6x of `insert` depending on size
and run. A real factor, then, and not an order of magnitude — the three-orders-of-magnitude gap
further down this section comes from doing one shift instead of k, never from the shift itself
being cheap.

### Any iterable on the right

The right-hand side is not required to be a list. Anything iterable is consumed into a temporary
sequence and spliced from there, so a `range` or a generator goes in directly:

```python
counts = [4, 7, 2]
counts[1:1] = range(10, 13)
print(counts)               # -> [4, 10, 11, 12, 7, 2]

counts = [4, 7, 2]
counts[1:1] = (x * 2 for x in (5, 6))
print(counts)               # -> [4, 10, 12, 7, 2]
```

A string splices as its characters and a dict as its keys — convenient exactly once, a readability
trap thereafter. Chapter 1 section 5 has both cases and the `TypeError` from a non-iterable
right-hand side.

**"Consumed first" carries a price: a generator on the right saves no memory at all.** It is drained
into a full temporary list before one element is written, and you pay for that list on top of the
room the result itself needs:

```python
import tracemalloc
n = 200_000
src = list(range(n))
for label in ('nums[1:1] = src', 'nums[1:1] = (x for x in src)'):
    nums = list(range(10))
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    if 'x for x' in label:
        nums[1:1] = (x for x in src)
    else:
        nums[1:1] = src
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    print(f'{label:30} {(peak - base) / 1024:8.1f} KiB')
# -> nums[1:1] = src                  1562.6 KiB
# -> nums[1:1] = (x for x in src)     3148.7 KiB
```

The first row is the block the 200,010-element result is built in. The second pays that and very
nearly as much again: the extra 1,586.1 KiB is the temporary list, 200,000 pointers at 8 bytes plus
the spare capacity it collected while being filled. Streaming into a splice is not streaming. If
the elements are already in a list, splice the list.

### A step other than 1 forbids resizing

Only a contiguous target can change the list's length. An extended slice — one whose step is
anything but 1 — names positions scattered through the list, so there is no coherent place for
surplus elements to go and no coherent way to close a gap. The lengths must agree exactly, and the
error names both counts:

```python
temps = [12, 15, 19, 22]
try:
    temps[::2] = [1, 2, 3]
except ValueError as e:
    print(e)     # -> attempt to assign sequence of size 3 to extended slice of size 2
temps[::2] = [1, 2]
print(temps)     # -> [1, 15, 2, 22]
temps[1:3:1] = [7, 7, 7]     # a step of exactly 1 is contiguous, and resizes like any other
print(temps)     # -> [1, 7, 7, 7, 22]
```

An extended-slice assignment is therefore a scatter-write, never an insertion: the one slice form
that cannot change a list's length, and so the one that never shifts anything. Its cost is exactly
the number of positions it names, wherever in the list they sit. On the million-element list above,
writing five elements into `nums[0:10:2]` measured 0.04 µs, against 130.4 µs in the same run for
the eleven-element assignment that resizes.

### The end forms, against their method spellings

`nums[len(nums):] = items` and `nums.extend(items)` do the same thing, for the same asymptotic
cost. Section 2 priced `+=` against `extend` and found them the same work; the splice is the third
spelling of it. Grow an empty list to a million elements in chunks of two hundred:

```python
import time
def grow(mode, total=1_000_000, chunk=200):
    more = list(range(chunk))
    nums = []
    t = time.perf_counter()
    for _ in range(total // chunk):
        if mode == 'extend':
            nums.extend(more)
        else:
            nums[len(nums):] = more
    return (time.perf_counter() - t) * 1000

best = {m: min(grow(m) for _ in range(15)) for m in ('extend', 'splice')}
for m, v in best.items():
    print(f'{m:7} {v:6.1f} ms   {v / best["extend"]:.2f}x')
# -> extend     0.8 ms   1.00x
# -> splice     1.0 ms   1.26x
```

The ordering never changes and the gap stays within a few tens of percent run to run: the same
amortized O(k) work, driven by the same spare-capacity mechanism from chapter 1 section 7, with the
splice paying a little extra for resolving a slice where `extend` just takes an argument. `extend`
also wins on legibility, so write `extend`. The splice spelling at the back is worth knowing only
so you recognise it when you meet it.

The front has no method. There is no `prepend`, and this is where the splice earns its place:

```python
import time
n = 100_000
more = list(range(-50, 0))

def splice():
    nums = list(range(n)); t = time.perf_counter()
    nums[:0] = more
    return (time.perf_counter() - t) * 1e6

def concat():
    nums = list(range(n)); t = time.perf_counter()
    nums = more + nums
    return (time.perf_counter() - t) * 1e6

print(round(min(splice() for _ in range(30)), 1), 'us')   # -> 11.4 us
print(round(min(concat() for _ in range(30)), 1), 'us')   # -> 117.8 us
```

Both are linear, but `more + nums` allocates a whole second block and copies every pointer into it
before rebinding the name, while `nums[:0] = more` moves the existing pointers inside the block the
list already owns. About ten to one here. The two also differ in a way that has nothing to do with
speed: `more + nums` rebinds one name and leaves every other name still pointing at the unchanged
original, where the splice edits the object itself and so is visible through all of them. Chapter 1
section 9 is where that distinction decides correctness.

### One shift instead of k shifts

This is the measurement to keep. Inserting `k` elements at index `i` one call at a time performs
`k` separate tail shifts. Splicing the same `k` elements performs one.

```python
import time
n = 100_000
batch = list(range(-1_000, 0))

def by_splice(i):
    readings = list(range(n))
    t = time.perf_counter()
    readings[i:i] = batch
    return (time.perf_counter() - t) * 1e6, readings

def one_at_a_time(i):
    readings = list(range(n))
    t = time.perf_counter()
    for j, x in enumerate(batch):
        readings.insert(i + j, x)
    return (time.perf_counter() - t) * 1e6, readings

for i in (0, n // 2):
    a = min(by_splice(i)[0] for _ in range(20))
    b = min(one_at_a_time(i)[0] for _ in range(20))
    print(f'i={i:>6}  splice {a:6.1f} us   inserts {b:9.1f} us   ratio {b / a:6.0f}x')
print(by_splice(0)[1] == one_at_a_time(0)[1])
# -> i=     0  splice   11.8 us   inserts   27770.1 us   ratio   2355x
# -> i= 50000  splice    6.4 us   inserts   13912.7 us   ratio   2182x
# -> True
```

Identical results, three orders of magnitude apart. The arithmetic is unremarkable once written
down: the loop moves about `k · (n - i)` pointers and the splice about `n - i`, so the ratio is
roughly `k` — a thousand here, and the measurement lands a little over twice that, the loop also
paying a thousand interpreted method calls.

**Whenever you find yourself calling `insert` inside a loop, you are paying for one shift per
iteration; collect the elements and splice them in one statement instead.**

The rewrite is mechanical. A loop that decides what to insert and inserts it in the same breath
becomes a loop that only decides, followed by one assignment:

```python
urgent = [('hotfix', 9), ('rollback', 7), ('page-oncall', 3)]

queue = ['build', 'lint', 'deploy']
for name, priority in urgent:          # one shift per accepted job
    if priority > 5:
        queue.insert(0, name)
print(queue)     # -> ['rollback', 'hotfix', 'build', 'lint', 'deploy']

queue = ['build', 'lint', 'deploy']
accepted = [name for name, priority in urgent if priority > 5]
queue[:0] = accepted                   # decide first, then one shift for all
print(queue)     # -> ['hotfix', 'rollback', 'build', 'lint', 'deploy']
```

The results differ, and the difference is instructive. Repeated `insert(0, ...)` puts each new
element in front of the previous one, so the accepted jobs come out reversed; the splice keeps them
in the order the comprehension produced, because splicing always preserves the order of the
right-hand side. If you wanted the loop's ordering, splice `accepted[::-1]` — deliberately, rather
than inheriting it from a cost mistake.

### Splicing a list into itself

The right-hand side is fully consumed before any writing begins, so a list can appear on both
sides; chapter 1 section 5 shows the harmless case. The one worth studying is where the target
overlaps the source, because what gets spliced in is the list as it was, not as it becomes:

```python
queue = ['a', 'b', 'c', 'd']
queue[1:3] = queue
print(queue)     # -> ['a', 'a', 'b', 'c', 'd', 'd']
```

The `'b'` and `'c'` that the target covered are gone from positions 1 and 2, yet both reappear,
because the right-hand side was the four-element original. Snapshot semantics, and correct — but
paid for. CPython copies the list before it starts writing, so the operation carries an extra block
of `n` pointers that the equivalent splice from a separate list does not:

```python
import tracemalloc
n = 200_000
for label in ('nums[:0] = nums', 'nums[:0] = other'):
    nums = list(range(n)); other = list(range(n))
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    if label == 'nums[:0] = nums':
        nums[:0] = nums
    else:
        nums[:0] = other
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    print(f'{label:18} peak above start {(peak - base) / 1024:8.1f} KiB')
# -> nums[:0] = nums    peak above start   4687.5 KiB
# -> nums[:0] = other   peak above start   3125.0 KiB
```

Both rows include the block the 400,000-element result is built in. The difference between them is
1,562.5 KiB, and 200,000 pointers at 8 bytes each is 1,562.5 KiB exactly: the extra allocation is
one full copy of the original list, and nothing else. It shows in the clock too — on a
500,000-element list, `nums[:0] = nums` measured between 1.7 and 2 times the cost of
`nums[:0] = other`, across repeated runs.

The hazard is not a wrong result. It is that the copy is nowhere in the source: a statement that
reads as pure rearrangement quietly peaks at an extra full block of memory. If the list is large
enough for that to matter, splice from an explicit `nums.copy()` so the allocation is something you
wrote.

---

## 5. Writing into a fixed-length list

### Two operations that share a word

`nums[i] = v` and `nums.insert(i, v)` are both described as putting a value into a list, and they
differ in exactly the respect that decides whether the code you are about to write is correct.

```python
readings = [18, 21, 19, 24]
same_object = id(readings)

readings[1] = 25
print(readings, len(readings))       # -> [18, 25, 19, 24] 4
print(id(readings) == same_object)   # -> True

readings.insert(1, 25)
print(readings, len(readings))       # -> [18, 25, 25, 19, 24] 5
print(id(readings) == same_object)   # -> True
```

Both mutate in place, and both leave you holding the same object, so both are visible through every
other name bound to it. The difference you can see from outside is the length. **`nums[i] = v`
replaces the object at a position that already exists, and `nums.insert(i, v)` brings a position
into existence that did not.** Writing overwrites; insertion grows.

That difference reads off as a length delta, and the forms are worth seeing next to each other:

```python
nums = [10, 20, 30, 40]
nums[1] = 99
print(len(nums), nums)         # -> 4 [10, 99, 30, 40]

nums = [10, 20, 30, 40]
nums[1:3] = [98, 99]
print(len(nums), nums)         # -> 4 [10, 98, 99, 40]

nums = [10, 20, 30, 40]
nums[1:3] = [98]
print(len(nums), nums)         # -> 3 [10, 98, 40]

nums = [10, 20, 30, 40]
nums.insert(1, 99)
print(len(nums), nums)         # -> 5 [10, 99, 20, 30, 40]

nums = [10, 20, 30, 40]
nums[1:1] = [99]
print(len(nums), nums)         # -> 5 [10, 99, 20, 30, 40]
```

The first two rows hold the length still; the rest move it. Look at what separates the second row
from the third. A slice assignment preserves the length only when the replacement holds exactly as
many items as the slice it replaces — the equal-length case from section 4, which is slot
overwriting with a wider brush and no shifting at all. The moment the counts differ, the tail slides
to fit and the length goes with it. And the last row is `insert` spelled as a slice: an empty slice
replaced by one item is a position created, carrying the O(n − i) shift section 3 costed out.

So there is one length-preserving family here — indexed assignment, and the equal-length splice
built out of it. Everything else in this chapter changes the count.

### The length is part of what you were handed

When a list arrives from somewhere else, its length is not yours to adjust. The caller allocated
those positions, holds a name bound to that object, and will read it back when you return:

```python
def apply_discount(prices, pct):
    for i in range(len(prices)):
        prices[i] = round(prices[i] * (100 - pct) / 100, 2)

shelf = [340.0, 125.0, 999.0, 60.0]
before = (len(shelf), id(shelf))

apply_discount(shelf, 10)
print(shelf)                              # -> [306.0, 112.5, 899.1, 54.0]
print((len(shelf), id(shelf)) == before)   # -> True
```

Every element was replaced and nothing was created or destroyed: four positions in, four positions
out, same object throughout. `range(len(prices))` is the right spelling because it derives the
index set from the length instead of assuming one — the loop cannot walk off an end it computed
itself. Chapter 1 section 9 has the rest of this story: why `prices = [...]` inside the function
would have changed nothing the caller can see, and why `prices[:] = [...]` would have been visible
but is not length-safe unless the right-hand side happens to be the same size.

A length-preserving write also asks nothing of the allocator, because it touches nothing but the
slot you name. The block is never reallocated, so the capacity does not move either:

```python
import sys

def capacity(lst):
    return (sys.getsizeof(lst) - sys.getsizeof([])) // 8

prices = list(range(1000))
print(len(prices), capacity(prices))   # -> 1000 1000

for i in range(len(prices)):
    prices[i] = prices[i] * 2
print(len(prices), capacity(prices))   # -> 1000 1000

prices.insert(0, 0)
print(len(prices), capacity(prices))   # -> 1001 1132

try:
    prices[1001] = 7                   # a slot the block owns and the list does not
except IndexError as e:
    print(e)                           # -> list assignment index out of range
print(len(prices), capacity(prices))   # -> 1001 1132
```

A thousand writes and the allocation is byte for byte what it was. One insertion and the list asks
for a bigger block — 1132 slots for 1001 items, the over-allocation from chapter 1 section 7. Those
131 spare slots are not 131 spare positions: index 1001 sits inside the block the list just took
and is still out of range, reading it fails the same way, and the refused write left both numbers
where they were. **`len()` is the count of positions you can index, and the room beyond it is a
fact about memory that only `getsizeof` can see.** Chapter 1 section 7 works through why the bounds
check answers that way; what it means here is that a fixed-length list is fixed at its length, and
no amount of capacity behind it gives you a position to write into. Per write, the cost is flat as
the list grows:

```python
import timeit

for n in (1_000, 100_000, 1_000_000):
    setup = f"nums = [0] * {n}\nr = range({n})"
    t = min(timeit.repeat("for i in r: nums[i] = 1", setup=setup, number=20, repeat=7)) / 20
    print(f"{n:>9} {t / n * 1e9:5.2f} ns per write")
# ->      1000  6.91 ns per write
# ->    100000  7.78 ns per write
# ->   1000000  7.90 ns per write
```

Timings shift from run to run; the shape is the claim, and the shape is a flat line. Over three
orders of magnitude the per-write cost barely moves — repeated runs put the million-element pass
around fifteen percent dearer per write than the thousand-element one, and that margin is the memory
system, not extra work. Rewriting every slot is linear in the length, with a constant that does not
grow with it: one pass, no reallocation, no shifting.

### Sized for the answer, not yet filled with it

The pattern this chapter's problems are built on is a list that already has all the positions its
final contents need, but not yet the contents. You get one by preallocating — `[None] * n`,
`[0] * n` — or by being handed one.

Chapter 1 section 4 settled what such a list contains: a placeholder-filled list is genuinely full,
reading a position you have not written yet hands you the placeholder rather than signalling
absence, and no slot can be in any state other than "holds this object". "Not yet meaningful" is
therefore not a property the list carries. It is a value you chose and a meaning you assigned to it.
Chapter 1 section 7 drew the consequence: once a list is longer than the data inside it, `len()`
stops reporting occupancy and the number of meaningful positions becomes a second number you
maintain.

A fixed-length input creates that situation by construction, and it puts two things on you that a
buffer you filled yourself does not.

The first is that **the count is the only record of where your data ends, so it has to move whenever
the data does.** Nothing in the list will move it for you, and nothing will complain if you forget:

```python
def record(buf, count, value):
    buf[count] = value
    return count + 1          # the new count has to travel back out with it

log = [0] * 6                 # six positions, none of them meaningful yet
count = 0

count = record(log, count, 18)
count = record(log, count, 21)
print(log, count)             # -> [18, 21, 0, 0, 0, 0] 2

record(log, count, 24)        # the returned count is dropped on the floor
record(log, count, 27)        # so this lands on top of the 24
print(log, count)             # -> [18, 21, 27, 0, 0, 0] 2
```

The 24 was written and then destroyed by the next write, because both writes were told the same
position was the free one. The length never changed, every value present is plausible, and one
entry is simply gone.

The second is that **the filler was somebody else's decision, and it may be a value you cannot tell
apart from data.**

```python
temps = [3, 0, 7, 12, 0, 0, 0, 0]   # eight positions; the first four are readings, in Celsius
count = 4

print(len(temps), count)                       # -> 8 4
print(temps[:count])                           # -> [3, 0, 7, 12]
print(sum(1 for t in temps if t != 0))         # -> 3
```

The last line is the trap in one expression. Four readings are present and it reports three, because
one of them is genuinely 0 °C and 0 is also what the reserved positions hold. No inspection of the
list can separate the reading from the filler; they are the same object. This is why a fixed-length
buffer travels with its count instead of surrendering it on demand: the count is information the
list does not contain. Recovering it by scanning costs a pass and, as above, can simply be wrong.

So derive your bounds from the count, not from `len()` — `range(count)` is the data,
`range(len(temps))` is the buffer. When the filler is yours to choose, choose one that cannot be
mistaken for an answer; chapter 1 section 4 makes that case in full.

### Shifting overwrites what you have not read

`insert` shifts a whole tail one position along and never loses an element doing it, and it can
afford that because it is not working inside a fixed length. The list comes out one longer than it
went in and everything that was in it is still in it: the position it needed was created rather
than taken from something that was using it.

A fixed length denies you that. Every position already holds something, so every write lands on a
value, and the only question is whether that value had already done its job. Take five sensor
readings and try to move each one position along, so that each position ends up holding what its
neighbour held:

```python
slots = [11, 12, 13, 14, 15]

for i in range(1, len(slots)):
    slots[i] = slots[i - 1]
    print(i, slots)
# -> 1 [11, 11, 13, 14, 15]
# -> 2 [11, 11, 11, 14, 15]
# -> 3 [11, 11, 11, 11, 15]
# -> 4 [11, 11, 11, 11, 11]
```

Watch position 1 on the first pass. Writing 11 there destroyed the 12, and the 12 was what the next
pass needed to read. So the next pass copies 11 again, and the one after that, and by the end a
single reading has been smeared across the whole list. Four of the five values no longer exist
anywhere in the process:

```python
original = [11, 12, 13, 14, 15]
slots = original.copy()
for i in range(1, len(slots)):
    slots[i] = slots[i - 1]

print(len(slots) == len(original))           # -> True
print(len(set(original)), len(set(slots)))   # -> 5 1
print(sum(original), sum(slots))             # -> 65 55
```

The length is perfect. The contract on the object was honoured exactly. And the data is gone, with
no exception raised, no warning, and nothing in the result that announces itself as wrong — a list
of five plausible readings that happens to be four-fifths fabrication. This is the failure mode to
fear, because a length check will not catch it and a spot check of position 0 will not either.

**In a fixed-length list every write destroys whatever occupied that position, so a shift is only
correct if it never overwrites a value it has not already read.** Stated as a working rule: read
what you want to keep before you overwrite where it lives. The loop above breaks that rule on its
very first iteration, and every iteration after it is operating on wreckage.

That is where this section stops, deliberately. There is a way to move values around inside a
fixed-length list without losing one of them, and finding it is the work the two problems in this
chapter are asking for — both hand you a list whose length must not change and whose destination
positions are also its source positions. Section 7 returns to the hazards that appear when the list
*is* allowed to change size, which are a different set entirely.

---

## 6. Inserting in order

Every insertion up to here let you name the position: `append` at the end, `insert` at an index you
chose, a slice at bounds you wrote. There is a common situation where you do not get to choose: the
list is held in sorted order, and must still be in sorted order once the new value is in. The
position is no longer yours to pick — it is a function of the value.

That splits the work into two questions with very different price tags. *Where does it go* is
answered by looking at the values. *Getting it in there* is the machinery of sections 2 through 4,
unchanged. The whole point of this section is that those two prices are not comparable, and the
cheap half gets all the attention.

### Finding the position by halving

Sorted order is information, and the standard library has a module that spends it. `bisect` does not
scan; it compares against the middle element, learns which half the value belongs in, discards the
other half, and repeats.

```python
from bisect import bisect_left, bisect_right

temps = [11, 14, 14, 14, 19, 23]
print(bisect_left(temps, 14), bisect_right(temps, 14))
# -> 1 4
print(bisect_left(temps, 15), bisect_right(temps, 15))
# -> 4 4
print(bisect_left(temps, 5), bisect_right(temps, 5))
# -> 0 0
print(bisect_left(temps, 99), bisect_right(temps, 99))
# -> 6 6
```

Both functions answer the same question — *at which index may this value be inserted so that the
list stays sorted* — and for a value not already present there is exactly one such index, so they
agree. The three 14s are where they part. `bisect_left` returns 1, the position just before the
run of equal values; `bisect_right` returns 4, just after it. **The names are about ties and nothing
else: `left` puts the newcomer ahead of its equals, `right` puts it behind them.**

Two spellings are worth knowing because you will read them. `bisect` is another name for
`bisect_right`, and `insort` is another name for `insort_right`, so the unsuffixed forms are the
tie-goes-last forms. None of these names is written in Python; each one comes from a C accelerator
module:

```python
import bisect
print(bisect.bisect is bisect.bisect_right)                   # -> True
print(bisect.insort is bisect.insort_right)                   # -> True
print(bisect.bisect_left.__module__, bisect.insort.__module__)
# -> _bisect _bisect
```

The halving is the whole reason to reach for this rather than a hand-written scan, and the cost is
easiest to see by counting comparisons rather than nanoseconds, since a count is a property of the
algorithm. Instrument `__lt__` and search a list of n elements at several targets:

```python
import math
from bisect import bisect_left

calls = 0

class Counted:
    __slots__ = ("v",)
    def __init__(self, v):
        self.v = v
    def __lt__(self, other):
        global calls
        calls += 1
        return self.v < other

for n in (1_000, 10_000, 100_000, 1_000_000):
    a = [Counted(i) for i in range(n)]
    worst = 0
    for target in (0, n // 3, n // 2, n - 1, n):
        calls = 0
        bisect_left(a, target)
        worst = max(worst, calls)
    print(f"{n:>9} {worst:>3} comparisons   log2(n) = {math.log2(n):.1f}")
# ->      1000  10 comparisons   log2(n) = 10.0
# ->     10000  14 comparisons   log2(n) = 13.3
# ->    100000  17 comparisons   log2(n) = 16.6
# ->   1000000  20 comparisons   log2(n) = 19.9
```

Twenty comparisons to place a value among a million. Each row is exactly `ceil(log2(n))`, which is
what halving buys: multiply the list by a thousand and add ten comparisons. Chapter 4 takes that
search apart on its own terms; here it is only the cheap half of an insertion.

### An insertion point is not a membership answer

The return value is an index, always, whether or not the value is in the list. It is easy to read it
as "found at 2" when it means "would go at 2".

```python
from bisect import bisect_left

prices = [12, 19, 25, 31]
print(bisect_left(prices, 20))        # -> 2      20 is not in the list
print(bisect_left(prices, 5))         # -> 0      nor is 5
print(bisect_left(prices, 99))        # -> 4      one past the end, a valid insertion point

try:
    prices[bisect_left(prices, 99)]
except IndexError as e:
    print(e)                          # -> list index out of range
```

**Turning an insertion point into a membership answer takes two extra steps you have to write
yourself: check that the index is in range, then check that the element there is equal.** The range
check is not optional, as the last four lines show. Chapter 1 section 8 writes that guard out in
full, where the point of it was beating `in` on a sorted list; the same guard shows up here for the
opposite reason, because the index is what you were after and the membership answer is the
afterthought.

The pair earns its keep on ties. The gap between them is the number of copies of a value, and the
slice between them is the stretch of equal values itself:

```python
from bisect import bisect_left, bisect_right
temps = [11, 14, 14, 14, 19, 23]
print(bisect_right(temps, 14) - bisect_left(temps, 14))       # -> 3
print(temps[bisect_left(temps, 14):bisect_right(temps, 14)])  # -> [14, 14, 14]
print(bisect_right(temps, 15) - bisect_left(temps, 15))       # -> 0
```

There is a precondition on all of this, and it is not checked. The list must already be sorted. Hand
`bisect` an unsorted list and it returns a confident, meaningless number, and `insort` puts the
value in a confident, meaningless place:

```python
from bisect import bisect_left, insort
scrambled = [31, 12, 25, 19]
print(bisect_left(scrambled, 20))     # -> 2
insort(scrambled, 20)
print(scrambled)                      # -> [31, 12, 20, 25, 19]

grid = [4, 8, 15, 16, 23, 42]
print(bisect_left(grid, 15), bisect_left(grid, 15, 3), bisect_left(grid, 15, 0, 2))
# -> 2 3 2
```

No exception, no warning. The last line shows the optional `lo` and `hi` arguments, which confine
the search to a window of the list — the way to search the sorted region of a list that is not
sorted throughout. They search that window in place, where handing `bisect` a slice would copy it
first at the cost chapter 1 section 5 measured, and the index that comes back is an index into the
whole list rather than into the window.

### insort: the search and the insertion together

`insort_left` and `insort_right` run the corresponding `bisect` and then insert at the index it
returned. They mutate the list in place and return `None`, which is the same convention as `append`
and `sort` and carries the same consequences for aliasing that chapter 1 section 9 laid out.

```python
from bisect import insort

readings = []
for r in (19, 11, 23, 14):
    insort(readings, r)
    print(r, readings)
# -> 19 [19]
# -> 11 [11, 19]
# -> 23 [11, 19, 23]
# -> 14 [11, 14, 19, 23]

print(insort(readings, 20))          # -> None
```

Because the list is the thing being changed, `insort` needs a real `insert` method and not merely
something indexable. The search half is happy with any sequence:

```python
from bisect import bisect_left, insort
readings = (11, 14, 19, 23)
print(bisect_left(readings, 17))     # -> 2
try:
    insort(readings, 17)
except AttributeError as e:
    print(e)                         # -> 'tuple' object has no attribute 'insert'
```

Now, when does the left/right choice actually change the result? Not for plain numbers:

```python
from bisect import insort_left, insort_right

a = [11, 14, 14, 14, 19, 23]
b = a[:]
insort_left(a, 14)
insort_right(b, 14)
print(a)          # -> [11, 14, 14, 14, 14, 19, 23]
print(b)          # -> [11, 14, 14, 14, 14, 19, 23]
print(a == b)     # -> True
```

Identical, and necessarily so: one 14 in a row of 14s is indistinguishable from another, so it does
not matter where among them it lands. **The choice only becomes observable when equal-comparing
elements carry something else that differs** — which is exactly what happens when you sort by one
field of a richer item.

### The key parameter

All four functions accept `key`, the same idea as `sorted(key=...)` from chapter 1 section 8:
ordering is decided by `key(element)` rather than by the element itself. Here is a queue of jobs
held in priority order, where two jobs already share priority 3:

```python
from bisect import bisect_left, bisect_right, insort_left, insort_right

jobs = [(1, "backup"), (3, "reindex"), (3, "vacuum"), (7, "report")]
priority = lambda job: job[0]

print(bisect_left(jobs, 3, key=priority), bisect_right(jobs, 3, key=priority))
# -> 1 3

left, right = jobs[:], jobs[:]
insort_left(left, (3, "purge"), key=priority)
insort_right(right, (3, "purge"), key=priority)
print(left)
# -> [(1, 'backup'), (3, 'purge'), (3, 'reindex'), (3, 'vacuum'), (7, 'report')]
print(right)
# -> [(1, 'backup'), (3, 'reindex'), (3, 'vacuum'), (3, 'purge'), (7, 'report')]
```

There is the difference, in a form you can see. `insort_right` is what you want for a work queue:
a newly arriving job of priority 3 waits behind the priority-3 jobs already queued, which is the
same first-come-first-served fairness that stable sorting gives you.

One asymmetry catches people. With `key` in play, `bisect` compares its argument against key values,
so you pass it a *key*; `insort` has to store the element, so you pass it a whole *item* and it
computes the key itself.

```python
from bisect import bisect_left
jobs = [(1, "backup"), (3, "reindex"), (3, "vacuum"), (7, "report")]
priority = lambda job: job[0]
try:
    bisect_left(jobs, (3, "purge"), key=priority)
except TypeError as e:
    print(e)     # -> '<' not supported between instances of 'int' and 'tuple'
```

The key function runs once per element the search actually probes, not once per element in the list,
and `insort` pays one extra call for the incoming item:

```python
from bisect import bisect_left, insort

calls = 0
def priority(job):
    global calls
    calls += 1
    return job[0]

data = [(i, "job") for i in range(1000)]

calls = 0
bisect_left(data, 500, key=priority)
print(calls)                                  # -> 9

calls = 0
insort(data[:], (500, "new"), key=priority)
print(calls)                                  # -> 11
```

Nine calls to place a value among a thousand, and eleven for `insort`: it is `insort_right`, whose
search takes ten probes here, plus one call on the incoming item to work out its key. A scan of
that list would have called the key function a thousand times. The precondition tightens
accordingly: the list must be sorted *by that key*, and a list sorted by some other key is just an
unsorted list as far as these functions are concerned.

### What it actually costs

Here is the honest accounting, and it is the reason this section exists. Chapter 1 section 8 named
the bill in one clause and moved on; this is where it comes due.

Finding the position costs about `log2(n)` comparisons — twenty on a million elements, measured
above. Then `insort` calls `list.insert`, and section 3 established what that does: every element
from the insertion point to the end moves one slot right. **Logarithmic search plus linear shift is
linear, so `insort` is O(n), and the elegant half of it is the half that does not matter.**

```python
import time
from bisect import insort

prev = None
for n in (500_000, 1_000_000, 2_000_000, 4_000_000):
    src = list(range(0, 2 * n, 2))          # sorted; n - 1 is odd, so it lands mid-list
    best = float("inf")
    for _ in range(50):
        nums = src[:]
        t = time.perf_counter()
        insort(nums, n - 1)
        best = min(best, (time.perf_counter() - t) * 1e6)
    growth = "" if prev is None else f"   x{best / prev:.2f}"
    prev = best
    print(f"n={n:>9}  {best:9.1f} us{growth}")
# -> n=   500000      162.4 us
# -> n=  1000000      347.5 us   x2.14
# -> n=  2000000      673.9 us   x1.94
# -> n=  4000000     1317.0 us   x1.95
```

Double the list, double the time. Twenty-odd comparisons do not double when the list does, so what
you are watching is the bulk pointer move and nothing else. The value lands mid-list, so every row
shifts half its list, and section 3's O(n − i) turns up inside `insort` unchanged.

### Repeated insort is quadratic

The consequence lands when you build a whole sorted list this way. Each `insort` is O(n) in the
current length, and the length grows by one each time, so n insertions cost on the order of n²/2
element moves. The alternative is to append everything — amortized constant per item, chapter 1
section 7 — and sort once at the end.

```python
import random, time
from bisect import insort

def keep_sorted(values):
    out = []
    for v in values:
        insort(out, v)
    return out

def sort_at_the_end(values):
    out = []
    for v in values:
        out.append(v)
    out.sort()
    return out

random.seed(7)
prev = None
for n in (25_000, 50_000, 100_000, 200_000):
    values = [random.random() for _ in range(n)]
    t = time.perf_counter(); a = keep_sorted(values);     slow = (time.perf_counter() - t) * 1000
    t = time.perf_counter(); b = sort_at_the_end(values); fast = (time.perf_counter() - t) * 1000
    assert a == b
    growth = "" if prev is None else f"  x{slow / prev:.2f}"
    prev = slow
    print(f"n={n:>7}  insort {slow:8.1f} ms   append+sort {fast:6.1f} ms   {slow / fast:5.0f}x{growth}")
# -> n=  25000  insort     47.8 ms   append+sort    2.1 ms      22x
# -> n=  50000  insort    183.3 ms   append+sort    4.7 ms      39x  x3.83
# -> n= 100000  insort    712.1 ms   append+sort    9.7 ms      74x  x3.88
# -> n= 200000  insort   2790.5 ms   append+sort   22.3 ms     125x  x3.92
```

Identical results, and at 200,000 values one route took 125 times longer than the other. The growth
column is the part to read: doubling n multiplies the `insort` build by very close to four every
step — the quadratic signature section 3 put on the front-insertion loop — while the sort-once
column roughly doubles. That gap is not a constant factor you can optimise away; it widens with
every doubling, so the 125× is a floor, not a headline.

**The rule that falls out: if you already have all the values, append them and sort once. Reach for
`insort` only when values arrive over time and the list has to be in order between arrivals.**

That second case is real, and `insort` is genuinely the right tool for it. The naive alternative
when order must hold after every arrival is to append and re-sort each time, which is worse:

```python
import random, time
from bisect import insort

random.seed(7)
n = 20_000
values = [random.random() for _ in range(n)]

def by_insort(values):
    out = []
    for v in values:
        insort(out, v)          # ordered after every arrival
    return out

def by_resort(values):
    out = []
    for v in values:
        out.append(v)
        out.sort()              # ordered after every arrival
    return out

t = time.perf_counter(); a = by_insort(values); x = (time.perf_counter() - t) * 1000
t = time.perf_counter(); b = by_resort(values); y = (time.perf_counter() - t) * 1000
assert a == b
print(f"insort {x:.1f} ms   append+sort each time {y:.1f} ms   {y / x:.1f}x")
# -> insort 31.1 ms   append+sort each time 333.9 ms   10.7x
```

Ten times faster, and both are quadratic. The difference is where the work goes: `insort` asks its
`log2(n)` questions and then moves memory in bulk, while `sort` has to re-establish what it is
looking at before it can place anything. Instrumenting `__lt__` and counting, at n = 2,000, makes
the split plain — 19,180 comparisons for the `insort` build against 2,036,052 for the repeated
sort, roughly ten per arrival against one per element already present.

So the honest statement is not that `insort` is fast. It is that among the ways to hold a list
continuously sorted while values arrive, `insort` is the cheapest. If the stream is long and the
list is large, the list is the wrong container: chapter 1 section 10 lays out what to reach for
instead, including `heapq`, which gives up full ordering, keeps only the smallest element cheap to
reach, and charges `log2(n)` per arrival rather than a linear shift.

One last caution, since `insort` mutates in place: it changes the length of the list underneath
whatever else is looking at it. Calling it on a list you are simultaneously iterating over, or
holding indexes into, is a different kind of mistake from an expensive one. Section 7 takes that
apart.

---

## 7. Hazards when the list changes size

Every insertion does two things at once: it changes the length, and it moves every element from the
insertion point onward one slot to the right. Anything that has already recorded a length or a
position is wrong from that instant. The bugs below are all that one fact, wearing different
clothes.

### Appending while you iterate does not stop

Chapter 1 section 6 has the mechanism: a list iterator holds the live list plus an integer
position, and the loop ends when that position reaches the *current* length. Appending pushes the
finish line away exactly as fast as the loop walks toward it. The guard is the only reason this
block terminates.

```python
queue = ['a', 'b']
handled = []
for job in queue:
    handled.append(job)
    queue.append(job + "'")     # every job schedules a follow-up job
    if len(handled) == 6:       # the loop has no other way to end
        break
print(handled)      # -> ['a', 'b', "a'", "b'", "a''", "b''"]
print(len(queue))   # -> 8
```

Watch the two numbers that decide when to stop. The position gains one per step; so does the
length; the gap between them is 2 at the start and 2 forever.

```python
queue = ['a', 'b']
it = iter(queue)
for _ in range(5):
    job = next(it)
    queue.append(job + "'")
    print(it.__reduce__()[2], len(queue))
# -> 1 3
# -> 2 4
# -> 3 5
# -> 4 6
# -> 5 7
```

The append does not have to be visible in the loop body. Any function you call from inside the loop
that appends to the same list has the same effect, and reads as an innocent one-line call.

A work queue that discovers more work is a legitimate thing to want. Write it as a loop whose
condition is re-evaluated against the list itself, so that draining it can actually end:

```python
queue = ['a', 'b']
handled = []
while queue:
    job = queue.pop()
    handled.append(job)
    if len(job) < 3:
        queue.append(job + "'")
print(handled)   # -> ['b', "b'", "b''", 'a', "a'", "a''"]
print(queue)     # -> []
```

### Inserting while you walk by index

`for i in range(len(jobs))` looks like it sidesteps the problem, because the range is built once
from the length at the start and never changes afterwards. It sidesteps nothing. You now hold a
fixed set of indices into a list whose contents keep sliding right out from under them.

```python
jobs = ['build', 'deploy', 'test', 'deploy']
for i in range(len(jobs)):
    print(i, jobs[i], jobs)
    if jobs[i] == 'deploy':
        jobs.insert(i, 'checkpoint')    # a checkpoint before every deploy
print(jobs)
# -> 0 build ['build', 'deploy', 'test', 'deploy']
# -> 1 deploy ['build', 'deploy', 'test', 'deploy']
# -> 2 deploy ['build', 'checkpoint', 'deploy', 'test', 'deploy']
# -> 3 deploy ['build', 'checkpoint', 'checkpoint', 'deploy', 'test', 'deploy']
# -> ['build', 'checkpoint', 'checkpoint', 'checkpoint', 'deploy', 'test', 'deploy']
```

At `i = 1` the deploy is found and a checkpoint goes in ahead of it — which pushes that same
deploy to index 2, where the next step meets it again, and again at index 3. Three checkpoints for
one deploy. Meanwhile the range still stops at 3, the last index of the list as it was, so the
second deploy is never examined at all. **A loop that inserts examines some elements more than
once and never reaches others, and a single insertion is enough to cause both.**

Writing it as `for job in jobs` rescues nothing. That loop carries the position from chapter 1
section 6, and an insertion at or before the position hands it the same element again on the next
step, so it fails the way the append loop above fails: it does not end.

The `while i < len(jobs)` form re-reads the length every time, which fixes the half that stops too
early and makes the other half unbounded:

```python
jobs = ['build', 'deploy', 'test']
i = 0
steps = 0
while i < len(jobs):
    if jobs[i] == 'deploy':
        jobs.insert(i, 'checkpoint')
    i += 1
    steps += 1
    if steps == 8:              # again, the only exit
        break
print(steps, len(jobs))         # -> 8 10
print(jobs[:4])                 # -> ['build', 'checkpoint', 'checkpoint', 'checkpoint']
```

You can repair either loop by hand — advance `i` past what you just inserted, and stop trusting a
bound computed before the list grew. It works, and it is the kind of correction that quietly falls
out of step the next time someone edits the loop body. The two approaches below need none.

### An index goes stale the moment something is inserted before it

Strip the loop away and the same bug is still there. Write an index down, change the shape of the
list, and the index now names a different element.

```python
prices = [10, 20, 30, 40]
i = prices.index(30)
print(i)              # -> 2
prices.insert(1, 15)  # a correction arrives for an earlier position
print(prices)         # -> [10, 15, 20, 30, 40]
print(prices[i])      # -> 20   not 30
```

An index is not a name for an element. It is a name for a position, and it is only meaningful
against a list of the exact shape it was computed from. An insertion at position p leaves every
index below p correct and makes every index at or above p point one element too early. That is true
of indices you keep in variables and equally true of indices you keep in another structure:

```python
names = ['ana', 'bo', 'cy']
where = {n: i for i, n in enumerate(names)}
print(where)                                        # -> {'ana': 0, 'bo': 1, 'cy': 2}
names.insert(1, 'ash')
print([names[where[n]] == n for n in where])        # -> [True, False, False]
```

The `True` is the one entry that happened to sit before the insertion point. That surviving half is
what makes the second correct approach below work.

### Correct approach one: build the new list

Change nothing in place. Chapter 1 section 6 reaches for this when elements are coming out; it works
the same way when they are going in. Take a harder job than the checkpoints above: a shift roster,
one owner per entry, and a handover marker wanted wherever the owner changes from one entry to the
next. The insertion points now depend on a *pair* of neighbours, so a loop that mutates as it walks
corrupts the very pairs it still has to examine. Walk the input and append the output you want,
insertions included:

```python
shift = ['ana', 'ana', 'bo', 'cy', 'cy']
out = []
for i, owner in enumerate(shift):
    if i and owner != shift[i - 1]:
        out.append('handover')      # a marker wherever the owner changes
    out.append(owner)
print(out)
# -> ['ana', 'ana', 'handover', 'bo', 'handover', 'cy', 'cy']
```

Nothing ever shifts, because every write lands at the end, where appends are amortized O(1)
(chapter 1 section 7). One pass, O(n) total, and the list you are reading is not the list you are
writing — `shift[i - 1]` still means what it meant before any marker existed, and no position
anywhere is invalidated. Where the list is allowed to grow, this is the default. If the caller
needs the change on their object rather than a new one, finish with `shift[:] = out` — chapter 1
section 9 has why that is a different statement from `shift = out`.

That last step is where the approach starts costing. `out` is longer than `shift`, so
`shift[:] = out` moves the count, and a fixed length forbids exactly that. **When the length is
fixed, the object you were handed is the answer, and a list of a different length cannot be written
into it.** That is the situation section 5 sets out, and the situation both of this chapter's
problems hand you.

That rules out one statement, though, not the whole approach. The second list still has somewhere to
land; it just has to arrive at exactly the count you were given, which is the one length-preserving
family section 5 names. `shift[:] = out` publishes as it stands only when `len(out) == len(shift)`,
and otherwise you cut it to fit on the way in:

```python
shift = ['ana', 'ana', 'bo']
out = ['ana', 'ana', 'handover', 'bo']       # one longer than the list you were handed
before = (len(shift), id(shift))
shift[:] = out[:len(shift)]                  # publish, cut to the count you were given
print(shift, (len(shift), id(shift)) == before)
# -> ['ana', 'ana', 'handover'] True
```

Same object, same length, answer inside it. So what a fixed length takes away is not the technique
but the discount: `out` is a second list of its own, O(n) of room standing next to the list you were
already handed, and that room is the thing the constraint exists to charge you for. Read it as a
budget on space rather than a ban, and the choice stays yours to make knowingly — which is the
choice this chapter's problems are built to make you make.

### Correct approach two: plan the insertions, then apply them

When the list has to stay the same object and only a few insertions are going in, you can do it in
two phases: compute every insertion point first, against the untouched list, then apply them.
Computing first is also what keeps the neighbour test honest — once a marker is in, `shift[i - 1]`
is no longer the entry it was. The staleness comes back during the applying, and the correction is
one number: each insertion already applied pushes every remaining planned position one slot right,
so the k-th insertion belongs at `points[k] + k`.

```python
shift = ['ana', 'ana', 'bo', 'cy', 'cy']
points = [i for i in range(1, len(shift)) if shift[i] != shift[i - 1]]
print(points)                                # -> [2, 3]
for offset, i in enumerate(points):
    shift.insert(i + offset, 'handover')     # offset == insertions applied so far
print(shift)
# -> ['ana', 'ana', 'handover', 'bo', 'handover', 'cy', 'cy']
```

Drop the `+ offset` and the plan is applied to a list that no longer matches it:

```python
shift = ['ana', 'ana', 'bo', 'cy', 'cy']
for i in [2, 3]:
    shift.insert(i, 'handover')
print(shift)
# -> ['ana', 'ana', 'handover', 'handover', 'bo', 'cy', 'cy']
```

Both markers piled up in front of `bo`, and the change into `cy` got none. Nothing raised; the
answer is just wrong.

The price is the one from section 3: every `insert` shifts the tail, so k insertions into a list
of length n cost O(n·k), against O(n) for building the result. Put both against the same input —
a roster where the owner changes every fourth entry, so k is about n/4:

```python
import timeit

def plan_and_insert(shift):
    out = shift.copy()
    points = [i for i in range(1, len(out)) if out[i] != out[i - 1]]
    for offset, i in enumerate(points):
        out.insert(i + offset, 'handover')
    return out

def build_new(shift):
    out = []
    for i, owner in enumerate(shift):
        if i and owner != shift[i - 1]:
            out.append('handover')
        out.append(owner)
    return out

for n in (5_000, 10_000, 20_000, 40_000):
    shift = (['ana'] * 4 + ['bo'] * 4) * (n // 8)
    a = min(timeit.repeat(lambda: plan_and_insert(shift), number=1, repeat=7))
    b = min(timeit.repeat(lambda: build_new(shift), number=1, repeat=7))
    print(f"n = {n:<6} plan {a * 1e3:8.3f} ms   build {b * 1e3:6.3f} ms   ratio {a / b:6.1f}")
# -> n = 5000   plan    1.018 ms   build  0.156 ms   ratio    6.5
# -> n = 10000  plan    3.791 ms   build  0.306 ms   ratio   12.4
# -> n = 20000  plan   14.568 ms   build  0.610 ms   ratio   23.9
# -> n = 40000  plan   57.446 ms   build  1.231 ms   ratio   46.7
```

The `copy()` gives each timed round a fresh list; one O(n) copy next to a quadratic does not change
the shape. Every doubling of n doubles the build and roughly quadruples the plan-and-insert, so the
ratio between them doubles too — the quadratic, showing itself. Use the plan when the object
identity matters and k is small; reach for it knowingly, not by habit.

### The list may not be yours alone

Two names, one list, and an insertion through either one is visible through both:

```python
baseline = [10, 20, 30]
current = baseline
current.insert(0, 5)
print(baseline, current is baseline)   # -> [5, 10, 20, 30] True

baseline = [10, 20, 30]
current = baseline.copy()              # now they are separate objects
current.insert(0, 5)
print(baseline, current)               # -> [10, 20, 30] [5, 10, 20, 30]
```

Chapter 1 section 9 covers names, aliasing, and what a parameter binding does. Changing the length
raises the stakes over merely writing a slot, because a co-owner may hold more than the object: an
index into it, a length it recorded, a loop currently walking it, or a slice taken earlier that is a
separate list and now quietly disagrees. You cannot see any of that from inside your function.

That leaves two honest options. Copy before you insert, `current = list(baseline)`, and hand back
the copy. Or mutate deliberately, say so in the docstring, and write the finished result through the
shared object in one statement so no holder ever sees a half-built state:

```python
jobs = ['build', 'deploy']
alias = jobs
jobs[:] = ['checkpoint'] + jobs        # right-hand side is built first, then stored
print(alias, alias is jobs)            # -> ['checkpoint', 'build', 'deploy'] True
```

### Four questions before you mutate a list you were handed

1. **Is it mine to change?** A list that arrived as a parameter belongs to the caller. If the
   contract does not say you may edit it, build and return a new one.
2. **Does its length have to stay the same?** Some contracts fix it: the object you were given *is*
   the answer, and the answer has exactly n slots. Then `append`, `insert`, `pop` and any slice
   assignment that changes the count are all off the table, and every change is a write into a slot
   that already exists — indexed assignment, or the equal-length splice built out of it. Section 5
   draws that line in full.
3. **Is anything iterating it right now?** Including a loop further up the call stack that you
   cannot see from here, and including your own loop over the very list you are inserting into.
4. **Does anyone else hold a reference?** Another name, another object's attribute, a container it
   was put into, or an index recorded before you started.

If question 1, 3 or 4 is uncertain, build a new list and return it. That answer is correct under all
three, and it is the cheaper one besides. Question 2 is the exception, and the only one: when the
count is fixed, the new list cannot be handed back, and it can only be written through the old one
if it is exactly the same length — which costs the extra room the constraint exists to deny. Do the
work in the slots you were already given and you pay neither. That is where section 5 leaves you,
and where this chapter's problems begin.

---

## 8. Drills

Eleven snippets. Same procedure as before: predict, run, read, in that order and no other. Write the
prediction down in full — the exact list, the exact length, the exact exception type and message
where one is involved — because "it grows" and "it raises something" cannot be wrong in the useful
way. The answer key is the next subsection, and every output there was produced by running the
snippet on CPython 3.14.4. Drill 11 reports this machine's timings; yours will differ in the
digits, so what you predict there is which column grows and by what factor.

### The drills

**Drill 1.**

```python
queue = ["ana", "bo", "cy"]
queue.insert(0, "zed")
print(queue)              # ?

queue.insert(len(queue), "dee")
print(queue)              # ?

queue.insert(2, "eve")
print(queue, len(queue))  # ?

back = queue.insert(1, "fay")
print(back)               # ?
```

**Drill 2.**

```python
temps = [12, 15, 19]
temps.insert(-1, 99)
print(temps)    # ?

temps.insert(-99, 0)
print(temps)    # ?

temps.insert(99, 100)
print(temps)    # ?

empty = []
empty.insert(7, 5)
print(empty)    # ?

try:
    empty[7] = 5
except IndexError as e:
    print(type(e).__name__, e)   # ?
```

**Drill 3.**

```python
codes = [10, 20, 30, 40]
codes[2:2] = [25]
print(codes, len(codes))          # ?

codes[1:3] = []
print(codes, len(codes))          # ?

codes[0:1] = [1, 2, 3]
print(codes, len(codes))          # ?

codes[len(codes):] = [99]
print(codes, len(codes))          # ?
```

**Drill 4.**

```python
names = ["ana", "cy"]
names[1:1] = "bo"
print(names)     # ?

names = ["ana", "cy"]
names[1:1] = ["bo"]
print(names)     # ?

names = ["ana", "cy"]
names.insert(1, "bo")
print(names)     # ?

names = ["ana", "cy"]
names[1:1] = ("bo", "di")
print(names)     # ?
```

**Drill 5.**

```python
rgb = [255, 128, 0, 64, 32, 16]
rgb[::2] = [1, 2, 3]
print(rgb)                       # ?

try:
    rgb[::2] = [7, 8]
except ValueError as e:
    print(type(e).__name__, e)   # ?

rgb[2:2:1] = [7, 8]
print(rgb, len(rgb))             # ?
```

**Drill 6.**

```python
a = [1, 2]
b = a
a = a + [3]
print(a, b)      # ?

c = [1, 2]
d = c
c += [3]
print(c, d)      # ?

e = [1, 2]
e += "xy"
print(e)         # ?

try:
    e = e + "z"
except TypeError as err:
    print(type(err).__name__, err)   # ?
```

**Drill 7.**

```python
import bisect

prios = [1, 2, 2, 5]
print(bisect.bisect_left(prios, 2), bisect.bisect_right(prios, 2))   # ?

jobs = [(1, "a"), (2, "b"), (2, "c"), (5, "d")]
keys = [p for p, _ in jobs]

left = jobs[:]
left.insert(bisect.bisect_left(keys, 2), (2, "new"))
print(left)     # ?

right = jobs[:]
right.insert(bisect.bisect_right(keys, 2), (2, "new"))
print(right)    # ?

print(bisect.insort is bisect.insort_right)   # ?
```

**Drill 8.**

```python
jobs = [1, 2, 3]
for j in jobs:
    if len(jobs) < 6:
        jobs.append(j * 10)
print(jobs)     # ?

seen = []
batch = ["a", "b", "c"]
for i, item in enumerate(batch):
    seen.append((i, item))
    if item == "a" and "urgent" not in batch:
        batch.insert(0, "urgent")
print(seen)     # ?
print(batch)    # ?
```

**Drill 9.**

```python
import sys

def capacity(lst):
    return (sys.getsizeof(lst) - sys.getsizeof([])) // 8

slots = [None] * 4
slots[1] = "x"
print(slots, len(slots))         # ?

try:
    slots[4] = "y"
except IndexError as e:
    print(type(e).__name__, e)   # ?

slots[4:] = ["y"]
print(slots, len(slots))         # ?

fixed = [0] * 4
print(len(fixed), capacity(fixed))   # ?
fixed.insert(0, 9)
print(len(fixed), capacity(fixed))   # ?
```

**Drill 10.** Trace the buffer and the count together; both are part of the answer.

```python
def record(buf, count, value):
    buf[count] = value
    return count + 1

slots = [0] * 5
count = 0

count = record(slots, count, 31)
record(slots, count, 42)
count = record(slots, count, 55)
print(slots, count)              # ?

full = [0] * 2
n = 0
n = record(full, n, 7)
n = record(full, n, 8)
try:
    n = record(full, n, 9)
except IndexError as e:
    print(type(e).__name__, e)   # ?

levels = [0, 4, 0, 9, 0, 0, 0]   # seven positions; the first four are readings, in Celsius
count = 4
print(len(levels), count)                      # ?
print(levels[:count])                          # ?
print(sum(1 for v in levels if v != 0))        # ?
print(levels.count(0), len(levels) - count)    # ?
```

**Drill 11.** Predict the shape, not the digits. For the first block, say for each of the three
columns whether doubling `n` roughly doubles the time or leaves it flat, and why the middle column
sits where it does relative to the first. For the second block, predict which line wins and by
roughly what order of magnitude.

```python
import timeit

def ms(stmt, n):
    return min(timeit.repeat(stmt, f"data = list(range({n}))", number=1, repeat=5)) * 1000

for n in (20_000, 40_000, 80_000):
    front = ms("for k in range(2000): data.insert(0, k)", n)
    mid = ms("for k in range(2000): data.insert(len(data) // 2, k)", n)
    end = ms("for k in range(2000): data.append(k)", n)
    print(n, round(front, 2), round(mid, 2), round(end, 2))   # ?

setup = "data = list(range(50_000)); extra = list(range(2_000))"
one = min(timeit.repeat("data[10:10] = extra", setup, number=1, repeat=5)) * 1000
many = min(timeit.repeat("for j, x in enumerate(extra): data.insert(10 + j, x)",
                         setup, number=1, repeat=5)) * 1000
print(round(one, 3), round(many, 3))   # ?
```

### The answer key

**1.** `['zed', 'ana', 'bo', 'cy']` / `['zed', 'ana', 'bo', 'cy', 'dee']` /
`['zed', 'ana', 'eve', 'bo', 'cy', 'dee'] 6` / `None`. `insert(i, x)` puts `x` at index `i` and
moves everything from `i` onward one slot to the right, so `insert(0, ...)` shifts the whole list
and `insert(len(queue), ...)` shifts nothing and puts the value exactly where `append` would. Same
place, same complexity class, and not the same speed: on a 50,000-element list this machine measured
`append` at 5.7 ns per call against 11.7 ns for `data.insert(10**9, 1)`, which drill 2's clamping
rule puts at the end without a `len` call — about two to one — rising to 18.2 ns, about three to
one, once the `len(data)` you would actually write is charged as well. **`insert` mutates and
returns `None`, so `queue = queue.insert(...)` destroys the list you were building.** (Sections 2
and 3; chapter 1 section 8 for why matching complexity is not matching speed.)

**2.** `[12, 15, 99, 19]` / `[0, 12, 15, 99, 19]` / `[0, 12, 15, 99, 19, 100]` / `[5]` /
`IndexError list assignment index out of range`. The index argument to `insert` is a *position
between elements*, resolved the way a slice bound is: negatives count back from the end, and
anything past either end clamps instead of raising. So `-1` means "before the last element", not
"at the end"; `-99` clamps to the front; `99` clamps to the back and behaves as `append`. **A
subscript assignment resolves the same number under the opposite rule — it must name an existing
slot, so it is bounds-checked and raises.** (Sections 3 and 5.)

**3.** `[10, 20, 25, 30, 40] 5` / `[10, 30, 40] 3` / `[1, 2, 3, 30, 40] 5` /
`[1, 2, 3, 30, 40, 99] 6`. Assigning to a contiguous slice replaces that span with however many
elements you supply, so the length moves by `len(replacement) - len(span)`: an empty target span
inserts, an empty replacement deletes, and a longer replacement does both at once.
`codes[len(codes):]` is the empty span at the far end, which makes that last line a spelling of
`extend`. (Section 4.)

**4.** `['ana', 'b', 'o', 'cy']` / `['ana', 'bo', 'cy']` / `['ana', 'bo', 'cy']` /
`['ana', 'bo', 'di', 'cy']`. **Splice assignment iterates its right-hand side; `insert` does not.**
A string is iterable, so splicing one in spreads its characters across separate slots — a silent
wrong answer, not an error. Any iterable works on the right, which is why the tuple splices cleanly
into two slots. When you mean one element, `insert` says so and cannot be misread. (Section 4.)

**5.** `[1, 128, 2, 64, 3, 16]` /
`ValueError attempt to assign sequence of size 2 to extended slice of size 3` /
`[1, 128, 7, 8, 2, 64, 3, 16] 8`. An extended slice — step other than 1 — selects scattered
positions with gaps between them that belong to other elements, so there is nowhere to put a
surplus and nothing to close a shortfall; the count must match exactly and the length cannot change.
A step of exactly 1 is contiguous even when you write it out, so `rgb[2:2:1]` is an ordinary empty
span and inserts. **The step is what decides whether a slice assignment can resize; it is not a
matter of how you spelled the bounds.** (Section 4; chapter 1 section 5.)

**6.** `[1, 2, 3] [1, 2]` / `[1, 2, 3] [1, 2, 3]` / `[1, 2, 'x', 'y']` /
`TypeError can only concatenate list (not "str") to list`. `a + [3]` builds a new list and rebinds
the name, leaving `b` on the original object; `c += [3]` calls `__iadd__`, which extends the
existing object in place, so `d` sees it. The two lines read as synonyms and differ in whether the
insertion is visible to every other name on that list. They also differ in what they accept:
`+=` is `extend`, so it takes any iterable and spreads a string into characters, while `+` demands
another list. Cost follows the same split, because `+` copies the whole left operand every time:
growing a list by repeated `+` took 10.5, 49.2 and 219.5 ms over 4,000, 8,000 and 16,000
iterations, quadrupling on each doubling, while `+=` took 0.12, 0.22 and 0.44 ms and merely
doubled. (Sections 2 and 4; chapter 1 sections 7 and 9.)

**7.** `1 3` / `[(1, 'a'), (2, 'new'), (2, 'b'), (2, 'c'), (5, 'd')]` /
`[(1, 'a'), (2, 'b'), (2, 'c'), (2, 'new'), (5, 'd')]` / `True`. On a run of equal keys,
`bisect_left` returns the index of the first, `bisect_right` the index just past the last — 1 and 3
here, and the gap between them is exactly the number of ties. Both keep the list sorted, so on plain
numbers the two results are indistinguishable; with records carrying a key, left cuts in ahead of
the existing ties and right queues behind them. `bisect.insort` is `insort_right`, so the default
is stable in the useful sense: equal keys stay in arrival order. Note also that the search is
O(log n) and the insertion it feeds is still O(n), because the tail still has to shift.
(Sections 3 and 6.)

**8.** `[1, 2, 3, 10, 20, 30]` / `[(0, 'a'), (1, 'a'), (2, 'b'), (3, 'c')]` /
`['urgent', 'a', 'b', 'c']`. The whole state an iterator carries is an integer position into the
live list, so every step reads whatever occupies the next slot at that moment — chapter 1 section 6
established that for a list shrinking underneath a loop, and growth is the same mechanism running
the other way. Appending extends what the loop will visit: the first block goes on to iterate over
the very items it added, and only the length guard stops it — run it without the guard and the list
is 53 elements long 50 steps in and still climbing. Inserting is worse than that. `insert(0, ...)`
slides every element one slot right while the position keeps advancing, so `'a'` moves into the slot
the iterator is about to read and is visited twice. **A list that changes length under an iterator
does not raise; it silently re-reads or skips.** Iterate `batch[:]` when the loop must see the
sequence it started with. (Section 7.)

**9.** `[None, 'x', None, None] 4` / `IndexError list assignment index out of range` /
`[None, 'x', None, None, 'y'] 5` / `4 4` / `5 8`. Subscript assignment overwrites one slot and
cannot change the length, which is what makes it the only tool available when a length is fixed;
it also cannot reach a slot that does not exist yet, so index 4 of a four-element list raises rather
than growing it. Slice assignment at that same position does grow it, which is why a fixed-length
requirement bans the slice form as well as `insert`, `append` and `pop`. The capacity readings show
the second cost of growing: `[0] * 4` is sized exactly, and the first `insert` reallocates to eight
slots, copying the block. (Sections 3 and 5; chapter 1 section 7.)

**10.** `[31, 55, 0, 0, 0] 2` / `IndexError list assignment index out of range` / `7 4` /
`[0, 4, 0, 9]` / `2` / `5 3`. The middle `record` call had its return value dropped, so the call
after it was told the same position was still free and wrote 55 on top of the 42. Nothing announces
the loss: the length is 5 before and after, no exception is raised, and the count and the two
surviving values agree with each other, so the buffer reads afterwards as a consistent record of two
entries rather than a damaged record of three. **A list will not track how much of itself is
meaningful, so on a fixed length the count is a second number you carry, and every write that
advances the frontier has to advance it.** That count is also the only thing keeping the subscript
inside the buffer: it is not a hint, it is the bound, and once it reaches the length the write
raises instead of growing the list (drills 2 and 9). The last block asks whether inspection can hand
the count back, and it cannot. Occupancy is 4 against a length of 7; the scan for non-filler values
reports 2, because two of the four readings are genuinely 0 °C and 0 is also what the reserved
positions hold; `levels.count(0)` goes at it from the other side and claims 5 free positions where 3
are free. When a reading and a reserved slot hold the same object, no amount of looking will
separate them. (Section 5; chapter 1 sections 4 and 7.)

**11.** This machine printed `20000 11.49 5.97 0.02` / `40000 23.82 11.98 0.02` /
`80000 45.3 23.48 0.02`, then `0.007 29.618`. The digits are this machine's; the ratios are the
answer.

The first column doubles when `n` doubles — 11.49, 23.82, 45.3 — because each of the 2,000 inserts
at index 0 shifts all `n` pointers, so the work is proportional to `n` per insert. The middle column
is consistently about half the first (5.97, 11.98, 23.48) and doubles in the same way: inserting at
the midpoint shifts only the half of the list that lies to the right of it. **Inserting in the
middle is not a cheap compromise between the two ends; it is the front's cost with a constant factor
of one half, and one half of O(n) is still O(n).** The third column does not move with `n` at all,
0.02 ms at every size across a fourfold range, because appending shifts nothing.

The second block places the same 2,000 elements at the same position two ways and produces identical
lists. One splice took 0.007 ms; two thousand inserts took 29.618 ms, about 4,200 times longer, and
repeated runs keep that multiplier in the four thousands rather than moving it. The
splice computes the final length once and moves each displaced pointer exactly once; the loop moves
those same pointers once per insertion. Whenever you know the whole batch up front, that is a single
slice assignment, not a loop. (Sections 3 and 4.)

### The readiness checklist

Chapter 1's scoring rule applies unchanged: explanation rather than recognition, out loud, in under
a minute. Each statement names the section that carries it and the drill that tests it.

You should be able to explain, without looking it up, why:

1. `append(x)` and `insert(len(nums), x)` put the value in the same place for the same complexity
   and still do not cost the same per call, while `insert(0, x)` costs O(n), and what exactly that
   O(n) is spent on. (Sections 2 and 3; drills 1 and 11.)
2. `nums.insert(-1, x)` does not put `x` at the end, and why `nums.insert(99, x)` on a short list
   is silent where `nums[99] = x` raises. (Sections 3 and 5; drill 2.)
3. inserting in the middle is O(n) rather than O(n/2) in any sense that matters, and what the
   measured half-factor does and does not tell you. (Section 3; drill 11.)
4. `nums[i:i] = [x]` changes the length while `nums[i] = x` cannot, and which of the two a
   fixed-length requirement leaves you. (Sections 4 and 5; drills 3 and 9.)
5. `nums[1:1] = "bo"` and `nums.insert(1, "bo")` give different lists, and what rule about the
   right-hand side produces the difference. (Section 4; drill 4.)
6. `nums[::2] = [...]` raises on a length mismatch while `nums[2:2] = [...]` accepts any length.
   (Section 4; drill 5.)
7. `nums += [x]` is visible through every other name bound to that list and `nums = nums + [x]` is
   not, and which of the two is quadratic inside a loop. (Sections 2 and 4; drill 6.)
8. `bisect_left` and `bisect_right` pick different insertion points among equal keys, why the
   resulting lists are both sorted, and why the O(log n) search does not make the insertion cheap.
   (Section 6; drill 7.)
9. a list that grows during a `for` loop over it can visit an element twice or run forever without
   raising anything. (Section 7; drill 8.)
10. a fixed-length buffer has to travel with its count as a separate number, why one dropped return
    value destroys an entry without changing the length or raising anything, and why scanning for
    the filler cannot recover the count afterwards. (Section 5; drill 10.)
11. one slice assignment beats a loop of `insert` calls by more than three orders of magnitude at
    2,000 elements, and what has to be true of your data before you can use it. (Sections 3 and 4;
    drill 11.)
