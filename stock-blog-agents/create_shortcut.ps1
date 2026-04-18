$desktop = [System.Environment]::GetFolderPath('Desktop')
$linkPath = Join-Path $desktop 'StockBlogAI.lnk'
$ws = New-Object -comObject WScript.Shell
$sc = $ws.CreateShortcut($linkPath)
$sc.TargetPath = 'C:\Users\user\コード\stock-blog-agents\起動_web.bat'
$sc.WorkingDirectory = 'C:\Users\user\コード\stock-blog-agents'
$sc.IconLocation = 'C:\Windows\System32\SHELL32.dll,14'
$sc.Save()
Write-Host "Shortcut updated: $linkPath"
