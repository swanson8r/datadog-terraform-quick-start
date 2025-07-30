data "terraform_remote_state" "logs_archive" {
  backend = "local"

  config = {
    path = "../datadog/logs_archiveterraform.tfstate"
  }
}
