from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import rdBase
from rdkit import RDLogger
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
import os
import requests
import time
import urllib.parse
from google import genai
from google.genai import types
from functions.get_chem_info import *
from functions.chem_files import *
from functions.chem_file_utils import *
#RDLogger.DisableLog('rdApp.*')

def search_by_structure_file(max_results: int = 5, **kwargs):
    """
    Finds compounds in PubChem containing the drawn substructure 
    and resolves their names AND CAS numbers.
    """
    mol, error = read_chemdraw_input()
    if error:
        return {"error": error}

    try:
        query_smiles = Chem.MolToSmiles(mol)
        
        # 1. Start Substructure Search
        search_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/substructure/smiles/JSON"
        res = requests.post(search_url, data={'smiles': query_smiles}, timeout=15)
        if res.status_code != 202:
            return {"error": f"Search rejected: {res.text}"}
        
        list_key = res.json().get('Waiting', {}).get('ListKey')
        
        # 2. Poll for CIDs
        cids_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/listkey/{list_key}/cids/JSON"
        cids = []
        for _ in range(10):
            time.sleep(2)
            poll = requests.get(cids_url)
            if poll.status_code == 200:
                cids = poll.json().get('IdentifierList', {}).get('CID', [])[:max_results]
                break
        
        if not cids:
            return {"message": "No matches found.", "smiles": query_smiles}

        # 3. Resolve names and CAS numbers
        results = []
        for cid in cids:
            # Get Name
            name_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/description/JSON"
            name_res = requests.get(name_url)
            name = "Unknown"
            if name_res.status_code == 200:
                info = name_res.json().get('InformationList', {}).get('Information', [{}])[0]
                name = info.get('Title', "Unknown")
            
            # Get CAS using our helper
            cas = get_cas_from_cid(cid)
            
            results.append({
                "name": name,
                "cas_number": cas,
                "pubchem_cid": cid
            })
        
        return {
            "query_smiles": query_smiles,
            "matches": results
        }

    except Exception as e:
        return {"error": str(e)}
    
def get_compounds_by_category(category: str, count: int = 10, **kwargs):
    """Finds compounds for a general class like 'Phenols' or 'Amino Acids'."""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{category}/cids/JSON"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return {"error": "Category not found."}
        cids = res.json().get('IdentifierList', {}).get('CID', [])[:count]
        
        names = []
        for cid in cids:
            n_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/description/JSON"
            n_res = requests.get(n_url)
            if n_res.status_code == 200:
                names.append(n_res.json()['InformationList']['Information'][0].get('Title'))
        return {"compounds": names}
    except Exception as e:
        return {"error": str(e)}
    
# Tool 1: The Substructure Search
schema_search_by_structure_file = types.FunctionDeclaration(
    name="search_by_structure_file",
    description="Finds compounds in PubChem that contain the substructure drawn in the input file. Returns names, CIDs, and CAS numbers.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "max_results": types.Schema(type=types.Type.INTEGER, description="Limit of compounds to return.")
        }
    ),
)

# Tool 2: The Category Search (e.g., 'Amino Acids')
schema_get_compounds_by_category = types.FunctionDeclaration(
    name="get_compounds_by_category",
    description="Fetches a set of compounds belonging to a specific biological or chemical class.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "category": types.Schema(type=types.Type.STRING, description="e.g. 'Amino Acids', 'Flavonoids'"),
            "count": types.Schema(type=types.Type.INTEGER)
        },
        required=["category"]
    ),
)

