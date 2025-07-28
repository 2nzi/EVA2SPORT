#!/bin/bash

set -e

echo -e "\033[1;35m=== INSTALLATION EVA2SPORT ===\033[0m"

# === UTILS ===
info() { echo -e "\033[1;36m[INFO]\033[0m $1"; }
success() { echo -e "\033[1;32m[OK]\033[0m $1"; }
warn() { echo -e "\033[1;33m[WARNING]\033[0m $1"; }
error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }

# === UV INSTALLATION ===
if ! command -v uv &> /dev/null; then
    info "uv non detecté, installation..."
    curl -Ls https://astral.sh/uv/install.sh | bash
    export PATH="$HOME/.cargo/bin:$PATH"
    success "uv installé"
else
    success "uv déjà installé"
fi

# === GPU DETECTION ===
USE_GPU=true
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
    success "GPU NVIDIA détecté: $GPU_NAME"
else
    warn "Pas de GPU NVIDIA détecté, fallback CPU"
    USE_GPU=false
fi

# === NETTOYAGE SI DEMANDÉ ===
if [ "$1" == "--force" ]; then
    info "Nettoyage environnement..."
    rm -rf .venv uv.lock
fi

# === ENV CREATION ===
info "Création de l’environnement Python 3.10..."
uv venv --python 3.10

# === DEPENDANCES ===
info "Installation des dépendances (pyproject.toml)..."
uv sync --extra jupyter

# === PYTORCH INSTALLATION ===
if [ "$USE_GPU" = true ]; then
    info "Installation PyTorch GPU (CUDA 12.1)..."
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
else
    info "Installation PyTorch CPU..."
fi

# === SAM2 ===
info "Installation de SAM2..."
uv pip install "sam-2 @ git+https://github.com/facebookresearch/sam2.git" --force-reinstall

# === CHECKPOINT ===
info "Téléchargement du modèle SAM2..."
mkdir -p checkpoints
if [ ! -f checkpoints/sam2.1_hiera_large.pt ]; then
    wget -O checkpoints/sam2.1_hiera_large.pt https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt || warn "Échec téléchargement (sera fait au premier usage)"
else
    success "Modèle déjà présent"
fi

# === VERIF ===
info "Vérification de l'installation PyTorch..."
uv run python -c "
import torch
print(f'PyTorch {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'Device name: {torch.cuda.get_device_name(0)}')
"

success "Installation complète!"
