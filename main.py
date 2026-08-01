import tkinter as tk
from tkinter import messagebox
import hashlib
import platform
import subprocess
import uuid
import requests
import os

SERVER = "https://license-serve-production.up.railway.app"

def get_hwid():
    components = []
    try:
        if platform.system() == "Windows":
            cpu = subprocess.check_output("wmic cpu get ProcessorId", shell=True).decode().split("\n")[1].strip()
        else:
            cpu = "CPU"
        components.append(cpu)
    except:
        components.append("CPU_UNKNOWN")
    try:
        if platform.system() == "Windows":
            board = subprocess.check_output("wmic csproduct get UUID", shell=True).decode().split("\n")[1].strip()
        else:
            board = "BOARD"
        components.append(board)
    except:
        components.append("BOARD_UNKNOWN")
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,48,8)][::-1])
    components.append(mac)
    return hashlib.sha256("|".join(components).encode()).hexdigest()

def load_key():
    try:
        with open("license.key", "r") as f:
            return f.read().strip()
    except:
        return None

def save_key(key):
    with open("license.key", "w") as f:
        f.write(key.strip())

def verify_license(key):
    try:
        r = requests.post(f"{SERVER}/api/verify", json={"key": key, "hwid": get_hwid()}, timeout=10)
        return r.json().get("valid", False)
    except:
        return False

def activate_license(key):
    try:
        r = requests.post(f"{SERVER}/api/activate", json={"key": key, "hwid": get_hwid()}, timeout=10)
        return r.json().get("success", False)
    except:
        return False

def show_main_app():
    root.destroy()
    app = tk.Tk()
    app.title("Program")
    app.geometry("400x200")
    app.configure(bg="#1a1a2e")
    tk.Label(app, text="Başarılar, keyiniz aktif edildi!", font=("Arial", 16, "bold"), fg="#00ff88", bg="#1a1a2e").pack(expand=True)
    app.mainloop()

def try_activate():
    key = entry.get().strip()
    if not key:
        messagebox.showwarning("Uyarı", "Lütfen bir key girin!")
        return
    btn.config(state="disabled", text="Kontrol ediliyor...")
    root.update()
    if activate_license(key):
        save_key(key)
        show_main_app()
    else:
        btn.config(state="normal", text="Aktive Et")
        messagebox.showerror("Hata", "Geçersiz key veya başka bir cihazda kullanılmış!")

# Kayıtlı key var mı kontrol et
root = tk.Tk()
root.title("Lisans Aktivasyonu")
root.geometry("420x220")
root.configure(bg="#1a1a2e")
root.resizable(False, False)

tk.Label(root, text="Lisans Anahtarı", font=("Arial", 18, "bold"), fg="white", bg="#1a1a2e").pack(pady=20)
entry = tk.Entry(root, font=("Arial", 13), width=30, justify="center")
entry.pack(pady=5)
btn = tk.Button(root, text="Aktive Et", font=("Arial", 12, "bold"), bg="#00ff88", fg="#1a1a2e", padx=20, pady=5, command=try_activate)
btn.pack(pady=15)

root.mainloop()