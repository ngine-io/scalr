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
  query: '100 - (avg by (job) (rate(node_cpu_seconds_total{mode="idle", instance=~"cluster-node.*"}[10m])) * 100)'
  config:
    url: http://prometheus.example.com:9090
    # Optional, defaults to true
    disable_ssl: true
```

!!! note
    The PromQL expression goes into the top level `query` key, everything
    connection related into `config`.

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
    # Optional, key of the JSON document to read, defaults to 'data'
    key: metric
    # Optional, request timeout in seconds, defaults to 60
    timeout: 60
    # Optional, number of attempts, defaults to 3
    retries: 3
    # Optional, seconds to wait between attempts, defaults to 2
    retry_wait: 2
  target: 5
```

A failing request is retried. If the endpoint stays unreachable, or the
configured key is missing, the policy reports no metric and is ignored for this
run instead of triggering a scaling action.

## Time Policy

Time based scaling, scaling during time ranges. The start time is inclusive,
the end time exclusive, and ranges may span midnight. Outside of the range the
policy reports no metric and is ignored.

```yaml
policy:
- name: Scaling up at 7 a.m. by factor 2 (pre-heating for known load)
  source: time
  target: 2
  config:
    start_time: "06:58"
    end_time: "07:00"
    metric: 1
```

```yaml
policy:
- name: Scaling down during night
  source: time
  target: 1
  config:
    start_time: "22:00"
    end_time: "05:00"
    metric: 10
```

## Random Policy

For testing purpose, random metric to get some action. Also available under the
name `dummy`.

```yaml
policy:
- name: get random nonsense
  source: random
  target: 3
  config:
    # Optional, defaults to 0
    start: 1
    # Optional, defaults to 100
    stop: 10
```
