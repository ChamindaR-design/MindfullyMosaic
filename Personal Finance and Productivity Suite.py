from tkcalendar import DateEntry
import tkinter as tk
from tkinter import simpledialog
import csv
from tkinter import ttk, messagebox
import pandas as pd
import pyttsx3
import sqlite3
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import timedelta
from datetime import datetime, date, timedelta
from tkcalendar import Calendar
import math

import webbrowser

import subprocess

def logout_and_launch():
    subprocess.Popen(["python", "launcher.exe"])
    root.destroy()

import traceback
import tkinter.messagebox as mb

bg_image = None # Global placeholder

def log_crash_info(exc):
    with open("error_report.txt", "a") as f:
        #f.write(f"\n\n--- {datetime.datetime.now()} ---\n")
        f.write(f"\n\n--- {datetime.now()} ---\n")
        f.write(traceback.format_exc())

try:
    # --- GUI Setup ---
    root = tk.Tk()
    root.title("MindfullyMosaic Personal Organiser")
    root.geometry("900x600")

    import os, sys
    db_path = os.path.join(os.path.dirname(sys.executable), "budget_data.db")
    conn = sqlite3.connect(db_path, isolation_level=None) # Autocommit mode
    cursor = conn.cursor()

    auth_conn = sqlite3.connect("user_login.db")
    auth_cursor = auth_conn.cursor()

    # Create tables if not exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expense_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS frequency_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT UNIQUE
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        category TEXT,
        frequency TEXT,
        amount REAL,
        date TEXT,
        notes TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budget_targets (
        type TEXT,
        category TEXT,
        frequency TEXT,
        year TEXT,
        annual_budget REAL,
        notes TEXT,
        PRIMARY KEY (type, category, frequency, year)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT NOT NULL,
        reminder_time TEXT,
        recurrence TEXT,
        is_completed INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payee TEXT NOT NULL,
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        reminder_time TEXT,
        recurrence TEXT,
        is_paid INTEGER DEFAULT 0,
        category TEXT
    )
    ''')
    #cursor.execute("ALTER TABLE tasks ADD COLUMN recurrence TEXT DEFAULT 'None'")
    #cursor.execute("ALTER TABLE tasks ADD COLUMN is_completed INTEGER DEFAULT 0")
    conn.commit()

    #try:
    #    cursor.execute("ALTER TABLE bills ADD COLUMN category TEXT DEFAULT 'General'")
    #except sqlite3.OperationalError:
    #    pass  # Column already exists

    # Seed defaults
    cursor.execute("SELECT COUNT(*) FROM expense_categories")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO expense_categories (name) VALUES (?)", [
            ("Rent",), ("Groceries",), ("Medical",), ("Transport",), ("Utilities",)
        ])
    cursor.execute("SELECT COUNT(*) FROM frequency_options")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO frequency_options (label) VALUES (?)", [
            ("One-off",), ("Weekly",), ("Monthly",), ("Annually",), ("Daily",), ("Biweekly",), ( "4-Weekly",), ("Quarterly",), ("Half-Yearly",)
        ])
    conn.commit()

    # === Frequency Conversion Factors ===
    frequency_multipliers = {
        "Daily": 365,
        "Weekly": 52,
        "Biweekly": 26,
        "4-Weekly": 13,
        "Monthly": 12,
        "Quarterly": 4,
        "Half-Yearly": 2,
        "Annually": 1,
        "One-off": 1
    }

    # Load values
    def get_categories():
        cursor.execute("SELECT name FROM expense_categories ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

    categories_list = get_categories() # Cache Categories on Startup

    def get_frequencies():
        cursor.execute("SELECT label FROM frequency_options ORDER BY label")
        return [row[0] for row in cursor.fetchall()]

    # === Safe Date Parser (for dd/mm/yyyy) ===
    def parse_date_safe(date_str):
        return datetime.strptime(date_str, "%d/%m/%Y").date()

    # App logic
    def refresh_dropdowns():
        new_categories = categories_list
        new_frequencies = get_frequencies()

        category_menu = category_option["menu"]
        category_menu.delete(0, "end")
        for item in new_categories:
            category_menu.add_command(label=item, command=tk._setit(category_var, item))

        frequency_menu = frequency_option["menu"]
        frequency_menu.delete(0, "end")
        for item in new_frequencies:
            frequency_menu.add_command(label=item, command=tk._setit(frequency_var, item))

    def add_category(name):
        try:
            cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (name.strip(),))
            conn.commit()
            refresh_dropdowns()
            messagebox.showinfo("Added", f"Category '{name}' added.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Exists", f"Category '{name}' already exists.")

    def delete_category(name):
        cursor.execute("DELETE FROM expense_categories WHERE name=?", (name.strip(),))
        conn.commit()
        refresh_dropdowns()
        messagebox.showinfo("Deleted", f"Category '{name}' deleted.")

    def add_frequency(label):
        try:
            cursor.execute("INSERT INTO frequency_options (label) VALUES (?)", (label.strip(),))
            conn.commit()
            refresh_dropdowns()
            messagebox.showinfo("Added", f"Frequency '{label}' added.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Exists", f"Frequency '{label}' already exists.")

    def delete_frequency(label):
        cursor.execute("DELETE FROM frequency_options WHERE label=?", (label.strip(),))
        conn.commit()
        refresh_dropdowns()
        messagebox.showinfo("Deleted", f"Frequency '{label}' deleted.")

    def add_entry():
        entry_type = type_var.get()
        category = category_var.get()
        frequency = frequency_var.get()
        date = date_var.get()
        notes = notes_var.get()
        try:
            amount = float(amount_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount must be a number.")
            return

        cursor.execute('''
            INSERT INTO ledger (type, category, frequency, amount, date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (entry_type, category, frequency, amount, date, notes))
        conn.commit()
        load_history()
        messagebox.showinfo("Added", f"{entry_type} of £{amount} added under {category}.")
        clear_inputs()

    def clear_inputs():
        type_var.set("Income")
        category_var.set(categories_list[0])
        frequency_var.set(get_frequencies()[0])
        amount_var.set("")
        date_var.set(datetime.today().strftime('%d/%m/%Y'))
        notes_var.set("")

    def speak_summary():
        df = pd.read_sql_query("SELECT * FROM ledger", conn)
        income_total = df[df["type"] == "Income"]["amount"].sum()
        expense_total = df[df["type"] == "Expense"]["amount"].sum()
        balance = income_total - expense_total
        engine.say(f"You've earned £{income_total:.2f}, spent £{expense_total:.2f}, and your balance is £{balance:.2f}.")
        engine.runAndWait()

    def load_history(apply_filters=False):
        # Clear existing rows
        for row in tree.get_children():
            tree.delete(row)

        query = "SELECT type, category, frequency, amount, date, notes FROM ledger WHERE 1=1"
        params = []

        if apply_filters:
            type_val = filter_type.get()
            cat_val = filter_category.get()
            start = filter_start.get().strip()
            end = filter_end.get().strip()

            # Convert dd/MM/yyyy to ISO format
            try:
                if start:
                    start = datetime.strptime(start, "%d/%m/%Y").strftime("%d/%m/%Y")
                if end:
                    end = datetime.strptime(end, "%d/%m/%Y").strftime("%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter dates as dd/MM/yyyy.")
                return

            if type_val != "All":
                query += " AND type = ?"
                params.append(type_val)
            if cat_val != "All":
                query += " AND category = ?"
                params.append(cat_val)
            if start:
                query += " AND date >= ?"
                params.append(start)
            if end:
                query += " AND date <= ?"
                params.append(end)

            try:
                cursor.execute(query, params)
                results = cursor.fetchall()
                for row in results:
                    row = list(row)

                    # Format date to dd/MM/yyyy for display
                    try:
                        if row[4]:
                            row[4] = datetime.strptime(row[4], "%d/%m/%Y").strftime("%d/%m/%Y")
                        else:
                            row[4] = "—"
                    except:
                        row[4] = "—"

                    # Format amount with £ and comma
                    try:
                        row[3] = f"£{float(row[3]):,.2f}"
                    except:
                        row[3] = "£0.00"

                    if row[5] is None:
                        row[5] = ""

                    tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Error Loading Data", str(e))

    def export_ledger(format="csv"):
        query = "SELECT type, category, frequency, amount, date, notes FROM ledger WHERE 1=1"
        params = []

        if filter_type.get() != "All":
            query += " AND type = ?"
            params.append(filter_type.get())
        if filter_category.get() != "All":
            query += " AND category = ?"
            params.append(filter_category.get())

        start = filter_start.get().strip()
        end = filter_end.get().strip()

        try:
            if start:
                start = datetime.strptime(start, "%d/%m/%Y").strftime("%d/%m/%Y")
                query += " AND date >= ?"
                params.append(start)
            if end:
                end = datetime.strptime(end, "%d/%m/%Y").strftime("%d/%m/%Y")
                query += " AND date <= ?"
                params.append(end)
        except ValueError:
            messagebox.showerror("Invalid Date", "Dates must be in dd/MM/yyyy format.")
            return

        try:
            df = pd.read_sql_query(query, conn, params=params)
            if df.empty:
                messagebox.showinfo("No Data", "No matching records to export.")
                return

            # Format date for export
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")

            filetypes = [("CSV Files", "*.csv")] if format == "csv" else [("Excel Files", "*.xlsx")]
            default_ext = ".csv" if format == "csv" else ".xlsx"
            file = filedialog.asksaveasfilename(defaultextension=default_ext, filetypes=filetypes)

            if file:
                if format == "csv":
                    df.to_csv(file, index=False)
                else:
                    df.to_excel(file, index=False)
                messagebox.showinfo("Export Successful", f"Ledger exported to:\n{file}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def draw_dashboard(frame):
        for widget in frame.winfo_children()[1:]:
            widget.destroy()  # Clear previous charts

        df = pd.read_sql_query("SELECT type, category, frequency, amount, date FROM ledger", conn)

        # Clean the data
        df = df.dropna(subset=["type", "category", "frequency", "amount"])
        df["frequency"] = df["frequency"].astype(str).str.strip()
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df = df.dropna(subset=["amount"])

        # Optional: enforce frequency order for clean plotting
        freq_order = ["One-off", "Weekly", "Monthly", "Annually"]
        df["frequency"] = pd.Categorical(df["frequency"], categories=freq_order, ordered=True)

        if df.empty:
            tk.Label(frame, text="No data to display.", fg="red").pack()
            return

        income_total = df[df["type"] == "Income"]["amount"].sum()
        expense_total = df[df["type"] == "Expense"]["amount"].sum()
        balance = income_total - expense_total

        # Summary
        summary = f"Total Income: £{income_total:,.2f} | Total Expenses: £{expense_total:,.2f} | Balance: £{balance:,.2f}"
        tk.Label(frame, text=summary, font=("Arial", 12, "bold")).pack(pady=5)

        # Pie Chart - Expenses by Category
        exp_df = df[df["type"] == "Expense"]
        pie_data = exp_df.groupby("category")["amount"].sum()
        if not pie_data.empty:
            fig1, ax1 = plt.subplots(figsize=(4, 3))
            ax1.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%", startangle=90)
            ax1.set_title("Expenses by Category")

            canvas1 = FigureCanvasTkAgg(fig1, master=frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(pady=5)

        # Bar Chart - Income vs Expense by Frequency
        bar_data = df.groupby(["type", "frequency"], observed=True)["amount"].sum().unstack(fill_value=0)
        fig2, ax2 = plt.subplots(figsize=(7, 4))  # Wider chart
        bar_data.T.plot(kind="bar", ax=ax2)

        ax2.set_title("Income vs Expense by Frequency")
        ax2.set_ylabel("£ Amount")
        ax2.set_xlabel("Frequency")
        ax2.legend(title="Type", bbox_to_anchor=(1.02, 1), loc='upper left')
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=30, ha='right')  # Rotate labels

        fig2.tight_layout()  # This is the key line

        canvas2 = FigureCanvasTkAgg(fig2, master=frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(pady=5, fill="both", expand=True)
        
        # Line Chart - Monthly Income vs Expense Trend
        df["Month"] = pd.to_datetime(df["date"], errors="coerce").dt.to_period("M").astype(str)
        trend_data = df.groupby(["Month", "type"], observed=True)["amount"].sum().unstack(fill_value=0)

        fig3, ax3 = plt.subplots(figsize=(6, 3.5))
        trend_data.plot(ax=ax3, marker="o", linestyle="-")
        ax3.set_title("Monthly Trend: Income vs Expense")
        ax3.set_ylabel("£ Amount")
        ax3.set_xlabel("Month")
        ax3.tick_params(axis="x", rotation=30)
        ax3.legend(title="Type", loc="upper left")
        fig3.tight_layout()
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if file_path:
            fig3.savefig(file_path)

        canvas3 = FigureCanvasTkAgg(fig3, master=frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(pady=5, fill="both", expand=True)

    def build_variance_data(selected_year=None):
        # 1. Get current FY bounds
        today = datetime.today()
        if selected_year:
            start_year = int(selected_year[:4])
        else:
            start_year = today.year if today.month >= 4 else today.year - 1

        fy_label = f"{start_year}/{str(start_year + 1)[-2:]}"
        fy_start = datetime(start_year, 4, 1)
        fy_end = datetime(start_year + 1, 3, 31)

        # 2. Load ledger entries within FY
        df = pd.read_sql_query("SELECT type, category, amount, date FROM ledger", conn)
        #df["date"] = pd.to_datetime(df["date"])
        #df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce") # Incorrect date format
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
        fy_df = df[(df["date"] >= fy_start) & (df["date"] <= fy_end)].copy()

        # 3. Calculate months elapsed (rounded up to include the current one)
        months_elapsed = (today.year - fy_start.year) * 12 + (today.month - 4) + 1

        # 4. Actuals: Sum by type/category
        actuals = fy_df.groupby(["type", "category"])["amount"].sum().reset_index()
        actuals.rename(columns={"amount": "actual"}, inplace=True)

        # 5. Budget: Get planned budgets
        budgets = pd.read_sql_query(
            "SELECT type, category, annual_budget FROM budget_targets WHERE year = ?", conn, params=(fy_label,)
        )
        budgets = budgets.groupby(["type", "category"]).sum().reset_index()

        # 6. Merge & compute metrics
        merged = pd.merge(budgets, actuals, on=["type", "category"], how="left").fillna(0)
        merged["variance"] = merged["annual_budget"] - merged["actual"]
        #merged["% used"] = (merged["actual"] / merged["annual_budget"]).clip(upper=1.5).round(2)
        merged["actual"] = pd.to_numeric(merged["actual"], errors="coerce")
        merged["annual_budget"] = pd.to_numeric(merged["annual_budget"], errors="coerce")
        merged["% used"] = (merged["actual"] / merged["annual_budget"]).clip(upper=1.5).round(2)
        merged["forecast"] = ((merged["actual"] / months_elapsed) * 12).round(2)

        return merged.sort_values(["type", "category"])

    def generate_variance_summary():
        selected_year = year_var.get()
        df = build_variance_data(selected_year)

        if df.empty:
            return "No variance data available to summarize."

        lines = []
        for _, row in df.iterrows():
            category = row["category"]
            actual = row["actual"]
            budget = row["annual_budget"]
            forecast = row["forecast"]
            pct_used = row["% used"]
            type_ = row["type"]

            if budget == 0:
                continue

            if type_.lower() == "income":
                if actual == 0:
                    lines.append(f"{category} income has not started yet.")
                elif actual < budget:
                    pct = (1 - actual / budget) * 100
                    lines.append(f"{category} income is behind target by {pct:.1f}%.")
                else:
                    lines.append(f"{category} income is on or above target.")
            else:
                if actual == 0:
                    lines.append(f"No expenses recorded yet for {category}.")
                elif forecast > budget:
                    pct = (forecast - budget) / budget * 100
                    lines.append(f"{category} expenses are forecast to exceed budget by {pct:.1f}%.")
                else:
                    lines.append(f"{category} is within budget so far.")

        return "\n".join(lines) if lines else "All categories are currently on track."

    def render_variance_table(parent):
        for widget in parent.winfo_children()[3:]:
            widget.destroy()

        selected_year = year_var.get()
        df = build_variance_data(selected_year)

        if df.empty:
            tk.Label(parent, text="No variance data available for this financial year.", fg="red").pack()
            return

        columns = ["Type", "Category", "Annual Budget", "Actual", "Variance", "% Used", "Forecast"]
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)

        tree.tag_configure("under_budget", background="#e7ffe7")  # light green
        tree.tag_configure("over_budget", background="#ffe7e7")   # light red

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        for _, row in df.iterrows():
            is_expense = row["type"].lower() == "expense"
            is_over = row["actual"] > row["annual_budget"] if is_expense else row["actual"] < row["annual_budget"]
            tag = "over_budget" if is_over else "under_budget"

            values = [
                row["type"],
                row["category"],
                f"£{row['annual_budget']:,.2f}",
                f"£{row['actual']:,.2f}",
                f"£{row['variance']:,.2f}",
                f"{row['% used']:.2%}",
                f"£{row['forecast']:,.2f}"
            ]
            tree.insert("", "end", values=values, tags=(tag,))

        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        vsb.pack(side="right", fill="y")

        # === BAR CHART ===
        fig, ax = plt.subplots(figsize=(7, 3.5))
        categories = df["category"]
        bar_width = 0.25
        x = range(len(categories))

        ax.bar([i - bar_width for i in x], df["annual_budget"], width=bar_width, label="Budget")
        ax.bar(x, df["actual"], width=bar_width, label="Actual")
        ax.bar([i + bar_width for i in x], df["forecast"], width=bar_width, label="Forecast")

        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=30, ha="right")
        ax.set_ylabel("£ Amount")
        ax.set_title("Budget vs Actual vs Forecast")
        ax.legend()

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)

    def export_variance_report(format="csv"):
        selected_year = year_var.get()
        df = build_variance_data(selected_year)

        if df.empty:
            messagebox.showinfo("No Data", "No data to export for the selected year.")
            return

        from tkinter import filedialog
        filetypes = [("CSV Files", "*.csv")] if format == "csv" else [("Excel Files", "*.xlsx")]
        default_ext = ".csv" if format == "csv" else ".xlsx"
        file = filedialog.asksaveasfilename(defaultextension=default_ext, filetypes=filetypes)

        if file:
            export_df = df.copy()
            export_df.columns = ["Type", "Category", "Annual Budget", "Actual", "Variance", "% Used", "Forecast"]
            try:
                if format == "csv":
                    export_df.to_csv(file, index=False)
                else:
                    export_df.to_excel(file, index=False)
                messagebox.showinfo("Export Successful", f"Report saved to:\n{file}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    def calculate_financial_year(date_str):
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        start_year = dt.year if dt.month >= 4 else dt.year - 1
        return f"{start_year}/{str(start_year + 1)[-2:]}"

    def save_budget(mode="replace"):
        try:
            amt_raw = float(budget_amount.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount must be numeric.")
            return

        try:
            dt = datetime.strptime(budget_date.get(), "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Invalid Date", "Enter date in dd/MM/yyyy format.")
            return

        fy = calculate_financial_year(dt.strftime("%d/%m/%Y"))
        freq = budget_frequency.get()
        multiplier = frequency_multipliers.get(freq, 1)
        amt = amt_raw * multiplier

        entry = (
            budget_type.get(),
            budget_category.get(),
            freq,
            fy,
            amt,
            budget_notes.get()
        )

        try:
            if mode == "replace":
                cursor.execute('''
                    DELETE FROM budget_targets 
                    WHERE type=? AND category=? AND year=?
                ''', (budget_type.get(), budget_category.get(), fy))

            cursor.execute('''
                INSERT INTO budget_targets 
                (type, category, frequency, year, annual_budget, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', entry)

            conn.commit()
            messagebox.showinfo("Replaced Budget", f"Budget for {fy} has been updated.")
            load_budget_summary()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def speak_budget_summary():
        try:
            amt_raw = float(budget_amount.get())
        except ValueError:
            return

        freq = budget_frequency.get()
        multiplier = frequency_multipliers.get(freq, 1)
        amt = amt_raw * multiplier

        try:
            dt = datetime.strptime(budget_date.get(), "%d/%m/%Y")
            fy = calculate_financial_year(dt.strftime("%d/%m/%Y"))
        except ValueError:
            fy = "the selected year"

        msg = (
            f"Your planned {budget_category.get()} {budget_type.get().lower()} "
            f"for {fy} is £{amt_raw:,.2f} per {freq.lower()}, "
            f"which totals £{amt:,.2f} annually."
        )
        engine.say(msg)
        engine.runAndWait()

    def load_budget_summary():
        for widget in tab_budget.grid_slaves():
            if int(widget.grid_info()["row"]) > 6:
                widget.destroy()

        today = datetime.today()
        fy_current = f"{today.year if today.month >= 4 else today.year - 1}/{str((today.year if today.month >= 4 else today.year - 1) + 1)[-2:]}"
        fy_previous = f"{int(fy_current[:4]) - 1}/{str(int(fy_current[:4]))[-2:]}"

        def display_table(fy_label, fy_value, row_offset):
            tk.Label(tab_budget, text=fy_label, font=("Arial", 10, "bold")).grid(row=row_offset, column=0, pady=5, sticky="w")

            columns = ("Type", "Category", "Frequency", "Budget (pa)", "Notes")
            tree = ttk.Treeview(tab_budget, columns=columns, show="headings", height=6)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor="w")
            tree.grid(row=row_offset+1, column=0, columnspan=4, padx=5, pady=5)

            cursor.execute("SELECT type, category, frequency, annual_budget, notes FROM budget_targets WHERE year=?", (fy_value,))
            for row in cursor.fetchall():
                row = list(row)
                row[3] = f"£{row[3]:,.2f}"
                tree.insert("", "end", values=row)

        display_table("Current Year Budget (2025/26)", fy_current, 7)
        display_table("Previous Year Budget (2024/25)", fy_previous, 14)

    def generate_monthly_report(month_year_str):
        """
        Input: month_year_str in format 'July 2025'
        Output: string summary report
        """
        try:
            report_month = datetime.strptime(month_year_str, "%B %Y")
        except:
            return "Please enter month as: July 2025"

        start_date = report_month.replace(day=1)
        end_date = (start_date.replace(day=28) + pd.DateOffset(days=4)).replace(day=1) - pd.Timedelta(days=1)
        fy_label = calculate_financial_year(start_date.strftime("%d/%m/%Y"))

        # Load ledger entries for that month
        df = pd.read_sql_query("SELECT type, category, amount, date FROM ledger", conn)
        df["date"] = pd.to_datetime(df["date"])
        month_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()

        # Budget per month (annual / 12)
        budgets = pd.read_sql_query(
            "SELECT type, category, annual_budget FROM budget_targets WHERE year = ?", conn, params=(fy_label,)
        )
        budgets["monthly_budget"] = budgets["annual_budget"] / 12

        actuals = month_df.groupby(["type", "category"])["amount"].sum().reset_index()
        merged = pd.merge(budgets, actuals, on=["type", "category"], how="left").fillna(0)

        lines = [f"📅 Monthly Report – {month_year_str}", "-"*40]
        for _, row in merged.iterrows():
            category = row["category"]
            actual = row["amount"]
            budget = row["monthly_budget"]
            type_ = row["type"]
            diff = actual - budget
            pct = (diff / budget * 100) if budget else 0

            if type_.lower() == "income":
                if actual == 0:
                    lines.append(f"– {category} income not received this month.")
                elif actual < budget:
                    lines.append(f"– {category} income under target by £{abs(diff):,.2f} ({abs(pct):.0f}%).")
                else:
                    lines.append(f"– {category} income met or exceeded target.")
            else:
                if actual == 0:
                    lines.append(f"– No spending in {category}.")
                elif actual > budget:
                    lines.append(f"– {category} overspent by £{diff:,.2f} ({pct:.0f}%).")
                else:
                    lines.append(f"– {category} within budget")

        return "\n".join(lines)

    def export_monthly_report_to_pdf(month_year_str):
        summary_text = generate_monthly_report(month_year_str)
        if "Please enter" in summary_text:
            messagebox.showerror("Invalid Input", summary_text)
            return

        from tkinter import filedialog
        safe_name = month_year_str.replace(" ", "_").replace(":", "")
        default_name = f"Monthly_Report_{safe_name}.pdf"

        file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=default_name,
            title="Save Monthly Report"
        )
        if not file:
            return

        try:
            c = canvas.Canvas(file, pagesize=A4)
            width, height = A4
            c.setFont("Helvetica-Bold", 14)
            c.drawString(1 * inch, height - 1 * inch, f"Monthly Budget Report – {month_year_str}")

            c.setFont("Helvetica", 11)
            y = height - 1.4 * inch
            for line in summary_text.split("\n"):
                if y < 1 * inch:
                    c.showPage()
                    y = height - 1 * inch
                    c.setFont("Helvetica", 11)
                c.drawString(1 * inch, y, line)
                y -= 14

            c.save()
            messagebox.showinfo("Export Successful", f"Report saved to:\n{file}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def add_task():
        title = task_title.get().strip()
        desc = task_desc.get().strip()
        due = task_due.get().strip()
        reminder = task_reminder.get().strip()
        recurrence = task_recurrence.get().strip()

        if not title or not due:
            messagebox.showerror("Missing Info", "Please provide at least a title and due date.")
            return

        try:
            if reminder:
                datetime.strptime(reminder, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Reminder Time must be in HH:MM format (e.g., 08:30).")
            return

        cursor.execute(
            "INSERT INTO tasks (title, description, due_date, reminder_time, recurrence) VALUES (?, ?, ?, ?, ?)",
            (title, desc, due, reminder, recurrence)
        )
        conn.commit()
        messagebox.showinfo("Task Added", f"Task '{title}' has been added.")
        load_tasks()
        clear_task_fields()

    def load_tasks():
        for row in task_tree.get_children():
            task_tree.delete(row)

        shown = 0
        overdue_count = 0
        today_count = 0
        incomplete_count = 0

        task_tree.tag_configure("completed", background="#d0f0d0")
        task_tree.tag_configure("overdue", background="#ffe6e6")

        filter_value = task_filter.get()
        today = date.today()
        week_ahead = today + timedelta(days=7)

        cursor.execute("SELECT id, title, description, due_date, reminder_time, recurrence, is_completed FROM tasks ORDER BY due_date ASC")
        for row in cursor.fetchall():
            row = list(row)
            recurrence = row[5]
            is_completed = row[6]

            if recurrence != "None":
                row[5] = f"🔁 {recurrence}"
            else:
                row[5] = "None"

            values = row[:6]
            due = datetime.strptime(row[3], "%d/%m/%Y").date()

            # Filter logic
            if filter_value == "Today" and due != today:
                continue
            if filter_value == "Overdue" and due >= today:
                continue
            if filter_value == "Incomplete" and is_completed:
                continue
            if filter_value == "Next 7 Days" and not (today <= due <= week_ahead):
                continue
                tag = "upcoming"

            # Update summary stats
            shown += 1
            if not is_completed:
                incomplete_count += 1
            if due == today:
                today_count += 1
            elif due < today and not is_completed:
                overdue_count += 1

            if is_completed:
                tag = "completed"
            elif due < today:
                tag = "overdue"
            elif today <= due <= week_ahead:
                tag = "upcoming"
            else:
                tag = ""

            task_tree.insert("", "end", values=values, tags=(tag,))

        summary = f"{shown} task(s) shown"
        if filter_value == "All":
            summary += f" — {incomplete_count} incomplete, {today_count} today, {overdue_count} overdue"
        task_count_label.config(text=summary)

    def delete_task():
        selected = task_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a task to delete.")
            return

        values = task_tree.item(selected, "values")
        task_id = values[0]
        title = values[1]
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the task:\n\n{title}")
        if not confirm:
            return

        try:
            cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()
            load_tasks()
            messagebox.showinfo("Deleted", f"Task '{title}' was removed.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def edit_task():
        selected = task_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a task to edit.")
            return

        #values = task_tree.item(selected, "values")
        item = task_tree.item(selected)
        values = item["values"]
        task_id, title, desc, due, reminder, recurrence = values

        # Fill the form fields
        task_title.set(title)
        task_desc.set(desc)
        task_due.set(due)
        task_reminder.set(reminder)  # fill into the time field
        task_recurrence.set(recurrence)

        # Change Add button to Save Edit temporarily
        def save_edit():
            new_title = task_title.get().strip()
            new_desc = task_desc.get().strip()
            new_due = task_due.get().strip()
            new_reminder = task_reminder.get().strip()
            new_recurrence = task_recurrence.get().strip()
            
            if not new_title or not new_due:
                messagebox.showerror("Missing Info", "Please enter a title and due date.")
                return

            try:
                if new_reminder:
                    datetime.strptime(new_reminder, "%H:%M")
            except ValueError:
                messagebox.showerror("Invalid Time", "Reminder Time must be in HH:MM format (e.g., 08:30).")
                return

            cursor.execute(
                "UPDATE tasks SET title=?, description=?, due_date=?, reminder_time=?, recurrence=? WHERE id=?",
                (new_title, new_desc, new_due, new_reminder, new_recurrence, task_id)
            )

            conn.commit()
            messagebox.showinfo("Updated", f"Task '{new_title}' updated.")
            load_tasks()
            task_button.config(text="Add Task", command=add_task)  # Reset
            clear_task_fields()

        # Override the existing button
        task_button.config(text="Save Edit", command=save_edit)
        
        cancel_btn = tk.Button(task_frame, text="Cancel", fg="red")
        cancel_btn.grid(row=5, column=2, padx=5)

        def cancel_edit():
            clear_task_fields()
            task_button.config(text="Add Task", command=add_task)
            cancel_btn.destroy()

        cancel_btn.config(command=cancel_edit)

    def clear_task_fields():
        task_title.set("")
        task_desc.set("")
        task_due.set(datetime.today().strftime('%d/%m/%Y'))
        task_reminder.set("")  # clear reminder time too
        task_recurrence.set("None")

    def generate_next_tasks():
        today = datetime.today().date()
        #cursor.execute("SELECT title, description, due_date, reminder_time, recurrence FROM tasks WHERE recurrence != 'None'")
        cursor.execute("SELECT title, description, due_date, reminder_time, recurrence FROM tasks WHERE recurrence != 'None' AND is_completed = 0")
        for title, desc, due_str, reminder, recurrence in cursor.fetchall():
            try:
                due = datetime.strptime(due_str, "%d/%m/%Y").date()
            except:
                continue

            if due > today:
                continue  # Not overdue yet

            # Calculate the new due date based on recurrence
            if recurrence == "Daily":
                next_due = due + timedelta(days=1)
            elif recurrence == "Weekly":
                next_due = due + timedelta(weeks=1)
            elif recurrence == "Monthly":
                # Handle monthly edge cases (e.g. Jan 31 → Feb 28)
                next_month = due.replace(day=1) + timedelta(days=32)
                next_due = next_month.replace(day=1)
            else:
                continue

            # Check if the task already exists for the next due date
            cursor.execute("""
                SELECT 1 FROM tasks WHERE title=? AND due_date=? AND recurrence=?
            """, (title, next_due.strftime("%d/%m/%Y"), recurrence))
            if cursor.fetchone():
                continue  # Already scheduled

            # Insert the next instance
            cursor.execute("""
                INSERT INTO tasks (title, description, due_date, reminder_time, recurrence)
                VALUES (?, ?, ?, ?, ?)
            """, (title, desc, next_due.strftime("%d/%m/%Y"), reminder, recurrence))

        conn.commit()
        load_tasks()  # Refresh table

    def add_bill():
        payee = bill_payee.get().strip()
        amount = bill_amount.get().strip()
        due = bill_due.get().strip()
        reminder = bill_reminder.get().strip()
        recurrence = bill_recurrence.get().strip()
        category = bill_category.get().strip()

        if not payee or not amount or not due:
            messagebox.showerror("Missing Info", "Please fill in payee, amount, and due date.")
            return

        try:
            amt_val = float(amount)
            if amt_val <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount must be a positive number.")
            return

        try:
            if reminder:
                datetime.strptime(reminder, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Reminder time must be in HH:MM format (e.g., 14:30).")
            return

        # Convert dd/mm/yyyy to yyyy-mm-dd before DB insert
        try:
            due_obj = datetime.strptime(due, "%d/%m/%Y")
            due_db = due_obj.strftime("%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Invalid Date", "Due date must be in DD/MM/YYYY format.")
            return

        try:
            #cursor.execute('''
            #    INSERT INTO bills (payee, amount, due_date, reminder_time, recurrence)
            #    VALUES (?, ?, ?, ?, ?)
            #''', (payee, amt_val, due_db, reminder, recurrence))
            cursor.execute('''
                INSERT INTO bills (payee, amount, due_date, reminder_time, recurrence, category)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (payee, amt_val, due_db, reminder, recurrence, category))
            conn.commit()
            messagebox.showinfo("Bill Added", f"'{payee}' for £{amt_val:,.2f} was added.")
            load_bills()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_bills():
        for row in bill_tree.get_children():
            bill_tree.delete(row)

        bill_tree.tag_configure("paid", background="#d0f0d0")
        bill_tree.tag_configure("unpaid", background="#ffe7e7")

        filter_type = bill_filter_option.get()
        category_filter = bill_category_filter.get()

        today = date.today()
        week_from_now = today + timedelta(days=7)

        query = "SELECT id, payee, category, amount, due_date, reminder_time, recurrence, is_paid FROM bills"
        where_clauses = []
        params = []

        # Build all WHERE conditions together
        if filter_type == "Unpaid Only":
            where_clauses.append("is_paid = 0")
        elif filter_type == "Due Today":
            where_clauses.append("due_date = ? AND is_paid = 0")
            params.append(today.strftime("%d/%m/%Y"))
        elif filter_type == "Due This Week":
            where_clauses.append("due_date BETWEEN ? AND ? AND is_paid = 0")
            params.extend([today.strftime("%d/%m/%Y"), week_from_now.strftime("%d/%m/%Y")])

        if category_filter != "All":
            where_clauses.append("category = ?")
            params.append(category_filter)

        # ✅ Finalise WHERE clause only once
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY due_date ASC"

        cursor.execute(query, params)

        for row in cursor.fetchall():
            row_id, payee, category, amount, due, reminder, recurrence, is_paid = row
            try:
                due = datetime.strptime(due, "%d/%m/%Y").strftime("%d/%m/%Y")
            except:
                pass

            amount = f"£{amount:,.2f}"
            tag = "paid" if is_paid else "unpaid"

            bill_tree.insert("", "end", values=[row_id, payee, category, amount, due, reminder, recurrence], tags=(tag,))

    def check_due_bills():
        today = date.today().strftime("%d/%m/%Y")
        now_time = datetime.now().strftime("%H:%M")

        # print(f"Reminder check at {now_time}") # Just to test quickly without waiting for the clock to match, temporarily add

        cursor.execute("""
            SELECT payee, amount, due_date, reminder_time, is_paid 
            FROM bills 
            WHERE due_date = ?
        """, (today,))

        rows = cursor.fetchall()
        for payee, amount, due, reminder, is_paid in rows:
            if is_paid:
                continue  # Skip paid bills

            notify = False
            if not reminder:
                notify = True  # Notify any time during the day
            # elif reminder == now_time:
            elif reminder <= now_time:
                notify = True

            if notify:
                msg = f"Reminder: '{payee}' bill of £{amount:,.2f} is due today."
                messagebox.showinfo("Bill Reminder", msg)

                try:
                    engine.say(msg)
                    engine.runAndWait()
                except Exception as e:
                    print("Voice error:", e)

    def edit_bill():
        selected = bill_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a bill to edit.")
            return

        values = bill_tree.item(selected)["values"]
        #bill_id, payee_val, amount_val, due_val, reminder_val, recurrence_val = values
        bill_id, payee_val, category_val, amount_val, due_val, reminder_val, recurrence_val = values

        # Populate form fields
        bill_payee.set(payee_val)
        bill_amount.set(amount_val.replace("£", "").replace(",", ""))
        bill_due.set(due_val)
        bill_reminder.set(reminder_val)
        bill_recurrence.set(recurrence_val)
        bill_category.set(category_val)

        def save_bill_edit():
            try:
                due_obj = datetime.strptime(bill_due.get(), "%d/%m/%Y")
                due_db = due_obj.strftime("%d/%m/%Y")
                amt_val = float(bill_amount.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Please check amount or date format.")
                return

            try:
            #    cursor.execute('''
            #        UPDATE bills
            #        SET payee = ?, amount = ?, due_date = ?, reminder_time = ?, recurrence = ?
            #        WHERE id = ?
            #    ''', (bill_payee.get(), amt_val, due_db, bill_reminder.get(), bill_recurrence.get(), bill_id))
                cursor.execute('''
                    UPDATE bills
                    SET payee = ?, amount = ?, due_date = ?, reminder_time = ?, recurrence = ?, category = ?
                    WHERE id = ?
                ''', (
                    bill_payee.get(),
                    amt_val,
                    due_db,
                    bill_reminder.get(),
                    bill_recurrence.get(),
                    bill_category.get().strip(),
                    bill_id
                ))

                conn.commit()
                messagebox.showinfo("Bill Updated", f"'{payee_val}' was updated.")
                load_bills()
                add_bill_button.config(text="Add Bill", command=add_bill)
            except Exception as e:
                messagebox.showerror("Update Failed", str(e))

        add_bill_button.config(text="Save Changes", command=save_bill_edit)
        # Cancel button appears during edit mode
        cancel_btn = tk.Button(bill_form, text="Cancel", fg="red")
        cancel_btn.grid(row=5, column=2, padx=5)

        def cancel_edit():
            # Reset fields
            bill_payee.set("")
            bill_amount.set("")
            bill_due.set(datetime.today().strftime("%d/%m/%Y"))
            bill_reminder.set("")
            bill_recurrence.set("None")

            # Restore button
            add_bill_button.config(text="Add Bill", command=add_bill)
            cancel_btn.destroy()

        cancel_btn.config(command=cancel_edit)
        #load_bills() # Reload bills on screen

    def export_bills_to_csv():
        from tkinter import filedialog
        #file = filedialog.asksaveasfilename(
        #    defaultextension=".csv",
        #    filetypes=[("CSV Files", "*.csv")],
        #    title="Export Bills"
        #)
        #if not file:
        #    return

        try:
            filter_type = bill_filter_option.get()
            query = "SELECT payee, amount, due_date, reminder_time, recurrence, is_paid FROM bills"
            params = []

            today = date.today()
            week_ahead = today + timedelta(days=7)

            if filter_type == "Unpaid Only":
                query += " WHERE is_paid = 0"
            elif filter_type == "Due Today":
                query += " WHERE due_date = ? AND is_paid = 0"
                params.append(today.strftime("%d/%m/%Y"))
            elif filter_type == "Due This Week":
                query += " WHERE due_date BETWEEN ? AND ? AND is_paid = 0"
                params.extend([today.strftime("%d/%m/%Y"), week_ahead.strftime("%d/%m/%Y")])
            query += " ORDER BY due_date ASC"

            df = pd.read_sql_query(query, conn, params=params)
            if df.empty:
                messagebox.showinfo("No Data", "No bills to export based on current filter.")
                return

            df["amount"] = df["amount"].apply(lambda x: f"£{x:,.2f}")
            df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce").dt.strftime("%d/%m/%Y")
            df["is_paid"] = df["is_paid"].map({0: "No", 1: "Yes"})

            df.columns = [
                "Payee",
                "Amount (£)",
                "Due Date (DD/MM/YYYY)",
                "Reminder Time (HH:MM)",
                "Repeat Frequency",
                "Paid?"
            ]

            default_name = f"{filter_type.replace(' ', '_')}_Bills_{today.strftime('%d-%m-%Y')}.csv"
            file = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")],
                title="Export Bills",
                initialfile=default_name
            )
            if not file:
                return

            df.to_csv(file, index=False)
            messagebox.showinfo("Export Successful", f"Bills exported to:\n{file}")

        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def get_safe_next_due(base_date, offset_days):
        """
        Returns a safely adjusted future date using the original day if possible,
        or the last valid day in the target month.
        """
        target = base_date.replace(day=1) + timedelta(days=offset_days)
        year, month = target.year, target.month
        last_day = calendar.monthrange(year, month)[1]
        safe_day = min(base_date.day, last_day)
        return target.replace(day=safe_day)

    def generate_next_bills():
        today = date.today()

        cursor.execute("""
            SELECT id, payee, amount, due_date, reminder_time, recurrence 
            FROM bills 
            WHERE is_paid = 1 AND recurrence != 'None'
        """)
        for bill_id, payee, amount, due_str, reminder, recurrence in cursor.fetchall():
            try:
                due = datetime.strptime(due_str, "%d/%m/%Y").date()
            except:
                continue

            if due > today:
                continue  # Not ready to recur yet

            # Calculate next due date
            #if recurrence == "Monthly":
            #    # next_due = (due.replace(day=1) + timedelta(days=32)).replace(day=due.day)
            #    next_month = due.replace(day=1) + timedelta(days=32)
            #    year = next_month.year
            #    month = next_month.month
            #    last_day = calendar.monthrange(year, month)[1]
            #    safe_day = min(due.day, last_day)
            #    next_due = next_month.replace(day=safe_day)
            #elif recurrence == "Quarterly":
            #    #next_due = (due.replace(day=1) + timedelta(days=95)).replace(day=due.day)
            #    next_quarter = due.replace(day=1) + timedelta(days=95)
            #    year = next_quarter.year
            #    month = next_quarter.month
            #    last_day = calendar.monthrange(year, month)[1]
            #    safe_day = min(due.day, last_day)
            #    next_due = next_quarter.replace(day=safe_day)
            #elif recurrence == "Yearly":
            #    try:
            #        next_due = due.replace(year=due.year + 1)
            #    except ValueError:
            #        next_due = due.replace(day=28, month=2, year=due.year + 1)
            #else:
            #    continue
            if recurrence == "Monthly":
                next_due = get_safe_next_due(due, 32)       # ~1 month ahead
            elif recurrence == "Quarterly":
                next_due = get_safe_next_due(due, 95)       # ~3 months ahead
            elif recurrence == "Yearly":
                try:
                    next_due = due.replace(year=due.year + 1)
                except ValueError:
                    next_due = due.replace(day=28, month=2, year=due.year + 1)
            else:
                continue


            # Check for duplicate
            cursor.execute("""
                SELECT 1 FROM bills WHERE payee=? AND due_date=? AND amount=? AND recurrence=?
            """, (payee, next_due.strftime("%d/%m/%Y"), amount, recurrence))
            if cursor.fetchone():
                continue  # Already generated

            # Insert next bill
            cursor.execute("""
                INSERT INTO bills (payee, amount, due_date, reminder_time, recurrence, is_paid)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (payee, amount, next_due.strftime("%d/%m/%Y"), reminder, recurrence))

        conn.commit()

    def delete_bill():
        selected = bill_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a bill to delete.")
            return

        values = bill_tree.item(selected)["values"]
        bill_id = values[0]
        payee = values[1]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the bill:\n\n{payee}")
        if not confirm:
            return

        try:
            cursor.execute("DELETE FROM bills WHERE id=?", (bill_id,))
            conn.commit()
            load_bills()
            messagebox.showinfo("Deleted", f"Bill '{payee}' was removed.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_bill_summary():
        today = date.today()
        week_ahead = today + timedelta(days=7)

        cursor.execute("""
            SELECT payee, amount, due_date, is_paid 
            FROM bills 
            ORDER BY due_date ASC
        """)
        rows = cursor.fetchall()

        unpaid = [r for r in rows if not r[3]]
        due_today = [r for r in unpaid if r[2] == today.strftime("%d/%m/%Y")]
        due_this_week = [r for r in unpaid if today.strftime("%d/%m/%Y") < r[2] <= week_ahead.strftime("%d/%m/%Y")]

        total_unpaid = sum(float(r[1]) for r in unpaid)
        next_bill = next((r for r in rows if not r[3]), None)

        msg = [
            f"📌 You have {len(unpaid)} unpaid bill(s) totaling £{total_unpaid:,.2f}.",
            f"📅 {len(due_this_week)} due this week, {len(due_today)} due today.",
        ]
        if next_bill:
            due_date = datetime.strptime(next_bill[2], "%d/%m/%Y").strftime("%d/%m/%Y")
            msg.append(f"🔔 Next upcoming: {next_bill[0]} on {due_date}.")

        summary = "\n".join(msg)

        top = tk.Toplevel()
        top.title("Bill Summary")
        tk.Label(top, text="📋 Overview", font=("Arial", 12, "bold")).pack(pady=10)
        text = tk.Text(top, wrap="word", width=60, height=6)
        text.insert("1.0", summary)
        text.config(state="disabled")
        text.pack(padx=10, pady=5)
        tk.Button(top, text="Close", command=top.destroy).pack(pady=5)

    def highlight_calendar_events():
        calendar.calevent_remove('all')  # Clear old markers

        # Tag unpaid bills
        cursor.execute("SELECT due_date FROM bills WHERE is_paid = 0")
        for (due_str,) in cursor.fetchall():
            try:
                dt = datetime.strptime(due_str, "%d/%m/%Y").date()
                calendar.calevent_create(dt, "Unpaid Bill", "bill_due")
            except:
                continue

        # Tag tasks (regardless of completion)
        cursor.execute("SELECT due_date FROM tasks")
        for (due_str,) in cursor.fetchall():
            try:
                dt = datetime.strptime(due_str, "%d/%m/%Y").date()
                calendar.calevent_create(dt, "Task Due", "task_due")
            except:
                continue

        # Tag styles
        calendar.tag_config("bill_due", background="#ff9999")   # soft red
        calendar.tag_config("task_due", background="#99ccff")   # soft blue

    def generate_bill_forecast():
        today = date.today()
        future = today + timedelta(days=30)

        cursor.execute("""
            SELECT payee, amount, due_date 
            FROM bills 
            WHERE is_paid = 0 AND due_date BETWEEN ? AND ?
            ORDER BY due_date ASC
        """, (today.strftime("%d/%m/%Y"), future.strftime("%d/%m/%Y")))
        
        rows = cursor.fetchall()
        if not rows:
            messagebox.showinfo("No Upcoming Bills", "No unpaid bills due in the next 30 days.")
            return

        summary = {}
        total_due = 0

        for payee, amount, due_str in rows:
            try:
                due = datetime.strptime(due_str, "%d/%m/%Y").date()
                key = due.strftime("%d/%m/%Y")
                summary.setdefault(key, []).append((payee, amount))
                total_due += amount
            except:
                continue

        report = [f"🔮 Upcoming Bills (Next 30 Days)", "-"*40]
        for date_str in sorted(summary):
            report.append(f"\n📅 {date_str}")
            for payee, amt in summary[date_str]:
                report.append(f"  • {payee}: £{amt:,.2f}")
        report.append(f"\n💰 Total Due: £{total_due:,.2f}")

        # Display
        top = tk.Toplevel()
        top.title("Bill Forecast")
        tk.Label(top, text="30-Day Payment Forecast", font=("Arial", 12, "bold")).pack(pady=10)
        txt = tk.Text(top, width=60, height=20, wrap="word")
        txt.insert("1.0", "\n".join(report))
        txt.config(state="disabled")
        txt.pack(padx=10, pady=5)
        tk.Button(top, text="Close", command=top.destroy).pack(pady=5)

    def show_bills_by_category_chart():
        try:
            cursor.execute("""
                SELECT category, SUM(amount)
                FROM bills
                WHERE is_paid = 0
                GROUP BY category
            """)
            data = cursor.fetchall()

            if not data:
                messagebox.showinfo("No Data", "No unpaid bills to visualize.")
                return

            labels, values = zip(*data)

            fig, ax = plt.subplots(figsize=(5.5, 4))
            ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.set_title("Unpaid Bills by Category")

            # Display in Toplevel window
            top = tk.Toplevel()
            top.title("Bill Category Breakdown")
            canvas = FigureCanvasTkAgg(fig, master=top)
            canvas.draw()
            canvas.get_tk_widget().pack(padx=10, pady=10, fill="both", expand=True)
            tk.Button(top, text="Close", command=top.destroy).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Chart Error", str(e))

    def suggest_monthly_budgets():
        recent_start = (datetime.today() - pd.DateOffset(months=3)).strftime("%d/%m/%Y")
        today = datetime.today().strftime("%d/%m/%Y")

        # Load recent expense data
        df = pd.read_sql_query("""
            SELECT category, amount, date FROM ledger
            WHERE type = 'Expense' AND date BETWEEN ? AND ?
        """, conn, params=(recent_start, today))

        if df.empty:
            return "No recent expense data found."

        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
        df["Month"] = df["date"].dt.to_period("M").astype(str)

        summary = df.groupby(["category", "Month"])["amount"].sum().reset_index()
        suggestions = summary.groupby("category")["amount"].mean().round(2).reset_index()
        suggestions.columns = ["category", "avg_monthly_spend"]

        # Compare with budget (optional)
        today = datetime.today()
        fy = calculate_financial_year(today.strftime("%d/%m/%Y"))
        budgets = pd.read_sql_query("""
            SELECT category, annual_budget FROM budget_targets
            WHERE type = 'Expense' AND year = ?
        """, conn, params=(fy,))
        budgets["monthly_budget"] = budgets["annual_budget"] / 12

        final = pd.merge(suggestions, budgets, on="category", how="left")

        def comment(row):
            if pd.isna(row["monthly_budget"]):
                return "No budget yet"
            diff = row["avg_monthly_spend"] - row["monthly_budget"]
            pct = (diff / row["monthly_budget"]) * 100
            if abs(pct) <= 10:
                return "✅ Aligned"
            elif pct > 10:
                return f"⚠️ Overspending by {pct:.0f}%"
            else:
                return f"⬇️ Underspending by {abs(pct):.0f}%"

        final["Note"] = final.apply(comment, axis=1)
        return final[["category", "avg_monthly_spend", "monthly_budget", "Note"]]
     
    # tree.bind("<<TreeviewSelect>>", lambda event: apply_suggestion_to_planner(tree))
     
    def apply_suggestion_to_planner(tree):
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0])["values"]

        category = values[0]
        avg_spend = values[1].replace("£", "").replace(",", "")
        
        try:
            amount = float(avg_spend)
        except ValueError:
            return

        # Prefill planner fields
        budget_type.set("Expense")
        budget_category.set(category)
        budget_frequency.set("Monthly")
        budget_amount.set(str(round(amount, 2)))
        budget_notes.set("Auto-filled from suggestions")

        # Optional confirmation
        messagebox.showinfo("Planner Updated", f"Prefilled Budget Planner for {category} (£{amount:,.2f}/mo)")
     
    def display_budget_suggestions(parent):
        for widget in parent.winfo_children()[1:]:
            widget.destroy()

        result = suggest_monthly_budgets()

        if isinstance(result, str):
            tk.Label(parent, text=result, fg="red").pack()
            return

        tree = ttk.Treeview(parent, columns=("Category", "Avg Spend", "Current Budget", "Note"), show="headings")
        for col in ("Category", "Avg Spend", "Current Budget", "Note"):
            tree.heading(col, text=col)
            tree.column(col, width=160, anchor="center")
        
        tree.bind("<<TreeviewSelect>>", lambda event: apply_suggestion_to_planner(tree))

        tree.pack(padx=10, pady=5, fill="both", expand=True)

        for _, row in result.iterrows():
            avg = f"£{row['avg_monthly_spend']:,.2f}"
            curr = f"£{row['monthly_budget']:,.2f}" if not pd.isna(row['monthly_budget']) else "—"
            tree.insert("", "end", values=[row["category"], avg, curr, row["Note"]])
            
        #tk.Button(tab_suggestions, text="🗣️ Speak Summary", command=speak_budget_summary).pack(pady0)
        #tk.Button(parent, text="📤 Export to CSV", command=export_budget_suggestions_to_csv).pack(pady=5)
        button_frame = tk.Frame(parent)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="🗣️ Speak Summary", command=speak_budget_summary).pack(side="left", padx=5)
        tk.Button(button_frame, text="📤 Export to CSV", command=export_budget_suggestions_to_csv).pack(side="left", padx=5)
        tk.Button(button_frame, text="📋 Copy to Clipboard", command=copy_budget_suggestions_to_clipboard).pack(side="left", padx=5)

    def speak_budget_summary():
        result = suggest_monthly_budgets()
        if isinstance(result, str):
            engine.say("No recent expense data found to analyze.")
            engine.runAndWait()
            return

        aligned = []
        over = []
        under = []
        missing = []

        for _, row in result.iterrows():
            cat = row["category"]
            note = row["Note"]

            if "Aligned" in note:
                aligned.append(cat)
            elif "Overspending" in note:
                over.append(f"{cat}, {note}")
            elif "Underspending" in note:
                under.append(f"{cat}, {note}")
            elif "No budget" in note:
                missing.append(cat)

        msg = []

        if over:
            msg.append("Warning: you are overspending in the following categories:")
            msg += over
        if under:
            msg.append("You may be underspending in:")
            msg += under
        if aligned:
            msg.append("Tracking well in:")
            msg.append(", ".join(aligned))
        if missing:
            msg.append("No current budget set for:")
            msg.append(", ".join(missing))

        if not msg:
            engine.say("No noteworthy trends found. All budgets appear balanced.")
        else:
            engine.say(" ".join(msg))

        engine.runAndWait()

    def export_budget_suggestions_to_csv():
        result = suggest_monthly_budgets()
        if isinstance(result, str):
            messagebox.showinfo("No Data", result)
            return

        from tkinter import filedialog
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export Budget Suggestions",
            initialfile="Suggested_Budgets.csv"
        )
        if not file:
            return

        try:
            result.columns = ["Category", "Avg Monthly Spend (£)", "Current Budget (£)", "Note"]
            result.to_csv(file, index=False)
            messagebox.showinfo("Export Successful", f"Suggestions saved to:\n{file}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def copy_budget_suggestions_to_clipboard():
        result = suggest_monthly_budgets()
        if isinstance(result, str):
            messagebox.showinfo("No Data", result)
            return

        lines = ["Suggested Budget Insights:\n"]
        for _, row in result.iterrows():
            cat = row["category"]
            avg = f"£{row['avg_monthly_spend']:,.2f}"
            curr = f"£{row['monthly_budget']:,.2f}" if not pd.isna(row["monthly_budget"]) else "—"
            note = row["Note"]
            lines.append(f"{cat}: Avg £{avg}, Current £{curr}, Note: {note}")

        summary = "\n".join(lines)

        try:
            root.clipboard_clear()
            root.clipboard_append(summary)
            root.update()  # Keeps clipboard alive after app closes
            messagebox.showinfo("Copied", "Budget summary copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")

    import threading
    import time
    import pyttsx3
    import simpleaudio as sa
    from tkinter import messagebox as mb
    import pygame
    pygame.mixer.init()
    import random

    # Global flags
    is_paused = False
    stop_session = False

    # Bell helper
    def play_bell(path):
        #try:
        #    wave_obj = sa.WaveObject.from_wave_file(path)
        #    play_obj = wave_obj.play()
        #    play_obj.wait_done()  # 🔑 Wait until sound finishes
        #    print(f"🔔 Played and finished: {path}")
        #except Exception as e:
        #    print("Bell error:", e)
        try:
            print(f"🔔 Playing bell with pygame: {path}")
            pygame.mixer.init()
            sound = pygame.mixer.Sound(path)
            sound.play()
            while pygame.mixer.get_busy():
                time.sleep(0.1)
            print("✅ Bell finished")
        except Exception as e:
            print("❌ Bell playback error:", e)
            messagebox.showerror("Playback Error", str(e))
            
    # Pause & Cancel controls (use in buttons)
    def toggle_pause():
        global is_paused
        is_paused = not is_paused
        state = "paused" if is_paused else "resumed"
        print(f"⏸️ Session {state}")

        # Proper voice feedback
        def speak_pause():
            engine = pyttsx3.init()
            engine.say(f"Session {state}")
            engine.runAndWait()
        
        threading.Thread(target=speak_pause).start()

    def cancel_session():
        global stop_session
        stop_session = True
        print("❌ Session cancelled")

    # Main meditation logic
    def start_meditation_session(style, minutes):
        global is_paused, stop_session
        is_paused = False
        stop_session = False

        def session():
            try:
                local_engine = pyttsx3.init()
                local_engine.setProperty("rate", 140)  # calm tone
                print("🧘‍♂️ Meditation started")

                play_bell("sounds/start_bell.wav")

                intro = f"Welcome to your {style.lower()} meditation. We will begin a {minutes} minute session. Please find a comfortable seated position."
                local_engine.say(intro)
                local_engine.runAndWait()
                print("✅ Intro complete")

                # Start ambient background (if selected)
                bg = soundscape_var.get()
                if bg != "None":
                    path = f"sounds/ambience/{bg.lower()}.mp3"
                    play_background(path)
                    print(f"🎵 Ambient loop started: {bg}")

                elapsed = 0
                total_seconds = minutes * 60

                if style == "Guided Breathing":
                    local_engine.say("Close your eyes gently. Inhale... and exhale...")
                    local_engine.runAndWait()
                    print("🌬️ Breathing started")

                    while elapsed < total_seconds and not stop_session:
                        if is_paused:
                            time.sleep(1)
                            continue
                        local_engine.say("Breathe in... and breathe out...")
                        local_engine.runAndWait()
                        time.sleep(30)
                        elapsed += 30
                        print(f"⏳ {elapsed}/{total_seconds} seconds")

                elif style == "Loving Kindness":
                    local_engine.say("Bring to mind someone you care about. Silently say: May you be happy. May you be safe. May you be well.")
                    local_engine.runAndWait()

                    while elapsed < total_seconds and not stop_session:
                        if is_paused:
                            time.sleep(1)
                            continue
                        time.sleep(5)
                        elapsed += 5

                elif style == "Body Scan":
                    local_engine.say("Begin by noticing your feet... then ankles... and slowly move up the body.")
                    local_engine.runAndWait()

                    while elapsed < total_seconds and not stop_session:
                        if is_paused:
                            time.sleep(1)
                            continue
                        time.sleep(5)
                        elapsed += 5
                
                elif style == "Zen (Silent Sitting)":
                    local_engine.say("We will sit quietly. A bell will sound every 5 minutes.")
                    local_engine.runAndWait()

                    bell_interval = 300  # 5 minutes
                    while elapsed < total_seconds and not stop_session:
                        if is_paused:
                            time.sleep(1)
                            continue
                        time.sleep(bell_interval)
                        elapsed += bell_interval
                        play_bell("sounds/start_bell.wav")
                        print(f"🔔 {elapsed} seconds passed")
                
                if not stop_session:
                    play_bell("sounds/end_bell.wav")
                    local_engine.say("Your session has ended. Gently open your eyes.")
                else:
                    local_engine.say("Meditation cancelled...")

                stop_background()
                print("🛑 Ambient sound stopped")

                local_engine.runAndWait()
                print("🎧 Meditation complete")

                # ✅ Log date and show streak
                if not stop_session:
                    with open("meditation_log.txt", "a") as f:
                        f.write(f"{datetime.today().strftime('%Y-%m-%d')}\n")

                streak, last_date = get_meditation_streak()
                msg = f"You've meditated {streak} day(s) in a row." if streak else "Welcome back. Let’s begin again."
                messagebox.showinfo("Streak Tracker", msg)
                print("📈", msg)
                local_engine.say(msg)
                local_engine.runAndWait()

                prompt_reflection(style)

            except Exception as e:
                print("❌ Meditation session error:", e)
                messagebox.showerror("Voice Error", str(e))
            
        threading.Thread(target=session, daemon=True).start()

    def get_meditation_streak(log_file="meditation_log.txt"):
        try:
            with open(log_file, "r") as f:
                dates = sorted(set(line.strip() for line in f if line.strip()))
        except FileNotFoundError:
            return 0, None

        today = datetime.today().date()
        streak = 0
        last_date = None

        for offset in range(len(dates)):
            check_day = today - timedelta(days=offset)
            if check_day.strftime("%Y-%m-%d") in dates:
                streak += 1
                last_date = check_day
            else:
                break

        return streak, last_date

    def prompt_reflection(style):
        def save_entry():
            note = text_box.get("1.0", "end").strip()
            mood = mood_var.get()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

            with open("meditation_journal.csv", "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, style, mood, note])

            messagebox.showinfo("Saved", "Reflection saved.")
            popup.destroy()

        popup = tk.Toplevel()
        popup.title("📝 Post-Session Reflection")
        tk.Label(popup, text="How are you feeling after this session?").pack(pady=5)

        mood_var = tk.StringVar(value="Neutral")
        tk.OptionMenu(popup, mood_var, "Calm", "Neutral", "Restless", "Grateful", "Sad", "Anxious", "Energized").pack()

        text_box = tk.Text(popup, width=50, height=6)
        text_box.pack(padx=10, pady=5)

        tk.Button(popup, text="Save Reflection", command=save_entry).pack(pady=5)

    def prepare_shot():
        # Generate and show wind value
        wind = random.uniform(-5, 5)
        direction = "➡️" if wind > 0 else "⬅️" if wind < 0 else "⭘"
        wind_label.config(text=f"Wind: {wind:+.1f} {direction}")
        
        # Store wind for the next shot
        prepare_shot.wind = wind

    def flash_apple():
        game_canvas.itemconfig(apple, fill="yellow")
        game_canvas.update()
        time.sleep(0.1)
        game_canvas.itemconfig(apple, fill="red")

    def shoot_arrow():
        angle = math.radians(angle_var.get())
        speed = power_var.get()
        wind = getattr(prepare_shot, "wind", 0.0)

        # Clear old arrow parts
        if hasattr(shoot_arrow, "last_arrow_parts"):
            for part in shoot_arrow.last_arrow_parts:
                game_canvas.delete(part)

        vx = speed * math.cos(angle) + wind
        vy = -speed * math.sin(angle)

        def animate():
            x, y = 50, 260
            t = 0
            g = 9.8

            # Initial arrow components
            shaft = game_canvas.create_line(x, y, x - 10, y - 5, fill="black", width=3)
            head = game_canvas.create_polygon(
                x, y,
                x - 5, y - 3,
                x - 5, y + 3,
                fill="dimgray"
            )
            shoot_arrow.last_arrow_parts = [shaft, head]

            while y < 280 and x < 600:
                dx = vx * 0.1
                dy = vy * 0.1 + 0.5 * g * t**2 * 0.01
                x += dx
                y += dy
                game_canvas.coords(shaft, x, y, x - 10, y - 5)
                game_canvas.coords(head, x, y, x - 5, y - 3, x - 5, y + 3)
                game_canvas.update()
                time.sleep(0.02)
                t += 0.1

                if 550 <= x <= 570 and 240 <= y <= 260:
                    #messagebox.showinfo("🎯 Hit!", "Bullseye! You hit the apple!")
                    flash_apple()
                    messagebox.showinfo("🎯 Hit!", "Bullseye! You hit the apple!")
                    return

            messagebox.showinfo("😕 Miss", "Oops! The wind may have pushed your arrow off course.")

        threading.Thread(target=animate).start()
     
    # Init text-to-speech engine
    engine = pyttsx3.init()

    # --- GUI Setup ---
    #root = tk.Tk()
    #root.title("MindfullyMosaic Personal Organiser")
    ##root.geometry("800x500") # Some widgets didn't fit on the screen
    #root.geometry("900x600")

    style = ttk.Style()

    style.configure("Entry.TFrame", background="#f9f9f9")      # light gray
    style.configure("History.TFrame", background="#f0fff0")    # mint
    style.configure("Settings.TFrame", background="#f0f8ff")   # pale cyan
    style.configure("Dashboard.TFrame", background="#e6f7ff")  # soft blue
    style.configure("Budget.TFrame", background="#fff4e6")     # peach
    style.configure("Variance.TFrame", background="#e8f0fe")   # lavender blue
    style.configure("Tasks.TFrame", background="#e6f7ff")      # soft blue
    style.configure("Calendar.TFrame", background="#e6f7ff")   # soft bluesoft blue
    style.configure("Bill.TFrame", background="#FFDE21")       # pinkish
    style.configure("Meditation.TFrame", background="#e6f7ff") # soft bluesoft blue
    #style.configure("Reflection.TFrame", background="#f0fff0")# mint
    style.configure("Mood.TFrame", background="#fff4e6")       # peach
    style.configure("Game.TFrame", background="#e8f0fe")       # lavender blue

    ## === Load Full Name from DB ===
    #cursor.execute("SELECT full_name FROM users WHERE email_address = ?", (logged_in_email,))
    #row = cursor.fetchone()
    #full_name = row[0] if row else "User"
    #first_name = full_name.strip().split()[0]  # Extract first word only

    # === Load logged-in user from session file ===
    #try:
    #    with open("session_user.txt", "r") as f:
    #        logged_in_email = f.read().strip()
    #except FileNotFoundError:
    #    logged_in_email = None

    try:
        with open("session_user.txt", "r") as f:
            logged_in_email = f.read().strip()
    except FileNotFoundError:
        messagebox.showerror("Session Error", "No logged-in session found.\nPlease log in using the launcher first.")
        sys.exit()  # Or root.destroy() if you’ve already initialized Tkinter

    # === Connect to databases ===
    auth_conn = sqlite3.connect("user_login.db")
    auth_cursor = auth_conn.cursor()

    main_conn = sqlite3.connect("budget_data.db")
    main_cursor = main_conn.cursor()

    # === Get full name from user_login.db ===
    auth_cursor.execute("SELECT full_name FROM users WHERE email_address = ?", (logged_in_email,))
    row = auth_cursor.fetchone()
    full_name = row[0] if row else "User"
    first_name = full_name.strip().split()[0]

    ##user_name = "Chaminda"  # You can load this dynamically from DB in the future
    #greeting_text = f"{get_greeting()}, {first_name} 👋"
    #tk.Label(root, text=greeting_text, font=("Arial", 12, "bold"), fg="#004d99").pack(pady=5)

    # === Dynamic Greeting ===
    def get_greeting():
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning"
        elif hour < 18:
            return "Good afternoon"
        else:
            return "Good evening"

    greeting_text = f"{get_greeting()}, {first_name} 👋"
    #tk.Label(root, text=greeting_text, font=("Arial", 12, "bold"), fg="#004d99").pack(pady=5)

    session_info = f"Logged in as: {full_name} ({logged_in_email})"
    #tk.Label(root, text=session_info, font=("Arial", 9), fg="gray").pack(pady=(0, 10))

    # === Top Bar UI ===
    top_bar = tk.Frame(root, bg="#f0f8ff")
    top_bar.pack(fill="x")

    #tk.Label(top_bar, text=greeting_text, font=("Arial", 12, "bold"), fg="#004d99", bg="#f0f8ff").pack(side="left", padx=10)
    #tk.Label(top_bar, text=session_info, font=("Arial", 9), fg="gray", bg="#f0f8ff").pack(side="right", padx=10)

    greeting_label = tk.Label(top_bar, text=greeting_text, font=("Arial", 12, "bold"), fg="#004d99", bg="#f0f8ff")
    greeting_label.pack(side="left", padx=10)

    engine.say(f"{get_greeting()}, {first_name}. Welcome to MindfullyMosaic.")
    engine.runAndWait()

    session_label = tk.Label(top_bar, text=session_info, font=("Arial", 9), fg="gray", bg="#f0f8ff")
    session_label.pack(side="right", padx=10)

    # === Top Logout/Exit Buttons ===


    def exit_app():
        try:
            messagebox.showinfo("Goodbye", "MindfullyMosaic is shutting down.")  # 👋 Friendly popup
        except:
            pass  # Don't block exit if GUI is already shutting down

        try:
            engine.say("Goodbye. MindfullyMosaic is shutting down.")
            engine.runAndWait()
        except:
            pass

        try:
            pygame.mixer.quit()  # 🛑 Stop audio playback
        except:
            pass

        try:
            root.destroy()  # 🧹 Cleanly close all GUI elements
        except:
            pass

        os._exit(0)  # ⛔ Force full shutdown (especially if threads/audio loops exist)

    exit_frame = tk.Frame(root)
    exit_frame.pack(pady=5, fill="x", padx=10)  # ⬅️ Add this here for spacing

    tk.Button(
        exit_frame,
        text="🔒 Logout",
        command=logout_and_launch,
        fg="white",
        bg="#cc0000",
        font=("Segoe UI", 10, "bold"),
        width=12
    ).pack(side="left", padx=10)

    tk.Button(
        exit_frame,
        text="🚪 Exit App",
        command=exit_app,
        fg="white",
        bg="red",
        font=("Segoe UI", 10, "bold"),
        width=12
    ).pack(side="left", padx=10)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # === TAB 1 and 2: Actuals Entry + Ledger History ===
    tab_entry = ttk.Frame(notebook, style="Entry.TFrame")
    notebook.add(tab_entry, text="📥 Actuals Entry")

    # Layout frames for left entry, right video, and bottom ledger
    top_left = ttk.LabelFrame(tab_entry, text="Income and Expense Entry")
    top_left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    top_right = ttk.LabelFrame(tab_entry, text="Relaxing Background Video")
    top_right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    bottom_frame = ttk.LabelFrame(tab_entry, text="Ledger History")
    bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

    tab_entry.columnconfigure(0, weight=3)
    tab_entry.columnconfigure(1, weight=1)
    tab_entry.rowconfigure(1, weight=1)

    # === Actuals Entry Form ===
    tk.Label(top_left, text="Type").grid(row=0, column=0, sticky="e")
    tk.Label(top_left, text="Category").grid(row=1, column=0, sticky="e")
    tk.Label(top_left, text="Frequency").grid(row=2, column=0, sticky="e")
    tk.Label(top_left, text="Amount (£)").grid(row=3, column=0, sticky="e")
    tk.Label(top_left, text="Date").grid(row=4, column=0, sticky="e")
    tk.Label(top_left, text="Notes").grid(row=5, column=0, sticky="e")

    type_var = tk.StringVar(value="Income")
    category_var = tk.StringVar(value=categories_list[0])
    frequency_var = tk.StringVar(value=get_frequencies()[0])
    amount_var = tk.StringVar()
    date_var = tk.StringVar(value=datetime.today().strftime('%d/%m/%Y'))
    notes_var = tk.StringVar()

    tk.OptionMenu(top_left, type_var, "Income", "Expense").grid(row=0, column=1, sticky="w")
    tk.OptionMenu(top_left, category_var, *categories_list).grid(row=1, column=1, sticky="w")
    tk.OptionMenu(top_left, frequency_var, *get_frequencies()).grid(row=2, column=1, sticky="w")
    tk.Entry(top_left, textvariable=amount_var).grid(row=3, column=1, sticky="w")
    DateEntry(top_left, textvariable=date_var, date_pattern='dd/MM/yyyy').grid(row=4, column=1, sticky="w")
    tk.Entry(top_left, textvariable=notes_var).grid(row=5, column=1, sticky="w")

    tk.Button(top_left, text="Add Entry", command=add_entry).grid(row=6, column=0, pady=10)
    tk.Button(top_left, text="Speak Summary", command=speak_summary).grid(row=6, column=1, pady=10)

    # === Video Button ===
    tk.Button(
        top_right,
        text="📺 Watch: Nature's Rest by Tim Janis\nRelax as you manage finances",
        command=lambda: webbrowser.open("https://www.youtube.com/watch?v=ciSYYc6Pwos"),
        font=("Segoe UI", 12),
        fg="red",
        wraplength=200,
        justify="center",
        bg="#e0f7fa",
        relief="raised"
    ).pack(padx=10, pady=30)

    # === Ledger History Section ===
    filter_frame = ttk.LabelFrame(bottom_frame, text="Filter Options")
    filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    filter_type = tk.StringVar(value="All")
    filter_category = tk.StringVar(value="All")
    filter_start = tk.StringVar()
    filter_end = tk.StringVar()

    tk.Label(filter_frame, text="Type:").grid(row=0, column=0)
    tk.OptionMenu(filter_frame, filter_type, "All", "Income", "Expense").grid(row=0, column=1, padx=5)
    tk.Label(filter_frame, text="Category:").grid(row=0, column=2)
    tk.OptionMenu(filter_frame, filter_category, "All", *categories_list).grid(row=0, column=3, padx=5)
    tk.Label(filter_frame, text="Start Date:").grid(row=1, column=0)
    tk.Entry(filter_frame, textvariable=filter_start).grid(row=1, column=1, padx=5)
    tk.Label(filter_frame, text="End Date:").grid(row=1, column=2)
    tk.Entry(filter_frame, textvariable=filter_end).grid(row=1, column=3, padx=5)

    tk.Button(filter_frame, text="Apply Filters", command=lambda: load_history(apply_filters=True)).grid(row=2, column=1, pady=5)
    tk.Button(filter_frame, text="Export CSV", command=lambda: export_ledger("csv")).grid(row=2, column=2, pady=5)
    tk.Button(filter_frame, text="Export Excel", command=lambda: export_ledger("excel")).grid(row=2, column=3, pady=5)

    # Ledger Table
    columns = ("Type", "Category", "Frequency", "Amount", "Date", "Notes")
    tree = ttk.Treeview(bottom_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="w")

    scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=5)
    scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
    bottom_frame.rowconfigure(1, weight=1)
    bottom_frame.columnconfigure(0, weight=1)

    # === TAB 3: Settings ===
    #tab_settings = tk.Frame(notebook)
    tab_settings = ttk.Frame(notebook, style="Settings.TFrame")
    notebook.add(tab_settings, text="⚙️ Settings")

    tk.Label(tab_settings, text="Manage Expense Categories", font=('Arial', 10, 'bold')).grid(row=0, column=0, pady=10, sticky='w')
    cat_entry_var = tk.StringVar()
    tk.Entry(tab_settings, textvariable=cat_entry_var).grid(row=1, column=0, padx=5, sticky='w')
    tk.Button(tab_settings, text="Add Category", command=lambda: add_category(cat_entry_var.get())).grid(row=1, column=1, sticky='w')
    tk.Button(tab_settings, text="Delete Category", command=lambda: delete_category(cat_entry_var.get())).grid(row=1, column=2, sticky='w')

    tk.Label(tab_settings, text="Manage Frequencies", font=('Arial', 10, 'bold')).grid(row=2, column=0, pady=10, sticky='w')
    freq_entry_var = tk.StringVar()
    tk.Entry(tab_settings, textvariable=freq_entry_var).grid(row=3, column=0, padx=5, sticky='w')
    tk.Button(tab_settings, text="Add Frequency", command=lambda: add_frequency(freq_entry_var.get())).grid(row=3, column=1, sticky='w')
    tk.Button(tab_settings, text="Delete Frequency", command=lambda: delete_frequency(freq_entry_var.get())).grid(row=3, column=2, sticky='w')

    # === TAB 4: Dashboard ===
    #tab_dashboard = tk.Frame(notebook)
    tab_dashboard = ttk.Frame(notebook, style="Dashboard.TFrame")
    notebook.add(tab_dashboard, text="📊 Dashboard")

    tk.Button(tab_dashboard, text="Load Dashboard", command=lambda: draw_dashboard(tab_dashboard)).pack(pady=10)

    # === TAB 5: Budget Planner ===
    #tab_budget = tk.Frame(notebook)
    tab_budget = ttk.Frame(notebook, style="Budget.TFrame")
    notebook.add(tab_budget, text="✨ Budget Planner")

    load_budget_summary()

    tk.Label(tab_budget, text="Type").grid(row=0, column=0, sticky="e")
    tk.Label(tab_budget, text="Category").grid(row=1, column=0, sticky="e")
    tk.Label(tab_budget, text="Frequency").grid(row=2, column=0, sticky="e")
    tk.Label(tab_budget, text="Amount (£)").grid(row=3, column=0, sticky="e")
    tk.Label(tab_budget, text="Start Date").grid(row=4, column=0, sticky="e")
    tk.Label(tab_budget, text="Notes").grid(row=5, column=0, sticky="e")

    budget_type = tk.StringVar(value="Expense")
    budget_category = tk.StringVar(value=categories_list[0])
    budget_frequency = tk.StringVar(value=get_frequencies()[0])
    budget_amount = tk.StringVar()
    budget_date = tk.StringVar(value=datetime.today().strftime('%d/%m/%Y'))
    budget_notes = tk.StringVar()

    tk.OptionMenu(tab_budget, budget_type, "Income", "Expense").grid(row=0, column=1)
    tk.OptionMenu(tab_budget, budget_category, *categories_list).grid(row=1, column=1)
    tk.OptionMenu(tab_budget, budget_frequency, *get_frequencies()).grid(row=2, column=1)
    tk.Entry(tab_budget, textvariable=budget_amount).grid(row=3, column=1)
    DateEntry(tab_budget, textvariable=budget_date, date_pattern='dd/MM/yyyy').grid(row=4, column=1)
    tk.Entry(tab_budget, textvariable=budget_notes).grid(row=5, column=1)

    tk.Button(tab_budget, text="Add/Replace Budget", command=lambda: save_budget()).grid(row=6, column=1, pady=10)
    tk.Button(tab_budget, text="Speak Budget Summary", command=lambda: speak_budget_summary()).grid(row=6, column=2, pady=10)

    # === TAB 6: Variance Report ===
    #tab_variance = tk.Frame(notebook)
    tab_variance = ttk.Frame(notebook, style="Variance.TFrame")
    notebook.add(tab_variance, text="🖥️ Variance Report")

    tk.Label(tab_variance, text="Variance Report (Budget vs Actual)", font=("Arial", 12, "bold")).pack(pady=5)

    # Year selector frame
    year_selector = tk.Frame(tab_variance)
    year_selector.pack(pady=5)

    tk.Label(year_selector, text="Select Year:").pack(side="left", padx=(0, 5))

    year_var = tk.StringVar()
    year_dropdown = ttk.Combobox(year_selector, textvariable=year_var, state="readonly", width=15)
    year_dropdown.pack(side="left")

    # Populate year dropdown from DB
    cursor.execute("SELECT DISTINCT year FROM budget_targets ORDER BY year DESC")
    years = [row[0] for row in cursor.fetchall()]
    if years:
        year_var.set(years[0])
        year_dropdown["values"] = years

    # Bind dropdown to refresh report when year changes
    year_dropdown.bind("<<ComboboxSelected>>", lambda e: render_variance_table(tab_variance))

    # Refresh button
    tk.Button(tab_variance, text="Refresh Report", command=lambda: render_variance_table(tab_variance)).pack(pady=5)

    # Load variance data immediately
    render_variance_table(tab_variance)

    export_frame = tk.Frame(tab_variance)
    export_frame.pack(pady=5)

    tk.Label(export_frame, text="Export Report:").pack(side="left", padx=(0, 5))
    tk.Button(export_frame, text="CSV", command=lambda: export_variance_report("csv")).pack(side="left", padx=5)
    tk.Button(export_frame, text="Excel", command=lambda: export_variance_report("excel")).pack(side="left", padx=5)

    def show_variance_summary():
        summary = generate_variance_summary()
        top = tk.Toplevel()
        top.title("Variance Summary")
        tk.Label(top, text="Plain-English Summary", font=("Arial", 12, "bold")).pack(pady=10)
        text = tk.Text(top, wrap="word", width=70, height=15)
        text.insert("1.0", summary)
        text.config(state="disabled")
        text.pack(padx=10, pady=5)
        tk.Button(top, text="Close", command=top.destroy).pack(pady=5)

    tk.Button(tab_variance, text="📋 View Summary", command=show_variance_summary).pack(pady=10)

    def show_monthly_report_prompt():
        top = tk.Toplevel()
        top.title("Monthly Report Generator")

        tk.Label(top, text="Enter Month & Year (e.g. July 2025):").pack(pady=5)
        month_input = tk.StringVar()
        tk.Entry(top, textvariable=month_input, width=25).pack(pady=5)

        def generate_and_display():
            summary = generate_monthly_report(month_input.get())
            report = tk.Toplevel()
            report.title("Monthly Budget Report")
            tk.Label(report, text="Monthly Summary", font=("Arial", 12, "bold")).pack(pady=10)
            text = tk.Text(report, wrap="word", width=70, height=20)
            text.insert("1.0", summary)
            text.config(state="disabled")
            text.pack(padx=10, pady=5)
            
            tk.Button(report, text="Export to PDF", command=lambda: export_monthly_report_to_pdf(month_input.get())).pack(pady=5)
        tk.Button(top, text="Generate Report", command=generate_and_display).pack(pady=5)
        
    tk.Button(tab_variance, text="🗓️ Monthly Report", command=show_monthly_report_prompt).pack(pady=5)

    # print("=== Variance Preview ===")
    # print(build_variance_data())

    # === TAB 7: Time Manager ===
    #tab_tasks = tk.Frame(notebook)
    tab_tasks = ttk.Frame(notebook, style="Tasks.TFrame")
    notebook.add(tab_tasks, text="🧭 Time Manager")

    # Create the Calendar View tab
    #tab_calendar = tk.Frame(notebook)
    tab_calendar = ttk.Frame(notebook, style="Calendar.TFrame")
    notebook.add(tab_calendar, text="📅 Calendar View")

    #calendar = Calendar(tab_calendar, selectmode="day", date_pattern="dd/MM/yyyy") # Looks bland and black and white
    calendar = Calendar(
        tab_calendar,
        selectmode="day",
        date_pattern="dd/MM/yyyy",
        font=("Arial", 12),              # ⬅️ Increase font size
        background="white",              # Background colour (optional)
        foreground="black",              # Day text colour
        headersbackground="#f0f0ff",     # Month header background
        headersforeground="blue",        # Day-of-week labels
        selectbackground="#007fff",      # Selected date color
        weekendbackground="#f9f9f9",     # Sunday/Saturday
        normalbackground="white",
        weekendforeground="grey"
    )
    #calendar.pack(pady=10)# Too small
    calendar.pack(pady=10, expand=True, fill="both")
    highlight_calendar_events()

    filter_frame = tk.Frame(tab_tasks)
    filter_frame.pack(pady=5)

    tk.Label(filter_frame, text="View:").pack(side="left", padx=5)

    task_filter = tk.StringVar(value="All")
    #tk.OptionMenu(filter_frame, task_filter, "All", "Today", "Overdue", "Incomplete", command=lambda _: load_tasks()).pack(side="left")
    tk.OptionMenu(filter_frame, task_filter, "All", "Today", "Overdue", "Incomplete", "Next 7 Days", command=lambda _: load_tasks()).pack(side="left")

    task_count_label = tk.Label(tab_tasks, text="", font=("Arial", 10))
    task_count_label.pack()

    tk.Label(tab_tasks, text="Add Task", font=("Arial", 12, "bold")).pack(pady=5)

    task_frame = tk.Frame(tab_tasks)
    task_frame.pack(pady=5)

    tk.Label(task_frame, text="Title:").grid(row=0, column=0, sticky="e")
    tk.Label(task_frame, text="Description:").grid(row=1, column=0, sticky="e")
    tk.Label(task_frame, text="Due Date:").grid(row=2, column=0, sticky="e")

    #tk.Label(task_frame, text="Reminder Time (HH:MM):").grid(row=3, column=0, sticky="e")

    tk.Label(task_frame, text="Reminder Time (HH:MM):").grid(row=3, column=0, sticky="e")
    task_reminder = tk.StringVar()
    tk.Entry(task_frame, textvariable=task_reminder, width=10).grid(row=3, column=1, sticky="w", padx=5)

    task_title = tk.StringVar()
    task_desc = tk.StringVar()
    task_due = tk.StringVar(value=datetime.today().strftime('%d/%m/%Y'))

    tk.Entry(task_frame, textvariable=task_title, width=30).grid(row=0, column=1, padx=5)
    tk.Entry(task_frame, textvariable=task_desc, width=30).grid(row=1, column=1, padx=5)
    DateEntry(task_frame, textvariable=task_due, date_pattern='dd/MM/yyyy').grid(row=2, column=1, padx=5)

    tk.Label(task_frame, text="Repeat:").grid(row=4, column=0, sticky="e")
    task_recurrence = tk.StringVar(value="None")
    tk.OptionMenu(task_frame, task_recurrence, "None", "Daily", "Weekly", "Monthly").grid(row=4, column=1, sticky="w", padx=5)

    #tk.Button(task_frame, text="Add Task", command=lambda: add_task()).grid(row=5, column=1, pady=10) # Duplicate

    # task_tree = ttk.Treeview(tab_tasks, columns=("Title", "Description", "Due"), show="headings", height=8)
    #task_tree = ttk.Treeview(tab_tasks, columns=("ID", "Title", "Description", "Due"), show="headings", height=8)
    task_tree = ttk.Treeview(tab_tasks, columns=("ID", "Title", "Description", "Due", "Reminder", "Recurrence"), show="headings", height=8)
    task_tree["displaycolumns"] = ("Title", "Description", "Due", "Reminder", "Recurrence")
    task_tree.tag_configure("completed", background="#d0f0d0")
    task_tree.tag_configure("overdue", background="#ffe6e6")  # Soft red
    task_tree.tag_configure("upcoming", background="#e6f7ff")  # Soft blue

    for col in ("Title", "Description", "Due", "Reminder", "Recurrence"):# 
        task_tree.heading(col, text=col)
        task_tree.column(col, width=200)
    task_tree.pack(pady=5, fill="both", expand=True)
    # task_tree["displaycolumns"] = ("Title", "Description", "Due")  # Hides ID from visual
    load_tasks() # Load tasks immediately

    def check_today_tasks():
        today = datetime.today().strftime('%d/%m/%Y')
        cursor.execute("SELECT title FROM tasks WHERE due_date = ?", (today,))
        tasks = [row[0] for row in cursor.fetchall()]
        if tasks:
            msg = f" You have {len(tasks)} task(s) due today:\n\n" + "\n".join(f"– {t}" for t in tasks)
            messagebox.showinfo("Today's Tasks", msg)
            for t in tasks:
                engine.say(f"Reminder: {t} is due today.")
            engine.runAndWait()

    root.after(1500, check_today_tasks)

    def check_due_reminders():
        now = datetime.now().strftime("%H:%M")
        today = datetime.today().strftime("%d/%m/%Y")

        cursor.execute("SELECT title, reminder_time FROM tasks WHERE due_date = ?", (today,))
        for title, reminder in cursor.fetchall():
            if reminder and reminder <= now:
                engine.say(f"Reminder: {title} is due now.")
                engine.runAndWait()
                messagebox.showinfo("Task Reminder", f" {title} is due now.")
                
    def mark_task_complete():
        selected = task_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a task to mark as complete.")
            return

        task_id = task_tree.item(selected)["values"][0]

        cursor.execute("UPDATE tasks SET is_completed = 1 WHERE id=?", (task_id,))
        conn.commit()
        load_tasks()

    def toggle_task_completion():
        selected = task_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a task to toggle completion.")
            return

        values = task_tree.item(selected, "values")
        task_id = values[0]

        # Get current completion status
        cursor.execute("SELECT is_completed FROM tasks WHERE id=?", (task_id,))
        current = cursor.fetchone()
        if not current:
            messagebox.showerror("Error", "Task not found.")
            return

        new_status = 0 if current[0] == 1 else 1

        cursor.execute("UPDATE tasks SET is_completed = ? WHERE id=?", (new_status, task_id))
        conn.commit()
        load_tasks()

    def export_tasks_to_csv():
        from tkinter import filedialog
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export Tasks"
        )
        if not file:
            return

        try:
            df = pd.read_sql_query(
                "SELECT title, description, due_date, reminder_time, recurrence, is_completed FROM tasks ORDER BY due_date ASC",
                conn
            )
            df["is_completed"] = df["is_completed"].map({0: "No", 1: "Yes"})
            df.to_csv(file, index=False)
            messagebox.showinfo("Export Successful", f"Tasks exported to:\n{file}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
            
    def import_tasks_from_csv():
        from tkinter import filedialog
        file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")], title="Import Tasks")
        if not file:
            return

        try:
            df = pd.read_csv(file)

            for _, row in df.iterrows():
                # Default to 0 if is_completed column is missing
                is_completed = row.get("is_completed", "No")
                is_completed = 1 if str(is_completed).lower() == "yes" else 0

                cursor.execute("""
                    INSERT INTO tasks (title, description, due_date, reminder_time, recurrence, is_completed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row.get("title", ""),
                    row.get("description", ""),
                    row.get("due_date", ""),
                    row.get("reminder_time", ""),
                    row.get("recurrence", "None"),
                    is_completed
                ))

            conn.commit()
            load_tasks()
            messagebox.showinfo("Import Successful", f"Tasks imported from:\n{file}")

        except Exception as e:
            messagebox.showerror("Import Failed", str(e))

    tk.Button(tab_tasks, text="✅ Mark as Complete", command=mark_task_complete).pack(pady=5)
    tk.Button(tab_tasks, text="🔄 Toggle Complete", command=toggle_task_completion).pack(pady=5)

    #check_today_tasks()

    tk.Button(tab_tasks, text="🗑️ Delete Selected Task", command=delete_task).pack(pady=5)
    tk.Button(tab_tasks, text="✏️ Edit Selected Task", command=edit_task).pack(pady=5)
    task_button = tk.Button(task_frame, text="Add Task", command=add_task)
    task_button.grid(row=5, column=1, pady=10)

    tk.Button(tab_tasks, text="📤 Export Tasks to CSV", command=export_tasks_to_csv).pack(pady=5)

    tk.Button(tab_tasks, text="📥 Import Tasks from CSV", command=import_tasks_from_csv).pack(pady=5)

    task_listbox = tk.Listbox(tab_calendar, width=60, height=10)
    task_listbox.pack(pady=5)

    #def show_tasks_for_day(event=None):
    #    selected = calendar.get_date()
    #    task_listbox.delete(0, tk.END)
    #    cursor.execute("SELECT title, description FROM tasks WHERE due_date = ?", (selected,))
    #    rows = cursor.fetchall()
    #    if rows:
    #        for title, desc in rows:
    #            task_listbox.insert(tk.END, f"• {title} — {desc}")
    #    else:
    #        task_listbox.insert(tk.END, "No tasks for this date.")

    def show_tasks_for_day(event=None):
        selected = calendar.get_date()
        task_listbox.delete(0, tk.END)

        # === Show Tasks ===
        cursor.execute("SELECT title, description FROM tasks WHERE due_date = ?", (selected,))
        task_rows = cursor.fetchall()
        if task_rows:
            task_listbox.insert(tk.END, "🧭 Tasks:")
            for title, desc in task_rows:
                task_listbox.insert(tk.END, f"• {title} — {desc if desc else 'No details'}")
        else:
            task_listbox.insert(tk.END, "🧭 No tasks for this date.")

        # === Show Bills ===
        cursor.execute("SELECT payee, amount, is_paid FROM bills WHERE due_date = ?", (selected,))
        bill_rows = cursor.fetchall()
        if bill_rows:
            task_listbox.insert(tk.END, "")
            task_listbox.insert(tk.END, "💰 Bills:")
            for payee, amount, is_paid in bill_rows:
                status = "✓ Paid" if is_paid else "❌ Unpaid"
                task_listbox.insert(tk.END, f"• {payee} — £{amount:,.2f} ({status})")
        else:
            task_listbox.insert(tk.END, "")
            task_listbox.insert(tk.END, "💰 No bills for this date.")

    calendar.bind("<<CalendarSelected>>", show_tasks_for_day)

    #def run_reminder_loop():
    #    check_due_reminders()
    #    root.after(60000, run_reminder_loop)  # Check every minute
    #    generate_next_bills()  # 🔁 create new recurring bills

    #run_reminder_loop()

    # === TAB 8: Bill Manager ===
    #tab_bills = tk.Frame(notebook)
    tab_bills = ttk.Frame(notebook, style="Bill.TFrame")
    notebook.add(tab_bills, text="📘 Bill Manager")

    # Filter Panel
    filter_frame = tk.Frame(tab_bills)
    filter_frame.pack(pady=5)

    tk.Label(filter_frame, text="Filter:").pack(side="left", padx=5)
    bill_filter_option = tk.StringVar(value="All")
    tk.OptionMenu(
        filter_frame,
        bill_filter_option,
        "All",
        "Unpaid Only",
        "Due Today",
        "Due This Week",
        command=lambda _: load_bills()
    ).pack(side="left", padx=5)

    tk.Label(filter_frame, text="Category:").pack(side="left", padx=5)
    bill_category_filter = tk.StringVar(value="All")
    categories = ["All"] + categories_list
    tk.OptionMenu(
        filter_frame,
        bill_category_filter,
        *categories,
        command=lambda _: load_bills()
    ).pack(side="left", padx=5)

    # Form to Add/Edit Bill
    tk.Label(tab_bills, text="Add Bill", font=("Arial", 12, "bold")).pack(pady=5)
    bill_form = tk.Frame(tab_bills)
    bill_form.pack(pady=5)

    # Bill Table
    bill_tree = ttk.Treeview(tab_bills, columns=("ID", "Payee", "Category", "Amount", "Due", "Reminder", "Recurrence"), show="headings")
    bill_tree["displaycolumns"] = ("Payee", "Category", "Amount", "Due", "Reminder", "Recurrence")

    for col in ("Payee", "Category", "Amount", "Due", "Reminder", "Recurrence"):
        bill_tree.heading(col, text=col)
        bill_tree.column(col, width=150)

    bill_tree.pack(pady=5, fill="both", expand=True)

    tk.Label(bill_form, text="Payee:").grid(row=0, column=0, sticky="e")
    tk.Label(bill_form, text="Amount (£):").grid(row=1, column=0, sticky="e")
    tk.Label(bill_form, text="Due Date:").grid(row=2, column=0, sticky="e")
    tk.Label(bill_form, text="Reminder Time (HH:MM):").grid(row=3, column=0, sticky="e")
    tk.Label(bill_form, text="Repeat:").grid(row=4, column=0, sticky="e")
    tk.Label(bill_form, text="Category:").grid(row=5, column=0, sticky="e")

    bill_payee = tk.StringVar()
    bill_amount = tk.StringVar()
    bill_due = tk.StringVar(value=datetime.today().strftime('%d/%m/%Y'))
    bill_reminder = tk.StringVar()
    bill_recurrence = tk.StringVar(value="None")
    bill_category = tk.StringVar()
    bill_category.set(categories_list[0])

    tk.Entry(bill_form, textvariable=bill_payee, width=30).grid(row=0, column=1, padx=5)
    tk.Entry(bill_form, textvariable=bill_amount, width=15).grid(row=1, column=1, padx=5)
    DateEntry(bill_form, textvariable=bill_due, date_pattern="dd/MM/yyyy").grid(row=2, column=1, padx=5)
    tk.Entry(bill_form, textvariable=bill_reminder, width=10).grid(row=3, column=1, sticky="w", padx=5)
    tk.OptionMenu(bill_form, bill_recurrence, "None", "Monthly", "Quarterly", "Yearly").grid(row=4, column=1, sticky="w", padx=5)
    tk.OptionMenu(bill_form, bill_category, *categories_list).grid(row=5, column=1, sticky="w", padx=5)

    def toggle_bill_paid():
        selected = bill_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a bill to toggle paid status.")
            return

        bill_id = bill_tree.item(selected)["values"][0]

        cursor.execute("SELECT is_paid FROM bills WHERE id=?", (bill_id,))
        current = cursor.fetchone()
        if not current:
            messagebox.showerror("Error", "Bill not found.")
            return

        new_status = 0 if current[0] == 1 else 1
        cursor.execute("UPDATE bills SET is_paid = ? WHERE id = ?", (new_status, bill_id))
        conn.commit()
        load_bills()

    bill_filter_option.set("All")
    bill_category_filter.set("All")
    load_bills()

    # Add Button
    add_bill_button = tk.Button(bill_form, text="Add Bill", command=add_bill)
    add_bill_button.grid(row=5, column=2, pady=10)

    # Action Buttons
    tk.Button(tab_bills, text="✅ Toggle Paid", command=toggle_bill_paid).pack(pady=5)
    tk.Button(tab_bills, text="✏️ Edit Selected Bill", command=edit_bill).pack(pady=5)
    tk.Button(tab_bills, text="📤 Export Bills to CSV", command=export_bills_to_csv).pack(pady=5)
    tk.Button(tab_bills, text="🗑️ Delete Selected Bill", command=delete_bill).pack(pady=5)
    tk.Button(tab_bills, text="📋 View Bill Summary", command=show_bill_summary).pack(pady=5)
    tk.Button(tab_bills, text="📆 Forecast (30 Days)", command=generate_bill_forecast).pack(pady=5)
    tk.Button(tab_bills, text="📊 Bills by Category", command=show_bills_by_category_chart).pack(pady=5)

    def run_reminder_loop():
        check_due_reminders()  # existing task reminders
        check_due_bills()      # 👈 new bill reminders
        root.after(60000, run_reminder_loop)  # recheck every minute
        
    run_reminder_loop()

    # === TAB 10: Mindful Meditation ===
    #tab_meditation = tk.Frame(notebook)
    tab_meditation = ttk.Frame(notebook, style="Meditation.TFrame")
    notebook.add(tab_meditation, text="🧘 Mindful Meditation")

    tab_journal = tk.Frame(notebook)
    notebook.add(tab_journal, text="📝 Reflection Journal")

    # Meditation Type Selector
    tk.Label(tab_meditation, text="Choose Your Practice", font=("Arial", 12, "bold")).pack(pady=5)
    tk.Label(tab_meditation, text="Meditation Type:").pack()
    meditation_type = tk.StringVar(value="Guided Breathing")
    tk.OptionMenu(tab_meditation, meditation_type, 
                  "Guided Breathing", 
                  "Loving Kindness", 
                  "Body Scan", 
                  "Zen (Silent Sitting)").pack(pady=5)

    tk.Label(tab_meditation, text="Ambient Sound:").pack()
    soundscape_var = tk.StringVar(value="None")
    tk.OptionMenu(tab_meditation, soundscape_var, "None", "Rain", "Stream", "Bowls", "Forest").pack(pady=5)

    # Duration Selector
    tk.Label(tab_meditation, text="Duration (minutes):").pack()
    duration_var = tk.IntVar(value=10)
    tk.Spinbox(tab_meditation, from_=5, to=30, increment=5, textvariable=duration_var, width=5).pack(pady=5)

    def play_background(path):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)  # Loop forever
        except Exception as e:
            print("🎵 Ambient sound error:", e)

    def stop_background():
        pygame.mixer.music.stop()

    # Start Session Button
    tk.Button(tab_meditation, text="🕯️ Begin Session", font=("Arial", 10, "bold"), command=lambda: start_meditation_session(
        meditation_type.get(), duration_var.get())
    ).pack(pady=10)

    # Pause / Resume and Cancel Controls
    def toggle_pause():
        global is_paused
        is_paused = not is_paused
        state = "paused" if is_paused else "resumed"
        print(f"⏸️ Session {state}")

        def speak_pause():
            local_engine = pyttsx3.init()
            local_engine.say(f"Session {state}")
            local_engine.runAndWait()

        threading.Thread(target=speak_pause).start()

    def cancel_session():
        global stop_session
        stop_session = True
        print("❌ Session cancelled")

    button_row = tk.Frame(tab_meditation)
    button_row.pack(pady=5)
    tk.Button(button_row, text="⏸ Pause / Resume", command=toggle_pause).pack(side="left", padx=10)
    tk.Button(button_row, text="❌ Cancel", command=cancel_session).pack(side="left", padx=10)

    # === Reflection Journal Viewer ===
    def load_journal():
        for row in journal_tree.get_children():
            journal_tree.delete(row)
        try:
            with open("meditation_journal.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header if present
                for row in reader:
                    if len(row) >= 4:
                        journal_tree.insert("", "end", values=row[:4])
        except FileNotFoundError:
            messagebox.showinfo("No Entries", "No journal entries yet.")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    tk.Label(tab_journal, text="Reflection History", font=("Arial", 12, "bold")).pack(pady=5)

    columns = ["Date/Time", "Type", "Mood", "Reflection"]
    journal_tree = ttk.Treeview(tab_journal, columns=columns, show="headings", height=12)
    for col in columns:
        journal_tree.heading(col, text=col)
        journal_tree.column(col, width=150, anchor="center")
    journal_tree.pack(padx=10, pady=5, fill="both", expand=True)

    #tab_mood = tk.Frame(notebook)
    tab_mood = ttk.Frame(notebook, style="Mood.TFrame")
    notebook.add(tab_mood, text="📈 Mood Trends")

    def plot_mood_trends():
        try:
            # Load CSV with mood data
            df = pd.read_csv("meditation_journal.csv", names=["Timestamp", "Type", "Mood", "Reflection"], header=0)
            df["Date"] = pd.to_datetime(df["Timestamp"]).dt.date

            # Count mood entries per day
            mood_counts = df.groupby(["Date", "Mood"]).size().unstack(fill_value=0)

            # Clear previous plot
            for widget in mood_canvas_frame.winfo_children():
                widget.destroy()

            # Create figure and axis
            fig, ax = plt.subplots(figsize=(7, 4))

            # Plot stacked bar chart
            mood_counts.plot(
                kind="bar",
                stacked=True,
                ax=ax,
                colormap="Pastel1",
                width=0.65
            )

            ax.set_title("Mood Trends Over Time", fontsize=12)
            ax.set_xlabel("Date", fontsize=10)
            ax.set_ylabel("Mood Count", fontsize=10)
            ax.tick_params(axis='x', labelrotation=45, labelsize=8)
            ax.legend(title="Mood", bbox_to_anchor=(1.02, 1), loc="upper left")

            fig.tight_layout()

            # Embed chart in Tkinter frame
            canvas = FigureCanvasTkAgg(fig, master=mood_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except FileNotFoundError:
            messagebox.showinfo("No Data", "No journal entries found.")
        except Exception as e:
            messagebox.showerror("Plot Error", str(e))

    tk.Label(tab_mood, text="Your Mood Journey", font=("Arial", 12, "bold")).pack(pady=5)
    tk.Button(tab_mood, text="📊 Generate Mood Chart", command=plot_mood_trends).pack(pady=5)

    mood_canvas_frame = tk.Frame(tab_mood)
    mood_canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Button(tab_journal, text="🔄 Refresh", command=load_journal).pack(pady=5)
    load_journal()

    # === TAB 11: Apple Shooter mini-game ===
    #tab_game = tk.Frame(notebook)
    tab_game = ttk.Frame(notebook, style="Game.TFrame")
    notebook.add(tab_game, text="🎯 Apple Shooter")

    # Angle and Power Input
    tk.Label(tab_game, text="Angle (degrees):").pack()
    angle_var = tk.DoubleVar(value=45)
    tk.Spinbox(tab_game, from_=10, to=80, increment=1, textvariable=angle_var, width=5).pack()

    tk.Label(tab_game, text="Power:").pack()
    power_var = tk.DoubleVar(value=50)
    tk.Spinbox(tab_game, from_=10, to=100, increment=5, textvariable=power_var, width=5).pack()

    wind_label = tk.Label(tab_game, text="Wind: +0.0 ➡️", font=("Arial", 10, "italic"))
    wind_label.pack()

    # Draw stick-figure archer
    def draw_archer():
        # Head
        game_canvas.create_oval(35, 240, 45, 250, fill="peachpuff", outline="black")
        
        # Body
        game_canvas.create_line(40, 250, 40, 270, width=2)

        # Arms (holding bow)
        game_canvas.create_line(30, 255, 50, 255, width=2)

        # Legs
        game_canvas.create_line(40, 270, 35, 285, width=2)  # left leg
        game_canvas.create_line(40, 270, 45, 285, width=2)  # right leg

        # Bow (optional – a simple curved line)
        game_canvas.create_arc(45, 245, 65, 265, start=90, extent=180, style="arc", outline="saddlebrown", width=2)

    # Canvas for the game
    # Make bg_image persistent to prevent garbage collection
    bg_image = tk.PhotoImage(file="images/background.png")  # Load image only once

    # Draw game canvas and background
    game_canvas = tk.Canvas(tab_game, width=600, height=300, bg="skyblue")
    game_canvas.pack(pady=10)
    game_canvas.create_image(0, 0, anchor="nw", image=bg_image)

    draw_archer()

    # Draw ground and apple target
    ground = game_canvas.create_rectangle(0, 280, 600, 300, fill="green")

    # Apple with red fill and shiny highlight
    apple = game_canvas.create_oval(550, 240, 570, 260, fill="red", outline="darkred")
    shine = game_canvas.create_oval(565, 245, 568, 248, fill="white", outline="white")

    # Buttons to interact with the game
    tk.Button(tab_game, text="🎯 Prepare Shot", command=prepare_shot).pack()
    tk.Button(tab_game, text="🏹 Shoot Arrow", command=shoot_arrow).pack(pady=5)

    # === TAB 11: Profile Settings ===
    tab_profile = ttk.Frame(notebook)
    notebook.add(tab_profile, text="👤 Profile Settings")

    tk.Label(tab_profile, text="Edit Your Profile", font=("Arial", 12, "bold")).pack(pady=10)

    # === Load Current Values ===
    auth_cursor.execute("SELECT full_name, email_address FROM users WHERE email_address = ?", (logged_in_email,))
    row = auth_cursor.fetchone()
    full_name_str = row[0] if row else ""
    email_str = row[1] if row else ""

    edit_name = tk.StringVar(value=full_name_str)
    edit_email = tk.StringVar(value=email_str)
    edit_password = tk.StringVar()

    tk.Label(tab_profile, text="Full Name").pack()
    tk.Entry(tab_profile, textvariable=edit_name, width=40).pack()

    tk.Label(tab_profile, text="Email Address").pack()
    tk.Entry(tab_profile, textvariable=edit_email, width=40).pack()

    tk.Label(tab_profile, text="New Password").pack()
    tk.Entry(tab_profile, textvariable=edit_password, show="*", width=40).pack()

    # === Update Logic ===
    def save_profile_edits():
        new_name = edit_name.get().strip()
        new_email = edit_email.get().strip()
        new_password = edit_password.get().strip()

        if not new_name or not new_email:
            messagebox.showerror("Missing Info", "Full name and email are required.")
            return

        try:
            if new_password:
                import bcrypt
                hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                auth_cursor.execute("""
                    UPDATE users SET full_name = ?, email_address = ?, hashed_password = ?
                    WHERE email_address = ?
                """, (new_name, new_email, hashed_pw, logged_in_email))
            else:
                auth_cursor.execute("""
                    UPDATE users SET full_name = ?, email_address = ?
                    WHERE email_address = ?
                """, (new_name, new_email, logged_in_email))

            auth_conn.commit()
            messagebox.showinfo("Success", "Profile updated!")
            # ✅ Refresh greeting and session display
            new_first_name = new_name.strip().split()[0]
            greeting_label.config(text=f"{get_greeting()}, {new_first_name} 👋")
            session_label.config(text=f"Logged in as: {new_name} ({new_email})")
            engine.say(f"Hello again, {new_first_name}. Your profile has been updated.")
            engine.runAndWait()
        except Exception as e:
            messagebox.showerror("Update Failed", str(e))

    tk.Button(tab_profile, text="💾 Save Changes", command=save_profile_edits).pack(pady=10)

    # Start the main event loop
    root.mainloop()
    
except Exception as e:
    log_crash_info(e)
    mb.showerror("Unexpected Error", "The app encountered a problem and will now close.\nSee error_report.txt for details.")