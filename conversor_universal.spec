# -*- mode: python ; coding: utf-8 -*-
# ──────────────────────────────────────────────────────────────────────────────
# conversor_universal.spec  —  PyInstaller spec para Conversor Universal
#
# Como usar:
#   1. Coloque ffmpeg.exe na mesma pasta deste arquivo
#   2. Execute:  python build.py
#      (ou diretamente:  pyinstaller conversor_universal.spec)
#
# NOTA TÉCNICA — pdf2docx / PyMuPDF (fitz):
#   Listar módulos em hiddenimports NÃO é suficiente para o fitz porque ele
#   carrega binários nativos (.pyd, .dll) em tempo de execução via caminhos
#   calculados dinamicamente. A solução correta é usar collect_all(), que
#   empacota TUDO: código Python, dados e binários nativos de uma vez.
# ──────────────────────────────────────────────────────────────────────────────

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# ── FFmpeg bundled ─────────────────────────────────────────────────────────────
_here   = Path(SPECPATH)
_ffmpeg = _here / 'ffmpeg.exe'
_binaries_extra = [(str(_ffmpeg), '.')] if _ffmpeg.exists() else []

# ── Coleta completa: fitz (PyMuPDF) e pdf2docx ────────────────────────────────
# collect_all retorna (datas, binaries, hiddenimports) — captura .pyd, .dll e
# arquivos de dados que o simples hiddenimports nunca alcança.
_d_fitz,     _b_fitz,     _h_fitz     = collect_all('fitz')
_d_pdf2docx, _b_pdf2docx, _h_pdf2docx = collect_all('pdf2docx')

# ── Coleta completa: Pillow ────────────────────────────────────────────────────
_d_pil, _b_pil, _h_pil = collect_all('PIL')

# ── Coleta completa: reportlab ────────────────────────────────────────────────
_d_rl, _b_rl, _h_rl = collect_all('reportlab')

# ── Coleta completa: ebooklib ─────────────────────────────────────────────────
_d_eb, _b_eb, _h_eb = collect_all('ebooklib')

# ── Une todos os dados e binários coletados ───────────────────────────────────
_all_datas    = _d_fitz + _d_pdf2docx + _d_pil + _d_rl + _d_eb
_all_binaries = _binaries_extra + _b_fitz + _b_pdf2docx + _b_pil + _b_rl + _b_eb
_all_hidden   = (
    _h_fitz + _h_pdf2docx + _h_pil + _h_rl + _h_eb
    + collect_submodules('docx')
    + collect_submodules('openpyxl')
    + collect_submodules('pypdf')
    + collect_submodules('striprtf')
    + collect_submodules('py7zr')
    + [
        # PySide6
        'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        # Documentos avulsos
        'pypdf', 'pypdf._crypt_filters',
        'docx', 'docx.oxml', 'docx.oxml.ns',
        'openpyxl', 'openpyxl.styles', 'openpyxl.utils',
        'xlrd',
        'striprtf', 'striprtf.striprtf',
        # Compactados
        'py7zr', 'rarfile',
    ]
)

a = Analysis(
    ['conversor_universal.py'],
    pathex=[str(_here)],
    binaries=_all_binaries,
    datas=_all_datas,
    hiddenimports=_all_hidden,
    hookspath=[str(_here / 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'PyQt5', 'PyQt6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ConversorUniversal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['ffmpeg.exe', 'ffprobe.exe', 'mupdf*.dll', '_mupdf*.pyd'],
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icone.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['ffmpeg.exe', 'ffprobe.exe', 'mupdf*.dll', '_mupdf*.pyd'],
    name='ConversorUniversal',
)
