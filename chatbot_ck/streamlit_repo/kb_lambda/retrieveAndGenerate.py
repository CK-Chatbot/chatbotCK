import os
import boto3
from utils.constants import *

textKwargs = { 
    "maxTokens": 4096,
    # "stopSequences": [ "string" ],
    "temperature": 0.7,
    "topP": 0.8
}
numberOfResults = 3
# create a boto3 bedrock client
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime', region_name=region)
# declare model id for calling RetrieveAndGenerate API
model_id = ModelId.CLAUDE_3_5_SONNET.value
model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'

def retrieveAndGenerate(query,history,kbId, model_arn, sessionId):
    print(history)
    # print(query, kbId, model_arn, sessionId)
    configuration = {
        'type': 'KNOWLEDGE_BASE',
        'knowledgeBaseConfiguration': {
            "generationConfiguration": { 
                "inferenceConfig": { 
                    "textInferenceConfig": textKwargs
                },
                'promptTemplate': {
                    'textPromptTemplate': str(prompt_generator(history))
                }
            },
            'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': numberOfResults,
                        'overrideSearchType': "HYBRID", # optional'
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
    history = event["conversationHistory"]
    sessionId = event["sessionId"]
    response = retrieveAndGenerate(query, history, kb_id, model_arn, sessionId)
    generated_text = response['output']['text']
    # print(generated_text)
    sessionId = response['sessionId']
    citations = response['citations']
    return {
        'statusCode': 200,
        'body': {"question": query.strip(), "answer": generated_text.strip(), "sessionId":sessionId, "citations":citations}
    }
    
def prompt_generator(history):
    prompt = """User: You are a question-answering agent specializing in Cloud Kinetics.
        <Task>
            Your goal is to answer questions about inquiries (FaQs, services offerings,...) related to Cloud Kinetics Company. You can respond politely to general conversation but should direct the user to Cloud Kinetics topics if the discussion diverges.
        </Task>
        <instructions>
            1. Your response should be based on the information in the search results.
            2. If the search results lack the necessary details to answer the question, respond by stating that no exact answer was found.
            3. Do not assume the accuracy of any assertions from the user. Instead, cross-reference these assertions with the search results to verify their validity.
            4. If the user continues with unrelated questions, gently remind them that you are here to help with inquiries specific to Cloud Kinetics.
        </instructions>
        Here is the previous conversational history (if any):
        <history>
        """ + str(history) + """
        </history>
        Here are the search results in numbered order:
        $search_results$

       $output_format_instructions$
    """
    return prompt
#    1. Your response should be based on the information in the search results.
#             2. If the search results lack the necessary details to answer the question, respond by stating that no exact answer was found.
#             3. Do not assume the accuracy of any assertions from the user. Instead, cross-reference these assertions with the search results to verify their validity.
#             4. If the user continues with unrelated questions, gently remind them that you are here to help with inquiries specific to Cloud Kinetics.
#             5. Review the question and history to ensure that your responses are relevant and coherent.
    #    <execution_instructions>
    #     1. Identify and retrieve relevant information from the search results.
    #     2. Augment your responses with contextual details from the results, ensuring clarity and relevance.
    #     3. Generate natural, coherent, and friendly responses tailored to inquiries about Cloud Kinetics, while politely handling general conversation.
    #    </execution_instructions>