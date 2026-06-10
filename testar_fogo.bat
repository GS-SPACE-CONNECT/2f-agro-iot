@echo off
title 2F-AGRO - Olho na Lavoura (teste de fogo)
echo ============================================
echo  2F-AGRO - Modo FOGO / queimada
echo  Abrindo a webcam... aponte para uma chama
echo  (vela, isqueiro, video de queimada).
echo  Pressione Q na janela de video para sair.
echo ============================================
echo.
cd /d C:\Users\jotin\Downloads\GS\repos\2f-agro-iot
C:\Users\jotin\Downloads\GS\.venv-iot-test\Scripts\python.exe olho_na_folha.py --source 0 --fogo --no-api
echo.
echo (Dica: chama de verdade "treme" - e isso que o detector usa pra
echo  separar fogo de coisa laranja parada. Aponte para uma vela ou
echo  para um video de queimada no celular.)
pause
