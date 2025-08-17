import sqlite3
import bcrypt
import tkinter as tk
from tkinter import messagebox, simpledialog
import smtplib
from email.message import EmailMessage
import random
import subprocess
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import os
import sys

EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASS = os.getenv("APP_PASSWORD")

#if not EMAIL or not APP_PASS:
#    messagebox.showerror("Env Error", "Missing email credentials. Please check your .env file.")
#    exit()  # Or use root.quit() if Tkinter is already initialized

# === Database Setup ===
DB_PATH = "user_login.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email_address TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    verified INTEGER DEFAULT 0,
    registered_at TEXT
)
""")
conn.commit()

# === Send Email Verification ===
def send_verification_email(to_address, code):
    msg = EmailMessage()
    msg.set_content(f"Welcome to MindfullyMosaic!\n\nYour 6-digit verification code is:\n\n{code}")
    msg["Subject"] = "Your Verification Code"
    msg["From"] = "your_email@gmail.com"
    msg["To"] = to_address

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            #smtp.login("EMAIL_ADDRESS", "APP_PASSWORD")  # Replace with your credentials
            smtp.login(EMAIL, APP_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        messagebox.showerror("Email Error", str(e))
        return False

# === Launch Main Suite ===
def launch_suite():
    try:
        #subprocess.Popen(["python", "Personal Finance and Productivity Suite.py"])
        suite_path = os.path.join(os.path.dirname(sys.executable), "Personal Finance and Productivity Suite.exe")
        subprocess.Popen([suite_path])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Launch Failed", str(e))

# === Registration ===
def register():
    name = full_name.get().strip()
    email = email_address.get().strip()
    password = password_entry.get().strip()

    if not name or not email or not password:
        messagebox.showerror("Missing Info", "All fields are required.")
        return

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cursor.execute("SELECT * FROM users WHERE email_address = ?", (email,))
    existing = cursor.fetchone()

    if existing:
        messagebox.showerror("Already Registered", "This email is already registered.")
        return

    code = str(random.randint(100000, 999999))
    if not send_verification_email(email, code):
        return

    entered_code = simpledialog.askstring("Verify Email", f"Check your inbox.\nEnter the 6-digit code sent to {email}:")
    if entered_code != code:
        messagebox.showerror("Invalid Code", "Verification failed.")
        return

    cursor.execute("""
        INSERT INTO users (full_name, email_address, hashed_password, verified, registered_at)
        VALUES (?, ?, ?, 1, ?)
    """, (name, email, hashed.decode(), datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    messagebox.showinfo("Success", "Registration complete!")
    launch_suite()

# === Login ===
def login():
    email = email_address.get().strip()
    password = password_entry.get().strip()

    cursor.execute("SELECT hashed_password, verified FROM users WHERE email_address = ?", (email,))
    record = cursor.fetchone()

    if not record:
        messagebox.showerror("Error", "User not found.")
        return
    stored_hash, is_verified = record

    if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
        messagebox.showerror("Error", "Incorrect password.")
        return
    if not is_verified:
        messagebox.showerror("Not Verified", "User not verified.")
        return

    # ✅ Save session
    with open("session_user.txt", "w") as f:
        f.write(email)

    messagebox.showinfo("Welcome", f"Login successful for {email}")
    launch_suite()

# === Test Email Delivery ===
def test_email_delivery():
    email = email_address.get().strip()
    if not email:
        messagebox.showerror("Missing Info", "Enter an email address first.")
        return

    test_code = str(random.randint(100000, 999999))
    success = send_verification_email(email, test_code)
    if success:
        messagebox.showinfo("Email Sent", f"A test message was sent to {email}.\nCheck your inbox.")
    else:
        messagebox.showerror("Failed", "Could not send test email.")

# === GUI Setup ===
root = tk.Tk()
root.title("MindfullyMosaic Launcher")
root.geometry("420x330")

if not EMAIL or not APP_PASS:
    messagebox.showerror("Env Error", "Missing email credentials. Please check your .env file.")
    root.quit()

tk.Label(root, text="Welcome to MindfullyMosaic", font=("Arial", 14, "bold")).pack(pady=10)

tk.Label(root, text="Full Name (to register)").pack()
full_name = tk.StringVar()
tk.Entry(root, textvariable=full_name, width=40).pack()

tk.Label(root, text="Email Address (to register & to login)").pack()
email_address = tk.StringVar()
tk.Entry(root, textvariable=email_address, width=40).pack()

tk.Label(root, text="Password (to register & to login)").pack()
password_entry = tk.StringVar()
tk.Entry(root, textvariable=password_entry, show="*", width=40).pack()

tk.Button(root, text="Register", command=register).pack(pady=5)
tk.Button(root, text="Login", command=login).pack(pady=5)
tk.Button(root, text="Test Email Delivery", command=test_email_delivery).pack(pady=5)

root.mainloop()
