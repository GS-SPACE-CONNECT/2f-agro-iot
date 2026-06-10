@echo off
title 2F-AGRO - Olho na Folha (teste de camera)
echo ============================================
echo  2F-AGRO - Olho na Folha
echo  Abrindo a webcam... aponte para uma folha.
echo  Pressione Q na janela de video para sair.
echo ============================================
echo.
cd /d C:\Users\jotin\Downloads\GS\repos\2f-agro-iot
C:\Users\jotin\Downloads\GS\.venv-iot-test\Scripts\python.exe olho_na_folha.py --source 0 --no-api
echo.
echo (Se aparecer "Camera index out of range":
echo  1. feche apps que usam a webcam - OBS, Teams, Zoom, navegador;
echo  2. confira se o venv NAO usa o Python da Microsoft Store - ele e
echo     bloqueado pelo Windows de acessar a camera. Use o do python.org.)
pause
