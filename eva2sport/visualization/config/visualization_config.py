"""
Configuration générale pour la visualisation
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from .minimap_config import MinimapConfig

@dataclass
class VisualizationConfig:
    """Configuration générale pour la visualisation"""
    
    # Paramètres de la figure
    figsize: Tuple[int, int] = (15, 8)
    dpi: int = 100
    
    # Paramètres vidéo
    fps: int = 30
    cleanup_frames: bool = True
    force_regenerate: bool = False
    
    # Minimap
    show_minimap: bool = True
    minimap_config: MinimapConfig = None
    
    # Annotation sur l'image
    show_image_annotations: bool = True
    annotation_font_size: int = 10
    annotation_box_alpha: float = 0.7
    
    # Couleurs par défaut
    default_player_color: str = 'red'
    default_ball_color: str = 'yellow'
    default_referee_color: str = 'black'
    default_staff_color: str = 'purple'
    default_unknown_color: str = 'gray'
    
    def __post_init__(self):
        """Initialisation après création"""
        if self.minimap_config is None:
            self.minimap_config = MinimapConfig.get_default()
        
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validation des paramètres"""
        # Validation figsize
        if len(self.figsize) != 2 or any(x <= 0 for x in self.figsize):
            raise ValueError(f"figsize doit être un tuple de 2 entiers positifs, reçu: {self.figsize}")
        
        # Validation dpi
        if self.dpi <= 0:
            raise ValueError(f"dpi doit être positif, reçu: {self.dpi}")
        
        # Validation fps
        if self.fps <= 0:
            raise ValueError(f"fps doit être positif, reçu: {self.fps}")
        
        # Validation annotation_font_size
        if self.annotation_font_size <= 0:
            raise ValueError(f"annotation_font_size doit être positif, reçu: {self.annotation_font_size}")
        
        # Validation annotation_box_alpha
        if not 0.0 <= self.annotation_box_alpha <= 1.0:
            raise ValueError(f"annotation_box_alpha doit être entre 0.0 et 1.0, reçu: {self.annotation_box_alpha}")
    
    def update_minimap(self, **kwargs) -> 'VisualizationConfig':
        """Met à jour la configuration minimap"""
        new_config = self.copy()
        new_config.minimap_config = self.minimap_config.update(**kwargs)
        return new_config
    
    def copy(self) -> 'VisualizationConfig':
        """Crée une copie de la configuration"""
        return VisualizationConfig(
            figsize=self.figsize,
            dpi=self.dpi,
            fps=self.fps,
            cleanup_frames=self.cleanup_frames,
            force_regenerate=self.force_regenerate,
            show_minimap=self.show_minimap,
            minimap_config=self.minimap_config,
            show_image_annotations=self.show_image_annotations,
            annotation_font_size=self.annotation_font_size,
            annotation_box_alpha=self.annotation_box_alpha,
            default_player_color=self.default_player_color,
            default_ball_color=self.default_ball_color,
            default_referee_color=self.default_referee_color,
            default_staff_color=self.default_staff_color,
            default_unknown_color=self.default_unknown_color
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la configuration en dictionnaire"""
        return {
            'figsize': self.figsize,
            'dpi': self.dpi,
            'fps': self.fps,
            'cleanup_frames': self.cleanup_frames,
            'force_regenerate': self.force_regenerate,
            'show_minimap': self.show_minimap,
            'minimap_config': self.minimap_config.to_dict(),
            'show_image_annotations': self.show_image_annotations,
            'annotation_font_size': self.annotation_font_size,
            'annotation_box_alpha': self.annotation_box_alpha,
            'default_player_color': self.default_player_color,
            'default_ball_color': self.default_ball_color,
            'default_referee_color': self.default_referee_color,
            'default_staff_color': self.default_staff_color,
            'default_unknown_color': self.default_unknown_color
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'VisualizationConfig':
        """Crée une configuration à partir d'un dictionnaire"""
        config_dict = config_dict.copy()
        if 'minimap_config' in config_dict:
            config_dict['minimap_config'] = MinimapConfig.from_dict(config_dict['minimap_config'])
        return cls(**config_dict)
    
    @classmethod
    def get_default(cls) -> 'VisualizationConfig':
        """Retourne la configuration par défaut"""
        return cls()
    
    @classmethod
    def get_high_quality(cls) -> 'VisualizationConfig':
        """Configuration haute qualité"""
        return cls(
            figsize=(20, 12),
            dpi=150,
            fps=60,
            minimap_config=MinimapConfig.get_analysis_view()
        )
    
    @classmethod
    def get_fast_preview(cls) -> 'VisualizationConfig':
        """Configuration pour aperçu rapide"""
        return cls(
            figsize=(10, 6),
            dpi=80,
            fps=15,
            cleanup_frames=False,
            minimap_config=MinimapConfig.get_broadcast_view()
        )
    
    @classmethod
    def get_tactical_analysis(cls) -> 'VisualizationConfig':
        """Configuration pour analyse tactique"""
        return cls(
            figsize=(16, 10),
            dpi=120,
            fps=30,
            minimap_config=MinimapConfig.get_tactical_view()
        )
    
    def __str__(self) -> str:
        """Représentation string de la configuration"""
        return f"VisualizationConfig(figsize={self.figsize}, fps={self.fps}, minimap={self.show_minimap})"
    
    def __repr__(self) -> str:
        """Représentation détaillée de la configuration"""
        return (f"VisualizationConfig(figsize={self.figsize}, dpi={self.dpi}, fps={self.fps}, "
                f"show_minimap={self.show_minimap}, minimap_config={self.minimap_config})") 