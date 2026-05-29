import os
from google import genai
from google.genai import types

def write_file(working_directory, file_path, content):
    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, file_path))
    valid_target_dir = os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs
    
    if not valid_target_dir:
        print(f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory')
        return
    elif os.path.isdir(target_dir):
        print(f'Error: Cannot write to "{file_path}" as it is a directory')
        return
    
    dir_path = os.path.dirname(target_dir)
    os.makedirs(dir_path, exist_ok=True)

    try:
        with open(target_dir,'w') as file:
            file.write(content)
            suc_mess = f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
            print(suc_mess)
            return suc_mess
    except Exception as error:
        error_mes = f"Error: {error}"
        print(error_mes)
        return error_mes

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="write text content to a specific file",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="Directory path to list files from, relative to the working directory (default is the working directory itself)",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content to write into the specific file",
            ),
        },
    ),
)