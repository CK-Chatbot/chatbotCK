from enum import Enum
import os
region = os.getenv("CDK_DEFAULT_REGION")
# get knowledge base id from environment variable
kb_id = os.getenv("KNOWLEDGE_BASE_ID")
account_id = os.getenv("CDK_DEFAULT_ACCOUNT")
# print(region,kb_id,account_id)

class ModelId(str, Enum):
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    CLAUDE_3_5_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    TITAN_EMBED_TEXT_V1 = "amazon.titan-embed-text-v1"
