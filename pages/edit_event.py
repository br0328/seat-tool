
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
import copy

page_model = {
    'tab': None,
    'backbone': None,
    'treeview': None,
    'topframe': None,
    'dropdown': None,
    'column_info': [
        ('line', { 'title': 'No', 'width': 40 })
    ] + [
        (f"val{i}", { 'title': f"Table {i}", 'editable': True, 'dtype': str })
        for i in range(1, desk_count + 1)
    ],
    'person': None,
    'event': None,
    'person_event': None,
    'history': [],
    'history_pos': 0,
    'from_info': (None, None),
    'buttons': None
}

def init_tab(notebook):
    page_model['tab'] = tab = create_tab(notebook, 'Edit-Event', on_tab_selected, on_save_event_clicked)
    
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
        style = 'ne.Treeview'
    )
    bottom_frame = Frame(tab)
    bottom_frame.pack(fill = 'both', expand = True)
    
    page_model['buttons'] = create_control_panel(
        master = bottom_frame,
        button_info = {
            'Save event': { 'click': on_save_event_clicked },
            'Export event\nto XLS': { 'click': on_export_clicked },
            'Undo': { 'click': on_undo_clicked },
            'Redo': { 'click': on_redo_clicked }
        }
    )
    tv = page_model['treeview']
    
    tv.bind("<ButtonPress-1>", on_move_down)
    tv.bind("<ButtonRelease-1>", on_move_up, add='+')
    tv.bind("<B1-Motion>", on_moving, add='+')
    tv.bind(get_shortcut_button(), on_shortcut_clicked)
    
    on_tab_selected()

def on_tab_selected():
    page_model['backbone'] = None
    page_model['person'] = load_table('tbl_person', 'surname, forename, mid')
    page_model['event'] = load_table('tbl_event', 'title')
    page_model['person_event'] = load_table('tbl_person_event')
    
    if page_model['dropdown'] is not None:
        page_model['dropdown'].destroy()

    page_model['evvar'] = tk.StringVar(page_model['topframe'])
    choices = []

    for _, r in page_model['event'].iterrows():
        choices.append(r['title'])

    page_model['dropdown'] = dropdown = tk.OptionMenu(page_model['topframe'], page_model['evvar'], *choices)
    dropdown.grid(row = 1, column = 1)

    page_model['buttons']['Undo']['state'] = 'disabled'
    page_model['buttons']['Redo']['state'] = 'disabled'
    
    update_treeview()

def on_save_event_clicked():
    eid = get_eid(page_model['event'], page_model['evvar'].get())
    df = page_model['backbone']
    
    if eid is None:
        messagebox.showerror('No Event', 'No event is loaded.')
        return
        
    if df is None:
        messagebox.showerror('No Event', 'No event is loaded.')
        return
    
    arr = []
    dcount = [0] * desk_count
    
    for _, r in df.iterrows():
        for cid in range(desk_count):
            mid = r[f"val{cid + 1}"]
            if mid == '': continue
            
            arr.append([int(mid), eid, cid + 1])
            dcount[cid] += 1
            
            if dcount[cid] >= desk_size + 1:
                messagebox.showerror('Desk Overflow', 'There is a desk exceeding limit size.')
                return
    
    df = page_model['person_event']
    df = df.drop(df[df['eid'] == eid].index)
    df = pd.concat([df, pd.DataFrame(arr, columns = ['mid', 'eid', 'val'])])
    
    if not save_table('tbl_person_event', df):
        messagebox.showerror('Error', 'Failed to save tbl_person_event.')
        return
    
    page_model['person_event'] = df
    on_check_clicked()

    bkup_db()
    update_pending(False)
    
    messagebox.showinfo('Success', 'Saved database successfully.')

def on_undo_clicked():
    backward_history()

def on_redo_clicked():
    forward_history()

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
    
    reset_history()
    update_columns()
    update_treeview()

def update_columns():
    df = page_model['backbone']
    show_colummns = set()
    
    for _, r in df.iterrows():
        for i in range(desk_count):
            v = null_or(r[f"val{i + 1}"], '')            
            
            if v != '' and int(v) != 0:
                for j in range(i + 1):
                    show_colummns.add(j + 1)
    
    show_colummns = [f"val{i}" for i in sorted(list(show_colummns))]
    page_model['treeview']['displaycolumns'] = ['line'] + show_colummns

def top_justfiy():
    df = page_model['backbone']
    arr = [['' for _ in range(desk_count)] for _ in range(desk_size + 1)]
    dcount = [0] * desk_count
    
    for _, r in df.iterrows():
        for i in range(desk_count):
            v = null_or(r[f"val{i + 1}"], '')
            
            if v != '' and int(v) != 0:
                arr[dcount[i]][i] = int(v)
                dcount[i] += 1
    
    page_model['backbone'] = pd.DataFrame(arr, columns = [f"val{i + 1}" for i in range(desk_count)])

def get_cell_text(mid, for_excel = False):
    if mid == '': return ''
    
    person = get_person(page_model['person'], mid)
    if person is None: return ''
    
    return person['surname'] + ' ' + person['forename'] + (' ' if for_excel else '\n') + str(mid)

def on_export_clicked():
    xls_path = filedialog.asksaveasfilename(title = 'Select an Excel file', defaultextension = '.xlsx')
    if xls_path is None or xls_path == '': return
    
    eid = get_eid(page_model['event'], page_model['evvar'].get())
    df = page_model['backbone']
    
    if eid is None:
        messagebox.showerror('No Event', 'No event is loaded.')
        return
        
    if df is None:
        messagebox.showerror('No Event', 'No event is loaded.')
        return
    
    arr = [([str(i + 1)] + ['' for _ in range(desk_count)]) for i in range(desk_size)]
    dcount = [0] * desk_count
    
    for _, r in df.iterrows():
        for cid in range(desk_count):
            mid = r[f"val{cid + 1}"]
            if mid == '': continue
            
            if dcount[cid] >= desk_size:
                messagebox.showerror('Desk Overflow', 'There is a desk exceeding limit size.')
                return
            
            arr[dcount[cid]][cid + 1] = get_cell_text(int(mid), for_excel = True)
            dcount[cid] += 1
    
    df = pd.DataFrame(arr, columns = ['Seat'] + [f"Table {i + 1}" for i in range(desk_count)])    
    df.to_excel(xls_path, index = False)
    
    messagebox.showinfo('Export', f"Successfully exported to {xls_path}")

def on_move_down(ev):
    page_model['from_info'] = (None, None)
    
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
            
            df = page_model['backbone']
            fri, fci = page_model['from_info']
            
            if fci != col_id:
                fmid = int(df.iloc[fri - 1][f"val{fci}"])
                found = False
                
                for i, r in df.iterrows():
                    if r[f"val{col_id}"] == '':
                        df.at[i, f"val{col_id}"] = str(fmid)
                        df.at[fri - 1, f"val{fci}"] = ''
                        found = True
                        break
                
                if found:
                    top_justfiy()
                    add_history()
                                        
                    update_pending(True)
                    update_treeview()
                else:
                    messagebox.showerror('Full Desk', 'Cannot find vacant seat in Table {}.'.format(col_id))            
        except Exception as exc:
            pass
        finally:
            page_model['from_info'] = (None, None)

def on_moving(ev):
    pass

def on_shortcut_clicked(ev):
    tv = page_model['treeview']
    popup_menu = None
    
    try:
        region = tv.identify('region', ev.x, ev.y)
        
        if region == 'cell':
            col_name = tv.column(tv.identify_column(ev.x), 'id')            
            
            if col_name.startswith('val'):
                col_id = int(col_name[3:])
                item = tv.item(tv.identify_row(ev.y), 'values')
                row_id = int(item[0])

                df = page_model['backbone']
                mid = df.iloc[row_id - 1][f"val{col_id}"]
                idx = None
                
                for i, r in df.iterrows():
                    if r[f"val{col_id}"] == '':
                        idx = i
                        break

                popup_menu = tk.Menu(page_model['tab'], tearoff = 0)                
                if idx is not None: popup_menu.add_command(label = f"Add Person", command = lambda: on_add_clicked(col_id, idx))
                if mid != '': popup_menu.add_command(label = f"Remove Person", command = lambda: on_remove_clicked(row_id, col_id))
                popup_menu.tk_popup(ev.x_root, ev.y_root)
    finally:
        if popup_menu is not None: popup_menu.grab_release()
        
def on_remove_clicked(row_id, col_id):
    df = page_model['backbone']
    df.at[row_id - 1, f"val{col_id}"] = ''
    
    top_justfiy()
    add_history()
    
    update_pending(True)
    update_treeview()

def on_add_clicked(col_id, idx):
    mid_list = page_model['backbone'].values.tolist()
    choices, seated = [], set()
    
    for ml in mid_list:
        for mid in ml:
            if mid != '': seated.add(str(mid))

    for _, r in page_model['person'].iterrows():
        if str(r['mid']) in seated: continue
        
        v = f"{r['mid']}: {r['surname']}, {r['forename']}"
        choices.append(v)

    if len(choices) == 0:
        messagebox.showerror('All Seated', 'All members are seated.')
        return

    dlg = tk.Toplevel()
    dlg.title('Add Person')

    tkvar = tk.StringVar(dlg)    
    dropdown = tk.OptionMenu(dlg, tkvar, *choices)
    
    tk.Label(dlg, text = 'Will be seated in Table ' + str(col_id)).grid(row = 0, column = 0)    
    tk.Label(dlg, text = "Choose a person").grid(row = 1, column = 0)
    dropdown.grid(row = 1, column = 1)

    entries = { 'person': tkvar }
    tk.Button(dlg, text = 'Save', command = lambda: on_add(dlg, entries, col_id, idx)).grid(row = 2, column = 1)

def on_add(dlg, entries, col_id, idx):    
    choice = null_or(entries['person'].get(), '')
    
    if choice != '':
        mid = choice.split(':')[0]
        
        df = page_model['backbone']
        df.at[idx, f"val{col_id}"] = mid

    dlg.destroy()
    
    add_history()
    update_pending(True)
    update_treeview()

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
    history.append(df)
    
    page_model['history'] = history
    page_model['history_pos'] = len(history) - 1
    
    page_model['buttons']['Undo']['state'] = 'normal'
    page_model['buttons']['Redo']['state'] = 'disabled'
    
def backward_history():
    history_pos = page_model['history_pos']
    if history_pos <= 0: return False
    
    history_pos -= 1
    page_model['backbone'] = copy.deepcopy(page_model['history'][history_pos])
    page_model['history_pos'] = history_pos
    
    update_pending(True)
    update_treeview()
    
    page_model['buttons']['Undo']['state'] = 'normal' if history_pos > 0 else 'disabled'
    page_model['buttons']['Redo']['state'] = 'normal'
    
    return True

def forward_history():
    history_pos = page_model['history_pos']
    if history_pos >= len(page_model['history']) - 1: return False
    
    history_pos += 1
    page_model['backbone'] = copy.deepcopy(page_model['history'][history_pos])
    page_model['history_pos'] = history_pos
    
    update_pending(True)
    update_treeview()
    
    page_model['buttons']['Undo']['state'] = 'normal'
    page_model['buttons']['Redo']['state'] = 'normal' if history_pos < len(page_model['history']) - 1 else 'disabled'
    
    return True