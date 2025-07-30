import glob
import json
import logging
import os
import re
import shutil
import subprocess

from constants import NESTED_RESOURCES, OTHER_RESOURCES
from yaml import CLoader as Loader
from yaml import load

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGLEVEL", "INFO").upper())
ch = logging.StreamHandler()
ch.setLevel(os.environ.get("LOGLEVEL", "INFO").upper())
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def state_move(resource_type, res_dir):
    tf_resources = (
        subprocess.check_output(
            [
                "terraform",
                "state",
                "list",
                f"-state=/terraform/datadog/{resource_type}/{res_dir}/terraform.tfstate",
            ],
            text=True,
        )
        .strip()
        .split("\n")
    )
    for res in tf_resources:
        if res:
            logger.debug(
                f"Moving {res} from /terraform/datadog/{resource_type}/{res_dir}/terraform.tfstate to /terraform/datadog/{resource_type}/terraform.tfstate"
            )
            try:
                result = subprocess.run(
                    [
                        "terraform",
                        "state",
                        "mv",
                        f"-state=/terraform/datadog/{resource_type}/{res_dir}/terraform.tfstate",
                        f"-state-out=/terraform/datadog/{resource_type}/terraform.tfstate",
                        f"{res}",
                        f"{res}",
                    ],
                    capture_output=True,
                    text=True,
                )
                result.check_returncode()
                logger.info(result.stdout)
            except Exception:
                if "Invalid target address" in result.stderr:
                    logger.warning(
                        f"Duplicate resource {res} found, removing from TF file"
                    )
                    remove_tf_resource(resource_type, res_dir, res)
                else:
                    logger.error(result.stderr)


def remove_tf_resource(resource_type, resource_dir, resource_name):
    tf_res_type, tf_res_name = resource_name.split(".")
    regex = f'(resource "{tf_res_type}" "{tf_res_name}" \{{\n .*?\n\}})'
    with open(
        f"/terraform/datadog/{resource_type}/{resource_dir}/{resource_type}.tf", "r"
    ) as tf:
        logger.debug(
            f'Removing {tf_res_name} from "/terraform/datadog/{resource_type}/{resource_dir}/{resource_type}.tf"'
        )
        tf_file = tf.read()
    with open(
        f"/terraform/datadog/{resource_type}/{resource_dir}/{resource_type}.tf", "w"
    ) as tf:
        tf.write(re.sub(regex, "", tf_file, flags=re.DOTALL))


def combine_tf_files(resource_type, res_dir):
    if os.path.exists(
        f"/terraform/datadog/{resource_type}/{res_dir}/{resource_type}.tf"
    ):
        logger.info(
            f"Combining /terraform/datadog/{resource_type}/{res_dir}/{resource_type}.tf with /terraform/datadog/{resource_type}/{resource_type}.tf"
        )
        subprocess.run(
            [
                f"cat /terraform/datadog/{resource_type}/{res_dir}/{resource_type}.tf >> /terraform/datadog/{resource_type}/{resource_type}.tf"
            ],
            shell=True,
        )


def check_path_exists(resources):
    output = {}
    for res_type, res_paths in resources.items():
        for res_path in res_paths:
            if os.path.exists(f"/terraform/datadog/{res_type}/{res_path}"):
                if res_type in output:
                    output[res_type].append(res_path)
                else:
                    output[res_type] = [res_path]
    return output


def copy_and_del(source, dest):
    logger.debug(f"Copying {source} to {dest}")
    shutil.copytree(source, dest, dirs_exist_ok=True)
    logger.debug(f"Deleting {source}")
    shutil.rmtree(source)


def sort_config(config):
    # this is a dirty hack to make sure weird nested stuff isnt processed first.
    sorted_conf = {}
    for res, paths in config.items():
        if len(paths) > 1:
            if paths[0] in ["slack_account_channels", "tagsets"]:
                sorted_conf[res] = paths[::-1]
            else:
                sorted_conf[res] = paths
        else:
            sorted_conf[res] = paths
    return sorted_conf


def process_tagset_init(res_type, key):
    dirs = os.listdir(f"/terraform/datadog/{res_type}/{key}")
    file_destination_source = f"/terraform/datadog/{res_type}/{key}/{dirs.pop(0)}/"
    copy_and_del(file_destination_source, f"/terraform/datadog/{res_type}")
    for dir in dirs:
        state_move(res_type, f"{key}/{dir}")
        combine_tf_files(res_type, f"{key}/{dir}")
    shutil.rmtree(f"/terraform/datadog/{res_type}/{key}/")


if __name__ == "__main__":
    with open("../conf.yaml", "r") as f:
        config = load(f, Loader=Loader)

    migratable = NESTED_RESOURCES + OTHER_RESOURCES

    to_migrate = {
        key: val
        for resource_conf in config["resources"]
        for key, val in resource_conf.items()
        if key in migratable and val
    }

    tf_directories = sort_config(
        check_path_exists(
            {
                resource_type: [
                    conf_key for conf in configs for conf_key, _ in conf.items()
                ]
                for resource_type, configs in to_migrate.items()
            }
        )
    )

    for resource_type in tf_directories.keys():
        if len(resource_dir := tf_directories.get(resource_type)) == 1:
            if "tagsets" in resource_dir:
                process_tagset_init(resource_type, "tagsets")
            else:
                copy_and_del(
                    f"/terraform/datadog/{resource_type}/{resource_dir[0]}/",
                    f"/terraform/datadog/{resource_type}",
                )
        else:
            resource_dirs = tf_directories.get(resource_type)
            if resource_type == "integration_slack_channel":
                process_tagset_init(resource_type, resource_dirs.pop(0))
            else:
                file_destination_source = (
                    f"/terraform/datadog/{resource_type}/{resource_dirs.pop(0)}/"
                )

                copy_and_del(
                    file_destination_source, f"/terraform/datadog/{resource_type}"
                )
            for res_dir in resource_dirs:
                if res_dir == "tagsets" or "slack" in res_dir:
                    dirs = os.listdir(f"/terraform/datadog/{resource_type}/{res_dir}")
                    for dir in dirs:
                        state_move(resource_type, f"{res_dir}/{dir}")
                        combine_tf_files(resource_type, f"{res_dir}/{dir}")
                        shutil.rmtree(
                            f"/terraform/datadog/{resource_type}/{res_dir}/{dir}"
                        )
                else:
                    state_move(resource_type, res_dir)
                    combine_tf_files(resource_type, res_dir)
                shutil.rmtree(f"/terraform/datadog/{resource_type}/{res_dir}/")

    for f in glob.glob("/terraform/datadog/**/terraform.tfstate"):
        with open(f, "r") as tfstate:
            tf_json = json.load(tfstate)
        tf_json["outputs"] = {}
        with open(f, "w") as tfstate:
            json.dump(tf_json, tfstate, indent=4)

    for f in glob.glob("/terraform/datadog/**/outputs.tf"):
        os.remove(f)

    for f in glob.glob("/terraform/datadog/**/provider.tf"):
        with open(f, "w") as provider:
            provider.write(
                """
terraform {
    required_providers {
        datadog = {
            source = "DataDog/datadog"
            version = "= 3.34.0"
        }
    }
}"""
            )
