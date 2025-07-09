"""
Renderer pour les arbitres
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Any
from .base_renderer import BaseRenderer

class RefereeRenderer(BaseRenderer):
    """Renderer pour les arbitres"""
    
    def render_on_image(self, ax: plt.Axes, x: float, y: float, 
                       object_id: str, object_info: Dict[str, Any]) -> None:
        """Dessine un arbitre sur l'image avec un losange"""
        color = self.get_object_color(object_info)
        diamond_size = 12
        
        # Créer le losange
        diamond = patches.Polygon(
            [(x, y - 5 - diamond_size), (x + diamond_size, y - 5),
             (x, y - 5 + diamond_size), (x - diamond_size, y - 5)],
            closed=True,
            facecolor=color,
            edgecolor='white',
            linewidth=2
        )
        ax.add_patch(diamond)
        
        # Dessiner l'ID si nécessaire
        if self.should_display_id(object_info):
            self.render_id_on_image(ax, x, y, object_id, color)
    
    def render_on_field(self, ax: plt.Axes, x: float, y: float,
                       object_id: str, object_info: Dict[str, Any],
                       point_size: int = 70) -> None:
        """Dessine un arbitre sur le terrain avec un cercle noir"""
        color = self.get_object_color(object_info)
        
        # Dessiner le cercle
        ax.scatter(
            x, y,
            color=color,
            s=point_size,
            zorder=5,
            edgecolors='white',
            linewidth=1
        )
        
        # Dessiner l'ID si nécessaire
        if self.should_display_id(object_info):
            self.render_id_on_field(ax, x, y, object_id)
    
    def get_default_color(self) -> str:
        """Retourne la couleur par défaut pour les arbitres"""
        return self.config.default_referee_color
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Types d'objets supportés"""
        return ['referee', 'arbitre'] 