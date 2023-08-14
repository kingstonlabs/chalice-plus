import json
import shutil
import os

from functools import cache

from chalice_plus.deploy_utils.ssm import get_ssm_parameter

CONFIG_PATH = ".chalice/config.json"


@cache
def load_config():
    with open(CONFIG_PATH) as config_file:
        config_contents = config_file.read()

    return json.loads(config_contents)


def load_ssm_parameters_to_config(stage):
    config = load_config()
    app_name = config.get("app_name")

    for parameter_name in config.get("ssm_parameters", []):
        parameter_value = get_ssm_parameter(app_name, stage, parameter_name)
        config["stages"][stage]["environment_variables"][parameter_name] = parameter_value

    shutil.copy2(CONFIG_PATH, f"{CONFIG_PATH}.bak")

    with open(CONFIG_PATH, "w") as config_file:
        config_file.write(json.dumps(config, indent=2))


def restore_config():
    os.replace(f"{CONFIG_PATH}.bak", CONFIG_PATH)


def get_app_name():
    config = load_config()
    return config.get("app_name")
