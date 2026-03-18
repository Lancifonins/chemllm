import os
import sys
from dotenv import load_dotenv
import argparse
from google import genai
from google.genai import types
from prompts import *
from functions.call_function import *

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if api_key == None:
    raise RuntimeError("No_API")
client = genai.Client(api_key=api_key)


def get_response(messages, verbose=False):
    for _ in range(20):
        response = client.models.generate_content(
        model = "gemini-2.5-flash",
        contents = messages,
        config=types.GenerateContentConfig(tools=[available_functions],system_instruction=system_prompt, temperature=0)
        )
        usage = response.usage_metadata
        prop_tokens_num = usage.prompt_token_count
        resp_tokens_num = usage.candidates_token_count
        
        last_user_text = messages[-1].parts[0].text if messages else "N/A"

        token_count_message = f"""User prompt: {last_user_text}
Prompt tokens: {prop_tokens_num}
Response tokens: {resp_tokens_num}"""
    
        if verbose:
            print(token_count_message)

        if response.candidates is not None:
            messages.append(response.candidates[0].content)

        if not response.function_calls:
            return response

        if response.function_calls is not None:
            list_of_function_calls = response.function_calls
            function_call_results = []
            for function_call in list_of_function_calls:
                print(f"Calling function: {function_call.name}({function_call.args})")
                function_call_result = call_function(function_call, verbose=verbose)
                if function_call_result.parts is None:
                    raise Exception("Function call result has no parts")
                if function_call_result.parts[0].function_response is None:
                    raise Exception("Function call result has no function response")
                if function_call_result.parts[0].function_response.response is None:
                    raise Exception("Function call result has no response content")
           
            
            function_call_results.append(function_call_result.parts[0])
            messages.append(types.Content(role="tool", parts=function_call_results))

            if verbose:
                print(f"-> {function_call_result.parts[0].function_response.response}")
                messages.append(types.Content(role="user", parts=function_call_results))

    else:
        print("Reached maximum number of iterations. Exiting.")
        sys.exit(1)