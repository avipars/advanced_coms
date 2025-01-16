@echo off
rem sslkeylog 
rem for decrypting your own https traffic via wireshark
set SSLKEYLOGFILE=%USERPROFILE%\Desktop\keylogfile.txt
start firefox rem or can start firefox like this start "" "C:\Program Files\Mozilla Firefox\firefox.exe"

rem Open File Explorer to the directory of the key log file
explorer.exe /e,C:\Users\blah\Desktop

rem Keep the command prompt window open
cmd /k
