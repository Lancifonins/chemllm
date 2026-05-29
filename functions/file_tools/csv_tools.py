import pandas as pd
import os
from google.genai import types

def search_csv(column_name, search_term,file_path="input_files/inv.csv"):
    """Reads a CSV and returns rows where the column matches the search term."""
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
        
    try:
        df = pd.read_csv(file_path)
        
        # Check if the column actually exists to prevent crashes
        if column_name not in df.columns:
            return {"error": f"Column '{column_name}' does not exist. Available columns: {list(df.columns)}"}
            
        # Perform a case-insensitive text search
        # We convert to string to ensure numbers don't break the .str accessor
        results = df[df[column_name].astype(str).str.contains(str(search_term), case=False, na=False)]
        
        if results.empty:
            return {"success": True, "message": f"No records found for '{search_term}' in '{column_name}'."}
            
        # Convert the filtered dataframe back to a dictionary for Gemini to read
        return {"success": True, "data": results.to_dict(orient="records")}
        
    except Exception as e:
        return {"error": f"Failed to read CSV: {str(e)}"}

schema_search_csv = types.FunctionDeclaration(
    name="search_csv",
    description="Searches a local CSV file for a specific term within a specific column and returns the matching rows. Use this to look up inventory, logs, or datasets.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(type=types.Type.STRING, description="The local path to the CSV file (e.g., 'data/inventory.csv')."),
            "column_name": types.Schema(type=types.Type.STRING, description="The exact name of the column to search in."),
            "search_term": types.Schema(type=types.Type.STRING, description="The value or text to search for.")
        },
        required=["file_path", "column_name", "search_term"]
    )
)

def check_inventory(cas_number, **kwargs):
    """A specialized wrapper that only checks the local lab inventory for a CAS number."""
    file_path = "input_files/inv.csv"
    
    # We reuse the generic search_csv logic you already wrote!
    result = search_csv(file_path=file_path, column_name="CAS Number", search_term=cas_number)
    
    # Make the AI's response a bit more natural if it's missing
    if result.get("success") and "message" in result:
         return {"inventory_status": f"CAS {cas_number} is NOT in the lab inventory."}
         
    return result

# --- NEW TAILORED SCHEMA ---
schema_check_inventory = types.FunctionDeclaration(
    name="check_inventory",
    description="Checks the local laboratory inventory to see if a specific chemical is in stock.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "cas_number": types.Schema(
                type=types.Type.STRING, 
                description="The strict CAS number of the chemical to look up (e.g., '58-08-2')."
            )
        },
        required=["cas_number"]
    )
)
