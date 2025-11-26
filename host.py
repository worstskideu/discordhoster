## Credits to @retiredskid on Discord
## This code has got some help from AI for final reviews and bug fixes
## Everything else got coded by my team, Discord Link is in the UI by clicking "Info"
## ENJOY


import os
import sys
import json
import subprocess
import threading
import queue
import time
import atexit
import platform
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
import customtkinter as ctk

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

C_BG_MAIN = "#FFFFFF"
C_BG_SIDEBAR = "#F3F4F6"
C_BG_CARD = "#FFFFFF"
C_TEXT_MAIN = "#111827"
C_TEXT_SUB = "#6B7280"
C_ACCENT = "#3B82F6"
C_ACCENT_HOVER = "#2563EB"
C_BORDER = "#E5E7EB"
C_SUCCESS = "#10B981"
C_ERROR = "#EF4444"
C_ITEM_HOVER = "#E5E7EB"
C_SELECTED = "#EFF6FF"

R_FULL = 20
R_CARD = 15
R_SMALL = 10

CONFIG_FILE = Path("hoster_config_final.json")
DISCORD_LINK = "https://discord.gg/MYhnRKQFcm" 

class BotConfig:
    def __init__(self, name):
        self.name = name
        self.auto_start = False
        self.auto_restart = True
        self.max_ram_mb = 1024
        self.launch_args = ""
        self.env_vars = ""
        self.custom_interpreter = ""

    def to_dict(self): return self.__dict__

    @staticmethod
    def from_dict(data):
        b = BotConfig(data['name'])
        b.auto_start = data.get('auto_start', False)
        b.auto_restart = data.get('auto_restart', True)
        b.max_ram_mb = data.get('max_ram_mb', 1024)
        b.launch_args = data.get('launch_args', "")
        b.env_vars = data.get('env_vars', "")
        b.custom_interpreter = data.get('custom_interpreter', "")
        return b

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Info")
        self.geometry("350x280")
        self.resizable(False, False)
        self.configure(fg_color=C_BG_MAIN)
        self.grab_set()

        ctk.CTkLabel(self, text="Thanks for choosing us", font=("Segoe UI", 16, "bold"), text_color=C_ACCENT).pack(pady=(50, 10))
        
        ctk.CTkButton(self, text="Join Discord Server For Help", height=40, corner_radius=R_FULL,
                      fg_color="#5865F2", hover_color="#4752C4",
                      font=("Segoe UI", 13, "bold"),
                      command=lambda: webbrowser.open(DISCORD_LINK)).pack(pady=20, padx=40, fill="x")

        ctk.CTkLabel(self, text="Credits: @retiredskid", font=("Segoe UI", 12), text_color=C_TEXT_SUB).pack(side="bottom", pady=30)

class RoundedFolderChip(ctk.CTkFrame):
    def __init__(self, master, path, command_remove):
        super().__init__(master, fg_color=C_BG_MAIN, corner_radius=R_SMALL, border_width=1, border_color=C_BORDER)
        self.pack(fill="x", pady=3, padx=5)
        
        name = os.path.basename(path) or path
        ctk.CTkLabel(self, text="📁", font=("Segoe UI Emoji", 12), text_color=C_TEXT_SUB).pack(side="left", padx=(10, 5))
        self.lbl = ctk.CTkLabel(self, text=name, font=("Segoe UI", 12), text_color=C_TEXT_MAIN, anchor="w")
        self.lbl.pack(side="left", fill="x", expand=True, pady=8)

        self.btn_del = ctk.CTkButton(self, text="×", width=24, height=24, corner_radius=12,
                                     fg_color="transparent", hover_color="#FEE2E2", text_color=C_ERROR,
                                     font=("Arial", 16), command=lambda: command_remove(path))
        self.btn_del.pack(side="right", padx=5)

class RoundedBotItem(ctk.CTkFrame):
    def __init__(self, master, name, folder_name, is_running, command_select):
        super().__init__(master, fg_color="transparent", corner_radius=R_CARD)
        self.name = name
        self.command_select = command_select
        self.is_selected = False
        
        self.grid_columnconfigure(1, weight=1)
        
        self.dot_color = C_SUCCESS if is_running else "#D1D5DB"
        self.dot = ctk.CTkLabel(self, text="●", font=("Arial", 14), text_color=self.dot_color)
        self.dot.grid(row=0, column=0, rowspan=2, padx=(10, 5))
        
        self.lbl_name = ctk.CTkLabel(self, text=name, font=("Segoe UI", 13, "bold"), text_color=C_TEXT_MAIN, anchor="w")
        self.lbl_name.grid(row=0, column=1, sticky="w", pady=(8, 0))
        
        self.lbl_fold = ctk.CTkLabel(self, text=folder_name, font=("Segoe UI", 10), text_color=C_TEXT_SUB, anchor="w")
        self.lbl_fold.grid(row=1, column=1, sticky="w", pady=(0, 8))

        for w in [self, self.dot, self.lbl_name, self.lbl_fold]:
            w.bind("<Button-1>", lambda e: self.command_select(self.name))
            w.bind("<Enter>", self.on_enter)
            w.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        if not self.is_selected: self.configure(fg_color=C_ITEM_HOVER)

    def on_leave(self, e):
        if not self.is_selected: self.configure(fg_color="transparent")

    def set_selected(self, s):
        self.is_selected = s
        self.configure(fg_color=C_SELECTED if s else "transparent")
        self.lbl_name.configure(text_color=C_ACCENT if s else C_TEXT_MAIN)

    def set_running(self, r):
        c = C_SUCCESS if r else "#D1D5DB"
        self.dot.configure(text_color=c)

class HosterProFinal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hoster")
        self.geometry("1200x850")
        self.configure(fg_color=C_BG_MAIN)
        
        self.folders = []
        self.bot_configs = {}
        self.processes = {}
        self.active_bot = None
        self.log_queue = queue.Queue()
        self.toplevel_window = None
        
        self.load_data()
        self.setup_ui()
        
        self.after(500, self.monitor_system)
        self.after(200, self.check_logs)
        self.after(1000, self.autostart_logic)
        atexit.register(self.shutdown)

    def setup_ui(self):
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=280, fg_color=C_BG_SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        head = ctk.CTkFrame(sidebar, fg_color="transparent")
        head.pack(fill="x", pady=(30, 5), padx=20)

        ctk.CTkLabel(head, text="HOSTER", font=("Segoe UI", 18, "bold"), text_color=C_TEXT_MAIN).pack(side="left")
        ctk.CTkButton(head, text="Info", width=25, height=25, corner_radius=10, fg_color="white", text_color=C_TEXT_MAIN, hover_color=C_ITEM_HOVER, font=("Segoe UI", 14, "bold"), command=self.open_settings).pack(side="right")

        ctk.CTkLabel(sidebar, text="Dashboard", font=("Segoe UI", 11), text_color=C_TEXT_SUB).pack(pady=(0, 20), padx=20, anchor="w")

        ctk.CTkLabel(sidebar, text="MONITORED FOLDERS", font=("Segoe UI", 10, "bold"), text_color=C_TEXT_SUB).pack(padx=20, anchor="w")

        bottom_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_container.pack(side="bottom", fill="x", padx=15, pady=20)

        stats_card = ctk.CTkFrame(bottom_container, fg_color=C_BG_MAIN, corner_radius=R_CARD, border_width=1, border_color=C_BORDER)
        stats_card.pack(fill="x", pady=(15, 0))
        
        self.lbl_cpu = ctk.CTkLabel(stats_card, text="CPU: 0%", font=("Segoe UI", 11, "bold"), text_color=C_TEXT_SUB)
        self.lbl_cpu.pack(side="left", padx=15, pady=12)
        
        ctk.CTkFrame(stats_card, width=1, height=15, fg_color=C_BORDER).pack(side="left", padx=5)

        self.lbl_ram = ctk.CTkLabel(stats_card, text="RAM: 0%", font=("Segoe UI", 11, "bold"), text_color=C_TEXT_SUB)
        self.lbl_ram.pack(side="left", padx=15, pady=12)

        btn_add = ctk.CTkButton(bottom_container, text="+ New Folder", height=40, corner_radius=R_FULL,
                                fg_color=C_BG_MAIN, text_color=C_ACCENT, hover_color="#FFFFFF",
                                border_width=1, border_color=C_BORDER, font=("Segoe UI", 12, "bold"),
                                command=self.add_folder)
        btn_add.pack(fill="x", side="top")

        self.scroll_folders = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", scrollbar_button_color=C_ITEM_HOVER, scrollbar_fg_color="transparent")
        self.scroll_folders.pack(fill="both", expand=True, padx=10, pady=10)

        mid = ctk.CTkFrame(self, width=320, fg_color=C_BG_MAIN, corner_radius=0)
        mid.grid(row=0, column=1, sticky="nsew")
        ctk.CTkFrame(mid, width=1, fg_color=C_BORDER).pack(side="right", fill="y")
        
        ctk.CTkLabel(mid, text="BOT LIBRARY", font=("Segoe UI", 10, "bold"), text_color=C_TEXT_SUB).pack(padx=20, pady=(30, 10), anchor="w")
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.refresh_bot_list)
        entry = ctk.CTkEntry(mid, textvariable=self.search_var, placeholder_text="Search bots...", 
                             height=40, corner_radius=R_FULL, border_width=1, border_color=C_BORDER, 
                             fg_color=C_BG_SIDEBAR, text_color=C_TEXT_MAIN)
        entry.pack(fill="x", padx=15, pady=(0, 15))

        self.scroll_bots = ctk.CTkScrollableFrame(mid, fg_color="transparent", scrollbar_button_color=C_BG_SIDEBAR, scrollbar_fg_color="transparent")
        self.scroll_bots.pack(fill="both", expand=True, padx=5)

        self.main_area = ctk.CTkFrame(self, fg_color=C_BG_MAIN, corner_radius=0)
        self.main_area.grid(row=0, column=2, sticky="nsew")
        
        self.placeholder = ctk.CTkLabel(self.main_area, text="Select a bot to manage", font=("Segoe UI", 16), text_color=C_TEXT_SUB)
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self.content = ctk.CTkFrame(self.main_area, fg_color="transparent")

        header_frm = ctk.CTkFrame(self.content, fg_color="transparent")
        header_frm.pack(fill="x", padx=40, pady=(40, 20))
        
        self.lbl_title = ctk.CTkLabel(header_frm, text="Bot Name", font=("Segoe UI", 30, "bold"), text_color=C_TEXT_MAIN)
        self.lbl_title.pack(side="left")
        
        self.lbl_status = ctk.CTkLabel(header_frm, text="STOPPED", height=24, corner_radius=12,
                                       font=("Segoe UI", 11, "bold"), text_color=C_TEXT_SUB, fg_color=C_BG_SIDEBAR)
        self.lbl_status.pack(side="left", padx=15)

        actions = ctk.CTkFrame(header_frm, fg_color="transparent")
        actions.pack(side="right")
        
        self.btn_start = ctk.CTkButton(actions, text="Start Service", width=130, height=38, corner_radius=R_FULL,
                                       fg_color=C_SUCCESS, hover_color="#059669", font=("Segoe UI", 13, "bold"),
                                       command=self.action_start)
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = ctk.CTkButton(actions, text="Stop Service", width=110, height=38, corner_radius=R_FULL,
                                      fg_color="transparent", border_width=1, border_color=C_ERROR, text_color=C_ERROR, hover_color="#FEF2F2",
                                      font=("Segoe UI", 13, "bold"), command=self.action_stop)
        self.btn_stop.pack(side="left", padx=5)

        self.tabs = ctk.CTkTabview(self.content, corner_radius=R_CARD, fg_color=C_BG_SIDEBAR, 
                                   segmented_button_fg_color="#E2E8F0", 
                                   segmented_button_selected_color=C_BG_MAIN,
                                   segmented_button_selected_hover_color="#FFFFFF",
                                   segmented_button_unselected_color="#E2E8F0",
                                   segmented_button_unselected_hover_color="#CBD5E1",
                                   text_color=C_TEXT_MAIN)
        self.tabs.pack(fill="both", expand=True, padx=40, pady=(10, 40))
        
        self.tabs.add("Console Output")
        self.tabs.add("Configuration")

        self.console = ctk.CTkTextbox(self.tabs.tab("Console Output"), corner_radius=R_CARD, fg_color="#1E293B", text_color="#E2E8F0", font=("Consolas", 12))
        self.console.pack(fill="both", expand=True, padx=10, pady=10)
        self.console.configure(state="disabled")

        scroll_cfg = ctk.CTkScrollableFrame(self.tabs.tab("Configuration"), fg_color="transparent", scrollbar_button_color=C_ITEM_HOVER, scrollbar_fg_color="transparent")
        scroll_cfg.pack(fill="both", expand=True, padx=10, pady=10)

        def mk_lbl(t): return ctk.CTkLabel(scroll_cfg, text=t, font=("Segoe UI", 12, "bold"), text_color=C_TEXT_SUB).pack(anchor="w", pady=(15,5))
        def mk_ent(): return ctk.CTkEntry(scroll_cfg, height=38, corner_radius=R_FULL, border_width=1, border_color=C_BORDER, fg_color=C_BG_MAIN, text_color=C_TEXT_MAIN)

        mk_lbl("Launch Options")
        self.chk_auto = ctk.CTkCheckBox(scroll_cfg, text="Auto-start on launch", corner_radius=6, border_width=1, fg_color=C_ACCENT, border_color="#CBD5E1", text_color=C_TEXT_MAIN)
        self.chk_auto.pack(anchor="w", pady=5)
        
        self.chk_restart = ctk.CTkCheckBox(scroll_cfg, text="Restart on crash", corner_radius=6, border_width=1, fg_color=C_ACCENT, border_color="#CBD5E1", text_color=C_TEXT_MAIN)
        self.chk_restart.pack(anchor="w", pady=5)

        mk_lbl("Launch Arguments")
        self.ent_args = mk_ent()
        self.ent_args.pack(fill="x")

        mk_lbl("Python Interpreter (Optional)")
        self.ent_py = mk_ent()
        self.ent_py.pack(fill="x")

        mk_lbl("Environment Variables (One per line)")
        self.txt_env = ctk.CTkTextbox(scroll_cfg, height=100, corner_radius=R_CARD, border_width=1, border_color=C_BORDER, fg_color=C_BG_MAIN, text_color=C_TEXT_MAIN)
        self.txt_env.pack(fill="x")

        mk_lbl("Resource Limit (Max RAM MB)")
        self.ent_ram = mk_ent()
        self.ent_ram.pack(fill="x")

        ctk.CTkButton(scroll_cfg, text="Save Changes", height=40, corner_radius=R_FULL, fg_color=C_TEXT_MAIN, hover_color="#334155", font=("Segoe UI", 13, "bold"), command=self.save_config).pack(fill="x", pady=30)

        self.refresh_folders()
        self.refresh_bot_list()

    def open_settings(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = SettingsWindow(self)
        else:
            self.toplevel_window.focus()

    def monitor_system(self):
        if PSUTIL_AVAILABLE:
            c = psutil.cpu_percent(interval=None)
            r = psutil.virtual_memory().percent
            self.lbl_cpu.configure(text=f"CPU: {c:.1f}%")
            self.lbl_ram.configure(text=f"RAM: {r:.1f}%")
        
        dead = []
        for n, p in self.processes.items():
            if p.poll() is not None:
                dead.append(n)
            elif PSUTIL_AVAILABLE:
                try:
                    mem = psutil.Process(p.pid).memory_info().rss / 1024 / 1024
                    cfg = self.get_config(n)
                    if mem > cfg.max_ram_mb:
                        self.log_queue.put((n, f"OVERLOAD: RAM usage {int(mem)}MB > {cfg.max_ram_mb}MB. Restarting..."))
                        self.restart_bot(n)
                except: pass

        for n in dead:
            code = self.processes[n].returncode
            del self.processes[n]
            self.log_queue.put((n, f"SYSTEM: Process ended (Code {code})"))
            self.update_status_ui(n, False)
            
            if self.get_config(n).auto_restart and code != 0:
                self.log_queue.put((n, "SYSTEM: Auto-restarting in 3s..."))
                threading.Timer(3.0, lambda x=n: self.action_start(x)).start()

        self.after(1000, self.monitor_system)

    def action_start(self, target_name=None):
        name = target_name or self.active_bot
        if not name or name in self.processes: return

        path = None
        wdir = None
        for f in self.folders:
            p = os.path.join(f, name + ".py")
            if os.path.exists(p):
                path = p
                wdir = f
                break
        
        if not path: return

        cfg = self.get_config(name)
        
        py = cfg.custom_interpreter
        if not py:
            for v in ["venv", ".venv", "env"]:
                vp = os.path.join(wdir, v)
                if os.path.isdir(vp):
                    py = os.path.join(vp, "Scripts", "python.exe") if platform.system() == "Windows" else os.path.join(vp, "bin", "python")
                    break
        if not py or not os.path.exists(py): py = sys.executable

        env = os.environ.copy()
        for line in cfg.env_vars.split('\n'):
            if '=' in line: k,v = line.split('=', 1); env[k.strip()] = v.strip()

        cmd = [py, "-u", path] + cfg.launch_args.split()

        try:
            si = None
            if platform.system() == "Windows":
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.Popen(cmd, cwd=wdir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace', startupinfo=si)
            
            self.processes[name] = proc
            threading.Thread(target=self.reader, args=(proc, name), daemon=True).start()
            self.log_queue.put((name, f"SYSTEM: Started (PID {proc.pid})"))
            self.update_status_ui(name, True)
        except Exception as e:
            self.log_queue.put((name, f"ERROR: {e}"))

    def action_stop(self):
        if self.active_bot and self.active_bot in self.processes:
            try:
                p = self.processes[self.active_bot]
                if PSUTIL_AVAILABLE:
                    par = psutil.Process(p.pid)
                    for c in par.children(recursive=True): c.terminate()
                    par.terminate()
                else: p.terminate()
            except: pass
            
            if self.active_bot in self.processes: del self.processes[self.active_bot]
            self.update_status_ui(self.active_bot, False)
            self.log_queue.put((self.active_bot, "SYSTEM: Stopped manually"))

    def restart_bot(self, name):
        if name in self.processes:
            try: self.processes[name].terminate()
            except: pass
            del self.processes[name]
        self.update_status_ui(name, False)
        self.after(1500, lambda: self.action_start(name))

    def reader(self, proc, name):
        for line in iter(proc.stdout.readline, ''):
            if line: self.log_queue.put((name, line.strip()))
        proc.stdout.close()

    def check_logs(self):
        while not self.log_queue.empty():
            try:
                n, m = self.log_queue.get_nowait()
                if self.active_bot == n:
                    self.console.configure(state="normal")
                    self.console.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {m}\n")
                    self.console.see("end")
                    self.console.configure(state="disabled")
            except: break
        self.after(100, self.check_logs)

    def select_bot(self, name):
        self.active_bot = name
        self.placeholder.place_forget()
        self.content.pack(fill="both", expand=True)
        
        self.lbl_title.configure(text=name)
        self.update_status_ui(name, name in self.processes)

        for n, item in self.bot_widgets.items(): item.set_selected(n == name)

        c = self.get_config(name)
        self.chk_auto.deselect(); self.chk_restart.deselect()
        if c.auto_start: self.chk_auto.select()
        if c.auto_restart: self.chk_restart.select()
        
        for w, v in [(self.ent_args, c.launch_args), (self.ent_py, c.custom_interpreter), (self.ent_ram, str(c.max_ram_mb))]:
            w.delete(0, "end"); w.insert(0, v)
        
        self.txt_env.delete("1.0", "end"); self.txt_env.insert("1.0", c.env_vars)
        self.console.configure(state="normal"); self.console.delete("1.0", "end"); self.console.insert("end", f"--- Log: {name} ---\n"); self.console.configure(state="disabled")

    def update_status_ui(self, name, running):
        if name in self.bot_widgets: self.bot_widgets[name].set_running(running)
        if self.active_bot == name:
            if running:
                self.lbl_status.configure(text="RUNNING", text_color=C_SUCCESS, bg_color="#DCFCE7")
                self.btn_start.configure(state="disabled", fg_color="#94A3B8")
                self.btn_stop.configure(state="normal", border_color=C_ERROR, text_color=C_ERROR)
            else:
                self.lbl_status.configure(text="STOPPED", text_color=C_TEXT_SUB, bg_color=C_BG_SIDEBAR)
                self.btn_start.configure(state="normal", fg_color=C_SUCCESS)
                self.btn_stop.configure(state="disabled", border_color=C_BORDER, text_color="#94A3B8")

    def refresh_bot_list(self, *a):
        s = self.search_var.get().lower()
        for w in self.scroll_bots.winfo_children(): w.destroy()
        self.bot_widgets = {}
        
        found = []
        for f in self.folders:
            if os.path.exists(f):
                fn = os.path.basename(f)
                for file in os.listdir(f):
                    if file.endswith(".py") and not file.startswith("_"):
                        if s in file.lower(): found.append((file[:-3], fn))
        
        found.sort()
        for n, fn in found:
            item = RoundedBotItem(self.scroll_bots, n, fn, n in self.processes, self.select_bot)
            item.pack(fill="x", pady=3, padx=5)
            self.bot_widgets[n] = item
            if self.active_bot == n: item.set_selected(True)

    def refresh_folders(self):
        for w in self.scroll_folders.winfo_children(): w.destroy()
        for f in self.folders:
            RoundedFolderChip(self.scroll_folders, f, self.rem_folder)

    def add_folder(self):
        p = ctk.filedialog.askdirectory()
        if p and p not in self.folders:
            self.folders.append(p); self.save_data(); self.refresh_folders(); self.refresh_bot_list()

    def rem_folder(self, p):
        if p in self.folders: self.folders.remove(p); self.save_data(); self.refresh_folders(); self.refresh_bot_list()

    def save_config(self):
        if not self.active_bot: return
        c = self.get_config(self.active_bot)
        c.auto_start = bool(self.chk_auto.get())
        c.auto_restart = bool(self.chk_restart.get())
        c.launch_args = self.ent_args.get()
        c.custom_interpreter = self.ent_py.get()
        c.env_vars = self.txt_env.get("1.0", "end-1c")
        try: c.max_ram_mb = int(self.ent_ram.get())
        except: pass
        self.save_data()

    def load_data(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    d = json.load(f)
                    self.folders = d.get('folders', [])
                    for k,v in d.get('configs', {}).items(): self.bot_configs[k] = BotConfig.from_dict(v)
            except: pass

    def save_data(self):
        with open(CONFIG_FILE, 'w') as f: json.dump({'folders': self.folders, 'configs': {k:v.to_dict() for k,v in self.bot_configs.items()}}, f, indent=2)

    def get_config(self, n):
        if n not in self.bot_configs: self.bot_configs[n] = BotConfig(n)
        return self.bot_configs[n]

    def autostart_logic(self):
        if hasattr(self, '_started'): return
        self._started = True
        for f in self.folders:
            if os.path.exists(f):
                for file in os.listdir(f):
                    if file.endswith(".py") and not file.startswith("_"):
                        n = file[:-3]
                        if self.get_config(n).auto_start: self.action_start(n)

    def shutdown(self):
        for p in self.processes.values():
            if p: p.kill()

if __name__ == "__main__":
    app = HosterProFinal()
    app.mainloop()