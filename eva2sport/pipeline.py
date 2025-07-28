# eva2sport/pipeline.py
"""
Pipeline principale EVA2SPORT
Orchestrateur complet du workflow de tracking vidéo
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from .config import Config
from .tracking.video_processor import VideoProcessor
from .tracking.sam2_tracker import SAM2Tracker
from .enrichment.annotation_enricher import AnnotationEnricher
from .export.project_exporter import ProjectExporter
from .visualization import VideoExporter, VisualizationConfig, MinimapConfig


class EVA2SportPipeline:
    """Pipeline principale pour le tracking vidéo avec SAM2"""
    
    def __init__(self, video_name: str, working_dir: Optional[str] = None,
                 segment_offset_before_seconds: Optional[float] = None,
                 segment_offset_after_seconds: Optional[float] = None,
                 event_timestamp_seconds: Optional[float] = None,
                 **kwargs):
        """
        Initialise la pipeline
        
        Args:
            video_name: Nom de la vidéo (sans extension)
            working_dir: Répertoire de travail (par défaut: répertoire courant)
            segment_offset_before_seconds: Offset avant en secondes (active le mode segment)
            segment_offset_after_seconds: Offset après en secondes (active le mode segment)
            event_timestamp_seconds: Timestamp de l'event en secondes (active le mode event)
            **kwargs: Autres paramètres de configuration
        """
        self.config = Config(
            video_name, 
            working_dir,
            segment_offset_before_seconds=segment_offset_before_seconds,
            segment_offset_after_seconds=segment_offset_after_seconds,
            event_timestamp_seconds=event_timestamp_seconds,
            **kwargs
        )
        
        # Modules de traitement
        self.video_processor = VideoProcessor(self.config)
        self.sam2_tracker = SAM2Tracker(self.config)
        self.enricher = AnnotationEnricher(self.config)
        self.exporter = ProjectExporter(self.config)
        
        # État de la pipeline
        self.project_config = None
        self.project_data = None
        self.results = {}
    
    def load_project_config(self) -> Dict[str, Any]:
        """Charge la configuration du projet depuis les JSONs (séparés ou non)"""
        print("📄 Chargement de la configuration projet...")

        # Chemins des nouveaux fichiers
        calib_path = self.config.config_path.parent / f"{self.config.VIDEO_NAME}_calib.json"
        objects_path = self.config.config_path.parent / f"{self.config.VIDEO_NAME}_objects.json"

        if calib_path.exists() and objects_path.exists():
            # Nouveau format : deux fichiers
            with open(calib_path, 'r', encoding='utf-8') as f:
                calib_data = json.load(f)
            with open(objects_path, 'r', encoding='utf-8') as f:
                objects_data = json.load(f)
            # Fusionne les deux dictionnaires (sans écraser)
            self.project_config = {**calib_data, **objects_data}
            print(f"✅ Config séparée chargée : calibration + {len(self.project_config.get('objects', []))} objets")
        elif self.config.config_path.exists():
            # Ancien format : un seul fichier
            with open(self.config.config_path, 'r', encoding='utf-8') as f:
                self.project_config = json.load(f)
            print(f"✅ Config unique chargée : {len(self.project_config.get('objects', []))} objets")
        else:
            raise FileNotFoundError("❌ Aucun fichier de configuration trouvé")

        return self.project_config
    
    def extract_frames(self, force: bool = False, event_frame: int = None) -> int:
        """Extrait les frames de la vidéo"""
        # Utiliser la valeur de config si event_frame n'est pas fourni explicitement
        if event_frame is None:
            event_frame = self.config.event_frame
            print("event frame : ",event_frame)

        if self.config.is_segment_mode or self.config.is_event_mode:
            if not self.project_config:
                raise ValueError("❌ Configuration projet requise pour le mode segmentation/event")
            
            initial_annotations = self.project_config['initial_annotations']
            
            # Utiliser la méthode centralisée pour sélectionner l'annotation la plus proche ET valide
            reference_frame = self.config.get_closest_valid_annotation_frame(initial_annotations)
            
            print(f"event_frame demandé: {event_frame}")
            print("Frames des initial_annotations:", [ann.get('frame', 0) for ann in initial_annotations])
            
            if reference_frame is None:
                print("❌ Aucune annotation valide trouvée dans l'intervalle de l'événement")
                return 0
            
            print(f"Frame choisie: {reference_frame}")
            
            self.results['reference_frame'] = reference_frame
            frames_count = self.video_processor.extract_segment_frames(
                reference_frame=reference_frame,
                force_extraction=force
            )
        else:
            # Mode complet
            frames_count = self.video_processor.extract_all_frames(force_extraction=force)
        
        self.config.extracted_frames_count = frames_count
        self.results['extracted_frames'] = frames_count

        print(f"✅ {frames_count} frames extraites")
        return frames_count
    
    def initialize_tracking(self) -> None:
        """Initialise le système de tracking SAM2 avec multi-anchor"""
        from .utils import eva_logger
        eva_logger.tracking("Initialisation du tracking SAM2 multi-anchor...")
        
        # Initialiser SAM2
        self.sam2_tracker.initialize_predictor()
        self.sam2_tracker.initialize_inference_state()
        
        # Ajouter les annotations initiales - VERSION MULTI-ANCHOR
        if not self.project_config:
            raise ValueError("❌ Configuration projet requise")
        
        segment_info = None
        if self.config.is_segment_mode or self.config.is_event_mode:
            reference_frame = self.results.get('reference_frame')
            if reference_frame is None:
                reference_frame = self.project_config['initial_annotations'][0].get('frame', 0)
            segment_info = self.video_processor.get_segment_info(reference_frame)

        # CHANGEMENT PRINCIPAL : utiliser add_multiple_initial_annotations
        added_objects, annotations_data = self.sam2_tracker.add_multiple_initial_annotations(
            self.project_config, segment_info
        )
        
        self.results['added_objects'] = added_objects
        self.results['initial_annotations'] = annotations_data
        
        eva_logger.success(f"Tracking multi-anchor initialisé: {len(added_objects)} objets")
    
    def run_tracking_propagation(self) -> Dict[str, Any]:
        """Exécute la propagation du tracking avec support multi-anchor"""
        from .utils import eva_logger
        eva_logger.info("Propagation du tracking...")
        
        if not self.project_config:
            raise ValueError("❌ Configuration projet requise")

        # 1. Créer la structure projet vide
        project_data = self.exporter.create_project_structure(
            self.project_config, 
            self.results['added_objects']
        )

        # 2. Vérifier si on a plusieurs anchors
        initial_annotations = self.results.get('initial_annotations', [])
        #anchor_frames = [ann['frame_for_sam'] for ann in initial_annotations]
        anchor_frames = [ann['frame_idx'] for ann in initial_annotations]
        unique_anchor_frames = sorted(list(set(anchor_frames)))
        
        if len(unique_anchor_frames) > 1:
            # MODE MULTI-ANCHOR
            eva_logger.info(f"Mode multi-anchor détecté: {len(unique_anchor_frames)} frames d'ancrage")
            
            if self.config.is_segment_mode or self.config.is_event_mode:
                total_frames = self.config.extracted_frames_count
                start_frame = 0
                end_frame = total_frames - 1
            else:
                start_frame = 0
                end_frame = len([f for f in project_data['metadata']['frame_mapping'] if f is not None]) - 1
            
            # Utiliser la nouvelle méthode multi-anchor
            propagation_results = self.sam2_tracker.run_multi_anchor_propagation(
                unique_anchor_frames, start_frame, end_frame
            )
        else:
            # MODE SINGLE-ANCHOR (fallback)
            eva_logger.info("Mode single-anchor (fallback)")
            anchor_frame_idx = unique_anchor_frames[0] if unique_anchor_frames else 0
            
            if self.config.is_segment_mode or self.config.is_event_mode:
                total_frames = self.config.extracted_frames_count
            else:
                total_frames = len([f for f in project_data['metadata']['frame_mapping'] if f is not None])
            
            propagation_results = self.sam2_tracker.run_bidirectional_propagation(
                anchor_frame_idx, total_frames
            )

        # 3. Convertir les résultats en annotations enrichies
        project_data = self.enricher.process_propagation_results(
            propagation_results, project_data, self.project_config
        )
        
        self.project_data = project_data
        total_annotations = sum(len(annotations) for annotations in project_data['annotations'].values())
        
        eva_logger.success(f"Propagation terminée: {total_annotations} annotations sur {len(project_data['annotations'])} frames")
        return project_data
    
    def enrich_annotations(self) -> Dict[str, Any]:
        """Enrichit les annotations avec projections terrain et calculs"""
        print("🎯 Enrichissement des annotations...")
        
        if not self.project_data:
            raise ValueError("❌ Données projet requises")
        
        # Enrichir avec projections terrain, bbox, etc.
        enriched_data = self.enricher.enrich_all_annotations(
            self.project_data, 
            self.project_config
        )
        
        self.project_data = enriched_data
        print(f"✅ Annotations enrichies")
        return enriched_data
    
    def export_results(self, include_visualization: bool = True) -> Dict[str, Path]:
        """Exporte les résultats finaux"""
        print("💾 Export des résultats...")
        
        if not self.project_data:
            raise ValueError("❌ Données projet requises")
        
        # Export JSON principal
        json_path = self.exporter.save_project_json(self.project_data)
        results_paths = {'json': json_path}
        
        # Export visualisations si demandé
        if include_visualization:
            viz_paths = self.exporter.create_visualizations(self.project_data)
            results_paths.update(viz_paths)
        
        # Statistiques finales
        self.exporter.display_final_statistics(self.project_data)
        
        print(f"✅ Export terminé: {len(results_paths)} fichiers créés")
        return results_paths
    
    def export_video(self, fps: int = 30, show_minimap: bool = True, 
                    cleanup_frames: bool = True, force_regenerate: bool = False,
                    minimap_config: Optional[Dict] = None,
                    preset: Optional[str] = None,
                    figsize: Tuple[int, int] = (15, 8),
                    dpi: int = 100) -> str:
        """
        Exporte la vidéo avec annotations et visualisations
        
        Args:
            fps: Frames par seconde de la vidéo
            show_minimap: Afficher la minimap
            cleanup_frames: Supprimer les frames temporaires après export
            force_regenerate: Forcer la régénération des frames
            minimap_config: Configuration de la minimap (rotation, half_field, etc.)
            preset: Preset de configuration ('default', 'high_quality', 'fast_preview', 'tactical_analysis')
            figsize: Taille de la figure
            dpi: Résolution des images
        
        Returns:
            str: Chemin de la vidéo générée
        """
        
        print("🎬 Export vidéo avec annotations...")
        
        # Créer l'exporteur vidéo avec preset ou configuration par défaut
        if preset:
            print(f"🎯 Utilisation du preset: {preset}")
            video_exporter = VideoExporter.create_with_preset(self.config, preset)
            
            # Appliquer les paramètres supplémentaires
            video_exporter.configure_visualization(
                fps=fps,
                show_minimap=show_minimap,
                cleanup_frames=cleanup_frames,
                force_regenerate=force_regenerate,
                figsize=figsize,
                dpi=dpi
            )
        else:
            # Configuration manuelle
            viz_config = VisualizationConfig(
                fps=fps,
                show_minimap=show_minimap,
                cleanup_frames=cleanup_frames,
                force_regenerate=force_regenerate,
                figsize=figsize,
                dpi=dpi
            )
            video_exporter = VideoExporter(self.config, viz_config)
        
        # Configurer la minimap si demandé
        if minimap_config:
            video_exporter.configure_minimap(**minimap_config)
            print(f"🎯 Minimap configurée: {minimap_config}")
        
        # Définir le chemin de sortie
        preset_suffix = f"_{preset}" if preset else ""
        output_path = str(self.config.output_dir / f"{self.config.VIDEO_NAME}_annotated{preset_suffix}.mp4")
        
        # Exporter la vidéo
        success = video_exporter.export_video(output_path)
        
        if success:
            print(f"✅ Vidéo exportée: {output_path}")
            
            # Afficher les statistiques
            stats = video_exporter.get_export_stats()
            if stats:
                print(f"📊 Statistiques: {stats['total_frames']} frames, {stats['total_objects']} annotations")
            
            return output_path
        else:
            raise Exception("❌ Échec de l'export vidéo")
    
    def run_full_pipeline(self, 
                         force_extraction: bool = False,
                         include_visualization: bool = True,
                         export_video: bool = False,
                         video_params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Exécute la pipeline complète
        
        Args:
            force_extraction: Force la ré-extraction des frames
            include_visualization: Inclut les visualisations dans l'export
            export_video: Inclut l'export vidéo
            video_params: Paramètres pour l'export vidéo
            
        Returns:
            Dictionnaire avec les résultats et chemins de fichiers
        """
        self.config.display_config()
        
        from .utils import eva_logger
        
        try:
            # Étape 1: Charger la configuration
            eva_logger.step(1, 7, "Chargement de la configuration")
            self.load_project_config()
            
            # Étape 2: Extraire les frames
            eva_logger.step(2, 7, "Extraction des frames")
            self.extract_frames(force=force_extraction)
            
            # Étape 3: Initialiser le tracking
            eva_logger.step(3, 7, "Initialisation du tracking")
            self.initialize_tracking()
            
            # Étape 4: Propagation du tracking
            eva_logger.step(4, 7, "Propagation du tracking")
            self.run_tracking_propagation()
            
            # Étape 5: Enrichissement
            eva_logger.step(5, 7, "Enrichissement des annotations")
            self.enrich_annotations()
            
            # Étape 6: Export
            eva_logger.step(6, 7, "Export des résultats")
            export_paths = self.export_results(include_visualization)
            
            # Étape 7: Export vidéo optionnel
            if export_video:
                try:
                    eva_logger.step(7, 7, "Export vidéo")
                    video_params = video_params or {}
                    video_path = self.export_video(**video_params)
                    export_paths['video'] = video_path
                except Exception as e:
                    eva_logger.warning(f"Export vidéo échoué (pipeline continue): {e}")
            
            # Résultats finaux
            final_results = self._create_final_results(export_paths)
            
            eva_logger.pipeline_end(success=True)
            eva_logger.progress(f"{final_results['frames_annotated']} frames traitées")
            eva_logger.progress(f"{final_results['objects_tracked']} objets suivis") 
            eva_logger.info(f"Fichier principal: {export_paths['json']}")
            
            return final_results
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            from datetime import datetime
            error_result = {
                'status': 'error',
                'error': str(e),
                'error_details': error_details,
                'video_name': self.config.VIDEO_NAME,
                'timestamp': datetime.now().isoformat()
            }
            self.results = error_result
            
            eva_logger.error(f"Erreur dans la pipeline: {e}")
            eva_logger.error("Détails de l'erreur:")
            eva_logger.error(error_details)
            
            return error_result
    
    def run_simple(self, force_extraction: bool = False) -> str:
        """
        Mode simple : exécute la pipeline et retourne le chemin du JSON
        
        Args:
            force_extraction: Force la ré-extraction des frames
            
        Returns:
            Chemin vers le fichier JSON de résultats
        """
        results = self.run_full_pipeline(
            force_extraction=force_extraction,
            include_visualization=False
        )
        
        if results['status'] == 'success':
            return str(results['export_paths']['json'])
        else:
            raise RuntimeError(f"Pipeline failed: {results['error']}")

    def _create_final_results(self, export_paths: Dict[str, str]) -> Dict[str, Any]:
        """Crée la structure des résultats finaux"""
        results = {
            'status': 'success',
            'video_name': self.config.VIDEO_NAME,
            'frames_extracted': self.results.get('extracted_frames', 0),
            'objects_tracked': len(self.results.get('added_objects', [])),
            'total_annotations': sum(len(annotations) for annotations in self.project_data['annotations'].values()),
            'frames_annotated': len(self.project_data['annotations']),
            'export_paths': export_paths,
            'config': {
                'frame_interval': self.config.FRAME_INTERVAL,
                'event_mode': self.config.is_event_mode,
                'segment_mode': self.config.is_segment_mode,
                'output_dir': str(self.config.output_dir)
            }
        }
        
        # Ajouter les informations spécifiques aux événements pour l'index
        if self.config.is_event_mode:
            results['event_timestamp'] = self.config.event_timestamp_seconds
            results['event_frame'] = self.config.event_frame
        
        # Ajouter les informations de segment pour l'index
        if hasattr(self, 'results') and 'reference_frame' in self.results:
            results['reference_frame'] = self.results['reference_frame']
            
            # Calculer les bornes du segment si disponibles
            if self.config.is_segment_mode or self.config.is_event_mode:
                try:
                    start_frame, end_frame, _ = self.config.calculate_segment_bounds_and_anchor(
                        self.results['reference_frame'], verbose=False
                    )
                    results['segment_start_frame'] = start_frame
                    results['segment_end_frame'] = end_frame
                except:
                    pass  # Si le calcul échoue, on continue sans ces infos
        
        return results