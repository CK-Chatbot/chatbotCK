import streamlit as st
import boto3
import json
from botocore.exceptions import ClientError
from kb_lambda import retrieveAndGenerate, uploadFile
from utils.constants import *
from chatdb.historyDb import ChatHistory
from llama_index.core.llms import ChatMessage, MessageRole

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "sessionId" not in st.session_state:
        st.session_state.sessionId = ""
    if "selected_session" not in st.session_state:
        st.session_state.selected_session = None

def generate_presigned_url(bucket_uri):
    s3 = boto3.client('s3')
    bucket_name, key = bucket_uri.split('/', 2)[-1].split('/', 1)
    try:
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=3600
        )
        return presigned_url
    except ClientError as e:
        st.error(f"Error generating presigned URL: {e}")

def display_chat_history(messages):
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_citations(citations, answer):
    url_array = []
    for citation in citations:
        display_text = citation['generatedResponsePart']['textResponsePart']['text']
        st.markdown(display_text)
        for reference in citation['retrievedReferences']:
            url_s3 = reference.get('location', {}).get('s3Location', {}).get('uri')
            url_webLocation = reference.get('location', {}).get('webLocation', {}).get('url')
            help_text = reference['content']['text']
            if url_s3:
                url_array.append((generate_presigned_url(url_s3), help_text))
            if url_webLocation:
                url_array.append((url_webLocation, help_text))
    
    if not citations:
        st.markdown(answer)
    
    for i, (url, help_text) in enumerate(url_array):
        st.markdown(f"[Doc link {i+1}]({url})", help=help_text)

def start_new_chat():
    st.session_state.selected_session = None
    st.session_state.messages = []
    st.session_state.sessionId = ""
    st.rerun()

def delete_session(session_id):
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('EXAMPLE_TABLE')
    
    try:
        table.delete_item(
            Key={'SessionId': session_id}
        )
        st.success(f"Session {session_id} deleted successfully!")
        # Clear session state if the deleted session was selected
        if st.session_state.selected_session == session_id:
            st.session_state.selected_session = None
            st.session_state.messages = []
        return True
    except Exception as e:
        st.error(f"Error deleting session: {e}")
        return False

def main():
    st.title("Financial Chatbot using Knowledge Bases for Amazon Bedrock")
    initialize_session_state()
    
    # Create sidebar for session management
    with st.sidebar:
        st.header("Session Management")
        
        # New Chat button at the top of sidebar
        if st.button("➕ New Chat", type="primary", use_container_width=True):
            start_new_chat()
        
        st.divider()  # Visual separator between new chat button and session list
        
        # Initialize ChatHistory for getting all sessions
        chat_history = ChatHistory(session_id="temp")
        all_sessions = chat_history.get_keys()
        
        if all_sessions:
            st.subheader("Available Sessions")
            # Sort sessions with current session at top
            sorted_sessions = sorted(all_sessions, 
                                  key=lambda x: x != st.session_state.selected_session)
            
            for session in sorted_sessions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Highlight current session
                    button_type = "primary" if session == st.session_state.selected_session else "secondary"
                    if st.button(f"Session: {session}", 
                               key=f"select_{session}", 
                               type=button_type,
                               use_container_width=True):
                        st.session_state.selected_session = session
                        history = ChatHistory(session_id=session)
                        messages = history.get_messages()
                        if messages:
                            st.session_state.messages = [
                                {"role": msg.role.value, "content": msg.content}
                                for msg in messages
                            ]
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_{session}"):
                        if delete_session(session):
                            st.rerun()
        else:
            st.info("No active sessions found")

    # Main chat interface
    if st.session_state.selected_session:
        st.info(f"Current Session: {st.session_state.selected_session}")
    
    # Display chat history
    display_chat_history(st.session_state.messages)

    # Chat input
    if prompt := st.chat_input("What is up?"):
        question = prompt
        st.chat_message("user").markdown(question)
        
        payload = {
            "question": prompt,
            "sessionId": st.session_state.selected_session or "",
            "conversationHistory": st.session_state.messages
        }
        
        result = retrieveAndGenerate.lambda_handler(event=payload, context=None)
        answer = result['body']['answer']
        sessionId = result['body']['sessionId']
        citations = result['body']['citations']
        
        # Handle the sessionId from response
        if not st.session_state.selected_session:
            st.session_state.selected_session = sessionId
            st.session_state.sessionId = sessionId
        
        history = ChatHistory(session_id=st.session_state.selected_session)

        # Add user message
        st.session_state.messages.append({"role": "user", "content": question})
        history.add_message(ChatMessage(role=MessageRole.USER, content=question))

        # Display assistant response
        with st.chat_message("assistant"):
            handle_citations(citations, answer)
            st.feedback(options="thumbs")
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": answer})
            history.add_message(ChatMessage(role=MessageRole.ASSISTANT, content=answer))

if __name__ == "__main__":
    main()
