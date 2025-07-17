# Traitement de Timestamps EVA2SPORT

Ce document explique comment utiliser le système de traitement de timestamps d'EVA2SPORT pour traiter plusieurs événements depuis différentes sources.

## 🚀 Vue d'ensemble

Le système de traitement de timestamps permet de :
- ✅ Lire des timestamps depuis des fichiers CSV
- ✅ Lire des timestamps depuis des fichiers JSON
- ✅ Utiliser des listes manuelles de timestamps
- ✅ Valider les timestamps contre la durée de la vidéo
- ✅ Filtrer les données CSV selon des critères spécifiques
- ✅ Éviter la création de dossiers pour les événements sans annotations valides

## 📋 Classes principales

### `TimestampReader`
Classe utilitaire pour lire des timestamps depuis différentes sources.

### `MultiEventManager`
Gestionnaire principal qui intègre le `TimestampReader` et traite les événements.

## 🔧 Utilisation

### 1. Traitement depuis un fichier CSV

#### Méthode simple
```python
from eva2sport.export.multi_event_manager import MultiEventManager

manager = MultiEventManager("SD_13_06_2025_cam1")

# Traitement avec méthode de commodité
results = manager.process_events_from_csv(
    csv_file="Timeline_g_SD.csv",  # Nom du fichier dans data/videos/
    timestamp_column='Start time',
    filter_column='Row',
    filter_value='PdB',
    segment_offset_before_seconds=5.0,
    segment_offset_after_seconds=5.0,
    video_params={
        'fps': 5,
        'show_minimap': True,
        'cleanup_frames': True
    }
)
```

#### Méthode avancée
```python
# Traitement avec configuration personnalisée
results = manager.process_multiple_events(
    csv_file="Timeline_g_SD.csv",  # Nom du fichier dans data/videos/
    csv_config={
        'timestamp_column': 'Start time',
        'filter_column': 'Row',
        'filter_value': 'PdB'
    },
    validate_timestamps=True,
    segment_offset_before_seconds=5.0,
    segment_offset_after_seconds=5.0,
    video_params={
        'fps': 5,
        'show_minimap': True,
        'cleanup_frames': True
    }
)
```

### 2. Traitement depuis une liste manuelle

```python
timestamps = [750.381, 959.696, 1029.001]

results = manager.process_multiple_events(
    event_timestamps=timestamps,
    segment_offset_before_seconds=3.0,
    segment_offset_after_seconds=3.0,
    video_params={
        'fps': 5,
        'show_minimap': False,
        'cleanup_frames': True
    }
)
```

### 3. Traitement depuis un fichier JSON

```python
results = manager.process_multiple_events(
    json_file="events.json",  # Nom du fichier dans data/videos/
    segment_offset_before_seconds=3.0,
    segment_offset_after_seconds=3.0
)
```

### 4. Inspection d'un fichier CSV

```python
# Récupérer les informations sur un CSV
csv_info = manager.get_csv_info("Timeline_g_SD.csv")  # Nom du fichier dans data/videos/

print(f"Colonnes: {csv_info['columns']}")
print(f"Lignes: {csv_info['rows_count']}")
print(f"Échantillon: {csv_info['sample_data'][:3]}")
```

### 5. Utilisation directe du TimestampReader

```python
from eva2sport.utils import TimestampReader
from eva2sport.config import Config

# Créer une config pour la résolution des chemins
config = Config("SD_13_06_2025_cam1", create_directories=False)
reader = TimestampReader(config)

# Lire depuis un CSV
timestamps = reader.read_from_csv(
    csv_file="Timeline_g_SD.csv",  # Nom du fichier dans data/videos/
    timestamp_column='Start time',
    filter_column='Row',
    filter_value='PdB'
)

# Valider contre la vidéo
valid_timestamps = reader.validate_timestamps(timestamps, "SD_13_06_2025_cam1")
```

## 📁 Gestion des chemins de fichiers

Le système gère intelligemment les chemins de fichiers via la classe `Config` :

### Résolution automatique (via `Config.resolve_data_file_path()`)
- **Nom simple** (`"Timeline_g_SD.csv"`) → Cherche dans `data/videos/Timeline_g_SD.csv`
- **Chemin relatif** (`"./data/videos/Timeline_g_SD.csv"`) → Résout depuis le répertoire de travail
- **Chemin absolu** (`"/path/to/file.csv"`) → Utilise le chemin exact

### Centralisé dans la configuration
La résolution des chemins est centralisée dans la classe `Config` pour une cohérence avec le reste du système EVA2SPORT :

```python
from eva2sport.config import Config

config = Config("SD_13_06_2025_cam1")
csv_path = config.get_csv_path("Timeline_g_SD.csv")  # Méthode de commodité
json_path = config.get_json_path("events.json")     # Méthode de commodité
```

### Exemples
```python
# Ces trois appels sont équivalents si vous êtes dans le répertoire du projet
manager.process_events_from_csv("Timeline_g_SD.csv")
manager.process_events_from_csv("./data/videos/Timeline_g_SD.csv") 
manager.process_events_from_csv("/absolute/path/to/project/data/videos/Timeline_g_SD.csv")
```

## 📊 Format des fichiers

### CSV
Le fichier CSV doit contenir au minimum une colonne avec les timestamps en secondes :

```csv
Start time,Row,Description
750.381,PdB,Event 1
959.696,PdB,Event 2
1029.001,Action,Event 3
```

### JSON
Le fichier JSON peut avoir différents formats :

```json
{
  "timestamps": [750.381, 959.696, 1029.001],
  "metadata": {
    "video_name": "SD_13_06_2025_cam1",
    "total_events": 3
  }
}
```

## 🛠️ Configuration CSV

### Paramètres disponibles
- `timestamp_column` : Nom de la colonne contenant les timestamps (défaut: "Start time")
- `filter_column` : Colonne à utiliser pour filtrer (optionnel)
- `filter_value` : Valeur à rechercher pour filtrer (optionnel)

### Exemple de filtrage
```python
csv_config = {
    'timestamp_column': 'Start time',
    'filter_column': 'Row',
    'filter_value': 'PdB'  # Ne garder que les lignes où 'Row' contient 'PdB'
}
```

## ⚙️ Fonctionnalités avancées

### Validation des timestamps
Le système peut automatiquement valider les timestamps contre la durée de la vidéo :
```python
results = manager.process_multiple_events(
    csv_file="events.csv",
    validate_timestamps=True  # Vérifie que les timestamps sont dans la durée de la vidéo
)
```

### Gestion des erreurs
Le système gère automatiquement :
- ✅ Fichiers CSV/JSON manquants
- ✅ Colonnes manquantes
- ✅ Timestamps invalides
- ✅ Événements sans annotations valides

### Évitement des dossiers inutiles
Le système vérifie **avant** de créer des dossiers si des annotations valides existent dans l'intervalle de chaque événement. Si aucune annotation valide n'est trouvée, l'événement est ignoré et aucun dossier n'est créé.

## 🎯 Exemples pratiques

### Traitement d'un match complet
```python
# Traiter tous les événements d'un match depuis un CSV
manager = MultiEventManager("match_2025_01_15")
results = manager.process_events_from_csv(
    csv_file="match_events.csv",
    timestamp_column='Time',
    filter_column='Type',
    filter_value='Goal',
    segment_offset_before_seconds=10.0,
    segment_offset_after_seconds=10.0
)
```

### Traitement rapide pour tests
```python
# Traitement rapide de quelques événements
quick_events = [120.5, 245.8, 367.2]
results = manager.process_multiple_events(
    event_timestamps=quick_events,
    segment_offset_before_seconds=2.0,
    segment_offset_after_seconds=2.0,
    video_params={'fps': 10, 'show_minimap': False}
)
```

## 🔍 Déboggage

### Vérifier un CSV avant traitement
```python
# Inspecter le CSV
csv_info = manager.get_csv_info("events.csv")
print(f"Colonnes disponibles: {csv_info['columns']}")

# Tester la lecture
reader = TimestampReader()
timestamps = reader.read_from_csv("events.csv", timestamp_column='Time')
print(f"Timestamps lus: {len(timestamps)}")
```

### Logs détaillés
Le système affiche automatiquement des logs détaillés :
```
📊 Lecture des timestamps depuis: Timeline_g_SD.csv
   📁 Chemin: C:\Users\user\project\data\videos\Timeline_g_SD.csv
🔍 Filtrage 'Row' = 'PdB': 120 → 45 lignes
✅ 45 timestamps extraits
📊 Plage: 120.5s → 3456.8s
✅ Validation des timestamps contre la durée de la vidéo
✅ 43 timestamps valides
```

## 🚫 Limitations

- Les fichiers CSV doivent être encodés en UTF-8
- Les timestamps doivent être en secondes (float)
- Le filtrage CSV utilise une recherche par substring
- La validation de timestamps nécessite l'accès au fichier vidéo

## 📝 Migration depuis l'ancienne version

### Avant
```python
# Ancienne méthode
event_timestamps = extract_timestamps_from_csv("events.csv")
results = manager.process_multiple_events(event_timestamps)
```

### Après
```python
# Nouvelle méthode
results = manager.process_events_from_csv("events.csv")
```

La nouvelle interface est plus simple, plus robuste et offre plus de fonctionnalités tout en évitant la création de dossiers inutiles. 