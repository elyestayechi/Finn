#!/bin/bash
# create-monitoring-structure.sh

echo "=== Creating monitoring directory structure ==="

# Create directories
mkdir -p monitoring/prometheus
mkdir -p monitoring/alertmanager  
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards

echo "✅ Created directory structure"

# Create default files if they don't exist
if [ ! -f "monitoring/prometheus/prometheus.yml" ]; then
    echo "Creating default prometheus.yml..."
    cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - alerts.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    metrics_path: /metrics
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 10s
EOF
    echo "✅ Created prometheus.yml"
else
    echo "✅ prometheus.yml already exists"
fi

if [ ! -f "monitoring/prometheus/alerts.yml" ]; then
    echo "Creating default alerts.yml..."
    cat > monitoring/prometheus/alerts.yml << 'EOF'
groups:
  - name: finn-alerts
    rules:
      - alert: BackendDown
        expr: up{job="backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend service is down"
          description: "The Finn backend service has been down for more than 1 minute"
EOF
    echo "✅ Created alerts.yml"
else
    echo "✅ alerts.yml already exists"
fi

if [ ! -f "monitoring/alertmanager/config.yml" ]; then
    echo "Creating default alertmanager config.yml..."
    cat > monitoring/alertmanager/config.yml << 'EOF'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'webhook'

receivers:
  - name: 'webhook'
    webhook_configs:
      - url: 'http://webhook:5000/'
        send_resolved: true
EOF
    echo "✅ Created alertmanager config.yml"
else
    echo "✅ alertmanager config.yml already exists"
fi

if [ ! -f "monitoring/grafana/provisioning/datasources/datasource.yml" ]; then
    echo "Creating default datasource.yml..."
    cat > monitoring/grafana/provisioning/datasources/datasource.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    version: 1
    editable: false
EOF
    echo "✅ Created datasource.yml"
else
    echo "✅ datasource.yml already exists"
fi

if [ ! -f "monitoring/grafana/provisioning/dashboards/dashboards.yml" ]; then
    echo "Creating default dashboards.yml..."
    cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Finn Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
    echo "✅ Created dashboards.yml"
else
    echo "✅ dashboards.yml already exists"
fi

echo "✅ Monitoring directory structure created successfully!"