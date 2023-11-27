import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import music

def unblock(uID, conn, cursor):
    cursor.execute('UPDATE user_details SET acc_status = ? WHERE user_id = ?', (1, uID))
    conn.commit()
    messagebox.showinfo("Success", f"User with ID {uID} unblocked successfully!")

def delete_user(uID, conn, cursor):
    cursor.execute('DELETE FROM user_details WHERE user_id = ?', (uID,))
    conn.commit()
    messagebox.showinfo("Success", f"User with ID {uID} deleted successfully!")

def see_user_details(uID, conn, cursor):
    try:
        cursor.execute("SELECT * FROM user_details WHERE user_id = ?", (uID,))
        user_data = cursor.fetchone()

        root = tk.Tk()
        root.title("User Details")
        root.geometry("1400x700")
        root.configure(bg="lightblue")

        if user_data is None:
            label = tk.Label(root, text=f"No user found with user_id: {uID}", bg="lightblue")
            label.pack(pady=20)
        else:
            label = tk.Label(root, text="User Details:", font=("Helvetica", 12), bg="lightblue")
            label.pack(pady=10)

            for column_name, value in zip(cursor.description, user_data):
                if column_name[0] != 'password':
                    if column_name[0]=='acc_status':
                              value=bool(value)
                    user_label = tk.Label(root, text=f"{column_name[0]}: {value}", bg="lightblue")
                    user_label.pack()

        conn.commit()

        def on_close():
            root.destroy()

        close_button = tk.Button(root, text="Close", command=on_close, bg="white")
        close_button.pack(pady=10)

        root.mainloop()

    except Exception as e:
        print(f"Error: {e}")

import tkinter as tk
from tkinter import ttk

def menu_main():
    # Connect to the SQLite database
    conn = sqlite3.connect('atm_database.db')
    cursor = conn.cursor()

    # Tkinter window setup
    root = tk.Tk()
    root.title("ATM Menu")
    root.geometry("1400x700")
    root.configure(bg="violet")

    label = tk.Label(root, text="ATM Menu", font=("Helvetica", 16), bg="violet")
    label.pack(pady=10)

    # Dropdown menu for options
    options_label = tk.Label(root, text="Select an option:", bg="violet")
    options_label.pack(pady=5)

    options = ["See user details", "Unblock user", "Delete user", "Logout"]
    selected_option = tk.StringVar(value=options[0])

    option_menu = ttk.Combobox(root, textvariable=selected_option, values=options, state="readonly")
    option_menu.pack(pady=5)

    uid_label = tk.Label(root, text="Enter the user ID:", bg="violet")
    uid_label.pack()

    uid_entry = tk.Entry(root)
    uid_entry.pack(pady=5)

    def on_submit():
        selected_choice = selected_option.get()
        uID = uid_entry.get()
        root.destroy()
        if selected_choice == "See user details":
            see_user_details(uID, conn, cursor)
            menu_main()
        elif selected_choice == "Unblock user":
            unblock(uID, conn, cursor)
            menu_main()
        elif selected_choice == "Delete user":
            delete_user(uID, conn, cursor)
            menu_main()
        elif selected_choice == "Logout":
            pass
        music.play_sound("sucess.mp3")
        conn.commit()
        
    # Close the Tkinter window after processing
    submit_button = tk.Button(root, text="Submit", command=on_submit, bg="white")
    submit_button.pack(pady=10)
    
    root.mainloop()
    conn.close()
