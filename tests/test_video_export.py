#!/usr/bin/env python3
"""
Script de test pour l'export vidéo corrigé avec configuration minimap
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).parent.parent))

from eva2sport.config import Config
from eva2sport.export.video_exporter import VideoExporter
from eva2sport.pipeline import EVA2SportPipeline

def test_video_export_basic():
    """Test de base de l'export vidéo"""
    
    # Configuration pour la vidéo de test
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    # Initialiser la configuration
    config = Config(VIDEO_NAME)
    
    # Vérifier que les fichiers nécessaires existent
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet non trouvé: {config.output_json_path}")
        print("💡 Assurez-vous d'avoir exécuté le pipeline d'inference d'abord")
        return False
    
    if not config.frames_dir.exists():
        print(f"❌ Dossier frames non trouvé: {config.frames_dir}")
        return False
    
    print(f"✅ Configuration validée")
    print(f"📁 Projet: {config.output_json_path}")
    print(f"🖼️ Frames: {config.frames_dir}")
    
    # Créer l'exporteur vidéo
    exporter = VideoExporter(config)
    
    # Obtenir les statistiques
    stats = exporter.get_export_stats()
    if stats:
        print(f"\n📊 STATISTIQUES:")
        print(f"   🎬 Frames: {stats['total_frames']}")
        print(f"   🎯 Annotations: {stats['total_objects']}")
        print(f"   📊 Moyenne/frame: {stats['avg_objects_per_frame']:.1f}")
        print(f"   🆔 Objets configurés: {stats['objects_config']}")
    
    return True, config, exporter




def test_pipeline_with_minimap():
    """Test du pipeline complet avec configuration minimap"""
    
    print("\n🚀 Test pipeline complet avec minimap")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    # Initialiser la pipeline
    pipeline = EVA2SportPipeline(VIDEO_NAME)
    
    # Vérifier si les fichiers nécessaires existent
    if not pipeline.config.config_path.exists():
        print(f"❌ Fichier config non trouvé: {pipeline.config.config_path}")
        print("💡 Assurez-vous d'avoir exécuté le pipeline d'inference d'abord")
        return False
    
    if not pipeline.config.output_json_path.exists():
        print(f"❌ Fichier projet non trouvé: {pipeline.config.output_json_path}")
        print("💡 Assurez-vous d'avoir exécuté le pipeline d'inference d'abord")
        return False
    
    try:
        # Test d'export vidéo avec minimap personnalisée via pipeline
        print("🎯 Export vidéo avec minimap personnalisée via pipeline...")
        
        video_path = pipeline.export_video(
            fps=3,
            show_minimap=True,
            cleanup_frames=False,
            force_regenerate=True,
            # minimap_config={
            #     'rotation': 180,
            #     'half_field': 'left',
            #     'transparency': 0.6,
            #     'position': 'lower left',
            #     'size': '35%'
            # }
        )
        
        print(f"✅ Pipeline export réussi: {video_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur pipeline: {e}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🧪 Tests complets de l'export vidéo EVA2SPORT")
    print("=" * 60)
    
    results = []

    print("\n" + "="*60)
    try:
        success = test_pipeline_with_minimap()
        results.append(("Pipeline avec minimap", success))
    except Exception as e:
        print(f"❌ Erreur test pipeline: {e}")
        results.append(("Pipeline avec minimap", False))
    
    # Résumé des résultats
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"   {test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ L'export vidéo avec minimap personnalisable fonctionne parfaitement.")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔍 Vérifiez les logs d'erreur ci-dessus.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 