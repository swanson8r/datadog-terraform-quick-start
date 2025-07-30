resource "datadog_logs_index_order" "logs_index_order_20250730194110" {
  indexes = ["${data.terraform_remote_state.logs_index.outputs.datadog_logs_index_logs_index_main_id}"]
  name    = "logs_index_order_20250730194110"
}
