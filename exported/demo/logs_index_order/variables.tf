data "terraform_remote_state" "logs_index" {
  backend = "local"

  config = {
    path = "../datadog/logs_indexterraform.tfstate"
  }
}
