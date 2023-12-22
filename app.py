
""" Main script
"""

from tkinter import ttk, messagebox
from pages import personal_data
from pages import hist_event
from pages import new_event
from pages import match
from pages import no_match
from pages import never_match
from pages import selection
from pages import manual
from pages import edit_event
from constant import *
from model import *
from util import *
from ui import *
import tkinter as tk
import os

# Run a callback function for a newly opened tab page
def on_tab_changed(e):
    tab = e.widget.select()
    name = e.widget.tab(tab, 'text')
    
    if glob_model['cur_tab'] is not None:
        save_callback = glob_model['save_callback'][glob_model['cur_tab_name']]
        
        if glob_model['pending'] and save_callback is not None:
            if messagebox.askyesno('Speichern', 'Es stehen noch Änderungen an.\nWerden Sie die Änderungen speichern?'):
                save_callback()

            update_pending(False)
    
    glob_model['cur_tab'] = tab
    glob_model['cur_tab_name'] = name
    open_callback = glob_model['tab_callback'][name] # The callback function is stored in glob_model['tab_callback']
    
    if open_callback: open_callback()

def on_window_close():
    if glob_model['cur_tab'] is not None:
        save_callback = glob_model['save_callback'][glob_model['cur_tab_name']]
        
        if glob_model['pending'] and save_callback is not None:
            if messagebox.askyesno('Speichern', 'Es stehen noch Änderungen an.\nWerden Sie die Änderungen speichern?'):
                save_callback()                

    glob_model['root'].destroy()

if not os.path.exists('./out/'): os.mkdir('./out/')
if not os.path.exists('./bkup/'): os.mkdir('./bkup/')

# UI root implementation
glob_model['root'] = root = tk.Tk()

root.protocol('WM_DELETE_WINDOW', on_window_close)
root.title(root_title)
root.update_idletasks()

new_width = root_width#root.winfo_width() * 5
new_height = root_height#root.winfo_height() * 4

root.geometry(f"{new_width}x{new_height}")

notebook = ttk.Notebook(root)
notebook.pack(expand = True, fill = 'both', padx = 10, pady = 10)

# Add tab pages
personal_data.init_tab(notebook)
hist_event.init_tab(notebook)
match.init_tab(notebook)
no_match.init_tab(notebook)
never_match.init_tab(notebook)
selection.init_tab(notebook)
new_event.init_tab(notebook)
edit_event.init_tab(notebook)
manual.init_tab(notebook)

notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
root.mainloop()

close_db(True) # Close local db
