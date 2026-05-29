import os
from google import genai
from google.genai import types

#file processing tools
from functions.file_tools.get_files_info import *
from functions.file_tools.get_file_content import *
from functions.file_tools.run_python_file import *
from functions.file_tools.write_file import *
from functions.file_tools.csv_tools import *

#chemistry processing tools
from functions.chem_tools.get_chem_info import *
from functions.chem_tools.chem_files import *
from functions.chem_tools.chem_reactions import *
from functions.chem_tools.chem_grids import *
from functions.chem_tools.chem_discovery import *
from functions.chem_tools.chem_file_utils import *
from functions.chem_tools.visual_tool import *

#literature searching tools
from functions.lit_tools.lit_tools import *



available_functions = types.Tool(
    function_declarations=[
        #file processing tools
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
        schema_search_csv,
        schema_check_inventory,
        #chemistry processing tools
        schema_get_compound_by_cas,
        schema_get_compound_by_name,
        schema_get_ghs_hazards,
        schema_get_compound_density,
        schema_export_to_chemdraw,
        schema_read_chemdraw_file,
        schema_batch_export_sdfs,
        schema_export_combined_canvas,
        schema_export_reaction_canvas,
        schema_draw_reaction,
        schema_export_chemical_grid,
        schema_search_by_structure_file,
        schema_get_compounds_by_category,
        schema_read_chemdraw_input,
        schema_get_input_structure_info,
        schema_get_cas_from_cid,
        schema_check_commercial_availability,
        schema_image_to_cdxml,
        #literature searching tools
        schema_get_paper_link_by_doi,
        schema_search_author_recent_work,
        schema_manage_watchlist,
                          ],
)

call_function_map = {
    #file processing tools
    "get_file_content": get_file_content,
    "get_files_info": get_files_info,
    "run_python_file": run_python_file,
    "write_file": write_file,
    "search_csv": search_csv,
    "check_inventory": check_inventory,
    #chemistry processing tools
    "get_compound_by_cas": get_compound_by_cas,
    "get_compound_by_name": get_compound_by_name,
    "get_ghs_hazards": get_ghs_hazards,
    "get_compound_density": get_compound_density,
    "export_to_chemdraw": export_to_chemdraw,
    "read_chemdraw_file": read_chemdraw_file,
    "batch_export_sdfs": batch_export_sdfs,
    "export_combined_canvas": export_combined_canvas,
    "draw_reaction": draw_reaction,
    "export_reaction_canvas": export_reaction_canvas,
    "export_chemical_grid": export_chemical_grid,
    "search_by_structure_file": search_by_structure_file,
    "get_compounds_by_category": get_compounds_by_category,
    "read_chemdraw_input": read_chemdraw_input,
    "get_input_structure_info": get_input_structure_info,
    "get_cas_from_cid": get_cas_from_cid,
    "check_commercial_availability": check_commercial_availability,
    "image_to_cdxml": image_to_cdxml,
    #literature searching tools
    "get_paper_link_by_doi": get_paper_link_by_doi,
    "search_author_recent_work": search_author_recent_work,
    "manage_watchlist": manage_watchlist,
}