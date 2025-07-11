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
        """Charge la configuration du projet depuis le JSON"""
        print("📄 Chargement de la configuration projet...")
        
        if not self.config.config_path.exists():
            raise FileNotFoundError(f"❌ Fichier config non trouvé: {self.config.config_path}")
        
        with open(self.config.config_path, 'r', encoding='utf-8') as f:
            self.project_config = json.load(f)
        
        print(f"✅ Configuration chargée: {len(self.project_config.get('objects', []))} objets")
        return self.project_config
    
    def extract_frames(self, force: bool = False) -> int:
        """Extrait les frames de la vidéo"""
        print("🎬 Extraction des frames...")
        
        if self.config.is_segment_mode or self.config.is_event_mode:
            # Mode segmentation ou event
            if not self.project_config:
                raise ValueError("❌ Configuration projet. requise pour le mode segmentation/event")
            
            reference_frame = self.project_config['initial_annotations'][0].get('frame', 0)
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
        """Initialise le système de tracking SAM2"""
        print("🤖 Initialisation du tracking SAM2...")
        
        # Initialiser SAM2
        self.sam2_tracker.initialize_predictor()
        self.sam2_tracker.initialize_inference_state()
        
        # Ajouter les annotations initiales
        if not self.project_config:
            raise ValueError("❌ Configuration projet requise")
        
        segment_info = None
        if self.config.is_segment_mode:
            segment_info = self.video_processor.get_segment_info(
                self.project_config['initial_annotations'][0].get('frame', 0)
            )
        
        added_objects, annotations_data = self.sam2_tracker.add_initial_annotations(
            self.project_config, segment_info
        )
        
        self.results['added_objects'] = added_objects
        self.results['initial_annotations'] = annotations_data
        
        print(f"✅ Tracking initialisé: {len(added_objects)} objets")
    
    def run_tracking_propagation(self) -> Dict[str, Any]:
        """Exécute la propagation bidirectionnelle du tracking"""
        print("🔄 Propagation du tracking...")
        
        if not self.project_config:
            raise ValueError("❌ Configuration projet requise")
        
        # Utiliser l'enricher pour créer la structure projet et gérer la propagation
        project_data = self.enricher.create_project_structure(
            self.project_config, 
            self.results['added_objects']
        )
        
        # Propagation bidirectionnelle
        project_data = self.enricher.run_bidirectional_propagation(
            self.sam2_tracker.predictor,
            self.sam2_tracker.inference_state,
            project_data,
            self.project_config
        )
        
        self.project_data = project_data
        total_annotations = sum(len(annotations) for annotations in project_data['annotations'].values())
        
        print(f"✅ Propagation terminée: {total_annotations} annotations sur {len(project_data['annotations'])} frames")
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
        
        try:
            # Étape 1: Charger la configuration
            self.load_project_config()
            
            # Étape 2: Extraire les frames
            self.extract_frames(force=force_extraction)
            
            # Étape 3: Initialiser le tracking
            self.initialize_tracking()
            
            # Étape 4: Propagation du tracking
            self.run_tracking_propagation()
            
            # Étape 5: Enrichissement
            self.enrich_annotations()
            
            # Étape 6: Export
            export_paths = self.export_results(include_visualization)
            
            # Étape 7: Export vidéo optionnel
            if export_video:
                try:
                    video_params = video_params or {}
                    video_path = self.export_video(**video_params)
                    export_paths['video'] = video_path
                except Exception as e:
                    print(f"⚠️ Export vidéo échoué (pipeline continue): {e}")
            
            # Résultats finaux
            final_results = self._create_final_results(export_paths)
            
            print("\n🎉 Pipeline terminée avec succès!")
            print(f"   📊 {final_results['frames_annotated']} frames traitées")
            print(f"   🎯 {final_results['objects_tracked']} objets suivis") 
            print(f"   📄 Fichier principal: {export_paths['json']}")
            
            return final_results
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e),
                'video_name': self.config.VIDEO_NAME
            }
            print(f"❌ Erreur dans la pipeline: {e}")
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

    def _create_final_results(self, export_paths: Dict) -> Dict:
        """Crée la structure des résultats finaux"""
        return {
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