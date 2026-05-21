# -*- mode: python ; coding: utf-8 -*-
# ============================================================================
# nhcx-extract.spec -- PyInstaller spec file for nhcx-extract
#
# Builds a single-file executable that bundles:
#   - Python runtime
#   - All pip dependencies (langchain, docling, langgraph, etc.)
#   - nhcx-local source code + rulebooks
#   - CLI entry point
#
# Usage (run on the TARGET OS):
#   pip install pyinstaller
#   pip install torch --index-url https://download.pytorch.org/whl/cpu
#   pip install .
#   pyinstaller nhcx-extract.spec
#
# Output:
#   dist/nhcx-extract       (Linux/Mac)
#   dist/nhcx-extract.exe   (Windows)
# ============================================================================

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# ── Locate the installed nhcx_local package ─────────────────────────────────
import nhcx_local
NHCX_PKG_DIR = Path(nhcx_local.__file__).parent

# ── Collect rulebook JSON files ─────────────────────────────────────────────
rulebook_datas = []
for subdir in ['abdm', 'nhcx']:
    rb_dir = NHCX_PKG_DIR / 'rulebooks' / subdir
    if rb_dir.exists():
        for json_file in rb_dir.glob('*.json'):
            # (source_path, dest_dir_inside_bundle)
            rulebook_datas.append(
                (str(json_file), f'nhcx_local/rulebooks/{subdir}')
            )

# ── Hidden imports ──────────────────────────────────────────────────────────
# These packages use dynamic imports that PyInstaller can't detect statically
hidden_imports = [
    # nhcx_local submodules
    'nhcx_local.cli',
    'nhcx_local.llm',
    'nhcx_local.ocr',
    'nhcx_local.classifier',
    'nhcx_local.fhir_utils',
    'nhcx_local.pipelines',
    'nhcx_local.pipelines.abdm',
    'nhcx_local.pipelines.nhcx',
    'nhcx_local.ocr_engines',
    'nhcx_local.ocr_engines.pypdf_engine',
    'nhcx_local.ocr_engines.docling_engine',
    'nhcx_local.ocr_engines.normaliser',
    # LangChain ecosystem (heavy dynamic imports)
    *collect_submodules('langchain_core'),
    *collect_submodules('langchain_ollama'),
    *collect_submodules('langgraph'),
    # Docling
    *collect_submodules('docling'),
    *collect_submodules('docling_core'),
    # Other
    'click',
    'rich',
    'pypdf',
    'pymupdf',
    'fitz',
    'pymupdf4llm',
    'yaml',
    'json',
    'urllib.request',
]

# ── Collect data files from key packages ────────────────────────────────────
extra_datas = list(rulebook_datas)

# Docling needs its model configs / data
docling_datas = collect_data_files('docling')
extra_datas.extend(docling_datas)

docling_core_datas = collect_data_files('docling_core')
extra_datas.extend(docling_core_datas)

# ── Analysis ────────────────────────────────────────────────────────────────
a = Analysis(
    ['src/nhcx_local/cli.py'],
    pathex=['src'],
    binaries=[],
    datas=extra_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude CUDA/GPU packages to keep size small
        'nvidia',
        'triton',
        'torch.cuda',
        'torch.distributed',
        'torch._inductor',
        # Exclude unnecessary stdlib
        'tkinter',
        'turtle',
        'idlelib',
        'test',
        'unittest',
    ],
    noarchive=False,
)

# ── Build ───────────────────────────────────────────────────────────────────
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='nhcx-extract',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,        # CLI tool, needs console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
