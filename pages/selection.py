
""" Selection Tab Page
"""

from tkinter import filedialog, messagebox, Frame
from constant import *
from model import *
from util import *
from ui import *
import pandas as pd
import copy

page_model = {
    'backbone': None,
    'treeview': None,
    'column_info': [
        ('line', { 'title': 'No', 'width': 40 }),
        ('surname', { 'title': 'Surname' }),
        ('forename', { 'title': 'Forename' }),
        ('mid', { 'title': 'Member-ID' }),
        #('val', { 'title': 'Selection', 'editable': True, 'dtype': int } )
    ],
    'visibility': True,
    'buttons': None,
    'history': [],
    'history_pos': 0
}

def init_tab(notebook):
    tab = create_tab(notebook, 'Selection', on_tab_selected, on_save_db_clicked)
    
    top_frame = Frame(tab, height = 700)
    top_frame.pack_propagate(False)
    top_frame.pack(fill = 'x', expand = False)
    
    page_model['treeview'], _ = create_treeview(
        master = top_frame,
        column_info = page_model['column_info'],
        dbl_click_callback = on_treeview_dbl_clicked,
        disable_hscroll = True
    )
    # page_model['treeview'], _ = create_checkbox_treeview(
    #     master = tab,
    #     column_info = page_model['column_info'],
    #     dbl_click_callback = on_treeview_dbl_clicked
    # )
    page_model['buttons'] = create_control_panel(
        master = tab,
        button_info = {
            'Toggle selection': { 'click': on_edit_line_clicked },
            'Load selection\nfrom CSV': { 'click': on_import_csv_clicked },
            'Visibility': { 'click': on_visibility_clicked },
            'Save Database': { 'click': on_save_db_clicked },
            'Undo': { 'click': on_undo_clicked },
            'Redo': { 'click': on_redo_clicked }
        }
    )
    
    page_model['buttons']['Visibility']['text'] = 'Show only\nselected lines'
    page_model['visibility'] = True
    
    page_model['treeview'].tag_configure('checked', background = 'lightgreen')
    on_tab_selected()

def on_undo_clicked():
    backward_history()

def on_redo_clicked():
    forward_history()
    
def on_tab_selected():
    person_df = load_table('tbl_person', 'surname, forename, mid')
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
    
    reset_history()
    update_treeview()

def on_treeview_dbl_clicked(tv, item, col_id):
    if not item:
        messagebox.showerror('Fehler', 'Keine Zeile ausgewählt.')
        return

    values = tv.item(item, 'values')
    df = page_model['backbone']
    idx = int(values[0]) - 1
    
    ov = int_nonzero_or_empty(df.iloc[idx]['val'])
    nv = 1 if ov == '' else 0
    
    df.at[idx, 'val'] = nv
    
    add_history()
    update_pending(True)
    update_treeview()

# Assumed that only selected members are listed in the CSV file
def on_import_csv_clicked():
    csv_path = filedialog.askopenfilename(title = 'Select an CSV file', filetypes = [('CSV Files', '*.csv')])
    if csv_path is None or not os.path.exists(csv_path): return
    
    try:
        df = pd.read_csv(csv_path)
        df = df.rename(columns = {'Mitgliedernummer': 'mid', 'Vorname': 'forename', 'Nachname': 'surname'})
        df['mid'] = pd.to_numeric(df['mid'], errors = 'coerce').fillna(0).astype('int64')
    except Exception:
        messagebox.showerror('Fehler', 'Error loading CSV file.')
        return
    
    person_df = load_table('tbl_person', 'surname, forename, mid')
    errors, records = [], []
    
    for _, r in df.iterrows():
        found = False
        
        for _, p in person_df.iterrows():
            if int(p['mid']) == int(r['mid']) and p['forename'] == r['forename'] and p['surname'] == r['surname']:
                found = True
                break
        
        if not found: errors.append(f"{r['mid']}: {r['forename']} {r['surname']}")
    
    if len(errors) > 0:
        messagebox.showwarning('Invalid Members', 'The following {} entries from CSV are inconsistent with the database.\nPlease check first name, last name and member ID, and correct them if necessary.\n\n{}'.
            format(len(errors), '\n'.join(errors)))
        return
    
    for _, person in person_df.iterrows():
        mid = person['mid']
        r = [person['surname'], person['forename'], mid]
        v = 0
        
        for _, pm in df.iterrows():
            if int(pm['mid']) == int(mid):
                v = 1
                break
        
        records.append(tuple(r + [v]))
    
    df = pd.DataFrame(records, columns = ['surname', 'forename', 'mid', 'val'])
    page_model['backbone'] = df
    
    reset_history()
    update_pending(True)
    update_treeview(lambda: messagebox.showinfo('Erfolg', 'CSV file loaded successfully.'))

def on_edit_line_clicked():
    tv = page_model['treeview']
    
    try:
        item = tv.selection()[0]
        on_treeview_dbl_clicked(tv, item, 0)
    except Exception:
        messagebox.showerror('Fehler', 'Bitte wählen Sie zunächst eine Zeile aus.')

def on_save_db_clicked():
    df = page_model['backbone']
    records = []
    
    for _, row in df.iterrows():
        records.append((row['mid'], get_int_nzoe(row['val'])))            
    
    person_match_df = pd.DataFrame(records, columns = ['mid', 'val'])
    
    if not save_table('tbl_person_selection', person_match_df):
        messagebox.showerror('Fehler', 'Failed to save tbl_person_selection.')
        return

    bkup_db()
    update_pending(False)
    
    messagebox.showinfo('Erfolg', 'Datenbank erfolgreich gespeichert.')

def on_visibility_clicked():
    if page_model['visibility']:
        page_model['buttons']['Visibility']['text'] = 'Show all\nlines'
    else:
        page_model['buttons']['Visibility']['text'] = 'Show only\nselected lines'
    
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
            messagebox.showerror('Eingabefehler', err)
            dlg.destroy()
            return
        else:
            rec_dict[key] = rv
    
    for key, rv in rec_dict.items():
        df.at[idx, key] = rv

    dlg.destroy()
    
    add_history()
    update_pending(True)
    update_treeview()

def update_treeview(callback = None):
    tv = page_model['treeview']
    tv.delete(*tv.get_children())

    df = page_model['backbone']
        
    for i, row in df.iterrows():
        cv = int_nonzero_or_empty(row['val'])
        tags = () if cv == '' else ('checked',)
        
        tv.insert(
            '', 'end', values = (
                i + 1, row['surname'], row['forename'], row['mid']#, int_nonzero_or_empty(row['val'])
            )
            , tags = tags
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