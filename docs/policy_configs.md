# Policy Configs

Policies define if and how much to scale.

## Metric Target

The target in is the metric we want to reach. A source metric returned higher than this target will result in scaling up, a lower to scaling down.

!!! example
    Given a target of 5, a source metric returned of 10 will results in a scaling factor 2.0.
    With 2 instances already running, a factor 2 will scale to 4 instances (2 x 2.0), except the max allow instances is lower than 4.

## Prometheus Policy

Query a Prometheus endpoint.

```yaml
policy:
- name: CPU avg load < 60%
  target: 60
  source: prometheus
  config:
    url: http://prometheus.example.com:9090
    query: '100 - (avg by (job) (rate(node_cpu_seconds_total{mode="idle", instance=~"cluster-node.*"}[10m])) * 100)'
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
