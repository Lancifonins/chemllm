import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import *
from functions.call_function import call_function
from functions.get_response import get_response
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

def start_advanced_chat(args):
    session = PromptSession(history=InMemoryHistory())
    print("Advanced Interactive Gemini Shell Active.")
    print("Type 'exit' or 'quit' to quit.")

    messages = []
    last_compound = None
    first_input = getattr(args, 'user_prompt', None)
    

    while True:
        try:
            if first_input:
                user_input = first_input
                print(f"Initial Prompt: {user_input}")
                first_input = None 
            else:
                user_input = session.prompt("You > ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("Session ended.")
                break

            if user_input.lower() == "/safety":
                if last_compound:
                    user_input = f"Show me the GHS safety hazards for {last_compound}"
                else:
                    print("No compound found in recent history to check.")
                    continue
            
            if not user_input:
                continue
                
            messages.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
            response = get_response(messages, verbose=args.verbose)

            if response and response.text:
                print(f"\nGemini: {response.text}\n")
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        # Extract the name or CAS used in the tool call
                        args_dict = part.function_call.args
                        last_compound = args_dict.get('name') or args_dict.get('cas_number') or args_dict.get('name_or_cas')

            

        except KeyboardInterrupt:
            continue  # Ctrl+C clears the current line
        except EOFError:
            break     # Ctrl+D exits

    

