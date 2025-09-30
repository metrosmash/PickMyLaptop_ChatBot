# Importing the libraries
from google import genai
from google.genai import types
import streamlit as st
import mysql.connector
#from Backend import init_chat_history, gemini_agent_setup
from frontend import streamlit_ui
import pandas as pd
from typing import List, Dict
from langchain_core.messages import HumanMessage
from langchain_core.messages import ToolMessage

from Backend import init_state, ChatState, agent_app, get_db_connection


# Streamlit UI
streamlit_ui()


# --- Initialize agent memory ---
if "agent_state" not in st.session_state:
    st.session_state.agent_state = init_state()

# # --- Initialize chat history ---
if "messages" not in st.session_state.agent_state:
    st.session_state.agent_state["messages"] = []

# --- Initialize database connection---
# if "db_conn" not in st.session_state:
#     st.session_state = get_db_connection()
if "db_conn" not in st.session_state or not st.session_state.db_conn.is_connected():
    try:
        st.session_state.db_conn = get_db_connection()
    except RuntimeError:
        st.stop()  # stop the app gracefully if connection fails


# --Close the Database Conection --
# this will close the database connection on close of the app
# if "db_conn" in st.session_state:
#     st.session_state.db_conn.close()



# Display past messages
for msg in st.session_state.agent_state["messages"]:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

# Input box
if user_input := st.chat_input("What laptop do you wish to get...."):
    # User message
    st.session_state.agent_state["messages"].append(HumanMessage(content=user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Run agent backend
    result = agent_app.invoke({
        **st.session_state.agent_state,
        "messages": st.session_state.agent_state.get("messages", []),
        "finished": st.session_state.agent_state.get("finished", False),
        "tool_in_use": st.session_state.agent_state.get("tool_in_use", False)
    })



    # Update agent state (memory)
    st.session_state.agent_state.update(result)

    # Get the latest AI response
    ai_response = st.session_state.agent_state["messages"][-1].content

    # Display it
    with st.chat_message("assistant"):
        st.markdown(ai_response)

## i have to rework the whole relationship between the add messages and the ai agent 
