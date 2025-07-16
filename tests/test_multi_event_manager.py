"""
Test du gestionnaire d'événements multiples EVA2SPORT
Structure de fichiers séparés + Index global
"""

import sys
import json
from pathlib import Path

# Ajouter le module eva2sport au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eva2sport.export.multi_event_manager import MultiEventManager


def test_multi_event_manager_complete():
    """Test complet du gestionnaire d'événements multiples"""
    print("🚀 TEST COMPLET GESTIONNAIRE MULTI-ÉVÉNEMENTS")
    print("=" * 70)
    
    video_name = "SD_13_06_2025_cam1"
    event_timestamps = [750.381,959.696, 1029.001]  # Réduire pour test plus rapide
    
    try:
        # 1. Créer le gestionnaire
        print("1. 🏗️ Création du gestionnaire...")
        manager = MultiEventManager(video_name)
        print(f"   ✅ Gestionnaire créé pour: {video_name}")
        print(f"   📄 Index global: {manager.index_file}")
        
        # 2. Traiter tous les événements
        print("\n2. 🚀 Traitement des événements multiples...")
        results = manager.process_multiple_events(
            event_timestamps,
            segment_offset_before_seconds=5.0,
            segment_offset_after_seconds=5.0,
            video_params={
                'fps': 5,
                'show_minimap': True,
                'cleanup_frames': True,
                'force_regenerate': True
            }
        )
        
        # 3. Vérifier les résultats
        print("\n3. ✅ VÉRIFICATION DES RÉSULTATS")
        print("-" * 50)
        
        success = True
        
        # Vérifier les résultats globaux
        if results['total_events'] != len(event_timestamps):
            print(f"   ❌ Nombre d'événements incorrect: {results['total_events']} != {len(event_timestamps)}")
            success = False
        else:
            print(f"   ✅ Nombre d'événements correct: {results['total_events']}")
        
        print(f"   📊 Événements réussis: {results['successful_events']}")
        print(f"   📊 Événements échoués: {results['failed_events']}")
        
        # 4. Vérifier l'index global
        print("\n4. 📋 VÉRIFICATION DE L'INDEX GLOBAL")
        print("-" * 50)
        
        if not manager.index_file.exists():
            print("   ❌ Fichier d'index global manquant")
            success = False
        else:
            print("   ✅ Fichier d'index global créé")
            
            # Vérifier le contenu de l'index
            with open(manager.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            print(f"   📊 Événements dans l'index: {len(index_data['events'])}")
            print(f"   📊 Total déclaré: {index_data['total_events']}")
            
            if len(index_data['events']) != results['successful_events']:
                print(f"   ❌ Incohérence dans l'index")
                success = False
            else:
                print(f"   ✅ Index cohérent")
        
        # 5. Vérifier la structure des fichiers
        print("\n5. 📁 VÉRIFICATION DE LA STRUCTURE DES FICHIERS")
        print("-" * 50)
        
        events_list = manager.get_events_list()
        for event in events_list:
            event_id = event['event_id']
            print(f"\n   📂 Événement: {event_id}")
            
            # Vérifier le dossier de l'événement
            event_dir = manager.video_output_dir / event_id
            if not event_dir.exists():
                print(f"      ❌ Dossier manquant: {event_dir}")
                success = False
                continue
            else:
                print(f"      ✅ Dossier créé: {event_dir}")
            
            # Vérifier le fichier JSON
            json_path = manager.video_output_dir / event['project_file']
            if not json_path.exists():
                print(f"      ❌ Fichier JSON manquant: {json_path}")
                success = False
            else:
                json_size = json_path.stat().st_size / 1024
                print(f"      ✅ Fichier JSON: {json_size:.1f}KB")
            
            # Vérifier le fichier vidéo
            if event['video_file']:
                video_path = manager.video_output_dir / event['video_file']
                if not video_path.exists():
                    print(f"      ❌ Fichier vidéo manquant: {video_path}")
                    success = False
                else:
                    video_size = video_path.stat().st_size / 1024**2
                    print(f"      ✅ Fichier vidéo: {video_size:.1f}MB")
            
            # Vérifier les sous-dossiers
            frames_dir = event_dir / "frames"
            masks_dir = event_dir / "masks"
            
            if frames_dir.exists():
                frames_count = len(list(frames_dir.glob("*.jpg")))
                print(f"      📁 Frames: {frames_count} fichiers")
            else:
                print(f"      ❌ Dossier frames manquant")
                success = False
            
            if masks_dir.exists():
                masks_count = len(list(masks_dir.glob("*.png")))
                print(f"      📁 Masks: {masks_count} fichiers")
            else:
                print(f"      ⚠️ Dossier masks manquant (normal si pas de masks)")
        
        # 6. Test de récupération d'événements
        print("\n6. 🔍 TEST DE RÉCUPÉRATION D'ÉVÉNEMENTS")
        print("-" * 50)
        
        # Test get_event_by_id
        first_event_id = f"event_{int(event_timestamps[0])}s"
        retrieved_event = manager.get_event_by_id(first_event_id)
        
        if retrieved_event:
            print(f"   ✅ Événement récupéré: {retrieved_event['event_id']}")
            print(f"      ⏰ Timestamp: {retrieved_event['timestamp_seconds']}s")
            print(f"      🎯 Objets: {retrieved_event['objects_count']}")
            print(f"      📝 Annotations: {retrieved_event['annotations_count']}")
        else:
            print(f"   ❌ Impossible de récupérer l'événement: {first_event_id}")
            success = False
        
        # Test get_events_list
        all_events = manager.get_events_list()
        if len(all_events) == results['successful_events']:
            print(f"   ✅ Liste complète récupérée: {len(all_events)} événements")
        else:
            print(f"   ❌ Liste incomplète: {len(all_events)} != {results['successful_events']}")
            success = False
        
        # 7. Affichage du résumé final
        print("\n7. 📊 RÉSUMÉ FINAL")
        print("-" * 50)
        manager.display_events_summary()
        
        # 8. Résultat final
        print(f"\n{'='*70}")
        if success and results['failed_events'] == 0:
            print("✅ TEST GESTIONNAIRE MULTI-ÉVÉNEMENTS RÉUSSI!")
            print("🎉 Structure multi-événements entièrement fonctionnelle")
            print(f"📄 Index global: {manager.index_file}")
            print(f"📁 Événements traités: {results['successful_events']}/{results['total_events']}")
        else:
            print("❌ TEST GESTIONNAIRE MULTI-ÉVÉNEMENTS AVEC ERREURS")
            if results['failed_events'] > 0:
                print(f"   {results['failed_events']} événement(s) ont échoué")
            if not success:
                print("   Problèmes de structure de fichiers détectés")
        
        return success and results['failed_events'] == 0
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE dans le test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_event_workflow():
    """Test du workflow d'un événement unique"""
    print("🚀 TEST WORKFLOW ÉVÉNEMENT UNIQUE")
    print("=" * 60)
    
    video_name = "SD_13_06_2025_cam1"
    event_timestamp = 959.696
    
    try:
        # 1. Créer le gestionnaire
        print("1. 🏗️ Création du gestionnaire...")
        manager = MultiEventManager(video_name)
        
        # 2. Traiter un événement unique
        print(f"\n2. 🎯 Traitement de l'événement: {event_timestamp}s")
        event_result = manager.add_event(
            event_timestamp,
            segment_offset_before_seconds=3.0,
            segment_offset_after_seconds=3.0,
            video_params={
                'fps': 5,
                'show_minimap': True,
                'cleanup_frames': True,
                'force_regenerate': True
            }
        )
        
        # 3. Vérifier le résultat
        print("\n3. ✅ VÉRIFICATION DU RÉSULTAT")
        print("-" * 40)
        
        if not event_result:
            print("   ❌ Événement non traité")
            return False
        
        print(f"   ✅ Événement traité: {event_result['event_id']}")
        print(f"   ⏰ Timestamp: {event_result['timestamp_seconds']}s")
        print(f"   📍 Frame annotation: {event_result['annotation_frame']}")
        print(f"   🎯 Objets suivis: {event_result['objects_count']}")
        print(f"   📝 Annotations: {event_result['annotations_count']}")
        print(f"   📄 Fichier JSON: {event_result['project_file']}")
        print(f"   🎬 Fichier vidéo: {event_result['video_file']}")
        
        # 4. Test de récupération
        print("\n4. 🔍 TEST DE RÉCUPÉRATION")
        print("-" * 40)
        
        retrieved = manager.get_event_by_id(event_result['event_id'])
        if retrieved and retrieved['event_id'] == event_result['event_id']:
            print(f"   ✅ Événement récupéré avec succès")
        else:
            print(f"   ❌ Problème de récupération")
            return False
        
        # 5. Affichage du résumé
        print("\n5. 📊 RÉSUMÉ")
        print("-" * 40)
        manager.display_events_summary()
        
        print(f"\n{'='*60}")
        print("✅ TEST ÉVÉNEMENT UNIQUE RÉUSSI!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_index_persistence():
    """Test de la persistance de l'index"""
    print("🚀 TEST PERSISTANCE DE L'INDEX")
    print("=" * 60)
    
    video_name = "SD_13_06_2025_cam1"
    
    try:
        # 1. Créer le gestionnaire et ajouter un événement
        print("1. 🏗️ Création et ajout d'un événement...")
        manager1 = MultiEventManager(video_name)
        initial_count = len(manager1.get_events_list())
        
        event_result = manager1.add_event(
            999.0,  # Timestamp unique pour ce test
            segment_offset_before_seconds=2.0,
            segment_offset_after_seconds=2.0,
            video_params={'fps': 5, 'show_minimap': False}
        )
        
        if not event_result:
            print("   ❌ Échec de l'ajout d'événement")
            return False
        
        new_count = len(manager1.get_events_list())
        print(f"   ✅ Événement ajouté: {initial_count} → {new_count}")
        
        # 2. Créer un nouveau gestionnaire et vérifier la persistance
        print("\n2. 🔄 Test de persistance...")
        manager2 = MultiEventManager(video_name)
        loaded_count = len(manager2.get_events_list())
        
        if loaded_count == new_count:
            print(f"   ✅ Index persisté correctement: {loaded_count} événements")
        else:
            print(f"   ❌ Problème de persistance: {loaded_count} != {new_count}")
            return False
        
        # 3. Vérifier que l'événement est bien là
        test_event = manager2.get_event_by_id("event_999s")
        if test_event:
            print(f"   ✅ Événement test récupéré: {test_event['event_id']}")
        else:
            print(f"   ❌ Événement test non trouvé")
            return False
        
        print(f"\n{'='*60}")
        print("✅ TEST PERSISTANCE RÉUSSI!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 TESTS GESTIONNAIRE MULTI-ÉVÉNEMENTS EVA2SPORT")
    print("=" * 70)
    
    # Menu de choix
    print("Choisissez le test à exécuter:")
    print("1. Test complet du gestionnaire multi-événements")
    print("2. Test workflow événement unique")
    print("3. Test persistance de l'index")
    print("4. Exécuter tous les tests")
    
    choice = input("\nVotre choix (1, 2, 3 ou 4): ").strip()
    
    success = True
    
    if choice == "1":
        print("\n🎯 EXÉCUTION TEST COMPLET")
        success = test_multi_event_manager_complete()
    elif choice == "2":
        print("\n🎯 EXÉCUTION TEST ÉVÉNEMENT UNIQUE")
        success = test_single_event_workflow()
    elif choice == "3":
        print("\n🎯 EXÉCUTION TEST PERSISTANCE")
        success = test_index_persistence()
    elif choice == "4":
        print("\n🎯 EXÉCUTION DE TOUS LES TESTS")
        print("\n" + "=" * 70)
        print("TEST 1/3: GESTIONNAIRE COMPLET")
        print("=" * 70)
        success1 = test_multi_event_manager_complete()
        
        print("\n" + "=" * 70)
        print("TEST 2/3: ÉVÉNEMENT UNIQUE")
        print("=" * 70)
        success2 = test_single_event_workflow()
        
        print("\n" + "=" * 70)
        print("TEST 3/3: PERSISTANCE")
        print("=" * 70)
        success3 = test_index_persistence()
        
        success = success1 and success2 and success3
        
        print("\n" + "=" * 70)
        print("RÉSUMÉ DES TESTS")
        print("=" * 70)
        print(f"Gestionnaire complet: {'✅ RÉUSSI' if success1 else '❌ ÉCHOUÉ'}")
        print(f"Événement unique: {'✅ RÉUSSI' if success2 else '❌ ÉCHOUÉ'}")
        print(f"Persistance: {'✅ RÉUSSI' if success3 else '❌ ÉCHOUÉ'}")
    else:
        print("❌ Choix invalide. Utilisation du test complet par défaut")
        success = test_multi_event_manager_complete()
    
    if success:
        print("\n🎯 TOUS LES TESTS RÉUSSIS!")
    else:
        print("\n❌ ÉCHEC DES TESTS")
        sys.exit(1) 