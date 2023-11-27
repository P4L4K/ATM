from tkinter import *
from PIL import ImageTk, Image
from tkinter import ttk, font
import sqlite3
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def run_atm_gui(uID):
    def show_user_info(*args):
        if len(args) >= 4:
            name, dob, mobile, email, *_ = args
            custom_font = font.Font(family="Helvetica", size=24)
            info_label.config(text=f"User id: {name}\nName: {dob}\nPassword: {mobile}\nBalance: {email}", font=custom_font)
        else:
            print("Invalid number of arguments for show_user_info")

    def on_image_click(event):
        user_data = get_user_details(uID)
        if user_data:
            show_user_info(*user_data)

    def get_user_details(uID):
        try:
            # Connect to SQLite database
            conn = sqlite3.connect('atm_database.db')
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM user_details WHERE user_id = ?", (uID,))
            user_data = cursor.fetchone()
            conn.commit()
            # Close the connection
            conn.close()
            return user_data
        except Exception as e:
            print(f"Error fetching user details: {e}")
            return None

    def display_transaction_data(passbook_tree, uID):
        try:
            # Connect to SQLite database
            conn = sqlite3.connect('atm_database.db')
            cursor = conn.cursor()

            # Fetch data from user's transaction table
            table_name = f'{uID}_transactions'
            cursor.execute(f'''
                SELECT balance, date
                FROM {table_name}
            ''')
            data = cursor.fetchall()

            if not data:
                print(f'No transactions found for user ID: {uID}')
                return

            # Unpack data into separate lists
            balances, dates = zip(*data)

            # Convert dates to datetime objects
            dates = [datetime.strptime(date, "%Y-%m-%d %H:%M:%S") for date in dates]

            # Clear existing data in the passbook_tree
            passbook_tree.delete(*passbook_tree.get_children())

            # Insert new data into the passbook_tree
            for i, (balance, date) in enumerate(data, 1):
                passbook_tree.insert("", i, text=str(i), values=(balance, date))

            # Plot the data
            fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
            ax.plot(dates, balances, marker='o')
            ax.set_title(f'Transaction Map for User ID: {uID}')
            ax.set_ylabel('Balance')
            ax.set_xlabel('Date')

            # Embed the plot in the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=root)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.place(x=970, y=390)
            canvas.draw()
        except Exception as e:
            print(f"Error displaying transaction data: {e}")
        finally:
            # Close the connection
            conn.close()

    # Create a Tkinter window
    root = Tk()
    root.title('ATM')
    root.geometry("1800x1000")
    root.iconbitmap('D:\\ATM')
    root.configure(bg='#87CEEB')  # SkyBlue color

    # Load user photo and display
    user_photo = ImageTk.PhotoImage(Image.open("userphoto.jpg"))
    user_photo_label = Label(image=user_photo, bg='#87CEEB')  # Background color
    user_photo_label.place(x=-70, y=-100)

    user_photo_label.bind("<Button-1>", on_image_click)

    # Load ATM barcode image and display
    barcode_img = ImageTk.PhotoImage(Image.open("atmbarcode.jpg"))
    barcode_label = Label(root, image=barcode_img, bg='#87CEEB')  # Background color
    barcode_label.place(x=1000, y=-40)

    # Display user information in a label
    custom_font_info = font.Font(family="Helvetica", size=20)
    info_label = Label(root, text="", justify=LEFT, font=custom_font_info, bg='#87CEEB')  # Background color
    info_label.place(x=500, y=50)

    # Create a Treeview for passbook display
    passbook_tree = ttk.Treeview(root, style='Custom.Treeview')
    passbook_tree["columns"] = ("Balance", "Date")
    passbook_tree.heading("#0", text="Index")
    passbook_tree.heading("Balance", text="Balance", anchor="center")
    passbook_tree.heading("Date", text="Date", anchor="center")
    passbook_tree.column("#0", width=50, anchor="center")
    passbook_tree.place(x=500, y=250)

    # Styling for Treeview
    style = ttk.Style(root)
    style.configure('Custom.Treeview', background='#F0F0F0', fieldbackground='#F0F0F0')  # Background color

    # Add Exit Program button
    button_quit = Button(root, text="Exit Program", command=root.destroy, font=("Helvetica", 20), bg='#FF4500', fg='white')  # Background and foreground color
    button_quit.place(x=600, y=700)

   
    # Display transaction data in passbook_tree
    display_transaction_data(passbook_tree, uID)

    root.mainloop()


