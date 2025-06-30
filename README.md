# EVA2SPORT 🏀⚽

Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive.

## 🚀 Installation rapide

### Prérequis

- Python 3.10 ou supérieur
- CUDA compatible GPU (recommandé)
- Git

### Installation avec uv (recommandé)

1. **Installer uv** (si pas déjà fait) :
```bash
# Windows
curl -LsSf https://astral.sh/uv/install.ps1 | powershell

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Cloner et installer le projet** :
```bash
git clone https://github.com/yourusername/EVA2SPORT.git
cd EVA2SPORT
uv sync
```

3. **Activer l'environnement** :
```bash
# Windows
uv run python --version

# Ou pour obtenir un shell
uv shell
```

### Installation alternative avec pip

```bash
git clone https://github.com/yourusername/EVA2SPORT.git
cd EVA2SPORT
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows

pip install -e .
```

### Installation avec Jupyter

Pour utiliser les notebooks :

```bash
uv sync --extra jupyter
# ou avec pip
pip install -e ".[jupyter]"
```

## 📋 Utilisation

### 1. Préparer vos données

Placez vos fichiers dans le dossier `data/videos/` :
- `video_name.mp4` - votre vidéo
- `video_name_config.json` - fichier de configuration

### 2. Lancer l'analyse

#### Via les notebooks Jupyter :
```bash
uv run jupyter lab
```

Ou alors ouvrir directement dans l'IDE.

`SAM_inference.ipynb` ou `SAM_viz.ipynb`.

<!-- 
#### Via script Python :
```python
from eva2sport import VideoSegmentationPipeline

pipeline = VideoSegmentationPipeline(
    video_path="data/videos/your_video.mp4",
    config_path="data/videos/your_video_config.json"
)

results = pipeline.run()
```

## 🔧 Configuration

Le fichier de configuration JSON doit contenir :

```json
{
    "calibration": {
        "camera_matrix": [...],
        "distortion_coefficients": [...]
    },
    "objects": [
        {
            "id": 1,
            "name": "player",
            "color": [255, 0, 0]
        }
    ],
    "initial_annotations": [
        {
            "frame_idx": 0,
            "annotations": [...]
        }
    ]
}
```

## 🐛 Problèmes courants

### Installation de SAM2 échoue

Si l'installation de SAM2 échoue, vérifiez :
- CUDA toolkit est installé et compatible
- PyTorch est bien installé avec CUDA
- Compilateur C++ disponible

### Windows WSL recommandé

Sur Windows, il est fortement recommandé d'utiliser WSL2 avec Ubuntu.

## 📦 Structure du projet 

## Installation en UNE commande

```powershell
# Cloner et installer
git clone https://github.com/yourusername/EVA2SPORT.git
cd EVA2SPORT
.\install.ps1
```

## Utilisation

```powershell
# Lancer Jupyter directement
uv run jupyter lab

# Ou activer l'environnement
uv shell
jupyter lab
```

C'est tout ! 🎉  -->