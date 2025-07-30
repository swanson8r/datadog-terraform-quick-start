resource "datadog_user" "user_bfe873e1-5687-11f0-a0a3-ce3e376c4195" {
  disabled = "false"
  email    = "" # manually redacted
  name     = "DD_READ"
  roles    = ["${data.terraform_remote_state.role.outputs.datadog_role_role_d420d5ec-5678-11f0-8b66-da7ad0900002_id}"]
}

resource "datadog_user" "user_d430e413-5678-11f0-a794-ea9d16548a75" {
  disabled = "false"
  email    = "robot-datadog-learning-center-admin@datadoghq.com"
  roles    = ["${data.terraform_remote_state.role.outputs.datadog_role_role_d4059688-5678-11f0-a7b6-da7ad0900002_id}"]
}

resource "datadog_user" "user_d58253f4-5678-11f0-ba2c-462526cde661" {
  disabled = "false"
  email    = "1x0y3u4vi1@ddtraining.datadoghq.com"
  name     = "1x0y3u4vi1"
  roles    = ["${data.terraform_remote_state.role.outputs.datadog_role_role_d4059688-5678-11f0-a7b6-da7ad0900002_id}"]
}
