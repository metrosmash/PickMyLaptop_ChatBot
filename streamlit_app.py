from google import genai
from google.genai import types
import streamlit as st
import mysql.connector
import pandas as pd
import random
import time
import os

import requests
from io import StringIO

# Show title and description.
st.title("PickMyLaptop_Chatbot")

st.write(
    "This is a simple chatbot that uses Gemini flash 2.5 model to help users pick their preferred laptop. "
    "To use this app, you need to provide a Gemini API key, which you can get [here]("
    "https://ai.google.dev/gemini-api/docs/api-key)."
    "You can also learn how to build this app step by step by [following our tutorial]("
    "https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# .streamlit/secrets.toml
# Retrieve credentials from Streamlit secrets

db_username = st.secrets["DB_username"]
db_password = st.secrets["DB_password"]
Gemini_Api_key = st.secrets["API_key"]


def query_sql_database(query: str):
    conn = None
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host="db4free.net",
            user=db_username,
            password=db_password,
            database="metro_laptop"
        )

        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            # Get column names
            columns = [i[0] for i in cursor.description]

            # Return as a DataFrame (or you could return list of dicts)
            df = pd.DataFrame(results, columns=columns)

            return df  # Let the AI agent process the DataFrame

    except mysql.connector.Error as e:
        # Return error message instead of raising
        return {"error": str(e)}

    finally:
        # Always clean up
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()


# result = query_sql_database("SELECT * FROM laptop_dataset LIMIT 5;")
# st.write(result)


# Setting the Bot prompt
with open("bot_prompt.txt", "r") as f:
    BOT_PROMPT = f.read()


# result = query_sql_database("SELECT * FROM laptop_dataset LIMIT 5;")

st.write("👋 Welcome to Laptop assistant Bot!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "Gemini_model" not in st.session_state:
    st.session_state["Gemini_model"] = "gemini-2.0-flash"


def get_conversation_memory():
    """
    Returns previous user-agent message pairs as formatted string.
    """

    context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    return context


assistant_function = [
    query_sql_database, get_conversation_memory
]

model_name = "gemini-2.0-flash"

client = genai.Client(api_key=Gemini_Api_key)


chat = client.chats.create(
    model=model_name,
    config=types.GenerateContentConfig(
        tools=assistant_function,
        system_instruction=BOT_PROMPT
    ),
)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
# Option 1
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



