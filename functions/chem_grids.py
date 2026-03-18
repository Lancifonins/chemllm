from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import rdBase
from rdkit import RDLogger
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
import os
import re
import requests
from google import genai
from google.genai import types
from functions.get_chem_info import get_compound_by_name

RDLogger.DisableLog('rdApp.*')

def get_mol_data(name, label_type):
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
    try:
        res = requests.get(f"{base_url}/{name}/property/SMILES/JSON", timeout=5)
        if res.status_code != 200:
            return None, None
        
        smiles = res.json()['PropertyTable']['Properties'][0]['SMILES']
        mol = Chem.MolFromSmiles(smiles)
        
        if mol:
            AllChem.Compute2DCoords(mol)
            
            # Double check that atoms actually have positions now
            if mol.GetNumConformers() == 0:
                AllChem.Compute2DCoords(mol, sampleSeed=0xf00d)

            # Proceed with CAS lookup
            cas = "N/A"
            if "cas" in label_type.lower():
                # ... (your existing CAS lookup logic)
                pass 

            return mol, cas # Now it successfully returns the molecule
    except Exception as e:
        # If it prints "DEBUG: 0", it means the line above 'except' actually succeeded
        print(f"DEBUG: Error fetching {name}: {e}")
        return None, None

def export_chemical_grid(chemical_names: list, columns: int = 3, label_type: str = "name", filename: str = "grid_layout.sdf", **kwargs):
    """
    The main tool to arrange chemicals in a grid with labels.
    """
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    combined = None
    x_spacing = 25.0
    y_spacing = 30.0
    success_count = 0

    for idx, name in enumerate(chemical_names):
        mol, cas = get_mol_data(name, label_type)
        
        if mol and mol.GetNumAtoms() > 0 and mol.GetNumConformers() > 0:
            success_count += 1
            col = (success_count - 1) % columns
            row = (success_count - 1) // columns
            
            shift_x = col * x_spacing
            shift_y = row * -y_spacing

            # Shift Structure Coordinates
            conf = mol.GetConformer()
            for i in range(mol.GetNumAtoms()):
                pos = conf.GetAtomPosition(i)
                conf.SetAtomPosition(i, (pos.x + float(shift_x), pos.y + float(shift_y), pos.z))
            
            # Merge into main canvas
            if combined is None:
                combined = mol
            else:
                combined = Chem.CombineMols(combined, mol)

            # --- Labeling Logic ---
            label_parts = []
            if "index" in label_type.lower(): label_parts.append(f"#{idx+1}")
            if "name" in label_type.lower(): label_parts.append(name.title())
            if "cas" in label_type.lower(): label_parts.append(f"CAS: {cas}")
            label_text = " | ".join(label_parts)

            # Create text label via Dummy Atom
            label_mol = Chem.MolFromSmiles("[*]")
            AllChem.Compute2DCoords(label_mol)
            label_conf = label_mol.GetConformer()
            # Place label 8 units below the center of the structure
            label_conf.SetAtomPosition(0, (float(shift_x), float(shift_y - 8.0), 0.0))
            label_mol.GetAtomWithIdx(0).SetProp("molFileAlias", label_text)
            
            combined = Chem.CombineMols(combined, label_mol)

    if not combined or success_count == 0:
        return {"error": "Failed to create grid: No valid molecules found."}

    # Ensure valid filename
    if not filename.endswith(".sdf"):
        filename = filename.split('.')[0] + ".sdf"
    
    full_path = os.path.join(export_dir, filename)
    writer = Chem.SDWriter(full_path)
    writer.write(combined)
    writer.close()

    return {
        "status": "success",
        "file": os.path.basename(full_path),
        "path": os.path.abspath(full_path),
        "count": success_count
    }

schema_export_chemical_grid = types.FunctionDeclaration(
    name="export_chemical_grid",
    description="Creates a grid of chemicals with labels underneath (Name, CAS, or Index).",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "chemical_names": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="List of chemicals."
            ),
            "columns": types.Schema(type=types.Type.INTEGER, description="Grid columns."),
            "label_type": types.Schema(
                type=types.Type.STRING,
                description="What to show: 'name', 'cas', 'index', 'index_name', or 'index_name_cas'."
            ),
            "filename": types.Schema(type=types.Type.STRING)
        },
        required=["chemical_names"]
    ),
)