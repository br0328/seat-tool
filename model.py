
""" Global model and db functions
"""

from constant import *
from schema import *
import pandas as pd
import sqlite3
import os

glob_model = {
    'local_conn': None, # Global variable for local db connection (It keeps alive for the whole app process)
    'tab_callback': {}, # Callback functions for tab pages opening,
    'root': None
}

# Load Sqlite3 db if exists,
# Create a new one if not found
def load_or_create_db():
    if glob_model['local_conn'] is not None: return glob_model['local_conn']

    if not os.path.exists(local_db_path):
        conn = sqlite3.connect(local_db_path)
        cursor = conn.cursor()

        # Run `CREATE TABLE ...` queries for empty tables
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

# Return pandas DataFrame from a table
def load_table(tbl, order = None):
    order_str = '' if order is None else f" ORDER BY {order}"
    conn = load_or_create_db()
    
    df = pd.read_sql(f"SELECT * FROM {tbl}{order_str}", conn)
    return df

# Overwrite a table by pandas DataFrame object
def save_table(tbl, df):
    conn = load_or_create_db()
    res = True
    
    try:
        df.to_sql(tbl, conn, if_exists = 'replace', index = False)
    except Exception:
        res = False
    
    return res

def get_comment(comm_df, tid, mid, cid):
    for _, r in comm_df.iterrows():
        if int(r['tid']) == int(tid) and int(r['mid']) == int(mid) and int(r['cid']) == int(cid): return r['val']
    
    return None

def get_person(person_df, mid):
    try:
        for _, r in person_df.iterrows():
            if int(r['mid']) == int(mid): return r
    except Exception:
        pass
    
    return None
