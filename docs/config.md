# Configs

Scale configuration is made by creating a `config.yml` or whatever file `SCALR_CONFIG` points to.

!!! hint
    The config will be re-read before every run, no need to restart a running Scalr service after a config change.

## Common Config Skeleton

!!! hint
    You find a sample config.yml in our [GitHub Repo](https://github.com/ngine-io/scalr/)

```yaml
---
# Name is used to group instances e.g. with a tag or label depending on the cloud provider
# NOTE: If you change the name, all current instances having the name are getting unmanaged.
name: my-app

# Change it to false to completely skip all action
enabled: true

# Change it to false to skip the scaling
dry_run: false

# Not scaling down below this value
min: 2

# Not scaling up above this value
max: 5

# The max value of instances to be scaled down in one run
max_step_down: 1

# Strategy of order to destroy instances
scale_down_selection: oldest

# After scaling down, wait for so long in seconds
cooldown_timeout: 60

# See Policy configs
policies: []

# See cloud config
cloud:
  kind: ...
  launch_config: {}
```
