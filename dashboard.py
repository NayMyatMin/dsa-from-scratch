#!/usr/bin/env python3
"""Generate dashboard.html — a live map of what to read, code, and experiment with next.

Everything shown is read from the repo at generation time: the section list and the counts
quoted on the page come from notes/, problem status comes from actually running the whole
test suite, and the chapter map comes from which directories exist. The figures are counted
from the files rather than typed in, so they cannot drift.

    uv run python dashboard.py          # regenerate, running the tests
    uv run python dashboard.py --fast   # regenerate, reusing the last live test run
    uv run python dashboard.py --serve  # regenerate, then serve it and open a browser
    uv run python dashboard.py --serve --port 9000   # ... on a port you pick

--serve defaults to port 8765 and walks upward to the next free port if that one is taken,
which usually means a dashboard from an earlier run is still serving.

--fast does not invent a status. The last live (passed, failed) per problem is cached inside
dashboard.html itself, restored on the next --fast run, and the page says how old it is. A
problem whose stub has changed since that run reverts to "unknown" rather than lying.

Reading progress is the one thing the repo cannot know, so it lives in your browser's
localStorage and survives regeneration. Prefer --serve: some browsers refuse to persist
localStorage for pages opened directly from disk, which would silently lose your ticks.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

ROOT = Path(__file__).parent
WPM = 130  # technical prose with code blocks reads slower than it looks
DEFAULT_PORT = 8765
# Editorial judgement, and the one thing here the files cannot supply: per chapter, the
# sections that carry the model everything later depends on, and so are worth reading
# before coding. A chapter absent from this map treats every section it has as core.
CORE_SECTIONS = {1: 7, 2: 5, 3: 6}
# The last live test run rides along inside the page it produced, so --fast has something
# true to show and no extra file has to appear in the working tree.
CACHE_RE = re.compile(r'<script type="application/json" id="cache">(.*?)</script>', re.S)


# --------------------------------------------------------------------------- model


@dataclass
class Section:
    num: int
    title: str
    words: int
    subsections: int
    code_blocks: int = 0
    drills: int = 0
    chapter: int = 1
    notes: str = ""

    @property
    def minutes(self) -> int:
        return max(1, round(self.words / WPM))

    @property
    def label(self) -> str:
        """How the section is named on the page and in the hero: chapter, then number."""
        return f"{self.chapter}.{self.num}"

    @property
    def core(self) -> bool:
        return self.num <= CORE_SECTIONS.get(self.chapter, self.num)

    @property
    def html_id(self) -> str:
        """Reading-progress key. Hashed from the title, so a tick follows its section when
        the notes are renumbered instead of silently landing on whatever is now in slot n."""
        return "s" + hashlib.sha1(self.title.encode("utf-8"),
                                  usedforsecurity=False).hexdigest()[:8]


@dataclass
class Problem:
    slug: str
    number: str
    title: str
    difficulty: str
    stub: str
    test: str
    started: bool
    passed: int = 0
    failed: int = 0
    unknown: bool = False

    @property
    def state(self) -> str:
        if self.unknown:
            return "unknown"
        if self.failed == 0 and self.passed > 0:
            return "green"
        return "started" if self.started else "todo"


@dataclass
class Chapter:
    num: int
    name: str
    notes: str | None = None
    note_words: int = 0
    problems: list[Problem] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    hints: str | None = None
    source_captured: bool = False

    @property
    def core_sections(self) -> int:
        return min(CORE_SECTIONS.get(self.num, len(self.sections)), len(self.sections))


CHAPTER_NAMES = {
    1: "Introduction",
    2: "Inserting Items Into an Array",
    3: "Deleting Items From an Array",
    4: "Searching for Items in an Array",
    5: "In-Place Operations",
    6: "Conclusion",
}


# ----------------------------------------------------------------------- discovery


def parse_sections(path: Path, chapter: int = 1) -> list[Section]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^## (\d+)\. (.+)$", text, flags=re.M)
    rel = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    out: list[Section] = []
    for i in range(1, len(parts), 3):
        num, title, body = int(parts[i]), parts[i + 1], parts[i + 2]
        out.append(Section(
            num, title, len(body.split()), body.count("\n### "),
            code_blocks=len(re.findall(r"^```python\b", body, flags=re.M)),
            drills=len({int(d) for d in re.findall(r"\bDrill (\d+)\b", body)}),
            chapter=chapter, notes=rel,
        ))
    return out


def docstring_header(stub: Path) -> tuple[str, str, str]:
    """Pull '485. Max Consecutive Ones  (Easy)' out of the module docstring."""
    first = stub.read_text(encoding="utf-8").lstrip('"').splitlines()[0].strip()
    m = re.match(r"(\d+)\.\s+(.+?)\s*\((\w+)\)", first)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return "?", stub.stem, "?"


def read_junit(report: Path) -> tuple[int, int] | None:
    """(passed, failed) out of pytest's own XML report, or None if there isn't one."""
    try:
        root = ElementTree.parse(report).getroot()
        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
        total = bad = skipped = 0
        for suite in suites:
            total += int(suite.get("tests", "0"))
            bad += int(suite.get("failures", "0")) + int(suite.get("errors", "0"))
            skipped += int(suite.get("skipped", "0"))
    except (OSError, ElementTree.ParseError, TypeError, ValueError):
        return None
    return max(total - bad - skipped, 0), bad


def run_tests(test_file: Path) -> tuple[int, int, bool]:
    """Return (passed, failed, unknown) by actually running pytest.

    The whole file runs, slow tier included: the slow tests are precisely the ones that
    catch a quadratic solution, so excluding them would let the page say "passing" about a
    suite that is red the moment you run it yourself.

    Counts come from pytest's machine-readable report rather than from its prose. Scanning
    stdout reads the first "N passed" anywhere in the output, and pytest prints its FAILED
    rows — test ids, assertion reprs — above the summary line.
    """
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.xml"
        try:
            r = subprocess.run(
                ["uv", "run", "pytest", str(test_file), "--no-header", "--tb=no",
                 f"--junit-xml={report}"],
                cwd=ROOT, capture_output=True, text=True, timeout=300,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return 0, 0, True
        counts = read_junit(report)
    # 0 = all passed, 1 = tests failed. 2 interrupted, 3 internal error, 4 usage error and
    # 5 nothing collected all mean the run never produced a verdict worth showing.
    if counts is None or r.returncode not in (0, 1):
        return 0, 0, True
    passed, failed = counts
    return (passed, failed, False) if passed or failed else (0, 0, True)


def stub_fingerprint(stub: Path) -> str:
    """Cheap 'has this changed since the last test run' marker."""
    try:
        st = stub.stat()
    except OSError:
        return ""
    return f"{st.st_size}:{st.st_mtime_ns}"


def read_cache() -> tuple[str, dict[str, dict]]:
    """Reload the last live test run from the page that run produced."""
    out = ROOT / "dashboard.html"
    if not out.exists():
        return "", {}
    try:
        m = CACHE_RE.search(out.read_text(encoding="utf-8"))
        blob = json.loads(m.group(1)) if m else {}
        return str(blob.get("at", "")), {
            str(slug): {"passed": int(v["passed"]), "failed": int(v["failed"]),
                        "stub": str(v["stub"])}
            for slug, v in dict(blob.get("problems", {})).items()
        }
    except (OSError, UnicodeDecodeError, AttributeError, TypeError, ValueError, KeyError):
        return "", {}


def discover(run: bool, cached: dict[str, dict] | None = None) -> list[Chapter]:
    cached = cached or {}
    chapters: list[Chapter] = []
    for num, name in CHAPTER_NAMES.items():
        ch = Chapter(num, name)

        for note in sorted((ROOT / "notes").glob(f"{num:02d}_*.md")):
            ch.notes = str(note.relative_to(ROOT))
            ch.note_words = len(note.read_text(encoding="utf-8").split())
            ch.sections = parse_sections(note, num)

        hints = ROOT / "hints" / f"ch{num:02d}.md"
        if hints.exists():
            ch.hints = str(hints.relative_to(ROOT))

        src = ROOT / ".leetcode-source"
        ch.source_captured = num == 1 or any(
            f"CHAPTER {num} " in p.read_text(encoding="utf-8") for p in src.glob("*.md")
        ) if src.exists() else False

        for stub in sorted((ROOT / "arrays101" / f"ch{num:02d}").glob("p*.py")):
            number, title, diff = docstring_header(stub)
            test = ROOT / "tests" / f"ch{num:02d}" / f"test_{stub.stem}.py"
            started = "NotImplementedError" not in stub.read_text(encoding="utf-8")
            p = Problem(
                slug=stub.stem, number=number, title=title, difficulty=diff,
                stub=str(stub.relative_to(ROOT)),
                test=str(test.relative_to(ROOT)) if test.exists() else "",
                started=started,
            )
            # --fast reuses the last live run, but only while the stub it was measured
            # against is untouched. An edited stub means we genuinely do not know.
            hit = None if run else cached.get(p.slug)
            if run and test.exists():
                p.passed, p.failed, p.unknown = run_tests(test)
            elif hit and hit["stub"] == stub_fingerprint(stub):
                p.passed, p.failed, p.unknown = hit["passed"], hit["failed"], False
            else:
                p.unknown = True
            ch.problems.append(p)

        chapters.append(ch)
    return chapters


# --------------------------------------------------------------------------- render

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#fbfaf9; --panel:#fff; --ink:#1a1a19; --dim:#6b6b68; --line:#e5e3e0;
  --accent:#c2571f; --green:#2c7a52; --amber:#a67514; --shadow:0 1px 2px rgba(0,0,0,.05);
}
@media (prefers-color-scheme:dark){
  :root{--bg:#16161a; --panel:#1e1e23; --ink:#eceae7; --dim:#9a9a96; --line:#2f2f36;
        --accent:#e8834a; --green:#4bb37c; --amber:#d9a441; --shadow:none}
}
:root[data-theme=dark]{--bg:#16161a;--panel:#1e1e23;--ink:#eceae7;--dim:#9a9a96;--line:#2f2f36;
  --accent:#e8834a;--green:#4bb37c;--amber:#d9a441;--shadow:none}
:root[data-theme=light]{--bg:#fbfaf9;--panel:#fff;--ink:#1a1a19;--dim:#6b6b68;--line:#e5e3e0;
  --accent:#c2571f;--green:#2c7a52;--amber:#a67514;--shadow:0 1px 2px rgba(0,0,0,.05)}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.55 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 80px;position:relative}
code,kbd{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.88em}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.02em}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.09em;color:var(--dim);
   margin:38px 0 14px;font-weight:600}
a{color:var(--accent)}
.sub{color:var(--dim);margin:0 0 26px;font-size:14px}
.bar{height:6px;background:var(--line);border-radius:99px;overflow:hidden;margin:10px 0 4px}
.bar>i{display:block;height:100%;background:var(--accent);transition:width .3s}
.hero{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:8px;padding:20px 22px;box-shadow:var(--shadow)}
.hero .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);font-weight:700}
.hero h3{margin:8px 0 6px;font-size:19px;letter-spacing:-.01em}
.hero p{margin:0 0 14px;color:var(--dim);font-size:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;
  padding:16px 18px;box-shadow:var(--shadow)}
.grid{display:grid;gap:12px}
@media(min-width:760px){.grid.two{grid-template-columns:1fr 1fr}}
.sec{display:flex;align-items:flex-start;gap:11px;padding:9px 10px;border-radius:6px;cursor:pointer;
  border:1px solid transparent}
.sec:hover{background:var(--bg)}
.sec input{margin:3px 0 0;accent-color:var(--accent);cursor:pointer;flex:none;width:15px;height:15px}
.sec .n{color:var(--dim);font-variant-numeric:tabular-nums;flex:none;width:30px;font-size:13px}
.sec .t{flex:1;min-width:0;overflow-wrap:anywhere}
.sec .m{color:var(--dim);font-size:12px;flex:none;font-variant-numeric:tabular-nums}
.sec.done .t{opacity:.45;text-decoration:line-through}
.prob{display:flex;align-items:center;gap:12px;padding:13px 0;border-bottom:1px solid var(--line)}
.prob:last-child{border-bottom:0}
.dot{width:9px;height:9px;border-radius:99px;flex:none;background:var(--dim)}
.dot.green{background:var(--green)} .dot.started{background:var(--amber)} .dot.todo{background:var(--line);
  border:1.5px solid var(--dim)}
.prob .meta{flex:1;min-width:0;overflow-wrap:anywhere}
.prob .meta b{font-weight:600} .prob .meta small{display:block;color:var(--dim);font-size:12.5px;margin-top:2px}
.pill{font-size:11px;padding:2px 8px;border-radius:99px;border:1px solid var(--line);color:var(--dim);flex:none}
.pill.green{color:var(--green);border-color:var(--green)}
.pill.started{color:var(--amber);border-color:var(--amber)}
pre{background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:10px 12px;
  overflow-x:auto;margin:10px 0 0;font-size:12.5px}
.tscroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{text-align:left;font-weight:600;color:var(--dim);font-size:11px;text-transform:uppercase;
   letter-spacing:.07em;padding:0 10px 8px 0;border-bottom:1px solid var(--line)}
td{padding:9px 10px 9px 0;border-bottom:1px solid var(--line)}
tr:last-child td{border-bottom:0}
.tick{color:var(--green);font-weight:700} .miss{color:var(--dim)}
.toggle{position:absolute;top:30px;right:20px;background:var(--panel);border:1px solid var(--line);
  color:var(--dim);border-radius:6px;padding:5px 10px;cursor:pointer;font-size:12px}
.foot{color:var(--dim);font-size:12px;margin-top:40px;border-top:1px solid var(--line);padding-top:14px}
"""

JS = """
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const KEY='arrays101.read.v2', OLD='arrays101.read.v1';
const save=s=>localStorage.setItem(KEY,JSON.stringify([...s]));

// v1 keyed a tick to the section's position, so inserting a section handed your tick to
// whatever moved into that slot. v2 keys on a hash of the title. Carry v1 over once, by
// position, which is what it meant at the time it was written.
function read(){
  try{
    const cur=localStorage.getItem(KEY);
    if(cur!==null) return new Set(JSON.parse(cur));
    const old=localStorage.getItem(OLD);
    if(old===null) return new Set();
    const was=new Set(JSON.parse(old));
    const now=new Set($$('.sec').filter(el=>was.has(el.dataset.legacy)).map(el=>el.dataset.id));
    save(now); return now;
  }catch{return new Set()}
}

function paint(){
  const done=read();
  $$('.sec').forEach(el=>{
    const id=el.dataset.id, on=done.has(id);
    el.classList.toggle('done',on); el.querySelector('input').checked=on;
  });
  const total=$$('.sec').length, n=$$('.sec.done').length;
  $('#readbar').style.width=(total?n/total*100:0)+'%';
  $('#readcount').textContent=`${n} of ${total} sections`;
  hero(done);
}

function hero(done){
  const secs=$$('.sec');
  const unread=secs.filter(el=>!done.has(el.dataset.id));
  // Gate on the core sections themselves, not on a count of them: ticking the tail of a
  // chapter leaves the sections this very sentence calls the core unread. Which sections
  // those are is decided per chapter in the generator and arrives stamped on the row.
  const coreLeft=unread.filter(el=>el.dataset.core==='1');
  const next=unread[0];
  const probs=DATA.problems;
  const prob=probs.find(p=>p.state!=='green'&&p.state!=='unknown');
  const stale=probs.filter(p=>p.state==='unknown');
  let lbl,h,p,cmd;
  if(coreLeft.length){
    const s=coreLeft[0];
    lbl='Read next';
    h=`§${s.dataset.label}. ${s.dataset.title}`;
    p=`${s.dataset.words} words, about ${s.dataset.min} minutes. ${s.dataset.note}`.trim();
    cmd='open '+s.dataset.notes;
  }else if(prob){
    lbl = prob.state==='started' ? 'Keep going' : 'Start coding';
    h=`${prob.number}. ${prob.title}`;
    p = prob.state==='started'
      ? `Chapter ${prob.chapter}. ${prob.passed} passing, ${prob.failed} failing. Run with -x to get one focused traceback.`
      : `Chapter ${prob.chapter}. Read the docstring, then replace the raise. The tests are the spec.`;
    cmd = prob.test ? `uv run pytest ${prob.test} -x` : 'uv run pytest';
  }else if(next){
    lbl='Read next';
    h=`§${next.dataset.label}. ${next.dataset.title}`;
    p=`${next.dataset.words} words, about ${next.dataset.min} minutes.`;
    cmd='open '+next.dataset.notes;
  }else if(stale.length){
    lbl='Test status unknown';
    h=`${stale.length} of ${probs.length} problems were not checked`;
    p='This page was built with --fast and has no live result for them, so nothing here knows whether they pass. Regenerate to actually run the suite.';
    cmd='uv run python dashboard.py';
  }else if(probs.length){
    const last=probs[probs.length-1].chapter;
    lbl=`Chapter ${last} complete`;
    h=`Ask for a review, then Chapter ${last+1}`;
    p=`All ${probs.length} problems are green and every section is read. The review conversation is where most of the remaining learning is.`;
    cmd=`git add -A && git commit -m "Chapter ${last} complete"`;
  }else{
    lbl='No problems found';
    h='Nothing to code in arrays101/';
    p='Every section is read, but the generator found no p*.py stubs to work on. If that is a surprise, the directory is the place to look.';
    cmd='ls arrays101/';
  }
  $('#hl').textContent=lbl; $('#hh').textContent=h; $('#hp').textContent=p; $('#hc').textContent=cmd;
}

// The rows are <label>s, so the browser does the toggling and the whole row is a real
// click target with a real accessible name. All this has to do is record the result.
document.addEventListener('change',e=>{
  const box=e.target;
  if(!box.matches('.sec input[type=checkbox]')) return;
  const done=read(), id=box.closest('.sec').dataset.id;
  box.checked?done.add(id):done.delete(id); save(done); paint();
});
$('#reset').addEventListener('click',e=>{
  e.preventDefault(); localStorage.removeItem(KEY); localStorage.removeItem(OLD); paint();
});
$('.toggle').addEventListener('click',()=>{
  const r=document.documentElement;
  const now=r.dataset.theme||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
  r.dataset.theme=now==='dark'?'light':'dark';
});
paint();
"""


def esc(s: str) -> str:
    """HTML-escape, quotes included: most of these land inside an attribute."""
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


def link(path: str) -> str:
    """A path, safe both as a URL and as an attribute value."""
    return esc(quote(path))


def js_json(obj: object) -> str:
    """JSON for embedding in a <script>. < > & become \\uXXXX escapes — still valid JSON,
    still the same string after parsing, but no title can close the script element."""
    return (json.dumps(obj)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def render(chapters: list[Chapter], ran: bool, cache: dict) -> str:
    sections = [s for c in chapters for s in c.sections]
    problems = [(c, p) for c in chapters for p in c.problems]
    total_words = sum(s.words for s in sections)
    total_min = sum(s.minutes for s in sections)

    def core_note(s: Section) -> str:
        """The one sentence the hero adds when the section it names is core."""
        if not s.core:
            return ""
        end = next((c.core_sections for c in chapters if c.num == s.chapter), s.num)
        return (f"Sections 1–{end} of chapter {s.chapter} are the core "
                "and are best read in order.")

    # data-legacy carries the v1 progress key, which was a position in a one-chapter page.
    # Only chapter 1 can claim it; emitting it on chapter 2 would hand a reader migrating
    # from v1 eight ticks they never made.
    def legacy(s: Section) -> str:
        return f'data-legacy="s{s.num}" ' if s.chapter == 1 else ""

    secs = "\n".join(
        f'<label class="sec" data-id="{s.html_id}" {legacy(s)}data-num="{s.num}" '
        f'data-ch="{s.chapter}" data-label="{s.label}" data-core="{int(s.core)}" '
        f'data-notes="{link(s.notes)}" data-note="{esc(core_note(s))}" '
        f'data-title="{esc(s.title)}" data-words="{s.words:,}" data-min="{s.minutes}">'
        f'<input type="checkbox" aria-label="Mark chapter {s.chapter} section {s.num}, '
        f'{esc(s.title)}, as read">'
        f'<span class="n">{s.label}</span>'
        f'<span class="t">{esc(s.title)}<br><small style="color:var(--dim);font-size:12px">'
        f"{s.subsections} subsections &middot; {s.words:,} words</small></span>"
        f'<span class="m">{s.minutes}m</span></label>'
        for s in sections
    )

    def prob_row(ch: Chapter, p: Problem) -> str:
        label = {"green": "passing", "started": f"{p.failed} failing", "todo": "not started",
                 "unknown": "unknown"}[p.state]
        cls = p.state if p.state in ("green", "started") else ""
        links = f'<a href="{link(p.stub)}">stub</a>'
        if p.test:
            links += f' &middot; <a href="{link(p.test)}">tests</a>'
        if ch.hints:
            links += f' &middot; <a href="{link(ch.hints)}">hints</a>'
        return (
            f'<div class="prob"><span class="dot {p.state}"></span>'
            f'<span class="meta"><b>{esc(p.number)}. {esc(p.title)}</b>'
            f"<small>{esc(p.difficulty)} &middot; {links}</small></span>"
            f'<span class="pill {cls}">{label}</span></div>'
        )

    # Grouped by chapter, because two chapters of stubs in one flat list stops saying which
    # problems belong to what you have just read.
    coded = [c for c in chapters if c.problems]
    probs = "\n".join(
        f'<h3 style="font-size:12px;text-transform:uppercase;letter-spacing:.08em;'
        f'color:var(--dim);margin:{0 if i == 0 else 22}px 0 2px;font-weight:600">'
        f"Chapter {c.num} &mdash; {esc(c.name)}</h3>\n"
        + "\n".join(prob_row(c, p) for p in c.problems)
        for i, c in enumerate(coded)
    )

    def yn(v: object) -> str:
        return '<span class="tick">&#10003;</span>' if v else '<span class="miss">&mdash;</span>'

    rows = "\n".join(
        f"<tr><td><b>{c.num}</b> &nbsp;{esc(c.name)}</td>"
        f"<td>{yn(c.notes)}{f' <small style=color:var(--dim)>{c.note_words:,}w</small>' if c.notes else ''}</td>"
        f"<td>{len(c.problems) or yn(False)}</td>"
        f"<td>{yn(c.hints)}</td><td>{yn(c.source_captured)}</td></tr>"
        for c in chapters
    )

    data = js_json({"problems": [
        {"number": p.number, "title": p.title, "state": p.state, "passed": p.passed,
         "failed": p.failed, "test": p.test, "stub": p.stub, "chapter": c.num}
        for c, p in problems
    ]})

    if ran:
        status = "live from pytest"
    elif any(p.state != "unknown" for _, p in problems) and cache.get("at"):
        status = f"as of {esc(str(cache['at']))} &mdash; rerun without --fast for live status"
    else:
        status = "not measured &mdash; rerun without --fast for live test status"

    # Everything the Experiment cards claim about the notes, counted from the notes.
    blocks = sum(s.code_blocks for s in sections)
    drilled = max(sections, key=lambda s: s.drills, default=None)
    measuring = next((s for s in sections if re.search(r"measur", s.title, re.I)), None)
    drills_copy = (
        f"&sect;{drilled.label} is {drilled.drills} predict-the-output drills with an answer "
        "key. The honest check on whether the rest landed."
        if drilled and drilled.drills else
        "The drills at the end of a chapter are the honest check on whether the rest landed."
    )
    measure_copy = (
        f"&sect;{measuring.label} gives a reusable timing harness. Pick any claim in the "
        "notes and try to break it."
        if measuring else
        "Pick any claim in the notes and try to break it with a timing harness of your own."
    )
    drills_cmd = f"open {drilled.notes}" if drilled and drilled.notes else "ls notes/"
    first_test = next((p.test for _, p in problems if p.test), "")
    code_cmd = f"uv run pytest {first_test} -x" if first_test else "uv run pytest"
    read_chapters = sum(1 for c in chapters if c.sections)
    chapter_word = "chapter" if read_chapters == 1 else "chapters"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arrays 101 — study dashboard</title><style>{CSS}</style></head><body>
<button class="toggle">theme</button>
<div class="wrap">

<h1>Arrays 101 &mdash; Python</h1>
<p class="sub">{read_chapters} {chapter_word} of notes, {len(problems)} problems, {total_words:,} words
&middot; test status {status}</p>

<div class="hero">
  <div class="lbl" id="hl"></div>
  <h3 id="hh"></h3>
  <p id="hp"></p>
  <pre id="hc"></pre>
</div>

<h2>Read &mdash; <span id="readcount"></span>, {total_min} minutes total</h2>
<div class="bar"><i id="readbar" style="width:0"></i></div>
<div class="card" style="margin-top:12px">{secs}</div>

<h2>Code</h2>
<div class="card">{probs}
<pre>{esc(code_cmd)}</pre></div>

<h2>Experiment</h2>
<div class="grid two">
  <div class="card"><b>Run the notes</b>
    <p style="color:var(--dim);font-size:13.5px;margin:6px 0 0">All {blocks:,} code blocks are
    runnable exactly as written. Paste as you read.</p><pre>uv run python</pre></div>
  <div class="card"><b>Test yourself</b>
    <p style="color:var(--dim);font-size:13.5px;margin:6px 0 0">{drills_copy}</p>
    <pre>{esc(drills_cmd)}</pre></div>
  <div class="card"><b>Measure something</b>
    <p style="color:var(--dim);font-size:13.5px;margin:6px 0 0">{measure_copy}</p></div>
  <div class="card"><b>Check the whole suite</b>
    <p style="color:var(--dim);font-size:13.5px;margin:6px 0 0">Every problem at once, slow tests
    included &mdash; the same tests the status above comes from. A hang there means your solution
    is quadratic.</p><pre>uv run pytest</pre></div>
</div>

<h2>Syllabus</h2>
<div class="card">
<div class="tscroll">
<table><thead><tr><th>Chapter</th><th>Notes</th><th>Problems</th><th>Hints</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>
</div>

<p class="foot">Generated from the repo &mdash; sections, problems and test results are all read at
generation time. Reading progress is stored in this browser.
<a href="#" id="reset">reset progress</a><br>
Regenerate with <code>uv run python dashboard.py</code>.</p>

</div>
<script type="application/json" id="cache">{js_json(cache)}</script>
<script>const DATA={data};{JS}</script></body></html>
"""


def serve(port: int = DEFAULT_PORT, *, scan: bool = True, tries: int = 10) -> int:
    """Serve the repo so the dashboard gets a real origin, and open it.

    The overwhelmingly common reason the port is taken is a dashboard left serving from an
    earlier run, so a busy default port walks upward to the next free one instead of dying
    on a traceback. An explicit --port is taken literally: if it is busy, say so and stop.
    """
    import errno
    import functools
    import http.server
    import webbrowser

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = None
    for candidate in range(port, port + (tries if scan else 1)):
        try:
            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", candidate), handler)
        except OSError as exc:
            if exc.errno not in (errno.EADDRINUSE, errno.EACCES):
                raise
        else:
            break

    if httpd is None:
        where = f"http://127.0.0.1:{port}/dashboard.html"
        busy = f"port {port} is" if not scan else f"ports {port}-{port + tries - 1} are"
        print(f"{busy} in use; the dashboard may already be running at {where}", file=sys.stderr)
        return 1

    with httpd:
        bound = httpd.server_address[1]
        if bound != port:
            print(f"port {port} is in use (the dashboard may already be running there) — "
                  f"using {bound} instead", file=sys.stderr)
        url = f"http://127.0.0.1:{bound}/dashboard.html"
        print(f"serving {url}  (ctrl-c to stop)", file=sys.stderr)
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped", file=sys.stderr)
    return 0


def parse_port(argv: list[str]) -> tuple[int, bool] | None:
    """Read --port N / --port=N. Returns (port, scan_upward_if_busy), or None if malformed."""
    for i, arg in enumerate(argv):
        if arg == "--port":
            raw = argv[i + 1] if i + 1 < len(argv) else ""
        elif arg.startswith("--port="):
            raw = arg.split("=", 1)[1]
        else:
            continue
        try:
            value = int(raw)
        except ValueError:
            print(f"--port wants a port number, got {raw!r}", file=sys.stderr)
            return None
        if not 1 <= value <= 65535:
            print(f"--port must be between 1 and 65535, got {value}", file=sys.stderr)
            return None
        return value, False
    return DEFAULT_PORT, True


def main() -> int:
    # The notes and this script's own output are UTF-8 whatever the locale says.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass

    parsed = parse_port(sys.argv[1:])
    if parsed is None:
        return 2
    run = "--fast" not in sys.argv
    if not sorted((ROOT / "notes").glob("[0-9][0-9]_*.md")):
        print("no chapter notes found in notes/", file=sys.stderr)
        return 1
    if run:
        print("running tests for live status ...", file=sys.stderr)

    out = ROOT / "dashboard.html"
    cached_at, cached = read_cache()          # before the page it lives in is replaced
    chapters = discover(run, cached)
    sections = [s for c in chapters for s in c.sections]
    problems = [p for c in chapters for p in c.problems]
    if run:
        cache = {"at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "problems": {p.slug: {"passed": p.passed, "failed": p.failed,
                                       "stub": stub_fingerprint(ROOT / p.stub)}
                              for p in problems if not p.unknown}}
    else:
        cache = {"at": cached_at, "problems": cached}

    # Write beside the page and rename over it: a failure part-way through leaves the
    # previous dashboard intact instead of truncating it to garbage.
    tmp = out.with_suffix(".html.tmp")
    try:
        tmp.write_text(render(chapters, run, cache), encoding="utf-8")
    except OSError as exc:
        tmp.unlink(missing_ok=True)
        print(f"could not write {out.name}: {exc}\nthe previous page is untouched",
              file=sys.stderr)
        return 1
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(out)

    green = sum(1 for p in problems if p.state == "green")
    unsure = sum(1 for p in problems if p.state == "unknown")
    if problems and unsure == len(problems):
        tally = f"{len(problems)} problems, test status unknown"
    else:
        tally = f"{green}/{len(problems)} problems green"
        tally += f", {unsure} unknown" if unsure else ""
    read = sum(1 for c in chapters if c.sections)
    print(f"wrote {out.relative_to(ROOT)} — {read} chapters, {len(sections)} sections, {tally}")
    if "--serve" in sys.argv:
        port, scan = parsed
        return serve(port, scan=scan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
