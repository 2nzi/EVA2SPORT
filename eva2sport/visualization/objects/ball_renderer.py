"""
Renderer pour les ballons
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Any
from .base_renderer import BaseRenderer

class BallRenderer(BaseRenderer):
    """Renderer pour les ballons"""
    
    def render_on_image(self, ax: plt.Axes, x: float, y: float, 
                       object_id: str, object_info: Dict[str, Any]) -> None:
        """Dessine un ballon sur l'image avec un triangle jaune"""
        triangle_size = 15
        
        # Créer le triangle pointant vers le haut
        triangle = patches.Polygon(
            [(x, y - 20), (x - triangle_size, y - 35), (x + triangle_size, y - 35)],
            closed=True,
            facecolor='yellow',
            edgecolor='yellow',
            linewidth=2
        )
        ax.add_patch(triangle)
        
        # Les ballons n'affichent généralement pas d'ID
        # (mais on peut forcer via la configuration)
        if self.should_display_id(object_info):
            self.render_id_on_image(ax, x, y, object_id, 'yellow')
    
    def render_on_field(self, ax: plt.Axes, x: float, y: float,
                       object_id: str, object_info: Dict[str, Any],
                       point_size: int = 70) -> None:
        """Dessine un ballon sur le terrain avec un triangle jaune"""
        triangle_size = np.sqrt(point_size) * 0.1
        
        # Créer le triangle
        triangle_points = np.array([
            [x, y - triangle_size],
            [x - triangle_size, y + triangle_size/2],
            [x + triangle_size, y + triangle_size/2]
        ])
        
        triangle = patches.Polygon(
            triangle_points,
            closed=True,
            facecolor='yellow',
            edgecolor='yellow',
            linewidth=2,
            zorder=5
        )
        ax.add_patch(triangle)
        
        # Les ballons n'affichent généralement pas d'ID sur le terrain
        if self.should_display_id(object_info):
            self.render_id_on_field(ax, x, y, object_id)
    
    def get_default_color(self) -> str:
        """Retourne la couleur par défaut pour les ballons"""
        return self.config.default_ball_color
    
    def should_display_id(self, object_info: Dict[str, Any]) -> bool:
        """Les ballons n'affichent généralement pas d'ID"""
        return False
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Types d'objets supportés"""
        return ['ball', 'ballon'] 