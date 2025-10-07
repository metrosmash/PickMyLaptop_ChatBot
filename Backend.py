# agent.py

import os
import json
import streamlit as st
from typing import Dict, Any
import mysql.connector
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from typing import TypedDict
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
with open("bot_prompt.txt", "r") as f:
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
    query_type: str
    tool_context: []


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
        st.error(f"Failed to connect to MySQL: {e}")
        raise ConnectionError(f"MySQL connection error: {e}")






def query_sql_database(query: str, state: Dict = None, values=None):
    """
    Execute a SQL query using a persistent connection.

    - query: SQL string with %s placeholders
    - values: None, a single value, or a tuple/list of multiple values
    - returns: list of dict rows or error dict
    :type state: object
    """
    conn = st.session_state.db_conn  # use the persistent connection
    query_type = state.get("query_type") if state else "use_value"

    try:
        with conn.cursor() as cursor:
            # Convert single value to tuple if needed
            if query_type == "use_value":
                if not isinstance(values, (tuple, list)):
                    values = (values,)
                cursor.execute(query, values)

            elif query_type == "use_keyword":
                # Keyword searches may require multiple placeholders
                if not isinstance(values, (tuple, list)):
                    values = tuple([values] * query.count("%s"))
                cursor.execute(query, values)

            elif query_type == "use_range":
                # Handle BETWEEN queries
                cursor.execute(query, values)
            # if values is not None:
            #     if not isinstance(values, (tuple, list)):
            #         values = (values,)
            #     cursor.execute(query, values)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in results]

    except mysql.connector.Error as e:
        # Try to reconnect once if connection dropped
        if not conn.is_connected():
            st.session_state.db_conn = get_db_connection()
            return query_sql_database(query, values, state)
        return {"error": f"MySQL error: {e}"}


# Setting up the tools that will be used
# Search by a common attribute
class AttributeSearch(BaseModel):
    attribute: str = Field(description="column of the database to search")
    value: object = Field(description="the value to search for ")


def attribute_search(attribute: str, value: object, state=None) -> dict:
    """
    Search laptops where a specific column matches a given value.
    Example: search_by_attribute("Brand", "Dell")
    """
    ALLOWED_COLUMNS = {"id", "Brand", "Product_Description", "Screen_Size", "RAM", "Processor",
                       "GPU", "GPU_Type", "Resolution", "Condition1", "Price", "SSD", "HDD"}
    if attribute not in ALLOWED_COLUMNS:
        raise ValueError("Invalid attribute name")

    query = f"SELECT * FROM `laptop_dataset` WHERE LOWER(`{attribute}`) LIKE %s LIMIT 10;"
    like_value = f"%{value.lower()}%"

    # Set query type dynamically
    if state is not None:
        state["query_type"] = "use_value"
    return query_sql_database(query, state, value)


#  Search for a specific laptop (by name or description)
class SpecificSearch(BaseModel):
    keyword: object = Field(description = "specific keyword to search for on the database ")



def search_specific_laptop(keyword: object,  state=None)-> dict:
    """
    Search for a laptop by brand, product description, or processor containing the keyword.
    Example: search_specific_laptop("MacBook")
    """
    query = """SELECT * FROM `laptop_dataset` 
    WHERE Brand LIKE %s OR Product_Description LIKE %s OR Processor LIKE %s OR Screen_Size LIKE %s OR RAM LIKE %s OR 
    GPU LIKE %s OR GPU_Type LIKE %s OR Condition1 Like %s LIMIT 10"""

    keyword = f"%{keyword}%"  # Partial match
    if state is not None:
        state["query_type"] = "use_keyword"

    # return query_sql_database(query, state, keyword)
    # Correct order of parameters: query, query_type, values
    return query_sql_database(
        query=query,
        state = state,
        values=(keyword, keyword, keyword, keyword, keyword, keyword, keyword, keyword)
    )



#  Search by range of common attributes
class RangeSearch(BaseModel):
    attribute: str = Field(description = "column in the database which will be searched using range of min - max")
    min_value: int = Field(description = "the minimum value in the range of search")
    max_value: int = Field(description = "the maximum value in the range of search")



def search_by_range(attribute: str, min_value: int, max_value: int, state=None)-> dict:
    """
    Search Laptop where a numeric attribute falls between two values.
    Example: search_by_range("Price", 500, 1000)
    """

    allowed_columns = {"id", "Brand", "Product_Description", "Screen_Size", "RAM", "Processor",
                       "GPU", "GPU_Type", "Resolution", "Condition1", "Price", "SSD", "HDD"}

    if attribute not in allowed_columns:
        raise ValueError("Invalid attribute name")

    query = f"SELECT * FROM `laptop_dataset` WHERE {attribute} BETWEEN %s AND %s LIMIT 10"

    if state is not None:
        state["query_type"] = "use_range"

    return query_sql_database(query, state, values = (min_value, max_value))



class AttributeRangeSearch(BaseModel):
    attribute: str = Field(description="The column name to match (e.g., Brand, GPU)")
    value: str = Field(description="The value to search for (e.g., Dell)")
    range_column: str = Field(description="The numeric column to filter by (e.g., Price, RAM)")
    min_value: int = Field(description="Minimum value for the range filter")
    max_value: int = Field(description="Maximum value for the range filter")

def attribute_range_search(
    attribute: str,
    value: str,
    range_column: str,
    min_value: int,
    max_value: int,
    state=None
) -> dict:

    """
    Search laptops where a specific attribute matches a value AND a numeric column falls within a range.
    Example:
        attribute_range_search(
            attribute="Brand", value="Dell",
            range_column="Price", min_value=100, max_value=500
        )
    """
    # 1. Validate inputs
    allowed_text_columns = {"Brand", "Product_Description", "Processor", "Condition", "GPU", "GPU_Type"}
    allowed_numeric_columns = {"Price", "RAM", "SSD", "HDD", "Screen_Size"}

    if attribute not in allowed_text_columns:
        raise ValueError(f"Invalid text column: {attribute}")
    if range_column not in allowed_numeric_columns:
        raise ValueError(f"Invalid numeric column: {range_column}")

    # 2. Build the query
    query = f"""
    SELECT * FROM `laptop_dataset`
    WHERE LOWER(`{attribute}`) LIKE %s
    AND `{range_column}` BETWEEN %s AND %s
    LIMIT 10;
    """

    # 3. Prepare values
    like_value = f"%{value.lower()}%"
    values = (like_value, min_value, max_value)

    # 4. Mark query type in state (optional)
    if state is not None:
        state["query_type"] = "specific_range"

    # 5.Execute
    return query_sql_database(query, state = state, values=values)



@tool(args_schema=AttributeSearch)
def get_attribute_search_tool(attribute: str, value: object, state=None) -> dict:
    """
    Search laptops where a specific column matches a given value.
    Example: search_by_attribute("Brand", "Dell")
    """
    return attribute_search(attribute, value, state=state)

@tool(args_schema= SpecificSearch)
def get_specific_search_tool(keyword: object, state=None)-> dict:
    """
    Search for a laptop by brand, product description, or processor containing the keyword.
    Example: search_specific_laptop("MacBook")
    """
    return search_specific_laptop(keyword, state=state)

@tool(args_schema= RangeSearch)
def get_range_search_tool(attribute: str, min_value: int, max_value: int, state=None) -> dict:
    """
    Search Laptop where a numeric attribute falls between two values.
    Example: search_by_range("Price", 500, 1000)
    """
    return search_by_range(attribute, min_value, max_value, state=state)

@tool(args_schema= AttributeRangeSearch)
def get_attribute_range_search(
    attribute: str,
    value: str,
    range_column: str,
    min_value: int,
    max_value: int,
    state=None
) -> dict:
    """
      Search laptops where a text attribute matches and a numeric column is within a range.
    """

    return attribute_range_search(
        attribute, value, range_column, min_value, max_value, state
    )


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

        # Ensure the list exists
        if "tool_context" not in inputs:
            inputs["tool_context"] = []

        for tool_call in message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_result = self.tools_by_name[tool_name].invoke(tool_args)

            # ✅ Store a structured record
            inputs["tool_context"].append({
                "tool": tool_name,
                "args": tool_args,
                "result": tool_result
            })

            return inputs


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

tools = [get_attribute_search_tool, get_specific_search_tool, get_range_search_tool, get_attribute_range_search]





def chatbot_with_welcome_msg(state: ChatState) -> ChatState:
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = laptop_chatbot

    # Add tool context if available
    if state.get("tool_context"):
        context_summary = "\n\n[Tool Results So Far:]\n"
        for idx, ctx in enumerate(state["tool_context"], 1):
            context_summary += (
                f"\nTool {idx}: {ctx['tool']}\n"
                f"Args: {json.dumps(ctx['args'], indent=2)}\n"
                f"Result: {json.dumps(ctx['result'], indent=2)}\n"
            )
        system_prompt += context_summary

    if state["messages"]:
        new_output = llm_with_tools.invoke([system_prompt] + state["messages"])
    else:
        new_output = AIMessage(content=Welcome_msg)

    # Optionally reset or keep tool_context
    # state["tool_context"] = []  # clear if you only want the latest
    # (Or keep it if you want accumulated memory of all tools)

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
            "tool_in_use": False,
            "tool_context": []}

