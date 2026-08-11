"""Spec for 977. Squares of a Sorted Array.

Both methods are held to the same correctness bar. `sortedSquares` is additionally held to the
follow-up's constraint: linear time, which rules out sorting the squares.

That constraint is enforced by three independent layers, because no single one is sufficient:

  static guard   `test_linear_does_not_sort` parses the whole solution module, walks the call
                 graph out of `sortedSquares`, and rejects the standard library's ordering
                 machinery wherever it is reachable.

  dynamic guard  `test_linear_comparison_budget` feeds the solution integers that tally every
                 order comparison they take part in, and holds the total to a linear budget.
                 This one sees hand-rolled sorts, which carry no telltale name.

  growth guard   `test_linear_does_not_grow_quadratically` times the solution at n and 8n and
                 rejects super-linear growth. This one sees costs that are invisible to a
                 comparison counter, such as repeated insertion at the front of a list.

Each layer covers a blind spot of the others, and the reason they are all needed is worth
knowing. Comparison counts measured on this repo's interpreter (CPython 3.14.4), n = 4000,
squares of a sorted array:

    two-pointer, one comparison per step        4_000    1.00n
    hand-written merge of the two halves        6_008    1.50n
    two-pointer written with max()              8_000    2.00n
    ------------------------------------------------- budget: 6n = 24_000
    bisect.insort into a kept-sorted list      43_086   10.77n
    heapify + repeated heappop                 49_852   12.46n
    repeated min() over the remaining values 7_998_000 1999.50n

Note what is missing from that table: `sorted()` itself, which costs only 8_192 comparisons
(2.05n) here. CPython's sort is adaptive, and the squares of a sorted array are two already
ordered runs in a V shape, so it merges them in essentially one pass -- indistinguishable from
a legitimate linear solution by comparison count alone. (On genuinely random data of the same
size the same call costs 42_622 comparisons, 10.66n.) That is precisely why the static guard
cannot be dropped in favour of the counter.

None of these layers is a proof. A determined workaround will always beat a source scan, and
the static guard in particular is a tripwire, not a sandbox. They exist so that the follow-up
cannot be passed by accident.

One known false positive, kept deliberately: the static guard cannot tell a local variable
named `sorted` from the builtin, so naming one that fails the guard. The message says so, and
shadowing a builtin is worth not doing anyway.
"""

import ast
import inspect
import random
import sys
import time

import pytest

from arrays101.ch01.p03_squares_of_sorted_array import Solution

CASES: list[tuple[list[int], list[int]]] = [
    # --- LeetCode's own examples ---------------------------------------------------
    ([-4, -1, 0, 3, 10], [0, 1, 9, 16, 100]),
    ([-7, -3, 2, 3, 11], [4, 9, 9, 49, 121]),
    # --- single element --------------------------------------------------------------
    ([0], [0]),
    ([5], [25]),
    ([-5], [25]),
    # --- entirely one sign -----------------------------------------------------------
    ([1, 2, 3, 4], [1, 4, 9, 16]),  # all positive: already in order
    ([-4, -3, -2, -1], [1, 4, 9, 16]),  # all negative: exactly reversed
    # --- zeros -----------------------------------------------------------------------
    ([0, 0, 0], [0, 0, 0]),
    ([-2, 0, 2], [0, 4, 4]),
    ([-1, 0], [0, 1]),
    ([0, 1], [0, 1]),
    # --- symmetric: every square appears twice ---------------------------------------
    ([-3, -3, 3, 3], [9, 9, 9, 9]),
    ([-2, -1, 1, 2], [1, 1, 4, 4]),
    # --- the crossover sits at each possible position --------------------------------
    ([-1, 2, 3, 4], [1, 4, 9, 16]),
    ([-3, -2, -1, 4], [1, 4, 9, 16]),
    ([-4, -3, 2, 3], [4, 9, 9, 16]),
    # --- lopsided magnitudes: the big value is on the left ----------------------------
    ([-100, 1, 2], [1, 4, 10000]),
    ([-1, 2, 100], [1, 4, 10000]),
    # --- duplicates ------------------------------------------------------------------
    ([-2, -2, -2], [4, 4, 4]),
    ([1, 1, 1], [1, 1, 1]),
    # --- constraint extremes ----------------------------------------------------------
    ([-10_000, 10_000], [100_000_000, 100_000_000]),
]


# ======================================================================================
# Layer 1: the static guard.
# ======================================================================================

# Modules that exist, in whole or in part, to put things in order. Anything imported from one
# of these is treated as tainted, whatever it is renamed to, because new ordering helpers keep
# being added and enumerating them by hand is a losing game.
_ORDERING_MODULES = frozenset({"heapq", "bisect", "operator", "functools", "builtins"})

_BANNED_NAMES = frozenset(
    {
        # the sort primitives
        "sorted",
        # the naive method: sortedSquares may not simply delegate to it
        "sortedSquaresNaive",
        # the modules above, referenced directly
        *_ORDERING_MODULES,
        # individual ordering entry points, in case one arrives by some other route
        "nsmallest",
        "nlargest",
        "heapify",
        "heappop",
        "heappush",
        "heappushpop",
        "heapreplace",
        "insort",
        "insort_left",
        "insort_right",
        "methodcaller",
        "attrgetter",
        "itemgetter",
        "cmp_to_key",
        "reduce",
        # dynamic lookup: hides the real name inside a string literal, where no AST walk
        # can see it
        "getattr",
        "setattr",
        # source-in-a-string escape hatches. Their mere presence in a solution to this
        # problem is disqualifying.
        "eval",
        "exec",
        "compile",
        "__import__",
        "__builtins__",
        "globals",
        "vars",
        "locals",
    }
)

# `.sort()` is only ever an attribute. Everything banned as a name is banned as an attribute
# too, so that `builtins.sorted` and `list.sort` are caught alongside the bare spellings.
_BANNED_ATTRS = _BANNED_NAMES | {"sort"}


def _tainted_aliases(tree: ast.Module) -> set[str]:
    """Names bound by an import that resolve to something banned.

    `from builtins import sorted as _srt` binds the real `sorted` to `_srt`; the call site then
    mentions no banned name at all. Resolve the alias back to what it came from.
    """
    tainted: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _BANNED_NAMES:
                    tainted.add(alias.asname or root)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            for alias in node.names:
                if root in _ORDERING_MODULES or alias.name in _BANNED_NAMES:
                    tainted.add(alias.asname or alias.name)
    return tainted


def _index_functions(tree: ast.Module) -> tuple[dict[str, ast.AST], dict[str, ast.AST]]:
    """Every module-level function and every method, by name."""
    module_fns: dict[str, ast.AST] = {}
    methods: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            module_fns[node.name] = node
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef | ast.AsyncFunctionDef):
                    methods.setdefault(sub.name, sub)
    return module_fns, methods


def _ordering_use_reachable_from(cls: type, entry: str) -> str | None:
    """Describe an ordering primitive reachable from `cls.entry`, or return None.

    Parses the whole solution module rather than one function body, then walks the call graph
    out of `entry`: calls to module-level functions and to sibling methods are followed, so a
    sort moved into a helper is still found. Within each reachable function, any *load* of a
    banned name or attribute counts -- not only a load that happens to sit in the callee
    position -- so binding `list.sort` to a local first does not help.

    Works on the AST rather than the text, so comments and docstrings that merely mention
    sorted() do not trip it.
    """
    tree = ast.parse(inspect.getsource(sys.modules[cls.__module__]))
    module_fns, methods = _index_functions(tree)
    banned_names = _BANNED_NAMES | _tainted_aliases(tree)

    seen: set[str] = set()
    stack: list[tuple[str, ast.AST]] = []
    if entry in methods:
        stack.append((entry, methods[entry]))

    while stack:
        where, fn = stack.pop()
        if where in seen:
            continue
        seen.add(where)
        origin = "" if where == entry else f" (reached from {entry}())"
        for node in ast.walk(fn):
            # A call whose callee is itself a call: getattr(x, "sort")() and
            # operator.methodcaller("sort")(x) both have this shape, and the method name hides
            # in a string literal the AST cannot inspect. Nothing legitimate in a linear
            # solution to this problem looks like this.
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Call):
                return (
                    f"{where}(){origin} calls the result of another call, which hides what is "
                    f"actually being called"
                )
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id in banned_names:
                    return f"{where}(){origin} uses the name {node.id!r}"
                if node.id in module_fns:
                    stack.append((node.id, module_fns[node.id]))
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                if node.attr in _BANNED_ATTRS:
                    return f"{where}(){origin} uses the attribute .{node.attr}"
                if node.attr in methods:
                    stack.append((node.attr, methods[node.attr]))
    return None


# ======================================================================================
# Layer 2: the comparison counter.
# ======================================================================================


class _BudgetBlown(Exception):
    """Raised from inside a comparison the moment the budget is exceeded."""


class _Counted(int):
    """An int that tallies every order comparison it takes part in.

    Arithmetic returns `_Counted` as well, so the tally survives squaring, negation and abs()
    and keeps counting the comparisons made between the squares themselves.
    """

    tally = 0
    budget = sys.maxsize

    __hash__ = int.__hash__

    @classmethod
    def _tick(cls) -> None:
        cls.tally += 1
        if cls.tally > cls.budget:
            # Bail out immediately rather than letting a quadratic solution grind through
            # millions of Python-level comparisons before the assertion runs.
            raise _BudgetBlown

    def __lt__(self, other):
        _Counted._tick()
        return int(self) < int(other)

    def __gt__(self, other):
        _Counted._tick()
        return int(self) > int(other)

    def __le__(self, other):
        _Counted._tick()
        return int(self) <= int(other)

    def __ge__(self, other):
        _Counted._tick()
        return int(self) >= int(other)

    def __mul__(self, other):
        return _Counted(int(self) * int(other))

    __rmul__ = __mul__

    def __add__(self, other):
        return _Counted(int(self) + int(other))

    __radd__ = __add__

    def __sub__(self, other):
        return _Counted(int(self) - int(other))

    def __rsub__(self, other):
        return _Counted(int(other) - int(self))

    def __pow__(self, other, mod=None):
        return _Counted(pow(int(self), int(other)))

    def __abs__(self):
        return _Counted(abs(int(self)))

    def __neg__(self):
        return _Counted(-int(self))

    def __pos__(self):
        return _Counted(int(self))


# ======================================================================================
# Tests.
# ======================================================================================


@pytest.mark.parametrize("nums,expected", CASES)
def test_naive(nums: list[int], expected: list[int]) -> None:
    original = list(nums)
    assert Solution().sortedSquaresNaive(nums) == expected
    assert nums == original, "return a new list; don't mutate the input"


@pytest.mark.parametrize("nums,expected", CASES)
def test_linear(nums: list[int], expected: list[int]) -> None:
    original = list(nums)
    assert Solution().sortedSquares(nums) == expected
    assert nums == original, "return a new list; don't mutate the input"


def test_linear_does_not_sort() -> None:
    """The follow-up asks for O(n). Sorting is O(n log n), so it is off the table.

    min()/max() on two scalars stay legal -- that's O(1) and shows up in a perfectly good
    linear solution. Only handing the collection to something that orders it is banned, and
    it stays banned when it is renamed, moved into a helper, or looked up by string.
    """
    found = _ordering_use_reachable_from(Solution, "sortedSquares")
    assert found is None, (
        f"{found}. That is a route to the library's ordering machinery, and it stays one when "
        f"it is renamed, moved into a helper, or looked up by string. The square-then-sort "
        f"version belongs in sortedSquaresNaive; the input here is already sorted, and the "
        f"O(n) solution exploits that ordering directly. (If the name above is one of your "
        f"own, rename it -- this guard cannot tell your `sorted` from the builtin.)"
    )


def test_linear_comparison_budget() -> None:
    """A linear solution compares each element a fixed number of times, not log n times.

    This catches the sorts that carry no banned name: a hand-written heap, an insertion sort,
    repeated min() over what is left. See the module docstring for the measured spread -- the
    most comparison-hungry correct solution measured spends 2.00 per element, the cheapest
    sort-based one spends 10.77.
    """
    n = 4_000
    budget = 6 * n
    rng = random.Random(977)
    nums = [_Counted(v) for v in sorted(rng.randint(-10_000, 10_000) for _ in range(n))]
    expected = sorted(int(v) * int(v) for v in nums)

    _Counted.tally = 0
    _Counted.budget = budget
    blown = False
    try:
        out = Solution().sortedSquares(nums)
    except _BudgetBlown:
        blown = True
    finally:
        _Counted.budget = sys.maxsize

    complaint = (
        f"sortedSquares spent more than {budget:,} order comparisons on {n:,} elements "
        f"(over {budget // n} per element). Anything that puts the squares in order by "
        f"comparing them against each other -- a heap, an insertion into a kept-sorted list, "
        f"repeated min() over the remaining values -- costs at least log n comparisons per "
        f"element. The input is already sorted; the O(n) solution exploits that ordering "
        f"directly."
    )
    assert not blown, complaint
    assert _Counted.tally <= budget, (
        f"{complaint} (measured {_Counted.tally:,}, {_Counted.tally / n:.2f} per element)"
    )
    assert [int(v) for v in out] == expected


def test_linear_ignores_value_range() -> None:
    """The cost must depend on how many numbers there are, not on how large they are.

    Bucketing the squares across every value the constraints permit sorts them without
    comparing anything, so neither of the other two guards sees it -- but it throws away the
    ordering the input came with, which is the one thing this problem is about. Inputs here
    deliberately run past the stated |nums[i]| <= 10^4 to make that dependency visible.
    """
    nums = [-(10**12), -(10**9), -7, 0, 3, 10**6, 10**12]
    assert Solution().sortedSquares(nums) == sorted(x * x for x in nums), (
        "sortedSquares broke on values outside the stated constraint range, which means its "
        "work is indexed by the values rather than driven by their order. The magnitudes are "
        "not the point -- the order they arrive in is."
    )


@pytest.mark.property
@pytest.mark.parametrize("method", ["sortedSquaresNaive", "sortedSquares"])
def test_matches_oracle_on_random_inputs(method: str) -> None:
    solve = getattr(Solution(), method)
    rng = random.Random(977)
    for _ in range(2000):
        n = rng.randint(1, 40)
        # Narrow ranges force ties; wide ranges force big crossovers.
        lo = rng.choice([-10_000, -50, -5, 0])
        hi = rng.choice([0, 5, 50, 10_000])
        nums = sorted(rng.randint(lo, max(lo, hi)) for _ in range(n))
        assert solve(nums) == sorted(x * x for x in nums), f"disagreed on {nums}"


@pytest.mark.slow
@pytest.mark.parametrize("method", ["sortedSquaresNaive", "sortedSquares"])
def test_large_input(method: str) -> None:
    solve = getattr(Solution(), method)
    rng = random.Random(1)
    nums = sorted(rng.randint(-10_000, 10_000) for _ in range(10_000))
    assert solve(nums) == sorted(x * x for x in nums)


@pytest.mark.slow
def test_linear_does_not_grow_quadratically() -> None:
    """Eight times the input should cost about eight times the work.

    A quadratic solution costs about sixty-four times as much, so the two are far enough apart
    that ordinary machine noise cannot confuse them. This is the layer that sees costs a
    comparison counter cannot: building the output with insert(0, ...) does exactly one
    comparison per element and still takes quadratic time, because every insert shifts the
    whole list along.

    Times are the best of several runs, which throws away interference from other processes.
    """
    n, factor, ceiling = 2_500, 8, 20.0
    rng = random.Random(1)
    small = sorted(rng.randint(-10_000, 10_000) for _ in range(n))
    big = sorted(rng.randint(-10_000, 10_000) for _ in range(n * factor))

    def best_of(xs: list[int], reps: int) -> float:
        solve = Solution().sortedSquares
        fastest = float("inf")
        for _ in range(reps):
            start = time.perf_counter()
            solve(xs)
            fastest = min(fastest, time.perf_counter() - start)
        return fastest

    small_time = best_of(small, 9)
    ratio = best_of(big, 3) / small_time
    assert ratio < ceiling, (
        f"{factor}x the input cost {ratio:.0f}x the time (n={n:,} -> {n * factor:,}). A linear "
        f"solution lands near {factor}x; {ratio:.0f}x means the per-element work grows with n. "
        f"The algorithm may well be right -- look instead for a step inside the loop that is "
        f"not O(1): inserting at the front of a list, searching a list with `in`, or slicing "
        f"it. Each of those is O(n) on its own, and doing it n times is the whole cost."
    )
