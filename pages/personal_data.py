
from tkinter import filedialog, messagebox
from model import *
from util import *
from ui import *
import pandas as pd
import copy

page_model = {
    'backbone': None,
    'is_excel': False,
    'treeview': None,
    'column_info': [
        ('line', { 'title': 'Line Nr.' }),
        ('surname', { 'title': 'Surname', 'editable': True }),
        ('forename', { 'title': 'Forename', 'editable': True }),
        ('mid', { 'title': 'Member-ID', 'editable': True, 'dtype': int }),
        ('branch', { 'title': 'Branches', 'editable': True, 'dtype': int })
    ],
    'history': [],
    'history_pos': 0,
    'buttons': []
}

def init_tab(notebook):
    tab = create_tab(notebook, 'Personal-Data', on_tab_selected)

    page_model['treeview'] = tv = create_treeview(
        master = tab,
        column_info = page_model['column_info'],
        dbl_click_callback = on_treeview_dbl_clicked
    )
    page_model['buttons'] = create_control_panel(
        master = tab,
        button_info = {
            'Load SQL\ndatabase': { 'click': on_load_database_clicked },
            'Load Excel\nDatabase': { 'click': on_load_excel_clicked },
            'Import CSV\nDatabase': { 'click': on_import_csv_clicked },
            'Save\nDatabase': { 'click': on_save_database },
            'Add new\nColumn': { 'click': None },
            'Add new Line': { 'click': on_add_line_clicked },
            'Edit Line': { 'click': on_edit_line_clicked },
            'Delete Line(s)': { 'click': on_delete_line_clicked },
            'Show next free\nMember-ID': { 'click': on_next_mid_clicked },
            'Undo': { 'click': on_undo_clicked },
            'Redo': { 'click': on_redo_clicked },
        }
    )
    tv.tag_configure('dup_full', background = 'orange')
    tv.tag_configure('dup_name', background = 'salmon')
    tv.tag_configure('dup_mid', background = 'light blue')
    
    on_tab_selected()

def on_tab_selected():
    on_load_database_clicked(True)

def on_treeview_dbl_clicked(tv, item):
    if not item:
        messagebox.showerror('Error', 'No row selected.')
        return

    values = tv.item(item, 'values')
    default_values = []
    
    for i, ci in enumerate(page_model['column_info']):
        key, info = ci        
        v = values[i] if key != 'branch' else values[i][6:]
        
        default_values.append(v)
    
    show_entry_dlg(False, default_values, page_model['column_info'], on_edit, tags = (item, ))

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
    
    add_history()
    update_treeview()

def on_add(dlg, entries, tags):
    column_info = page_model['column_info']
    df = page_model['backbone']
    
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
    
    rec_dict['display'] = max(list(df['display'])) + 1 if len(df) > 0 else 1
    page_model['backbone'] = pd.concat([df, pd.Series(rec_dict).to_frame().T], ignore_index = True)
    
    dlg.destroy()
    
    add_history()    
    update_treeview()

def on_load_excel_clicked():
    xls_path = filedialog.askopenfilename(title = 'Select an Excel file', filetypes = [('Excel Files', '*.xlsx')])
    if xls_path is None or not os.path.exists(xls_path): return
    
    try:
        df = pd.read_excel(xls_path)
        df = df.rename(columns = {'Forename': 'forename', 'Surname': 'surname', 'Member_ID': 'mid', 'Branch': 'branch'})        
        
        df['branch'] = df['branch'].apply(lambda x: int(x[6:]))
        df['display'] = range(1, len(df) + 1)
    except Exception:
        messagebox.showerror('Error', 'Error loading Excel file.')
        return
    
    page_model['backbone'] = df
    page_model['is_excel'] = True
    
    reset_history()
    update_treeview(lambda: messagebox.showinfo('Success', 'Excel file loaded successfully.'))

def on_load_database_clicked(is_init = False):
    page_model['backbone'] = load_table('tbl_person')
    page_model['is_excel'] = False
    
    reset_history()
    update_treeview(None if is_init else lambda: messagebox.showinfo('Success', 'SQL database loaded successfully.'))

def on_import_csv_clicked():
    csv_path = filedialog.askopenfilename(title = 'Select a CSV file', filetypes = [('CSV Files', '*.csv')])
    if csv_path is None or not os.path.exists(csv_path): return
    
    try:
        df = pd.read_csv(csv_path, usecols = ['Forename', 'Surname', 'Member_ID', 'Branch'])
        
        df = df.rename(columns = {'Forename': 'forename', 'Surname': 'surname', 'Member_ID': 'mid', 'Branch': 'branch'})
        df['display'] = range(1, len(df) + 1)

        if df['mid'].isnull().any():
            max_mid = df['mid'].max()
            mid = max_mid + 1 if pd.notna(max_mid) else 1
        
            messagebox.showerror(
                'Import Error',
                'There are entries without Member_ID in the CSV file. Please add a Member_ID in Editor X and export the CSV file again.\n'
                f'The next available Member_ID is: {mid}'
            )
            return

        try:
            df['mid'] = pd.to_numeric(df['mid'], errors = 'coerce').fillna(0).astype('int64')
        except pd.errors.IntCastingNaNError as e:
            messagebox.showerror('Import Error', 'Non-numeric values in the Member_ID column.')
            return
        
        try:
            df['branch'] = df['branch'].apply(lambda x: int(x[6:]))
        except Exception:
            messagebox.showerror('Import Error', 'Error in Branch column.')
            return
    except Exception:
        messagebox.showerror('Error', 'Error loading CSV file.')
        return

    page_model['backbone'] = df
    page_model['is_excel'] = False
    
    reset_history()
    update_treeview(lambda: messagebox.showinfo('Success', 'CSV loaded successfully.'))

def on_add_line_clicked():
    column_info = page_model['column_info']
    show_entry_dlg(True, ['' for _ in column_info], column_info, on_add)

def on_edit_line_clicked():
    tv = page_model['treeview']
    
    try:
        item = tv.selection()[0]
        on_treeview_dbl_clicked(tv, item)
    except Exception:
        messagebox.showerror('Error', 'Please select a row first.')

def on_delete_line_clicked():
    tv = page_model['treeview']
    df = page_model['backbone']
    
    items = tv.selection()
    
    if not items:
        messagebox.showerror('Error', 'Please select row(s) to delete.')
        return

    indices = [df.index[int(tv.item(it, 'values')[0]) - 1] for it in items]    
    page_model['backbone'] = df.drop(indices).reset_index(drop = True)

    add_history()
    update_treeview()

def on_next_mid_clicked():
    df = page_model['backbone']
    mid = max(list(df['mid'])) + 1 if len(df) > 0 else 1
    
    messagebox.showinfo('Info', f"The next free Member_ID is {mid}.")

def on_undo_clicked():
    backward_history()

def on_redo_clicked():
    forward_history()

def on_save_database():
    df = page_model['backbone']
    invalids = set(df['dup_full']) | set(df['dup_name']) | set(df['dup_mid'])
    
    if True in invalids:
        messagebox.showerror('Error', 'There exist(s) invalid record(s).\nPlease fix and retry.')
        return

    records = []
    
    for _, row in df.iterrows():
        records.append((
            row['mid'], row['surname'], row['forename'], row['branch'], row['display']
        ))

    out_df = pd.DataFrame(records, columns = ['mid', 'surname', 'forename', 'branch', 'display'])
    ok = save_table('tbl_person', out_df)
    
    if ok:
        messagebox.showinfo('Success', 'Saved database successfully.')
    else:
        messagebox.showerror('Error', 'Failed to save database.')

def update_treeview(callback = None):
    tv = page_model['treeview']
    tv.delete(*tv.get_children())

    df = page_model['backbone']
    
    df['dup_full'] = df.duplicated(subset = ['forename', 'surname', 'mid'], keep = False)
    df['dup_name'] = df.duplicated(subset = ['forename', 'surname'], keep = False)
    df['dup_mid'] = df.duplicated(subset = ['mid'], keep = False)
        
    for i, row in df.iterrows():
        if row['dup_full']:
            tags = ('dup_full',)
        elif row['dup_name']:
            tags = ('dup_name',)
        elif row['dup_mid']:
            tags = ('dup_mid',)
        else:
            tags = ()

        tv.insert(
            '', 'end', values = (
                i + 1, row['surname'], row['forename'], row['mid'], f"Branch{row['branch']}"
            ),
            tags = tags
        )

    if callback: callback()

def reset_history():
    page_model['history'].clear()
    page_model['history_pos'] = -1
    
    add_history()
    
    page_model['buttons']['Undo']['state'] = 'disabled'
    page_model['buttons']['Redo']['state'] = 'disabled'

def add_history():
    df = copy.deepcopy(page_model['backbone'])
    history = page_model['history']
    
    history = history[:page_model['history_pos'] + 1]
    history.append((df, page_model['is_excel']))
    
    page_model['history'] = history
    page_model['history_pos'] = len(history) - 1
    
    page_model['buttons']['Undo']['state'] = 'normal'
    page_model['buttons']['Redo']['state'] = 'disabled'

def backward_history():
    history_pos = page_model['history_pos']
    if history_pos <= 0: return False
    
    history_pos -= 1
    page_model['backbone'], page_model['is_excel'] = page_model['history'][history_pos]
    page_model['history_pos'] = history_pos
    
    update_treeview()
    
    page_model['buttons']['Undo']['state'] = 'normal' if history_pos > 0 else 'disabled'
    page_model['buttons']['Redo']['state'] = 'normal'
    
    return True

def forward_history():
    history_pos = page_model['history_pos']
    if history_pos >= len(page_model['history']) - 1: return False
    
    history_pos += 1
    page_model['backbone'], page_model['is_excel'] = page_model['history'][history_pos]
    page_model['history_pos'] = history_pos
    
    update_treeview()
    
    page_model['buttons']['Undo']['state'] = 'normal'
    page_model['buttons']['Redo']['state'] = 'normal' if history_pos < len(page_model['history']) - 1 else 'disabled'
    
    return True