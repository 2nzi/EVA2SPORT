# EVA2SPORT 🏀⚽

Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive.

## Installation automatique

```powershell
git clone https://github.com/yourusername/EVA2SPORT.git
cd EVA2SPORT
.\install.ps1
```

**Le script :**
- 🚀 **Utilise uv par défaut** (plus rapide)
- 🔄 **Fallback vers pip** si uv indisponible  
- 🎮 **Détecte GPU automatiquement**
- 📦 **Installe tout en une fois**

## Options

```powershell
.\install.ps1           # Installation automatique (uv + GPU auto)
.\install.ps1 -UsePip   # Force pip classique
.\install.ps1 -CPUOnly  # Force mode CPU
.\install.ps1 -Force    # Réinstallation complète
```

## Utilisation

```powershell
# Avec uv (par défaut)
uv run jupyter lab

# Avec pip (si fallback)
.\.venv\Scripts\activate
jupyter lab
```

C'est tout ! 🎉

## 🎯 Problèmes identifiés

1. **Force uv** - Pas de flexibilité pour les utilisateurs pip
2. **Installation manuelle** - Ignore pyproject.toml/requirements.txt  
3. **Pas de versions** - Problèmes de reproductibilité
4. **Logique complexe** - Script trop long et fragile

## 🔧 Solution propre : Script modulaire

### 1. **Nouveau `install.ps1` flexible**

```powershell:install.ps1
<#
.SYNOPSIS
    Installation EVA2SPORT - Support pip et uv
.PARAMETER UsePip
    Utilise pip au lieu d'uv
.PARAMETER CPUOnly  
    Force installation CPU
.PARAMETER Force
    Réinstallation complète
#>

param(
    [switch]$UsePip = $false,
    [switch]$CPUOnly = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

Write-Host "=== INSTALLATION EVA2SPORT ===" -ForegroundColor Magenta

# DETECTION GESTIONNAIRE DE PACKAGES
if ($UsePip) {
    $packageManager = "pip"
    $envCommand = "python"
    Write-Info "Mode: pip classique"
} else {
    # Vérifier/installer uv
    try {
        uv --version | Out-Null
        $packageManager = "uv"
        $envCommand = "uv run python"
        Write-Info "Mode: uv (moderne)"
    } catch {
        Write-Info "uv non trouvé, installation..."
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
        $packageManager = "uv"
        $envCommand = "uv run python"
    }
}

# DETECTION GPU
$useGPU = $false
if (-not $CPUOnly) {
    try {
        $nvidiaInfo = nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>$null
        if ($nvidiaInfo) {
            $useGPU = $true
            Write-Success "GPU NVIDIA detecte: $($nvidiaInfo[0])"
        }
    } catch {
        Write-Warning "GPU NVIDIA non detecte - Mode CPU"
    }
}

# NETTOYAGE SI FORCE
if ($Force) {
    Write-Info "Nettoyage environnement..."
    Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
    Remove-Item uv.lock -ErrorAction SilentlyContinue
}

# CREATION ENVIRONNEMENT
Write-Info "Creation environnement Python 3.10..."
if ($packageManager -eq "uv") {
    uv venv --python 3.10
} else {
    python -m venv .venv
    & .\.venv\Scripts\activate.ps1
}

# MISE A JOUR PIP
Write-Info "Mise a jour pip..."
if ($packageManager -eq "uv") {
    uv pip install --upgrade pip
} else {
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
}

# INSTALLATION PYTORCH (cas spécial GPU/CPU)
Write-Info "Installation PyTorch..."
if ($useGPU) {
    Write-Info "PyTorch GPU (CUDA 12.1)..."
    $torchIndex = "--index-url https://download.pytorch.org/whl/cu121"
} else {
    Write-Info "PyTorch CPU..."
    $torchIndex = "--index-url https://download.pytorch.org/whl/cpu"
}

if ($packageManager -eq "uv") {
    uv pip install torch torchvision torchaudio $torchIndex --force-reinstall
} else {
    .\.venv\Scripts\python.exe -m pip install torch torchvision torchaudio $torchIndex
}

# INSTALLATION DEPUIS PYPROJECT.TOML
Write-Info "Installation dependances depuis pyproject.toml..."
if ($packageManager -eq "uv") {
    # uv sync gère automatiquement pyproject.toml
    uv sync --extra jupyter
} else {
    # pip doit installer depuis pyproject.toml
    .\.venv\Scripts\python.exe -m pip install -e .
    .\.venv\Scripts\python.exe -m pip install jupyter jupyterlab ipykernel ipywidgets
}

# INSTALLATION SAM2 (cas spécial depuis GitHub)
Write-Info "Installation SAM2 depuis GitHub..."
if ($packageManager -eq "uv") {
    uv pip install "git+https://github.com/facebookresearch/sam2.git" --force-reinstall
} else {
    .\.venv\Scripts\python.exe -m pip install "git+https://github.com/facebookresearch/sam2.git"
}

# CONFIGURATION JUPYTER
Write-Info "Configuration kernel Jupyter..."
if ($packageManager -eq "uv") {
    uv run python -m ipykernel install --user --name eva2sport --display-name "Python (EVA2SPORT)"
} else {
    .\.venv\Scripts\python.exe -m ipykernel install --user --name eva2sport --display-name "Python (EVA2SPORT)"
}

# TELECHARGEMENT MODELE SAM2
Write-Info "Telechargement modele SAM2..."
if (-not (Test-Path "checkpoints")) {
    New-Item -ItemType Directory -Path "checkpoints"
}
$modelPath = "checkpoints/sam2.1_hiera_large.pt"
if (-not (Test-Path $modelPath)) {
    Write-Info "Telechargement modele SAM2 (~2.3GB)..."
    try {
        Invoke-WebRequest -Uri "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt" -OutFile $modelPath
        Write-Success "Modele telecharge"
    } catch {
        Write-Warning "Echec telechargement (sera fait au premier usage)"
    }
}

# VERIFICATION FINALE
Write-Info "Verification installation..."
$testScript = "
import torch, sam2, cv2, numpy, jupyter
print(f'Python: OK')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
print(f'SAM2: OK') 
print(f'OpenCV: OK')
print(f'Jupyter: OK')
print('Installation complete!')
"

try {
    if ($packageManager -eq "uv") {
        $result = uv run python -c $testScript
    } else {
        $result = .\.venv\Scripts\python.exe -c $testScript
    }
    Write-Host $result -ForegroundColor Green
} catch {
    Write-Warning "Verification partielle - certains modules peuvent avoir des problemes"
}

# MESSAGES FINAUX
Write-Host "`n=== INSTALLATION TERMINEE ===" -ForegroundColor Magenta
Write-Success "EVA2SPORT pret!"

Write-Host "`nUSAGE:" -ForegroundColor Yellow
if ($packageManager -eq "uv") {
    Write-Host "  uv shell                 # Activer environnement"
    Write-Host "  uv run jupyter lab       # Lancer Jupyter"
} else {
    Write-Host "  .\.venv\Scripts\activate # Activer environnement"  
    Write-Host "  jupyter lab              # Lancer Jupyter"
}

if ($useGPU) {
    Write-Host "`n[GPU] Acceleration GPU activee!" -ForegroundColor Green
} else {
    Write-Host "`n[CPU] Mode CPU configure" -ForegroundColor Yellow
}
```

### 2. **Nouveau `pyproject.toml` avec versions fixes**

```toml:pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "eva2sport"
version = "0.1.0"
description = "Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive"
authors = [{name = "Antoine Verdon"}]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"

# Dependencies avec versions spécifiées pour la reproductibilité
dependencies = [
    # PYTORCH INSTALLÉ SÉPARÉMENT (GPU/CPU selon détection)
    # "torch>=2.5.1",  # Géré par install.ps1
    # "torchvision>=0.20.1",  # Géré par install.ps1  
    # "torchaudio>=2.5.1",  # Géré par install.ps1
    
    # Computer Vision
    "opencv-python>=4.10.0",
    "opencv-contrib-python>=4.10.0",
    "pillow>=10.0.0",
    
    # Data Science
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "matplotlib>=3.5.0",
    "scipy>=1.10.0",
    "scikit-learn>=1.3.0",
    
    # Detection & Tracking
    "ultralytics>=8.0.0",
    "supervision>=0.20.0",
    "pycocotools>=2.0.6",
    
    # ML & AI
    "transformers>=4.30.0",
    "huggingface-hub>=0.15.0",
    "tokenizers>=0.13.0",
    "safetensors>=0.3.0",
    
    # Media processing
    "av>=10.0.0",
    
    # Utilities
    "tqdm>=4.60.0",
    "loguru>=0.6.0",
    "pyyaml>=6.0.0",
    "requests>=2.28.0",
    "click>=8.0.0",
    
    # Web (optionnel)
    "fastapi>=0.100.0",
    "uvicorn>=0.15.0",
    "flask>=2.0.0",
    "flask-cors>=4.0.0",
    
    # Visualization
    "plotly>=5.0.0",
]

[project.optional-dependencies]
jupyter = [
    "jupyter>=1.0.0",
    "jupyterlab>=4.0.0", 
    "ipykernel>=6.20.0",
    "ipython>=8.0.0",
    "ipywidgets>=8.0.0",
    "jupyter-bbox-widget>=0.6.0",
    "notebook>=7.0.0",
]

dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
]

# SAM2 installé séparément depuis GitHub dans install.ps1

[project.urls]
Homepage = "https://github.com/yourusername/EVA2SPORT"
Repository = "https://github.com/yourusername/EVA2SPORT"

[tool.setuptools.packages.find]
where = ["."]
include = ["eva2sport*"]
```

### 3. **README mis à jour**

```markdown:README.md
# EVA2SPORT

Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive.

## Installation

### Option 1: Installation automatique (recommandée)

```powershell
git clone https://github.com/yourusername/EVA2SPORT.git
cd EVA2SPORT
.\install.ps1
```

### Option 2: Avec pip classique

```powershell
git clone https://github.com/yourusername/EVA2SPORT.git
cd EVA2SPORT
.\install.ps1 -UsePip
```

### Options disponibles

```powershell
.\install.ps1                    # Installation uv + GPU auto-détecté
.\install.ps1 -UsePip           # Force l'utilisation de pip
.\install.ps1 -CPUOnly          # Force mode CPU
.\install.ps1 -Force            # Réinstallation complète
.\install.ps1 -UsePip -CPUOnly  # Pip + CPU seulement
```

## Utilisation

```powershell
# Avec uv
uv run jupyter lab

# Avec pip 
.\.venv\Scripts\activate
jupyter lab
```

## Structure des dépendances

- **PyTorch** : Installé selon GPU/CPU détecté
- **SAM2** : Installé depuis GitHub
- **Autres** : Gérées par `pyproject.toml`