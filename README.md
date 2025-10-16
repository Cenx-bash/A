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
