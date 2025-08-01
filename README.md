# EVA2SPORT⚽

[![Install Status](https://img.shields.io/badge/install-automatic-green)](./install.ps1)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![PyTorch](https://img.shields.io/badge/pytorch-2.5+-orange)](https://pytorch.org)



## 🎬 Résultat en action

https://github.com/user-attachments/assets/49f97043-2ef4-4dae-baa9-35fb35d7be2f

*Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive*

---


<br>
<br>

TUTO VIDEO: https://github.com/user-attachments/assets/6336aa21-64ce-4331-965e-2dfff3b0b5c2


## 🚀 Installation préalable

### 📋 Étape 1 : Installer Git (si nécessaire)

**Vérifiez d'abord si Git est installé :**
```powershell
git --version
```

**Si Git n'est pas installé :**
```powershell
# Option 1 : Téléchargement direct (recommandé)
# https://git-scm.com/download/win

# Option 2 : Via winget (Windows 10/11)
winget install Git.Git
```

### 📋 Étape 2 : Récupérer le projet

```powershell
# Cloner le projet
git clone https://github.com/2nzi/EVA2SPORT.git
cd EVA2SPORT
```

---
<br>
<br>

## 🎯 Recommandations d'utilisation

### 🤔 **Quel mode choisir ?**

| Votre situation | Mode recommandé | Avantages |
|-----------------|-----------------|-----------|
| 🖥️ **Pas de GPU puissant** <br/> *(GPU intégré, ancien GPU, ou CPU uniquement)* | 🌐 **Google Colab** | GPU A100, installation automatique, simplicité |
| 💪 **GPU puissant disponible** <br/> *(RTX 3070+, RTX 4060+ idéalement)* | 💻 **Pipeline locale** | Performance maximale, contrôle total, pas de limite de temps |

### 🚀 **Installation selon votre choix**

#### 🌐 **Mode Google Colab (GPU faible/absent)**

**Aucune installation nécessaire !** 
- Utilisez directement : **[SAM_EVA2PERF_COLAB.ipynb](notebook/SAM_EVA2PERF_COLAB.ipynb)**
- GPU (à louer) fourni par Google : 100 crédit = 10€ | L4 ~ 2 credit/h | A100 ~ 7 credit/h
- Installation automatique de toutes les dépendances

#### 💻 **Mode Pipeline locale (GPU puissant)**

```powershell
# Installation automatique complète
.\install.ps1

# Vérification de votre GPU
uv run python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

**L'installation se charge automatiquement de :**
- ✅ Installer uv (gestionnaire de paquets Python moderne)
- ✅ Détecter et configurer votre GPU automatiquement  
- ✅ Installer Python 3.10+ si nécessaire
- ✅ Télécharger le modèle SAM2 (~2GB)
- ✅ Configurer l'environnement complet

*⏱️ Temps d'installation : 5-15 minutes selon votre connexion*

---

<br>
<br>


## 📊 Workflow Complet - 3 Étapes

### 🎯 **Étape 1 : Préparez vos données**

**Créez vos fichiers de configuration** avec nos interfaces simplifiées :
- 📊 **Calibration caméra** : <https://2nzi-footballfieldcalibaration.hf.space/>
- 🎯 **Annotation objets** : <https://2nzi-pointtrackapp.hf.space/>

**📖 Guide détaillé :** [Configuration des données](data/README.md)

**Résultat :** Vous obtenez 2 fichiers pour votre vidéo :
```
📁 data/videos/
├── 🎥 ma_video.mp4
├── 📊 ma_video_calib.json          # Configuration caméra
└── 🎯 ma_video_objects.json        # Annotations objets
```

### 🚀 **Étape 2 : Choisissez votre mode de traitement**

#### 🌐 **Mode A : Google Colab (recommandé si GPU faible)**

**3 types de traitement disponibles :**

| Mode | Description | Temps | Usage |
|------|-------------|-------|-------|
| 🎯 **Segment événement** | Traite un événement précis (ex: 10s autour d'un but) | ⚡ 2-5 min | Actions spécifiques |
| 🎬 **Vidéo complète** | Analyse toute la vidéo | ⏳ 10-30 min | Analyse globale |
| 📊 **Multi-événements CSV** | Traite plusieurs événements depuis un fichier Timeline | ⏱️ Variable | Analyse en lot |

**🚀 Démarrage :** [SAM_EVA2PERF_COLAB.ipynb](notebook/SAM_EVA2PERF_COLAB.ipynb)

#### 💻 **Mode B : Pipeline locale (recommandé si GPU puissant)**

**Plusieurs scripts selon vos besoins :**

```powershell
# Mode événement lecture csv events
python examples/event_processing.py

# Mode pipeline complète
python tests/test_full_pipeline.py

# Mode multi-événements 
python tests/test_multi_event_manager.py
```

### 📊 **Étape 3 : Récupérez vos résultats**

**Fichiers générés automatiquement :**
```
📁 data/videos/outputs/ma_video/
├── 📁 frames/                          # Images extraites
├── 📄 ma_video_project.json            # Données de tracking
└── 🎥 ma_video_annotated.mp4           # Vidéo finale annotée
```

---

<br>
<br>
<br>


## 🔧 Aide et Troubleshooting

### 🚨 **Problèmes courants**

| Problème | Solution |
|----------|----------|
| `git command not found` | ✅ Installez Git : https://git-scm.com/download/win |
| `uv not found` | ✅ Relancez `.\install.ps1` |
| `CUDA not available` | 🌐 Utilisez Google Colab |
| `Out of memory` | 🔄 Augmentez la FRAME_INTERVAL ou utilisez Colab |
| `FileNotFoundError: calib.json` | 📊 Suivez le guide de configuration des données |

### 💡 **Optimisation performances**

**Pour GPU local :**
```powershell
# Vérifier votre configuration GPU
nvidia-smi

# Surveiller l'utilisation durant le traitement
watch -n 1 nvidia-smi
```

**Pour Google Colab :**
- ✅ Utilisez Colab Pro pour GPU A100 et sessions plus longues
- 🔄 Sauvegardez régulièrement sur Google Drive

---

## 📚 Organisation de la documentation

| Guide | Objectif | Quand l'utiliser |
|-------|----------|------------------|
| **[🛠️ README Principal](README.md)** | Installation + vue d'ensemble | ✅ **Point de départ** |
| **[📁 Configuration des Données](data/README.md)** | Processus complet avec interfaces externes | ✅ Étape 1 obligatoire |
| **[📔 Guide des Notebooks](notebook/README.md)** | Notebooks Colab + locaux | ✅ Mode notebook choisi |
| **[⚙️ Guide Pipeline](examples/README.md)** | Scripts Python | ✅ Mode pipeline choisi |

### 🔄 **Navigation rapide**
- 🆕 **Nouveau sur EVA2SPORT ?** → Lisez ce README puis [Configuration des données](data/README.md)
- 🎬 **Données prêtes ?** → Choisissez [Colab](notebook/SAM_EVA2PERF_COLAB.ipynb) ou [Pipeline locale](examples/)
- 🐛 **Problème ?** → Consultez les sections troubleshooting de chaque guide

---

## 🎥 Ressources et tutoriels

### 📹 **Vidéos de démonstration**
- 🎬 **[Tutoriel complet d'utilisation](docs/DEMO_TRACKING.mp4)**
- 📊 **[Résultat final en action](docs/VIDEO_EXEMPLE_GITHUB.mp4)**


---

### 📋 **Prérequis système**

**Minimum (mode Colab) :**
- Connexion internet stable
- Navigateur moderne

**Recommandé (mode local) :**
- Windows 10/11 avec PowerShell
- GPU NVIDIA avec 6GB+ VRAM (RTX 3070+, RTX 4060+)
- ~5GB d'espace disque libre
- 16GB+ RAM recommandés

---

