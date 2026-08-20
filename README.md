<img src="https://raw.githubusercontent.com/hsnwhte/pluggle/main/assets/banner.svg" width="150" alt="Pluggle">

# Pluggle v0.12.0 - beta

Generic, plugin-based ETL & data sync engine. Fetches from a source transforms it, and
loads it to a target — with the transform step designed to carry your own business
logic, not a fixed built-in one. Source and target types can be API, database, or file.

> **Status: Beta.** Core pipeline (Fetch → Decode → Extract →
> Transform → Load/Export) is implemented and tested. See
> [Known Limitations](#6-known-limitations) before relying on this in
> production.

## 1. Installation

```bash
pip install pluggle
```

Every source/target type (file, DB, API) and every supported format (JSON, XML, CSV,
HTML, DOCX, XLSX, PDF) is included — no optional extras to remember.

For contributing to Pluggle itself (running the test suite, linting):

```bash
git clone https://github.com/hsnwhte/pluggle.git
cd pluggle
pip install -e ".[dev]"
```

## 2. Configuration

Pluggle reads optional settings from a `.env` file in the project root:

```
PLUGGLE_STORE_ADDRESS=sqlite:///data/runtime.sqlite
PLUGGLE_STRATEGIES_DIR=data/strategies
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

`PLUGGLE_STRATEGIES_DIR` sets where installed strategies are stored — relative to the
project root or an absolute path. Keep it on persistent storage when deploying, so
strategies survive a rebuild.

For local PostgreSQL testing, `docker-compose.yml` is included:

```bash
docker compose up -d
```

## 3. Usage

```bash
pluggle run \
  --source-type file --source-address ./data/input.xml \
  --target-type file --target-address ./data/output.json \
  --target-format json
```

Run `pluggle run --help` for the full list of options.

### 3.1 Other commands

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

## 4. Writing and installing a Transform strategy

Transform is the one phase with no fixed built-in implementation — it's where your own
business logic (field mapping, filtering, reshaping data to fit your target) lives. The
strategy `default` is a built-in passthrough (copies data through unchanged) and always
exists; every other strategy is installed by you.

Every Transform strategy implements `TransformStrategyProtocol`: the class name must
start with `TransformStrategy`, and it must declare a `meta` attribute holding its
identity.

```python
from pluggle.models.dto import StrategyMeta, TransformableData, TransformedData
from pluggle.enums import ContentFormat


class TransformStrategyMyMapping:
    meta = StrategyMeta(name="my-mapping", version="v1.0")

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

`meta.name` must be lowercase, using digits and single hyphens between segments
(`my-mapping`, not `My_Mapping`). `meta.version` must be `vX.Y`. Invalid values are
rejected rather than corrected — the identity you declare is the identity you get. Name
and version together identify a strategy: two versions of the same strategy can be
installed side by side, but installing the same name *and* version twice is refused.

Install it:

```bash
pluggle install-strategy --from-path /path/to/my_strategy.py
```

Or install a reviewed strategy from the companion
[pluggle-strategies](https://github.com/hsnwhte/pluggle-strategies)
catalog by name, instead of a local path:

```bash
pluggle install-strategy --from-repo <name>_<version>
```

Or install everything the catalog offers, skipping what's already present:

```bash
pluggle install-strategy --all
```

Installing copies the file into Pluggle's strategies directory as `<name>_<version>.py`.
List what's installed with `pluggle show --mode strategies`, then reference one in a
run:

```bash
pluggle run ... --transform-strategy <name>_<version>
```

Giving just the name resolves to the highest installed version.

Uninstall with:

```bash
pluggle uninstall-strategy --name <name>_<version>
```

Or remove every installed strategy at once (asks for confirmation):

```bash
pluggle uninstall-strategy --all
```

`default` cannot be uninstalled. Don't edit the strategies directory by hand — use these
commands so the strategy map always matches what's actually on disk.

## 5. Programmatic API

`pluggle.interfaces.api` exposes the same strategy management for other Python
applications to call in-process, without going through the CLI:

```python
from pluggle.interfaces import api
from pluggle.models.dto import InputArgs

api.run(input_args)  # execute a pipeline, returns the final registry entry id

api.list_available_strategies()  # names in the pluggle-strategies catalog
api.list_installed_strategies()  # names currently installed
api.install_from_repo(repo_name)
api.install_all_in_repo()  # skips what's already installed
api.uninstall(strategy_name)
api.uninstall_all()
```

Functions return plain Python objects and let Pluggle's exceptions propagate — the
calling application decides how to report them.

## 6. Known Limitations

- **No dependency management for installed strategies**: a Transform strategy installed
  via `install-strategy` may import third-party libraries not bundled with Pluggle. You
  are responsible for installing any such dependencies yourself — Pluggle does not
  manage them.
- **Uninstalling a strategy breaks its lineage**: registry rows from past runs keep the
  strategy's name and version, but once the file is removed nothing resolves that
  reference back to actual code.

## 7. Notes for contributors

- **A strategy's identity comes from its `meta`, not its filename.** The installed
  filename is derived from `meta`, which is what makes conflict detection a plain
  file-existence check — but renaming a file by hand changes nothing about which
  strategy it is.
- **`RegistryEntry.address` means different things by phase.** In Fetch, Decode, Extract
  and Transform it's a payload address (look it up via
  `payload_store.load`). In Load and Export it's the target itself — a connection string
  or a file path.
- **The canonical format is not always `list[dict]`.** It's any JSON-serializable `list`
  or `dict`. CSV/JSON/PDF Extract produce lists of records; XML/HTML produce a nested
  dict; DOCX/XLSX produce a dict keyed by internal zip member. The shape follows the
  source format's own structure rather than one fixed convention.

## 8. Roadmap

See `docs/ROADMAP.md` for planned milestones.