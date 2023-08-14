import boto3

from functools import cache


@cache
def get_ssm_client(region_name=None):
    return boto3.client('ssm', region_name=region_name)


@cache
def get_ssm_parameter(app_name, stage, parameter_name):
    ssm_client = get_ssm_client()
    response = ssm_client.get_parameter(Name=f"{app_name}.{stage}.{parameter_name}")
    return response.get("Parameter", {}).get("Value")
