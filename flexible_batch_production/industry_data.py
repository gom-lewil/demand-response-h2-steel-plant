from yaml import safe_load

def get_input_dict(file_path='0_input_data/equipment_input_data.dat'):
    with open(file_path, 'r') as f:
        return safe_load(f)
