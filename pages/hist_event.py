
from tkinter import filedialog, messagebox
from constant import *
from model import *
from util import *
from ui import *
import pandas as pd

page_model = {
    'backbone': None,
    'evdf': None,
    'treeview': None,
    'vscroll': None,
    'column_info': None,
    'buttons': None,
    'evcount': None,
    'tab': None
}

def init_tab(notebook):
    page_model['tab'] = create_tab(notebook, 'Hist-Events', on_tab_selected)
    on_tab_selected()

def on_tab_selected():
    page_model['evdf'] = load_table('tbl_event', 'display')
    heavy_refresh()

def heavy_refresh():
    if page_model['treeview']:
        page_model['treeview'].destroy()
        page_model['vscroll'].destroy()
        
        for _, but in page_model['buttons'].items():
            but.destroy()
    
    ev_df = page_model['evdf']
    person_df = load_table('tbl_person', 'display')
    person_ev_df = load_table('tbl_person_event')
    
    page_model['column_info'] = [
        ('line', { 'title': 'Line Nr.' }),
        ('surname', { 'title': 'Surname' }),
        ('forename', { 'title': 'Forename' }),
        ('mid', { 'title': 'Member-ID' })
    ] + [
        (f"ev{i}", { 'title': row['title'], 'editable': True, 'dtype': int })
        for i, row in ev_df.iterrows()
    ]
    page_model['treeview'], page_model['vscroll'] = create_treeview(
        master = page_model['tab'],
        column_info = page_model['column_info'],
        dbl_click_callback = on_treeview_dbl_clicked
    )
    page_model['buttons'] = create_control_panel(
        master = page_model['tab'],
        button_info = {
            'Edit line': { 'click': on_edit_line_clicked },
            'Add new column': { 'click': on_add_column_clicked },
            'Save database': { 'click': on_save_db_clicked },
        }
    )    
    page_model['evcount'] = len(ev_df)
    records = []
    
    for _, person in person_df.iterrows():
        mid = person['mid']
        r = [person['surname'], person['forename'], mid]
                
        for _, ev in ev_df.iterrows():
            eid = ev['eid']
            val = 0
            
            for _, pe in person_ev_df.iterrows():
                if pe['mid'] == mid and pe['eid'] == eid:
                    val = pe['val']
                    break
            
            r.append(val)
        
        records.append(tuple(r))
    
    df = pd.DataFrame(records, columns = ['surname', 'forename', 'mid'] + [f"ev{i}" for i in range(page_model['evcount'])])
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
        
        if key.startswith('ev'):
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

def on_add_column_clicked():
    dlg = tk.Toplevel()
    dlg.title('Add Event')

    evar = tk.StringVar(dlg, value = '')
    ent = tk.Entry(dlg, textvariable = evar)
    
    tk.Label(dlg, text = 'Event Name: ').grid(row = 0, column = 0)
    ent.grid(row = 0, column = 1)
    
    entries = { 'title': evar }
    tk.Button(dlg, text = 'Add', command = lambda: on_add(dlg, entries)).grid(row = 1, column = 1)

def on_add(dlg, entries):
    title = entries['title'].get()
    ev_df = page_model['evdf']
    
    if title == '':
        messagebox.showerror('Error', 'Event name should not be empty string.')
        dlg.destroy()
        return
    
    rec_dict = {
        'eid': max(list(ev_df['eid'])) + 1 if len(ev_df) > 0 else 1,
        'title': title,
        'display': max(list(ev_df['display'])) + 1 if len(ev_df) > 0 else 1
    }
    page_model['evdf'] = pd.concat([ev_df, pd.Series(rec_dict).to_frame().T], ignore_index = True)
    
    dlg.destroy()    
    heavy_refresh()

def on_save_db_clicked():
    df = page_model['backbone']
    ev_df = page_model['evdf']
    
    records = []
    
    for _, row in df.iterrows():
        mid = row['mid']
        
        for i, ev in ev_df.iterrows():
            records.append((
                mid, ev['eid'], get_int_nzoe(row[f"ev{i}"])
            ))
    
    person_ev_df = pd.DataFrame(records, columns = ['mid', 'eid', 'val'])
    
    if not save_table('tbl_event', ev_df):
        messagebox.showerror('Error', 'Failed to save tbl_event.')
        return
    
    if not save_table('tbl_person_event', person_ev_df):
        messagebox.showerror('Error', 'Failed to save tbl_person_event.')
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
                [int_nonzero_or_empty(row[f"ev{k}"]) for k in range(page_model['evcount'])]
            )
        )

    if callback: callback()