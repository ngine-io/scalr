# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Scalr (`scalr-ngine` on PyPI) autoscales cloud instances: on each run it reads a YAML config, asks one or more policies for a scaling factor, and creates or destroys instances in a cloud provider to match. User docs live in `docs/` (mkdocs, published to https://ngine-io.github.io/scalr/).

## Commands

The project uses [uv](https://docs.astral.sh/uv/); dependencies are pinned in `uv.lock`.

```shell
uv sync --group dev          # set up the environment
make test                    # pytest with coverage on the current interpreter
make test-all                # pytest on every Python in PYTHON_VERSIONS (3.10–3.14), envs in .venvs/
make lint                    # ruff check + ruff format --check (what CI runs)
make format                  # ruff --fix + ruff format
make docs                    # mkdocs serve

# Single test file / test
uv run --group dev pytest tests/test_scalr.py
uv run --group dev pytest tests/test_scalr.py::test_name -q

# Run the app
uv run scalr-ngine --config sample/config.yml             # one run
uv run scalr-ngine --config config.yml --periodic --interval 60
```

pytest is configured with `filterwarnings = error`, so any new warning (except `DeprecationWarning`) fails the suite. Ruff line length is 100, target `py310`.

## Architecture

One scaling run is `app_once()` in [scalr/app.py](scalr/app.py):

1. `ScalingConfig.from_yaml_file()` ([scalr/config.py](scalr/config.py)) — pydantic v2 models with `extra="forbid"` so unknown/misspelled keys fail validation. The config is re-read on every run (periodic mode never needs a restart).
2. `CloudAdapterFactory.create(cfg.cloud.kind)` → `configure(filter_name=cfg.name, launch=cfg.cloud.launch_config)`. `cfg.name` is the scaling group; adapters tag/label instances with it and only manage instances carrying that tag.
3. `Scalr.get_factor()` ([scalr/scalr.py](scalr/scalr.py)) builds each policy via `PolicyAdapterFactory` and takes the **maximum** factor. Policies returning `<= 0` mean "no opinion" and are ignored.
4. `Scalr.calc_diff()` computes `desired = ceil(current * factor)`, clamps to `[min, max]`, and limits scale-down to `max_step_down`. `current == 0` is treated as 1 for the calculation. If every policy reports "no opinion" (or there are none), the factor is 0 and the group drifts down to `min` — this is intended and covered by tests.
5. `Scalr.scale()` deploys/destroys (skipped under `dry_run`), then `ensure_instances_running()`; a cooldown sleep follows any non-zero diff.

Prometheus gauges are defined in [scalr/metric.py](scalr/metric.py) and set from `app.py`; the exporter HTTP server is only started in `--periodic` mode.

### Adapters (plugin pattern)

- **Cloud adapters** subclass `CloudAdapter` ([scalr/cloud/__init__.py](scalr/cloud/__init__.py)) and live in `scalr/cloud/adapters/`. Contract: `get_current_instances()` **must return instances sorted oldest first** — `Scalr.select_instance()` relies on index `0`/`-1` for the `oldest`/`youngest` scale-down strategies. Credentials come from env vars read in the adapter `__init__` (e.g. `HCLOUD_API_TOKEN`, `CLOUDSCALE_API_TOKEN`, `VULTR_API_KEY`, `CLOUDSTACK_API_*`).
- **Policy adapters** subclass `PolicyAdapter` ([scalr/policy/__init__.py](scalr/policy/__init__.py)) in `scalr/policy/adapters/` and implement only `get_current()`. The base `get_scaling_factor()` returns `target / current` and swallows any exception (logging it and returning `0`), so a broken metric source never triggers scaling by itself.
- New adapters must be registered in the `ADAPTERS` dict of [scalr/cloud/factory.py](scalr/cloud/factory.py) or [scalr/policy/factory.py](scalr/policy/factory.py); the dict key is the `cloud.kind` / policy `source` value used in config. Document them in `docs/cloud.md` / `docs/policy_configs.md`.

### Errors and logging

- All intentional errors derive from `ScalrError` ([scalr/exceptions.py](scalr/exceptions.py)); `main()` catches it and exits 1.
- [scalr/log.py](scalr/log.py) loads `.env` and configures the `scalr` logger at import time: `logging.ini` (or `SCALR_LOG_CONFIG`) takes full control if present, otherwise a dedicated stdout handler at `SCALR_LOG_LEVEL`. It deliberately avoids `logging.basicConfig()` because cloud SDKs call it on import.

## Testing conventions

Tests never hit real clouds. Cloud adapter tests monkeypatch the SDK client class in the adapter module with hand-written fakes (see `tests/test_cloud_hcloud.py`); HTTP-based code uses `responses`. Shared fixtures in `tests/conftest.py` provide a valid config dict, a `ScalingConfig`, a YAML `config_file`, a `DummyCloudAdapter`, and an oldest-first instance list.
