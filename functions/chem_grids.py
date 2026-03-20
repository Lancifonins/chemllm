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
    """Fetches SMILES and CAS, ensuring a 2D conformer is generated."""
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
    try:
        res = requests.get(f"{base_url}/{name}/property/SMILES/JSON", timeout=5)
        if res.status_code != 200:
            return None, None
        
        smiles = res.json()['PropertyTable']['Properties'][0]['SMILES']
        mol = Chem.MolFromSmiles(smiles)
        
        if mol:
            # Generate 2D coordinates (ignore the 0 success code)
            AllChem.Compute2DCoords(mol)
            if mol.GetNumConformers() == 0:
                AllChem.Compute2DCoords(mol, sampleSeed=0xf00d)

            cas = "N/A"
            if "cas" in label_type.lower():
                syn_res = requests.get(f"{base_url}/{name}/synonyms/JSON", timeout=5)
                if syn_res.status_code == 200:
                    data = syn_res.json()
                    info = data.get('InformationList', {}).get('Information', [])
                    if info:
                        synonyms = info[0].get('Synonym', [])
                        cas_regex = re.compile(r'^\d{2,7}-\d{2}-\d$')
                        for syn in synonyms:
                            clean_syn = syn.strip()
                            if cas_regex.match(clean_syn):
                                cas = clean_syn
                                break
            return mol, cas
    except Exception as e:
        print(f"DEBUG: Error fetching {name}: {e}")
        return None, None
    return None, None

def export_chemical_grid(chemical_names: list, columns: int = 3, label_type: str = "name", filename: str = "grid_layout.sdf", **kwargs):
    """Arranges chemicals in a centered grid with stacked labels underneath."""
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    combined = None
    x_spacing = 35.0 # Centered layout needs more breathing room
    y_spacing = 45.0
    line_height = 2.2 # Vertical space between label lines
    success_count = 0

    for idx, name in enumerate(chemical_names):
        mol, cas = get_mol_data(name, label_type)
        
        if mol and mol.GetNumAtoms() > 0 and mol.GetNumConformers() > 0:
            success_count += 1
            col = (success_count - 1) % columns
            row = (success_count - 1) // columns
            
            # Target center coordinates for this grid cell
            target_x = float(col * x_spacing)
            target_y = float(row * -y_spacing)

            # --- CENTERING LOGIC ---
            conf = mol.GetConformer()
            # Calculate the geometric center (Centroid) of the current molecule
            all_x = [conf.GetAtomPosition(i).x for i in range(mol.GetNumAtoms())]
            all_y = [conf.GetAtomPosition(i).y for i in range(mol.GetNumAtoms())]
            centroid_x = sum(all_x) / len(all_x)
            centroid_y = sum(all_y) / len(all_y)

            # Shift every atom so the Centroid moves to (target_x, target_y)
            for i in range(mol.GetNumAtoms()):
                pos = conf.GetAtomPosition(i)
                new_x = (pos.x - centroid_x) + target_x
                new_y = (pos.y - centroid_y) + target_y
                conf.SetAtomPosition(i, (new_x, new_y, 0.0))
            
            # Merge molecule into the canvas
            combined = mol if combined is None else Chem.CombineMols(combined, mol)

            # --- STACKED LABEL LOGIC ---
            lines = []
            if "index" in label_type.lower(): lines.append(f"{idx+1}") #change the index format here
            if "name" in label_type.lower(): lines.append(name.title())
            if "cas" in label_type.lower(): lines.append(f"CAS: {cas}")

            # Labels start 10 units below the structure's center
            label_y_start = target_y - 12.0
            
            for line_idx, text in enumerate(lines):
                # Create a placeholder dummy atom for each line of text
                label_mol = Chem.MolFromSmiles("[*]")
                AllChem.Compute2DCoords(label_mol)
                l_conf = label_mol.GetConformer()
                
                # Position directly under target_x (the horizontal center)
                current_label_y = label_y_start - (line_idx * line_height)
                l_conf.SetAtomPosition(0, (target_x, current_label_y, 0.0))
                
                # Set the alias property for ChemDraw/SDF viewers
                label_mol.GetAtomWithIdx(0).SetProp("molFileAlias", text)
                combined = Chem.CombineMols(combined, label_mol)

    if not combined:
        return {"error": "No valid molecules were found."}

    # Ensure extension is correct
    if not filename.lower().endswith(".sdf"):
        filename = filename.split('.')[0] + ".sdf"
    
    full_path = os.path.join(export_dir, filename)
    writer = Chem.SDWriter(full_path)
    writer.write(combined)
    writer.close()

    return {
        "status": "success",
        "path": os.path.abspath(full_path),
        "compounds": success_count,
        "layout": f"{columns} columns, centered"
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