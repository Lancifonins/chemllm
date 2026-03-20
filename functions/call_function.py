import os
from google import genai
from google.genai import types
from functions.get_files_info import *
from functions.get_file_content import *
from functions.run_python_file import *
from functions.write_file import *
from functions.get_chem_info import *
from functions.chem_files import *
from functions.chem_reactions import *
from functions.chem_grids import *
from functions.chem_discovery import *
from functions.chem_file_utils import *
from functions.function_declaration import *

def call_function(function_call, verbose=False):
    if verbose:
        print(f"Calling function: {function_call.name}({function_call.args})")
    else:
        print(f" - Calling function: {function_call.name}")
    
    function_map = call_function_map
    function_name = function_call.name or ""
    
    if function_name not in function_map:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )
    
    # 1. Prepare the arguments
    args = dict(function_call.args) if function_call.args else {}

    args["working_directory"] = "."  # Default working directory for all functions; can be overridden for specific functions below

    # 2. SELECTIVE INJECTION
    # Only add working_directory to tools that interact with the local filesystem
    file_system_tools = ["get_file_content", "get_files_info", "run_python_file", "write_file"]
    
    if function_name in file_system_tools:
        args["working_directory"] = "."  # or any specific directory you want to restrict to

    # 3. SAFE EXECUTION
    try:
        # We execute the function from the map
        result = function_map[function_name](**args)
        function_result = str(result)
    except TypeError as e:
        # This catches if Gemini or the injector sends wrong arguments
        function_result = f"Argument Error: {str(e)}"
    except Exception as e:
        function_result = f"Execution Error: {str(e)}"

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": function_result},
            )
        ],
    )
