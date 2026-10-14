# hooks/hook-pdf2docx.py
# Hook PyInstaller para pdf2docx
# Garante que todos os submódulos e dados sejam incluídos.

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('pdf2docx')
hiddenimports += collect_submodules('pdf2docx')
