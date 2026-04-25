# Find My Files — UI Polish Design

**Date:** 2026-04-25
**Scope:** Three targeted additions to `Find My Files.html` (browser prototype)
**Approach:** Three separate in-place edits, one feature at a time

---

## Overview

The existing prototype covers all four panels (Search, Results, History, Settings) with dark/light mode, drive chips, sort/filter, CSV/HTML export, and search history. This spec adds three missing features that are listed as shipped in the README but absent from the prototype.

---

## Feature 1 — Status Bar

### Layout
The app's top-level layout changes from a flat flex-row (`sidebar + main`) to a flex-column:

```
┌──────────────────────────────────┐
│  sidebar │  main content          │  ← flex-row, flex: 1
├──────────────────────────────────┤
│  status bar (full width, 24px)   │  ← always visible
└──────────────────────────────────┘
```

The outer `<div style="display:flex; height:100vh; ...">` gets `flex-direction:column`. The existing sidebar+main row is wrapped in a new `<div style="display:flex; flex:1; overflow:hidden;">`.

### State: No search run
```
Ready
```
- Text: `"Ready"` in `#64748B` (muted gray)
- `searchMeta` state is `null`

### State: After search completes
```
12 results  ·  1.8s  ·  C:\  D:\  ·  "report"
```
- Result count: `#00E0FF` (cyan) in dark mode, `#8A4DFF` (brand purple) in light mode
- Separators + remaining text: `#64748B` muted
- All text: `font-family: Geist Mono, monospace`, `font-size: 10px`

### Styling
| Property | Dark | Light |
|---|---|---|
| Background | `#334155` | `#F3F4F6` |
| Top border | `1px solid #475569` | `1px solid #E5E7EB` |
| Height | `24px` | `24px` |
| Padding | `0 14px` | `0 14px` |

### State shape
Add to App state, initialized to `null`:

```ts
searchMeta:
  | { cancelled: true }
  | { count: number; durationMs: number; query: string; drives: string[] }
  | null
```

When `handleSearch` resolves: record `Date.now() - startTime`, set `searchMeta` with count/duration/query/drives.
When cancel fires: App's `handleCancel` sets `searchMeta = { cancelled: true }` (see Feature 2).

---

## Feature 2 — Cancel Button

### Behaviour
During an active search the primary Search button **transforms** into a Cancel button. No new element is added — the same button changes appearance and handler.

### Idle state (existing)
```jsx
<Button variant="primary" dark={dark} icon="search" onClick={doSearch}>
  Search
</Button>
```

### Searching state (new)
```jsx
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
  gap: 7,
  width: "100%",
  fontFamily: "inherit",
  transition: "all .2s",
}} onClick={doCancel}>
  ✕  Cancel Search
</button>
```

### Prop chain
`SearchPanel` receives a new `onCancel` prop from App:

```jsx
// App
function handleCancel() {
  setSearchMeta({ cancelled: true });
}

<SearchPanel dark={dark} onSearch={handleSearch} onCancel={handleCancel} />
```

### `doCancel` logic inside SearchPanel
```js
function doCancel() {
  clearInterval(searchIntervalRef.current);
  setSearching(false);
  setProgress(0);
  onCancel(); // notifies App to set searchMeta = { cancelled: true }
}
```

- `searchIntervalRef` — a `useRef` added to `SearchPanel` to hold the interval ID (replaces the current `let iv` local variable, which can't be accessed by a cancel handler defined outside the interval callback)
- After cancel, view stays on Search panel — no navigation
- Status bar shows `"Cancelled"` in `#F87171` (red) while `searchMeta.cancelled === true`

### Progress bar
The progress bar div remains visible during searching. It disappears when `searching` becomes false (cancelled or complete) — no change needed there.

---

## Feature 3 — Zero-Results Empty State

### Trigger condition
Distinct from the existing "no filter matches" empty state. Triggered when `results.length === 0` at the time the search completes (i.e. `handleSearch` is called with an empty result set, or a future IPC response returns zero hits).

For the prototype, `handleSearch` currently always injects `FAKE_RESULTS`. Add a demo trigger: if the query term is exactly `"zzz"` (case-insensitive), `handleSearch` passes an empty array instead of `FAKE_RESULTS`. This makes the empty state demonstrable without any UI toggle.

The `ResultsTable` component receives `results` as a prop. When `results.length === 0`, render the empty state instead of the table.

### Empty state markup
```jsx
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
  /* existing table */
)}
```

The existing "no filter matches" state (when `filtered.length === 0` but `results.length > 0`) is unchanged.

---

## Implementation Order

1. **Status bar** — layout change + new `StatusBar` component + `searchMeta` state
2. **Cancel button** — refactor `SearchPanel` to use `useRef` for interval, add `doCancel`, swap button appearance
3. **Zero-results empty state** — conditional render in `ResultsTable`

Each edit is independent. If one breaks something, the others are unaffected.

---

## Files Changed

| File | Change |
|---|---|
| `Find My Files.html` | All three edits (single file — self-contained prototype) |

No other files change.

---

## Out of Scope

- D, E, F from the gaps list (individual history delete, settings browse button, About section) — deferred
- Electron integration — this is prototype polish only
- Any changes to `Primitives.jsx` or `colors_and_type.css`
