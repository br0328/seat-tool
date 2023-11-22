
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
        ('line', { 'title': 'Line Nr.' })
    ] + [
        (f"val{i}", { 'title': f"Table {i}", 'editable': True, 'dtype': str })
        for i in range(1, new_event_col_count + 1)
    ]
}

def init_tab(notebook):
    tab = create_tab(notebook, 'New-Event', on_tab_selected)
    
    page_model['treeview'], _ = create_treeview(
        master = tab,
        column_info = page_model['column_info'],
        dbl_click_callback = on_treeview_dbl_clicked
    )
    create_control_panel(
        master = tab,
        button_info = {
            'Generate\nnew event': { 'click': on_add_line_clicked },
            'Add to Hist-event and\nsave database': { 'click': on_save_db_clicked },
            'Export event\nto XLS': { 'click': on_export_clicked },
            'Import event\nfrom XLS': { 'click': on_import_clicked }
        }
    )
    on_tab_selected()

def on_tab_selected():
    page_model['backbone'] = load_table('tbl_new_event', 'display')
    update_treeview()

def on_treeview_dbl_clicked(tv, item):
    if not item:
        messagebox.showerror('Error', 'No row selected.')
        return

    values = tv.item(item, 'values')    
    show_entry_dlg(False, values, page_model['column_info'], on_edit, tags = (item, ))

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
    update_treeview()

def on_add_line_clicked():
    column_info = page_model['column_info']
    show_entry_dlg(True, ['' for _ in column_info], column_info, on_add)

def on_save_db_clicked():
    df = page_model['backbone']
    ev_df = load_table('tbl_event', 'display')
    
    eid = max(list(ev_df['eid'])) + 1 if len(ev_df) > 0 else 1
    display = max(list(ev_df['display'])) + 1 if len(ev_df) > 0 else 1
    
    for _, row in df.iterrows():
        rec = {
            'eid': eid,
            'title': row['val1'],
            'display': display
        }
        ev_df = pd.concat([ev_df, pd.Series(rec).to_frame().T], ignore_index = True)
        
        eid += 1
        display += 1
    
    if not save_table('tbl_event', ev_df):
        messagebox.showerror('Error', 'Failed to save tbl_event.')
        return
    
    if not save_table('tbl_new_event', df):
        messagebox.showerror('Error', 'Failed to save tbl_new_event.')
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
                [i + 1] +
                [null_or(row[f"val{k + 1}"], '') for k in range(new_event_col_count)]
            )
        )

    if callback: callback()

def on_export_clicked():
    page_model['backbone'].to_excel('./out/new_event.xlsx', index = False)
    messagebox.showinfo('Export', 'Successfully exported to ./out/new_event.xlsx!')

def on_import_clicked():
    xls_path = filedialog.askopenfilename(title = 'Select an Excel file', filetypes = [('Excel Files', '*.xlsx')])
    if xls_path is None or not os.path.exists(xls_path): return
    
    try:
        df = pd.read_excel(xls_path)
    except Exception:
        messagebox.showerror('Error', 'Error loading Excel file.')
        return
    
    page_model['backbone'] = df
    update_treeview(lambda: messagebox.showinfo('Success', 'Excel file loaded successfully.'))
