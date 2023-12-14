
""" New-Event Tab Page
"""

from tkinter import filedialog, messagebox, Frame, Label
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
    'conflict': None,
    'treeview': None,
    'confview': None,
    'label': None,
    'score': 0,
    'column_info': [
        ('line', { 'title': 'No', 'width': 40 })
    ] + [
        (f"val{i}", { 'title': f"Table {i}", 'editable': True, 'dtype': str })
        for i in range(1, desk_count + 1)
    ],
    'person': None,
    'selection': None,
    'match': None,
    'no-match': None,
    'never-match': None,
    'event': None
}

def init_tab(notebook):
    tab = create_tab(notebook, 'New-Event', on_tab_selected)
    
    st = ttk.Style()
    st.configure('ne.Treeview', rowheight = 40)
    
    top_frame = Frame(tab, height = 370)
    top_frame.pack_propagate(False)
    top_frame.pack(fill = 'x', expand = False)

    page_model['treeview'], _ = create_treeview(
        master = top_frame,
        column_info = page_model['column_info'],
        dbl_click_callback = None,#on_treeview_dbl_clicked,
        style = 'ne.Treeview',
        disable_hscroll = True
    )
    brk_frame = Frame(tab, height = 50)
    brk_frame.pack_propagate(False)
    brk_frame.pack(fill = 'x', expand = False)
    
    page_model['label'] = Label(brk_frame, text = 'Click "Generate new event" button.')
    page_model['label'].grid(row = 0, column = 0)
    
    mid_frame = Frame(tab, height = 300)
    mid_frame.pack_propagate(False)
    mid_frame.pack(fill = 'x', expand = False)
    
    page_model['confview'], _ = create_treeview(
        master = mid_frame,
        column_info = [
            ('line', { 'title': 'No' }),
            ('person1', { 'title': 'Person1' }),
            ('person2', { 'title': 'Person2' }),
            ('val', { 'title': 'Value' }),
            ('conflict', { 'title': 'Conflict' })
        ],
        style = 'ne.Treeview',
        dbl_click_callback = None,
        disable_hscroll = True
    )    
    bottom_frame = Frame(tab)
    bottom_frame.pack(fill = 'both', expand = True)
    
    # top_frame.config(height = int(tab.winfo_reqheight() * 0.8))
    # bottom_frame.config(height = int(tab.winfo_reqheight() * 0.1))
    
    create_control_panel(
        master = bottom_frame,
        button_info = {
            'Generate\nnew event': { 'click': on_add_line_clicked },
            'Add to Hist-event and\nsave database': { 'click': on_save_db_clicked },
            'Export event\nto XLS': { 'click': on_export_clicked },
            #'Import event\nfrom XLS': { 'click': on_import_clicked }
        }
    )
    on_tab_selected()

def on_tab_selected():
    page_model['backbone'] = load_table('tbl_new_event', 'display')
    page_model['conflict'] = None
    page_model['person'] = load_table('tbl_person')
    page_model['selection'] = load_table('tbl_person_selection')
    page_model['match'] = load_table('tbl_person_match')
    page_model['no-match'] = load_table('tbl_person_no_match')
    page_model['never-match'] = load_table('tbl_person_never_match')
    page_model['event'] = load_table('tbl_person_event')
    
    update_treeview()

def on_treeview_dbl_clicked(tv, item, col_id):
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
    engine = Engine(page_model['person'], page_model['selection'], page_model['event'], page_model['match'], page_model['no-match'], page_model['never-match'])
    res_df, conf_df, score = engine.calculate()
    
    plan = np.zeros((desk_count, desk_size), dtype = np.int64)
    dcount = np.zeros(desk_count, dtype = np.int64)
    
    for _, r in res_df.iterrows():
        d = r['val'] - 1
        plan[d, dcount[d]] = r['mid']
        dcount[d] += 1
    
    records = []
    
    for i in range(desk_size):
        r = {}
        r['neid'] = r['display'] = i + 1
        
        for j in range(desk_count):
            r[f"val{j + 1}"] = plan[j, i]
        
        records.append(r)
    
    page_model['backbone'] = pd.DataFrame(records, columns = ['neid', 'display'] + [f"val{i + 1}" for i in range(desk_count)])
    page_model['conflict'] = conf_df
    page_model['score'] = score
    
    update_treeview()

def on_save_db_clicked():
    dlg = tk.Toplevel()
    dlg.title('Add Event')

    evar = tk.StringVar(dlg, value = '')
    ent = tk.Entry(dlg, textvariable = evar)
    
    tk.Label(dlg, text = 'Event Name: ').grid(row = 0, column = 0)
    ent.grid(row = 0, column = 1)
    
    entries = { 'title': evar }
    tk.Button(dlg, text = 'Add', command = lambda: on_add_event(dlg, entries)).grid(row = 1, column = 1)

def on_add_event(dlg, entries):
    title = entries['title'].get()
    
    if title == '':
        messagebox.showerror('Error', 'Event name should not be empty string.')
        dlg.destroy()
        return
    
    dlg.destroy()
    
    df = page_model['backbone']
    ev_df = load_table('tbl_event', 'display')
    person_ev_df = load_table('tbl_person_event')
    
    eid = max(list(ev_df['eid'])) + 1 if len(ev_df) > 0 else 1
    display = max(list(ev_df['display'])) + 1 if len(ev_df) > 0 else 1
    
    rec = {
        'eid': eid,
        'title': title,
        'display': display
    }
    ev_df = pd.concat([ev_df, pd.Series(rec).to_frame().T], ignore_index = True)
    
    for _, r in df.iterrows():
        for i in range(desk_count):
            mid = int(null_or(r[f"val{i + 1}"], 0))
            if mid <= 0: continue
            
            rec = {
                'eid': eid,
                'mid': mid,
                'val': i + 1
            }
            person_ev_df = pd.concat([person_ev_df, pd.Series(rec).to_frame().T], ignore_index = True)            
    
    if not save_table('tbl_event', ev_df):
        messagebox.showerror('Error', 'Failed to save tbl_event.')
        return
    
    if not save_table('tbl_person_event', person_ev_df):
        messagebox.showerror('Error', 'Failed to save tbl_person_event.')
        return
    
    page_model['event'] = person_ev_df
    page_model['backbone'] = df = df.drop(df.index)
    page_model['conflict'] = None
    
    if not save_table('tbl_new_event', df):
        messagebox.showerror('Error', 'Failed to save tbl_new_event.')
        return

    messagebox.showinfo('Success', 'Saved database successfully.')
    update_treeview()

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
                [get_cell_text(null_or(row[f"val{k + 1}"], '')) for k in range(desk_count)]
            )
        )

    cv = page_model['confview']
    cv.delete(*cv.get_children())
    
    df = page_model['conflict']

    if df is not None:
        i = 0
        
        for _, row in df.iterrows():
            cv.insert(
                '', 'end', values = tuple(
                    [
                        i + 1,
                        get_cell_text(null_or(row['id1'], '')),
                        get_cell_text(null_or(row['id2'], '')),
                        '{:.1f}'.format(row['val']),
                        row['conflict']
                    ]
                )
            )
            i += 1
        
        page_model['label'].config(text = 'Goodness = {:.1f},  Conflicts = {}'.format(page_model['score'], i))
    else:
        page_model['label'].config(text = 'Click "Generate new event" button.')
            
    if callback: callback()

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
