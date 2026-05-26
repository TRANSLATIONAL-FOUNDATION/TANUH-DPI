#!/bin/bash
# Builds a PyInstaller executable for Forgensic on an Ubuntu 22.04 base.
# Building on older glibc (Ubuntu 22.04) ensures forward-compatibility with Ubuntu 24.04.

echo "[*] Starting Ubuntu 22.04 Docker build container..."

docker run --rm -v "$(pwd)/..:/workspace" -w /workspace/forgensic ubuntu:22.04 /bin/bash -c "
    echo '[*] Installing system dependencies...'
    apt-get update && apt-get install -y python3 python3-pip python3-venv tesseract-ocr libgl1 libglib2.0-0 tk-dev python3-tk libxext6 libxrender1 libsm6
    
    echo '[*] Setting up Python environment...'
    python3 -m venv venv
    source venv/bin/activate
    
    echo '[*] Installing Python requirements...'
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install pyinstaller customtkinter
    
    echo '[*] Running PyInstaller...'
    pyinstaller forgensic_gui.spec --clean
"

echo "[*] Build complete! Check the forgensic/dist folder for the executable."
