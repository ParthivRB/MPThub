# --- FORCE PYINSTALLER TO BUNDLE SCIENCE LIBRARIES ---
# We import these here so the App includes them for the external 'mpthub' library
import pandas, numpy, trackpy, matplotlib, scipy, openpyxl, sqlalchemy
try: import yaml
except ImportError: pass
# -----------------------------------------------------

import os, json, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# IMPORT YOUR SEPARATE FILE HERE
import mpthub_headless

# --- SETUP PATHS ---
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

SETTINGS_FILE = BASE_DIR / "app_settings.json"
RUN_CONFIG = BASE_DIR / "run_config.json"
DEFAULT_DIR = Path.home()

# --- MEMORY ---
def load_settings():
    defaults = {"last_excel": str(DEFAULT_DIR), "last_data": str(DEFAULT_DIR), "mpt_lib": ""}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f: return {**defaults, **json.load(f)}
        except: pass
    return defaults

def save_settings(key, value):
    current = load_settings()
    current[key] = str(value)
    with open(SETTINGS_FILE, "w") as f: json.dump(current, f, indent=2)
    return current

# --- HELPERS ---
def get_sizes(path):
    wb = openpyxl.load_workbook(path)
    return {str(r[0]).strip(): float(r[1]) for r in wb.active.iter_rows(min_row=2, max_col=2, values_only=True) if r[0]}

def scan(folder, sizes):
    items = []
    for r, _, files in os.walk(str(folder)):
        for f in files:
            if f.lower().endswith(".csv"):
                key = next((k for k in sizes if k.strip().lower() in r.lower()), None)
                fname = key if key else Path(r).name
                items.append({
                    "file_name": f, "folder_name": fname, 
                    "size": sizes.get(fname, 0.0), "file_path": str(Path(r)/f)
                })
    return sorted(items, key=lambda x: x["folder_name"])

# --- GUI ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MPTHub Automated")
        self.geometry("900x700")
        self.settings = load_settings()
        self.paths = {
            "excel": tk.StringVar(value=""), 
            "data": tk.StringVar(value=""),
            "lib": tk.StringVar(value=self.settings["mpt_lib"])
        }
        self.defaults = {"delta_t": 33.33, "filter": 30, "frames": 400, "width_px": 512, "width_um": 318.2, "analysis_time": 13.33, "temperature": 25.0}
        self.items = []
        self._ui()

    def _ui(self):
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=5)
        ttk.Label(top, text="MPTHub Library Folder:").pack(side="left")
        ttk.Entry(top, textvariable=self.paths["lib"]).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(top, text="Locate...", command=self._set_lib).pack(side="left")

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=1, padx=10, pady=5)
        t1, t2, t3 = ttk.Frame(nb), ttk.Frame(nb), ttk.Frame(nb)
        nb.add(t1, text="1. Scan"); nb.add(t2, text="2. Settings"); nb.add(t3, text="3. Run")

        # Tab 1
        for i, (lbl, key, mk) in enumerate([("Excel File:", "excel", "last_excel"), ("Data Folder:", "data", "last_data")]):
            ttk.Label(t1, text=lbl).grid(row=i, column=0, padx=10, pady=10)
            ttk.Entry(t1, textvariable=self.paths[key], width=60).grid(row=i, column=1)
            def browse(k=key, m=mk):
                start = self.settings.get(m, str(DEFAULT_DIR))
                p = filedialog.askopenfilename(initialdir=start) if k=="excel" else filedialog.askdirectory(initialdir=start)
                if p: 
                    self.paths[k].set(p)
                    save_settings(m, str(Path(p).parent) if k=="excel" else p)
            ttk.Button(t1, text="Browse", command=browse).grid(row=i, column=2)
        ttk.Button(t1, text="SCAN FILES", command=self._scan).grid(row=2, column=1, pady=20)
        self.lbl = ttk.Label(t1, text="Ready"); self.lbl.grid(row=3, column=1)

        # Tab 2
        self.ents = {}
        for i, (k, v) in enumerate(self.defaults.items()):
            ttk.Label(t2, text=k).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            self.ents[k] = tk.StringVar(value=str(v))
            ttk.Entry(t2, textvariable=self.ents[k]).grid(row=i, column=1)
        ttk.Button(t2, text="Update Defaults", command=self._update).grid(row=8, column=1, pady=10)

        # Tab 3
        cols = ("file_name", "size", "delta_t", "filter")
        self.tree = ttk.Treeview(t3, columns=cols, show="headings"); self.tree.pack(fill="both", expand=1)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.bind("<Double-1>", self._edit)
        
        self.run_btn = ttk.Button(t3, text="RUN BATCH", command=self._run)
        self.run_btn.pack(pady=10)
        ttk.Label(t3, text="Log Output:").pack(anchor="w", padx=10)
        self.log_text = tk.Text(t3, height=8, state="disabled")
        self.log_text.pack(fill="x", padx=10, pady=(0, 10))

    def _set_lib(self):
        p = filedialog.askdirectory()
        if p:
            self.paths["lib"].set(p)
            save_settings("mpt_lib", p)

    def _scan(self):
        try:
            self.items = scan(self.paths["data"].get(), get_sizes(self.paths["excel"].get()))
            self.run_items = [{**i, **self.defaults} for i in self.items]
            self.tree.delete(*self.tree.get_children())
            for i in self.run_items: self.tree.insert("", "end", values=(i["file_name"], i["size"], i["delta_t"], i["filter"]))
            self.lbl.config(text=f"Found {len(self.items)} files.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def _update(self):
        self.defaults = {k: float(v.get()) for k, v in self.ents.items()}
        messagebox.showinfo("OK", "Defaults updated.")

    def _edit(self, event):
        row = self.tree.identify_row(event.y)
        if not row: return
        idx = self.tree.index(row); item = self.run_items[idx]
        top = tk.Toplevel(self); top.title(f"Edit {item['file_name']}")
        vars = {}
        for i, k in enumerate(["size"] + list(self.defaults.keys())):
            ttk.Label(top, text=k).grid(row=i, column=0); v = tk.StringVar(value=str(item.get(k,0))); ttk.Entry(top, textvariable=v).grid(row=i, column=1)
            vars[k] = v
        def save():
            for k,v in vars.items(): item[k] = float(v.get())
            self.tree.item(row, values=(item["file_name"], item["size"], item["delta_t"], item["filter"]))
            top.destroy()
        ttk.Button(top, text="Save", command=save).grid(row=99, column=1)

    def _log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _run(self):
        if not self.paths["lib"].get(): return messagebox.showerror("Error", "Set MPTHub Library Folder first.")
        
        payload = {"library_path": self.paths["lib"].get(), "items": self.run_items}
        
        self.run_btn.config(state="disabled")
        self.log_text.config(state="normal"); self.log_text.delete("1.0", "end"); self.log_text.config(state="disabled")

        def worker():
            # CALL THE FUNCTION FROM THE OTHER FILE
            mpthub_headless.run_analysis(payload, status_callback=self._log)
            
            self.run_btn.config(state="normal")
            messagebox.showinfo("Done", "Batch analysis complete.")

        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__": App().mainloop()