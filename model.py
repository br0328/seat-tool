
from constant import *
from schema import *
import pandas as pd
import sqlite3
import os

glob_model = {
    'local_conn': None,
    'tab_callback': {}
}

def load_or_create_db():
    if glob_model['local_conn'] is not None: return glob_model['local_conn']

    if not os.path.exists(local_db_path):
        conn = sqlite3.connect(local_db_path)
        cursor = conn.cursor()

        for _, sch in schemas.items():
            cursor.execute(sch)

        conn.commit()
    else:
        conn = sqlite3.connect(local_db_path)

    glob_model['local_conn'] = conn    
    return conn

def commit_db():
    conn = glob_model['local_conn']
    
    if conn is None: return
    conn.commit()    

def close_db(no_commit = False):
    conn = glob_model['local_conn']
    
    if conn is None: return
    if not no_commit: conn.commit()
        
    glob_model['local_conn'] = None
    conn.close()

def load_table(tbl):
    conn = load_or_create_db()
    df = pd.read_sql(f'SELECT * FROM {tbl}', conn)
    return df

def save_table(tbl, df):
    conn = load_or_create_db()
    res = True
    
    try:
        df.to_sql(tbl, conn, if_exists = 'replace', index = False)
    except Exception:
        res = False
    
    return res