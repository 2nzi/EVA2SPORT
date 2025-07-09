#!/usr/bin/env python3
"""
Exemple d'utilisation simple de la nouvelle architecture modulaire
"""

from eva2sport.config import Config
from eva2sport.visualization import VideoExporter, MinimapConfig
from eva2sport.pipeline import EVA2SportPipeline

def exemple_simple():
    """Exemple le plus simple possible"""
    print("🎯 Exemple 1: Le plus simple")
    print("=" * 40)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    # Utilisation la plus simple
    exporter = VideoExporter(config)
    success = exporter.export_video()
    
    if success:
        print("✅ Vidéo exportée avec succès!")
    
    return success

def exemple_avec_preset():
    """Exemple avec preset prédéfini"""
    print("\n🎯 Exemple 2: Avec preset")
    print("=" * 40)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    # Utilisation avec preset
    exporter = VideoExporter.create_with_preset(config, 'tactical_analysis')
    success = exporter.export_video()
    
    if success:
        print("✅ Vidéo tactique exportée!")
    
    return success

def exemple_minimap_personnalisee():
    """Exemple avec minimap personnalisée"""
    print("\n🎯 Exemple 3: Minimap personnalisée")
    print("=" * 40)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    # Configuration minimap personnalisée - terrain complet
    exporter = VideoExporter(config)
    exporter.configure_minimap(
        rotation=0,
        half_field='full',  # Nouveau: 'full' pour terrain complet
        transparency=0.4,
        position='upper right',
        size='45%'
    )
    
    success = exporter.export_video()
    
    if success:
        print("✅ Vidéo avec minimap terrain complet exportée!")
    
    return success

def exemple_via_pipeline():
    """Exemple via le pipeline"""
    print("\n🎯 Exemple 4: Via pipeline")
    print("=" * 40)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    # Utilisation via pipeline
    pipeline = EVA2SportPipeline(VIDEO_NAME)
    
    try:
        video_path = pipeline.export_video(
            preset='fast_preview',
            minimap_config={
                'rotation': 180,
                'half_field': 'right'  # Options: 'left', 'right', 'full'
            }
        )
        
        print(f"✅ Pipeline terminé: {video_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

    """Exemple montrant toutes les options de half_field"""
    print("\n🎯 Exemple 5: Toutes les vues de terrain")
    print("=" * 40)
    
    VIDEO_NAME = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    config = Config(VIDEO_NAME)
    
    # Configurations différentes pour chaque type de vue
    configurations = [
        {
            'half_field': 'full',
            'desc': 'terrain complet',
            'config': {'rotation': 0, 'transparency': 0.4, 'size': '50%', 'position': 'upper right'}
        },
        {
            'half_field': 'left', 
            'desc': 'demi-terrain gauche',
            'config': {'rotation': 90, 'transparency': 0.5, 'size': '35%', 'position': 'upper left'}
        },
        {
            'half_field': 'right',
            'desc': 'demi-terrain droit', 
            'config': {'rotation': 90, 'transparency': 0.6, 'size': '35%', 'position': 'lower right'}
        }
    ]
    
    for conf in configurations:
        print(f"  📺 Configuration: {conf['desc']}")
        print(f"     🔄 Rotation: {conf['config']['rotation']}°")
        print(f"     💧 Transparence: {conf['config']['transparency']}")
        print(f"     📏 Taille: {conf['config']['size']}")
        print(f"     📍 Position: {conf['config']['position']}")
        
        exporter = VideoExporter(config)
        # Configurer avec tous les paramètres
        exporter.configure_minimap(
            half_field=conf['half_field'],
            **conf['config']
        )
        print(f"     ✅ Minimap configurée pour {conf['desc']}")
        print()
    
    print("✅ Toutes les vues configurées avec succès!")
    return True

def main():
    """Exemples d'utilisation"""
    print("🚀 EXEMPLES D'UTILISATION - NOUVELLE ARCHITECTURE")
    print("=" * 60)
    
    # Exécuter les exemples
    exemples = [
        exemple_simple,
        # exemple_avec_preset, 
        # exemple_minimap_personnalisee,
        # exemple_via_pipeline,
    ]
    
    for exemple in exemples:
        try:
            exemple()
        except Exception as e:
            print(f"❌ Erreur dans {exemple.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("📚 Plus d'exemples dans tests/test_video_export.py")
    print("📖 Documentation complète dans eva2sport.visualization")

if __name__ == "__main__":
    main() 