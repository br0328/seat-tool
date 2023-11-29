
""" Main script
"""

from pages import personal_data
from pages import hist_event
from pages import new_event
from pages import match
from pages import no_match
from pages import never_match
from pages import selection
from pages import manual
from tkinter import ttk
from model import *
from util import *
from ui import *
import tkinter as tk
import os

# Run a callback function for a newly opened tab page
def on_tab_changed(e):
    tab = e.widget.select()
    name = e.widget.tab(tab, "text")
    
    callback = glob_model['tab_callback'][name] # The callback function is stored in glob_model['tab_callback']
    if callback: callback()

if not os.path.exists('./out/'): os.mkdir('./out/')

# UI root implementation
glob_model['root'] = root = tk.Tk()
root.title("Seating Generation")
root.update_idletasks()

new_width = root.winfo_width() * 5
new_height = root.winfo_height() * 4

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
manual.init_tab(notebook)

notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
root.mainloop()

close_db(True) # Close local db
