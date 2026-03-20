from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import rdBase
from rdkit import RDLogger
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
import os
import requests
import time
from google import genai
from google.genai import types
from functions.get_chem_info import get_compound_by_name
from functions.chem_files import export_to_chemdraw
import urllib.parse

import os
from rdkit import Chem

def read_chemdraw_input(filename="single_mol_file.cdxml", **kwargs):
    """
    Reads the specific input file from the project's 'input_files' directory.
    Includes **kwargs to ignore 'working_directory' if passed by the agent.
    """
    # Define the absolute target directory relative to the project root
    base_dir = "input_files"
    file_path = os.path.join(base_dir, filename)
    
    # Debug print so you can see the REAL path in your terminal
    print(f"DEBUG: Attempting to read file at: {os.path.abspath(file_path)}")
    
    if not os.path.exists(file_path):
        return None, f"File not found at: {file_path}. Please ensure the file exists in the 'input_files' folder."

    try:
        # Standard RDKit parsing with fallback
        mol = Chem.MolFromCDXMLFile(file_path)
        if not mol:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = f.read()
            mol = Chem.MolFromCDXMLBlock(data)
            
        if mol and mol.GetNumAtoms() > 0:
            return mol, None
        return None, "File found but RDKit could not parse a valid structure."
    except Exception as e:
        return None, f"Parsing error: {str(e)}"
    
schema_read_chemdraw_input = types.FunctionDeclaration(
    name="read_chemdraw_input",
    description="Reads the primary structural input from 'input_files/single_mol_file.cdxml'. Returns the chemical formula, molecular weight, and SMILES string to verify the drawing is correct.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={} # No arguments needed as it uses the fixed path
    ),
)