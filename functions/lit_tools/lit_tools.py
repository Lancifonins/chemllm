import requests

from google import genai
from google.genai import types

import streamlit as st

from datetime import datetime, timedelta

from modules.author import *

def get_paper_link_by_doi(doi: str, **kwargs):
    """
    Resolves a DOI to its official publisher webpage and retrieves basic metadata.
    Example DOI: '10.1021/jacs.1c04015'
    """
    # Clean the DOI (strip 'doi:' or 'https://doi.org/' if the user pasted the full URL)
    clean_doi = doi.split("doi.org/")[-1].replace("doi:", "").strip()
    
    # 1. The Direct URL (Standard Resolver)
    webpage_url = f"https://doi.org/{clean_doi}"
    
    # 2. Fetch Metadata from Crossref (to confirm it's the right paper)
    api_url = f"https://api.crossref.org/v1/works/{clean_doi}"
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json().get('message', {})
            title = data.get('title', ["Unknown Title"])[0]
            journal = data.get('container-title', ["Unknown Journal"])[0]
            year = data.get('published-print', {}).get('date-parts', [[None]])[0][0]
            
            return {
                "status": "Success",
                "title": title,
                "journal": journal,
                "year": year,
                "url": webpage_url,
                "message": f"Found '{title}' in {journal}."
            }
        else:
            # Fallback if metadata fails but the link is still valid
            return {
                "status": "Link Only",
                "url": webpage_url,
                "message": "DOI link generated, but metadata could not be retrieved."
            }
            
    except Exception as e:
        return {"error": f"Resolution failed: {str(e)}"}
    
schema_get_paper_link_by_doi = types.FunctionDeclaration(
    name="get_paper_link_by_doi",
    description="Converts a DOI (Digital Object Identifier) into a direct link to the paper's webpage and provides the Title and Journal.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "doi": types.Schema(
                type=types.Type.STRING, 
                description="The DOI string (e.g., '10.1038/s41586-021-03444-y')."
            )
        },
        required=["doi"]
    ),
)

def search_author_recent_work(orcid: str = None, name: str = None, days_back: int = 180, **kwargs):
    """
    ORCID-FIRST DISCOVERY TOOL:
    If only a name is provided, the agent MUST ask for an ORCID.
    Uses 'from-created-date' for 2026 ASAP paper precision.
    """
    # THE GATEKEEPER: Prioritize ORCID above all else
    if not orcid:
        if name:
            # Instead of searching, let the agent to ask the user
            return {
                "error": "ORCID required for high-precision tracking.",
                "instruction": f"I see you want to search for '{name}'. To ensure I don't show you papers from a different researcher with the same name, please provide their 16-digit ORCID iD first."
            }
        return {"error": "I need an ORCID to perform a precise 2026 search."}

    # If ORCID is present, proceed with the 'Time-Proof' logic
    url = "https://api.crossref.org/works"
    now = datetime.now()
    created_threshold = (now - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Filter strictly by ORCID and recently created records
    params = {
        "filter": f"orcid:{orcid},from-created-date:{created_threshold}",
        "rows": 20
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        items = response.json().get('message', {}).get('items', [])
        
        extracted = []
        for i in items:
            # DATE PARSING: Get the most authoritative date for 2026
            p_date = i.get('published-online') or i.get('published-print') or i.get('issued') or i.get('created')
            date_parts = p_date.get('date-parts', [[0, 0, 0]])[0]
            
            sort_key = list(date_parts)
            while len(sort_key) < 3: sort_key.append(1)
            
            # SAFETY GATE: 2025/2026 science only. Change the timegate here
            if sort_key[0] < (now.year - 1):
                continue

            extracted.append({
                "title": i.get('title', ["No Title"])[0],
                "doi": i.get('DOI'),
                "journal": i.get('container-title', ["-"])[0],
                "date_array": sort_key,
                "display_date": "-".join(map(str, date_parts))
            })

        # PERFECT CHRONOLOGY: Sort by [Year, Month, Day] Descending
        extracted.sort(key=lambda x: x['date_array'], reverse=True)
        
        return {
            "orcid_searched": orcid,
            "results": extracted[:5]
        }
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

def manage_watchlist(action: str, orcid: str = None, name: str = None, affiliation: str = None, days_back: int = 500, **kwargs):
    """
    Unified management of your research tracking registry (ORCID-primary).
    Actions: 
    - 'add': Tracks a researcher (Requires ORCID and Name).
    - 'remove': Stops tracking (Requires ORCID).
    - 'list': Shows everyone on your watchlist.
    - 'update': Scans the entire registry for new 2026 publications.
    """

    #Check the user info.
    username = st.session_state.get('username')
    if not username:
        return {"error": "System Error: No active user session detected."}
    registry = AuthorRegistry(username=username)
    
    if action == "update":
        # Scans registry using the ORCID-loop in registry.check_all_updates
        return registry.check_all_updates(days_back=days_back)
    
    elif action == "add":
        if not orcid or not name:
            return {"error": "Both ORCID and Name are required to add a researcher to the primary registry."}
        
        success = registry.add_author(orcid=orcid, name=name, affiliation=affiliation)
        return {
            "message": f"Successfully added {name} ({orcid}) to your tracking registry." 
            if success else f"Researcher with ORCID {orcid} is already being tracked."
        }
    
    elif action == "remove":
        if not orcid:
            return {"error": "I need an ORCID to uniquely identify who to remove."}
        
        success = registry.remove_author(orcid) 
        
        if success:
            return {"message": f"Successfully removed researcher with ORCID {orcid}."}
        else:
            return {"message": f"ORCID {orcid} was not found in your registry."}
    
    elif action == "clear":
        return {"message": registry.clear_registry()}
    
    elif action == "list":
        tracked = registry.watchlist
        if not tracked:
            return {"message": "Your watchlist is currently empty."}
        
        return {
            "count": len(tracked),
            "authors": [
                {
                    "orcid": oid, 
                    "name": data.get('name'), 
                    "affiliation": data.get('affiliation', 'Global')
                } 
                for oid, data in tracked.items()
            ]
        }
    
# Tool for Step 1: Discovery
schema_search_author_recent_work = types.FunctionDeclaration(
    name="search_author_recent_work",
    description="High-precision 2026 paper discovery. MANDATORY: You must prioritize ORCID. If the user gives only a name, you must stop and ask them for the ORCID to ensure search accuracy and avoid name-collision errors.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "orcid": types.Schema(type=types.Type.STRING, description="The unique 16-digit researcher ID (e.g., 0000-0003-3560-5760)."),
            "name": types.Schema(type=types.Type.STRING, description="Author name (used only to prompt the user if ORCID is missing)."),
            "days_back": types.Schema(type=types.Type.INTEGER, description="Default is 180 to catch the full 2025/2026 window.")
        }
    )
)

# Tool for Steps 2 & 3: Management
schema_manage_watchlist = types.FunctionDeclaration(
    name="manage_watchlist",
    description="Manages your permanent author registry. Use 'clear' to delete the entire watchlist at once.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "action": types.Schema(
                type=types.Type.STRING, 
                enum=["add", "remove", "list", "update", "clear"] # Added 'clear'
            ),
            # Other properties remain the same...
        },
        required=["action"]
    )
)