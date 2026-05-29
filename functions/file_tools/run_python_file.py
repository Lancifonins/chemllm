import os
import subprocess
import sys
from google import genai
from google.genai import types

def run_python_file(working_directory, file_path, args=None):
    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, file_path))
    valid_target_dir = os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs
    if not valid_target_dir:
        print(f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory')
        return
    if not os.path.isfile(target_dir):
        print(f'Error: "{file_path}" does not exist or is not a regular file')
        return
    _,extension = os.path.splitext(file_path)
    if extension.lower() != '.py':
        print(f'Error: "{file_path}" is not a Python file')
        return
    
    command = ["python", target_dir]
    additional_args = args
    if additional_args:
        command.extend(additional_args)
    
    try:
        run_result = subprocess.run(command,cwd=working_dir_abs,timeout=30,capture_output=True,text=True)
        result_str = ""
        if run_result.returncode != 0:
            result_str += "Process exited with code X"
        if run_result.stdout == "" and run_result.stderr == "":
            result_str += "No output produced"
        stdout_mes = f"STDOUT: {run_result.stdout}"
        stderr_mes = f"STDERR: {run_result.stderr}"
        result_str += stdout_mes
        result_str += stderr_mes
        print(result_str)
        return result_str
    except Exception as e:
        er_str = f"Error: executing Python file: {e}"
        print(er_str)
        return er_str

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="run a certain python file",
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
