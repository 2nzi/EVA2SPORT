"""
Test de la pipeline complète EVA2SPORT
Tracking complet + Export + Visualisation
"""

import sys
from pathlib import Path

# Ajouter le module eva2sport au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eva2sport import EVA2SportPipeline


def test_full_pipeline():
    """Test de la pipeline complète avec tracking et export"""
    
    print("🚀 TEST PIPELINE COMPLÈTE EVA2SPORT")
    print("=" * 50)
    
    # Configuration
    video_name = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    try:
        # 1. Créer la pipeline
        print("1. 🏗️ Création de la pipeline...")
        pipeline = EVA2SportPipeline(
            video_name,
            segment_offset_before_seconds=2.0,
            segment_offset_after_seconds=2.0
        )
        print(f"   ✅ Pipeline créée pour: {video_name}")
        
        # 2. Exécution complète avec export vidéo
        print("\n2. 🚀 Exécution pipeline complète avec export vidéo...")
        print("   ⚡ Cela peut prendre plusieurs minutes...")

        results = pipeline.run_full_pipeline(
            force_extraction=True,
            export_video=True,
            video_params={
                'fps': 5,                      # FPS réduit pour test rapide
                'show_minimap': True,          # Inclure minimap
                'cleanup_frames': True,        # Nettoyer après
                'force_regenerate': True       # Utiliser frames existantes
            }
        )

        # Vérification additionnelle si la vidéo a été créée
        if results['status'] == 'success' and 'video' in results['export_paths']:
            video_path = results['export_paths']['video']
            if Path(video_path).exists():
                video_size = Path(video_path).stat().st_size / 1024**2
                print(f"   📊 Taille vidéo: {video_size:.1f}MB")
        
        # 3. Affichage des résultats
        print("\n3. 📊 RÉSULTATS FINAUX")
        print("-" * 30)
        
        if results['status'] == 'success':
            print(f"   ✅ Status: {results['status']}")
            print(f"   🎬 Vidéo: {results['video_name']}")
            print(f"   🖼️ Frames extraites: {results['frames_extracted']}")
            print(f"   🎯 Objets suivis: {results['objects_tracked']}")
            print(f"   📝 Annotations totales: {results['total_annotations']}")
            print(f"   🎬 Frames annotées: {results['frames_annotated']}")
            
            print(f"\n   📁 Fichiers générés:")
            for file_type, path in results['export_paths'].items():
                print(f"      📄 {file_type}: {path}")
            
            print(f"\n   ⚙️ Configuration:")
            print(f"      🔄 Intervalle: {results['config']['frame_interval']}")
            print(f"      🎯 Mode segmentation: {results['config']['segment_mode']}")
            print(f"      📁 Dossier sortie: {results['config']['output_dir']}")
            
        else:
            print(f"   ❌ Status: {results['status']}")
            print(f"   ❌ Erreur: {results['error']}")
            return False
        
        print("\n" + "=" * 50)
        print("✅ TEST PIPELINE COMPLÈTE RÉUSSI!")
        print("🎉 Tous les modules fonctionnent correctement")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR dans le test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_mode_pipeline():
    """Test de la pipeline complète en mode event"""
    
    print("🚀 TEST PIPELINE MODE EVENT")
    print("=" * 50)
    
    # Configuration
    video_name = "SD_13_06_2025_cam1"
    event_timestamp = 959.696

    
    try:
        # 1. Créer la pipeline en mode event
        print("1. 🏗️ Création de la pipeline en mode event...")
        pipeline = EVA2SportPipeline(
            video_name,
            event_timestamp_seconds=event_timestamp,
            segment_offset_before_seconds=3.0,
            segment_offset_after_seconds=3.0
        )
        print(f"   ✅ Pipeline créée pour event à {event_timestamp}s")
        
        # 2. Exécution complète avec export vidéo
        print("\n3. 🚀 Exécution pipeline complète mode event...")
        print("   ⚡ Cela peut prendre plusieurs minutes...")

        results = pipeline.run_full_pipeline(
            force_extraction=True,
            export_video=True,
            video_params={
                'fps': 5,                      # FPS réduit pour test rapide
                'show_minimap': True,          # Inclure minimap
                'cleanup_frames': True,        # Nettoyer après
                'force_regenerate': True      # Forcer la régénération
            }
        )

        # 4. Vérification des résultats
        print("\n4. 📊 RÉSULTATS MODE EVENT")
        print("-" * 30)
        
        if results['status'] == 'success':
            print(f"   ✅ Status: {results['status']}")
            print(f"   🎬 Vidéo: {results['video_name']}")
            print(f"   ⏰ Event timestamp: {event_timestamp}s")
            print(f"   📍 Event frame: {pipeline.config.event_frame}")
            print(f"   🖼️ Frames extraites: {results['frames_extracted']}")
            print(f"   🎯 Objets suivis: {results['objects_tracked']}")
            print(f"   📝 Annotations totales: {results['total_annotations']}")
            print(f"   🎬 Frames annotées: {results['frames_annotated']}")
            
            # Vérification spécifique au mode event
            if 'video' in results['export_paths']:
                video_path = results['export_paths']['video']
                if Path(video_path).exists():
                    video_size = Path(video_path).stat().st_size / 1024**2
                    print(f"   📊 Taille vidéo: {video_size:.1f}MB")
            
            print(f"\n   📁 Fichiers générés:")
            for file_type, path in results['export_paths'].items():
                print(f"      📄 {file_type}: {path}")
            
            print(f"\n   ⚙️ Configuration:")
            print(f"      🔄 Intervalle: {results['config']['frame_interval']}")
            print(f"      🎯 Mode event: {pipeline.config.is_event_mode}")
            print(f"      📁 Dossier sortie: {results['config']['output_dir']}")
            
        else:
            print(f"   ❌ Status: {results['status']}")
            print(f"   ❌ Erreur: {results['error']}")
            return False
        
        print("\n" + "=" * 50)
        print("✅ TEST PIPELINE MODE EVENT RÉUSSI!")
        print("🎉 Le mode event fonctionne correctement")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR dans le test mode event: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_mode_pipeline_multiple_events():
    """Test pipeline mode event pour plusieurs timestamps"""
    print("🚀 TEST PIPELINE MODE EVENT MULTI-EVENTS")
    print("=" * 50)

    video_name = "SD_13_06_2025_cam1"
    event_timestamps = [1029.001, 959.696]

    all_success = True

    for idx, event_timestamp in enumerate(event_timestamps):
        print(f"\n--- Événement {idx+1} à {event_timestamp}s ---")
        try:
            pipeline = EVA2SportPipeline(
                video_name,
                event_timestamp_seconds=event_timestamp,
                segment_offset_before_seconds=5.0,
                segment_offset_after_seconds=5.0
            )
            print(f"   ✅ Pipeline créée pour event à {event_timestamp}s")

            results = pipeline.run_full_pipeline(
                force_extraction=True,
                export_video=True,
                video_params={
                    'fps': 5,
                    'show_minimap': True,
                    'cleanup_frames': True,
                    'force_regenerate': True
                }
            )

            if results['status'] == 'success':
                print(f"   ✅ Event {idx+1} réussi")
            else:
                print(f"   ❌ Event {idx+1} échoué: {results['error']}")
                all_success = False

        except Exception as e:
            print(f"   ❌ Exception pour event {idx+1}: {e}")
            import traceback
            traceback.print_exc()
            all_success = False

    print("\n" + "=" * 50)
    if all_success:
        print("✅ TEST MULTI-EVENTS RÉUSSI!")
    else:
        print("❌ TEST MULTI-EVENTS AVEC ERREURS")
    return all_success
    

if __name__ == "__main__":
    print("🧪 TESTS EVA2SPORT PIPELINE")
    print("=" * 50)
    
    # Menu de choix
    print("Choisissez le test à exécuter:")
    print("1. Test pipeline mode segment (original)")
    print("2. Test pipeline mode event (nouveau)")
    print("3. Test pipeline mode event (plusieurs events)")
    print("4. Test gestionnaire d'événements multiples → voir test_multi_event_manager.py")
    print("5. Test événement unique avec gestionnaire")
    print("6. Exécuter les deux tests")
    
    choice = input("\nVotre choix (1, 2, 3, 4, 5 ou 6): ").strip()
    
    success = True
    
    if choice == "1":
        print("\n🎯 EXÉCUTION TEST MODE SEGMENT")
        success = test_full_pipeline()
    elif choice == "2":
        print("\n🎯 EXÉCUTION TEST MODE EVENT")
        success = test_event_mode_pipeline()
    elif choice == "3":
        print("\n🎯 EXÉCUTION TEST MODE EVENT")
        success = test_event_mode_pipeline_multiple_events()
    elif choice == "4":
        print("\n🎯 REDIRECTION VERS TEST SPÉCIALISÉ")
        print("   Pour tester le gestionnaire multi-événements, lancez:")
        print("   python tests/test_multi_event_manager.py")
        success = True
    elif choice == "5":
        print("\n🎯 EXÉCUTION TEST ÉVÉNEMENT UNIQUE AVEC GESTIONNAIRE")
        # This test is now handled by test_multi_event_manager.py
        print("   Pour tester l'événement unique, lancez:")
        print("   python tests/test_multi_event_manager.py --single-event <timestamp>")
        success = True
    elif choice == "6":
        print("\n🎯 EXÉCUTION DES DEUX TESTS")
        print("\n" + "=" * 60)
        print("TEST 1/2: MODE SEGMENT")
        print("=" * 60)
        success1 = test_full_pipeline()
        
        print("\n" + "=" * 60)
        print("TEST 2/2: MODE EVENT")
        print("=" * 60)
        success2 = test_event_mode_pipeline()
        
        success = success1 and success2
        
        print("\n" + "=" * 60)
        print("RÉSUMÉ DES TESTS")
        print("=" * 60)
        print(f"Mode segment: {'✅ RÉUSSI' if success1 else '❌ ÉCHOUÉ'}")
        print(f"Mode event: {'✅ RÉUSSI' if success2 else '❌ ÉCHOUÉ'}")
    else:
        print("❌ Choix invalide. Utilisation du test par défaut (mode segment)")
        success = test_full_pipeline()
    
    if success:
        print("\n🎯 TOUS LES TESTS RÉUSSIS!")
    else:
        print("\n❌ ÉCHEC DES TESTS")
        sys.exit(1)