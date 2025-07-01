# EVA2SPORT⚽

[![Install Status](https://img.shields.io/badge/install-automatic-green)](./install.ps1)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![PyTorch](https://img.shields.io/badge/pytorch-2.5+-orange)](https://pytorch.org)


## 🎬 Résultat en action

Découvrez EVA2SPORT en action avec cette démonstration de segmentation en temps réel :

<video src="docs/VIDEO_EXEMPLE_GITHUB.mp4" controls width="100%"></video>


Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive.

## 🚀 Installation rapide

### 📋 Prérequis

**Seul prérequis manuel :**
- **Git** pour cloner le repository

**Prérequis automatiques :**
- **Windows 10/11** avec PowerShell
- **uv** (sera installé automatiquement par `install.ps1`)
- **Python 3.10+** (sera installé automatiquement par uv si nécessaire)
- **~5GB d'espace disque** (modèles + dépendances)
- **Connexion internet** pour téléchargements

#### Installation de Git (si pas déjà installé)
```powershell
# Option 1 : Téléchargement direct
# https://git-scm.com/download/win

# Option 2 : Via winget
winget install Git.Git

# Vérification
git --version
```

### 🚀 Installation du projet en 3 étapes

```powershell
# 1. Cloner le projet
git clone https://github.com/2nzi/EVA2SPORT.git
cd EVA2SPORT

# 2. Lancer l'installation automatique (installe uv + Python + dépendances)
.\install.ps1

# 3. Démarrer Jupyter
uv run jupyter lab
```

**C'est tout !** 🎉 L'installation se charge de :
- ✅ Installer uv automatiquement
- ✅ Détecter votre GPU automatiquement  
- ✅ Installer Python 3.10 si nécessaire
- ✅ Télécharger le modèle SAM2
- ✅ Configurer l'environnement complet

*⏱️ Temps d'installation : 5-15 minutes selon votre connexion*

### 🚨 Si Git n'est pas installé

**Message d'erreur typique :**

## 📊 Workflow Complet - 3 Étapes Simples

### 🎯 **Étape 1 : Configuration des Données**
Créez vos fichiers de configuration avec nos interfaces extérieures :
- 🛠️ **[Guide complet de configuration](data/README.md)** - Processus détaillé avec interfaces
- 📄 Génère : `votre_video_config.json`

### 🚀 **Étape 2 : Choisir votre Mode de Traitement**

#### 💻 **Mode Notebook Local** (recommandé)

```powershell
# Après installation
uv run jupyter lab
```

# Puis suivre le guide notebook
- 📖 **[Guide notebook complet](notebook/README.md)** - Instructions détaillées
- ⚡ Performance optimale avec votre GPU

#### ☁️ **Mode Google Colab** 
- 📖 **[Guide Colab détaillé](notebook/README.md#mode-2--google-colab)**
- ✅ Aucune installation requise
- 🔄 GPU A100 + sauvegarde Drive

#### ⚙️ **Mode Pipeline Python** (bientôt)
- 🚧 Scripts autonomes pour production
- 🔄 En développement

### 📊 **Étape 3 : Visualisation & Analyse**
- 🎥 Génération vidéo annotée
- 📈 Statistiques détaillées par équipe/joueur (TODO)

### Premier test
```powershell
# Vérifier que tout fonctionne
uv run python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

## 📚 Organisation de la Documentation

Cette documentation est organisée en guides spécialisés pour vous accompagner étape par étape :

| Guide | Objectif | Quand l'utiliser |
|-------|----------|------------------|
| **[📁 Configuration des Données](data/README.md)** | Processus complet avec les 2 interfaces externes | ✅ **Première étape obligatoire** |
| **[📔 Guide des Notebooks](notebook/README.md)** | Utilisation locale + Colab | ✅ Après configuration des données |
| **[🛠️ README Principal](README.md)** | Installation + vue d'ensemble | ✅ Point de départ |

### 🔄 Navigation rapide
- 🚀 **Nouveau sur EVA2SPORT ?** → Commencez ici puis [Configuration](data/README.md)
- 🎬 **Vidéo prête ?** → [Guide Notebooks](notebook/README.md)  
- 🐛 **Problème ?** → Sections troubleshooting de chaque guide



## 🎥 Tutoriels Vidéo

Nouveau sur EVA2SPORT ? Regardez notre tutoriel complet :

[![EVA2SPORT - Guide Complet](docs/assets/thumbnails/main-tutorial-thumbnail.png)](LIEN_VOTRE_VIDEO)

📚 **[Tous les tutoriels disponibles](docs/tutorials/README.md)**
