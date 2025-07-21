# Importing the libraries
from google import genai
from google.genai import types
import streamlit as st
import mysql.connector
from Backend import query_sql_database
from frontend import streamlit_ui
import pandas as pd
from typing import List, Dict

# Config and Secrets
# Retrieve credentials from Streamlit secrets

db_username = st.secrets["DB_username"]
db_password = st.secrets["DB_password"]
Gemini_Api_key = st.secrets["API_key"]



# Setting the Bot prompt
with open("Bot_prompt1.txt", "r") as f:
    BOT_PROMPT = f.read()


# Streamlit UI
streamlit_ui()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "Gemini_model" not in st.session_state:
    st.session_state["Gemini_model"] = "gemini-2.0-flash"


# Memory Setup
def get_conversation_memory():
    """
    Returns previous user-agent message pairs as formatted string.
    """

    context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    return context


# Gemini Agent Setup
assistant_function = [
    query_sql_database, get_conversation_memory
]

client = genai.Client(api_key=Gemini_Api_key)
chat = client.chats.create(
    model=st.session_state["Gemini_model"],
    config=types.GenerateContentConfig(
        tools=assistant_function,
        system_instruction=BOT_PROMPT
    ),
)

# Chat Logic

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What can i do for you - "):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    response = chat.send_message(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response.text)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response.text})
