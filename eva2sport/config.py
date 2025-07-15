"""
Configuration EVA2SPORT - Version Simplifiée
Environnement local/production uniquement
"""

from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
import torch


@dataclass
class EventInterval:
    """Représente un intervalle d'event avec ses bornes"""
    event_frame: int
    start_frame: int
    end_frame: int
    annotation_frame: Optional[int] = None
    
    def contains_annotation(self, annotation_frame: int) -> bool:
        """Vérifie si l'annotation est dans l'intervalle"""
        return self.start_frame <= annotation_frame <= self.end_frame
    
    def set_annotation(self, annotation_frame: int):
        """Définit la frame d'annotation après vérification"""
        if not self.contains_annotation(annotation_frame):
            raise ValueError(f"Frame d'annotation {annotation_frame} en dehors de l'intervalle [{self.start_frame}, {self.end_frame}]")
        self.annotation_frame = annotation_frame


class Config:
    """Configuration centralisée pour EVA2SPORT"""
    
    def __init__(self, video_name: str, working_dir: Optional[str] = None,
                 segment_offset_before_seconds: Optional[float] = None,
                 segment_offset_after_seconds: Optional[float] = None,
                 event_timestamp_seconds: Optional[float] = None,
                 **kwargs):
        """
        Configuration simple et prévisible
        
        Args:
            video_name: Nom de la vidéo (sans extension)
            working_dir: Répertoire de travail (défaut: répertoire courant)
            segment_offset_before_seconds: Offset avant en secondes (mode segment)
            segment_offset_after_seconds: Offset après en secondes (mode segment)
            event_timestamp_seconds: Timestamp de l'event en secondes (mode event)
        """
        # Base
        self.VIDEO_NAME = video_name
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        
        # Configuration par défaut
        self.FRAME_INTERVAL = kwargs.get('frame_interval', 3)
        self.EXTRACT_FRAMES = kwargs.get('extract_frames', True)
        self.FORCE_EXTRACTION = kwargs.get('force_extraction', False)
        
        # Segmentation - juste stocker les offsets
        self.SEGMENT_OFFSET_BEFORE_SECONDS = segment_offset_before_seconds
        self.SEGMENT_OFFSET_AFTER_SECONDS = segment_offset_after_seconds
        
        # Event mode
        self.event_timestamp_seconds = event_timestamp_seconds
        self.event_frame = None
        
        # SAM2
        self.SAM2_MODEL = "sam2.1_hiera_l"
        self.SAM2_CHECKPOINT = "sam2.1_hiera_large.pt"
        
        # Setup
        self._setup_paths()
        self._setup_device()
        self.setup_directories()
        
        # Initialiser event_frame après setup (besoin du FPS)
        if self.event_timestamp_seconds is not None:
            self.event_frame = self.seconds_to_frames(self.event_timestamp_seconds)
    
    def _setup_paths(self):
        """Chemins simples et prévisibles"""
        # Structure attendue : working_dir/data/videos/
        self.videos_dir = self.working_dir / "data" / "videos"
        self.checkpoints_dir = self.working_dir / "checkpoints"
        
        # Fichiers
        self.video_path = self.videos_dir / f"{self.VIDEO_NAME}.mp4"
        self.config_path = self.videos_dir / f"{self.VIDEO_NAME}_config.json"
        
        # Sortie
        self.output_dir = self.videos_dir / "outputs" / self.VIDEO_NAME
        self.frames_dir = self.output_dir / "frames"
        self.masks_dir = self.output_dir / "masks"
        self.output_json_path = self.output_dir / f"{self.VIDEO_NAME}_project.json"
        
        # Checkpoint
        self.checkpoint_path = self.checkpoints_dir / self.SAM2_CHECKPOINT
        self.model_config_path = f"configs/sam2.1/{self.SAM2_MODEL}.yaml"
    
    def _setup_device(self):
        """Device automatique"""
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
    
    def setup_directories(self):
        """Crée les dossiers nécessaires"""
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir.mkdir(exist_ok=True)
        self.masks_dir.mkdir(exist_ok=True)
        self.checkpoints_dir.mkdir(exist_ok=True)
    
    def validate_requirements(self) -> bool:
        """Valide que tous les prérequis sont présents"""
        issues = []
        
        if not self.video_path.exists():
            issues.append(f"Vidéo manquante: {self.video_path}")
        
        if not self.config_path.exists():
            issues.append(f"Config manquante: {self.config_path}")
        
        if not self.checkpoint_path.exists():
            issues.append(f"Checkpoint manquant: {self.checkpoint_path}")
        
        if issues:
            print("❌ Prérequis manquants:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Tous les prérequis sont présents")
        return True
    
    def get_closest_initial_annotation_frame(self, initial_annotations: List[Dict]) -> int:
        """Retourne la frame de l'annotation initiale la plus proche de l'event/target"""
        if not initial_annotations:
            return 0
        
        target_frame = self.event_frame if self.event_frame is not None else 0
        closest_ann = min(
            initial_annotations,
            key=lambda ann: abs(ann.get('frame', 0) - target_frame)
        )
        return closest_ann.get('frame', 0)
    
    def calculate_segment_bounds_and_anchor(self, reference_frame: int) -> Tuple[int, int, int]:
        """
        Calcule les bornes du segment et l'index d'ancrage de manière centralisée
        
        Returns:
            Tuple[start_frame, end_frame, anchor_frame_in_segment]
        """
        import cv2
        
        # Obtenir les informations vidéo
        cap = cv2.VideoCapture(str(self.video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        # Calculer les offsets en frames
        fps = self.get_video_fps()
        offset_before_frames = int((self.SEGMENT_OFFSET_BEFORE_SECONDS or 0.0) * fps)
        offset_after_frames = int((self.SEGMENT_OFFSET_AFTER_SECONDS or 0.0) * fps)
        
        # Calculer les bornes selon le mode
        if self.is_event_mode:
            # Mode event : bornes basées sur l'event
            start_frame = max(0, self.event_frame - offset_before_frames)
            end_frame = min(total_frames - 1, self.event_frame + offset_after_frames)
            
            print(f"   🎯 Calcul bounds (mode event):")
            print(f"      📍 Frame event: {self.event_frame}")
            print(f"      📍 Frame annotation: {reference_frame}")
            print(f"      📍 Segment: frames {start_frame} à {end_frame}")
        else:
            # Mode segment : bornes basées sur l'annotation
            start_frame = max(0, reference_frame - offset_before_frames)
            end_frame = min(total_frames - 1, reference_frame + offset_after_frames)
            
            print(f"   🎯 Calcul bounds (mode segmentation):")
            print(f"      📍 Frame annotation: {reference_frame}")
            print(f"      📍 Segment: frames {start_frame} à {end_frame}")
        
        # Calculer l'index dans le segment
        reference_frame_processed = reference_frame // self.FRAME_INTERVAL
        segment_start_processed = start_frame // self.FRAME_INTERVAL
        anchor_frame_in_segment = reference_frame_processed - segment_start_processed
        
        print(f"      📍 Segment start traité: {segment_start_processed}")
        print(f"      📍 Index dans segment: {anchor_frame_in_segment}")
        
        # Vérification des bornes
        if hasattr(self, 'extracted_frames_count') and self.extracted_frames_count > 0:
            if anchor_frame_in_segment < 0 or anchor_frame_in_segment >= self.extracted_frames_count:
                raise ValueError(f"❌ Index anchor {anchor_frame_in_segment} en dehors des frames disponibles [0, {self.extracted_frames_count - 1}]")
        
        return start_frame, end_frame, anchor_frame_in_segment

    @property
    def is_segment_mode(self) -> bool:
        """Détermine automatiquement si on est en mode segmentation"""
        return (self.SEGMENT_OFFSET_BEFORE_SECONDS is not None or 
                self.SEGMENT_OFFSET_AFTER_SECONDS is not None)
    
    @property
    def is_event_mode(self) -> bool:
        """Détermine si on est en mode event"""
        return self.event_timestamp_seconds is not None
    
    def create_event_interval(self, annotation_frame: int) -> EventInterval:
        """Crée l'intervalle d'event et vérifie que l'annotation est dedans"""
        if not self.is_event_mode:
            raise ValueError("Non configuré pour le mode event")
        
        fps = self.get_video_fps()
        
        # Calculer les bornes de l'intervalle event
        offset_before_frames = int((self.SEGMENT_OFFSET_BEFORE_SECONDS or 0.0) * fps)
        offset_after_frames = int((self.SEGMENT_OFFSET_AFTER_SECONDS or 0.0) * fps)
        
        start_frame = max(0, self.event_frame - offset_before_frames)
        end_frame = self.event_frame + offset_after_frames
        
        # Créer l'intervalle
        interval = EventInterval(
            event_frame=self.event_frame,
            start_frame=start_frame,
            end_frame=end_frame
        )
        
        # Vérifier et définir l'annotation
        interval.set_annotation(annotation_frame)
        
        # Logging
        print(f"🎯 Mode event - Intervalle créé:")
        print(f"   📍 Event timestamp: {self.event_timestamp_seconds}s (frame {self.event_frame})")
        print(f"   📍 Frame annotation: {annotation_frame}")
        print(f"   📊 Intervalle: frames {start_frame} à {end_frame}")
        print(f"   📉 Offset avant: {self.SEGMENT_OFFSET_BEFORE_SECONDS or 0.0}s ({offset_before_frames} frames)")
        print(f"   📈 Offset après: {self.SEGMENT_OFFSET_AFTER_SECONDS or 0.0}s ({offset_after_frames} frames)")
        
        return interval
    
    def create_segment_bounds(self, reference_frame: int) -> Tuple[int, int]:
        """Crée les bornes du segment pour une frame de référence (mode segment classique)"""
        if not self.is_segment_mode:
            raise ValueError("Non configuré pour le mode segment")
            
        fps = self.get_video_fps()
        offset_before_frames = int((self.SEGMENT_OFFSET_BEFORE_SECONDS or 0.0) * fps)
        offset_after_frames = int((self.SEGMENT_OFFSET_AFTER_SECONDS or 0.0) * fps)
        
        start_frame = max(0, reference_frame - offset_before_frames)
        end_frame = reference_frame + offset_after_frames
        
        return start_frame, end_frame
    
    def display_config(self):
        """Affichage simple de la configuration"""
        print(f"📋 Configuration EVA2SPORT:")
        print(f"   🎬 Vidéo: {self.VIDEO_NAME}")
        print(f"   📁 Répertoire: {self.working_dir}")
        print(f"   🖥️ Device: {self.device}")
        print(f"   ⏯️ Intervalle: {self.FRAME_INTERVAL}")
        
        if self.is_event_mode:
            print(f"   🎯 Mode: Event")
            print(f"   ⏰ Event timestamp: {self.event_timestamp_seconds}s")
            print(f"   📍 Event frame: {self.event_frame}")
            print(f"   📉 Offset avant: {self.SEGMENT_OFFSET_BEFORE_SECONDS or 0.0}s")
            print(f"   📈 Offset après: {self.SEGMENT_OFFSET_AFTER_SECONDS or 0.0}s")
        elif self.is_segment_mode:
            print(f"   🎯 Mode: Segmentation")
            print(f"   📉 Offset avant: {self.SEGMENT_OFFSET_BEFORE_SECONDS or 0.0}s")
            print(f"   📈 Offset après: {self.SEGMENT_OFFSET_AFTER_SECONDS or 0.0}s")
        else:
            print(f"   🎯 Mode: Vidéo complète")
    
    # Méthodes utilitaires (FPS, etc.) - comme avant mais sans logique Colab
    def get_video_fps(self) -> float:
        if not self.video_path.exists():
            return 25.0
        
        import cv2
        cap = cv2.VideoCapture(str(self.video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) if cap.isOpened() else 25.0
        cap.release()
        return fps if fps > 0 else 25.0
    
    def seconds_to_frames(self, seconds: float, fps: float = None) -> int:
        if fps is None:
            fps = self.get_video_fps()
        return int(round(seconds * fps))
    
    def get_segment_offsets_frames(self):
        """Calcule les offsets en frames"""
        if not self.is_segment_mode:
            raise ValueError("❌ Les offsets ne sont disponibles qu'en mode segmentation")
        
        fps = self.get_video_fps()
        offset_before = self.seconds_to_frames(self.SEGMENT_OFFSET_BEFORE_SECONDS or 0.0, fps)
        offset_after = self.seconds_to_frames(self.SEGMENT_OFFSET_AFTER_SECONDS or 0.0, fps)
        return offset_before, offset_after