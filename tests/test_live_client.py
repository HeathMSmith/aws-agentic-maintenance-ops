"""Tests for the live Bedrock Runtime client factory."""

from unittest.mock import MagicMock, patch

from agent.bedrock.live_client import create_live_bedrock_client


def test_create_live_bedrock_client():
    """Create a Bedrock client using credentials from an assumed role."""

    credentials = {
        "AccessKeyId": "test-access-key",
        "SecretAccessKey": "test-secret-key",
        "SessionToken": "test-session-token",
    }

    sts_client = MagicMock()
    sts_client.assume_role.return_value = {
        "Credentials": credentials,
    }

    base_session = MagicMock()
    base_session.client.return_value = sts_client

    assumed_session = MagicMock()
    bedrock_client = MagicMock()
    assumed_session.client.return_value = bedrock_client

    with patch(
        "agent.bedrock.live_client.boto3.Session",
        side_effect=[base_session, assumed_session],
    ) as mock_session:
        result = create_live_bedrock_client(
            profile_name="portfolio",
            role_arn="arn:aws:iam::123456789012:role/test-role",
        )

    mock_session.assert_any_call(
        profile_name="portfolio",
        region_name="us-east-1",
    )

    sts_client.assume_role.assert_called_once_with(
        RoleArn="arn:aws:iam::123456789012:role/test-role",
        RoleSessionName="maintenance-ops-live",
    )

    mock_session.assert_any_call(
        aws_access_key_id="test-access-key",
        aws_secret_access_key="test-secret-key",
        aws_session_token="test-session-token",
        region_name="us-east-1",
    )

    assumed_session.client.assert_called_once_with("bedrock-runtime")

    assert result is bedrock_client
