# agent.py

import os
import json
import streamlit as st
from typing import Dict, Any, List
from langgraph.graph import StateGraph
from langchain_google_genai import GoogleGenerativeAI

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


from langgraph.graph import StateGraph, END
from typing import TypedDict, List

from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_core.messages.ai import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI


# Setting up the Api keys
db_username = st.secrets["DB_username"]
db_password = st.secrets["DB_password"]
Gemini_Api_key = st.secrets["API_key"]
# this GOOGlE_API_KEY  for the current python session
os.environ["GOOGLE_API_KEY"] = Gemini_Api_key


# Define the bot prompt

laptop_chatbot = (
    "system",
    "You are a helpful, knowledgeable, and friendly Laptop Sales Assistant. "
    "Your goal is to help users find the best laptops based on their needs, preferences, and budget. "
    "You have access to an SQL database containing laptop specifications, prices, and descriptions, "
    "as well as three tools to assist your searches: "
    "`attribute_search` (search laptops by a specific column and value), "
    "`specific_search` (search laptops by a keyword in brand, description, or processor), "
    "and `range_search` (search laptops by numeric attributes within a specified range). "
    "Use these tools and the database to give accurate, helpful recommendations.\n\n"
    "Always ask clarifying questions if the user's request is vague or missing important details "
    "(e.g., budget, intended use, preferred brands, etc.). "
    "Provide concise, clear advice that balances performance and value for money. "
    "If multiple laptops match the request, suggest the top 2–3 options with brief explanations. "
    "Do not make up data—rely only on the information provided via the SQL database or tools. "
    "If no match is found, kindly inform the user and suggest alternatives. "
    "Respond in a warm and helpful tone, like a tech-savvy friend who wants the best for the user."
)

Welcome_msg = "Hello, What can i do for you" # just for now i will change it later

# --- Define the state ---

class ChatState(TypedDict):
    """State representing the customer's Laptop conversation."""

    # The chat conversation. This preserves the conversation history
    # between nodes. The `add_messages` annotation indicates to LangGraph
    # that state is updated by appending returned messages, not replacing
    # them.
    messages: Annotated[list, add_messages]

    # The customer's specifics of laptop.
    chat: list[str]

    # This Flag helps end the conversation with the llm
    finished: bool
    # This Flag helps indicate to the human node that the tool is in use
    tool_in_use: bool


# --- Define chatbot node ---

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

#tools = [get_attribute_search_tool, get_specific_search_tool, get_range_search_tool]


def chatbot_with_welcome_msg(state: ChatState) -> ChatState:
    """The chatbot itself. A wrapper around the model's own chat interface."""
    #llm_with_tools = llm.bind_tools(tools)

    if state["messages"]:
        # If there are messages, continue the conversation with the Gemini model.
        new_output = llm.invoke([laptop_chatbot] + state["messages"])
    else:
        # If there are no messages, start with the welcome message.
        new_output = AIMessage(content=Welcome_msg)

    return state | {"messages": [new_output]}



# --- Build graph ---
graph = StateGraph(ChatState)
graph.add_node("chatbot", chatbot_with_welcome_msg)
graph.set_entry_point("chatbot")
graph.set_finish_point("chatbot")

agent_app = graph.compile()

# --- Exposed functions for frontend ---
def init_state() -> Dict[str, Any]:
    """Initialize memory state."""
    return {"history": []}

def run_agent(state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    """Run the agent with given state + user input."""
    result = agent_app.invoke({"input": user_input, **state})
    return {"output": result["output"], "history": result["history"]}
