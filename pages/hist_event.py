
""" Hist-Event Tab Page
"""

from tkinter import messagebox, Frame
from constant import *
from model import *
from util import *
from ui import *
import pandas as pd
import copy

page_model = {
    'backbone': None, # Back DataFrame
    'evdf': None, # Event DataFrame
    'treeview': None,
    'scroll': None,
    'column_info': None,
    'buttons': None,
    'history': [],
    'history_pos': 0,
    'evcount': None,
    'tab': None,
    'topframe': None
}

def init_tab(notebook):
    page_model['tab'] = create_tab(notebook, 'Hist-Events', on_tab_selected, on_save_db_clicked)
    
    page_model['topframe'] = top_frame = Frame(page_model['tab'], height = 700)
    top_frame.pack_propagate(False)
    top_frame.pack(fill = 'x', expand = False)
    
    on_tab_selected()    

def on_tab_selected():
    page_model['evdf'] = load_table('tbl_event', 'title')
    
    reset_history()
    heavy_refresh()

# Any change of Event table causes full refresh of the page
def heavy_refresh():
    if page_model['treeview']:
        page_model['treeview'].destroy()
        page_model['scroll'][0].destroy()
        page_model['scroll'][1].destroy()
        
        for _, but in page_model['buttons'].items():
            but.destroy()
    
    ev_df = page_model['evdf']
    person_df = load_table('tbl_person', 'surname, forename, mid')
    person_ev_df = load_table('tbl_person_event')
    
    page_model['column_info'] = [
        ('line', { 'title': 'Nr', 'width': 40 }),
        ('surname', { 'title': 'Nachname' }),
        ('forename', { 'title': 'Vorname' }),
        ('mid', { 'title': 'Member-ID' })
    ] + [
        (f"ev{i}", { 'title': row['title'], 'editable': True, 'dtype': int })
        for i, row in ev_df.iterrows()
    ]
    page_model['treeview'], page_model['scroll'] = create_treeview(
        master = page_model['topframe'],
        column_info = page_model['column_info'],
        dbl_click_callback = on_treeview_dbl_clicked
    )
    page_model['buttons'] = create_control_panel(
        master = page_model['tab'],
        button_info = {
            #'Edit line': { 'click': on_edit_line_clicked },
            'Neue Spalte hinzufügen': { 'click': on_add_column_clicked },
            'Datenbank speichern': { 'click': on_save_db_clicked },
            'Undo': { 'click': on_undo_clicked },
            'Redo': { 'click': on_redo_clicked }
        }
    )
    page_model['buttons']['Undo']['state'] = 'normal' if page_model['history_pos'] > 0 else 'disabled'
    page_model['buttons']['Redo']['state'] = 'normal' if page_model['history_pos'] < len(page_model['history']) - 1 else 'disabled'
    
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
    
    page_model['treeview'].bind(get_shortcut_button(), on_shortcut_clicked)
    update_treeview()

def on_undo_clicked():
    backward_history()

def on_redo_clicked():
    forward_history()
    
def on_shortcut_clicked(ev):
    tv = page_model['treeview']
    popup_menu = None
    
    try:
        region = tv.identify('region', ev.x, ev.y)
        
        if region == 'cell':
            ev_df = page_model['evdf']
            col_name = tv.column(tv.identify_column(ev.x), 'id')
            col_id = int(col_name[2:])

            popup_menu = tk.Menu(page_model['tab'], tearoff = 0)
            popup_menu.add_command(label = f"Spaltenüberschrift bearbeiten {ev_df.iloc[col_id]['title']}", command = lambda: on_edit_column_clicked(col_id))
            popup_menu.add_command(label = f"Spalte löschen {ev_df.iloc[col_id]['title']}", command = lambda: on_delete_column_clicked(col_id))
            popup_menu.add_command(label = 'Zellenwert bearbeiten', command = lambda: on_treeview_dbl_clicked(tv, tv.identify_row(ev.y), tv.identify_column(ev.x)))

            popup_menu.tk_popup(ev.x_root, ev.y_root)
    except Exception:
        pass
    finally:
        if popup_menu is not None: popup_menu.grab_release()

def on_edit_column_clicked(ev_id):
    ev_df = page_model['evdf']
    
    dlg = tk.Toplevel()
    dlg.title('Ereignis bearbeiten')

    evar = tk.StringVar(dlg, value = ev_df.iloc[ev_id]['title'])
    ent = tk.Entry(dlg, textvariable = evar)
    
    tk.Label(dlg, text = 'Veranstaltungsname: ').grid(row = 0, column = 0)
    ent.grid(row = 0, column = 1)
    
    entries = { 'title': evar }
    tk.Button(dlg, text = 'Speichern', command = lambda: on_edit_column(dlg, entries, ev_id)).grid(row = 1, column = 1)

def on_edit_column(dlg, entries, ev_id):    
    title = entries['title'].get()
    
    if title == '':
        messagebox.showerror('Fehler', 'Der Ereignisname sollte keine leere Zeichenfolge sein.')
        dlg.destroy()
        return
    
    ev_df = page_model['evdf']
    ev_df.at[ev_id, 'title'] = title    
    
    dlg.destroy()
    
    add_history()
    update_pending(True)
    heavy_refresh()
    
def on_delete_column_clicked(ev_id):
    ev_df = page_model['evdf']
    
    if messagebox.askyesno('Ereignis löschen', 'Bist du sicher, das du das löschen möchtest?'):
        page_model['evdf'] = ev_df.drop([ev_id]).reset_index(drop = True)
        
        add_history()
        update_pending(True)
        heavy_refresh()

def on_treeview_dbl_clicked(tv, item, col_id):
    if not item or not col_id: return

    try:
        col_name = tv.column(col_id, 'id')
        col_idx = int(col_name[2:])
    except Exception:
        return

    v = tv.item(item, 'values')[col_idx + 4]
    
    dlg = tk.Toplevel()
    dlg.title('Zelle bearbeiten')

    evar = tk.StringVar(dlg, value = v)
    ent = tk.Entry(dlg, textvariable = evar)
    
    tk.Label(dlg, text = 'Wert: ').grid(row = 0, column = 0)
    ent.grid(row = 0, column = 1)
    
    entries = { 'title': evar }
    tk.Button(dlg, text = 'Speichern', command = lambda: on_edit_cell(dlg, entries, item, col_idx)).grid(row = 1, column = 1)
    
# def on_edit_line_clicked():
#     tv = page_model['treeview']
    
#     try:
#         item = tv.selection()[0]
#         on_treeview_dbl_clicked(tv, item)
#     except Exception:
#         messagebox.showerror('Fehler', 'Bitte wählen Sie zunächst eine Zeile aus.')

def on_add_column_clicked():
    dlg = tk.Toplevel()
    dlg.title('Ereignis hinzufügen')

    evar = tk.StringVar(dlg, value = '')
    ent = tk.Entry(dlg, textvariable = evar)
    
    tk.Label(dlg, text = 'Veranstaltungsname: ').grid(row = 0, column = 0)
    ent.grid(row = 0, column = 1)
    
    entries = { 'title': evar }
    tk.Button(dlg, text = 'Hinzufügen', command = lambda: on_add_column(dlg, entries)).grid(row = 1, column = 1)

def on_add_column(dlg, entries):
    title = entries['title'].get()
    ev_df = page_model['evdf']
    
    if title == '':
        messagebox.showerror('Fehler', 'Der Ereignisname sollte keine leere Zeichenfolge sein.')
        dlg.destroy()
        return
    
    rec_dict = {
        'eid': max(list(ev_df['eid'])) + 1 if len(ev_df) > 0 else 1,
        'title': title,
        'display': max(list(ev_df['display'])) + 1 if len(ev_df) > 0 else 1
    }
    page_model['evdf'] = pd.concat([ev_df, pd.Series(rec_dict).to_frame().T], ignore_index = True)
    
    dlg.destroy()    
    
    add_history()
    update_pending(True)
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
        messagebox.showerror('Fehler', 'tbl_event konnte nicht gespeichert werden.')
        return
    
    if not save_table('tbl_person_event', person_ev_df):
        messagebox.showerror('Fehler', 'tbl_person_event konnte nicht gespeichert werden.')
        return

    bkup_db()
    update_pending(False)
    
    messagebox.showinfo('Erfolg', 'Datenbank erfolgreich gespeichert.')
    
def on_edit_cell(dlg, entries, item, col_idx):
    tv = page_model['treeview']
    idx = int(tv.item(item, 'values')[0]) - 1
    df = page_model['backbone']
    
    try:
        v = int(entries['title'].get())
    except Exception:
        messagebox.showerror('Geben Sie Fehler ein', 'Es muss ein ganzzahliger Wert sein.')
        return
        
    df.at[idx, f"ev{col_idx}"] = v
    
    dlg.destroy()
    
    add_history()
    update_pending(True)
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
        tv.insert(
            '', 'end', values = tuple(
                [i + 1, row['surname'], row['forename'], row['mid']] +
                [int_nonzero_or_empty(row[f"ev{k}"]) for k in range(page_model['evcount'])]
            )
        )

    if callback: callback()

def reset_history():
    page_model['history'].clear()
    page_model['history_pos'] = -1
    
    add_history()

def add_history():    
    df = copy.deepcopy(page_model['backbone'])
    ev_df = copy.deepcopy(page_model['evdf'])
    history = page_model['history']
    
    history = history[:page_model['history_pos'] + 1]
    history.append((df, ev_df))
    
    page_model['history'] = history
    page_model['history_pos'] = len(history) - 1
    
def backward_history():
    history_pos = page_model['history_pos']
    if history_pos <= 0: return False
    
    history_pos -= 1
    page_model['backbone'], page_model['evdf'] = copy.deepcopy(page_model['history'][history_pos])
    page_model['history_pos'] = history_pos
    
    update_pending(True)
    heavy_refresh()
    
    return True

def forward_history():
    history_pos = page_model['history_pos']
    if history_pos >= len(page_model['history']) - 1: return False
    
    history_pos += 1
    page_model['backbone'], page_model['evdf'] = copy.deepcopy(page_model['history'][history_pos])
    page_model['history_pos'] = history_pos
    
    update_pending(True)
    heavy_refresh()
    
    return True