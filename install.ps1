<#
.SYNOPSIS
    Installation EVA2SPORT - uv seulement
.PARAMETER CPUOnly  
    Force installation CPU
.PARAMETER Force
    Réinstallation complète
#>

param(
    [switch]$CPUOnly = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

Write-Host "=== INSTALLATION EVA2SPORT ===" -ForegroundColor Magenta

# INSTALLATION UV SI NECESSAIRE
try {
    uv --version | Out-Null
    Write-Success "uv detecte"
} catch {
    Write-Info "Installation d'uv..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    Start-Sleep 2
    uv --version | Out-Null
    Write-Success "uv installe"
}

# DETECTION GPU
$useGPU = $true
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
uv venv --python 3.10

# INSTALLATION DEPENDANCES DE BASE
Write-Info "Installation dependances depuis pyproject.toml..."
uv sync --extra jupyter

# INSTALLATION PYTORCH
if ($useGPU) {
    Write-Info "Installation PyTorch GPU (CUDA 12.1)..."
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
} else {
    Write-Info "PyTorch CPU (depuis pyproject.toml)"
}

# INSTALLATION SAM2 - COMMENTE POUR TEST
Write-Info "Installation SAM2 depuis GitHub..."
uv pip install "sam-2 @ git+https://github.com/facebookresearch/sam2.git" --force-reinstall

# CONFIGURATION JUPYTER - COMMENTE POUR TEST
Write-Info "Configuration kernel Jupyter..."
try {
    uv run python -m ipykernel install --user --name eva2sport --display-name "Python (EVA2SPORT)"
    Write-Success "Kernel Jupyter configure"
} catch {
    Write-Warning "Echec configuration kernel (non critique)"
}

# TELECHARGEMENT MODELE SAM2 - COMMENTE POUR TEST
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
} else {
    Write-Success "Modele SAM2 deja present"
}

# VERIFICATION FINALE
Write-Info "Verification PyTorch et CUDA..."
$testScript = @'
import torch
print(f'PyTorch {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'Device count: {torch.cuda.device_count()}')
    print(f'Current device: {torch.cuda.current_device()}')
    print(f'Device name: {torch.cuda.get_device_name(0)}')
else:
    print('CUDA version: N/A')
    print('Device count: 0')
'@

try {
    $result = uv run python -c $testScript
    Write-Host $result -ForegroundColor Green
} catch {
    Write-Warning "Erreur verification PyTorch"
}

# ACTIVATION DE L'ENVIRONNEMENT
Write-Info "Activation de l'environnement virtuel..."
try {
    & .\.venv\Scripts\activate.ps1
    Write-Success "Environnement virtuel active"
} catch {
    Write-Warning "Impossible d'activer automatiquement l'environnement"
    Write-Info "Lancez manuellement: .\.venv\Scripts\activate.ps1"
}

# MESSAGES FINAUX
Write-Host "`n=== INSTALLATION TERMINEE ===" -ForegroundColor Magenta
Write-Success "EVA2SPORT pret et environnement active!"

Write-Host "`nUSAGE:" -ForegroundColor Yellow
Write-Host "  python -c 'import torch; print(torch.cuda.is_available())'   # Tester PyTorch"
Write-Host "  jupyter notebook                                              # Lancer Jupyter"
Write-Host "  deactivate                                                    # Desactiver environnement"
Write-Host ""
Write-Host "  Ou avec uv (sans activation):" -ForegroundColor Cyan
Write-Host "  uv run python -c 'import torch; print(torch.cuda.is_available())'"
Write-Host "  uv run jupyter notebook"

if ($useGPU) {
    Write-Host "`nGPU: Acceleration NVIDIA activee" -ForegroundColor Green
} else {
    Write-Host "`nCPU: Mode processeur" -ForegroundColor Yellow
}

Write-Success "Installation terminee et environnement active!" 