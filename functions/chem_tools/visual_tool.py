import os
import re
import requests

from google import genai
from google.genai import types
import DECIMER
from DECIMER import predict_SMILES

from rdkit import Chem
from rdkit.Chem import AllChem

import urllib.parse

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

def image_to_cas(image_path, **kwargs):
    """Extracts a structure from an image and securely looks up its CAS via PubChem."""
    try:
        # Get the SMILES
        smiles = predict_SMILES(image_path)
        if not smiles:
            return {"error": "DECIMER could not extract a structure from this image."}
            
        encoded_smiles = urllib.parse.quote(smiles)
        
        # Use PubChem to standardise the SMILES and get the exact CID
        cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{encoded_smiles}/cids/JSON"
        cid_response = requests.get(cid_url)
        
        if cid_response.status_code != 200:
            return {"error": f"PubChem could not resolve this SMILES into a CID: {smiles}"}
            
        cids = cid_response.json().get('IdentifierList', {}).get('CID', [])
        if not cids:
            return {"error": "No CID found for this structure."}
            
        primary_cid = cids[0]

        synonym_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{primary_cid}/synonyms/JSON"
        syn_response = requests.get(synonym_url)
        
        if syn_response.status_code != 200:
             return {"error": f"Found structure (CID {primary_cid}), but could not retrieve synonyms."}
             
        synonyms = syn_response.json()['InformationList']['Information'][0].get('Synonym', [])
        
        cas_pattern = re.compile(r'^[1-9]\d{1,6}-\d{2}-\d$')
        
        # Filter the synonym list and remove duplicates
        cas_numbers = list(set([syn for syn in synonyms if cas_pattern.match(syn)]))
        
        if cas_numbers:
            return {
                "success": True,
                "smiles_extracted": smiles,
                "pubchem_cid": primary_cid,
                "cas_numbers": cas_numbers[:5] # Return top 5 matches to avoid overwhelming the AI
            }
        else:
            return {
                "error": f"Structure resolved (CID: {primary_cid}), but no CAS numbers were found in the database.",
                "smiles_extracted": smiles
            }
            
    except Exception as e:
        return {"error": str(e)}

schema_image_to_cas = types.FunctionDeclaration(
    name="image_to_cas",
    description="Analyzes an image of a chemical structure, extracts its SMILES string, and queries the NIH database to find its official CAS registry number.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "image_path": types.Schema(
                type=types.Type.STRING, 
                description="The local file path to the input image."
            )
        },
        required=["image_path"]
    )
)