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
#RDLogger.DisableLog('rdApp.*')

def search_by_structure_file(file_path: str, max_results: int = 10, **kwargs):
    """
    Reads a ChemDraw (.cdxml) or SDF file and uses its structure to 
    perform a PubChem substructure search.
    """
    try:
        # 1. Parse the file into an RDKit molecule object
        if file_path.endswith('.cdxml'):
            # CDXML is XML-based; RDKit's Molfiles/SMILES parsers are usually separate
            # We use RDKit's internal CDXML support (if available) or convert via SMILES
            mol = Chem.MolFromCDXMLFile(file_path)
        elif file_path.endswith('.sdf'):
            suppl = Chem.SDMolSupplier(file_path)
            mol = next(suppl) if suppl else None
        else:
            return {"error": "Unsupported format. Please use .cdxml or .sdf"}

        if not mol:
            return {"error": f"Failed to parse structure from {file_path}"}

        # 2. Convert to SMILES for the API query
        query_smiles = Chem.MolToSmiles(mol)
        
        # 3. Submit to PubChem via POST (The most stable method)
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/substructure/smiles/JSON"
        res = requests.post(url, data={'smiles': query_smiles}, timeout=15)
        
        if res.status_code != 202:
            return {"error": f"PubChem rejected structure: {res.text}"}
        
        list_key = res.json().get('Waiting', {}).get('ListKey')
        
        # 4. Polling for results
        result_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/listkey/{list_key}/cids/JSON"
        cids = []
        for _ in range(10):
            time.sleep(2)
            poll_res = requests.get(result_url)
            if poll_res.status_code == 200:
                cids = poll_res.json().get('IdentifierList', {}).get('CID', [])[:max_results]
                break
        
        if not cids:
            return {"error": "No matching compounds found for this structure."}

        # 5. Resolve CIDs to Names
        names = []
        for cid in cids:
            n_res = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/description/JSON")
            if n_res.status_code == 200:
                title = n_res.json()['InformationList']['Information'][0].get('Title')
                if title: names.append(title)
        
        return {"compounds_found": names, "query_smiles": query_smiles}

    except Exception as e:
        return {"error": f"Structural search error: {str(e)}"}
    
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
    description="Finds compounds in PubChem using a local ChemDraw (.cdxml) or SDF file as the structural query.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(type=types.Type.STRING, description="The path to the query file (e.g., 'query.cdxml')."),
            "max_results": types.Schema(type=types.Type.INTEGER, description="Number of results to return.")
        },
        required=["file_path"]
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

