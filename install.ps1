<#
.SYNOPSIS
    Installation complète EVA2SPORT avec détection GPU automatique
#>

param(
    [switch]$Force = $false,
    [switch]$CPUOnly = $false
)

$ErrorActionPreference = "Stop"

function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

Write-Host "=== INSTALLATION COMPLETE EVA2SPORT ===" -ForegroundColor Magenta

# Installation uv si nécessaire
Write-Info "Verification d'uv..."
try {
    uv --version | Out-Null
    Write-Success "uv disponible"
} catch {
    Write-Info "Installation d'uv..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
}

# DETECTION GPU AUTOMATIQUE
$useGPU = $false
if (-not $CPUOnly) {
    Write-Info "Detection GPU NVIDIA..."
    try {
        $nvidiaInfo = nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>$null
        if ($nvidiaInfo) {
            $useGPU = $true
            Write-Success "GPU NVIDIA detecte: $($nvidiaInfo[0])"
            Write-Info "Installation PyTorch GPU activee"
        } else {
            Write-Warning "Aucun GPU NVIDIA detecte - Installation PyTorch CPU"
        }
    } catch {
        Write-Warning "nvidia-smi non disponible - Installation PyTorch CPU"
    }
}

# Nettoyage si demandé
if ($Force -and (Test-Path ".venv")) {
    Write-Info "Nettoyage environnement existant..."
    Remove-Item -Recurse -Force ".venv"
}

# Créer environnement
Write-Info "Creation environnement Python 3.10..."
uv venv --python 3.10

# INSTALLATION PYTORCH AVEC DETECTION GPU
Write-Info "Installation PyTorch..."
if ($useGPU) {
    Write-Info "Installation PyTorch GPU (CUDA 12.1)..."
    uv pip uninstall torch torchvision torchaudio
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
} else {
    Write-Info "PyTorch GPU error"
}

# Installation des autres dépendances
Write-Info "Installation Computer Vision..."
uv pip install opencv-python opencv-contrib-python pillow

Write-Info "Installation Data Science..."
uv pip install numpy pandas matplotlib scipy scikit-learn

Write-Info "Installation Jupyter ecosystem..."
uv pip install jupyter jupyterlab ipykernel ipython ipywidgets notebook jupyter-bbox-widget

Write-Info "Installation ML et utilities..."
uv pip install transformers huggingface-hub tokenizers tqdm loguru pyyaml requests

Write-Info "Installation Computer Vision avance..."
uv pip install ultralytics supervision pycocotools

Write-Info "Installation Web et visualisation..."
uv pip install fastapi uvicorn flask flask-cors plotly

# Installation SAM2
Write-Info "Installation SAM2 (methode Colab)..."

# Supprimer dossier local s'il existe
if (Test-Path "sam2") {
    Remove-Item -Recurse -Force "sam2"
}

# Installer directement depuis Git (comme Colab)
uv pip install "git+https://github.com/facebookresearch/sam2.git" --force-reinstall

Write-Success "SAM2 installe sans conflit de noms"

# Configuration Jupyter kernel
Write-Info "Configuration kernel Jupyter..."
uv run python -m ipykernel install --user --name eva2sport --display-name "Python (EVA2SPORT)"

# Téléchargement modèle SAM2
Write-Info "Telechargement modele SAM2..."
if (-not (Test-Path "checkpoints")) {
    New-Item -ItemType Directory -Path "checkpoints"
}
$modelPath = "checkpoints/sam2.1_hiera_large.pt"
if (-not (Test-Path $modelPath)) {
    Write-Info "Telechargement modele SAM2 (~2.3GB)..."
    Invoke-WebRequest -Uri "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt" -OutFile $modelPath
}

# VERIFICATION COMPLETE AVEC GPU
Write-Info "Verification complete de l'installation..."
$testResult = uv run python -c "
import sys
print('=== CONFIGURATION SYSTEME ===')
print(f'Python: {sys.version.split()[0]}')

print('\\n=== TEST PYTORCH ===')
try:
    import torch
    print(f'PyTorch: {torch.__version__}')
    print(f'CUDA available: {torch.cuda.is_available()}')
    
    if torch.cuda.is_available():
        print(f'CUDA version: {torch.version.cuda}')
        print(f'GPU count: {torch.cuda.device_count()}')
        for i in range(torch.cuda.device_count()):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
            print(f'GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)')
        
        # Test tensor GPU
        x = torch.rand(100, 100).cuda()
        print('[OK] Test tensor GPU: OK')
    else:
        print('[WARNING] Mode CPU seulement')
        
except Exception as e:
    print(f'[ERROR] Erreur PyTorch: {e}')

print('\\n=== TEST MODULES ===')
modules = ['sam2', 'cv2', 'numpy', 'pandas', 'matplotlib', 'jupyter', 'ultralytics', 'supervision']
success = 0
for module in modules:
    try:
        __import__(module)
        print(f'[OK] {module}: OK')
        success += 1
    except ImportError:
        print(f'[ERROR] {module}: ERREUR')

print(f'\\n=== RESULTAT ===')
print(f'Modules: {success}/{len(modules)} OK')

# Test SAM2 spécifique
try:
    import sam2
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'SAM2 device recommande: {device}')
    print('[OK] SAM2 + PyTorch: Configuration optimale')
except Exception as e:
    print(f'[ERROR] Erreur SAM2: {e}')
"

Write-Host $testResult -ForegroundColor Green

# Messages finaux
Write-Host "`n=== INSTALLATION TERMINEE ===" -ForegroundColor Magenta
if ($useGPU) {
    Write-Host "[GPU] GPU NVIDIA detecte et configure!" -ForegroundColor Green
    Write-Host "[PERF] Performances SAM2 optimisees" -ForegroundColor Green
} else {
    Write-Host "[CPU] Mode CPU configure" -ForegroundColor Yellow
    Write-Host "[TIP] Pour GPU: Installez pilotes NVIDIA et relancez avec -Force" -ForegroundColor Yellow
}

Write-Host "`nUSAGE:" -ForegroundColor Yellow
Write-Host "  uv shell                 # Activer environnement"
Write-Host "  uv run jupyter lab       # Lancer Jupyter directement"
Write-Host "  uv run python script.py  # Executer un script"

Write-Success "EVA2SPORT pret a l'emploi!" 