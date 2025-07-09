"""
Wrapper pour la compatibilité avec l'ancienne API du VideoExporter
Utilise la nouvelle architecture modulaire en arrière-plan
"""

from pathlib import Path
from typing import Dict, Tuple, Optional, Any
import warnings

from ..config import Config
from ..visualization import VideoExporter as NewVideoExporter
from ..visualization import VisualizationConfig, MinimapConfig

class VideoExporter:
    """
    Wrapper de compatibilité pour l'ancienne API VideoExporter
    
    ⚠️ Cette classe est dépréciée. Utilisez directement eva2sport.visualization.VideoExporter
    """
    
    def __init__(self, config: Config):
        """
        Initialise l'exporteur vidéo (version de compatibilité)
        
        Args:
            config: Configuration du projet
        """
        # Avertissement de dépréciation
        warnings.warn(
            "eva2sport.export.video_exporter.VideoExporter est déprécié. "
            "Utilisez eva2sport.visualization.VideoExporter à la place.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.config = config
        self.visualization_config = VisualizationConfig.get_default()
        
        # Utiliser la nouvelle architecture
        self._new_exporter = NewVideoExporter(config, self.visualization_config)
        
        # Configuration minimap par défaut (pour compatibilité)
        self.minimap_config = {
            'rotation': 0,
            'half_field': "full",
            'invert_x': False,
            'invert_y': True,
            'transparency': 0.4,
            'size': "35%",
            'position': 'lower center'
        }
    
    def configure_minimap(self, **config) -> None:
        """
        Configure les paramètres de la minimap (version de compatibilité)
        
        Args:
            **config: Paramètres de configuration
        """
        # Mettre à jour la configuration locale
        self.minimap_config.update(config)
        
        # Convertir vers la nouvelle API
        self._new_exporter.configure_minimap(**config)
        
        print(f"✅ Configuration minimap mise à jour: {config}")
    
    def get_minimap_config(self) -> Dict:
        """Retourne la configuration actuelle de la minimap"""
        return self.minimap_config.copy()
    
    def reset_minimap_config(self) -> None:
        """Remet la configuration de la minimap aux valeurs par défaut"""
        self.minimap_config = {
            'rotation': 0,
            'half_field': "full",
            'invert_x': False,
            'invert_y': True,
            'transparency': 0.4,
            'size': "35%",
            'position': 'lower center'
        }
        
        # Réinitialiser la configuration dans la nouvelle architecture
        self._new_exporter.visualization_config = VisualizationConfig.get_default()
        self._new_exporter._update_components()
        
        print("✅ Configuration minimap remise aux valeurs par défaut")
    
    def export_video(self, output_video_path: str = None, fps: int = 30, 
                    show_minimap: bool = True, figsize: Tuple[int, int] = (15, 8), 
                    dpi: int = 100, cleanup_frames: bool = True,
                    force_regenerate: bool = False) -> bool:
        """
        Exporte toutes les frames en vidéo avec annotations (version de compatibilité)
        
        Args:
            output_video_path: Chemin de sortie pour la vidéo
            fps: Frames par seconde de la vidéo
            show_minimap: Afficher la minimap sur chaque frame
            figsize: Taille des figures
            dpi: Résolution des images
            cleanup_frames: Supprimer les frames temporaires après création
            force_regenerate: Forcer la régénération des frames
        
        Returns:
            bool: True si succès, False sinon
        """
        # Configurer l'exporteur avec les paramètres fournis
        self._new_exporter.configure_visualization(
            fps=fps,
            figsize=figsize,
            dpi=dpi,
            show_minimap=show_minimap,
            cleanup_frames=cleanup_frames,
            force_regenerate=force_regenerate
        )
        
        # Exporter avec la nouvelle architecture
        return self._new_exporter.export_video(output_video_path)
    
    def get_export_stats(self) -> Dict:
        """Retourne des statistiques sur les données disponibles pour l'export"""
        return self._new_exporter.get_export_stats()
    
    # Méthodes pour accéder à la nouvelle architecture
    def get_new_exporter(self) -> NewVideoExporter:
        """
        Retourne l'instance de la nouvelle architecture
        
        Returns:
            Instance de la nouvelle architecture VideoExporter
        """
        return self._new_exporter
    
    def upgrade_to_new_api(self) -> NewVideoExporter:
        """
        Migre vers la nouvelle API
        
        Returns:
            Instance de la nouvelle architecture VideoExporter
        """
        print("🔄 Migration vers la nouvelle architecture...")
        print("📝 Consultez example_new_architecture.py pour les exemples d'utilisation")
        print("📚 Documentation: eva2sport.visualization.VideoExporter")
        
        return self._new_exporter