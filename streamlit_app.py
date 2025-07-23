# Importing the libraries
from google import genai
from google.genai import types
import streamlit as st
import mysql.connector
from Backend import init_chat_history, gemini_agent_setup
from frontend import streamlit_ui
import pandas as pd
from typing import List, Dict

#Streamlit UI
streamlit_ui()

# Initialize chat history
init_chat_history()

# Gemini Agent Setup
chat = gemini_agent_setup()

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
