# Mülltermine Bergheim Implementation Plan

> **For agentic workers:** Execute inline using the executing-plans skill; request an independent code review before publishing.

**Goal:** Publish an installable standalone Home Assistant app with PDF rule preview and automatic calendar renewal.

**Architecture:** Pure Python parsing/rule/export modules, persistent document/config store, scheduled public-source downloader, two HTTP surfaces (Ingress editor and read-only calendar). Browser UI uses the same evaluation endpoint as saved calendar generation.

**Tech Stack:** Python 3.12+, pdfplumber, regex (bounded execution), icalendar; standard-library HTTP server; HTML/CSS/JavaScript; Docker and Supervisor app metadata.

**Spec:** `docs/design.md`

## Global Constraints

- Repository: `up-quirk/muelltermine-bergheim`.
- Persistent configuration and source files under `/data`; no HA Core dependency in parsing modules.
- PDF parsing supports the official 2026/2027 Bergheim grids; preview never saves rules.
- Editor restricted to Ingress; externally mapped server only exposes read-only data.
- Bad downloads, wrong years, and missing next-year documents do not erase valid data.
- Existing Home Assistant configuration is migrated only after the standalone app is verified.

## Tasks

- [ ] 1. Core parsing and matching: `muelltermine/{models,parsers,rules,calendar}.py`, tests in `tests/test_core.py`. First assert exact independently known dates/counts for official 2026/2027 PDFs, combined collections and container exclusion. Run failing tests, implement, run passing tests. Check invalid regex and execution limits. ICS export must have stable UIDs and exclusive all-day end dates.
- [ ] 2. Download and persistence: `muelltermine/{sources,store,service}.py`, `tests/test_service.py`. First cover changed links, district isolation, unpublished next year, failed-download retention, config persistence and draft-preview isolation. Implement bounded HTTPS download, configurable `{year}`/`{publication_year}`/`{month}` templates and link regex; per-year atomic replacement, cache invalidation on rule changes, daily refresh.
- [ ] 3. HTTP and editor: `muelltermine/web.py`, `muelltermine/static/{index.html,app.js,style.css}`, `tests/test_web.py`. First assert preview leaves config untouched, saved rules change exports, upload size/type validation and editor/read-only separation. Build responsive German two-column editor, highlighted matches, rule feedback, PDF selection/upload, settings and status. Verify in browser against actual PDF.
- [ ] 4. Packaging: `muelltermine_bergheim/{config.yaml,Dockerfile,run.py}`, pinned requirements, repository metadata, README/DOCS, license, CI. Build and run Linux container, test Ingress-style paths and read-only feed. Inspect narrow privileges and data persistence.
- [ ] 5. Review and publication: independent reviewer inspects implementation and reported verification. Fix significant findings, commit, create public repository and push tested source, verify remote content and publish an initial version. Provide installation link and explicit test/deployment status.

## Verification cases

Literal expectations: 2026 Rest 26 / Gelb 26 / Bio 44 / Papier 13; 2027 Rest 26 / Gelb 26 / Bio 43 / Papier 13. January 2027 normal Rest is 5 and 19 January; large-container 6 January must be excluded. Combined 14 January yields Bio and Papier. PDF abbreviation `gelbe To` on 18 March 2026 is included. Parser rejects requested 2027 with a 2026 file. Preview edits affect only returned results until explicit save.
