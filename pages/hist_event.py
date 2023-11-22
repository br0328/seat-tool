
from util import *
from ui import *

def init_tab(notebook):
    tab = create_tab(notebook, 'Hist-Events', on_tab_selected)
    
    create_treeview(
        master = tab,
        column_info = [
            ('line', { 'title': 'Line Nr.' }),
            ('surname', { 'title': 'Surname' }),
            ('forename', { 'title': 'Forename' }),
            ('mid', { 'title': 'Member-ID' })
        ],
        dbl_click_callback = on_treeview_dbl_clicked
    )
    create_control_panel(
        master = tab,
        button_info = {
            'Edit line': { 'click': on_edit_line_clicked },
            'Add new column': { 'click': on_add_column_clicked },
            'Save database': { 'click': on_save_db_clicked },
        }
    )

def on_tab_selected():
    pass

def on_treeview_dbl_clicked(tv, item):
    pass

def on_edit_line_clicked():
    pass

def on_add_column_clicked():
    pass

def on_save_db_clicked():
    pass
