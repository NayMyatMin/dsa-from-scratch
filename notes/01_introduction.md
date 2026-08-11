# Chapter 1 — Arrays and Python Lists

This is the whole of the foundation. Everything in the chapters that follow — inserting, deleting,
searching, working in place — is a technique built on top of the machinery described here, so the
time spent on this chapter pays back across all nineteen problems rather than just the three that
sit alongside it.

It is written to be self-contained. You should not need to look anything up while reading it, and
you should not need to come back to it later to check a claim, because every claim is demonstrated
rather than asserted.

## How to read this

**Run the code.** Every block is executable exactly as written, and every `# -> value` comment is a
real observed result, not an illustration. There are 273 of them. Open a session next to this
document and paste as you go:

```bash
uv run python
```

Some blocks continue the one before them within a section, reusing a variable that was set up
earlier. Some blocks deliberately end in an exception, and say so on the offending line — those are
demonstrations, and the exception is the point.

**Predict before you run.** The habit this chapter is really trying to build is the reflex of
forming an expectation and then checking it. Section 12 is nothing but that, and it is the honest
test of whether the rest of it landed.

**Measurements come from this machine.** Every number was measured on CPython 3.14.4, the
interpreter in this repository's virtual environment, on a 64-bit build. Deterministic values —
object sizes, capacities, printed output — will reproduce exactly for you. Timings will not; they
depend on your hardware and on what else is running. What should reproduce is the *shape*: the
ratios, the orderings, and the growth curves. Section 11 teaches you how to measure these things
yourself, which matters more than any individual figure here.

## The sections

| | Section | What it settles |
|---|---|---|
| 1 | [What an array is, and why it is fast](#1-what-an-array-is-and-why-it-is-fast) | Contiguity, indexes, and where constant-time access comes from |
| 2 | [What a Python list actually is](#2-what-a-python-list-actually-is) | The object layout, and why a slot holds an address |
| 3 | [Creating lists](#3-creating-lists) | Every construction form, and the mutable-repetition trap |
| 4 | [Reading and writing elements](#4-reading-and-writing-elements) | The two primitive operations, and the off-by-one |
| 5 | [Slicing, completely](#5-slicing-completely) | Clamping, negative steps, and slice assignment |
| 6 | [Iterating](#6-iterating) | The iterator protocol, and why mutating mid-loop skips |
| 7 | [Length and capacity](#7-length-and-capacity) | Over-allocation, the growth rule, and amortized cost |
| 8 | [The cost of every operation](#8-the-cost-of-every-operation) | The full table, derived rather than memorised |
| 9 | [Names, aliasing, and changing a list in place](#9-names-aliasing-and-changing-a-list-in-place) | Rebinding versus mutating, and why it decides correctness |
| 10 | [When a list is the wrong container](#10-when-a-list-is-the-wrong-container) | The rest of the landscape, and why `list` still wins here |
| 11 | [Measuring instead of guessing](#11-measuring-instead-of-guessing) | How to settle any of this yourself, permanently |
| 12 | [Drills, and how to know you have it](#12-drills-and-how-to-know-you-have-it) | Twelve predictions, an answer key, and a readiness check |

Sections 1 through 7 are the core and are best read in order. Sections 8 through 11 are reference
you will come back to. Section 12 is the exit exam.

When you finish, the three problems in `arrays101/ch01/` are waiting, and every trap in them is
something this chapter has already warned you about.

---

## 1. What an array is, and why it is fast

### A box of DVDs

Start with a physical object, because the physical version of this idea is the whole idea.

You own a pile of DVDs. You could keep them the way things actually accumulate in a house: one on
the shelf under the television, one on the kitchen counter, three in a bedroom drawer, one still in
the car. Nothing is lost. Every disc is *somewhere*. But the question "where is the nature
documentary" has become expensive. Answering it means walking rooms, opening drawers, and checking
the car — and the walk gets longer every time you buy another DVD and every time you acquire
another surface to put one on.

So you buy a box, and you put every DVD in it. That single act imposes three constraints, and each
one is doing real work.

**The box holds one kind of thing.** DVDs, not DVDs mixed with cereal boxes and a hammer. Because
every item is the same shape and the same thickness, a position in the box is a *measurable*
distance from the front. The eighth case is eight case-widths in. If the box held items of assorted
sizes, "the eighth one" would still be a real disc, but you could not compute where it sits without
inspecting the seven in front of it first.

**Everything is in one place.** The box is a single continuous run of storage — no second box in
the loft, no overflow shelf. You go to exactly one location, and once you are there, every disc
you own is within arm's reach.

**Positions are numbered.** Slot 0, slot 1, slot 2, and so on to the back. A number is not a
description of a disc; it is the identity of a *place*. Two different discs can occupy slot 3 on two
different days, and slot 3 means the same location both times.

Put those three together and something specific becomes possible: you can retrieve any disc without
searching. You know it is in slot 8, you count eight widths in, and you pull. Reaching slot 8 takes
the same effort as reaching slot 1 — and, more surprisingly, the same effort whether the box holds
twenty discs or two thousand.

### The same box, in memory

An array is that box. **It is a collection of items held in neighbouring memory locations — one
run of storage, no gaps, no second location.** That word *neighbouring*, or more formally
*contiguous*, is not a detail of the implementation. It is the point of the structure.

The number that identifies a place is called an **index**. Indexes start at 0, so the first item
lives at index 0, the second at index 1, and in general the k-th item lives at index k − 1. For a
collection of N items, the valid indexes run from 0 up to N − 1 inclusive — N distinct indexes,
none of them equal to N.

That off-by-one is not arbitrary. Read an index as *how far in from the front*, not as *which one in
sequence*: the first item is zero widths in, and the last of five is four widths in.

```python
temps = [17.2, 18.9, 21.4, 20.1, 16.8]   # five daily readings, degrees C

print(len(temps))                 # -> 5
print(temps[0])                   # -> 17.2   zero in from the front: the 1st reading
print(temps[2])                   # -> 21.4   two in from the front: the 3rd reading
print(temps[4])                   # -> 16.8   four in from the front: the 5th and last

print(list(range(len(temps))))    # -> [0, 1, 2, 3, 4]
```

Index 5 is not a slot that happens to be empty. It is not a slot at all — the run of storage ended
one position earlier:

```python
temps = [17.2, 18.9, 21.4, 20.1, 16.8]

try:
    temps[5]
except IndexError as e:
    print(e)                      # -> list index out of range
```

Python will also take an index from the far end — `temps[-1]` reaches the last reading — but
those are not extra slots, only a second way of naming the same five places. Section 4 gives
that rule properly. For the rest of this section, an index means a count forward from the front.

### Why the machine can jump straight to slot i

Here is the payoff, and it is arithmetic rather than magic.

The run of storage begins at some address — call it the base. Every slot occupies the same number
of bytes — call that the stride. The slot at index `i` therefore begins at `base + i * stride`.
That is one multiply and one add. The machine does not walk the earlier slots to get there, does
not consult a lookup table, and does not care what value is sitting in any other slot. It computes
an address and reads it.

One more step happens before the arithmetic, and it is worth naming because it is what produced the
`IndexError` above: the index is first checked against the length, a number the list already has on
hand rather than one it has to work out. That check does not grow with the collection, so it costs
the same on a list of ten and a list of ten million, and the guarantee below survives it intact.

You can watch the stride directly. Ask Python how many bytes a list of `n` slots occupies:

```python
import sys

for n in (0, 1, 2, 10, 100, 1000, 10_000):
    print(n, sys.getsizeof([None] * n))
# -> 0 56
# -> 1 64
# -> 2 72
# -> 10 136
# -> 100 856
# -> 1000 8056
# -> 10000 80056
```

Fifty-six bytes of fixed overhead, then exactly eight more bytes for every additional slot, with no
drift at any size. That perfectly uniform 8 is the stride. (What those eight bytes hold is section
2's subject; what matters here is that the number never varies, which is precisely what makes the
multiply valid.)

Since reaching slot `i` is a fixed amount of arithmetic, reaching it should cost the same regardless
of `i` and regardless of how many slots exist. It does:

```python
import timeit

setup = "readings = list(range(1_000_000))"
for pos in (10, 1_000, 100_000, 900_000):
    t = min(timeit.repeat(f"readings[{pos}]", setup, number=200_000, repeat=5))
    print(pos, round(t / 200_000 * 1e9, 1), "ns")
# -> 10 5.7 ns
# -> 1000 5.4 ns
# -> 100000 5.5 ns
# -> 900000 5.6 ns
```

Flat. Now compare it against the thing arrays let you avoid — actually looking for something,
which means starting at the front and checking slots until you find it. With the same
`readings = list(range(1_000_000))`, the value stored at index `pos` is `pos` itself, so
`readings.index(pos)` has to examine `pos + 1` slots before it can answer:

| position in a 1,000,000-element list | `readings[pos]` | `readings.index(pos)` |
|---|---|---|
| 10 | 6.0 ns | 0.07 µs |
| 1,000 | 5.5 ns | 5.5 µs |
| 100,000 | 5.5 ns | 567 µs |
| 900,000 | 5.6 ns | 5,393 µs |

The search column grows in proportion to how far in the target sits, at about 5.5 to 6 nanoseconds
per slot examined. The index column does not move. **Constant-time access to any position,
independent of position and of size, is the defining property of an array, and it is the reason
arrays sit underneath almost every other data structure you will ever use** — hash tables, heaps,
dynamic strings, and the buffers behind files and sockets are all arrays with bookkeeping bolted on.

### What contiguity buys beyond the jump

The address arithmetic is the famous benefit. It is not the only one.

Memory hardware does not deliver individual bytes; it delivers blocks, and it watches your access
pattern. Reading one slot pulls in the whole block surrounding it, so the reads of its immediate
neighbours are already paid for. And once the hardware notices you moving forward at a steady
stride, it starts fetching blocks *ahead* of you, so the data arrives before you ask for it. A
sequential walk through contiguous storage is the pattern memory systems are best at.

To measure what that is worth, take one list of five million slots and touch every slot exactly
once — first in index order, then in a shuffled order. Identical work, identical number of reads,
only the order differs.

One trap has to be disarmed before that measurement means anything. The loop is driven by a list
of indexes, and pulling each index out of that list means following a pointer to an integer object.
Shuffle the index list and those integers get visited in scattered order too — so the driver is
penalised right alongside the reads you are trying to measure. The penalty is not small: a
driver-only loop that touches no slot of `data` at all costs 92 ms over the shuffled indexes
against 17 ms over the ordered ones. Rebuilding each index as a freshly allocated object with
`i + 0` lays them back down in a contiguous run in the order its own list names them, and running
the driver by itself as a control column proves whether that worked.

```python
import random, time

N = 5_000_000
data = [0] * N
in_order = list(range(N))
scattered = in_order[:]
random.seed(7)
random.shuffle(scattered)

# Rebuild each index as a freshly allocated object, so that either list, walked
# front to back, reads index objects that were allocated back to back.
in_order = [i + 0 for i in in_order]
scattered = [i + 0 for i in scattered]

def timed(order, read):
    best = float("inf")
    for _ in range(5):
        t0 = time.perf_counter()
        if read:
            for i in order:
                data[i]
        else:
            for i in order:
                i
        best = min(best, time.perf_counter() - t0)
    return best

for name, order in (("in order ", in_order), ("scattered", scattered)):
    full = timed(order, read=True)
    driver = timed(order, read=False)
    print(name, round(full * 1e3), round(driver * 1e3), round((full - driver) * 1e3))
# -> in order  27 17 10
# -> scattered 134 16 118
```

Read the middle column first. It is the same loop with `data[i]` deleted, and it costs 16–17 ms
whichever order the indexes are in. **That equality is the entire value of the control: it says
both walks pay the same price to produce their indexes, so every millisecond of difference in the
first column is a difference in the reads.** Subtract it and the reads alone come to 10 ms in
order against 118 ms scattered.

Across five runs here the isolated read cost ranged from 8.6 to 11.2 ms in order and from 118 to
130 ms scattered — between 10.9 and 14.6 times slower, or roughly 1.9 nanoseconds per slot against
25. Nothing about the algorithm changed. Only the order of addresses did.

That 1.9 ns sits below the 5.5 ns measured earlier for a single indexing statement, and the gap is
the subtraction doing its job: the earlier figure timed a whole statement, this one has the loop's
own machinery taken off it and leaves little more than the subscript and the memory behind it.

What is being walked contiguously here is `data`'s own run of slots, forty megabytes of it.
Whether the things those slots refer to are themselves neighbours in memory is a separate question,
and section 2's.

So contiguity is worth having twice: once for the O(1) jump, and once again for every loop that
reads slots in the order they are stored.

### The cost of reserving space you will not use

The box has a downside, and it is the same downside in memory.

A box built to hold 1000 DVDs takes up the floor space of a box for 1000 DVDs even if you own
fifteen. The 985 empty slots are not free — they are occupying a corner of the room that nothing
else can use. And the room does not care that you *intend* to fill them eventually.

Memory works exactly this way. Reserving slots takes the bytes now, whether or not you put anything
meaningful in them:

```python
import sys

box = [None] * 1000
print(sys.getsizeof(box))    # -> 8056

for k in range(15):          # fill the fifteen you actually have
    box[k] = k
print(sys.getsizeof(box))    # -> 8056   unchanged
print(len(box))              # -> 1000   still a thousand positions
```

The reservation costs you time as well as bytes, and for the same reason: the 985 unused positions
are real slots holding a real value, so anything that walks the box walks all thousand of them.

```python
print(sum(1 for slot in box if slot is not None))   # -> 15
print(sum(1 for slot in box if slot is None))       # -> 985
```

Both of those passes did a thousand reads. One of them found fifteen things worth having.

At scale the reservation is visible from outside the process. Reserving ten million slots and
storing nothing in them raised this interpreter's peak resident memory from 14.7 MiB to 90.9 MiB —
a 76.3 MiB jump, matching the 80,000,056 bytes the list reports for itself. That memory is
unavailable to every other program on the machine for as long as you hold it.

The trade runs both ways, which is why sizing is a real decision and not a free one. Reserve too
little and you will have to move to a bigger box later, copying everything you own into it. Reserve
too much and you pay rent on emptiness. Sections 7 and 8 are about how Python resolves that trade on
your behalf, and what it costs when it does.

### What Python gives you for this job

The container is the **list**. Square brackets to write it, `nums[i]` to index it, and it delivers
the property this section has been building toward: one run of uniformly sized, contiguous slots,
with the address of slot `i` computed rather than searched for.

```python
rgb = [255, 128, 0]
print(rgb[1])                # -> 128
rgb[1] = 64
print(rgb)                   # -> [255, 64, 0]
```

Two things make it more than the box. Its length is not fixed at creation — add to it and it
arranges for a bigger run of storage without telling you. And the stride stays eight bytes whatever
you store, which is how one list can hold a float, a string, and another list at once without the
arithmetic breaking:

```python
import sys

mixed = [3.5, "hello", [1, 2], None, print]
print(len(mixed))            # -> 5
print(sys.getsizeof(mixed))  # -> 96     56 + 5 * 8, the size of any five-slot list
print(mixed[2])              # -> [1, 2]
```

Five wildly different things, and the box still measures 56 + 5 × 8. Nothing about the address of
slot 2 depended on what slots 0 and 1 turned out to be holding.

### The one rule Python does not enforce

Go back to the box's first constraint, because that mixed list has just walked straight through it.
"The box holds one kind of thing" was doing two jobs at once. One was physical: same-shaped items
give you a measurable stride, which is what makes `base + i * stride` valid. The other was logical:
everything in the box is a DVD, so everything in the box answers to the same operations.

**Python keeps the physical half and hands you the logical half to look after yourself.** The
stride is eight bytes no matter what you store, so the arithmetic never needed you to declare a
type, and nothing stops you mixing. But the expectation the box encoded has not gone away. It has
moved to the point of use:

```python
readings = [12, 7, "n/a", 19]     # the list accepts this without complaint
print(len(readings))              # -> 4

try:
    sorted(readings)
except TypeError as e:
    print(e)    # -> '<' not supported between instances of 'str' and 'int'

try:
    sum(readings)
except TypeError as e:
    print(e)    # -> unsupported operand type(s) for +: 'int' and 'str'
```

Storing the string cost nothing and raised nothing. The bill arrives later, at the first operation
that assumed a shared shape, and the message names two types rather than a position — by then the
list has no idea which slot started the trouble.

So homogeneity becomes your discipline rather than the language's rule, and the way you write that
discipline down is an annotation:

```python
def average(nums: list[int]) -> float:
    return sum(nums) / len(nums)

print(average.__annotations__["nums"])   # -> list[int]
print(average([1.5, 2.5]))               # -> 2.0   annotated int, given floats, runs anyway
```

`list[int]` is a claim addressed to the next person reading the function, and to any checker you
choose to run over it. The interpreter records the claim and declines to act on it. Section 10 has
the container that does act on it — `array.array`, where a typecode fixes what may go in and the
type is a hard constraint rather than a hint, which is the box's rule genuinely implemented.

The rule's other half survives untouched, and it is the half you will use daily: items of one type
share properties. A list whose slots all hold records of the same shape — tuples with the same
fields in the same order, dicts with the same keys, instances of one dataclass — is the box of DVDs
you will actually write, and every loop over it can rely on each slot answering the same questions.

Both of the freedoms above — a length that is not fixed at creation, and a stride that holds at
eight bytes regardless — follow from what a list is made of. That is section 2.


---

## 2. What a Python list actually is

A list is two allocations, not one. There is a small fixed-size header — the thing whose address
`id()` reports — and, somewhere else on the heap entirely, a separately allocated contiguous block
of machine-word slots. The header never changes size, and never changes address for the life of the
list. The block is reallocated as the list grows.

### The header, field by field

CPython's `list` is a C struct with five fields. You can read them directly, because `id()` on a
standard CPython build returns the object's actual address and `ctypes` will happily overlay a
struct on it. The language itself promises only that `id()` returns an integer that is unique and
constant for the object's lifetime; that it is the address is a CPython implementation detail, and
so is everything else in this section.

```python
import ctypes

class PyListObject(ctypes.Structure):
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),                 # reference count
        ("ob_type",   ctypes.c_void_p),                  # pointer to the `list` type object
        ("ob_size",   ctypes.c_ssize_t),                 # element count -- what len() reads
        ("ob_item",   ctypes.POINTER(ctypes.c_void_p)),  # pointer to the block of slots
        ("allocated", ctypes.c_ssize_t),                 # how many slots the block can hold
    ]

temps = [18, 21, 19]
raw = PyListObject.from_address(id(temps))

print(ctypes.sizeof(PyListObject))   # -> 40
print(raw.ob_size, len(temps))       # -> 3 3
print(raw.allocated)                 # -> 4
print(list.__basicsize__)            # -> 40
```

Five pointer-sized fields, 40 bytes, regardless of how many elements the list holds. Taking them one
at a time:

- `ob_refcnt` and `ob_type` are the two fields every Python object begins with: how many references
  currently point at this object, and what type it is. Nothing list-specific.
- `ob_size` is the element count, stored as a plain integer in the header. This is what `len()`
  reads. It is a field load, not a traversal — `len()` on a ten-million-element list does the same
  work as `len()` on an empty one, and it is always exact.
- `ob_item` is the address of the element block. It is a pointer, which is the whole reason the
  block can move without the list object moving.
- `allocated` is how many slots the block can hold. It is at least `ob_size` and often more; the gap
  between the two is spare capacity waiting to be filled.

That gap is why `allocated` reads 4 for a three-element list. `[18, 21, 19]` never asks for exactly
three slots: because every element is a constant, the compiler stores them as one tuple and emits
"build an empty list, then extend it from this tuple", and the extend path rounds the request up so
the next append is free. Build the same three elements a way that names the length in advance and
you get an exact fit:

```python
dawn, noon, dusk = 18, 21, 19
print(PyListObject.from_address(id([dawn, noon, dusk])).allocated)  # -> 3
print(PyListObject.from_address(id([0] * 3)).allocated)             # -> 3
print(PyListObject.from_address(id(list(range(1000)))).allocated)   # -> 1000
```

A literal with non-constant elements pushes the three values and builds a list of exactly that size.
Repetition and `list(...)` over a sized iterable both know the final length up front and allocate
precisely that. Growth by appending is the case that cannot know, and section 7 is about the policy
it uses instead.

The practical reading: `allocated` is an implementation-chosen number and `ob_size` is the one that
means something. `len()` is the supported way to ask for `ob_size`; no expression in the language
reports `allocated` at all, which is why the rest of this chapter reads it straight out of the
struct whenever capacity is the question.

The claim that the header and the block are separate allocations is directly checkable: force the
block to be reallocated and watch the header address stay exactly where it was.

```python
def block_address(lst):
    raw = PyListObject.from_address(id(lst))
    return ctypes.cast(raw.ob_item, ctypes.c_void_p).value

readings = [1, 2, 3]
header_before, block_before = id(readings), block_address(readings)
readings.extend(range(1000))

print(id(readings) == header_before)              # -> True
print(block_address(readings) == block_before)    # -> False
print(len(readings))                              # -> 1003
```

Every name bound to `readings` kept working across a reallocation that moved a thousand elements to
a new address, because none of those names ever pointed at the elements. They point at the header,
and the header is what got updated.

### Which build these numbers come from

Everything above is specific to CPython, and it is specific to one *build* of CPython. There are two
supported ones as of 3.14: the long-standing build with the global interpreter lock, and the
free-threaded build, which removes it — 3.14 is the first release where free-threading is a fully
supported configuration rather than an experiment. The two do not share an object header. Ask which
one you are on before trusting any byte count:

```python
import sys, sysconfig

print(sys._is_gil_enabled())                         # -> True
print(sysconfig.get_config_var("Py_GIL_DISABLED"))   # -> 0
print(list.__basicsize__)                            # -> 40
```

`True` and `0` say the lock is present, and every number in this chapter was measured on that build.
On the free-threaded build those same three lines print `False`, `1` and `56`. The header is larger
there because `ob_refcnt` is not a single field: a reference count that only the owning thread
touches can be updated without an atomic instruction, so the count is split into a thread-local part
and a shared part, sitting alongside a thread id, a per-object mutex and a byte of flags. The
five-field overlay above would misread every one of them. What survives unchanged is the tail —
`ob_size`, `ob_item` and `allocated` are still the last three words of the header on both builds.

What that does to the numbers is narrower than you would expect. Measured on both, the list side is
identical and the element side is not:

| | lock build | free-threaded build |
|---|---:|---:|
| `list.__basicsize__` | 40 | 56 |
| `sys.getsizeof([])` | 56 | 56 |
| `sys.getsizeof([0] * 1000)` | 8056 | 8056 |
| `sys.getsizeof(0)` | 28 | 44 |

An empty list costs 56 bytes either way, for two different reasons: on the lock build that is a
40-byte struct plus a 16-byte collector header, and on the free-threaded build it is a 56-byte
struct with the collector's bookkeeping folded into it. So the `56 + 8n` arithmetic derived below
holds on both. Every figure that counts the *objects behind* the pointers moves, though, because an
`int` went from 28 bytes to 44.

One behaviour worth knowing, since the header changed underneath it: eight threads each appending
200,000 items to one shared list finish with exactly 1,600,000 elements on both builds. A single
`append` is indivisible either way. The lock build gets that from the interpreter lock; the
free-threaded build gets it from a lock the list carries itself.

### Reading capacity directly

`allocated` is the only direct instrument for capacity in this chapter, so it deserves a name rather
than a fresh `ctypes` incantation each time. It is always the last word of the header, on either
build, which makes a one-line reader that needs no struct definition and no build check:

```python
import ctypes

def allocated(lst: list) -> int:
    """Capacity: how many slots this list's block can hold. CPython-specific."""
    return ctypes.c_ssize_t.from_address(id(lst) + list.__basicsize__ - 8).value

print(allocated([]), allocated([0] * 3), allocated(list(range(1000))))   # -> 0 3 1000

caps, lst = [], []
for i in range(20):
    lst.append(i)
    caps.append(allocated(lst))
print(caps)   # -> [4, 4, 4, 4, 8, 8, 8, 8, 16, 16, 16, 16, 16, 16, 16, 16, 24, 24, 24, 24]
```

**`allocated(lst)` is the ground truth; the arithmetic `(sys.getsizeof(lst) - 56) // 8` used
elsewhere is a proxy derived from it.** The proxy is not an independent measurement — a list
computes its own `sys.getsizeof` answer *from* `allocated`, adding the header size to eight bytes
per allocated slot. That is why the two can never disagree:

```python
import sys

EMPTY = sys.getsizeof([])
lst, mismatches = [], 0
for i in range(200_000):
    lst.append(i)
    if allocated(lst) != (sys.getsizeof(lst) - EMPTY) // 8:
        mismatches += 1
print(EMPTY, mismatches)   # -> 56 0
```

Zero disagreements across 200,000 appends, and zero on the free-threaded build too. Use the proxy
when you would rather not import `ctypes`; use `allocated` when capacity *is* the question, because
it reads the field instead of inferring it.

### A list is a GC-tracked container

`sys.getsizeof([])` reports 56, not the 40 the struct occupies. The extra 16 bytes are the
garbage-collector header: two pointer-sized fields that sit immediately *before* every GC-tracked
object and thread it into a doubly linked list the collector can walk.

```python
import gc, sys

print(sys.getsizeof([]), list.__basicsize__)   # -> 56 40
print(gc.is_tracked([]))                       # -> True
print(gc.is_tracked(7))                        # -> False
```

Reference counting alone reclaims an object the moment its count hits zero, and for an integer that
is enough — an integer cannot refer to anything, so it cannot participate in a cycle. A list can
refer to anything, including itself:

```python
log = ["start"]
log.append(log)

print(log[1] is log)   # -> True
print(len(log))        # -> 2
```

Delete the name `log` and the list's reference count drops to one, not zero, because the list is
still holding a reference to itself from inside its own element block. Nothing else can reach it and
nothing will ever decrement that last count. The cyclic collector exists to find exactly this, and
it can only find it if it knows the object is there and knows how to walk its slots — which is what
being tracked means. The 16 bytes are what you pay for it, once per list, no matter the length.

Tracking is a property of the object, not just the type: a tuple of immutable contents gets
untracked at the first collection that notices it can never be part of a cycle. Lists are mutable,
so no such reasoning is ever available and a list stays tracked for its whole life.

### When the collector runs, and what it costs

The 16 bytes are the standing cost of being tracked. The recurring cost is the scanning, and to
predict that you need to know what starts a scan. It is not a timer, and it is not memory pressure.
**Allocating a tracked object is what triggers a collection, so the collector's cost scales with how
many containers you create — not with how many cycles you have.**

CPython keeps a counter that rises by one each time a tracked object is created and falls by one
each time a tracked object is freed. When the net figure crosses a threshold, a scan runs and the
counter resets. The thresholds are readable, and so is the counter:

```python
import gc

print(gc.get_threshold())   # -> (2000, 10, 0)

gc.collect()
before = gc.get_count()[0]
keep = [[] for _ in range(1500)]
print(gc.get_count()[0] - before)   # -> 1501

before = gc.get_count()[0]
values = [i * 1.5 for i in range(1500)]
print(gc.get_count()[0] - before)   # -> 1
```

Fifteen hundred lists moved the counter by 1501 — one per list, plus the list holding them. Fifteen
hundred floats moved it by 1, the one being the list they went into. The first threshold is 2000, so
another five hundred lists would have set a scan going and five hundred more floats would not.
Nothing about the *contents* of those containers entered into it, only that they exist and are
tracked.

Newly created objects are the young generation. A scan walks them, follows the slots of every
tracked object it reaches, and looks for groups whose reference counts are entirely explained by
references from inside the group — a group nothing outside can reach, which is exactly the
self-referential `log` above. Whatever survives is promoted to an older generation that is examined
far less often, and in increments rather than all at once, so a large body of long-lived data does
not make each young scan proportionally worse: building 200,000 lists took 3.1 ms with two million
tracked objects already alive and 4.7 ms with none, the difference being allocator warmth rather
than collector work.

Because allocation drives the counter, the scan happens whether or not there is anything to find:

```python
import gc

runs = []
gc.callbacks.append(lambda phase, info: runs.append(info) if phase == "stop" else None)

gc.collect(); runs.clear()
containers = [[] for _ in range(100_000)]     # 100,000 tracked objects
print(len(runs), sum(r["collected"] for r in runs))   # -> 50 0

gc.collect(); runs.clear()
numbers = [i * 1.5 for i in range(100_000)]   # 100,000 untracked floats
print(len(runs), sum(r["collected"] for r in runs))   # -> 0 0
```

Fifty scans for the lists — 100,000 divided by the 2000 threshold — and every one of them reclaimed
nothing, because empty lists form no cycles. The floats triggered no scan at all, because a `float`
cannot refer to anything and is therefore untracked and invisible to the counter. Same object count,
same loop, two entirely different collector bills. In time:

```python
import gc, time

def best(make, gc_on, reps=7):
    out = float("inf")
    for _ in range(reps):
        gc.enable() if gc_on else gc.disable()
        gc.collect()
        t0 = time.perf_counter()
        result = make()
        out = min(out, time.perf_counter() - t0)
        del result
    gc.enable()
    return out * 1000

tracked = lambda: [[] for _ in range(200_000)]         # 200,000 tracked containers
untracked = lambda: [i * 1.5 for i in range(200_000)]  # 200,000 untracked floats

print(round(best(tracked, True), 2), round(best(tracked, False), 2))      # -> 6.06 2.97
print(round(best(untracked, True), 2), round(best(untracked, False), 2))  # -> 3.16 3.05
```

Building tracked containers costs about twice as much with the collector enabled; building the same
number of untracked objects costs the same either way. The absolute milliseconds belong to this
machine, but the shape held across every run: 2.0x for the containers in a fresh process, rising to
2.7x when the process was already holding a few million tracked objects from earlier examples, and
1.0x for the floats throughout.

That ratio has a direct consequence for measurement. Timing tools routinely disable the cyclic
collector for the duration of a timed region so that results repeat, which means an allocation-heavy
loop gets quoted at its collector-free speed and then runs at the other one in your program. Section
11 shows the disabling happening and what to do about it; the reason it matters is this subsection.

### The slots hold addresses, not values

`ob_item` points at the element block. Each slot in that block is one 8-byte pointer on a 64-bit
build. The slot does not contain your object; it contains the object's address, and the object
itself lives wherever the allocator put it. Continuing the session above:

```python
slots = [raw.ob_item[i] for i in range(raw.ob_size)]

print(slots == [id(x) for x in temps])                                # -> True
print(ctypes.cast(raw.ob_item, ctypes.c_void_p).value == id(temps))   # -> False
```

The slots hold exactly the numbers `id()` reports, and the block lives at a different address from
the header. You can see the same thing without `ctypes`: building a list never copies the object you
put in it.

```python
reading = 1299
prices = [reading, 2450, 899]

print(prices[0] is reading)   # -> True

base = block_address(prices)
inside_block = range(base, base + 8 * len(prices))
print([id(x) in inside_block for x in prices])   # -> [False, False, False]

print([id(x) for x in prices])   # one run: [4459636176, 4459636112, 4459636144]
```

`prices[0] is reading` is the whole argument in one line: the list stored the object you handed it,
not a copy of it. The second check makes the geometry explicit — the block occupies 24 bytes
starting at `base`, and not one of the three integers lives inside that range. The block holds three
addresses; the objects are elsewhere.

The addresses in the last line come from one run and change every run, so do not expect to
reproduce them. What is worth noticing is that they are in no particular relation to slot order:
position 0 happens to hold the highest of the three. The pointers in the block are contiguous by
construction, always. Where they point was decided by the allocator, in some cases before the list
existed, and the list never had a say in it. How far apart those targets drift is measured below,
under what the indirection costs.

### Memory accounting, measured

The block is exactly 8 bytes per slot, so a list with an exactly-sized block costs `56 + 8n`.
`[0] * n` allocates exactly `n` slots, which makes the arithmetic checkable:

```python
import sys

for n in (0, 1, 10, 100, 1000, 10_000):
    print(n, sys.getsizeof([0] * n), 56 + 8 * n)
```

| `n` | `sys.getsizeof([0] * n)` | `56 + 8n` |
|---|---|---|
| 0 | 56 | 56 |
| 1 | 64 | 64 |
| 10 | 136 | 136 |
| 100 | 856 | 856 |
| 1000 | 8056 | 8056 |
| 10000 | 80056 | 80056 |

**`sys.getsizeof` stops at the pointer block — it never follows a pointer, so the objects your list
actually holds are not in that number.** A list holding one enormous integer reports the same size
as a list holding one small one:

```python
big = 10 ** 5000

print(sys.getsizeof(big))     # -> 2240
print(sys.getsizeof([big]))   # -> 64
```

64 bytes for a container whose single element is 2240 bytes. To get the real figure you have to walk
the elements yourself, deduplicating by identity so shared objects are counted once:

```python
def deep_size(lst):
    """Shallow size plus the shallow size of each distinct element. One level only."""
    seen = set()
    total = sys.getsizeof(lst)
    for x in lst:
        if id(x) not in seen:
            seen.add(id(x))
            total += sys.getsizeof(x)
    return total

nums = list(range(1000))
print(sys.getsizeof(nums), deep_size(nums))    # -> 8056 36056

zeros = [0] * 1000
print(sys.getsizeof(zeros), deep_size(zeros))  # -> 8056 8084
```

Both lists have identical shallow size, and their real costs differ by a factor of 4.5. `nums` holds
1000 distinct `int` objects at 28 bytes each: 8056 + 28000 = 36056. `zeros` holds the same address
1000 times, so there is one 28-byte object behind all of it: 8056 + 28 = 8084. Scaled up, a
million-element list of distinct integers is 8,000,056 bytes of pointers and 36,000,056 bytes in
total — 36 MB where the pointer block alone suggested 8.

`deep_size` is deliberately one level deep. Point it at a list of lists and it will count 56 bytes
plus slots for each inner list and stop there, missing everything inside them; a fully general
version has to recurse, and has to decide what to do about the objects a container reaches through
attributes rather than elements. The one-level version is enough to make the point here — that the
shallow number can be off by any factor you like. Section 11 carries the recursive version, along
with the two cautions that only bite once you are measuring nested structures for real.

### What the indirection costs

Footprint is the first bill, and you just measured it: 36 bytes per integer, of which 8 are the slot
and 28 are the object.

Locality is the second, and it is the one that shows up as wall-clock time. Walking a list streams
one contiguous stretch of pointers, which the CPU prefetches perfectly — and then dereferences each
pointer to an address that may be anywhere. You can isolate that effect exactly, because two lists
containing *the same objects in a different order* differ in nothing except the order in which
memory gets touched. First, measure how far apart "anywhere" is:

```python
import random, statistics

ordered = list(range(1_000_000))
shuffled = ordered[:]
random.seed(0)
random.shuffle(shuffled)

def strides(lst, n=20_000):
    """Byte distances between the objects behind neighbouring slots."""
    return [abs(id(b) - id(a)) for a, b in zip(lst[:n], lst[1:n + 1])]

near, far = strides(ordered), strides(shuffled)

print(int(statistics.median(near)))                        # -> 32
print(round(sum(d <= 64 for d in near) / len(near), 3))    # -> 0.996
print(round(statistics.median(far) / 2 ** 20))             # -> 9   (megabytes)
print(round(sum(d <= 64 for d in far) / len(far), 3))      # -> 0.0
```

Neighbouring slots of `ordered` lead to objects a median of 32 bytes apart — the allocator's size
class for a 28-byte `int` — and 99.6% of consecutive pairs land within 64 bytes of each other, which
is one cache line. The hardware fetches the next element while it is still working on the current
one. Adjacent slots of `shuffled` lead to objects a median of about 9 MB apart, and *no* consecutive
pair is within a cache line: 0.0, not a small fraction. Every step is a different page. The megabyte
figure drifts between runs and the exact size class depends on what the process allocated before the
list; the two proportions, 0.996 against 0.0, are what reproduce. Now time the identical arithmetic
over each, continuing the same session:

```python
import time

def best(f, reps=9):
    times = []
    for _ in range(reps):
        start = time.perf_counter()
        f()
        times.append(time.perf_counter() - start)
    return min(times)

t_ordered = best(lambda: sum(ordered))
t_shuffled = best(lambda: sum(shuffled))

print(round(t_ordered, 4), round(t_shuffled, 4))   # -> e.g. 0.0023 0.0139, machine-dependent
print(round(t_shuffled / t_ordered, 1))            # -> e.g. 6.1
```

Same objects, same element count, same additions, same 8,000,056-byte pointer block. The absolute
timings belong to whatever machine you run them on; the ratio is the finding, and across runs here
it stayed between 5x and 9x. Nothing about the complexity changed — both are one linear pass adding
a million integers. Every pointer dereference just became a cache miss. This is a large part of why
a Python-level loop carries a heavy constant factor even when its complexity class is optimal, and
why "O(n) so it will be fine" is a claim about growth, not about speed.

### What the indirection buys

A slot is a generic pointer, so it can point at anything. Heterogeneity therefore needs no ceremony
at all — no wrapper type, no declaration, no conversion on the way out:

```python
import sys

mixed = [1, "two", [3], None]

print(sys.getsizeof(mixed))               # -> 88
print([sys.getsizeof(x) for x in mixed])  # -> [28, 44, 64, 16]
```

The list costs `56 + 8 * 4 = 88` bytes and the four objects behind it have shallow sizes of 28, 44,
64 and 16 — an integer, a string, another list, and the `None` singleton. The container neither
knows nor cares which is which; it is holding four addresses of identical width. Retrieving one
costs the same for every element, and a wrongly-typed element is caught at the point of use, not at
the point of storage — which is the tradeoff, not a free lunch.

The second benefit is that storing an object costs the same no matter how large it is. Putting that
2240-byte integer into a list copies 8 bytes. Putting a one-megabyte string into a list copies 8
bytes. Storage is O(1) in the size of the value, always, because only the address moves. The same
fact makes `shuffled = ordered[:]` cheap in a way that is easy to under-appreciate: it copies eight
million bytes of pointers and zero bytes of integers, and afterwards both lists point at exactly the
same million objects.

### Small integers are shared, and `is` is not `==`

CPython preallocates the `int` objects from -5 to 256 at startup and hands out the same object every
time one of those values is produced. Above and below that window, arithmetic allocates a fresh
object each time.

```python
z = 0
a, b = z + 256, z + 256
print(a is b, a == b)   # -> True True

c, d = z + 257, z + 257
print(c is d, c == d)   # -> False True

e, f = z - 5, z - 5
g, h = z - 6, z - 6
print(e is f, g is h)   # -> True False
```

The values are computed at run time here on purpose; write them as literals and the compiler folds
and deduplicates the constants, which hides the effect behind a different mechanism entirely. You do
not have to take the window's boundaries on faith — measure them:

```python
def computed(v):
    return (v + 1) - 1     # forces a fresh object unless the value is cached

shared = [v for v in range(-20, 400) if computed(v) is computed(v)]
print(min(shared), max(shared), len(shared))   # -> -5 256 262
print(shared == list(range(-5, 257)))          # -> True
```

One contiguous window, 262 values, no gaps. It is a caching detail with no semantic content: the
values are the same either way, and nothing about your program's meaning depends on which side of
256 a number falls.

**`is` compares the addresses in the slots; `==` compares the objects those addresses lead to.** The
-5 to 256 window makes `is` accidentally correct on small numbers, so a comparison written with the
wrong operator survives every test that uses small numbers and fails the first time a value reaches
257. Use `is` only for `None`, for `True`/`False`, and when you genuinely mean "the same object" —
which, for a list, is exactly the question section 9 is about.

There is one place the two operators are not yours to choose between, because the container does the
choosing. **List equality and membership compare identity first and only fall through to `==` when
the addresses differ**, so an element is always considered to match itself no matter what its `==`
says. The float `nan` is the value that makes this visible, since it is defined to be unequal to
everything including itself:

```python
missing = float("nan")
readings = [12.5, missing, 13.1]

print(missing == missing)          # -> False
print(missing in readings)         # -> True
print(readings == readings[:])     # -> True
print(readings.index(missing), readings.count(missing))   # -> 1 1
```

A value that is not equal to itself is still found in a list that holds it, still counted once, and
still removable by `remove`. You can watch the short-circuit rather than infer it, by counting how
often `__eq__` is actually reached:

```python
calls = 0

class Sensor:
    def __eq__(self, other):
        global calls
        calls += 1
        return False

s = Sensor()
print(s == s, calls)          # -> False 1

calls = 0
print(s in [s], calls)        # -> True 0

calls = 0
print([s] == [s], calls)      # -> True 0

calls = 0
print([s] == [Sensor()], calls)   # -> False 1
```

`s == s` runs `__eq__` and honours its `False`. `s in [s]` never runs it, because the identity check
answered first. This is the same rule the hash-based containers apply once a hash has matched, which
is why `missing in {missing}` is `True` while `missing in {float("nan")}` is `False` — two objects,
two addresses, and `==` given the final word only in the second case. So when section 8 describes
set matching as `hash` then `==`, read it as `hash`, then identity, then `==`: the middle step is
invisible until a value declines to equal itself.


---

## 3. Creating lists

Many constructs bring a list into existence, and the ones worth knowing differ in what they
allocate, not only in how they read. Every one of them ends in the same place — a header and a
block of slots — but reaches it by one of three routes: allocate the exact length, allocate a
length rounded up, or grow the block as the elements arrive. Which route a construct takes is a
property of the construct, not of what you hand it, and it is measurable.

### The literal

```python
empty = []
temps = [18, 21, 19]
print(len(temps))               # -> 3
```

`[]` compiles to a single `BUILD_LIST 0` opcode. `list()` compiles to a name lookup plus a call —
the name is resolved at run time, on every construction — and costs about twice as much: 9.96 ns
against 19.53 ns per construction, measured over two million iterations each. Both produce a
56-byte object with zero slots. Write `[]`.

What a literal allocates depends on whether its elements are constants. A literal of names,
`[a, b, c]`, emits `BUILD_LIST 3` and allocates exactly three slots. Three or more constants are
folded by the compiler into a single constant tuple, loaded whole, and unpacked with `LIST_EXTEND`,
which allocates four. Two or fewer constants stay a plain `BUILD_LIST`:

```python
import sys

print(sys.getsizeof([1, 2]))        # -> 72    56 + 2 slots, from BUILD_LIST 2
print(sys.getsizeof([1, 2, 3]))     # -> 88    56 + 4 slots, from LIST_EXTEND
```

That extra slot is not waste in any meaningful sense — it is the allocator's granularity, and you
will see it again in a moment.

### `list(iterable)`

`list(x)` walks `x` and builds a fresh list of pointers to whatever it yields. When `x` reports its
own length — a `range`, a `str`, a `tuple`, another `list`, a `set`, a `dict`, a `dict` view — the
constructor asks first and allocates the whole block once.

```python
import sys

print(sys.getsizeof(list(range(1000))))     # -> 8056
print(list("abc"))                          # -> ['a', 'b', 'c']
print(sys.getsizeof(list("abc")))           # -> 88
```

8056 bytes is 56 bytes of list header plus 1000 pointer slots of 8 bytes each. Not one slot of
slack. When the length is odd the constructor rounds up to the next even count — 999 items get
1000 slots, and the three characters of `"abc"` get four — because the allocator's granularity is
16 bytes on this platform, and a half-used 16-byte chunk buys nothing.

An iterable that cannot report a length gets no such treatment. A generator expression has neither
`__len__` nor a length hint, so `list()` falls back to growing the block as it goes:

```python
import sys

def slots(lst):
    return (sys.getsizeof(lst) - 56) // 8

print(slots(list(range(99))))               # -> 100
print(slots(list(x for x in range(99))))    # -> 108
```

The same 99 elements, eight slots apart. The sized form asked and got it right; the unsized form
guessed its way up.

### Repetition

```python
zeros = [0] * 1000
blank = [None] * 8
```

Repetition knows the result length by arithmetic, so it allocates exactly `n` slots — including for
odd `n`, where it does not round up — and then fills every one of them with the *same pointer*.

```python
zeros = [0] * 1000
print(len({id(x) for x in zeros}))          # -> 1
print(zeros[0] is zeros[999])               # -> True
```

One `int` object, one thousand references to it. That is why repetition is the cheapest way to
reach a given length: 0.74 µs for `[0] * 1000`, against 6.12 µs for `list(range(1000))`, which has
to build fresh `int` objects for most of what it yields. Not for all of them — the small integers
are shared, as section 2 covered, so the first 257 values come out of that cache and only the
remaining 743 are freshly built:

```python
a = list(range(1000))
b = list(range(1000))
print(sum(x is y for x, y in zip(a, b)))    # -> 257
```

The count is a multiplier and is taken literally. Zero or less produces an empty list rather than
an error:

```python
print([0] * 0)      # -> []
print([0] * -3)     # -> []
```

A non-integer count is an error: `[0] * 2.0` raises `TypeError: can't multiply sequence by non-int
of type 'float'`. The zero case matters in practice — `[None] * n`, where `n` came out of a
computation and turned out to be 0, hands you an empty list to append to rather than a crash.

### The comprehension

```python
temps = [18, 21, 19]
doubled = [t * 2 for t in temps]
print(doubled)                  # -> [36, 42, 38]
```

A comprehension has no length to consult in advance — the iterable may be a generator, and the `if`
clause may drop items — so it grows the list as it goes, exactly as a loop of `append` would. It
gets no preallocation even when the source obviously has one to give: the growth path is chosen by
the construct, not by the argument.

The loop variable belongs to the comprehension, not to the code around it. It is compiled with its
own storage and the outer binding is restored afterwards, so a comprehension can reuse a name you
are already using without destroying it:

```python
t = "outer"
doubled = [t * 2 for t in range(3)]
print(doubled)                  # -> [0, 2, 4]
print(t)                        # -> outer
```

Inside the comprehension `t` is the loop value; outside it is still the string. That containment is
what makes the comprehension safe to drop into the middle of a function, and it is also what makes
the fix later in this section work.

### From an existing list

`list(x)`, `x.copy()`, `x[:]`, and `copy.copy(x)` all produce a new list of length `len(x)` holding
the same pointers, and all four cost the same to within noise: 0.12, 0.11, 0.11, and 0.14 µs
respectively for a 100-element list.

They do not all allocate the same block. `x.copy()`, `x[:]`, and `copy.copy(x)` take a slicing path
that allocates exactly `len(x)` slots. `list(x)` takes the constructor path from above, which
rounds an odd length up to the next even one:

```python
import copy, sys

def slots(lst):
    return (sys.getsizeof(lst) - 56) // 8

src = [0] * 99
print(slots(src))                   # -> 99
print(slots(list(src)))             # -> 100
print(slots(src.copy()))            # -> 99
print(slots(src[:]))                # -> 99
print(slots(copy.copy(src)))        # -> 99
```

One slot, eight bytes, and only on an odd length. It is not a reason to prefer one of them; it is a
reason not to assume they are the same call underneath. Choose on readability: `x.copy()` says what
it does, `x[:]` is terser and older, `list(x)` is the one to reach for when `x` might not be a list
in the first place.

### Merging: `a + b` and `[*a, *b]`

Two constructs build one list out of several. They produce equal results and take different routes
to get there.

```python
a = [18, 21, 19]
b = [22, 20]

print(a + b)            # -> [18, 21, 19, 22, 20]
print([*a, *b])         # -> [18, 21, 19, 22, 20]
```

`a + b` adds the two lengths, allocates that many slots once, and copies both pointer blocks in.
`[*a, *b]` compiles to `BUILD_LIST 0` followed by one `LIST_EXTEND` per starred item — an empty
list, extended twice. So its final block is the product of a growth step and carries the slack a
growth step leaves:

```python
import sys

def slots(lst):
    return (sys.getsizeof(lst) - 56) // 8

a = [18, 21, 19]
b = [22, 20]

print(slots(a + b))         # -> 5     exact: 3 + 2
print(slots([*a, *b]))      # -> 8     grown, and rounded up
```

Five elements in eight slots. The overshoot is proportionally largest when the lists are small and
disappears as they grow — at 500 plus 500 both forms report 1000 slots exactly. Three spare slots,
24 bytes, on a five-element merge is not a reason to choose between them. Two other differences
are.

**Unpacking accepts any iterable; `+` accepts only another list.**

```python
a = [18, 21, 19]

print([*a, *range(2), *'xy'])   # -> [18, 21, 19, 0, 1, 'x', 'y']
print([*a, 0, *a])              # -> [18, 21, 19, 0, 18, 21, 19]

a + range(2)    # TypeError: can only concatenate list (not "range") to list
```

The `[*a, 0, *a]` line is the part `+` has no spelling for at all: unpacking interleaves bare
elements with spread-out iterables inside one expression. That is what makes it the general form
for assembling a list out of pieces — a leading label, then the readings themselves, then a
trailing marker, in one literal.

The other difference is chaining. Each `+` produces a whole new list, so a four-way concatenation
builds and throws away two intermediates, copying the early elements four times over. Unpacking
extends one list four times and copies each element once. Merging four 10,000-element lists:

| Expression | Time |
|---|---|
| `a + b + c + d` | 151.04 µs |
| `[*a, *b, *c, *d]` | 65.56 µs |

For two lists the forms are within noise of each other — 0.22 µs against 0.25 µs for a pair of
hundred-element lists — because there is no intermediate to avoid. **Use `+` for two lists, and
unpacking for three or more, for anything that is not a list, or for anything that mixes single
elements with iterables.**

### Everything else that hands you a list

The three routes are not a property of the particular spellings above; they are a property of every
call that returns a list. Anything that can ask its source for a length allocates once, anything
that cannot grows. Ninety-nine elements arriving eight different ways:

```python
import sys

def slots(lst):
    return (sys.getsizeof(lst) - 56) // 8

src = [0] * 99
txt = ' '.join('x' for _ in range(99))

print(slots(src[:]))                # -> 99     exact
print(slots(src[:50] + src[50:]))   # -> 99     exact
print(slots(list(src)))             # -> 100    sized, rounded up
print(slots(sorted(src)))           # -> 100    sized, rounded up
print(slots([*src]))                # -> 100
print(slots([x for x in src]))      # -> 108    grown
print(slots(list(map(str, src))))   # -> 108    grown
print(slots(txt.split()))           # -> 112    grown
```

`sorted()` builds its result with the sized constructor path and then sorts in place, so it lands
where `list()` lands. `map` is a lazy iterator with no length to report, so `list(map(...))` grows
exactly as a comprehension does — which is one reason to write the comprehension, since it is the
same allocation for less indirection. `str.split()` does not know how many pieces it will find
until it has found them, so it grows too, and overshoots hardest of the three.

You do not need to memorise that list. You need the question it answers: *can this construct know
the length before it starts?* Everything else follows.

### Known length allocates exactly; growing does not

**When the length is known at construction time, the list is sized once, precisely; when it is
grown one element at a time, it carries slack.** Every form above at n = 1000, where the length is
even and the odd-length rounding does not apply:

| Expression | Bytes | Slots |
|---|---|---|
| `[0] * 1000` | 8056 | 1000 |
| `[None] * 1000` | 8056 | 1000 |
| `list(range(1000))` | 8056 | 1000 |
| `list(src)` / `src[:]` / `src.copy()` | 8056 | 1000 |
| `sorted(src)` | 8056 | 1000 |
| `a + b` (500 + 500) | 8056 | 1000 |
| `[*a, *b]` (500 + 500) | 8056 | 1000 |
| `[x for x in src]` | 8856 | 1100 |
| `list(x for x in src)` | 8856 | 1100 |
| `list(map(str, src))` | 8856 | 1100 |
| 1000 × `out.append(x)` | 8856 | 1100 |
| `txt.split()` (1000 pieces) | 8888 | 1104 |

The grown forms hold 100 slots — 800 bytes — that contain nothing you can reach. `len()` still
returns 1000 for all twelve. Section 7 explains where that 1100 comes from and why the overshoot is
what makes `append` cheap; take it here as a fact you have measured.

### When preallocating is worth it

Rarely, if the goal is speed. Building a 1000-element result three ways:

| Approach | Time |
|---|---|
| `[x * 2 for x in src]` | 12.71 µs |
| `out = []` then `out.append(x * 2)` | 15.18 µs |
| `out = [None] * n` then `out[i] = x * 2` | 19.63 µs |

The preallocated version is the *slowest*. It pays for the fill pass, then an `enumerate`, then a
full `STORE_SUBSCR` with a bounds check per element, where the comprehension emits a single
`LIST_APPEND` opcode. The comprehension wins on both counts: fastest, and clearest about intent.

Preallocate when you genuinely cannot produce elements in order — when you compute results into
scattered positions, or fill a fixed-size buffer from several passes, or need `out[i]` to be
assignable before you know what goes there. Preallocate for *shape*, not for speed.

### `[None] * n` creates n real elements

```python
buf = [None] * 5
print(len(buf))                 # -> 5
print(buf)                      # -> [None, None, None, None, None]
print(bool(buf))                # -> True
buf[5]                          # IndexError: list index out of range
```

This is a list of length five whose five elements each hold `None`. It is not five empty positions
waiting to be filled — **there is no such thing as an unoccupied slot you can observe**. `len()`
says 5, the list is truthy, and index 5 raises.

`None` is the honest placeholder precisely because it is a real object that means "nothing yet",
and because reading one back that you forgot to overwrite fails loudly the moment you use it:

```python
buf = [None] * 3
buf[0] + 1      # TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
```

A placeholder of `0` would have silently absorbed that addition and given you a wrong answer with
no traceback. Choose the placeholder that cannot be mistaken for a result.

### Repetition of a mutable element

Repetition stores the same pointer `n` times. When the repeated object is immutable that is
invisible and free. When it is mutable it is the single most common way to lose an afternoon.

```python
grid = [[0] * 3] * 2
print(grid)                     # -> [[0, 0, 0], [0, 0, 0]]

grid[0][0] = 9
print(grid)                     # -> [[9, 0, 0], [9, 0, 0]]
```

You wrote to row 0 and row 1 changed. Nothing magical happened. `[0] * 3` was evaluated **once**,
producing one list object; `* 2` then filled the outer list's two slots with two copies of the same
pointer. There is one inner list, referenced twice. Section 2's model says a slot holds an address,
and here both slots hold the same address:

```python
grid = [[0] * 3] * 2
print(grid[0] is grid[1])               # -> True
print(len({id(row) for row in grid}))   # -> 1
```

The comprehension form re-evaluates its expression on every iteration, so it builds a genuinely new
inner list each time:

```python
grid = [[0] * 3 for _ in range(2)]
grid[0][0] = 9
print(grid)                             # -> [[9, 0, 0], [0, 0, 0]]
print(grid[0] is grid[1])               # -> False
print(len({id(row) for row in grid}))   # -> 2
```

The inner `[0] * 3` is still repetition, and still correct: `0` is immutable, so sharing one pointer
to it three times is exactly what you want. Only the *outer* dimension needs the comprehension. The
rule is not "avoid `*`" — it is that **repetition is safe for immutable elements and wrong for
mutable ones.**

### One flat list instead of a list of rows

A grid does not have to be a list of lists. `R * C` cells fit in one list of length `R * C`, with
the cell at row `r` and column `c` living at index `r * C + c`. Section 1 argued that a single
contiguous block is what makes positional access fast; the flat layout is that argument applied to
two dimensions, and the comprehension form is not.

```python
import sys

R, C = 100, 100

nested = [[0] * C for _ in range(R)]
flat = [0] * (R * C)

print(sys.getsizeof(nested))                # -> 920      the outer list alone
print(sys.getsizeof(nested[0]))             # -> 856      and one of its 100 rows
print(sys.getsizeof(nested)
      + sum(sys.getsizeof(row) for row in nested))   # -> 86520
print(sys.getsizeof(flat))                  # -> 80056
```

The nested grid is 101 separate list objects: one outer block of 100 pointers, each aiming at a
56-byte header somewhere else on the heap, each of those aiming at its own block of 100 slots. The
flat grid is one object and one block. The 6464-byte difference is 64.64 bytes per row — a 56-byte
header plus the outer slot pointing at it — and it is a fixed tax per row, not per cell, so it
matters most when the rows are short. The outer list reading 920 rather than 856 is the same
comprehension overshoot from earlier in this section: 100 rows in 108 slots.

Reading and writing swap a subscript for arithmetic:

```python
R, C = 100, 100
nested = [[0] * C for _ in range(R)]
flat = [0] * (R * C)

r, c = 37, 42
nested[r][c] = 9
flat[r * C + c] = 9
print(nested[r][c], flat[r * C + c])    # -> 9 9
```

**Flattening trades per-cell cost for whole-grid cost, and it is the whole-grid side that wins.**
A single cell is *slower* flat — 13.57 ns against 6.17 ns to read, 12.66 against 6.49 to write —
because `nested[r][c]` is two subscripts executed in C while `flat[r * C + c]` is a multiply and an
add on `int` objects executed as bytecode, allocating a fresh `int` for the index every time it
lands outside the small-integer cache. Anything that touches the whole grid goes the other way,
because one block means one pass and no pointer chase:

| Operation | Nested | Flat |
|---|---|---|
| build, 100 × 100 | 14.97 µs | 6.54 µs |
| `sum` of all cells | 26.3 µs | 20.5 µs |
| `max` of all cells | 73.57 µs | 68.31 µs |
| count occurrences of a value | 11.88 µs | 10.10 µs |
| independent copy | 16.24 µs | 9.03 µs |
| extract one column | 1.01 µs | 0.14 µs |

The last two rows are the interesting ones. A flat grid's independent copy is `flat[:]` — the
shallow copy *is* a full copy, because there is no second level to share. There are no rows to
alias, so the trap that opened this subsection cannot occur in a flat layout at all, and
`copy.deepcopy` never enters the conversation. And a column is `flat[c::C]`, one strided slice
done in C, against a comprehension that walks every row object.

What you give up is everything that treated a row as an object. `len(grid[r])` becomes the constant
`C` you are carrying around; a row is `flat[r * C:(r + 1) * C]`, which is a copy rather than the
row itself, so writing to it changes nothing; and there is no per-row bounds check left:

```python
R, C = 3, 4
flat = list(range(R * C))
nested = [[r * C + c for c in range(C)] for r in range(R)]

print(flat[0 * C + 5])      # -> 5     column 5 of a 4-column grid, silently row 1
nested[0][5]                # IndexError: list index out of range

print(flat[1 * C + -1])     # -> 3     a negative column walks into the previous row
print(nested[1][-1])        # -> 7
```

That is the real price: the nested form validates the column for free on every access, and the
flat form validates nothing until `r * C + c` leaves the list entirely. Reach for flat when the
grid is large, the rows are short, the work is whole-grid rather than per-cell, or you want the
aliasing question to not exist. Reach for nested when you index cells one at a time in ordinary
code and want the second subscript to catch your mistakes.

### Deep copying

Every construction above that starts from an existing list — `list(x)`, `x.copy()`, `x[:]`,
`copy.copy(x)` — allocates a new pointer block and copies the pointers into it, which means
**a shallow copy duplicates the arrows, never the things the arrows aim at.** Section 5 prices that
against slicing and shows a write leaking through one; section 9 covers the case one step further
back, where no copy was made at all and a second name simply took hold of the same object.

What none of them do is duplicate the elements. When you need that, `copy.deepcopy` walks the whole
structure and rebuilds it, and a write into the copy stops at the boundary:

```python
import copy

readings = [[18, 19], [21, 22]]
deep = copy.deepcopy(readings)
deep[1][0] = -1
print(readings, deep)       # -> [[18, 19], [21, 22]] [[18, 19], [-1, 22]]
```

It keeps a memo of the objects it has already rebuilt, so the *shape* of the original survives:
something referenced twice is still referenced twice afterwards, and a structure that refers to
itself does not send the copy into infinite recursion.

```python
import copy

row = [1, 2]
grid = [row, row]               # one row object, two references

deep = copy.deepcopy(grid)
print(deep[0] is deep[1])       # -> True    still shared, but with each other
print(deep[0] is grid[0])       # -> False   and not with the original

cyclic = [1, 2]
cyclic.append(cyclic)
clone = copy.deepcopy(cyclic)
print(clone[2] is clone)        # -> True
print(len(clone))               # -> 3
```

It is not cheap. Copying a 100 × 10 grid of lists:

| Form | Time |
|---|---|
| `grid.copy()` | 0.11 µs |
| `list(grid)` | 0.12 µs |
| `copy.copy(grid)` | 0.14 µs |
| `[row[:] for row in grid]` | 3.25 µs |
| `copy.deepcopy(grid)` | 67.98 µs |

Roughly 600× the shallow copy, and 20× the hand-written one-level-deep copy. When you know the
structure is exactly two levels — a list of lists of numbers — `[row[:] for row in grid]` buys you
independent rows for a twentieth of the price. Know it before you use it, though: that expression
copies one level and one level only, so if a row itself holds lists you are back to sharing, one
layer down. Reach for `copy.deepcopy` when the nesting is arbitrary or the elements are not lists,
not as a reflex.

The cheapest deep copy is the one the layout made unnecessary. A grid held flat has no second
level to duplicate, so the whole question collapses back into `flat[:]` — 9.03 µs for the
100 × 100 grid above, against 407 µs to `copy.deepcopy` the nested version of the same data. That
is the strongest argument the flat layout has, and the reason to choose between the two shapes
when you build the structure rather than when you first need to copy it.


---

## 4. Reading and writing elements

Everything a list does decomposes into two operations: put an object at a numbered position, and
get the object back out. Each one resolves the index, checks it against the length, and steps that
many slots into a contiguous block. The work does not depend on which position you name or how many
positions there are, which is why both are O(1) on a four-element list and on a four-million-element
list alike.

### Writing overwrites one slot

`nums[i] = value` assigns to a *position*, not to a name.

```python
temps = [18, 21, 19]
old = temps[1]
slot_before = id(temps[1])

temps[1] = 25

print(temps)                        # -> [18, 25, 19]
print(id(temps[1]) == slot_before)  # -> False
print(old)                          # -> 21
print(len(temps))                   # -> 3
```

Four things to read out of that. The list is the same list: same object, same length, same three
slots. Slot 1 now holds a different address. The integer `21` was not altered — integers cannot be
altered — it was merely dropped from that slot, and `old` still names it. And the length did not
move, because writing to an existing position replaces rather than inserts.

**A slot holds an address, so an indexed write moves exactly one 8-byte pointer.** The header is
untouched: same length field, same element block at the same address. No other slot is read or
written, and no object is copied, however large it is. The only other work is bookkeeping — the
incoming object's reference count goes up by one, the outgoing object's goes down by one.

That bookkeeping is what decides the fate of the displaced object. The write does not erase it; it
survives exactly as long as something else still refers to it. CPython counts references and frees
an object the moment its count hits zero:

```python
class Reading:
    def __init__(self, tag): self.tag = tag
    def __del__(self): print(f"[{self.tag} freed]")

log = [Reading("A"), Reading("B")]
kept = log[1]                     # a second reference to the B object

log[0] = None                     # -> [A freed]   the slot held the only reference
log[1] = None                     # nothing printed - `kept` still refers to B
print("both slots overwritten")   # -> both slots overwritten
# -> [B freed]                    printed at shutdown, when `kept` finally goes away
```

`A` is freed the instant its slot is overwritten, before the next line runs. `B` is not, because
`kept` holds it. This is also the one way an indexed write can cost more than moving a pointer: if
the displaced object held the last reference to a large nested structure, freeing it walks that
whole structure right there in the assignment. The write is still O(1); the cleanup it triggers is
proportional to what you threw away. The same accounting, without a custom class:

```python
import sys

label = "".join(["sensor-", "07"])
readings = [label, None]
print(sys.getrefcount(label) - 1)   # -> 2   (the name, plus the slot)
readings[0] = None
print(sys.getrefcount(label) - 1)   # -> 1   (just the name now)
```

`sys.getrefcount` reports one extra reference — its own argument — which is why both lines subtract
one. The point is the drop from 2 to 1: overwriting a slot released a reference and nothing else.

### Reading hands back the object, not a copy

`nums[i]` copies the address out of slot `i` and hands you a reference to the very object stored
there. Nothing is duplicated and the list is not touched.

```python
rows = [[1, 2], [3, 4]]
first = rows[0]

print(first is rows[0])   # -> True
first.append(9)
print(rows)               # -> [[1, 2, 9], [3, 4]]
print(len(rows))          # -> 2
```

With immutable elements — ints, strings, tuples — the distinction is invisible, because there is
nothing you can do to the object you got back. With a mutable element it is the whole story:
`first` and `rows[0]` are two names for one list, so mutating through either is visible through the
other. **Reading takes a reference out; it does not take the element out.** The list still holds
the same address afterwards.

The index is an ordinary expression, evaluated at runtime, and the requirement it has to satisfy is
narrower and more precise than "be an integer":

```python
prices = [340, 125, 999, 60]
n = len(prices)

print(prices[n - 2])   # -> 999   any integer expression works
print(prices[True])    # -> 125   True answers __index__ with 1
prices[1.0]            # TypeError: list indices must be integers or slices, not float
```

**A subscript does not demand an `int`; it demands an object that answers `__index__`.** That
method is the protocol for "I can stand in for a position", and it is specified to be exact and
lossless — an object either has an integer value or it has no business being an index. `bool`
defines it, which is the real reason `True` reaches slot 1. `float` does not define it, and the
omission is deliberate rather than an oversight: `1.0` does define `__int__`, and `int(1.0)` is
`1`, but that conversion throws information away in general, and a subscript is not a place where
silent rounding belongs. Anything that does define `__index__` works, including a type you write:

```python
import operator

class Slot:
    def __index__(self): return 2

prices = [340, 125, 999, 60]
print(prices[Slot()])         # -> 999
print(operator.index(True))   # -> 1
operator.index(2.0)           # TypeError: 'float' object cannot be interpreted as an integer
```

`operator.index` is that protocol called on its own, and it hands down the same verdict a subscript
would, one step earlier — useful when you want to validate a position before you use it. The
rejection of floats holds on both sides of an assignment: `prices[1.0] = 0` raises the same
`TypeError` as the read. That matters more than it looks, because `len(nums) / 2` is a float and
will not index anything. Use `//` when you are computing a position.

### The valid range is 0 to len − 1

Indices start at 0. The first element is at index 0, so the *last* element is at index
`len(nums) - 1`.

```python
prices = [340, 125, 999, 60]
print(prices[0])     # -> 340
print(prices[3])     # -> 60
print(len(prices))   # -> 4
print(prices[4])     # IndexError: list index out of range
```

**`len(nums)` is a count of items, and a count is one more than the largest index — so
`nums[len(nums)]` is always out of range.** This is the off-by-one that produces more `IndexError`s
than any other cause. A four-element list has four elements and a highest index of 3. Whenever you
compute an index from a length, subtract one — or let `range(len(nums))` do it for you.

The empty list is the degenerate case of the same rule: `len([])` is 0, so the valid range runs
from 0 up to −1, which is empty. There is no index at all that reads from `[]`.

### Negative indices

A negative index is resolved by adding the length to it: `nums[i]` for negative `i` means
`nums[len(nums) + i]`. That is the whole rule, and it holds across the entire negative range.

```python
prices = [340, 125, 999, 60]
n = len(prices)
print(all(prices[i] == prices[n + i] for i in range(-n, 0)))   # -> True
print(prices[-1], prices[n - 1])                               # -> 60 60
```

The list does that addition itself, against its own length, at the moment of the lookup — so a
negative index tracks the current end of the list rather than a position fixed when you wrote it.

`nums[-1]` is the idiomatic way to reach the last element. Prefer it to `nums[len(nums) - 1]`: it
is shorter, it evaluates `nums` once, and it cannot be got wrong by an off-by-one.

The valid negative range is `-len(nums)` through `-1`, mirroring the positive range `0` through
`len(nums) - 1`. `prices[-4]` is the first element; `prices[-5]` raises, because `4 + (-5)` is −1,
which is still not a position. Note the asymmetry at the other end: there is no `-0`. `-0` *is* `0`,
so the negative range starts at `-1` and counting backward never wraps around through zero.

```python
prices = [340, 125, 999, 60]
print(prices[-0])    # -> 340   same as prices[0], not the last element
print(prices[-4])    # -> 340
print(prices[-5])    # IndexError: list index out of range
```

### Unpacking reads every position at once

Assigning a list to a tuple of names reads the whole thing in one statement: each position in turn,
each element bound to a name.

```python
temps = [18.5, 16.75, 20.0]
a, b, c = temps
print(a, b, c)          # -> 18.5 16.75 20.0
```

The counts must match exactly, and a mismatch raises `ValueError`, not `IndexError`. The statement
is checked as a whole rather than failing on one bad subscript, and the message tells you which
direction you were off in:

```python
temps = [18.5, 16.75, 20.0]

try:
    a, b = temps
except ValueError as e:
    print(e)            # -> too many values to unpack (expected 2, got 3)

try:
    a, b, c, d = temps
except ValueError as e:
    print(e)            # -> not enough values to unpack (expected 4, got 3)
```

One name in the target may carry a `*`, which relaxes the count: the starred name absorbs whatever
the fixed names leave over, from either end or from the middle.

```python
nums = [10, 20, 30, 40]

first, *rest = nums
print(first, rest)          # -> 10 [20, 30, 40]

*init, last = nums
print(init, last)           # -> [10, 20, 30] 40

head, *middle, tail = nums
print(head, middle, tail)   # -> 10 [20, 30] 40
```

**The starred target is not a view and not a lazy object — it builds a real list, and costs what
building a list of that length costs.**

```python
import sys

nums = list(range(1000))
first, *rest = nums

print(len(rest), rest is nums)   # -> 999 False
print(sys.getsizeof(rest))       # -> 8056
print(sys.getsizeof(nums))       # -> 8056
```

Eight kilobytes of fresh pointers, to read one element off the front. In a single statement that is
a fair price for the clarity. In a loop it is the quadratic trap section 5 prices for repeated
slicing, arriving by a different spelling and for exactly the same reason — a full copy of the
remainder on every pass:

```python
import timeit

def drain(n):
    nums = list(range(n))
    total = 0
    while nums:
        first, *nums = nums
        total += first
    return total

for n in (2000, 4000, 8000, 16000):
    t = min(timeit.repeat('drain(n)', globals={'drain': drain, 'n': n},
                          number=3, repeat=5)) / 3
    print(f'n={n:>6}  {t * 1e3:8.2f} ms')
# n=  2000      3.88 ms
# n=  4000     16.22 ms
# n=  8000     68.27 ms
# n= 16000    282.76 ms
```

Doubling the length roughly quadruples the time. Unpack when you know the shape and want the names
for it. Do not unpack to peel one element off a list you are still working through.

### The ways an access fails

Out-of-range access raises rather than returning a placeholder or silently doing nothing. The
message differs by operation, which is a free diagnostic in a traceback. Measured on
`prices = [340, 125, 999, 60]`:

| Expression | Exception message |
|---|---|
| `prices[4]` | `IndexError: list index out of range` |
| `prices[-5]` | `IndexError: list index out of range` |
| `[][0]` | `IndexError: list index out of range` |
| `[][-1]` | `IndexError: list index out of range` |
| `prices[4] = 0` | `IndexError: list assignment index out of range` |
| `prices[-5] = 0` | `IndexError: list assignment index out of range` |
| `del prices[4]` | `IndexError: list assignment index out of range` |
| `prices.pop(4)` | `IndexError: pop index out of range` |
| `[].pop()` | `IndexError: pop from empty list` |
| `prices.index(9)` | `ValueError: list.index(x): x not in list` |
| `prices.remove(9)` | `ValueError: list.remove(x): x not in list` |
| `first, *rest = []` | `ValueError: not enough values to unpack (expected at least 1, got 0)` |

The word `assignment` in the message tells you the failure was on the write side even when the
statement contains several subscripts, and `del` reports itself as an assignment because it goes
through the same slot-writing machinery.

The split between the two exception types is the split between the two questions you can ask. An
`IndexError` means you named a position that does not exist. A `ValueError` means the position was
never the problem — you named a *value*, and no position holds it. `index` and `remove` search by
value, and neither has a quiet failure mode: absence raises.

`index` also takes optional `start` and `stop` bounds, which is how you find a later occurrence
without touching the list:

```python
vals = [1, 2, 3, 2]
print(vals.index(2))        # -> 1
print(vals.index(2, 2))     # -> 3   the search begins at position 2
print(vals.index(2, 1, 3))  # -> 1   stop is exclusive, exactly as in a slice
vals.index(2, 4)            # ValueError: list.index(x): x not in list
```

Prefer that to slicing off the front and searching the rest. A slice copies O(k) elements you did
not need, and it renumbers the answer — the index it returns is a position in the copy, and you
have to add the offset back yourself to get a position in the original. `start` searches the
original list and reports a position you can use directly.

The important consequence of the assignment case: **indexed assignment can only rewrite a position
that already exists.** It never grows the list. `prices[4] = 0` on a four-element list is an error,
not an extension; `append` is the operation that adds a position. On an empty list every indexed
assignment fails, `out[0] = 1` included.

### There is no empty slot to read

A list can own more pointer slots than it currently uses:

```python
import sys

nums = []
for x in (10, 20, 30):
    nums.append(x)

print(len(nums))                                        # -> 3
print((sys.getsizeof(nums) - sys.getsizeof([])) // 8)   # -> 4
print(nums[3])                                          # IndexError: list index out of range
```

Three items, four slots paid for. The fourth slot physically exists in the allocation, but no
expression in the language can reach it — `nums[3]` raises exactly as it would if the block were
exactly three slots wide. Section 7 covers why that spare slot is there.

**Every position from 0 to `len - 1` holds a real object, and no position outside that range is
readable, so occupancy and length are one number rather than two.** There is nothing to track
alongside `len()`, no "is this slot filled" test to write, and no value reserved to mean empty. This
also means a placeholder-filled list is genuinely full: `[None] * 6` has length 6 and six real
elements, each of which is the object `None`. It is not six empty slots — `None` is an object like
any other, and reading slot 3 gives it to you rather than signalling absence.

That model has a consequence worth stating plainly, because it is where the model stops describing
and starts handing you a job. **A position exists because something was put there, so a list can
never give you back a value you did not choose.** There is no read that manufactures one on your
behalf, and no condition a slot can be in other than "holds this object". So when you want a fixed
number of positions before you have the values to put in them, you write the fill out yourself —
`[None] * 6`, `[0.0] * n`, `[''] * n` — and that fill is a decision you are making, not a
formality you are performing.

This is what makes section 3's argument for `None` over `0` load-bearing rather than a matter of
taste. `[0] * n` and `[None] * n` are equally full, equally valid, and equally cheap; the entire
difference is what happens when you read back a position you meant to overwrite and did not. `None`
cannot be mistaken for a temperature, a price, or a running total, so the omission surfaces as a
`TypeError` at the first arithmetic that touches it. `0` is a plausible answer to any of those
questions, so it survives the arithmetic and leaves as a wrong number with no traceback attached.
Choosing the fill is choosing how loudly your own oversights fail.

### Reading and writing in one statement

Compound assignment is not a third primitive. It is a read and a write with an operation wedged
between them:

```python
nums = [10, 20, 30]

nums[0] += 5
print(nums)              # -> [15, 20, 30]

nums[0], nums[2] = nums[2], nums[0]
print(nums)              # -> [30, 20, 15]
```

`nums[0] += 5` compiles to a subscript load, an addition, and a subscript store — so the index
expression is evaluated once and reused for both halves. The swap works for a related reason: the
entire right-hand side is evaluated into a tuple before any assignment happens, so both reads
complete before either write starts. Written as two statements it would need a temporary, because
the first write would destroy a value the second one still needs.

That store is a genuine subscript assignment and not a detail of the syntax, and the two halves can
be told apart. When the element is mutable, the operation mutates it in place and the store then
writes the very same address back into the slot it came from:

```python
rows = [[1, 2]]
inner = rows[0]

rows[0] += [3]
print(rows)               # -> [[1, 2, 3]]
print(inner is rows[0])   # -> True   the store put back the object the operation had mutated
```

Nothing here depends on the store succeeding, because it stores what was already there. Section 9
shows the case where the store is the half that *fails* — and since the operation ran first, the
mutation has already landed by the time the assignment raises.

### Filling a list with an indexed loop

When you know the size in advance, allocate the positions first and then write into them:

```python
BASE = 18
adjust = [0.5, -1.25, 2.0, 0.0, -0.75]

temps = [0.0] * len(adjust)        # five real slots, each holding 0.0
for i in range(len(temps)):
    temps[i] = BASE + adjust[i]

print(temps)   # -> [18.5, 16.75, 20.0, 18.0, 17.25]
```

The preallocation is load-bearing, not decoration. Starting from `temps = []` would fail on the
first iteration, because indexed assignment cannot create a position that does not exist yet.

`range(len(temps))` yields exactly `0, 1, 2, 3, 4` — the valid index set, derived from the length
rather than typed out. That is why it is the correct spelling, and why `range(1, len(temps) + 1)` is
a bug: it starts one past the first element and ends one past the last.

Reading is where the calculation changes. An indexed read loop pays for an index object and a
subscript on every pass to produce a value it uses immediately, and iterating the list directly is
faster than any indexed form; section 6 measures the three loop forms against each other and works
out which to reach for when.

### Removing an element

`del` and `pop` both remove by position. They differ only in whether you get the removed object
back: `del` is a statement and evaluates to nothing, `pop` is a method that returns what it removed.

```python
prices = [340, 125, 999, 60]
del prices[1]
print(prices, len(prices))   # -> [340, 999, 60] 3

prices = [340, 125, 999, 60]
gone = prices.pop(1)
print(gone, prices)          # -> 125 [340, 999, 60]

last = prices.pop()          # no argument: the last element
print(last, prices)          # -> 60 [340, 999]
```

Both take the same index space as reading, negatives included:

```python
vals = [1, 2, 3, 4]
del vals[-1]
print(vals)                  # -> [1, 2, 3]
print(vals.pop(-2), vals)    # -> 2 [1, 3]
```

`remove` is the by-value sibling of these two. It scans for the first element equal to its argument
and deletes that position, and it returns nothing. When no element matches it raises
`ValueError: list.remove(x): x not in list`, so removing a value that is not there is an error
rather than a no-op.

None of the three leaves a hole, because there is no such thing as a hole. Everything after position
`i` shifts one slot left and the length drops by one, so removal from anywhere but the end costs
O(n) in the size of the tail. Section 8 does that arithmetic properly.

At the read/write level the consequence to internalise is that removal invalidates positions:

```python
prices = [340, 125, 999, 60]
i = 2
print(prices[i])   # -> 999
del prices[0]
print(prices[i])   # -> 60    same index, different element
```

An index is a position in the current list, not a handle on an element. Change the list's shape and
every index past the change point now means something else.


---

## 5. Slicing, completely

### The half-open interval

`nums[start:stop]` selects the elements from index `start` up to *but not including* `stop`.

```python
temps = [12, 15, 19, 22, 18, 14, 11]
print(temps[1:4])        # -> [15, 19, 22]
print(len(temps[1:4]))   # -> 3
```

**Stop being exclusive is what makes the length of a slice equal `stop - start`, with no
correction term to remember.** That arithmetic holds when both bounds are non-negative and land
inside the list; negative bounds have `len(nums)` added to them first, and bounds outside the list
get clamped, both of which change the count. Each gets its own treatment below. Two more
properties fall directly out of the half-open rule:

```python
print(temps[:3] + temps[3:] == temps)                                # -> True
print(temps[0:2] + temps[2:5] + temps[5:7] == temps)                 # -> True
print(all(temps[:k] + temps[k:] == temps for k in range(-20, 20)))   # -> True
```

Any single cut point splits the list into two pieces that concatenate back to the original, and
adjacent slices tile without overlap or gaps because the `stop` of one is the `start` of the next.
The third line makes the point at its strongest: the split identity holds for *every* integer `k`,
including negative ones and ones far outside the list. If `stop` were inclusive you would be
writing `temps[:k] + temps[k+1:]` and quietly dropping an element every time you got the `+1`
wrong.

### Omitted and negative bounds

Omit `start` and it defaults to the beginning; omit `stop` and it defaults to the end. Omit both
and you get a full copy — a *new* list with the same elements.

```python
print(temps[:3])          # -> [12, 15, 19]
print(temps[3:])          # -> [22, 18, 14, 11]
print(temps[:])           # -> [12, 15, 19, 22, 18, 14, 11]
print(temps[:] is temps)  # -> False
```

A negative bound counts back from the end: `-1` is the last element, `-2` the one before it. It is
resolved by adding `len(nums)`, so `temps[-2:]` means `temps[5:]`. The two forms mix freely in one
slice, and after resolution the half-open rule applies unchanged.

```python
print(temps[-2:])            # -> [14, 11]
print(temps[:-2])            # -> [12, 15, 19, 22, 18]
print(temps[-5:-2])          # -> [19, 22, 18]
print(temps[2:-2])           # -> [19, 22, 18]
print(temps[-5:5])           # -> [19, 22, 18]
print(temps[-3:] == temps[len(temps) - 3:])   # -> True
```

Because the resolution is `bound + len(nums)`, `-0` is not a way to say "the end": `0` and `-0` are
the same integer, so `temps[:-0]` resolves `stop` to `0` and selects nothing. When you want "up to
the end", omit the bound.

```python
print(temps[:-0])   # -> []
print(temps[:0])    # -> []
```

When `start` lands at or past `stop`, the interval is empty and you get an empty list. No error,
no warning:

```python
print(temps[4:1])     # -> []
print(temps[-1:-4])   # -> []
print(temps[5:5])     # -> []
```

### The third argument: step

`nums[start:stop:step]` takes every `step`-th element. A positive step walks left to right and the
selected indices are `start`, `start + step`, `start + 2 * step`, and so on while they stay short
of `stop`.

```python
print(temps[::2])      # -> [12, 19, 18, 11]
print(temps[1::2])     # -> [15, 22, 14]
print(temps[2::3])     # -> [19, 14]
print(temps[::10])     # -> [12]
```

A step larger than the list is not an error; it simply selects the first element and then runs off
the end.

A negative step walks backwards, and this is where the meaning of `start` and `stop` needs care:
**with a negative step, `start` is still the first index visited and `stop` is still the first
index not visited — you are just moving right to left, so `start` must be the larger index.**

```python
print(temps[::-1])       # -> [11, 14, 18, 22, 19, 15, 12]
print(temps[::-2])       # -> [11, 18, 19, 12]
print(temps[4:1:-1])     # -> [18, 22, 19]
print(temps[1:4:-1])     # -> []
print(temps[-1::-3])     # -> [11, 22, 12]
```

`temps[4:1:-1]` starts at index 4 and stops before index 1, yielding indices 4, 3, 2.
`temps[1:4:-1]` asks to walk left from 1 and stop before 4, which visits nothing. This is the
single most common slicing mistake: reversing the step but leaving the bounds in ascending order,
which silently produces an empty list rather than the reversed run you wanted.

With the step omitted or positive, an omitted `start` means index 0 and an omitted `stop` means
`len(nums)`. With a negative step those defaults flip: `start` becomes `len(nums) - 1` and `stop`
becomes "one position before the front", which no literal can express — writing `-1` there means
the last element, not the position before index 0.

```python
print(temps[3::-1])       # -> [22, 19, 15, 12]
print(temps[3:-8:-1])     # -> [22, 19, 15, 12]   (-8 lands below the front)
print(temps[5:0:-1])      # -> [14, 18, 22, 19, 15]  (index 0 excluded)
print(temps[5:-100:-1])   # -> [14, 18, 22, 19, 15, 12]
print(temps[5:-1:-1])     # -> []   (-1 means index 6, which is above 5)
```

That is why `nums[::-1]` is the reversal idiom: only an omitted `stop` reaches past index 0, so it
is the only spelling that keeps the first element.

A step of `0` describes no walk at all, so it is rejected, and a bound that is not an integer is a
type error:

```python
try:
    temps[::0]
except ValueError as e:
    print(e)    # -> slice step cannot be zero

try:
    temps['a':2]
except TypeError as e:
    print(e)    # -> slice indices must be integers or None or have an __index__ method
```

Those two are the whole list of ways to make a *read* slice fail. Every bound you can write as an
integer, however far out of range or inverted, is accepted in silence. That silence is worth a
subsection of its own.

### Clamping, and the silence it buys

An out-of-range *index* raises. An out-of-range *slice bound* is silently clamped into range.

```python
temps = [12, 15, 19, 22, 18, 14, 11]

try:
    temps[99]
except IndexError as e:
    print(e)             # -> list index out of range

print(temps[99:])        # -> []
print(temps[99:200])     # -> []
print(temps[3:99])       # -> [22, 18, 14, 11]
print(temps[-99:2])      # -> [12, 15]
print(temps[-99:-98])    # -> []
```

**A slice never raises for a bad bound; it returns whatever it found, and "nothing" is a perfectly
acceptable answer.** Put the two side by side and the asymmetry is stark — `temps[99]` and
`temps[99:100]` ask for the same nonexistent element, and only one of them tells you:

```python
try:
    temps[99]
except IndexError as e:
    print('index :', e)   # -> index : list index out of range
print('slice :', temps[99:100])   # -> slice : []
```

This is exactly the mechanism by which off-by-one errors survive testing. A window that is
supposed to be three wide silently becomes two wide, then one wide, at the tail:

```python
for i in range(len(temps)):
    print(i, temps[i:i + 3], len(temps[i:i + 3]))
# 0 [12, 15, 19] 3
# 1 [15, 19, 22] 3
# 2 [19, 22, 18] 3
# 3 [22, 18, 14] 3
# 4 [18, 14, 11] 3
# 5 [14, 11] 2
# 6 [11] 1
```

Nothing here fails. If your logic assumed three elements, it now runs on two, and the bug surfaces
as a wrong number rather than a traceback. When a slice's width matters, either bound the loop so
short slices never arise, or check the width before using it:

```python
width = 3
for i in range(len(temps) - width + 1):
    print(i, temps[i:i + width])
# 0 [12, 15, 19]
# 1 [15, 19, 22]
# 2 [19, 22, 18]
# 3 [22, 18, 14]
# 4 [18, 14, 11]
```

The clamping is not something you have to guess at. `slice.indices` performs it on demand and
reports the concrete bounds, which is the subject of the last subsection.

### What a slice costs

A slice builds a new list and copies `k` pointers into it, where `k` is the number of elements
selected. That is O(k) time and O(k) additional memory.

The memory is directly measurable. A list object's header is 56 bytes and each slot is 8 bytes, so
a `k`-element slice occupies `56 + 8 * k` bytes, allocated exactly rather than with room to grow:

| expression | `sys.getsizeof` |
| --- | --- |
| `nums = list(range(1000))` | 8056 |
| `nums[:]` | 8056 |
| `nums[:500]` | 4056 |
| `nums[:100]` | 856 |
| `nums[:0]` | 56 |

The time tracks `k`, not the length of the source. Slicing 1000 elements costs the same whether
the list holds ten thousand or ten million:

```python
import timeit
for n in (10_000, 100_000, 1_000_000, 10_000_000):
    t = min(timeit.repeat('nums[:1000]', setup=f'nums = list(range({n}))',
                          number=20_000, repeat=5)) / 20_000
    print(f'len {n:>10}  {t * 1e6:.2f} us')
# len      10000  0.96 us
# len     100000  0.95 us
# len    1000000  0.95 us
# len   10000000  0.95 us
```

Sweeping `k` instead shows the linear term plus a fixed cost per slice:

```python
import timeit
nums = list(range(1_000_000))
for k in (0, 10, 1000, 100_000, 1_000_000):
    number = 200_000 if k <= 1000 else 200
    t = min(timeit.repeat(f'nums[:{k}]', globals={'nums': nums},
                          number=number, repeat=5)) / number
    print(f'k={k:>9}  {t * 1e6:10.3f} us')
# k=        0       0.015 us
# k=       10       0.028 us
# k=     1000       0.966 us
# k=   100000     189.546 us
# k=  1000000    2570.337 us
```

An empty slice still takes about 15 nanoseconds: that is the cost of allocating a list object and
returning it, independent of `k`. That floor is why the *per-element* rate is not constant. Around
1 nanosecond per element in the middle of the range, it looks worse at `k=10` because the fixed
15 nanoseconds dominate ten elements' worth of copying, and it drifts up again past `k=100_000` as
the copy outgrows cache and becomes limited by memory traffic. The shape is still linear; only the
constant in front of it moves.

Because each slice is O(k), a slice inside a loop is the same trap as any operation that has to
touch the whole tail: `nums = nums[1:]` reads like constant work in the body, but it copies
everything still there, so the total is `n + (n-1) + (n-2) + ...`, which is O(n²). Section 8 puts
that shape on the clock and shows how the doubling ratios give it away; walking with an index
instead does the same job in linear time.

Only the *references* are copied, never the objects they point at. This makes a slice a **shallow
copy**: a new outer list, the same inner objects.

```python
import sys
photos = ['x' * 100_000 for _ in range(1000)]
print(sum(sys.getsizeof(p) for p in photos))   # -> 100041000   (~100 MB of strings)
print(sys.getsizeof(photos[:]))                # -> 8056        (the copy)
print(photos[:][0] is photos[0])               # -> True
```

100 MB of string data, an 8 KB copy. The same is true of nested lists: `grid[:]` gives you a new
outer list whose entries are the very same row objects, so mutating a row through one is visible
through the other.

```python
grid = [[0, 0], [0, 0]]
copy = grid[:]
copy[0][0] = 9
print(grid)                      # -> [[9, 0], [0, 0]]
print(copy[0] is grid[0])        # -> True
copy[1] = ['new']
print(grid)                      # -> [[9, 0], [0, 0]]
```

Replacing a slot in the copy leaves the original alone, because that writes a new pointer into the
copy's own array. Mutating through a slot reaches the shared object. Both lines are doing exactly
what the pointer picture predicts.

`nums[::-1]` is a slice like any other and pays the same O(k) copy, so when you only need to look
at the elements backwards rather than keep them that way, `reversed(nums)` walks the original
without allocating a second list — section 8 prices the two against each other.

### Slice assignment

A slice can be the *target* of an assignment, and this is where slices stop being a read operation.

**Assigning to a contiguous slice replaces that run with the right-hand side, and the two need not
be the same length — the list grows or shrinks to fit.**

```python
nums = [12, 15, 19, 22, 18]
nums[1:3] = [0, 0, 0, 0]
print(nums, len(nums))     # -> [12, 0, 0, 0, 0, 22, 18] 7

nums = [12, 15, 19, 22, 18]
nums[1:4] = [99]
print(nums, len(nums))     # -> [12, 99, 18] 3

nums = [12, 15, 19, 22, 18]
nums[1:4] = []
print(nums, len(nums))     # -> [12, 18] 2
```

An *extended* slice — one with a step other than 1 — has no such freedom. Its targets are
scattered through the list, so there is no coherent way to insert or delete; the lengths must
match exactly.

```python
nums = [12, 15, 19, 22, 18, 14]
nums[::2] = [0, 0, 0]
print(nums)                # -> [0, 15, 0, 22, 0, 14]

nums = [12, 15, 19, 22, 18, 14]
try:
    nums[::2] = [0, 0]
except ValueError as e:
    print(e)   # -> attempt to assign sequence of size 2 to extended slice of size 3

nums = [12, 15, 19, 22, 18, 14]
try:
    nums[::2] = []
except ValueError as e:
    print(e)   # -> attempt to assign sequence of size 0 to extended slice of size 3
```

A negative step is an extended slice too, and obeys the same rule:

```python
nums = [1, 2, 3, 4]
nums[::-1] = [9, 8, 7, 6]
print(nums)                # -> [6, 7, 8, 9]
```

A step of exactly `1`, written out, still counts as contiguous, so it resizes happily:

```python
nums = [12, 15, 19, 22, 18]
nums[1:4:1] = [9]
print(nums)                # -> [12, 9, 18]
```

Three shapes are worth naming because they read as idioms:

```python
nums = [12, 15, 19]
nums[:] = [1, 2, 3, 4, 5]      # replace every element, same list object
print(nums)                    # -> [1, 2, 3, 4, 5]

prices = [10, 20, 30]
prices[1:1] = [11, 12]         # empty target: splice in, remove nothing
print(prices)                  # -> [10, 11, 12, 20, 30]

prices = [10, 20, 30, 40, 50]
del prices[1:3]                # remove a run
print(prices)                  # -> [10, 40, 50]
```

`del nums[a:b]` and `nums[a:b] = []` do the same thing; `del` is the clearer spelling when there is
nothing to put back. `del` needs no length agreement even on an extended slice, because there is
no right-hand side to agree with:

```python
prices = [10, 20, 30, 40, 50, 60]
del prices[::2]
print(prices)                  # -> [20, 40, 60]

nums = [1, 2, 3]
del nums[:]
print(nums)                    # -> []
```

Assignment targets clamp exactly as reads do, so an out-of-range empty target is an insertion
point rather than an error. An inverted target collapses to the position of its `start`:

```python
readings = [1, 2, 3]
readings[99:99] = [0]
print(readings)                # -> [1, 2, 3, 0]

readings = [1, 2, 3]
readings[-99:-99] = [0]
print(readings)                # -> [0, 1, 2, 3]

readings = [0, 1, 2, 3, 4, 5, 6]
readings[5:1] = ['x']          # start 5, stop clamped up to 5: an empty run at index 5
print(readings)                # -> [0, 1, 2, 3, 4, 'x', 5, 6]
```

The right-hand side may be **any iterable**, not just a list:

```python
nums = [0, 0, 0]
nums[:] = 'abc'
print(nums)                    # -> ['a', 'b', 'c']
nums[:] = range(4)
print(nums)                    # -> [0, 1, 2, 3]
nums[:] = (c.upper() for c in 'xyz')
print(nums)                    # -> ['X', 'Y', 'Z']
nums[:] = {'r': 1, 'g': 2}     # iterating a dict yields its keys
print(nums)                    # -> ['r', 'g']
```

The iterable is consumed into a temporary sequence *before* any writing happens, which is why a
list can be spliced into itself without the read chasing the write:

```python
nums = [1, 2, 3]
nums[:0] = nums
print(nums)                    # -> [1, 2, 3, 1, 2, 3]
```

Something non-iterable on the right is a `TypeError`. The message says "extended slice" whatever
the target actually was, so do not read it as a diagnosis of the slice — it is telling you about
the right-hand side:

```python
nums = [1, 2, 3]
try:
    nums[0:1] = 9
except TypeError as e:
    print(e)                   # -> must assign iterable to extended slice
```

`nums[:] = ...` writes through to the existing list object rather than producing a new one; section
9 covers when that distinction changes the outcome of a program.

### The slice object

`nums[1:4]` is syntax sugar for indexing with a `slice` instance. The compiler is explicit about
it — the colons become a constant `slice(1, 4, None)` handed to the subscript operation:

```python
import dis
dis.dis(compile('nums[1:4]', '<s>', 'eval'))
#   0           RESUME                   0
#
#   1           LOAD_NAME                0 (nums)
#               LOAD_CONST               0 (slice(1, 4, None))
#               BINARY_OP               26 ([])
#               RETURN_VALUE
```

So you can build one by hand, store it in a variable, pass it around, and use it as either a read
or an assignment target:

```python
WINDOW = slice(2, 5)
temps = [12, 15, 19, 22, 18, 14, 11]
print(temps[WINDOW])           # -> [19, 22, 18]
temps[WINDOW] = [0, 0, 0]
print(temps)                   # -> [12, 15, 0, 0, 0, 14, 11]
```

A `slice` stores exactly the three parts you gave it, as read-only attributes, and an omitted part
stays `None` rather than being filled in with a default. Two slices with equal parts compare equal
and hash equal, so a slice works as a dict key or a set member:

```python
s = slice(2, 5)
print(s.start, s.stop, s.step)             # -> 2 5 None
print(slice(1, 4) == slice(1, 4, None))    # -> True
print({slice(1, 4): 'window'}[slice(1, 4)])   # -> window
try:
    s.start = 0
except AttributeError as e:
    print(e)                               # -> readonly attribute
```

The defaults get filled in only when the slice meets a concrete length, and `indices(length)` is
the method that does it: it applies the clamping and default-filling described above and hands
back a concrete `(start, stop, step)` triple, which is how you find out what a slice will actually
do before doing it.

```python
print(slice(2, 99).indices(7))            # -> (2, 7, 1)
print(slice(None, None, -1).indices(7))   # -> (6, -1, -1)
print(slice(-99, 2).indices(7))           # -> (0, 2, 1)
print(len(range(*slice(2, 99).indices(7))))   # -> 5
```

The second line is the "one position before the front" from earlier, made concrete: `stop` comes
back as `-1`, a value you could not have written as a literal bound because `-1` in source means
the last element. The last line gives the element count a slice will produce without building the
slice, by handing the resolved triple to `range` and asking its length.

### The same rules, every sequence

Almost nothing above this point is a list feature. The colons compile to a `slice` object, and
every sequence type receives that same object and resolves it the same way: half-open bounds,
negative bounds resolved by adding the length, out-of-range bounds clamped rather than raised, a
step that sets stride and direction.

```python
temps  = [12, 15, 19, 22, 18, 14, 11]
label  = 'temperate'
frozen = (12, 15, 19, 22, 18, 14, 11)
counts = range(0, 70, 10)

print(temps[1:4])     # -> [15, 19, 22]
print(label[1:4])     # -> emp
print(frozen[1:4])    # -> (15, 19, 22)
print(counts[1:4])    # -> range(10, 40, 10)

print(label[3:99], repr(label[4:1]), label[::-1])
# -> perate '' etarepmet
print(frozen[-2:], frozen[99:], frozen[::2])
# -> (14, 11) () (12, 19, 18, 11)
print(counts[-2:], counts[99:], counts[::-1])
# -> range(50, 70, 10) range(70, 70, 10) range(60, -10, -10)
```

**What varies from one sequence type to the next is the type of the answer and whether anything
was copied to produce it — never the arithmetic that chose the elements.**

The type of the answer mirrors the source. Slicing a `str` gives a `str`, a `tuple` gives a
`tuple`, `bytes` gives `bytes`, a `range` gives a `range`, an `array.array` gives an `array.array`
(section 10 uses that one). `range(10)[10:20]` is `range(10, 10)` — an empty *range*, not an empty
list. Slicing a list gives a plain `list`, and it does so even when the source is a list subclass;
the new list carries the elements, not the class:

```python
class Reading(list):
    pass

readings = Reading([12, 15, 19, 22])
print(type(readings[1:3]))               # -> <class 'list'>
print(isinstance(readings[:], Reading))  # -> False
```

`range` is the sharpest case of the second half, because it copies nothing whatsoever. It stores a
start, a stop and a step, so slicing it is arithmetic on three integers and the result is another
`range` occupying the same 48 bytes at any length. A `str` slice pays the copy its length implies:

```python
import sys
counts = range(10_000_000)
text = 'x' * 10_000_000
print(sys.getsizeof(counts))              # -> 48
print(sys.getsizeof(counts[:5_000_000]))  # -> 48
print(sys.getsizeof(text[:5_000_000]))    # -> 5000041
```

Timed the same way as the list slices above, taking five million elements off the `range` ran in
0.045 µs while taking five million characters off the string took 123.8 µs. One of those is O(1)
in the size of the slice and the other is O(k), which is the whole distinction.

Slice *assignment* is the part that does not generalise, because it needs somewhere to write.
`list`, `bytearray` and `array.array` accept it; `str`, `bytes`, `tuple` and `range` are read-only
and say so plainly:

```python
label = 'temperate'
try:
    label[1:4] = 'XYZ'
except TypeError as e:
    print(e)     # -> 'str' object does not support item assignment
```

That read-only nature also buys a shortcut: a full slice of an immutable sequence has nothing to
protect, so CPython hands back the original object instead of duplicating it. A list, which can
change underneath you, always gets a real copy. The shortcut is a `str`/`bytes`/`tuple`
optimisation rather than a rule about immutability — a `range` slice always builds a new `range`,
which costs the same 48 bytes either way:

```python
label  = ''.join('temperate')
frozen = tuple([12, 15, 19])
temps  = [12, 15, 19]
counts = range(3)

print(label[:] is label)     # -> True
print(frozen[:] is frozen)   # -> True
print(temps[:] is temps)     # -> False
print(counts[:] is counts, counts[:] == counts)   # -> False True
```

This is also why `indices` takes a length rather than a sequence. Resolving a slice depends on
nothing but its three parts and how many elements it is being applied to, so one answer serves
every type that holds that many.


---

## 6. Iterating

### The three forms, in order of how often they are right

```python
temps = [18, 21, 19, 25]

for t in temps:                    # you need the values
    pass

for i, t in enumerate(temps):      # you need the position and the value
    pass

for i in range(len(temps)):        # you are writing into temps[i]
    temps[i] = temps[i] + 1

print(temps)                       # -> [19, 22, 20, 26]
```

**Direct iteration is the default because it is the only form that says nothing beyond what you
mean.** It carries no index you have to keep correct, no `len()` call, and no bracket lookup. It is
also the fastest of the three. Summing 100,000 ints, best of 11 runs of 20 iterations each:

| Form | Time |
|---|---|
| `for x in nums` | 1.23 ms |
| `for i in range(len(nums))` with `nums[i]` | 1.70 ms |
| `for i, x in enumerate(nums)` | 2.07 ms |

`enumerate` comes last, but not for the reason usually given. It does *not* allocate a fresh tuple
on every step. CPython's `enumerate` keeps one two-tuple and refills it in place whenever nothing
else holds a reference to it — which is exactly the situation when the loop header immediately
unpacks it into `i, x`:

```python
it = enumerate(['a', 'b', 'c'])
first = next(it)
address = id(first)
del first                              # drop the only outside reference
print(id(next(it)) == address)         # -> True    same tuple, refilled

pairs = list(enumerate(['a', 'b', 'c']))
print(len({id(p) for p in pairs}))     # -> 3       kept pairs must be distinct objects
```

What you actually pay for is smaller and duller: a fresh integer object for the index once the
counter climbs past the small ints CPython keeps cached, a call into the iterator per step, and an
`UNPACK_SEQUENCE` plus a second name to store in the loop header. Readability wins over 0.8 ms
per hundred thousand elements — but `enumerate` is not a zero-cost way to get an index, and if
you never use the index you are paying for nothing.

### enumerate, including start

`enumerate` yields `(index, value)` pairs. It takes a second argument, `start`, which offsets only
the number it reports — it does not skip any elements:

```python
temps = [18, 21, 19]

for day, t in enumerate(temps, start=1):
    print(day, t)
# -> 1 18
# -> 2 21
# -> 3 19
```

Use `start` for human-facing numbering. Do not use it to try to fake an offset into the list; the
value you get back is still `temps[day - 1]`, so any indexing you do with `day` is now off by one.

### range(len(...)) is the writing form

Iterating by index is correct precisely when the index is what you need — because you are
assigning into a slot. `for t in temps` binds `t` to the value stored in a slot; rebinding `t`
inside the loop changes the name and leaves the list alone.

```python
temps = [18, 21, 19]
for t in temps:
    t = t + 1
print(temps)              # -> [18, 21, 19]   nothing happened

temps = [18, 21, 19]
for i in range(len(temps)):
    temps[i] += 1
print(temps)              # -> [19, 22, 20]
```

`enumerate` also gives you the index, so `for i, t in enumerate(temps): temps[i] = t * 10` works and
reads well when you need the old value and the slot together. Reaching for `range(len(...))` when
you only ever read `nums[i]` is the habit to break; reaching for it when you are writing is simply
correct.

To write into slots from the back, wrap the range rather than the list: `reversed(range(len(nums)))`
hands you `len(nums) - 1` down to `0` without building a list of indices.

```python
temps = [18, 21, 19]
for i in reversed(range(len(temps))):
    temps[i] = temps[i] + i
print(temps)              # -> [18, 22, 21]
```

### Walking two sequences with zip

`zip` yields tuples drawn one element at a time from each of its arguments. It is lazy — a `zip`
object is 64 bytes regardless of how long or how many its inputs are — and it stops as soon as its
shortest argument runs out:

```python
channels = ['red', 'green', 'blue']
levels = [255, 128]

print(list(zip(channels, levels)))     # -> [('red', 255), ('green', 128)]
```

That silent truncation loses `'blue'` without a word. `strict=True` turns the mismatch into an
error instead:

```python
channels = ['red', 'green', 'blue']
levels = [255, 128]

try:
    list(zip(channels, levels, strict=True))
except ValueError as e:
    print(e)            # -> zip() argument 2 is shorter than argument 1
```

The check is positional, so the message names which argument disagreed: zipping `levels` first
reports `zip() argument 2 is longer than argument 1`. The error is raised *lazily*, at the moment
the shortest input runs dry, not up front — calling `next()` on the zip above yields both pairs
successfully, and only the third call raises. **`strict=True` costs nothing measurable** —
building a 100,000-element sum list took 2.00 ms without it and 1.91 ms with it, a gap that is
run-to-run noise and lands in both directions — so make it your default whenever the two
sequences are supposed to be the same length.

`enumerate` and `zip` compose:

```python
channels = ['red', 'green', 'blue']
levels = [255, 128, 64]

for rank, (name, level) in enumerate(zip(channels, levels, strict=True), start=1):
    print(rank, name, level)
# -> 1 red 255
# -> 2 green 128
# -> 3 blue 64
```

### Backwards: reversed() versus nums[::-1]

Both walk a list from the end, and they cost very different things. `nums[::-1]` builds a complete
reversed copy first; `reversed(nums)` returns a small iterator that walks the original backwards and
allocates nothing per element.

```python
import sys

nums = list(range(1000))
print(sys.getsizeof(nums[::-1]))       # -> 8056
print(sys.getsizeof(reversed(nums)))   # -> 48
```

Summing 100,000 elements, best of 7 runs of 100: `sum(reversed(nums))` took 219.3 us,
`sum(nums[::-1])` took 400.3 us. Roughly half the time and 0.6% of the memory. When a problem
constrains extra space, `nums[::-1]` has already spent O(n) of it before your loop body runs once.

`reversed()` needs an object that can be walked from the end on demand: either one that defines
`__reversed__`, or one that supports the sequence protocol — `len()` plus integer indexing. Lists,
tuples, strings and `range` objects all qualify. A generator does not know its own length and cannot
be indexed, so `reversed(x for x in [1, 2, 3])` raises
`TypeError: 'generator' object is not reversible`. An object with `__getitem__` but no `__len__`
fails a step earlier, with `TypeError: object of type 'X' has no len()`.

For a list, the object `reversed()` hands back is a `list_reverseiterator`, and it works the same
way as a forward one: a reference to the live list plus a position, counting down instead of up.
Everything below about mutation applies to it too.

### The iterator protocol

A `for` loop is two builtins in a trench coat. `iter(obj)` asks the object for an iterator;
`next(it)` pulls the next value; `StopIteration` ends the loop.

```python
temps = [18, 21, 19]
it = iter(temps)
while True:
    try:
        t = next(it)
    except StopIteration:
        break
    print(t)          # -> 18, then 21, then 19
```

`next` also takes a default, which is how you ask for "the next one, if there is one" without
writing the `try`:

```python
print(next(iter([]), 'empty'))     # -> empty
```

The important part is what a list iterator actually holds. It is not a snapshot of the elements and
not a copy of the list — it is a reference to the live list plus a single integer position.
CPython will show you both:

```python
colors = ['red', 'green', 'blue']
it = iter(colors)
print(next(it))            # -> red
print(it.__reduce__())     # -> (<built-in function iter>, (['red', 'green', 'blue'],), 1)
```

That trailing `1` is the position. **The iterator reads `the_list[position]` at the moment you ask
for it, then increments `position` by one — so it sees every change you make to the list while the
loop is running.**

```python
prices = [10, 20, 30, 40]
it = iter(prices)
print(next(it))       # -> 10
prices[1] = 99
print(next(it))       # -> 99   the new value, not the old one
prices.append(50)
print(list(it))       # -> [30, 40, 50]   the appended element is included
```

Iteration stops when the position reaches the *current* length. Shrink the list below the position
and the loop simply ends early, with no error:

```python
nums = [1, 2, 3, 4, 5]
it = iter(nums)
print(next(it), next(it))   # -> 1 2      position is now 2
del nums[2:]                # nums is [1, 2]; position 2 is already past the end
print(list(it))             # -> []       no error, just nothing left
```

### Iterables and iterators are not the same thing

A list is an *iterable*: it can produce iterators, and `iter()` hands you a brand-new one, with its
own position, every time you ask. An iterator is the cursor itself, and `iter()` on one gives that
same cursor straight back — which is what lets a `for` loop accept either.

```python
temps = [18, 21, 19]
print(iter(temps) is iter(temps))   # -> False   two independent cursors

it = iter(temps)
print(iter(it) is it)               # -> True    a cursor is its own iterator
```

The consequence is that `zip`, `enumerate` and `reversed` objects are single-use. They are
iterators, not iterables that can be re-walked, so a second pass over one finds nothing:

```python
z = zip('ab', 'cd')
print(list(z))        # -> [('a', 'c'), ('b', 'd')]
print(list(z))        # -> []   already exhausted
```

This is why you store `list(zip(a, b))` when you need the pairs twice, and why a loop that consumes
part of an iterator and then hands it to another loop makes the second loop resume rather than
restart. A list has none of this problem: it is an iterable, so it can be walked as many times as
you like, and each `for` over it starts a fresh cursor at position zero.

### Mutating length while iterating

The hazard follows directly from the mechanism. Removing an element shifts every later element down
one slot, but the iterator's position still advances by one — so the element that slid into the
vacated slot is stepped straight over.

```python
guests = ['ana', 'bo', 'bo', 'cy']
it = iter(guests)
print(next(it), it.__reduce__()[2])   # -> ana 1
print(next(it), it.__reduce__()[2])   # -> bo 2
guests.remove('bo')                   # tail shifts down; position stays 2
print(guests)                         # -> ['ana', 'bo', 'cy']
print(next(it))                       # -> cy    the second 'bo' was never seen
```

Written as an ordinary loop it looks entirely reasonable and is entirely wrong:

```python
guests = ['ana', 'bo', 'bo', 'cy']
for name in guests:
    if name == 'bo':
        guests.remove(name)
print(guests)            # -> ['ana', 'bo', 'cy']   one 'bo' survived

crew = ['bo', 'bo', 'bo', 'bo']
for name in crew:
    if name == 'bo':
        crew.remove(name)
print(crew)              # -> ['bo', 'bo']          half of them survived
```

A list will not warn you about this. (A `dict` raises
`RuntimeError: dictionary changed size during iteration`, and a `set` raises
`RuntimeError: Set changed size during iteration`; a list produces a quietly wrong answer.)

There is exactly one operation where a list does object, and it is not iteration. `list.sort`
empties the list for the duration of the sort, so a key function that looks at the list sees `[]`
rather than a half-ordered arrangement — and if that key function changed the length, the sort
refuses on the way out:

```python
temps = [18, 21, 19, 25]

def bump(t):
    temps.append(t)          # the key function mutates the list being sorted
    return t

try:
    temps.sort(key=bump)
except ValueError as e:
    print(e)                 # -> list modified during sort

print(temps)                 # -> [18, 19, 21, 25]   sorted anyway; the appends are discarded

lengths = []
temps.sort(key=lambda t: (lengths.append(len(temps)), t)[1])
print(lengths)               # -> [0, 0, 0, 0]   the list is empty for the whole sort
```

**Sorting raises where iterating stays silent because a sort cannot tolerate the block moving
underneath it** — it is reordering the slots itself, so a concurrent change would corrupt the
result rather than merely skip an element. `sorted(nums, key=...)` copies its input first, has
nothing to protect, and never raises this.

Back to the loop, where nothing protects you. `enumerate` and `zip` do not help, because over a
list they are wrapped around that same list iterator and inherit its position:

```python
guests = ['ana', 'bo', 'bo', 'cy']
for i, name in enumerate(guests):
    if name == 'bo':
        guests.remove(name)
print(guests)            # -> ['ana', 'bo', 'cy']   same skip, same cause
```

Appending during iteration fails the other way — the position never catches the length, so the
loop never ends:

```python
queue = [1, 2]
seen = 0
for x in queue:
    seen += 1
    queue.append(x)
    if seen == 10:       # without this guard, this loop does not terminate
        break
print(seen, len(queue))  # -> 10 12
```

Changing the *length* is the hazard. Reassigning existing slots is completely safe, because no
element moves and the length never changes:

```python
temps = [18, 21, 19]
for i, t in enumerate(temps):
    temps[i] = t + 1
print(temps)             # -> [19, 22, 20]
```

### The two correct approaches

Build a new list, usually with a comprehension. This is the one to reach for by default:

```python
guests = ['ana', 'bo', 'cy', 'bo']
guests = [name for name in guests if name != 'bo']
print(guests)            # -> ['ana', 'cy']
```

If the caller needs the original object updated rather than a new one, assign the comprehension
into the full slice — `guests[:] = [name for name in guests if name != 'bo']` — for the reason
section 9 gets into.

Or iterate over a copy and mutate the original. The iterator then holds a position into a list that
nothing is shifting:

```python
guests = ['ana', 'bo', 'cy', 'bo']
for name in guests.copy():
    if name == 'bo':
        guests.remove(name)
print(guests)            # -> ['ana', 'cy']
```

This is correct but strictly more expensive, in two separate ways. The copy is O(n) extra space and
O(n) time up front: walking 100,000 elements took 0.79 ms directly and 0.98 ms via `.copy()`, with
the copy itself accounting for about 0.19 ms. Worse, each `remove` is another O(n) scan-and-shift,
so the loop is O(n²) overall. On a 20,000-element list where half the entries are removed, the
comprehension took 0.21 ms and the copy-and-remove loop took 246 ms — over a thousand times
slower, for the same answer. Prefer the comprehension unless you specifically need the mutations
to land on the original object as they happen.

A third form shows up in other people's code: deleting by descending index.

```python
guests = ['ana', 'bo', 'bo', 'cy']
for i in reversed(range(len(guests))):
    if guests[i] == 'bo':
        del guests[i]
print(guests)            # -> ['ana', 'cy']
```

This is correct for the same mechanical reason the copy is — a deletion at index `i` only shifts
elements *after* `i`, and you have already visited those. Recognize it when you read it. It is still
O(n²), and it is harder to see at a glance than the comprehension, so it is not what you should
write.

### Lazy transforms: map, filter, and itertools

The comprehension is the right default, and it has one cost that is easy to stop noticing: it
builds the whole result before anything downstream sees an element. `zip`, `enumerate` and
`reversed` do not, and they are three members of a much larger family with the same trait — each
returns an iterator holding a reference to its source plus whatever small state it needs, and
allocates nothing per element. Their size is therefore independent of how much data flows through
them. With `nums = list(range(1000))`:

| expression | `sys.getsizeof` |
| --- | --- |
| `[x for x in nums]` | 8856 |
| `nums[100:900]` | 6456 |
| `(x for x in nums)` | 200 |
| `islice(nums, 100, 900)` | 72 |
| `accumulate(nums)` | 72 |
| `zip(nums, nums)` | 64 |
| `map(str, nums)` | 56 |
| `pairwise(nums)` | 56 |
| `filter(None, nums)` | 48 |
| `chain(nums, nums)` | 48 |

`map(f, xs)` yields `f(x)` for each element. `filter(pred, xs)` yields the elements `pred` accepts,
and `filter(None, xs)` yields the ones that are truthy:

```python
prices = [100, 0, 104, 0, 99]
print(list(filter(None, prices)))      # -> [100, 104, 99]
print(list(map(abs, [-3, 4, -5])))     # -> [3, 4, 5]
```

Laziness alone does not make them faster. Over 100,000 elements, `list(map(str, nums))` took 3.21 ms
and `[str(x) for x in nums]` took 3.32 ms — a wash. Introduce a `lambda` and `map` loses outright,
because a comprehension evaluates its expression inline while `map` pays a call per element:
`list(map(lambda x: x * 2, nums))` took 2.84 ms against 1.40 ms for `[x * 2 for x in nums]`.
**Reach for `map` when the function already has a name; write a comprehension when you would have to
invent a `lambda` in order to use `map`.**

`itertools` supplies the rest of the family. `chain` walks several sequences as one without joining
them:

```python
from itertools import chain

morning = ['ana', 'bo']
evening = ['cy']
print(list(chain(morning, evening)))   # -> ['ana', 'bo', 'cy']
```

For two 500,000-element lists, `sum(a + b)` took 4.93 ms with a peak allocation of 8,000,032 bytes,
while `sum(chain(a, b))` took 3.84 ms with a peak of 80 bytes.

`pairwise` hands you each element alongside the next one, which is the whole of an adjacent-pair
walk without the index arithmetic:

```python
from itertools import pairwise

prices = [100, 104, 99, 99, 112]
print(list(pairwise(prices)))                # -> [(100, 104), (104, 99), (99, 99), (99, 112)]
print([b - a for a, b in pairwise(prices)])  # -> [4, -5, 0, 13]
print(list(pairwise([])), list(pairwise([1])))   # -> [] []
```

It yields `n - 1` pairs, and nothing at all for inputs of length 0 or 1 — the two boundary cases
you would otherwise have to get right by hand in `range(len(prices) - 1)`.

`accumulate` yields the running result of folding a function across the sequence, defaulting to
addition:

```python
from itertools import accumulate

print(list(accumulate([3, 1, 4, 1, 5])))        # -> [3, 4, 8, 9, 14]
print(list(accumulate([3, 1, 4, 1, 5], max)))   # -> [3, 3, 4, 4, 5]
```

You can write your own member of the family with a generator function. `yield` turns the function
into one that runs nothing when called — it hands back a generator object and executes the body
only as values are pulled out of it:

```python
import sys

def to_celsius(readings):
    for raw in readings:
        yield raw / 10 - 40

g = to_celsius([580, 601, 555])
print(sys.getsizeof(g))    # -> 208    no work done yet, and no output list
print(next(g))             # -> 18.0
print(list(g))             # -> [20.1, 15.5]
print(list(g))             # -> []     exhausted, like every iterator here
```

That last line is the price of the whole family, and you have already met it: **these objects are
cursors, so they are single-use, they have no length, and they cannot be indexed or reversed.**

```python
try:
    len(map(str, [1, 2, 3]))
except TypeError as e:
    print(e)               # -> object of type 'map' has no len()
```

So when you need the result twice, or need its length, or need to index into it, call `list(...)` on
it once and pay the O(n) deliberately. When you need it once and are feeding it straight into `sum`,
`min`, `max`, `any`, `all`, a `for` loop or another iterator, leave it lazy and the intermediate
list never exists.

### islice against a slice

This is where the family pays back what section 5 charged. `nums[a:b]` copies `b - a` pointers into
a fresh list before you touch a single element; `itertools.islice(nums, a, b)` yields the same
elements and builds nothing.

```python
import tracemalloc
from itertools import islice

nums = list(range(1_000_000))

tracemalloc.start()
total = sum(nums[200_000:800_000])
print(tracemalloc.get_traced_memory()[1])          # -> 4800032
tracemalloc.stop()

tracemalloc.start()
total = sum(islice(nums, 200_000, 800_000))
print(tracemalloc.get_traced_memory()[1])          # -> 104
tracemalloc.stop()
```

The two took 2.81 ms and 2.80 ms, which is run-to-run noise. **Same elements, same time, 4.8 MB of
peak allocation against 104 bytes** — that is the O(k) space from section 5 removed for free.

There is one shape where it reverses, and it comes from the same mechanism. A slice computes where
`a` is and copies from there; `islice` has only the iterator protocol to work with, so it reaches
`a` by pulling and discarding `a` elements one at a time. Taking a ten-element window from near the
end of a million-element list, `sum(nums[900_000:900_010])` took 0.07 us and
`sum(islice(nums, 900_000, 900_010))` took 1784.83 us.

So the rule is about the ratio, not about laziness being better: `islice` wins when you will consume
most of what you skip past, or when the source cannot be sliced at all. `islice` also refuses
negative bounds — `islice(nums, -1)` raises
`ValueError: Stop argument for islice() must be None or an integer: 0 <= x <= sys.maxsize.` — and
its step must be positive, so `nums[::-1]` and `nums[-3:]` have no `islice` spelling.

### Short-circuiting with any and all

`any` stops at the first truthy element and `all` stops at the first falsy one. Neither looks at the
rest.

```python
flags = [False] * 1_000_000
flags[0] = True
print(any(flags))      # -> True
```

That call took 0.015 us. Move the single `True` to the end and the identical call takes 1419.9 us,
roughly ninety-five thousand times longer — the gap is the short circuit, and it is the entire
reason to use `any` rather than build a list of booleans and inspect it.

That makes the bracket the most expensive character in the expression. A generator argument is
consumed lazily and stops early; a list comprehension argument is fully evaluated before `any` is
even called:

```python
calls = 0

def hot(t):
    global calls
    calls += 1
    return t > 30

temps = [12, 45, 18, 22, 31, 9, 40, 15]

calls = 0
print(any(hot(t) for t in temps), calls)     # -> True 2
calls = 0
print(any([hot(t) for t in temps]), calls)   # -> True 8
```

Both answer `True`; the second one called `hot` four times as often and allocated an eight-element
list to throw away. **Drop the brackets whenever a generator expression is the sole argument.**

The empty cases are worth committing to memory rather than re-deriving: `any([])` is `False` and
`all([])` is `True`. `all` returning `True` for nothing is the answer that makes it compose — a
condition no element violates is satisfied.


---

## 7. Length and capacity

Ask how long a collection is and there are two different honest answers. One is how many items it
could hold — how many numbered positions have been set aside for it. The other is how many items
are sitting in it right now. A box built for six sensor readings that currently holds four has both
a six and a four in it, and they mean entirely different things. The first number is the
**capacity**. The second is the **length**. Keeping them apart is the whole of this section,
because Python answers one of them loudly and the other one not at all.

### `len()` is a stored field, not a count-up

`len(nums)` is the length: the number of items currently present. It is not computed by walking the
list. Every list object carries its length in a field of its C-level struct (`ob_size`), updated
whenever the list changes, and `len()` reads that field and returns it.

**Reading the length is constant-time: the work does not scale with how many items there are.** You
can see it directly:

```python
import timeit

for n in (10, 256, 257, 1_000, 1_000_000, 50_000_000):
    lst = [0] * n
    best = min(timeit.repeat("len(lst)", globals={"lst": lst}, number=1_000_000, repeat=9))
    print(f"n={n:<12} {best * 1e3:.1f} ns per call")
    del lst

# -> n=10           7.0 ns per call
# -> n=256          7.2 ns per call
# -> n=257          10.3 ns per call
# -> n=1000         10.2 ns per call
# -> n=1000000      10.1 ns per call
# -> n=50000000     10.2 ns per call
```

Fifty million elements is fifty thousand times one thousand, and those two rows agree to a tenth of
a nanosecond. But there is a visible step between 256 and 257, it is about 3 ns wide, and it
reproduces run after run in any order the sizes are measured. It deserves an explanation rather
than a wave at noise.

It is not the length. What changed at 257 is the *return value*. CPython keeps one shared `int`
object for every value from -5 to 256 and hands out that same object every time (section 2), so
`len()` on a list of 256 returns something that already exists, while `len()` on a list of 257 has
to allocate a fresh `int` to carry the answer out. That allocation is the 3 ns, and it is the same
3 ns at 257 as at fifty million.

You can pin it on the answer rather than on the list by shrinking a list that was once huge and
timing the very same object again:

```python
import timeit

lst = [0] * 1_000_000
header = id(lst)
del lst[10:]                             # same list object, now ten items long

best = min(timeit.repeat("len(lst)", globals={"lst": lst}, number=1_000_000, repeat=9))
print(len(lst), id(lst) == header)       # -> 10 True
print(f"{best * 1e3:.1f} ns per call")   # -> 7.2 ns per call
```

Same object, same header, same field being read, and it is back in the fast row the moment its
answer is small enough to be a shared one. The field read itself is flat: above 256 the timings are
constant across five orders of magnitude, and the one step in the table is the cost of boxing the
number, not of counting it. So `while i < len(nums)` is safe: it does not quietly turn an O(n) loop
into an O(n²) one.

Be precise about what that does *not* claim. Calling `len()` a million times still costs a million
function calls, and that is real interpreter overhead:

```python
import timeit

setup = "prices = [0] * 100_000"
inline = "i = 0\nwhile i < len(prices):\n    i += 1"
hoisted = "n = len(prices)\ni = 0\nwhile i < n:\n    i += 1"

print(min(timeit.repeat(inline, setup, number=20, repeat=5)) * 1000 / 20)    # -> 1.60 ms
print(min(timeit.repeat(hoisted, setup, number=20, repeat=5)) * 1000 / 20)   # -> 0.97 ms
```

That is 6.3 ns per iteration in that run and 6.0 ns in a repeat: a fixed toll on an otherwise empty
loop body, not growth. `for i in range(len(nums))` calls `len` exactly once and pays it once.

### Capacity is real, and private

The element block behind a list is deliberately larger than the list needs, so that the next
`append` usually has somewhere to put its value. That spare room is the capacity. It lives in a
field named `allocated` on the C-level struct, and no expression in the language reports it.

You can back it out. `sys.getsizeof` returns the object header plus one pointer slot per allocated
position, at 8 bytes a slot:

```python
import sys

EMPTY = sys.getsizeof([])                       # -> 56, the header with no element block
SLOT = 8

def capacity(lst: list) -> int:
    return (sys.getsizeof(lst) - EMPTY) // SLOT

print(capacity([]), capacity([0]))              # -> 0 1
```

Two things make that arithmetic legitimate. A slot holds a *pointer*, which is why it is one
machine word wide — 8 bytes on the 64-bit build these numbers come from. And storing pointers is
also why `sys.getsizeof` on a list measures the list's own block and nothing that block points at:

```python
small = [0] * 3
big = [10**200] * 3

print(sys.getsizeof(small), sys.getsizeof(big))         # -> 80 80
print(sys.getsizeof(small[0]), sys.getsizeof(big[0]))   # -> 28 116
```

Three pointers cost three pointers whatever they point to. So `capacity` reports slots, not bytes
of payload, which is the number this section is about. Treat it as a measuring instrument only:
`allocated` is not exposed as an attribute, no method returns it, and nothing in Python lets you
set it directly.

### Where the capacity jumps

Grow a list by repeated `append` from empty and print the capacity every time it changes:

```python
lst = []
seen = -1
for n in range(41):
    c = capacity(lst)
    if c != seen:
        print(f"length {n:>2}   bytes {sys.getsizeof(lst):>3}   capacity {c:>2}   spare {c - n}")
        seen = c
    lst.append(n)
```

| length reached | bytes | capacity | spare slots |
|---:|---:|---:|---:|
| 0 | 56 | 0 | 0 |
| 1 | 88 | 4 | 3 |
| 5 | 120 | 8 | 3 |
| 9 | 184 | 16 | 7 |
| 17 | 248 | 24 | 7 |
| 25 | 312 | 32 | 7 |
| 33 | 376 | 40 | 7 |

Between those rows nothing happens to the memory at all: lengths 9 through 16 all report 184 bytes
and capacity 16. Six reallocations carried this list from 0 to 40 items.

### The rule that produces those jumps

When a list has to hold more than its block allows, CPython picks the new capacity from two numbers:
the length it must reach, and the length it is at now. There are two branches, and which one fires
depends on how big the jump is.

```python
def new_allocated(oldsize: int, newsize: int) -> int:
    if newsize == 0:
        return 0
    over = (newsize + (newsize >> 3) + 6) & ~3   # branch one: leave room to grow into
    if newsize - oldsize > over - newsize:       # is the jump bigger than that room?
        return (newsize + 3) & ~3                # branch two: round the request, keep nothing spare
    return over

print(new_allocated(0, 1), new_allocated(4, 5), new_allocated(8, 9))       # -> 4 8 16
print(new_allocated(16, 17), new_allocated(24, 25), new_allocated(32, 33)) # -> 24 32 40
```

Those six outputs are exactly the six capacities in the table, and all six came from branch one.
Check three by hand. Reaching length 5: `5 + (5 >> 3) + 6` is `5 + 0 + 6 = 11`, and `& ~3` clears
the low two bits, rounding 11 down to 8. Reaching length 17: `17 + 2 + 6 = 25`, rounded down to 24.
Reaching length 33: `33 + 4 + 6 = 43`, rounded down to 40.

**An `append` always takes branch one, because it asks for a single slot and branch one never offers
fewer than three.** The expression adds 6 before rounding down to a multiple of 4, and rounding down
to a multiple of 4 can subtract at most 3, so the spare it grants is at least 3 at every length. A
jump of one can never exceed that, and neither can `insert`, which also adds exactly one item.
Branch two therefore belongs entirely to the bulk operations — `extend`, `+=`, `*=`, slice
assignment — where a single call can ask for thousands of positions at once.

Watch it fire. Ten items in a list, then a thousand more in one call:

```python
b = [0] * 10
b.extend(range(1000))

print(len(b), capacity(b))            # -> 1010 1012
print(new_allocated(10, 1010))        # -> 1012
print((1010 + (1010 >> 3) + 6) & ~3)  # -> 1140, what branch one alone would have said
```

The jump was 1000 slots; branch one would have supplied only 130 spare on top of the 1010 needed.
CPython reads that as evidence the caller knows its own size and stops guessing: 1010 rounds up to
1012, and the list ends with two spare slots rather than 130. The `readings.extend(range(1000))` in
section 2, which took a three-element list to length 1003, lands the same way — branch two, and a
capacity of 1004.

Simulating both branches against `sys.getsizeof` gives zero mismatches for every length from 0 to
200,000 *reached by appending*, and zero across 2500 randomly sized `extend` calls onto non-empty
lists. The append-only walk exercises branch one and nothing else, which is exactly why the second
branch is easy to miss.

This rule is CPython's, not a promise the language makes, and the constants have been retuned
before. Everything measured here is CPython 3.14. What is stable across versions is the *shape* of
the rule, and that is the part worth internalising.

**The growth is geometric with a factor of 1.125, not a doubling.** The `newsize >> 3` term is
one-eighth of the size, so each new block is about nine-eighths of the old one; the `+ 6` only
matters while the list is tiny. At scale the ratio is exact — consecutive capacities measured near
a million elements are 741708, 834428, 938736, 1056084, each 1.1250 times the last. A modest factor
means more reallocations than a doubling would need, in exchange for far less memory sitting idle.
Reaching length 741709 allocates a block of 834428, leaving 92719 slots spare: about one ninth of
the block, where a doubling would have left one half of it empty.

### Why `append` is constant time on average

Most appends are cheap: there is a free slot, the value's pointer goes into it, `ob_size` goes up by
one. That is constant work. Occasionally there is no free slot, and the append must obtain a larger
block and move every existing element into it — work proportional to the current length.

The saving grace is that the two things scale against each other. Because capacity grows by a fixed
*factor*, the expensive copies get rarer at exactly the rate they get more expensive. Reaching
length 1000 costs a 1000-element copy and buys 128 free appends afterwards; reaching 8000 costs an
8000-element copy and buys 1004. Here is the count behind that:

```python
import sys, time

N = 1_000_000
lst, times, reallocs, prev = [], [], 0, sys.getsizeof([])
for i in range(N):
    t0 = time.perf_counter_ns()
    lst.append(i)
    times.append(time.perf_counter_ns() - t0)
    size = sys.getsizeof(lst)
    if size != prev:
        reallocs += 1
        prev = size

times.sort()
print(reallocs)                # -> 86
print(times[N // 2])           # -> 83     median nanoseconds
print(times[-1])               # -> 240125 slowest single append
```

Eighty-six reallocations across a million appends. Total elements copied over those 86 events, as
counted from the rule above, is 8,445,096 — about 8.4 per append, a constant multiple, not one
copy per element per append.

That constant is predictable rather than lucky. Each reallocation copies the whole list, and the
list at the *previous* reallocation was only 1/1.125, or 8/9, as long. Walk the copies backwards
from the last one and they form a geometric series with ratio 8/9:

    1 + 8/9 + (8/9)² + (8/9)³ + ...  =  1 / (1 - 8/9)  =  9

so the total copying is about 9 times the length at the final reallocation. In this run the final
reallocation fired at length 938,737, and 9 x 938,737 = 8,448,633 — within 0.05% of the 8,445,096
elements actually copied. It reads as 8.4n rather than 9n only because the last 61,263 appends
landed in already-allocated slots and copied nothing at all.

Nothing in that sum depends on how large n is. Run ten times as many appends and both the length at
the final reallocation and the total copying grow by the same factor; the multiplier stays 9. Total
work for n appends is therefore proportional to n, and the work per append averages out to a
constant. That is what "O(1) amortized" means.

Now the caveat the word "amortized" is carrying. The slowest single append in that run took 240
microseconds: roughly three thousand times the 83-nanosecond median. **Only the average across the
whole sequence is guaranteed; any individual `append` may take time proportional to the current
length.** Five repeats of that run put the worst case at 174, 188, 209, 240 and 287 microseconds,
since it also includes whatever the operating system charges for handing over the memory. The 86
reallocations, by contrast, came out identical every time. For reasoning about a solution's
complexity none of this matters. For a latency budget it can.

### Building at a known size allocates exactly

When a list is built from something whose length is known up front, the constructor sizes the block
once and leaves no slack:

```python
known = list(range(1000))
grown = []
for i in range(1000):
    grown.append(i)

print(capacity([0] * 1000))                # -> 1000   (8056 bytes)
print(capacity(known))                     # -> 1000   (8056 bytes)
print(capacity(list(known)))               # -> 1000   (8056 bytes)
print(capacity(known[:]))                  # -> 1000   (8056 bytes)
print(capacity([x for x in range(1000)]))  # -> 1100   (8856 bytes)
print(capacity(grown))                     # -> 1100   (8856 bytes)
```

Identical contents, identical length, 800 bytes apart. A comprehension does not know how many items
it will produce, so it grows the same way appending does and stops on whatever capacity the last
jump handed it — 1100, which is where 28 growths from empty leave you standing at length 1000.

There is no capacity hint independent of content. Nothing takes "this will end up holding a million
things" and sets a million slots aside while the list stays empty; capacity is only ever a
consequence of items you actually supplied. **What you can do is supply them all at once: hand a
sized iterable to `extend` on an empty list and the block is sized exactly, in a single
allocation.**

```python
src = range(1000)

exact = []
exact.extend(src)          # empty list, source of known length: one allocation, no slack

grown = []
for x in src:
    grown.append(x)

print(len(exact), capacity(exact))   # -> 1000 1000
print(len(grown), capacity(grown))   # -> 1000 1100
```

This is the same exact sizing the constructor does, reached on a list that already exists rather
than only at the moment of creation, which makes `out = []` followed by `out.extend(src)` a genuine
reserve-then-fill: one allocation, one copy, nothing spare. Two conditions attach to it. The list
must still be empty, since a non-empty one gets the branch-two rounding above instead, and the
source must be able to report its length. An odd count rounds up to the next even one, and a source
that cannot say how long it is falls back to growing:

```python
odd = []
odd.extend(range(999))
print(len(odd), capacity(odd))     # -> 999 1000

lazy = []
lazy.extend(x for x in range(1000))
print(len(lazy), capacity(lazy))   # -> 1000 1100
```

The other lever is to build the list at full size in one go, which is what `[None] * n` is for when
you want a fixed-size buffer to fill in by index:

```python
buf = [None] * 1000
print(len(buf), capacity(buf))    # -> 1000 1000
buf[0] = "first"
print(len(buf), capacity(buf))    # -> 1000 1000
```

Assigning into a position that already exists moves neither number. It overwrites a pointer in a
slot that was already counted, so it does no allocation and no copying — which is why writing into
a pre-sized list is the one way to fill a list with no reallocation at all.

### Shrinking gives the memory back

Capacity is not a high-water mark. Pop a thousand-element list down to empty and watch:

```python
lst = list(range(1000))
prev = capacity(lst)
while lst:
    lst.pop()
    c = capacity(lst)
    if c != prev:
        print(f"len={len(lst):<4} capacity {prev} -> {c}")
        prev = c

# -> len=499  capacity 1000 -> 564
# -> len=281  capacity 564 -> 320
# -> len=159  capacity 320 -> 184
# -> len=91   capacity 184 -> 108
# -> len=53   capacity 108 -> 64
# -> len=31   capacity 64 -> 40
# -> len=19   capacity 40 -> 24
# -> len=11   capacity 24 -> 16
# -> len=7    capacity 16 -> 12
# -> len=5    capacity 12 -> 8
# -> len=1    capacity 8 -> 4
# -> len=0    capacity 4 -> 0
```

Nothing shrinks until the length drops *below half* the capacity — at length 500 the block is
still 1000 slots — and then the same rule fires on the new length: `499 + 62 + 6 = 567`, rounded
down to 564. Then nothing again until 281, and so on. Twelve shrinks take the list down, against
the 28 growths that appending from empty to 1000 would have needed, and the block is released
entirely at length 0.

The half-empty threshold is there for the same reason the growth factor is geometric. If a block
were resized the moment one slot went spare, a loop that alternated `append` and `pop` across a
boundary would copy the entire list on every single call. The gap between "grow when full" and
"shrink when half empty" is slack that absorbs that oscillation, so `pop()` from the end is O(1)
amortized on exactly the argument `append` is. A list that briefly got large and then drained does
give the memory back, but it does not hand it back one slot at a time.

### A list that arrives as a parameter

Here is the practical payoff. When a function receives a list and no separate size argument, that
list is exactly the size of its data. Whatever spare capacity exists behind it is unreachable, so
from your side length and capacity coincide and there is only one number to care about:

```python
readings = []
for r in (18, 19, 21, 20, 22, 23, 21, 20, 19):
    readings.append(r)

print(len(readings))                    # -> 9
print(capacity(readings))               # -> 16
print(readings[len(readings) - 1])      # -> 19
print(list(range(len(readings))))       # -> [0, 1, 2, 3, 4, 5, 6, 7, 8]

try:
    readings[9]                         # slot 9 exists in the block, but not in the list
except IndexError as e:
    print(e)                            # -> list index out of range
```

Sixteen slots exist. Nine of them are yours. Index 9 is inside the allocated block and still raises
`IndexError`, because the length field is what bounds checking consults. There is no way to read a
spare slot, so there is no way to be confused by one.

Three consequences to carry into the problems. `len(nums)` is the count of real items, full stop —
never a capacity you have to correct for. The valid indexes are `0` through `len(nums) - 1`; the
length is a quantity of items, not the highest index. And iterating means covering `0` up to but
not including `len(nums)`, which is exactly what `range(len(nums))` yields and exactly what
`for x in nums` visits. There are no leftover positions, no uninitialised positions, and nothing to
skip: every index below `len(nums)` holds a value that was deliberately put there — unless you
preallocated placeholders, in which case the deliberate value is `None` and the count is yours to
keep. That case is next.

### When length stops meaning occupancy

Everything above rested on an assumption worth making explicit: that the list holds exactly the
items you put in it. For a list you grew from its contents — appended to, comprehended, extended
from a source — that is true by construction. The only way a position entered the length is that a
value went into it, so the length *is* the occupancy and there is nothing to track alongside it.
**Length equals occupancy for a list built from its contents, and only for such a list.**

Preallocation breaks the equality deliberately. `[None] * 6` is six real elements, so `len()`
reports 6 from the first moment and keeps reporting 6 however much of the buffer is meaningful. The
number of entries you care about is a second number, and maintaining it is your job:

```python
buf = [None] * 6
filled = 0                   # the next free position, and the count of real entries

for reading in (18.2, 19.0, 21.4):
    buf[filled] = reading
    filled += 1

print(len(buf))              # -> 6
print(filled)                # -> 3
print(buf)                   # -> [18.2, 19.0, 21.4, None, None, None]
print(buf[4] is None)        # -> True
```

`buf[4]` reads without complaint and gives you `None`. Nothing verifies that you filled positions in
order, nothing objects if you overwrite an entry that already held a reading, and nothing stops you
leaving position 2 alone and writing position 3 instead. The three positions still holding `None`
are gaps in your data, and `None` means "nothing here yet" only because you decided it does — the
language attaches no such meaning to it and will not warn you about one.

Recovering the occupancy from the buffer alone costs a pass over every position, which is precisely
why you keep the counter:

```python
print(sum(1 for slot in buf if slot is not None))   # -> 3
```

Right answer, six reads to get it. At a thousand positions holding fifteen entries it is a thousand
reads for an answer a single integer could have held — which is the box from section 1, and the
reason its fifteen DVDs had to be counted rather than looked up.

Name the trade and it stops being a trap. Preallocating buys you positions that are assignable
before you know what belongs in them, which is what a fixed-size buffer filled across several passes
or from scattered indexes actually needs. It costs you the guarantee that `len()` means occupancy,
and hands you a counter to carry in its place. Build from the contents instead and the guarantee
comes back: `len()` is the answer, and there is no second number.


---

## 8. The cost of every operation

The whole table first. It is worth memorising only if you can regenerate it, so the derivations
follow underneath.

| Operation | Time | What it actually does |
|---|---|---|
| `nums[i]`, `nums[i] = v` | O(1) | one bounds check, one pointer offset |
| `len(nums)` | O(1) | reads a stored field; nothing is counted |
| `nums.append(x)` | O(1) amortized | writes into spare capacity; occasionally reallocates |
| `nums.pop()` | O(1) amortized | drops the last pointer; occasionally shrinks the block |
| `nums.insert(i, x)` | O(n − i) | moves every element from `i` onward one slot right |
| `nums.pop(i)`, `del nums[i]` | O(n − i) | moves every element after `i` one slot left |
| `nums.remove(x)` | O(n) | scans for the first `x`, then shifts the tail |
| `x in nums` | O(n) | identity check then equality, one element at a time |
| `nums.index(x)`, `nums.count(x)` | O(n) | the same scan |
| `min(nums)`, `max(nums)`, `sum(nums)` | O(n) | one pass |
| `for x in nums` | O(n) | one pass, no copy |
| `nums == other` | O(n) | element by element until a mismatch |
| `nums < other`, `nums <= other` | O(n) | element by element until the first difference decides it |
| `nums[a:b]` | O(b − a) time **and space** | builds a new list |
| `nums[a:b] = other` | O(k) if `k == b − a`, else O(k + n − b) | equal lengths overwrite slots; a changed count slides the tail |
| `del nums[a:b]` | O(n − b) | slides the tail left over the hole |
| `nums.clear()`, `del nums[:]` | O(n) | drops a reference to every element |
| `nums.sort()` | O(n log n), **O(n) best** | in place; merges stretches already in order, plus a buffer of up to n/2 pointers |
| `sorted(nums)` | O(n log n), **O(n) best** | the same, plus a full copy of the list |
| `nums.reverse()` | O(n) time, O(1) space | swaps pointers in place |
| `nums[::-1]` | O(n) time **and space** | a new list |
| `reversed(nums)` | O(1) | a 48-byte lazy iterator |
| `nums.extend(other)`, `nums += other` | O(k) amortized | appends `k` items to `nums` itself |
| `nums + other` | O(n + k) time and space | a third list |
| `nums * k` | O(n·k) time and space | a new list of `n·k` pointers |
| `list(nums)`, `nums.copy()` | O(n) time and space | a new list |

Throughout, `n` is `len(nums)` and `k` is `len(other)`. "Amortized" is the word from the previous
section: an individual `append` may reallocate, but the reallocations are rare enough and the
growth pattern generous enough that a run of `m` appends costs O(m) in total. The two best cases in
the sort rows are not decoration; they are the subject of their own subsection below, and they
decide whether a benchmark of sorting means anything.

### One fact generates most of that table

A list holds its element pointers in one contiguous block, so position `i` is found by arithmetic.
That is why a read costs the same at any size:

```python
import timeit
for n in (100, 10_000, 1_000_000):
    setup = f"nums = list(range({n}))"
    read = min(timeit.repeat("nums[50]", setup=setup, number=1_000_000, repeat=7))
    print(n, round(read * 1000, 1), "ns per read")
# -> 100 5.6 ns per read
# -> 10000 5.6 ns per read
# -> 1000000 5.8 ns per read
```

**Call it 5.6 nanoseconds, and treat that as the reference cost of one interpreted element read for
the rest of the chapter**: a non-negative index, best of seven runs of a million reads, on this
machine. Wherever a later comparison says "the cost of reading one element", it means this number,
measured this way. Quoting a constant is only useful if the way it was obtained is fixed too.

Position within the list is irrelevant, exactly as the arithmetic predicts. What does cost something
is the *form* of the index:

| expression on a million-element list | time |
|---|---|
| `nums[0]` | 5.8 ns |
| `nums[500]` | 5.2 ns |
| `nums[500_000]` | 5.4 ns |
| `nums[999_999]` | 5.7 ns |
| `nums[-1]` | 8.9 ns |
| `nums[len(nums) - 1]` | 14.4 ns |

The four non-negative reads are the same number within measurement noise. A negative index costs
about 60 per cent
more because the length has to be fetched and added before the offset arithmetic can run — the
resolution rule is real work, not notation. That is still no reason to avoid it: `nums[-1]` remains
the right way to reach the last element, because spelling the same thing as `nums[len(nums) - 1]`
pays for a `len` call and an interpreted subtraction on top and lands at 14.4 ns.

Contiguity is also the entire cost story for everything else. **Any operation that changes the
population before position `i` must physically move every element after `i`, because slot `j` has
to keep holding element `j`.** Add at the end and nothing moves. Add at the front and all `n`
pointers slide one slot over. That sentence produces every O(n − i) row above, and it is why
`append`/`pop` are the cheap pair and `insert(0, x)`/`pop(0)` the expensive one.

The `n − i` is literal, not a flourish. Insert the same value into the same list at five different
positions and the cost falls off in a straight line as `i` moves right:

```python
import time
n = 1_000_000
for i in (0, 250_000, 500_000, 750_000, n):
    best = float("inf")
    for _ in range(30):
        nums = list(range(n))
        t = time.perf_counter()
        nums.insert(i, 0)
        best = min(best, (time.perf_counter() - t) * 1e6)
    print(f"insert at {i:>7}: {best:7.1f} us   ({n - i:>7} elements after it)")
# -> insert at       0:   270.3 us   (1000000 elements after it)
# -> insert at  250000:   203.3 us   ( 750000 elements after it)
# -> insert at  500000:   138.3 us   ( 500000 elements after it)
# -> insert at  750000:    69.1 us   ( 250000 elements after it)
# -> insert at 1000000:     0.3 us   (      0 elements after it)
```

Halve the number of elements sitting after the insertion point and you halve the cost. At the very
end there is nothing after the insertion point, so `insert(len(nums), x)` is just `append`. Deletion
runs the same curve in reverse: `del nums[10:20]` on a million elements measured 203.1 µs because
999,980 pointers slide left, while `del nums[999_990:]` measured 1.21 µs because nothing does. What
you index by is irrelevant; what matters is how much lives to the right of the edit.

The shift is not a Python loop. It is a single bulk memory move at C speed across a block of
8-byte pointers:

```python
import timeit
for n in (1_000, 100_000, 1_000_000):
    setup = f"nums = list(range({n}))"
    pair = min(timeit.repeat("nums.insert(0, 0); nums.pop()", setup=setup, number=1000, repeat=7))
    base = min(timeit.repeat("nums.pop(); nums.append(0)", setup=setup, number=1000, repeat=7))
    cost = (pair - base) * 1e6            # nanoseconds for one insert(0, x)
    print(n, round(cost), "ns", round(cost / n, 3), "ns per element moved")
# -> 1000 284 ns 0.284 ns per element moved
# -> 100000 27663 ns 0.277 ns per element moved
# -> 1000000 277367 ns 0.277 ns per element moved
```

Dead linear, at about 0.28 nanoseconds per element. That is the trap: shifting a million pointers
takes 0.28 ms, which feels instant, so the wall clock never warns you that you wrote an O(n)
operation. Put it in a loop and the quadratic term is already there, invisible, waiting for a
bigger input.

### Watching the quadratic appear

The experiment is to empty a list one element at a time, from the front or from the back. Both
loops call `pop` the same number of times and finish in the same state; the only difference is
which end they take from.

```python
import time

def drain(n, front):
    nums = list(range(n))
    t = time.perf_counter()
    while nums:
        nums.pop(0) if front else nums.pop()
    return (time.perf_counter() - t) * 1000

for n in (20_000, 40_000, 80_000, 160_000):
    print(n, round(drain(n, True), 2), round(drain(n, False), 2))
```

| n | `pop(0)` | growth | `pop()` | growth |
|---|---|---|---|---|
| 20,000 | 18.53 ms | — | 0.27 ms | — |
| 40,000 | 93.19 ms | ×5.0 | 0.56 ms | ×2.07 |
| 80,000 | 392.31 ms | ×4.2 | 1.10 ms | ×1.96 |
| 160,000 | 1594.31 ms | ×4.1 | 2.27 ms | ×2.06 |

Doubling `n` roughly quadruples the front version and roughly doubles the back version. Those two
columns are the two complexity classes made visible: draining from the back is n operations of
constant cost, while draining from the front is n operations whose cost starts at n and works
down, summing to n²/2 pointer moves. At 160,000 elements the two differ by 702×, and that
multiplier itself doubles every time the input does.

### Matching is identity first, then equality

Every scanning row in the table — `in`, `index`, `count`, `remove`, `==` — is described loosely as
"comparing elements". The precise rule is one step longer, and the extra step is visible.

**When a container looks for an element, it asks `is` before it asks `==`, and a hit on identity
ends the question.** The same rule holds inside a `set` or a `dict`, on top of the hash lookup: the
hash finds the slot, and an occupant that is the very same object matches without any comparison at
all.

The demonstration is a value that is not equal to itself. A float NaN — produced by
`float('nan')` — compares unequal to everything, including itself:

```python
n = float("nan")
print(n == n)                              # -> False
print(n in [n])                            # -> True
print(n in {n})                            # -> True
print([n] == [n])                          # -> True
print(float("nan") in [float("nan")])      # -> False
print(float("nan") in {float("nan")})      # -> False
```

`n in [n]` says the list found something it could never have matched by equality — `n == n` on the
line above is `False`. It found it by identity: the object being searched for is the object stored
in the slot, so the scan stops before equality is ever consulted. `[n] == [n]` succeeds for the same
reason, one level down, since comparing the two lists means comparing their elements and those
elements are one object. The last two lines run the same searches for a *different* NaN object,
which has no identity to fall back on, and equality duly says no.

Nothing about this is specific to NaN; it is just the value that makes the two questions disagree
without any help from you. A cheap way to watch the shortcut fire on ordinary objects is to make
equality refuse to run at all:

```python
class Loud:
    def __eq__(self, other):
        raise AssertionError("__eq__ ran")
    __hash__ = object.__hash__

b = Loud()
print([b] == [b])       # -> True    the elements are the same object
print(b in [b])         # -> True
print([b].index(b))     # -> 0
print(b in {b})         # -> True
```

Four operations that are documented in terms of equality, and `__eq__` never executed once. It
would execute the moment either side held a different object.

Two things follow. The first is practical: identity is cheap, so a search that finds the exact
object you already had in hand is faster than one that has to compare its way in. The second is a
correction to a natural assumption — `a == b` on two lists does not mean every pair of elements had
`__eq__` called on it, so a custom class cannot use `__eq__` as a reliable hook for "my object was
compared".

### Ordering compares element by element

Lists are ordered as well as compared for equality, and the rule is the one you would design
yourself: walk both lists in step, and the first position where the elements differ decides the
whole comparison. If one list runs out first and everything before that matched, the shorter one is
smaller.

```python
print([1, 2] < [1, 2, 3])                  # -> True    a prefix is smaller
print([1, 10] < [2])                       # -> True    position 0 decides; length never matters
print([1, 2, 3] < [1, 2])                  # -> False
print(["apple", "pear"] < ["apple", "plum"])   # -> True    "pear" < "plum"
print([] < [0])                            # -> True
print(sorted([[3, 1], [1, 9], [1, 2]]))    # -> [[1, 2], [1, 9], [3, 1]]
```

`[1, 10] < [2]` is the line worth staring at. Ten is larger than two, and the longer list is the
smaller one, because the comparison never reaches position 1: `1 < 2` already settled it. Lists are
not compared by length, by sum, or by their largest element.

The comparison stops at the deciding pair, which means it can succeed on lists that hold values it
could not order:

```python
print([1, "a"] < [2, 0])                   # -> True   decided at position 0, "a" never touched
try:
    [1, 2] < [1, "a"]
except TypeError as e:
    print(e)     # -> '<' not supported between instances of 'int' and 'str'
```

The first comparison works because position 0 decides it and the mismatched pair is never reached.
The second reaches position 1, where `2 < "a"` has no answer, and raises. Equality is more forgiving
— `1 == "a"` is simply `False`, so `==` between any two lists always returns a bool.

### Sorting has a best case

The complexity row says O(n log n), and read alone it suggests a fixed price per element. It is not.
`list.sort` uses Timsort, which begins by identifying stretches of the input that are already in
order — ascending, or strictly descending, which it flips in place — and then merges those stretches
together. **Input that already consists of ordered stretches costs a linear number of comparisons,
not n log n, and that is the single most important thing to know before timing a sort.**

The mechanism is easiest to see by counting comparisons rather than nanoseconds, since the count is
a property of the algorithm and not of the machine:

```python
import math, random

calls = 0

class Counted:
    __slots__ = ("v",)
    def __init__(self, v):
        self.v = v
    def __lt__(self, other):
        global calls
        calls += 1
        return self.v < other.v

def comparisons(values):
    global calls
    items = [Counted(v) for v in values]
    calls = 0
    items.sort()
    return calls

random.seed(7)
n = 100_000
shuffled = [random.random() for _ in range(n)]
ascending = sorted(shuffled)
descending = ascending[::-1]
disturbed = ascending[:]
for _ in range(n // 100):
    i, j = random.randrange(n), random.randrange(n)
    disturbed[i], disturbed[j] = disturbed[j], disturbed[i]

print(comparisons(shuffled))     # -> 1531722
print(comparisons(ascending))    # -> 99999
print(comparisons(descending))   # -> 99999
print(comparisons(disturbed))    # -> 271374
print(int(n * math.log2(n)))     # -> 1660964
```

| input, n = 100,000 | comparisons |
|---|---|
| random order | 1,531,722 |
| already ascending | 99,999 |
| exactly descending | 99,999 |
| ascending, then 1,000 random swaps | 271,374 |
| n·log₂n, for reference | 1,660,964 |

The random case lands just under n·log₂n, which is what the complexity row promises. Ordered input
costs exactly n − 1 comparisons: one pass establishes that the whole list is a single run, and there
is nothing to merge. Descending input costs the same n − 1, because a descending stretch is
recognised and reversed rather than sorted. Disturbing one per cent of a sorted list still costs
under a fifth of the random figure.

On the clock, with a million floats:

```python
import random, time

random.seed(7)
data = [random.uniform(-50, 150) for _ in range(1_000_000)]
ordered = sorted(data)

def best(src):
    out = float("inf")
    for _ in range(7):
        nums = src[:]
        t = time.perf_counter()
        nums.sort()
        out = min(out, (time.perf_counter() - t) * 1000)
    return out

print(round(best(data), 1))            # -> 139.0   random order
print(round(best(ordered), 1))         # -> 13.9    already ascending
print(round(best(ordered[::-1]), 1))   # -> 16.4    exactly descending
```

Ten times faster on ordered input. Keep that ratio in mind whenever you time a sort, because
`sort` mutates its argument: time it twice on the same list and the second run measures the best
case, not the operation. Section 11 turns that into a rule about benchmark setup, and the number it
reports there is this best case leaking into a measurement.

Three more properties of sorting are worth having by name.

**It is stable.** Elements that compare equal keep the order they were in. That is what makes
sorting by one field and then another produce a sensible combined order.

```python
records = [("banana", 3), ("apple", 3), ("cherry", 1), ("date", 3), ("elder", 1)]
print(sorted(records, key=lambda r: r[1]))
# -> [('cherry', 1), ('elder', 1), ('banana', 3), ('apple', 3), ('date', 3)]
```

The three items with count 3 come out in their original relative order — `banana`, `apple`, `date`
— not alphabetically. Nothing sorted them further, so nothing disturbed them.

**`key=` computes a sort value once per element**, not once per comparison, and the original
elements are what you get back. `reverse=True` reverses the ordering without breaking stability:
equal elements still come out in their original order rather than flipped.

```python
words = ["Delta", "alpha", "Charlie", "bravo"]
print(sorted(words))                       # -> ['Charlie', 'Delta', 'alpha', 'bravo']
print(sorted(words, key=str.lower))        # -> ['alpha', 'bravo', 'Charlie', 'Delta']
print(sorted(words, key=len, reverse=True))  # -> ['Charlie', 'Delta', 'alpha', 'bravo']
```

The first line is not a bug: uppercase letters sort before lowercase ones, so a plain sort of mixed
capitalisation is rarely what you meant. The third line puts the only 7-letter word first and leaves
the three 5-letter words in the order they arrived, which is stability under `reverse=True`.

**Elements must be mutually orderable, and the check happens at comparison time.** There is no
up-front validation:

```python
try:
    sorted([3, "a", 1])
except TypeError as e:
    print(e)     # -> '<' not supported between instances of 'str' and 'int'
```

Which is the same rule the previous subsection reached from the other direction. A sort is a long
sequence of `<` comparisons, so a list that cannot be compared pairwise cannot be sorted — and, as
with the list comparison, the error only appears if the offending pair actually gets compared.

### Membership testing is the most valuable row in the table

`x in nums` compares `x` against elements until something matches, so one test is O(n) — and O(n)
even when the list happens to be sorted, because the scan has no idea that it is. Inside a loop
over `m` items that is O(n·m). A `set` computes `hash(x)`, jumps straight to the one table slot
that could hold it, and compares only what it finds there, making each test O(1) on average:

```python
n = 16_000
catalogue = [f"sku-{i}" for i in range(n)]
discontinued = catalogue[::2]

live = [s for s in catalogue if s not in discontinued]   # 563.34 ms  -- quadratic
dset = set(discontinued)
live = [s for s in catalogue if s not in dset]           # 0.640 ms   -- linear
```

| n | list version | growth | set version |
|---|---|---|---|
| 1,000 | 2.78 ms | — | 0.037 ms |
| 4,000 | 36.58 ms | ×13.2 | 0.217 ms |
| 16,000 | 563.34 ms | ×15.4 | 0.640 ms |
| 64,000 | 9515.30 ms | ×16.9 | 3.260 ms |

Quadrupling `n` multiplies the list column by roughly 16, which is the signature of O(n²); the set
column never leaves single-digit milliseconds. The set timings include building the set. The two
versions return identical results — only the container being interrogated changed.

The set is not free, and the costs are worth naming:

- **Construction is O(n).** `set(range(100_000))` measured 1.406 ms, against 0.013 ms for 1000
  lookups into it — one build costs about as much as a hundred thousand queries. Build it once,
  outside the loop. Rebuilding it inside the loop restores exactly the quadratic behaviour you were
  removing.
- **Memory.** For 100,000 ints, `sys.getsizeof` reports 800,056 bytes as a list and 4,194,520 as a
  set — 5.2× more, because a hash table stays deliberately sparse.
- **Order and duplicates are gone.** `set([500, 3, 17, 999, 42])` prints `{3, 999, 42, 17, 500}`.
  If you need the surviving items in their original order, keep the list for output and use the set
  only for the test — which is exactly what the comprehension above does.
- **Equal values collapse regardless of type.** `{1, 1.0, True}` is `{1}`, and `1.0 in {1}` is
  `True`. A list scan has the same matching semantics, so this is not a behaviour change — but a set
  makes it visible by silently absorbing the duplicates.
- **O(1) is the average, not the guarantee.** Keys whose hashes land in the same region of the
  table get compared one after another, so lookups slow down when the hashes cluster. `hash(i)` is
  `i` for an int, so 100,000 ints spaced exactly `2**20` apart measured 49.2 ns per lookup against
  16.0 ns for 100,000 random ints — a constant factor, not a change of class, and you have to work
  at it to see even that.

What a set will not accept is anything unhashable, which rules out storing lists in one; section 10
covers that constraint and the tuple that gets around it, since it is really a question about which
container to choose rather than about what an operation costs.

Two neighbours of the set are worth knowing. When you need a value attached to each key rather than
a yes/no, a `dict` has the same lookup cost and carries the payload. And when the list is already
sorted and you would rather not pay for a second copy of the data, the `bisect` module turns the
scan into a binary search:

```python
import bisect, timeit

srt = list(range(1_000_000))
target = 999_999

scan = min(timeit.repeat("target in srt", globals=globals(), number=20, repeat=5)) / 20
def probe():
    i = bisect.bisect_left(srt, target)
    return i < len(srt) and srt[i] == target
search = min(timeit.repeat(probe, number=100_000, repeat=5)) / 100_000
print(round(scan * 1e6, 1), "us scanning")     # -> 5625.7 us scanning
print(round(search * 1e9, 1), "ns searching")  # -> 144.2 ns searching
```

O(log n) against O(n), no extra memory, and it needs the list to be sorted and to stay sorted —
inserting into the right place costs the O(n − i) shift from the top of the section.

### Cheap at both ends: `collections.deque`

Every O(n − i) row above exists because a list keeps its elements in one contiguous block. A `deque`
gives that up, storing elements in a chain of fixed-size blocks instead, so neither end needs a
shift. On 100,000 elements, best of five runs of 10,000 operations:

| operation ×10,000 | `list` | `deque` |
|---|---|---|
| add at the front, then remove from the other end | 282.33 ms | 0.17 ms |
| remove from the front, then add at the other end | 126.27 ms | 0.17 ms |

The list figures are the shift, paid ten thousand times: 28.2 µs for one `insert(0, x)` and 12.6 µs
for one `pop(0)` at this length, both linear in it and both far too small to notice on a single
call. The deque figures do not move with the container's size — repeating the same measurement on a
million elements gives 0.16 ms and 0.17 ms — because nothing beyond the end block is touched.

What it surrenders is the first row of the table. **Indexing into the middle of a deque is O(n) in
the deque's length, so the constant you save at the ends is charged back the moment you subscript**
— which is why the choice is a real one rather than a free upgrade. Section 10 measures the middle
index and covers the rest of the container: `rotate`, `maxlen`, memory per element, and the fact
that a deque refuses slicing outright.

### The costs no complexity table shows

Several operations hide a copy, and a copy is invisible in the timing if the machine has memory to
spare. `tracemalloc` measures it directly, reporting the high-water mark of bytes allocated while
an expression ran:

```python
import random, tracemalloc

def peak(expression):
    random.seed(7)
    nums = list(range(100_000))
    random.shuffle(nums)
    tracemalloc.start()
    tracemalloc.reset_peak()
    result = expression(nums)
    high = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return high

print(peak(lambda a: a[:]))          # -> 800008
print(peak(lambda a: a.reverse()))   # -> 0
print(peak(lambda a: sorted(a)))     # -> 1199840
print(peak(lambda a: a + a))         # -> 1600008
```

The full set of results on that 100,000-element list:

| Expression | Peak extra bytes | In place? |
|---|---|---|
| `nums[:]` | 800,008 | no — a new list |
| `nums[::-1]` | 800,008 | no — a new list |
| `nums.reverse()` | 0 | yes |
| `reversed(nums)` | 48 | no, and no copy either |
| `sorted(nums)` | 1,199,840 | no — the copy plus a merge buffer |
| `nums.sort()` | 399,832 | yes — merge buffer only |
| `nums + nums` | 1,600,008 | no — a third list |

Read those against 800,000 bytes, which is what 100,000 pointers occupy. A copy costs exactly one
list; `sorted()` costs a copy plus a merge buffer of up to half the list; `sort()` pays only the
buffer. The 48 bytes for `reversed()` are the iterator object itself — it holds a reference to the
original list and an index, and produces elements on demand.

Reversal is the clearest: `nums[::-1]` measured 0.236 ms and a full copy, `nums.reverse()` 0.016 ms
and nothing, `reversed(nums)` 0.00003 ms and 48 bytes. For sorting, the time difference is small
when comparisons dominate — 8.72 ms for `sorted()` against 8.62 ms for `sort()` on 100,000 random
floats — but the memory difference is threefold and permanent.

The `nums + other` row hides the sharpest cost of all, because it is the row you land on by
accident. Accumulating with `out = out + [x]` inside a loop rebuilds the whole result on every
iteration, copying 1 + 2 + … + n pointers, which is n(n+1)/2 — quadratic, from an operation the
table prices as merely linear. Measured, it takes 13.92 ms to accumulate 5,000 items, 69.04 ms for
10,000, 315.43 ms for 20,000 and 1379.41 ms for 40,000 — ×5.0, ×4.6 and ×4.4 for each doubling,
settling toward the ×4 that is the signature of a quadratic, the same shape as `pop(0)` above.
Writing `out += [x]` or `out.append(x)` instead keeps it
linear because neither one copies the accumulated result; section 9 has the mechanism, which is that
`+=` mutates the list already there while `+` builds a new one and rebinds the name.

Slice assignment has the same fault line — matching lengths rewrite slots, a changed count shifts
the tail:

```python
nums = list(range(100_000))
nums[10:20] = [0] * 10   # 0.032 us  -- 10 slots rewritten, nothing moves
nums = list(range(100_000))
nums[10:20] = [0] * 11   # 12.577 us -- one extra element, so 99,980 pointers move
```

That is a factor of nearly 400 between two lines that differ by a single element, and the reason is
the table row: `nums[a:b] = other` is O(k) when `k == b − a`, and O(k + n − b) otherwise.

### Complexity class is not speed

Two numbers already measured above sit about 20× apart for the *same* element: 0.28 ns to move one
pointer inside a bulk C memory move, 5.6 ns to read one element from interpreted Python. Work done
inside CPython's own C implementation is roughly an order of magnitude cheaper per element than the
same work written as a Python loop, and an order of magnitude buys a lot of `log n`.

```python
import random, time
random.seed(7)
nums = [random.uniform(-50, 150) for _ in range(1_000_000)]

sorted(nums)                     # 145.7 ms  -- O(n log n), entirely in C

out = []                         # 236.3 ms  -- O(n), one pass, interpreted
for x in nums:
    y = min(max(x, 0.0), 100.0)
    out.append(round(y, 1))
```

The linear pass loses. Sorting a million floats costs less than clamping and rounding a million
floats — and the sort is not being flattered by its best case here, since the input is in random
order. Moving that same loop inside a function brings it to 157.9 ms, since local variable access is
cheaper than global — still a loss. **Complexity tells you how cost grows; the constant factor
tells you what it costs at the size you are actually running.**

Two guards against over-applying that. The first is that the C advantage is not automatic. On a
million ints, `sum(nums)` beat an equivalent accumulation loop 2.27 ms to 12.32 ms, a rout — but
`nums.count(7)` measured 5.28 ms against a hand-written counting loop's 4.38 ms and lost. Summing
shifts a genuine arithmetic step per element into C, while counting performs one equality test per
element either way, so C has less to save. But that only explains why the margin is thin, not why it
reverses, and a reversal deserves evidence rather than a story.

Here is the evidence. The interpreter rewrites its own bytecode once a code path has run enough
times, replacing a general instruction with one specialised to the types it keeps seeing. Warm the
loop up on ints and disassemble it:

```python
import dis

def hand(nums, target):
    c = 0
    for x in nums:
        if x == target:
            c += 1
    return c

for _ in range(50):
    hand([1, 2, 3, 7] * 250, 7)

print([i.opname for i in dis.get_instructions(hand, adaptive=True) if "COMPARE" in i.opname])
# -> ['COMPARE_OP_INT']
```

`COMPARE_OP_INT` is a comparison that already knows both operands are ints and skips the generic
dispatch. `list.count` is compiled C that cannot specialise itself this way. So the prediction is
that the loop wins exactly on element types the interpreter has a specialised comparison for, and
loses on the ones it does not. Running the same pair over a million elements of five different
types, alongside the opcode each one specialises to:

| element type | `nums.count(t)` | hand-written loop | specialised comparison |
|---|---|---|---|
| `int` | 5.28 ms | 4.38 ms | `COMPARE_OP_INT` |
| `float` | 5.18 ms | 4.60 ms | `COMPARE_OP_FLOAT` |
| `str` | 6.09 ms | 5.75 ms | `COMPARE_OP_STR` |
| one-element `tuple` | 10.03 ms | 12.91 ms | none |
| one-element `list` | 11.56 ms | 14.58 ms | none |

The line falls exactly where the specialisation does. Three types have a dedicated comparison
instruction and the interpreted loop wins all three; two do not, the comparison becomes expensive
enough that C's saved dispatch overhead matters again, and `count` wins both. Five element types is
evidence, not proof — but it is a testable prediction that held, which is a different kind of claim
from the one it replaced.

The second guard is that growth rate wins in the end, by an unbounded margin. A 0.28 ns constant did
not save `pop(0)`, which was still 702× behind at 160,000 elements and falls further behind on
every doubling. Constant factors are worth a few multiples; a complexity class is worth an
arbitrary number of them, and the input decides which one you are being paid in.


---

## 9. Names, aliasing, and changing a list in place

### A name is a label bound to an object

Assignment does not build a container and does not copy anything. `temps = [18, 21, 19]` creates one
list object and binds the name `temps` to it. Assigning that name to a second name binds the second
name to the very same object, so the object now answers to two labels.

```python
temps = [18, 21, 19]
readings = temps

print(temps is readings)           # -> True
print(id(temps) == id(readings))   # -> True

readings.append(25)
print(temps)                       # -> [18, 21, 19, 25]
```

`readings.append(25)` never mentions `temps`, yet `temps` now has four elements, because there was
only ever one list. **A name tells you nothing about how many other names are bound to the same
object.** `id(obj)` returns an integer identifying an object for as long as it is alive, and `is`
compares those identities. Two names are aliases exactly when `a is b`.

The direction of the relationship matters: the name is attached to the object, not the other way
round. `del` proves it by removing a label and leaving the object standing:

```python
temps = [18, 21, 19]
readings = temps

del temps
print(readings)     # -> [18, 21, 19]

try:
    temps
except NameError as e:
    print(e)        # -> name 'temps' is not defined
```

`del temps` deleted a binding, not a list. The list is still there because `readings` still names
it. Only when the last name goes does the object become unreachable and get reclaimed.

### A slice is a copy, not a window

Aliasing is a whole-object relationship, and it is the only kind Python has. Two names can share a
list; two lists can never share part of one. A slice used as a value is a second list holding its
own copied pointers, independent of the original from the moment it exists:

```python
temps  = [18, 21, 19, 24, 22]
window = temps[1:3]

print(window, window is temps)   # -> [21, 19] False

window[0] = 99
print(temps)                     # -> [18, 21, 19, 24, 22]
temps[1] = 0
print(window)                    # -> [99, 19]
```

Neither write is visible from the other name. **A slice of k elements costs O(k) in time and
space because there is no way for it to cost less — a partial view of a list is not a thing that
exists.** The copy is real memory: for `big = list(range(1_000_000))`, `sys.getsizeof(big[:1000])`
is 8056 bytes and `sys.getsizeof(big[:100_000])` is 800056. Time tracks the same line; slicing
100,000 elements out of `big` measured 193.6 µs, and 200,000 elements 386.6 µs.

A slice on the *left* of an assignment is the opposite thing. `temps[1:3] = [0]` is a store into
`temps` itself, and a later subsection is about exactly that. Read a slice as a copy only when it is
being used as a value.

If you want a genuine window — a second handle onto part of one block of storage, where a write
through either handle is seen by both — you need a container that keeps its elements in a raw
block instead of as pointers. `memoryview` in section 10 is that tool, and it declines lists for
precisely this reason:

```python
try:
    memoryview([1, 2, 3])
except TypeError as e:
    print(e)   # -> memoryview: a bytes-like object is required, not 'list'
```

### is versus ==

`==` asks whether two lists hold equal elements. `is` asks whether there is one list or two. They
answer different questions, and they routinely disagree.

```python
a = [18, 21, 19]
b = [18, 21, 19]
c = a

print(a == b)   # -> True
print(a is b)   # -> False
print(a == c)   # -> True
print(a is c)   # -> True
```

`a` and `b` are two objects holding equal values; writing into one leaves the other untouched. `a`
and `c` are one object under two names. Reach for `==` when you mean "same contents", which is
nearly always, and keep `is` for genuine identity questions and for `x is None`.

The disagreement runs the other way too, and that is the more dangerous direction. Equal immutable
values are sometimes shared behind your back, so `is` can answer `True` for two names you never
deliberately aliased:

```python
a = 1000
b = 1000
c = int('1000')

print(a == b, a is b)   # -> True True
print(a == c, a is c)   # -> True False
```

`a` and `b` name one object because the compiler stored a single `1000` constant for the module and
handed it out twice; `c` was built at run time, so it is a second object. All three are equal. An
identity test used as a value test would therefore have passed twice and failed once on the same
number, which is why `is` is only ever a question about objects, never about values.

The sharing is not even stable across the ways you can run that code. Typed one statement at a time
at an interactive prompt, each line compiles on its own, no constant is shared, and `a is b` prints
`False` — same source, opposite answer. Nothing here is a rule to memorise; the rule is to stop
asking `is` about values.

One caution about `id()`: it identifies *live* objects only, and in CPython a freed address can be
handed out again.

```python
print(id([1, 2]) == id([3, 4]))   # -> True
a, b = [1, 2], [3, 4]
print(id(a) == id(b))             # -> False
```

The first list is discarded before the second is built, so the allocator reuses the address. Bind
both objects to names before comparing their ids.

### Passing a list to a function

Calling a function binds the parameter name to the same object the caller holds. Nothing is copied
at the boundary. Two consequences follow, and they point in opposite directions: **mutating the
object through the parameter is visible to the caller, while rebinding the parameter name only
re-labels a local name that disappears when the function returns.**

Here are two functions with identical bodies except for one line.

```python
def discount_rebind(prices):
    prices = [p * 0.9 for p in prices]      # binds the local name to a NEW list
    print('inside:', prices)

def discount_inplace(prices):
    prices[:] = [p * 0.9 for p in prices]   # writes through into the caller's list
    print('inside:', prices)

shop = [10.0, 20.0]
discount_rebind(shop)
print('after: ', shop)
# -> inside: [9.0, 18.0]
# -> after:  [10.0, 20.0]

shop = [10.0, 20.0]
discount_inplace(shop)
print('after: ', shop)
# -> inside: [9.0, 18.0]
# -> after:  [9.0, 18.0]
```

Both print the same thing inside. Only one of them changed anything the caller can observe. The
identity check shows precisely where the connection is severed:

```python
shop = [10.0, 20.0]
outer = id(shop)

def trace(prices):
    print(id(prices) == outer)   # -> True    same object on entry
    prices = [0.0]
    print(id(prices) == outer)   # -> False   the link is cut here

trace(shop)
```

A parameter is an ordinary local name that happens to start out bound to the caller's object. That
gives you exactly two channels back to the caller: mutate the object you were handed, or `return` a
new one and let the caller bind it. There is no third option, and in particular no assignment to a
bare parameter name can reach out of the function. The same reasoning covers every argument you
pass, not just lists — any mutable object arrives as an alias.

### nums = ... rebinds, nums[:] = ... overwrites

This is the distinction the rest of the section hangs on. `nums = something` changes which object
the name points at and leaves the old object exactly as it was. `nums[:] = something` leaves the
name alone and replaces the contents of the object the name already points at. An alias makes the
difference visible without any function call:

```python
a = [1, 2, 3]
b = a

a[:] = [9, 9]
print(a, b, a is b)   # -> [9, 9] [9, 9] True

a = [7]
print(a, b)           # -> [7] [9, 9]
```

The slice assignment reached through `a` and edited the object `b` also names. The plain assignment
walked `a` away and left `b` standing where it was.

Read the two statements by their left-hand sides. A bare name on the left is a *binding*: the
object on the right gets a label, and whatever the name held before is simply dropped. Anything
else on the left — `a[0]`, `a[1:3]`, `a[:]` — is a *store into an object*, which asks the existing
object to change itself and never moves the name.

`nums[:] = ...` is the widest of those stores: it replaces every slot at once. It accepts any
iterable, and the new contents need not be the same length as the old, because the list resizes to
fit:

```python
nums = [1, 2, 3]
alias = nums

nums[:] = range(5)
print(nums, len(nums), alias is nums)   # -> [0, 1, 2, 3, 4] 5 True

nums[:] = (x * 2 for x in nums)
print(nums, alias is nums)              # -> [0, 2, 4, 6, 8] True
```

Two costs are worth naming. The right-hand side is fully built before anything is written, so
`nums[:] = [f(x) for x in nums]` allocates a whole second list and then copies it in — the result
is in-place, the work is not. And the write itself touches every slot, so it is O(n) even when you
only meant to change one element; when one element is what you mean, `nums[i] = value` is the
cheaper store and reaches the caller just as well. `nums.clear()` followed by `nums.extend(...)`
gets you the same end state as slice assignment, one object throughout.

### Which operations mutate, and which build a new object

Every row below was run on `nums = [30, 10, 20]`, checking the list afterwards and inspecting the
return value.

| Expression | Mutates `nums` | Returns |
| --- | --- | --- |
| `nums.sort()` | yes | `None` |
| `sorted(nums)` | no | a new list |
| `nums.reverse()` | yes | `None` |
| `nums[::-1]` | no | a new list |
| `nums.append(9)` | yes | `None` |
| `nums.extend([9])` | yes | `None` |
| `nums += [9]` | yes | — |
| `nums.insert(0, 9)` | yes | `None` |
| `nums.remove(10)` | yes | `None` |
| `nums.pop()` | yes | the removed element |
| `nums.clear()` | yes | `None` |
| `nums *= 2` | yes | — |
| `del nums[0]` | yes | — |
| `nums[0] = 9` | yes | — |
| `nums[:] = [9]` | yes | — |
| `nums + [9]` | no | a new list |
| `nums * 2` | no | a new list |
| `nums[:]`, `nums.copy()`, `list(nums)` | no | a new list |
| `[x for x in nums]` | no | a new list |
| `reversed(nums)`, `enumerate(nums)` | no | a lazy iterator, not a list |

The pattern in the right-hand column is a convention worth leaning on: **a list method that changes
the list returns `None`**, so a returned value is your signal that a new object was built. `pop` is
the exception, and it returns the element it removed rather than the list. The convention also
produces one of the most common typos in Python:

```python
nums = [30, 10, 20]
nums = nums.sort()
print(nums)          # -> None
```

`sort()` did sort the list, then returned `None`, and the assignment threw the sorted list away by
rebinding the name to `None`.

### += mutates, x = x + y rebinds

`+=` on a list is not shorthand for `x = x + y`. `list.__iadd__` extends the existing object and
then rebinds the name to that same object; `+` builds a third list and rebinds the name to it. An
alias tells them apart:

```python
a = [1, 2]
b = a
a += [3]
print(a, b, a is b)     # -> [1, 2, 3] [1, 2, 3] True

a = [1, 2]
b = a
a = a + [3]
print(a, b, a is b)     # -> [1, 2, 3] [1, 2] False
```

Because `+=` is `extend` underneath, it also accepts any iterable, while `+` insists on a list:

```python
a = [1, 2]
a += 'xy'
print(a)                # -> [1, 2, 'x', 'y']

a = [1, 2]
try:
    a = a + 'xy'
except TypeError as e:
    print(e)            # -> can only concatenate list (not "str") to list
```

The costs separate too, though not all for the same reason. Building a 2000-element list, best of 7
runs of 200:

| Loop body | Time |
| --- | --- |
| `out.append(i)` | 25.5 µs |
| `out += [i]` | 71.7 µs |
| `out = out + [i]` | 2079.8 µs |

`+=` costs roughly 2.8× the append loop, and that is a constant factor: every step builds and then
discards the one-element list `[i]`. The third row is a different shape of problem. `out + [i]`
copies everything accumulated so far, so the total work is 1 + 2 + … + n — quadratic. At 2000
elements it is already about 80× the append loop, and the multiple keeps climbing with the length:
measured the same way, it is roughly 44× at 1000 elements and 163× at 4000. Section 8 prices both
against a larger list.

`*=` and `*` split the same way: `a *= 2` mutates in place, `a = a * 2` builds a new list.

That `+=` mutates *and then* rebinds is observable in one memorable case, where the rebinding half
fails after the mutation has already happened:

```python
config = ('sensors', [1, 2])
try:
    config[1] += [3]
except TypeError as e:
    print(e)            # -> 'tuple' object does not support item assignment
print(config)           # -> ('sensors', [1, 2, 3])
```

The list was extended, then the attempt to store the result back into the tuple slot raised.

### Why this decides correctness when the caller checks the input

Some functions are judged by what they return; others are judged by the state of the list they were
handed. When the requirement is "modify the input", the caller inspects its own list afterwards and
ignores whatever came back. Under that kind of check, a rebinding solution is wrong no matter how
correct its logic:

```python
def normalise(levels):
    levels = [min(v, 255) for v in levels]

def normalise_inplace(levels):
    levels[:] = [min(v, 255) for v in levels]

def check(fn):
    rgb = [300, 128, 64]
    fn(rgb)
    return rgb == [255, 128, 64]

print(check(normalise))           # -> False
print(check(normalise_inplace))   # -> True
```

Nothing raises, nothing prints a traceback about types, and the computed values were right in both
cases. The object the caller held was simply never touched. That is what makes the failure hard to
read: the arithmetic you were worried about worked, and the one line that mattered was the
assignment.

When the requirement is in-place, every statement that is supposed to matter has to write *through*
a name — `levels[:] = ...`, `levels[i] = ...`, `levels.sort()`, `levels.pop()`, `levels.reverse()` —
and never `levels = ...`. A quick self-check before you call it done: throw the return value away
and look only at the argument you passed in. If it is unchanged, the function did nothing, however
convincing its body looked.

The mistake mirrors, too. A function judged by its return value that also rearranges its argument
along the way is wrong even when the returned value is right, because it has left a change in the
caller's data that nobody asked for.

### Copy what you do not own; do not copy what you must change

The two habits are mirror images, and choosing between them is a matter of reading the contract.

A helper that is only supposed to *report* something must not leave the caller's data rearranged:

```python
def hottest(readings):
    readings.sort(reverse=True)     # side effect the caller never asked for
    return readings[0]

data = [3, 9, 5]
print(hottest(data), data)          # -> 9 [9, 5, 3]
```

The caller asked a question and got its data rearranged as payment. Take a copy first and the
answer is the same while the caller's list survives intact. Both spellings below work, and both
work for the same reason — the local name now points at an object nobody else can see:

```python
def hottest_sorted(readings):
    readings = sorted(readings, reverse=True)   # new list, name rebound to it
    return readings[0]

def hottest_copy(readings):
    readings = list(readings)                   # explicit copy, then mutate freely
    readings.sort(reverse=True)
    return readings[0]

data = [3, 9, 5]
print(hottest_sorted(data), data)   # -> 9 [3, 9, 5]
print(hottest_copy(data), data)     # -> 9 [3, 9, 5]
```

Note that `readings = sorted(readings, ...)` is the *same* rebinding that was a bug one subsection
ago. Nothing about the statement changed; the contract did. Rebinding is right when your job is to
produce a value and wrong when your job is to change the caller's object.

Section 3 covers what a copy does and does not duplicate — the short version is that these copies
duplicate the list, not the elements, so if the elements are themselves mutable you can still write
through into shared objects. For a list of numbers that distinction does not arise.

Three rules cover the cases you will meet:

- Copy when you were handed data you do not own and you need to reorder, filter, or otherwise
  disturb it to compute your answer.
- Do not copy when changing the caller's object *is* the job — there the defensive copy taken out
  of reflex is exactly the silent failure from the previous subsection.
- Copy nothing at all when you can avoid the mutation outright. `max(data)` answers the question
  above without sorting, without a copy, and in O(n) rather than O(n log n); the cheapest way to
  keep someone's data intact is not to touch it.

### Mutable default arguments

The same model explains a trap that looks unrelated. A default value is evaluated once, when the
`def` statement runs, and stored on the function object. Every call that omits the argument binds
the parameter to that one stored object.

```python
def log(reading, seen=[]):
    seen.append(reading)
    return seen

print(log(18))               # -> [18]
print(log(21))               # -> [18, 21]
print(log(19))               # -> [18, 21, 19]
print(log.__defaults__)      # -> ([18, 21, 19],)
```

There is no fresh list per call; there is one list, aliased by `seen` on every call, accumulating.
The fix is to store an immutable sentinel and build the list inside the body, where the code runs
once per call:

```python
def log(reading, seen=None):
    if seen is None:
        seen = []
    seen.append(reading)
    return seen

print(log(18), log(21))      # -> [18] [21]
print(log.__defaults__)      # -> (None,)
```

Use `is None` rather than `if not seen`, because an empty list the caller deliberately passed is
falsy and would be silently replaced. This is one of the few places where identity really is the
question being asked: you want to know whether this is the sentinel object, not whether it happens
to compare equal to something.

The sentinel version still hands the caller's own list straight to `append` when one is supplied,
which is the aliasing rule again rather than an exception to it:

```python
def log(reading, seen=None):
    if seen is None:
        seen = []
    seen.append(reading)
    return seen

mine = []
log(18, mine)
log(21, mine)
print(mine)                  # -> [18, 21]
```

That is usually what you want from an accumulator, but it is a mutation of an object you were
merely lent, so it belongs in the docstring. The same trap applies to any mutable default — `{}`,
`set()`, a list built by a call in the parameter list — and immutable defaults such as `0`, `None`,
`()`, or a string are safe for the same reason: shared or not, nothing can write into them.


---

## 10. When a list is the wrong container

A list keeps 8-byte pointers in a resizable block and reaches any position with one multiply and one
add. Four consequences fall out of that design, and each one is a door another container walks
through: the pointer costs bytes on top of the object it points at, the values themselves are
scattered rather than packed, the block only grows cheaply at its right-hand end, and positional
access is the single operation it is genuinely fast at. Everything below trades one of those away
for something else.

Not every entry is a replacement. `heapq` is a discipline imposed on an ordinary list, and `range`
and `str` are sequences you may be about to convert into a list without needing to.

### array.array: raw values, packed

`array.array` stores fixed-width machine values laid end to end. There are no pointers in the block
and no per-element Python objects behind it — just bytes. You choose the width and signedness with
a one-character **typecode** at construction, and the array enforces it forever after.

```python
import array
print(array.typecodes)                    # -> bBuwhHiIlLqQfd
print(array.array('i').itemsize)          # -> 4
```

| typecode | stores | bytes each |
|---|---|---|
| `b` / `B` | signed / unsigned char | 1 |
| `h` / `H` | signed / unsigned short | 2 |
| `i` / `I` | signed / unsigned int | 4 |
| `l` / `L` | signed / unsigned long | 8 |
| `q` / `Q` | signed / unsigned long long | 8 |
| `f` / `d` | float, double | 4 / 8 |
| `w` | single Unicode character | 4 |

Those widths are the machine's C types rather than fixed by the language: `l` is only guaranteed to
be at least 4 bytes and `q` at least 8, and both measure 8 here. Ask with `.itemsize` rather than
assume. `array.typecodes` also lists `u`, an older spelling of the character typecode that is
deprecated and scheduled for removal in Python 3.16; write `w`.

```python
import array
print(array.array('l').itemsize, array.array('q').itemsize)   # -> 8 8
print(array.array('w', 'hi'))                                 # -> array('w', 'hi')
```

The type is a hard constraint, not a hint:

```python
import array
readings = array.array('i', [5, 10, 15, 20])
readings[1] = 99
print(readings)                # -> array('i', [5, 99, 15, 20])
print(readings[1:3])           # -> array('i', [99, 15])   slicing returns an array

try:
    readings.append(1.5)
except TypeError as e:
    print(e)                   # -> 'float' object cannot be interpreted as an integer
try:
    array.array('b', [200])
except OverflowError as e:
    print(e)                   # -> signed char is greater than maximum
```

"Packed" is literal. The storage is exactly `len(a) * itemsize` bytes with nothing in between, and
`tobytes` hands you those bytes unchanged while `frombytes` reads them back.

```python
import array, sys
a = array.array('i', [1, 2, 3])
print(a.tobytes())
# -> b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00'
print(len(a.tobytes()) == len(a) * a.itemsize)   # -> True
print(sys.byteorder)                             # -> little

b = array.array('i')
b.frombytes(a.tobytes())
print(b)                                         # -> array('i', [1, 2, 3])
```

Three 4-byte values, twelve bytes, the low byte of each value first because this machine is
little-endian. That ordering belongs to the machine and not to the format, so an array written on
one machine and read on another may need `.byteswap()` to come back correct.

Now the memory. Compare a list against an `array('i')` holding the same values, using integers above
256 so none of them are the interpreter's preallocated small ints. The list's honest cost is its
pointer block *plus* the 28-byte `int` object behind each distinct pointer.

```python
import array, sys

def deep(seq):                                  # pointer block + the objects it reaches
    seen, total = set(), sys.getsizeof(seq)
    for x in seq:
        if id(x) not in seen:
            seen.add(id(x))
            total += sys.getsizeof(x)
    return total

for n in (0, 1, 4, 16, 1000, 1_000_000):
    vals = range(1000, 1000 + n)
    print(n, sys.getsizeof(list(vals)), deep(list(vals)),
          sys.getsizeof(array.array('i', [0]) * n))
```

| `n` | list, pointers only | list, pointers + ints | `array('i')` | ratio (deep list / array) |
|---|---|---|---|---|
| 0 | 56 | 56 | 80 | 0.70 |
| 1 | 72 | 100 | 84 | 1.19 |
| 4 | 88 | 200 | 96 | 2.08 |
| 16 | 184 | 632 | 144 | 4.39 |
| 1,000 | 8,056 | 36,056 | 4,080 | 8.84 |
| 1,000,000 | 8,000,056 | 36,000,056 | 4,000,080 | 9.00 |

**At a million elements the array is 9 times smaller; at zero elements it is larger, and at one
element the win is 16 bytes.** The array's empty header is 80 bytes against the list's 56, and that
deficit has to be paid off four bytes at a time. Below roughly a dozen elements the difference is
tens of bytes and not worth a thought. For large `n` the exact costs are `80 + 4n` for the array and
`56 + 36n` for a list of distinct ints, so the gap only becomes interesting when `n` is large.

One caveat on that table: `array.array('i', range(n))` over-allocates the way an append-grown list
does, reporting 4,091,948 bytes for a million elements rather than 4,000,080. The exactly-sized
construction above (`array.array('i', [0]) * n`) is the one with no slack.

What you do not get is faster access. The block holds raw bytes, not objects, so **reading an
element has to build a brand-new Python `int` on the spot** — the win is footprint, not speed.

```python
import array
a = array.array('i', [1000, 2000, 3000])
x, y = a[0], a[0]
print(x == y, x is y)      # -> True False   two separate objects, same value

l = [1000, 2000, 3000]
u, v = l[0], l[0]
print(u == v, u is v)      # -> True True    one object, two references
```

That allocation shows up on the clock. Indexing the middle of a million-element container, best of 7
runs of 200,000: the list took 5.7 ns and the array 14.2 ns. `sum()` over the same data took 2.41 ms
for the list and 4.88 ms for the array. Reach for `array.array` when you are holding tens of
millions of numbers and memory is the binding constraint. Not otherwise.

### bytes and bytearray

For data that genuinely is bytes — file contents, network frames, pixel channels — the
specialised pair is `bytes` (immutable) and `bytearray` (mutable). Both store exactly one byte per
element, with no pointers and no per-element objects behind them.

```python
import sys
frame = bytes([0, 1, 2, 255])
print(frame[0], len(frame))            # -> 0 4
print(sys.getsizeof(bytes(1000)))      # -> 1033     33 + n
print(sys.getsizeof(bytearray(1000)))  # -> 1057     56 + n
print(sys.getsizeof([0] * 1000))       # -> 8056

buf = bytearray(frame)
buf[0] = 99
print(buf)                             # -> bytearray(b'c\x01\x02\xff')

try:
    frame[0] = 99
except TypeError as e:
    print(e)   # -> 'bytes' object does not support item assignment
```

Both come out roughly 8 times smaller than the equivalent list, and their empty headers are small
enough — 33 bytes for `bytes`, 56 for `bytearray` — that the saving starts almost immediately
instead of after a break-even point.

The immutable/mutable split is the same split as tuple/list, with the same practical consequence:
`hash(b'abc')` works and `hash(bytearray(b'abc'))` raises `TypeError: unhashable type: 'bytearray'`,
so a `bytes` can key a dict and a `bytearray` cannot.

Two details bite people. Indexing yields an `int` while slicing yields a `bytes`, so `data[0]` and
`data[0:1]` are not comparable to each other. And `bytearray` is a full mutable sequence — `append`,
`extend`, `insert`, `del` all work, and `append` amortises against spare capacity exactly the way a
list's does — but every value that goes in is checked against `0..255` and rejected outside it.

```python
data = b'hi'
print(data[0], data[0:1])    # -> 104 b'h'
print(data[0] == b'h')       # -> False    an int is never equal to a bytes
print(data[0:1] == b'h')     # -> True

buf = bytearray(b'hi')
buf.append(33)
buf.extend(b'!!')
print(buf)                   # -> bytearray(b'hi!!!')

try:
    buf.append(256)
except ValueError as e:
    print(e)                 # -> byte must be in range(0, 256)
```

`bytes` is also what text becomes on the way to a file or a socket: `str.encode` produces it and
`bytes.decode` reverses the trip. `'naïve'.encode('utf-8')` is `b'na\xc3\xafve'` — five characters,
six bytes — which is the clearest reminder available that a `bytes` counts storage and a `str`
counts characters.

### str: an immutable sequence of characters

A `str` is a sequence like the others: `len`, indexing, negative indices, slicing, iteration, `in`.
It is also immutable, so none of its slots can be reassigned. Indexing yields a length-1 `str`
rather than a number, which is the one place it parts company with the pair above: `b'temperate'[0]`
is `116` and `'temperate'[0]` is `'t'`.

```python
label = 'temperate'
print(label[0], label[0:1], label[-1], len(label))   # -> t t e 9
print(label[0] == label[0:1])                        # -> True

raw = b'temperate'
print(raw[0], raw[0:1])                              # -> 116 b't'

try:
    label[0] = 'x'
except TypeError as e:
    print(e)     # -> 'str' object does not support item assignment
```

Immutability costs nothing until you accumulate. **Every transform of a `str` allocates a new one,
so a loop that grows a string one piece at a time re-copies everything it has built so far on every
step.** The fix is the one a list wants too: collect the pieces, join once at the end.

```python
parts = []
for piece in ['sensor', '-', '07']:
    parts.append(piece)
print(''.join(parts))                # -> sensor-07
print('-'.join(['12', '15', '19']))  # -> 12-15-19

try:
    ''.join(['a', 7])
except TypeError as e:
    print(e)     # -> sequence item 1: expected str instance, int found
```

The measurement is more interesting than the rule, because CPython defends the naive version part of
the way. When the accumulator is a plain local name holding the only reference to the string, the
interpreter resizes it in place instead of copying, and the loop stays near-linear. Put that same
accumulator anywhere else — an attribute, a slot in a list, a global — and the reference count is no
longer one, the in-place path is gone, and the copying comes back. Building a string from `n`
two-character pieces, best of 5:

| `n` | `out += piece` (local name) | `obj.s += piece` (attribute) | `''.join(parts)` |
|---|---|---|---|
| 10,000 | 0.23 ms | 1.42 ms | 0.10 ms |
| 20,000 | 0.46 ms | 4.85 ms | 0.19 ms |
| 40,000 | 0.95 ms | 24.82 ms | 0.40 ms |
| 80,000 | 2.10 ms | 127.80 ms | 0.79 ms |

The join column doubles when `n` doubles. The attribute column quadruples — that is the quadratic
shape, and by 80,000 pieces it is 162 times slower than joining. The local column is linear only
because of an optimisation you did not ask for and cannot see in the source, and it is still 2.7
times slower than joining. Collect and join rather than relying on the interpreter to notice.

### memoryview: a window, not a copy

Slicing a list, a `bytes`, or a `bytearray` allocates a new object holding copied data, so the cost
is proportional to the slice. `memoryview` wraps any object that exposes a raw buffer and hands you
slices that are pure bookkeeping — a start, a length, a stride — pointing into storage that was
already there.

```python
import sys
lst = [0] * 1_000_000
buf = bytearray(1_000_000)
mv  = memoryview(buf)

print(sys.getsizeof(lst[:500_000]))   # -> 4000056
print(sys.getsizeof(buf[:500_000]))   # -> 500057
print(sys.getsizeof(mv[:500_000]))    # -> 184
print(sys.getsizeof(mv[:1]))          # -> 184     same, regardless of length
```

Timed, best of 9: the list slice took 509.2 µs, the `bytearray` slice 8.2 µs, and the `memoryview`
slice 0.083 µs. **The memoryview slice is flat in both time and space because it copies nothing.**

Being a view is the whole point, so writes go straight through to the underlying buffer, and a view
onto immutable data refuses them:

```python
buf = bytearray(4)
mv = memoryview(buf)
mv[0] = 7
print(buf[0])                         # -> 7
print(memoryview(b'abc').readonly)    # -> True
```

`memoryview` works on `bytes`, `bytearray` and `array.array`, and reports the element format of
whatever it wrapped (`memoryview(array.array('i', [1,2])).itemsize` is 4). It does not work on a
list — `memoryview([1, 2, 3])` raises `TypeError: memoryview: a bytes-like object is required, not
'list'` — because a list has no raw buffer to point at, only pointers.

`cast` reinterprets the same bytes under a different typecode without touching them, which is how
you read a byte buffer as machine integers, and `tobytes` is the explicit copy for when you finally
do want one.

```python
raw = bytearray(8)
ints = memoryview(raw).cast('i')
ints[0] = 7
print(len(ints), ints.itemsize)   # -> 2 4
print(bytes(raw))                 # -> b'\x07\x00\x00\x00\x00\x00\x00\x00'
print(memoryview(b'abcdef')[2:5].tobytes())   # -> b'cde'
```

The cost of pointing into someone else's storage is that the storage may not move while you are
pointing at it. An outstanding view locks the underlying object against resizing, and the block only
lifts when every view is released.

```python
buf = bytearray(8)
mv = memoryview(buf)
try:
    buf.append(0)
except BufferError as e:
    print(e)          # -> Existing exports of data: object cannot be re-sized
mv.release()
buf.append(0)
print(len(buf))       # -> 9
```

That is worth knowing before you hand a view to code you did not write. Using the view as a context
manager releases it at the end of the `with` block and saves you the bookkeeping.

### tuple: the immutable sibling

A tuple is a list whose length and whose slots are both fixed at construction. What is frozen is
which objects the tuple points at, not those objects themselves: `t = ([1], 2)` will never point
anywhere else, and `t[0].append(3)` still works. Because the length is fixed, there is no spare
capacity to track and nothing to reallocate, so the elements live inline in the tuple object itself
instead of in a second block, and there is no `allocated` field. Watch the difference in how the two
grow:

```python
import sys
lst = []
for n in range(9):
    print(n, sys.getsizeof(lst), sys.getsizeof(tuple(range(n))))
    lst.append(n)
# -> 0 56 48
# -> 1 88 56
# -> 2 88 64
# -> 3 88 72
# -> 4 88 80
# -> 5 120 88
# -> 6 120 96
# -> 7 120 104
# -> 8 120 112
```

The list jumps in steps as it over-allocates; the tuple is exactly `48 + 8n` at every size, never a
byte more. Against an exactly-sized list the saving is a flat 8 bytes — real, but not a reason to
choose one.

The reason to choose one is **hashability**. A tuple of hashable elements is itself hashable, so it
can be a dict key or a set member; a list never can.

```python
palette = {(255, 128, 0): 'orange', (0, 0, 0): 'black'}
print(palette[(255, 128, 0)])         # -> orange

try:
    {[255, 128, 0]: 'orange'}
except TypeError as e:
    print(e)     # -> cannot use 'list' as a dict key (unhashable type: 'list')
```

Hashability is contagious in one direction only: `hash(([1], 2))` still raises
`TypeError: unhashable type: 'list'`, because the tuple hashes its elements. That is the same
mutability rule as the paragraph above, seen from the other side — the tuple's own slots are frozen,
so it can offer a stable hash only if everything it points at is frozen too.

### range: three integers and some arithmetic

A `range` is a sequence that stores no elements at all. It holds a start, a stop and a step, and
computes element `i` on demand as `start + i * step`. That is enough to be a complete read-only
sequence — `len`, indexing, negative indices, slicing, `reversed`, `in`, `.index` — at a footprint
that does not depend on how many elements it describes.

```python
import sys
r = range(0, 1_000_000, 5)
print(len(r), r[0], r[-1], r[3])          # -> 200000 0 999995 15
print(r[10:20:3])                         # -> range(50, 100, 15)
print(r.start, r.stop, r.step)            # -> 0 1000000 5
print(r.index(15), 15 in r, 16 in r)      # -> 3 True False
print(list(reversed(range(5))))           # -> [4, 3, 2, 1, 0]
print(sys.getsizeof(range(10)), sys.getsizeof(range(10_000_000)))   # -> 48 48

try:
    r[0] = 5
except TypeError as e:
    print(e)     # -> 'range' object does not support item assignment
```

Forty-eight bytes at ten elements and forty-eight at ten million. Slicing gives back a `range`
rather than a list, which section 5 uses to make a general point about what the type of a slice
tells you.

Membership is where the arithmetic pays off. Asking whether an `int` is in a range is a bounds check
and a remainder, not a walk. `9_999_999 in range(10_000_000)` measured 31.6 ns, while the same test
against `list(range(10_000_000))` took 56.1 ms — a factor near 1.8 million, with the range answering
from 48 bytes against 80,000,056 for the list's pointer block alone.

That shortcut is for integers only, and the fallback is worse than a list.
`9_999_999.0 in range(10_000_000)` walks the values one at a time and took 123.9 ms.

So whenever you are about to write `list(range(n))` and everything you will then do is walk it or
test it, **the `list(` and `)` are the entire cost and buy nothing.** Build the real list when you
need to mutate slots, or when something downstream genuinely requires a list.

### collections.deque: cheap ends, expensive middle

A `deque` is a doubly-linked chain of fixed-size blocks rather than one run of storage. Adding or
removing at either end touches only the end block. There is no tail to shift, ever.

```python
from collections import deque
d = deque(range(1_000_000))
l = list(range(1_000_000))
```

Best of 5 runs of 2,000 operations on those million-element containers:

| operation | `deque` | `list` |
|---|---|---|
| add + remove at the left end | 0.015 µs | 445.4 µs |
| add + remove at the right end | 0.019 µs | 0.015 µs |

Thirty thousand times faster at the left end, indistinguishable at the right. The bill arrives on
indexing, because reaching position `i` means walking the block chain from whichever end is nearer:

| access | time |
|---|---|
| `d[0]` | 8.2 ns |
| `d[999_999]` | 9.3 ns |
| `d[500_000]` | 50,964 ns |
| `l[500_000]` | 5.8 ns |

**Middle indexing is O(n) on a deque and it is not a small constant** — 51 µs, nearly 9,000 times
slower than the list. A deque also refuses slicing outright (`d[1:2]` raises `TypeError: sequence
index must be integer, not 'slice'`), and costs 8.25 bytes per element against the list's 8, because
each 64-element block carries two link pointers.

The end operations are spelled `append` / `pop` on the right and `appendleft` / `popleft` on the
left, and `rotate(k)` moves every element `k` places toward the right end in constant time per step,
wrapping around. A `deque` is therefore the container to reach for whenever you are consuming from
one end and adding at the other — a work queue, or a breadth-first traversal — since `list.pop(0)`
is exactly the shift-everything-down operation you are trying to avoid.

```python
from collections import deque
q = deque([1, 2, 3, 4, 5])
q.rotate(2)
print(list(q))                # -> [4, 5, 1, 2, 3]
q.rotate(-2)
print(list(q))                # -> [1, 2, 3, 4, 5]
print(q.popleft(), q.pop())   # -> 1 5
```

`maxlen` turns it into a fixed-size sliding window: once full, every push at one end discards from
the other.

```python
from collections import deque
window = deque(maxlen=3)
for reading in [10, 20, 30, 40, 50]:
    window.append(reading)
print(list(window))       # -> [30, 40, 50]
window.appendleft(5)
print(list(window))       # -> [5, 30, 40]
```

Note that the discard is silent. `maxlen` is a statement that only the last few elements matter, not
a guard against overflow, and if you needed the elements it dropped you will not be told.

### heapq: the smallest element, kept at index 0

`heapq` is not a container. It is a handful of functions that impose an ordering discipline on an
ordinary list, and the list stays an ordinary list throughout — print it, slice it, measure it, hand
it to anything that expects a list.

```python
import heapq
prices = [42, 7, 19, 3, 88, 25]
heapq.heapify(prices)
print(type(prices))              # -> <class 'list'>
print(prices)                    # -> [3, 7, 19, 42, 88, 25]
print(prices[0])                 # -> 3      the smallest, always
print(heapq.heappop(prices))     # -> 3
print(prices)                    # -> [7, 25, 19, 42, 88]
heapq.heappush(prices, 1)
print(prices)                    # -> [1, 25, 7, 42, 88, 19]
```

The discipline is a rule about index arithmetic: the element at `i` is no larger than the elements
at `2i + 1` and `2i + 2`. **That is the whole of a heap — a binary tree whose parent-child links are
computed from positions instead of stored as pointers, which works only because the slots are
contiguous and reachable by multiply-and-add.**

```python
import heapq
h = [42, 7, 19, 3, 88, 25, 11]
heapq.heapify(h)
print(h)   # -> [3, 7, 11, 42, 88, 25, 19]
print(all(h[i] <= h[2*i + 1] for i in range((len(h) - 1) // 2)))   # -> True
print(all(h[i] <= h[2*i + 2] for i in range((len(h) - 2) // 2)))   # -> True
```

The list is not sorted and is not trying to be — 88 sits ahead of 25. Only position 0 is promised.

Each push or pop repairs a single root-to-leaf path, so both are O(log n), and arranging an existing
list into heap order is O(n) rather than the O(n log n) that sorting it would cost. On a million
random integers:

| operation | time |
|---|---|
| `heapify` on a copy of the list | 21.7 ms, of which 2.4 ms is the copy |
| `sorted` on the same data | 138.1 ms |
| `heappush` + `heappop` pair, n = 1,000 | 178.5 ns |
| `heappush` + `heappop` pair, n = 1,000,000 | 346.8 ns |
| `min()` over the plain list | 6,913.4 µs |
| `bisect.insort` + `pop(0)` on a sorted list | 403.9 µs |

The push-pop pair grew by less than a factor of two while the data grew by a factor of a thousand;
that nearly flat curve is what O(log n) looks like on a clock. Both alternatives lose badly:
scanning for the minimum costs about 20,000 times more per removal, and keeping the list fully
sorted instead pays the O(n) shift on every insertion.

It is a min-heap and there is no `reverse` parameter — for largest-first, negate the values or use
`nlargest`. Elements are compared with `<`, so mixed types raise, and a tuple attaches a payload to
a priority with the first element deciding.

```python
import heapq
print(heapq.nsmallest(3, [42, 7, 19, 3, 88, 25]))   # -> [3, 7, 19]
print(heapq.nlargest(2, [42, 7, 19, 3, 88, 25]))    # -> [88, 42]

tasks = [(3, 'rinse'), (1, 'wash'), (2, 'soak')]
heapq.heapify(tasks)
print(heapq.heappop(tasks))                         # -> (1, 'wash')
```

A heap costs exactly what its list costs — `sys.getsizeof` is unchanged by `heapify`, since there is
no wrapper object and no second block. Reach for it when the operation you keep repeating is "give
me the smallest one and take it out".

### set and dict: when the operation is not positional

If what you actually do most is ask "have I seen this value" or "what is stored under this key",
position is not the question and a list is the wrong answer. Both `set` and `dict` hash the value to
compute where it lives, so the lookup does not depend on how much is stored.

Membership tests against 100,000 integers, best of 5 runs of 200:

| test | time |
|---|---|
| `x in list` (present, halfway) | 307.3 µs |
| `x in list` (absent) | 612.9 µs |
| `x in set` | 0.010 µs |
| `k in dict` | 0.009 µs |

Roughly 60,000 times faster, and the gap grows with size because only one side grows at all. The
list has to compare its way along until it finds the value or runs out, which is why the absent case
costs twice the halfway case; the set and the dict compute one hash and look in one place.

The price is memory, ordering, and what you are allowed to store. Those 100,000 integers cost
800,056 bytes as a list, 4,194,520 as a set and 5,242,960 as a dict — the hash table keeps a large
fraction of its slots empty so that collisions stay rare. Those three figures are container overhead
only; the same 100,000 `int` objects sit behind all three, so the comparison is fair, but none of
the numbers is the total.

Ordering: dicts preserve insertion order, sets do not, and neither is positional. A set refuses
subscripting outright, and `d[3]` on a dict means the key `3`, never the fourth item. And every
element of a set or key of a dict must be hashable, which is where the tuple from two subsections
ago earns its keep.

```python
seen = {1, 2, 3}
try:
    seen[0]
except TypeError as e:
    print(e)     # -> 'set' object is not subscriptable

try:
    seen.add([4])
except TypeError as e:
    print(e)     # -> cannot use 'list' as a set element (unhashable type: 'list')
```

The practical rule: an `x in nums` inside a loop over `nums` is quadratic, and converting `nums` to
a set beforehand makes it linear. Build the set once, outside the loop — rebuilding it inside gets
you the quadratic cost back with extra allocation on top.

Two neighbours of these two change answers often enough to name. The first is
`collections.Counter`, for when the question is "how many times does each value appear". It is a
`dict` subclass that answers in one linear pass, where calling `list.count` once per distinct value
rescans the entire list every time.

```python
from collections import Counter
readings = [12, 15, 12, 19, 15, 12]
counts = Counter(readings)
print(counts)                    # -> Counter({12: 3, 15: 2, 19: 1})
print(counts[12], counts[99])    # -> 3 0      a missing key counts zero
print(99 in counts)              # -> False    and reading it did not insert it
print(counts.most_common(2))     # -> [(12, 3), (15, 2)]
```

Counting `n` integers drawn from `n` possible values:

| `n` | `{x: xs.count(x) for x in set(xs)}` | `Counter(xs)` |
|---|---|---|
| 5,000 | 93.2 ms | 0.14 ms |
| 10,000 | 368.8 ms | 0.28 ms |
| 20,000 | 1,484.9 ms | 0.55 ms |

Four times the work for twice the data on the left against twice the work for twice the data on the
right: quadratic against linear, and 2,700-fold apart by 20,000 elements.

The second is `bisect`, for when the list is already sorted and you would rather not pay for a
second copy of the data. `bisect_left` and `bisect_right` locate where a value belongs in O(log n)
probes — the leftmost and rightmost valid insertion points respectively — and `insort` puts it
there.

```python
import bisect
prices = [10, 20, 20, 30]
print(bisect.bisect_left(prices, 20), bisect.bisect_right(prices, 20))   # -> 1 3
i = bisect.bisect_left(prices, 25)
print(i, i < len(prices) and prices[i] == 25)   # -> 3 False    not present
bisect.insort(prices, 25)
print(prices)                                   # -> [10, 20, 20, 25, 30]
```

Section 8 prices that search against a scan. The comparison that belongs here is `bisect` against
`set`: on a million sorted integers a set lookup took 21.7 ns and a `bisect_left` probe 132.6 ns,
but the list occupied 8,000,056 bytes against the set's 33,554,648. **Six times slower per lookup,
four times smaller, and the order is preserved** — which is the trade whenever the data is already
sorted and large. Keeping it sorted is the part that is not free: `insort` is O(log n) to find the
position and O(n) to shift, measured at 261.4 µs per insertion at a million elements.

### numpy.ndarray

For numeric work at scale the answer is `numpy.ndarray`: contiguous typed storage like
`array.array`, but multidimensional, and with arithmetic that runs as a single compiled loop over
the whole buffer instead of one interpreted step per element. That vectorisation is the real
difference: a vectorised operation never builds one Python object per element, which is exactly the
cost you measured on `array.array` above. It is a third-party library rather than part of the
standard library, and it is not installed here — `import numpy` in this environment raises
`ModuleNotFoundError: No module named 'numpy'`. Know it exists and reach for it in numerical code;
do not expect it in a practice or interview environment.

### Choosing

| what you do most | reach for |
|---|---|
| index, append, iterate in order | `list` |
| test membership, deduplicate | `set` |
| look up a value by key | `dict` |
| count occurrences of many values | `collections.Counter` |
| search a collection you keep sorted | `bisect` over a `list` |
| repeatedly take the smallest | `heapq` over a `list` |
| use the sequence as a dict key or set member | `tuple` |
| walk or test a span of integers | `range` |
| build a string out of many pieces | a `list` of pieces, then `''.join` |
| push and pop at both ends, or keep a fixed-size window | `deque` |
| hold tens of millions of same-typed numbers | `array.array` |
| handle raw byte data | `bytes` / `bytearray` |
| slice a large buffer repeatedly without copying | `memoryview` |
| arithmetic across whole numeric arrays | `numpy.ndarray` |

For interview-style array problems the built-in `list` is essentially always right. The inputs are
lists, the outputs are lists, the sizes are small enough that a 9x memory factor is irrelevant, and
the operations asked for are exactly the ones a list is fast at. The substitutions that regularly
change an answer from too slow to fast enough make a short list: a `set` for membership, a `Counter`
for tallies, `''.join` for accumulated text, and `heapq` when what you keep asking for is the
smallest thing. The rest of this section is context, not advice. That is still worth having:
choosing `list` because you priced the alternatives is a different act from choosing it because it
is the only container you know.


---

## 11. Measuring instead of guessing

Every claim in the preceding sections arrived with a number attached, and the numbers came from
somewhere. This section is that somewhere: how to get a timing you can defend, how to tell a linear
operation from a quadratic one without knowing what either does, and how to find out what a
structure really costs in memory. Everything below was measured on CPython 3.14.4 on an arm64
machine, which is a caveat the last subsection turns into a rule.

### One reading of the clock is not a measurement

Start the clock, do the thing, stop the clock. Here is that method applied to a list index — an
operation section 8 established as O(1) and clocked in single-digit nanoseconds:

```python
import time

nums = list(range(1000))
for _ in range(8):
    t0 = time.perf_counter_ns()
    nums[500]
    print(time.perf_counter_ns() - t0, end="  ")
print()
# -> 458  291  125  125  83  83  42  84

print(time.get_clock_info("perf_counter").resolution * 1e9)   # -> 41.666666666666664
```

Eight readings of the same operation spanning 42 to 458 nanoseconds, a factor of 11. Two separate
things are wrong here. Every reading is a multiple of about 41.7 nanoseconds, because that is the
clock's resolution on this machine — the readings are quantised, and the quantum is larger than the
thing being measured. And the two `perf_counter_ns` calls themselves cost more than the indexing
does, so even the smallest reading is mostly measurement apparatus.

**A single reading gives you your operation plus the clock plus whatever else the machine chose to
do during that microsecond, with no way to separate them.** The real cost of that index, measured
properly, is 7.79 nanoseconds — under one tick of the clock you tried to read it with.

The fix is to run the operation many times inside one timed region, so the per-operation cost is a
division rather than a clock reading, and then to do that whole thing several times, so you can see
the spread. That is what `timeit` is for.

### `timeit.repeat`, and why you quote the minimum

`timeit.repeat(stmt, setup, number=N, repeat=R)` runs `stmt` `N` times inside one timed region and
returns `R` such totals. You get a distribution, not a point:

```python
import timeit

totals = timeit.repeat("sum(nums)", "nums = list(range(100_000))", number=100, repeat=15)
per_call = [t * 1000 / 100 for t in totals]
print(f"min {min(per_call):.4f}  mean {sum(per_call)/len(per_call):.4f}  max {max(per_call):.4f}")
# -> min 0.2034  mean 0.2150  max 0.2265        milliseconds per sum()
```

Which of those three do you quote? Run the same measurement again while thirty busy processes
compete for this machine's ten cores, and the answer stops being a matter of taste:

| | min | mean | max |
|---|---:|---:|---:|
| idle machine | 0.2034 ms | 0.2150 ms | 0.2265 ms |
| under competing load | 0.2059 ms | 0.2258 ms | 0.4062 ms |

The maximum rose 79%. The mean rose 5%. The minimum rose 1.2%, which is inside its own run-to-run
noise. **Interference can only ever make your code look slower, never faster, so the minimum is the
reading with the least contamination in it and the only one that reproduces.** A mean estimates your
code plus the machine's mood. A minimum estimates your code.

Two honest qualifications. The minimum is optimistic by construction — it is the run that got the
warmest caches and the luckiest scheduling, so it is a floor on cost, not a typical cost. And it
discards exactly the information a latency budget needs: section 7's worst single `append` took some
five thousand times the median, and no minimum would ever have shown you that. When tail behaviour
is the question, look at the maximum on purpose.

One thing `timeit` does silently is worth knowing. It disables the cyclic garbage collector for the
duration of each timed region and restores it afterwards. That makes results repeatable, and it
makes allocation-heavy code look better than it will behave:

```python
import gc, time

def build():
    return [[0] * 10 for _ in range(200_000)]

def best(gc_on):
    out = float("inf")
    for _ in range(5):
        gc.enable() if gc_on else gc.disable()
        gc.collect()
        t0 = time.perf_counter()
        result = build()
        out = min(out, time.perf_counter() - t0)
        del result
    gc.enable()
    return out * 1000

print(round(best(True), 2), round(best(False), 2))   # -> 19.09 8.68
```

Creating 200,000 small lists costs 19.1 ms with the collector running and 8.7 ms without it. A
`timeit` number for that code is the 8.7; your program will experience the 19.1.

For a single expression there is a command-line form that needs no file at all:

    python -m timeit -s "nums = list(range(10_000))" "nums.index(9_999)"

It picks the loop count itself and prints `N loops, best of 5: T per loop` — `best of` being the
minimum, the same statistic for the same reason. Reach for it when you have one question; reach for
the harness below when you are comparing several forms, because a comparison is only meaningful if
every candidate got the same setup and the same loop count.

### Keep construction out of the timed region

The most common way to produce a confidently wrong number is to build the input inside the timed
statement. You then measure the construction as well, and construction is frequently the larger half:

```python
import timeit

both = min(timeit.repeat("nums = list(range(10_000)); nums.count(7)", number=1000, repeat=7))
op   = min(timeit.repeat("nums.count(7)", "nums = list(range(10_000))", number=1000, repeat=7))
made = min(timeit.repeat("nums = list(range(10_000))", number=1000, repeat=7))

print(round(both * 1e3, 2), round(op * 1e3, 2), round(made * 1e3, 2))   # -> 103.8 36.11 68.26
```

Microseconds per iteration. The scan costs 36.11; the naive measurement reports 103.8, inflating it
2.9x, and 66% of what it reported was `list(range(10_000))`. The `setup` argument exists precisely
for this — it runs outside the clock.

The second trap is subtler and bites whenever the operation mutates its input. `setup` runs **once
per repeat, not once per execution**, which you can check directly:

```python
import timeit

calls = {"setup": 0, "stmt": 0}
timeit.repeat(lambda: calls.__setitem__("stmt", calls["stmt"] + 1),
              setup=lambda: calls.__setitem__("setup", calls["setup"] + 1),
              number=10, repeat=3)
print(calls)      # -> {'setup': 3, 'stmt': 30}
```

Three setups, thirty statements. So an input built in `setup` is shared by all ten executions, and if
the first execution changes it, the other nine measure something else entirely:

```python
import random, timeit

random.seed(7)
data = [random.random() for _ in range(100_000)]
env = {"data": data}

reused = min(timeit.repeat("nums.sort()", "nums = data[:]", globals=env, number=10, repeat=7))
fresh  = min(timeit.repeat("nums = data[:]; nums.sort()", globals=env, number=10, repeat=7))
copy   = min(timeit.repeat("nums = data[:]", globals=env, number=10, repeat=7))

print(round(reused * 100, 3))          # -> 0.987 ms   nine of the ten sorts got sorted input
print(round((fresh - copy) * 100, 3))  # -> 8.383 ms   the real cost
```

The first form understates the sort by 8.5x, because after execution one the data is in order and
CPython's sort detects the ordered run and does almost nothing. When the operation mutates, the input
has to be rebuilt inside the timed region and the rebuild subtracted — which is what the `copy` term
is doing.

### A harness worth keeping

Three functions cover nearly everything. Paste them into a scratch file and stop rewriting them.

```python
import math
import timeit


def bench(stmt, setup="pass", *, env=None, number=None, repeat=7):
    """Best-case seconds for one execution of `stmt`. The setup is never timed."""
    timer = timeit.Timer(stmt, setup, globals=env)
    if number is None:
        number, _ = timer.autorange()          # smallest 1/2/5 x 10**k giving a total over 0.2 s
    return min(timer.repeat(repeat=repeat, number=number)) / number


def compare(cases, setup="pass", *, env=None, unit="us", **kw):
    scale = {"s": 1, "ms": 1e3, "us": 1e6, "ns": 1e9}[unit]
    times = {name: bench(stmt, setup, env=env, **kw) for name, stmt in cases.items()}
    fastest = min(times.values())
    for name, t in sorted(times.items(), key=lambda kv: kv[1]):
        print(f"{name:<20}{t * scale:9.3f} {unit}   {t / fastest:4.2f}x")


def growth(make, run, sizes, repeat=5):
    """Time run(data) at each size and report the ratio between neighbouring sizes."""
    previous = None
    for n in sizes:
        data = make(n)                          # built before the clock starts
        t = min(timeit.repeat(lambda: run(data), number=1, repeat=repeat))
        if previous is None:
            print(f"n = {n:<9}{t * 1e3:10.3f} ms")
        else:
            r = t / previous
            print(f"n = {n:<9}{t * 1e3:10.3f} ms   x{r:5.2f}   exponent {math.log2(r):.2f}")
        previous = t
```

`autorange` chooses the loop count for you, so `number` is never a guess; the keyword is spelled
`env` rather than `globals` only to keep the builtin reachable inside the function body.

These three do not all measure the same kind of thing, and the difference has to be said out loud in
a section about not fooling yourself. `bench` and `compare` hand `timeit` a **statement string**,
which it compiles into the body of the timing loop — what you measure is the statement. `growth`
hands it a **callable**, and a callable has to be called, so what you measure is the statement plus
one Python function call. Time the same work both ways and the gap is visible:

```python
import timeit

nums = list(range(1000))
big = list(range(100_000))


def index_call():
    nums[500]


def sum_call():
    sum(big)


def both(stmt, fn, number):
    """The same work, timed as a statement and as a callable."""
    a = min(timeit.repeat(stmt, globals=globals(), number=number, repeat=15)) / number
    b = min(timeit.repeat(fn, number=number, repeat=15)) / number
    print(f"{stmt:<12}{a * 1e9:12.1f} ns{b * 1e9:12.1f} ns   {b / a:6.3f}x")


both("nums[500]", index_call, 2_000_000)
both("sum(big)", sum_call, 2_000)

# -> nums[500]            7.5 ns        14.6 ns    1.937x
# -> sum(big)        274357.8 ns    277453.5 ns    1.011x
```

The same call sits in both rows and costs the same in both — seven to nine nanoseconds, holding
steady across reruns. In the first row that doubles the answer. In the second it is one part in
thirty thousand, far below the measurement's own noise: rerun that row and the ratio wanders by a few
percent in both directions, 0.998 on one run here and 1.054 on another, which is the machine and not
the call. **A fixed cost of eight nanoseconds is decisive when you are timing an operation that takes
eight nanoseconds and undetectable when you are timing one that takes a quarter of a millisecond.**
Time nanosecond-scale expressions with statement strings, where the number you get back is the
expression and nothing else; reach for a callable when the work is large enough that a call is
rounding error.

`growth` is the callable case on purpose, because a size sweep needs a function it can hand fresh
data to. Two things keep that honest. Its rows are read as ratios, and the call is a constant added
to every row, which affects a ratio far less than it affects either term. And with `number=1` there
is exactly one call per timed region, so the entire fixed apparatus — the call plus `timeit`'s own
per-region machinery — is one tick of the clock:

```python
import timeit

print(round(min(timeit.repeat(lambda: None, number=1, repeat=5)) * 1e9, 1))   # -> 41.9  nanoseconds
```

Forty-two nanoseconds is a floor to keep in mind when a `growth` row comes back small, and a reason
to push the sizes up until the rows are milliseconds.

Now a real question. There are four obvious ways to copy a list. Is any of them meaningfully faster?

```python
compare({
    "nums[:]":           "nums[:]",
    "list(nums)":        "list(nums)",
    "nums.copy()":       "nums.copy()",
    "[x for x in nums]": "[x for x in nums]",
}, setup="nums = list(range(10_000))")

# -> nums.copy()            15.320 us   1.00x
# -> nums[:]                15.505 us   1.01x
# -> list(nums)             16.413 us   1.07x
# -> [x for x in nums]      49.502 us   3.23x
```

Read that carefully, because it answers one question and declines another. The comprehension is
decisively slower — 3.2x here, and never under 3x on any rerun — because it moves each pointer
through the interpreter one at a time instead of bulk-copying the block. That is a factor, and a
factor is a finding.

The top three are a different story. `nums.copy()` and `nums[:]` land within a percent or two and
trade places from run to run, so the measurement simply did not separate them. `list(nums)` sits
five to nine percent behind both, and it did so in every one of a dozen reruns, which makes the gap
real rather than noise — the general constructor has to work out what it was handed before it can
take the bulk-copy path. Real is not the same as worth acting on. **A gap of a few percent means
nothing until it survives a dozen reruns pointing the same way, and even when it does survive, a few
percent is almost never a reason to write the code differently.** Choose among those three on
readability.

### Measure growth, not time

An absolute timing tells you what something costs today, at one size, on one machine. The more
durable question is how the cost moves when the input grows, and you can read that off ratios
without knowing anything about the implementation.

Take two functions that build a log of sensor readings, one adding each new value at the front and
one at the back. Section 8 established the classes: `insert(0, v)` moves every element already
present, `append` moves none.

```python
def prepend_all(values):
    log = []
    for v in values:
        log.insert(0, v)
    return log


def append_all(values):
    log = []
    for v in values:
        log.append(v)
    return log


sizes = [10_000, 20_000, 40_000, 80_000, 160_000]

growth(lambda n: list(range(n)), prepend_all, sizes)
# -> n = 10000        13.995 ms
# -> n = 20000        56.502 ms   x 4.04   exponent 2.01
# -> n = 40000       232.434 ms   x 4.11   exponent 2.04
# -> n = 80000       929.123 ms   x 4.00   exponent 2.00
# -> n = 160000     3770.630 ms   x 4.06   exponent 2.02

growth(lambda n: list(range(n)), append_all, sizes)
# -> n = 10000         0.074 ms
# -> n = 20000         0.146 ms   x 1.95   exponent 0.97
# -> n = 40000         0.293 ms   x 2.01   exponent 1.01
# -> n = 80000         0.598 ms   x 2.04   exponent 1.03
# -> n = 160000        1.126 ms   x 1.88   exponent 0.91
```

The arithmetic behind the exponent column is one line. If cost grows like `n**k`, doubling `n`
multiplies the cost by `2**k`, so `k = log2(ratio)`. Double the input and get four times the time and
`k` is 2; get twice the time and `k` is 1; get the same number back and `k` is 0.

| ratio on doubling `n` | exponent | class |
|---:|---:|---|
| ~1 | 0 | constant |
| ~2 | 1 | linear |
| ~2.2 | ~1.1 | linear with a log factor |
| ~4 | 2 | quadratic |
| ~8 | 3 | cubic |

**You never need to know what an operation does to find out how it scales — run it at four sizes and
read the exponent off the ratios.** The quadratic column sits on 2.0 to within a few hundredths at
every doubling. The linear one wobbles between 0.91 and 1.03, and that wobble is worth accounting
for rather than waving at, because the harness itself contributes to these rows.

Start with what it contributes. Every row carries the callable overhead measured above — one Python
call plus `timeit`'s per-region machinery, about 42 ns — which against the 0.074 ms of the smallest
row is one part in seventeen hundred, and a smaller share of every row above it. It also cannot
produce a wobble. A constant added to both terms of a ratio only ever pulls that ratio toward 1, so
it can push an exponent *below* the true value and never above it, and two of these four exponents
sit above 1. What is left is the clock and the scheduler: 0.074 ms is under two thousand ticks of the
41.7 ns clock from the first subsection, and anything the machine chooses to do during one of those
runs lands squarely in the ratio. When the fastest row is that small, push the sizes up until it
takes at least a few milliseconds, or raise `repeat`, rather than reading meaning into the third
decimal place.

The early rows deserve the least trust for a second reason. At small sizes two distortions pull the
ratio in opposite directions: fixed per-call overhead is a larger share of a small time, which drags
the ratio down — the 42 ns floor is the harness's own share of that, and whatever `run` itself does
before touching its first element adds more — while a small input sits entirely in cache and runs
disproportionately fast, which pushes the ratio up. Neither has anything to do with the algorithm,
and both fade as the sizes grow. Read the classification off the last rows.

Where ratios cannot help you is separating `n` from `n log n`. Sorting, through the same harness:

```python
import random

random.seed(1)
pool = [random.random() for _ in range(1_600_000)]
growth(lambda n: pool[:n], sorted, [100_000, 200_000, 400_000, 800_000, 1_600_000])
# -> n = 100000        8.686 ms
# -> n = 200000       19.353 ms   x 2.23   exponent 1.16
# -> n = 400000       44.917 ms   x 2.32   exponent 1.21
# -> n = 800000      100.585 ms   x 2.24   exponent 1.16
# -> n = 1600000     218.865 ms   x 2.18   exponent 1.12
```

Consistently above 1 and drifting slowly down, which is the signature of a log factor: the `log n`
term keeps growing, but ever more slowly relative to `n`. You will not tell that apart from linear by
eye. Separating linear from quadratic, on the other hand, takes one doubling and no expertise — and
quadratic is the failure mode that actually costs you.

Three practical notes on the sweep. Use at least four sizes, doubling each time, because two points
fit any curve you like. Build each input through `make`, outside the timed call, as `growth` does.
And if `run` mutates its argument, `growth` as written is wrong for the same reason the sort
measurement was, so move the construction inside and subtract it.

### Sizing a whole structure

Section 2 settled what `sys.getsizeof` reports and what it leaves out, and left you a one-level
helper. Nested data needs the recursive version, which earns a place next to the harness:

```python
import sys

def total_size(obj, seen=None):
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return 0
    seen.add(id(obj))
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        for key, value in obj.items():
            size += total_size(key, seen) + total_size(value, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            size += total_size(item, seen)
    return size


inventory = [{"sku": f"sku-{i}", "count": i} for i in range(1000)]
print(sys.getsizeof(inventory))     # -> 8856
print(total_size(inventory))        # -> 268836
```

Thirty times what the shallow figure suggested — and the shallow figure is itself odd, which is the
more useful of the two observations. A thousand-slot list ought to report `56 + 8 * 1000` = 8056 by
section 2's arithmetic, and this one reports 8856. **`sys.getsizeof` gives you the block that was
allocated, not the part of it you are using**, so two lists holding the same thousand elements report
different sizes according to how they were built:

```python
import sys

grown = []
for i in range(1000):
    grown.append(i)
exact = list(range(1000))

print(len(grown), len(exact))                            # -> 1000 1000
print(sys.getsizeof(grown), sys.getsizeof(exact))        # -> 8856 8056
```

Eight hundred bytes of spare capacity in one and none in the other, at identical length and identical
contents. The comprehension that built `inventory` grew slot by slot the same way, which is the whole
of its extra 800 bytes. So a size comparison between two structures is only a comparison of their
contents if both were built the same way; otherwise part of what you measured is allocation history,
and no amount of rerunning will separate the two afterwards.

Three cautions come with the helper. The identity check is not decoration — it is what keeps the
total honest when one object is reachable by two paths:

```python
shared = [255, 0, 0]
print(total_size([shared, shared]))          # -> 216
print(total_size([shared, [255, 0, 0]]))     # -> 304
```

An 88-byte inner list charged once against two charged separately: an 88-byte gap between structures
that compare equal. Second, `seen` holds `id()` values, which are unique only among objects alive at
the same moment, so keep the structure alive for as long as you are measuring it. Third, the integers
and strings the walk counts may be shared with the rest of the program, so the total tells you what
the structure is made of, not what deleting it would hand back.

### `tracemalloc` measures what was actually allocated

When you want the allocator's own account rather than an estimate, `tracemalloc` instruments it and
reports both the bytes currently held and the high-water mark reached on the way — that peak is the
number that reveals whether an operation quietly built a temporary copy. Start it, run the code, read
the pair, stop it. It sees only allocations made while it is running, and it slows the program down
substantially — the build below takes about seven times as long with it on — so treat it as a
diagnostic, not as something to leave switched on.

```python
import sys, tracemalloc

tracemalloc.start()
grid = [[(r, g, 0) for g in range(200)] for r in range(200)]
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(current, peak)          # -> 3212160 3212160
print(sys.getsizeof(grid))    # -> 1656
print(total_size(grid))       # -> 3218456
```

A 1656-byte object by the shallow measure, 3.2 MB in fact, and the recursive helper agreed with the
allocator to within 0.2%. Current equals peak here because nothing temporary was built; when the two
differ, the gap is the copy you did not know you were making.

### The tool behind the instruction listings

Two earlier sections settled arguments by pointing at instruction names — section 3 read `BUILD_LIST`
and `LIST_EXTEND` off two list displays to explain why `[1, 2]` allocates two slots and `[1, 2, 3]`
allocates four, and later read `STORE_SUBSCR` against `LIST_APPEND`; section 5 printed a listing to
establish that a colon inside brackets is a `slice`. This is the tool those came from, and it is one
line.

CPython does not execute your source. It compiles each function once into a sequence of instructions
for a stack machine, and the interpreter executes that sequence. `dis.dis(f)` prints it. Four
conventions cover almost everything you will want to read: `LOAD_*` pushes something onto the stack,
`STORE_*` pops something into a name, `FAST` means a function-local slot rather than a dictionary
lookup, and the number in the middle column is the instruction's operand, with `dis` printing what it
resolves to in parentheses.

```python
import dis

def f(nums, i, j):
    a = nums[i]
    b = nums[i:j]

dis.dis(f)
# -> (source-line column, RESUME, and the implicit `return None` omitted)
# ->   LOAD_FAST_BORROW_LOAD_FAST_BORROW 1 (nums, i)
# ->   BINARY_OP               26 ([])
# ->   STORE_FAST               3 (a)
# ->
# ->   LOAD_FAST_BORROW_LOAD_FAST_BORROW 1 (nums, i)
# ->   LOAD_FAST_BORROW         2 (j)
# ->   BINARY_SLICE
# ->   STORE_FAST               4 (b)
```

`LOAD_FAST_BORROW_LOAD_FAST_BORROW` looks alarming and is not: it is two local loads fused into one
instruction because they were adjacent, and `BORROW` means the load does not bump the object's
reference count, since the instruction that consumes it will not outlive the frame holding it. Both
are savings the compiler applies without changing meaning, and neither affects what follows. Read it
as "push `nums`, push `i`".

You do not have to read bytecode fluently for it to pay off. Often the whole insight is that two
similar-looking expressions produce *different* instructions. Indexing compiles to `BINARY_OP 26
([])`. Slicing compiles to `BINARY_SLICE`, a different instruction consuming a third operand. Writing
splits the same way: `nums[i] = v` emits `STORE_SUBSCR` and `nums[i:j] = v` emits `STORE_SLICE`.
These are separate paths through the interpreter, and that is the observation worth carrying — the
surface syntax differs by two characters and the machinery underneath does not overlap, which is the
same fact the cost table records when it charges an index O(1) and a slice O(b − a) in time and
space.

### The bytecode rewrites itself as it runs

That listing is not the last word, because it is not what runs after the first few passes. **CPython
counts how often each instruction executes, and once one is hot it replaces the instruction in place
with a variant specialised to the types it has actually been seeing.** A generic `BINARY_OP` that has
only ever added two ints becomes an add-two-ints instruction that checks the types and jumps straight
to the integer path, falling back to the generic version if the assumption ever fails. `dis` will
show you the current state with `adaptive=True`.

Take one counting loop and run it over two element types. The source is identical; the bytecode after
warm-up is not:

```python
import dis

SRC = """
def count_matches(values, target):
    hits = 0
    for x in values:
        if x == target:
            hits += 1
    return hits
"""


def fresh():
    ns = {}
    exec(SRC, ns)                      # a separate code object the interpreter has never run
    return ns["count_matches"]


def opnames(f):
    return [i.opname for i in dis.get_instructions(f, adaptive=True)]


def became(f, generic):
    """What the instruction `generic` turned into, once `f` had run."""
    return [b for a, b in zip(opnames(cold), opnames(f)) if a == generic]


cold, over_ints, over_tuples = fresh(), fresh(), fresh()
for _ in range(30):
    over_ints(list(range(1000)), 7)
    over_tuples([(i,) for i in range(1000)], (7,))

for generic in ("FOR_ITER", "COMPARE_OP", "BINARY_OP"):
    print(f"{generic:<12}{str(became(over_ints, generic)):<25}{became(over_tuples, generic)}")

# ->                 over ints                over one-element tuples
# -> FOR_ITER    ['FOR_ITER_LIST']        ['FOR_ITER_LIST']
# -> COMPARE_OP  ['COMPARE_OP_INT']       ['COMPARE_OP']
# -> BINARY_OP   ['BINARY_OP_ADD_INT']    ['BINARY_OP_ADD_INT']
```

`FOR_ITER` became `FOR_ITER_LIST` in both, because both iterate a list. `BINARY_OP` became
`BINARY_OP_ADD_INT` in both, because `hits += 1` adds two ints whatever the elements are. And
`COMPARE_OP` — the one instruction that touches an element — became `COMPARE_OP_INT` in the first and
stayed generic in the second, because there is no comparable shortcut for comparing two tuples. Same
source, same loop, two different programs by the thirtieth call.

Three things you have already seen collapse into this one mechanism.

It is why section 8's result is shaped the way it is. There, `list.count` lost to a hand-written
counting loop on a list of ints and won on a list of one-element tuples. The flip is the
`COMPARE_OP_INT` above: the interpreted loop earns that instruction by running hot over ints, and
`count`'s generic comparison machinery has no equivalent to earn.

It is why a single cold call is not a measurement even when the clock is adequate. A function's first
executions run generic instructions and the specialised forms arrive shortly after, so the cost of
the first call is not the cost of the tenth. Compile a fresh function each time, time its first `k`
calls against the same `k` calls once warm, and take the minimum of many trials:

```python
import time

SRC = "def combine(a, b):\n" + "\n".join(f"    t{i} = a + b" for i in range(40)) + "\n    return t0\n"


def first_vs_warm(k, trials=500):
    first, warm = [], []
    for _ in range(trials):
        ns = {}
        exec(compile(SRC, "<s>", "exec"), ns)      # a function the interpreter has never seen
        f = ns["combine"]
        t0 = time.perf_counter_ns()
        for _ in range(k):
            f(1, 2)
        first.append((time.perf_counter_ns() - t0) / k)
        for _ in range(2000):
            f(1, 2)                                 # warm it up
        t0 = time.perf_counter_ns()
        for _ in range(k):
            f(1, 2)
        warm.append((time.perf_counter_ns() - t0) / k)
    return min(first), min(warm)


for k in (1, 4, 16):
    cold, hot = first_vs_warm(k)
    print(f"first {k:<3} call(s){cold:8.1f} ns     warm{hot:8.1f} ns     {cold / hot:.2f}x")

# -> first 1   call(s)   292.0 ns     warm   167.0 ns     1.75x
# -> first 4   call(s)   208.2 ns     warm   166.5 ns     1.25x
# -> first 16  call(s)   164.1 ns     warm   148.4 ns     1.11x
```

The very first call costs 1.75x the warm one, and the penalty thins out as you average over more
early calls, because the warm-up is a fixed number of executions spread over however many you
measure. That is also why `timeit`'s design is right: running the statement `N` times inside one
timed region amortises the warm-up to nothing at the loop counts `autorange` picks, and taking the
minimum across repeats hands you a region that was fully warm. The body of a long-running loop is a
different case — it specialises during the first call, because the instructions inside it execute
thousands of times before that call returns. A summing loop over 2000 elements, measured the same
way, costs only 1.03x on its first call.

And it is why the version qualification below is not a formality. Which operations have specialised
forms is a property of one interpreter, decided instruction by instruction by the people who build
it, and it moves between releases. A result that turns on a fast path is a result about the
interpreter you measured on.

### The discipline

**Measure on the interpreter you will run on.** Every number in this chapter is CPython 3.14.4 on
arm64, and that qualification is part of the measurement rather than a disclaimer bolted to it.
Version to version, the set of specialised instructions above changes and so does the cost of a
Python-level loop; machine to machine, cache sizes move the point at which locality starts to
dominate. Print the provenance next to the result and you will never have to wonder later which run
a number came from:

```python
import platform, sys

print(sys.version.split()[0], platform.python_implementation(), platform.machine())
# -> 3.14.4 CPython arm64
```

**Measure at the size you will actually run at.** The copy comparison above is not one result, it is
a curve, and the curve is not monotone:

| `n` | `nums.copy()` | `[x for x in nums]` | ratio |
|---:|---:|---:|---:|
| 10 | 0.021 us | 0.083 us | 3.90x |
| 1,000 | 0.901 us | 6.176 us | 6.86x |
| 100,000 | 187.2 us | 487.3 us | 2.60x |

The same two expressions, with penalties of 3.9x, 6.9x and 2.6x. At ten elements fixed call overhead
dominates both. At a hundred thousand, memory traffic does, and the interpreter loop counts for
proportionally less. A benchmark at the wrong size answers a question you were not asking.

**Change one thing at a time.** Rewrite a loop, hoist a lookup out of it, and swap a list for a set
in a single edit, get a 3x improvement, and what you have learned is that those three changes
together are 3x faster — which is not enough to know whether one of them made things worse. Keep the
harness open, change one expression, rerun, record. It costs seconds.

**Prefer a measurement to an argument.** Section 8 contains two results no amount of reasoning would
have produced: `sum` beating a hand-written accumulation loop by 5.4x, and `list.count` *losing* to a
hand-written counting loop. Both pit C against interpreted Python, and the plausible story predicts
the first and gets the second backwards. When someone tells you which of two forms is faster —
including when that someone is you — the claim is one five-line `compare` call away from being
settled, and until that call has been made, nobody in the room knows.


---

## 12. Drills, and how to know you have it

Eighteen snippets follow. Each one is short, each one has a crisp answer, and each one fails in a
specific way if a specific piece of your model is wrong. Work them in one order and do not deviate
from it: predict, run, read. Write the prediction down in full, including the exact punctuation of
the output — "something like a list of lists" is not a prediction. Running before you predict turns
a diagnostic into a demonstration, and reading the answer before you run costs you the one moment
where a wrong model announces itself. The answer key is in the next subsection, and every output
there was produced by running the snippet on CPython 3.14.4. Drills 16 and 18 are the exception:
they report timings, the timings are this machine's, and yours will differ. What you predict there
is the shape of the result — which column grows, and by what factor — not the digits.

### The drills

**Drill 1.**

```python
prices = [4.0, 2.5, 9.0]
snapshot = prices
prices.sort()
print(snapshot)             # ?
print(snapshot is prices)   # ?
prices *= 2
print(len(snapshot))        # ?
```

**Drill 2.**

```python
grid = [[18, 19], [21, 22]]
shallow = grid[:]
shallow.append([30, 31])
shallow[0].append(20)
print(grid)                      # ?
print(len(grid), len(shallow))   # ?
```

**Drill 3.**

```python
rows = [[0] * 3] * 2
rows[0][0] = 9
print(rows)                                     # ?

cols = [[0] * 3 for _ in range(2)]
cols[0][0] = 9
print(cols)                                     # ?
print(rows[0] is rows[1], cols[0] is cols[1])   # ?
```

**Drill 4.**

```python
import sys

label = "".join(["sensor-", "07"])
readings = [label, "sensor-08"]
kept = readings[0]
print(sys.getrefcount(label) - 1)   # ?

readings[0] = "sensor-09"
print(sys.getrefcount(label) - 1)   # ?
print(readings, len(readings))      # ?
print(kept)                         # ?
```

**Drill 5.**

```python
temps = [12, 15, 19]
print(temps[3:])      # ?
print(temps[1:99])    # ?
print(temps[-99:2])   # ?
print(temps[2:1])     # ?
try:
    temps[3]
except IndexError as e:
    print(type(e).__name__, e)   # ?
```

**Drill 6.**

```python
temps = [12, 15, 19, 22, 18, 14, 11]
print(temps[4:1:-1])    # ?
print(temps[1:4:-1])    # ?
print(temps[3::-1])     # ?
print(temps[3:-8:-1])   # ?
print(temps[3:-1:-1])   # ?
```

**Drill 7.**

```python
counts = [1, 2, 3, 4, 5]
counts[1:4] = [0]
print(counts, len(counts))       # ?
counts[1:1] = [7, 8]
print(counts, len(counts))       # ?
try:
    counts[::2] = [0, 0]
except ValueError as e:
    print(type(e).__name__, e)   # ?
```

**Drill 8.**

```python
rgb = [255, 128, 0]
print(rgb[-1], rgb[-3])   # ?
print(rgb[-4:])           # ?
print(rgb[:-0])           # ?
try:
    rgb[-4]
except IndexError as e:
    print(type(e).__name__, e)   # ?
```

**Drill 9.**

```python
temps = [18, 21, 19]
for t in temps:
    t = t + 1
print(temps)                     # ?

temps = [18, 21, 19]
for i in range(len(temps)):
    temps[i] += 1
print(temps)                     # ?

temps = [18, 21, 19]
try:
    for i in range(1, len(temps) + 1):
        temps[i] += 1
except IndexError as e:
    print(type(e).__name__, e, temps)   # ?
```

**Drill 10.**

```python
channels = ["red", "green", "blue"]
levels = [255, 128]

print(list(zip(channels, levels)))    # ?
try:
    list(zip(channels, levels, strict=True))
except ValueError as e:
    print(type(e).__name__, e)        # ?
try:
    list(zip(levels, channels, strict=True))
except ValueError as e:
    print(type(e).__name__, e)        # ?
```

**Drill 11.**

```python
names = ["ana", "bo", "bo", "cy"]
for n in names:
    if n == "bo":
        names.remove(n)
print(names)    # ?

names = ["ana", "bo", "bo", "cy"]
for n in names[:]:
    if n == "bo":
        names.remove(n)
print(names)    # ?
```

**Drill 12.**

```python
import sys

def capacity(lst):
    return (sys.getsizeof(lst) - sys.getsizeof([])) // 8

grown = []
for k in range(5):
    grown.append(k)
exact = [0] * 5

print(len(grown), capacity(grown))   # ?
print(len(exact), capacity(exact))   # ?
grown.pop()
print(len(grown), capacity(grown))   # ?
```

**Drill 13.**

```python
def normalise(values):
    values = sorted(values)

def normalise_inplace(values):
    values[:] = sorted(values)

a = [3, 1, 2]
normalise(a)
print(a)          # ?

b = [3, 1, 2]
normalise_inplace(b)
print(b)          # ?

def grow_a(v):
    v += [99]

def grow_b(v):
    v = v + [99]

p = [1]
grow_a(p)
print(p)          # ?

q = [1]
grow_b(q)
print(q)          # ?
```

**Drill 14.**

```python
u = [1, 2, 3]
v = [1, 2, 3]
w = u
print(u == v, u is v, u is w)          # ?

n = 500
big = 1000
print(n + n == big, (n + n) is big)    # ?

half = 50
small = 100
print((half + half) is small)          # ?
```

**Drill 15.**

```python
temps = [12, 15, 19]
lazy = reversed(temps)
eager = temps[::-1]
temps[0] = 99
print(list(lazy))    # ?
print(eager)         # ?

again = reversed([1, 2, 3])
print(list(again), list(again))   # ?
```

**Drill 16.** Predict the *shape*, not the digits: for each of the three columns below, say whether
doubling the input roughly doubles the number or roughly quadruples it, and name the complexity
class that implies. Then write the one-line change that removes the first column's growth, and say
what that change costs you in memory and in ordering. For the second block, name the container you
would reach for if both ends had to be cheap.

```python
import timeit

def scan_ms(n):
    catalogue = [f"sku-{i}" for i in range(n)]
    discontinued = catalogue[::2]
    stmt = "[s for s in catalogue if s not in discontinued]"
    return min(timeit.repeat(stmt, globals=locals(), number=1, repeat=3)) * 1000

for n in (2_000, 4_000, 8_000):
    print(n, round(scan_ms(n), 2))   # ?

for n in (10_000, 20_000, 40_000):
    front = min(timeit.repeat("while q: q.pop(0)", f"q = list(range({n}))",
                              number=1, repeat=5)) * 1000
    back = min(timeit.repeat("while q: q.pop()", f"q = list(range({n}))",
                             number=1, repeat=5)) * 1000
    print(n, round(front, 2), round(back, 2))   # ?
```

**Drill 17.**

```python
import sys

row = list(range(10_000))
ints = [0] * 3
rows = [row] * 3
print(sys.getsizeof(ints), sys.getsizeof(rows))   # ?
print(sys.getsizeof(row))                         # ?
```

**Drill 18.** Three timings, one run of each. Below the snippet are three conclusions somebody might
draw from the numbers it prints. Decide which of them this run actually supports before you look at
the key.

```python
import time

nums = list(range(1_000))

t0 = time.perf_counter_ns()
nums.index(999)
a = time.perf_counter_ns() - t0

t0 = time.perf_counter_ns()
999 in nums
b = time.perf_counter_ns() - t0

t0 = time.perf_counter_ns()
nums[999]
c = time.perf_counter_ns() - t0

print(a, b, c)   # ?
```

1. `list.index` is slower than the `in` operator.
2. Subscripting is roughly thirty-five times faster than scanning this list.
3. Both scans cost microseconds and the subscript does not.

### The answer key

**1.** `[2.5, 4.0, 9.0]` / `True` / `6`. Assignment binds a second name to the same object, so every
in-place operation is visible through both names — and `sort()` and `*=` are both in-place, the
latter because `list` implements `__imul__`, so augmented assignment mutates the existing object and
stores the same object back. (Section 9.)

**2.** `[[18, 19, 20], [21, 22]]` / `2 3`. A slice copy allocates a new pointer block and copies the
pointers, so the outer lengths diverge; both blocks still point at the same two inner lists, so
appending to `shallow[0]` is appending to `grid[0]`. One level of the structure was copied and the
rest was shared, which is what "shallow" names. (Sections 3 and 5.)

**3.** `[[9, 0, 0], [9, 0, 0]]` / `[[9, 0, 0], [0, 0, 0]]` / `True False`. Repetition evaluates its
left operand once and stores that one address n times; a comprehension re-evaluates its expression
each iteration and builds a distinct list each time. (Section 3.)

**4.** `3` / `2` / `['sensor-09', 'sensor-08'] 2` / `sensor-07`. Three references exist before the
write: the name `label`, the slot, and `kept`. **The write moves exactly one 8-byte pointer — it
does not erase what was there, it displaces it, and the displaced object survives exactly as long
as something else still refers to it.** Here `kept` does, so the count falls to 2 rather than to 0
and the string is still readable afterwards. Had nothing else referred to it, the count would have
reached 0 and CPython would have freed it inside the assignment statement. Note also that the
length did not move: a write to an existing position replaces rather than inserts, so `readings` is
still two long. `sys.getrefcount` reports one extra reference — its own argument — which is why
both reads subtract one. (Section 4.)

One trap in reading this drill, worth knowing because it looks like the mechanism failing. Move
`print(kept)` above the second `getrefcount` and the count prints 3, not 2: the object you just
handed to `print` is still sitting in the frame's evaluation stack. Reference counts are exact, and
exact means they count every reference, including the ones your source does not name.

**5.** `[]` / `[15, 19]` / `[12, 15]` / `[]` / `IndexError list index out of range`. Slice bounds
are clamped into range before use — `slice(-99, 2).indices(3)` reports `(0, 2, 1)` — and a start at
or past the stop yields an empty list rather than an error, while a bare index is bounds-checked
and raises. **The same out-of-range number is silent in a slice and fatal in an index.** That
asymmetry
is why an off-by-one in slice arithmetic reaches you as quietly wrong data instead of a traceback.
(Sections 4 and 5.)

**6.** `[18, 22, 19]` / `[]` / `[22, 19, 15, 12]` / `[22, 19, 15, 12]` / `[]`. A negative step does
not swap the meaning of the bounds: `start` is still the first index visited and `stop` is still
the first index not visited, so **going backwards, `start` has to be the larger index.**
`temps[4:1:-1]` visits 4, 3, 2. `temps[1:4:-1]` asks to walk left from 1 and stop before 4, which
visits nothing at all — and says nothing about it. That is the whole failure: bounds left in
ascending order after the step was flipped, producing an empty list where a reversed run was
wanted.

The third and fourth lines agree for a reason worth extracting. With a negative step the omitted
`stop` means "one position before the front", a position no literal can name, and it is the only
spelling that reaches index 0. `-8` gets there only because it clamps to the same place:
`slice(3, None, -1).indices(7)` and `slice(3, -8, -1).indices(7)` both report `(3, -1, -1)`. Do not
confuse that reported `-1` with an index you can write — written as a bound, `-1` resolves to
index 6, which is above 3, so `temps[3:-1:-1]` is empty. This is why `nums[::-1]` is the reversal
idiom and `nums[len(nums)-1:-1:-1]` is not. (Section 5.)

**7.** `[1, 0, 5] 3` / `[1, 7, 8, 0, 5] 5` /
`ValueError attempt to assign sequence of size 2 to extended slice of size 3`. Assigning to a
contiguous slice replaces that span with however many elements you supply, so the length changes and
an empty target slice inserts. An extended slice with a step is not contiguous, so there is nowhere
to put a mismatched count and it raises instead. Deletion has no count to mismatch, so `del
counts[::2]` is legal on the same slice that rejects assignment — on `[1, 2, 3, 4, 5]` it leaves
`[2, 4]`. (Section 5.)

**8.** `0 255` / `[255, 128, 0]` / `[]` / `IndexError list index out of range`. A negative index is
resolved as `len(rgb) + i` and then bounds-checked, so `-3` is valid and `-4` is not; as a slice
bound the same `-4` clamps to `0`. `-0` is `0`, so `rgb[:-0]` is `rgb[:0]`, an empty slice — not
"up to the end", which is the trap in writing `nums[:-k]` with a `k` that can reach zero.
(Sections 4 and 5.)

**9.** `[18, 21, 19]` / `[19, 22, 20]` / `IndexError list index out of range [18, 22, 20]`. The
first loop changes nothing. `for t in temps` binds `t` to the object a slot holds, and `t = t + 1`
rebinds that name to a different object; the slot was never involved, so the list is untouched at
the end. **A value loop hands you the object, an indexed loop hands you the position, and only a
position can be assigned to.** That is the entire rule for choosing between them: reach for the
index when you are writing into `temps[i]`, and reach for `for t in temps` — which carries no index
to keep correct and no bracket lookup — every other time.

The third block is the off-by-one that the second block avoids for free. Indices run from 0 to
`len(temps) - 1`, so a three-element list has a highest index of 2, and `range(len(temps))` yields
exactly `[0, 1, 2]` — the valid index set, no arithmetic required. `range(1, len(temps) + 1)`
yields `[1, 2, 3]`, which is the same *count* of indices and the wrong *set* of them. It gets two
iterations in, having already written `[18, 22, 20]`, and then dies on `temps[3]`. Half the work
done, an exception in flight, and a list left in a state that is neither the input nor the intended
output. (Sections 4 and 6.)

**10.** `[('red', 255), ('green', 128)]` / `ValueError zip() argument 2 is shorter than argument 1`
/ `ValueError zip() argument 2 is longer than argument 1`. **`zip` stops when its shortest argument
runs out and reports nothing** — `'blue'` is simply gone from the result, and there is no traceback
to lead you back to the line that dropped it. `strict=True` converts that silence into a
`ValueError`. The check is positional, which is why the message names an argument number rather
than a variable, and why swapping the two arguments changes "shorter" to "longer". The error is
raised lazily, at the moment the shortest input runs dry rather than up front: consume that zip one
step at a time and both pairs arrive successfully before the third `next()` raises. Make
`strict=True` your default whenever the sequences are supposed to be the same length — it costs
nothing measurable, and it converts a wrong answer into a stack trace. (Section 6.)

**11.** `['ana', 'bo', 'cy']` / `['ana', 'cy']`. A list iterator holds an integer position, not a
snapshot; `remove` shifts the tail down one slot while the position still advances, so the element
that slid into the vacated slot is stepped over. Iterating a copy gives the loop a sequence nothing
mutates. (Section 6.)

**12.** `5 8` / `5 5` / `4 8`. Five appends overshoot to eight slots, because growth is geometric and
that overshoot is what makes `append` O(1) amortized; `[0] * 5` knows its length up front and
allocates exactly five. `pop()` does not shrink the block here, so length and capacity move
independently. (Section 7.)

The helper's arithmetic is worth unpacking. `sys.getsizeof([])` is 56 on a 64-bit build: that is the
fixed object header, identical for a list of any length. Every slot beyond it is one 8-byte pointer,
so subtracting the header and dividing by 8 counts slots, not elements — capacity, not length. And
nothing in the result depends on what the slots point at.

Shrinking lags, and lags coarsely. The block is kept whenever the new length is still at least half
the allocation, and when the block is recomputed the new size runs back through the same
over-allocating formula. Keep popping this five-element list and the capacity reads 8, 8, 8, then 4
— it never tracks the length step for step. One more result worth knowing: a list literal of
constants is built by extending an empty list, so `sys.getsizeof([1, 2, 3])` is 88, a capacity of
4, while `[0] * 3`, which is sized up front, is 80.

**13.** `[3, 1, 2]` / `[1, 2, 3]` / `[1, 99]` / `[1]`. `values = ...` rebinds a local name and leaves
the caller's object untouched; `values[:] = ...` reaches through the name and overwrites the
object's contents. `v += [99]` extends in place, `v = v + [99]` builds a new list and rebinds; the
two lines look like synonyms and are not. Any requirement to modify the argument itself is a
requirement to reach through the name. (Section 9.)

**14.** `True False True` / `True False` / `True`. `==` compares contents element by element, `is`
compares addresses. `n + n` builds a new int at runtime, so it is a different object from `big`; the
last line is `True` only because CPython pre-allocates and reuses the small integers, which is an
interning detail and not something to rely on. (Sections 2 and 9.)

**15.** `[19, 15, 99]` / `[19, 15, 12]` / `[3, 2, 1] []`. `reversed()` returns a 48-byte iterator
that reads the live list when you consume it, so the later write to `temps[0]` shows up;
`temps[::-1]` materialised an 80-byte copy immediately, before that write happened. An iterator is
also single-use — the second `list(again)` finds it exhausted and yields nothing, which is why the
two calls on one line disagree. (Sections 6 and 8.)

**16.** This machine printed `2000 8.45` / `4000 36.6` / `8000 149.75`, then `10000 3.88 0.12` /
`20000 18.45 0.24` / `40000 91.5 0.47`. Yours will differ in the digits; the factors are the point.

The first column multiplies by 4.33 and then by 4.09 each time `n` doubles. Quadrupling on a
doubling is the signature of O(n²), and it is O(n²) for a reason with nothing clever in it: `s not
in discontinued` scans that list until it matches or runs out, so an O(n) test sits inside an O(n)
comprehension. **A membership test against a list is a scan, and a scan inside a loop is a
quadratic you did not intend to write.** The one-line fix is to hash the values once — build
`dset = set(discontinued)` before the comprehension and test `s not in dset` — which took 0.042,
0.070 and 0.176 ms at the same three sizes, doubling rather than quadrupling. At `n = 8000` that is
149.75 ms against 0.176 ms, and the two versions return identical lists.

What the fix costs, since it is not free. Memory: those 4,000 SKU strings occupy 32,056 bytes as a
list container and 131,288 as a set, 4.1× more, because a hash table stays deliberately sparse.
Ordering: a set does not preserve insertion order and cannot be subscripted, which is exactly why
the fix keeps the list for the output and uses the set only for the test. And the elements have to
be hashable, so a set of coordinates has to store `(r, c)` rather than `[r, c]`.

The second block is the same shape of mistake with a different O(n) hiding in it. `pop(0)` removes
the front slot and then shifts every remaining pointer down one position, so emptying the list that
way is quadratic — 3.88, 18.45 and 91.5 ms, multiplying by 4.8 and 5.0 on each doubling, decisively
not the ×2 a linear cost would give. `pop()` removes from the end, shifts nothing, and gives
0.12, 0.24 and 0.47 ms: exact doubling, O(n) overall. `insert(0, x)` is `pop(0)` in reverse and
costs the same. When both ends genuinely have to be cheap, the container is `collections.deque`,
which pays for that with O(n) access to the middle. (Sections 8 and 10.)

**17.** `80 80` / `80056`. `sys.getsizeof` reports the header plus the pointer block and nothing the
pointers lead to, so a three-slot list costs 80 bytes whether the slots hold small ints or 80 KB
lists. Adding the referents by identity gives `80 + 80056 = 80136`, because the three slots hold the
same address. (Sections 2 and 11.)

**18.** One run here printed `5917 5667 166`. Only conclusion 3 survives.

Conclusion 1 is not supported. Measured properly — `timeit.repeat(..., number=100_000, repeat=9)`,
quoting the minimum — four separate sessions gave `nums.index(999)` at 5700, 6120, 6156 and 6060 ns
and `999 in nums` at 5968, 6021, 5916 and 5498 ns. The two ranges overlap, and the ordering flips:
`index` came out faster in the first session and slower in the other three. **Each statement's own
readings span 456 and 523 ns, both wider than the 250 ns gap the single run appeared to show, and
the sign of that gap is not stable — so it is not a difference at all.**

Conclusion 2 is not supported either, and it is wrong by a factor of thirty. That 166 ns for
`nums[999]` is almost entirely apparatus: `time.get_clock_info("perf_counter").resolution` is
41.7 ns on this machine, so every reading is a multiple of it, and five trials of the same three
lines gave subscript readings of 166, 166, 125, 83 and 83 — quantised, and dominated by the two
clock calls that bracket the operation. The real figure is 5.3 ns. Against a scan of roughly
5.5 µs that is a thousandfold, not thirty-five-fold.

Conclusion 3 survives because the gap it claims is three orders of magnitude wide, and no amount of
clock noise or scheduling luck at this scale closes it. That is the rule the drill is for: a single
reading can support a claim about orders of magnitude and can support nothing finer. Anything
tighter than that needs many runs inside one timed region, the minimum quoted rather than the mean,
and the input built in setup rather than in the statement. (Section 11.)

### The readiness checklist

Score yourself on explanation, not recognition. **For each statement below you should be able to
give the mechanism out loud, without looking it up, in under a minute.** Each one names the section
that carries it and the drill that tests it; anything you cannot explain, re-read that section and
then re-run that drill from scratch, predicting again before you look.

You should be able to explain, without looking it up, why:

1. every slot in a list is the same width, whatever objects the list holds, and why that is what
   makes `nums[i]` cost the same for any `i`. (Sections 1 and 2; drill 17.)
2. `len(nums)` is a field read rather than a count, and why it tells you nothing about how many
   bytes the list occupies. (Sections 2 and 7; drill 12.)
3. two lists can be equal without being the same object, and why identity checks on small integers
   can appear to work anyway. (Sections 2 and 9; drill 14.)
4. `[[0] * 3] * 2` shares a row and `[[0] * 3 for _ in range(2)]` does not. (Section 3; drill 3.)
5. the highest valid index of `nums` is `len(nums) - 1`, so `nums[len(nums)]` raises — while
   `nums[len(nums):]` quietly returns an empty list instead. (Sections 4 and 5; drills 5 and 8.)
6. writing `nums[1] = x` cannot change the list's length, what becomes of the value that was in that
   slot, and what decides whether it still exists afterwards. (Section 4; drill 4.)
7. `temps[1:4:-1]` is empty while `temps[4:1:-1]` is not, and why an omitted `stop` is the only
   spelling that reaches index 0 on the way back. (Section 5; drill 6.)
8. assigning to `nums[1:4]` can change the list's length while assigning to `nums[1]` cannot, and
   why the same assignment raises on `nums[::2]`. (Section 5; drill 7.)
9. `for x in nums` is the default form, and what specifically makes an index load-bearing rather
   than decorative. (Sections 4 and 6; drill 9.)
10. `zip` stops at its shortest argument without saying so, and what `strict=True` changes about
    when and how you find out. (Section 6; drill 10.)
11. removing elements from a list while iterating over it skips some of them, and why iterating over
    `nums[:]` fixes it. (Section 6; drill 11.)
12. `reversed(nums)` and `nums[::-1]` produce the same order at different costs, and which of them a
    stated O(1)-extra-space constraint rules out. (Sections 6 and 8; drill 15.)
13. `append` is O(1) on average even though an occasional append has to relocate the entire block,
    and why the average is the honest number to quote. (Sections 7 and 8; drill 12.)
14. `insert(0, x)` and `pop(0)` are O(n) while `append(x)` and `pop()` are not, and what container
    you would reach for if you needed both ends cheaply. (Sections 8 and 10; drill 16.)
15. `x in nums` inside a loop makes the whole loop quadratic, and what you give up in memory and in
    ordering by switching the container to a set. (Sections 8 and 10; drill 16.)
16. assignment, `nums[:]` and a deep copy give three different degrees of sharing, and which of them
    still lets a write reach the original. (Sections 3, 5 and 9; drills 1 and 2.)
17. `nums[:] = ...` is visible to a caller and `nums = ...` is not, and which one an in-place
    requirement demands. (Section 9; drill 13.)
18. a single timing run supports a claim about orders of magnitude and nothing finer, and what you
    would run instead to make a performance claim you would defend. (Section 11; drill 18.)
