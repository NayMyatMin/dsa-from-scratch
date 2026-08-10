# Chapter 1 — Introduction, in Python

Covers the card's four articles: *Array – A DVD box?*, *What Is an Array?*, *Accessing Elements in
Arrays*, *Array Capacity VS Length*.

The card is written in Java, and Java's array model leaks into every sentence of it: you declare a
size up front, that size never changes, and you track "how many slots am I actually using" in a
separate variable. Python hands you a `list` and all of that vanishes. It's tempting to conclude
the chapter doesn't apply.

It applies. The mechanics didn't disappear — they moved into the runtime, where you stopped being
billed for them explicitly and started being billed for them silently. This note is about where
the bill comes from.

Every snippet below is runnable. Run them. The numbers in this file were measured on the Python
3.14.4 in this repo's venv, so you should reproduce them exactly with `uv run python`.

---

## 1. The DVD shelf holds tickets, not DVDs

The card's analogy: an array is a shelf of numbered slots, and you can jump straight to slot 7
without walking past slots 0–6. That part is true in Python.

What differs is what sits in the slot. A Java `int[]` stores the integers themselves, packed
end to end — slot `i` lives at `base + i*4` bytes, and the CPU reads the value directly. A Python
`list` stores *pointers*. The slots are packed end to end, 8 bytes each, but each one holds an
address, and the actual `int` object lives somewhere else on the heap entirely.

```python
nums = [10, 20, 30]
print([id(x) for x in nums])   # three heap addresses, not near each other
print(id(nums[0]) == id(10))   # True — the list didn't copy 10, it pointed at it
```

Two consequences worth carrying with you:

**Memory.** A `list` of 1000 ints costs 8056 bytes for the pointer array *plus* 28 bytes per
distinct int object. A Java `int[1000]` costs 4000 bytes, full stop.

**Cache locality.** Walking a Java `int[]` streams contiguous memory, which the CPU prefetches
perfectly. Walking a Python `list` reads contiguous *pointers* and then chases each one to a
scattered heap address. This is a large part of why the same O(n) loop is ~50× slower in Python
than in C — the algorithmic complexity is identical, the constant factor is not.

The consolation prize: because the slots hold generic pointers, a Python list is heterogeneous for
free. `[1, "two", [3]]` needs no boxing ceremony, no `Object[]`, no casts on the way out.

> **Aside — small-int caching.** CPython pre-allocates the int objects from −5 to 256 and reuses
> them, so `id(nums[0]) == id(10)` above is `True` for `10` but would be `False` for `1000`. That
> is an interning detail, not an array detail. Never write `is` where you mean `==`.

---

## 2. Python's four array-ish types

"Array" in Python is ambiguous. Four distinct things claim the name, and only one of them ever
shows up on LeetCode.

| Type | Stores | Resizable | Homogeneous | Use it when |
|---|---|---|---|---|
| `list` | pointers to any objects | yes | no | **Always, on LeetCode** |
| `array.array` | raw C values, packed | yes | yes, one typecode | You need Java-like packing without NumPy |
| `bytearray` | raw bytes | yes | `0..255` only | Byte/binary work |
| `numpy.ndarray` | raw C values, n-dimensional | no (fixed shape) | yes | Numeric work at scale |

`array.array` is the closest thing to the card's mental model, and it's in the standard library:

```python
import array, sys

a = array.array('i', range(1000))   # 'i' = signed 4-byte int, packed contiguously
l = list(range(1000))
print(sys.getsizeof(a), sys.getsizeof(l))   # 4200  8056  -> ~1.9x
```

You will not use it for these problems. It's here so that "Python doesn't have real arrays" stops
being something you believe — it has them, LeetCode just doesn't hand them to you.

---

## 3. Accessing elements

**Indexing is O(1)**, exactly as the card describes: `nums[i]` compiles down to a bounds check and
one pointer offset. No search, no traversal, regardless of `i`.

**Negative indices** have no Java equivalent and are not a special case in the runtime — `nums[-1]`
is rewritten to `nums[len(nums) - 1]`. Prefer it over `nums[len(nums)-1]`; it's the idiom.

**Out of range raises `IndexError`** — Python's `ArrayIndexOutOfBoundsException`. But note the
asymmetry that catches everyone:

```python
nums = [1, 2, 3]
nums[5]      # IndexError
nums[5:]     # []      <- slices clamp silently, they never raise
nums[1:99]   # [2, 3]
```

A slice that runs off the end returns whatever it found. That silence is convenient right up until
it hides an off-by-one.

**Slicing copies.** This is the single most expensive habit in Python interview code:

```python
first_half = nums[:n//2]     # O(n) time AND O(n) extra space — a new list
reversed_copy = nums[::-1]   # same
```

When a problem says *"modify in-place with O(1) extra memory"* — and Chapter 5 of this card is
entirely such problems — slicing is disqualified. `reversed(nums)` gives you a lazy iterator
instead; `nums.reverse()` mutates with no copy at all.

**Iteration.** Three forms, in descending order of how often they're right:

```python
for x in nums: ...                  # you need the values
for i, x in enumerate(nums): ...    # you need both
for i in range(len(nums)): ...      # you need indices only, or you're writing to nums[i]
```

That third form is a Java accent. It's not *wrong* — in-place problems genuinely need it — but
reaching for it by default is the clearest tell that someone is writing Java in Python.

One hard rule: **never mutate a list's length while iterating over it.** The iterator holds an
index, not a snapshot, so removing an element shifts the tail left and the iterator skips one.

```python
nums = [1, 2, 2, 3]
for x in nums:
    if x == 2:
        nums.remove(x)
print(nums)      # [1, 2, 3]  — the second 2 survived
```

---

## 4. Capacity vs length — the chapter that hides

In Java, this distinction is your problem. `new int[6]` gives you six slots forever; if you're only
using four of them, *you* keep the `4` in a variable, and the array itself can't tell you.

In Python, `len(nums)` is the length. Capacity is real, but it's a private field on the list object
called `allocated`, and nothing in the language surface exposes it. You can back it out:

```python
import sys
lst = []
for n in range(25):
    capacity = (sys.getsizeof(lst) - sys.getsizeof([])) // 8
    print(f"len={n:<3} capacity={capacity}")
    lst.append(n)
```

Measured here (empty list header = 56 bytes, 8 bytes per pointer slot):

```
len:       0   1   2   3   4   5   6   7   8   9  ... 16  17 ... 24
capacity:  0   4   4   4   4   8   8   8   8  16  ... 16  24 ... 24
```

Capacity jumps at len 1, 5, 9, 17 — to 4, 8, 16, 24. That's CPython's `list_resize`:

```c
new_allocated = ((size_t)newsize + (newsize >> 3) + 6) & ~(size_t)3;
```

Roughly **1.125× plus 6, rounded down to a multiple of 4**. Note it's *not* the 2× you may have
been taught — CPython trades a few extra reallocations for much less wasted memory.

**Why this makes `append` O(1) amortized.** Most appends write into a slot that already exists:
O(1). Occasionally one finds `allocated` full, allocates a bigger block, and copies everything:
O(n). Because capacity grows *geometrically*, those copies get rarer at exactly the rate they get
more expensive, and the total copying across n appends sums to O(n) — O(1) each on average. Any
single append can still be slow; the average cannot.

**Constructing from a known length skips all of it.** `list(range(1000))` measures 8056 bytes —
exactly 1000 slots, zero slack, because the constructor knew the size and allocated once. Same for
`[0] * 1000`. Preallocating a result list beats appending to it, when you know n.

**The operations that are secretly O(n).** Capacity only helps at the *end* of the list. Anything
that touches the front has to `memmove` the entire tail:

```python
nums.insert(0, x)   # O(n) — shifts every element right
nums.pop(0)         # O(n) — shifts every element left
nums.append(x)      # O(1) amortized
nums.pop()          # O(1)
```

A loop doing `pop(0)` n times is O(n²) and will time out on LeetCode's larger cases. When you need
both ends, `collections.deque` gives O(1) at each — but it's a doubly-linked list of blocks, so it
gives up O(1) random indexing to do it. That trade is the whole reason both types exist.

This is exactly the card's "shifting elements" material. Java makes you write the shift loop by
hand; Python does the `memmove` for you at C speed. The complexity is identical. Only the
visibility changed — which is precisely why it's easy to write accidentally quadratic Python.

---

## 5. The in-place trap — learn this now, not in Chapter 5

LeetCode's in-place problems ignore your return value and inspect the list you were handed. Python
makes it very easy to modify a *different* list by accident:

```python
def wrong(nums):
    nums = sorted(nums)     # rebinds the local name to a NEW list.
                            # The caller's list is untouched. Silent wrong answer.

def right(nums):
    nums.sort()             # mutates in place

def also_right(nums):
    nums[:] = sorted(nums)  # slice-assign overwrites the caller's contents
```

`nums = ...` points a local name somewhere new. `nums[:] = ...` reaches through the name and
overwrites the object. Python's argument passing gives you a *reference to the same object*, so
mutation is visible to the caller and rebinding is not.

Chapter 5 is nothing but this. Chapter 1's problems don't need it. Internalize it anyway — it is
the most common way a correct Python algorithm gets marked wrong.

---

## 6. Complexity reference for `list`

| Operation | Complexity | Notes |
|---|---|---|
| `nums[i]`, `nums[i] = v` | O(1) | |
| `len(nums)` | O(1) | stored field, never counted |
| `nums.append(x)` | O(1) amortized | occasional O(n) realloc |
| `nums.pop()` | O(1) | |
| `nums.insert(i, x)` | O(n) | shifts the tail |
| `nums.pop(i)`, `del nums[i]` | O(n) | shifts the tail |
| `nums.remove(x)` | O(n) | searches, then shifts |
| `x in nums` | O(n) | **use a `set` if you're doing this in a loop** |
| `nums[a:b]` | O(b−a) time and space | copies |
| `nums.sort()`, `sorted(nums)` | O(n log n) | `sort()` in place, `sorted()` copies |
| `nums.reverse()` | O(n), O(1) space | `nums[::-1]` copies instead |
| `min`, `max`, `sum` | O(n) | |

The one that decides pass/fail most often is `x in nums`. Nested inside a loop it's a silent O(n²),
and swapping the container to a `set` makes it O(n) with a one-line change.

---

## 7. Before you start the problems

Run these and predict each answer *before* you look. Getting one wrong is worth more than the
three problems that follow.

```python
import sys

a = [1, 2, 3]
b = a
b.append(4)
print(a)                            # 1. ?

c = a[:]
c.append(5)
print(a)                            # 2. ?

grid = [[0] * 3] * 2
grid[0][0] = 9
print(grid)                         # 3. ?  (this one bites hard)

print(sys.getsizeof([0] * 1000),
      sys.getsizeof(list(range(1000))))   # 4. equal or not?

nums = [1, 2, 3]
print(nums[3:])                     # 5. ?
```

Then open `arrays101/ch01/`. Three problems: **485 Max Consecutive Ones**, **1295 Find Numbers with
Even Number of Digits**, **977 Squares of a Sorted Array**.

Each one has a trap that this note has already warned you about.
