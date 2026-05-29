import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from tkcalendar import DateEntry

DB = "mess.db"

def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS Meals (meal_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, meal_taken TEXT, FOREIGN KEY(user_id) REFERENCES Users(user_id))")
    cur.execute("CREATE TABLE IF NOT EXISTS Payments (payment_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, status TEXT, FOREIGN KEY(user_id) REFERENCES Users(user_id))")
    con.commit(); con.close()

def refresh():
    for row in tree.get_children():
        tree.delete(row)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT u.user_id, u.name, m.date, m.meal_taken, p.status FROM Users u JOIN Meals m ON u.user_id = m.user_id JOIN Payments p ON u.user_id = p.user_id")
    for row in cur.fetchall():
        tree.insert("", tk.END, values=row)
    con.close()

def search():
    q = e_search.get().strip()
    if not q:
        refresh(); return
    for row in tree.get_children():
        tree.delete(row)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT u.user_id, u.name, m.date, m.meal_taken, p.status FROM Users u JOIN Meals m ON u.user_id = m.user_id JOIN Payments p ON u.user_id = p.user_id WHERE u.name LIKE ?", (f"%{q}%",))
    for row in cur.fetchall():
        tree.insert("", tk.END, values=row)
    con.close()

def add():
    name = e_name.get().strip()
    date = cal_date.get_date().strftime("%Y-%m-%d")
    meal = meal_var.get()
    pay  = pay_var.get()
    if not name:
        messagebox.showerror("Error", "Name is required"); return
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("INSERT INTO Users (name) VALUES (?)", (name,))
    uid = cur.lastrowid
    cur.execute("INSERT INTO Meals (user_id, date, meal_taken) VALUES (?, ?, ?)", (uid, date, meal))
    cur.execute("INSERT INTO Payments (user_id, date, status) VALUES (?, ?, ?)", (uid, date, pay))
    con.commit(); con.close(); refresh()

def delete():
    selected = tree.focus()
    if not selected:
        messagebox.showerror("Error", "Select a record to delete"); return
    uid = tree.item(selected)["values"][0]
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("DELETE FROM Meals WHERE user_id = ?", (uid,))
    cur.execute("DELETE FROM Payments WHERE user_id = ?", (uid,))
    cur.execute("DELETE FROM Users WHERE user_id = ?", (uid,))
    cur.execute("SELECT COUNT(*) FROM Users")
    if cur.fetchone()[0] == 0:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='Users'")
    con.commit(); con.close(); refresh()

def update():
    selected = tree.focus()
    if not selected:
        messagebox.showerror("Error", "Select a record to update"); return
    uid  = tree.item(selected)["values"][0]
    name = e_name.get().strip()
    date = cal_date.get_date().strftime("%Y-%m-%d")
    meal = meal_var.get()
    pay  = pay_var.get()
    if not name:
        messagebox.showerror("Error", "Name is required"); return
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("UPDATE Users SET name = ? WHERE user_id = ?", (name, uid))
    cur.execute("UPDATE Meals SET date = ?, meal_taken = ? WHERE user_id = ?", (date, meal, uid))
    cur.execute("UPDATE Payments SET date = ?, status = ? WHERE user_id = ?", (date, pay, uid))
    con.commit(); con.close(); refresh()

def on_select(event):
    selected = tree.focus()
    if not selected: return
    vals = tree.item(selected)["values"]
    e_name.delete(0, tk.END)
    e_name.insert(0, vals[1])
    try:
        from datetime import datetime
        cal_date.set_date(datetime.strptime(str(vals[2]), "%Y-%m-%d").date())
    except Exception:
        pass
    meal_var.set(vals[3])
    pay_var.set(vals[4])

root = tk.Tk()
root.title("Mess Management System")
root.geometry("720x500")

frame_top = tk.Frame(root)
frame_top.pack(pady=8)

tk.Label(frame_top, text="Name:").grid(row=0, column=0, padx=4, pady=4, sticky="e")
e_name = tk.Entry(frame_top, width=18)
e_name.grid(row=0, column=1, padx=4)

tk.Label(frame_top, text="Date:").grid(row=0, column=2, padx=4, sticky="e")
cal_date = DateEntry(frame_top, width=13, date_pattern="yyyy-mm-dd")
cal_date.grid(row=0, column=3, padx=4)

tk.Label(frame_top, text="Meal:").grid(row=1, column=0, padx=4, pady=4, sticky="e")
meal_var = tk.StringVar(value="Yes")
ttk.Combobox(frame_top, textvariable=meal_var, values=["Yes", "No"],
             width=8, state="readonly").grid(row=1, column=1, padx=4)

tk.Label(frame_top, text="Payment:").grid(row=1, column=2, padx=4, sticky="e")
pay_var = tk.StringVar(value="Paid")
ttk.Combobox(frame_top, textvariable=pay_var, values=["Paid", "Pending"],
             width=10, state="readonly").grid(row=1, column=3, padx=4)

frame_btn = tk.Frame(root)
frame_btn.pack(pady=5)
for txt, cmd in [("Add", add), ("Delete", delete), ("Update", update), ("Refresh", refresh)]:
    tk.Button(frame_btn, text=txt, width=10, command=cmd).pack(side=tk.LEFT, padx=6)

frame_search = tk.Frame(root)
frame_search.pack(pady=3)
tk.Label(frame_search, text="Search by Name:").pack(side=tk.LEFT, padx=4)
e_search = tk.Entry(frame_search, width=20)
e_search.pack(side=tk.LEFT, padx=4)
tk.Button(frame_search, text="Search", width=8, command=search).pack(side=tk.LEFT, padx=4)

cols = ("user_id", "name", "date", "meal_taken", "payment_status")
tree = ttk.Treeview(root, columns=cols, show="headings", height=13)
for col in cols:
    tree.heading(col, text=col.replace("_", " ").title())
    tree.column(col, width=125, anchor="center")
tree.pack(padx=10, pady=8, fill=tk.BOTH, expand=True)
tree.bind("<<TreeviewSelect>>", on_select)

init_db(); refresh()
root.mainloop()
