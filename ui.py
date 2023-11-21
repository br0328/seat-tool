
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from model import *
from util import *
import tkinter as tk

def create_tab(master, name, callback):
    tab = ttk.Frame(master)
    master.add(tab, text = name)
    
    glob_model['tab_callback'][tab] = callback
    return tab

def create_treeview(master, column_info, edit_callback):
    tv = ttk.Treeview(master, columns = list(column_info.keys()), show = 'headings')

    for name, info in column_info.items():
        regularize_dict(info, {
            'title': '', 'width': 0, 'anchor': 'center'
        })
        tv.column(name, width = info['width'], anchor = info['anchor'])
        tv.heading(name, text = info['title'], anchor = 'center')

    tv.bind('<Double-1>', lambda e: edit_callback(tv, tv.identify_row(e.y)))
    tv.pack(expand = True, fill = 'both', padx = 10, pady = 10)

    return tv

def create_button(master, name, click_callback):
    but = tk.Button(master, text = name, command = click_callback)
    but.pack(side = tk.LEFT, padx = 4, pady = 5)
    return but

def create_control_panel(master, button_info):
    buttons = []
    
    for name, info in button_info.items():
        regularize_dict(info, {
            'click': None            
        })
        but = create_button(master, name, info['click'])
        buttons.append(but)
    
    return buttons
