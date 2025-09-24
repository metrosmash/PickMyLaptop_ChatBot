from typing import Annotated
from typing_extensions import TypedDict
from typing import Literal

from pprint import pprint

from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages.ai import AIMessage

#Secret api here

# defining the state of the langgraph
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

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

#Define the sql tools with pydantic
from pydantic import BaseModel, Field


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

    query = f"SELECT * FROM Laptop WHERE {attribute} = ? LIMIT 10"
    cursor.execute(query, (value,))
    return cursor.fetchall()


#  Search for a specific laptop (by name or description)
class SpecificSearch(BaseModel):
    keyword: object = Field(description = "specific keyword to search for on the database ")



def search_specific_laptop(keyword: object)-> dict:
    """
    Search for a laptop by brand, product description, or processor containing the keyword.
    Example: search_specific_laptop("MacBook")
    """
    query = """
    SELECT * FROM Laptop
    WHERE Brand LIKE ? OR Product_Description LIKE ? OR Processor LIKE ? OR Screen_Size LIKE ? OR RAM LIKE ? OR GPU LIKE ? OR GPU_Type LIKE ? OR Condition Like ? LIMIT 10
    """
    keyword = f"%{keyword}%"  # Partial match
    cursor.execute(query, (keyword, keyword, keyword, keyword, keyword, keyword, keyword, keyword))
    return cursor.fetchall()


#  Search by range of common attributes
class RangeSearch(BaseModel):
    attribute: str = Field(description = "column in the database which will be searched using range of min - max")
    min_value: int = Field(description = "the minimum value in the range of search")
    max_value: int = Field(description = "the maximum value in the range of search")



def search_by_range(attribute: str, min_value: int, max_value: int)-> dict:
    """
    Search Laptop where a numeric attribute falls between two values.
    Example: search_by_range("Price", 500, 1000)
    """
    query = f"SELECT * FROM Laptop WHERE {attribute} BETWEEN ? AND ? LIMIT 10"
    cursor.execute(query, (min_value, max_value))
    return cursor.fetchall()

# same with the tools
from langchain_core.tools import tool

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


@tool(args_schema= RangeSearch)
def get_range_search_tool(attribute: str, min_value: int, max_value: int)-> dict:
    """
    Search Laptop where a numeric attribute falls between two values.
    Example: search_by_range("Price", 500, 1000)
    """
    return search_by_range(attribute, min_value, max_value)

#Defining the Chatbot

import json

from langgraph.graph import StateGraph, END
from typing import TypedDict, List

from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

tools = [get_attribute_search_tool, get_specific_search_tool, get_range_search_tool]


def chatbot_with_welcome_msg(state: ChatState) -> ChatState:
    """The chatbot itself. A wrapper around the model's own chat interface."""
    llm_with_tools = llm.bind_tools(tools)

    if state["messages"]:
        # If there are messages, continue the conversation with the Gemini model.
        new_output = llm_with_tools.invoke([laptop_chatbot] + state["messages"])
    else:
        # If there are no messages, start with the welcome message.
        new_output = AIMessage(content=Welcome_msg)

    return state | {"messages": [new_output]}

#Defining the human node

from langchain_core.messages.ai import AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI


# this function works on the instance of flags
# the tool_in_use flag is used to check if the model is calling the tools if so then the user is not asked for input
def human_node(state: ChatState) -> ChatState:
    last_msg = state["messages"][-1]

    # 🚨 If a tool just ran, skip asking the user
    # This uses the defualt - false trick
    """state.get("tool_in_use", False) means:

    “Look up the key "tool_in_use" in state.
    If it exists, return its value.
    If it doesn’t exist, fall back to False.”
    """
    if state.get("tool_in_use", False):
        state["tool_in_use"] = False  # reset for next turn
        return state  # don’t ask user, just continue to model

    print("Model:", last_msg.content)
    user_input = input("User: ")

    # this uses the finished flag to quit the chat when the user inputs ("q","quit", "exit")
    if user_input in {"q", "quit", "exit"}:
        state["finished"] = True

    return state | {"messages": [("user", user_input)]}

#Defining the maybe human maybe exit node function
from pprint import pprint
from typing import Literal
from IPython.display import Image, display

# this function is used to add a conditional edge to the human node for exiting
def maybe_exit_human_node(state: ChatState) -> Literal["chatbot", "__end__"]:
    """Route to the chatbot, unless it looks like the user is exiting."""
    if state.get("finished", False):
        return END
    else:
        return "chatbot"


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

# Compiling the workflow

# Start building a new graph.
graph_builder = StateGraph(ChatState)

tool_node = BasicToolNode(tools=tools)
# Add the chatbot and human nodes to the app graph.
graph_builder.add_node("chatbot", chatbot_with_welcome_msg)
graph_builder.add_node("human", human_node)
graph_builder.add_node("tools", tool_node)

# Start with the chatbot again.
graph_builder.add_edge(START, "chatbot")

# The chatbot will always go to the human next.
graph_builder.add_edge("chatbot", "human");
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", END: END},
)
graph_builder.add_edge("tools", "chatbot")

# add the conditional edge to the maybe exit human node under here

graph_builder.add_conditional_edges("human", maybe_exit_human_node)

chat_with_human_graph = graph_builder.compile()

Image(chat_with_human_graph.get_graph().draw_mermaid_png())

# using the ai to chat



# The default recursion limit for traversing nodes is 25 - setting it higher means
# you can try a more complex order with multiple steps and round-trips (and you
# can chat for longer!)
# config = {"recursion_limit": 100}

# Remember that this will loop forever, unless you input `q`, `quit` or one of the
# other exit terms defined in `human_node`.
# Uncomment this line to execute the graph:
# state = chat_with_human_graph.invoke({"messages": []}, config)

# Things to try:
#  - Just chat! There's no ordering or menu yet.
#  - 'q' to exit.

# pprint(state)

