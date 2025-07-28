"""
Wrapper SAM2 pour EVA2SPORT
Extrait du notebook SAM_inference_segment.ipynb
"""

import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from ..config import Config
from ..utils import eva_logger


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
        
        # Optimisation automatique des paramètres mémoire
        from ..utils import gpu_optimizer
        memory_settings = gpu_optimizer.optimize_sam2_memory_settings()
        
        if verbose:
            recommendation = gpu_optimizer.get_memory_recommendation()
            print(f"   💾 Mémoire GPU: {recommendation}")
            print(f"   ⚙️  Paramètres SAM2: video_cpu={memory_settings['offload_video_to_cpu']}, state_cpu={memory_settings['offload_state_to_cpu']}")
        
        # Initialisation de l'état d'inférence avec paramètres optimisés
        self.inference_state = self.predictor.init_state(
            video_path=str(self.config.frames_dir),
            **memory_settings
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
                from ..utils import gpu_optimizer
                stats = gpu_optimizer.get_memory_stats()
                print(f"   💾 GPU Memory: {stats['allocated']:.2f}GB utilisés / {stats['total']:.2f}GB total")
        
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
    
    def run_bidirectional_propagation(self, anchor_frame: int, total_frames: int) -> Dict[str, Any]:
        """Exécute la propagation bidirectionnelle SAM2 depuis l'anchor frame"""
        if self.predictor is None or self.inference_state is None:
            raise ValueError("❌ SAM2 non initialisé")
        
        print("🔄 Propagation bidirectionnelle SAM2...")
        print(f"   📊 Anchor index: {anchor_frame}, Total frames: {total_frames}")
        
        propagation_results = {}
        
        # Phase 1: Propagation inverse (anchor → 0)
        if anchor_frame > 0:
            print(f"🔄 Phase 1: Propagation inverse (frame {anchor_frame} → 0)")
            
            for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(
                self.inference_state,
                start_frame_idx=anchor_frame,
                max_frame_num_to_track=anchor_frame + 1,
                reverse=True
            ):
                propagation_results[out_frame_idx] = {
                    'obj_ids': out_obj_ids,
                    'mask_logits': out_mask_logits
                }
        
        # Phase 2: Propagation avant (anchor → fin)
        remaining_frames = total_frames - anchor_frame
        if remaining_frames > 1:
            print(f"🔄 Phase 2: Propagation avant (frame {anchor_frame} → {total_frames - 1})")
            
            for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(
                self.inference_state,
                start_frame_idx=anchor_frame,
                max_frame_num_to_track=remaining_frames,
                reverse=False
            ):
                # Éviter de traiter à nouveau l'anchor frame
                if out_frame_idx == anchor_frame and out_frame_idx in propagation_results:
                    continue
                
                propagation_results[out_frame_idx] = {
                    'obj_ids': out_obj_ids,
                    'mask_logits': out_mask_logits
                }
        
        print(f"✅ Propagation terminée: {len(propagation_results)} frames")
        return propagation_results

    def add_multiple_initial_annotations(self, project_config: Dict[str, Any], 
                                   segment_info: Optional[Dict] = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Version multi-anchor : ajoute TOUTES les annotations dans la plage au lieu d'une seule
        
        Args:
            project_config: Configuration du projet
            segment_info: Info du segment (pour mode segment/event)
        
        Returns:
            Tuple (objets ajoutés, données annotations)
        """
        
        eva_logger.tracking("Ajout des annotations initiales multi-anchor...")
        
        # Récupérer TOUTES les annotations dans la plage
        if segment_info:
            start_frame = segment_info['start_frame']
            end_frame = segment_info['end_frame']
            anchor_annotations = self.config.get_all_annotations_in_range(
                project_config['initial_annotations'], start_frame, end_frame
            )
        else:
            anchor_annotations = self.config.get_all_annotations_in_range(
                project_config['initial_annotations']
            )
        
        if not anchor_annotations:
            eva_logger.error("Aucune annotation trouvée dans la plage de traitement")
            return [], []
        
        eva_logger.success(f"Mode multi-anchor: {len(anchor_annotations)} frames d'ancrage")
        
        # Traiter chaque frame d'ancrage
        all_added_objects = []
        all_annotations_data = []
        
        for i, frame_data in enumerate(anchor_annotations):
            frame_idx = frame_data.get('frame', 0)
            annotations = frame_data.get('annotations', [])
            
            eva_logger.info(f"Traitement anchor {i+1}/{len(anchor_annotations)}: frame {frame_idx} ({len(annotations)} objets)")
            
            # Calculer l'index dans le segment traité
            if segment_info:
                processed_frame_idx = self._calculate_processed_frame_index(frame_idx, segment_info)
            else:
                processed_frame_idx = frame_idx
            
            # Ajouter les annotations pour cette frame
            frame_objects, frame_data = self._add_annotations_for_frame(
                processed_frame_idx, annotations, project_config
            )
            
            all_added_objects.extend(frame_objects)
            all_annotations_data.extend(frame_data)
        
        eva_logger.success(f"Multi-anchor terminé: {len(all_added_objects)} objets sur {len(anchor_annotations)} frames")
        
        return all_added_objects, all_annotations_data

    def _calculate_processed_frame_index(self, original_frame: int, segment_info: Dict) -> int:
        """Calcule l'index de frame dans le segment traité"""
        start_frame = segment_info['start_frame']
        return (original_frame - start_frame) // self.config.FRAME_INTERVAL

    def _add_annotations_for_frame(self, frame_idx: int, annotations: List[Dict], 
                                project_config: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Ajoute les annotations pour une frame spécifique"""
        
        # Création du mapping obj_id -> obj_type  
        obj_types = {}
        for obj in project_config['objects']:
            obj_types[obj['obj_id']] = obj['obj_type']
        
        added_objects = []
        annotations_data = []
        
        for annotation in annotations:
            obj_id = annotation['obj_id']
            obj_type = obj_types.get(obj_id, f'unknown_{obj_id}')
            points_data = annotation['points']
            
            # Extraction des coordonnées et labels
            points = np.array([[p['x'], p['y']] for p in points_data], dtype=np.float32)
            labels = np.array([p['label'] for p in points_data], dtype=np.int32)
            
            eva_logger.debug(f"  🎯 Frame {frame_idx} - Objet {obj_id} ({obj_type}): {len(points)} points à ({points[0][0]:.0f}, {points[0][1]:.0f})")
            
            # Ajouter à SAM2
            _, out_obj_ids, out_mask_logits = self.predictor.add_new_points_or_box(
                self.inference_state,
                frame_idx,
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
            
            # Stocker les données d'annotation
            annotations_data.append({
                'frame_idx': frame_idx,
                'obj_id': obj_id,
                'obj_type': obj_type,
                'points': points_data
            })
        
        return added_objects, annotations_data

    def run_multi_anchor_propagation(self, anchor_frames: List[int], start_frame: int, end_frame: int) -> Dict[str, Any]:
        """
        Exécute la propagation SAM2 avec multiple anchors par segments
        
        Args:
            anchor_frames: Liste des frames d'ancrage (triées par ordre croissant)
            start_frame: Frame de début du segment
            end_frame: Frame de fin du segment
            
        Returns:
            Résultats de propagation pour toutes les frames
        """
        if self.predictor is None or self.inference_state is None:
            raise ValueError("❌ SAM2 non initialisé")
        
        from ..utils import eva_logger
        
        eva_logger.info(f"Propagation multi-anchor avec {len(anchor_frames)} anchors")
        eva_logger.info(f"Segment: [{start_frame}, {end_frame}], Anchors: {anchor_frames}")
        
        propagation_results = {}
        
        # Trier les anchors pour s'assurer qu'ils sont dans l'ordre
        sorted_anchors = sorted(anchor_frames)
        
        # Segments à traiter
        segments = []
        
        # Segment 1: start_frame → premier_anchor (si le premier anchor n'est pas au début)
        if sorted_anchors[0] > start_frame:
            segments.append({
                'start': start_frame,
                'end': sorted_anchors[0],
                'anchor': sorted_anchors[0],
                'direction': 'reverse',
                'name': f"Segment 1: [{start_frame} → {sorted_anchors[0]}] depuis anchor({sorted_anchors[0]})"
            })
        
        # Segments intermédiaires: anchor_i → anchor_i+1
        for i in range(len(sorted_anchors) - 1):
            current_anchor = sorted_anchors[i]
            next_anchor = sorted_anchors[i + 1]
            
            segments.append({
                'start': current_anchor,
                'end': next_anchor,
                'anchor': current_anchor,
                'direction': 'forward',
                'name': f"Segment {i+2}: [{current_anchor} → {next_anchor}] depuis anchor({current_anchor})"
            })
        
        # Segment final: dernier_anchor → end_frame (si le dernier anchor n'est pas à la fin)
        if sorted_anchors[-1] < end_frame:
            segments.append({
                'start': sorted_anchors[-1],
                'end': end_frame,
                'anchor': sorted_anchors[-1],
                'direction': 'forward',
                'name': f"Segment {len(segments)+1}: [{sorted_anchors[-1]} → {end_frame}] depuis anchor({sorted_anchors[-1]})"
            })
        
        # Exécuter chaque segment
        for i, segment in enumerate(segments, 1):
            eva_logger.info(f"🔄 {segment['name']}")
            
            if segment['direction'] == 'reverse':
                # Propagation inverse
                max_frames = segment['anchor'] - segment['start'] + 1
                
                for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(
                    self.inference_state,
                    start_frame_idx=segment['anchor'],
                    max_frame_num_to_track=max_frames,
                    reverse=True
                ):
                    if segment['start'] <= out_frame_idx <= segment['end']:
                        propagation_results[out_frame_idx] = {
                            'obj_ids': out_obj_ids,
                            'mask_logits': out_mask_logits
                        }
            else:
                # Propagation avant
                max_frames = segment['end'] - segment['start'] + 1
                
                for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(
                    self.inference_state,
                    start_frame_idx=segment['anchor'],
                    max_frame_num_to_track=max_frames,
                    reverse=False
                ):
                    if segment['start'] <= out_frame_idx <= segment['end']:
                        # Éviter de réécraser les frames d'ancrage déjà traitées
                        if out_frame_idx not in propagation_results:
                            propagation_results[out_frame_idx] = {
                                'obj_ids': out_obj_ids,
                                'mask_logits': out_mask_logits
                            }
        
        eva_logger.success(f"Propagation multi-anchor terminée: {len(propagation_results)} frames")
        return propagation_results