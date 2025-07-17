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
        segment_offset_before_seconds=5.0,
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


def example_csv_inspection():
    """Exemple d'inspection d'un fichier CSV"""
    print("\n🚀 EXEMPLE: INSPECTION D'UN FICHIER CSV")
    print("=" * 60)
    
    video_name = "SD_13_06_2025_cam1"
    csv_file = "Timeline_g_SD.csv"  # Nom du fichier dans data/videos/
    
    # Créer le gestionnaire
    manager = MultiEventManager(video_name)
    
    try:
        # Récupérer les informations sur le CSV
        csv_info = manager.get_csv_info(csv_file)
        
        print(f"📄 Fichier: {csv_info['file_path']}")
        print(f"📊 Nombre de lignes: {csv_info['rows_count']}")
        print(f"📋 Colonnes disponibles: {csv_info['columns']}")
        
        if csv_info['sample_data']:
            print("\n🔍 Échantillon de données:")
            for i, row in enumerate(csv_info['sample_data'][:3]):
                print(f"   Ligne {i+1}: {row}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


def example_timestamp_reader():
    """Exemple d'utilisation directe du TimestampReader"""
    print("\n🚀 EXEMPLE: UTILISATION DIRECTE DU TIMESTAMPREADER")
    print("=" * 60)
    
    csv_file = "Timeline_g_SD.csv"  # Nom du fichier dans data/videos/
    
    # Créer le lecteur avec une config
    from eva2sport.config import Config
    config = Config("SD_13_06_2025_cam1", create_directories=False)
    reader = TimestampReader(config)
    
    try:
        # Lire depuis le CSV
        timestamps = reader.read_from_csv(
            csv_file=csv_file,
            timestamp_column='Start time',
            filter_column='Row',
            filter_value='PdB'
        )
        
        print(f"📊 {len(timestamps)} timestamps lus")
        if timestamps:
            print(f"📊 Premier: {timestamps[0]:.1f}s")
            print(f"📊 Dernier: {timestamps[-1]:.1f}s")
        
        # Valider contre la vidéo
        video_name = "SD_13_06_2025_cam1"
        valid_timestamps = reader.validate_timestamps(timestamps, video_name)
        
        print(f"✅ {len(valid_timestamps)} timestamps valides")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


def example_create_sample_csv():
    """Exemple de création d'un CSV d'exemple"""
    print("\n🚀 EXEMPLE: CRÉATION D'UN CSV D'EXEMPLE")
    print("=" * 60)
    
    sample_timestamps = [120.5, 245.8, 367.2, 489.6, 612.1]
    additional_columns = {
        'Row': ['PdB', 'PdB', 'Action', 'PdB', 'Action'],
        'Description': ['Event 1', 'Event 2', 'Event 3', 'Event 4', 'Event 5']
    }
    
    output_path = "sample_timeline.csv"  # Sera créé dans data/videos/
    
    TimestampReader.create_sample_csv(
        output_path=output_path,
        sample_timestamps=sample_timestamps,
        additional_columns=additional_columns
    )
    
    print(f"✅ CSV d'exemple créé: {output_path}")


if __name__ == "__main__":
    print("🧪 EXEMPLES D'UTILISATION - TRAITEMENT DE TIMESTAMPS EVA2SPORT")
    print("=" * 80)
    
    # Menu de choix
    print("\nChoisissez l'exemple à exécuter:")
    print("1. Traitement depuis un fichier CSV")
    print("2. Traitement depuis une liste manuelle")
    print("3. Inspection d'un fichier CSV")
    print("4. Utilisation directe du TimestampReader")
    print("5. Création d'un CSV d'exemple")
    print("6. Exécuter tous les exemples")
    
    choice = input("\nVotre choix (1-6): ").strip()
    
    if choice == "1":
        example_csv_processing()
    elif choice == "2":
        example_manual_processing()
    elif choice == "3":
        example_csv_inspection()
    elif choice == "4":
        example_timestamp_reader()
    elif choice == "5":
        example_create_sample_csv()
    elif choice == "6":
        example_csv_inspection()
        example_timestamp_reader()
        example_create_sample_csv()
        example_manual_processing()
        example_csv_processing()
    else:
        print("❌ Choix invalide")
        sys.exit(1)
    
    print("\n�� Exemple terminé!") 