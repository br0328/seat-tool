
""" Common UI functions based on TkInter
"""

from tkinter import messagebox
from tkinter import ttk
from model import *
from util import *
import ttkwidgets as ttkw
import tkinter as tk

class HoverInfo:
    def __init__(self, master):
        self.master = master
        self.tooltip = None
        self.hovering = False

    def show_tooltip(self, text, x, y):
        if not self.hovering:
            self.tooltip = tk.Toplevel(self.master)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            label = tk.Label(self.tooltip, text = text, background = "#ffffe0", relief = "solid", borderwidth = 1)
            label.pack(ipadx = 1)

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# Create a tab page
def create_tab(master, name, callback):
    tab = ttk.Frame(master)
    master.add(tab, text = name)
    
    glob_model['tab_callback'][name] = callback
    return tab

# Create a Treeview widget configured by column information and double-click callback function
def create_treeview(master, column_info, dbl_click_callback, style = 'Treeview', disable_select = False, disable_hscroll = False):
    tv = ttk.Treeview(master, columns = [key for key, _ in column_info], show = 'headings', style = style, selectmode = 'none' if disable_select else 'browse')

    for key, info in column_info:
        regularize_dict(info, {
            'title': '', 'width': 0, 'anchor': 'center', 'editable': False, 'dtype': str
        })
        tv.column(key, width = info['width'], anchor = info['anchor'], minwidth = 10)
        tv.heading(key, text = info['title'], anchor = 'center')

    # Add an external v-scrollbar
    vscrollbar = ttk.Scrollbar(master, orient = "vertical", command = tv.yview)
    vscrollbar.pack(side ='right', fill ='y')
    
    tv.configure(yscrollcommand = vscrollbar.set)
    
    if not disable_hscroll:
        # Add an external h-scrollbar
        hscrollbar = ttk.Scrollbar(master, orient = "horizontal", command = tv.xview)
        hscrollbar.pack(side ='bottom', fill ='x')
        
        tv.configure(xscrollcommand = hscrollbar.set)
    else:
        hscrollbar = None
    
    if dbl_click_callback is not None:
        tv.bind('<Double-1>', lambda e: dbl_click_callback(tv, tv.identify_row(e.y), tv.identify_column(e.x)))

    tv.pack(expand = True, fill = 'both', padx = 10, pady = 10)

    return tv, (vscrollbar, hscrollbar)

def create_checkbox_treeview(master, column_info, dbl_click_callback):
    tv = ttkw.CheckboxTreeview(master, columns = [key for key, _ in column_info], show = ('headings', 'tree'), selectmode = 'browse')

    for key, info in column_info:
        regularize_dict(info, {
            'title': '', 'width': 0, 'anchor': 'center', 'editable': False, 'dtype': str
        })
        tv.column(key, width = info['width'], anchor = info['anchor'])
        tv.heading(key, text = info['title'], anchor = 'center')

    # Add an external v-scrollbar
    vscrollbar = ttk.Scrollbar(master, orient = "vertical", command = tv.yview)
    vscrollbar.pack(side ='right', fill ='y')
    
    tv.configure(yscrollcommand = vscrollbar.set)    
    tv.bind('<Double-1>', lambda e: dbl_click_callback(tv, tv.identify_row(e.y), tv.identify_column(e.x)))
    tv.pack(expand = True, fill = 'both', padx = 10, pady = 10)

    return tv, vscrollbar

# Create a button with its click callback function
def create_button(master, name, click_callback):
    but = tk.Button(master, text = name, command = click_callback or show_not_developed_alert)
    but.pack(side = tk.LEFT, padx = 4, pady = 5)
    return but

# Create a control panel including numerous buttons
def create_control_panel(master, button_info):
    buttons = {}
    
    for name, info in button_info.items():
        regularize_dict(info, {
            'click': None
        })
        but = create_button(master, name, info['click'])
        buttons[name] = but
    
    return buttons

# Show entry input dialog for Add or Edit
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

# Dummy dialog
def show_not_developed_alert():
    messagebox.showerror('Error', 'This function is not yet developed.')
