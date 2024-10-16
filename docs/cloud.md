# Cloud configs

Cloud config to be used for lunching new instances.

!!! Warning
    Changing a cloud launch config have no affect to already running cloud instances. But this may change in the future.

## cloudscale.ch

```yaml
cloud:
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
cloud:
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
cloud:
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
cloud:
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

## Vultr Cloud

```yaml
cloud:
  kind: vultr
  launch_config:
    plan: vc2-1c-1gb
    # Debian 11
    os_id: 477
    region: fra
    sshkey_id:
      - xxxxxxxx-...
    user_data: |
      #!/bin/sh
      echo "Hello World" > /root/hello-world.txt
    # script_id: ...
    # iso_id: ...
    # snapshot_id ...
    # enable_ipv6: true
    # backups: enabled
    # app_id: app_id
    # image_id: image_id
    # activation_email: true
    # attach_private_network: [...]
    # app_id: ...
    # image_id: ...
    # ddos_protection: true
    # firewall_group_id: ...
    # enable_private_network: true
```

## Apache CloudStack

```yaml
  kind: cloudstack
  launch_config:
    service_offering: cpu2-ram2
    template: Linux Template xyz
    zone: my-zone
    ssh_key: my_ssh_key
    tags:
      project: gemini
    root_disk_size: 20
    user_data: |
      #cloud-config
      manage_etc_hosts: true
      packages:
        - nginx
```
