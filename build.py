#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — Script de automação de build do Conversor Universal
=======================================================================
Executa em sequência:
  1. Instala dependências Python (pip)
  2. Baixa o FFmpeg estático para Windows (se ainda não existir)
  3. Gera o executável com PyInstaller → dist/ConversorUniversal/
  4. (Opcional) Compila o instalador via Inno Setup → ConversorUniversal_Setup.exe

Uso:
    python build.py              # build completo
    python build.py --skip-ffmpeg  # pula o download do FFmpeg
    python build.py --inno       # também compila o instalador Inno Setup
"""

import argparse
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).parent.resolve()

# ─── URL do FFmpeg estático para Windows (build essencial, ~80 MB) ─────────────
FFMPEG_ZIP_URL = (
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
)
FFMPEG_EXE = HERE / "ffmpeg.exe"

# ─── Caminhos do Inno Setup (tentativas comuns de instalação) ─────────────────
INNO_PATHS = [
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe"),
]


def run(cmd: list, **kw):
    """Executa um comando e interrompe em caso de erro."""
    print(f"\n>>> {' '.join(str(c) for c in cmd)}\n")
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(f"Erro ao executar: {cmd[0]}  (código {r.returncode})")
    return r


def install_requirements():
    print("=" * 60)
    print("  [1/4] Instalando dependências Python...")
    print("=" * 60)
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install", "-r", str(HERE / "requirements.txt")])


def download_ffmpeg():
    print("=" * 60)
    print("  [2/4] Verificando FFmpeg...")
    print("=" * 60)

    if FFMPEG_EXE.exists():
        print(f"  FFmpeg já encontrado em: {FFMPEG_EXE}")
        return

    print(f"  Baixando FFmpeg de:\n  {FFMPEG_ZIP_URL}")
    print("  (pode demorar alguns minutos dependendo da conexão...)\n")

    tmp_zip = HERE / "_ffmpeg_download.zip"
    try:
        def _progress(block, block_size, total):
            downloaded = block * block_size
            if total > 0:
                pct = min(downloaded * 100 // total, 100)
                bar = "#" * (pct // 5)
                print(f"\r  [{bar:<20}] {pct}%", end="", flush=True)

        urllib.request.urlretrieve(FFMPEG_ZIP_URL, tmp_zip, _progress)
        print()

        print("  Extraindo ffmpeg.exe...")
        with zipfile.ZipFile(tmp_zip) as z:
            # Procura o ffmpeg.exe dentro do zip (está em subpastas)
            target = next(
                n for n in z.namelist()
                if n.endswith("/bin/ffmpeg.exe") or n == "ffmpeg.exe"
            )
            with z.open(target) as src, open(FFMPEG_EXE, "wb") as dst:
                shutil.copyfileobj(src, dst)

        print(f"  FFmpeg extraído em: {FFMPEG_EXE}")
    finally:
        tmp_zip.unlink(missing_ok=True)


def run_pyinstaller():
    print("=" * 60)
    print("  [3/4] Gerando executável com PyInstaller...")
    print("=" * 60)

    hooks_dir = HERE / "hooks"
    if not hooks_dir.exists():
        sys.exit(
            "  ERRO: Pasta hooks/ nao encontrada!\n"
            "     Certifique-se de que hook-fitz.py e hook-pdf2docx.py\n"
            f"     estejam em: {hooks_dir}"
        )
    print(f"  Hooks encontrados: {list(hooks_dir.glob('hook-*.py'))}")

    spec = HERE / "conversor_universal.spec"
    run([sys.executable, "-m", "PyInstaller", "--clean", str(spec)], cwd=HERE)

    dist = HERE / "dist" / "ConversorUniversal"
    if dist.exists():
        print(f"\n  ✅ Executável gerado em:\n     {dist}")
    else:
        sys.exit("  ❌ Pasta dist/ConversorUniversal não encontrada após build.")


def run_inno():
    print("=" * 60)
    print("  [4/4] Compilando instalador com Inno Setup...")
    print("=" * 60)

    iscc = next((p for p in INNO_PATHS if p.exists()), None)
    if iscc is None:
        print(
            "  ⚠️  Inno Setup não encontrado. Pule esta etapa ou instale em:\n"
            "     https://jrsoftware.org/isdl.php\n"
            "  O diretório dist/ConversorUniversal/ ainda pode ser distribuído diretamente."
        )
        return

    iss = HERE / "installer.iss"
    run([str(iscc), str(iss)], cwd=HERE)

    setup_exe = HERE / "dist" / "ConversorUniversal_Setup.exe"
    if setup_exe.exists():
        print(f"\n  ✅ Instalador gerado em:\n     {setup_exe}")
    else:
        print("  ⚠️  Instalador não gerado — verifique o log do Inno Setup.")


def main():
    parser = argparse.ArgumentParser(description="Build do Conversor Universal")
    parser.add_argument("--skip-ffmpeg", action="store_true",
                        help="Pula o download do FFmpeg (use se já tiver ffmpeg.exe na pasta)")
    parser.add_argument("--inno", action="store_true",
                        help="Compila o instalador .exe com Inno Setup após o build")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  Conversor Universal — Script de Build")
    print("=" * 60)

    install_requirements()

    if not args.skip_ffmpeg:
        download_ffmpeg()
    else:
        print("\n  [2/4] Download do FFmpeg ignorado (--skip-ffmpeg).")

    run_pyinstaller()

    if args.inno:
        run_inno()
    else:
        print("\n  [4/4] Compilação do instalador ignorada.")
        print("        Use --inno para gerar o Setup.exe via Inno Setup.")

    print("\n" + "=" * 60)
    print("  BUILD CONCLUÍDO!")
    print(f"  Saída: {HERE / 'dist' / 'ConversorUniversal'}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
