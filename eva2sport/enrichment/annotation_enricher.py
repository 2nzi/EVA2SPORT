"""
Enrichisseur d'annotations avec projections terrain et calculs géométriques
Extrait du notebook SAM_inference_segment.ipynb
"""

import uuid
import base64
import colorsys
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch
from pycocotools.mask import encode as encode_rle, toBbox

from ..config import Config
from .projection_utils import ProjectionUtils
from .bbox_calculator import BBoxCalculator


class AnnotationEnricher:
    """Enrichit les annotations avec projections terrain et métadonnées"""
    
    def __init__(self, config: Config):
        self.config = config
        self.projection_utils = ProjectionUtils()
        self.bbox_calculator = BBoxCalculator()
    
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
    
    def run_bidirectional_propagation(self, predictor, inference_state, 
                                    project_data: Dict[str, Any],
                                    project_config: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute la propagation bidirectionnelle et enrichit les annotations"""
        
        print("🔄 Propagation bidirectionnelle avec enrichissement...")
        
        # ✅ CORRECTION: Utiliser la méthode corrigée
        anchor_processed_idx = self._get_anchor_processed_index(project_data, project_config)
        
        # En mode segmentation/event, total_frames = extracted_frames_count
        if self.config.is_segment_mode or self.config.is_event_mode:
            total_frames = self.config.extracted_frames_count
        else:
            total_frames = len([f for f in project_data['metadata']['frame_mapping'] if f is not None])
        
        print(f"   📊 Anchor index: {anchor_processed_idx}, Total frames: {total_frames}")
        
        # Phase 1: Propagation inverse (anchor → 0)
        if anchor_processed_idx > 0:
            print(f"🔄 Phase 1: Propagation inverse (frame {anchor_processed_idx} → 0)")
            
            for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(
                inference_state,
                start_frame_idx=anchor_processed_idx,
                max_frame_num_to_track=anchor_processed_idx + 1,
                reverse=True
            ):
                self._process_frame_annotations(
                    project_data, project_config, out_frame_idx, 
                    out_obj_ids, out_mask_logits, predictor, inference_state
                )
        
        # Phase 2: Propagation avant (anchor → fin)
        remaining_frames = total_frames - anchor_processed_idx
        if remaining_frames > 1:
            print(f"🔄 Phase 2: Propagation avant (frame {anchor_processed_idx} → {total_frames - 1})")
            
            for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(
                inference_state,
                start_frame_idx=anchor_processed_idx,
                max_frame_num_to_track=remaining_frames,
                reverse=False
            ):
                # Éviter de traiter à nouveau l'anchor frame
                if out_frame_idx == anchor_processed_idx and str(out_frame_idx) in project_data['annotations']:
                    continue
                
                self._process_frame_annotations(
                    project_data, project_config, out_frame_idx,
                    out_obj_ids, out_mask_logits, predictor, inference_state
                )
        
        return project_data
    
    def enrich_all_annotations(self, project_data: Dict[str, Any], 
                             project_config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit toutes les annotations avec projections terrain"""
        
        print("🎯 Enrichissement des annotations avec projections terrain...")
        
        cam_params = project_config['calibration']['camera_parameters']
        enriched_count = 0
        
        for frame_idx, annotations in project_data['annotations'].items():
            for annotation in annotations:
                # Enrichir avec projection terrain si bbox disponible
                if annotation.get('bbox', {}).get('output'):
                    bbox = annotation['bbox']['output']
                    points_output = self.bbox_calculator.calculate_points_from_bbox(
                        bbox, cam_params
                    )
                    annotation['points']['output'] = points_output
                    enriched_count += 1
        
        print(f"✅ {enriched_count} annotations enrichies avec projections terrain")
        return project_data
    
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
        
        # Utiliser la méthode centralisée pour calculer les bornes et l'ancrage
        _, _, anchor_frame_in_segment = self.config.calculate_segment_bounds_and_anchor(reference_frame)
        
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
    
    def _get_anchor_processed_index(self, project_data: Dict[str, Any], 
                                  project_config: Dict[str, Any]) -> int:
        """Calcule l'index de la frame d'ancrage dans les frames traitées"""
        
        if self.config.is_segment_mode or self.config.is_event_mode:
            # Utiliser la méthode centralisée pour sélectionner l'annotation la plus proche
            reference_frame = self.config.get_closest_initial_annotation_frame(
                project_config['initial_annotations']
            )
            
            # Utiliser la méthode centralisée pour calculer les bornes et l'ancrage
            _, _, anchor_frame_in_segment = self.config.calculate_segment_bounds_and_anchor(reference_frame)
            
            return anchor_frame_in_segment
            
        else:
            # Mode complet : utiliser le mapping
            anchor_frame = project_data['metadata']['anchor_frame']
            frame_mapping = project_data['metadata']['frame_mapping']
            
            if anchor_frame < len(frame_mapping) and frame_mapping[anchor_frame] is not None:
                return frame_mapping[anchor_frame]
            
            return 0
    
    def _process_frame_annotations(self, project_data: Dict[str, Any], 
                                 project_config: Dict[str, Any],
                                 frame_idx: int, obj_ids: List[int], 
                                 mask_logits: torch.Tensor,
                                 predictor, inference_state) -> None:
        """Traite les annotations d'une frame"""
        
        if str(frame_idx) not in project_data['annotations']:
            project_data['annotations'][str(frame_idx)] = []

        cam_params = project_config['calibration']['camera_parameters']

        for i, obj_id in enumerate(obj_ids):
            annotation = self._create_mask_annotation(
                obj_id=obj_id,
                mask_logits=mask_logits[i],
                predictor=predictor,
                inference_state=inference_state,
                frame_idx=frame_idx,
                cam_params=cam_params
            )
            project_data['annotations'][str(frame_idx)].append(annotation)
    
    def _create_mask_annotation(self, obj_id: int, mask_logits: torch.Tensor,
                              predictor, inference_state, frame_idx: int,
                              cam_params: Dict) -> Dict:
        """Crée une annotation de masque complète"""
        
        # Conversion en masque binaire
        mask = (mask_logits > 0.0).cpu().numpy()
        if mask.ndim == 3 and mask.shape[0] == 1:
            mask = np.squeeze(mask, axis=0)

        # Encodage RLE
        if not mask.flags['F_CONTIGUOUS']:
            mask = np.asfortranarray(mask)

        rle = encode_rle(mask.astype(np.uint8))
        base64_counts = base64.b64encode(rle["counts"]).decode('ascii')

        # Calcul bbox et points output
        bbox_output = None
        points_output = None

        if mask.sum() > 0:
            bbox = toBbox(rle)
            bbox_output = {
                "x": int(bbox[0]),
                "y": int(bbox[1]),
                "width": int(bbox[2]),
                "height": int(bbox[3])
            }
            # Calcul des points output depuis la bbox
            points_output = self.bbox_calculator.calculate_points_from_bbox(
                bbox_output, cam_params
            )

        # Score du masque
        mask_score = self._get_object_score(predictor, inference_state, frame_idx, obj_id)

        return {
            "id": str(uuid.uuid4()),
            "objectId": str(obj_id),
            "type": "mask",
            "mask": {
                "format": "rle_coco_base64",
                "size": [int(rle["size"][0]), int(rle["size"][1])],
                "counts": base64_counts
            },
            "bbox": {
                "output": bbox_output
            },
            "points": {
                "output": points_output
            },
            "maskScore": mask_score,
            "pose": None,
            "warning": False
        }
    
    def _get_object_score(self, predictor, inference_state, frame_idx: int, obj_id: int) -> Optional[float]:
        """Récupère le score d'objet de manière sûre"""
        try:
            obj_idx = predictor._obj_id_to_idx(inference_state, obj_id)
            obj_output_dict = inference_state["output_dict_per_obj"][obj_idx]
            temp_output_dict = inference_state["temp_output_dict_per_obj"][obj_idx]

            # Chercher dans les outputs
            frame_output = None
            if frame_idx in temp_output_dict["cond_frame_outputs"]:
                frame_output = temp_output_dict["cond_frame_outputs"][frame_idx]
            elif frame_idx in temp_output_dict["non_cond_frame_outputs"]:
                frame_output = temp_output_dict["non_cond_frame_outputs"][frame_idx]
            elif frame_idx in obj_output_dict["cond_frame_outputs"]:
                frame_output = obj_output_dict["cond_frame_outputs"][frame_idx]
            elif frame_idx in obj_output_dict["non_cond_frame_outputs"]:
                frame_output = obj_output_dict["non_cond_frame_outputs"][frame_idx]

            if frame_output and "object_score_logits" in frame_output:
                object_score_logits = frame_output["object_score_logits"]
                return torch.sigmoid(object_score_logits).item()
            return None

        except Exception:
            return None