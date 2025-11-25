import os, sys, json, warnings, contextlib
from pathlib import Path

# --- CORE LOGIC ---
def run_analysis(config_data, status_callback=None):
    """
    Runs the analysis. 
    Called by config_gui.py inside a thread.
    """
    def log(msg):
        print(msg)
        if status_callback: status_callback(msg)

    # 1. SMART PATH FIX
    raw_path = config_data.get("library_path", "")
    if not raw_path: return log("❌ Error: No library path provided.")
    
    lib_path = Path(raw_path)
    # If user selected the inner 'mpt' folder, move up automatically
    if lib_path.name == "mpt": lib_path = lib_path.parent
    
    MPTHUB_DIR = str(lib_path)
    if MPTHUB_DIR not in sys.path: sys.path.insert(0, MPTHUB_DIR)

    # 2. SILENCE WARNINGS
    warnings.filterwarnings("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

    try:
        from mpt.database import persist
        from mpt.model import Analysis, General
    except ImportError as e:
        log(f"❌ Error: Could not load 'mpt' library.")
        log(f"   Debug details: {e}")
        log(f"   Looking in: {MPTHUB_DIR}")
        return

    # 3. HELPER CLASSES
    @contextlib.contextmanager
    def safe_env(path):
        with open(os.devnull, "w") as null:
            old_out, old_err, old_cwd = sys.stdout, sys.stderr, os.getcwd()
            sys.stdout, sys.stderr = null, null
            try:
                os.chdir(path)
                yield
            finally:
                sys.stdout, sys.stderr = old_out, old_err
                os.chdir(old_cwd)

    class HeadlessParent:
        def __init__(self, path):
            self.general = General()
            if hasattr(self.general, "config"):
                self.general.config.save_folder = str(path)
                self.general.update()
        def show_message(self, *a, **k): pass

    # 4. EXECUTE
    items = config_data.get("items", [])
    log(f"--- Processing {len(items)} Files ---")

    for cfg in items:
        path = Path(cfg["file_path"])
        if not path.exists(): continue
        
        log(f"⚙️  {path.name}...")

        try:
            dest = path.parent / path.stem
            dest.mkdir(exist_ok=True)
            persist()

            a = Analysis()
            c = a.config
            val = lambda x: float(x) if x else 0.0
            
            c.p_size = val(cfg.get("size"))
            c.delta_t = val(cfg.get("delta_t"))
            c.fps = 1000.0 / c.delta_t
            c.min_frames = val(cfg.get("filter"))
            c.total_frames = val(cfg.get("frames"))
            c.width_px = val(cfg.get("width_px"))
            c.width_si = val(cfg.get("width_um"))
            c.time = val(cfg.get("analysis_time"))
            c.temperature_C = val(cfg.get("temperature"))
            a.update()

            with safe_env(MPTHUB_DIR):
                a.load_reports([str(path)])
                if hasattr(a, "get_valid_trajectories"): a.get_valid_trajectories()
                if hasattr(a, "start_trackpy"): a.start_trackpy()
                a.export(HeadlessParent(dest))
                a.summary = a.summary.iloc[0:0]
            
            log(f"   ✅ Done")

        except Exception as e:
            log(f"   ❌ Error: {e}")

    log("\nAll tasks completed.")

# If run directly (for debugging), load the file
if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent
    RUN_CONFIG = BASE_DIR / "run_config.json"
    if RUN_CONFIG.exists():
        with open(RUN_CONFIG) as f:
            run_analysis(json.load(f))