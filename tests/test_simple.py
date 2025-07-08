"""
Script de test ultra-simple pour EVA2SPORT
"""

import sys
from pathlib import Path

# Ajouter eva2sport au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import eva2sport

def main():
    """Test rapide de la pipeline"""
    
    print("🚀 EVA2SPORT - Test Simple")
    print("=" * 40)
    
    # Votre vidéo de test
    video_name = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    try:
        # Option 1: Test ultra-simple (une ligne)
        print("\n📋 Option 1: Test ultra-simple")
        print("Code: eva2sport.track_video(video_name)")
        
        # Décommentez pour exécuter:
        # results = eva2sport.track_video(video_name)
        # print(f"✅ Terminé ! JSON: {results['export_paths']['json']}")
        
        # Option 2: Test étape par étape
        print("\n📋 Option 2: Test étape par étape")
        
        # Créer pipeline
        pipeline = eva2sport.create_pipeline(video_name)
        print(f"✅ Pipeline créée pour: {pipeline.config.VIDEO_NAME}")
        
        # Vérifier configuration
        pipeline.load_project_config()
        print(f"✅ Configuration chargée")
        
        # Vérifier frames
        frames_count = pipeline.extract_frames(force=False)
        print(f"✅ Frames disponibles: {frames_count}")
        
        print("\n🎉 Pipeline prête ! Utilisez:")
        print("   pipeline.run_full_pipeline()  # Pour exécution complète")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n🔍 Vérifications:")
        print("1. Les fichiers vidéo et config existent-ils ?")
        print("2. SAM2 est-il installé ?")
        print("3. Le checkpoint SAM2 est-il téléchargé ?")

if __name__ == "__main__":
    main()