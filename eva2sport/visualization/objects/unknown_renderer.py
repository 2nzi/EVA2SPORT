"""
Renderer pour les objets de type inconnu
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Any
from .base_renderer import BaseRenderer

class UnknownRenderer(BaseRenderer):
    """Renderer pour les objets de type inconnu"""
    
    def render_on_image(self, ax: plt.Axes, x: float, y: float, 
                       object_id: str, object_info: Dict[str, Any]) -> None:
        """Dessine un objet inconnu sur l'image avec un cercle"""
        color = self.get_object_color(object_info)
        
        # Créer le cercle
        circle = patches.Circle(
            (x, y - 5),
            radius=10,
            facecolor=color,
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(circle)
        
        # Dessiner l'ID si nécessaire
        if self.should_display_id(object_info):
            self.render_id_on_image(ax, x, y, object_id, color)
    
    def render_on_field(self, ax: plt.Axes, x: float, y: float,
                       object_id: str, object_info: Dict[str, Any],
                       point_size: int = 70) -> None:
        """Dessine un objet inconnu sur le terrain avec un cercle gris"""
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
        """Retourne la couleur par défaut pour les objets inconnus"""
        return self.config.default_unknown_color
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Types d'objets supportés"""
        return ['unknown'] 