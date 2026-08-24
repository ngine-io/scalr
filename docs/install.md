# Install and base settings

## Install

!!! warning
    Scalr is in beta.

Scalr requires Python 3.10 or newer.

```shell
pip install scalr-ngine
```

## Settings

Settings can be set either by ENV vars or by providing a `.env` file:

### Common ENV variables

```ini
# One of DEBUG, INFO, WARNING, ERROR. Defaults to INFO
SCALR_LOG_LEVEL=INFO
# Path to the scaling config. Defaults to ./config.yml
SCALR_CONFIG=./config.yml
# Optional path to a logging config file. Defaults to ./logging.ini if present
SCALR_LOG_CONFIG=./logging.ini
# Run periodically instead of once. One of 1/true/yes/on
SCALR_PERIODIC=false
# Interval in seconds used with SCALR_PERIODIC. Defaults to 60
SCALR_INTERVAL=60
# Port of the Prometheus exporter in periodic mode. Defaults to 8000
SCALR_PROMETHEUS_EXPORTER_PORT=8000
```

## Cloud ENV variables

### Cloudscale.ch API token

```ini
CLOUDSCALE_API_TOKEN=<...>
```

### CloudStack API settings

```ini
CLOUDSTACK_API_ENDPOINT=https://cloud.example.com/client/api
CLOUDSTACK_API_KEY=<...>
CLOUDSTACK_API_SECRET=<...>
```

### DigitalOcean API access token

```ini
DIGITALOCEAN_ACCESS_TOKEN=<...>
```

### Hetzner Cloud API token

```ini
HCLOUD_API_TOKEN=<...>
```

### Vultr API key

```ini
VULTR_API_KEY=<...>
```
