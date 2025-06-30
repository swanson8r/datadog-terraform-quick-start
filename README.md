# Datadog As Code Quick Start

This repository contains scripts to generate a repository of Terraform files for a given Datadog account.
The inspiration for creating this has come from many experiences with Datadog customers that want to
maintain their Datadog environment as code, but also don't want to start from scratch.

This quick-start allows for a small amount of configuration that will generate Terraform files from existing
Datadog resources along with their current state, allowing for granular management by resource type in a
very short span of time.

## Supported Datadog resources

- Dashboards
  - Dashboard configurations
  - Dashboard lists
- Logging
  - Archives
  - Archive ordering
  - Custom pipelines
  - Integration pipelines
  - Pipeline ordering
  - Indexes
  - Index ordering
- Integrations
  - AWS
    - Accounts
    - Log Lambdas
    - Log collection rules
  - Azure
    - Accounts
  - PagerDuty
    - Services
  - Slack
    - Channels
- Metric metadata
- Monitors
- Security Rules
  - Enabled default rules
  - Custom rules
- SLOs
- Synthetics
  - Test definitions
  - Global variables
  - Private locations
- User Management
  - Users
  - Roles

## Use Cases

There are several reasons to consider using this tool, and probably more that we have not thought of.

- Create a basis for managing observability as code
- Import your most important/critical resources to ensure consistency in the future
- Import different sets of resources for different teams to manage
- Provide a backup of your current Datadog state

## What Does This Do, and How Does It Work?

The quick start is powered by:

- [Terraform](https://www.terraform.io/)
- [Terraformer](https://github.com/GoogleCloudPlatform/terraformer)
- [Datadog Terraform provider](https://registry.terraform.io/providers/DataDog/datadog/latest/docs)
- [Docker Compose](https://github.com/docker/compose)
- and some custom scripting (bash and python)

Terraformer utilizes Terraform and the Datadog provider to convert Datadog API responses into Terraform files
along with their current state (for details, see
[Importing Datadog Resources into Terraform](https://docs.datadoghq.com/containers/guide/how-to-import-datadog-resources-into-terraform/#terraformer)).
The custom scripting manipulates those files to address some of the limitations of Terraformer itself, in addition to executing
the Terraformer commands required to pull down Datadog resources based on the provided configuration.

The end result is a `tree` of files similar to this example:

```bash
.
└── datadog
    ├── dashboard
    │   ├── dashboard.tf
    │   ├── provider.tf
    │   └── terraform.tfstate
    ├── integration_slack_channel
    │   ├── integration_slack_channel.tf
    │   ├── provider.tf
    │   └── terraform.tfstate
    ├── monitor
    │   ├── monitor.tf
    │   ├── provider.tf
    │   └── terraform.tfstate
    └── user
        ├── provider.tf
        ├── terraform.tfstate
        └── user.tf
```

Each type of resource will have its own state file tracked independently, so changes to monitors will not
require interaction with any other resource types (for example).

We chose to not be prescriptive with [Next Steps](#next-steps) after this import has been completed,
 as there can be many directions to go based on organizational preference or initial necessity for generating these files.

## What Doesn't This Do?

- This quick start will not affect the current state of your Datadog environment; it will only read the state and generate Terraform files based on it
- It will not maintain the state that it imported; this is a one time import, not programmatic management
- Any resource that is not imported via the configuration of this toolset will not be managed by Terraform

## Requirements

All that is required to run this is [docker-compose](https://docs.docker.com/compose/install/#scenario-one-install-docker-desktop-recommended)
 (included in [Docker](https://www.docker.com/)).

> [!TIP]
> If you choose to use the files generated outside of this repository,
> you will also need to have [Terraform](https://developer.hashicorp.com/terraform/install) installed.

## Configuration

> [!IMPORTANT]
> Application key must be [scoped](https://docs.datadoghq.com/account_management/api-app-keys/#scope-application-keys)
> to have **read** capabilities to the account

1. Rename the sample environment file [.env.sample](.env.sample) to become the default:

    ```bash
    mv .env.sample .env
    ```

2. Update `.env` file values:
   - `DD_API_KEY` and `DD_APP_KEY` with your [Datadog API and Application keys](https://docs.datadoghq.com/account_management/api-app-keys/)

   - If your [Datadog Site value](https://docs.datadoghq.com/getting_started/site/#access-the-datadog-site) is *not* the default of **US1**
    (`app.datadoghq.com`), set `DD_HOST` to the **SITE URL** corresponding to your **SITE**. Otherwise, leave it empty.

3. Build a custom Docker image defined in the [docker-compose.yml](docker-compose.yml) build step:

    ```bash
    docker-compose build 
    ```

4. Edit the [conf.yaml](conf.yaml) file to configure which datadog resources to import into Terraform
   - see [conf_example.yaml](conf_example.yaml) for more detail

## Usage

### Initial Run

Run the Docker image to execute the Datadog Terraform import process

 ```bash
 docker-compose run ddtf
 ```

### Subsequent Runs

If a subsequent run is required to include a missed resource or apply a configuration change,
it is recommended that the generated files in the `terraform/datadog` directory be removed before proceeding.
This will avoid unintentional duplication of resource definitions due to how files are imported and merged,
and maintain the general cleanliness of the resulting files.

> [!IMPORTANT]
> Ensure that the [providers.tf](terraform/providers.tf) file in the parent [terraform](terraform) directory is **not**
> deleted as part of this cleanup

## Next Steps

Now that you have generated your desired Datadog resources as Terraform files, there are many directions you
can choose to make next steps towards.

> [!TIP]
> We recommend moving the generated files from `terraform/datadog` to another folder or repository;
> if you choose to run the code in this repository again, those will be overwritten

### State Backends

- Generally speaking, it is not desirable to store Terraform state files locally, as that could lead to accidentally committing
  credentials to a repository, or make collaboration difficult
- After the files are generated, you may want to create a `backend.tf`
  file or add to [provider.tf](terraform/provider.tf) to establish one of the many
  [Remote State Backends that Terraform provides](https://developer.hashicorp.com/terraform/language/backend)
- Once you have configured a remote backend (such as [Azure Storage](https://developer.hashicorp.com/terraform/language/backend/azurerm)
 or [AWS S3](https://developer.hashicorp.com/terraform/language/backend/s3)), you will need to migrate the locally generated state file there:

   ```bash
   terraform init -migrate-state 
   ```

### Initialize Terraform for a resource type

- Each type of resource contains its own state file, and is managed independently
  - In order to be able to manage these with Terraform, it will need to be initialized *within* the resource directory by executing `terraform init`
  - You will now be able to run additional Terraform commands scoped to this resource

### CI

- Consider building a CI process around a repository containing the generated files. This can allow for reviewing changes
  to critical dashboards and monitors to maintain standards and consistency, or preserve ownership of monitoring to a dedicated
  team. A common process would look something like this:
  - User enters a merge/pull request to the repository with a change to a resource
  - A job detects a change to that resource type, and runs a `terraform plan` against the resource to show the
    user or reviewer exactly what would change, and ensure nothing is done unintentionally
  - The change is reviewed, approved, and merged
  - Another set of jobs runs to apply the changes and commit the new state

### Separate Management Responsibilities

- While this repository is intended to be used for grabbing large sets of resources based on configuration at a time, it is also possible
  to utilize it multiple times for smaller sets.
- Example: Terraform Monitor configurations can be broken out for management by their owning teams
  - Utilize this tooling to pull down monitors for one team tag at a time
  - Move each team's generated files out to a team-specific directory or separate repository.
  - This can allow for distinct management on a team by team or app by app basis and reduce the need for a monolithic type monitoring repository.

### Add New Dashboards via JSON

> [!NOTE]
> If you are going to replace a dashboard/monitor that has already been imported in HCL,
> you will want to remove that entry from the Terraform file *before* applying the JSON change.  

- Admittedly, the generated Terraform files for monitors and dashboards can be clunky, large, and difficult to understand how and where
  changes are made.
- The good news is that monitors and dashboards (only) can be exported from Datadog as JSON and then established within
  the Terraform files in the same format. This allows a user to go and make graphical changes in the UI, export the results, and then
  recommit the changes to the repository.
- There are a few ways to go about this, but the following is a suggested method. Given the following structure:

   ```bash
    .
    └── datadog
        ├── dashboard
        │   ├── dashboard.tf
        │   ├── provider.tf
        │   └── terraform.tfstate
        └── monitor
            ├── provider.tf
            ├── terraform.tfstate
            └── monitor.tf
    ```

- We can then create a `files` directory within each resource directory, export a dashboard as JSON, and add that file to the created directory:

    ```bash
    .
    └── datadog
    │   └── dashboard
    │       ├── dashboard.tf
    │       ├── files
    │       │   └── example.json
    │       ├── provider.tf
    │       └── tfstate.tf
    │   └── monitor
    │       ├── provider.tf
    │       ├── terraform.tfstate
    │       └── monitor.tf
    ```

- Within the `dashboard.tf` file, we can then add the following:

    ```hcl
    resource "datadog_dashboard_json" "example_dashboard" {
        dashboard = file("../example.json")
    }
    ```

- This process is the same for monitors, just utilizing the appropriate files

> [!NOTE]
> Exporting a Datadog resource as JSON and then applying it with Terraform will cause a
> duplicate resource in Datadog, since the state was not imported. To avoid this, you can utilize
> the `terraform import` command which will update the state file appropriately.
> Example:
> `terraform import datadog_dashboard_json.example_dashboard abc-123-xyz`

## Known Issues

There are some known issues with this repository, largely due to the usage of other
open source tools.

### Not all Datadog resources available

- Terraformer does not support all of the Datadog resources that are currently available
  from the [Datadog provider](https://github.com/DataDog/terraform-provider-datadog/releases).
   As more functionality is [released](https://github.com/GoogleCloudPlatform/terraformer/releases), this repository will be updated.

### GCP integration importing

- As of time of writing, Terraformer has not caught up with the change to how
 [GCP](https://github.com/GoogleCloudPlatform/terraformer/blob/master/docs/gcp.md) accounts are
  added to Datadog, and as a result, GCP accounts cannot be imported directly.
- The good news is that creating the required Terraform definitions for these is not overly complicated, and documentation
  for doing such [can be found here](https://registry.terraform.io/providers/DataDog/datadog/latest/docs/resources/integration_gcp_sts)

### Monitor Downtime importing

- Due to API changes as of time of writing, Terraformer is not up to date with importing
 [Monitor downtimes](https://docs.datadoghq.com/api/latest/downtimes/)

### PagerDuty schedules

- Due to API changes as of time of writing, [Terraformer](https://github.com/GoogleCloudPlatform/terraformer/blob/master/docs/pagerduty.md)
 is not up to date with importing
 [PagerDuty Schedules](https://registry.terraform.io/providers/PagerDuty/pagerduty/latest/docs/resources/schedule) (services work, however)

### Terraformer/Datadog Provider performance

- Due to a potentially large amount of API requests that are required to generate these files, sometimes the performance
  of this scripting can be slow, or present errors.
- The majority of the common occurrences have been accounted for by built-in Terraformer retries
  and additional retry loops within the scripting around this process. Any failures should be validated, as a retry was likely successful.

### Not intended to be run regularly

- As stated in [What Doesn't This Do?](#what-doesnt-this-do), this repository is meant for an initial quick-start import. 

> [!WARNING]
> This Quick Start repositiory is **not** meant to be a regularly run process,
> and if used as such may cause unintentional behavior within the management of Datadog resources.
> See [Next Steps > CI](#ci) for suggestions.

## Support

Have a question, need some help, or want to report a bug?
Please enter an [issue](https://github.com/nobstech/datadog-terraform-quick-start/issues) within the repository.

Need more help than we can give through an Issue? [Head over to our website and get in touch!](https://www.nobs.tech/contact)

![logo](https://nobs-images.s3.us-east-2.amazonaws.com/nobs-logos-text-purple.png)
