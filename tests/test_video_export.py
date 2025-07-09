#!/usr/bin/env python3
"""
Tests complets pour l'export vidéo avec la nouvelle architecture modulaire
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).parent.parent))

from eva2sport.config import Config
from eva2sport.visualization import VideoExporter, VisualizationConfig, MinimapConfig
from eva2sport.pipeline import EVA2SportPipeline

def test_new_architecture_basic():
    """Test de base avec la nouvelle architecture"""
    
    print("🎯 Test 1: Nouvelle architecture - utilisation de base")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    # Vérifications de base
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet non trouvé: {config.output_json_path}")
        return False
    
    # Créer l'exporteur avec la nouvelle architecture
    exporter = VideoExporter(config)
    
    # Obtenir les statistiques
    stats = exporter.get_export_stats()
    if stats:
        print(f"📊 STATISTIQUES:")
        print(f"   🎬 Frames: {stats['total_frames']}")
        print(f"   🎯 Annotations: {stats['total_objects']}")
        print(f"   📊 Moyenne/frame: {stats['avg_objects_per_frame']:.1f}")
        print(f"   🆔 Objets configurés: {stats['objects_config']}")
    
    print(f"✅ Test architecture de base réussi")
    return True, config, exporter

def test_configuration_presets():
    """Test des presets de configuration"""
    
    print("\n🎯 Test 2: Presets de configuration")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet non trouvé: {config.output_json_path}")
        return False
    
    # Tester différents presets
    presets = ['default', 'high_quality', 'fast_preview', 'tactical_analysis']
    
    for preset in presets:
        print(f"\n📋 Test preset: {preset}")
        
        try:
            exporter = VideoExporter.create_with_preset(config, preset)
            current_config = exporter.get_current_config()
            
            print(f"   ⚙️ FPS: {current_config['fps']}")
            print(f"   📐 Taille: {current_config['figsize']}")
            print(f"   🔄 Rotation minimap: {current_config['minimap_config']['rotation']}")
            print(f"   📍 Position: {current_config['minimap_config']['position']}")
            print(f"   ✅ Preset {preset} configuré avec succès")
            
        except Exception as e:
            print(f"   ❌ Erreur avec preset {preset}: {e}")
            return False
    
    print(f"✅ Tous les presets testés avec succès")
    return True

def test_minimap_configurations():
    """Test des configurations minimap avancées"""
    
    print("\n🎯 Test 3: Configurations minimap avancées")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet non trouvé: {config.output_json_path}")
        return False
    
    # Test des configurations minimap avec validation
    test_configs = [
        {
            'name': 'Vue tactique',
            'config': {
                'rotation': 90,
                'half_field': 'left',
                'invert_y': True,
                'transparency': 0.5,
                'position': 'upper left',
                'size': "35%"
            }
        },
        {
            'name': 'Vue complète',
            'config': {
                'rotation': 0,
                'half_field': 'full',
                'transparency': 0.4,
                'position': 'upper right',
                'size': "45%"
            }
        },
        {
            'name': 'Vue broadcast',
            'config': {
                'rotation': 180,
                'half_field': 'right',
                'transparency': 0.7,
                'position': 'lower center',
                'size': "30%"
            }
        }
    ]
    
    for test_data in test_configs:
        print(f"\n📺 Test configuration: {test_data['name']}")
        
        try:
            # Test avec classe MinimapConfig
            minimap_config = MinimapConfig(**test_data['config'])
            
            # Test avec l'exporteur
            exporter = VideoExporter(config)
            exporter.configure_minimap(**minimap_config.to_dict())
            
            current_config = exporter.get_current_config()
            print(f"   🔄 Rotation: {current_config['minimap_config']['rotation']}")
            print(f"   📍 Position: {current_config['minimap_config']['position']}")
            print(f"   💧 Transparence: {current_config['minimap_config']['transparency']}")
            print(f"   ✅ Configuration {test_data['name']} appliquée avec succès")
            
        except Exception as e:
            print(f"   ❌ Erreur configuration {test_data['name']}: {e}")
            return False
    
    print(f"✅ Toutes les configurations minimap testées avec succès")
    return True

def test_validation_and_errors():
    """Test de la validation et gestion d'erreurs"""
    
    print("\n🎯 Test 4: Validation et gestion d'erreurs")
    print("=" * 50)
    
    # Test des valeurs invalides
    test_cases = [
        {
            'name': 'Rotation invalide',
            'config': {'rotation': 45},  # Doit être 0, 90, 180, 270
            'should_fail': True
        },
        {
            'name': 'Transparence invalide',
            'config': {'transparency': 1.5},  # Doit être 0.0-1.0
            'should_fail': True
        },
        {
            'name': 'Taille invalide',
            'config': {'size': '150%'},  # Doit être 10%-80%
            'should_fail': True
        },
        {
            'name': 'half_field invalide',
            'config': {'half_field': 'center'},  # Doit être 'left', 'right', 'full'
            'should_fail': True
        },
        {
            'name': 'Configuration valide',
            'config': {'rotation': 90, 'transparency': 0.5, 'size': '35%', 'half_field': 'full'},
            'should_fail': False
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Test: {test_case['name']}")
        
        try:
            minimap_config = MinimapConfig(**test_case['config'])
            
            if test_case['should_fail']:
                print(f"   ❌ ERREUR: Validation devrait échouer pour {test_case['name']}")
                return False
            else:
                print(f"   ✅ Configuration valide acceptée")
                
        except ValueError as e:
            if test_case['should_fail']:
                print(f"   ✅ Validation échouée comme attendu: {e}")
            else:
                print(f"   ❌ ERREUR: Validation ne devrait pas échouer: {e}")
                return False
        except Exception as e:
            print(f"   ❌ ERREUR inattendue: {e}")
            return False
    
    # Test preset invalide
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    try:
        exporter = VideoExporter.create_with_preset(config, 'invalid_preset')
        print(f"   ❌ ERREUR: Preset invalide devrait échouer")
        return False
    except ValueError:
        print(f"   ✅ Preset invalide rejeté comme attendu")
    
    print(f"✅ Tous les tests de validation réussis")
    return True

def test_pipeline_with_new_architecture():
    """Test du pipeline avec la nouvelle architecture"""
    
    print("\n🎯 Test 5: Pipeline avec nouvelle architecture")
    print("=" * 50)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    # Initialiser la pipeline
    pipeline = EVA2SportPipeline(VIDEO_NAME)
    
    # Vérifier les fichiers nécessaires
    if not pipeline.config.config_path.exists():
        print(f"❌ Fichier config non trouvé: {pipeline.config.config_path}")
        return False
    
    if not pipeline.config.output_json_path.exists():
        print(f"❌ Fichier projet non trouvé: {pipeline.config.output_json_path}")
        return False
    
    try:
        # Test avec preset
        print("📺 Test export avec preset 'fast_preview'...")
        video_path = pipeline.export_video(
            fps=5,
            preset='fast_preview',
            cleanup_frames=False,
            force_regenerate=True,
            minimap_config={
                'rotation': 90,
                'half_field': 'left',
                'transparency': 0.6,
                'position': 'lower center'
            }
        )
        
        print(f"✅ Export avec preset réussi: {video_path}")
        
        # Test sans preset
        print("📺 Test export sans preset...")
        video_path2 = pipeline.export_video(
            fps=3,
            figsize=(12, 8),
            dpi=80,
            cleanup_frames=False,
            force_regenerate=True,
            minimap_config={
                'rotation': 180,
                'half_field': 'right',
                'transparency': 0.4
            }
        )
        
        print(f"✅ Export sans preset réussi: {video_path2}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur pipeline: {e}")
        return False

def test_compatibility():
    """Test de compatibilité avec l'ancienne API"""
    
    print("\n🎯 Test 6: Compatibilité avec ancienne API")
    print("=" * 50)
    
    # Import de l'ancienne API (wrapper de compatibilité)
    from eva2sport.export.video_exporter import VideoExporter as OldVideoExporter
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    if not config.output_json_path.exists():
        print(f"❌ Fichier projet non trouvé: {config.output_json_path}")
        return False
    
    try:
        # Test avec l'ancienne API
        old_exporter = OldVideoExporter(config)
        old_exporter.configure_minimap(rotation=90, half_field='left')
        
        # Obtenir l'exporteur de nouvelle génération
        new_exporter = old_exporter.upgrade_to_new_api()
        stats = new_exporter.get_export_stats()
        
        print(f"✅ Compatibilité vérifiée - {stats['total_frames']} frames disponibles")
        return True
        
    except Exception as e:
        print(f"❌ Erreur compatibilité: {e}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🧪 TESTS COMPLETS - NOUVELLE ARCHITECTURE MODULAIRE")
    print("=" * 70)
    
    # Liste des tests à exécuter
    tests = [
        test_new_architecture_basic,
        test_configuration_presets,
        test_minimap_configurations,
        test_validation_and_errors,
        test_pipeline_with_new_architecture,
        test_compatibility
    ]
    
    results = []
    
    for test_func in tests:
        try:
            # Exécuter le test
            if test_func.__name__ == 'test_new_architecture_basic':
                result = test_func()
                success = result[0] if isinstance(result, tuple) else result
            else:
                success = test_func()
            
            results.append((test_func.__name__, success))
            
        except Exception as e:
            print(f"❌ Erreur dans {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))
    
    # Résumé des résultats
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"   {test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ La nouvelle architecture modulaire fonctionne parfaitement.")
        print("🚀 Prêt pour la production avec:")
        print("   • Configuration typée et validée")
        print("   • Presets prédéfinis")
        print("   • API modulaire et extensible")
        print("   • Compatibilité préservée")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔍 Vérifiez les logs d'erreur ci-dessus.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 