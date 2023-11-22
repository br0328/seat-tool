
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from model import *
from util import *
import tkinter as tk

def create_tab(master, name, callback):
    tab = ttk.Frame(master)
    master.add(tab, text = name)
    
    glob_model['tab_callback'][name] = callback
    return tab

def create_treeview(master, column_info, dbl_click_callback):
    tv = ttk.Treeview(master, columns = [key for key, _ in column_info], show = 'headings')

    for key, info in column_info:
        regularize_dict(info, {
            'title': '', 'width': 0, 'anchor': 'center', 'editable': False, 'dtype': str
        })
        tv.column(key, width = info['width'], anchor = info['anchor'])
        tv.heading(key, text = info['title'], anchor = 'center')

    vscrollbar = ttk.Scrollbar(master, orient = "vertical", command = tv.yview)
    vscrollbar.pack(side ='right', fill ='y')
    
    tv.configure(yscrollcommand = vscrollbar.set)    
    tv.bind('<Double-1>', lambda e: dbl_click_callback(tv, tv.identify_row(e.y)))
    tv.pack(expand = True, fill = 'both', padx = 10, pady = 10)

    return tv, vscrollbar

def create_button(master, name, click_callback):
    but = tk.Button(master, text = name, command = click_callback or show_not_developed_alert)
    but.pack(side = tk.LEFT, padx = 4, pady = 5)
    return but

def create_control_panel(master, button_info):
    buttons = {}
    
    for name, info in button_info.items():
        regularize_dict(info, {
            'click': None
        })
        but = create_button(master, name, info['click'])
        buttons[name] = but
    
    return buttons

def show_entry_dlg(is_add, values, column_info, callback, tags = ()):
    dlg = tk.Toplevel()
    dlg.title('Add Entry' if is_add else 'Edit Entry')

    entries, row = {}, 0
    
    for i, ci in enumerate(column_info):
        key, info = ci
        if not info['editable']: continue
        
        evar = tk.StringVar(dlg, value = values[i])
        ent = tk.Entry(dlg, textvariable = evar)
        
        tk.Label(dlg, text = info['title'] + ': ').grid(row = row, column = 0)
        ent.grid(row = row, column = 1)
        
        entries[key] = evar
        row += 1

    tk.Button(dlg, text = 'Add' if is_add else 'Save', command = lambda: callback(dlg, entries, tags)).grid(row = row, column = 1)

def show_not_developed_alert():
    messagebox.showerror('Error', 'This function is not yet developed.')
