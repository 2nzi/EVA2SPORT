#!/usr/bin/env python3
"""
Tests d'export vidéo avec différents paramètres de minimap
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).parent.parent))

from eva2sport.config import Config
from eva2sport.visualization import VideoExporter
from eva2sport.pipeline import EVA2SportPipeline

def get_video_fps(config: Config) -> int:
    """Calcule le FPS par défaut basé sur la vidéo ou retourne 10 FPS"""
    try:
        # Essayer de récupérer le FPS de la vidéo original et diviser par frame_interval
        if hasattr(config, 'FRAME_INTERVAL') and config.FRAME_INTERVAL > 0:
            # Supposons 25 FPS pour la vidéo originale (valeur typique)
            original_fps = 25
            calculated_fps = max(1, original_fps // config.FRAME_INTERVAL)
            print(f"📊 FPS calculé: {original_fps} / {config.FRAME_INTERVAL} = {calculated_fps}")
            return calculated_fps
        else:
            print(f"📊 FPS par défaut: 10")
            return 10
    except:
        print(f"📊 FPS par défaut: 10")
        return 10

def test_export_terrain_complet():
    """Test export avec terrain complet"""
    
    print("🎯 Test 1: Export avec terrain complet")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    pipeline = EVA2SportPipeline(VIDEO_NAME)
    config = pipeline.config
    
    # Vérifier les fichiers
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet manquant, skip test")
        return True
    
    try:
        fps = get_video_fps(config)
        
        video_path = pipeline.export_video(
            fps=fps,
            cleanup_frames=False,
            force_regenerate=True,
            minimap_config={
                'half_field': 'full',
                'rotation': 0,
                'transparency': 0.4,
                'position': 'upper right',
                'size': '50%'
            }
        )
        
        print(f"✅ Export terrain complet réussi: {video_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur export terrain complet: {e}")
        return False

def test_export_demi_terrain_gauche():
    """Test export avec preset tactical_analysis"""
    
    print("\n🎯 Test 2: Export avec preset tactical_analysis")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    pipeline = EVA2SportPipeline(VIDEO_NAME)
    config = pipeline.config
    
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet manquant, skip test")
        return True
    
    try:
        fps = get_video_fps(config)
        
        video_path = pipeline.export_video(
            fps=fps,
            preset='tactical_analysis',
            cleanup_frames=False,
            force_regenerate=True,
            minimap_config={
                'half_field': 'left',
                'transparency': 0.5
            }
        )
        
        print(f"✅ Export preset tactical_analysis réussi: {video_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur export preset tactical_analysis: {e}")
        return False

def test_export_demi_terrain_droit():
    """Test export avec preset fast_preview"""
    
    print("\n🎯 Test 3: Export avec preset fast_preview")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    pipeline = EVA2SportPipeline(VIDEO_NAME)
    config = pipeline.config
    
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet manquant, skip test")
        return True
    
    try:
        fps = get_video_fps(config)
        
        video_path = pipeline.export_video(
            fps=fps,
            preset='fast_preview',
            cleanup_frames=False,
            force_regenerate=True,
            minimap_config={
                'half_field': 'right',
                'transparency': 0.6
            }
        )
        
        print(f"✅ Export preset fast_preview réussi: {video_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur export preset fast_preview: {e}")
        return False

def test_export_style_broadcast():
    """Test export avec preset high_quality"""
    
    print("\n🎯 Test 4: Export avec preset high_quality")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    pipeline = EVA2SportPipeline(VIDEO_NAME)
    config = pipeline.config
    
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet manquant, skip test")
        return True
    
    try:
        fps = get_video_fps(config)
        
        video_path = pipeline.export_video(
            fps=fps,
            preset='high_quality',
            cleanup_frames=False,
            force_regenerate=True,
            minimap_config={
                'half_field': 'full',
                'transparency': 0.3
            }
        )
        
        print(f"✅ Export preset high_quality réussi: {video_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur export preset high_quality: {e}")
        return False

def test_export_avec_preset():
    """Test export avec preset default"""
    
    print("\n🎯 Test 5: Export avec preset default")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    pipeline = EVA2SportPipeline(VIDEO_NAME)
    config = pipeline.config
    
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet manquant, skip test")
        return True
    
    try:
        fps = get_video_fps(config)
        
        video_path = pipeline.export_video(
            fps=fps,
            cleanup_frames=False,
            force_regenerate=True,
            minimap_config={}
        )
        
        print(f"✅ Export preset default réussi: {video_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur export preset default: {e}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🧪 TESTS EXPORT VIDÉO - DIFFÉRENTS PARAMÈTRES MINIMAP")
    print("=" * 60)
    
    # Tests d'export avec différents paramètres
    tests = [
        # test_export_terrain_complet,
        # test_export_demi_terrain_gauche,
        # test_export_demi_terrain_droit,
        # test_export_style_broadcast,
        test_export_avec_preset
    ]
    
    # Exécuter les tests
    results = []
    for test_func in tests:
        try:
            success = test_func()
            results.append((test_func.__name__, success))
        except Exception as e:
            print(f"❌ Erreur dans {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES EXPORTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"   {test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TOUS LES EXPORTS RÉUSSIS!")
        print("📺 Vidéos générées avec différents paramètres de minimap")
        print("📁 Consultez le dossier de sortie pour voir les résultats")
    else:
        print("⚠️ CERTAINS EXPORTS ONT ÉCHOUÉ")
        print("🔍 Vérifiez les erreurs ci-dessus")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 