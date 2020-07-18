# Launch configs

Launch config to use for new instances.

!!! Warning
    Changing a launch config have no affect to running Cloud instances. But this may change in the future.

## Cloudscale.ch

```yaml

kind: cloudscale_ch
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

## Hetzner Cloud

```yaml
kind: hcloud
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
