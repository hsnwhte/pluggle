v0.1 -- [DONE] Project scaffolding complete. src layout, pyproject.toml, .gitignore,
docs/ set up. Core Pydantic DTOs and exception hierarchy defined. No working logic yet.

v0.2 -- [DONE] Storage layer works. StorageBackend Protocol defined, SQLiteStorage
reference implementation complete. Registry (hash-based lineage tracking) functional and
tested.

v0.3 -- [DONE] First vertical slice, fetch side: API source strategy implemented.
Fetcher processor calls it, writes to phase-1 storage via registry. Unit tests pass.

v0.4 -- [DONE] First vertical slice, decode/extract side: XML decode + extract strategy
implemented. Data reaches phase-2 storage in canonical format. Unit tests pass.

v0.5 -- [DONE] First vertical slice, transform + load side: Transformer + Database
(SQLAlchemy-based) load strategy implemented. End-to-end pipeline runs: API source -> DB
target, fully working, fully tested.

v0.6 -- [DONE] ALPHA release: CLI interface complete (interfaces/cli). Selector/Factory
mechanism generalized (not hardcoded to the v0.5 path). Devtools inspect tool
functional.

v0.7 -- [DONE] Extended content format strategies: CSV, HTML, DOCX, XLSX, and PDF
sources added (Decode + Extract), proving the
"new strategy = new file, not new architecture" claim. API Content-Type detection
implemented (ApiFetchStrategy now reads the real Content-Type header instead of assuming
JSON; raises explicitly if the header is missing/unrecognized). DB-side dialect support
confirmed via SQLAlchemy's own abstraction — no new strategy code required, only
verification against a non-SQLite dialect. Test coverage extended for each new format.
Manual end-to-end verification via devtools. PipelineRunRecord is extended to include
status.

FetchCache implemented: Fetch strategies check FetchCache by api_url before hitting the
source, and write to fetch_cache table in Runtime Database after a successful fetch.

OCR and Attachment support considered and deliberately dropped:
both are domain-specific business logic (image-to-text, file-reference tracking), not
engine-level concerns. Belongs in downstream Transform strategies or domain frameworks
(e.g. a QMS layer), not in Pluggle core. See DIARY.md.

Consistency review, concrete checklist:
[x] Every new strategy file (CSV/HTML/DOCX/XLSX/PDF Decode and Extract) follows the same
internal structure as the reference strategy
[x] RunStatus is never left at RUNNING after a completed process, including
unexpected/non-PluggleError exceptions
[x] FetchCache is only written to and read from for API sources, never DB or FILE
[x] TEST_REPORT.md entries exist for every new format combination added this milestone

v0.75 -- [DONE] Storage backend refactored to dialect-agnostic single version:
Proves storage layer is swappable, not just extensible on the strategy side. DB rollback
safety across a run added. Transform strategy identity: assign a shortened unique id
(UUID4) to each installed strategy at install time, stored in the registry alongside
strategy_name. Numeric strategy ids can shift across install/uninstall and class names
aren't guaranteed unique — neither is a reliable lineage record on its own.

Consistency review, concrete checklist:
[x] PostgreSQL backend passes the same test suite as SQLite, unmodified (proves the
Protocol abstraction actually holds)
[x] A run interrupted mid-phase leaves no orphaned/partial rows once rollback safety is
in place
[x] Every RegistryEntry produced by an installed Transform strategy carries a resolvable
strategy UUID

v0.8 -- [DONE] CI pipeline set up (scope to be defined at implementation time — likely
GitHub Actions, running the test suite on push at minimum). Error handling audited
across the codebase (no bare Exception/ValueError anywhere; every failure mode maps to a
specific, meaningful exception). Logging finalized across all processors and strategies,
not just the Orchestrator.

Consistency review, concrete checklist:
[x] CI runs the full test suite on every push and blocks merge on failure
[x] grep for "raise Exception" / "raise ValueError" across src/pluggle returns nothing
[x] Every processor and strategy logs at least start/success/ failure at a consistent
level
[x] Optional dependency groups (api, xml, docx, xlsx, pdf)
verified to fail with a clear, actionable error when a feature is used without its group
installed — not a raw ImportError

v0.85 [DONE] -- pluggle-strategies: a separate, curated repo of vetted Transform
strategies (manually reviewed before being added, not an open marketplace).
`pluggle install-strategy --from-repo <name>` fetches and installs directly, in addition
to the existing local-file install path. Transform strategy identity revisited if
repo-sourced strategies raise new lineage questions. (Scope likely to grow as the repo
takes shape.)

v0.9 [DONE]-- BETA release: README complete (setup, summary, rationale) complete.
Published to PyPI (pip install pluggle becomes real).

Real-consumer validation: pluggle-ncr's first TransformStrategy (Excel source)
implemented and run end-to-end against Pluggle as an external dependency (pip install,
not copy-pasted code). Any friction/gaps found this way get fixed in Pluggle core, not
worked around in pluggle-strategies.

Consistency review, concrete checklist:
[x] Public API surface documented (Protocols, UnitOfWork, Selector, Orchestrator, CLI
commands) — private/self-explanatory methods skipped by design
[x] Every raised exception uses the custom hierarchy (grep for bare "raise Exception" /
"raise ValueError" returns nothing)

v0.10 [DONE] -- Breaking change. Strategy identity switched from a generated uid to
name + version declared by the strategy itself in a `StrategyMeta` class attribute.
Previously installed strategies and existing registry rows are not compatible:
strategies must be reinstalled and the runtime store reset. Versions of the same
strategy can coexist; a bare name resolves to the highest. Programmatic API added
(`pluggle/interfaces/api.py`) for other applications to call in-process, alongside the
CLI. `transform_installer` renamed to
`strategy_manager` and its install function split into `install_from_path` /
`install_from_repo`, plus `install_all_from_repo` (exposed as
`install-strategy --all`). Devtools runtime store override fixed — it sat below the
pluggle imports and never took effect, so test runs wrote to a stale SQLite file while
`setup-test-env` prepared PostgreSQL.

v0.11 [DONE] -- Installed strategies moved out of the package directory. Location is now
configurable via `PLUGGLE_STRATEGIES_DIR`, defaulting to `data/strategies`, so
strategies survive a virtualenv rebuild and don't depend on site-packages being
writable.

v1.0 -- Full release: portfolio-ready. Documented, tested, demonstrably extensible.
Public-facing polish complete.