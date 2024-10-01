#!/usr/bin/env python3
import os

import aws_cdk as cdk

from chatbot_ck.Bedrock_stack import BedrockStack

app = cdk.App()
env = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
                        region=os.getenv('CDK_DEFAULT_REGION'))

BedrockStack(app, "BedrockStack"+os.getenv('SUFFIX',''),
    env=env
    )

app.synth()
