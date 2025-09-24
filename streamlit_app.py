# Importing the libraries
from google import genai
from google.genai import types
import streamlit as st
import mysql.connector
#from Backend import init_chat_history, gemini_agent_setup
from frontend import streamlit_ui
import pandas as pd
from typing import List, Dict

from Backend import init_state, run_agent


#Streamlit UI
streamlit_ui()


# --- Initialize agent memory ---
if "agent_state" not in st.session_state:
    st.session_state.agent_state = {"messages": []}

# # --- Initialize chat history ---
# if "messages" not in st.session_state:
#     st.session_state.messages = []


# Display past messages
for msg in st.session_state.agent_state["messages"]:
    role = "user" if msg.type == "human" else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

# Input box
if prompt := st.chat_input("Say something..."):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run agent backend
    result = run_agent(st.session_state.agent_state, prompt)
    response = result["output"]

    # Update agent state (memory)
    st.session_state.agent_state["messages"] = result["messages"]

    # Assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)


## i have to rework the whole relationship between the add messages and the ai agent 
