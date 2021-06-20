# Configs

Scale configuration is made by creating a `config.yml` or whatever file `SCALR_CONFIG` points to.

!!! note
    The config will be re-read before every run, no need to restart a running Scalr service after a config change.

## Common Config

```yaml
---
# Whether this config is enabled or disabled
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

# See Policy configs
policy: []

# See Launch config
kind: ...
launch_config: {}
```
