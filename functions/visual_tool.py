import os
from google import genai
from google.genai import types
import DECIMER
from DECIMER import predict_SMILES
from rdkit import Chem
from rdkit.Chem import AllChem

def image_to_cdxml(image_path, export_file="image.mol",**kwargs):
    # 1. Setup the export directory securely
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        
    full_path = os.path.join(export_dir, os.path.basename(export_file))

    try:
        # 2. Extract SMILES via DECIMER
        smiles = predict_SMILES(image_path)

        # 3. RDKit Conversion & Safety Catch
        mol = Chem.MolFromSmiles(smiles)
        
        if mol is None:
            return {"error": f"DECIMER predicted an invalid structure: {smiles}"}

        # 4. THE FIX: Generate layout and write as a .mol file
        AllChem.Compute2DCoords(mol)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(Chem.MolToMolBlock(mol))

        return {
            "success": True, 
            "smiles": smiles,
            "saved_path": full_path
        }
        
    except Exception as e:
        return {"error": str(e)}
    
schema_image_to_cdxml = types.FunctionDeclaration(
    name="image_to_chemdraw",
    description="Converts an image of a chemical structure into an editable .mol file, which can be natively opened in ChemDraw. Use this when the user asks to extract a molecule from an image.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "image_path": types.Schema(
                type=types.Type.STRING, 
                description="The local file path to the input image (e.g., 'screenshot.png')."
            ),
            "export_file": types.Schema(
                type=types.Type.STRING, 
                description="The filename for the output file. MUST end with .mol (e.g., 'catalyst.mol')."
            )
        },
        required=["image_path"]
    )
)