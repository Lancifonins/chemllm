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

def export_reaction_canvas(chemical_names: list, filename: str = "reaction_layout.sdf", **kwargs) -> dict:
    """
    Merges multiple chemicals into a SINGLE drawing on a SINGLE canvas.
    This is the foundation for future reaction-mapping tools.
    """
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    combined_mol = None
    success_names = []
    
    try:
        for name in chemical_names:
            # Reusing the PubChem lookup logic
            base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
            res = requests.get(f"{base_url}/name/{name}/property/SMILES/JSON", timeout=5)
            
            if res.status_code == 200:
                smiles = res.json()['PropertyTable']['Properties'][0]['SMILES']
                mol = Chem.MolFromSmiles(smiles)
                
                if mol:
                    if combined_mol is None:
                        combined_mol = mol
                    else:
                        # CombineMols creates a single object containing multiple fragments
                        combined_mol = Chem.CombineMols(combined_mol, mol)
                    success_names.append(name)

        if combined_mol is None:
            return {"error": "No valid molecules were found to combine."}

        # Generate coordinates for the entire group
        # This automatically spaces them out so they don't overlap
        AllChem.Compute2DCoords(combined_mol)
        
        if not filename.endswith(".sdf"):
            filename += ".sdf"
        full_path = os.path.join(export_dir, filename)

        writer = Chem.SDWriter(full_path)
        writer.write(combined_mol)
        writer.close()

        return {
            "status": "success",
            "file_name": filename,
            "compounds": success_names,
            "path": os.path.abspath(full_path),
            "message": f"Reaction canvas created with {', '.join(success_names)}."
        }

    except Exception as e:
        return {"error": f"Reaction export failed: {str(e)}"}
    
schema_export_reaction_canvas = types.FunctionDeclaration(
    name="export_reaction_canvas",
    description="Merges multiple chemicals into a single drawing on one canvas. Best for side-by-side comparison or setting up reactions. Saves to an .sdf file.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "chemical_names": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="A list of chemical names to put on the canvas, e.g., ['Aspirin', 'Water']",
            ),
            "filename": types.Schema(
                type=types.Type.STRING,
                description="The name of the file to save (e.g., 'reaction_layout.sdf').",
            )
        },
        required=["chemical_names"]
    ),
)

def draw_reaction(reactants: list, products: list, reagents: list = None, filename: str = "reaction.sdf", **kwargs):
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    def get_mol(name):
        base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
        try:
            res = requests.get(f"{base_url}/name/{name}/property/SMILES/JSON", timeout=5)
            if res.status_code == 200:
                smiles = res.json()['PropertyTable']['Properties'][0]['SMILES']
                mol = Chem.MolFromSmiles(smiles)
                if mol:
                    AllChem.Compute2DCoords(mol)
                    return mol
        except Exception as e:
            print(f"DEBUG: Could not fetch {name}: {e}")
        return None

    combined = None
    spacing = 7.0 # If changing the spacing, change it here.

    def add_fragment(names, x_offset):
        nonlocal combined
        current_local_x = x_offset
        
        for name in names:
            mol = get_mol(name)
            if mol and mol.GetNumAtoms() > 0:
                mol.SetProp("_Name", name)
                
                # Ensure we have coordinates
                if mol.GetNumConformers() == 0:
                    AllChem.Compute2DCoords(mol)
                
                conf = mol.GetConformer()
                
                # --- THE ULTIMATE FIX: Manual Coordinate Shift ---
                # We bypass all Matrix/Transform modules and edit the Point3D directly
                for i in range(mol.GetNumAtoms()):
                    pos = conf.GetAtomPosition(i)
                    # Create a new point shifted by current_local_x
                    new_pos = (pos.x + float(current_local_x), pos.y, pos.z)
                    conf.SetAtomPosition(i, new_pos)
                
                if combined is None:
                    combined = mol
                else:
                    combined = Chem.CombineMols(combined, mol)
                
                current_local_x += spacing
        return current_local_x

    # 1. Position Reactants (Left)
    reactant_end_x = add_fragment(reactants, 0)
    
    # 2. Position Reagents (Middle)
    reagent_end_x = reactant_end_x
    if reagents:
        reagent_end_x = add_fragment(reagents, reactant_end_x + spacing)

    # 3. Position Products (Right)
    # Extra spacing (1.5x) to represent the reaction arrow gap
    add_fragment(products, reagent_end_x + (spacing * 1.2))

    if combined is None:
        return {"error": "No molecules were successfully retrieved."}

    # Save to file
    full_path = os.path.join(export_dir, filename if filename.endswith(".sdf") else f"{filename}.sdf")
    writer = Chem.SDWriter(full_path)
    writer.write(combined)
    writer.close()

    return {
        "status": "success",
        "path": os.path.abspath(full_path),
        "message": f"Successfully created reaction canvas: {os.path.basename(full_path)}"
    }

schema_draw_reaction = types.FunctionDeclaration(
    name="draw_reaction",
    description="Draws a full chemical reaction by positioning reactants on the left, reagents in the middle, and products on the right.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "reactants": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Names of starting materials (e.g. ['benzene', 'nitric acid'])"
            ),
            "products": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Names of final products (e.g. ['nitrobenzene'])"
            ),
            "reagents": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Names of catalysts or solvents (e.g. ['sulfuric acid'])"
            ),
            "filename": types.Schema(
                type=types.Type.STRING,
                description="Output filename (default 'reaction.sdf')"
            )
        },
        required=["reactants", "products"]
    ),
)