import os
from google import genai
from google.genai import types

def get_files_info(working_directory, directory="."):
    
    print(f"Result for '{directory}' directory:")
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target_dir = os.path.normpath(os.path.join(working_dir_abs, directory))
        if not os.path.isdir(target_dir):
            raise Exception
            print(f'    Error: "{directory}" is not a directory')
        valid_target_dir = os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs
        if valid_target_dir:
            contents = os.listdir(target_dir)
            for content in contents:
                content_name = str(content)
                content_file_path = f"{target_dir}/{content_name}"
                content_size = os.path.getsize(content_file_path)
                if os.path.isdir(content_file_path):
                    content_status = "is_dir=True"
                else:
                    content_status = "is_dir=False"
                content_message = f"""
    {content_name}: file_size={content_size}, {content_status}"""
                print(content_message)
        else:
            print(f'    Error: Cannot list "{directory}" as it is outside the permitted working directory')
    except Exception as error:
        print(f"Error: {error}")
    
    
schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in a specified directory relative to the working directory, providing file size and directory status but not the contents",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="Directory path to list files from, relative to the working directory (default is the working directory itself)",
            ),
        },
    ),
)
