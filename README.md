# 🅰️ Project A — Script Collection by Zenn

> "The code doesn’t bite — it whispers."  
> — A digital experiment in poetry, automation, and cybersecurity.

---

## 🌸 Overview
This folder contains a series of **safe experimental scripts** — each designed for learning, creativity, and security exploration.  
They range from playful local “surprises” to system automation tools, written across Windows and Linux.

Each script is crafted for:
- Learning scripting fundamentals  
- Understanding security boundaries  
- Practicing defense and containment  
- Showing that code can also be art  

---

## 🧩 Contents

| Script | Type | Description |
|--------|------|-------------|
| **A_Little_Surprise.bat** | Windows Batch | A playful GUI-based timer script that shows messages, waits, and schedules a harmless reminder. Demonstrates use of PowerShell + Task Scheduler. |
| **A_Little_Surprise.vbs** | Windows VBS | A VBScript rewrite of the same concept with MessageBox dialogs and countdown logic. Runs natively without CMD windows. |
| **LoveLetter_Linux.sh** | Bash (Linux) | A modern, poetic Linux version using Zenity for GUI, progress bars, and optional background audio. Creates a hidden note and a clean log file. |
| **Find-LiveHosts.ps1** | PowerShell | Scans local subnets for reachable hosts via `Test-Connection`. Useful for safe, authorized network exploration. |
| **Check-WinRM.ps1** | PowerShell | Tests if WinRM (Windows Remote Management) is available on target hosts — good for learning about secure remote admin protocols. |
| **Remote-ShowMessage.ps1** | PowerShell | Sends a consent-based message box to a remote machine via `Invoke-Command`. Demonstrates safe use of PowerShell Remoting. |

---

## ⚙️ How to Run

### 🪟 On Windows
```bash
# Run Batch or VBS
A_Little_Surprise.bat
# or
wscript A_Little_Surprise.vbs

# Run PowerShell scripts
powershell -ExecutionPolicy Bypass -File Find-LiveHosts.ps1

🐧 On Linux / Parrot OS
# Make the script executable
chmod +x LoveLetter_Linux.sh

# Run it
./LoveLetter_Linux.sh


💡 If Zenity or Paplay isn’t installed, you can add them with:

sudo apt install zenity pulseaudio-utils

🧠 Purpose

These scripts are part of a cybersecurity learning challenge — a self-defense game where Zenn explores how scripts behave, where flaws appear, and how to stop or patch them safely.
It’s all about understanding, not exploiting.

🛡️ Safety Notes

Every script here is non-destructive.

None of them spread, modify, or delete system files.

You should only run them on machines you control.

Feel free to read or modify the source before executing.

🪶 Credits

Created by Zenn
Ateneo de Naga University

“To code is to speak to machines with poetry.” 🕊️

🌈 Future Ideas

Add a GUI launcher for all scripts

Integrate defense detection logs

Convert more of the Windows tools into portable Linux versions

Build a terminal dashboard to view and run scripts easily
