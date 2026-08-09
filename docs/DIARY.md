### 📅 2026-07-26, Sunday (v0.1.0 → v0.2.0)

**17:00** | *[IMPORTANT REMINDER]*
In v1, `ApiFetchStrategy` hardcodes the returned data's format as
`ExtractableFormat.JSON`. In reality, the source may return JSON/XML/text/CSV depending
on its `Content-Type` header. We're not solving this now because v1's vertical slice
connects to a single, known test API (which always returns JSON).

Future work: read `response.headers.get("content-type")` and map it to the appropriate
`ExtractableFormat`. An unknown/unsupported Content-Type will likely require a new
exception (e.g. `FetchUnsupportedFormatError`).

### 📅 2026-07-27, Monday (v0.1.0 → v0.2.0)

**17:30** | *[MILESTONE]*
Completed the v0.2 vertical slice: Fetch and Decode phases working end-to-end, plus full
unit test coverage for the storage layer.

**Fetch & Decode implementation**

- Implemented `ApiFetchStrategy` (httpx) and `DBFetchStrategy` (SQLAlchemy, table
  autoload) — both static methods, normalized output to
  `ExtractableData` (bytes + format enum), keeping Extract phase blind to data origin.
- Implemented `XmlDecodeStrategy` (lxml), MVP scope: XML only. CSV/JSON/HTML stubbed
  with TODO, deferred to v0.7.

**Dependency injection cleanup**

- Removed direct instantiation of SQLite backends from `Orchestrator`
  and all `*SQLite` storage classes (`PayloadStoreSQLite`,
  `RegistryStoreSQLite`, `PipelineRunRecordsSQLite`) — these now receive a `Session` via
  constructor injection instead of creating their own. Orchestrator remains fully blind
  to which backend is in use.

**Manual end-to-end verification (devtools)**

- Built `devtools/db_managers/` (init_pipeline_db.py, init_test_dbs.py, db_tools.py) to
  bootstrap and reset local SQLite databases for testing.
- Verified all three working paths manually via `run_orchestrator.py`:
  file→XML decode, API fetch (legislation.gov.uk XML feed, mislabeled as JSON — known
  limitation, see Content-Type detection note), DB fetch (SQLite source with a
  hand-seeded test_table). All three wrote correct Registry + Payload entries with
  correct run_id/phase/strategy_name/ content_hash/address.

**Unit tests (first real pytest suite)**

- Wrote full coverage for `PipelineRunRecordsSQLite`, `RegistryStoreSQLite`
  (save_entry + all three get_entry_by_* methods), and `PayloadStoreSQLite`
  (save + load).
- Tests caught a real bug: `RegistryEntry.run_id` was defined as
  `mapped_column` (missing `()`) instead of `mapped_column(index=True)` — SQLAlchemy
  silently stored a bound method reference instead of an int, which only surfaced as a
  Pydantic ValidationError when converting to
  `RegistryRecord`.

**Process notes**

- Adopted feature-branch + PR workflow starting this session (previously committed
  directly to main). PR descriptions carry the detailed breakdown; commit messages stay
  short.
- Confirmed roadmap definition for v0.2 ("Storage layer works... Registry functional and
  tested") is now fully met.

### 📅 2026-07-28, Tuesday (v0.2.0 → v0.3.0)

**09:12** | *[MILESTONE]*
Completed v0.3: Fetch phase vertical slice, with full strategy-level unit test coverage
for both source types (API and DB).

**Fetch strategy tests**

- `DBFetchStrategy`: covered successful multi-row fetch, table-not-found, invalid
  connection URL, and missing table name. Testing surfaced a real gap —
  `NoSuchTableError` was not being caught alongside
  `OperationalError`, allowing a raw SQLAlchemy exception to leak past the strategy's
  error boundary. Fixed by catching both.
- `ApiFetchStrategy`: covered success plus all mapped HTTP status codes
  (400/401/403/404/429/5xx) using `unittest.mock` to simulate `httpx`
  responses without making real network calls.

**Testing infrastructure**

- Adopted fixture composition as the standard pattern for storage and strategy tests:
  shared setup (engine, session, mock responses) is defined once per fixture and
  requested by name where needed.
- Introduced `tmp_path` (file-backed SQLite) for `DBFetchStrategy` tests, since the
  strategy creates its own engine internally and cannot share an in-memory (`:memory:`)
  database with the test's own connection.
- Introduced `unittest.mock` (`patch`, `MagicMock`, `side_effect`) for isolating
  `ApiFetchStrategy` from real HTTP calls.

**Process**

- Continued the feature-branch + PR workflow. DBFetchStrategy and ApiFetchStrategy tests
  were committed separately to keep history readable.

**Status**
Both Fetch strategies are now implemented and verified at the unit level. Decode
strategy tests (XmlDecodeStrategy) remain for a future iteration before the Extract
phase begins.

**12:21** | *[FUTURE IDEA]*
**Configurable canonical/normalized format for Extract phase**
Currently `Extract` strategies hardcode their output to JSON (`json.dumps(...)`). A
`settings.NORMALIZED_FORMAT` constant could name this choice explicitly, but doesn't yet
decouple the actual serialization logic — every Extract strategy still calls
`json.dumps`
directly. Making the format genuinely swappable (e.g. to support a different canonical
structure) would require a serializer injection layer: something like
`settings.NORMALIZED_SERIALIZER` mapping to a callable (`json.dumps`, or an
alternative), which each Extract strategy would call instead of hardcoding `json`. Not
needed now — noting it as a deferred architectural idea, not a current requirement.

**13:07** | *[MILESTONE]*
Completed v0.4: Decode and Extract phases implemented and fully unit tested, completing
the XML vertical slice from raw source through to canonical (JSON) transform-ready data.

**Decode phase**

- `XmlDecodeStrategy` (lxml-based) tested: successful parse, and malformed XML correctly
  raising `DecodeMalformedError`.

**Extract phase**

- Clarified the architectural boundary between Extract and Transform:
  Extract performs structural, domain-agnostic conversion only (source format →
  canonical dict, no field selection or business logic). Target-format awareness and BLL
  injection are reserved for Transform, which will require an explicit
  `transform_strategy` with no default implementation.
- `XmlExtractStrategy` built on `xmltodict`, converting parsed XML into a canonical JSON
  structure (`TransformableData`). Chose to keep
  `lxml` (syntax validation in Decode) and add `xmltodict` (structural conversion in
  Extract) as separate, purpose-fit dependencies rather than forcing one library to do
  both jobs.
- Renamed `ExtractableFormat` to `ContentFormat` (now shared across
  Decode/Extract/Fetch/Transform, no longer scoped to one phase) and added
  `RegistryEntry.content_format` so Selector and Registry never need to infer format by
  inspecting payload content.
- `ExtractableData.format` renamed to `source_format`; new
  `TransformableData.origin_format` tracks what the canonical JSON was originally
  converted from.
- `XmlExtractStrategy` tested: successful conversion against a real sample file. Testing
  caught a real bug — `xmltodict.parse()` requires
  `str` input, not `bytes`; the strategy was passing raw bytes directly.

**Process**

- `settings.NORMALIZED_FORMAT` introduced as the single source of truth for Extract's
  canonical output format (currently JSON). Noted as a deferred idea: true format
  flexibility would need a serializer injection layer, not just a named constant — not
  needed yet.

**Status**
Fetch, Decode, and Extract phases are now implemented and tested. Transform and Load
remain before the full pipeline (v0.5) is complete.

**14:34** | *[FUTURE IDEA]*
**Transform strategy installer & registry system**

Currently (and for the rest of v1), Transform strategies follow the same pattern as all
other strategies: a simple `TRANSFORM_STRATEGY_MAP`
dict in `strategies/transform/__init__.py`, selected explicitly via a
`transform_strategy` argument (no auto-detection, since Transform strategies encode
business logic, not just format handling).

This works fine for a single or small number of hand-written strategies. It won't scale
once Transform strategies start being authored by third parties and "installed" into the
project, because:

- Name collisions become possible once strategies aren't all written by the same person
  in the same session
- There's no way to distinguish "built-in" (shipped with Pluggle) from
  "installed" (added later, possibly by someone else) strategies
- There's no tracking of what's actually installed, so `RegistryEntry`
  can't reliably reference *which* strategy (beyond its name string)
  produced a given payload

Deferred design sketch, to revisit in v1.x:

- A `strategy_installer.py` devtool that registers a strategy (name, source — built-in
  vs. installed, maybe file path or package origin)
  into a small catalog (a dedicated table or a structured config file)
- A `settings`/`.env` distinction between built-in and installed strategy locations
- Only becomes necessary once there's a real second author of Transform strategies — not
  needed for the v1 single-author, single-strategy case.

Deliberately not building this now — v1's priority is a complete, working pipeline (see
ROADMAP.md v0.5) over anticipatory infrastructure for a scenario that doesn't exist yet.

**19:58** | *[STATUS TRACKER]*

### Pluggle capability matrix (source_format × target_format)

Source codes: db_json, api_json, api_xml, api_csv, api_html, file_xml, file_json,
file_csv, file_html (db_xml/db_csv/db_html don't exist — DB fetch has no format choice)

Target codes: db, api_json, api_xml, api_csv, api_html, file_json, file_xml, file_csv,
file_html

| Src\Trg | db     | a_json | a_xml | a_csv | a_html | f_json | f_xml | f_csv | f_html |
|---------|--------|--------|-------|-------|--------|--------|-------|-------|--------|
| db      | [DONE] | [ ]    | [ ]   | [ ]   | [ ]    | [DONE] | LTD** | LTD** | LTD**  |
| a_json  | LTD**  | [ ]    | [ ]   | [ ]   | [ ]    | [DONE] | LTD** | LTD** | LTD**  |
| a_xml   | [DONE] | LTD**  | LTD** | LTD** | LTD**  | LTD**  | LTD** | LTD** | LTD**  |
| a_csv   | LTD**  | LTD**  | LTD** | LTD** | LTD**  | LTD**  | LTD** | LTD** | LTD**  |
| a_html  | LTD**  | LTD**  | LTD** | LTD** | LTD**  | LTD**  | LTD** | LTD** | LTD**  |
| f_xml   | [ ]    | [ ]    | [ ]   | [ ]   | [ ]    | [ ]    | [ ]   | [ ]   | [ ]    |
| f_json  | TODO*  | TODO*  | TODO* | TODO* | TODO*  | TODO*  | TODO* | TODO* | TODO*  |
| f_csv   | TODO*  | TODO*  | TODO* | TODO* | TODO*  | TODO*  | TODO* | TODO* | TODO*  |
| f_html  | TODO*  | TODO*  | TODO* | TODO* | TODO*  | TODO*  | TODO* | TODO* | TODO*  |

TODO: CsvDecodeStrategy, JsonDecodeStrategy, HtmlDecodeStrategy are stubbed, not
implemented (planned v0.7). file_json specifically needs a DecodeStrategy for JSON files
(distinct from JsonExtractStrategy, which handles already-decoded JSON content, not raw
file reading).

LTD: ApiFetchStrategy always labels source_format as JSON regardless of actual
Content-Type. Real XML/CSV/HTML API responses will fail at Extract (JsonExtractStrategy
chokes on non-JSON content) unless/until Content-Type-based detection is implemented
(see earlier diary note).

Note: db_xml / db_csv / db_html do not exist as source combinations — DBFetchStrategy
has no format selection; it always produces real JSON from table rows (not a limitation,
just a different mechanism).

**Note on Transform testing:** All LTD results above used
`SamplePassthroughTransformStrategy`, which does not perform real format conversion —
content passes through unchanged regardless of
`target_format`. This means only target_format=JSON combinations represent a true
end-to-end validation; XML/CSV/HTML targets marked OK only confirm the pipeline
*mechanism* works, not that real format conversion happens (no Transform strategy
implements that yet).

Extract side: JsonExtractStrategy and XmlExtractStrategy are implemented.
CsvExtractStrategy and HtmlExtractStrategy remain stubbed (v0.7).

### 📅 2026-07-29, Wednesday (v0.4 → v0.5)

**07:51** | *[FUTURE IDEA - for Beta version]*
**Input/output consistency checks (file extension vs. target_format)**

Currently, Pluggle does not validate that a user-provided `target_address`
file extension matches the chosen `target_format`. For example, a user can set
`target_format=JSON` while `target_address` ends in `.xml` — the file will be written
with the correct (JSON) content, but a misleading extension. This is a deliberate v1
choice (the user is expected to provide the full, correct path — no auto-inference), but
it's a real usability gap: nothing warns the user their file naming doesn't match the
actual content.

Similarly worth revisiting together: broader input/output sanity checks in general —
e.g. confirming `source_address` actually points to something reachable before running
the full pipeline, or surfacing a clear warning (not necessarily an error) when
address/format mismatches like this are detected.

Deferred to Beta: this is a UX/safety-net improvement, not a core pipeline correctness
issue — the pipeline itself works correctly regardless of the misleading filename.

**14:48** | *[MILESTONE]*
**v0.5 complete: full pipeline, Fetch through Export/Load, tested end-to-end**

**New implementations**

- `JsonExtractStrategy`, `JsonDecodeStrategy` — completed the JSON leg of the pipeline
  (validation-only, content passed through unchanged, consistent with the "Extract stays
  lossless" principle)
- `TransformStrategyProtocol` — deliberately broken from the static-method pattern used
  everywhere else: takes `__init__(target_format, data)`, parameterless `transform()`.
  Rationale: Transform carries business logic (target-format-aware conversion, injected
  by the user via
  `transform_strategy_name`), unlike Fetch/Decode/Extract/Load/Export, which are pure
  format/protocol handlers with no default implementation needed. Documented as an
  intentional protocol asymmetry.
- `SamplePassthroughTransformStrategy` — a demo strategy proving the mechanism works
  end-to-end; does not perform real format conversion. Included in
  `TRANSFORM_STRATEGY_MAP` under an explicitly named
  `sample_` key so it can never be mistaken for a production default.
- `LoadStrategyProtocol` / `ExportStrategyProtocol`, `DBLoadStrategy`,
  `ApiLoadStrategy`, `ExportStrategy` — Load is the mirror of Fetch (API/DB,
  target-aware), Export is the mirror of Decode (file-based). Export ended up
  format-independent (single strategy handles all formats, since it never interprets
  content) once `target_format`
  was scoped out of its responsibility.
- `MimeType` enum (HTTP `Content-Type` values) kept deliberately separate from
  `ContentFormat` (internal format representation) — different concerns, mapped via a
  small dict inside `ApiLoadStrategy` rather than merged

### 📅 2026-07-30, Thursday | *[MILESTONE / KNOWN LIMITATION]*

**Devtools CLI and manual test infrastructure built**
**06:55** | *[MILESTONE]*
Built out the devtools CLI (`pluggle-dev`, via `python -m devtools.main`)
mirroring the production `pluggle` CLI's `run` command, plus supporting tooling:

- `db_tools.py`: engine/session helpers, `reset_table`
- `setup-test-env` / `reset-test-env` commands to bootstrap and tear down dev
  pipeline/source/target databases
- `TestPackage` dataclass + `TEST_PACKAGES` catalog (`test_packages.py`), injectable via
  `test --test-pack <key>`, so full InputArgs combinations can be replayed with a single
  number instead of re-typing 8 CLI flags each time
- Real test data downloaded (jsonplaceholder.typicode.com/comments — 500 nested records)
  for realistic-scale manual testing

**Test 1 (file→file, comments.json→output.json) passed.**

**Test 2 (file→db, comments.json→dev_target_data_text) surfaced a known/expected
limitation:** `DBLoadStrategy` uses source JSON keys directly as target column names.
Since `SamplePassthroughTransformStrategy`
performs no field mapping, the source's field names (`postId`, `id`,
`name`, `email`, `body`) don't match the target table's schema (`id`,
`data`) — result: `IntegrityError: NOT NULL constraint failed:
dev_target_data_text.data`.

This is not a bug — it's confirmation that Transform must own field mapping/schema
adaptation, exactly as designed. A real Transform strategy (not passthrough) is required
whenever source and target schemas differ. Serves as a concrete demonstration of why
Transform carries business logic and has no default implementation.

**08:59** | *[MILESTONE]*
**All 9 source × target type combinations manually verified end-to-end**

Completed the full manual test matrix (FILE/DB/API × FILE/DB/API) via the devtools CLI's
injectable TestPackage catalog. All 9 combinations now pass.

**Real bugs found and fixed along the way:**

- `DBLoadStrategy` produced `INSERT ... DEFAULT VALUES` (and a resulting
  `IntegrityError`) when given an empty `rows` list — SQLAlchemy interprets an empty
  parameter list for `executemany` as
  "insert one row with no values" rather than "insert nothing." Fixed with an explicit
  empty check; logs a `WARNING` (not an error) since an empty source is a valid, if
  noteworthy, condition — not a failure.
- `JsonExtractStrategy` assumed all JSON sources are lists. API sources that return a
  single resource (e.g. `GET /todos/1`) return a bare JSON object instead. Since the
  internal canonical format is always
  `list[dict]`, added a wrap-into-single-element-list step for bare objects.
- Confirmed (again, via a fresh source/target combination) that
  `SamplePassthroughTransformStrategy` fails whenever source and target field names
  don't match — this is expected, not a bug, and is exactly why Transform requires real
  business logic per use case. Wrote a second devtools-only sample strategy (field
  mapping for the
  `comments` shape) to demonstrate a working non-passthrough Transform.

**Process note:** chose to reuse a compatible source (`/comments/1`
instead of `/todos/1`) rather than write a third mapping strategy for a single test
case — pragmatic reuse over unnecessary strategy proliferation.

**Status:** devtools CLI, TestPackage injection, and the full combination matrix are now
a reliable foundation for regression-testing future changes to the pipeline.

**11:09** | *[FUTURE IDEA]*
**Third-party strategy dependency management**

Installed Transform strategies may import libraries not part of Pluggle's own dependency
set (e.g. `pandas`). `install_strategy()`
copies the file but does not manage its dependencies — if the strategy's own imports
aren't already installed in the environment, loading it will fail with a standard
`ImportError`/`ModuleNotFoundError`.

Deliberate v1 choice: the strategy author is responsible for documenting and the user
for installing any extra dependencies their custom strategy needs. No `requirements.txt`
-per-strategy mechanism, no automatic pip install. Revisit only if this becomes a real
friction point once third-party strategies actually exist.

**11:50** | *[MILESTONE] (v0.5.0 → v0.6.0)*
**v0.6 complete: CLI, logging, generalized Selector, and a real Transform strategy
installer**

**CLI (`pluggle`)**

- `run` command wired to full pipeline, Typer-based, tip-annotated parameters with short
  flags
- Callback-based shared setup (`--debug` now applies to every command, not duplicated
  per-command)
- `ValidationError`/`PluggleError` caught at the CLI boundary, clean user-facing
  messages instead of raw tracebacks

**Logging**

- `logging_config.py`: console handler (INFO+) always on, file handler (DEBUG+, UTF-8)
  added when `--debug` is passed
- Orchestrator now logs phase-level progress (start/success per phase, strategy used,
  exceptions logged before re-raising)
- Deliberately stopped at Orchestrator-level logging — deeper, per-strategy logging
  remains scoped to v0.8

**Selector/Factory generalization**

- Confirmed: all six `get_*_strategy` methods already follow the same map-lookup +
  `StrategyNotFoundError` pattern. This roadmap item was effectively already satisfied
  by consistently applying the same pattern each time a new phase (Transform, Load,
  Export) was added.

**Devtools**

- `pluggle-dev` CLI mirrors `run`, plus `setup-test-env`,
  `reset-test-env`, `inspect` (pretty-prints a payload's JSON content — DB Browser shows
  raw BLOBs, this decodes them)
- `TestPackage` catalog + `--test-pack` injection: all 9 source×target combinations
  replayable by number
- Two real edge-case bugs found and fixed: empty `rows` list caused
  `DBLoadStrategy` to attempt `INSERT ... DEFAULT VALUES` (now skipped with a `WARNING`
  log); API sources returning a bare JSON object instead of a list broke the
  `list[dict]` canonical assumption (now wrapped)

**Transform strategy installer (originally scoped to v1.x, completed early)**

- Transform strategies are now referenced by **numeric id**, not name. Id `0` is the
  built-in passthrough — permanent, cannot be uninstalled.
- `pluggle install-strategy --path <file>`: validates the file (exactly one class named
  `TransformStrategy*`, and — via a newly
  `@runtime_checkable` `TransformStrategyProtocol` — an `isinstance`
  check that it actually implements the required methods), then copies it into
  `strategies/transform/installed/` under a standardized name and assigns the next
  available id.
- `pluggle uninstall-strategy --id <n>`: removes the file from disk.
  `TRANSFORM_STRATEGY_MAP` is rebuilt from the `installed/` folder on every process
  start, so there's no separate registry to keep in sync — the filesystem *is* the
  source of truth.
- `pluggle show-strategies`: lists all currently installed ids.
- Scoped out (see earlier diary note, still valid): no dependency management for what an
  installed strategy itself imports.

**Documentation**

- `README.md`: minimal Alpha-stage version — install, usage, how to write and install a
  Transform strategy, honest known-limitations list
- `LICENSE`: MIT

**Status**
v0.6 fully complete. Alpha release conditions (per original roadmap)
met: CLI, generalized Selector, functional devtools inspect tool — plus a working
plugin-style installer well ahead of its original v1.x schedule.

### 📅 2026-07-31, Friday (v0.6 -> v0.7)

**13:54** | *[RESOLVE]*
**v0.7 scope progress — new format strategies, API Content-Type detection,
Attachment/OCR dropped**

Decode + Extract implemented for CSV, HTML, DOCX, XLSX, PDF. Each Decode strategy stays
minimal (validate + carry raw bytes); each Extract strategy converts to a canonical
structure — `list[dict]` for CSV/PDF, raw `xmltodict`-parsed nested dict for XML/HTML,
and (after reconsidering `python-docx`/`openpyxl` vs. raw-XML-via-zipfile) a full
`{filename.xml: <parsed>}` dict per internal ZIP member for DOCX/XLSX. Deliberately
chose the "lossless but raw" approach over library-mediated output for DOCX/XLSX —
reasoning: Pluggle is a young engine, Transform strategies are still few, but each one
written adds a reference example that makes the next easier. The library-mediated route
would have been easier short-term but hides structure Transform might need.

`ApiFetchStrategy` now reads the actual `Content-Type` response header instead of
assuming JSON. Added `content_format_to_mime` /
`mime_to_content_format` in `helpers.py`, mapping by enum member name (both enums share
member names for shared formats) rather than a hand-maintained dict — image mime types
(PNG/JPEG) intentionally have no `ContentFormat` counterpart and raise cleanly if looked
up. Missing or unrecognized Content-Type headers raise explicitly rather than silently
defaulting to JSON — deliberate choice, may revisit if this proves too strict in
practice.

Confirmed DB-side dialect support requires no new strategy code — SQLAlchemy's dialect
abstraction already handles it, same principle established back when SQLite was first
chosen. Only verification against a real non-SQLite dialect remains open.

**Dropped: Attachment/AttachmentRef and OCR.** Both were explored in some depth (DTO/ORM
drafts for Attachment, considered as `v0.7`/`v0.75`
scope) before recognizing they're domain-specific business logic, not engine
responsibilities — a parser/sync engine doesn't need to
"understand" attachments as a first-class concept when it can already carry arbitrary
binary content through the existing pipeline. Belongs in a downstream Transform strategy
or a domain-specific framework (e.g. a future QMS layer), not Pluggle core. Good
instance of catching scope creep mid-design rather than after building it.

**Remaining before v0.7 is done:** devtools extension for new formats, Selector-side
fixes, pytest coverage for all new strategies, full manual end-to-end verification. Not
detailing further here — tracked in progress, not this entry.

### 📅 2026-08-03, Monday

**15:12** | *[FUTURE IDEA — post-v1.0]*
**pluggle-llm: a lightweight LLM API tool for Transform strategies**

Idea: a separate, small companion package (not part of Pluggle core)
that gives Transform strategy authors an easy way to call LLM APIs (OpenAI, Anthropic,
etc.) from within a strategy — e.g. summarizing, classifying, or enriching data
mid-transform.

Scope stays deliberately narrow: this is a *tool* a Transform strategy can call, not a
new pipeline capability. Fetch/Decode/Extract/Load/ Export stay untouched; Transform
still only talks to the runtime DB, nothing changes architecturally. The tool would
expose a small set of convenience methods so a Transform strategy just passes kwargs and
gets a result back, without the strategy author needing to hand-roll HTTP requests,
retries, or provider-specific request shapes.

Two motivations: (1) learning how to properly manage LLM API requests (rate limiting,
retries, provider differences) in a small, isolated scope rather than a large one; (2)
keeping it a genuinely light, optional companion — not a dependency Pluggle core ever
needs.

Not scoped into any current roadmap version — revisit after v1.0.

**17:09** | *[RESOLVE]*
**Transform strategy identity — class name isn't a reliable enough lineage record**

While manually testing v0.7, noticed `RegistryEntry.strategy_name`
stores the Transform strategy's class name. Realized this isn't a strong enough
identifier long-term: numeric strategy ids (used to select a strategy at runtime) can
shift across install/uninstall, and class names aren't guaranteed unique between
strategy authors. Neither is a stable, unique reference for lineage purposes.

Idea: assign each installed strategy a persistent unique identifier (UUID7 —
time-sortable, so ids remain roughly ordered by install time)
at install time, store it alongside the class name in the registry. Deferred to v0.75,
not urgent for v0.7's own scope.

**17:56** | *[TODO v0.8]*
**Transform failures need a generic hint, even without knowing the cause**

Manually testing a mismatched strategy (csv source, comments-shaped Transform strategy)
produced a bare `KeyError: 'id'` traceback — correct behavior, but not helpful to a user
seeing it for the first time. Pluggle can't know why a Transform strategy failed (it's
entirely user-authored), but it can wrap Transform exceptions with a generic,
non-specific hint — e.g. "Transform strategy raised an error; check that the strategy
matches the shape of the data it receives" — without pretending to diagnose the actual
cause. Add during v0.8's error handling audit.

**18:24** | *[RESOLVE]*
**DevTargetDataBlob left untested — no current strategy produces bytes**

All manual test packages so far load into `dev_target_data_text`
(TEXT column). `dev_target_data_blob` (BLOB) has never been exercised, because every
Transform strategy written so far (passthrough, and the comments-shaped mapper) produces
`str` values, not `bytes`. Not adding a test for it now — would require writing a
Transform strategy purely to exercise an untested table, not because of a real need.
Revisit if a real use case for binary output through DB Load ever comes up.

### 📅 2026-08-04, Tuesday

**06:34** | *[RESOLVE]*
**Canonical format definition corrected**

Found a stale comment (in JsonExtractStrategy) claiming the internal canonical format is
always `list[dict]`. That was only ever true for CSV/JSON/PDF. XML/HTML
(xmltodict-parsed) produce a nested dict; DOCX/ XLSX produce a dict keyed by internal
zip member filename. The correct definition: canonical format is any JSON-serializable
`list` or
`dict` — the outer shape follows the source format's own natural structure, not a fixed
list-of-records shape. Corrected the misleading comment.

**10:14** | *[MILESTONE v0.7 COMPLETE]*
**v0.7 complete: format strategies, FetchCache, RunStatus, dialect verified, 102 tests
passing**

**Format strategies** — Decode + Extract implemented and tested for CSV, HTML, DOCX,
XLSX, PDF (JSON and XML already existed, extended with consistent error handling).
Confirmed the "new strategy = new file, not new architecture" claim holds across five
new formats. Canonical Extract output redefined mid-session: not always
`list[dict]` as an earlier comment claimed, but any JSON-serializable
`list` or `dict` — the outer shape follows the source format's own structure
(CSV/JSON/PDF produce lists of records, XML/HTML produce nested dicts, DOCX/XLSX produce
a dict per internal zip member).

**API Content-Type detection** — `ApiFetchStrategy` now reads the real
`Content-Type` header instead of assuming JSON; raises explicitly if missing or
unrecognized. `helpers.py` gained
`content_format_to_mime`/`mime_to_content_format`, mapped by shared enum member names
rather than a hand-maintained dict.

**FetchCache implemented** — keyed by `api_url` (not content hash, which isn't known
before a fetch happens), scoped to API sources only. Checked before fetching, written
after a successful fetch.

**RunStatus tracking** — `PipelineRunRecord` extended with `status`
(RUNNING/COMPLETE/INTERRUPTED), `interrupted_phase`,
`interrupted_after_entry_id`. `Orchestrator.run()` wrapped in try/except, updates status
on both success and failure paths.

**OCR and Attachment support dropped** — both explored in some depth (DTO/ORM drafts for
Attachment) before recognizing they're domain-specific business logic, not engine
responsibilities. A good catch of scope creep mid-design.

**Real bugs found and fixed:**

- `RegistryStoreSQLite.get_entry_by_run_id`/`get_entry_by_hash`
  referenced a non-existent `payload_address` attribute (should be
  `address`) — would have raised AttributeError on any real call
- `.htm` extension wasn't recognized by Selector's decode map
- `HtmlDecodeStrategy`/`XmlDecodeStrategy` didn't catch `OSError`, so missing files
  raised raw lxml errors instead of
  `DecodeSourceFileNotFoundError`
- `DBLoadStrategy` empty-rows edge case (INSERT DEFAULT VALUES) — found during v0.7's
  own manual testing, fixed with an explicit empty check + WARNING log

**DB dialect support confirmed for real** — installed Docker Desktop, ran a PostgreSQL
container, verified `DBFetchStrategy` works completely unmodified against it. Closes the
one roadmap item that had been sitting on a theoretical claim ("SQLAlchemy handles
this") rather than actual verification.

**Testing:** 77 automated (pytest) + 25 manual (devtools) = 102 tests passing. New
`docs/TEST_REPORT.md` created as a standalone, externally-reviewable verification log,
separate from ROADMAP/DIARY.

**Deferred to v0.75:** Transform strategy identity (UUID7 per installed strategy), DB
rollback safety across a run, Docker Compose setup for reproducible PostgreSQL dev
environment.

**Status:** v0.7 fully complete, all consistency-review checklist items confirmed.

**10:31** | *[NOTE]*

### Capability matrix v2 (2026-08-03) — DONE / TODO only

Superseded the earlier DONE/LTD/TODO matrix. Since API Content-Type detection now works
correctly, no source/target combination is architecturally blocked anymore — everything
remaining is either untested or requires a Transform strategy that doesn't exist yet
(e.g. one producing XML/CSV/HTML instead of JSON). Both are TODO, not a hard limitation.

| Src\Trg | db    | a_json | a_xml | a_csv | a_html | f_json | f_xml | f_csv | f_html |
|---------|-------|--------|-------|-------|--------|--------|-------|-------|--------|
| db      | DONE  | DONE   | TODO* | TODO* | TODO*  | DONE   | TODO* | TODO* | TODO*  |
| a_json  | DONE  | DONE   | TODO* | TODO* | TODO*  | DONE   | TODO* | TODO* | TODO*  |
| a_xml   | DONE* | DONE   | TODO* | TODO* | TODO*  | TODO   | TODO* | TODO* | TODO*  |
| a_csv   | DONE* | DONE   | TODO* | TODO* | TODO*  | DONE   | TODO* | TODO* | TODO*  |
| a_html  | DONE* | DONE   | TODO* | TODO* | TODO*  | TODO   | TODO* | TODO* | TODO*  |
| f_xml   | DONE* | DONE   | TODO* | TODO* | TODO*  | DONE   | TODO* | TODO* | TODO*  |
| f_json  | DONE  | DONE   | TODO* | TODO* | TODO*  | DONE   | TODO* | TODO* | TODO*  |
| f_csv   | DONE* | DONE   | TODO* | TODO* | TODO*  | DONE   | TODO* | TODO* | TODO*  |
| f_html  | DONE* | DONE   | TODO* | TODO* | TODO*  | DONE   | TODO* | TODO* | TODO*  |

\* DONE means the combination was tested and its behavior was confirmed as expected.
This includes cases where the pipeline correctly failed due to a known Transform/target
schema mismatch (see Tests 11/14/17/20/23), not just cases where data successfully
reached the target. TODO means not yet tested.

\* TODO All non-JSON target format columns (a_xml, a_csv, a_html, f_xml, f_csv, f_html)
remain TODO, not because of any architectural limitation — `target_format` and
`Content-Type` header handling are already fully implemented on the Load/Export side.
What's missing is a concrete Transform strategy that actually converts canonical JSON
into XML/CSV/HTML output; every strategy written so far (passthrough, comments-mapper)
only produces JSON. Writing and validating a non-JSON-producing Transform strategy is
deferred to v0.9's real-consumer validation phase (pluggle-ncr), where a genuine use
case will drive what gets built, rather than writing one now just to close a matrix
cell.

### 📅 2026-08-05, Wednesday

**06:48** | *[RESOLVE — v0.75]*
**PostgreSQL storage backend confirmed via full manual test suite**

Added `.env`-based configuration (`PLUGGLE`, `LOG_DIR`)
to `settings.py`, replacing hardcoded storage addresses — settings now follow an
"override via environment, sensible default otherwise"
pattern throughout. Same pattern applied to `devtools/settings.py`.

Pointed `PLUGGLE_STORE_ADDRESS` at the Docker-hosted PostgreSQL container and re-ran all
31 manual test packages. All 31 produced the expected result (26 PASS/expected-FAIL
matching prior SQLite runs) — no code changes were needed to `PayloadStoreSQLite`/
`RegistryStoreSQLite`/`PipelineRunRecordsSQLite`/`FetchCacheStoreSQLite`, confirming the
SQLAlchemy Session-based implementation was already dialect-agnostic. Test 26 (the
standalone dialect_check table) was excluded after the table was manually dropped — kept
as a one-off manual verification rather than folded into `setup-test-env`, since
devtools is a personal tool and doesn't need every path automated.

**Open question surfaced but not yet resolved:** whether Pluggle should eventually take
advantage of PostgreSQL-specific features (JSONB columns, real concurrent-write support)
rather than just being dialect-portable. Concluded this is a separate, larger concern
(would require an async-capable Orchestrator to actually benefit from concurrent
writes) — not in scope for v0.75, noted for a possible future milestone.

**Status:** v0.75's "PostgreSQL storage backend added... proves storage layer is
swappable" requirement is effectively satisfied — the existing SQL-based storage classes
already work correctly against PostgreSQL without modification, no new backend-specific
class was needed as originally assumed in the roadmap wording.

**07:45** | *[RESOLVE]*

- Tested postgres_bakcend.py with 11 tests, all passing.
- Developed over the SQLite storage test suite, and runned against a Docker-hosted
  PostgreSQL instance. Confirms the storage classes are genuinely dialect-agnostic —
  same code, same tests, different engine.
- Test isolation handled via transaction-rollback fixtures (each test runs in its own
  transaction, rolled back afterwards) rather than drop/create per test, since
  PostgreSQL doesn't reset sequence counters on rollback and repeated schema teardown
  proved slow and unreliable.

**09:16** | *[REFACTORING]*
**UnitOfWork introduced; storage layer renamed and consolidated**

Refactored storage access around a `UnitOfWork` class — the classic Unit of Work
pattern: one object owns the sessions, provides the four stores, and defines transaction
boundaries (`commit()` / `rollback()`). Implemented as a context manager (`__enter__`/
`__exit__`), so sessions are always closed and an unhandled exception inside the `with`
block triggers an automatic rollback. Commit stays manual rather than automatic on clean
exit — auto-commit would break the transaction-rollback isolation the tests rely on, and
explicit commits make "when does this become permanent" visible at the call site.

Two separate sessions on purpose: pipeline work (payload/registry/ fetch-cache) is
rollback-able, while run records are not — an INTERRUPTED status must survive the
rollback that discards the run's partial writes.

Storage naming corrected alongside it. `sqlite_backend.py` and its
`...SQLite`-suffixed classes were misleading: the code contains nothing SQLite-specific
and had already been proven to work unmodified against PostgreSQL. Now `backend.py`
(single implementation) and
`backend_protocols.py` (contracts). `db_session_factory.py` deleted — its one function
moved into `UnitOfWork`. CLI and devtools updated to construct a `UnitOfWork` instead of
wiring four stores by hand; devtools passes its own engine so it stays isolated from the
app's runtime database.

Merged `test_sqlite_backend.py` and `test_postgres_backend.py` into a single
`test_backend.py`, parametrized over both engines — 11 tests × 2 backends, all passing.
Same test code, same assertions, two different database engines: the strongest evidence
so far that the storage layer is genuinely swappable. Also dropped the hardcoded `== 1`
id assertions, which were fragile since PostgreSQL doesn't reset sequence counters on
rollback.

**12:33** | *[MILESTONE - v.0.7.0 -> v0.7.5]*
**v0.75 complete: dialect-agnostic storage, UnitOfWork, rollback safety, strategy UIDs**

**Storage backend refactored.** `sqlite_backend.py` and its
`...SQLite`-suffixed classes were misleading — the code contained nothing
SQLite-specific and had already been proven to work unmodified against PostgreSQL. Now
`backend.py` (single implementation) and
`backend_protocols.py` (contracts). The roadmap originally assumed a *new* PostgreSQL
backend would be needed; the real work turned out to be proving the existing one was
already portable and correcting the naming to say so honestly.

**UnitOfWork introduced.** Owns the sessions, provides the four stores, defines
transaction boundaries. Implemented as a context manager, so sessions always close and
an unhandled exception triggers rollback. Two sessions on purpose: pipeline writes are
rollback-able, run records are not — an INTERRUPTED status must survive the rollback
that discards the run's partial writes. `db_session_factory.py` deleted, absorbed.

**Rollback safety implemented and verified.** Store methods now `flush()`
instead of `commit()`, so IDs are still assigned but the transaction stays open and
reversible. `PipelineRunRecords` keeps its commits. Verified live: a run that fails
mid-pipeline leaves `registry` and
`payloads` empty for that run, while `pipeline_runs` retains an INTERRUPTED row with the
failing phase.

**Discussed and rejected: "resume from where it left off."** Keeping partial data would
allow restarting an interrupted run from its last successful phase, but that requires
idempotency guarantees the targets (APIs, DBs) don't provide, and it would let payload
BLOBs accumulate from every failed run. Decided the surviving payload has low diagnostic
value anyway — it was a *valid* output; the missing information is whatever the failing
phase couldn't produce, which never reaches the DB regardless.

**`interrupted_after_entry_id` removed.** With rollback in place it would point at a row
that no longer exists. `interrupted_phase` alone answers the question it was meant to
answer.

**Transform strategy identity via UID.** Each installed strategy now gets a shortened
UUID4 (12 hex chars) at install time, embedded in its filename and used as its key in
`TRANSFORM_STRATEGY_MAP`. This removed the numeric-id system entirely — the original
problem was that numbers shift across install/uninstall, and UIDs make that impossible.
`uninstall` now finds the file directly by name instead of computing a list index. The
built-in passthrough keeps the reserved key `"default"`, which is also
`InputArgs.transform_strategy_uid`'s default value, so users only type a UID when they
actually want a custom strategy. Registry stores the UID *alongside* `strategy_name`,
not instead of it — the name gives readable context for every phase, the UID gives a
unique lineage reference for Transform.

**Chose UUID4 over UUID7.** UUID7 is time-sortable because its first 48 bits are a
timestamp — truncating it to 12 chars would keep *only*
the timestamp and discard all randomness, making same-millisecond collisions certain. At
12 hex chars (48 bits of randomness), UUID4 gives roughly 281 trillion values; collision
probability stays negligible well past any realistic number of strategies.

**Accepted limitation: uninstall breaks lineage.** Once a strategy file is deleted,
historical registry rows carry a UID that resolves to nothing. Accepted deliberately —
uninstall is an intentional act, and
`strategy_name` still gives partial context. A central strategy repository would solve
this properly, but only becomes relevant in a hosted/SaaS scenario.

**`postgres-playground` removed from the roadmap.** It was a personal PostgreSQL
learning goal (PL/pgSQL triggers, RPC functions, RLS policies), not a Pluggle
deliverable — a product roadmap should describe the product, not the developer's study
plan.

**Also fixed during the final test pass:** `HtmlExtractStrategy` now raises a new, more
specific `ExtractSyntaxError` for `XMLSyntaxError`/
`ParserError` instead of a blanket `except Exception` →
`ExtractMalformedError`. Its `UnicodeDecodeError` test was deleted — that path stopped
existing when the strategy moved from `xmltodict`
(which required `.decode()`) to `lxml.html` (which handles bytes and encoding detection
itself).

**Testing:** 87 pytest tests passing, including `test_backend.py`
parametrized over both SQLite and PostgreSQL (11 tests × 2 engines). All 31 manual test
packages re-verified against PostgreSQL earlier in the day.

**Status:** v0.75 complete. All three consistency-review checklist items confirmed.

### 📅 2026-08-07, Friday

**12:28** | *[MILESTONE v0.8]*
**v0.8 CLI expansion, and a real SQLite concurrency bug found and fixed**

**New CLI commands:** `show` (paginated list of runs/registry/strategies, replacing
`show-strategies`), `inspect` (registry entry metadata or raw payload content, by
`--record` kind), `version`, `doctor` (env/DB/ directory health check). All parameter
and command help text filled in last, after the commands themselves worked.

**Architecture shift: Orchestrator now owns its UnitOfWork.**
Previously CLI constructed a `UnitOfWork` and injected it into
`Orchestrator`. Changed to `Orchestrator.__init__` constructing
`self.uow = UnitOfWork()` itself — CLI now only passes `input_args`. The original reason
for injection (mockable in tests) wasn't actually exercised (Orchestrator has no unit
tests), so the tradeoff favored simplicity. `UnitOfWork()` still reads
`PLUGGLE_STORE_ADDRESS` from
`.env`, so backend selection is unaffected by this change — it was never a CLI concern
to begin with.

**`UnitOfWork` now auto-creates tables on construction**
(`create_all(checkfirst=True)`), removing a class of "table doesn't exist" errors on
first run — no separate setup step needed, matching SQLite's existing "just works" file
creation.

**The real fight: SQLite locks under two sessions.** `UnitOfWork` uses two sessions by
design (pipeline writes are rollback-able, run records aren't). Under SQLite this caused
"database is locked" — sometimes as a long hang (up to a connect timeout), sometimes as
an immediate
`OperationalError`, depending on which fix was tried. Multiple approaches attempted
before landing on the real fix:

- WAL journal mode + `busy_timeout` — didn't help; the two sessions' write windows still
  overlapped enough to hit the timeout.
- Single shared connection for both sessions — fixed the locking, but broke rollback:
  `run_records_session.commit()` and
  `pipeline_session.rollback()` turned out to affect the same underlying transaction
  when bound to one connection, so committing the run-status update also made the
  (should-be-rolled-back) pipeline writes permanent. Verified this broke the guarantee
  with a live test (test-pack 11): registry rows from the failed run persisted instead
  of disappearing.
- Separate connection + AUTOCOMMIT isolation level on
  `run_records_session` — got past the immediate lock, but
  `register_run()` itself then hung, likely colliding with
  `create_all()`'s own connection.

**Actual fix: kept two independent sessions (`bind=self.engine`, no shared connection,
no WAL/AUTOCOMMIT tricks), and removed the implicit ordering `UnitOfWork.__enter__`/
`__exit__` was hiding.** Orchestrator no longer wraps `run()` in `with self.uow:` — it
manages commit/rollback/update_record/close explicitly in
`try/except/finally`, so the sequence (commit pipeline → mark COMPLETE, or rollback
pipeline → mark INTERRUPTED) is visible in the code rather than implied by
context-manager exit order. This is what actually resolved it: the lock was never really
about SQLite's concurrency model in isolation — it was about *when* each session's
transaction closed relative to the other, and that ordering had been invisible inside
`__exit__`.

CLI/devtools entry points (`show`, `inspect`, `install-strategy`, etc.)
still use `with UnitOfWork() as uow:` — they're single-shot, one-session operations
where the implicit ordering was never the problem.

**Verified live:** test-pack 11 (expected FAIL) now correctly leaves
`registry`/`payloads` empty for the failed run *and* marks
`pipeline_runs` as INTERRUPTED with the right phase — both guarantees holding
simultaneously, on SQLite, for the first time today.

**Testing:** 87 pytest tests re-verified after the full sequence of changes, all
passing.

**Status:** v0.8 complete — error handling audit, logging decision, CI pipeline, and
(unplanned but necessary) this SQLite concurrency fix.

### 📅 2026-08-08, Saturday

**14:26** | *[RESOLVE]*
**First real Transform strategy written and working: 8D Excel mapper**

Wrote the first entry for the `pluggle-strategies` catalog — a Transform strategy that
maps a specific 8D Problem Solving Excel template (LearnLeanSigma's free template) into
structured JSON, ready for DB loading. This is also the first genuine end-to-end proof
that Pluggle works on real-world input rather than test fixtures.

**What the strategy does:** reads the raw
`{zip_member_path: parsed_xml}` dict that `XlsxExtractStrategy`
produces, pulls values from known cell coordinates on one sheet, and assembles them into
a nested Pydantic model tree (`Document` →
`DocMeta`/`Definitions`/`DocBody` → `D1`–`D7`).

**Technical obstacles solved along the way**, none of which were obvious from the
outside:

- **Shared strings indirection.** Text cells don't hold their text — they hold an
  integer index into `xl/sharedStrings.xml`. Cells carry
  `@t="s"` when this applies; without `@t`, the `v` value is the real (numeric) content.
  Excel omits `@t` for numbers rather than writing
  `@t="n"`, which cost some debugging time.
- **`xml:space="preserve"`.** Some shared-string entries parse as a plain string, others
  as `{"@xml:space": "preserve", "#text": "..."}`
  depending on whether Excel decided whitespace mattered. Needed a resolver that handles
  both shapes.
- **Excel serial dates.** Dates are stored as day counts from 1899-12-30 — not
  1900-01-01, because Excel deliberately preserves a Lotus 1-2-3 bug treating 1900 as a
  leap year. Verified the conversion by round-tripping a known date (2026-08-08 → 46242,
  matching the raw value in the file).
- **Date serialization.** Kept `date` types on the models (so Pydantic still validates
  them) and used `model_dump(mode="json")` rather than downgrading the fields to `str` —
  Pydantic handles ISO conversion at dump time.
- **Checkboxes.** The hardest part. Checkbox state lives in
  `xl/ctrlProps/ctrlPropsN.xml`, entirely outside the cell grid; a checked box gets
  `@checked="Checked"`, an unchecked one simply omits the attribute (so it's a presence
  check, not a value comparison). Mapping *which* file belongs to *which* checkbox
  required following
  `drawing1.xml` → `r:id` → `drawing1.xml.rels` → actual target path. Since this
  strategy is template-specific anyway, hardcoded the resulting mapping as a
  `CHECKBOXES` dict rather than resolving the relationship chain at runtime.

**Generic model builder.** `_build_model(model: type[M]) -> M` fills any of the Pydantic
models by iterating `model_fields` and looking each field name up in `COORDS`/
`CHECKBOXES`. Used a `TypeVar` bound to `BaseModel` so the return type tracks

### 📅 2026-08-08, Saturday

**12:26** | *[MILESTONE — v0.8.0 → v0.85.0]*
**v0.85 complete: pluggle-strategies repo, `--from-repo`, first real strategy**

**`pluggle-strategies` repo created and populated.** MIT-licensed,
`catalog.json` (machine-readable: name → file/summary/hints),
`.md` alongside each `.py` (human-readable: usage, source attribution, known
limitations). First entry: an 8D Excel mapper built against Learn Lean Sigma's free 8D
Problem Solving template — the first proof that Pluggle handles a real-world file, not
just test fixtures. Full writeup of the debugging (shared strings, Excel serial dates,
checkbox extraction via ctrlProps) is in the previous entry.

**`--from-repo` implemented.** `install-strategy` now accepts
`--from-path` or `--from-repo <name>`, mutually exclusive in intent (both given → warns
and prefers repo). Fetches `catalog.json` from
`raw.githubusercontent.com`, resolves the entry, downloads the `.py`
to a temp path, then runs through the exact same
`_load_strategy_from_file` + copy-to-`installed/` path as a local install — no
duplicated logic. Since `.md` files share the `.py`'s basename by convention, the docs
link is derived rather than stored as a separate catalog field. Success message prints
the doc URL alongside the new UID.

**`uninstall-strategy --all` added**, with a confirmation prompt before removing
everything. Lives in `transform_installer.py` as
`uninstall_all()`, reusing `uninstall_strategy()` per file rather than duplicating
removal logic — consistent with the CLI-stays-thin, installer-does-the-work split
established earlier.

**Revisited transform strategy identity, decided not to change it.**
Two open questions surfaced from using `--from-repo`:

1. Installing the same repo strategy twice produces two different UIDs (no dedup) —
   because UID assignment is random per install, not content-derived.
2. Uninstalling a strategy still discards its lineage — a UID in old registry rows
   resolves to nothing once the file is gone (documented limitation since v0.75).

Considered switching the installed filename from a random UID to a content hash (would
give dedup "for free" — same content, same filename, second install is a no-op).
Considered a database-backed
`InstalledStrategies` table so uninstalled strategies stay resolvable. Decided against
both for now: hash-as-identity conflates two different questions (lineage vs.
deduplication) that don't need one answer, and a persistence table adds a fifth store, a
new `UnitOfWork` dependency, and turns install/uninstall from filesystem-only to
DB-and-filesystem — real cost for a single-user, pre-Beta project with no reported need.
Filesystem stays the sole source of truth. Revisit if Beta feedback actually surfaces
this as a problem, not before.

**Collapsed optional dependency groups into core dependencies**
Discovered while wiring up `httpx` for `--from-repo` that it needed to move from the
`api` optional group to core — installing a strategy from the catalog is a base CLI
feature, not something gated behind an extra. That prompted a wider look: `docx`/`xlsx`
groups depend on
`xmltodict` (their Extract strategies parse the internal zip's XML members) but that
dependency lived in the separate `xml` group, undeclared as a sub-dependency —
installing `pluggle[docx]` alone wouldn't have pulled in what DOCX Extract actually
needs.

Rather than start declaring inter-group dependencies, checked the actual cost of just
merging everything: roughly 20-25MB total (lxml is the heaviest single piece, being a
compiled C library). At current bandwidth that's a few seconds, not a real UX cost.
Moved
`httpx`, `psycopg2-binary`, `lxml`, `xmltodict`, `python-docx`,
`openpyxl`, `pypdf` all into core `dependencies`. Only `dev` stays optional now (pytest,
ruff — nothing an end user needs).

Net effect: `pip install pluggle` now gives every format/source supported out of the
box, matching the "batteries included" instinct that already drove making tables
auto-create and `.env` optional. The isolated-install verification from v0.8 (fresh
venv, missing
`httpx` → clear `ModuleNotFoundError`) is no longer the relevant test — there's no
meaningful "isolated" install to verify anymore, by design.

**Status:** v0.85 complete.


