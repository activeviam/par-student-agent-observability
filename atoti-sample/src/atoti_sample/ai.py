"""Atoti Intelligence configured with Amazon Bedrock.

See https://docs.activeviam.com/atoti-intelligence/6.2/developer-guide/enable-ai-tools/llm/amazon-bedrock-python
"""

from __future__ import annotations

import logging
import os
from typing import Final

from atoti_ai import AiConfig
from atoti_ai_amazon_bedrock import ChatConfig, ConnectionConfig

_LOGGER: Final = logging.getLogger(__name__)

_DEFAULT_AWS_REGION: Final = "eu-west-3"
_DEFAULT_BEDROCK_MODEL: Final = "eu.anthropic.claude-sonnet-4-6"


def create_ai_config() -> AiConfig | None:
    """Return the AI config, or ``None`` when the AWS credentials are not set."""
    if not {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"} <= os.environ.keys():
        _LOGGER.warning(
            "AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY is not set: starting without Atoti Intelligence."
        )
        return None

    connection_config = ConnectionConfig(
        aws_access_key=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        # Only needed for temporary credentials (AWS SSO, assumed role...).
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN") or None,
        aws_region=os.environ.get("AWS_REGION", _DEFAULT_AWS_REGION),
    )
    chat_config = ChatConfig(
        model=os.environ.get("BEDROCK_MODEL", _DEFAULT_BEDROCK_MODEL),
    )
    return AiConfig(connection=connection_config, chat=chat_config)
