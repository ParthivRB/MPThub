# 🔬 MPTHub Automated Batch Processor

This repository provides a streamlined, portable Graphical User Interface (GUI) wrapper for performing high-throughput Microparticle Tracking (MPT) analysis using the external `mpthub` library. This setup ensures clean terminal output, precise control over processing parameters, and easy setup across different machines.

---

## ✨ Features

* **GUI Interface:** Easily manage input paths and analysis parameters via a user-friendly Tkinter GUI (`config_gui.py`).
* **Persistent Memory:** The application remembers the last folders used for data and configuration files, reducing setup time.
* **Customization:** Set global defaults (Delta_t, Filter, Temperature, etc.) and apply them to all files.
* **Granular Control (New):** Double-click any file in the run list to override its parameters individually.
* **Clean Execution:** Suppresses internal Python warnings (Pandas/NumPy) and fixes the common "missing asset" crash by dynamically managing the working directory.
* **Portable Configuration:** Configuration is handled via `run_config.json`, which includes the dynamic path to the `mpthub` library, making the script location-agnostic.

---

## ⚙️ Setup and Installation

### Prerequisites

1.  **Python 3.9+:** Required for modern syntax and dependency compatibility.
2.  **External `mpthub-main` Library:** You must have the main `mpthub-main` source code downloaded on your machine, as this script uses it as an external dependency.

### Installation Steps

1.  **Clone or Download:** Get the contents of this repository onto your machine.
2.  **Open Terminal:** Navigate into the main project directory where `requirements.txt` is located.

3.  **Create and Activate Virtual Environment (Recommended)**
    ```bash
    # 1. Create the environment
    python3 -m venv .venv

    # 2. Activate the environment
    source .venv/bin/activate
    ```

4.  **Install Dependencies**
    ```bash
    # This installs all necessary scientific libraries (pandas, matplotlib, trackpy, etc.)
    pip install -r requirements.txt
    ```

---

## 🚀 Usage Guide

The entire process is launched from the main GUI script.

### 1. Launch the GUI

Make sure your `.venv` is active, then run:

```
python mpthub_batch.py
```

### 2. Initial Setup (Locate MPTHub Library)
When the GUI opens, the first step is to tell the program where the mpthub-main source code folder is located on your computer.

Click the "Locate..." button next to the MPTHub Library Folder field.

Select the root directory of your downloaded mpthub-main folder (e.g., ~/Downloads/mpthub-main). (This path is saved permanently using the memory feature.)

### 3. Scan Inputs (Tab 1)
Size Excel File: Select the .xlsx file containing your particle size data (folder name to size map).

Data Folder: Select the root directory containing all your processed .csv data files.

Click SCAN FILES. This builds the list of files to be processed and applies the current global settings.

### 4. Adjust Settings
Global Settings (Tab 2): Use this tab to change default parameters like Delta_t or Temperature. Remember to click Update Defaults after making changes.

Per-File Overrides (Tab 3): After scanning, you can double-click any row in the list to open a dedicated editor and modify settings for that specific file.

### 5. Run Batch (Tab 3)
Click the RUN BATCH button.

The terminal will provide clean, minimalistic feedback:

```
--- Processing 25 Files ---
⚙️ PLGAPEGNP_CVM 1.csv... ✅ Done
⚙️ PLGAPEGNP_CVM 2.csv... ✅ Done
...
All tasks completed.
```

📂 Project Structure
File	Description
mpthub_batch.py	Primary entry point; launches the GUI.
config_gui.py	GUI logic. Handles scanning, setting overrides, and saving the execution configuration.
mpthub_headless.py	Execution Engine. Reads run_config.json, manages environment paths, executes mpt analysis, and ensures clean terminal logging.
requirements.txt	Lists all Python dependencies (pandas, matplotlib, trackpy, etc.).
app_settings.json	Created on first run. Stores the last used folder paths and the MPTHub library location.
run_config.json	Created by GUI. The execution payload containing all file-specific parameters sent to the headless script.
