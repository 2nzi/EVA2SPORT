"""
Wrapper SAM2 pour EVA2SPORT
Extrait du notebook SAM_inference_segment.ipynb
"""

import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from ..config import Config


class SAM2Tracker:
    """Wrapper pour SAM2 Video Predictor avec gestion simplifiée"""
    
    def __init__(self, config: Config):
        self.config = config
        self.predictor = None
        self.inference_state = None
        self.added_objects = []
        self.initial_annotations_data = []
    
    def initialize_predictor(self, verbose: bool = True) -> None:
        """Initialise le predictor SAM2"""
        try:
            from sam2.build_sam import build_sam2_video_predictor
        except ImportError:
            raise ImportError("❌ SAM2 non installé. Installez-le avec: pip install SAM2")
        
        if verbose:
            print(f"🤖 Initialisation SAM2...")
            print(f"   🧠 Modèle: {self.config.model_config_path}")
            print(f"   💾 Checkpoint: {self.config.checkpoint_path}")
            print(f"   🖥️  Device: {self.config.device}")
        
        # Vérification du checkpoint
        if not self.config.checkpoint_path.exists():
            raise FileNotFoundError(f"❌ Checkpoint SAM2 non trouvé: {self.config.checkpoint_path}")
        
        # Construction du predictor avec gestion des types
        self.predictor = build_sam2_video_predictor(
            config_file=self.config.model_config_path,
            ckpt_path=str(self.config.checkpoint_path),
            device=self.config.device
        )
        
        # Forcer le type float32 pour éviter les problèmes de dtype
        if hasattr(self.predictor, 'model'):
            self.predictor.model = self.predictor.model.float()
        
        if verbose:
            print("✅ Predictor SAM2 initialisé")
    
    def initialize_inference_state(self, verbose: bool = True) -> None:
        """Initialise l'état d'inférence avec vérifications"""
        if self.predictor is None:
            raise ValueError("❌ Predictor non initialisé. Appelez initialize_predictor() d'abord")
        
        if verbose:
            print(f"\n🎬 Initialisation état d'inférence...")
            print(f"   📁 Frames: {self.config.frames_dir}")
        
        # Vérification des frames
        if not hasattr(self.config, 'extracted_frames_count') or self.config.extracted_frames_count == 0:
            raise ValueError(f"❌ Aucune frame extraite. Extrayez d'abord les frames.")
        
        # Initialisation de l'état d'inférence
        self.inference_state = self.predictor.init_state(
            video_path=str(self.config.frames_dir),
            offload_video_to_cpu=True,    # Économise la mémoire GPU
            offload_state_to_cpu=False    # Garde l'état en GPU
        )
        
        # Reset de l'état
        self.predictor.reset_state(self.inference_state)
        
        # Vérification
        loaded_frames = self.inference_state["num_frames"]
        
        if verbose:
            print(f"\n✅ SAM2 initialisé:")
            print(f"   🖼️  Frames extraites: {self.config.extracted_frames_count}")
            print(f"   🎬 Frames chargées: {loaded_frames}")
            print(f"   ✅ Correspondance: {'OK' if self.config.extracted_frames_count == loaded_frames else 'ERREUR'}")
            
            if self.config.device.type == "cuda":
                allocated = torch.cuda.memory_allocated() / 1024**3
                print(f"   💾 GPU Memory: {allocated:.2f}GB")
        
        if self.config.extracted_frames_count != loaded_frames:
            print(f"⚠️ Incohérence frames : {self.config.extracted_frames_count} extraites vs {loaded_frames} chargées")
    
    def add_initial_annotations(self, project_config: Dict[str, Any], 
                               segment_info: Optional[Dict] = None) -> Tuple[List[Dict], List[Dict]]:
        """Ajoute les annotations initiales depuis la configuration projet"""
        if self.predictor is None or self.inference_state is None:
            raise ValueError("❌ SAM2 non initialisé. Appelez initialize_predictor() et initialize_inference_state() d'abord")
        
        print(f"🎯 Ajout des annotations initiales...")

        # Création du mapping obj_id -> obj_type
        obj_types = {}
        for obj in project_config['objects']:
            obj_types[obj['obj_id']] = obj['obj_type']

        # Extraction automatique des annotations et frames depuis le JSON
        all_annotations = []
        annotation_frames = []

        for frame_data in project_config['initial_annotations']:
            frame_idx_original = frame_data['frame']  # ← Frame originale du JSON
            
            # Conversion avec prise en compte de la segmentation
            frame_idx_processed = frame_idx_original // self.config.FRAME_INTERVAL
            
            # Ajustement pour le mode segmentation
            if segment_info:
                # Calculer l'offset par rapport au début du segment
                segment_start_processed = segment_info['start_frame'] // self.config.FRAME_INTERVAL
                frame_idx_segment = frame_idx_processed - segment_start_processed
                
                print(f"   🎯 MODE SEGMENTATION:")
                print(f"      📍 Frame originale: {frame_idx_original}")
                print(f"      📍 Frame traitée: {frame_idx_processed}")
                print(f"      📍 Segment commence à: {segment_start_processed} (traité)")
                print(f"      📍 Index dans le segment: {frame_idx_segment}")
                
                # Vérifier que la frame est dans le segment
                segment_end_processed = segment_info['end_frame'] // self.config.FRAME_INTERVAL
                if frame_idx_processed < segment_start_processed or frame_idx_processed > segment_end_processed:
                    raise ValueError(f"❌ Frame d'annotation {frame_idx_processed} en dehors du segment [{segment_start_processed}, {segment_end_processed}]")
                
                # Utiliser l'index dans le segment
                frame_idx_for_sam = frame_idx_segment
            else:
                frame_idx_for_sam = frame_idx_processed
            
            annotations = frame_data['annotations']
            annotation_frames.append(frame_idx_for_sam)

            print(f"   📍 Frame {frame_idx_original} (original) → {frame_idx_for_sam} (pour SAM2): {len(annotations)} annotations")

            for annotation in annotations:
                all_annotations.append({
                    'frame_original': frame_idx_original,
                    'frame_processed': frame_idx_processed,
                    'frame_for_sam': frame_idx_for_sam,  # ← Nouvel index pour SAM2
                    'obj_id': annotation['obj_id'],
                    'points': annotation['points'],
                    'obj_type': obj_types.get(annotation['obj_id'], f'unknown_{annotation["obj_id"]}')
                })

        if not all_annotations:
            raise ValueError(f"❌ Aucune annotation trouvée dans le fichier config")

        print(f"   📊 Total: {len(all_annotations)} annotations sur {len(set(annotation_frames))} frames")

        # Ajout des annotations à SAM2 avec les frames converties
        added_objects = []

        for annotation_data in all_annotations:
            frame_idx_for_sam = annotation_data['frame_for_sam']  # ← Utiliser l'index ajusté
            frame_idx_original = annotation_data['frame_original']
            obj_id = annotation_data['obj_id']
            obj_type = annotation_data['obj_type']
            points_data = annotation_data['points']

            # Extraction des coordonnées et labels
            points = np.array([[p['x'], p['y']] for p in points_data], dtype=np.float32)
            labels = np.array([p['label'] for p in points_data], dtype=np.int32)

            print(f"   🎯 Frame {frame_idx_original}→{frame_idx_for_sam} - Objet {obj_id} ({obj_type}): {len(points)} points à ({points[0][0]:.0f}, {points[0][1]:.0f})")

            # Utiliser frame_idx_for_sam (ajusté pour le segment)
            _, out_obj_ids, out_mask_logits = self.predictor.add_new_points_or_box(
                self.inference_state,
                frame_idx_for_sam,  # ← Frame ajustée pour SAM2
                obj_id,
                points,
                labels
            )

            # Éviter les doublons dans added_objects
            if not any(obj['obj_id'] == obj_id for obj in added_objects):
                added_objects.append({
                    'obj_id': obj_id,
                    'obj_type': obj_type,
                    'points_count': len(points)
                })

        # Vérification
        sam_obj_ids = self.inference_state["obj_ids"]

        print(f"\n📊 RÉSUMÉ ANNOTATIONS:")
        print(f"   🎯 Annotations configurées: {len(all_annotations)}")
        print(f"   🎯 Objets uniques: {len(added_objects)}")
        print(f"   ✅ Objets ajoutés à SAM2: {len(sam_obj_ids)}")
        print(f"   🆔 IDs: {sorted(sam_obj_ids)}")
        
        if segment_info:
            print(f"   🎯 Mode segmentation: Frame d'annotation ajustée")
        else:
            print(f"   🎬 Mode complet: Frames utilisées")

        # Résumé par type
        type_counts = {}
        for obj in added_objects:
            obj_type = obj['obj_type']
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        print(f"   🏷️  Types: {dict(type_counts)}")
        
        # Sauvegarder pour usage ultérieur
        self.added_objects = added_objects
        self.initial_annotations_data = all_annotations

        return added_objects, all_annotations
    
    def propagate_tracking(self, verbose: bool = True) -> Dict[str, Any]:
        """Propage le tracking sur toutes les frames"""
        if self.predictor is None or self.inference_state is None:
            raise ValueError("❌ SAM2 non initialisé")
        
        if verbose:
            print("🔄 Propagation du tracking...")
        
        # Propagation sur toutes les frames
        video_segments = {}
        for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state):
            video_segments[out_frame_idx] = {
                'obj_ids': out_obj_ids,
                'mask_logits': out_mask_logits
            }
        
        if verbose:
            print(f"✅ Tracking propagé sur {len(video_segments)} frames")
        
        return video_segments
    
    def initialize_full_pipeline(self, project_config: Dict[str, Any], 
                                segment_info: Optional[Dict] = None, 
                                verbose: bool = True) -> Tuple[List[Dict], List[Dict], Dict[str, Any]]:
        """Initialise complètement SAM2 et ajoute les annotations"""
        
        # Initialisation SAM2
        self.initialize_predictor(verbose=verbose)
        self.initialize_inference_state(verbose=verbose)
        
        # Ajout des annotations initiales
        added_objects, initial_annotations = self.add_initial_annotations(
            project_config, segment_info
        )
        
        # Propagation du tracking
        video_segments = self.propagate_tracking(verbose=verbose)
        
        return added_objects, initial_annotations, video_segments