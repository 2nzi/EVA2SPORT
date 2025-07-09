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
            segment_offset_before_seconds=5.0,
            segment_offset_after_seconds=5.0
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


if __name__ == "__main__":
    print("🧪 TESTS EVA2SPORT PIPELINE")
    print("=" * 50)
    
    # Test pipeline complète
    success = test_full_pipeline()
    
    if success:
        print("\n🎯 TOUS LES TESTS RÉUSSIS!")
    else:
        print("\n❌ ÉCHEC DES TESTS")
        sys.exit(1)