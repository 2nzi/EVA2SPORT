"""
Factory pour les renderers d'objets
"""

from typing import Dict, Any
from .base_renderer import BaseRenderer
from .player_renderer import PlayerRenderer
from .ball_renderer import BallRenderer
from .referee_renderer import RefereeRenderer
from .staff_renderer import StaffRenderer
from .unknown_renderer import UnknownRenderer
from ..config.visualization_config import VisualizationConfig

class ObjectRendererFactory:
    """Factory pour créer les bons renderers selon le type d'objet"""
    
    # Mapping des types d'objets vers leurs renderers
    RENDERER_MAPPING = {
        'player': PlayerRenderer,
        'ball': BallRenderer,
        'ballon': BallRenderer,
        'referee': RefereeRenderer,
        'arbitre': RefereeRenderer,
        'staff': StaffRenderer,
        'unknown': UnknownRenderer
    }
    
    def __init__(self, config: VisualizationConfig):
        """
        Initialise la factory
        
        Args:
            config: Configuration de visualisation
        """
        self.config = config
        self._renderer_cache = {}
    
    def get_renderer(self, object_type: str) -> BaseRenderer:
        """
        Récupère le renderer approprié pour un type d'objet
        
        Args:
            object_type: Type de l'objet
            
        Returns:
            Instance du renderer approprié
        """
        # Utiliser le cache pour éviter de recréer les renderers
        if object_type not in self._renderer_cache:
            renderer_class = self.RENDERER_MAPPING.get(object_type, UnknownRenderer)
            self._renderer_cache[object_type] = renderer_class(self.config)
        
        return self._renderer_cache[object_type]
    
    def render_object_on_image(self, ax, x: float, y: float,
                              object_id: str, object_info: Dict[str, Any]) -> None:
        """
        Dessine un objet sur l'image
        
        Args:
            ax: Axes matplotlib
            x: Coordonnée X
            y: Coordonnée Y
            object_id: ID de l'objet
            object_info: Informations de l'objet
        """
        object_type = object_info.get('type', 'unknown')
        renderer = self.get_renderer(object_type)
        renderer.render_on_image(ax, x, y, object_id, object_info)
    
    def render_object_on_field(self, ax, x: float, y: float,
                              object_id: str, object_info: Dict[str, Any],
                              point_size: int = 70) -> None:
        """
        Dessine un objet sur le terrain
        
        Args:
            ax: Axes matplotlib
            x: Coordonnée X
            y: Coordonnée Y
            object_id: ID de l'objet
            object_info: Informations de l'objet
            point_size: Taille du point
        """
        object_type = object_info.get('type', 'unknown')
        renderer = self.get_renderer(object_type)
        renderer.render_on_field(ax, x, y, object_id, object_info, point_size)
    
    def get_supported_types(self) -> list:
        """
        Retourne la liste des types d'objets supportés
        
        Returns:
            Liste des types supportés
        """
        return list(self.RENDERER_MAPPING.keys())
    
    def clear_cache(self):
        """Vide le cache des renderers"""
        self._renderer_cache.clear()
    
    def update_config(self, new_config: VisualizationConfig):
        """
        Met à jour la configuration et vide le cache
        
        Args:
            new_config: Nouvelle configuration
        """
        self.config = new_config
        self.clear_cache()
    
    @classmethod
    def register_renderer(cls, object_type: str, renderer_class: type):
        """
        Enregistre un nouveau renderer pour un type d'objet
        
        Args:
            object_type: Type d'objet
            renderer_class: Classe du renderer
        """
        if not issubclass(renderer_class, BaseRenderer):
            raise ValueError(f"Le renderer doit hériter de BaseRenderer")
        
        cls.RENDERER_MAPPING[object_type] = renderer_class
    
    @classmethod
    def get_renderer_for_type(cls, object_type: str) -> type:
        """
        Retourne la classe de renderer pour un type d'objet
        
        Args:
            object_type: Type d'objet
            
        Returns:
            Classe du renderer
        """
        return cls.RENDERER_MAPPING.get(object_type, UnknownRenderer) 