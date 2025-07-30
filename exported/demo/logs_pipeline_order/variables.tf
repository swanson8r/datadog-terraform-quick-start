data "terraform_remote_state" "logs_custom_pipeline" {
  backend = "local"

  config = {
    path = "../datadog/logs_custom_pipelineterraform.tfstate"
  }
}

data "terraform_remote_state" "logs_integration_pipeline" {
  backend = "local"

  config = {
    path = "../datadog/logs_integration_pipelineterraform.tfstate"
  }
}
