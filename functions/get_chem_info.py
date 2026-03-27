import requests
import re
from google import genai
from google.genai import types

def get_compound_by_cas(cas_number:str,**kwargs) -> dict:
    """
    Search PubChem for a compound using its CAS Registry Number.
    """
    # PubChem URL for CAS to CID (Compound ID) lookup
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    search_url = f"{base_url}/compound/name/{cas_number}/JSON"

    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status() # Raise error if request fails
        
        data = response.json()
        
        # Extract basic info
        compounds = data.get('PC_Compounds', [])
        if not compounds:
            return f"No compound found for CAS: {cas_number}"

        # Get the Compound ID (CID)
        cid = compounds[0].get('id', {}).get('id', {}).get('cid')
        
        # Now let's get the common name and molecular weight
        detail_url = f"{base_url}/compound/cid/{cid}/property/Title,MolecularWeight,MolecularFormula/JSON"
        detail_res = requests.get(detail_url)
        detail_data = detail_res.json()
        
        properties = detail_data['PropertyTable']['Properties'][0]
        
        return {
            "name": properties.get('Title'),
            "formula": properties.get('MolecularFormula'),
            "molecular_weight": properties.get('MolecularWeight'),
            "pubchem_cid": cid,
            "link": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
        }

    except Exception as e:
        return f"Error connecting to PubChem: {str(e)}"
    
schema_get_compound_by_cas = types.FunctionDeclaration(
    name="get_compound_by_cas",
    description="Get chemical compound information by its CAS number, including its common name, molecular formula, molecular weight, and a link to its PubChem page.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "cas_number": types.Schema(
                type=types.Type.STRING,
                description="The CAS Registry Number of the compound (e.g., '50-00-0' for Formaldehyde).",
            ),
        },
        required=["cas_number"]
    ),
)


# In functions/get_chem_info.py

def get_compound_by_name(name: str, **kwargs) -> dict:
    """
    Retrieves chemical information including CAS, weight, formula, and SMILES using a name.
    """

    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    
    try:
        # 1. Get CID from Name
        res = requests.get(f"{base_url}/compound/name/{name}/JSON", timeout=5)
        res.raise_for_status()
        cid = res.json()['PC_Compounds'][0]['id']['id']['cid']
        
        # 2. Get Properties (Title, Weight, Formula, SMILES)
        prop_url = f"{base_url}/compound/cid/{cid}/property/Title,MolecularWeight,MolecularFormula,CanonicalSMILES/JSON"
        prop_res = requests.get(prop_url, timeout=5)
        props = prop_res.json()['PropertyTable']['Properties'][0]

        # 3. Get Synonyms to find the CAS Number
        syn_url = f"{base_url}/compound/cid/{cid}/synonyms/JSON"
        syn_res = requests.get(syn_url, timeout=5)
        synonyms = syn_res.json().get('InformationList', {}).get('Information', [{}])[0].get('Synonym', [])

        # Search the synonyms for a CAS pattern
        cas_number = "Not found"
        for syn in synonyms:
            if re.match(r'^\d{2,7}-\d{2}-\d$', syn):
                cas_number = syn
                break

        # 4. Return the consolidated object
        return {
            "name": props.get("Title"),
            "molecular_weight": props.get("MolecularWeight"),
            "formula": props.get("MolecularFormula"),
            "smiles": props.get("CanonicalSMILES"),
            "cas_number": cas_number, # <-- Added this
            "pubchem_cid": cid
        }

    except Exception as e:
        return {"error": f"Search failed for '{name}': {str(e)}"}
    
schema_get_compound_by_name = types.FunctionDeclaration(
    name="get_compound_by_name",
    description="Get chemical compound information by its common or IUPAC name, including its CAS number, molecular weight, formula, SMILES, and a link to its PubChem page.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "name": types.Schema(
                type=types.Type.STRING,
                description="The common or IUPAC name of the compound (e.g., 'Aspirin' or 'Sodium Chloride').",
            ),
        },
        required=["name"]
    ),
)
       
def get_ghs_hazards(name_or_cas: str,**kwargs) -> dict:
    """
    Retrieves GHS hazard statements (e.g., 'H225: Highly flammable liquid') for a compound.
    
    Args:
        name_or_cas: The name or CAS number of the chemical.
    """
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"
    
    try:
        # First, we need the CID
        search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name_or_cas}/JSON"
        cid = requests.get(search_url).json()['PC_Compounds'][0]['id']['id']['cid']
        
        # Now get the 'PugView' which contains the GHS classification
        view_url = f"{base_url}/{cid}/JSON?heading=GHS+Classification"
        res = requests.get(view_url, timeout=5).json()
        
        # Navigate the complex PubChem JSON tree for GHS
        # This is a simplified extraction of the 'H-Statements'
        sections = res['Record']['Section'][0]['Information'][0]['Value']['StringWithMarkup']
        hazards = [item['String'] for item in sections if "H" in item['String']]

        return {
            "compound": name_or_cas,
            "ghs_hazards": hazards[:5], # Return the top 5 most relevant
            "source": "PubChem GHS"
        }
    except Exception:
        return {"error": f"GHS data not found for {name_or_cas}."}
    
schema_get_ghs_hazards = types.FunctionDeclaration(
    name="get_ghs_hazards",
    description="Get GHS hazard statements for a compound by its name or CAS number.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "name_or_cas": types.Schema(
                type=types.Type.STRING,
                description="The common name, IUPAC name, or CAS number of the compound (e.g., 'Aspirin' or '50-00-0').",
            ),
        },
        required=["name_or_cas"]
    ),
)

import requests
import re

def get_cas_from_cid(cid: int, **kwargs):
    """
    Stand-alone agent tool to resolve a CID to a CAS number.
    """
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {"error": f"PubChem ID {cid} not found or API unavailable."}
            
        data = response.json()
        synonyms = data.get('InformationList', {}).get('Information', [{}])[0].get('Synonym', [])
        
        # Standard CAS pattern: [2-7 digits]-[2 digits]-[1 digit]
        cas_pattern = re.compile(r'^\d{2,7}-\d{2}-\d$')
        
        # Filter synonyms for the first matching CAS format
        cas_numbers = [s for s in synonyms if cas_pattern.match(s)]
        
        if cas_numbers:
            return {
                "cid": cid,
                "cas_number": cas_numbers[0],
                "all_cas_found": cas_numbers # Sometimes there are multiple
            }
        else:
            return {"cid": cid, "message": "No CAS number found in PubChem synonyms."}
            
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}
    
schema_get_cas_from_cid = types.FunctionDeclaration(
    name="get_cas_from_cid",
    description="Converts a PubChem Compound ID (CID) into a Chemical Abstracts Service (CAS) registry number by searching through synonyms.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "cid": types.Schema(
                type=types.Type.INTEGER, 
                description="The PubChem CID to look up (e.g., 2244 for Aspirin)."
            )
        },
        required=["cid"]
    ),
)

def check_commercial_availability(identifier, **kwargs):
    """
    Checks if a chemical is commercially available using either a 
    PubChem CID (int) or a CAS Number (str).
    """
    cid = None
    
    # 1. Handle Input Type
    if isinstance(identifier, str) and re.match(r'^\d{2,7}-\d{2}-\d$', identifier):
        # Resolve CAS to CID first
        res = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{identifier}/cids/JSON")
        if res.status_code == 200:
            cid = res.json().get('IdentifierList', {}).get('CID', [None])[0]
        else:
            return {"error": f"Could not find a CID for CAS {identifier}"}
    elif isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        cid = int(identifier)
    else:
        return {"error": "Invalid input. Please provide a CID (int) or CAS (str: ###-##-#)."}

    # 2. Query PubChem for Data Sources/Vendors
    # This endpoint specifically lists the providers of the substance
    sources_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/sources/JSON"
    
    try:
        response = requests.get(sources_url, timeout=10)
        if response.status_code != 200:
            return {"cid": cid, "available": False, "message": "No vendor data found."}
            
        data = response.json()
        # PubChem separates sources into 'Category'. We want 'Chemical Vendors'.
        sources = data.get('InformationList', {}).get('Information', [])
        
        vendors = []
        for entry in sources:
            # Not all sources are vendors (some are databases or government labs)
            # We check the 'RegistryName' or the vendor list if available
            source_name = entry.get('SourceName')
            if source_name:
                vendors.append(source_name)
        
        # We limit the return list so the agent isn't overwhelmed by 500 vendors
        return {
            "cid": cid,
            "is_commercially_available": len(vendors) > 0,
            "vendor_count": len(vendors),
            "top_vendors": vendors[:10],
            "pubchem_source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}#section=Chemical-Vendors"
        }
            
    except Exception as e:
        return {"error": f"Availability check failed: {str(e)}"}
    
schema_check_commercial_availability = types.FunctionDeclaration(
    name="check_commercial_availability",
    description="Determines if a chemical is available for purchase. Accepts either a PubChem CID or a CAS Number.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "identifier": types.Schema(
                type=types.Type.STRING, 
                description="The identifier to check. Can be a CAS number (e.g., '50-78-2') or a CID (e.g., '2244')."
            )
        },
        required=["identifier"]
    ),
)