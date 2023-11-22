
from tkinter import filedialog, messagebox
from tkhtmlview import HTMLScrolledText
from constant import *
from model import *
from util import *
from ui import *
import pandas as pd

page_model = {
    'tab': None,
    'webview': None
}

def init_tab(notebook):
    page_model['tab'] = create_tab(notebook, 'Manual', on_tab_selected)
    
def on_tab_selected():
    if page_model['webview'] is not None: return
    
    webview = HTMLScrolledText(page_model['tab'])
    webview.pack(expand = True, fill = 'both', padx = 10, pady = 10)

    if os.path.exists(manual_doc_path):
        with open(manual_doc_path, 'r', encoding = 'utf-8') as fp:
            html = fp.read()
            webview.set_html(html)
    else:
        messagebox.showerror("Error", f"The file `{manual_doc_path}` was not found.")
        return
    
    page_model['webview'] = webview