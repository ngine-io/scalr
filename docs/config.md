# Configs

Scale configuration is made by creating a `config.yml` or whatever file `SCALR_CONFIG` points to.

!!! note
    The config will be re-read before every run, no need to restart a running Scalr service after a config change.

## Common Config

```yaml
---
name: my scaling config
base_rule:
  # Whether this config is enabled or disabled
  enabled: true

  # Allows to run Scalr without any actions taken.
  dry_run: false

  # Time to let Scalr hold on further actions after an action was taken.
  cooldown: 120

  # Range in which Scalr will scale.
  min: 2
  max: 5

  # Define how many instances can be scaled down at once.
  #  0: no scaling down
  # -1: no limit.
  max_step_down: 1

# Optional: time based rules (first match)
time_rules:
  - name: More capacity on Black Friday 2021
    days_of_year:
      - Nov26
    # Do not evaluate further rules on match
    on_match: break
    rule:
      min: 3
      max: 8

  - name: Turn off scaling during weekly maintenance
    days_of_year:
      - Wed
    times_of_day:
      - 01:00-04:00
    rule:
      enabled: false

  - name: Allow Lights off on weekends
    weekdays:
      - Sun
      - Sat
    rule:
      min: 0
      max_step_down: 2

# See Policy configs
policies: []

# See Launch config
kind: ...
launch_config: {}
```
