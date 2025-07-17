# Tests EVA2SPORT

Ce dossier contient les tests pour la pipeline EVA2SPORT.

## 🧪 Tests disponibles

### 1. `test_full_pipeline.py`
**Test principal de la pipeline**
- Test mode segment (original)
- Test mode event (nouveau)
- Test mode event (plusieurs events)

```bash
python tests/test_full_pipeline.py
```

### 2. `test_multi_event_manager.py`
**Test spécialisé pour le gestionnaire multi-événements**
- Test complet du gestionnaire multi-événements
- Test workflow événement unique
- Test persistance de l'index
- Vérification de la structure des fichiers

```bash
python tests/test_multi_event_manager.py
```

### 3. `test_video_export.py`
**Test de l'export vidéo**
- Test de génération de vidéos annotées
- Test des paramètres d'export

```bash
python tests/test_video_export.py
```

## 📁 Structure de sortie multi-événements

Avec le gestionnaire multi-événements, la structure de sortie est organisée comme suit :

```
data/videos/outputs/
├── SD_13_06_2025_cam1_events_index.json          # Index global
├── SD_13_06_2025_cam1_event_959s/                # Événement 1
│   ├── SD_13_06_2025_cam1_event_959s_project.json
│   ├── frames/
│   ├── masks/
│   └── SD_13_06_2025_cam1_event_959s_annotated.mp4
├── SD_13_06_2025_cam1_event_1029s/               # Événement 2
│   ├── SD_13_06_2025_cam1_event_1029s_project.json
│   ├── frames/
│   ├── masks/
│   └── SD_13_06_2025_cam1_event_1029s_annotated.mp4
```

## 🚀 Utilisation recommandée

### Pour tester la pipeline de base :
```bash
python tests/test_full_pipeline.py
```

### Pour tester le système multi-événements :
```bash
python tests/test_multi_event_manager.py
```

### Pour tester l'export vidéo :
```bash
python tests/test_video_export.py
```

## 📊 Exemple d'utilisation programmatique

```python
from eva2sport.export.multi_event_manager import MultiEventManager

# Créer le gestionnaire
manager = MultiEventManager("SD_13_06_2025_cam1")

# Traiter plusieurs événements
results = manager.process_multiple_events(
    [959.696, 1029.001, 1150.5],
    segment_offset_before_seconds=5.0,
    segment_offset_after_seconds=5.0
)

# Afficher le résumé
manager.display_events_summary()

# Récupérer un événement spécifique
event = manager.get_event_by_id("event_959s")
```

## 🔧 Configuration

Les tests utilisent des paramètres par défaut optimisés pour la rapidité :
- `fps: 5` (au lieu de 25)
- `show_minimap: True`
- `cleanup_frames: True`
- `force_regenerate: True`

Pour des tests de production, ajustez ces paramètres selon vos besoins. 