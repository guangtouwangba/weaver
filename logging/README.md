# Self-Hosted Logging Infrastructure

This directory contains configuration files for the self-hosted Loki + Grafana logging stack.

## Components

- **Loki**: Log aggregation and storage system
- **Grafana**: Visualization and query interface

## Files

- `loki-config.yaml`: Loki server configuration
- `grafana-datasource.yaml`: Grafana data source configuration (auto-provisioning Loki)
- `docker-compose-logging.yml`: Local testing setup

## Deployment on Zeabur

### Option 1: Separate Logging Service

Create a new Zeabur service with a custom Dockerfile that includes both Loki and Grafana.

### Option 2: Manual Service Creation

1. Create Loki service from `grafana/loki:latest`
2. Create Grafana service from `grafana/grafana:latest`
3. Configure network connectivity between services

## Environment Variables

### Loki Service
- No special env vars required (uses mounted config)

### Grafana Service
- `GF_SECURITY_ADMIN_PASSWORD`: Admin dashboard password
- `GF_INSTALL_PLUGINS`: (optional) Additional plugins

## Volume Mounts

### Loki
- `/loki`: Data storage (chunks, indexes, compactor)

### Grafana
- `/var/lib/grafana`: Dashboard and settings storage
- `/etc/grafana/provisioning/datasources`: Auto-provision Loki datasource

## Accessing Logs

1. Open Grafana at `http://grafana-service-url:3000`
2. Login with username `admin` and configured password
3. Navigate to "Explore" → Select "Loki" data source
4. Use LogQL queries to search logs

Example queries:
```logql
{service="backend"}
{service="frontend", level="error"}
{service="backend"} |= "database"
```

## Log Retention

Default retention: **7 days** (168 hours)

To adjust, modify `retention_period` in `loki-config.yaml`.

