"""
Gestionnaire d'événements multiples pour EVA2SPORT
Gère l'index global et les fichiers séparés par événement
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from ..config import Config
from ..pipeline import EVA2SportPipeline
from ..utils import TimestampReader


class MultiEventManager:
    """Gestionnaire pour traiter plusieurs événements avec index global"""
    
    def __init__(self, video_name: str, working_dir: Optional[str] = None):
        """
        Initialise le gestionnaire d'événements multiples
        
        Args:
            video_name: Nom de la vidéo de base (sans suffixe d'événement)
            working_dir: Répertoire de travail
        """
        self.video_name = video_name
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        
        # Chemins pour l'index global - Structure hiérarchique
        self.videos_dir = self.working_dir / "data" / "videos"
        self.base_output_dir = self.videos_dir / "outputs"
        self.video_output_dir = self.base_output_dir / video_name
        self.index_file = self.video_output_dir / f"{video_name}_events_index.json"
        
        # Utilitaires - Créer avec une config temporaire pour la résolution des chemins
        from ..config import Config
        temp_config = Config(video_name, working_dir, create_directories=False)
        self.timestamp_reader = TimestampReader(temp_config)
        
        # État
        self.events_index = self._load_or_create_index()
        
    def _load_or_create_index(self) -> Dict[str, Any]:
        """Charge ou crée l'index des événements"""
        # Créer le dossier de la vidéo si nécessaire
        self.video_output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "video_name": self.video_name,
                "created_at": datetime.now().isoformat(),
                "total_events": 0,
                "events": []
            }
    
    def add_event(self, event_timestamp: float, 
                  segment_offset_before: float = 3.0,
                  segment_offset_after: float = 3.0,
                  **kwargs) -> Dict[str, Any]:
        """
        Ajoute et traite un nouvel événement
        
        Args:
            event_timestamp: Timestamp de l'événement en secondes
            segment_offset_before: Offset avant l'événement
            segment_offset_after: Offset après l'événement
            **kwargs: Autres paramètres pour la pipeline
            
        Returns:
            Résultats du traitement de l'événement
        """
        event_id = f"event_{int(event_timestamp)}s"
        
        print(f"🎯 Traitement de l'événement: {event_id}")
        print(f"   ⏰ Timestamp: {event_timestamp}s")
        
        # Vérifier si l'événement existe déjà
        existing_event = self._find_event_by_id(event_id)
        if existing_event:
            print(f"   ⚠️ Événement {event_id} existe déjà")
            return existing_event
        
        try:
            # Extraire les paramètres segment_offset_* des kwargs pour éviter les conflits
            pipeline_kwargs = kwargs.copy()
            
            # Utiliser les valeurs des kwargs si présentes, sinon les paramètres par défaut
            segment_offset_before_seconds = kwargs.get('segment_offset_before_seconds', segment_offset_before)
            segment_offset_after_seconds = kwargs.get('segment_offset_after_seconds', segment_offset_after)
            
            # Supprimer ces paramètres des kwargs pour éviter les conflits
            pipeline_kwargs.pop('segment_offset_before_seconds', None)
            pipeline_kwargs.pop('segment_offset_after_seconds', None)
            
            # Vérifier s'il y a des annotations valides AVANT de créer toute config
            if not self._has_valid_annotations_for_event(
                event_timestamp, 
                segment_offset_before_seconds, 
                segment_offset_after_seconds
            ):
                print(f"   ❌ Événement {event_id} ignoré - pas de tracking possible")
                return None
            
            # Créer et exécuter la pipeline pour cet événement
            pipeline = EVA2SportPipeline(
                self.video_name,
                event_timestamp_seconds=event_timestamp,
                segment_offset_before_seconds=segment_offset_before_seconds,
                segment_offset_after_seconds=segment_offset_after_seconds,
                **pipeline_kwargs
            )
            
            # Exécuter la pipeline
            results = pipeline.run_full_pipeline(
                force_extraction=True,
                export_video=True,
                video_params=kwargs.get('video_params', {
                    'fps': 5,
                    'show_minimap': True,
                    'cleanup_frames': True,
                    'force_regenerate': True
                })
            )
            
            if results['status'] == 'success':
                # Ajouter à l'index
                event_info = {
                    "event_id": event_id,
                    "timestamp_seconds": event_timestamp,
                    "frame_range": [
                        results.get('segment_start_frame', 0),
                        results.get('segment_end_frame', 0)
                    ],
                    "annotation_frame": results.get('reference_frame', 0),
                    "project_file": str(Path(results['export_paths']['json']).relative_to(self.video_output_dir)),
                    "video_file": str(Path(results['export_paths']['video']).relative_to(self.video_output_dir)) if 'video' in results['export_paths'] else None,
                    "objects_count": results['objects_tracked'],
                    "annotations_count": results['total_annotations'],
                    "frames_count": results['frames_extracted'],
                    "status": "completed",
                    "processed_at": datetime.now().isoformat(),
                    "config": {
                        "segment_offset_before": segment_offset_before_seconds,
                        "segment_offset_after": segment_offset_after_seconds,
                        "frame_interval": results['config']['frame_interval']
                    }
                }
                
                self.events_index["events"].append(event_info)
                self.events_index["total_events"] = len(self.events_index["events"])
                self.events_index["last_updated"] = datetime.now().isoformat()
                
                self._save_index()
                
                print(f"   ✅ Événement {event_id} traité avec succès")
                return event_info
            else:
                error_msg = results.get('error', 'Erreur inconnue')
                print(f"   ❌ Échec du traitement de l'événement {event_id}: {error_msg}")
                
                # Afficher les détails de l'erreur si disponibles
                if 'error_details' in results and results['error_details']:
                    print(f"   💥 Détails de l'erreur:")
                    for line in results['error_details'].split('\n'):
                        if line.strip():
                            print(f"      {line}")
                
                return None
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"   ❌ Erreur lors du traitement de l'événement {event_id}: {e}")
            print(f"   💥 Détails de l'erreur:")
            for line in error_details.split('\n'):
                if line.strip():
                    print(f"      {line}")
            return None
    
    def process_multiple_events(self, event_timestamps: Optional[List[float]] = None,
                               csv_file: Optional[Union[str, Path]] = None,
                               json_file: Optional[Union[str, Path]] = None,
                               csv_config: Optional[Dict[str, str]] = None,
                               validate_timestamps: bool = True,
                               **kwargs) -> Dict[str, Any]:
        """
        Traite plusieurs événements depuis différentes sources
        
        Args:
            event_timestamps: Liste manuelle des timestamps d'événements
            csv_file: Fichier CSV contenant les timestamps
            json_file: Fichier JSON contenant les timestamps
            csv_config: Configuration pour la lecture CSV (timestamp_column, filter_column, filter_value)
            validate_timestamps: Valider les timestamps contre la durée de la vidéo
            **kwargs: Paramètres communs pour tous les événements
            
        Returns:
            Résumé du traitement de tous les événements
        """
        # Récupérer les timestamps depuis la source appropriée
        timestamps = self._get_timestamps_from_source(
            event_timestamps, csv_file, json_file, csv_config, validate_timestamps
        )
        
        if not timestamps:
            print("❌ Aucun timestamp à traiter")
            return {
                "total_events": 0,
                "successful_events": 0,
                "failed_events": 0,
                "events_details": []
            }
        
        print(f"🚀 TRAITEMENT DE {len(timestamps)} ÉVÉNEMENTS")
        print("=" * 60)
        
        results = {
            "total_events": len(timestamps),
            "successful_events": 0,
            "failed_events": 0,
            "events_details": []
        }
        
        for i, timestamp in enumerate(timestamps):
            print(f"\n--- Événement {i+1}/{len(timestamps)} ---")
            
            event_result = self.add_event(timestamp, **kwargs)
            
            if event_result:
                results["successful_events"] += 1
                results["events_details"].append({
                    "timestamp": timestamp,
                    "status": "success",
                    "event_id": event_result["event_id"]
                })
            else:
                results["failed_events"] += 1
                results["events_details"].append({
                    "timestamp": timestamp,
                    "status": "failed",
                    "event_id": f"event_{int(timestamp)}s"
                })
        
        print(f"\n{'='*60}")
        print(f"📊 RÉSUMÉ DU TRAITEMENT MULTI-ÉVÉNEMENTS")
        print(f"   🎯 Total événements: {results['total_events']}")
        print(f"   ✅ Réussis: {results['successful_events']}")
        print(f"   ❌ Échecs: {results['failed_events']}")
        print(f"   📄 Index global: {self.index_file}")
        
        return results
    
    def get_events_list(self) -> List[Dict[str, Any]]:
        """Retourne la liste de tous les événements"""
        return self.events_index["events"]
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un événement par son ID"""
        return self._find_event_by_id(event_id)
    
    def _find_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Trouve un événement par son ID"""
        for event in self.events_index["events"]:
            if event["event_id"] == event_id:
                return event
        return None
    
    def _save_index(self):
        """Sauvegarde l'index des événements"""
        # S'assurer que le dossier parent existe
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.events_index, f, indent=2, ensure_ascii=False)
    
    def _has_valid_annotations_for_event(self, event_timestamp: float,
                                        segment_offset_before_seconds: float,
                                        segment_offset_after_seconds: float) -> bool:
        """
        Vérifie s'il y a des annotations valides dans l'intervalle de l'événement
        SANS créer de config temporaire pour éviter la création de dossiers
        
        Args:
            event_timestamp: Timestamp de l'événement
            segment_offset_before_seconds: Offset avant
            segment_offset_after_seconds: Offset après
            
        Returns:
            True si au moins une annotation est dans l'intervalle
        """
        import json
        import cv2
        
        # Charger la configuration du projet directement
        # Utiliser la config temporaire du timestamp_reader pour la résolution des chemins
        temp_config = self.timestamp_reader.config
        config_path = temp_config.config_path
        calib_path = temp_config.videos_dir / f"{self.video_name}_calib.json"
        objects_path = temp_config.videos_dir / f"{self.video_name}_objects.json"
        
        try:
            if calib_path.exists() and objects_path.exists():
                # Nouveau format : deux fichiers
                with open(calib_path, 'r', encoding='utf-8') as f:
                    calib_data = json.load(f)
                with open(objects_path, 'r', encoding='utf-8') as f:
                    objects_data = json.load(f)
                project_config = {**calib_data, **objects_data}
            elif config_path.exists():
                # Ancien format : un seul fichier
                with open(config_path, 'r', encoding='utf-8') as f:
                    project_config = json.load(f)
            else:
                print(f"   ❌ Configuration non trouvée pour {self.video_name}")
                return False
            
            # Récupérer les annotations initiales
            initial_annotations = project_config.get('initial_annotations', [])
            if not initial_annotations:
                print(f"   ⚠️ Aucune annotation initiale trouvée")
                return False
            
            # Récupérer le FPS de la vidéo directement
            video_path = temp_config.video_path
            if not video_path.exists():
                print(f"   ❌ Vidéo non trouvée: {video_path}")
                return False
                
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                print(f"   ❌ Impossible d'ouvrir la vidéo: {video_path}")
                return False
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            
            if fps <= 0:
                fps = 25.0  # Valeur par défaut
            
            # Calculer l'event_frame et l'intervalle
            event_frame = int(event_timestamp * fps)
            offset_before_frames = int((segment_offset_before_seconds or 0.0) * fps)
            offset_after_frames = int((segment_offset_after_seconds or 0.0) * fps)
            
            start_frame = max(0, event_frame - offset_before_frames)
            end_frame = event_frame + offset_after_frames
            
            print(f"   ⚠️ Vérification annotations pour événement:")
            print(f"   📍 Event frame: {event_frame}")
            print(f"   📍 Annotations disponibles: {[ann.get('frame', 0) for ann in initial_annotations]}")
            print(f"   📊 Intervalle événement: frames {start_frame} à {end_frame}")
            
            # Vérifier s'il y a au moins une annotation dans l'intervalle
            for ann in initial_annotations:
                annotation_frame = ann.get('frame', 0)
                if start_frame <= annotation_frame <= end_frame:
                    print(f"   ✅ Annotation valide trouvée: frame {annotation_frame}")
                    return True
            
            print(f"   ❌ Aucune annotation valide dans l'intervalle")
            return False
            
        except Exception as e:
            print(f"   ❌ Erreur lors de la vérification des annotations: {e}")
            return False
    
    def _get_timestamps_from_source(self, event_timestamps: Optional[List[float]] = None,
                                   csv_file: Optional[Union[str, Path]] = None,
                                   json_file: Optional[Union[str, Path]] = None,
                                   csv_config: Optional[Dict[str, str]] = None,
                                   validate_timestamps: bool = True) -> List[float]:
        """
        Récupère les timestamps depuis différentes sources
        
        Args:
            event_timestamps: Liste manuelle des timestamps
            csv_file: Fichier CSV contenant les timestamps
            json_file: Fichier JSON contenant les timestamps
            csv_config: Configuration pour la lecture CSV
            validate_timestamps: Valider les timestamps contre la durée de la vidéo
            
        Returns:
            Liste des timestamps à traiter
        """
        timestamps = []
        
        # Priorité 1: Liste manuelle
        if event_timestamps:
            print("📋 Utilisation de la liste manuelle de timestamps")
            timestamps = list(event_timestamps)
        
        # Priorité 2: Fichier CSV
        elif csv_file:
            print("📊 Lecture des timestamps depuis un fichier CSV")
            
            # Configuration par défaut pour CSV
            csv_config = csv_config or {}
            timestamp_column = csv_config.get('timestamp_column', 'Start time')
            filter_column = csv_config.get('filter_column')
            filter_value = csv_config.get('filter_value')
            
            try:
                timestamps = self.timestamp_reader.read_from_csv(
                    csv_file=csv_file,
                    timestamp_column=timestamp_column,
                    filter_column=filter_column,
                    filter_value=filter_value
                )
            except Exception as e:
                print(f"❌ Erreur lors de la lecture du CSV: {e}")
                return []
        
        # Priorité 3: Fichier JSON
        elif json_file:
            print("📄 Lecture des timestamps depuis un fichier JSON")
            
            try:
                timestamps = self.timestamp_reader.read_from_json(json_file)
            except Exception as e:
                print(f"❌ Erreur lors de la lecture du JSON: {e}")
                return []
        
        else:
            print("❌ Aucune source de timestamps fournie")
            return []
        
        # Validation des timestamps si demandée
        if validate_timestamps and timestamps:
            print("✅ Validation des timestamps contre la durée de la vidéo")
            timestamps = self.timestamp_reader.validate_timestamps(
                timestamps, self.video_name
            )
        
        return timestamps
    
    def process_events_from_csv(self, csv_file: Union[str, Path],
                               timestamp_column: str = 'Start time',
                               filter_column: Optional[str] = None,
                               filter_value: Optional[str] = None,
                               **kwargs) -> Dict[str, Any]:
        """
        Méthode de commodité pour traiter les événements depuis un CSV
        
        Args:
            csv_file: Fichier CSV contenant les timestamps
            timestamp_column: Nom de la colonne contenant les timestamps
            filter_column: Colonne à utiliser pour filtrer les lignes
            filter_value: Valeur à rechercher pour filtrer
            **kwargs: Paramètres communs pour tous les événements
            
        Returns:
            Résumé du traitement de tous les événements
        """
        csv_config = {
            'timestamp_column': timestamp_column,
            'filter_column': filter_column,
            'filter_value': filter_value
        }
        
        return self.process_multiple_events(
            csv_file=csv_file,
            csv_config=csv_config,
            **kwargs
        )
    
    def get_csv_info(self, csv_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Récupère les informations sur un fichier CSV
        
        Args:
            csv_file: Chemin vers le fichier CSV
            
        Returns:
            Informations sur le CSV
        """
        return self.timestamp_reader.get_csv_info(csv_file)
    
    def display_events_summary(self):
        """Affiche un résumé des événements"""
        print(f"\n📋 RÉSUMÉ DES ÉVÉNEMENTS - {self.video_name}")
        print("=" * 50)
        
        if not self.events_index["events"]:
            print("   ❌ Aucun événement traité")
            return
        
        print(f"   🎬 Vidéo: {self.video_name}")
        print(f"   📊 Total événements: {self.events_index['total_events']}")
        print(f"   📅 Créé: {self.events_index['created_at']}")
        if "last_updated" in self.events_index:
            print(f"   🔄 Dernière mise à jour: {self.events_index['last_updated']}")
        
        print(f"\n   📋 LISTE DES ÉVÉNEMENTS:")
        for i, event in enumerate(self.events_index["events"], 1):
            print(f"      {i}. {event['event_id']}")
            print(f"         ⏰ Timestamp: {event['timestamp_seconds']}s")
            print(f"         📍 Frame: {event['annotation_frame']}")
            print(f"         🎯 Objets: {event['objects_count']}")
            print(f"         📝 Annotations: {event['annotations_count']}")
            print(f"         ✅ Status: {event['status']}")
            print(f"         📄 Fichier: {event['project_file']}")
            if event['video_file']:
                print(f"         🎬 Vidéo: {event['video_file']}")
            print()
        
        print(f"   📄 Index global: {self.index_file}") 