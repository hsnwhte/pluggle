# Pluggle v0.85 - alpha

Generic, plugin-based ETL & data sync engine. Fetches from a source transforms it, and
loads it to a target — with the transform step designed to carry your own business
logic, not a fixed built-in one. Source and target types can be API, database, or file.

> **Status: Alpha.** Core pipeline (Fetch → Decode → Extract →
> Transform → Load/Export) is implemented and tested. See
> [Known Limitations](#known-limitations) before relying on this in
> production.

## Installation

```bash
pip install -e .
```

Every source/target type (file, DB, API) and every supported format (JSON, XML, CSV,
HTML, DOCX, XLSX, PDF) is included — no optional extras to remember. Only `dev` (tests,
linting) stays optional, for contributing to Pluggle itself:

```bash
pip install -e ".[dev]"
```

## Configuration

Pluggle reads optional settings from a `.env` file in the project root:

```
PLUGGLE_STORE_ADDRESS=sqlite:///data/runtime.sqlite
LOG_DIR=logs
```

A template is provided at `.env.example` — copy it to `.env` and adjust as needed:

```bash
cp .env.example .env
```

`PLUGGLE_STORE_ADDRESS` accepts any SQLAlchemy connection string — SQLite and PostgreSQL
are both verified. `LOG_DIR` may be relative to the project root or an absolute path.
Both have sensible defaults, so a `.env` file is optional; tables are created
automatically on first run.

For local PostgreSQL testing, `docker-compose.yml` is included:

```bash
docker compose up -d
```

## Usage

```bash
pluggle run \
  --source-type file --source-address ./data/input.xml \
  --target-type file --target-address ./data/output.json \
  --target-format json
```

Run `pluggle run --help` for the full list of options.

### Other commands

```bash
pluggle show --mode runs        # list past pipeline runs
pluggle show --mode registry     # list per-phase registry entries
pluggle show --mode strategies   # list installed Transform strategies
pluggle inspect --record registry --id <entry_id>   # entry metadata
pluggle inspect --record payload --id <payload_address>  # raw content
pluggle doctor                   # check env, DB connection, directories
pluggle version                  # print installed version
```

Run any command with `--help` for its full option list.

## Writing and installing a Transform strategy

Transform is the one phase with no fixed built-in implementation — it's where your own
business logic (field mapping, filtering, reshaping data to fit your target) lives. The
strategy `default` is a built-in passthrough (copies data through unchanged) and always
exists; every other strategy is installed by you.

Every Transform strategy implements `TransformStrategyProtocol`, and the class name must
start with `TransformStrategy`:

```python
from pluggle.models.dto import TransformableData, TransformedData
from pluggle.enums import ContentFormat


class TransformStrategyMyMapping:
    def __init__(self, *, target_format: ContentFormat, data: TransformableData,
                 **kwargs):
        self.target_format = target_format
        self.data = data

    def transform(self) -> TransformedData:
        # your logic here — data.content is canonical JSON (bytes)
        ...
        return TransformedData(content=...)
```

A file must contain exactly one class matching that naming pattern.

Install it:

```bash
pluggle install-strategy --path /path/to/my_strategy.py
```

Or install a reviewed strategy from the companion
[pluggle-strategies](https://github.com/hsnwhte/pluggle-strategies)
catalog by name, instead of a local path:

```bash
pluggle install-strategy --from-repo <name>
```

This copies the file into Pluggle's `installed/` strategies folder and assigns it a
unique id (printed on install). List installed strategies and their ids with
`pluggle show --mode strategies`, then reference one in a run:

```bash
pluggle run ... --transform-strategy <uid>
```

Uninstall with:

```bash
pluggle uninstall-strategy --uid <uid>
```

Or remove every installed strategy at once (asks for confirmation):

```bash
pluggle uninstall-strategy --all
```

`default` cannot be uninstalled. Don't edit the `installed/` folder by hand — use these
commands so the strategy map always matches what's actually on disk.

## Known Limitations

- **No filename/format consistency check**: nothing validates that a file's extension
  matches `--target-format` (e.g. writing JSON content to a `.xml`-named file goes
  unflagged).
- **No dependency management for installed strategies**: a Transform strategy installed
  via `install-strategy` may import third-party libraries not bundled with Pluggle. You
  are responsible for installing any such dependencies yourself — Pluggle does not
  manage them.
- **Uninstalling a strategy breaks its lineage**: registry rows from past runs keep the
  strategy's uid, but once the file is removed that uid no longer resolves to anything.
  The recorded strategy class name remains as partial context.
- **`--from-repo` doesn't deduplicate**: installing the same catalog strategy twice
  produces two separate installs with different uids, rather than recognizing it's
  already installed.

## Roadmap

See `docs/ROADMAP.md` for planned milestones.