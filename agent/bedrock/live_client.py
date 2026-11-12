"""Create a Bedrock Runtime client using temporary IAM role credentials."""

import boto3


DEFAULT_REGION = "us-east-1"


def create_live_bedrock_client(
    profile_name: str,
    role_arn: str,
    region_name: str = DEFAULT_REGION,
):
    """Assume an IAM role and initialize a Bedrock Runtime client."""

    base_session = boto3.Session(
        profile_name=profile_name,
        region_name=region_name,
    )

    sts = base_session.client("sts")

    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="maintenance-ops-live",
    )

    credentials = response["Credentials"]

    assumed_session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=region_name,
    )

    return assumed_session.client("bedrock-runtime")
