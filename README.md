# Conversor Universal de Arquivos

Programa de mesa (Windows) para converter arquivos sem depender de sites:
arraste o arquivo, escolha o formato e pronto. Feito para a secretaria
da escola, que vive recebendo arquivos no formato errado.

## Formatos

- **Documentos**: PDF ↔ DOCX, DOCX ↔ TXT, TXT → PDF, RTF e EPUB → TXT.
- **Planilhas**: XLSX ↔ CSV, XLS → XLSX, CSV → PDF.
- **Imagens**: JPG, PNG, BMP, GIF, WEBP e outros, entre si.
- **Vídeo e áudio**: MP4, MKV, AVI, MOV, MP3, WAV, AAC, OGG, FLAC
  (usa o FFmpeg embutido).
- **Compactados**: ZIP, TAR, 7Z, RAR.

## Tecnologias

Python · PySide6 · FFmpeg · pdf2docx · python-docx · reportlab ·
openpyxl · Pillow · PyInstaller · Inno Setup (instalador).

## Download

Baixe a versão pronta para Windows na página **Releases** deste repositório
(arquivo `.zip`; descompacte e abra o `.exe`). O Windows pode mostrar um
aviso de segurança na primeira vez, porque o programa não tem assinatura
digital: clique em **Mais informações → Executar assim mesmo**.

## Como gerar o executável no próprio computador

```bash
python build.py            # instala dependências, baixa o FFmpeg e gera o .exe
python build.py --inno     # também gera o instalador
```

## Privacidade

Este repositório tem **apenas o código**. Nenhum dado de aluno, planilha,
banco de dados ou credencial faz parte dele: esses arquivos ficam só no
computador da escola e estão bloqueados pelo `.gitignore`.
