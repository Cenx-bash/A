from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from datetime import datetime
import json
import os
import pathlib
import threading
import queue
import csv
import sys
import subprocess
import platform
import traceback

# -----------------------
# Configuration
# -----------------------
HERE = pathlib.Path(__file__).resolve().parent
LOG_FILE = HERE / "typing_log.jsonl"
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB rotate
LOG_BACKUP_TEMPLATE = HERE / "typing_log_{ts}.jsonl"
ENCODING = "utf-8"

_log_queue: "queue.Queue[dict]" = queue.Queue()
_writer_stop = threading.Event()
_writer_thread: threading.Thread | None = None
_writer_lock = threading.Lock()

# -----------------------
# Writer thread
# -----------------------
def log_writer_worker():
    """Consume events and write to file."""
    while not _writer_stop.is_set() or not _log_queue.empty():
        try:
            entry = _log_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        try:
            _rotate_if_needed()
            with open(LOG_FILE, "a", encoding=ENCODING) as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            traceback.print_exc(file=sys.stderr)
        finally:
            _log_queue.task_done()

def start_writer():
    global _writer_thread
    if _writer_thread is None or not _writer_thread.is_alive():
        _writer_stop.clear()
        _writer_thread = threading.Thread(target=log_writer_worker, daemon=True)
        _writer_thread.start()

def stop_writer_and_flush(timeout: float = 3.0):
    _writer_stop.set()
    if _writer_thread:
        _writer_thread.join(timeout=timeout)

def _rotate_if_needed():
    """Rotate log when too large."""
    with _writer_lock:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size >= MAX_LOG_SIZE_BYTES:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = LOG_BACKUP_TEMPLATE.with_name(LOG_BACKUP_TEMPLATE.name.replace("{ts}", ts))
            LOG_FILE.rename(dest)

def enqueue_entry(entry: dict):
    start_writer()
    try:
        _log_queue.put_nowait(entry)
    except queue.Full:
        print("⚠️ Log queue full, entry dropped", file=sys.stderr)

# -----------------------
# App class
# -----------------------
class TypingRecorderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NOTE PAD — Linux Edition 🐧")
        self.root.geometry("850x550")
        self.recording = True
        self.key_counts: dict[str, int] = {}
        self.total_keys = 0
        self._preview_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self._build_ui()
        self.txt.bind("<Key>", self._on_key)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._update_status()

    def _build_ui(self):
        lbl = tk.Label(self.root, text="Focus here and type. Only this window is recorded.", font=("Segoe UI", 11))
        lbl.pack(pady=(10,5))

        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(control_frame, text="Pause", width=10, command=self.toggle_pause).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Show Log", width=10, command=self.show_log).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Stats", width=8, command=self.show_stats).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Export CSV", width=10, command=self.export_csv).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Clear Log", width=10, command=self.clear_log).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Open Folder", width=12, command=self.open_log_folder).pack(side=tk.RIGHT, padx=5)

        self.txt = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Consolas", 12))
        self.txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        status_frame = tk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(status_frame, textvariable=self._preview_var, fg="green", anchor="w").pack(side=tk.LEFT)
        tk.Label(status_frame, textvariable=self.status_var, anchor="e").pack(side=tk.RIGHT)

    # -----------------------
    # Events
    # -----------------------
    def _on_key(self, event: tk.Event):
        if not self.recording:
            return
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "key_sym": str(event.keysym),
            "char": event.char if event.char.isprintable() else "",
        }
        enqueue_entry(entry)
        self.total_keys += 1
        self.key_counts[entry["key_sym"]] = self.key_counts.get(entry["key_sym"], 0) + 1
        self._preview_var.set(f"Last: {entry['key_sym']}  •  Total: {self.total_keys}")
        self.root.after(2500, lambda: self._preview_var.set(""))
        self._update_status()

    def toggle_pause(self):
        self.recording = not self.recording
        self._update_status()

    def _update_status(self):
        state = "⏺ Recording" if self.recording else "⏸ Paused"
        self.status_var.set(f"{state} | Keys: {self.total_keys}")

    # -----------------------
    # Utilities
    # -----------------------
    def show_log(self):
        win = tk.Toplevel(self.root)
        win.title("Recorded Log")
        win.geometry("800x500")
        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True)
        if LOG_FILE.exists():
            text.insert("1.0", LOG_FILE.read_text(encoding=ENCODING))
        else:
            text.insert("1.0", "(No log file yet)")
        text.configure(state="disabled")

    def show_stats(self):
        win = tk.Toplevel(self.root)
        win.title("Typing Stats")
        win.geometry("400x400")
        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 10))
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", f"Total keys: {self.total_keys}\n\nTop keys:\n")
        for k, v in sorted(self.key_counts.items(), key=lambda kv: kv[1], reverse=True):
            txt.insert(tk.END, f"{k}: {v}\n")
        txt.configure(state="disabled")

    def export_csv(self):
        if not LOG_FILE.exists():
            messagebox.showinfo("No log", "No log to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(LOG_FILE, "r", encoding=ENCODING) as src, open(path, "w", newline="", encoding=ENCODING) as dest:
            writer = csv.writer(dest)
            writer.writerow(["timestamp", "key_sym", "char"])
            for line in src:
                try:
                    obj = json.loads(line)
                    writer.writerow([obj.get("ts",""), obj.get("key_sym",""), obj.get("char","")])
                except:
                    continue
        messagebox.showinfo("Exported", f"Saved CSV to:\n{path}")

    def clear_log(self):
        if messagebox.askyesno("Clear log", "Delete current log file?"):
            LOG_FILE.unlink(missing_ok=True)
            messagebox.showinfo("Cleared", "Log file removed.")

    def open_log_folder(self):
        try:
            if platform.system() == "Linux":
                subprocess.Popen(["xdg-open", str(HERE)])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(HERE)])
            else:
                subprocess.Popen(["explorer", str(HERE)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def _on_close(self):
        stop_writer_and_flush(3.0)
        self.root.destroy()

# -----------------------
# Entry
# -----------------------
if __name__ == "__main__":
    try:
        start_writer()
        root = tk.Tk()
        app = TypingRecorderApp(root)
        root.mainloop()
    finally:
        stop_writer_and_flush(3.0)
