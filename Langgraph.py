from typing import Annotated
from typing_extensions import TypedDict
from typing import Literal

from pprint import pprint

from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages.ai import AIMessage


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]

    # The customer's specifics of laptop.
    chat: list[str]


laptop_chatbot = (
    "system",
    "You are a helpful, knowledgeable, and friendly Laptop Sales Assistant."
    "Your goal is to help users find the best laptops based on their needs, preferences, and budget."
    "You have access to an SQL database containing laptop specifications, prices, and descriptions."
    "Use this information to give accurate, helpful recommendations."
    "\n\n"
    "Always ask clarifying questions if the user's request is vague or "
    "missing important details (e.g., budget, intended use, preferred brands, etc.)."
    "Provide concise, clear advice that balances performance and value for money."
    "If multiple laptops match the request, suggest the top 2–3 options with brief explanations."
    "Do not make up data—rely only on the information provided via the SQL database or tools."
    "If no match is found, kindly inform the user and suggest alternatives."
    "Respond in a warm and helpful tone, like a tech-savvy friend who wants the best for the user"

)

Welcome_msg = "Hello, What can i do for you" # just for now i will change it later

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Define your chatbot
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")


def human_node(state: ChatState) -> ChatState:
    """Display the last model message to the user, and receive the user's input."""
    last_msg = state["messages"][-1]
    print("Model:", last_msg.content)

    user_input = input("User: ")
    # If it looks like the user is trying to quit, flag the conversation
    # as over.
    if user_input in {"q", "quit", "exit", "goodbye"}:
        state["finished"] = True

    return state | {"messages": [("user", user_input)]}

def chatbot_with_welcome_msg(state: ChatState) -> ChatState:
    """The chatbot itself. A wrapper around the model's own chat interface."""
    if state["messages"]:
        # If there are messages, continue the conversation with the Gemini model.
        new_output = llm.invoke([laptop_chatbot] + state["messages"])
    else:
        # If there are no messages, start with the welcome message.
        new_output = AIMessage(content=Welcome_msg)

    return state | {"messages": [new_output]}

# Start building a new graph.
graph_builder = StateGraph(ChatState)

# Add the chatbot and human nodes to the app graph.
graph_builder.add_node("chatbot", chatbot_with_welcome_msg)
graph_builder.add_node("human", human_node)

# Start with the chatbot again.
graph_builder.add_edge(START, "chatbot")

# The chatbot will always go to the human next.
graph_builder.add_edge("chatbot", "human");


def maybe_exit_human_node(state: ChatState) -> Literal["chatbot", "__end__"]:
    """Route to the chatbot, unless it looks like the user is exiting."""
    if state.get("finished", False):
        return END
    else:
        return "chatbot"


graph_builder.add_conditional_edges("human", maybe_exit_human_node)

chat_with_human_graph = graph_builder.compile()


config = {"recursion_limit": 100}

# Remember that this will loop forever, unless you input `q`, `quit` or one of the
# other exit terms defined in `human_node`.
# Uncomment this line to execute the graph:
state = chat_with_human_graph.invoke({"messages": []}, config)


pprint(state)