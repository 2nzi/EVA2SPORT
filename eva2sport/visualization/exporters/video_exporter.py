"""
Exporteur vidéo refactorisé utilisant l'architecture modulaire
"""

import os
import json
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from typing import Dict, List, Tuple, Optional, Any
import cv2
from tqdm import tqdm

from ...config import Config
from ..config.visualization_config import VisualizationConfig
from ..config.minimap_config import MinimapConfig
from ..objects.object_renderer_factory import ObjectRendererFactory
from ..field.field_drawer import FieldDrawer

class VideoExporter:
    """Exporteur vidéo avec architecture modulaire"""
    
    def __init__(self, config: Config, visualization_config: Optional[VisualizationConfig] = None):
        """
        Initialise l'exporteur vidéo
        
        Args:
            config: Configuration du projet
            visualization_config: Configuration de visualisation (optionnel)
        """
        self.config = config
        self.visualization_config = visualization_config or VisualizationConfig.get_default()
        
        # Initialiser les composants
        self.renderer_factory = ObjectRendererFactory(self.visualization_config)
        self.field_drawer = FieldDrawer(self.visualization_config)
    
    def configure_visualization(self, **kwargs) -> None:
        """
        Configure les paramètres de visualisation
        
        Args:
            **kwargs: Paramètres de configuration
        """
        # Créer une nouvelle configuration
        new_config = self.visualization_config.copy()
        
        # Mettre à jour les paramètres généraux
        for key, value in kwargs.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
        
        # Appliquer la nouvelle configuration
        self.visualization_config = new_config
        self._update_components()
    
    def configure_minimap(self, **kwargs) -> None:
        """
        Configure les paramètres de la minimap
        
        Args:
            **kwargs: Paramètres de configuration minimap
        """
        self.visualization_config = self.visualization_config.update_minimap(**kwargs)
        self._update_components()
    
    def _update_components(self) -> None:
        """Met à jour tous les composants avec la nouvelle configuration"""
        self.renderer_factory.update_config(self.visualization_config)
        self.field_drawer.update_config(self.visualization_config)
    
    def export_video(self, output_video_path: Optional[str] = None) -> bool:
        """
        Exporte toutes les frames en vidéo avec annotations
        
        Args:
            output_video_path: Chemin de sortie pour la vidéo
            
        Returns:
            True si succès, False sinon
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
            available_frames = self._get_available_frames(project)
            
            if not available_frames:
                print("❌ Aucune frame disponible pour l'export")
                return False
            
            print(f"📊 {len(available_frames)} frames à traiter")
            
            # Générer les frames annotées
            successful_frames = self._generate_annotated_frames(
                project, available_frames, temp_frames_dir
            )
            
            if successful_frames == 0:
                print("❌ Aucune frame n'a pu être générée")
                return False
            
            print(f"✅ Frames générées: {successful_frames}/{len(available_frames)}")
            
            # Créer la vidéo à partir des frames
            success = self._create_video_from_frames(
                str(temp_frames_dir), output_video_path
            )
            
            # Nettoyer si demandé
            if self.visualization_config.cleanup_frames and success:
                import shutil
                shutil.rmtree(temp_frames_dir)
                print("🧹 Frames temporaires supprimées")
            elif not self.visualization_config.cleanup_frames:
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
    
    def _get_available_frames(self, project: Dict) -> List[str]:
        """Récupère la liste des frames disponibles"""
        available_frames = list(project['annotations'].keys())
        available_frames = [f for f in available_frames if f.isdigit()]
        available_frames.sort(key=int)
        return available_frames
    
    def _generate_annotated_frames(self, project: Dict, available_frames: List[str], 
                                  temp_frames_dir: Path) -> int:
        """Génère toutes les frames annotées"""
        successful_frames = 0
        failed_frames = []
        
        for frame_id in tqdm(available_frames, desc="🖼️ Génération des frames"):
            output_frame_path = temp_frames_dir / f"frame_{int(frame_id):05d}.png"
            
            # Vérifier si la frame existe déjà
            if output_frame_path.exists() and not self.visualization_config.force_regenerate:
                successful_frames += 1
                continue
            
            if self._generate_single_frame(frame_id, str(output_frame_path), project):
                successful_frames += 1
            else:
                failed_frames.append(frame_id)
        
        if failed_frames:
            print(f"⚠️ Frames échouées: {failed_frames}")
        
        return successful_frames
    
    def _generate_single_frame(self, frame_id: str, output_path: str, project: Dict) -> bool:
        """Génère une frame annotée"""
        try:
            # Charger les données
            objects_config = project.get('objects', {})
            frame_annotations = project['annotations'][frame_id]
            img = self._load_frame_image(frame_id)
            
            # Créer la figure principale
            fig, ax_main = plt.subplots(
                figsize=self.visualization_config.figsize,
                dpi=self.visualization_config.dpi
            )
            ax_main.imshow(img)
            ax_main.axis('off')
            
            # Dessiner les objets sur l'image
            self._draw_objects_on_image(ax_main, frame_annotations, objects_config)
            
            # Ajouter la minimap si demandée
            if self.visualization_config.show_minimap:
                self._create_minimap(ax_main, frame_annotations, objects_config, frame_id)
            
            # Sauvegarder la figure
            plt.tight_layout()
            plt.savefig(
                output_path,
                bbox_inches='tight',
                pad_inches=0,
                dpi=self.visualization_config.dpi
            )
            plt.close(fig)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de la frame {frame_id}: {e}")
            return False
    
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
    
    def _draw_objects_on_image(self, ax: plt.Axes, frame_annotations: List, 
                              objects_config: Dict) -> None:
        """Dessine tous les objets sur l'image"""
        for annotation in frame_annotations:
            if not annotation or 'points' not in annotation:
                continue
            
            output = annotation['points'].get('output')
            if not output:
                continue
            
            image_points = output.get('image', {})
            center_bottom = image_points.get('CENTER_BOTTOM')
            
            if center_bottom and 'x' in center_bottom and 'y' in center_bottom:
                x, y = center_bottom['x'], center_bottom['y']
                object_id = annotation['objectId']
                object_info = objects_config.get(str(object_id), {})
                
                # Utiliser la factory pour dessiner l'objet
                self.renderer_factory.render_object_on_image(ax, x, y, object_id, object_info)
    
    def _create_minimap(self, ax_main: plt.Axes, frame_annotations: List, 
                       objects_config: Dict, frame_id: str) -> None:
        """Crée la minimap avec le terrain et les objets"""
        # Extraire les points du terrain
        field_points = self._extract_field_points(frame_annotations, objects_config)
        
        if not field_points:
            return
        
        # Créer l'axe inset pour la minimap
        minimap_config = self.visualization_config.minimap_config
        inset_ax = inset_axes(
            ax_main,
            width=minimap_config.size,
            height=minimap_config.size,
            loc=minimap_config.position,
            borderpad=0.5
        )
        inset_ax.patch.set_alpha(minimap_config.transparency)
        
        # Dessiner le terrain avec les objets
        self.field_drawer.draw_field_with_objects(inset_ax, field_points)
        
        # Ajouter le titre
        visible_count = len(field_points)
        total_count = len(frame_annotations)
        # title = f'Frame {frame_id} - {visible_count}/{total_count} objets projetés'
        title = f''
        inset_ax.set_title(title, fontsize=10, color='white', pad=8)
    
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
    
    def _create_video_from_frames(self, frames_dir: str, output_video_path: str) -> bool:
        """Crée une vidéo à partir des images annotées avec codec H.264 pour compatibilité web"""
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
            
            # S'assurer que les dimensions sont paires (requis pour H.264)
            if width % 2 != 0:
                width -= 1
            if height % 2 != 0:
                height -= 1
            
            # Utiliser H.264 pour une meilleure compatibilité web
            success = self._try_create_video_h264(image_files, frames_dir, output_video_path, width, height)
            
            if not success:
                print("⚠️ H.264 non disponible, utilisation de mp4v comme fallback...")
                success = self._try_create_video_fallback(image_files, frames_dir, output_video_path, width, height)
            
            return success
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de la vidéo: {e}")
            return False
    
    def _try_create_video_h264(self, image_files: List[str], frames_dir: str, 
                              output_video_path: str, width: int, height: int) -> bool:
        """Tente de créer la vidéo avec le codec H.264"""
        # Utiliser la priorité de codecs configurée
        codec_priority = list(self.visualization_config.video_codec_priority)
        # Filtrer pour ne garder que les codecs H.264
        h264_codecs = [c for c in codec_priority if c in ['avc1', 'h264', 'H264']]
        
        if not h264_codecs:
            h264_codecs = ['avc1', 'h264', 'H264']  # Fallback
        
        print(f"🎯 Tentative H.264 avec qualité '{self.visualization_config.video_quality}'")
        if self.visualization_config.video_bitrate:
            print(f"📊 Bitrate cible: {self.visualization_config.video_bitrate} kbps")
        
        for codec_name in h264_codecs:
            try:
                print(f"🔧 Test codec: {codec_name}")
                fourcc = cv2.VideoWriter_fourcc(*codec_name)
                
                # Paramètres selon la qualité
                video_params = self._get_video_params_for_quality()
                
                video_writer = cv2.VideoWriter(
                    output_video_path, fourcc, self.visualization_config.fps, 
                    (width, height), **video_params
                )
                
                if video_writer.isOpened():
                    print(f"✅ Codec H.264 '{codec_name}' initialisé")
                    success = self._write_frames_to_video(video_writer, image_files, frames_dir, width, height)
                    video_writer.release()
                    
                    if success:
                        file_size = self._get_file_size_mb(output_video_path)
                        print(f"🎉 Vidéo H.264 créée avec succès!")
                        print(f"🏷️ Codec: {codec_name}, Qualité: {self.visualization_config.video_quality}")
                        print(f"📁 Taille: {file_size:.1f} MB")
                        return True
                else:
                    video_writer.release()
                    
            except Exception as e:
                print(f"❌ Codec '{codec_name}' non disponible: {e}")
                continue
        
        return False
    
    def _get_video_params_for_quality(self) -> Dict:
        """Retourne les paramètres vidéo selon la qualité configurée"""
        # OpenCV a des limitations sur les paramètres avancés
        # Ces paramètres sont principalement informatifs pour l'utilisateur
        quality_settings = {
            'low': {'quality_hint': 'Optimisé pour la taille de fichier'},
            'medium': {'quality_hint': 'Équilibre qualité/taille'},
            'high': {'quality_hint': 'Haute qualité'},
            'ultra': {'quality_hint': 'Qualité maximale'}
        }
        
        params = quality_settings.get(self.visualization_config.video_quality, {})
        
        # Log des paramètres pour information
        if params.get('quality_hint'):
            print(f"⚙️ {params['quality_hint']}")
        
        # OpenCV ne supporte pas beaucoup de paramètres avancés
        # mais nous pouvons au moins retourner des paramètres de base
        return {}
    
    def _get_file_size_mb(self, file_path: str) -> float:
        """Retourne la taille du fichier en MB"""
        try:
            import os
            return os.path.getsize(file_path) / (1024 * 1024)
        except:
            return 0.0
    
    def _try_create_video_fallback(self, image_files: List[str], frames_dir: str,
                                  output_video_path: str, width: int, height: int) -> bool:
        """Crée la vidéo avec un codec de fallback"""
        try:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                output_video_path, fourcc, self.visualization_config.fps, (width, height)
            )
            
            if not video_writer.isOpened():
                print("❌ Impossible de créer le writer vidéo même avec mp4v")
                return False
            
            success = self._write_frames_to_video(video_writer, image_files, frames_dir, width, height)
            video_writer.release()
            return success
            
        except Exception as e:
            print(f"❌ Erreur avec codec fallback: {e}")
            return False
    
    def _write_frames_to_video(self, video_writer: cv2.VideoWriter, image_files: List[str],
                              frames_dir: str, width: int, height: int) -> bool:
        """Écrit toutes les frames dans la vidéo"""
        print(f"🎬 Création de la vidéo avec {len(image_files)} frames ({width}x{height})...")
        
        for image_file in tqdm(image_files, desc="🎞️ Assemblage vidéo"):
            image_path = os.path.join(frames_dir, image_file)
            frame = cv2.imread(image_path)
            
            if frame is not None:
                # Redimensionner si nécessaire pour s'assurer des bonnes dimensions
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
                
                video_writer.write(frame)
            else:
                print(f"⚠️ Impossible de lire: {image_file}")
                return False
        
        return True
    
    def get_export_stats(self) -> Dict:
        """Retourne des statistiques sur les données disponibles pour l'export"""
        try:
            project = self._load_project_data()
            available_frames = self._get_available_frames(project)
            
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
                'frames_range': f"{min(available_frames)}-{max(available_frames)}" if available_frames else "N/A",
                'visualization_config': self.visualization_config.to_dict()
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur lors du calcul des statistiques: {e}")
            return {}
    
    def get_supported_object_types(self) -> List[str]:
        """Retourne les types d'objets supportés"""
        return self.renderer_factory.get_supported_types()
    
    def get_current_config(self) -> Dict:
        """Retourne la configuration actuelle"""
        return self.visualization_config.to_dict()
    
    @classmethod
    def create_with_preset(cls, config: Config, preset: str) -> 'VideoExporter':
        """
        Crée un VideoExporter avec une configuration prédéfinie
        
        Args:
            config: Configuration du projet
            preset: Nom du preset
                - 'default': Configuration standard
                - 'high_quality': Export haute qualité (H.264 Ultra, 8 Mbps)
                - 'fast_preview': Aperçu rapide (H.264 Low, 1 Mbps)
                - 'tactical_analysis': Analyse tactique (H.264 High, 4 Mbps)
                - 'web_optimized': Optimisé pour le web (H.264 Medium, 2.5 Mbps)
            
        Returns:
            Instance de VideoExporter configurée
        """
        preset_map = {
            'default': VisualizationConfig.get_default,
            'high_quality': VisualizationConfig.get_high_quality,
            'fast_preview': VisualizationConfig.get_fast_preview,
            'tactical_analysis': VisualizationConfig.get_tactical_analysis,
            'web_optimized': VisualizationConfig.get_web_optimized
        }
        
        if preset not in preset_map:
            raise ValueError(f"Preset inconnu: {preset}. Disponibles: {list(preset_map.keys())}")
        
        visualization_config = preset_map[preset]()
        print(f"🎬 Configuration '{preset}' chargée:")
        print(f"   📐 Résolution: {visualization_config.figsize} @ {visualization_config.dpi} DPI")
        print(f"   🎞️ FPS: {visualization_config.fps}")
        print(f"   🏷️ Qualité: {visualization_config.video_quality}")
        if visualization_config.video_bitrate:
            print(f"   📊 Bitrate: {visualization_config.video_bitrate} kbps")
        
        return cls(config, visualization_config) 