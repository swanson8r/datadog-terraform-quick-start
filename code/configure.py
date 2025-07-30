import logging
import os
import subprocess
import sys

from constants import (
    HAS_COLONS,
    ID_MAP,
    LIST_RESOURCES,
    NESTED_RESOURCES,
    NO_ID_RESOURCES,
    OTHER_RESOURCES,
    SUPPORTED_RESOURCES,
)
from schema import SchemaError
from validate_conf import config_schema
from yaml import CLoader as Loader
from yaml import load

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGLEVEL", "INFO").upper())
ch = logging.StreamHandler()
ch.setLevel(os.environ.get("LOGLEVEL", "INFO").upper())
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def handle_list_resources(list_resources):
    for resource, conf in list_resources.items():
        # join() doesnt like integers
        conf = [str(c) for c in conf]
        # strings with colons need to be wrapped in single quotes, otherwise they are treated
        # as an "and" type statement instead of something like an ARN value
        if resource in HAS_COLONS:
            conf = [f"'{c}'" for c in conf]
        write_command(
            "{provider}/{service}",
            resource,
            [f'--filter="Name={ID_MAP.get(resource, "id")};Value={":".join(conf)}"'],
        )


def handle_no_id_resources(no_id):
    if no_id:
        resources = list(set(no_id))
        write_command("{provider}/{service}", ",".join(resources))


def handle_nested_resources(nested):
    for resource, confs in nested.items():
        for conf in confs:
            for conf_type, values in conf.items():
                if conf_type == "ids":
                    values = [str(v) for v in values]
                    write_command(
                        "{provider}/{service}/ids",
                        resource,
                        [
                            f'--filter="Name={ID_MAP.get(resource, "id")};Value={":".join(values)}"'
                        ],
                    )
                elif conf_type == "tags":
                    tags_type(resource, values)
                elif conf_type == "tagsets":
                    tagsets(resource, values)


def handle_other_resources(resources):
    for resource, conf in resources.items():
        if resource == "integration_aws":
            handle_aws_integration(resource, conf)
        elif resource == "integration_slack_channel":
            handle_slack_channel(resource, conf)


def handle_aws_integration(resource, confs):
    for conf in confs:
        for conf_key, values in conf.items():
            values = [str(v) for v in values]
            if conf_key == "account_role":
                values = [f"'{v}'" for v in values]
            write_command(
                f"{{provider}}/{{service}}/{conf_key}",
                resource,
                [
                    f'--filter="Name={ID_MAP.get(conf_key, "id")};Value={":".join(values)}"'
                ],
            )


def handle_slack_channel(resource, confs):
    for conf in confs:
        for conf_key, values in conf.items():
            if conf_key == "slack_account_names":
                for value in values:
                    write_command(
                        f"{{provider}}/{{service}}/slack_account_names/{value}",
                        resource,
                        [f'--filter="Name=account_name;Value={value}"'],
                    )
            else:
                for accounts in values:
                    for account_name, channels in accounts.items():
                        channels = [f"#{chan}" for chan in channels]
                        write_command(
                            f"{{provider}}/{{service}}/slack_account_channels/{account_name}",
                            resource,
                            [
                                f'--filter="Name=account_name;Value={account_name}"',
                                f'--filter="Name=channel_name;Value={":".join(channels)}"',
                            ],
                        )


def tags_type(resource, values):
    vals = [f"'{v}'" for v in values]
    write_command(
        "{provider}/{service}/tags",
        resource,
        [f'--filter="Name=tags;Value={":".join(vals)}"'],
    )


def tagsets(resource, values):
    for tagset in values:
        for set_name, sets in tagset.items():
            vals = [f"'{v}'" for v in sets]
        write_command(
            f"{{provider}}/{{service}}/tagsets/{set_name}",
            resource,
            [f'--filter="Name=tags;Value={":".join(vals)}"'],
        )


def write_command(path, resource, filters=None):
    base = "/usr/local/bin/terraformer import datadog"
    if filters:
        command = (
            f'{base} -n 5 -m 1000 -p {path} --resources={resource} {" ".join(filters)}'
        )
    else:
        command = f"{base} -n 5 -m 1000 -p {path} --resources={resource}"
    logger.debug(f"Running the following command: {command}")
    run_command(command)


def run_command(command, retries=3):
    output = subprocess.run(
        command, shell=True, capture_output=True, cwd="/terraform", text=True
    )
    try:
        # terraformer exits with code 0 on some failures; catch those to retry
        if (
            "error initializing resources in service" in output.stdout
            or "Unable to refresh resource" in output.stdout
            or "cannot assign requested address" in output.stdout
        ):
            raise Exception
        output.check_returncode()
        logger.info(output.stdout)
    except:
        if retries > 0:
            logger.warning(
                f'Command "{command}" failed with error {output.stdout}, {retries} retries left...retrying'
            )
            run_command(command, retries=retries - 1)
        else:
            logger.error(
                f'Command "{command}" failed with error {output.stdout} - no retries left.'
            )


def filter_resources(no_ids, config, filter):
    return {
        key: val
        for resource_conf in config["resources"]
        for key, val in resource_conf.items()
        if key in filter and key not in no_ids
    }


if __name__ == "__main__":
    try:
        with open("../conf.yaml", "r") as f:
            config = load(f, Loader=Loader)
    except FileNotFoundError:
        raise FileNotFoundError('Could not find file "conf.yaml", ensure it is present')

    if not config["resources"]:
        logger.error(
            'No resources were defined in conf.yaml, did you mean to add "all"? Exiting, please reconfigure.'
        )
        sys.exit(1)
    try:
        config_schema.validate(config)
    except SchemaError as e:
        raise Exception(e.code)

    config_resources = list(set().union(*(d.keys() for d in config["resources"])))

    for res in config_resources:
        if res not in SUPPORTED_RESOURCES:
            logger.error(
                f"Resource type '{res}' found in config, but it is not supported. It will not be imported."
            )

    if "all" in config_resources:
        logger.info('Found "all" in configuration; importing all supported resources.')
        write_command("{provider}/{service}","*")
        sys.exit(0)

    no_ids = [
        key
        for resource_conf in config["resources"]
        for key, val in resource_conf.items()
        if not val
    ] + [res for res in NO_ID_RESOURCES if res in config["resources"]]
    handle_no_id_resources(no_ids)

    list_resources = filter_resources(no_ids, config, LIST_RESOURCES)
    handle_list_resources(list_resources)

    nested_resources = filter_resources(no_ids, config, NESTED_RESOURCES)
    handle_nested_resources(nested_resources)

    other_resources = filter_resources(no_ids, config, OTHER_RESOURCES)
    handle_other_resources(other_resources)
