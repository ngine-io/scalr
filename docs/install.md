# Install and base settings

## Install

!!! warning
    Scalr is in beta.

```shell
pip install scalr-ngine
```

## Settings

Settings can be set either by ENV vars or by providing a `.env` file:

### Common ENV variables

```ini
SCALR_LOG_LEVEL=INFO
SCALR_CONFIG=./config.yml

# apply to --periodic
SCALR_INTERVAL=20
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

### Exoscale API settings

```ini
EXOSCALE_API_KEY=<...>
EXOSCALE_API_SECRET=<...>
```

### Hetzner Cloud API token

```ini
HCLOUD_API_TOKEN=<...>
```

### Vultr API key

```ini
VULTR_API_KEY=<...>
```
