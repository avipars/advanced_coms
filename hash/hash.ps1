# SHA hash via powershell
Set-Variable -Name hello -Value (Get-FileHash -Path "C:\lab5\hi.txt" -Algorithm SHA256)