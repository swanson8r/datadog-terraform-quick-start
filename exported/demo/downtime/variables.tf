data "terraform_remote_state" "monitor" {
  backend = "local"

  config = {
    path = "../datadog/monitorterraform.tfstate"
  }
}
