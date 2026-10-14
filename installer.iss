; ══════════════════════════════════════════════════════════════════════════════
; installer.iss — Script Inno Setup para Conversor Universal
;
; Gera:  dist\ConversorUniversal_Setup.exe
;
; Pré-requisitos:
;   • PyInstaller já executado → dist\ConversorUniversal\ existe
;   • Inno Setup 6 instalado   → https://jrsoftware.org/isdl.php
;
; Como compilar manualmente:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; Ou via script:
;   python build.py --inno
; ══════════════════════════════════════════════════════════════════════════════

#define MyAppName      "Conversor Universal"
#define MyAppVersion   "1.2.0"
#define MyAppPublisher "Secretaria Escolar"
#define MyAppExeName   "ConversorUniversal.exe"
#define MyAppDir       "ConversorUniversal"
; Caminho relativo ao arquivo .iss (ajuste se necessário)
#define MySourceDir    "dist\ConversorUniversal"

[Setup]
; Metadados do instalador
AppId={{CECE473C-716A-471D-8570-774DEEA8CD06}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://escola.exemplo
AppSupportURL=https://escola.exemplo
DefaultDirName={autopf}\{#MyAppDir}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Saída do instalador
OutputDir=dist
OutputBaseFilename=ConversorUniversal_Setup
; Compressão máxima (LZMA2)
Compression=lzma2/ultra64
SolidCompression=yes
; Compatibilidade
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Aparência
WizardStyle=modern
; Privilégios — instala para o usuário atual (não requer admin)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english";             MessagesFile: "compiler:Default.isl"

[Tasks]
; Opção de atalho na Área de Trabalho (marcada por padrão)
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; \
  GroupDescription: "Atalhos:"; Flags: checkedonce

; Opção de atalho no Menu Iniciar (marcada por padrão)
Name: "startmenuicon"; Description: "Criar atalho no Menu Iniciar"; \
  GroupDescription: "Atalhos:"; Flags: checkedonce

[Files]
; Copia toda a pasta gerada pelo PyInstaller
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Atalho no Menu Iniciar
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
  Tasks: startmenuicon

; Atalho na Área de Trabalho
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
  Tasks: desktopicon

; Desinstalador no Menu Iniciar
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Oferece abrir o programa ao final da instalação
Filename: "{app}\{#MyAppExeName}"; \
  Description: "Iniciar {#MyAppName}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove a pasta de configurações do usuário ao desinstalar (opcional)
; Type: filesandordirs; Name: "{userappdata}\EscolaExemplo"

[Code]
// Verifica se a pasta de origem existe antes de compilar
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
