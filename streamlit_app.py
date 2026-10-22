# Importing the libraries

import streamlit as st
from frontend import streamlit_ui
import pandas as pd
from typing import List, Dict
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

from Backend import init_state, ChatState, agent_app
from database import health_check
from database.exceptions import DatabaseConnectionError


# Streamlit UI
streamlit_ui()


# --- Initialize agent memory ---
if "agent_state" not in st.session_state:
    st.session_state.agent_state = init_state()

# # --- Initialize chat history ---
if "messages" not in st.session_state.agent_state:
    st.session_state.agent_state["messages"] = []

# --- Verify the database is reachable ---
# No connection is stored in session_state anymore: database/db.py checks one out of
# a shared pool for each query and returns it. Holding one connection per browser
# session is exactly how you exhaust a free-tier host's connection limit.
if not st.session_state.get("db_ready"):
    try:
        info = health_check()
        st.session_state.db_ready = True
        st.session_state.db_version = info.get("version")
    except DatabaseConnectionError as error:
        st.error(f"Database is not reachable: {error}")
        st.stop()  # stop the app gracefully if the DB is down


# Display past messages

# Show only messages intended for the chat UI
for msg in st.session_state.agent_state["messages"]:
    if not isinstance(msg, (HumanMessage, AIMessage)):
        continue

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
