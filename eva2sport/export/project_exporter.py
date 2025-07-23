"""
Exporteur de projets EVA2SPORT - Version Simplifiée
"""

import json
import uuid
import colorsys
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from ..config import Config


class ProjectExporter:
    """Exporteur pour sauvegarder et visualiser les projets"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def save_project_json(self, project_data: Dict[str, Any], 
                         compact: bool = False) -> Path:
        """Sauvegarde le projet au format JSON"""
        
        print(f"💾 Sauvegarde du projet JSON...")
        
        # Sauvegarde principale (formatée)
        json_path = self.config.output_json_path
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarde compacte optionnelle
        if compact:
            compact_path = json_path.with_suffix('.compact.json')
            with open(compact_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, separators=(',', ':'), ensure_ascii=False)
        
        # Statistiques
        file_size = json_path.stat().st_size / 1024  # KB
        print(f"   📄 JSON sauvé: {json_path}")
        print(f"   💾 Taille: {file_size:.1f} KB")
        
        return json_path
    
    def create_visualizations(self, project_data: Dict[str, Any]) -> Dict[str, Path]:
        """Crée les visualisations du projet"""
        viz_paths = {}
        
        # Rapport texte
        report_path = self._create_text_report(project_data)
        viz_paths['report'] = report_path
        
        return viz_paths
    
    def display_final_statistics(self, project_data: Dict[str, Any]) -> None:
        """Affiche les statistiques finales"""
        
        total_annotations = sum(len(annotations) for annotations in project_data['annotations'].values())
        frames_with_annotations = len(project_data['annotations'])
        
        print(f"\n📊 STATISTIQUES FINALES:")
        print(f"   🎬 Frames traitées: {frames_with_annotations}")
        print(f"   🎯 Annotations totales: {total_annotations}")
        print(f"   📊 Moyenne par frame: {total_annotations / frames_with_annotations:.1f}")
        
        # Statistiques par type d'objet
        type_counts = {}
        for annotations in project_data['annotations'].values():
            for annotation in annotations:
                obj_id = annotation['objectId']
                obj_type = project_data['objects'][obj_id]['type']
                type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        
        print(f"   🏷️  Par type: {dict(type_counts)}")
    
    def _create_text_report(self, project_data: Dict[str, Any]) -> Path:
        """Crée un rapport texte du projet"""
        
        report_path = self.config.output_dir / f"{self.config.VIDEO_NAME_WITH_EVENT}_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"📊 RAPPORT EVA2SPORT - {self.config.VIDEO_NAME}\n")
            f.write("=" * 50 + "\n\n")
            
            # Métadonnées
            metadata = project_data['metadata']
            f.write(f"🎬 Vidéo: {project_data['video']}\n")
            f.write(f"📅 Créé: {metadata['created_at']}\n")
            f.write(f"⏯️  FPS: {metadata['fps']}\n")
            f.write(f"📐 Résolution: {metadata['resolution']['width']}x{metadata['resolution']['height']}\n")
            f.write(f"🎯 Frames originales: {metadata['frame_count_original']}\n")
            f.write(f"🎬 Frames traitées: {metadata['frame_count_processed']}\n")
            f.write(f"⏯️  Intervalle: {metadata['frame_interval']}\n\n")
            
            # Objets
            f.write(f"👥 OBJETS SUIVIS ({len(project_data['objects'])} total):\n")
            f.write("-" * 30 + "\n")
            for obj_id, obj_data in project_data['objects'].items():
                f.write(f"  🎯 ID {obj_id}: {obj_data['type']}")
                if obj_data.get('team'):
                    f.write(f" (Équipe: {obj_data['team']})")
                if obj_data.get('jersey_number'):
                    f.write(f" (N°{obj_data['jersey_number']})")
                f.write(f"\n")
            
            # Statistiques annotations
            total_annotations = sum(len(annotations) for annotations in project_data['annotations'].values())
            f.write(f"\n🎯 ANNOTATIONS ({total_annotations} total):\n")
            f.write("-" * 30 + "\n")
            f.write(f"  📊 Frames avec annotations: {len(project_data['annotations'])}\n")
            f.write(f"  📊 Moyenne par frame: {total_annotations / len(project_data['annotations']):.1f}\n")
            
            f.write(f"\n")
        
        print(f"   📄 Rapport créé: {report_path}")
        return report_path

    def create_project_structure(self, project_config: Dict[str, Any], 
                               added_objects: List[Dict]) -> Dict[str, Any]:
        """Crée la structure JSON du projet depuis la configuration"""
        
        # Informations vidéo
        video_info = self._get_video_info()
        
        # Frame d'ancrage
        anchor_frame = self._get_anchor_frame(project_config)
        
        # Mapping des frames
        frame_mapping, processed_frames = self._generate_frame_mapping(
            video_info['total_frames'], anchor_frame
        )
        
        # Structure des objets avec couleurs
        objects = self._create_objects_structure(project_config, added_objects)
        
        return {
            "format_version": "1.0",
            "video": f"{self.config.VIDEO_NAME}.mp4",
            "metadata": {
                "project_id": str(uuid.uuid4()),
                "created_at": datetime.now().isoformat() + "Z",
                "fps": video_info['fps'],
                "resolution": {
                    "width": video_info['width'],
                    "height": video_info['height'],
                    "aspect_ratio": round(video_info['width'] / video_info['height'], 2)
                },
                "frame_interval": self.config.FRAME_INTERVAL,
                "frame_count_original": video_info['total_frames'],
                "frame_count_processed": len(processed_frames),
                "frame_mapping": frame_mapping,
                "anchor_frame": anchor_frame,
                "static_video": False
            },
            "calibration": project_config['calibration'],
            "objects": objects,
            "initial_annotations": project_config['initial_annotations'],
            "annotations": {}
        }
    
    # ===== MÉTHODES AUXILIAIRES DÉPLACÉES =====
    
    def _get_video_info(self) -> Dict[str, Any]:
        """Récupère les informations de la vidéo (utilise la méthode centralisée)"""
        return self.config.get_video_info()
    
    def _get_anchor_frame(self, project_config: Dict[str, Any]) -> int:
        """Récupère la frame d'ancrage depuis la configuration"""
        if not project_config.get('initial_annotations'):
            return 0
        
        # Utiliser la méthode centralisée pour sélectionner l'annotation la plus proche
        reference_frame = self.config.get_closest_initial_annotation_frame(
            project_config['initial_annotations']
        )
        
        # Utiliser la méthode centralisée pour calculer les bornes et l'ancrage (sans logs répétés)
        _, _, anchor_frame_in_segment = self.config.calculate_segment_bounds_and_anchor(reference_frame, verbose=False)
        
        return anchor_frame_in_segment
            
    def _generate_frame_mapping(self, total_frames: int, anchor_frame: int) -> Tuple[List[Optional[int]], List[int]]:
        """Génère le mapping frame_originale → frame_traitée"""
        frame_mapping = [None] * total_frames
        processed_frames = set()
        processed_idx = 0
        
        # S'assurer que anchor_frame est incluse
        if 0 <= anchor_frame * self.config.FRAME_INTERVAL < total_frames:
            frame_mapping[anchor_frame * self.config.FRAME_INTERVAL] = processed_idx
            processed_frames.add(anchor_frame * self.config.FRAME_INTERVAL)
            processed_idx += 1
        
        # Ajouter les frames selon l'intervalle
        for original_idx in range(0, total_frames, self.config.FRAME_INTERVAL):
            if original_idx not in processed_frames:
                frame_mapping[original_idx] = processed_idx
                processed_frames.add(original_idx)
                processed_idx += 1
        
        # Réorganiser par ordre chronologique
        sorted_frames = sorted(processed_frames)
        final_mapping = [None] * total_frames
        
        for new_idx, original_frame in enumerate(sorted_frames):
            final_mapping[original_frame] = new_idx
        
        return final_mapping, sorted_frames
    
    def _create_objects_structure(self, project_config: Dict[str, Any], 
                                added_objects: List[Dict]) -> Dict[str, Dict]:
        """Crée la structure des objets avec couleurs"""
        config_objects_mapping = {}
        for obj in project_config['objects']:
            config_objects_mapping[obj['obj_id']] = obj

        objects = {}
        for obj_data in added_objects:
            obj_id = str(obj_data['obj_id'])
            obj_type = obj_data['obj_type']

            # Récupérer les informations complètes depuis le config
            config_obj = config_objects_mapping.get(int(obj_id), {})

            # Couleur aléatoire reproductible
            random.seed(int(obj_id) * 12345)
            hue = random.random()
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )

            objects[obj_id] = {
                "id": obj_id,
                "type": obj_type,
                "team": config_obj.get('team', None),
                "jersey_number": config_obj.get('jersey_number', None),
                "jersey_color": config_obj.get('jersey_color', None),
                "role": config_obj.get('role', None),
                "display_color": hex_color
            }

        return objects