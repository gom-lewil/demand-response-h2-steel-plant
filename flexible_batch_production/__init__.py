"""Framework for optimising dispatch of batch processes"""
__version__ = "0.1"

from .construct import multi_equipment_model
from .generation_data import get_wind_farm_output
from .industry_data import get_input_dict
from .solve import solve_model, safe_model_results
from .analyse import model_summary_plot, loaded_model_summary_plot, sorted_model_summary_plot, hourlize_model_data
from .load import load_model, fill_empty_equipments
