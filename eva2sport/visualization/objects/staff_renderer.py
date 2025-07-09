"""
Renderer pour le staff
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Any
from .base_renderer import BaseRenderer

class StaffRenderer(BaseRenderer):
    """Renderer pour le staff"""
    
    def render_on_image(self, ax: plt.Axes, x: float, y: float, 
                       object_id: str, object_info: Dict[str, Any]) -> None:
        """Dessine un membre du staff sur l'image avec un carré"""
        color = self.get_object_color(object_info)
        square_size = 10
        
        # Créer le carré
        square = patches.Rectangle(
            (x - square_size, y - 5 - square_size),
            square_size * 2,
            square_size * 2,
            facecolor=color,
            edgecolor='white',
            linewidth=2
        )
        ax.add_patch(square)
        
        # Dessiner l'ID si nécessaire
        if self.should_display_id(object_info):
            self.render_id_on_image(ax, x, y, object_id, color)
    
    def render_on_field(self, ax: plt.Axes, x: float, y: float,
                       object_id: str, object_info: Dict[str, Any],
                       point_size: int = 70) -> None:
        """Dessine un membre du staff sur le terrain avec un carré"""
        color = self.get_object_color(object_info)
        square_size = np.sqrt(point_size) * 0.6
        
        # Créer le carré
        square = patches.Rectangle(
            (x - square_size/2, y - square_size/2),
            square_size,
            square_size,
            facecolor=color,
            edgecolor='white',
            linewidth=2,
            zorder=5
        )
        ax.add_patch(square)
        
        # Dessiner l'ID si nécessaire
        if self.should_display_id(object_info):
            self.render_id_on_field(ax, x, y, object_id)
    
    def get_default_color(self) -> str:
        """Retourne la couleur par défaut pour le staff"""
        return self.config.default_staff_color
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Types d'objets supportés"""
        return ['staff'] 