' ALittleSurprise.vbs
' Advanced, safe, local "surprise" using a temp HTA GUI (no Cancel buttons, no shutdown)
Option Explicit

Dim fso, shell, tmpFolder, scriptFolder, htaPath, notePath, logPath, audioPath
Dim htaContent, totalSeconds, userName, compName, ts

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' === configuration ===
scriptFolder = fso.GetAbsolutePathName(".") & "\"            ' folder where the VBS runs
tmpFolder = shell.ExpandEnvironmentStrings("%TEMP%") & "\"
htaPath = tmpFolder & "ALittleSurprise_UI.hta"
notePath = scriptFolder & "HiddenNote.txt"
logPath = scriptFolder & "LoveLetter_Log.txt"
audioPath = scriptFolder & "background.wav"     ' optional, place a wav file in same folder
totalSeconds = 300                              ' 5 minutes
userName = shell.ExpandEnvironmentStrings("%USERNAME%")
compName = shell.ExpandEnvironmentStrings("%COMPUTERNAME%")
ts = Now

' === logging helper ===
Call AppendLog("Script started at " & ts)

' === create hidden note (auditable, harmless) ===
On Error Resume Next
Dim noteFile
Set noteFile = fso.CreateTextFile(notePath, True)
noteFile.WriteLine "💌 A Quiet Note"
noteFile.WriteLine "-----------------"
noteFile.WriteLine "Created on: " & Now
noteFile.WriteLine ""
noteFile.WriteLine "Dear reader,"
noteFile.WriteLine "Curiosity can be gentle. The kindest code leaves no scars."
noteFile.WriteLine "Be kind to the machine that keeps your secrets."
noteFile.Close
fso.GetFile(notePath).Attributes = fso.GetFile(notePath).Attributes Or 2  ' make hidden (2 = hidden)
Call AppendLog("Hidden note created at " & notePath)
On Error GoTo 0

' === build HTA contents (embedded JS handles countdown & UI) ===
htaContent = _
"<!DOCTYPE html>" & vbCrLf & _
"<html>" & vbCrLf & _
"<head>" & vbCrLf & _
"  <title>A Little Surprise</title>" & vbCrLf & _
"  <HTA:APPLICATION ID='loveApp' APPLICATIONNAME='ALittleSurprise' BORDER='thin' " & _
"SCROLL='no' SINGLEINSTANCE='yes' SYSMENU='no' SHOWINTASKBAR='yes' />" & vbCrLf & _
"  <style>" & vbCrLf & _
"    body { font-family: Segoe UI, Tahoma, Arial; background:#111; color:#f8f1f1; margin:0; padding:20px; }" & vbCrLf & _
"    .card { background: linear-gradient(135deg,#2b2b2b,#151515); padding:18px; border-radius:12px; width:560px; margin:auto; box-shadow: 0 8px 30px rgba(0,0,0,0.6);} " & vbCrLf & _
"    h1 { margin:0 0 8px 0; font-size:20px; }" & vbCrLf & _
"    p { margin:6px 0 12px 0; color:#cfcfcf }" & vbCrLf & _
"    #bar { width:100%; height:18px; background:#333; border-radius:9px; overflow:hidden; }" & vbCrLf & _
"    #fill { height:100%; width:0%; background: linear-gradient(90deg,#ff5f7a,#ffb86b); transition: width 0.6s ease; }" & vbCrLf & _
"    #timeleft { font-weight:600; margin-top:10px; }" & vbCrLf & _
"    .foot { margin-top:14px; text-align:right; }" & vbCrLf & _
"    button { padding:8px 12px; border-radius:8px; border:0; background:#2d89ef; color:white; font-weight:600; cursor:pointer; }" & vbCrLf & _
"    button:active { transform: translateY(1px);} " & vbCrLf & _
"  </style>" & vbCrLf & _
"</head>" & vbCrLf & _
"<body>" & vbCrLf & _
"  <div class='card'>" & vbCrLf & _
"    <h1>♥ A Little Surprise ♥</h1>" & vbCrLf & _
"    <p>I love you ❤️<br/>This is a calm, local surprise — for your eyes only.</p>" & vbCrLf & _
"    <div id='bar'><div id='fill'></div></div>" & vbCrLf & _
"    <div id='timeleft'>Starting soon...</div>" & vbCrLf & _
"    <div class='foot'><button id='btnOk' onclick='onOk()' style='display:none'>Close</button></div>" & vbCrLf & _
"  </div>" & vbCrLf & _
"" & vbCrLf & _
"<script language='javascript'>" & vbCrLf & _
"  (function(){ " & vbCrLf & _
"    var total = " & CStr(totalSeconds) & "; " & vbCrLf & _
"    var remaining = total; " & vbCrLf & _
"    var fill = document.getElementById('fill'); " & vbCrLf & _
"    var timeleft = document.getElementById('timeleft'); " & vbCrLf & _
"    var btn = document.getElementById('btnOk'); " & vbCrLf & _
"    var tick = 1000; " & vbCrLf & _
"    var started = new Date(); " & vbCrLf & _
"    " & vbCrLf & _
"    function fmt(s) {" & vbCrLf & _
"      var m = Math.floor(s/60); var sec = s%60; if(sec<10) sec='0'+sec; return m+':'+sec;" & vbCrLf & _
"    }" & vbCrLf & _
"    " & vbCrLf & _
"    function step() {" & vbCrLf & _
"      var pct = Math.round(( (total - remaining) / total) * 100 ); " & vbCrLf & _
"      fill.style.width = pct + '%'; " & vbCrLf & _
"      timeleft.innerHTML = 'Time left: ' + fmt(remaining) + ' (' + pct + '%)'; " & vbCrLf & _
"      if(remaining<=0) {" & vbCrLf & _
"         timeleft.innerHTML = 'All done. Thank you.'; " & vbCrLf & _
"         fill.style.width = '100%'; " & vbCrLf & _
"         btn.style.display = 'inline-block'; " & vbCrLf & _
"         // play gentle chime through HTA (if allowed)" & vbCrLf & _
"         try { var snd = document.getElementById('aud'); if(snd) snd.play(); } catch(e){}" & vbCrLf & _
"         return; " & vbCrLf & _
"      }" & vbCrLf & _
"      remaining--; " & vbCrLf & _
"      setTimeout(step, tick); " & vbCrLf & _
"    }" & vbCrLf & _
"    // initial slight delay so UI settles" & vbCrLf & _
"    setTimeout(step, 800);" & vbCrLf & _
"  })();" & vbCrLf & _
"  function onOk() { window.close(); }" & vbCrLf & _
"</script>" & vbCrLf

' optional audio element injection if file present
If fso.FileExists(audioPath) Then
  htaContent = htaContent & "<audio id='aud' src='file:///" & Replace(audioPath, "\", "/") & "' preload='auto'></audio>" & vbCrLf
End If

htaContent = htaContent & vbCrLf & _
"</body>" & vbCrLf & _
"</html>"

' === write HTA to temp and run it ===
On Error Resume Next
Dim htaFile
Set htaFile = fso.CreateTextFile(htaPath, True)
htaFile.Write htaContent
htaFile.Close
Call AppendLog("HTA UI written to " & htaPath)
On Error GoTo 0

' run HTA (wait until closed)
Dim ret
ret = shell.Run("mshta.exe " & Chr(34) & htaPath & Chr(34), 1, True)

Call AppendLog("HTA closed by user. Cleaning up temporary HTA.")
' remove the temp HTA quietly
On Error Resume Next
If fso.FileExists(htaPath) Then fso.DeleteFile(htaPath), True
On Error GoTo 0

' final friendly message (VBScript-level)
MsgBox "The surprise has finished. A hidden note was placed here:" & vbCrLf & vbCrLf & notePath, vbInformation + vbOKOnly, "All Done"

Call AppendLog("Script finished at " & Now)
' === helpers ===
Sub AppendLog(text)
  On Error Resume Next
  Dim lf
  Set lf = fso.OpenTextFile(logPath, 8, True)
  lf.WriteLine "[" & Now & "] " & text
  lf.Close
  On Error GoTo 0
End Sub

' === end ===
