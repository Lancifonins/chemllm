import sys
print(f"DEBUG: Python is running from: {sys.executable}")

import os
from dotenv import load_dotenv
import argparse
from google import genai
from google.genai import types

from prompts import *
from functions.call_function import call_function
from functions.adv_response import start_advanced_chat
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory



load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
    
def main():
    print("Hello from Chemllm! This is a demo of the Gemini API with a chemistry-related prompt.")

    parser = argparse.ArgumentParser(description="Gemini Interactive Tool-Calling Chatbot")
    parser.add_argument("user_prompt", type=str, nargs="?", default=None, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    start_advanced_chat(args)


if __name__ == "__main__":
    main()
