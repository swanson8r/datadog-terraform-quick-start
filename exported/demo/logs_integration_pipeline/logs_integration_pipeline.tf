resource "datadog_logs_integration_pipeline" "Datadog-0020-Agent" {
  is_enabled = "true"
}

resource "datadog_logs_integration_pipeline" "Java" {
  is_enabled = "true"
}

resource "datadog_logs_integration_pipeline" "Nginx" {
  is_enabled = "true"
}

resource "datadog_logs_integration_pipeline" "NodeJS" {
  is_enabled = "true"
}

resource "datadog_logs_integration_pipeline" "Postgresql" {
  is_enabled = "true"
}

resource "datadog_logs_integration_pipeline" "Redis" {
  is_enabled = "true"
}

resource "datadog_logs_integration_pipeline" "Ruby" {
  is_enabled = "true"
}

resource "datadog_logs_integration_pipeline" "python" {
  is_enabled = "true"
}
