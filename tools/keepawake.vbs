' keepawake.vbs - Prevents idle screen lock inside a Windows (Citrix) session
' by periodically sending the harmless F15 key. Fallback for environments where
' PowerShell runs in Constrained Language Mode.
'
' Usage (inside the Citrix session):
'   cscript //nologo keepawake.vbs
'
' Stop with Ctrl+C (or close the console window).

Set wsh = CreateObject("WScript.Shell")

count = 0
Do
    wsh.SendKeys "{F15}"
    count = count + 1
    WScript.Echo Time & " keypress #" & count & " sent"
    WScript.Sleep 60000
Loop
