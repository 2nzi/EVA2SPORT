# 📔 Guide des Notebooks - EVA2SPORT

## 🎯 Recommandations d'utilisation

| Environnement | Utilisation recommandée | Avantages |
|---------------|-------------------------|-----------|
| 🌐 **Google Colab** | ✅ **Notebooks (recommandé)** | Installation automatique, GPU à louer facilement accessible |
| 💻 **Local** | ⚙️ **Pipeline Python** | Performance optimale, contrôle total |

> 💡 **Pour usage local**, nous recommandons plutôt la **pipeline Python** avec les scripts dans `/examples/` ou `/tests/`. Les notebooks sont principalement optimisés pour Google Colab.

## 🎬 Tutoriel vidéo

Suivez cette démonstration complète de l'utilisation des notebooks : 'new_url'


---

## 📋 Prérequis

### 🆕 **Nouvelle configuration** : 2 fichiers séparés

**Ancien système** (dépréciée) :
- ❌ `nom_video_config.json` (fichier unique)

**Nouveau système** (recommandé) :
- ✅ `nom_video_calib.json` (calibration caméra)
- ✅ `nom_video_objects.json` (annotations d'objets)

### 📁 Fichiers requis

Avant de commencer, assurez-vous d'avoir :
```
📁 Votre dossier de travail/
├── 🎥 nom_video.mp4                    # Vidéo source
├── 📊 nom_video_calib.json             # 🆕 Configuration caméra
└── 🎯 nom_video_objects.json           # 🆕 Annotations objets
```

**Exemple de nom de fichiers :**
```
📁 /content/data/videos/
├── 🎥 SD_13_06_2025_cam1.mp4
├── 📊 SD_13_06_2025_cam1_calib.json
├── 🎯 SD_13_06_2025_cam1_objects.json
└── Timeline_g_SD.csv (optionel)
```

> 📚 **Guide de configuration détaillée** : [Configuration des fichiers](../data/README.md)

---

## 🌐 Mode recommandé : Google Colab

### 🚀 **Notebook principal : SAM_EVA2PERF_COLAB.ipynb**

Ce notebook utilise directement la **librairie EVA2Sport** pour une utilisation simplifiée !

#### ✨ **Fonctionnalités principales**

| Cas d'usage | Description | Temps de traitement |
|-------------|-------------|-------------------|
| 🎯 **Segment spécifique** | Traite un événement précis | ⚡ 2-5 minutes |
| 🎬 **Vidéo complète** | Analyse toute la vidéo | ⏳ 10-30 minutes |
| 📊 **Multi-événements CSV** | Traite plusieurs événements depuis un fichier CSV | ⏱️ Variable |

#### 🛠️ **Installation automatique**

Le notebook installe automatiquement :
```python
# Cellule 1: Installation des dépendances
!pip install git+https://github.com/2nzi/EVA2SPORT.git@dev-pipeline-eva2sport
!pip install git+https://github.com/facebookresearch/sam2.git
!pip install opencv-python torch
```

#### ⚙️ **Configuration simplifiée**

```python
# Cellule 3: Configuration globale - MODIFIEZ SELON VOS BESOINS
VIDEO_NAME = "SD_13_06_2025_cam1"  # ⚠️ Nom de base de votre vidéo
WORKING_DIR = "/content"

# ✅ Le notebook détecte automatiquement :
# - SD_13_06_2025_cam1.mp4
# - SD_13_06_2025_cam1_calib.json  
# - SD_13_06_2025_cam1_objects.json
```

#### 🚀 **Utilisation**

1. **📁 Upload vos fichiers** dans `/content/data/videos/`
2. **⚙️ Modifiez** `VIDEO_NAME` dans la cellule 3
3. **▶️ Exécutez** les cellules selon votre cas d'usage
4. **💾 Récupérez** les résultats depuis Google Drive (dernière cellule)

### 🎯 **Cas d'usage détaillés**

#### **🎯 Cas 1 : Segment spécifique**
```python
# Cellule 5: Configuration du segment
EVENT_TIMESTAMP = 959  # secondes ⚠️ MODIFIEZ SELON VOTRE ÉVÉNEMENT
OFFSET_BEFORE = 10.0   # secondes avant l'événement
OFFSET_AFTER = 5.0     # secondes après l'événement

# Résultat : Vidéo annotée du segment 949s-964s
```

#### **🎬 Cas 2 : Vidéo complète**
```python
# Cellule 6: Traitement complet
PROCESS_FULL_VIDEO = True  # ⚠️ Changez en True pour activer

# Résultat : Toute la vidéo annotée
```

#### **📊 Cas 3 : Multi-événements CSV**
```python
# Cellule 7: Traitement depuis CSV
CSV_FILE = "Timeline_g_SD.csv"
timestamp_column = 'Start time'    # ⚠️ Nom de votre colonne
filter_column = 'Row'              # ⚠️ Colonne de filtrage  
filter_value = 'PdB'               # ⚠️ Valeur à filtrer

# Résultat : Plusieurs vidéos annotées selon le CSV
```

---

## 💻 Usage local (optionnel)

### ⚠️ **Recommandation importante**

Pour un **usage local**, nous recommandons plutôt d'utiliser la **pipeline Python** :

```powershell
# Scripts recommandés pour usage local
.\examples\event_processing.py      # 🚀 Script principal
.\tests\test_full_pipeline.py       # 🧪 Tests complets
.\tests\test_multi_event_manager.py # 📊 Tests multi-événements
```


### 🛠️ **Si vous voulez quand même utiliser les notebooks en local**


#### Notebooks disponibles (mode local - old version)

https://github.com/2nzi/EVA2SPORT/blob/main/docs/DEMO_TRACKING.mp4

- `SAM_inference.ipynb` - Traitement principal SAM2
- `SAM_viz.ipynb` - Visualisation des résultats
- `SAM_inference_segment.ipynb` - Segmentation vidéo avancée

---

## 🔄 Migration depuis l'ancienne version

### 🔄 **Comment migrer vos fichiers**

Si vous avez encore l'ancien fichier `nom_video_config.json` :

1. **📄 Séparez** votre configuration en 2 fichiers
2. **✂️ Extrayez** la section `calibration` → `nom_video_calib.json`
3. **✂️ Extrayez** la section `objects` → `nom_video_objects.json`

**Exemple de migration :**

```json
// Ancien: SD_13_06_2025_cam1_config.json
{
  "calibration": { 
    "camera_matrix": [...],
    "distortion_coeffs": [...],
    // ... autres paramètres de calibration
  },
  "objects": [
    ...
  ]
}
```

**Devient :**

```json
// Nouveau: SD_13_06_2025_cam1_calib.json
{
  "calibration":[...]
}
```

```json
// Nouveau: SD_13_06_2025_cam1_objects.json
[
  {
    "objects": [...], 
    "initial_annotations":[...]
  }
]
```

---

## 🎯 Structure des sorties

Les notebooks génèrent automatiquement :

```
📁 data/videos/outputs/nom_video/
├── 📁 frames/                          # 🖼️ Images extraites
├── 📁 masks/                           # 🎭 Masques de segmentation
├── 📄 nom_video_project.json           # 📊 Résultats complets
└── 🎥 nom_video_annotated.mp4          # 🎬 Vidéo finale annotée
```

---



## 📚 Ressources

- 📖 [Configuration des fichiers](../data/README.md)
- 🚀 [Scripts d'exemple](../examples/)
- 🧪 [Tests de la pipeline](../tests/)
- 📋 [Documentation SAM2](https://github.com/facebookresearch/sam2)

---
