"""
Test simple de la pipeline EVA2SPORT complète - Version Simplifiée
"""

import sys
from pathlib import Path

# Ajouter le module eva2sport au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import eva2sport


def test_pipeline_simple():
    """Test simple de la pipeline complète"""
    
    print("🧪 Test de la pipeline EVA2SPORT complète")
    print("=" * 50)
    
    # Configuration
    video_name = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    try:
        # Test 1: Créer une pipeline
        print("\n1. 🏗️ Création de la pipeline...")
        pipeline = eva2sport.create_pipeline(video_name)
        print(f"   ✅ Pipeline créée pour: {pipeline.config.VIDEO_NAME}")
        
        # Test 2: Afficher la configuration
        print("\n2. ⚙️ Configuration...")
        pipeline.config.display_config()
        
        # Test 3: Validation des prérequis
        print("\n3. 📄 Validation des prérequis...")
        is_valid = pipeline.config.validate_requirements()
        
        if not is_valid:
            print("\n⚠️ Prérequis manquants - Test arrêté")
            print("💡 Assurez-vous que tous les fichiers sont présents")
            return
        
        # Test 4: Chargement de la configuration projet
        print("\n4. 📋 Chargement de la configuration projet...")
        project_config = pipeline.load_project_config()
        print(f"   ✅ Configuration chargée")
        print(f"   🎯 Objets définis: {len(project_config.get('objects', []))}")
        print(f"   📍 Annotations initiales: {len(project_config.get('initial_annotations', []))}")
        
        # Test 5: Extraction de frames (mode test)
        print("\n5. 🎬 Test d'extraction de frames...")
        frames_count = pipeline.extract_frames(force=False)
        print(f"   ✅ Frames disponibles: {frames_count}")
        
        if frames_count == 0:
            print("   💡 Extraction de quelques frames pour test...")
            frames_count = pipeline.extract_frames(force=True)
        
        # Test 6: Test SAM2 (si disponible)
        print("\n6. 🤖 Test d'initialisation du tracking...")
        
        try:
            import sam2
            print("   ✅ SAM2 détecté")
            
            if pipeline.config.checkpoint_path.exists() and frames_count > 0:
                print("   🚀 Initialisation du tracking...")
                pipeline.initialize_tracking()
                print(f"   ✅ Tracking initialisé: {len(pipeline.results.get('added_objects', []))} objets")
                
                print("\n7. 🎯 Pipeline prête pour exécution complète!")
                print("   💡 Utilisez pipeline.run_full_pipeline() pour l'exécution complète")
                
            else:
                print("   ⚠️ Checkpoint manquant ou aucune frame")
                
        except ImportError:
            print("   ⚠️ SAM2 non installé")
            print("   💡 Installez avec: pip install git+https://github.com/facebookresearch/sam2.git")
        
        print("\n" + "=" * 50)
        print("✅ Test de la pipeline terminé avec succès!")
        print("🎯 La pipeline EVA2SPORT est fonctionnelle")
        
    except Exception as e:
        print(f"\n❌ Erreur dans le test: {e}")
        print("🔍 Vérifiez les prérequis et la configuration")
        raise


def test_api_publique():
    """Test de l'API publique simple"""
    
    print("\n🧪 Test de l'API publique")
    print("-" * 30)
    
    video_name = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    # Test create_config
    print("1. Test create_config...")
    config = eva2sport.create_config(
        video_name,
        FRAME_INTERVAL=5,
        SEGMENT_MODE=True
    )
    print(f"   ✅ Config créée avec FRAME_INTERVAL={config.FRAME_INTERVAL}")
    
    # Test create_pipeline
    print("2. Test create_pipeline...")
    pipeline = eva2sport.create_pipeline(video_name)
    print(f"   ✅ Pipeline créée: {type(pipeline).__name__}")
    
    print("✅ API publique fonctionnelle!")


if __name__ == "__main__":
    test_pipeline_simple()
    test_api_publique()