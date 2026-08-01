import tkinter as tk
from tkinter import messagebox
import hashlib
import platform
import subprocess
import uuid
import requests

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

def activate_license(key):
    try:
        r = requests.post(f"{SERVER}/api/activate", json={"key": key, "hwid": get_hwid()}, timeout=10)
        return r.json()
    except:
        return {"success": False, "reason": "Sunucuya bağlanılamadı"}

def show_main_app(remaining, plan):
    root.destroy()
    app = tk.Tk()
    app.title("Program")
    app.geometry("420x250")
    app.configure(bg="#1a1a2e")
    app.resizable(False, False)

    tk.Label(app, text="✅ Başarılar, keyiniz aktif edildi!", font=("Arial", 14, "bold"), fg="#00ff88", bg="#1a1a2e").pack(pady=30)

    if plan == "lifetime":
        plan_text = "Plan: Lifetime ♾️"
        sure_text = "Kalan Süre: Sınırsız"
    else:
        plan_text = f"Plan: {'1 Haftalık' if plan == 'weekly' else '1 Aylık'}"
        sure_text = f"Kalan Süre: {remaining}"

    tk.Label(app, text=plan_text, font=("Arial", 12), fg="white", bg="#1a1a2e").pack()
    tk.Label(app, text=sure_text, font=("Arial", 12), fg="#ffcc00", bg="#1a1a2e").pack(pady=5)

    app.mainloop()

def try_activate():
    key = entry.get().strip()
    if not key:
        messagebox.showwarning("Uyarı", "Lütfen bir key girin!")
        return
    btn.config(state="disabled", text="Kontrol ediliyor...")
    root.update()
    result = activate_license(key)
    if result.get("success"):
        remaining = result.get("remaining", "Sınırsız")
        plan = result.get("plan", "lifetime")
        show_main_app(remaining, plan)
    else:
        btn.config(state="normal", text="Aktive Et")
        messagebox.showerror("Hata", result.get("reason", "Geçersiz key!"))

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