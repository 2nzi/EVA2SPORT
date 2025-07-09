"""
Renderer de base pour les objets
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from ..config.visualization_config import VisualizationConfig

class BaseRenderer(ABC):
    """Classe de base pour tous les renderers d'objets"""
    
    def __init__(self, config: VisualizationConfig):
        """
        Initialise le renderer
        
        Args:
            config: Configuration de visualisation
        """
        self.config = config
    
    @abstractmethod
    def render_on_image(self, ax: plt.Axes, x: float, y: float, 
                       object_id: str, object_info: Dict[str, Any]) -> None:
        """
        Dessine l'objet sur l'image principale
        
        Args:
            ax: Axes matplotlib
            x: Coordonnée X sur l'image
            y: Coordonnée Y sur l'image
            object_id: ID de l'objet
            object_info: Informations de l'objet
        """
        pass
    
    @abstractmethod
    def render_on_field(self, ax: plt.Axes, x: float, y: float,
                       object_id: str, object_info: Dict[str, Any],
                       point_size: int = 70) -> None:
        """
        Dessine l'objet sur le terrain (minimap)
        
        Args:
            ax: Axes matplotlib
            x: Coordonnée X sur le terrain
            y: Coordonnée Y sur le terrain
            object_id: ID de l'objet
            object_info: Informations de l'objet
            point_size: Taille du point
        """
        pass
    
    def get_object_color(self, object_info: Dict[str, Any]) -> str:
        """
        Récupère la couleur de l'objet
        
        Args:
            object_info: Informations de l'objet
            
        Returns:
            Couleur de l'objet
        """
        # Priorité : couleur du maillot > couleur d'affichage > couleur par défaut
        return (object_info.get('jersey_color') or 
                object_info.get('display_color') or 
                self.get_default_color())
    
    @abstractmethod
    def get_default_color(self) -> str:
        """
        Retourne la couleur par défaut pour ce type d'objet
        
        Returns:
            Couleur par défaut
        """
        pass
    
    def should_display_id(self, object_info: Dict[str, Any]) -> bool:
        """
        Détermine si l'ID doit être affiché
        
        Args:
            object_info: Informations de l'objet
            
        Returns:
            True si l'ID doit être affiché
        """
        return True  # Par défaut, afficher l'ID
    
    def render_id_on_image(self, ax: plt.Axes, x: float, y: float,
                          object_id: str, color: str) -> None:
        """
        Dessine l'ID de l'objet sur l'image
        
        Args:
            ax: Axes matplotlib
            x: Coordonnée X
            y: Coordonnée Y
            object_id: ID de l'objet
            color: Couleur de l'objet
        """
        if not self.config.show_image_annotations:
            return
            
        ax.annotate(
            f'{object_id}', 
            (x, y + 5), 
            xytext=(0, 0),
            textcoords='offset points', 
            fontsize=self.config.annotation_font_size,
            ha='center', 
            va='center',
            color='white', 
            weight='bold',
            bbox=dict(
                boxstyle="round,pad=0.2,rounding_size=0.5",
                facecolor=color,
                alpha=self.config.annotation_box_alpha,
                edgecolor=color
            )
        )
    
    def render_id_on_field(self, ax: plt.Axes, x: float, y: float,
                          object_id: str) -> None:
        """
        Dessine l'ID de l'objet sur le terrain
        
        Args:
            ax: Axes matplotlib
            x: Coordonnée X
            y: Coordonnée Y
            object_id: ID de l'objet
        """
        if not self.config.minimap_config.show_object_ids:
            return
            
        ax.text(
            x, y, str(object_id),
            color='white',
            fontsize=self.config.minimap_config.id_font_size,
            ha='center',
            va='center',
            weight='bold',
            zorder=6
        )
    
    @classmethod
    def get_supported_types(cls) -> list:
        """
        Retourne les types d'objets supportés par ce renderer
        
        Returns:
            Liste des types supportés
        """
        return [] 