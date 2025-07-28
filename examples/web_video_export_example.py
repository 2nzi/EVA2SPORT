#!/usr/bin/env python3
"""
Exemple d'export vidéo optimisé pour le web avec codec H.264
"""

import sys
from pathlib import Path

# Ajouter le chemin du module
sys.path.append(str(Path(__file__).parent.parent))

from eva2sport.config import Config
from eva2sport.visualization.exporters.video_exporter import VideoExporter

def export_video_web_compatible():
    """Exemple d'export vidéo compatible web"""
    
    # Configuration du projet (à adapter selon votre projet)
    config = Config(
        project_dir="data/videos/outputs/mon_projet",
        video_name="match_exemple"
    )
    
    print("🌐 Export vidéo optimisé pour le web")
    print("=" * 50)
    
    # Méthode 1: Utiliser le preset web optimisé (recommandé)
    print("\n📋 Méthode 1: Preset web optimisé")
    exporter = VideoExporter.create_with_preset(config, 'web_optimized')
    
    # Export avec le preset
    success = exporter.export_video("sortie_web_compatible.mp4")
    
    if success:
        print("✅ Export réussi avec preset 'web_optimized'")
    else:
        print("❌ Échec de l'export")
    
    print("\n" + "="*50)
    
    # Méthode 2: Configuration manuelle pour cas spécifiques
    print("\n⚙️ Méthode 2: Configuration personnalisée")
    
    exporter_custom = VideoExporter(config)
    
    # Configuration pour streaming web léger
    exporter_custom.configure_visualization(
        figsize=(12, 8),  # Résolution modérée
        dpi=90,           # DPI optimisé
        fps=25,           # 25 FPS pour web
        video_quality='medium',
        video_bitrate=1800,  # 1.8 Mbps - léger pour streaming
        cleanup_frames=True
    )
    
    # Configuration minimap pour analyse
    exporter_custom.configure_minimap(
        size='15%',
        position='upper right',
        transparency=0.8
    )
    
    success_custom = exporter_custom.export_video("sortie_streaming.mp4")
    
    if success_custom:
        print("✅ Export personnalisé réussi")
    else:
        print("❌ Échec de l'export personnalisé")
    
    print("\n" + "="*50)
    
    # Méthode 3: Comparaison de plusieurs presets
    print("\n📊 Méthode 3: Comparaison des presets disponibles")
    
    presets = ['fast_preview', 'web_optimized', 'tactical_analysis', 'high_quality']
    
    for preset_name in presets:
        print(f"\n🎬 Test du preset '{preset_name}':")
        try:
            test_exporter = VideoExporter.create_with_preset(config, preset_name)
            
            # Afficher les statistiques
            stats = test_exporter.get_export_stats()
            print(f"   📁 Frames disponibles: {stats.get('total_frames', 'N/A')}")
            print(f"   👥 Objets détectés: {stats.get('total_objects', 'N/A')}")
            
            # Test de configuration (sans export réel)
            config_info = test_exporter.get_current_config()
            print(f"   🎞️ Configuration: {config_info['fps']} FPS, qualité {config_info['video_quality']}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

def compare_codecs():
    """Compare les codecs disponibles sur le système"""
    
    print("\n🔍 Vérification des codecs disponibles")
    print("=" * 40)
    
    import cv2
    
    # Test des codecs courants
    codecs_to_test = [
        ('avc1', 'H.264 (AVC1)'),
        ('h264', 'H.264 (h264)'),
        ('H264', 'H.264 (H264)'),
        ('mp4v', 'MPEG-4'),
        ('XVID', 'Xvid'),
        ('MJPG', 'Motion JPEG')
    ]
    
    available_codecs = []
    
    for codec_code, codec_name in codecs_to_test:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec_code)
            # Test avec une résolution standard
            test_writer = cv2.VideoWriter('test_codec.mp4', fourcc, 30, (1920, 1080))
            
            if test_writer.isOpened():
                available_codecs.append((codec_code, codec_name))
                print(f"✅ {codec_name} ({codec_code}) - DISPONIBLE")
                test_writer.release()
                
                # Nettoyer le fichier test
                import os
                try:
                    os.remove('test_codec.mp4')
                except:
                    pass
            else:
                print(f"❌ {codec_name} ({codec_code}) - NON DISPONIBLE")
                test_writer.release()
                
        except Exception as e:
            print(f"❌ {codec_name} ({codec_code}) - ERREUR: {e}")
    
    print(f"\n📋 Codecs disponibles: {len(available_codecs)}/{len(codecs_to_test)}")
    
    if any('h264' in codec[0].lower() or 'avc1' in codec[0].lower() for codec in available_codecs):
        print("🎉 H.264 est disponible - Export web optimisé possible!")
    else:
        print("⚠️ H.264 non disponible - Les vidéos pourront être moins compatibles avec les navigateurs")
    
    return available_codecs

def main():
    """Fonction principale"""
    
    print("🎬 EVA2SPORT - Export vidéo moderne avec H.264")
    print("=" * 60)
    
    # Vérifier les codecs disponibles
    available_codecs = compare_codecs()
    
    # Exemples d'export (décommentez pour tester avec vos données)
    # export_video_web_compatible()
    
    print("\n📖 Instructions d'utilisation:")
    print("1. Configurez votre projet dans config")
    print("2. Utilisez VideoExporter.create_with_preset(config, 'web_optimized')")
    print("3. Appelez exporter.export_video() pour générer la vidéo")
    print("\n💡 Conseil: Le preset 'web_optimized' est recommandé pour une compatibilité web maximale")

if __name__ == "__main__":
    main() 