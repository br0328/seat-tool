
""" No-Match Tab Page
"""

from tkinter import messagebox
from constant import *
from model import *
from util import *
from ui import *
import pandas as pd

page_model = {
    'backbone': None,
    'treeview': None,
    'column_info': [
        ('line', { 'title': 'Line Nr.' }),
        ('surname', { 'title': 'Surname' }),
        ('forename', { 'title': 'Forename' }),
        ('mid', { 'title': 'Member-ID' })
    ] + [
        (f"val{i}", { 'title': f"No-Match-{i + 1}", 'editable': True, 'dtype': int })
        for i in range(no_match_col_count)
    ]
}

def init_tab(notebook):
    tab = create_tab(notebook, 'No-Match', on_tab_selected)
    
    page_model['treeview'], _ = create_treeview(
        master = tab,
        column_info = page_model['column_info'],
        dbl_click_callback = on_treeview_dbl_clicked
    )
    create_control_panel(
        master = tab,
        button_info = {
            'Edit Line': { 'click': on_edit_line_clicked },
            'Save Database': { 'click': on_save_db_clicked }
        }
    )
    on_tab_selected()

def on_tab_selected():
    person_df = load_table('tbl_person', 'display')
    person_match_df = load_table('tbl_person_no_match')
    
    records = []
    
    for _, person in person_df.iterrows():
        mid = person['mid']
        r = [person['surname'], person['forename'], mid]
        v = [0] * no_match_col_count
        
        for _, pm in person_match_df.iterrows():
            if pm['mid'] == mid:
                v = [pm[f"val{i + 1}"] for i in range(no_match_col_count)]
                break
        
        records.append(tuple(r + v))
    
    df = pd.DataFrame(records, columns = ['surname', 'forename', 'mid'] + [f"val{i}" for i in range(no_match_col_count)])
    page_model['backbone'] = df
    
    update_treeview()

def on_treeview_dbl_clicked(tv, item):
    if not item:
        messagebox.showerror('Error', 'No row selected.')
        return

    values = tv.item(item, 'values')
    default_values = []
    
    for i, ci in enumerate(page_model['column_info']):
        key, info = ci
        v = values[i]
        
        if key.startswith('val'):
            v = int(v) if v != '' else 0
        
        default_values.append(v)
    
    show_entry_dlg(False, default_values, page_model['column_info'], on_edit, tags = (item, ))

def on_edit_line_clicked():
    tv = page_model['treeview']
    
    try:
        item = tv.selection()[0]
        on_treeview_dbl_clicked(tv, item)
    except Exception:
        messagebox.showerror('Error', 'Please select a row first.')

def on_save_db_clicked():
    df = page_model['backbone']
    records = []
    
    for _, row in df.iterrows():
        mid = row['mid']
        
        records.append(tuple(
            [mid] +
            [get_int_nzoe(row[f"val{i}"]) for i in range(no_match_col_count)]
        ))            
    
    person_match_df = pd.DataFrame(records, columns = ['mid'] + [f"val{i + 1}" for i in range(no_match_col_count)])
    
    if not save_table('tbl_person_no_match', person_match_df):
        messagebox.showerror('Error', 'Failed to save tbl_person_no_match.')
        return

    messagebox.showinfo('Success', 'Saved database successfully.')
    
def on_edit(dlg, entries, tags):
    tv = page_model['treeview']
    column_info = page_model['column_info']
    df = page_model['backbone']
    
    item = tags[0]
    idx = int(tv.item(item, 'values')[0]) - 1
    rec_dict = {}
    
    for key, evar in entries.items():
        ci = find_info_by_column_key(column_info, key)
        v = evar.get()
        rv, err = check_ci_validation(ci, v)
        
        if err is not None:
            messagebox.showerror('Entry Error', err)
            dlg.destroy()
            return
        else:
            rec_dict[key] = rv
    
    for key, rv in rec_dict.items():
        df.at[idx, key] = rv

    dlg.destroy()
    update_treeview()

def update_treeview(callback = None):
    tv = page_model['treeview']
    tv.delete(*tv.get_children())

    df = page_model['backbone']
        
    for i, row in df.iterrows():
        tv.insert(
            '', 'end', values = tuple(
                [i + 1, row['surname'], row['forename'], row['mid']] +
                [int_nonzero_or_empty(row[f"val{k}"]) for k in range(no_match_col_count)]
            )
        )

    if callback: callback()