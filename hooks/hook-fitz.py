# hooks/hook-fitz.py
# Hook PyInstaller para PyMuPDF (fitz)
# Garante que todos os binários nativos e arquivos de dados sejam incluídos.

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('fitz')
