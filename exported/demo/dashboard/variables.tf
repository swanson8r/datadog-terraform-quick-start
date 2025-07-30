data "terraform_remote_state" "monitor" {
  backend = "local"

  config = {
    path = "../datadog/monitorterraform.tfstate"
  }
}

data "terraform_remote_state" "service_level_objective" {
  backend = "local"

  config = {
    path = "../datadog/service_level_objectiveterraform.tfstate"
  }
}
