"""
Classe pour dessiner un terrain de football en 2D
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple, Literal

class FootballField2D:
    """Classe pour dessiner un terrain de football en 2D"""

    def __init__(self, field_length: float = 105, field_width: float = 68, 
                 line_color: str = 'white', background_color: str = '#2d5a27', 
                 line_width: float = 2):
        """
        Initialise le terrain de football
        
        Args:
            field_length: Longueur du terrain en mètres
            field_width: Largeur du terrain en mètres
            line_color: Couleur des lignes
            background_color: Couleur de fond
            line_width: Épaisseur des lignes
        """
        self.field_length = field_length
        self.field_width = field_width
        self.line_color = line_color
        self.background_color = background_color
        self.line_width = line_width

        # Dimensions standards FIFA
        self.penalty_length = 16.5
        self.penalty_width = 40.32
        self.goal_area_length = 5.5
        self.goal_area_width = 18.32
        self.center_circle_radius = 9.15
        self.penalty_spot_distance = 11
        self.goal_width = 7.32
        self.goal_depth = 1.5

        # Paramètres de transformation actuels
        self.rotation = 0
        self.half_field = None
        self.invert_x = False
        self.invert_y = False

    def _rotate_coordinates(self, coords: np.ndarray, rotation: int) -> np.ndarray:
        """
        Applique une rotation aux coordonnées
        
        Args:
            coords: Coordonnées à transformer (N, 2)
            rotation: Angle de rotation (0, 90, 180, 270)
            
        Returns:
            Coordonnées transformées
        """
        if rotation == 0:
            return coords
        elif rotation == 90:
            return np.column_stack([-coords[:, 1], coords[:, 0]])
        elif rotation == 180:
            return np.column_stack([-coords[:, 0], -coords[:, 1]])
        elif rotation == 270:
            return np.column_stack([coords[:, 1], -coords[:, 0]])
        else:
            raise ValueError(f"La rotation doit être 0, 90, 180 ou 270 degrés, reçu: {rotation}")

    def draw(self, ax: Optional[plt.Axes] = None, show_plot: bool = True, 
             figsize: Tuple[int, int] = (12, 8), rotation: int = 0,
             half_field: Literal['left', 'right', 'full'] = 'full', 
             invert_x: bool = False, invert_y: bool = True) -> plt.Axes:
        """
        Dessine le terrain de football
        
        Args:
            ax: Axes matplotlib (crée une nouvelle figure si None)
            show_plot: Afficher le plot
            figsize: Taille de la figure
            rotation: Rotation du terrain (0, 90, 180, 270)
            half_field: Afficher seulement une moitié ('left', 'right', None)
            invert_x: Inverser l'axe X
            invert_y: Inverser l'axe Y
            
        Returns:
            Axes matplotlib
        """
        # Stocker les paramètres de transformation
        self.rotation = rotation
        self.half_field = half_field
        self.invert_x = invert_x
        self.invert_y = invert_y

        # Créer la figure si nécessaire
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        # Configurer le fond
        ax.set_facecolor(self.background_color)

        # Dessiner tous les éléments du terrain
        self._draw_field_outline(ax)
        self._draw_center_line(ax)
        self._draw_center_circle(ax)
        self._draw_penalty_areas(ax)
        self._draw_goal_areas(ax)
        self._draw_penalty_spots(ax)
        self._draw_penalty_arcs(ax)
        self._draw_goals(ax)

        # Configurer les axes
        self._configure_axes(ax)

        if show_plot:
            plt.tight_layout()
            plt.show()

        return ax

    def _draw_field_outline(self, ax: plt.Axes) -> None:
        """Dessine le contour du terrain principal"""
        field_corners = np.array([
            [-self.field_length/2, -self.field_width/2],
            [self.field_length/2, -self.field_width/2],
            [self.field_length/2, self.field_width/2],
            [-self.field_length/2, self.field_width/2],
            [-self.field_length/2, -self.field_width/2]
        ])
        rotated_corners = self._rotate_coordinates(field_corners, self.rotation)
        ax.plot(rotated_corners[:, 0], rotated_corners[:, 1],
                color=self.line_color, linewidth=self.line_width)

    def _draw_center_line(self, ax: plt.Axes) -> None:
        """Dessine la ligne médiane"""
        center_line = np.array([
            [0, -self.field_width/2],
            [0, self.field_width/2]
        ])
        rotated_line = self._rotate_coordinates(center_line, self.rotation)
        ax.plot(rotated_line[:, 0], rotated_line[:, 1],
                color=self.line_color, linewidth=self.line_width)

    def _draw_center_circle(self, ax: plt.Axes) -> None:
        """Dessine le cercle central et le point central"""
        # Cercle central
        circle_points = 100
        theta = np.linspace(0, 2*np.pi, circle_points)
        x_circle = self.center_circle_radius * np.cos(theta)
        y_circle = self.center_circle_radius * np.sin(theta)

        circle_coords = np.column_stack([x_circle, y_circle])
        rotated_circle = self._rotate_coordinates(circle_coords, self.rotation)
        ax.plot(rotated_circle[:, 0], rotated_circle[:, 1],
                color=self.line_color, linewidth=self.line_width)

        # Point central
        center_point = np.array([[0, 0]])
        rotated_center = self._rotate_coordinates(center_point, self.rotation)
        ax.plot(rotated_center[0, 0], rotated_center[0, 1], 'o',
                color=self.line_color, markersize=3)

    def _draw_penalty_areas(self, ax: plt.Axes) -> None:
        """Dessine les surfaces de réparation"""
        # Surface de réparation gauche
        penalty_left = np.array([
            [-self.field_length/2, -self.penalty_width/2],
            [-self.field_length/2 + self.penalty_length, -self.penalty_width/2],
            [-self.field_length/2 + self.penalty_length, self.penalty_width/2],
            [-self.field_length/2, self.penalty_width/2],
            [-self.field_length/2, -self.penalty_width/2]
        ])
        rotated_left = self._rotate_coordinates(penalty_left, self.rotation)
        ax.plot(rotated_left[:, 0], rotated_left[:, 1],
                color=self.line_color, linewidth=self.line_width)

        # Surface de réparation droite
        penalty_right = np.array([
            [self.field_length/2, -self.penalty_width/2],
            [self.field_length/2 - self.penalty_length, -self.penalty_width/2],
            [self.field_length/2 - self.penalty_length, self.penalty_width/2],
            [self.field_length/2, self.penalty_width/2],
            [self.field_length/2, -self.penalty_width/2]
        ])
        rotated_right = self._rotate_coordinates(penalty_right, self.rotation)
        ax.plot(rotated_right[:, 0], rotated_right[:, 1],
                color=self.line_color, linewidth=self.line_width)

    def _draw_goal_areas(self, ax: plt.Axes) -> None:
        """Dessine les surfaces de but"""
        # Surface de but gauche
        goal_left = np.array([
            [-self.field_length/2, -self.goal_area_width/2],
            [-self.field_length/2 + self.goal_area_length, -self.goal_area_width/2],
            [-self.field_length/2 + self.goal_area_length, self.goal_area_width/2],
            [-self.field_length/2, self.goal_area_width/2],
            [-self.field_length/2, -self.goal_area_width/2]
        ])
        rotated_left = self._rotate_coordinates(goal_left, self.rotation)
        ax.plot(rotated_left[:, 0], rotated_left[:, 1],
                color=self.line_color, linewidth=self.line_width)

        # Surface de but droite
        goal_right = np.array([
            [self.field_length/2, -self.goal_area_width/2],
            [self.field_length/2 - self.goal_area_length, -self.goal_area_width/2],
            [self.field_length/2 - self.goal_area_length, self.goal_area_width/2],
            [self.field_length/2, self.goal_area_width/2],
            [self.field_length/2, -self.goal_area_width/2]
        ])
        rotated_right = self._rotate_coordinates(goal_right, self.rotation)
        ax.plot(rotated_right[:, 0], rotated_right[:, 1],
                color=self.line_color, linewidth=self.line_width)

    def _draw_penalty_spots(self, ax: plt.Axes) -> None:
        """Dessine les points de penalty"""
        penalty_spots = np.array([
            [-self.field_length/2 + self.penalty_spot_distance, 0],
            [self.field_length/2 - self.penalty_spot_distance, 0]
        ])
        rotated_spots = self._rotate_coordinates(penalty_spots, self.rotation)
        ax.plot(rotated_spots[:, 0], rotated_spots[:, 1], 'o',
                color=self.line_color, markersize=3)

    def _draw_penalty_arcs(self, ax: plt.Axes) -> None:
        """Dessine les arcs de cercle des surfaces de réparation"""
        arc_angles = np.linspace(-np.pi/3, np.pi/3, 50)

        # Arc gauche
        arc_x_left = (-self.field_length/2 + self.penalty_spot_distance +
                      self.center_circle_radius * np.cos(arc_angles))
        arc_y_left = self.center_circle_radius * np.sin(arc_angles)

        mask_left = arc_x_left >= -self.field_length/2 + self.penalty_length
        if np.any(mask_left):
            arc_left_coords = np.column_stack([arc_x_left[mask_left], arc_y_left[mask_left]])
            rotated_arc_left = self._rotate_coordinates(arc_left_coords, self.rotation)
            ax.plot(rotated_arc_left[:, 0], rotated_arc_left[:, 1],
                    color=self.line_color, linewidth=self.line_width)

        # Arc droit
        arc_x_right = (self.field_length/2 - self.penalty_spot_distance +
                       self.center_circle_radius * np.cos(np.pi - arc_angles))
        arc_y_right = self.center_circle_radius * np.sin(np.pi - arc_angles)

        mask_right = arc_x_right <= self.field_length/2 - self.penalty_length
        if np.any(mask_right):
            arc_right_coords = np.column_stack([arc_x_right[mask_right], arc_y_right[mask_right]])
            rotated_arc_right = self._rotate_coordinates(arc_right_coords, self.rotation)
            ax.plot(rotated_arc_right[:, 0], rotated_arc_right[:, 1],
                    color=self.line_color, linewidth=self.line_width)

    def _draw_goals(self, ax: plt.Axes) -> None:
        """Dessine les buts"""
        # But gauche
        goal_left_posts = np.array([
            [-self.field_length/2, -self.goal_width/2],
            [-self.field_length/2 - self.goal_depth, -self.goal_width/2],
            [-self.field_length/2 - self.goal_depth, self.goal_width/2],
            [-self.field_length/2, self.goal_width/2]
        ])
        rotated_left_goal = self._rotate_coordinates(goal_left_posts, self.rotation)
        ax.plot(rotated_left_goal[:, 0], rotated_left_goal[:, 1],
                color=self.line_color, linewidth=self.line_width + 1)

        # But droit
        goal_right_posts = np.array([
            [self.field_length/2, -self.goal_width/2],
            [self.field_length/2 + self.goal_depth, -self.goal_width/2],
            [self.field_length/2 + self.goal_depth, self.goal_width/2],
            [self.field_length/2, self.goal_width/2]
        ])
        rotated_right_goal = self._rotate_coordinates(goal_right_posts, self.rotation)
        ax.plot(rotated_right_goal[:, 0], rotated_right_goal[:, 1],
                color=self.line_color, linewidth=self.line_width + 1)

    def _configure_axes(self, ax: plt.Axes) -> None:
        """Configure les axes et l'apparence générale"""
        ax.set_aspect('equal')

        # Calculer les limites selon la rotation
        if self.rotation in [0, 180]:
            max_x = self.field_length/2 + 10
            max_y = self.field_width/2 + 10
        else:
            max_x = self.field_width/2 + 10
            max_y = self.field_length/2 + 10

        x_min, x_max = -max_x, max_x
        y_min, y_max = -max_y, max_y

        # Ajuster pour demi-terrain
        if self.half_field == 'left':
            if self.rotation == 0:
                x_max = 5
            elif self.rotation == 90:
                y_max = 5
            elif self.rotation == 180:
                x_min = -5
            elif self.rotation == 270:
                y_min = -5
        elif self.half_field == 'right':
            if self.rotation == 0:
                x_min = -5
            elif self.rotation == 90:
                y_min = -5
            elif self.rotation == 180:
                x_max = 5
            elif self.rotation == 270:
                y_max = 5

        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])

        # Appliquer les inversions
        if self.invert_x:
            ax.invert_xaxis()
        if self.invert_y:
            ax.invert_yaxis()

        # Style des axes
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])

    def get_field_dimensions(self) -> Tuple[float, float]:
        """
        Retourne les dimensions du terrain
        
        Returns:
            Tuple (longueur, largeur)
        """
        return self.field_length, self.field_width

    def get_transformed_coordinates(self, coords: np.ndarray) -> np.ndarray:
        """
        Transforme des coordonnées selon la configuration actuelle
        
        Args:
            coords: Coordonnées à transformer
            
        Returns:
            Coordonnées transformées
        """
        return self._rotate_coordinates(coords, self.rotation) 