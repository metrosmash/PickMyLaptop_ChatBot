# agent.py

import os
import json
import streamlit as st
from typing import Dict, Any, List
import mysql.connector
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

# for the tools
from pydantic import BaseModel, Field
from langchain_core.tools import tool


# Setting up the Api keys
db_username = st.secrets["DB_username"]
db_password = st.secrets["DB_password"]
Gemini_Api_key = st.secrets["API_key"]
# this GOOGlE_API_KEY  for the current python session
os.environ["GOOGLE_API_KEY"] = Gemini_Api_key


# Define the Bot prompt
with open("bot_promptv1.txt", "r") as f:
    laptop_chatbot = f.read()

Welcome_msg = "Hello, What can i do for you"  # just for now i will change it later


# --- Define the state ---

class ChatState(TypedDict):
    """State representing the customer's Laptop conversation."""

    # The chat conversation. This preserves the conversation history
    # between nodes. The `add_messages` annotation indicates to LangGraph
    # that state is updated by appending returned messages, not replacing
    # them.
    messages: Annotated[list, add_messages]

    # This Flag helps indicate to the human node that the tool is in use
    tool_in_use: bool


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="db4free.net",
            user=db_username,
            password=db_password,
            database="metro_laptop",
            connection_timeout=10  # ⏱ optional safety timeout
        )
        if conn.is_connected():
            return conn
        else:
            raise ConnectionError(" Could not connect to the database")
    except mysql.connector.Error as e:
        # return {"error": f"MySQL error: {e}"}
        st.error(f"❌ Failed to connect to MySQL: {e}")
        raise ConnectionError(f"MySQL connection error: {e}")






def query_sql_database(query: str, values=None):
    """
    Execute a SQL query using a persistent connection.

    - query: SQL string with %s placeholders
    - values: None, a single value, or a tuple/list of multiple values
    - returns: list of dict rows or error dict
    """
    conn = st.session_state.db_conn  # ✅ use the persistent connection

    try:
        with conn.cursor() as cursor:
            # ✅ Convert single value to tuple if needed
            if values is not None:
                if not isinstance(values, (tuple, list)):
                    values = (values,)
                cursor.execute(query, values)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in results]

    except mysql.connector.Error as e:
        # ✅ Try to reconnect once if connection dropped
        if not conn.is_connected():
            st.session_state.db_conn = get_db_connection()
            return query_sql_database(query, values)
        return {"error": f"MySQL error: {e}"}


# Setting up the tools that will be used
# Search by a common attribute
class Attribute_search(BaseModel):
    attribute: str = Field(description = "column of the database to search")
    value: object = Field(description = "the value to search for " )


def attribute_search(attribute: str, value: object)-> dict:
    """
    Search laptops where a specific column matches a given value.
    Example: search_by_attribute("Brand", "Dell")
    """
    ALLOWED_COLUMNS = {"id", "Brand", "Product_Description", "Screen_Size", "RAM", "Processor",
                       "GPU", "GPU_Type", "Resolution", "Condition", "Price", "SSD", "HDD"}
    if attribute not in ALLOWED_COLUMNS:
        raise ValueError("Invalid attribute name")

    query = f"SELECT * FROM `laptop_dataset` WHERE LOWER(`{attribute}`) LIKE %s LIMIT 10;"
    like_value = f"%{value.lower()}%"

    # cursor.execute(query, (value,))
    # return cursor.fetchall()
    return query_sql_database(query, value)


#  Search for a specific laptop (by name or description)
class SpecificSearch(BaseModel):
    keyword: object = Field(description = "specific keyword to search for on the database ")



def search_specific_laptop(keyword: object)-> dict:
    """
    Search for a laptop by brand, product description, or processor containing the keyword.
    Example: search_specific_laptop("MacBook")
    """
    query = """SELECT * FROM `laptop_dataset` WHERE Brand LIKE %s OR Product_Description LIKE %s OR Processor LIKE %s OR 
    Screen_Size LIKE %s OR RAM LIKE %s OR GPU LIKE %s OR GPU_Type LIKE %s OR Condition Like %s LIMIT 10"""

    keyword = f"'%{keyword}%'"  # Partial match
    query_sql_database(query, (keyword, keyword, keyword, keyword, keyword, keyword, keyword, keyword))
    # cursor.execute(query, (keyword, keyword, keyword, keyword, keyword, keyword, keyword, keyword))
    # return cursor.fetchall()


## Log of what to do next
'''
1.)Check the ⏳ Let me check the database for you, please wait...
its not syncing with the data
2.)the specific search tool is not working work on it 
add the database  
3.)add the remaining tools when done 
'''
@tool(args_schema=Attribute_search)
def get_attribute_search_tool(attribute: str, value: object) -> dict:
    """
    Search laptops where a specific column matches a given value.
    Example: search_by_attribute("Brand", "Dell")
    """
    return attribute_search(attribute, value)

@tool(args_schema= SpecificSearch)
def get_specific_search_tool(keyword: object)-> dict:
    """
    Search for a laptop by brand, product description, or processor containing the keyword.
    Example: search_specific_laptop("MacBook")
    """
    return search_specific_laptop(keyword)


# add sql capabilities here
"""
I will need to revamp the sql capabilities of the tools 
like on the kaggle notebook all i had to do was keep the cursor open
but now i need to open it anytime the AI is using a tool 

"""

# Setting up the tool Node
class BasicToolNode():
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        tool_outputs = []

        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            tool_outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            # Convert tool result into an AIMessage instead of ToolMessage
            # tool_outputs.append(
            #     AIMessage(
            #         content=f"Here are the results from **{tool_call['name']}**:\n{json.dumps(tool_result, indent=2)}"
            #     )
            # )
        # return {"messages": state["messages"] + tool_outputs}
        return {"messages": tool_outputs}


def route_tools(
        state: ChatState,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:

        if not ai_message.content:
            ai_message.content = "⏳ Let me check the database for you, please wait..."
        state["tool_in_use"] = True
        return "tools"
    return END


# --- Define chatbot node ---

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

#tools = [get_attribute_search_tool, get_specific_search_tool, get_range_search_tool]
tools = [get_attribute_search_tool, get_specific_search_tool]

def chatbot_with_welcome_msg(state: ChatState) -> ChatState:
    """The chatbot itself. A wrapper around the model's own chat interface."""
    llm_with_tools = llm.bind_tools(tools)

    if state["messages"]:
        # If there are messages, continue the conversation with the Gemini model.
        new_output = llm_with_tools.invoke([laptop_chatbot] + state["messages"])
        # new_output = llm.invoke([laptop_chatbot] + state["messages"])
    else:
        # If there are no messages, start with the welcome message.
        new_output = AIMessage(content=Welcome_msg)

    return state | {"messages": [new_output]}


# --- Build graph ---
graph = StateGraph(ChatState)
tool_node = BasicToolNode(tools=tools)

graph.add_node("chatbot", chatbot_with_welcome_msg)
graph.add_node("tools", tool_node)
graph.set_entry_point("chatbot")

graph.add_conditional_edges(
    "chatbot",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", END: END},
)
graph.set_finish_point("chatbot")

agent_app = graph.compile()

# --- Exposed functions for frontend ---
def init_state() -> Dict[str, Any]:
    """Initialize memory state."""
    return {"messages": [],
            "finished": False,
            "tool_in_use": False}

