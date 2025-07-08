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


class VideoExporter:
    """Exporteur vidéo avec visualisations avancées"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Configuration minimap par défaut
        self.minimap_config = {
            'rotation': 90,
            'half_field': 'right',
            'invert_x': False,
            'invert_y': True,
            'transparency': 0.65,
            'size': "35%",
            'position': 'lower center'
        }
    
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
        """Dessine tous les objets sur l'image (version simplifiée)"""
        for x, y, obj_id, obj_info in zip(x_coords, y_coords, object_ids, object_infos):
            # Dessiner un cercle simple pour chaque objet
            color = obj_info.get('display_color', 'red')
            circle = patches.Circle((x, y), radius=15, facecolor=color, 
                                  edgecolor='white', linewidth=2)
            ax.add_patch(circle)
            
            # Ajouter l'ID
            ax.text(x, y, str(obj_id), ha='center', va='center', 
                   fontsize=10, color='white', weight='bold')
    
    def _create_minimap(self, ax_main, field_points: Dict, frame_id: str, total_objects: int):
        """Crée la minimap simplifiée"""
        # Version simplifiée - juste ajouter du texte pour l'instant
        ax_main.text(0.02, 0.02, f'Frame {frame_id} - {len(field_points)} objets', 
                    transform=ax_main.transAxes, fontsize=12, color='white',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
    
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