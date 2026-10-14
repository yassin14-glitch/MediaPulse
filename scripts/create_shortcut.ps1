$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "MediaPulse Pro.lnk"
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "D:\Work\Projects\dist\MediaPulsePro\MediaPulsePro.exe"
$shortcut.WorkingDirectory = "D:\Work\Projects\dist\MediaPulsePro"
$shortcut.IconLocation = "D:\Work\Projects\dist\MediaPulsePro\assets\icon.ico"
$shortcut.Description = "MediaPulse Pro - Universal Multimedia Video & Audio Downloader"
$shortcut.Save()
Write-Output "Shortcut created at $shortcutPath"
