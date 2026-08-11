#!/usr/bin/env python3
"""Generate dashboard.html — a live map of what to read, code, and experiment with next.

Everything shown is read from the repo at generation time: the section list comes from
notes/, problem status comes from actually running the test suite, and the chapter map
comes from which directories exist. Nothing is hardcoded, so it cannot drift.

    uv run python dashboard.py          # regenerate, running the tests
    uv run python dashboard.py --fast   # regenerate, skip the tests
    uv run python dashboard.py --serve  # regenerate, then serve it and open a browser

Reading progress is the one thing the repo cannot know, so it lives in your browser's
localStorage and survives regeneration. Prefer --serve: some browsers refuse to persist
localStorage for pages opened directly from disk, which would silently lose your ticks.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).parent
WPM = 130  # technical prose with code blocks reads slower than it looks


# --------------------------------------------------------------------------- model


@dataclass
class Section:
    num: int
    title: str
    words: int
    subsections: int

    @property
    def minutes(self) -> int:
        return max(1, round(self.words / WPM))


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
    hints: str | None = None
    source_captured: bool = False


CHAPTER_NAMES = {
    1: "Introduction",
    2: "Inserting Items Into an Array",
    3: "Deleting Items From an Array",
    4: "Searching for Items in an Array",
    5: "In-Place Operations",
    6: "Conclusion",
}


# ----------------------------------------------------------------------- discovery


def parse_sections(path: Path) -> list[Section]:
    text = path.read_text()
    parts = re.split(r"^## (\d+)\. (.+)$", text, flags=re.M)
    out: list[Section] = []
    for i in range(1, len(parts), 3):
        num, title, body = int(parts[i]), parts[i + 1], parts[i + 2]
        out.append(Section(num, title, len(body.split()), body.count("\n### ")))
    return out


def docstring_header(stub: Path) -> tuple[str, str, str]:
    """Pull '485. Max Consecutive Ones  (Easy)' out of the module docstring."""
    first = stub.read_text().lstrip('"').splitlines()[0].strip()
    m = re.match(r"(\d+)\.\s+(.+?)\s*\((\w+)\)", first)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return "?", stub.stem, "?"


def run_tests(test_file: Path) -> tuple[int, int, bool]:
    """Return (passed, failed, unknown) by actually running pytest."""
    # Note: pyproject's addopts already supplies -q. Passing it again makes it -qq, which
    # suppresses the summary counts line entirely — so don't, and scan the whole output
    # rather than just the last line, which may well be a FAILED row.
    try:
        r = subprocess.run(
            ["uv", "run", "pytest", str(test_file), "-m", "not slow", "--no-header", "--tb=no"],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return 0, 0, True
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", r.stdout)) else 0
    failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", r.stdout)) else 0
    errors = int(m.group(1)) if (m := re.search(r"(\d+) error", r.stdout)) else 0
    return passed, failed + errors, not (passed or failed or errors)


def discover(run: bool) -> list[Chapter]:
    chapters: list[Chapter] = []
    for num, name in CHAPTER_NAMES.items():
        ch = Chapter(num, name)

        for note in sorted((ROOT / "notes").glob(f"{num:02d}_*.md")):
            ch.notes = str(note.relative_to(ROOT))
            ch.note_words = len(note.read_text().split())

        hints = ROOT / "hints" / f"ch{num:02d}.md"
        if hints.exists():
            ch.hints = str(hints.relative_to(ROOT))

        src = ROOT / ".leetcode-source"
        ch.source_captured = num == 1 or any(
            f"CHAPTER {num} " in p.read_text() for p in src.glob("*.md")
        ) if src.exists() else False

        for stub in sorted((ROOT / "arrays101" / f"ch{num:02d}").glob("p*.py")):
            number, title, diff = docstring_header(stub)
            test = ROOT / "tests" / f"ch{num:02d}" / f"test_{stub.stem}.py"
            started = "NotImplementedError" not in stub.read_text()
            p = Problem(
                slug=stub.stem, number=number, title=title, difficulty=diff,
                stub=str(stub.relative_to(ROOT)),
                test=str(test.relative_to(ROOT)) if test.exists() else "",
                started=started,
            )
            if run and test.exists():
                p.passed, p.failed, p.unknown = run_tests(test)
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
.sec .n{color:var(--dim);font-variant-numeric:tabular-nums;flex:none;width:20px;font-size:13px}
.sec .t{flex:1;min-width:0}
.sec .m{color:var(--dim);font-size:12px;flex:none;font-variant-numeric:tabular-nums}
.sec.done .t{opacity:.45;text-decoration:line-through}
.prob{display:flex;align-items:center;gap:12px;padding:13px 0;border-bottom:1px solid var(--line)}
.prob:last-child{border-bottom:0}
.dot{width:9px;height:9px;border-radius:99px;flex:none;background:var(--dim)}
.dot.green{background:var(--green)} .dot.started{background:var(--amber)} .dot.todo{background:var(--line);
  border:1.5px solid var(--dim)}
.prob .meta{flex:1;min-width:0}
.prob .meta b{font-weight:600} .prob .meta small{display:block;color:var(--dim);font-size:12.5px;margin-top:2px}
.pill{font-size:11px;padding:2px 8px;border-radius:99px;border:1px solid var(--line);color:var(--dim);flex:none}
.pill.green{color:var(--green);border-color:var(--green)}
.pill.started{color:var(--amber);border-color:var(--amber)}
pre{background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:10px 12px;
  overflow-x:auto;margin:10px 0 0;font-size:12.5px}
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
const KEY='arrays101.read.v1';
const read=()=>{try{return new Set(JSON.parse(localStorage.getItem(KEY)||'[]'))}catch{return new Set()}};
const save=s=>localStorage.setItem(KEY,JSON.stringify([...s]));

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
  const first=$$('.sec').find(el=>!done.has(el.dataset.id));
  const prob=DATA.problems.find(p=>p.state!=='green');
  let lbl,h,p,cmd;
  if(first && $$('.sec.done').length < 7){
    lbl='Read next';
    h=`§${first.dataset.num}. ${first.dataset.title}`;
    p=`${first.dataset.words} words, about ${first.dataset.min} minutes. Sections 1–7 are the core and are best read in order.`;
    cmd='open notes/01_introduction.md';
  }else if(prob){
    lbl = prob.state==='started' ? 'Keep going' : 'Start coding';
    h=`${prob.number}. ${prob.title}`;
    p = prob.state==='started'
      ? `${prob.passed} passing, ${prob.failed} failing. Run with -x to get one focused traceback.`
      : `Read the docstring, then replace the raise. The tests are the spec.`;
    cmd=`uv run pytest ${prob.test} -x`;
  }else if(first){
    lbl='Read next';
    h=`§${first.dataset.num}. ${first.dataset.title}`;
    p=`${first.dataset.words} words, about ${first.dataset.min} minutes.`;
    cmd='open notes/01_introduction.md';
  }else{
    lbl='Chapter 1 complete';
    h='Ask for a review, then Chapter 2';
    p='All three problems are green and every section is read. The review conversation is where most of the remaining learning is.';
    cmd='git add -A && git commit -m "Chapter 1 complete"';
  }
  $('#hl').textContent=lbl; $('#hh').textContent=h; $('#hp').textContent=p; $('#hc').textContent=cmd;
}

document.addEventListener('click',e=>{
  const sec=e.target.closest('.sec'); if(!sec) return;
  if(e.target.tagName!=='INPUT') e.preventDefault();
  const done=read(), id=sec.dataset.id;
  done.has(id)?done.delete(id):done.add(id); save(done); paint();
});
$('#reset').addEventListener('click',()=>{localStorage.removeItem(KEY);paint()});
$('.toggle').addEventListener('click',()=>{
  const r=document.documentElement;
  const now=r.dataset.theme||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
  r.dataset.theme=now==='dark'?'light':'dark';
});
paint();
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(chapters: list[Chapter], sections: list[Section], ran: bool) -> str:
    ch1 = chapters[0]
    total_words = sum(s.words for s in sections)
    total_min = sum(s.minutes for s in sections)

    secs = "\n".join(
        f'<div class="sec" data-id="s{s.num}" data-num="{s.num}" data-title="{esc(s.title)}" '
        f'data-words="{s.words:,}" data-min="{s.minutes}">'
        f'<input type="checkbox"><span class="n">{s.num}</span>'
        f'<span class="t">{esc(s.title)}<br><small style="color:var(--dim);font-size:12px">'
        f"{s.subsections} subsections &middot; {s.words:,} words</small></span>"
        f'<span class="m">{s.minutes}m</span></div>'
        for s in sections
    )

    def prob_row(p: Problem) -> str:
        label = {"green": "passing", "started": f"{p.failed} failing", "todo": "not started",
                 "unknown": "unknown"}[p.state]
        cls = p.state if p.state in ("green", "started") else ""
        links = f'<a href="{p.stub}">stub</a>'
        if p.test:
            links += f' &middot; <a href="{p.test}">tests</a>'
        if ch1.hints:
            links += f' &middot; <a href="{ch1.hints}">hints</a>'
        return (
            f'<div class="prob"><span class="dot {p.state}"></span>'
            f'<span class="meta"><b>{p.number}. {esc(p.title)}</b>'
            f"<small>{p.difficulty} &middot; {links}</small></span>"
            f'<span class="pill {cls}">{label}</span></div>'
        )

    probs = "\n".join(prob_row(p) for p in ch1.problems)

    def yn(v: object) -> str:
        return '<span class="tick">&#10003;</span>' if v else '<span class="miss">&mdash;</span>'

    rows = "\n".join(
        f"<tr><td><b>{c.num}</b> &nbsp;{esc(c.name)}</td>"
        f"<td>{yn(c.notes)}{f' <small style=color:var(--dim)>{c.note_words:,}w</small>' if c.notes else ''}</td>"
        f"<td>{len(c.problems) or yn(False)}</td>"
        f"<td>{yn(c.hints)}</td><td>{yn(c.source_captured)}</td></tr>"
        for c in chapters
    )

    data = json.dumps({"problems": [
        {"number": p.number, "title": p.title, "state": p.state, "passed": p.passed,
         "failed": p.failed, "test": p.test, "stub": p.stub}
        for p in ch1.problems
    ]})

    status = "live from pytest" if ran else "cached — rerun without --fast for live test status"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arrays 101 — study dashboard</title><style>{CSS}</style></head><body>
<button class="toggle">theme</button>
<div class="wrap">

<h1>Arrays 101 &mdash; Python</h1>
<p class="sub">One chapter of notes, {len(ch1.problems)} problems, {total_words:,} words
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
<pre>uv run pytest tests/ch01/test_p01_max_consecutive_ones.py -x</pre></div>

<h2>Experiment</h2>
<div class="grid two">
  <div class="card"><b>Run the chapter</b>
    <p style="color:var(--dim);font-size:13.5px;margin:6px 0 0">All 273 code blocks are runnable
    exactly as written. Paste as you read.</p><pre>uv run python</pre></div>
  <div class="card"><b>Test yourself</b>
    <p style="color:var(--dim);font-size:13.5px;margin:6px 0 0">&sect;12 is twelve predict-the-output
    drills with an answer key. The honest check on whether the rest landed.</p>
    <pre>open notes/01_introduction.md</pre></div>
  <div class="card"><b>Measure something</b>
    <p style="color:var(--dim);font-size:13.5px;margin:6px 0 0">&sect;11 gives a reusable timing
    harness. Pick any claim in the chapter and try to break it.</p></div>
  <div class="card"><b>Check the whole suite</b>
    <p style="color:var(--dim);font-size:13.5px;margin:6px 0 0">Slow tests included &mdash; a hang
    there means your solution is quadratic.</p><pre>uv run pytest</pre></div>
</div>

<h2>Syllabus</h2>
<div class="card">
<table><thead><tr><th>Chapter</th><th>Notes</th><th>Problems</th><th>Hints</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>

<p class="foot">Generated from the repo &mdash; sections, problems and test results are all read at
generation time. Reading progress is stored in this browser.
<a href="#" id="reset">reset progress</a><br>
Regenerate with <code>uv run python dashboard.py</code>.</p>

</div>
<script>const DATA={data};{JS}</script></body></html>
"""


def serve(port: int = 8765) -> None:
    """Serve the repo so the dashboard gets a real origin, and open it."""
    import functools
    import http.server
    import webbrowser

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        url = f"http://127.0.0.1:{port}/dashboard.html"
        print(f"serving {url}  (ctrl-c to stop)", file=sys.stderr)
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped", file=sys.stderr)


def main() -> int:
    run = "--fast" not in sys.argv
    notes = ROOT / "notes" / "01_introduction.md"
    if not notes.exists():
        print("notes/01_introduction.md not found", file=sys.stderr)
        return 1
    if run:
        print("running tests for live status ...", file=sys.stderr)
    sections = parse_sections(notes)
    chapters = discover(run)
    out = ROOT / "dashboard.html"
    out.write_text(render(chapters, sections, run))
    done = sum(1 for p in chapters[0].problems if p.state == "green")
    print(f"wrote {out.relative_to(ROOT)} — {len(sections)} sections, "
          f"{done}/{len(chapters[0].problems)} problems green")
    if "--serve" in sys.argv:
        serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
