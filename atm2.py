import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import atm_email as e
import barcode
import otp
import getpass
from datetime import datetime
import matplotlib.pyplot as plt
import unique_id
import admin_control
import profile_2

# Connect to SQLite database
conn = sqlite3.connect('atm_database.db')
cursor = conn.cursor()

#printing the passbook
def display_transaction_table(uID):
    # Fetch data from user's transaction table
    table_name = f'{uID}_transactions'
    cursor.execute(f'''
        SELECT balance, date
        FROM {table_name}
    ''')
    data = cursor.fetchall()

    # Create a GUI window
    window = tk.Tk()
    window.title(f'Transaction Table for User ID: {uID}')
    window.geometry("1200x600")
    # Create a treeview widget for the table
    tree = ttk.Treeview(window)
    tree["columns"] = ("Balance", "Date")
    tree.heading("#0", text="Index")
    tree.heading("Balance", text="Balance", anchor="center")  # Center align the Balance column
    tree.heading("Date", text="Date", anchor="center")  # Center align the Date column

    # Set anchor attribute for each column
    for col in tree["columns"]:
        tree.column(col, anchor="center")
    # Set the width of the index column to make it appear centered
    tree.column("#0", width=50, anchor="center")
    # Insert data into the treeview
    for i, (balance, date) in enumerate(data, 1):
        tree.insert("", i, text=str(i), values=(balance, date))

    # Pack the treeview
    tree.pack(expand=True, fill="both")

    # Start the GUI event loop
    window.mainloop()

#printing the transaction analysis
def plot_transaction_map(uID):
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

    # Plot the data
    plt.plot( dates,balances, marker='o')
    plt.title(f'Transaction Map for User ID: {uID}')
    plt.xlabel('Date')
    plt.ylabel('Balance')
    plt.show()

# Function to get total ATM balance from the database
def total_atm_balance():
    cursor.execute('SELECT SUM(note * balance) FROM atm_balance')
    result = cursor.fetchone()[0]
    conn.commit()
    return float(result) if result is not None else 0.0
#inserting new data in the user transaction
def insert_transaction(uID, balance):
    table_name = f'{uID}_transactions'
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f'''
        INSERT INTO {table_name} (balance, date)
        VALUES (?, ?)
    ''', (balance, date))
    conn.commit()
    print(f'Transaction recorded for user ID: {uID}')

# Function to get user balance from the database
def balance(uID):
    cursor.execute('SELECT balance FROM user_details WHERE user_id = ?', (uID,))
    result = cursor.fetchone()
    if result:
        print("Your current balance:", result[0])
        return float(result[0])
    else:
        print("User not found.")
        return 0

# Function to send login alert email
def login_alert(uID):
    cursor.execute('SELECT email FROM user_details WHERE user_id = ?', (uID,))
    result = cursor.fetchone()
    if result:
        e.send_email(result[0], "Alert", "Someone accessed your ATM ID")

# Function to send password change OTP email
def pass_change_otp(uID):
    c = 0
    while c < 3:
        otp_s = otp.generate_otp()
        cursor.execute('SELECT email FROM user_details WHERE user_id = ?', (uID,))
        result = cursor.fetchone()
        if result:
            e.send_email(result[0], "Password change !!", f"OTP for changing user ID password: {otp_s}")
            conn.commit()
            otp_r = input("Enter the OTP: ")
            if otp_r == otp_s:
                print("OTP verification successful!")
                return 1
            else:
                print("Wrong OTP !!")
                if c < 2:
                    choice = input("Type 'yes' to resend OTP or 'end' to return: ")
                    if choice == 'end':
                        return 0
        c += 1
    if c == 3:
        cursor.execute('UPDATE user_details SET acc_status = 0 WHERE user_id = ?', (uID,))
        print("Your account is blocked. Please contact the admin!!")
        conn.commit()
    return 0

# Function to send low amount notification email
def low_amount_notification():
    cursor.execute('SELECT email FROM user_details WHERE user_id = "adm"')
    result = cursor.fetchone()
    if result:
        e.send_email(result[0], "Alert", "Low amount in the ATM!!")

# Function to send amount overload notification email
def amount_overload_notification():
    cursor.execute('SELECT email FROM user_details WHERE user_id = "adm"')
    result = cursor.fetchone()
    if result:
        e.send_email(result[0], "Alert", "ATM overload!!")

# Function to send ATM closed notification email
def atm_closed_notification(reason):
    cursor.execute('SELECT email FROM user_details WHERE user_id = "adm"')
    result = cursor.fetchone()
    if result:
        if reason == "overload":
            e.send_email(result[0], "Alert", "ATM shutdown due to overload!!")
        elif reason == "underflow":
            e.send_email(result[0], "Alert", "ATM shutdown due to less money!!")

# Function to check conditions after withdrawal
def after_withdrawal_check(uID):
    if total_atm_balance() <= 113000:
        low_amount_notification()
        return 1
    if total_atm_balance() < 56500:
        atm_closed_notification("underflow")
        print("Logging out.....\n")
        print("ATM has no money :-(")
        return 0
    notes = [100, 200, 500]
    for i in notes:
        cursor.execute('SELECT balance, min_requirement_for_operation FROM atm_balance WHERE note = ?', (i,))
        result = cursor.fetchone()
        if result and result[0] < result[1]:
            atm_closed_notification("underflow")
            print("Logging out.....\n")
            print("ATM has no money !!")
            return 0
    return 1

# Function to check conditions after deposit
def after_deposit_check(uID):
    if total_atm_balance() >= 300000 and total_atm_balance() < 400000:
        amount_overload_notification()
        return 1
    elif total_atm_balance() >= 400000:
        # Max capacity of ATM is 5 lakh
        # Max amount a user can deposit is 1 lakh
        # The ATM is closed if after any deposit the amount reaches 4 lakh or above
        atm_closed_notification("overload")
        print("Logging out....\n")
        print("ATM is full !!")
        return 0
    return 1

#deposit function
def deno_to_deposit_notes(uID, max_deposit):
    denominations = [100, 200, 500]
    amt = 0

    def on_submit():
        nonlocal amt
        for i, entry in enumerate(entries):
            count = int(entry.get())  # count of the number of notes of index i of denominations
            if count < 0:
                count = 0
            if (amt + count * denominations[i]) > max_deposit:
                messagebox.showinfo("Alert!", f"\nThe number of notes for {denominations[i]} exceeds the maximum limit for deposit.")
                deno_window.after(100, deno_window.destroy)
                return int(amt)
            else:
                amt += count * denominations[i]
                cursor.execute('''
                    UPDATE user_details
                    SET balance = balance + ?
                    WHERE user_id = ?
                ''', (count * denominations[i], uID))

                cursor.execute('''
                    UPDATE atm_balance
                    SET balance = balance + ?
                    WHERE note = ?
                ''', (count, denominations[i]))

        total_amount_label.config(text=f"Total amount: {amt}")
        conn.commit()
        deno_window.after(1000, deno_window.destroy)

    # Create the Tkinter window
    deno_window = tk.Tk()
    deno_window.title("Denomination Section")
    deno_window.geometry("1200x600")  # Increased window size

    entries = []
    # Create and pack the components in the window
    tk.Label(deno_window, text="Enter the number of specified notes:", pady=10, font=("Arial", 24)).pack(pady=40)

    for denom in denominations:
        entry_frame = tk.Frame(deno_window)
        entry_frame.pack(pady=10)
        tk.Label(entry_frame, text=f"{denom}:", padx=20, font=("Arial", 18)).pack(side="left")
        entry = tk.Entry(entry_frame, width=5, font=("Arial", 18))
        entry.pack(side="left", padx=5)
        entries.append(entry)

    tk.Button(deno_window, text="Submit", command=on_submit, pady=5, font=("Arial", 16)).pack(pady=40)

    total_amount_label = tk.Label(deno_window, text="", pady=10, font=("Arial", 12))
    total_amount_label.pack()

    deno_window.mainloop()
    return int(amt)

# Deposit function modified to use SQLite database
def deposit(uID):
    # Taking the amount to be deposited
    max_deposit = 100000
    if uID == "adm":
        max_deposit = 300000
    print("Deposit section")
    amt = deno_to_deposit_notes(uID, max_deposit)

    # Checking for max deposit limit
    #cursor.execute('UPDATE user_details SET balance = balance + ? WHERE user_id = ?', (amt, uID))
    print(f'''\tAmount {amt} deposited successfully into your account''')
    print('''\n\t"We're here to safeguard the fruits of your life's hard work and achievements."
\tSo stay tension-free :-))
''')
    conn.commit()

#withdrawal section
def deno_to_getspecific_notes(uID):
    denominations = [100, 200, 500]
    amt = 0

    def on_submit():
        nonlocal amt
        for i, entry in enumerate(entries):
            count = int(entry.get())  # count of a no of notes of index i of denominations
            cursor.execute('SELECT max_withdrawal_limit FROM atm_balance WHERE note = ?', (denominations[i],))
            max_limit = cursor.fetchone()[0]
            if count > max_limit:
                messagebox.showinfo("Alert!", f"Transaction failed\nThe number of notes for {denominations[i]} and the bigger notes exceeds the maximum limit.")
                deno_window.after(100, deno_window.destroy)
                return int(amt)  # Return instead of calling deno() recursively
            else:
                if count < 0:
                    count = 0
                cursor.execute('SELECT balance FROM user_details WHERE user_id = ?', (uID,))
                user_balance = cursor.fetchone()[0]
                if (amt + count * denominations[i] > user_balance):
                    messagebox.showinfo("Alert!", f"Transaction failed for {denominations[i]} and above\nThe total amount exceeds your account balance.")
                    deno_window.after(100, deno_window.destroy)
                    return int(amt)  # Return instead of calling deno() recursively
                else:
                    amt += count * denominations[i]
                    cursor.execute('UPDATE atm_balance SET balance = balance - ? WHERE note = ?', (count, denominations[i]))

        total_amount_label.config(text=f"Total amount: {amt}")
        conn.commit()
        deno_window.after(1000, deno_window.destroy)

    # Create the Tkinter window
    deno_window = tk.Tk()
    deno_window.title("Denomination Section")
    deno_window.geometry("1200x600")  # Increased window size

    entries = []
    # Create and pack the components in the window
    tk.Label(deno_window, text="Enter the number of specified notes:", pady=10, font=("Arial", 24)).pack(pady=40)

    for denom in denominations:
        entry_frame = tk.Frame(deno_window)
        entry_frame.pack(pady=10)
        tk.Label(entry_frame, text=f"{denom}:", padx=20, font=("Arial", 18)).pack(side="left")
        entry = tk.Entry(entry_frame, width=5, font=("Arial", 18))
        entry.pack(side="left", padx=5)
        entries.append(entry)

    tk.Button(deno_window, text="Submit", command=on_submit, pady=5, font=("Arial", 16)).pack(pady=40)

    total_amount_label = tk.Label(deno_window, text="", pady=10, font=("Arial", 12))
    total_amount_label.pack()

    deno_window.mainloop()
    return int(amt)
# Function to fetch withdrawal from ATM
def fetching_withdrawal_atm(note, amt):
    count = amt // note
    amt = amt % note
    cursor.execute('UPDATE atm_balance SET balance = balance - ? WHERE note = ?', (count, note))
    conn.commit()
    print(f"no of {note} noted withdrawn :",count)
    return amt
# Withdrawal function modified to use SQLite database
def withdrawal(uID):
    print('Withdrawal section')
    choice = int(input('''
1. Get particular notes of your choice
2. Direct [Enter the amount and let the system decide the type of notes]

Enter your choice: '''))

    # getting the amount and fetching it from atm_balance
    amt = 0
    if choice == 2:
        amt = float(input("Enter the amount to be withdrawn: "))
        cursor.execute('SELECT balance FROM user_details WHERE user_id = ?', (uID,))
        user_balance = cursor.fetchone()[0]
        if user_balance <amt:
            print("\nSorry! Transaction failed due to insufficient balance")
            print("Don't be sad :-)\n")
            return
        else:
            given_amt = amt
            notes = [500, 200, 100]
            for note in notes:
                if amt >= note:
                    if note==100:
                        amt = fetching_withdrawal_atm(note, amt)
                    else:
                        amt = fetching_withdrawal_atm(note, amt - note) + note
            if amt != 0:
                print("Only the valid amount is being withdrawn")
            amt = given_amt - amt

    elif choice == 1:
        amt = deno_to_getspecific_notes(uID)

    else:
        print("Invalid choice!")
        return

    # Cutting the amount from the user account
    cursor.execute('UPDATE user_details SET balance = balance - ? WHERE user_id = ?', (amt, uID))
    print("Amount being withdrawn:", amt)
    print('''\nWithdrawal successful''')
    print('''\n\t"Each withdrawal is a deduction from your bank balance, not from the boundless opportunities that life offers."\n''')
    conn.commit()

#menu
# Function to check if user account is active
def is_account_active(uID):
    cursor.execute('SELECT acc_status FROM user_details WHERE user_id = ?', (uID,))
    acc_status = cursor.fetchone()[0]
    return bool(acc_status)

# Function to check user password
def check_user_password(uID, password):
    cursor.execute('SELECT password FROM user_details WHERE user_id = ?', (uID,))
    stored_password = cursor.fetchone()[0]
    return password == stored_password

# Function to update user password
def update_user_password(uID, new_password):
    cursor.execute('UPDATE user_details SET password = ? WHERE user_id = ?', (new_password, uID))
    conn.commit()

# taking new password as input
def new_password():
            new_pass = getpass.getpass("Enter new password: ")
            confirm_pass = getpass.getpass("Confirm new password: ")
            while new_pass != confirm_pass:
                print("Both passwords are not the same!")
                new_pass = getpass.getpass("Enter new password: ")
                confirm_pass = getpass.getpass("Confirm new password: ")
            return new_pass
def menu(uID):
    r=True
    print("""Please choose an Option from below : 
1. Bank Balance
2. Deposit 
3. Withdrawal
4. Change password                               
5. Query 
6. Graphical Transaction analysis 
7. Tabular Transaction data
8. user profile
9. Logout        
""")
    choice = int(input("Enter your choice no: "))
    if choice == 1:
        balance(uID)
        print('''\n\t"Your bank balance may reflect financial stability,\n\tbut the richness of life is measured in happiness and well-being.\n\tDon't just check your balance; check your heart, too."\n\n''')
        menu(uID)
    elif choice == 2:
        deposit(uID)
        insert_transaction(uID,balance(uID))
        
        cursor.execute('UPDATE user_details SET balance = ? WHERE user_id = ?', (total_atm_balance(), 'adm'))
        if after_deposit_check(uID):
            menu(uID)
        else:
            r=False
    elif choice == 3:
        withdrawal(uID)
        insert_transaction(uID,balance(uID))
        cursor.execute('UPDATE user_details SET balance = ? WHERE user_id = ?', (total_atm_balance(), 'adm'))
        if after_withdrawal_check(uID):
            menu(uID)
        else:
            r=False
    elif choice == 4:
        if pass_change_otp(uID):
            new_pass=new_password()
            update_user_password(uID, new_pass)
            
            print("Password change successful !!\nLogging out....")
        else:
            
            print("Password change unsuccessful !!\nLogging out....")
    elif choice == 5:
        barcode.open_image()
        menu(uID)
    elif choice==6:
        plot_transaction_map(uID)
        menu(uID)
    elif choice==7:
        display_transaction_table(uID)
        menu(uID)
    elif choice==8:
        profile_2.run_atm_gui(uID)
        menu(uID)
    else:
        print("""
        Thanks for logging in
        Have a great day :-) 
        Logging out....       
        """)
    return r


def admin():
    print("ONLY ADMIN CAN LOGIN !!")
    login('adm')
def login(uID):
    # user login
    # check for the validity of the user
    if is_account_active(uID):
        login_alert(uID)  # sending login alert
        c = 0
        while c < 3:
            paskey = getpass.getpass("Enter your password: ")  # getting password
            if check_user_password(uID, paskey):
                cursor.execute('SELECT name FROM user_details WHERE user_id = ?', (uID,))
                user_name = cursor.fetchone()[0]
                print("\nWelcome", user_name)
                if not(menu(uID)):
                    admin()  # atm shutdown
                break
            c += 1
            print("Oops! You Entered a wrong password\nNo of attempts left:", 3 - c, "\n")
        if c == 3:  # blocking the account for wrong password
            cursor.execute('UPDATE user_details SET acc_status = ? WHERE user_id = ?', (False, uID))
            print("Your user ID is blocked.\nContact the admin/branch for help")
            conn.commit()

        main_menu()  # user logged out moving back to main page
    else:
        print("Oops! You Entered an invalid UserID or the account is blocked.")
        main_menu()

#creating new account 
def new_acc_otp(eID):
    c = 0
    while c < 3:
        otp_s = otp.generate_otp()
        e.send_email(eID, "New Account creation !!", f"OTP for confirmation of your new account at our bank: {otp_s}")
        otp_r = input("Enter the OTP: ")
        if otp_r == otp_s:
            print("OTP verification successful!")
            return 1
        else:
            print("Wrong OTP !!")
            if c < 2:
                choice = input("Type 'yes' to resend OTP or 'end' to return: ")
                if choice == 'end':
                    return 0
        c += 1
    if c == 3:
        print("Account creation failed !!\nWe are sorry")
    return 0
def new_acc_enotification(uID):
    cursor.execute('SELECT email FROM user_details WHERE user_id = ?', (uID,))
    result = cursor.fetchone()
    if result:
        e.send_email(result[0], "New account Created ", f"Your new account is created successfully at our bank\nYour user ID is {uID}")
def check_phone_number_exists(phone_number):
    # Execute SELECT query to check if phone number exists
    cursor.execute("SELECT user_id FROM user_details WHERE phone_no = ?;", (phone_number,))
    
    # Fetch the result
    result = cursor.fetchone()
    
    # Check if the result is not None (phone number exists)
    if result is not None:
        return False
    else:
        return True
def create_new_user():
    print("Welcome to our bank ")
    name=input("Enter your name: ")
    eID=input("Enter your email: ")
    phn=input("Enter phone no : ")
    if check_phone_number_exists(phn):
        #sending otp 
        if new_acc_otp(eID):
            uID=unique_id.generate_unique_code(phn)
            print("Your unique user id :",uID)
            #creating pass
            pas=new_password()
            # Insert a new row into the user_details table
            cursor.execute('''
            INSERT INTO user_details (user_id, name, email, password, phone_no, balance, acc_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (uID, name, eID, pas, phn,0.0,1))
            conn.commit()
            # create the user passbook table
            # Create the table
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {uID}_transactions (
            balance INTEGER NOT NULL,
            date TEXT NOT NULL
            );
            ''')
            conn.commit()
            #taking safety deposit
            print("You need to deposit  a minimum amount of 1500 rupees as safety deposit.")
            while(balance(uID)<float(1500)):
                deposit(uID)
                insert_transaction(uID,balance(uID))
            print("Your account is created sucessfully !!\n\t We are pleased to have you as our new family member :-)\n")
            new_acc_enotification(uID)

        else:
            main_menu()
    else:
        print("An account already exists with the given phone no\n")

#to check for valid user   
def check_user_id_exists(user_id):
    # Execute SELECT query to check if user ID exists
    cursor.execute("SELECT user_id FROM user_details WHERE user_id = ?;", (user_id,))
    
    # Fetch the result
    result = cursor.fetchone()
    
    # Check if the result is not None (user ID exists)
    if result is not None:
        return True
    else:
        return False   
'''
def login_alert_otp(uID):
    c = 0
    while c < 3:
        otp_s = otp.generate_otp()
        cursor.execute('SELECT email FROM user_details WHERE user_id = ?', (uID,))
        result = cursor.fetchone()
        if result:
            e.send_email(result[0], "login otp !!", f"OTP for login into user account: {otp_s}")
            otp_r = input("Enter the OTP: ")
            if otp_r == otp_s:
                print("OTP verification successful!")
                return 1
            else:
                print("Wrong OTP !!")
                if c < 2:
                    choice = input("Type 'yes' to resend OTP or 'end' to return: ")
                    if choice == 'end':
                        return 0
        c += 1
    
    return 0
'''
from tkinter import simpledialog, messagebox
def login_alert_otp(uID):
    c = 0
    while c < 3:
        otp_s = otp.generate_otp()
        cursor.execute('SELECT email FROM user_details WHERE user_id = ?', (uID,))
        result = cursor.fetchone()
        if result:
            e.send_email(result[0], "Login OTP !!", f"OTP for login into user account: {otp_s}")
            
            # Use Tkinter for OTP input
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            otp_r = simpledialog.askstring("OTP Verification", "Enter the OTP:")
            root.destroy()  # Close the Tkinter window
            
            if otp_r == otp_s:
                print("OTP verification successful!")
                return 1
            else:
                print("Wrong OTP !!")
                if c < 2:
                    choice = input("Type 'yes' to resend OTP or 'end' to return: ")
                    if choice == 'end':
                        return 0
        c += 1
    return 0

def main_menu():
    def login_menu():
        root.destroy()
        user_id = simpledialog.askstring("Login", "Enter your user id:")
        if check_user_id_exists(user_id):
            if login_alert_otp(user_id):
                login(user_id)
                
            else:
                messagebox.showinfo("Error", "OTP verification failed !!")
        else:
            messagebox.showinfo("Error", "Invalid user id")
        main_menu()

    def create_user_menu():
        root.destroy()
        create_new_user()
        main_menu()
        
    def admin_menu():
        root.destroy()
        login_alert("adm")
        if login_alert_otp("adm"):
            password = simpledialog.askstring("Admin Login", "Enter your password:")
            if check_user_password("adm", password):
                admin_control.menu_main()
            else:
                messagebox.showinfo("Error", "Wrong password !!")
        else:
            messagebox.showinfo("Error", "OTP verification failed !!")
        main_menu()
 
    root = tk.Tk()
    root.title("Main Menu")
    root.geometry("400x300")  # Set the window size
    root.configure(bg='blue')  # Set the background color

    login_button = tk.Button(root, text="Login", command=login_menu)
    login_button.pack(pady=10)

    create_user_button = tk.Button(root, text="Create New User", command=create_user_menu)
    create_user_button.pack(pady=10)

    admin_button = tk.Button(root, text="Admin Section", command=admin_menu)
    admin_button.pack(pady=10)
    
    root.mainloop()

main_menu()

conn.commit()
conn.close()


