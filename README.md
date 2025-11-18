# PickMyLaptop_ChatBot

An AI-powered Laptop Advisor that helps you choose the perfect laptop tailored to your needs with web3 capabilities.


## Table of contents
- Overview
- Features
- Repository structure
- Requirements
- Setup & Configuration
- Database
- Running locally
- How it works (architecture)
- Available tools / agent capabilities
- Examples (user prompts)
- Troubleshooting
- Contributing
- License & credits


## Overview
PickMyLaptop_ChatBot is a Python-based conversational assistant that recommends laptops based on user requirements. It uses a large language model (Google Gemini via the langchain adapter) with tool integrations to query a MySQL laptop dataset and return curated results. The repository includes a Streamlit UI for interaction and an agent backend that runs search tools against a `laptop_dataset` database.


## Features
- Natural-language chat interface (Streamlit UI)
- LLM-driven assistant (Google Gemini via langchain/google genai integration)
- Database-backed recommendations (MySQL)
- Tool-enabled agent to run structured searches (attribute, keyword, range, combined)
- Context-aware tool result summarization to the LLM
- Modular code: backend agent, frontend UI, prompt file


## Repository structure
- Backend.py — Agent, tools, DB connection logic, and state graph
- streamlit_app.py — Streamlit application (UI entry point)
- frontend.py — Additional UI/utility code (if used by app)
- bot_prompt.txt — System prompt used to configure assistant behavior
- requirements.txt — Python dependencies
- Data/ — folder for dataset(s) or supporting files (may be empty)
- LICENSE — project license
- README.md — this file


## Requirements
- Python 3.9+ (3.10+ recommended)
- MySQL-accessible database (the code points to db4free.net by default)
- Internet access for LLM API (Google Generative AI / Gemini)

Install dependencies:

pip install -r requirements.txt


## Setup & Configuration

1. Clone the repo:

   git clone https://github.com/metrosmash/PickMyLaptop_ChatBot.git
   cd PickMyLaptop_ChatBot

2. Create a virtual environment and install requirements:

   python -m venv .venv
   source .venv/bin/activate  # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt

3. Configure secrets used by the app

   The backend reads secrets via streamlit.secrets in Backend.py. Provide the following keys:

   - DB_username — MySQL username
   - DB_password — MySQL password
   - API_key — Google API / Gemini key used by the LangChain adapter

   Option A — Streamlit secrets file:
   Create `.streamlit/secrets.toml` with:

   DB_username = "your_db_username"
   DB_password = "your_db_password"
   API_key = "your_google_api_key"

   Option B — Environment variables:
   You can also export GOOGLE_API_KEY manually; Backend.py sets it from st.secrets at runtime.

4. Database connection parameters

   Backend.py uses:
   - host: db4free.net
   - database: metro_laptop

   If you use your own MySQL host, update the connection details inside Backend.py or make them configurable.


## Database

The agent queries a table named `laptop_dataset`. Columns referenced in code include:
- id, Brand, Product_Description, Screen_Size, RAM, Processor, GPU, GPU_Type, Resolution, Condition1, Price, SSD, HDD

Example (simplified) CREATE TABLE statement:

CREATE TABLE laptop_dataset (
  id INT PRIMARY KEY AUTO_INCREMENT,
  Brand VARCHAR(255),
  Product_Description TEXT,
  Screen_Size FLOAT,
  RAM INT,
  Processor VARCHAR(255),
  GPU VARCHAR(255),
  GPU_Type VARCHAR(255),
  Resolution VARCHAR(100),
  Condition1 VARCHAR(100),
  Price DECIMAL(10,2),
  SSD INT,
  HDD INT
);

Adjust types to match your data and import rows from CSV as needed.


## Running locally

Start the Streamlit app:

streamlit run streamlit_app.py

Open the provided local URL (usually http://localhost:8501).


## How it works (architecture)

- The LLM (Google Gemini via langchain adapter) drives conversation and can emit structured "tool calls".
- Backend.py defines typed tools that run parameterized SQL queries against the MySQL dataset.
- A state graph (langgraph) composes a chatbot node and a tool node:
  - chatbot node: runs the LLM, injects system prompt from bot_prompt.txt, and includes any tool results into the prompt context
  - tool node: runs the requested DB queries and appends tool results into state.tool_context
- The Streamlit UI calls functions exposed by the compiled graph to initialize state and handle messages.


## Available tools / agent capabilities

- Attribute search (attribute, value)
  - Example: find laptops where Brand ~ "Dell"
- Specific search (keyword)
  - Example: search across Brand, Product_Description, Processor for "MacBook"
- Range search (attribute, min_value, max_value)
  - Example: Price BETWEEN 500 AND 1000
- Attribute + Range (attribute, value, range_column, min_value, max_value)
  - Example: Brand = "Dell" AND Price BETWEEN 300 AND 800

These tools are implemented in Backend.py as:
- attribute_search / get_attribute_search_tool
- search_specific_laptop / get_specific_search_tool
- search_by_range / get_range_search_tool
- attribute_range_search / get_attribute_range_search


## Examples (user prompts)

- "I want a 14-inch laptop with 16GB RAM for under $1200."
- "Show me Dell laptops with an RTX GPU and price between 800 and 1500."
- "Recommend a value laptop for programming with at least 8GB of RAM."

The assistant will parse intent, call the appropriate tool(s), and present structured results.


## Troubleshooting

- Missing/invalid API key: verify `API_key` is set and valid for the Google Generative API.
- DB connection failures: check DB credentials, host reachability, and that the `metro_laptop` database and `laptop_dataset` table exist.
- LangGraph/LangChain compatibility: ensure versions in requirements.txt are installed; some LLM adapters require particular versions.
- Streamlit secrets vs. env vars: Backend.py expects `st.secrets["DB_username"]`, `st.secrets["DB_password"]`, `st.secrets["API_key"]`. If you use environment variables directly, ensure they are set before running the app.


## Contributing

- Open issues for feature requests or bugs.
- Submit PRs with clear descriptions and tests where applicable.
- Follow repository style conventions and update README if you add new tools or configuration options.


## License & credits
See the LICENSE file in the repository for licensing details.

