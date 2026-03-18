from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import rdBase
from rdkit import RDLogger
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
import os
import requests
from google import genai
from google.genai import types
from functions.get_chem_info import get_compound_by_name

RDLogger.DisableLog('rdApp.*')

def export_to_chemdraw(name_or_smiles: str, filename: str = "molecule.sdf", **kwargs) -> dict:
    try:
        # --- NEW: Folder Management ---
        export_dir = "exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            print(f"DEBUG: Created directory '{export_dir}'")

        # 1. SMILES or Name Lookup
        mol = Chem.MolFromSmiles(name_or_smiles)
        if mol is None:
            base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
            res = requests.get(f"{base_url}/name/{name_or_smiles}/property/SMILES/JSON", timeout=10)
            res.raise_for_status()
            smiles = res.json()['PropertyTable']['Properties'][0]['SMILES']
            mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            return {"error": f"Could not create structure for {name_or_smiles}"}

        # 2. Add 2D Coordinates & Metadata
        AllChem.Compute2DCoords(mol)
        mol.SetProp("_Name", name_or_smiles)

        # 3. Path Management
        if not filename.endswith(".sdf"):
            filename = filename.rsplit('.', 1)[0] + ".sdf"
        
        # Ensure the file goes into the exports folder
        full_path = os.path.join(export_dir, os.path.basename(filename))

        # 4. Write as SDF
        writer = Chem.SDWriter(full_path)
        writer.write(mol)
        writer.close()

        return {
            "status": "success",
            "file_name": os.path.basename(full_path),
            "folder": export_dir,
            "path": os.path.abspath(full_path),
            "message": f"Saved to {export_dir}/{os.path.basename(full_path)}"
        }
    except Exception as e:
        return {"error": f"Tool Failure: {str(e)}"}
    
schema_export_to_chemdraw = types.FunctionDeclaration(
    name="export_to_chemdraw",
    description="Saves a chemical structure to an .sdf file. Note: Use .sdf extension. These files open perfectly in ChemDraw and other chemistry software.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "name_or_smiles": types.Schema(
                type=types.Type.STRING,
                description="The name of the chemical or its SMILES string.",
            ),
            "filename": types.Schema(
                type=types.Type.STRING,
                description="The name of the file to save (default 'molecule.cdxml').",
            )
        },
        required=["name_or_smiles"]
    ),
)

def read_chemdraw_file(file_path: str, **kwargs) -> dict:
    """
    Reads a .cdxml file and returns the chemical information (SMILES and Formula).
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found at {file_path}"}
    
    try:
        # RDKit reads the first molecule found in the CDXML
        mol = Chem.MolFromCDXMLFile(file_path)
        if mol is None:
            return {"error": "Could not extract a valid molecule from this ChemDraw file."}
        
        return {
            "smiles": Chem.MolToSmiles(mol),
            "formula": Chem.rdMolDescriptors.CalcMolFormula(mol),
            "molecular_weight": Chem.rdMolDescriptors.CalcExactMolWt(mol),
            "message": "Successfully read molecule from ChemDraw file."
        }
    except Exception as e:
        return {"error": f"Error reading CDXML: {str(e)}"}
    
schema_read_chemdraw_file = types.FunctionDeclaration(
    name="read_chemdraw_file",
    description="Read a ChemDraw (.cdxml) file and return the chemical information (SMILES and Formula).",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the ChemDraw file to read.",
            )
        },
        required=["file_path"]
    )
)

def batch_export_sdfs(chemical_names: list, **kwargs) -> dict:
    """
    Takes a list of chemical names and exports them all as .sdf files.
    """
    results = []
    errors = []
    
    for name in chemical_names:
        # We reuse our existing function for each name
        # We sanitize the filename by replacing spaces with underscores
        safe_filename = name.lower().replace(" ", "_") + ".sdf"
        res = export_to_chemdraw(name_or_smiles=name, filename=safe_filename)
        
        if res.get("status") == "success":
            results.append(name)
        else:
            errors.append(f"{name}: {res.get('error')}")
            
    return {
        "status": "completed",
        "exported_count": len(results),
        "exported_compounds": results,
        "failed_count": len(errors),
        "errors": errors
    }

schema_batch_export_sdfs = types.FunctionDeclaration(
    name="batch_export_sdfs",
    description="Takes a list of chemical names and exports them all as .sdf files. Filenames are sanitized by replacing spaces with underscores.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "chemical_names": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="A list of chemical names to export.",
            )
        },
        required=["chemical_names"]
    )
)


def export_combined_canvas(chemical_names: list, filename: str = "combined_drawing.sdf", **kwargs) -> dict:
    """
    Merges multiple chemicals into a SINGLE drawing on a SINGLE canvas.
    Ideal for side-by-side comparison in ChemDraw.
    """
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    combined_mol = None
    success_names = []
    
    try:
        for name in chemical_names:
            # 1. Reuse your existing name-to-SMILES lookup logic
            base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
            res = requests.get(f"{base_url}/name/{name}/property/SMILES/JSON", timeout=5)
            
            if res.status_code == 200:
                smiles = res.json()['PropertyTable']['Properties'][0]['SMILES']
                mol = Chem.MolFromSmiles(smiles)
                
                if mol:
                    # 2. Merge logic
                    if combined_mol is None:
                        combined_mol = mol
                    else:
                        combined_mol = Chem.CombineMols(combined_mol, mol)
                    success_names.append(name)

        if combined_mol is None:
            return {"error": "No valid molecules were found to combine."}

        # 3. Generate coordinates for the ENTIRE group at once
        # This prevents them from being drawn directly on top of each other
        AllChem.Compute2DCoords(combined_mol)
        
        # 4. Save to the exports folder
        if not filename.endswith(".sdf"):
            filename += ".sdf"
        full_path = os.path.join(export_dir, filename)

        writer = Chem.SDWriter(full_path)
        writer.write(combined_mol)
        writer.close()

        return {
            "status": "success",
            "file_name": filename,
            "compounds_included": success_names,
            "path": os.path.abspath(full_path),
            "message": f"Created a single canvas with {len(success_names)} molecules."
        }

    except Exception as e:
        return {"error": f"Combined export failed: {str(e)}"}
    
schema_export_combined_canvas = types.FunctionDeclaration(
    name="export_combined_canvas",
    description="Merges multiple chemicals into a SINGLE drawing on a SINGLE canvas. Ideal for side-by-side comparison in ChemDraw.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "chemical_names": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="A list of chemical names to include in the combined drawing.",
            ),
            "filename": types.Schema(
                type=types.Type.STRING,
                description="The name of the file to save (default 'combined_drawing.sdf').",
            )
        },
        required=["chemical_names"]
    )
)