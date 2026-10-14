#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor Universal de Arquivos
Vídeos • Áudios • Documentos • Compactados • Imagens
Desenvolvido pela Secretaria Escolar
"""

import sys
import os
import csv
import zipfile
import tarfile
import shutil
from pathlib import Path
from html.parser import HTMLParser

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QProgressBar, QFileDialog,
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent

# ─── PALETA DA ESCOLA ────────────────────────────────────────────────────────────
C_PRIMARY = "#9eb89b"
C_LIGHT   = "#cedcca"
C_BG      = "#fefefe"
C_DARK    = "#5c7a59"
C_TEXT    = "#2a3a2a"
C_BORDER  = "#b5ccb2"
C_HOVER   = "#8aab87"
C_ACCENT  = "#4a6e47"
C_ERROR   = "#c0392b"
C_SUCCESS = "#27ae60"

QSS = f"""
* {{ font-family: 'Segoe UI', 'Ubuntu', 'Cantarell', sans-serif; }}
QMainWindow {{ background: {C_BG}; }}
QWidget#root {{ background: {C_BG}; }}
QLabel {{ color: {C_TEXT}; background: transparent; }}
QLabel#title {{ color: {C_ACCENT}; font-size: 20px; font-weight: bold; }}
QLabel#subtitle {{ color: #7a9a7a; font-size: 12px; }}
QLabel#fileinfo {{ color: {C_DARK}; font-size: 13px; font-style: italic; }}
QLabel#status {{ font-size: 13px; }}
QLabel#sig {{ color: {C_BORDER}; font-size: 10px; }}

QFrame#dropzone {{
    background: {C_LIGHT};
    border: 2px dashed {C_PRIMARY};
    border-radius: 16px;
}}

QPushButton#primary {{
    background: {C_PRIMARY};
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#primary:hover {{ background: {C_HOVER}; }}
QPushButton#primary:pressed {{ background: {C_ACCENT}; }}
QPushButton#primary:disabled {{ background: {C_LIGHT}; color: #aaa; }}

QPushButton#secondary {{
    background: transparent;
    color: {C_ACCENT};
    border: 2px solid {C_PRIMARY};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
}}
QPushButton#secondary:hover {{ background: {C_LIGHT}; }}

QComboBox {{
    background: {C_LIGHT};
    color: {C_TEXT};
    border: 2px solid {C_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-width: 160px;
}}
QComboBox:focus {{ border-color: {C_PRIMARY}; }}
QComboBox QAbstractItemView {{
    background: {C_BG};
    color: {C_TEXT};
    selection-background-color: {C_LIGHT};
    border: 1px solid {C_BORDER};
}}
QComboBox::drop-down {{ border: none; width: 20px; }}

QProgressBar {{
    background: {C_LIGHT};
    border: none;
    border-radius: 8px;
    height: 16px;
    text-align: center;
    font-size: 11px;
    color: {C_TEXT};
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {C_DARK}, stop:1 {C_PRIMARY});
    border-radius: 8px;
}}
"""

# ─── PERSISTÊNCIA DE CONFIGURAÇÕES ───────────────────────────────────────────

def load_outdir() -> str:
    """Carrega o diretório de saída salvo nas configurações do sistema."""
    s = QSettings("EscolaExemplo", "ConversorUniversal")
    return s.value("outdir", os.path.expanduser("~"))

def save_outdir(path: str) -> None:
    """Persiste o diretório de saída nas configurações do sistema."""
    s = QSettings("EscolaExemplo", "ConversorUniversal")
    s.setValue("outdir", path)

# ─── DETECÇÃO DO FFMPEG (BUNDLED OU DO SISTEMA) ───────────────────────────────

def get_ffmpeg() -> str:
    """
    Retorna o caminho do executável ffmpeg.
    Prioriza a versão embutida no pacote PyInstaller (.exe).
    """
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
        ff = base / ('ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg')
        if ff.exists():
            return str(ff)
    return 'ffmpeg'

# ─── MAPEAMENTO DE FORMATOS ───────────────────────────────────────────────────

VIDEO_EXT = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv',
             '.webm', '.mpeg', '.m4v', '.ts', '.3gp', '.ogv'}
AUDIO_EXT = {'.mp3', '.wav', '.aac', '.ogg', '.flac',
             '.m4a', '.wma', '.opus', '.aiff', '.alac'}
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.gif',
             '.tiff', '.tif', '.webp', '.ico'}
ZIP_EXT   = {'.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.xz', '.tgz'}
DOC_EXT   = {'.pdf', '.docx', '.doc', '.txt', '.rtf',
             '.xlsx', '.xls', '.csv', '.epub'}

FORMAT_MAP = {
    'video': ['MP4', 'MKV', 'AVI', 'MOV', 'WMV', 'FLV', 'WEBM',
              'GIF', 'MP3', 'WAV', 'AAC', 'OGG', 'OPUS'],
    'audio': ['MP3', 'WAV', 'AAC', 'OGG', 'FLAC', 'M4A', 'OPUS'],
    'image': ['JPG', 'PNG', 'BMP', 'GIF', 'TIFF', 'WEBP', 'ICO'],
    'zip':   ['ZIP', 'TAR', 'TAR.GZ', '7Z'],
    'doc': {
        '.pdf':  ['DOCX', 'TXT'],
        '.docx': ['PDF', 'TXT'],
        '.doc':  ['TXT'],
        '.txt':  ['PDF', 'DOCX'],
        '.rtf':  ['TXT'],
        '.xlsx': ['CSV'],
        '.xls':  ['XLSX', 'CSV'],
        '.csv':  ['XLSX', 'PDF'],
        '.epub': ['TXT'],
    }
}

def detect_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXT: return 'video'
    if ext in AUDIO_EXT: return 'audio'
    if ext in IMAGE_EXT: return 'image'
    if ext in ZIP_EXT:   return 'zip'
    if ext in DOC_EXT:   return 'doc'
    return 'unknown'

def get_formats(path: str) -> list:
    t = detect_type(path)
    if t == 'video': return FORMAT_MAP['video']
    if t == 'audio': return FORMAT_MAP['audio']
    if t == 'image': return FORMAT_MAP['image']
    if t == 'zip':   return FORMAT_MAP['zip']
    if t == 'doc':
        ext = Path(path).suffix.lower()
        return FORMAT_MAP['doc'].get(ext, [])
    return []

def base_stem(path: Path) -> str:
    """Remove todas as extensões compostas. Ex: 'arquivo.tar.gz' -> 'arquivo'."""
    name = path.name
    while '.' in name:
        name = Path(name).stem
    return name


# ─── THREAD DE CONVERSÃO ──────────────────────────────────────────────────────

class ConversionWorker(QThread):
    progress = Signal(int)
    done     = Signal(str)
    failed   = Signal(str)

    def __init__(self, src: str, fmt: str, outdir: str):
        super().__init__()
        self.src    = src
        self.fmt    = fmt.lower()
        self.outdir = outdir

    def run(self):
        try:
            result = self._convert()
            self.done.emit(result)
        except Exception as e:
            self.failed.emit(str(e))

    def _convert(self) -> str:
        src  = Path(self.src)
        fmt  = self.fmt
        base = base_stem(src)
        out  = Path(self.outdir) / f"{base}.{fmt}"
        kind = detect_type(self.src)

        if kind in ('video', 'audio'):
            if fmt == 'gif':
                self._video_to_gif(src, out)
            else:
                self._ffmpeg(src, out)
            return str(out)
        elif kind == 'image':
            self._img(src, out)
            return str(out)
        elif kind == 'zip':
            return self._repack(src, base)
        elif kind == 'doc':
            result = self._doc(src, out, fmt)
            return result or str(out)
        return str(out)

    # ── FFmpeg — video/audio (bundled no .exe) ────────────────────────────────
    def _ffmpeg(self, src: Path, out: Path):
        import subprocess
        self.progress.emit(5)
        flags = 0x08000000 if sys.platform == 'win32' else 0  # CREATE_NO_WINDOW
        cmd = [get_ffmpeg(), '-y', '-i', str(src), str(out)]
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True,
                                creationflags=flags)
        for pct in range(10, 90, 10):
            if proc.poll() is not None:
                break
            self.progress.emit(pct)
            self.msleep(500)
        proc.wait()
        if proc.returncode != 0:
            stderr = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(
                f"FFmpeg falhou na conversao.\nDetalhes: {stderr[-400:]}"
            )
        self.progress.emit(100)

    # ── Video -> GIF (two-pass palette, FFmpeg bundled) ───────────────────────
    def _video_to_gif(self, src: Path, out: Path):
        """
        Converte video em GIF animado com qualidade superior via dois passes:
          1o Gera a paleta de cores otimizada (palettegen)
          2o Aplica a paleta na conversao final (paletteuse)
        Parametros: 15 fps, largura 640 px (mantém proporcao), loop infinito.
        """
        import subprocess, tempfile
        ff = get_ffmpeg()
        flags = 0x08000000 if sys.platform == 'win32' else 0

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
            palette = Path(tf.name)

        try:
            self.progress.emit(5)
            vf_base = "fps=15,scale=640:-1:flags=lanczos"

            # 1o passe: gera paleta otimizada
            r1 = subprocess.run(
                [ff, '-y', '-i', str(src),
                 '-vf', f"{vf_base},palettegen=stats_mode=diff",
                 str(palette)],
                stderr=subprocess.PIPE, text=True, creationflags=flags
            )
            if r1.returncode != 0:
                raise RuntimeError(f"FFmpeg falhou ao gerar paleta.\n{r1.stderr[-300:]}")
            self.progress.emit(50)

            # 2o passe: gera o GIF usando a paleta
            r2 = subprocess.run(
                [ff, '-y', '-i', str(src), '-i', str(palette),
                 '-lavfi', f"{vf_base} [x]; [x][1:v] paletteuse=dither=bayer",
                 '-loop', '0',
                 str(out)],
                stderr=subprocess.PIPE, text=True, creationflags=flags
            )
            if r2.returncode != 0:
                raise RuntimeError(f"FFmpeg falhou ao gerar GIF.\n{r2.stderr[-300:]}")
            self.progress.emit(100)
        finally:
            palette.unlink(missing_ok=True)

    # ── Imagens — Pillow ──────────────────────────────────────────────────────
    def _img(self, src: Path, out: Path):
        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError("Pillow nao instalado.\nUse: pip install Pillow")

        self.progress.emit(20)
        img = Image.open(src)
        self.progress.emit(50)

        fmt_map = {
            '.jpg': 'JPEG', '.jpeg': 'JPEG',
            '.png': 'PNG',  '.bmp': 'BMP',
            '.gif': 'GIF',  '.tiff': 'TIFF', '.tif': 'TIFF',
            '.webp': 'WEBP', '.ico': 'ICO',
        }
        pil_fmt = fmt_map.get(out.suffix.lower(),
                              out.suffix.upper().lstrip('.'))

        if pil_fmt == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')

        if pil_fmt == 'ICO':
            img.thumbnail((256, 256), Image.LANCZOS)

        img.save(str(out), format=pil_fmt)
        self.progress.emit(100)

    # ── Recompactacao ─────────────────────────────────────────────────────────
    def _repack(self, src: Path, base: str) -> str:
        self.progress.emit(5)
        tmp = Path(self.outdir) / "__conversor_tmp__"
        tmp.mkdir(exist_ok=True)
        try:
            ext = ''.join(src.suffixes).lower()
            if src.suffix.lower() == '.zip':
                with zipfile.ZipFile(src) as z:
                    z.extractall(tmp)
            elif src.suffix.lower() == '.tar':
                with tarfile.open(src, 'r:') as t:
                    t.extractall(tmp)
            elif ext in ('.tar.gz', '.tgz'):
                with tarfile.open(src, 'r:gz') as t:
                    t.extractall(tmp)
            elif ext == '.tar.bz2':
                with tarfile.open(src, 'r:bz2') as t:
                    t.extractall(tmp)
            elif src.suffix.lower() == '.7z':
                try:
                    import py7zr
                    with py7zr.SevenZipFile(src, 'r') as z:
                        z.extractall(tmp)
                except ImportError:
                    raise RuntimeError("py7zr nao instalado.\nUse: pip install py7zr")
            elif src.suffix.lower() == '.rar':
                try:
                    import rarfile
                    with rarfile.RarFile(src) as r:
                        r.extractall(tmp)
                except ImportError:
                    raise RuntimeError("rarfile nao instalado.\nUse: pip install rarfile")
            else:
                raise RuntimeError(f"Extracao de '{src.suffix}' nao suportada.")

            self.progress.emit(50)

            fmt = self.fmt
            if fmt == 'zip':
                out = Path(self.outdir) / f"{base}.zip"
                with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
                    for f in tmp.rglob('*'):
                        if f.is_file():
                            z.write(f, f.relative_to(tmp))
            elif fmt == 'tar':
                out = Path(self.outdir) / f"{base}.tar"
                with tarfile.open(out, 'w:') as t:
                    t.add(tmp, arcname='.')
            elif fmt == 'tar.gz':
                out = Path(self.outdir) / f"{base}.tar.gz"
                with tarfile.open(out, 'w:gz') as t:
                    t.add(tmp, arcname='.')
            elif fmt == '7z':
                try:
                    import py7zr
                    out = Path(self.outdir) / f"{base}.7z"
                    with py7zr.SevenZipFile(out, 'w') as z:
                        z.writeall(tmp, '.')
                except ImportError:
                    raise RuntimeError("py7zr nao instalado.\nUse: pip install py7zr")
            else:
                raise RuntimeError(f"Formato '{fmt}' nao suportado para compactados.")

        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        self.progress.emit(100)
        return str(out)

    # ── Documentos — 100% Python, sem LibreOffice ─────────────────────────────
    def _doc(self, src: Path, out: Path, fmt: str) -> str:
        self.progress.emit(10)
        ext = src.suffix.lower()

        # PDF -> DOCX
        if ext == '.pdf' and fmt == 'docx':
            try:
                from pdf2docx import Converter
                cv = Converter(str(src))
                cv.convert(str(out), start=0, end=None)
                cv.close()
            except ImportError:
                raise RuntimeError("pdf2docx nao instalado.\nUse: pip install pdf2docx")

        # PDF -> TXT
        elif ext == '.pdf' and fmt == 'txt':
            try:
                import pypdf
                reader = pypdf.PdfReader(str(src))
                text = '\n'.join((p.extract_text() or '') for p in reader.pages)
                out.write_text(text, encoding='utf-8')
            except ImportError:
                raise RuntimeError("pypdf nao instalado.\nUse: pip install pypdf")

        # TXT -> PDF
        elif ext == '.txt' and fmt == 'pdf':
            self._txt_to_pdf(src, out)

        # TXT -> DOCX
        elif ext == '.txt' and fmt == 'docx':
            try:
                from docx import Document as DocxDoc
                doc = DocxDoc()
                for linha in src.read_text(encoding='utf-8', errors='replace').splitlines():
                    doc.add_paragraph(linha)
                doc.save(str(out))
            except ImportError:
                raise RuntimeError("python-docx nao instalado.\nUse: pip install python-docx")

        # DOCX / DOC -> TXT
        elif ext in ('.docx', '.doc') and fmt == 'txt':
            try:
                from docx import Document as DocxDoc
                doc = DocxDoc(str(src))
                texto = '\n'.join(p.text for p in doc.paragraphs)
                out.write_text(texto, encoding='utf-8')
            except ImportError:
                raise RuntimeError("python-docx nao instalado.\nUse: pip install python-docx")

        # DOCX / DOC -> PDF
        elif ext in ('.docx', '.doc') and fmt == 'pdf':
            try:
                from docx import Document as DocxDoc
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.units import cm

                doc = DocxDoc(str(src))
                styles = getSampleStyleSheet()
                story = []
                for para in doc.paragraphs:
                    txt = para.text.strip()
                    if not txt:
                        story.append(Spacer(1, 0.25 * cm))
                        continue
                    sname = para.style.name
                    if sname.startswith('Heading 1'):
                        story.append(Paragraph(txt, styles['h1']))
                    elif sname.startswith('Heading'):
                        story.append(Paragraph(txt, styles['h2']))
                    else:
                        story.append(Paragraph(txt, styles['Normal']))
                SimpleDocTemplate(str(out), pagesize=A4).build(story)
            except ImportError as ie:
                pkg = 'python-docx' if 'docx' in str(ie) else 'reportlab'
                raise RuntimeError(f"{pkg} nao instalado.\nUse: pip install {pkg}")

        # RTF -> TXT
        elif ext == '.rtf' and fmt == 'txt':
            try:
                from striprtf.striprtf import rtf_to_text
                texto = rtf_to_text(src.read_text(encoding='latin-1', errors='replace'))
                out.write_text(texto, encoding='utf-8')
            except ImportError:
                raise RuntimeError("striprtf nao instalado.\nUse: pip install striprtf")

        # XLSX -> CSV
        elif ext == '.xlsx' and fmt == 'csv':
            try:
                import openpyxl
                wb = openpyxl.load_workbook(str(src), read_only=True, data_only=True)
                ws = wb.active
                with open(str(out), 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    for row in ws.iter_rows(values_only=True):
                        writer.writerow(['' if v is None else v for v in row])
                wb.close()
            except ImportError:
                raise RuntimeError("openpyxl nao instalado.\nUse: pip install openpyxl")

        # XLS -> XLSX
        elif ext == '.xls' and fmt == 'xlsx':
            try:
                import xlrd, openpyxl
                rb = xlrd.open_workbook(str(src))
                rs = rb.sheet_by_index(0)
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = rs.name
                for i in range(rs.nrows):
                    ws.append(rs.row_values(i))
                wb.save(str(out))
            except ImportError as ie:
                pkg = 'xlrd' if 'xlrd' in str(ie) else 'openpyxl'
                raise RuntimeError(f"{pkg} nao instalado.\nUse: pip install {pkg}")

        # XLS -> CSV
        elif ext == '.xls' and fmt == 'csv':
            try:
                import xlrd
                rb = xlrd.open_workbook(str(src))
                rs = rb.sheet_by_index(0)
                with open(str(out), 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    for i in range(rs.nrows):
                        writer.writerow(rs.row_values(i))
            except ImportError:
                raise RuntimeError("xlrd nao instalado.\nUse: pip install xlrd")

        # CSV -> XLSX
        elif ext == '.csv' and fmt == 'xlsx':
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                with open(str(src), newline='', encoding='utf-8', errors='replace') as f:
                    for row in csv.reader(f):
                        ws.append(row)
                wb.save(str(out))
            except ImportError:
                raise RuntimeError("openpyxl nao instalado.\nUse: pip install openpyxl")

        # CSV -> PDF
        elif ext == '.csv' and fmt == 'pdf':
            try:
                from reportlab.lib.pagesizes import landscape, A4
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
                from reportlab.lib import colors as rl_colors

                with open(str(src), newline='', encoding='utf-8', errors='replace') as f:
                    data = list(csv.reader(f))
                if not data:
                    raise RuntimeError("CSV esta vazio.")
                data = [row[:30] for row in data[:500]]

                pdf_doc = SimpleDocTemplate(str(out), pagesize=landscape(A4))
                tbl = Table(data)
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor(C_PRIMARY)),
                    ('TEXTCOLOR',  (0, 0), (-1, 0), rl_colors.white),
                    ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID',       (0, 0), (-1, -1), 0.5, rl_colors.grey),
                    ('FONTSIZE',   (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [rl_colors.white, rl_colors.HexColor('#f0f5ef')]),
                ]))
                pdf_doc.build([tbl])
            except ImportError:
                raise RuntimeError("reportlab nao instalado.\nUse: pip install reportlab")

        # EPUB -> TXT
        elif ext == '.epub' and fmt == 'txt':
            try:
                import ebooklib
                from ebooklib import epub

                class _TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.parts = []
                    def handle_data(self, data):
                        self.parts.append(data)

                book = epub.read_epub(str(src))
                chunks = []
                for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                    p = _TextExtractor()
                    p.feed(item.get_content().decode('utf-8', errors='replace'))
                    chunks.append(''.join(p.parts))
                out.write_text('\n\n'.join(chunks), encoding='utf-8')
            except ImportError:
                raise RuntimeError("ebooklib nao instalado.\nUse: pip install ebooklib")

        else:
            raise RuntimeError(
                f"Conversao de '{ext.upper()}' para '{fmt.upper()}' nao suportada.\n\n"
                "O Conversor Universal opera sem softwares externos.\n"
                "Consulte os formatos disponiveis para este tipo de arquivo."
            )

        self.progress.emit(100)
        return str(out)

    def _txt_to_pdf(self, src: Path, out: Path):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas as rl_canvas
        except ImportError:
            raise RuntimeError("reportlab nao instalado.\nUse: pip install reportlab")

        c = rl_canvas.Canvas(str(out), pagesize=A4)
        W, H = A4
        linhas = src.read_text(encoding='utf-8', errors='replace').splitlines()
        y = H - 60
        c.setFont('Helvetica', 11)
        for linha in linhas:
            while len(linha) > 110:
                c.drawString(50, y, linha[:110])
                linha = linha[110:]
                y -= 15
                if y < 50:
                    c.showPage()
                    c.setFont('Helvetica', 11)
                    y = H - 60
            if y < 50:
                c.showPage()
                c.setFont('Helvetica', 11)
                y = H - 60
            c.drawString(50, y, linha)
            y -= 15
        c.save()


# ─── ZONA DE ARRASTE ──────────────────────────────────────────────────────────

class DropZone(QFrame):
    fileDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(175)
        self.setCursor(Qt.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        emoji = QLabel("📂")
        emoji.setFont(QFont("", 40))
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet("background: transparent;")

        lbl1 = QLabel("Arraste o arquivo aqui")
        lbl1.setFont(QFont("", 15, QFont.Bold))
        lbl1.setAlignment(Qt.AlignCenter)
        lbl1.setStyleSheet(f"color: {C_ACCENT}; background: transparent;")

        lbl2 = QLabel("ou clique para selecionar")
        lbl2.setAlignment(Qt.AlignCenter)
        lbl2.setStyleSheet("color: #8aaa87; font-size: 12px; background: transparent;")

        tipos = QLabel("Video  •  Audio  •  Imagem  •  Documento  •  Compactado")
        tipos.setAlignment(Qt.AlignCenter)
        tipos.setStyleSheet("color: #9aab97; font-size: 11px; background: transparent;")

        lay.addWidget(emoji)
        lay.addWidget(lbl1)
        lay.addWidget(lbl2)
        lay.addSpacing(4)
        lay.addWidget(tipos)

    def mousePressEvent(self, e):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo", "",
                                              "Todos os arquivos (*.*)")
        if path:
            self.fileDropped.emit(path)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet(
                "QFrame#dropzone { background: #c0dab9; "
                "border: 2px dashed #4a6e47; border-radius: 16px; }"
            )

    def dragLeaveEvent(self, e):
        self.setStyleSheet("")

    def dropEvent(self, e: QDropEvent):
        urls = e.mimeData().urls()
        if urls:
            self.fileDropped.emit(urls[0].toLocalFile())
        self.dragLeaveEvent(None)


# ─── JANELA PRINCIPAL ─────────────────────────────────────────────────────────

class ConversorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversor Universal de Arquivos")
        self.setMinimumSize(660, 630)
        self.current_file = None
        self.outdir = load_outdir()   # carrega diretorio persistido
        self.worker = None
        self._build_ui()
        self.setStyleSheet(QSS)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        v = QVBoxLayout(root)
        v.setContentsMargins(38, 28, 38, 18)
        v.setSpacing(16)

        hdr = QHBoxLayout()
        logo = QLabel("🌿")
        logo.setFont(QFont("", 32))
        info = QVBoxLayout()
        info.setSpacing(2)
        titulo = QLabel("Conversor Universal de Arquivos")
        titulo.setObjectName("title")
        sub = QLabel("Videos  •  Audios  •  Imagens  •  Documentos  •  Compactados")
        sub.setObjectName("subtitle")
        info.addWidget(titulo)
        info.addWidget(sub)
        hdr.addWidget(logo)
        hdr.addSpacing(10)
        hdr.addLayout(info)
        hdr.addStretch()
        v.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {C_BORDER}; max-height: 1px;")
        v.addWidget(sep)

        self.drop = DropZone()
        self.drop.fileDropped.connect(self.on_file)
        v.addWidget(self.drop)

        self.fi = QLabel("Nenhum arquivo selecionado")
        self.fi.setObjectName("fileinfo")
        self.fi.setAlignment(Qt.AlignCenter)
        v.addWidget(self.fi)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background: {C_BORDER}; max-height: 1px;")
        v.addWidget(sep2)

        row1 = QHBoxLayout()
        lbl_fmt = QLabel("Converter para:")
        lbl_fmt.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.combo = QComboBox()
        self.combo.setEnabled(False)
        self.combo.setMinimumWidth(180)
        row1.addWidget(lbl_fmt)
        row1.addWidget(self.combo)
        row1.addStretch()
        v.addLayout(row1)

        row2 = QHBoxLayout()
        self.dir_lbl = QLabel(f"📁  {self.outdir}")
        self.dir_lbl.setStyleSheet(f"color: {C_DARK}; font-size: 12px;")
        self.dir_lbl.setWordWrap(True)
        dir_btn = QPushButton("Alterar pasta")
        dir_btn.setObjectName("secondary")
        dir_btn.clicked.connect(self.pick_dir)
        row2.addWidget(self.dir_lbl, 1)
        row2.addWidget(dir_btn)
        v.addLayout(row2)

        self.btn = QPushButton("⚙️   Converter Arquivo")
        self.btn.setObjectName("primary")
        self.btn.setEnabled(False)
        self.btn.setFixedHeight(50)
        self.btn.clicked.connect(self.start_conversion)
        v.addWidget(self.btn)

        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        self.pbar.setVisible(False)
        self.pbar.setTextVisible(True)
        self.pbar.setFormat("%p%")
        self.pbar.setFixedHeight(18)
        v.addWidget(self.pbar)

        self.status = QLabel("")
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setWordWrap(True)
        v.addWidget(self.status)

        v.addStretch()

        sig = QLabel("Desenvolvido pela Secretaria Escolar")
        sig.setObjectName("sig")
        sig.setAlignment(Qt.AlignCenter)
        v.addWidget(sig)

    def on_file(self, path: str):
        self.current_file = path
        p = Path(path)
        try:
            size = p.stat().st_size
            sz = f"{size/1024:.1f} KB" if size < 1_000_000 else f"{size/1_000_000:.1f} MB"
        except Exception:
            sz = "?"

        kind = detect_type(path)
        icones = {
            'video':   '🎬 Video',
            'audio':   '🎵 Audio',
            'image':   '🖼️ Imagem',
            'zip':     '🗜️ Compactado',
            'doc':     '📄 Documento',
            'unknown': '❓ Tipo desconhecido',
        }
        self.fi.setText(f"{icones[kind]}  •  {p.name}  •  {sz}")

        fmts = get_formats(path)
        self.combo.clear()
        if fmts:
            self.combo.addItems(fmts)
            self.combo.setEnabled(True)
            self.btn.setEnabled(True)
            self.status.setText("")
        else:
            self.combo.setEnabled(False)
            self.btn.setEnabled(False)
            self.status.setText("⚠️  Formato de arquivo nao suportado para conversao.")
            self.status.setStyleSheet(f"color: {C_ERROR};")

    def pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Selecionar pasta de saida", self.outdir)
        if d:
            self.outdir = d
            self.dir_lbl.setText(f"📁  {d}")
            save_outdir(d)   # persiste imediatamente

    def start_conversion(self):
        if not self.current_file:
            return
        self.pbar.setVisible(True)
        self.pbar.setValue(0)
        self.btn.setEnabled(False)
        self.status.setText("⏳  Processando...")
        self.status.setStyleSheet(f"color: {C_DARK};")

        fmt = self.combo.currentText()
        self.worker = ConversionWorker(self.current_file, fmt, self.outdir)
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_fail)
        self.worker.start()

    def on_done(self, path: str):
        self.pbar.setValue(100)
        self.btn.setEnabled(True)
        self.status.setText(f"✅  Arquivo salvo em: {path}")
        self.status.setStyleSheet(f"color: {C_SUCCESS}; font-weight: bold;")

    def on_fail(self, msg: str):
        self.pbar.setVisible(False)
        self.btn.setEnabled(True)
        self.status.setText("❌  Falhou — veja os detalhes abaixo.")
        self.status.setStyleSheet(f"color: {C_ERROR};")
        QMessageBox.critical(self, "Erro na conversao", msg)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = ConversorApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
