"""
Configuration EVA2SPORT - Version Simplifiée
Environnement local/production uniquement
"""

from pathlib import Path
from typing import Optional
import torch


class Config:
    """Configuration centralisée pour EVA2SPORT"""
    
    def __init__(self, video_name: str, working_dir: Optional[str] = None,
                 segment_offset_before_seconds: Optional[float] = None,
                 segment_offset_after_seconds: Optional[float] = None,
                 **kwargs):
        """
        Configuration simple et prévisible
        
        Args:
            video_name: Nom de la vidéo (sans extension)
            working_dir: Répertoire de travail (défaut: répertoire courant)
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
        
        # SAM2
        self.SAM2_MODEL = "sam2.1_hiera_l"
        self.SAM2_CHECKPOINT = "sam2.1_hiera_large.pt"
        
        # Setup
        self._setup_paths()
        self._setup_device()
        self.setup_directories()
    
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
    
    @property
    def is_segment_mode(self) -> bool:
        """Détermine automatiquement si on est en mode segmentation"""
        return (self.SEGMENT_OFFSET_BEFORE_SECONDS is not None or 
                self.SEGMENT_OFFSET_AFTER_SECONDS is not None)
    
    def display_config(self):
        """Affichage simple de la configuration"""
        print(f"📋 Configuration EVA2SPORT:")
        print(f"   🎬 Vidéo: {self.VIDEO_NAME}")
        print(f"   📁 Répertoire: {self.working_dir}")
        print(f"   🖥️ Device: {self.device}")
        print(f"   ⏯️ Intervalle: {self.FRAME_INTERVAL}")
        
        if self.is_segment_mode:
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