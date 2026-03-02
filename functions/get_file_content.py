import os
from google import genai
from google.genai import types
rd_limits = 10000

def get_file_content(working_directory, file_path):
    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, file_path))
    valid_target_dir = os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs
    if not valid_target_dir:
        print(f'Error: Cannot read "{file_path}" as it is outside the permitted working directory')
        return
    
    if not os.path.isfile(target_dir):
        print(f'Error: File not found or is not a regular file: "{file_path}"')
        return

    try:
        with open(target_dir,'r') as data_file:
            rd_counter = 0
            limited_file = ""
            while True:
                limited_char = data_file.read(1)
                limited_file += limited_char
                rd_counter += 1
                if rd_counter == rd_limits:
                    limited_file += f'[...File "{file_path}" truncated at {rd_limits} characters]'
                    break
                elif not limited_char:
                    break
        return limited_file
    except Exception as e:
        print(f"Error: {Exception}")

schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="read the contents of a certain file with a limit of how many words to read",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="Directory path to list files from, relative to the working directory (default is the working directory itself)",
            ),
        },
    ),
)

