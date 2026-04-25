# Roadmap

This document outlines the planned development trajectory for **Find My Files**.

Priorities can shift based on user feedback. Open an issue to suggest features or vote on existing ones.

---

## v0.2 — Search Power-Ups *(Target: Q3 2026)*

- [ ] **Full-text content search** — search inside file contents (plain text, PDF, DOCX)
- [ ] **File size filter** — min/max size range picker
- [ ] **Date range filter** — filter by created or modified date
- [ ] **Exclude patterns** — skip folders like `node_modules`, `Windows`, `.git`
- [ ] **Multiple query terms** — AND / OR logic across name patterns

---

## v0.3 — Background & Automation *(Target: Q4 2026)*

- [ ] **Scheduled scans** — run a saved search on a timer; results notify via system tray
- [ ] **System tray integration** — minimize to tray, quick-search from tray icon
- [ ] **Save search profiles** — named presets (e.g. "Nightly log sweep")
- [ ] **Result diffing** — compare two runs of the same search, highlight changes

---

## v0.4 — Network & Advanced *(Target: Q1 2027)*

- [ ] **Network / UNC path support** — search mapped drives and `\\server\share` paths
- [ ] **Regex search mode** — power-user pattern matching
- [ ] **Bulk copy / move** — act on selected results from inside the app
- [ ] **Custom export templates** — user-defined HTML report layout

---

## v1.0 — Production Ready *(Target: Q2 2027)*

- [ ] **Auto-updater** — in-app update check and install via `electron-updater`
- [ ] **Code-signed installer** — Windows Authenticode signature
- [ ] **Telemetry opt-in** — anonymous crash + usage reporting
- [ ] **Accessibility audit** — keyboard navigation, high-contrast mode, screen reader support
- [ ] **Localization scaffold** — i18n support (English + Spanish at launch)

---

## Backlog / Under Consideration

- macOS + Linux builds
- Plugin system for custom result actions
- Integration with Windows Search index (faster but limited scope)
- Cloud drive support (OneDrive, Google Drive)

---

*Last updated: 2026-04-25*
