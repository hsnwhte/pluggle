# Pluggle — Manual & Automated Test Report

This report tracks manual end-to-end verification (via devtools) and automated test
suite results for each Pluggle release. It exists alongside `docs/ROADMAP.md` (what's
planned) and `docs/DIARY.md`
(development narrative) as a focused, at-a-glance record of what has actually been
verified to work — intended for anyone evaluating the project from the outside.

Each entry below documents a single manual test run: what was tested, with what input,
what the result was, and what that confirms. Automated (pytest) results are summarized
separately at the end of each version section.

---

## v0.7

### Automated (pytest)

**Summary (as of 2026-08-04):**

- Total: 77 tests passing
- Coverage by category: storage (11), fetch (7), decode (27), extract (19), transform
  (1), load (11), export (1)

#### Test run 1

- Total tests: 77
- Failed: 4
- Passed: 73
- Warnings: 0
- Pluggle App Bugs: 0
- Test Design Shortcomings: 2
    1. `html_decode_strategy.py` / `xml_decode_stratgy.py`: neither catches `OSError`(`FileNotFoundError does not catch the error 
      raised by dependency`), so a missing file raises a raw `lxml`
       `OSError` instead of `DecodeSourceFileNotFoundError`.
    2. `test_decode_malformed` for CSV and HTML: the "malformed" sample files aren't
       actually malformed enough — `csv.Sniffer()` and
       `lxml.html.parse()` are too tolerant to reject them, so no exception is raised.
       Test expectation doesn't match real strategy behavior; needs a
       genuinely-malformed sample or a mocked failure instead.

#### Test run 2

- Total tests: 77
- Failed: 0
- Passed: 77
- Warnings: 0
- Pluggle App Bugs: 0
- Test Design Shortcomings: FIXED

### Manual verification

**Summary (as of 2026-08-04):**

- Total manual test packages run: 31
- Valid results: 31 (26 passed as expected, 5 failed as expected)
- Pluggle App Bugs: 6
  `.htm` extension, OSError handling in HTML/XML Decode, empty-rows DB insert,
  bare-JSON-object wrapping, `+xml` mime type variants, HtmlExtractStrategy's
  xmltodict→lxml.html rewrite for real-world HTML tolerance.
- Note: `DevTargetDataBlob` (binary DB target) not yet exercised — no current Transform
  strategy produces bytes output.

#### Test 1 — file (json)→file (json)

- **Input:** `comments.json` (500 records, jsonplaceholder sample)
- **Command:** `python -m devtools.main test --test-pack 1`
- **Verifies:** Decode (JSON)→Extract (JSON)→Transform (installed strategy)→Export
- **Result:** PASS — output file matches expected structure

#### Test 2 — file (json)→db

- **Input:** `comments.json`
- **Command:** `python -m devtools.main test --test-pack 2`
- **Verifies:** Decode (JSON)→Extract (JSON)→Transform (installed strategy)→Load (DB)
- **Result:** PASS

#### Test 3 — file (json)→api

- **Input:** `comments.json`
- **Command:** `python -m devtools.main test --test-pack 3`
- **Verifies:** Decode (JSON)→Extract (JSON)→Transform (installed strategy)→Load (API)
- **Result:** PASS

#### Test 4 — db→file (json)

- **Input:** dev source DB table (`dev_source_data_text`)
- **Command:** `python -m devtools.main test --test-pack 4`
- **Verifies:** Fetch (DB)→Extract (JSON)→Transform (passthrough)→Export
- **Result:** PASS

#### Test 5 — db→db

- **Input:** dev source DB table (`dev_source_data_text`)
- **Command:** `python -m devtools.main test --test-pack 5`
- **Verifies:** Fetch (DB)→Extract (JSON)→Transform (passthrough)→Load (DB)
- **Result:** PASS

#### Test 6 — db→api

- **Input:** dev source DB table (`dev_source_data_text`)
- **Command:** `python -m devtools.main test --test-pack 6`
- **Verifies:** Fetch (DB)→Extract (JSON)→Transform (passthrough)→Load (API)
- **Result:** PASS

#### Test 7 — api→file (json)

- **Input:** dev source API endpoint
- **Command:** `python -m devtools.main test --test-pack 7`
- **Verifies:** Fetch (API, Content-Type detection)→Extract (JSON)→Transform
  (passthrough)→Export
- **Result:** PASS

#### Test 8 — api→db

- **Input:** dev source API endpoint
- **Command:** `python -m devtools.main test --test-pack 8`
- **Verifies:** Fetch (API)→FetchCache write→Extract (JSON)→Transform (installed
  strategy)→Load (DB)
- **Result:** PASS

#### Test 9 — api→api

- **Input:** dev source API endpoint
- **Command:** `python -m devtools.main test --test-pack 9`
- **Verifies:** Fetch (API)→FetchCache write→Extract (JSON)→Transform (passthrough)→Load
  (API)
- **Result:** PASS

#### Test 10 — file (csv)→file (json)

- **Input:** `cities.csv`
- **Command:** `python -m devtools.main test --test-pack 10`
- **Verifies:** Decode (CSV, validation + raw bytes)→Extract (CSV→list[dict])→Transform
  (passthrough)→Export
- **Result:** PASS
-

#### Test 11 — file (csv)→db

- **Input:** `cities.csv`
- **Command:** `python -m devtools.main test --test-pack 11`
- **Verifies:** Decode (CSV)→Extract (CSV→list[dict])→Transform (strategy id=1,
  comments-shaped)→Load (DB)
- **Result:** FAIL (expected) — `KeyError: 'id'`. Strategy id=1 expects comment-shaped
  fields (`id`, `name`, `email`, `body`), but `cities.csv`
  has a different schema. Confirms Transform must match the source shape it's given —
  not a bug, expected behavior given a mismatched strategy. A CSV-appropriate strategy
  needs to be written and installed before retrying.

#### Test 12 — file (csv)→api

- **Input:** `cities.csv`
- **Command:** `python -m devtools.main test --test-pack 12`
- **Verifies:** Decode (CSV)→Extract (CSV→list[dict])→Transform (passthrough)→Load (API)
- **Result:** PASS

#### Test 13 — file (html)→file (json)

- **Input:** `The_World_Wide_Web_project.htm`
- **Command:** `python -m devtools.main test --test-pack 13`
- **Verifies:** Decode (HTML)→Extract (HTML)→Transform (passthrough)→Export
- **Result:** FAIL (expected) — file extension is `.htm`, not `.html`. Selector's decode
  strategy lookup keys on file suffix and doesn't recognize `.htm` as an alias for
  `.html`. Confirms Selector's extension-based dispatch is strict/literal, not fuzzy — a
  real gap worth deciding on (support `.htm` as an alias, or leave it and require users
  to rename).
-
    - **Result:** PASS (after two fixes)
- **Bugs found and fixed along the way:**
    1. `.htm` extension wasn't recognized by Selector's DECODE_STRATEGY_MAP (only
       `.html` was registered) — added `"htm"` as an alias.
    2. `HtmlDecodeStrategy` only caught `etree.ParseError`, but `lxml`
       raises `OSError` for unreadable/malformed file access — widened the except clause
       to catch both.

#### Test 14 — file (html)→db

- **Input:** `The World Wide Web project.htm`
- **Command:** `python -m devtools.main test --test-pack 14`
- **Verifies:** Decode (HTML)→Extract (HTML)→Transform (strategy id=1, comments-shaped)
  →Load (DB)
- **Result:** FAIL (expected) — strategy id=1 doesn't match HTML's extracted shape
  (comments-specific field mapping). Confirms the same
  "Transform must match source shape" behavior seen in Test 11. No fix needed — an
  HTML-appropriate strategy would need to be written.

#### Test 15 — file (html)→api

- **Input:** `The World Wide Web project.htm`
- **Command:** `python -m devtools.main test --test-pack 15`
- **Verifies:** Decode (HTML)→Extract (HTML)→Transform (passthrough)→Load (API)
- **Result:** PASS

#### Test 16 — file (xml)→file (json)

- **Input:** `cd_catalog.xml`
- **Command:** `python -m devtools.main test --test-pack 16`
- **Verifies:** Decode (XML)→Extract (XML via xmltodict)→Transform (passthrough)→Export
- **Result:** PASS

#### Test 17 — file (xml)→db

- **Input:** `cd_catalog.xml`
- **Command:** `python -m devtools.main test --test-pack 17`
- **Verifies:** Decode (XML)→Extract (XML)→Transform (strategy id=1, comments-shaped)
  →Load (DB)
- **Result:** FAIL (expected) — strategy id=1 doesn't match XML's extracted shape. Same
  expected behavior as Tests 11 and 14.

#### Test 18 — file (xml)→api

- **Input:** `cd_catalog.xml`
- **Command:** `python -m devtools.main test --test-pack 18`
- **Verifies:** Decode (XML)→Extract (XML)→Transform (passthrough)→Load (API)
- **Result:** PASS

#### Test 19 — file (docx)→file (json)

- **Input:** `sample-files.com-basic-text.docx`
- **Command:** `python -m devtools.main test --test-pack 19`
- **Verifies:** Decode (DOCX, raw bytes)→Extract (DOCX, per-XML-member zip dict via
  xmltodict)→Transform (passthrough)→Export
- **Result:** PASS

#### Test 20 — file (docx)→db

- **Input:** `sample-files.com-basic-text.docx`
- **Command:** `python -m devtools.main test --test-pack 20`
- **Verifies:** Decode (DOCX)→Extract (DOCX)→Transform (passthrough)→Load (DB)
- **Result:** FAIL (expected) — DOCX's raw per-file-XML shape doesn't match
  `dev_target_data_text`'s schema. Same "Transform must match target shape" behavior as
  prior DB-target tests. No fix needed.

#### Test 21 — file (docx)→api

- **Input:** `sample-files.com-basic-text.docx`
- **Command:** `python -m devtools.main test --test-pack 21`
- **Verifies:** Decode (DOCX)→Extract (DOCX)→Transform (passthrough)→Load (API)
- **Result:** PASS

#### Test 22 — file (xlsx)→file (json)

- **Input:** `Free_Test_Data_100KB_XLSX.xlsx`
- **Command:** `python -m devtools.main test --test-pack 22`
- **Verifies:** Decode (XLSX, raw bytes)→Extract (XLSX, per-XML-member zip dict)
  →Transform (passthrough)→Export
- **Result:** PASS

#### Test 23 — file (xlsx)→db

- **Input:** `Free_Test_Data_100KB_XLSX.xlsx`
- **Command:** `python -m devtools.main test --test-pack 23`
- **Verifies:** Decode (XLSX)→Extract (XLSX)→Transform (passthrough)→Load (DB)
- **Result:** FAIL (expected) — same schema mismatch pattern as Test 20.

#### Test 24 — file (xlsx)→api

- **Input:** `Free_Test_Data_100KB_XLSX.xlsx`
- **Command:** `python -m devtools.main test --test-pack 24`
- **Verifies:** Decode (XLSX)→Extract (XLSX)→Transform (passthrough)→Load (API)
- **Result:** PASS

#### Test 25 — api (csv)→file (json)

- **Input:** Federal Register API, `.csv` format
  (`https://www.federalregister.gov/api/v1/documents.csv?per_page=5`)
- **Command:** `python -m devtools.main test --test-pack 25`
- **Verifies:** ApiFetchStrategy's Content-Type detection correctly identifies a
  genuinely CSV-returning API source (not just JSON) → Decode/Extract (CSV)→Transform
  (passthrough)→Export
- **Result:** PASS

#### Test 26 — db (postgresql)→file (json)

- **Input:** Docker-hosted PostgreSQL container, `dialect_check` table
- **Command:** `python -m devtools.main test --test-pack 26`
- **Verifies:** Full pipeline (Fetch→Extract→Transform→Export) against a non-SQLite
  dialect, replacing the standalone
  `postgres_dialect_check.py` script with a proper TestPackage entry
- **Result:** PASS

#### Test 27 — api (csv)→api (json)

- **Input:** Federal Register API, `.csv` format
- **Command:** `python -m devtools.main test --test-pack 27`
- **Verifies:** CSV-returning API source → API target (json), closing the a_csv × a_json
  matrix gap
- **Result:** PASS

#### Test 28 — api (xml/rss)→api (json)

- **Input:** NASA RSS feed (`https://www.nasa.gov/feed/`)
- **Command:** `python -m devtools.main test --test-pack 28`
- **Verifies:** Content-Type detection for XML variants
- **Result:** Initially FAILED — `Content-Type: application/rss+xml`
  wasn't recognized (MimeType only had bare `application/xml`). Fixed by normalizing any
  `+xml`-suffixed mime type to `application/xml`
  before lookup, rather than adding every XML variant as a separate MimeType member.
  Currently investigating a second failure at the Extract phase (xmltodict parsing the
  RSS content) — see next entry once resolved.
-

#### Test 29 — api (html)→api (json)

- **Input:** `https://www.example.org/` (IANA example domain)
- **Command:** `python -m devtools.main test --test-pack 29`
- **Verifies:** HTML-returning API source → API target (json), closing the a_html ×
  a_json matrix gap
- **Result:** PASS (after a fix) — `info.cern.ch` (original candidate)
  failed to connect (likely outdated TLS on that historic server), switched to
  `example.org`. That surfaced a real limitation:
  `HtmlExtractStrategy` used `xmltodict`, which rejects standard, valid HTML with
  unclosed tags (`<meta>`, `<br>`) because it expects strict XML. Rewrote
  `HtmlExtractStrategy` to use `lxml.html` with a small recursive element-to-dict helper
  instead — genuinely tolerant of real-world HTML, not just XML-shaped HTML. Noted for a
  full strategy consistency pass in v0.9 (this strategy now deviates slightly from the
  shared static-method pattern with a module-level helper function).

#### Test 30 — api (xml/rss)→file (json)

- **Input:** NASA RSS feed (`https://www.nasa.gov/feed/`)
- **Command:** `python -m devtools.main test --test-pack 30`
- **Verifies:** a_xml × f_json matrix gap
- **Result:** PASS

#### Test 31 — api (html)→file (json)

- **Input:** `https://www.example.org/`
- **Command:** `python -m devtools.main test --test-pack 31`
- **Verifies:** a_html × f_json matrix gap
- **Result:** PASS

## v0.75

### Automated (pytest)

- Total: 87 tests passing
- `tests/storage/test_backend.py` — parametrized over both engines (11 tests × 2
  backends: SQLite and PostgreSQL), replacing the previously separate SQLite and
  PostgreSQL test files
- Coverage by category: storage (22 — 11 tests × 2 engines), fetch (7), decode (27),
  extract (18), transform (1), load (11), export (1)
- Test isolation for PostgreSQL uses transaction-rollback fixtures (each test in its own
  transaction, rolled back after) rather than drop/create per test — PostgreSQL doesn't
  reset sequence counters on rollback, and repeated schema teardown proved slow and
  unreliable

### Manual verification

**Summary (as of 2026-08-03):** All 31 manual test packages re-run against a PostgreSQL
backend (`PLUGGLE_STORE_ADDRESS` pointed at a Docker-hosted PostgreSQL container instead
of SQLite). All produced the expected result — identical outcomes to the SQLite runs,
with no code changes to any storage class. Test 26 excluded (its
`dialect_check` table was manually dropped and isn't part of
`setup-test-env`; kept as a one-off verification rather than an automated fixture).

This confirms the storage layer is genuinely swappable: switching backends is a
configuration change, not a code change.

## v0.12.0

### Automated (pytest)

- Total: 112 tests passing (up from 87)
- New: `tests/test_strategy_manager.py` — 20 tests covering strategy installation, the
  module that carried the v0.10 identity refactor without any test coverage. Installs
  are redirected to a temp directory by monkeypatching the module-level
  `INSTALLED_STRATEGIES_DIR`; `httpx.get` is faked. Nothing touches the real strategies
  directory or the network.
    - `_load_strategy_from_file`: valid load, plus each failure branch (missing file,
      syntax error, no matching class, multiple matching classes, missing `meta`)
    - `install_from_path`: name derivation, duplicate rejection, side-by-side versions
    - `get_repo_catalog` / `_fetch_strategy_from_repo`: success, missing entry, network
      failure, doc URL derivation
    - `install_from_repo`, `install_all_in_repo`: counts, skipping already-installed,
      empty catalog
    - `uninstall_strategy`, `uninstall_all`: success and not-found paths
- New: target extension validation tests in the `InputArgs` suite — matching extension,
  mismatch, missing extension, and non-file targets where the check must not fire
- Two bugs surfaced by these tests: the protocol check accepted strategies missing
  `meta` (`and` where `or` was needed), and
  `install_all_in_repo` discarded the list of installed names it had built