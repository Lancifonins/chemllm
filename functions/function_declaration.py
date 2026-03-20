import os
from google import genai
from google.genai import types
from functions.get_files_info import *
from functions.get_file_content import *
from functions.run_python_file import *
from functions.write_file import *
from functions.get_chem_info import *
from functions.chem_files import *
from functions.chem_reactions import *
from functions.chem_grids import *
from functions.chem_discovery import *
from functions.chem_file_utils import *

available_functions = types.Tool(
    function_declarations=[schema_get_files_info,
                           schema_get_file_content,
                           schema_run_python_file,
                           schema_write_file,
                           schema_get_compound_by_cas,
                           schema_get_compound_by_name,
                           schema_get_ghs_hazards,
                           schema_export_to_chemdraw,
                           schema_read_chemdraw_file,
                           schema_batch_export_sdfs,
                           schema_export_combined_canvas,
                           schema_export_reaction_canvas,
                           schema_draw_reaction,
                           schema_export_chemical_grid,
                           schema_search_by_structure_file,
                           schema_get_compounds_by_category,
                           schema_read_chemdraw_input
                          ],
)

call_function_map = {
    "get_file_content": get_file_content,
    "get_files_info": get_files_info,
    "run_python_file": run_python_file,
    "write_file": write_file,
    "get_compound_by_cas": get_compound_by_cas,
    "get_compound_by_name": get_compound_by_name,
    "get_ghs_hazards": get_ghs_hazards,
    "export_to_chemdraw": export_to_chemdraw,
    "read_chemdraw_file": read_chemdraw_file,
    "batch_export_sdfs": batch_export_sdfs,
    "export_combined_canvas": export_combined_canvas,
    "draw_reaction": draw_reaction,
    "export_reaction_canvas": export_reaction_canvas,
    "export_chemical_grid": export_chemical_grid,
    "search_by_structure_file": search_by_structure_file,
    "get_compounds_by_category": get_compounds_by_category,
    "read_chemdraw_input": read_chemdraw_input
}