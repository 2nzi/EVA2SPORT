# 🎯 SAM2 Inference avec Segmentation Vidéo

Ce notebook permet d'utiliser SAM2 pour le suivi d'objets dans une vidéo, avec une fonctionnalité de **segmentation vidéo** qui permet de traiter seulement une partie de la vidéo autour d'une frame de référence.

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Types de frames et conversions](#types-de-frames-et-conversions)
3. [Mode segmentation vs mode complet](#mode-segmentation-vs-mode-complet)
4. [Configuration](#configuration)
5. [Fonctionnement step-by-step](#fonctionnement-step-by-step)
6. [Exemples concrets](#exemples-concrets)
7. [Troubleshooting](#troubleshooting)

---

## 🔍 Vue d'ensemble

Le notebook traite une vidéo en plusieurs étapes :
1. **Extraction des frames** selon un intervalle défini
2. **Ajout d'annotations initiales** sur une frame de référence
3. **Propagation bidirectionnelle** pour suivre les objets
4. **Génération des annotations** pour toutes les frames

Le système supporte deux modes :
- **Mode complet** : traite toute la vidéo
- **Mode segmentation** : traite seulement un segment autour de la frame de référence

---

## 🎬 Types de frames et conversions

### 📊 Types de frames

Le système utilise plusieurs types d'indexation des frames :

| Type | Description | Exemple | Usage |
|------|-------------|---------|-------|
| **Frame originale** | Index dans la vidéo source | `280` | Référence utilisateur |
| **Frame traitée** | Index après application de l'intervalle | `93` | Calculs internes |
| **Frame pour SAM** | Index utilisé par SAM2 | `7` | Modèle SAM2 |
| **Frame d'ancrage** | Frame de référence avec annotation | `280` | Point de départ |

### 🔄 Processus de conversion

```
📹 Vidéo originale (624 frames)
    ↓ (FRAME_INTERVAL = 3)
🎬 Frames traitées (208 frames)
    ↓ (MODE SEGMENTATION)
🎯 Segment extrait (14 frames)
    ↓ (NOMMAGE SÉQUENTIEL)
📁 Fichiers: 00000.jpg → 00013.jpg
```

### 📐 Formules de conversion

#### Mode complet
```python
frame_traitée = frame_originale // FRAME_INTERVAL
```

#### Mode segmentation
```python
# 1. Conversion de base
frame_traitée = frame_originale // FRAME_INTERVAL

# 2. Calcul du segment
segment_start = référence_frame - OFFSET_BEFORE
segment_end = référence_frame + OFFSET_AFTER
segment_start_traité = segment_start // FRAME_INTERVAL

# 3. Index dans le segment
frame_pour_sam = frame_traitée - segment_start_traité
```

---

## 🎯 Mode segmentation vs mode complet

### 🎬 Mode complet (`SEGMENT_MODE = False`)

```python
# Configuration
SEGMENT_MODE = False
FRAME_INTERVAL = 3

# Résultat
- Traite toute la vidéo
- Extrait 1 frame sur 3
- Nommage: 00000.jpg, 00001.jpg, 00002.jpg...
- Frame anchor conserve sa position relative
```

**Exemple :**
- Vidéo : 624 frames
- Intervalle : 3
- Frames extraites : 208 (0, 3, 6, 9, 12, ...)
- Nommage : 00000.jpg (frame 0), 00001.jpg (frame 3), etc.

### 🎯 Mode segmentation (`SEGMENT_MODE = True`)

```python
# Configuration
SEGMENT_MODE = True
SEGMENT_OFFSET_BEFORE = 20
SEGMENT_OFFSET_AFTER = 20
FRAME_INTERVAL = 3

# Résultat
- Traite seulement un segment autour de la frame de référence
- Extrait 1 frame sur 3 dans ce segment
- Nommage séquentiel : 00000.jpg, 00001.jpg, 00002.jpg...
- Frame anchor repositionnée dans le segment
```

**Exemple :**
- Frame de référence : 280
- Segment : frames 260 à 300 (41 frames)
- Avec intervalle 3 : frames 260, 263, 266, ..., 299 (14 frames)
- Nommage : 00000.jpg à 00013.jpg
- Frame anchor 280 → index 7 dans le segment

---

## ⚙️ Configuration

### 🎯 Paramètres principaux

```python
class Config:
    # Vidéo et extraction
    VIDEO_NAME = "ma_video"
    FRAME_INTERVAL = 3                    # 1 frame sur 3
    EXTRACT_FRAMES = True
    FORCE_EXTRACTION = False
    
    # 🎯 SEGMENTATION VIDÉO
    SEGMENT_MODE = True                   # Active la segmentation
    
    # 🕐 OFFSETS EN SECONDES (RECOMMANDÉ)
    SEGMENT_OFFSET_BEFORE_SECONDS = 2.0  # Secondes avant la référence
    SEGMENT_OFFSET_AFTER_SECONDS = 2.0   # Secondes après la référence
    
    # 🎬 OFFSETS EN FRAMES (OPTIONNEL)
    SEGMENT_OFFSET_BEFORE = None          # Frames avant (auto-calculé)
    SEGMENT_OFFSET_AFTER = None           # Frames après (auto-calculé)
    
    # SAM2
    SAM2_MODEL = "sam2.1_hiera_l"        # ou "sam2.1_hiera_s"
```

### 🕐 Offsets en secondes vs frames

Le système privilégie maintenant les **offsets en secondes** car c'est plus intuitif :

| Paramètre | Description | Exemple | Conversion automatique |
|-----------|-------------|---------|----------------------|
| `SEGMENT_OFFSET_BEFORE_SECONDS` | Secondes avant la référence | `2.0` | → 50 frames (à 25 FPS) |
| `SEGMENT_OFFSET_AFTER_SECONDS` | Secondes après la référence | `3.0` | → 75 frames (à 25 FPS) |
| `SEGMENT_OFFSET_BEFORE` | Frames avant (optionnel) | `50` | Utilisé si secondes = None |
| `SEGMENT_OFFSET_AFTER` | Frames après (optionnel) | `75` | Utilisé si secondes = None |

### 🔄 Conversion automatique

Le système détecte automatiquement le FPS de votre vidéo et convertit :

```python
# Configuration en secondes
SEGMENT_OFFSET_BEFORE_SECONDS = 2.0
SEGMENT_OFFSET_AFTER_SECONDS = 3.0

# Vidéo à 25 FPS → Conversion automatique
# 2.0s × 25 FPS = 50 frames avant
# 3.0s × 25 FPS = 75 frames après

# Vidéo à 30 FPS → Conversion automatique  
# 2.0s × 30 FPS = 60 frames avant
# 3.0s × 30 FPS = 90 frames après
```

### 📊 Priorité des paramètres

1. **Secondes** (si définies) : utilisées en priorité
2. **Frames** (si secondes = None) : utilisées en fallback  
3. **Défaut** (si tout = None) : 2.0 secondes

```python
# Exemple de configuration
if SEGMENT_OFFSET_BEFORE_SECONDS is not None:
    offset_frames = SEGMENT_OFFSET_BEFORE_SECONDS × FPS
elif SEGMENT_OFFSET_BEFORE is not None:
    offset_frames = SEGMENT_OFFSET_BEFORE  
else:
    offset_frames = 2.0 × FPS  # Défaut: 2 secondes
```

### 🎯 Paramètres de segmentation

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `SEGMENT_MODE` | Active/désactive la segmentation | `True` |
| `SEGMENT_OFFSET_BEFORE` | Frames avant la référence | `150` |
| `SEGMENT_OFFSET_AFTER` | Frames après la référence | `300` |

---

## 🚀 Fonctionnement step-by-step

### 1. 📋 Configuration centralisée
```python
cfg = Config()
cfg.setup_directories()
cfg.display_config()
```

### 2. 🤖 Installation SAM2
- Auto-détection Colab/Local
- Téléchargement des checkpoints si nécessaire

### 3. 📄 Chargement configuration projet
```python
project_config = load_and_validate_project_config(cfg.config_path)
```

### 4. 🎬 Extraction des frames
```python
# Mode segmentation
if cfg.SEGMENT_MODE:
    extracted_count = extract_segment_frames(...)
else:
    extracted_count = extract_frames(...)
```

### 5. 🤖 Initialisation SAM2
```python
predictor = initialize_sam2_predictor(cfg)
inference_state = initialize_inference_state(predictor, cfg)
```

### 6. 🎯 Ajout annotations initiales
```python
# Conversion des frames avec support segmentation
added_objects = add_initial_annotations(
    predictor, inference_state, project_config, 
    cfg.FRAME_INTERVAL, segment_info
)
```

### 7. 🔄 Propagation bidirectionnelle
```python
# Depuis la frame anchor vers les deux directions
project = run_sam2_bidirectional_propagation(cfg, project_config)
```

### 8. 💾 Sauvegarde
```python
save_project_results(cfg, project)
```

---

## 📝 Exemples concrets

### 🎯 Exemple 1 : Segmentation courte

```python
# Configuration
SEGMENT_MODE = True
SEGMENT_OFFSET_BEFORE_SECONDS = 1.0      # 1 seconde avant
SEGMENT_OFFSET_AFTER_SECONDS = 1.0       # 1 seconde après
FRAME_INTERVAL = 1

# Vidéo de 1000 frames à 25 FPS, annotation à la frame 500 (20s)
# Résultat :
# - Segment temporel : 19s à 21s (2 secondes au total)
# - Segment en frames : 475 à 525 (51 frames)
# - Extraction : toutes les frames du segment
# - Nommage : 00000.jpg à 00050.jpg
# - Frame anchor 500 → index 25 dans le segment
```

### 🎯 Exemple 2 : Segmentation avec intervalle

```python
# Configuration
SEGMENT_MODE = True
SEGMENT_OFFSET_BEFORE_SECONDS = 6.0      # 6 secondes avant
SEGMENT_OFFSET_AFTER_SECONDS = 12.0      # 12 secondes après
FRAME_INTERVAL = 10

# Vidéo de 2000 frames à 25 FPS, annotation à la frame 1000 (40s)
# Résultat :
# - Segment temporel : 34s à 52s (18 secondes au total)
# - Segment en frames : 850 à 1300 (451 frames)
# - Extraction : 1 frame sur 10 dans le segment
# - Frames extraites : 850, 860, 870, ..., 1300 (46 frames)
# - Nommage : 00000.jpg à 00045.jpg
# - Frame anchor 1000 → index 15 dans le segment
```

### 🎯 Exemple 3 : Mode complet

```python
# Configuration
SEGMENT_MODE = False
FRAME_INTERVAL = 5

# Vidéo de 500 frames à 25 FPS, annotation à la frame 250 (10s)
# Résultat :
# - Traite toute la vidéo (20 secondes)
# - Extraction : frames 0, 5, 10, 15, ..., 495 (100 frames)
# - Nommage : 00000.jpg à 00099.jpg
# - Frame anchor 250 → index 50 (250 // 5)
```

---

## 🎯 Frame Anchor : Explications détaillées

### 📍 Qu'est-ce que la frame anchor ?

La **frame anchor** (frame d'ancrage) est la frame de référence qui contient votre annotation initiale. C'est le point de départ de la propagation.

### 🔄 Transformations de la frame anchor

```python
# Exemple concret avec offsets en secondes
frame_anchor_originale = 280      # Frame dans la vidéo source
FRAME_INTERVAL = 3
SEGMENT_OFFSET_BEFORE_SECONDS = 0.67  # ~0.67s avant
SEGMENT_OFFSET_AFTER_SECONDS = 0.67   # ~0.67s après
FPS_VIDEO = 30                    # FPS de la vidéo

# 1. Conversion des secondes en frames
offset_before_frames = round(0.67 × 30) = 20
offset_after_frames = round(0.67 × 30) = 20

# 2. Conversion avec intervalle
frame_anchor_traitée = 280 // 3 = 93

# 3. Calcul du segment
segment_start = 280 - 20 = 260
segment_end = 280 + 20 = 300
segment_start_traité = 260 // 3 = 86

# 4. Position dans le segment
frame_anchor_pour_sam = 93 - 86 = 7

# 5. Résultat final
# - Frame originale : 280
# - Frame traitée : 93  
# - Frame pour SAM2 : 7
# - Fichier extrait : 00007.jpg
# - Durée du segment : 1.33s (40 frames à 30 FPS)
```

### 📊 Métadonnées stockées

Le système stocke toutes ces informations :

```json
{
  "metadata": {
    "anchor_frame": 280,           // Frame originale
    "anchor_processed_idx": 7,     // Index pour SAM2
    "segment_mode": true,
    "segment_start_frame": 260,
    "segment_end_frame": 300,
    "segment_reference_frame": 280
  }
}
```

---

## 🔧 Troubleshooting

### ❌ Erreur : "index out of bounds"

**Cause :** Frame anchor mal convertie pour le mode segmentation

**Solution :**
```python
# Vérifier les calculs
print(f"Frame anchor originale: {frame_anchor_originale}")
print(f"Frame anchor traitée: {frame_anchor_traitée}")
print(f"Frame anchor pour SAM: {frame_anchor_pour_sam}")
print(f"Frames disponibles: 0 à {extracted_frames_count - 1}")
```

### ❌ Erreur : "Fichier frame non trouvé"

**Cause :** Nommage des frames incorrect

**Solution :**
- En mode segmentation : frames nommées 00000.jpg, 00001.jpg, etc.
- En mode complet : frames nommées selon l'index traité

### ❌ Performance lente

**Solutions :**
- Réduire la taille du segment avec des offsets plus petits
- Augmenter `FRAME_INTERVAL` pour moins de frames
- Utiliser le modèle SAM2 small (`sam2.1_hiera_s`)

---

## 🎉 Conseils d'utilisation

### 💡 Choix du mode

- **Mode segmentation** : Pour des vidéos longues, focus sur une action spécifique
- **Mode complet** : Pour des vidéos courtes ou analyse complète

### 💡 Choix des offsets

```python
# Action courte (quelques secondes)
SEGMENT_OFFSET_BEFORE = 30
SEGMENT_OFFSET_AFTER = 30

# Action moyenne (10-20 secondes)  
SEGMENT_OFFSET_BEFORE = 150
SEGMENT_OFFSET_AFTER = 300

# Action longue (30+ secondes)
SEGMENT_OFFSET_BEFORE = 500
SEGMENT_OFFSET_AFTER = 1000
```

### 💡 Choix de l'intervalle

```python
# Mouvement rapide
FRAME_INTERVAL = 1    # Toutes les frames

# Mouvement normal
FRAME_INTERVAL = 3    # 1 frame sur 3

# Mouvement lent
FRAME_INTERVAL = 10   # 1 frame sur 10
```

---

## 🚀 Exemple pratique : Utilisation des offsets en secondes

### 📋 Scénario

Vous avez une vidéo de football de 10 minutes et vous voulez suivre un joueur spécifique pendant une action de 30 secondes autour du moment où il touche le ballon.

### ⚙️ Configuration recommandée

```python
# Dans la cellule de configuration
class Config:
    # Vidéo
    VIDEO_NAME = "match_football_10min"
    FRAME_INTERVAL = 2                    # 1 frame sur 2 pour économiser
    
    # 🎯 SEGMENTATION VIDÉO
    SEGMENT_MODE = True                   # ✅ Active la segmentation
    
    # 🕐 OFFSETS EN SECONDES (INTUITIVE)
    SEGMENT_OFFSET_BEFORE_SECONDS = 15.0  # 15 secondes avant le touch
    SEGMENT_OFFSET_AFTER_SECONDS = 15.0   # 15 secondes après le touch
    
    # ⚡ Plus besoin de calculer les frames manuellement !
    # Le système détecte automatiquement :
    # - FPS de la vidéo (ex: 25 FPS)
    # - Conversion : 15s × 25 FPS = 375 frames
    # - Avec FRAME_INTERVAL=2 : ~188 frames extraites
```

### 📊 Résultat affiché

```
📋 CONFIGURATION CENTRALISÉE:
   🌍 Environnement: 🖥️ Local
   🎬 Vidéo: match_football_10min
   ⏯️  Intervalle frames: 2
   🎯 Segmentation: ✅ Activée
   🎥 FPS vidéo: 25.0
   🕐 Offset avant: 15.0s (375 frames)
   🕐 Offset après: 15.0s (375 frames)
   🤖 Modèle SAM2: sam2.1_hiera_l
```

### 🎯 Avantages des offsets en secondes

| Méthode | Complexité | Exemple | Portabilité |
|---------|------------|---------|-------------|
| **Frames** | 🔴 Difficile | `OFFSET_BEFORE = 375` | ❌ Dépend du FPS |
| **Secondes** | 🟢 Simple | `OFFSET_BEFORE_SECONDS = 15.0` | ✅ Universal |

### 🔄 Flexibilité

```python
# Cas d'usage différents - même configuration !

# Vidéo lente (match analysé) - 10 FPS
# 15s × 10 FPS = 150 frames

# Vidéo normale (diffusion TV) - 25 FPS  
# 15s × 25 FPS = 375 frames

# Vidéo haute qualité (caméra sport) - 60 FPS
# 15s × 60 FPS = 900 frames

# ✅ Même valeur SEGMENT_OFFSET_BEFORE_SECONDS = 15.0
# ✅ Conversion automatique selon la vidéo
```

### 💡 Conseils pratiques

```python
# 🏃‍♂️ Actions rapides (sprint, but)
SEGMENT_OFFSET_BEFORE_SECONDS = 3.0
SEGMENT_OFFSET_AFTER_SECONDS = 3.0

# ⚽ Actions moyennes (passe, dribble)
SEGMENT_OFFSET_BEFORE_SECONDS = 8.0
SEGMENT_OFFSET_AFTER_SECONDS = 8.0

# 🎯 Séquences longues (construction de jeu)
SEGMENT_OFFSET_BEFORE_SECONDS = 20.0
SEGMENT_OFFSET_AFTER_SECONDS = 20.0

# 📊 Analyse complète (mi-temps)
SEGMENT_OFFSET_BEFORE_SECONDS = 300.0  # 5 minutes
SEGMENT_OFFSET_AFTER_SECONDS = 300.0   # 5 minutes
```

---

## 📚 Ressources

- [SAM2 Documentation](https://github.com/facebookresearch/sam2)
- [Notebook principal](SAM_inference_segment.ipynb)
- [Configuration exemple](../data/videos/example_config.json)

---

*Ce README couvre le fonctionnement complet du notebook SAM_inference_segment.ipynb avec la fonctionnalité de segmentation vidéo.* 