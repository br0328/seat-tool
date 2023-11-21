
def regularize_dict(d, default_dict):
    for k, v in default_dict.items():
        if k not in d.keys(): d[k] = v
