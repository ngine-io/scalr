# Launch configs

Launch config to be used for new instances.

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

## Apache CloudStack

```yaml
kind: cloudstack
launch_config:
  service_offering: Micro
  template: Linux Debian 10
  zone: de-xy-1
  ssh_key: my-key
  tags:
    project: gemini
  root_disk_size: 20
  user_data: |
    #cloud-config
    manage_etc_hosts: true
    package_update: true
    package_upgrade: true
    packages:
      - nginx
```

## DigitalOcean

```yaml
kind: digitalocean
launch_config:
  size: s-1vcpu-1gb
  image: debian-10-x64
  region: ams3
  ssh_keys:
    - 'b5:be:e8:...'
  tags:
    - 'project:gemini'
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
