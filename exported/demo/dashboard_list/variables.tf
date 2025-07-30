data "terraform_remote_state" "dashboard" {
  backend = "local"

  config = {
    path = "../datadog/dashboardterraform.tfstate"
  }
}
