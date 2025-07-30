resource "datadog_logs_index" "logs_index_main" {
  daily_limit         = "0"
  disable_daily_limit = "true"

  filter {
    query = ""
  }

  name           = "main"
  retention_days = "15"
}
