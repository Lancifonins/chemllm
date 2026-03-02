import os
from dotenv import load_dotenv
import argparse
from google import genai
from google.genai import types
from prompts import *
from functions.call_function import *
from functions.get_response import *


load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
    
messages = [types.Content(role="user", parts=[types.Part(text=args.user_prompt)])]
def main():
    print("Hello from 1stllm!")
    response = get_response(messages, verbose=args.verbose)

    print(response.text)


if __name__ == "__main__":
    main()
