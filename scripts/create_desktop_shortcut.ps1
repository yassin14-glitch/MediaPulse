# Creates a Windows Desktop shortcut for MediaPulse Pro
$targetExe = "D:\Work\Projects\dist\MediaPulsePro\MediaPulsePro.exe"
$iconPath = "D:\Work\Projects\assets\icon.ico"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutFile = Join-Path $desktopPath "MediaPulse Pro.lnk"

$wscript = New-Object -ComObject WScript.Shell
$shortcut = $wscript.CreateShortcut($shortcutFile)
$shortcut.TargetPath = $targetExe
$shortcut.WorkingDirectory = [System.IO.Path]::GetDirectoryName($targetExe)
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = "MediaPulse Pro - Universal Video & Audio Downloader"
$shortcut.Save()

Write-Host "Desktop shortcut created successfully at: $shortcutFile"
