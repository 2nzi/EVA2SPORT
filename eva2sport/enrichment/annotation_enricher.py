"""
Enrichisseur d'annotations avec projections terrain et calculs géométriques
Extrait du notebook SAM_inference_segment.ipynb
"""

import uuid
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime

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
    
    def process_propagation_results(self, propagation_results: Dict[str, Any], 
                                  project_data: Dict[str, Any], 
                                  project_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convertit les résultats de propagation SAM2 en annotations enrichies"""
        
        print("🎯 Traitement des résultats de propagation...")
        
        # Initialiser les annotations si nécessaire
        if 'annotations' not in project_data:
            project_data['annotations'] = {}
        
        cam_params = project_config['calibration']['camera_parameters']
        total_processed = 0
        
        # Traiter chaque frame de la propagation
        for frame_idx, frame_results in propagation_results.items():
            obj_ids = frame_results['obj_ids']
            mask_logits = frame_results['mask_logits']
            
            # Initialiser les annotations pour cette frame
            if str(frame_idx) not in project_data['annotations']:
                project_data['annotations'][str(frame_idx)] = []
            
            # Traiter chaque objet détecté
            for i, obj_id in enumerate(obj_ids):
                annotation = self._create_mask_annotation(
                    obj_id=obj_id,
                    mask_logits=mask_logits[i],
                    predictor=None,  # Passé None car nous n'avons pas accès direct ici
                    inference_state=None,
                    frame_idx=frame_idx,
                    cam_params=cam_params
                )
                project_data['annotations'][str(frame_idx)].append(annotation)
                total_processed += 1
        
        print(f"✅ {total_processed} annotations créées depuis la propagation")
        return project_data
    
    # ===== MÉTHODES AUXILIAIRES (SEULEMENT CELLES LIÉES À L'ENRICHISSEMENT) =====
    
    def _get_anchor_processed_index(self, project_data: Dict[str, Any], 
                                  project_config: Dict[str, Any]) -> int:
        """Calcule l'index de la frame d'ancrage dans les frames traitées"""
        
        if self.config.is_segment_mode or self.config.is_event_mode:
            # Utiliser la méthode centralisée pour sélectionner l'annotation la plus proche
            reference_frame = self.config.get_closest_initial_annotation_frame(
                project_config['initial_annotations']
            )
            
            # Utiliser la méthode centralisée pour calculer les bornes et l'ancrage (sans logs répétés)
            _, _, anchor_frame_in_segment = self.config.calculate_segment_bounds_and_anchor(reference_frame, verbose=False)
            
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
        # Vérifier que predictor et inference_state sont disponibles
        if predictor is None or inference_state is None:
            return None
            
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