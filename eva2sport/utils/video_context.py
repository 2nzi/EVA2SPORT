"""
Context manager pour optimiser l'accès aux fichiers vidéo
Évite les ouvertures répétées de cv2.VideoCapture
"""

import cv2
from pathlib import Path
from typing import Dict, Any, Union
from contextlib import contextmanager


class VideoContextManager:
    """Gestionnaire de contexte pour les accès vidéo optimisés"""
    
    def __init__(self):
        self._video_cache = {}
    
    @contextmanager
    def open_video(self, video_path: Union[str, Path]):
        """
        Context manager pour ouvrir une vidéo
        
        Args:
            video_path: Chemin vers la vidéo
            
        Yields:
            cv2.VideoCapture: Instance de capture vidéo
        """
        video_path = str(video_path)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"❌ Impossible d'ouvrir la vidéo: {video_path}")
        
        try:
            yield cap
        finally:
            cap.release()
    
    def get_video_info_cached(self, video_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Récupère les informations vidéo avec mise en cache
        
        Args:
            video_path: Chemin vers la vidéo
            
        Returns:
            Dictionary avec fps, total_frames, width, height, duration_seconds
        """
        video_path = str(video_path)
        
        # Vérifier le cache
        if video_path in self._video_cache:
            return self._video_cache[video_path]
        
        # Valeurs par défaut si vidéo non trouvée
        if not Path(video_path).exists():
            info = {
                'fps': 25.0,
                'total_frames': 0,
                'width': 1920,
                'height': 1080,
                'duration_seconds': 0.0
            }
            self._video_cache[video_path] = info
            return info
        
        # Extraire les informations
        with self.open_video(video_path) as cap:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Valeurs par défaut si invalides
            fps = fps if fps > 0 else 25.0
            duration_seconds = total_frames / fps if fps > 0 and total_frames > 0 else 0.0
            
            info = {
                'fps': fps,
                'total_frames': total_frames,
                'width': width,
                'height': height,
                'duration_seconds': duration_seconds
            }
            
            # Mettre en cache
            self._video_cache[video_path] = info
            return info
    
    def clear_cache(self):
        """Vide le cache des informations vidéo"""
        self._video_cache.clear()


# Instance globale pour partage
video_context = VideoContextManager() 