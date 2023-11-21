
from util import *
from ui import *

def init_tab(notebook):
    hist_event_tab = create_tab(notebook, 'Hist-Events', None)
    
    create_treeview(
        master = hist_event_tab,
        column_info = {
            'line': { 'title': 'Line Nr.' },
            'surname': { 'title': 'Surname' },
            'forename': { 'title': 'Forename' },
            'mid': { 'title': 'Member-ID' }
        },
        edit_callback = on_treeview_edit
    )
    create_control_panel(
        master = hist_event_tab,
        button_info = {
            'Edit line': { 'click': on_edit_line_clicked },
            'Add new column': { 'click': on_add_column_clicked },
            'Save database': { 'click': on_save_db_clicked },
        }
    )

def on_treeview_edit(tv, item):
    pass

def on_edit_line_clicked():
    pass

def on_add_column_clicked():
    pass

def on_save_db_clicked():
    pass
