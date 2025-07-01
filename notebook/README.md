# 📔 Guide des Notebooks - EVA2SPORT

Ce guide explique comment utiliser EVA2SPORT via les notebooks Jupyter, en mode local ou Google Colab.

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir :
- ✅ **Configuration vidéo complète** : [Guide de configuration](../data/README.md)
- ✅ **Fichiers requis** : `nom_video.mp4` + `nom_video_config.json`

## 🎯 Vue d'ensemble des notebooks

| Notebook | Rôle | Utilisation |
|----------|------|-------------|
| `SAM_inference.ipynb` | 🚀 **Traitement principal** | Segmentation SAM2 + génération results |
| `SAM_viz.ipynb` | 📊 **Visualisation** | Analyse et visualisation des résultats |

### 🔄 Workflow complet
```
📄 config.json → 🚀 SAM_inference → 📊 project.json → 📈 SAM_viz → 🎥 vidéo annotée
```

---

## 💻 Mode 1 : Notebook Local

### 🛠️ Installation préalable
```powershell
# Depuis la racine du projet
.\install.ps1
```

### 🚀 Lancement
```powershell
# Démarrer Jupyter Lab
uv run jupyter lab

# Ou dans votre IDE préféré (VS Code, Cursor...)
```

### 📝 Utilisation de SAM_inference.ipynb

#### 1. **Configuration du projet**
```python
# 📋 CONFIGURATION PRINCIPALE - Modifiez ces valeurs
VIDEO_NAME = "votre_video"              # ⚠️ Nom sans extension
VIDEOS_DIR = "../data/videos"           # 📁 Chemin des vidéos
FRAME_INTERVAL = 3                      # 🎬 Intervalle extraction (1=toutes, 3=1 sur 3)
```

#### 2. **Options d'extraction**
```python
EXTRACT_FRAMES = True                   # ✅ Extraire les frames
FORCE_EXTRACTION = False                # 🔄 Forcer même si frames existent
```


### 📊 Utilisation de SAM_viz.ipynb

#### 1. **Configuration**
Utilisez les **mêmes paramètres** que SAM_inference :
```python
VIDEO_NAME = "votre_video"              # ⚠️ Identique à SAM_inference
VIDEOS_DIR = "../data/videos"           # 📁 Même chemin
```

#### 2. **Fonctionnalités disponibles**
- 🎥 **Visualisation frame par frame**
- 🎭 **Affichage des masques** de segmentation  
- 📊 **Statistiques** par objet/équipe
- 🎨 **Génération vidéo annotée** finale

---

## ☁️ Mode 2 : Google Colab

Parfait pour tester sans installation locale !

### 🚀 Configuration Colab - SAM_inference

#### 1. **Upload dans Colab**
```python
# Uploadez SAM_inference.ipynb dans Colab
# Créez un dossier 'videos' dans Colab
```

#### 2. **Modification obligatoire**
```python
using_colab = True                      # ⚠️ CHANGEZ À True
VIDEO_NAME = "votre_video"
VIDEOS_DIR = "./videos"                 # 📁 Chemin Colab
```

#### 3. **Upload de vos fichiers**
Dans Colab, uploadez dans `/content/videos/` :
- `votre_video.mp4`
- `votre_video_config.json`

#### 4. **Installation automatique**
La première cellule installe automatiquement :
- ✅ SAM2 + dépendances
- ✅ Modèle SAM2
- ✅ Configuration CUDA

### 📊 Configuration Colab - SAM_viz

#### 1. **Option A : Zip depuis Drive**
```python
# Le notebook peut restaurer depuis un zip Google Drive
zip_path = f'/content/drive/MyDrive/{VIDEO_NAME}.zip'
```

#### 2. **Option B : Upload direct**
Uploadez tous les fichiers de résultats dans `/content/videos/outputs/`


---

## 🎯 Configuration Détaillée

### 📹 Paramètres Vidéo

```python
# Ajustez selon vos besoins
FRAME_INTERVAL = 1                      # Toutes les frames (plus précis, plus lent)
FRAME_INTERVAL = 3                      # 1 frame sur 3 (balance qualité/vitesse)  
```

### ⚙️ Paramètres SAM2

```python
# Dans les cellules SAM2, vous pouvez ajuster :
sam2_checkpoint = "sam2.1_hiera_large.pt"  # Modèle (large=précis, small=rapide)
```

### 💾 Gestion des sorties

Les notebooks génèrent automatiquement :
```
videos/outputs/votre_video/
├── frames/                             # 🖼️ Images extraites
├── votre_video_project.json            # 📊 Résultats complets
└── votre_video_annotated.mp4           # 🎥 Vidéo finale annotée
```

---

## 🔧 Troubleshooting

### 🚨 Erreurs courantes

| Erreur | Solution |
|--------|----------|
| `FileNotFoundError: config.json` | Vérifiez le nom et l'emplacement du fichier config |
| `CUDA out of memory` | Réduisez FRAME_INTERVAL ou redémarrez le kernel |
| `Module 'sam2' not found` | En local: relancez `.\install.ps1` |
| `Checkpoint not found` | Vérifiez le téléchargement du modèle SAM2 |
| `Kernel shutdown` | Relancer tout le notebook |


### 🔄 Reprendre un traitement interrompu

```python
# GPU A100 conseillé sur colab
# Les résultats partiels sont sauvegardés automatiquement
# Relancer le notebook

```

---

## 📊 Analyse des Résultats

### 📄 Fichier project.json

Structure des résultats générés :
```json
{
  "calibration": {
    ...
  },
  "objects": [
    ...
  ],
  "initial_annotations": [
    ...
  ]
}
```

### 🎥 Vidéo annotée

La vidéo finale contient :
TODO

---

## 🚀 Prochaines étapes

- **📈 Analysez vos résultats** avec SAM_viz.ipynb
- **🔄 Itérez** : ajustez la config si nécessaire  
- **⚙️ Production** : [Pipeline Python](../README.md#mode-3--pipeline-python-bientôt) (bientôt)