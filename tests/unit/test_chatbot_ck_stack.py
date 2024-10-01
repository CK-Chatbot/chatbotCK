import aws_cdk as core
import aws_cdk.assertions as assertions

from chatbot_ck.chatbot_ck_stack import ChatbotCkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in chatbot_ck/chatbot_ck_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ChatbotCkStack(app, "chatbot-ck")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
