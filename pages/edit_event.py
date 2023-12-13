
""" Edit-Event Tab Page
"""

from tkinter import filedialog, messagebox, Frame, Label, Button
from constant import *
from engine import *
from model import *
from util import *
from ui import *
import pandas as pd
import numpy as np
import random

page_model = {
    'backbone': None,
    'treeview': None,
    'topframe': None,
    'dropdown': None,
    'column_info': [
        ('line', { 'title': 'Line Nr.' })
    ] + [
        (f"val{i}", { 'title': f"Table {i}", 'editable': True, 'dtype': str })
        for i in range(1, desk_count + 1)
    ],
    'person': None,
    'event': None,
    'person_event': None,
    'from_info': (None, None)
}

def init_tab(notebook):
    tab = create_tab(notebook, 'Edit-Event', on_tab_selected)
    
    st = ttk.Style()
    st.configure('ne.Treeview', rowheight = 40)
    
    page_model['topframe'] = top_frame = Frame(tab, height = 100)
    top_frame.pack_propagate(False)
    top_frame.pack(fill = 'x', expand = False)
    
    Frame(top_frame, height = 15).grid(row = 0, column = 0)
    Label(top_frame, text = 'Select Event: ').grid(row = 1, column = 0)
    Button(top_frame, text = 'Load', command = on_check_clicked).grid(row = 1, column = 2)
    
    mid_frame = Frame(tab, height = 650)
    mid_frame.pack_propagate(False)
    mid_frame.pack(fill = 'x', expand = False)

    page_model['treeview'], _ = create_treeview(
        master = mid_frame,
        column_info = page_model['column_info'],
        dbl_click_callback = None,
        style = 'ne.Treeview',
        disable_hscroll = True
    )
    bottom_frame = Frame(tab)
    bottom_frame.pack(fill = 'both', expand = True)
    
    create_control_panel(
        master = bottom_frame,
        button_info = {
            'Save event': { 'click': on_save_event_clicked },
            'Export event\nto XLS': { 'click': on_export_clicked }
        }
    )
    tv = page_model['treeview']
    
    tv.bind("<ButtonPress-1>", on_move_down)
    tv.bind("<ButtonRelease-1>", on_move_up, add='+')
    tv.bind("<B1-Motion>", on_moving, add='+')

    on_tab_selected()

def on_tab_selected():
    page_model['backbone'] = None
    page_model['person'] = load_table('tbl_person')
    page_model['event'] = load_table('tbl_event')
    page_model['person_event'] = load_table('tbl_person_event')
    
    if page_model['dropdown'] is not None:
        page_model['dropdown'].destroy()

    page_model['evvar'] = tk.StringVar(page_model['topframe'])
    choices = set()

    for _, r in page_model['event'].iterrows():
        choices.add(r['title'])

    page_model['dropdown'] = dropdown = tk.OptionMenu(page_model['topframe'], page_model['evvar'], *choices)
    dropdown.grid(row = 1, column = 1)

    update_treeview()

def on_save_event_clicked():
    pass

def on_check_clicked():
    eid = get_eid(page_model['event'], page_model['evvar'].get())
    if eid is None: return
    
    df = page_model['person_event']
    
    df = df[df['eid'] == eid]
    arr = [['' for _ in range(desk_count)] for _ in range(desk_size + 1)]
    dcount = [0] * desk_count
    
    for _, r in df.iterrows():
        v = int(r['val']) - 1
        if v < 0 or v >= desk_count: continue
        
        arr[dcount[v]][v] = int(r['mid'])
        dcount[v] += 1
    
    page_model['backbone'] = pd.DataFrame(arr, columns = [f"val{i + 1}" for i in range(desk_count)])
    update_treeview()

def get_cell_text(mid, for_excel = False):
    if mid == '': return ''
    
    person = get_person(page_model['person'], mid)
    if person is None: return ''
    
    return person['surname'] + ' ' + person['forename'] + (' ' if for_excel else '\n') + str(mid)

def on_export_clicked():
    xls_path = filedialog.asksaveasfilename(title = 'Select an Excel file', defaultextension = '.xlsx')
    if xls_path is None or xls_path == '': return
    
    df = page_model['backbone']
    df = df.drop(['display'], axis = 1)
    
    rename_dict = { 'neid': 'Seat'}
    
    for i in range(1, desk_count + 1):
        rename_dict[f"val{i}"] = f"Table {i}"
        df[f"val{i}"] = df[f"val{i}"].astype(str)
        
    df = df.rename(columns = rename_dict)
    
    for i, r in df.iterrows():
        for j in range(1, desk_count + 1):
            col = f"Table {j}"
            df.at[i, col] = get_cell_text(int(r[col]) if r[col] is not None else '', for_excel = True)
    
    df.to_excel(xls_path, index = False)
    messagebox.showinfo('Export', f"Successfully exported to {xls_path}")

def on_move_down(ev):
    try:
        tv = page_model['treeview']    
        col = tv.identify_column(ev.x)
        
        if col is None: return
        col_id = tv.column(col, "id")
        
        if not col_id.startswith('val'): return
        
        col_id = int(col_id[3:])
        item = tv.identify_row(ev.y)
        if item is None: return

        row_id = int(tv.item(item, 'values')[0])        
        page_model['from_info'] = (row_id, col_id)
    except Exception:
        return
    
def on_move_up(ev):
    if page_model['from_info'][0] is not None:
        try:
            tv = page_model['treeview']
            col_id = tv.column(tv.identify_column(ev.x), "id")        
            if not col_id.startswith('val'): return
            
            col_id = int(col_id[3:])
            row_id = int(tv.item(tv.identify_row(ev.y), 'values')[0])
            
            df = page_model['backbone']
            fri, fci = page_model['from_info']
            
            tmp = df.iloc[row_id - 1][f"val{col_id}"]
            
            df.at[row_id - 1, f"val{col_id}"] = df.iloc[fri - 1][f"val{fci}"]
            df.at[fri - 1, f"val{fci}"] = tmp
            
            update_treeview()
        except Exception as exc:
            print(exc)
        finally:
            page_model['from_info'] = (None, None)

def on_moving(ev):
    pass
 
def update_treeview(callback = None):
    tv = page_model['treeview']
    tv.delete(*tv.get_children())

    df = page_model['backbone']
    
    if df is not None:        
        for i, row in df.iterrows():
            tv.insert(
                '', 'end', values = tuple(
                    [i + 1] +
                    [get_cell_text(null_or(row[f"val{k + 1}"], '')) for k in range(desk_count)]
                )
            )
    
    if callback: callback()