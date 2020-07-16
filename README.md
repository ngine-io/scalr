# Scalr - Autoscaling for Clouds

Scalr allows to scale Cloud instances based on base config and policy checks in a configurable interval. Scalr has 3 pluggable interfaces: config, cloud, policy. 

## Cloud Plugins

This is the connector to the API of your Cloud provider. It reads current available servers of your Scalr group and scales up and down based on a calcualtor factor:

- [Cloudscale.ch](https://www.cloudscale.ch/)
- [Hetzner Cloud](https://www.hetzner.com/cloud)
- [Cloudstack](https://cloudstack.apache.org) (planned)
- [Exoscale](https://www.exoscale.com) (planned)
- [PCextreme](https://www.pcextreme.com) (planned)
- [Vultr](https://www.vultr.com) (planned)

## Policy

A policy defines check of a target value (amount of CPU, amount of HTTP requests, etc) and where to gather the metric from, such as the follwoing. Multiple policies can be used in a single config.

- HTTP endpoint returning JSON
- [Prometheus](https://prometheus.io) (planned)
- [InfluxDB](https://www.influxdata.com/) (planned)

## Config

Your Cloud and Policy configuration are defined in a configuration endpoint. Scalr reads its config on every run and can be changed inbetween runs.

- Static YAML file
- API, configs can be changed by HTTP post (planned)
- [etcd](https://etcd.io) (planned)
- [consul](https://www.consul.io) (planned)
- HTTP endpoint returning JSON

## Install

WARNING: Scalr is heavily under development.

```shell
pip install https://github.com/ngine-io/scalr/archive/main.zip
```

## Setup

Setup can be initialised either by ENV vars or by providing a `.env` file:

```ini
SCALR_DB=scalr_db.json
SCALR_INTERVAL=20
SCALR_LOG_LEVEL=DEBUG
SCALR_CONFIG=./config.yml
CLOUDSCALE_API_TOKEN=<...>
HCLOUD_API_TOKEN=<...>
```

## YAML Configuration

Scale configuration is made by creating a `config.yml` or whatever file `SCALR_CONFIG` points to.

NOTE: The config will be re-read before every run, no need to restart a running Scalr service after a config change.

### Config Cloudscale.ch

```yaml
---
kind: cloudscale_ch
enabled: true

# Allows to run Scalr without any actions taken.
dry_run: false

# Time to let Scalr hold on further actions after an action was taken.
cooldown: 120

# Range in which Scalr will scale.
min: 0
max: 2

# Define how many instances can be scaled down at once.
max_step_down: 1

policy:

# Query a Prometheus endpoint (not yet implemented).
# - name: Get Loadbalancer metrics
#   target: 1000
#   source: prometheus
#   query: "scalar(avg(haproxy_server_current_sessions))"

# Query an InfluxDB endpoint (not yet implemented).
# - name: Get CPU metrics
#   target: 70
#   source: influxdb
#   query: "select value from cpu_load_short;"

# Query a web endpoint.
# A JSON return o {"metric": <int>} is expected in this case.
- name: get metric from web
  source: web
  query: http://localhost:8000/target.json
  config:
    # Optional headers
    headers:
      Authorization: Bearer xyz
    # Optional default key 'data'
    key: metric
  # Target is the metric we want to reach. A source metric returned higher than this target will result in scaling up, a lower to scaling down.
  # For example: given a target of 5, a source metric returned of 10 will results in a scaling factor 2.0.
  # With 2 instances already running, a factor 2 will scale to 4 instances (2 x 2.0), except the max allow instances is lower than 4.
  target: 5

# For testing purpose, random metric to get some action.
- name: get random nonsense
  source: random
  target: 3
  config:
    start: 1
    stop: 10

# Launch config to use for new instances.
# (Changing a launch config have no affect to running Cloud instances. But this may change in the future.)
launch_config:
  flavor: flex-2
  image: debian-10
  zone: lpg1
  tags:
    project: gemini
  ssh_keys:
    - ssh-rsa AAAA...
  user_data: |
    #cloud-config
    manage_etc_hosts: true
    package_update: true
    package_upgrade: true
    packages:
      - nginx
```

### Config Hetzner Cloud

```yaml
---
kind: hcloud
policy:
# ... list of policies
launch_config:
  server_type: cx11
  image: debian-10
  labels:
    project: gemini
  location: fsn1
  ssh_keys:
    - my_key
  user_data: |
    #cloud-config
    manage_etc_hosts: true
    package_update: true
    package_upgrade: true
    packages:
      - nginx
```

## Start Scalr

```shell
scalr-ngine
```

## License

MIT License
