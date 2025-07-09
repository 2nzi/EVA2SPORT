"""
Exporteur vidéo EVA2SPORT
Inspiré du notebook SAM_viz.ipynb
"""

import os
import json
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from typing import Dict, List, Tuple, Optional, Any
import cv2
from tqdm import tqdm

from ..config import Config


class FieldDrawer:
    """Gestionnaire du dessin des objets sur le terrain"""

    def __init__(self):
        self.drawing_functions = {
            'player': self._draw_player,
            'ball': self._draw_ball,
            'ballon': self._draw_ball,
            'referee': self._draw_referee,
            'arbitre': self._draw_referee,
            'staff': self._draw_staff,
            'unknown': self._draw_unknown
        }

    def get_object_color(self, object_info: Dict) -> str:
        """Récupère la couleur appropriée pour un objet"""
        object_type = object_info.get('type', 'unknown')
        
        if object_type == 'player':
            return object_info.get('jersey_color') or object_info.get('display_color', 'red')
        else:
            return object_info.get('display_color', 'blue')

    def should_display_id(self, object_info: Dict, object_type_filter: List[str] = None) -> bool:
        """Détermine si l'ID doit être affiché selon le type d'objet"""
        object_type = object_info.get('type', 'unknown')
        if object_type_filter is None:
            return object_type not in ['ballon', 'ball']
        return object_type in object_type_filter

    def _draw_player(self, ax, x: float, y: float, object_info: Dict, point_size: int = 70):
        """Dessine un cercle pour un joueur sur le terrain"""
        color = self.get_object_color(object_info)
        ax.scatter(x, y, color=color, s=point_size, zorder=5,
                  edgecolors='white', linewidth=1)

    def _draw_ball(self, ax, x: float, y: float, point_size: int = 70, **kwargs):
        """Dessine un triangle vert pour le ballon sur le terrain"""
        triangle_size = np.sqrt(point_size) * 0.1
        triangle_points = np.array([
            [x, y - triangle_size],
            [x - triangle_size, y + triangle_size/2],
            [x + triangle_size, y + triangle_size/2]
        ])
        triangle = patches.Polygon(triangle_points, closed=True,
                                 facecolor='yellow', edgecolor='yellow', linewidth=2, zorder=5)
        ax.add_patch(triangle)

    def _draw_referee(self, ax, x: float, y: float, point_size: int = 70, **kwargs):
        """Dessine un cercle noir pour l'arbitre sur le terrain"""
        ax.scatter(x, y, color='black', s=point_size, zorder=5,
                  edgecolors='white', linewidth=1)

    def _draw_staff(self, ax, x: float, y: float, point_size: int = 70, **kwargs):
        """Dessine un carré pour le staff sur le terrain"""
        square_size = np.sqrt(point_size) * 0.6
        square = patches.Rectangle((x - square_size/2, y - square_size/2),
                                 square_size, square_size,
                                 facecolor='purple', edgecolor='white', linewidth=2, zorder=5)
        ax.add_patch(square)

    def _draw_unknown(self, ax, x: float, y: float, point_size: int = 70, **kwargs):
        """Dessine un cercle gris pour les objets de type inconnu"""
        ax.scatter(x, y, color='gray', s=point_size, zorder=5,
                  edgecolors='white', linewidth=1)

    def draw_object(self, ax, x: float, y: float, object_info: Dict, object_id: str, point_size: int = 70):
        """Dessine un objet sur le terrain"""
        object_type = object_info.get('type', 'unknown')
        draw_function = self.drawing_functions.get(object_type, self._draw_unknown)

        # Appeler la fonction avec les bons paramètres
        if object_type in ['ball', 'ballon']:
            draw_function(ax, x, y, point_size)
        elif object_type == 'player':
            draw_function(ax, x, y, object_info, point_size)
        else:
            draw_function(ax, x, y, point_size)

        # Afficher l'ID seulement pour les joueurs
        if self.should_display_id(object_info, ['player']):
            ax.text(x, y, str(object_id), color='white', fontsize=9,
                   ha='center', va='center', weight='bold', zorder=6)


class FootballField2D:
    """Classe pour dessiner un terrain de football en 2D"""

    def __init__(self, field_length=105, field_width=68, line_color='white',
                 background_color='#2d5a27', line_width=2):
        self.field_length = field_length
        self.field_width = field_width
        self.line_color = line_color
        self.background_color = background_color
        self.line_width = line_width

        # Dimensions standards
        self.penalty_length = 16.5
        self.penalty_width = 40.32
        self.goal_area_length = 5.5
        self.goal_area_width = 18.32
        self.center_circle_radius = 9.15
        self.penalty_spot_distance = 11
        self.goal_width = 7.32
        self.goal_depth = 1.5

        # Paramètres de transformation
        self.rotation = 0
        self.half_field = None
        self.invert_x = False
        self.invert_y = False

    def _rotate_coordinates(self, coords, rotation):
        """Applique une rotation aux coordonnées"""
        if rotation == 0:
            return coords
        elif rotation == 90:
            return np.column_stack([-coords[:, 1], coords[:, 0]])
        elif rotation == 180:
            return np.column_stack([-coords[:, 0], -coords[:, 1]])
        elif rotation == 270:
            return np.column_stack([coords[:, 1], -coords[:, 0]])
        else:
            raise ValueError("La rotation doit être 0, 90, 180 ou 270 degrés")

    def draw(self, ax=None, show_plot=True, figsize=(12, 8), rotation=0,
             half_field=None, invert_x=False, invert_y=True):
        """Dessine le terrain de football"""
        # Stocker les paramètres
        self.rotation = rotation
        self.half_field = half_field
        self.invert_x = invert_x
        self.invert_y = invert_y

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        ax.set_facecolor(self.background_color)

        # Dessiner tous les éléments
        self._draw_field_outline(ax)
        self._draw_center_line(ax)
        self._draw_center_circle(ax)
        self._draw_penalty_areas(ax)
        self._draw_goal_areas(ax)
        self._draw_penalty_spots(ax)
        self._draw_penalty_arcs(ax)
        self._draw_goals(ax)

        # Configuration des axes
        self._configure_axes(ax, rotation, half_field, invert_x, invert_y)

        if show_plot:
            plt.tight_layout()
            plt.show()

        return ax

    def _draw_field_outline(self, ax):
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

    def _draw_center_line(self, ax):
        """Dessine la ligne médiane"""
        center_line = np.array([
            [0, -self.field_width/2],
            [0, self.field_width/2]
        ])
        rotated_line = self._rotate_coordinates(center_line, self.rotation)
        ax.plot(rotated_line[:, 0], rotated_line[:, 1],
                color=self.line_color, linewidth=self.line_width)

    def _draw_center_circle(self, ax):
        """Dessine le cercle central et le point central"""
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

    def _draw_penalty_areas(self, ax):
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

    def _draw_goal_areas(self, ax):
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

    def _draw_penalty_spots(self, ax):
        """Dessine les points de penalty"""
        penalty_spots = np.array([
            [-self.field_length/2 + self.penalty_spot_distance, 0],
            [self.field_length/2 - self.penalty_spot_distance, 0]
        ])
        rotated_spots = self._rotate_coordinates(penalty_spots, self.rotation)
        ax.plot(rotated_spots[:, 0], rotated_spots[:, 1], 'o',
                color=self.line_color, markersize=3)

    def _draw_penalty_arcs(self, ax):
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

    def _draw_goals(self, ax):
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

    def _configure_axes(self, ax, rotation, half_field, invert_x, invert_y):
        """Configure les axes et l'apparence générale"""
        ax.set_aspect('equal')

        # Calculer les limites
        if rotation in [0, 180]:
            max_x = self.field_length/2 + 10
            max_y = self.field_width/2 + 10
        else:
            max_x = self.field_width/2 + 10
            max_y = self.field_length/2 + 10

        x_min, x_max = -max_x, max_x
        y_min, y_max = -max_y, max_y

        # Ajuster pour demi-terrain
        if half_field == 'left':
            if rotation == 0:
                x_max = 5
            elif rotation == 90:
                y_max = 5
            elif rotation == 180:
                x_min = -5
            elif rotation == 270:
                y_min = -5
        elif half_field == 'right':
            if rotation == 0:
                x_min = -5
            elif rotation == 90:
                y_min = -5
            elif rotation == 180:
                x_max = 5
            elif rotation == 270:
                y_max = 5

        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])

        if invert_x:
            ax.invert_xaxis()
        if invert_y:
            ax.invert_yaxis()

        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])


class VideoExporter:
    """Exporteur vidéo avec visualisations avancées"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Configuration minimap par défaut
        self.minimap_config = {
            'rotation': 0,
            'half_field': "null",
            'invert_x': False,
            'invert_y': True,
            'transparency': 0.65,
            'size': "35%",
            'position': 'lower center'
        }
        
        # Initialiser les classes de dessin du notebook
        self.field_drawer = FieldDrawer()
    
    def configure_minimap(self, **config):
        """Configure les paramètres de la minimap
        
        Args:
            **config: Paramètres de configuration disponibles:
                - rotation: Rotation du terrain (0, 90, 180, 270)
                - half_field: Affichage demi-terrain ('left', 'right', None)
                - invert_x: Inverser l'axe X (bool)
                - invert_y: Inverser l'axe Y (bool)
                - transparency: Transparence de la minimap (0.0-1.0)
                - size: Taille de la minimap (str, ex: "35%")
                - position: Position de la minimap (str, ex: 'lower center')
        
        Exemples:
            # Terrain tourné à 90° avec demi-terrain gauche
            exporter.configure_minimap(rotation=90, half_field='left')
            
            # Minimap plus transparente en haut à droite
            exporter.configure_minimap(transparency=0.3, position='upper right')
            
            # Inverser l'axe Y et changer la taille
            exporter.configure_minimap(invert_y=True, size="40%")
        """
        self.minimap_config.update(config)
        print(f"✅ Configuration minimap mise à jour: {config}")
    
    def get_minimap_config(self) -> Dict:
        """Retourne la configuration actuelle de la minimap"""
        return self.minimap_config.copy()
    
    def reset_minimap_config(self):
        """Remet la configuration de la minimap aux valeurs par défaut"""
        self.minimap_config = {
            'rotation': 0,
            'half_field': "null",
            'invert_x': False,
            'invert_y': True,
            'transparency': 0.65,
            'size': "35%",
            'position': 'lower center'
        }
        print("✅ Configuration minimap remise aux valeurs par défaut")
    
    def export_video(self, output_video_path: str = None, fps: int = 30, 
                    show_minimap: bool = True, figsize: Tuple[int, int] = (15, 8), 
                    dpi: int = 100, cleanup_frames: bool = True,
                    force_regenerate: bool = False) -> bool:
        """
        Exporte toutes les frames en vidéo avec annotations
        
        Args:
            output_video_path: Chemin de sortie pour la vidéo
            fps: Frames par seconde de la vidéo
            show_minimap: Afficher la minimap sur chaque frame
            figsize: Taille des figures
            dpi: Résolution des images
            cleanup_frames: Supprimer les frames temporaires après création
            force_regenerate: Forcer la régénération des frames
        
        Returns:
            bool: True si succès, False sinon
        """
        
        # Définir le chemin de sortie par défaut
        if output_video_path is None:
            output_video_path = str(self.config.output_dir / f"{self.config.VIDEO_NAME}_annotated.mp4")
        
        # Créer le dossier pour les frames temporaires
        temp_frames_dir = self.config.output_dir / "temp_annotated_frames"
        temp_frames_dir.mkdir(exist_ok=True)
        
        print(f"🎬 Démarrage de l'export vidéo...")
        print(f"📁 Frames temporaires: {temp_frames_dir}")
        print(f"🎥 Vidéo de sortie: {output_video_path}")
        
        try:
            # Charger le projet et obtenir toutes les frames
            project = self._load_project_data()
            available_frames = list(project['annotations'].keys())
            available_frames = [f for f in available_frames if f.isdigit()]
            available_frames.sort(key=int)  # Trier numériquement
            
            if not available_frames:
                print("❌ Aucune frame disponible pour l'export")
                return False
            
            print(f"📊 {len(available_frames)} frames à traiter")
            
            # Générer les frames annotées
            successful_frames = 0
            failed_frames = []
            
            for frame_id in tqdm(available_frames, desc="🖼️ Génération des frames"):
                output_frame_path = temp_frames_dir / f"frame_{int(frame_id):05d}.png"
                
                # Vérifier si la frame existe déjà
                if output_frame_path.exists() and not force_regenerate:
                    successful_frames += 1
                    continue
                
                if self._visualize_frame_to_file(frame_id, str(output_frame_path), 
                                               show_minimap, figsize, dpi, project):
                    successful_frames += 1
                else:
                    failed_frames.append(frame_id)
            
            print(f"✅ Frames générées: {successful_frames}/{len(available_frames)}")
            
            if failed_frames:
                print(f"⚠️ Frames échouées: {failed_frames}")
            
            if successful_frames == 0:
                print("❌ Aucune frame n'a pu être générée")
                return False
            
            # Créer la vidéo à partir des frames
            success = self._create_video_from_frames(str(temp_frames_dir), output_video_path, fps)
            
            # Nettoyer les frames temporaires si demandé
            if cleanup_frames and success:
                import shutil
                shutil.rmtree(temp_frames_dir)
                print("🧹 Frames temporaires supprimées")
            elif not cleanup_frames:
                print(f"💾 Frames conservées dans: {temp_frames_dir}")
            
            if success:
                print(f"🎉 Export vidéo terminé avec succès!")
                print(f"📹 Vidéo sauvegardée: {output_video_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export vidéo: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_project_data(self) -> Dict:
        """Charge les données du projet depuis le fichier JSON"""
        with open(self.config.output_json_path) as f:
            return json.load(f)
    
    def _load_frame_image(self, frame_id: str) -> Image.Image:
        """Charge l'image d'une frame"""
        image_path_jpg = self.config.frames_dir / f"{int(frame_id):05d}.jpg"
        image_path_jpeg = self.config.frames_dir / f"{int(frame_id):05d}.jpeg"
        
        if image_path_jpg.exists():
            return Image.open(image_path_jpg)
        elif image_path_jpeg.exists():
            return Image.open(image_path_jpeg)
        else:
            print(f"⚠️ Image non trouvée: {image_path_jpg}")
            return Image.new('RGB', (1920, 1080), color='black')
    
    def _visualize_frame_to_file(self, frame_id: str, output_path: str, 
                                show_minimap: bool, figsize: Tuple[int, int], 
                                dpi: int, project: Dict) -> bool:
        """Visualise une frame et la sauvegarde dans un fichier"""
        
        try:
            # Charger les données
            objects_config = project.get('objects', {})
            frame_annotations = project['annotations'][frame_id]
            img = self._load_frame_image(frame_id)
            
            # Extraire les données
            x_coords, y_coords, object_ids, object_infos = self._extract_image_points(
                frame_annotations, objects_config)
            
            # Créer la figure principale
            fig, ax_main = plt.subplots(figsize=figsize, dpi=dpi)
            ax_main.imshow(img)
            ax_main.axis('off')
            
            # Dessiner les objets sur l'image
            self._draw_image_objects(ax_main, x_coords, y_coords, object_ids, object_infos)
            
            # Ajouter la minimap si demandée
            if show_minimap:
                field_points = self._extract_field_points(frame_annotations, objects_config)
                if field_points:
                    self._create_minimap(ax_main, field_points, frame_id, len(frame_annotations))
            
            # Sauvegarder la figure
            plt.tight_layout()
            plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=dpi)
            plt.close(fig)  # Fermer la figure pour libérer la mémoire
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de la frame {frame_id}: {e}")
            return False
    
    def _extract_image_points(self, frame_annotations: List, objects_config: Dict) -> Tuple[List, List, List, List]:
        """Extrait les coordonnées image avec les informations des objets"""
        x_coords, y_coords, object_ids, object_infos = [], [], [], []
        
        for annotation in frame_annotations:
            if not annotation or 'points' not in annotation:
                continue
            
            output = annotation['points'].get('output')
            if not output:
                continue
            
            image_points = output.get('image', {})
            center_bottom = image_points.get('CENTER_BOTTOM')
            
            if center_bottom and 'x' in center_bottom and 'y' in center_bottom:
                x_coords.append(center_bottom['x'])
                y_coords.append(center_bottom['y'])
                
                object_id = annotation['objectId']
                object_ids.append(object_id)
                object_infos.append(objects_config.get(str(object_id), {}))
        
        return x_coords, y_coords, object_ids, object_infos
    
    def _extract_field_points(self, frame_annotations: List, objects_config: Dict) -> Dict:
        """Extrait les coordonnées terrain avec les informations des objets"""
        field_points = {}
        
        for annotation in frame_annotations:
            if not annotation or 'points' not in annotation:
                continue
            
            output = annotation['points'].get('output')
            if not output:
                continue
            
            field_points_data = output.get('field', {})
            center_bottom = field_points_data.get('CENTER_BOTTOM')
            
            if center_bottom and isinstance(center_bottom, dict):
                object_id = annotation['objectId']
                field_points[object_id] = {
                    'x': center_bottom['x'],
                    'y': center_bottom['y'],
                    'info': objects_config.get(str(object_id), {})
                }
        
        return field_points
    
    def _draw_image_objects(self, ax, x_coords: List, y_coords: List, 
                           object_ids: List, object_infos: List):
        """Dessine tous les objets sur l'image avec la logique du notebook"""
        for x, y, obj_id, obj_info in zip(x_coords, y_coords, object_ids, object_infos):
            self._draw_single_object(ax, x, y, obj_id, obj_info)
    
    def _draw_single_object(self, ax, x: float, y: float, object_id: str, object_info: Dict):
        """Dessine un objet sur l'image selon son type"""
        object_type = object_info.get('type', 'unknown')
        color = self._get_object_color(object_info)
        
        # Dessiner la forme selon le type
        if object_type == 'player':
            self._draw_player(ax, x, y, color)
        elif object_type in ['ballon', 'ball']:
            self._draw_ball(ax, x, y)
        elif object_type in ['arbitre', 'referee']:
            self._draw_referee(ax, x, y, color)
        elif object_type == 'staff':
            self._draw_staff(ax, x, y, color)
        else:
            self._draw_unknown(ax, x, y, color)
        
        # Afficher l'ID si nécessaire
        if self._should_display_id(object_info):
            self._draw_annotation(ax, x, y, object_id, color)
    
    def _get_object_color(self, object_info: Dict) -> str:
        """Récupère la couleur appropriée pour un objet"""
        object_type = object_info.get('type', 'unknown')
        
        if object_type == 'player':
            return object_info.get('jersey_color') or object_info.get('display_color', 'red')
        else:
            return object_info.get('display_color', 'blue')
    
    def _should_display_id(self, object_info: Dict) -> bool:
        """Détermine si l'ID doit être affiché selon le type d'objet"""
        object_type = object_info.get('type', 'unknown')
        return object_type not in ['ballon', 'ball']
    
    def _draw_player(self, ax, x: float, y: float, color: str = 'red'):
        """Dessine les arcs de cercle pour un joueur"""
        ellipse_width, ellipse_height = 50, 20
        gap_size = 120
        arc_linewidth = 2
        
        for gap_center in [90, 270]:  # Haut et bas
            other_gap = 270 if gap_center == 90 else 90
            gap_start = gap_center - gap_size // 2
            gap_end = gap_center + gap_size // 2
            other_start = other_gap - gap_size // 2
            other_end = other_gap + gap_size // 2
            
            arc = patches.Arc((x, y-5), width=ellipse_width, height=ellipse_height,
                            angle=0, theta1=gap_end, theta2=other_start + (360 if other_start < gap_end else 0),
                            color=color, linewidth=arc_linewidth)
            ax.add_patch(arc)
    
    def _draw_ball(self, ax, x: float, y: float):
        """Dessine un triangle jaune pour le ballon"""
        triangle_size = 15
        triangle = patches.Polygon(
            [(x, y-20), (x-triangle_size, y-35), (x+triangle_size, y-35)],
            closed=True, facecolor='yellow', edgecolor='yellow', linewidth=2
        )
        ax.add_patch(triangle)
    
    def _draw_referee(self, ax, x: float, y: float, color: str = 'black'):
        """Dessine un losange pour l'arbitre"""
        diamond_size = 12
        diamond = patches.Polygon(
            [(x, y-5-diamond_size), (x+diamond_size, y-5),
             (x, y-5+diamond_size), (x-diamond_size, y-5)],
            closed=True, facecolor=color, edgecolor='white', linewidth=2
        )
        ax.add_patch(diamond)
    
    def _draw_staff(self, ax, x: float, y: float, color: str = 'purple'):
        """Dessine un carré pour le staff"""
        square_size = 10
        square = patches.Rectangle(
            (x-square_size, y-5-square_size), square_size*2, square_size*2,
            facecolor=color, edgecolor='white', linewidth=2
        )
        ax.add_patch(square)
    
    def _draw_unknown(self, ax, x: float, y: float, color: str = 'blue'):
        """Dessine un cercle pour les objets de type inconnu"""
        circle = patches.Circle((x, y-5), radius=10,
                              facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(circle)
    
    def _draw_annotation(self, ax, x: float, y: float, object_id: str, color: str):
        """Dessine l'annotation (ID) pour un objet"""
        ax.annotate(f'{object_id}', (x, y+5), xytext=(0, 0),
                   textcoords='offset points', fontsize=10, ha='center', va='center',
                   color='white', weight='bold',
                   bbox=dict(boxstyle="round,pad=0.2,rounding_size=0.5",
                           facecolor=color, alpha=0.7, edgecolor=color))
    
    def _create_minimap(self, ax_main, field_points: Dict, frame_id: str, total_objects: int):
        """Crée la minimap avec le terrain et les objets (version notebook)"""
        config = self.minimap_config
        
        # Créer l'axe inset pour la minimap
        inset_ax = inset_axes(ax_main, width=config['size'], height=config['size'],
                             loc=config['position'], borderpad=0.5)
        inset_ax.patch.set_alpha(config['transparency'])
        
        # Créer le terrain avec la classe du notebook
        field = FootballField2D(line_color='white', background_color='black', line_width=1.5)
        field.draw(ax=inset_ax, show_plot=False,
                  rotation=config['rotation'], half_field=config['half_field'],
                  invert_x=config['invert_x'], invert_y=config['invert_y'])
        
        # Dessiner les objets sur le terrain
        self._draw_field_objects(inset_ax, field, field_points)
        
        # Configuration finale
        visible_count = len(field_points)
        title = f'Frame {frame_id} - {visible_count}/{total_objects} objets projetés'
        inset_ax.set_title(title, fontsize=10, color='white', pad=8)
    
    def _draw_field_objects(self, ax, field: FootballField2D, field_points: Dict):
        """Dessine tous les objets sur le terrain"""
        for obj_id, point_data in field_points.items():
            # Appliquer la rotation aux coordonnées
            original_coords = np.array([[point_data['x'], point_data['y']]])
            rotated_coords = field._rotate_coordinates(original_coords, field.rotation)
            x, y = rotated_coords[0]
            
            # Dessiner l'objet
            self.field_drawer.draw_object(ax, x, y, point_data['info'], obj_id, point_size=150)
    
    def _create_video_from_frames(self, frames_dir: str, output_video_path: str, fps: int = 30) -> bool:
        """Crée une vidéo à partir des images annotées"""
        try:
            # Lister toutes les images
            image_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
            
            if not image_files:
                print("❌ Aucune image trouvée dans le dossier")
                return False
            
            # Lire la première image pour obtenir les dimensions
            first_image_path = os.path.join(frames_dir, image_files[0])
            first_image = cv2.imread(first_image_path)
            
            if first_image is None:
                print(f"❌ Impossible de lire l'image: {first_image_path}")
                return False
            
            height, width, layers = first_image.shape
            
            # Créer le writer vidéo
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
            
            if not video_writer.isOpened():
                print("❌ Impossible de créer le writer vidéo")
                return False
            
            print(f"🎬 Création de la vidéo avec {len(image_files)} frames...")
            
            # Ajouter chaque image à la vidéo
            for image_file in tqdm(image_files, desc="🎞️ Assemblage vidéo"):
                image_path = os.path.join(frames_dir, image_file)
                frame = cv2.imread(image_path)
                
                if frame is not None:
                    video_writer.write(frame)
                else:
                    print(f"⚠️ Impossible de lire: {image_file}")
            
            # Finaliser la vidéo
            video_writer.release()
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de la vidéo: {e}")
            return False
    
    def get_export_stats(self) -> Dict:
        """Retourne des statistiques sur les données disponibles pour l'export"""
        try:
            project = self._load_project_data()
            available_frames = list(project['annotations'].keys())
            available_frames = [f for f in available_frames if f.isdigit()]
            
            # Compter les objets par frame
            total_objects = 0
            for frame_id in available_frames:
                frame_annotations = project['annotations'][frame_id]
                objects_count = len([ann for ann in frame_annotations if ann is not None])
                total_objects += objects_count
            
            stats = {
                'total_frames': len(available_frames),
                'total_objects': total_objects,
                'avg_objects_per_frame': total_objects / len(available_frames) if available_frames else 0,
                'objects_config': len(project.get('objects', {})),
                'frames_range': f"{min(available_frames)}-{max(available_frames)}" if available_frames else "N/A"
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur lors du calcul des statistiques: {e}")
            return {}