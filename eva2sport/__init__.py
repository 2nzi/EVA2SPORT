"""
EVA2SPORT - Pipeline de Tracking Vidéo avec SAM2

Usage simple:
    >>> import eva2sport
    >>> results = eva2sport.track_video("ma_video")

Usage avancé:
    >>> pipeline = eva2sport.create_pipeline("ma_video")
    >>> results = pipeline.run_full_pipeline()
"""

from .pipeline import EVA2SportPipeline
from .config import Config
from typing import Optional

def create_pipeline(video_name: str, working_dir: str = None,
                   segment_offset_before_seconds: Optional[float] = None,
                   segment_offset_after_seconds: Optional[float] = None,
                   **kwargs) -> EVA2SportPipeline:
    """
    Crée une pipeline de tracking vidéo
    
    Args:
        video_name: Nom de la vidéo (sans extension)
        working_dir: Répertoire de travail (défaut: répertoire courant)
        segment_offset_before_seconds: Offset avant en secondes (active le mode segment)
        segment_offset_after_seconds: Offset après en secondes (active le mode segment)
        **kwargs: Autres paramètres de configuration
    
    Returns:
        Pipeline configurée et prête à l'usage
    
    Example:
        >>> # Mode complet
        >>> pipeline = eva2sport.create_pipeline("match_football")
        >>> # Mode segmentation
        >>> pipeline = eva2sport.create_pipeline("match_football", 
        ...                                     segment_offset_before_seconds=2.0,
        ...                                     segment_offset_after_seconds=3.0)
    """
    return EVA2SportPipeline(
        video_name, 
        working_dir,
        segment_offset_before_seconds=segment_offset_before_seconds,
        segment_offset_after_seconds=segment_offset_after_seconds,
        **kwargs
    )

def track_video(video_name: str, working_dir: str = None, 
                force_extraction: bool = False) -> dict:
    """
    Mode ultra-simple : tracking complet en une ligne
    
    Args:
        video_name: Nom de la vidéo
        working_dir: Répertoire de travail
        force_extraction: Force ré-extraction frames
    
    Returns:
        Dictionnaire avec résultats et chemins de fichiers
    
    Example:
        >>> results = eva2sport.track_video("match_football")
        >>> print(f"JSON créé: {results['export_paths']['json']}")
    """
    pipeline = create_pipeline(video_name, working_dir)
    return pipeline.run_full_pipeline(force_extraction=force_extraction)

def create_config(video_name: str, working_dir: str = None, **kwargs) -> Config:
    """
    Crée une configuration personnalisée
    
    Args:
        video_name: Nom de la vidéo
        working_dir: Répertoire de travail
        **kwargs: Options de configuration (FRAME_INTERVAL, SEGMENT_MODE, etc.)
    
    Returns:
        Configuration personnalisée
    
    Example:
        >>> config = eva2sport.create_config(
        ...     "match_football", 
        ...     FRAME_INTERVAL=5,
        ...     SEGMENT_MODE=True
        ... )
    """
    config = Config(video_name, working_dir)
    
    # Appliquer les options personnalisées
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config

# === EXPORTS PUBLICS ===
__all__ = [
    # Fonctions principales (usage simple)
    'create_pipeline',
    'track_video', 
    'create_config',
    
    # Classes principales (usage avancé)
    'EVA2SportPipeline',
    'Config',
]

# === MÉTADONNÉES ===
__version__ = "1.0.0"
__author__ = "EVA2SPORT Team"
__description__ = "Pipeline de tracking vidéo avec SAM2 pour l'analyse sportive"