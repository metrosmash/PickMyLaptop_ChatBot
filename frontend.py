from google import genai
from google.genai import types
import streamlit as st
import mysql.connector


# Streamlit UI
def streamlit_ui():

    # Show title and description.
    st.title("💻 PickMyLaptop_Chatbot V.0")
    st.write("👋 Welcome to your smart laptop shopping assistant!")

    st.markdown("""Looking for the perfect laptop but not sure where to start? You're in the right place! 
    **PickMyLaptop_Chatbot V.0** is an intelligent assistant powered by **Gemini Flash 2.5**, designed to guide you 
    through the laptop selection process based on your preferences, needs, and budget.
    
    Whether you're a student, gamer, professional, or casual user, our AI assistant can help you:
    - Compare different laptop models
    - Understand key features and specs
    - Find laptops within your price range
    - Make confident, informed decisions
    
    Start by telling the chatbot what you're looking for – and let the assistant do the rest!
    """)

# st.write(
#     "This is a simple chatbot that uses Gemini flash 2.5 model to help users pick their preferred laptop. "
#     "To use this app, you need to provide a Gemini API key, which you can get [here]("
#     "https://ai.google.dev/gemini-api/docs/api-key)."
#     "You can also learn how to build this app step by step by [following our tutorial]("
#     "https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
# )