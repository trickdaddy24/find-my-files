# Find My Files — UI Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three missing UI features to `Find My Files.html`: a status bar, a cancel button, and a zero-results empty state.

**Architecture:** All changes are confined to a single self-contained HTML file (`Find My Files.html`). No build step — the file runs directly in a browser via Babel inline transform. Each task is independent; completing them in order is recommended but not required.

**Tech Stack:** React 18 (UMD), Babel standalone, Lucide icons (UMD), Geist font (Google Fonts CDN). No npm, no bundler.

---

## File Map

| File | Change |
|---|---|
| `Find My Files.html` | All three edits — single file, self-contained prototype |

No other files change.

---

## Task 1: Status Bar

**File:** `Find My Files.html`

The status bar is a 24 px strip at the very bottom of the app showing search metadata after a search completes, or "Ready" when idle, or "Cancelled" after a cancel.

### Layout change

The outer `App` div currently uses `display:flex` (row). Wrap the sidebar+main in a new inner div, and make the outer div a column so the status bar can sit below.

**Current structure (line 654):**
```jsx
<div style={{ display:"flex", height:"100vh", background:bg, backgroundImage:radialBg, overflow:"hidden", transition:"background .3s" }}>
  <Sidebar ... />
  <main ...>...</main>
</div>
```

**New structure:**
```jsx
<div style={{ display:"flex", flexDirection:"column", height:"100vh", background:bg, backgroundImage:radialBg, overflow:"hidden", transition:"background .3s" }}>
  <div style={{ display:"flex", flex:1, overflow:"hidden" }}>
    <Sidebar ... />
    <main ...>...</main>
  </div>
  <StatusBar dark={dark} meta={searchMeta} />
</div>
```

### `searchMeta` state

- [ ] **Step 1: Add `searchMeta` state to App**

Inside the `App` function, after the existing `useState` declarations (around line 626), add:

```jsx
const [searchMeta, setSearchMeta] = useState(null);
```

- [ ] **Step 2: Pass `durationMs` from SearchPanel to App**

`SearchPanel.doSearch` currently calls `onSearch({ query, drives, ext })` after the fake delay. Add `durationMs` to that call so App can record it.

Find in `SearchPanel.doSearch` (around line 189):
```js
function doSearch() {
  if (!query.trim() || drives.length === 0) return;
  setSearching(true);
  setProgress(0);
  let p = 0;
  const iv = setInterval(() => {
```

Replace with:
```js
function doSearch() {
  if (!query.trim() || drives.length === 0) return;
  setSearching(true);
  setProgress(0);
  const startTime = Date.now();
  let p = 0;
  const iv = setInterval(() => {
```

Then find the `setTimeout` inside `doSearch` (around line 199):
```js
    setTimeout(() => {
      clearInterval(iv);
      setProgress(100);
      setSearching(false);
      onSearch({ query: query.trim(), drives, ext });
    }, 1800);
```

Replace with:
```js
    setTimeout(() => {
      clearInterval(iv);
      setProgress(100);
      setSearching(false);
      onSearch({ query: query.trim(), drives, ext, durationMs: Date.now() - startTime });
    }, 1800);
```

- [ ] **Step 3: Update `handleSearch` in App to set `searchMeta`**

Find `handleSearch` in `App` (around line 637):
```js
  function handleSearch({ query, drives, ext }) {
    setLastSearch({ query, drives, ext });
    setResults(FAKE_RESULTS);
    setHistory(h => {
      const entry = { id: Date.now(), query, drives, ext, date: new Date().toISOString().slice(0,10), count: FAKE_RESULTS.length };
      return [entry, ...h].slice(0, 50);
    });
    setView("results");
  }
```

Replace with:
```js
  function handleSearch({ query, drives, ext, durationMs }) {
    const resultSet = query.trim().toLowerCase() === "zzz" ? [] : FAKE_RESULTS;
    setLastSearch({ query, drives, ext });
    setResults(resultSet);
    setSearchMeta({ count: resultSet.length, durationMs: durationMs ?? 1800, query, drives });
    setHistory(h => {
      const entry = { id: Date.now(), query, drives, ext, date: new Date().toISOString().slice(0,10), count: resultSet.length };
      return [entry, ...h].slice(0, 50);
    });
    setView("results");
  }
```

> Note: The `query === "zzz"` trigger is added here (Task 3 demo trigger). It's a one-liner — no harm doing it now.

- [ ] **Step 4: Add the `StatusBar` component**

Add this component above the `App` function (before line 617):

```jsx
// ── Status Bar ────────────────────────────────────────────────────────────────
function StatusBar({ dark, meta }) {
  const bg     = dark ? "#334155" : "#F3F4F6";
  const topBorder = dark ? "#475569" : "#E5E7EB";
  const accent = dark ? "#00E0FF" : "#8A4DFF";
  const muted  = "#64748B";

  let content;
  if (!meta) {
    content = <span style={{ color: muted }}>Ready</span>;
  } else if (meta.cancelled) {
    content = <span style={{ color: "#F87171" }}>Cancelled</span>;
  } else {
    const ms = meta.durationMs < 1000
      ? `${meta.durationMs}ms`
      : `${(meta.durationMs / 1000).toFixed(1)}s`;
    content = (
      <>
        <span style={{ color: accent }}>{meta.count} {meta.count === 1 ? "result" : "results"}</span>
        <span style={{ color: muted }}> · </span>
        <span style={{ color: muted }}>{ms}</span>
        <span style={{ color: muted }}> · </span>
        <span style={{ color: muted }}>{meta.drives.join("  ")}</span>
        <span style={{ color: muted }}> · </span>
        <span style={{ color: muted }}>"{meta.query}"</span>
      </>
    );
  }

  return (
    <div style={{
      height: 24,
      flexShrink: 0,
      background: bg,
      borderTop: `1px solid ${topBorder}`,
      display: "flex",
      alignItems: "center",
      padding: "0 14px",
      fontFamily: "Geist Mono, monospace",
      fontSize: 10,
    }}>
      {content}
    </div>
  );
}
```

- [ ] **Step 5: Wire layout change in App**

Find the `return` in `App` (line 653):
```jsx
  return (
    <div style={{ display:"flex", height:"100vh", background:bg, backgroundImage:radialBg, overflow:"hidden", transition:"background .3s" }}>
      <Sidebar
```

Replace with:
```jsx
  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100vh", background:bg, backgroundImage:radialBg, overflow:"hidden", transition:"background .3s" }}>
      <div style={{ display:"flex", flex:1, overflow:"hidden" }}>
      <Sidebar
```

Then find the closing `</main>` and the closing `</div>` of the outer div (around line 697):
```jsx
      </main>
    </div>
  );
```

Replace with:
```jsx
      </main>
      </div>
      <StatusBar dark={dark} meta={searchMeta} />
    </div>
  );
```

- [ ] **Step 6: Manual verification**

Open `Find My Files.html` in a browser.

- Before searching: status bar shows "Ready" in muted gray at the bottom of the screen
- Run a search for "report": status bar shows `12 results · 1.8s · C:\  D:\ · "report"` in the correct colors
- The rest of the app layout is unchanged — sidebar, main content, and panels all display correctly

---

## Task 2: Cancel Button

**File:** `Find My Files.html`

During an active search, the Search button transforms into a Cancel button. Clicking it stops the fake interval, resets progress, and sets `searchMeta` to `{ cancelled: true }`.

### Refactor interval to `useRef`

The current code uses `let iv` inside `doSearch`, which can't be accessed from a cancel handler defined outside the closure.

- [ ] **Step 1: Add `searchIntervalRef` to `SearchPanel`**

Find the state declarations at the top of `SearchPanel` (line 164):
```jsx
function SearchPanel({ dark, onSearch }) {
  const [query, setQuery]       = useState("");
  const [ext, setExt]           = useState("*");
  const [drives, setDrives]     = useState(["C:\\","D:\\"]);
  const [extra, setExtra]       = useState("");
  const [searching, setSearching] = useState(false);
  const [progress, setProgress] = useState(0);
```

Replace with:
```jsx
function SearchPanel({ dark, onSearch, onCancel }) {
  const [query, setQuery]       = useState("");
  const [ext, setExt]           = useState("*");
  const [drives, setDrives]     = useState(["C:\\","D:\\"]);
  const [extra, setExtra]       = useState("");
  const [searching, setSearching] = useState(false);
  const [progress, setProgress] = useState(0);
  const searchIntervalRef       = useRef(null);
```

- [ ] **Step 2: Replace `let iv` with `searchIntervalRef` in `doSearch`**

Find inside `doSearch` (lines 193–204):
```js
  let p = 0;
  const iv = setInterval(() => {
    p += Math.random() * 18 + 5;
    if (p >= 100) { p = 100; clearInterval(iv); }
    setProgress(Math.min(p, 100));
  }, 120);
  setTimeout(() => {
    clearInterval(iv);
    setProgress(100);
    setSearching(false);
    onSearch({ query: query.trim(), drives, ext, durationMs: Date.now() - startTime });
  }, 1800);
```

Replace with:
```js
  let p = 0;
  searchIntervalRef.current = setInterval(() => {
    p += Math.random() * 18 + 5;
    if (p >= 100) { p = 100; clearInterval(searchIntervalRef.current); }
    setProgress(Math.min(p, 100));
  }, 120);
  setTimeout(() => {
    clearInterval(searchIntervalRef.current);
    setProgress(100);
    setSearching(false);
    onSearch({ query: query.trim(), drives, ext, durationMs: Date.now() - startTime });
  }, 1800);
```

- [ ] **Step 3: Add `doCancel` function inside `SearchPanel`**

Add this function inside `SearchPanel`, after `doSearch` and before the `return`:

```js
  function doCancel() {
    clearInterval(searchIntervalRef.current);
    setSearching(false);
    setProgress(0);
    onCancel();
  }
```

- [ ] **Step 4: Replace the Search button with a conditional**

Find the search button block (lines 269–290):
```jsx
      {/* Search button + progress */}
      <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
        <Button
          variant="primary"
          dark={dark}
          icon={searching ? "loader" : "search"}
          disabled={!query.trim() || drives.length === 0 || searching}
          onClick={doSearch}
        >
          {searching ? "Searching…" : "Search"}
        </Button>
        {searching && (
```

Replace with:
```jsx
      {/* Search button + progress */}
      <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
        {searching ? (
          <button style={{
            padding: "10px 22px",
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            border: "2px solid rgba(239,68,68,.4)",
            background: "rgba(239,68,68,.15)",
            color: "#F87171",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 7,
            width: "100%",
            fontFamily: "inherit",
            transition: "all .2s",
          }} onClick={doCancel}>
            ✕  Cancel Search
          </button>
        ) : (
          <Button
            variant="primary"
            dark={dark}
            icon="search"
            disabled={!query.trim() || drives.length === 0}
            onClick={doSearch}
          >
            Search
          </Button>
        )}
        {searching && (
```

- [ ] **Step 5: Add `handleCancel` in App and pass `onCancel` to SearchPanel**

In `App`, add this function after `handleRerun`:

```js
  function handleCancel() {
    setSearchMeta({ cancelled: true });
  }
```

Find the `SearchPanel` usage in `App`'s return (around line 663):
```jsx
        {view === "search" && (
          <SearchPanel dark={dark} onSearch={handleSearch} />
        )}
```

Replace with:
```jsx
        {view === "search" && (
          <SearchPanel dark={dark} onSearch={handleSearch} onCancel={handleCancel} />
        )}
```

- [ ] **Step 6: Manual verification**

Open `Find My Files.html` in a browser.

- Click Search (with a query entered): the button transforms to a red "✕  Cancel Search" button; the progress bar runs beneath it
- Click Cancel: the button reverts to "Search", progress bar disappears, status bar shows "Cancelled" in red
- After cancel, the view stays on the Search panel (no navigation to Results)
- A normal search that completes still works: Search button is disabled during search, results appear, status bar shows result metadata

---

## Task 3: Zero-Results Empty State

**File:** `Find My Files.html`

When `results.length === 0` after a search completes, `ResultsTable` renders an empty state instead of the table. The demo trigger is query `"zzz"` (case-insensitive).

> The `query === "zzz"` branch in `handleSearch` was already added in Task 1, Step 3. If Task 1 is complete, no change is needed in `App`.

- [ ] **Step 1: Verify the demo trigger is in place**

In `App.handleSearch`, confirm this line exists (added in Task 1, Step 3):
```js
const resultSet = query.trim().toLowerCase() === "zzz" ? [] : FAKE_RESULTS;
```

If Task 1 was skipped, add the `"zzz"` branch to `handleSearch` now:

```js
  function handleSearch({ query, drives, ext, durationMs }) {
    const resultSet = query.trim().toLowerCase() === "zzz" ? [] : FAKE_RESULTS;
    setLastSearch({ query, drives, ext });
    setResults(resultSet);
    setSearchMeta({ count: resultSet.length, durationMs: durationMs ?? 1800, query, drives });
    setHistory(h => {
      const entry = { id: Date.now(), query, drives, ext, date: new Date().toISOString().slice(0,10), count: resultSet.length };
      return [entry, ...h].slice(0, 50);
    });
    setView("results");
  }
```

- [ ] **Step 2: Add empty state to `ResultsTable`**

`ResultsTable` renders a `<div>` as its outer wrapper (line 362). The content starts with a toolbar div. Add the conditional at the very top of the returned JSX, just inside the outer wrapper, before the toolbar:

Find the start of `ResultsTable`'s return (line 362):
```jsx
  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100%", overflow:"hidden" }}>
      {/* Toolbar */}
      <div style={{ padding:"20px 28px 14px", flexShrink:0 }}>
```

Replace with:
```jsx
  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100%", overflow:"hidden" }}>
      {results.length === 0 ? (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", flex: 1, padding: "48px 24px", textAlign: "center",
        }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14,
            background: "rgba(239,68,68,.1)",
            border: "1px solid rgba(239,68,68,.2)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 24, marginBottom: 16,
          }}>🔍</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: ink, marginBottom: 8, letterSpacing: "-0.01em" }}>
            No files found
          </div>
          <div style={{ fontSize: 13, color: subtle, maxWidth: 300, lineHeight: 1.7, marginBottom: 20 }}>
            No files matching <strong style={{ color: ink, fontFamily: "Geist Mono, monospace" }}>"{query}"</strong> were
            found on <span style={{ fontFamily: "Geist Mono, monospace" }}>{drives.join("  ")}</span>.
            Try a shorter search term or add more drives.
          </div>
          <Button variant="secondary" dark={dark} icon="arrow-left" small onClick={onNewSearch}>
            New Search
          </Button>
        </div>
      ) : (
      <>
      {/* Toolbar */}
      <div style={{ padding:"20px 28px 14px", flexShrink:0 }}>
```

Then close the ternary's `else` branch. Find the closing `</div>` of `ResultsTable`'s outer wrapper — after the `{sorted.length === 0 && ...}` block (around line 466):

```jsx
      </div>
    </div>
  );
```

Replace with:
```jsx
      </div>
      </>
      )}
    </div>
  );
```

- [ ] **Step 3: Manual verification**

Open `Find My Files.html` in a browser.

- Search for "zzz": the Results panel shows the red-tinted 🔍 icon, "No files found", a message with the query and drives in monospace, and a "← New Search" button
- Clicking "New Search" returns to the Search panel
- Status bar shows "0 results · 1.8s · C:\  D:\ · "zzz""
- Any other query (e.g. "report") still shows the full results table — the existing "no filter matches" empty state still works when filtering produces 0 visible rows from a non-empty result set

---

## Commit Sequence

Each task can be committed independently:

```bash
# After Task 1:
git add "Find My Files.html"
git commit -m "feat: add status bar showing search metadata"

# After Task 2:
git add "Find My Files.html"
git commit -m "feat: add cancel button during active search"

# After Task 3:
git add "Find My Files.html"
git commit -m "feat: add zero-results empty state with demo trigger"
```
