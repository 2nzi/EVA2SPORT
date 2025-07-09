"""
Renderer pour les joueurs
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Any
from .base_renderer import BaseRenderer

class PlayerRenderer(BaseRenderer):
    """Renderer pour les joueurs"""
    
    def render_on_image(self, ax: plt.Axes, x: float, y: float, 
                       object_id: str, object_info: Dict[str, Any]) -> None:
        """Dessine un joueur sur l'image avec des arcs de cercle"""
        color = self.get_object_color(object_info)
        
        # Paramètres des arcs de cercle
        ellipse_width, ellipse_height = 50, 20
        gap_size = 120  # Taille des gaps en degrés
        arc_linewidth = 2
        
        # Dessiner les arcs (haut et bas)
        for gap_center in [90, 270]:  # Haut et bas
            other_gap = 270 if gap_center == 90 else 90
            gap_start = gap_center - gap_size // 2
            gap_end = gap_center + gap_size // 2
            other_start = other_gap - gap_size // 2
            other_end = other_gap + gap_size // 2
            
            arc = patches.Arc(
                (x, y - 5),
                width=ellipse_width,
                height=ellipse_height,
                angle=0,
                theta1=gap_end,
                theta2=other_start + (360 if other_start < gap_end else 0),
                color=color,
                linewidth=arc_linewidth
            )
            ax.add_patch(arc)
        
        # Dessiner l'ID si nécessaire
        if self.should_display_id(object_info):
            self.render_id_on_image(ax, x, y, object_id, color)
    
    def render_on_field(self, ax: plt.Axes, x: float, y: float,
                       object_id: str, object_info: Dict[str, Any],
                       point_size: int = 70) -> None:
        """Dessine un joueur sur le terrain avec un cercle coloré"""
        color = self.get_object_color(object_info)
        
        # Dessiner le cercle
        ax.scatter(
            x, y,
            color=color,
            s=point_size,
            zorder=5
        )
        
        # Dessiner l'ID si nécessaire
        if self.should_display_id(object_info):
            self.render_id_on_field(ax, x, y, object_id)
    
    def get_default_color(self) -> str:
        """Retourne la couleur par défaut pour les joueurs"""
        return self.config.default_player_color
    
    def should_display_id(self, object_info: Dict[str, Any]) -> bool:
        """Les joueurs affichent toujours leur ID"""
        return True
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Types d'objets supportés"""
        return ['player'] 