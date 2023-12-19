
""" Manual HTML Tab Page
"""

from tkhtmlview import HTMLScrolledText, RenderHTML
from tkinter import messagebox
from constant import *
from ui import *

page_model = {
    'tab': None,
    'webview': None
}

def init_tab(notebook):
    page_model['tab'] = create_tab(notebook, 'Manual', on_tab_selected)
    
def on_tab_selected():
    if page_model['webview'] is not None: return
    
    # webview = HTMLText(root, html=RenderHTML('index.html'))
    # webview.pack(fill="both", expand=True)
    # webview.fit_height()

    webview = HTMLScrolledText(page_model['tab'], html = RenderHTML(manual_doc_path))
    webview.pack(expand = True, fill = 'both', padx = 10, pady = 10)

    # if os.path.exists(manual_doc_path):
    #     with open(manual_doc_path, 'r', encoding = 'utf-8') as fp:
    #         html = fp.read()
    #         webview.set_html(html)
    # else:
    #     messagebox.showerror("Error", f"The file `{manual_doc_path}` was not found.")
    #     return
    
    page_model['webview'] = webview