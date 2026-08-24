![license](https://img.shields.io/pypi/l/scalr-ngine.svg)
![python versions](https://img.shields.io/pypi/pyversions/scalr-ngine.svg)
![status](https://img.shields.io/pypi/status/scalr-ngine.svg)
[![pypi version](https://img.shields.io/pypi/v/scalr-ngine.svg)](https://pypi.org/project/scalr-ngine/)
![PyPI - Downloads](https://img.shields.io/pypi/dw/scalr-ngine)
[![Codecov](https://img.shields.io/codecov/c/github/ngine-io/scalr)](https://codecov.io/gh/ngine-io/scalr)

# Scalr - Autoscaling for Clouds

Scale Cloud instances based on policy checks in a configurable interval.

## Documentation

Please visit https://ngine-io.github.io/scalr/

## Development

The project uses [uv](https://docs.astral.sh/uv/). Dependencies live in
`pyproject.toml` and are pinned in `uv.lock`.

```shell
# Create the environment from the lock file
uv sync --group dev

# Tests on the current interpreter
make test

# Tests on every supported interpreter (3.10 - 3.13)
make test-all

# Lint and format
make lint
make format

# Refresh the pinned versions
make upgrade
```

## License

MIT License
