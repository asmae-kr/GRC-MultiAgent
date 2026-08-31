@echo off
REM ============================================================
REM  Lanceur automatique de watcher.py (GRC-MultiAgent)
REM  - Active l'environnement virtuel
REM  - Relance automatiquement le script s'il plante
REM  - Affiche tout a l'ecran (pas de redirection, pour debug facile)
REM ============================================================

cd /d "C:\Users\asmae.kaddar\Desktop\GRC-MultiAgent"

:boucle
echo ============================================
echo Demarrage de watcher.py - %date% %time%
echo ============================================

call .venv\Scripts\activate.bat
python watcher.py

echo ============================================
echo watcher.py s'est arrete - redemarrage dans 10 secondes
echo (Ferme cette fenetre pour tout arreter definitivement)
echo ============================================
timeout /t 10
goto boucle