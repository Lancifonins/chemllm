from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import rdBase
from rdkit import RDLogger
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem import rdmolfiles, Descriptors, rdMolDescriptors
import os
import requests
import time
from google import genai
from google.genai import types
from functions.get_chem_info import get_compound_by_name
from functions.chem_files import export_to_chemdraw
import urllib.parse


def read_chemdraw_input(filename="single_mol_file.sdf", **kwargs):
    """
    The 'Indestructible' Reader.
    Uses SDF format which works even when XML/Data parsers are broken.
    """
    base_dir = "input_files"
    file_path = os.path.join(base_dir, filename)
    
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}. Please save your drawing as an .sdf file."

    try:
        # SDMolSupplier is the oldest and most stable part of RDKit.
        suppl = Chem.SDMolSupplier(file_path)
        mol = next(suppl) if suppl else None
        
        if mol and mol.GetNumAtoms() > 0:
            return mol, None
            
        return None, "File found, but RDKit could not find any atoms in the SDF."
        
    except Exception as e:
        return None, f"SDF Error: {str(e)}"

    
schema_read_chemdraw_input = types.FunctionDeclaration(
    name="read_chemdraw_input",
    description="Reads the primary structural input from 'input_files/single_mol_file.sdf'. Returns the chemical formula, molecular weight, and SMILES string to verify the drawing is correct.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={} # No arguments needed as it uses the fixed path
    ),
)

def get_input_structure_info(**kwargs):
    """
    Agent tool to verify 'input_files/single_mol_file.sdf'.
    """
    mol, error = read_chemdraw_input()
    
    if error:
        return {"error": error}
        
    try:
        smiles = Chem.MolToSmiles(mol)
        mw = round(Descriptors.MolWt(mol), 2)
        formula = rdMolDescriptors.CalcMolFormula(mol)
        
        return {
            "status": "Success",
            "format": "SDF",
            "formula": formula,
            "molecular_weight": mw,
            "smiles": smiles
        }
    except Exception as e:
        return {"error": f"Property calculation failed: {e}"}
    
schema_get_input_structure_info = types.FunctionDeclaration(
    name="get_input_structure_info",
    description="Reads the chemical drawing in 'input_files/single_mol_file.sdf' and returns Formula and Molecular Weight. Use this to verify the drawing is being read correctly.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={} # No arguments required; it defaults to the input folder
    ),
)