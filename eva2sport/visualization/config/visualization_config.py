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
    
    # Paramètres de qualité vidéo
    video_quality: str = 'medium'  # 'low', 'medium', 'high', 'ultra'
    video_codec_priority: Tuple[str, ...] = ('avc1', 'h264', 'H264', 'mp4v')
    video_bitrate: Optional[int] = None  # Bitrate en kbps, None pour auto
    
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
        
        # Validation video_quality
        valid_qualities = ['low', 'medium', 'high', 'ultra']
        if self.video_quality not in valid_qualities:
            raise ValueError(f"video_quality doit être l'un de {valid_qualities}, reçu: {self.video_quality}")
        
        # Validation video_bitrate
        if self.video_bitrate is not None and self.video_bitrate <= 0:
            raise ValueError(f"video_bitrate doit être positif ou None, reçu: {self.video_bitrate}")
        
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
            video_quality=self.video_quality,
            video_codec_priority=self.video_codec_priority,
            video_bitrate=self.video_bitrate,
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
            'video_quality': self.video_quality,
            'video_codec_priority': self.video_codec_priority,
            'video_bitrate': self.video_bitrate,
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
        """Configuration haute qualité pour export final"""
        return cls(
            figsize=(20, 12),
            dpi=150,
            fps=60,
            video_quality='ultra',
            video_bitrate=8000,  # 8 Mbps
            minimap_config=MinimapConfig.get_analysis_view()
        )
    
    @classmethod
    def get_fast_preview(cls) -> 'VisualizationConfig':
        """Configuration pour aperçu rapide"""
        return cls(
            figsize=(10, 6),
            dpi=80,
            fps=15,
            video_quality='low',
            video_bitrate=1000,  # 1 Mbps
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
            video_quality='high',
            video_bitrate=4000,  # 4 Mbps
            minimap_config=MinimapConfig.get_tactical_view()
        )
    
    @classmethod
    def get_web_optimized(cls) -> 'VisualizationConfig':
        """Configuration optimisée pour la compatibilité web"""
        return cls(
            figsize=(16, 9),  # Format 16:9 standard
            dpi=100,
            fps=30,
            video_quality='medium',
            video_bitrate=2500,  # 2.5 Mbps - bon compromis qualité/taille
            video_codec_priority=('avc1', 'h264'),  # Priorité absolue à H.264
            minimap_config=MinimapConfig.get_broadcast_view()
        )
    
    def __str__(self) -> str:
        """Représentation string de la configuration"""
        return f"VisualizationConfig(figsize={self.figsize}, fps={self.fps}, minimap={self.show_minimap})"
    
    def __repr__(self) -> str:
        """Représentation détaillée de la configuration"""
        return (f"VisualizationConfig(figsize={self.figsize}, dpi={self.dpi}, fps={self.fps}, "
                f"show_minimap={self.show_minimap}, minimap_config={self.minimap_config})") 