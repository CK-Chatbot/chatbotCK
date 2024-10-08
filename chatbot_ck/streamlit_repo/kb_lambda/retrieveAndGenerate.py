import os
import boto3
from utils.constants import *

textKwargs = { 
    "maxTokens": 2048,
    # "stopSequences": [ "string" ],
    "temperature": 0.7,
    "topP": 0.8
}
# create a boto3 bedrock client
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime', region_name=region)
# declare model id for calling RetrieveAndGenerate API
model_id = ModelId.CLAUDE_3_5_SONNET.value
model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'

def retrieveAndGenerate(query, kbId, model_arn, sessionId):
    # print(query, kbId, model_arn, sessionId)
    configuration = {
        'type': 'KNOWLEDGE_BASE',
        'knowledgeBaseConfiguration': {
            "generationConfiguration": { 
                "inferenceConfig": { 
                    "textInferenceConfig": textKwargs
                }
            },
            'knowledgeBaseId': kbId,
            'modelArn': model_arn
        }
    }
    if sessionId != "":
        return bedrock_agent_runtime_client.retrieve_and_generate(
            input={
                'text': query
            },
            retrieveAndGenerateConfiguration= configuration,
            sessionId=sessionId
        )
    else:
        return bedrock_agent_runtime_client.retrieve_and_generate(
            input={
                'text': query
            },
            retrieveAndGenerateConfiguration= configuration
        )

def lambda_handler(event, context):
    query = event["question"]
    sessionId = event["sessionId"]
    response = retrieveAndGenerate(query, kb_id, model_arn, sessionId)
    generated_text = response['output']['text']
    # print(generated_text)
    sessionId = response['sessionId']
    citations = response['citations']
    return {
        'statusCode': 200,
        'body': {"question": query.strip(), "answer": generated_text.strip(), "sessionId":sessionId, "citations":citations}
    }
    
