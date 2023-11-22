
import pandas as pd

def regularize_dict(d, default_dict):
    for k, v in default_dict.items():
        if k not in d.keys(): d[k] = v

def find_info_by_column_key(column_info, key):
    for k, ci in column_info:
        if key == k: return ci
    
    return None

def check_ci_validation(ci, val):
    res = val
    
    if ci['dtype'] == int:
        try:
            res = int(val)
        except Exception:
            return 0, f"The field `{ci['title']}` requires integer value."
    
    return res, None

def null_or(val, def_val):
    if pd.isna(val) or pd.isnull(val): return def_val
    return val