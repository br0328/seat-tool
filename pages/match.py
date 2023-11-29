
""" Match Tab Page
"""

from tkinter import messagebox
from constant import *
from model import *
from util import *
from ui import *
import pandas as pd

page_tid = 0
page_title = 'Match'
page_col = 'Match'
page_tbl = 'tbl_person_match'
page_col_count = match_col_count

page_model = {    
    'backbone': None,
    'treeview': None,
    'column_info': [
        ('line', { 'title': 'Line Nr.' }),
        ('surname', { 'title': 'Surname' }),
        ('forename', { 'title': 'Forename' }),
        ('mid', { 'title': 'Member-ID' })
    ] + [
        (f"val{i}", { 'title': f"{page_col}-{i + 1}", 'editable': True, 'dtype': int })
        for i in range(page_col_count)
    ],
    'comment': None,
    'person': None,
    'tab': None,
    'hovertext': None,
    'hoverdlg': None
}

def init_tab(notebook):
    page_model['tab'] = tab = create_tab(notebook, page_title, on_tab_selected)
    
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
    page_model['treeview'].bind(get_shortcut_button(), on_shortcut_clicked)
    page_model['treeview'].bind("<Enter>", on_enter)
    page_model['treeview'].bind("<Leave>", on_leave)

    page_model['hoverdlg'] = HoverInfo(tab)
    page_model['treeview'].bind("<Motion>", on_enter)
    
    on_tab_selected()

def on_tab_selected():
    page_model['person'] = person_df = load_table('tbl_person', 'surname, forename, mid')
    person_match_df = load_table(page_tbl)
    records = []
    
    for _, person in person_df.iterrows():
        mid = person['mid']
        r = [person['surname'], person['forename'], mid]
        v = [0] * page_col_count
        
        for _, pm in person_match_df.iterrows():
            if pm['mid'] == mid:
                v = [pm[f"val{i + 1}"] for i in range(page_col_count)]
                break
        
        records.append(tuple(r + v))
    
    df = pd.DataFrame(records, columns = ['surname', 'forename', 'mid'] + [f"val{i}" for i in range(page_col_count)])
    
    page_model['backbone'] = df    
    page_model['comment'] = load_table('tbl_comment')
    
    update_treeview()

def on_shortcut_clicked(ev):
    tv = page_model['treeview']
    popup_menu = None
    
    try:
        region = tv.identify('region', ev.x, ev.y)
        
        if region == 'cell':
            col_name = tv.column(tv.identify_column(ev.x), 'id')            
            
            if col_name.startswith('val'):
                col_id = int(col_name[3:])
                row_id = tv.item(tv.identify_row(ev.y), 'values')[3]
                
                comm = get_comment(page_model['comment'], page_tid, row_id, col_id)                
                popup_menu = tk.Menu(page_model['tab'], tearoff = 0)
                
                if comm is None:
                    popup_menu.add_command(label = f"Add Comment", command = lambda: on_comment_clicked(True, row_id, col_id, comm))
                else:
                    popup_menu.add_command(label = f"Edit Comment", command = lambda: on_comment_clicked(False, row_id, col_id, comm))
                    
                popup_menu.tk_popup(ev.x_root, ev.y_root)
    finally:
        if popup_menu is not None: popup_menu.grab_release()

def on_comment_clicked(is_add, mid, cid, comm):
    dlg = tk.Toplevel()
    dlg.title('Add Comment' if is_add else 'Edit Comment')

    evar = tk.StringVar(dlg, value = '' if is_add else comm)
    ent = tk.Entry(dlg, textvariable = evar)
    
    tk.Label(dlg, text = 'Comment: ').grid(row = 0, column = 0)
    ent.grid(row = 0, column = 1)
    
    entries = { 'val': evar }
    tk.Button(dlg, text = 'Add' if is_add else 'Save', command = lambda: on_comment(dlg, entries, is_add, mid, cid)).grid(row = 1, column = 1)

def on_comment(dlg, entries, is_add, mid, cid):
    comm = entries['val'].get()    
    comm_df = page_model['comment']
    
    if is_add:
        rec_dict = {
            'tid': page_tid,
            'mid': mid,
            'cid': cid,
            'val': comm
        }
        page_model['comment'] = pd.concat([comm_df, pd.Series(rec_dict).to_frame().T], ignore_index = True)
    else:
        idx = comm_df[(comm_df['tid'] == 0) & (comm_df['mid'] == mid) & (comm_df['cid'] == cid)].index[0]
        comm_df.at[idx, 'val'] = comm        
    
    dlg.destroy()

def on_enter(ev):
    page_model['hoverdlg'].hide_tooltip()
    
    try:
        tv = page_model['treeview']        
        
        col_id = tv.column(tv.identify_column(ev.x), "id")        
        if not col_id.startswith('val'): return
        
        col_id = col_id[3:]
        row_id = tv.item(tv.identify_row(ev.y), 'values')[3]
        person_id = tv.item(tv.identify_row(ev.y), 'values')[int(col_id) + 4]
        
        msg = ''        
        person = get_person(page_model['person'], person_id)        
        if person is not None: msg = person['surname'] + ', ' + person['forename']
        
        comm = get_comment(page_model['comment'], page_tid, row_id, col_id) or ''
        
        if comm != '':
            if msg == '':
                msg = comm
            else:
                msg += '\n' + comm
        
        if msg == '': return
        
        x = tv.winfo_rootx()
        y = tv.winfo_rooty()

        page_model['hoverdlg'].show_tooltip(msg, x, y)
    except Exception:
        pass

def on_leave(event):
    page_model['hoverdlg'].hide_tooltip()
    
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
            [get_int_nzoe(row[f"val{i}"]) for i in range(page_col_count)]
        ))            
    
    person_match_df = pd.DataFrame(records, columns = ['mid'] + [f"val{i + 1}" for i in range(page_col_count)])
    
    if not save_table(page_tbl, person_match_df):
        messagebox.showerror('Error', 'Failed to save tbl_person_match.')
        return

    if not save_table('tbl_comment', page_model['comment']):
        messagebox.showerror('Error', 'Failed to save tbl_comment.')
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
                [int_nonzero_or_empty(row[f"val{k}"]) for k in range(page_col_count)]
            )
        )

    if callback: callback()