"""
Gestionnaire pour dessiner les objets sur le terrain
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any
from ..objects.object_renderer_factory import ObjectRendererFactory
from ..config.visualization_config import VisualizationConfig
from .football_field import FootballField2D

class FieldDrawer:
    """Gestionnaire pour dessiner les objets sur le terrain"""
    
    def __init__(self, config: VisualizationConfig):
        """
        Initialise le FieldDrawer
        
        Args:
            config: Configuration de visualisation
        """
        self.config = config
        self.renderer_factory = ObjectRendererFactory(config)
    
    def draw_field_with_objects(self, ax: plt.Axes, field_points: Dict[str, Dict[str, Any]]) -> None:
        """
        Dessine le terrain avec tous les objets
        
        Args:
            ax: Axes matplotlib
            field_points: Dict avec object_id comme clé et données de position/info comme valeur
        """
        # Créer le terrain
        field = FootballField2D(
            line_color=self.config.minimap_config.line_color,
            background_color=self.config.minimap_config.background_color
        )
        
        # Dessiner le terrain
        field.draw(
            ax=ax,
            show_plot=False,
            rotation=self.config.minimap_config.rotation,
            half_field=self.config.minimap_config.half_field,
            invert_x=self.config.minimap_config.invert_x,
            invert_y=self.config.minimap_config.invert_y
        )
        
        # Dessiner tous les objets
        for obj_id, point_data in field_points.items():
            self.draw_object(ax, obj_id, point_data, field)
    
    def draw_object(self, ax: plt.Axes, object_id: str, point_data: Dict[str, Any], 
                   field: FootballField2D) -> None:
        """
        Dessine un objet sur le terrain
        
        Args:
            ax: Axes matplotlib
            object_id: ID de l'objet
            point_data: Données de position et info de l'objet
            field: Instance du terrain pour les transformations
        """
        # Extraire les coordonnées
        x, y = point_data['x'], point_data['y']
        object_info = point_data['info']
        
        # Appliquer la rotation aux coordonnées
        original_coords = np.array([[x, y]])
        rotated_coords = field.get_transformed_coordinates(original_coords)
        transformed_x, transformed_y = rotated_coords[0]
        
        # Dessiner l'objet avec le renderer approprié
        self.renderer_factory.render_object_on_field(
            ax, transformed_x, transformed_y, object_id, object_info,
            point_size=self.config.minimap_config.point_size
        )
    
    def update_config(self, new_config: VisualizationConfig) -> None:
        """
        Met à jour la configuration
        
        Args:
            new_config: Nouvelle configuration
        """
        self.config = new_config
        self.renderer_factory.update_config(new_config) 