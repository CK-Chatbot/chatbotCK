import os
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.storage.chat_store.dynamodb.base import DynamoDBChatStore



messages = [
    ChatMessage(role=MessageRole.USER, content="Who are you?"),
    ChatMessage(
        role=MessageRole.ASSISTANT, content="I am your helpful AI assistant."
    ),
]

class ChatHistory:
    # Initializing a chat history with a key of "SessionID"
    def __init__(self, session_id):
        self.session_id = session_id
        self.chat_store = DynamoDBChatStore(
            table_name="EXAMPLE_TABLE")
    def getSessionId(self):
        return self.session_id
    # Getting the history with a key of "SessionID"
    def get_messages(self):
        return self.chat_store.get_messages(key=self.session_id)
    
    # Setting the history with a key of "SessionID"
    def set_messages(self, messages):
        self.chat_store.set_messages(key=self.session_id, messages=messages)

    # Adding a message to the history with a key of "SessionID"
    def add_message(self, message):
        if not self.chat_store.get_messages(key=self.session_id):
            self.chat_store.set_messages(key=self.session_id, messages=[message])
        self.chat_store.add_message(key=self.session_id, message=message)
    
    def get_keys(self):
        return self.chat_store.get_keys()
    
    def delete_key(self, key):
        self.chat_store.delete_message(key)
    


       
    




# Appending a message to an existing chat history
message = ChatMessage(role=MessageRole.USER, content="What can you do?")

# print(chat_store.get_messages("123"))
