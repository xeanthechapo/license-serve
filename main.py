import tkinter as tk
from tkinter import messagebox
import hashlib
import platform
import subprocess
import uuid
import requests
import webbrowser

SERVER = "https://license-serve-production.up.railway.app"
DISCORD_LINK = "https://discord.gg/MJNH9r2xA"

BG = "#0d0d0d"
BG2 = "#141414"
RED = "#e63946"
RED_DARK = "#c1121f"
RED_GLOW = "#ff4d5a"
WHITE = "#ffffff"
GRAY = "#666666"
FONT = "Segoe UI"

def get_hwid():
    try:
        result = subprocess.run(
            ["powershell", "-Command", "(Get-CimInstance Win32_ComputerSystemProduct).UUID"],
            capture_output=True, text=True, timeout=5
        )
        board = result.stdout.strip()
    except:
        board = "BOARD_UNKNOWN"
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,48,8)][::-1])
    raw = f"{board}|{mac}|{platform.node()}"
    return hashlib.sha256(raw.encode()).hexdigest()

def activate_license(key):
    try:
        r = requests.post(f"{SERVER}/api/activate", json={"key": key, "hwid": get_hwid()}, timeout=10)
        return r.json()
    except Exception as e:
        return {"success": False, "reason": f"Sunucuya bağlanılamadı: {e}"}

def use_single_key(key):
    try:
        r = requests.post(f"{SERVER}/api/use_single", json={"key": key}, timeout=10)
        return r.json()
    except Exception as e:
        return {"success": False, "reason": f"Hata: {e}"}

def draw_glow_text(canvas, x, y, text, size=38):
    for offset, color in [(6,"#3d0000"),(4,"#7a0000"),(3,"#b30000"),(2,"#cc0000"),(1,"#e63946")]:
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    canvas.create_text(x+dx, y+dy, text=text, font=(FONT, size, "bold"), fill=color)
    canvas.create_text(x, y, text=text, font=(FONT, size, "bold"), fill="#ff4d5a")

def show_inject_animation(app, key, is_single):
    win = tk.Toplevel(app)
    win.title("XEAN Injector")
    win.geometry("420x220")
    win.configure(bg=BG)
    win.resizable(False, False)
    win.grab_set()

    tk.Frame(win, bg=RED, height=3).pack(fill="x")

    tk.Label(win, text="⚡ XEAN INJECTOR", font=(FONT, 14, "bold"), fg=RED_GLOW, bg=BG).pack(pady=(25, 5))
    status_label = tk.Label(win, text="Başlatılıyor...", font=(FONT, 9), fg=GRAY, bg=BG)
    status_label.pack(pady=(0, 20))

    # Progress bar zemin
    bar_bg = tk.Frame(win, bg=BG2, width=340, height=18)
    bar_bg.pack()
    bar_bg.pack_propagate(False)
    bar_fill = tk.Frame(bar_bg, bg=RED, width=0, height=18)
    bar_fill.place(x=0, y=0)

    percent_label = tk.Label(win, text="0%", font=(FONT, 9, "bold"), fg=WHITE, bg=BG)
    percent_label.pack(pady=10)

    steps = [
        (15, "Modüller yükleniyor..."),
        (35, "Bellek taranıyor..."),
        (55, "İşlem enjekte ediliyor..."),
        (75, "Bağlantılar doğrulanıyor..."),
        (90, "Son kontroller yapılıyor..."),
        (100, "Tamamlandı!"),
    ]

    def animate(i=0):
        if i < len(steps):
            percent, text = steps[i]
            width = int(340 * percent / 100)
            bar_fill.config(width=width)
            percent_label.config(text=f"{percent}%")
            status_label.config(text=text)
            win.after(450, lambda: animate(i+1))
        else:
            win.after(400, finish)

    def finish():
        if is_single:
            result = use_single_key(key)
            if not result.get("success"):
                win.destroy()
                messagebox.showerror("Hata", result.get("reason", "Inject başarısız!"))
                return

        win.destroy()
        success = tk.Toplevel(app)
        success.title("Başarılı")
        success.geometry("380x180")
        success.configure(bg=BG)
        success.resizable(False, False)
        success.grab_set()

        tk.Frame(success, bg=RED, height=3).pack(fill="x")
        tk.Label(success, text="✔", font=(FONT, 30, "bold"), fg=RED_GLOW, bg=BG).pack(pady=(20,5))
        tk.Label(success, text="Başarıyla inject edildi!", font=(FONT, 13, "bold"), fg=WHITE, bg=BG).pack()
        tk.Label(success, text="Discord sunucumuza yönlendiriliyorsunuz...", font=(FONT, 8), fg=GRAY, bg=BG).pack(pady=(5,15))

        webbrowser.open(DISCORD_LINK)

        if is_single:
            return True

    animate()

def show_main_app(remaining, plan, key, used=False):
    root.destroy()
    app = tk.Tk()
    app.title("XEAN")
    app.geometry("600x430")
    app.configure(bg=BG)
    app.resizable(False, False)

    tk.Frame(app, bg=RED, height=3).pack(fill="x")

    canvas = tk.Canvas(app, width=600, height=100, bg=BG, highlightthickness=0)
    canvas.pack()
    draw_glow_text(canvas, 300, 55, "XEAN", size=42)

    tk.Frame(app, bg="#2a0000", height=1).pack(fill="x", padx=40)
    tk.Label(app, text="✔  Lisansınız başarıyla aktifleştirildi", font=(FONT, 11), fg=RED_GLOW, bg=BG).pack(pady=10)

    card = tk.Frame(app, bg=BG2, padx=30, pady=18)
    card.pack(padx=50, fill="x")
    tk.Frame(card, bg=RED, width=3).pack(side="left", fill="y", padx=(0,15))
    info = tk.Frame(card, bg=BG2)
    info.pack(side="left", fill="both", expand=True)

    if plan == "lifetime":
        plan_text = "♾   Lifetime"
    elif plan == "monthly":
        plan_text = "📅   1 Aylık"
    elif plan == "weekly":
        plan_text = "⏱   1 Haftalık"
    else:
        plan_text = "🎯   Single Use"

    tk.Label(info, text="PLAN", font=(FONT, 8, "bold"), fg=GRAY, bg=BG2).grid(row=0, column=0, sticky="w")
    tk.Label(info, text="KALAN SÜRE", font=(FONT, 8, "bold"), fg=GRAY, bg=BG2).grid(row=0, column=1, sticky="w", padx=(60,0))
    tk.Label(info, text=plan_text, font=(FONT, 13, "bold"), fg=RED_GLOW, bg=BG2).grid(row=1, column=0, sticky="w")
    tk.Label(info, text=remaining, font=(FONT, 13, "bold"), fg=WHITE, bg=BG2).grid(row=1, column=1, sticky="w", padx=(60,0))

    is_single = (plan == "single")

    def on_inject():
        show_inject_animation(app, key, is_single)
        if is_single:
            inject_btn.config(state="disabled", text="Zaten Kullanıldı", bg="#1a1a1a", fg=GRAY, disabledforeground=GRAY)

    inject_btn = tk.Button(app, text="⚡  INJECT ET", font=(FONT, 11, "bold"),
                           bg=RED, fg=WHITE, activebackground=RED_DARK,
                           relief="flat", padx=30, pady=10,
                           cursor="hand2", command=on_inject)
    inject_btn.pack(pady=15)

    if is_single and used:
        inject_btn.config(state="disabled", text="Zaten Kullanıldı", bg="#1a1a1a", fg=GRAY, disabledforeground=GRAY)

    tk.Label(app, text="© 2024 XEAN. Tüm hakları saklıdır.", font=(FONT, 8), fg=GRAY, bg=BG).pack(side="bottom", pady=6)
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
        show_main_app(result.get("remaining", "Tek Kullanım"), result.get("plan", "single"), key, result.get("used", False))
    else:
        btn.config(state="normal", text="AKTİF ET")
        messagebox.showerror("Hata", result.get("reason", "Geçersiz lisans anahtarı!"))

root = tk.Tk()
root.title("XEAN — Lisans Aktivasyonu")
root.geometry("580x420")
root.configure(bg=BG)
root.resizable(False, False)

tk.Frame(root, bg=RED, height=3).pack(fill="x")

canvas = tk.Canvas(root, width=580, height=120, bg=BG, highlightthickness=0)
canvas.pack()
draw_glow_text(canvas, 290, 65, "XEAN", size=44)

tk.Label(root, text="L İ S A N S  A K T İ V A S Y O N U", font=(FONT, 9, "bold"), fg=GRAY, bg=BG).pack()
tk.Frame(root, bg="#2a0000", height=1).pack(fill="x", padx=60, pady=12)

tk.Label(root, text="Lisans Anahtarı", font=(FONT, 9), fg=GRAY, bg=BG).pack()
entry_frame = tk.Frame(root, bg=RED, padx=1, pady=1)
entry_frame.pack(pady=8)
entry = tk.Entry(entry_frame, font=("Consolas", 13), width=30, justify="center",
                 bg=BG2, fg=WHITE, insertbackground=RED, relief="flat", bd=10)
entry.pack()
entry.focus()

btn = tk.Button(root, text="AKTİF ET", font=(FONT, 11, "bold"),
                bg=RED, fg=WHITE, activebackground=RED_DARK, activeforeground=WHITE,
                relief="flat", padx=40, pady=10, cursor="hand2", command=try_activate)
btn.pack(pady=15)

tk.Label(root, text="© 2024 XEAN. Tüm hakları saklıdır.", font=(FONT, 8), fg=GRAY, bg=BG).pack(side="bottom", pady=6)
tk.Frame(root, bg=RED, height=2).pack(fill="x", side="bottom")

root.mainloop()