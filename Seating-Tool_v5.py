import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import pandas as pd
import sqlite3
import os
from tkhtmlview import HTMLScrolledText
#from tkhtmlview import HTMLLabel
# import fitz  # PyMuPDF
#from PIL import Image, ImageTk


# Globale Variable für das DataFrame
df = None

# Globale Variable für den Treeview
tv = None

history = []  # History-Stack zum Speichern von Zuständen vor Änderungen

redo_history = []  # Stack für Redo


########################################################################################################
def save_state(df):
    """Saves the current status of the DataFrame in the undo stack."""
    global history
    history.append(df.copy())

def undo():
    """Restores the last state of the DataFrame from the undo stack and saves the current state in the redo stack."""
    global df, history, redo_history
    if history:
        redo_history.append(df.copy())  # Save the current state in the redo stack
        df = history.pop()
        display_data_in_treeview()  # You need to translate the function name and its definition too
    else:
        messagebox.showinfo("Undo", "No further steps to undo.")

def redo():
    """Restores the last undone step from the redo stack."""
    global df, history, redo_history
    if redo_history:
        history.append(df.copy())  # Save the current state for possible re-undoing
        df = redo_history.pop()
        display_data_in_treeview()  # You need to translate the function name and its definition too
    else:
        messagebox.showinfo("Redo", "No further steps to restore.")  # "Wiederherstellen" translated to "Redo"


########################################################################################################
def check_duplicates_in_df(df):
    # Check for Case A
    full_duplicates = df[df.duplicated(subset=['Forename', 'Surname', 'Member_ID'], keep=False)]
    if not full_duplicates.empty:
        messagebox.showwarning(
            "Duplicates Found - Case A",
            "Complete duplicates found:\n" + full_duplicates.to_string(index=False),
            
        )
        return True  # Duplicates were found

    # Check for Case B
    partial_duplicates = df[df.duplicated(subset=['Forename', 'Surname'], keep=False) & ~df.duplicated(subset=['Member_ID'], keep=False)]
    if not partial_duplicates.empty:
        messagebox.showwarning(
            "Duplicates Found - Case B",
            "Partial duplicates found (same forename and surname):\n" + partial_duplicates.to_string(index=False)
        )
        return True  # Duplicates were found

    # Check for Case C
    member_id_duplicates = df[df.duplicated(subset=['Member_ID'], keep=False)]
    if not member_id_duplicates.empty:
        messagebox.showwarning(
            "Duplicates Found - Case C",
            "Duplicates with the same Member_ID found:\n" + member_id_duplicates.to_string(index=False)
        )
        return True  # Duplicates were found

    return False  # No duplicates found




def display_and_decide(df_duplicates, color, df_new_copy, do_not_import_list):
    if not df_duplicates.empty:
        response = messagebox.askyesno(
            f"Duplicates Found - Case {color}",
            f"Duplicates in case {color} found:\n{df_duplicates.to_string(index=False)}\nDo you want to import these entries?"
        )
        if response:
            # The user wants to import the duplicates.
            # No action required as the rows are already in df_new_copy
            pass
        else:
            # The user does not want to import the duplicates.
            # Add the indices of the duplicates to be removed to the list
            indices_to_remove = df_duplicates.index[df_duplicates.index >= len(df)].tolist()
            do_not_import_list.extend([index - len(df) for index in indices_to_remove])














########################################################################################################
def import_contacts():
    global df
    filepath = filedialog.askopenfilename(title="Select a CSV file", filetypes=[("CSV files", "*.csv")])
    if not filepath:
        return
    df_new = pd.read_csv(filepath, usecols=['Forename', 'Surname', 'Member_ID', 'Branch'])

    if df_new['Member_ID'].isnull().any():
        # Find the current highest Member_ID
        highest_member_number = df_new['Member_ID'].max()
        next_member_number = highest_member_number + 1 if pd.notna(highest_member_number) else 1
        next_member_number = int(next_member_number)
    
        messagebox.showerror(
            "Import Error",
            "There are entries without Member_ID in the CSV file. Please add a Member_ID in Editor X and export the CSV file again.\n"
            f"The next available Member_ID is: {next_member_number}"
        )
        return  # Abort the import

    # Convert data to integers, treating non-integer values as NaN
    try:
        df_new['Member_ID'] = pd.to_numeric(df_new['Member_ID'], errors='coerce').fillna(0).astype('int64')
    except pd.errors.IntCastingNaNError as e:
        messagebox.showerror("Import Error", "Non-numeric values in the Member_ID column.")
        return
    
    # Check for Case A: Complete duplicates in the new file
    full_duplicates = df_new[df_new.duplicated(subset=['Forename', 'Surname', 'Member_ID'], keep=False)]
    if not full_duplicates.empty:
        messagebox.showwarning(
            "Duplicates Found - Case Orange",
            "Identical duplicates (Orange) found within the import CSV file:\n\n" + full_duplicates.to_string(index=False) + "\n\nPlease eliminate the duplicates in Editor X and create a new duplicate-free CSV file."
        )
        return  # Stop the import if complete duplicates are found

    # Check for Case B: Partial duplicates in the new file
    partial_duplicates = df_new[df_new.duplicated(subset=['Forename', 'Surname'], keep=False) & ~df_new.duplicated(subset=['Member_ID'], keep=False)]
    if not partial_duplicates.empty:
        response = messagebox.askyesno(
            "Duplicates Found - Case Red",
            "Duplicates with identical forename and surname but different Member_IDs found within the import CSV file:\n\n" + partial_duplicates.to_string(index=False) + "\n\nDo you want to continue with the import?"
        )
        if not response:
            return  # Stop the import if the user chooses 'Do Not Import'

    # Check for Case C: Member_ID duplicates in the new file
    member_id_duplicates = df_new[df_new.duplicated(subset=['Member_ID'], keep=False)]
    if not member_id_duplicates.empty:
        messagebox.showwarning(
            "Duplicates Found - Case Blue",
            "Duplicates with the same Member_ID (Blue) found within the import CSV file:\n\n" + member_id_duplicates.to_string(index=False) + "\n\nPlease change the Member_ID in Editor X and create a new duplicate-free CSV file."
        )
        return  # Stop the import if Member_ID duplicates are found

    # Remove duplicates from the new file
    df_new = df_new.drop_duplicates(subset=['Forename', 'Surname', 'Member_ID'], keep='first')

    # A temporary list to store the indices of duplicates to be removed
    indices_to_remove = []












   # Combine the new DataFrame with the existing one
    
    if df is not None:
        df_new_copy = df_new.copy()
        combined_df = pd.concat([df, df_new_copy], ignore_index=True)

        indices_to_remove = []
    
        # Remove orange duplicates directly without user interaction
        orange_case_duplicates = combined_df.duplicated(subset=['Forename', 'Surname', 'Member_ID'], keep=False)
        df_orange = combined_df[orange_case_duplicates]
        indices_to_remove.extend(df_orange.index[df_orange.index >= len(df)].tolist())

        # Check for blue duplicates
        blue_case_duplicates = combined_df.duplicated(subset=['Member_ID'], keep=False) & ~orange_case_duplicates
        df_blue = combined_df[blue_case_duplicates]
        decide_and_collect(df_blue, "Blue", indices_to_remove)
    
        # Check for red duplicates
        red_case_duplicates = combined_df.duplicated(subset=['Forename', 'Surname'], keep=False) & ~combined_df.duplicated(subset=['Member_ID'], keep=False)
        df_red = combined_df[red_case_duplicates]
        decide_and_collect(df_red, "Red", indices_to_remove)
    
        # Remove the lines to be removed from df_new
        df_new.drop(df_new.index[[index - len(df) for index in indices_to_remove if index >= len(df)]], inplace=True)

        # Add the cleaned new data to the existing DataFrame
        df = pd.concat([df, df_new], ignore_index=True)

    else:
        df = df_new

    display_data_in_treeview()
    messagebox.showinfo("Import", "Entries have been imported and duplicates removed, if any.")



def decide_and_collect(df_duplicates, color, indices_to_remove):
    global df
    if not df_duplicates.empty:
        response = messagebox.askyesno(
            f"Duplicates Found - Case {color}",
            f"Duplicates between import CSV file and database in case {color} found:\n\n{df_duplicates.to_string(index=False)}\n\nDo you want to import these entries?"
        )
        if not response:
            # Add the indices of the duplicates to be removed to the list
            indices_to_remove.extend(df_duplicates.index[df_duplicates.index >= len(df)].tolist())














########################################################################################################
def load_database():
    global df, tv
    if not os.path.isfile('kontakte.db'):
        messagebox.showerror("Error", "The database 'kontakte.db' does not exist.")
        return
    conn = sqlite3.connect('kontakte.db')
    try:
        df = pd.read_sql('SELECT * FROM kontakte', conn)
        
        # Convert numbers to integers
        df['Member_ID'] = df['Member_ID'].astype('int64')
        duplicates_found = check_for_duplicates(df)
        if duplicates_found:
            messagebox.showinfo("Duplicates Found", "Duplicates have been found in the database. \n They are highlighted in blue, red, and orange. \n Please check the marked entries.")
        display_data_in_treeview_Personal_Data(tv)  # Updated for the "Personal_Data" tab
    except pd.io.sql.DatabaseError as e:
        messagebox.showerror("Error", f"Error loading the database: {e}")
    finally:
        conn.close()


########################################################################################################
def save_to_database():
    global df
    if df is None or df.empty:
        messagebox.showinfo("Information", "There are no contacts to save.")
        return
    conn = sqlite3.connect('kontakte.db')
    try:
        df.to_sql('kontakte', conn, if_exists='replace', index=False)  # Use 'replace' to overwrite the existing table
        messagebox.showinfo("Information", "Contacts have been saved to the database!")
    except Exception as e:
        messagebox.showerror("Error", f"Error saving to the database: {e}")
    finally:
        conn.close()
    
    # Clear the table display in the Treeview after saving
    #clear_data_in_treeview()

########################################################################################################
def clear_data_in_treeview():
    global tv
    # Delete all existing entries in the Treeview
    tv.delete(*tv.get_children())
    # Remove the columns
    tv['columns'] = []
    for col in tv['columns']:
        tv.heading(col, text="")
        tv.column(col, width=0, minwidth=0)










########################################################################################################
def check_for_duplicates(df):
    # First, we create new columns for the check, initialized with False
    df['duplicated_full'] = False
    df['duplicated_names'] = False
    df['duplicated_member_number'] = False

    # Check for Case A
    full_duplicates_mask = df.duplicated(subset=['Forename', 'Surname', 'Member_ID'], keep=False)
    df.loc[full_duplicates_mask, 'duplicated_full'] = True

    # Check for Case B
    partial_duplicates_mask = df.duplicated(subset=['Forename', 'Surname'], keep=False) & ~df.duplicated(subset=['Member_ID'], keep=False)
    df.loc[partial_duplicates_mask, 'duplicated_names'] = True

    # Check for Case C
    member_id_duplicates_mask = df.duplicated(subset=['Member_ID'], keep=False)
    df.loc[member_id_duplicates_mask, 'duplicated_member_number'] = True


########################################################################################################
def clean_duplicates(df):
    return df.drop_duplicates(subset=['Forename', 'Surname'], keep='first')


########################################################################################################
def edit_selected_row(treeview, tab_name):
    try:
        selected_item = treeview.selection()[0]  # The ID of the selected row in the given Treeview
        edit_entry(treeview, tab_name, selected_item)
    except IndexError:
        messagebox.showerror("Error", "Please select a row first.")


    
########################################################################################################
def edit_entry(treeview, tab_name, item):
    if not item:
        messagebox.showerror("Error", "No row selected.")
        return

    values = treeview.item(item, 'values')
    edit_window = tk.Toplevel()
    edit_window.title("Edit Entry")

    editable_columns = []
    if tab_name == 'Personal_Data':
        editable_columns = ['Surname', 'Forename', 'Member_ID']
    elif tab_name == 'Match':
        editable_columns = ['Match_1', 'Match_2', 'Match_3', 'Match_4', 'Match_5']

    entries = {}
    for i, label in enumerate(editable_columns, start=1):
        tk.Label(edit_window, text=label).grid(row=i, column=0)
        # Here is the adjustment:
        value_index = i + 4 if tab_name == 'Match' else i
        entry_var = tk.StringVar(edit_window, value=values[value_index])
        entry = tk.Entry(edit_window, textvariable=entry_var)
        entry.grid(row=i, column=1)
        entries[label] = entry_var

    tk.Button(edit_window, text="Save", command=lambda: save_changes(item, entries, editable_columns, edit_window, treeview)).grid(row=len(editable_columns) + 1, column=1)






########################################################################################################
########################################################################################################
def save_changes(item, entries, editable_columns, edit_window, treeview):
    row_number = treeview.item(item, "values")[0]
    
    # First sort the DataFrame and reset the index
    df.sort_values(by=['Surname', 'Forename', 'Member_ID'], ascending=True, inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    df_index = int(row_number) - 1  # Convert to 0-based index
    
    # Update the DataFrame with the new values from the input fields
    for label, entry_var in entries.items():
        # Check if the value is a number and convert it accordingly
        if label == 'Member_ID':  # or any other column that expects a number
            try:
                # Try to convert the value to an integer
                df.at[df_index, label] = int(entry_var.get())
            except ValueError:
                # If the conversion fails, show an error message
                messagebox.showerror("Error", f"The value for {label} must be an integer.")
                return  # End the function prematurely
        else:
            # For all other columns that expect strings, insert the value directly
            df.at[df_index, label] = entry_var.get()
    
    # Close the editing window.
    edit_window.destroy()
    
    # Update the duplicate status in the DataFrame.
    check_for_duplicates(df)
    
    # Update the Treeview for 'Personal_Data'
    # display_data_in_treeview(tv)

    # Update the Treeview for 'Match'
    # display_data_in_treeview(tv4)
    
    
    if treeview == tv:  # If the Treeview corresponds to the "Personal_Data" tab
        display_data_in_treeview_Personal_Data(treeview)  # Updated for the "Personal_Data" tab
    else:
        display_data_in_treeview(treeview)  # Remains for the "Match" tab
    

        
    
    

########################################################################################################
def add_column():
    global df, tv
    column_name = simpledialog.askstring("New Column", "Enter the name of the new column:")
    if column_name:
        if column_name in df.columns:
            messagebox.showerror("Error", f"Column '{column_name}' already exists.")
            return
        df[column_name] = ""  # Add new column with empty strings
        display_data_in_treeview()  # Update the Treeview







        
        
########################################################################################################
def delete_selected_row():
    global df    
    save_state(df)  # Save the state before deleting   

    df = df.sort_values(by=['Surname', 'Forename', 'Member_ID'], ascending=True).reset_index(drop=True)
    
    selected_items = tv.selection()
    if not selected_items:
        messagebox.showerror("Error", "Please select a row to delete.")
        return

    # Create a list of the selected DataFrame indices based on the row number in the Treeview
    indices_to_drop = [df.index[int(tv.item(item, 'values')[0]) - 1] for item in selected_items]
    
    # Delete the corresponding rows in the DataFrame
    df = df.drop(indices_to_drop).reset_index(drop=True)

    # Update the Treeview to reflect the deleted rows
    display_data_in_treeview_Personal_Data(tv)  # Updated for the "Personal_Data" tab


########################################################################################################
def check_and_show_duplicates():
    global df
    if df is None or df.empty:
        messagebox.showinfo("Information", "There are no contacts to check.")
        return

    # First sort the DataFrame
    df.sort_values(by=['Surname', 'Forename', 'Member_ID'], ascending=True, inplace=True)

    # Find the indices of duplicates
    duplicates_mask = df.duplicated(subset=['Forename', 'Surname'], keep=False)

    if duplicates_mask.any():
        number_of_duplicates = duplicates_mask.sum()
        response = messagebox.askyesno("Duplicates Found", 
                                      f"{number_of_duplicates} duplicates found. Would you like to display them?")
        if response:
            # Do not clean the duplicates, just show them
            display_data_in_treeview()
    else:
        messagebox.showinfo("No Duplicates", "No duplicates were found.")
        display_data_in_treeview()


########################################################################################################
def add_row():
    # Dialog window to add a new row
    add_window = tk.Toplevel()
    add_window.title("Add New Entry")

    # Labels and Entry Widgets
    labels = ['Forename', 'Surname', 'Member_ID']
    entries = {}
    for i, label in enumerate(labels):
        tk.Label(add_window, text=label).grid(row=i, column=0)
        entry = tk.Entry(add_window)
        entry.grid(row=i, column=1)
        entries[label] = entry

    # Button to add the new row
    tk.Button(add_window, text="Add", command=lambda: save_new_row(entries, add_window)).grid(row=len(labels), column=1)
    display_data_in_treeview_Personal_Data(tv)  # Updated for the "Personal_Data" tab









########################################################################################################
def save_new_row(entries, add_window):
    new_data = {label: entry.get() for label, entry in entries.items()}
    global df
    # Add the new data to the DataFrame.
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    add_window.destroy()
    
    # Update the duplicate status in the DataFrame.
    check_for_duplicates(df)
    
    # Update the Treeview.
    display_data_in_treeview()


########################################################################################################
def display_data_in_treeview(treeview):
    global df

    # Delete existing data in the Treeview
    treeview.delete(*treeview.get_children())
    
    # Check if df exists and is not empty
    if df is not None and not df.empty:
        # Convert Match columns to integers, if they exist
        df = convert_match_columns_to_int(df)

        # Sort the DataFrame and reset the index
        df.sort_values(by=['Surname', 'Forename', 'Member_ID'], ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Check for duplicates in each case
        df['duplicated_full'] = df.duplicated(subset=['Forename', 'Surname', 'Member_ID'], keep=False)
        df['duplicated_names'] = df.duplicated(subset=['Forename', 'Surname'], keep=False) & ~df['duplicated_full']
        df['duplicated_member_number'] = df.duplicated(subset=['Member_ID'], keep=False) & ~df['duplicated_full']

        # Insert the sorted data into the Treeview
        for index, row in df.iterrows():
            tags = ()
            if row['duplicated_full']:
                tags = ('full_duplicate',)
            elif row['duplicated_names']:
                tags = ('name_duplicate',)
            elif row['duplicated_member_number']:
                tags = ('member_id_duplicate',)

            match_values = [row.get('Match_1', ''), row.get('Match_2', ''), row.get('Match_3', ''), row.get('Match_4', ''), row.get('Match_5', '')]

            treeview.insert('', 'end', values=(index + 1, row['Surname'], row['Forename'], row['Member_ID'], row['Branch']) + tuple(match_values), tags=tags)

        # Configure the tags to highlight duplicates
        treeview.tag_configure('full_duplicate', background='orange')
        treeview.tag_configure('name_duplicate', background='salmon')
        treeview.tag_configure('member_id_duplicate', background='light blue')








# Function to read the HTML content from the file
def read_html_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return "<p>File not found.</p>"
    
    
########################################################################################################
def display_html_in_tab7():
    # Path to the HTML file
    html_filepath = "User-Manual.html"
    
    # Remove all previous widgets from Tab 2, if present
    for widget in tab7.winfo_children():
        widget.destroy()
    
    # Create the HTML display widget in Tab 2
    html_display = HTMLScrolledText(tab7)
    html_display.pack(expand=True, fill='both', padx=10, pady=10)

    # Read the HTML content from the file and display it in the widget
    if os.path.exists(html_filepath):
        with open(html_filepath, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()
            html_display.set_html(html_content)
    else:
        messagebox.showerror("Error", f"The file '{html_filepath}' was not found.")


########################################################################################################
def tab_changed(event):
    selected_tab = event.widget.select()
    tab_text = event.widget.tab(selected_tab, "text")
    
    if tab_text == 'Personal_Data':
        # Make buttons visible for Tab 1
        for button in buttons:
            button.pack(side=tk.LEFT, padx=4, pady=5)
        display_data_in_treeview(tv)
    elif tab_text == 'Match':
        # Display data for Match_Tab
        display_data_in_treeview(tv4)
    elif tab_text == "Manual":
        # Hide the buttons for Tab 2
        for button in buttons:
            button.pack_forget()
        # Show HTML content in Tab 2
        display_html_in_tab7()


########################################################################################################
def load_excel_file():
    global df
    filepath = filedialog.askopenfilename(title="Select an Excel file", filetypes=[("Excel files", "*.xlsx")])
    if not filepath:
        return  # User cancelled the dialog

    try:
        # Load the Excel file into a temporary DataFrame
        df_temp = pd.read_excel(filepath)
        
        print(df_temp)

        # Rename the 'ID' column to 'Member_ID'
        df_temp.rename(columns={'ID': 'Member_ID'}, inplace=True)
        
        df_temp.rename(columns={'Branch_Categories': 'Branch'}, inplace=True)

        # Optionally, rename more columns if necessary
        # df_temp.rename(columns={'old_column1': 'new_column1', 'old_column2': 'new_column2'}, inplace=True)

        # If df already exists and is not empty, you can decide whether to add the data 
        # or replace the existing DataFrame.
        if df is not None and not df.empty:
            # Combine df with df_temp, for example by adding or merging, as needed.
            # Example: df = pd.concat([df, df_temp], ignore_index=True)
            df = df_temp  # Replaces the existing DataFrame if you want.
        else:
            df = df_temp

        messagebox.showinfo("Success", "Excel file loaded successfully!")
        display_data_in_treeview(tv)  # Update the Treeview with the new data
    except Exception as e:
        messagebox.showerror("Error", f"Error loading the Excel file: {e}")










########################################################################################################
def show_comment_dialog(event):
    # Check if a row is selected in the Treeview
    selected_item = tv.selection()
    if selected_item:
        item_id = selected_item[0]
        # Open a dialog to enter a comment
        comment = simpledialog.askstring("Comment", "Enter a comment:")
        if comment:
            # Here you can add the comment to an internal structure or process it
            print(f"Comment for Item {item_id}: {comment}")


########################################################################################################
def right_click_menu(event):
    try:
        region = tv.identify("region", event.x, event.y)
        if region == "cell":
            row_id = tv.identify_row(event.y)
            col_id = tv.identify_column(event.x)
            column_name = tv.column(col_id, "id")
            item_id = tv.item(row_id, 'values')[0]

            # Load and display the comment
            old_comment = load_comment(item_id, column_name)
            
            # Create a popup menu
            popup_menu = tk.Menu(root, tearoff=0)
            popup_menu.add_command(label="Show Comment", command=lambda: show_comment(old_comment))
            popup_menu.add_command(label="Edit Comment", command=lambda: edit_comment_dialog(item_id, column_name, old_comment))

            # Display the popup menu at the position of the cursor
            popup_menu.tk_popup(event.x_root, event.y_root)
    finally:
        # Ensure that the popup menu is released
        popup_menu.grab_release()


########################################################################################################
def show_comment(comment):
    messagebox.showinfo("Comment", comment)




########################################################################################################
def edit_comment_dialog(item_id, column_name, old_comment):
    new_comment = simpledialog.askstring("Edit Comment", "Enter comment:", initialvalue=old_comment)
    if new_comment is not None and new_comment != old_comment:
        save_comment(item_id, column_name, new_comment)
        # Optionally: Update the Treeview if you want to display the comment directly
        # tv.set(row_id, column=col_id, value=new_comment)





########################################################################################################
# Initialize the database and the 'comments' table with the new schema
def initialize_database():
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        item_id TEXT NOT NULL,
        column_name TEXT NOT NULL,
        comment TEXT,
        PRIMARY KEY (item_id, column_name)
    )
    ''')
    
    conn.commit()
    conn.close()











########################################################################################################
# Saving comments to the database
def save_comment(item_id, column_name, comment):
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    # Save the comment with the item_id and column name
    cursor.execute('''INSERT OR REPLACE INTO comments (item_id, column_name, comment)
                      VALUES (?, ?, ?)''', (item_id, column_name, comment))
    conn.commit()
    conn.close()


########################################################################################################
# Loading comments from the database
def load_comment(item_id, column_name):
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    # Load the comment that matches the item_id and column name
    cursor.execute('SELECT comment FROM comments WHERE item_id = ? AND column_name = ?', (item_id, column_name))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ""




########################################################################################################
def find_next_Member_ID():
    global df
    highest_number_db = df['Member_ID'].max() if df is not None and not df.empty else 0
    filepath = filedialog.askopenfilename(title="Select the current CSV file corresponding to the status of Editor X.", filetypes=[("CSV Files", "*.csv")])
    if not filepath:
        messagebox.showinfo("Action Cancelled", "No CSV file selected.")
        return

    try:
        df_csv = pd.read_csv(filepath, usecols=['Member_ID'])
        highest_number_csv = df_csv['Member_ID'].max() if not df_csv.empty else 0
    except Exception as e:
        messagebox.showerror("Error", f"Error reading the CSV file: {e}")
        return

    highest_number = max(highest_number_db, highest_number_csv)
    next_number = int(highest_number + 1)
    messagebox.showinfo("Next free Member_ID", f"The next free Member_ID is: {next_number}")



########################################################################################################
def convert_match_columns_to_int(df):
    match_columns = ['Match_1', 'Match_2', 'Match_3', 'Match_4', 'Match_5']
    for column in match_columns:
        if column in df.columns:
            # Convert the column to numeric values, NaNs become 0
            df[column] = pd.to_numeric(df[column], errors='coerce').fillna(0).astype(int)
    return df



########################################################################################################
# Insert the data without Match columns
def display_data_in_treeview_Personal_Data(treeview):
    global df
    # Clear existing data in the Treeview
    treeview.delete(*treeview.get_children())
    
    # Check if df is present and not empty
    if df is not None and not df.empty:
        # Convert Match columns to Integer if they exist
        df = convert_match_columns_to_int(df)

        # Sort the DataFrame and reset the index
        df.sort_values(by=['Surname', 'Forename', 'Member_ID'], ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Check for duplicates in each case
        check_for_duplicates(df)

        # Insert the sorted data into the Treeview
        for index, row in df.iterrows():
            tags = ()  # Empty tag as default
            if row['duplicated_full']:
                tags = ('full_duplicate',)
            elif row['duplicated_names']:
                tags = ('names_duplicate',)
            elif row['duplicated_member_number']:
                tags = ('member_number_duplicate',)
            
            # Note that here you insert only the data for the existing columns
            treeview.insert('', 'end', values=(index + 1, row['Surname'], row['Forename'], row['Member_ID'], row['Branch']), tags=tags)

        # Configure the tags to highlight duplicates
        treeview.tag_configure('full_duplicate', background='orange')
        treeview.tag_configure('names_duplicate', background='salmon')
        treeview.tag_configure('member_number_duplicate', background='light blue')

















########################################################################################################
# Create the main window
root = tk.Tk()
root.title("Seating Generation")


initialize_database()


# Wait for the window to be rendered
root.update_idletasks()

# Get the current width and height of the window
current_width = root.winfo_width()
current_height = root.winfo_height()

# Set the new width and height (double the size)
new_width = current_width * 5
new_height = current_height * 5

# Update the size of the window
root.geometry(f"{new_width}x{new_height}")

# Create a Notebook (Tab Widget)
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both', padx=10, pady=10)



########################################################################################################
########################################################################################################
# Tab 1: Personal_Data
########################################################################################################

tab1 = ttk.Frame(notebook)
notebook.add(tab1, text='Personal_Data')

# Create a Treeview for the database table in Tab 1
tv = ttk.Treeview(tab1, columns=('Line-No', 'Surname', 'Forename', 'Member_ID', 'Branch'), show='headings')

# Configure the columns with alignment to the center
tv.column('Line-No', width=40, anchor='center')
tv.column('Surname', width=100, anchor='center')
tv.column('Forename', width=100, anchor='center')
tv.column('Member_ID', width=100, anchor='center')
tv.column('Branch', width=100, anchor='center')

# Configure the column headings with alignment to the center
tv.heading('Line-No', text='Line No.', anchor='center')
tv.heading('Surname', text='Surname', anchor='center')
tv.heading('Forename', text='Forename', anchor='center')
tv.heading('Member_ID', text='Member_ID', anchor='center')
tv.heading('Branch', text='Branch', anchor='center')

# Bind the double-click event to the Treeview
tv.bind('<Double-1>', lambda e: edit_entry(tv, 'Personal_Data', tv.identify_row(e.y)))

tv.pack(expand=True, fill='both', padx=10, pady=10)



# Bind the right-click event to the Treeview
tv.bind("<Button-3>", right_click_menu)  # '<Button-3>' is the right-click event on Windows and Unix, on macOS use '<Button-2>'













########################
# Add the buttons

# Initialize the buttons outside of the function so that they are only created once
# Ensure these variables are defined before the `tab_changed` function
btn_load = tk.Button(tab1, text="Load SQL \n Database", command=load_database)
btn_load_excel = tk.Button(tab1, text="Load XLS \n Database", command=load_excel_file)
btn_import = tk.Button(tab1, text="Import Contacts \n from CSV", command=import_contacts)
btn_save = tk.Button(tab1, text="Save SQL \n Database", command=save_to_database)
btn_add_column = tk.Button(tab1, text="Add New \n Column", command=add_column)
btn_add_row = tk.Button(tab1, text="Add New \n Line", command=add_row)
btn_delete_row = tk.Button(tab1, text="Delete \n Line(s)", command=delete_selected_row)
btn_edit = tk.Button(tab1, text="Edit \n Line", command=lambda: edit_selected_row(tv, 'Personal_Data'))
btn_next_number = tk.Button(tab1, text="Show next \n Free Member ID", command=find_next_Member_ID)

btn_undo = tk.Button(tab1, text="Undo", command=undo)
btn_redo = tk.Button(tab1, text="Redo", command=redo)


buttons = [btn_load, btn_load_excel, btn_import, btn_save, btn_add_column, btn_add_row, btn_delete_row, btn_edit, btn_next_number, btn_undo, btn_redo]  # btn_load_excel added

for button in buttons:
    button.pack(side=tk.LEFT, padx=4, pady=5)




########################################################################################################
########################################################################################################
# Tab 4: Match
########################################################################################################


# Create two tabs
tab4 = ttk.Frame(notebook)
notebook.add(tab4, text='Match')

# Create a Treeview for the database table in Tab 1
tv4 = ttk.Treeview(tab4, columns=('Line-No', 'Surname', 'Forename', 'Member_ID', 'Branch', 'Match_1', 'Match_2', 'Match_3', 'Match_4', 'Match_5'), show='headings')

# Configure the columns with center alignment
# Configure the new column headers and their properties.
tv4.column('Line-No', width=40, anchor='center')
tv4.column('Surname', width=100, anchor='center')  # Adjust the widths as appropriate
tv4.column('Forename', width=100, anchor='center')
tv4.column('Member_ID', width=100, anchor='center')
tv4.column('Branch', width=100, anchor='center')
tv4.column('Match_1', width=100, anchor='center')  # New columns
tv4.column('Match_2', width=100, anchor='center')
tv4.column('Match_3', width=100, anchor='center')
tv4.column('Match_4', width=100, anchor='center')
tv4.column('Match_5', width=100, anchor='center')

# Configure the column headings with center alignment
tv4.heading('Line-No', text='Line No.', anchor='center')
tv4.heading('Surname', text='Surname', anchor='center')
tv4.heading('Forename', text='Forename', anchor='center')
tv4.heading('Member_ID', text='Member_ID', anchor='center')
tv4.heading('Branch', text='Branch', anchor='center')
tv4.heading('Match_1', text='Match_1', anchor='center')  # New column headings
tv4.heading('Match_2', text='Match_2', anchor='center')
tv4.heading('Match_3', text='Match_3', anchor='center')
tv4.heading('Match_4', text='Match_4', anchor='center')
tv4.heading('Match_5', text='Match_5', anchor='center')

tv4.pack(expand=True, fill='both', padx=10, pady=10)

tv4.bind('<Double-1>', lambda e: edit_entry(tv4, 'Match', tv4.identify_row(e.y)))








# # Bind the right-click event to the Treeview
# tv.bind("<Button-2>", right_click_menu)  # '<Button-3>' is the right-click event on Windows and Unix, use '<Button-2>' on macOS


# ########################
# # Add the buttons

# Initialize the buttons outside of the function, so they are created only once
# Make sure these variables are defined before the `tab_changed` function
# btn_load = tk.Button(tab4, text="Load \n Database", command=load_database)
# btn_import = tk.Button(tab4, text="Import Contacts \n from CSV", command=import_contacts)
# btn_save = tk.Button(tab4, text="Save \n Database", command=save_to_database)
# btn_add_column = tk.Button(tab4, text="Add \n Column", command=add_column)
# btn_add_row = tk.Button(tab4, text="Add New \n Line", command=add_row)
# btn_delete_row = tk.Button(tab4, text="Delete \n Line(s)", command=delete_selected_row)
btn4_edit = tk.Button(tab4, text="Edit \n Line", command=lambda: edit_selected_row(tv4, 'Match'))

# btn_load_excel = tk.Button(tab4, text="Load \n Excel File", command=load_excel_file)
# btn_next_number = tk.Button(tab4, text="Show next free \n Member ID", command=find_next_Member_ID)

# btn_undo = tk.Button(tab4, text="Undo", command=undo)
# btn_redo = tk.Button(tab4, text="Redo", command=redo)


buttons = [btn4_edit]  # btn_load_excel added

for button in buttons:
    button.pack(side=tk.LEFT, padx=4, pady=5)




########################################################################################################
########################################################################################################
# Tab 7: Manual
########################################################################################################

tab7 = ttk.Frame(notebook)
notebook.add(tab7, text='Manual')

# Bind the tab change event to the tab_changed function
notebook.bind("<<NotebookTabChanged>>", tab_changed)





root.mainloop()
