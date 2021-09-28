# Scalr - Autoscaling for Clouds

Scalr allows to scale Cloud instances based on policy checks in a configurable interval. Scalr has 2 pluggable interfaces: cloud, policy.

## Cloud Plugins

This is the connector to the API of your Cloud provider. It reads current available servers of your Scalr group and scales up and down based on a calculation factor received from one or more policies:

- [Cloudscale.ch](https://www.cloudscale.ch)
- [Hetzner Cloud](https://www.hetzner.com/cloud)
- [DigitalOcean](https://www.digitalocean.com)
- [Apache CloudStack](https://cloudstack.apache.org)
- [Exoscale](https://www.exoscale.com)
- [Vultr](https://www.vultr.com) (planned)

## Policy Plugins

A policy defines check of a target value (amount of CPU, amount of HTTP requests, etc) and where to gather the metric from, such as the following. Multiple policies can be used in a single config.

- HTTP endpoint returning JSON
- Random Metric (for testing)
- [Prometheus](https://prometheus.io)
- [InfluxDB](https://www.influxdata.com/) (planned)

## Config Interfaces

Your Cloud and policy configuration are defined by a configuration. Scalr reads its configuration on every run and can be changed inbetween runs.

- Static YAML file
- Static JSON file
- HTTP endpoint returning JSON

## Install

!!! warning
    Scalr is in beta.

```shell
pip install scalr-ngine
```

## Start Scalr

As "one shot" to be used as cron job:

```shell
scalr-ngine
```

As daemon:

```shell
scalr-ngine --periodic
```
