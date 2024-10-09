#!/usr/bin/env python3
import os

import aws_cdk as cdk

from chatbot_ck.Bedrock_stack import BedrockStack
from chatbot_ck.streamlit_stack import StreamlitStack
from aws_cdk import (
    Fn
)
app = cdk.App()
env = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
                        region=os.getenv('CDK_DEFAULT_REGION'))

bedrock_stack=BedrockStack(app, "BedrockStack"+ os.getenv('SUFFIX',''),env=env)
streamlit_stack=StreamlitStack(app, "StreamlitStack",env=env)
streamlit_stack.add_dependency(bedrock_stack,reason="Create Knowledge Base on Bedrock first")

app.synth()
