import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess, threading, os, sys, signal
from pathlib import Path

APP_TITLE = "OPC → Influx Runner"


# Base dir = folder tempat .exe/.py ini berada
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)).resolve()
PROJECT_DIR = Path(sys.argv[0]).resolve().parent  # lokasi file ini
# Kalau Anda ingin paksa working dir ke folder tertentu, set manual di sini:
WORK_DIR = PROJECT_DIR  # pastikan di sinilah .env & script logger berada

# Path ke script logger & python venv
SCRIPT_PATH = (WORK_DIR / "boiler_kep_to_influx_change_only.py").resolve()
VENV_PY = (WORK_DIR / "venv" / "Scripts" / "python.exe").resolve()

# Jika miss, coba python biasa (fallback)
if not VENV_PY.exists():
    VENV_PY = Path(sys.executable).resolve()

# Flag untuk Windows: perlu NEW_PROCESS_GROUP agar bisa kirim CTRL_BREAK_EVENT
CREATE_NEW_PROCESS_GROUP = 0x00000200 if os.name == "nt" else 0

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.proc = None
        self.reader_th = None

        top = tk.Frame(root); top.pack(padx=10, pady=10)

        self.start_btn = tk.Button(top, text="▶ Start", width=12, bg="green", fg="white", command=self.start)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = tk.Button(top, text="■ Stop", width=12, bg="red", fg="white", state="disabled", command=self.stop)
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.status = tk.Label(top, text="Idle", anchor="w")
        self.status.grid(row=0, column=2, padx=10)

        self.log = scrolledtext.ScrolledText(root, width=100, height=28, bg="#111", fg="#0f0", insertbackground="#0f0")
        self.log.pack(padx=10, pady=(0,10))
        self.log.config(state="disabled")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.log_msg(f"Working dir: {WORK_DIR}\nPython venv: {VENV_PY}\nScript: {SCRIPT_PATH}\n")

    def start(self):
        if not SCRIPT_PATH.exists():
            messagebox.showerror("Error", f"Script not found:\n{SCRIPT_PATH}")
            return
        if not VENV_PY.exists():
            messagebox.showerror("Error", f"Python not found:\n{VENV_PY}")
            return
        if self.proc:
            messagebox.showinfo("Info", "Script already running.")
            return

        self.log_msg(f"Starting: {VENV_PY} {SCRIPT_PATH}\n")
        try:
            self.proc = subprocess.Popen(
                [str(VENV_PY), str(SCRIPT_PATH)],
                cwd=str(WORK_DIR),              # <<< penting agar dotenv baca .env
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=CREATE_NEW_PROCESS_GROUP  # perlu utk CTRL_BREAK
            )
        except Exception as e:
            messagebox.showerror("Start failed", str(e))
            return

        self.reader_th = threading.Thread(target=self._reader, daemon=True)
        self.reader_th.start()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.config(text="Running")

    def _reader(self):
        try:
            for line in self.proc.stdout:
                self.log_msg(line)
        except Exception as e:
            self.log_msg(f"[reader] {e}\n")
        finally:
            self.proc = None
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.status.config(text="Idle")

    def stop(self):
        if not self.proc:
            return
        self.log_msg("Stopping script...\n")
        try:
            if os.name == "nt":
                # kirim Ctrl+Break (butuh CREATE_NEW_PROCESS_GROUP saat start)
                self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.proc.terminate()
        except Exception as e:
            self.log_msg(f"[stop] {e}\n")

    def log_msg(self, msg: str):
        self.log.config(state="normal")
        self.log.insert(tk.END, msg)
        self.log.see(tk.END)
        self.log.config(state="disabled")

    def on_close(self):
        if self.proc:
            if not messagebox.askyesno("Exit", "Script still running. Stop it and exit?"):
                return
            self.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
