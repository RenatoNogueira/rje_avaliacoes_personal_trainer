import customtkinter
import os
from pathlib import Path

# Caminho do CustomTkinter
ctk_path = os.path.dirname(customtkinter.__file__)

spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('{ctk_path.replace(os.sep, "/")}', 'customtkinter/'),
        ('exercises-ptbr-full-translation.json', '.'),
        ('version.py', '.'),
        ('gui', 'gui'),
        ('reports', 'reports'),
        ('utils', 'utils'),
        ('data', 'data'),  # Inclui pasta data vazia ou com templates
    ],
    hiddenimports=['PIL._tkinter_finder', 'fpdf', 'matplotlib', 'requests'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
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
    name='RJE_Avaliacoes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # False para não abrir terminal preto
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None, # Se tiver icone .ico, coloque o caminho aqui ex: 'assets/icon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RJE_Avaliacoes',
)
"""

with open("rje_avaliacoes.spec", "w", encoding="utf-8") as f:
    f.write(spec_content)

print("Arquivo rje_avaliacoes.spec criado com sucesso!")
