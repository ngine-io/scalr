# Policy Configs

Policies define if and how much to scale.

## Metric Target

The target in is the metric we want to reach. A source metric returned higher than this target will result in scaling up, a lower to scaling down.

For example: given a target of 5, a source metric returned of 10 will results in a scaling factor 2.0.
With 2 instances already running, a factor 2 will scale to 4 instances (2 x 2.0), except the max allow instances is lower than 4.

## Prometheus Policy

Query a Prometheus endpoint (not yet implemented).

```yaml
policy:
- name: Get Loadbalancer metrics
  target: 1000
  source: prometheus
  query: "scalar(avg(haproxy_server_current_sessions))"
```

## InfluxDB Policy

Query an InfluxDB endpoint (not yet implemented).

```yaml
policy:
- name: Get CPU metrics
  target: 70
  source: influxdb
  query: "select value from cpu_load_short;"
```

## Web Policy

Query a web endpoint.

A JSON return `{"metric": <int>}` is expected in this case.

```yaml
policy:
- name: get metric from web
  source: web
  query: http://localhost:8000/target.json
  config:
    # Optional headers
    headers:
      Authorization: Bearer xyz
    # Optional default key 'data'
    key: metric
  target: 5
```

## Random Policy

For testing purpose, random metric to get some action.

```yaml
policy:
- name: get random nonsense
  source: random
  target: 3
  config:
    start: 1
    stop: 10
```
