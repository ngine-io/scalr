# Scalr - Autoscaling for Clouds

Scalr allows to scale Cloud instances based on policy checks in a configurable interval. Scalr has 3 pluggable interfaces: config, cloud, policy.

## Cloud Plugins

This is the connector to the API of your Cloud provider. It reads current available servers of your Scalr group and scales up and down based on a calculation factor:

- [Cloudscale.ch](https://www.cloudscale.ch/)
- [Hetzner Cloud](https://www.hetzner.com/cloud)
- [Cloudstack](https://cloudstack.apache.org) (planned)
- [Exoscale](https://www.exoscale.com) (planned)
- [PCextreme](https://www.pcextreme.com) (planned)
- [Vultr](https://www.vultr.com) (planned)

## Policy Plugins

A policy defines check of a target value (amount of CPU, amount of HTTP requests, etc) and where to gather the metric from, such as the follwoing. Multiple policies can be used in a single config.

- HTTP endpoint returning JSON
- [Prometheus](https://prometheus.io) (planned)
- [InfluxDB](https://www.influxdata.com/) (planned)

## Config Interfaces / Plugins

Your Cloud and policy configuration are defined by a configuration endpoint. Scalr reads its configuration on every run and can be changed inbetween runs.

- Static YAML file
- API, configs can be changed by HTTP post (planned)
- [etcd](https://etcd.io) (planned)
- [consul](https://www.consul.io) (planned)
- HTTP endpoint returning JSON

## Install

!!! warning
    Scalr is heavily under development. This will break.


```shell
pip install https://github.com/ngine-io/scalr/archive/main.zip
```

## Start Scalr

```shell
scalr-ngine
```
