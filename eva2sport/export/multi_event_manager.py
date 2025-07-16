"""
Gestionnaire d'événements multiples pour EVA2SPORT
Gère l'index global et les fichiers séparés par événement
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import Config
from ..pipeline import EVA2SportPipeline


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
                print(f"   ❌ Échec du traitement de l'événement {event_id}: {results['error']}")
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur lors du traitement de l'événement {event_id}: {e}")
            return None
    
    def process_multiple_events(self, event_timestamps: List[float], 
                               **kwargs) -> Dict[str, Any]:
        """
        Traite plusieurs événements
        
        Args:
            event_timestamps: Liste des timestamps d'événements
            **kwargs: Paramètres communs pour tous les événements
            
        Returns:
            Résumé du traitement de tous les événements
        """
        print(f"🚀 TRAITEMENT DE {len(event_timestamps)} ÉVÉNEMENTS")
        print("=" * 60)
        
        results = {
            "total_events": len(event_timestamps),
            "successful_events": 0,
            "failed_events": 0,
            "events_details": []
        }
        
        for i, timestamp in enumerate(event_timestamps):
            print(f"\n--- Événement {i+1}/{len(event_timestamps)} ---")
            
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
        """Sauvegarde l'index global"""
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.events_index, f, indent=2, ensure_ascii=False)
    
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