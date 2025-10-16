#!/usr/bin/env python3
"""
typing_recorder_improved.py
Consent-based keyboard capture demo (only captures while this window is focused).

Improvements over the basic version:
- Background writer thread and queue to avoid blocking the UI on disk writes.
- Log rotation (max file size threshold).
- Pause / Resume recording.
- Live key preview and per-key frequency counters (in-memory).
- Export log to CSV, view & search recorded entries.
- Safe shutdown flush of pending logs and graceful error handling.
- Clear, explicit consent on start; never captures system-wide keystrokes.
"""

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
import traceback

# -----------------------
# Configuration
# -----------------------
HERE = pathlib.Path(__file__).resolve().parent
LOG_FILE = HERE / "typing_log.jsonl"
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024   # rotate at 5 MB
LOG_BACKUP_TEMPLATE = HERE / "typing_log_{ts}.jsonl"
ENCODING = "utf-8"

# -----------------------
# Threaded log writer
# -----------------------
_log_queue: "queue.Queue[dict]" = queue.Queue()
_writer_stop = threading.Event()
_writer_thread: threading.Thread | None = None
_writer_lock = threading.Lock()  # for rotation

def log_writer_worker():
    """Background writer: consumes from queue and appends to JSONL file."""
    try:
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
                # Never crash the thread; print to stderr for debugging
                print("Log writer error:", file=sys.stderr)
                traceback.print_exc()
            finally:
                _log_queue.task_done()
    except Exception:
        print("Log writer fatal error:", file=sys.stderr)
        traceback.print_exc()

def start_writer():
    global _writer_thread
    if _writer_thread is None or not _writer_thread.is_alive():
        _writer_stop.clear()
        _writer_thread = threading.Thread(target=log_writer_worker, daemon=True, name="TypingLogWriter")
        _writer_thread.start()

def stop_writer_and_flush(timeout: float = 3.0):
    """Signal writer to stop and wait for queue to drain."""
    _writer_stop.set()
    if _writer_thread:
        _writer_thread.join(timeout=timeout)

def _rotate_if_needed():
    """Rotate log file if it exceeds MAX_LOG_SIZE_BYTES. This uses a lock to avoid races."""
    with _writer_lock:
        try:
            if LOG_FILE.exists() and LOG_FILE.stat().st_size >= MAX_LOG_SIZE_BYTES:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = LOG_BACKUP_TEMPLATE.with_name(LOG_BACKUP_TEMPLATE.name.replace("{ts}", ts))
                LOG_FILE.rename(dest)
        except Exception:
            # ignore rotate errors (we'll still try to write)
            traceback.print_exc(file=sys.stderr)

def enqueue_entry(entry: dict):
    """Place entry into queue for background write."""
    start_writer()
    try:
        _log_queue.put_nowait(entry)
    except queue.Full:
        # extremely unlikely: drop entry but keep app alive
        print("Log queue full; dropping entry", file=sys.stderr)

# -----------------------
# App (Tkinter)
# -----------------------
class TypingRecorderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Typing Recorder — Consent-based demo (focus-only)")
        self.root.geometry("820x520")
        # State
        self.recording = True
        self.key_counts: dict[str, int] = {}
        self.total_keys = 0
        # Build UI
        self._build_menu()
        self._build_main()
        # Bindings
        self.txt.bind("<Key>", self._on_key)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        # Last preview text
        self._preview_var.set("")
        # show initial status
        self._update_status()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=False)
        filemenu.add_command(label="Export log to CSV...", command=self.export_csv)
        filemenu.add_command(label="Clear log file", command=self.clear_log_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=filemenu)

        toolsmenu = tk.Menu(menubar, tearoff=False)
        toolsmenu.add_command(label="View Log", command=self.show_log)
        toolsmenu.add_command(label="View Stats", command=self.show_stats)
        menubar.add_cascade(label="Tools", menu=toolsmenu)

        helpmenu = tk.Menu(menubar, tearoff=False)
        helpmenu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menubar)

    def _build_main(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=(8, 2))

        lbl = tk.Label(top_frame, text="Focus this box and type. Keys are recorded locally (focused window only).", font=("Segoe UI", 11))
        lbl.pack(side=tk.LEFT, padx=(4,0))

        ctrl_frame = tk.Frame(self.root)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=(0,8))

        self._preview_var = tk.StringVar()
        preview_lbl = tk.Label(ctrl_frame, textvariable=self._preview_var, font=("Consolas", 11), fg="#0b6623")
        preview_lbl.pack(side=tk.LEFT, padx=(4,8))

        self.status_var = tk.StringVar()
        status_lbl = tk.Label(ctrl_frame, textvariable=self.status_var, anchor="w")
        status_lbl.pack(side=tk.LEFT, padx=(8,4))

        btn_frame = tk.Frame(ctrl_frame)
        btn_frame.pack(side=tk.RIGHT)
        self.pause_btn = tk.Button(btn_frame, text="Pause", width=10, command=self.toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Show Log", command=self.show_log, width=10).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Stats", command=self.show_stats, width=8).pack(side=tk.LEFT, padx=6)

        # Scrolled text for typing
        self.txt = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=18, font=("Consolas", 12))
        self.txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,8))

        # Bottom frame with quick controls
        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=10, pady=(0,10))
        tk.Button(bottom, text="Clear UI Text", command=lambda: self.txt.delete("1.0", tk.END)).pack(side=tk.LEFT)
        tk.Button(bottom, text="Open Log Folder", command=self.open_log_folder).pack(side=tk.LEFT, padx=6)
        tk.Button(bottom, text="Clear Stats", command=self.clear_stats).pack(side=tk.LEFT, padx=6)
        tk.Button(bottom, text="Help / Consent", command=self._show_consent_note).pack(side=tk.RIGHT)

    # -----------------------
    # Event handling
    # -----------------------
    def _on_key(self, event: tk.Event):
        """Only called when widget is focused & receives key events."""
        # Don't record if paused
        if not self.recording:
            return

        try:
            ts = datetime.utcnow().isoformat() + "Z"
            key_sym = str(event.keysym)
            char = event.char if event.char and event.char.isprintable() else ""
            widget = str(event.widget)

            entry = {
                "ts": ts,
                "key_sym": key_sym,
                "char": char,
                "widget": widget
            }

            # queue entry to be written
            enqueue_entry(entry)

            # update in-memory stats & preview
            self.total_keys += 1
            self.key_counts[key_sym] = self.key_counts.get(key_sym, 0) + 1
            self._preview_var.set(f"Last: {key_sym} {repr(char)}  •  Total keys: {self.total_keys}")

            # keep a short preview visible for a moment
            self.root.after(2500, lambda: self._preview_var.set(""))
            self._update_status()
        except Exception:
            traceback.print_exc()

    # -----------------------
    # Commands & utilities
    # -----------------------
    def toggle_pause(self):
        self.recording = not self.recording
        self.pause_btn.config(text="Resume" if not self.recording else "Pause")
        self._update_status()

    def _update_status(self):
        status = "Recording" if self.recording else "Paused"
        status += f" — keys recorded: {self.total_keys}"
        self.status_var.set(status)

    def show_log(self):
        """Open the JSONL log in a viewer with search."""
        viewer = tk.Toplevel(self.root)
        viewer.title("Recorded Entries (local file)")
        viewer.geometry("820x520")
        text = scrolledtext.ScrolledText(viewer, wrap=tk.WORD, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True)

        search_frame = tk.Frame(viewer)
        search_frame.pack(fill=tk.X, padx=6, pady=(0,6))
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6,6))
        def do_search():
            s = search_var.get().strip().lower()
            text.tag_remove("hl", "1.0", tk.END)
            if not s:
                return
            idx = "1.0"
            while True:
                idx = text.search(s, idx, nocase=True, stopindex=tk.END)
                if not idx:
                    break
                end = f"{idx}+{len(s)}c"
                text.tag_add("hl", idx, end)
                idx = end
            text.tag_config("hl", background="yellow")
        tk.Button(search_frame, text="Find", command=do_search).pack(side=tk.LEFT)

        try:
            if LOG_FILE.exists():
                with open(LOG_FILE, "r", encoding=ENCODING) as fh:
                    content = fh.read()
                # Pretty format JSONL lines for readability
                pretty = []
                for line in content.splitlines():
                    try:
                        obj = json.loads(line)
                        pretty.append(json.dumps(obj, ensure_ascii=False, indent=2))
                    except Exception:
                        pretty.append(line)
                text.insert("1.0", "\n\n".join(pretty))
            else:
                text.insert("1.0", "(No log file found yet)")
        except Exception as e:
            text.insert("1.0", f"Error reading log file: {e}\n")
            traceback.print_exc()
        text.configure(state="disabled")

    def show_stats(self):
        """Show top keys and simple stats in a dialog."""
        top = tk.Toplevel(self.root)
        top.title("Typing Statistics")
        top.geometry("480x420")
        frm = tk.Frame(top)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        lbl = tk.Label(frm, text=f"Total keys recorded (this session): {self.total_keys}", font=("Segoe UI", 11))
        lbl.pack(pady=(0,8))
        # Top 20 keys
        items = sorted(self.key_counts.items(), key=lambda kv: kv[1], reverse=True)
        text = scrolledtext.ScrolledText(frm, height=18, font=("Consolas", 11))
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", "Key\tCount\n----\t-----\n")
        for k, v in items[:200]:
            text.insert(tk.END, f"{k}\t{v}\n")
        text.configure(state="disabled")

    def export_csv(self):
        """Export log JSONL to CSV via Save dialog."""
        if not LOG_FILE.exists():
            messagebox.showinfo("No log", "No log file to export.")
            return
        target = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Export log to CSV")
        if not target:
            return
        try:
            with open(LOG_FILE, "r", encoding=ENCODING) as inf, open(target, "w", newline="", encoding=ENCODING) as outf:
                writer = csv.writer(outf)
                writer.writerow(["ts", "key_sym", "char", "widget"])
                for line in inf:
                    try:
                        obj = json.loads(line)
                        writer.writerow([obj.get("ts",""), obj.get("key_sym",""), obj.get("char",""), obj.get("widget","")])
                    except Exception:
                        # skip malformed lines
                        continue
            messagebox.showinfo("Export complete", f"Exported log to:\n{target}")
        except Exception as e:
            messagebox.showerror("Export failed", f"Failed to export CSV: {e}")
            traceback.print_exc()

    def clear_log_file(self):
        if not LOG_FILE.exists():
            messagebox.showinfo("No log", "No log file to clear.")
            return
        if not messagebox.askyesno("Clear log", "This will delete the current log file. Continue?"):
            return
        try:
            LOG_FILE.unlink(missing_ok=True)
            messagebox.showinfo("Cleared", "Log file removed.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not remove log file: {e}")
            traceback.print_exc()

    def clear_stats(self):
        if messagebox.askyesno("Clear stats", "Reset in-memory counters for this session?"):
            self.key_counts.clear()
            self.total_keys = 0
            self._update_status()

    def open_log_folder(self):
        try:
            import subprocess, platform
            folder = str(HERE)
            if platform.system() == "Windows":
                subprocess.Popen(["explorer", folder])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def _show_about(self):
        messagebox.showinfo("About", "Typing Recorder — improved\nConsent-only, local logging for learning.\nAuthor: you (with guidance)")

    def _show_consent_note(self):
        messagebox.showinfo("Consent Reminder",
            "This app records keys typed INTO ITS WINDOW ONLY.\n"
            "It does NOT capture system-wide keyboard events.\n\n"
            "Use only on machines you control and with explicit consent.")

    def _on_close(self):
        if messagebox.askyesno("Exit", "Quit and flush logs?"):
            try:
                # flush and stop writer
                stop_writer_and_flush(timeout=5.0)
            finally:
                self.root.destroy()

# -----------------------
# Program entrypoint
# -----------------------
def require_consent_and_run():
    # Ask for consent upfront (modal)
    root = tk.Tk()
    root.withdraw()
    consent = messagebox.askyesno("Consent required",
        "This demo will record keys typed into its window and save them locally.\n\n"
        "Do you consent to this on this machine? (Only local, only focused window)")
    if not consent:
        messagebox.showinfo("Cancelled", "Consent not given. Exiting.")
        root.destroy()
        return

    root.deiconify()
    app = TypingRecorderApp(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        require_consent_and_run()
    except Exception:
        traceback.print_exc()
    finally:
        # ensure background writer stops if program exits unexpectedly
        stop_writer_and_flush(timeout=2.0)
