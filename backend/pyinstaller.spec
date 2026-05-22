# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Event Med AI backend sidecar.
#
# Build from the project root with:
#   pyinstaller backend/pyinstaller.spec --clean --noconfirm
#
# Output: dist/event-med-backend(.exe). The GitHub Actions release workflow
# renames this with the Rust target triple suffix Tauri expects, e.g.
# `event-med-backend-aarch64-apple-darwin`.

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

# SPECPATH is provided by PyInstaller and is the absolute path to this spec's
# directory (backend/). Resolve everything against it so the build works no
# matter what cwd pyinstaller is invoked from.
_spec_dir = SPECPATH
_project_root = os.path.dirname(_spec_dir)

hiddenimports = []
datas = []
binaries = []

# FastAPI / Uvicorn and the ecosystems they pull in at runtime.
for pkg in (
    "uvicorn",
    "fastapi",
    "pydantic",
    "pydantic_settings",
    "sqlalchemy",
    "httpx",
    "google.genai",
):
    try:
        _b, _d, _h = collect_all(pkg)
        binaries += _b
        datas += _d
        hiddenimports += _h
    except Exception:
        # Package not installed in this environment — skip gracefully.
        pass

# Our own backend package — make sure every router/model module is picked up.
hiddenimports += collect_submodules("backend")

# Alembic migration scripts (if any)
_alembic_dir = os.path.join(_project_root, "alembic")
_alembic_ini = os.path.join(_project_root, "alembic.ini")
if os.path.isdir(_alembic_dir):
    datas += [(_alembic_dir, "alembic")]
if os.path.isfile(_alembic_ini):
    datas += [(_alembic_ini, ".")]

# Bundled .env (optional) — release workflow writes one with the cloud preview
# key; in dev the user provides their own.
_env_file = os.path.join(_project_root, ".env")
if os.path.isfile(_env_file):
    datas += [(_env_file, ".")]

# Bundled RAG knowledge base. The FTS5 engine in backend/ai/rag_engine.py
# expects to find this at <bundle>/backend/data/harm_reduction_kb.json
_kb_file = os.path.join(_project_root, "backend", "data", "harm_reduction_kb.json")
if os.path.isfile(_kb_file):
    datas += [(_kb_file, os.path.join("backend", "data"))]

a = Analysis(
    [os.path.join(_spec_dir, "entrypoint.py")],
    pathex=[_project_root, _spec_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "pandas",
        "torch",
        "transformers",
        "sentence_transformers",
        "chromadb",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="event-med-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
