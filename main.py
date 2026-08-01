import tkinter as tk
from tkinter import messagebox
import hashlib
import platform
import subprocess
import uuid
import requests

SERVER = "https://license-serve-production.up.railway.app"

BG = "#0d0d0d"
BG2 = "#141414"
RED = "#e63946"
RED_DARK = "#c1121f"
RED_GLOW = "#ff4d5a"
WHITE = "#ffffff"
GRAY = "#666666"
FONT = "Segoe UI"

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

def draw_glow_text(canvas, x, y, text, size=38):
    # Glow katmanları (dıştan içe, kırmızı parıltı)
    for offset, color, alpha_size in [
        (6, "#3d0000", size),
        (4, "#7a0000", size),
        (3, "#b30000", size),
        (2, "#cc0000", size),
        (1, "#e63946", size),
    ]:
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    canvas.create_text(x+dx, y+dy, text=text, font=(FONT, alpha_size, "bold"), fill=color)
    # Ana metin
    canvas.create_text(x, y, text=text, font=(FONT, size, "bold"), fill="#ff4d5a")

def show_main_app(remaining, plan):
    root.destroy()
    app = tk.Tk()
    app.title("XEAN")
    app.geometry("600x400")
    app.configure(bg=BG)
    app.resizable(False, False)

    # Üst şerit
    tk.Frame(app, bg=RED, height=3).pack(fill="x")

    # XEAN canvas glow
    canvas = tk.Canvas(app, width=600, height=100, bg=BG, highlightthickness=0)
    canvas.pack()
    draw_glow_text(canvas, 300, 55, "XEAN", size=42)

    # Ayraç
    tk.Frame(app, bg="#2a0000", height=1).pack(fill="x", padx=40)

    tk.Label(app, text="✔  Lisansınız başarıyla aktifleştirildi",
             font=(FONT, 11), fg="#ff4d5a", bg=BG).pack(pady=12)

    # Bilgi kartı
    card = tk.Frame(app, bg=BG2, padx=30, pady=18)
    card.pack(padx=50, fill="x")

    tk.Frame(card, bg=RED, width=3).pack(side="left", fill="y", padx=(0,15))

    info = tk.Frame(card, bg=BG2)
    info.pack(side="left", fill="both", expand=True)

    if plan == "lifetime":
        plan_text = "♾   Lifetime"
    elif plan == "monthly":
        plan_text = "📅   1 Aylık"
    else:
        plan_text = "⏱   1 Haftalık"

    tk.Label(info, text="PLAN", font=(FONT, 8, "bold"), fg=GRAY, bg=BG2).grid(row=0, column=0, sticky="w")
    tk.Label(info, text="KALAN SÜRE", font=(FONT, 8, "bold"), fg=GRAY, bg=BG2).grid(row=0, column=1, sticky="w", padx=(60,0))
    tk.Label(info, text=plan_text, font=(FONT, 14, "bold"), fg=RED_GLOW, bg=BG2).grid(row=1, column=0, sticky="w")
    tk.Label(info, text=remaining, font=(FONT, 14, "bold"), fg=WHITE, bg=BG2).grid(row=1, column=1, sticky="w", padx=(60,0))

    tk.Label(app, text="© 2024 XEAN. Tüm hakları saklıdır.",
             font=(FONT, 8), fg=GRAY, bg=BG).pack(side="bottom", pady=8)
    tk.Frame(app, bg=RED, height=2).pack(fill="x", side="bottom")

    app.mainloop()

def try_activate():
    key = entry.get().strip()
    if not key:
        messagebox.showwarning("Uyarı", "Lütfen lisans anahtarınızı girin!")
        return
    btn.config(state="disabled", text="Doğrulanıyor...")
    root.update()
    result = activate_license(key)
    if result.get("success"):
        show_main_app(result.get("remaining", "Sınırsız"), result.get("plan", "lifetime"))
    else:
        btn.config(state="normal", text="AKTİF ET")
        messagebox.showerror("Hata", result.get("reason", "Geçersiz lisans anahtarı!"))

# Ana pencere
root = tk.Tk()
root.title("XEAN — Lisans Aktivasyonu")
root.geometry("580x420")
root.configure(bg=BG)
root.resizable(False, False)

# Üst şerit
tk.Frame(root, bg=RED, height=3).pack(fill="x")

# XEAN glow canvas
canvas = tk.Canvas(root, width=580, height=120, bg=BG, highlightthickness=0)
canvas.pack()
draw_glow_text(canvas, 290, 65, "XEAN", size=44)

tk.Label(root, text="L İ S A N S  A K T İ V A S Y O N U", font=(FONT, 9, "bold"), fg=GRAY, bg=BG).pack()

# Ayraç
tk.Frame(root, bg="#2a0000", height=1).pack(fill="x", padx=60, pady=12)

# Giriş kutusu
tk.Label(root, text="Lisans Anahtarı", font=(FONT, 9), fg=GRAY, bg=BG).pack()
entry_frame = tk.Frame(root, bg=RED, padx=1, pady=1)
entry_frame.pack(pady=8)
entry = tk.Entry(entry_frame, font=("Consolas", 13), width=30, justify="center",
                 bg=BG2, fg=WHITE, insertbackground=RED, relief="flat", bd=10)
entry.pack()
entry.focus()

# Buton
btn = tk.Button(root, text="AKTİF ET", font=(FONT, 11, "bold"),
                bg=RED, fg=WHITE, activebackground=RED_DARK, activeforeground=WHITE,
                relief="flat", padx=40, pady=10, cursor="hand2", command=try_activate)
btn.pack(pady=15)

tk.Label(root, text="© 2024 XEAN. Tüm hakları saklıdır.", font=(FONT, 8), fg=GRAY, bg=BG).pack(side="bottom", pady=6)
tk.Frame(root, bg=RED, height=2).pack(fill="x", side="bottom")

root.mainloop()