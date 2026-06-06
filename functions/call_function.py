import os
from google import genai
from google.genai import types

#file processing tools
from functions.file_tools.get_files_info import *
from functions.file_tools.get_file_content import *
from functions.file_tools.run_python_file import *
from functions.file_tools.write_file import *
from functions.file_tools.csv_tools import *

#chemistry processing tools
from functions.chem_tools.get_chem_info import *
from functions.chem_tools.chem_files import *
from functions.chem_tools.chem_reactions import *
from functions.chem_tools.chem_grids import *
from functions.chem_tools.chem_discovery import *
from functions.chem_tools.chem_file_utils import *
from functions.chem_tools.visual_tool import *

#literature searching tools
from functions.lit_tools.lit_tools import *

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
    
    args = dict(function_call.args) if function_call.args else {}

    args["working_directory"] = "."  # Default working directory for all functions; can be overridden for specific functions below

    file_system_tools = ["get_file_content", "get_files_info", "run_python_file", "write_file"]
    
    if function_name in file_system_tools:
        args["working_directory"] = "." 
    try:
        result = function_map[function_name](**args)
        function_result = str(result)
    except TypeError as e:
        # Catches if Gemini or the injector sends wrong arguments
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
