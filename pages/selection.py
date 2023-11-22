
""" Selection Tab Page
"""

from tkinter import filedialog, messagebox
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
        ('mid', { 'title': 'Member-ID' }),
        ('val', { 'title': 'Selection', 'editable': True, 'dtype': int } )
    ],
    'visibility_button': None,
    'visibility': True
}

def init_tab(notebook):
    tab = create_tab(notebook, 'Selection', on_tab_selected)
    
    page_model['treeview'], _ = create_treeview(
        master = tab,
        column_info = page_model['column_info'],
        dbl_click_callback = on_treeview_dbl_clicked
    )
    page_model['visibility_button'] = create_control_panel(
        master = tab,
        button_info = {
            'Edit Line': { 'click': on_edit_line_clicked },
            'Load selection\nfrom CSV': { 'click': on_import_csv_clicked },
            'Visibility': { 'click': on_visibility_clicked },
            'Save Database': { 'click': on_save_db_clicked }
        }
    )['Visibility']
    
    page_model['visibility_button']['text'] = 'Show only\nselected lines'
    page_model['visibility'] = True
    
    on_tab_selected()

def on_tab_selected():
    person_df = load_table('tbl_person', 'display')
    person_match_df = load_table('tbl_person_selection')
    
    records = []
    
    for _, person in person_df.iterrows():
        mid = person['mid']
        r = [person['surname'], person['forename'], mid]
        v = 0
        
        for _, pm in person_match_df.iterrows():
            if pm['mid'] == mid:
                v = null_or(pm['val'], 0)
                break
        
        if v != 0 or page_model['visibility']: records.append(tuple(r + [v]))
    
    df = pd.DataFrame(records, columns = ['surname', 'forename', 'mid', 'val'])
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

# Assumed that only selected members are listed in the CSV file
def on_import_csv_clicked():
    csv_path = filedialog.askopenfilename(title = 'Select an CSV file', filetypes = [('CSV Files', '*.csv')])
    if csv_path is None or not os.path.exists(csv_path): return
    
    try:
        df = pd.read_excel(csv_path)
        df = df.rename(columns = {'Member_ID': 'mid'})
    except Exception:
        messagebox.showerror('Error', 'Error loading CSV file.')
        return
    
    person_df = load_table('tbl_person', 'display')    
    records = []
    
    for _, person in person_df.iterrows():
        mid = person['mid']
        r = [person['surname'], person['forename'], mid]
        v = 0
        
        for _, pm in df.iterrows():
            if pm['mid'] == mid:
                v = 1
                break
        
        records.append(tuple(r + [v]))
    
    df = pd.DataFrame(records, columns = ['surname', 'forename', 'mid', 'val'])
    page_model['backbone'] = df
    
    update_treeview(lambda: messagebox.showinfo('Success', 'CSV file loaded successfully.'))

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
        records.append((row['mid'], get_int_nzoe(row['val'])))            
    
    person_match_df = pd.DataFrame(records, columns = ['mid', 'val'])
    
    if not save_table('tbl_person_selection', person_match_df):
        messagebox.showerror('Error', 'Failed to save tbl_person_selection.')
        return

    messagebox.showinfo('Success', 'Saved database successfully.')

def on_visibility_clicked():
    if page_model['visibility']:
        page_model['visibility_button']['text'] = 'Show all\nlines'
    else:
        page_model['visibility_button']['text'] = 'Show only\nselected lines'
    
    page_model['visibility'] = not page_model['visibility']
    on_tab_selected()

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
            '', 'end', values = (
                i + 1, row['surname'], row['forename'], row['mid'], int_nonzero_or_empty(row['val'])
            )
        )

    if callback: callback()