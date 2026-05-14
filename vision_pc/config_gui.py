import tkinter as tk
from tkinter import messagebox
import json
import os

CONFIG_FILE = "config_json/config.json"


def save_config(data):
    os.makedirs("config_json", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save():
    data = {
        "fanuc_ip": ip_entry.get(),
        "fanuc_port": int(port_entry.get())
    }

    save_config(data)
    messagebox.showinfo("OK", "Saved")


root = tk.Tk()
root.title("FANUC CONFIG")
root.geometry("300x200")

tk.Label(root, text="FANUC IP").pack()
ip_entry = tk.Entry(root)
ip_entry.pack()

tk.Label(root, text="PORT").pack()
port_entry = tk.Entry(root)
port_entry.pack()

tk.Button(root, text="SAVE", command=save).pack(pady=10)

root.mainloop()