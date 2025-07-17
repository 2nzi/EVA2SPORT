#!/usr/bin/env python3
"""
Exemple d'utilisation du système de traitement de timestamps EVA2SPORT
Montre comment utiliser différentes sources de timestamps
"""

import sys
from pathlib import Path

# Ajouter le module eva2sport au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eva2sport.export.multi_event_manager import MultiEventManager
from eva2sport.utils import TimestampReader


def example_csv_processing():
    """Exemple de traitement depuis un fichier CSV"""
    print("🚀 EXEMPLE: TRAITEMENT DEPUIS UN FICHIER CSV")
    print("=" * 60)
    
    video_name = "SD_13_06_2025_cam1"
    csv_file = "Timeline_g_SD.csv"  # Nom du fichier dans data/videos/
    
    # Créer le gestionnaire
    manager = MultiEventManager(video_name)
    
    # Option 1: Utiliser la méthode de commodité
    print("\n📊 Option 1: Méthode de commodité")
    results = manager.process_events_from_csv(
        csv_file=csv_file,
        timestamp_column='Start time',
        filter_column='Row',
        filter_value='PdB',
        segment_offset_before_seconds=10.0,
        segment_offset_after_seconds=5.0,
        video_params={
            'fps': 5,
            'show_minimap': True,
            'cleanup_frames': True
        }
    )
    
    # Option 2: Utiliser la méthode générale
    # print("\n📊 Option 2: Méthode générale")
    # results = manager.process_multiple_events(
    #     csv_file=csv_file,
    #     csv_config={
    #         'timestamp_column': 'Start time',
    #         'filter_column': 'Row',
    #         'filter_value': 'PdB'
    #     },
    #     segment_offset_before_seconds=5.0,
    #     segment_offset_after_seconds=5.0,
    #     video_params={
    #         'fps': 5,
    #         'show_minimap': True,
    #         'cleanup_frames': True
    #     }
    # )
    
    print(f"\n✅ Résultats: {results['successful_events']}/{results['total_events']} événements traités")


def example_manual_processing():
    """Exemple de traitement depuis une liste manuelle"""
    print("\n🚀 EXEMPLE: TRAITEMENT DEPUIS UNE LISTE MANUELLE")
    print("=" * 60)
    
    video_name = "SD_13_06_2025_cam1"
    timestamps = [750.381, 959.696, 1029.001]
    
    # Créer le gestionnaire
    manager = MultiEventManager(video_name)
    
    # Traiter les événements
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
    
    print(f"\n✅ Résultats: {results['successful_events']}/{results['total_events']} événements traités")



if __name__ == "__main__":
    print("🧪 EXEMPLES D'UTILISATION - TRAITEMENT DE TIMESTAMPS EVA2SPORT")
    print("=" * 80)
    
    # Menu de choix
    print("\nChoisissez l'exemple à exécuter:")
    print("1. Traitement depuis un fichier CSV")
    print("2. Traitement depuis une liste manuelle")

    
    choice = input("\nVotre choix (1-2): ").strip()
    
    if choice == "1":
        example_csv_processing()
    elif choice == "2":
        example_manual_processing()

    else:
        print("❌ Choix invalide")
        sys.exit(1)
    
    print("\n�� Exemple terminé!") 