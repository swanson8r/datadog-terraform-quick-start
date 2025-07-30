data "terraform_remote_state" "synthetics_test" {
  backend = "local"

  config = {
    path = "../datadog/synthetics_testterraform.tfstate"
  }
}
