#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uninstall.py — Desinstalador completo do Conversor Universal
====================================================================
Remove TODOS os rastros deixados pelo projeto e pelo build.py:

  [1] Pacotes pip instalados pelas dependências do projeto
  [2] Chave de registro do Windows com a configuração (QSettings)
  [3] Aplicativo instalado via Setup.exe (chama o desinstalador oficial)
  [4] (Opcional) Apaga a pasta do próprio projeto

Compatível com Windows (10/11). No Linux/macOS as etapas 2 e 3 são
adaptadas automaticamente (registro não existe; app não é instalado via Inno).

Uso:
    python uninstall.py              # interativo, confirma cada etapa
    python uninstall.py --all        # remove tudo sem perguntar
    python uninstall.py --no-app     # pula a desinstalação do app instalado
    python uninstall.py --no-pip     # pula a remoção dos pacotes pip
    python uninstall.py --no-reg     # pula a limpeza do registro
    python uninstall.py --delete-project-dir  # apaga a pasta do projeto no final
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ─── Pacotes que o build.py instala ────────────────────────────────────────────
PIP_PACKAGES = [
    "PySide6",
    "Pillow",
    "pypdf",
    "pdf2docx",
    "python-docx",
    "reportlab",
    "openpyxl",
    "xlrd",
    "ebooklib",
    "striprtf",
    "py7zr",
    "rarfile",
    "pyinstaller",
]

# ─── Chave de registro criada pelo QSettings ───────────────────────────────────
REG_KEY = r"HKCU\Software\EscolaExemplo"

# ─── Nomes possíveis do app instalado (para localizar o desinstalador) ─────────
APP_NAMES = [
    "Conversor Universal",
    "ConversorUniversal",
]

# ─── Pasta padrão de instalação (Inno Setup com PrivilegesRequired=lowest) ─────
APP_INSTALL_DIRS = [
    Path(os.environ.get("LOCALAPPDATA", ""), "Programs", "ConversorUniversal"),
    Path(os.environ.get("ProgramFiles", ""), "ConversorUniversal"),
    Path(os.environ.get("ProgramFiles(x86)", ""), "ConversorUniversal"),
]

IS_WINDOWS = sys.platform == "win32"


# ─── Utilitários ──────────────────────────────────────────────────────────────

def header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def ask(question: str, auto: bool) -> bool:
    """Retorna True se o usuário confirmar (ou se --all foi passado)."""
    if auto:
        print(f"  {question} [S/n] → S (automático)")
        return True
    r = input(f"  {question} [S/n]: ").strip().lower()
    return r in ("", "s", "sim", "y", "yes")


def run_silent(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


# ─── Etapa 1: Remoção dos pacotes pip ─────────────────────────────────────────

def remove_pip(auto: bool):
    header("[1/4] Remover pacotes Python instalados (pip)")
    pkgs = " ".join(PIP_PACKAGES)
    print(f"  Serão removidos:\n  {pkgs}\n")

    if not ask("Confirmar remoção dos pacotes pip?", auto):
        print("  Etapa ignorada.")
        return

    cmd = [sys.executable, "-m", "pip", "uninstall", "-y"] + PIP_PACKAGES
    r = run_silent(cmd)

    if r.returncode == 0:
        print("  ✅ Pacotes removidos com sucesso.")
    else:
        # pip retorna código não-zero se algum pacote já não estava instalado —
        # isso não é um erro real.
        print("  ✅ Remoção concluída (alguns pacotes já não estavam instalados).")

    if r.stdout:
        for line in r.stdout.splitlines():
            if "Successfully" in line or "not installed" in line.lower():
                print(f"     {line.strip()}")


# ─── Etapa 2: Limpeza do Registro do Windows (QSettings) ──────────────────────

def remove_registry(auto: bool):
    header("[2/4] Remover configurações do Registro do Windows (QSettings)")

    if not IS_WINDOWS:
        print("  Sistema não-Windows detectado — etapa ignorada.")
        return

    print(f"  Chave a remover: {REG_KEY}\n")

    if not ask("Confirmar remoção da chave de registro?", auto):
        print("  Etapa ignorada.")
        return

    # Verifica se a chave existe antes de tentar remover
    check = run_silent(["reg", "query", REG_KEY])
    if check.returncode != 0:
        print("  ℹ️  Chave não encontrada — nada a fazer.")
        return

    r = run_silent(["reg", "delete", REG_KEY, "/f"])
    if r.returncode == 0:
        print("  ✅ Chave de registro removida.")
    else:
        print(f"  ⚠️  Falha ao remover o registro:\n  {r.stderr.strip()}")


# ─── Etapa 3: Desinstalar o aplicativo instalado ──────────────────────────────

def find_uninstaller() -> Path | None:
    """Procura o Uninstall.exe gerado pelo Inno Setup."""
    for d in APP_INSTALL_DIRS:
        unins = d / "unins000.exe"
        if unins.exists():
            return unins
    return None


def remove_app(auto: bool):
    header("[3/4] Desinstalar o aplicativo (Setup.exe / Inno Setup)")

    if not IS_WINDOWS:
        print("  Sistema não-Windows detectado — etapa ignorada.")
        return

    uninstaller = find_uninstaller()

    if uninstaller is None:
        print("  ℹ️  Aplicativo instalado não encontrado em nenhum local padrão.")
        print("      Se instalou em local customizado, desinstale pelo")
        print("      Painel de Controle → Adicionar ou Remover Programas.")
        return

    print(f"  Desinstalador encontrado em:\n  {uninstaller}\n")

    if not ask("Confirmar desinstalação do aplicativo?", auto):
        print("  Etapa ignorada.")
        return

    # /VERYSILENT suprime janelas; /NORESTART evita reinicialização automática
    r = subprocess.run([str(uninstaller), "/VERYSILENT", "/NORESTART"])
    if r.returncode == 0:
        print("  ✅ Aplicativo desinstalado (atalhos e entradas de menu removidos).")
    else:
        print(f"  ⚠️  Desinstalador retornou código {r.returncode}.")
        print("      Tente desinstalar manualmente pelo Painel de Controle.")


# ─── Etapa 4 (opcional): Apagar a pasta do projeto ────────────────────────────

def remove_project_dir(auto: bool):
    header("[4/4] Apagar a pasta do projeto")

    project_dir = Path(__file__).parent.resolve()
    print(f"  Pasta do projeto:\n  {project_dir}\n")
    print("  ⚠️  ATENÇÃO: esta operação é IRREVERSÍVEL.")
    print("      Todos os arquivos .py, .spec, .iss, requirements.txt")
    print("      e os diretórios dist/ e build/ serão apagados.\n")

    if not ask("Confirmar exclusão da pasta do projeto?", auto):
        print("  Etapa ignorada — pasta mantida.")
        return

    try:
        shutil.rmtree(project_dir)
        print("  ✅ Pasta do projeto removida.")
    except Exception as e:
        print(f"  ⚠️  Não foi possível remover a pasta:\n  {e}")
        print("      Feche todos os programas que usam a pasta e tente novamente,")
        print("      ou apague manualmente pelo Explorador de Arquivos.")


# ─── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Desinstalador completo do Conversor Universal"
    )
    parser.add_argument("--all",  action="store_true",
                        help="Remove tudo sem pedir confirmacao")
    parser.add_argument("--no-pip", action="store_true",
                        help="Pula remocao dos pacotes pip")
    parser.add_argument("--no-reg", action="store_true",
                        help="Pula limpeza do registro do Windows")
    parser.add_argument("--no-app", action="store_true",
                        help="Pula desinstalacao do app instalado")
    parser.add_argument("--delete-project-dir", action="store_true",
                        help="Apaga a pasta do projeto apos as demais etapas")
    args = parser.parse_args()

    auto = args.all

    print("\n" + "=" * 60)
    print("  Conversor Universal — Desinstalador Completo")
    print("=" * 60)
    print("\n  Este script remove todos os rastros deixados pelo projeto:")
    print("  pacotes pip, configuracoes de registro, app instalado")
    print("  e (opcionalmente) a pasta do projeto.\n")

    if not auto:
        confirma = input("  Deseja continuar? [S/n]: ").strip().lower()
        if confirma not in ("", "s", "sim", "y", "yes"):
            print("\n  Desinstalacao cancelada.\n")
            sys.exit(0)

    if not args.no_pip:
        remove_pip(auto)

    if not args.no_reg:
        remove_registry(auto)

    if not args.no_app:
        remove_app(auto)

    if args.delete_project_dir:
        remove_project_dir(auto)
    else:
        header("[4/4] Pasta do projeto")
        print("  Pasta do projeto NÃO foi apagada (use --delete-project-dir para isso).")
        print(f"  Localização: {Path(__file__).parent.resolve()}")

    print("\n" + "=" * 60)
    print("  DESINSTALACAO CONCLUIDA!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
