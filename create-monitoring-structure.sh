#!/bin/bash
echo "=== Creating test directories ==="
mkdir -p Back/test-results Back/coverage
chmod 777 Back/test-results Back/coverage

echo "=== Creating monitoring directory structure ==="

# Create monitoring directories
mkdir -p monitoring/prometheus
mkdir -p monitoring/alertmanager
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards

# Create prometheus config files if they don't exist
if [ ! -f monitoring/prometheus/prometheus.yml ]; then
    cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

rule_files:
  - alerts.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s

  - job_name: 'backend'
    metrics_path: /metrics
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 10s
    scrape_timeout: 5s

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s
EOF
fi

if [ ! -f monitoring/prometheus/alerts.yml ]; then
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

      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total{job="backend"}[5m]) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "Backend CPU usage is above 80% for 5 minutes"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes{job="backend"} > 1.6e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Backend memory usage is above 1.6GB for 5 minutes"

      - alert: HighErrorRate
        expr: rate(analysis_failure_total[5m]) / rate(analysis_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High analysis error rate"
          description: "Loan analysis error rate is above 10% for 5 minutes"
EOF
fi

# Create alertmanager config
if [ ! -f monitoring/alertmanager/config.yml ]; then
    cat > monitoring/alertmanager/config.yml << 'EOF'
global:
  resolve_timeout: 5m
  smtp_smarthost: 'localhost:25'
  smtp_from: 'alertmanager@finn.local'

route:
  group_by: ['alertname', 'job']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default-receiver'

  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      repeat_interval: 30m

receivers:
  - name: 'default-receiver'
    webhook_configs:
      - url: 'http://webhook:5000/'
        send_resolved: true

  - name: 'critical-alerts'
    webhook_configs:
      - url: 'http://webhook:5000/critical'
        send_resolved: true
    email_configs:
      - to: 'admin@finn.local'
        send_resolved: true
EOF
fi

# Create grafana datasource config
if [ ! -f monitoring/grafana/provisioning/datasources/datasource.yml ]; then
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
    jsonData:
      timeInterval: 15s
      httpMethod: GET
EOF
fi

# Create grafana dashboards config
if [ ! -f monitoring/grafana/provisioning/dashboards/dashboards.yml ]; then
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
fi

echo "=== Monitoring structure created successfully ==="