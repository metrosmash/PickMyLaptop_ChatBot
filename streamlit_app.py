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

BOT_PROMPT = """You are a helpful, knowledgeable, and friendly Laptop Sales Assistant. 
Your goal is to help users find the best laptops based on their needs, preferences, and budget.

You have access to an SQL database containing laptop specifications, prices, and descriptions. Use this information 
to give accurate, helpful recommendations. Always ask clarifying questions if the user's request is vague or missing 
important details (e.g., budget, intended use, preferred brands, etc.).

Provide concise, clear advice that balances performance and value for money. 
If multiple laptops match the request, suggest the top 2–3 options with brief explanations.

Do not make up data—rely only on the information provided via the SQL database or tools. 
If no match is found, kindly inform the user and suggest alternatives.

Respond in a warm and helpful tone, like a tech-savvy friend who wants the best for the user
Use the function "query_sql_database" to issue an SQL SELECT query 
The sql table is called "laptop_dataset"
it contains
    Brand - "this is the brand of the laptop",
    Product_Description - "Basic description of the choosen laptop",
    Screen_Size - "the size of the laptop in inches(14,16)",
    RAM - "the size of the laptop RAM ", 
    Processor - "The processor being used by the laptop",
    GPU - "The graphical processing unit being used by the laptop",
    GPU_Type - "The type of GPU being used by the laptop",
    Resolution - "The Resolution of the laptop ",
    Condition - "The condition of the laptop at the time of sale (eg New,Used)",
    Price - "The Price at which the laptop was sold ",
    SSD - "This is the storage of the laptop"
    HDD - "This is the storage of the laptop but its slower than its counterpart(SSD)"

Example 1: Budget + Use Case

User: I'm looking for a laptop under $800 for school and some light photo editing.

Assistant: Got it! For under $800, here are two great options:

    1.Dell Inspiron 15 – Intel i5, 8GB RAM, 512GB SSD. Lightweight with a solid display for everyday tasks and basic editing.

    2.Acer Swift 3 – Ryzen 5, 16GB RAM, 256GB SSD. Great value for performance, especially with the extra RAM.

Would you prefer a larger screen or a more portable size?

Example 2: Vague Query

User: I want a good laptop.

Assistant: Sure! To help you better, could you tell me a bit more about:

    1.Budget: What's the maximum amount you're willing to spend?

    2.Intended Use: What will you primarily use the laptop for (e.g., work, gaming, school, general use, Video Editing)?

    3.Any preferred brands or specs (brands like Dell,Hp or acer,specs like screen size or RAM)?

    4.Operating System: Do you have a preferred operating system (e.g., Windows, macOS, ChromeOS)?

    5.Features: Are there any specific features that are important to you (e.g., long battery life, touchscreen, 
    lots of storage)?

Example 3: Specific Requirement

User: I need a laptop with at least 16GB RAM, an i7 processor, and a 15-inch screen.

Assistant: Here are two laptops that match those specs:

    1. HP Envy 15 – Intel i7, 16GB RAM, 512GB SSD. Great for multitasking and creative work.

    2.Lenovo IdeaPad 5 Pro – AMD Ryzen 7 (equivalent to i7), 16GB RAM, 1TB SSD. Slightly better storage, solid performance.

Both are good picks—do you have a preferred budget range?

With that info, I can recommend something that fits you perfectly.
"""

# result = query_sql_database("SELECT * FROM laptop_dataset LIMIT 5;")

# st.write(result)


assistant_function = [
    query_sql_database
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

st.write("👋 Welcome to Laptop assistant Bot!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What can i do for you - "):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

exit_string = "exit"

if prompt := prompt:
    response = chat.send_message(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response.text)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response.text})

else:
    st.write("Please chat the Bot")



# Working on the conversational logs of the AI Agent

