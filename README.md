# 🔍 Find My Files

> A fast, cross-drive file search utility for Windows — built with Electron + Node.js.

[![License: MIT](https://img.shields.io/badge/License-MIT-8A4DFF.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-2EC7FF.svg)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/platform-Windows-blue.svg)]()
[![Built With](https://img.shields.io/badge/built%20with-Electron-47848F.svg)](https://www.electronjs.org/)

---

## What Is It?

**Find My Files** is a desktop application for Windows that lets you search across multiple hard drives for files and folders by name or extension. Results are displayed in a clean, readable table and can be exported as CSV or HTML reports for further use.

Powered by the [Login X](https://github.com/trickdaddy24/login-x) design system — clean SaaS in light mode, full cyberpunk neon in dark mode.

---

## Features

- 🗂 **Multi-drive search** — configure default drives once; add more at search time
- 🔎 **Search by name or extension** — wildcard support (e.g. `*.log`, `report*`)
- 📋 **Exportable results** — export to `.csv` or styled `.html` report
- 🕓 **Search history** — revisit and re-run any previous query instantly
- 📂 **Open in Explorer** — click any result to open the file or folder directly
- 🌙 **Dark / Light mode** — persists between sessions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop shell | [Electron](https://www.electronjs.org/) v28+ |
| UI framework | React 18 + Babel (inline JSX) |
| Design system | Login X (Geist Sans, brand tokens) |
| File search | Node.js `fs` + `path` (recursive walk) |
| Export | CSV string builder / HTML template |
| State persistence | `localStorage` + Electron `app.getPath('userData')` |
| Packaging | `electron-builder` (NSIS installer for Windows) |

---

## Getting Started

### Prerequisites

- **Node.js** v18 or higher
- **npm** v9 or higher
- Windows 10 / 11

### Install

```bash
git clone https://github.com/YOUR_USERNAME/find-my-files.git
cd find-my-files
npm install
```

### Run in development

```bash
npm run dev
```

### Build Windows installer

```bash
npm run build
# Output: dist/Find My Files Setup x.x.x.exe
```

---

## Project Structure

```
find-my-files/
├── main.js                  Electron main process
├── preload.js               IPC bridge (contextBridge)
├── renderer/
│   ├── index.html           App shell
│   ├── App.jsx              Root React component
│   ├── components/
│   │   ├── Sidebar.jsx      Navigation rail
│   │   ├── SearchPanel.jsx  Drive picker + search form
│   │   ├── ResultsTable.jsx Results grid + export buttons
│   │   └── HistoryPanel.jsx Past searches list
│   └── styles/
│       └── tokens.css       Login X design tokens
├── lib/
│   ├── fileSearch.js        Recursive drive walker (Node.js)
│   └── exporter.js          CSV + HTML export helpers
├── package.json
├── electron-builder.yml
├── CHANGELOG.md
└── ROADMAP.md
```

---

## IPC API

The renderer communicates with the main process via a typed IPC bridge:

| Channel | Direction | Payload | Response |
|---|---|---|---|
| `search:start` | renderer → main | `{ drives, query, extension }` | stream of `search:result` events |
| `search:result` | main → renderer | `{ path, name, size, modified, type }` | — |
| `search:done` | main → renderer | `{ total, durationMs }` | — |
| `search:cancel` | renderer → main | — | — |
| `open:path` | renderer → main | `{ path }` | opens in Explorer |
| `drives:list` | renderer → main | — | `string[]` of available drive letters |
| `settings:get` | renderer → main | — | `Settings` object |
| `settings:set` | renderer → main | `Partial<Settings>` | — |

---

## Settings Schema

Stored in `%APPDATA%/find-my-files/settings.json`:

```json
{
  "defaultDrives": ["C:\\", "D:\\"],
  "theme": "dark",
  "maxResults": 5000,
  "showHiddenFiles": false,
  "exportPath": "%USERPROFILE%\\Documents"
}
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full release notes.

### v0.1.0 — 2026-04-25 (initial release)
- Core file search by name and extension
- Multi-drive configuration (saved defaults + per-search override)
- Results table with sort and filter
- CSV + HTML export
- Search history (last 50 queries)
- Open file/folder in Windows Explorer
- Dark / Light mode toggle

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full plan.

| Version | Target | Feature |
|---|---|---|
| **v0.2** | Q3 2026 | Full-text content search (indexed) |
| **v0.2** | Q3 2026 | File size and date range filters |
| **v0.3** | Q4 2026 | Scheduled / background scans |
| **v0.3** | Q4 2026 | System tray + notifications |
| **v0.4** | Q1 2027 | Network drive (UNC path) support |
| **v0.4** | Q1 2027 | Regex search mode |
| **v1.0** | Q2 2027 | Auto-updater + signed installer |

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit with [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `chore:`
4. Open a PR against `main`

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting.

---

## License

MIT © 2026 — see [LICENSE](LICENSE) for details.
