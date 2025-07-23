"""
Optimiseur de mémoire GPU pour EVA2SPORT
Adapte automatiquement les paramètres SAM2 selon la mémoire disponible
"""

import torch
import gc
from typing import Dict, Any
from contextlib import contextmanager


class GPUMemoryOptimizer:
    """Optimiseur de mémoire GPU pour EVA2SPORT"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.initial_memory = 0
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Récupère les statistiques mémoire GPU en GB"""
        if self.device.type != "cuda":
            return {"allocated": 0.0, "reserved": 0.0, "free": 0.0, "total": 0.0}
        
        allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        reserved = torch.cuda.memory_reserved() / 1024**3    # GB
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        free = total - reserved
        
        return {
            "allocated": allocated,
            "reserved": reserved, 
            "free": free,
            "total": total
        }
    
    def clear_cache(self):
        """Nettoie le cache GPU"""
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
            gc.collect()
    
    def record_initial_memory(self):
        """Enregistre la mémoire initiale"""
        if self.device.type == "cuda":
            self.initial_memory = torch.cuda.memory_allocated()
    
    def get_memory_usage_since_start(self) -> float:
        """Retourne l'utilisation mémoire depuis le démarrage (GB)"""
        if self.device.type != "cuda":
            return 0.0
        
        current = torch.cuda.memory_allocated()
        return (current - self.initial_memory) / 1024**3
    
    @contextmanager
    def memory_context(self, clear_after: bool = True):
        """Context manager pour surveiller l'utilisation mémoire"""
        initial_stats = self.get_memory_stats()
        
        try:
            yield initial_stats
        finally:
            if clear_after:
                self.clear_cache()
    
    def optimize_sam2_memory_settings(self) -> Dict[str, bool]:
        """
        Détermine les meilleurs paramètres mémoire pour SAM2
        
        Returns:
            Dict avec offload_video_to_cpu et offload_state_to_cpu
        """
        stats = self.get_memory_stats()
        
        # Si pas de GPU, forcer CPU
        if self.device.type != "cuda":
            return {
                "offload_video_to_cpu": True,
                "offload_state_to_cpu": True
            }
        
        free_memory = stats["free"]
        
        # Si moins de 4GB libres, économiser au maximum
        if free_memory < 4.0:
            return {
                "offload_video_to_cpu": True,
                "offload_state_to_cpu": True
            }
        # Si moins de 8GB libres, économiser modérément  
        elif free_memory < 8.0:
            return {
                "offload_video_to_cpu": True,
                "offload_state_to_cpu": False
            }
        # Si beaucoup de mémoire, optimiser pour la performance
        else:
            return {
                "offload_video_to_cpu": False,
                "offload_state_to_cpu": False
            }
    
    def should_process_in_batches(self, total_frames: int, threshold_frames: int = 100) -> bool:
        """Détermine si le traitement doit être fait par batch"""
        stats = self.get_memory_stats()
        
        # Si peu de mémoire disponible et beaucoup de frames
        if stats["free"] < 6.0 and total_frames > threshold_frames:
            return True
        
        return False
    
    def get_memory_recommendation(self) -> str:
        """Retourne une recommandation textuelle sur l'état mémoire"""
        stats = self.get_memory_stats()
        
        if self.device.type != "cuda":
            return "CPU uniquement - pas de GPU détecté"
        
        free_memory = stats["free"]
        
        if free_memory >= 12.0:
            return f"Excellente ({free_memory:.1f}GB libres) - Performance optimale"
        elif free_memory >= 8.0:
            return f"Bonne ({free_memory:.1f}GB libres) - Performance élevée"
        elif free_memory >= 4.0:
            return f"Correcte ({free_memory:.1f}GB libres) - Quelques optimisations activées"
        else:
            return f"Limitée ({free_memory:.1f}GB libres) - Toutes les optimisations activées"


# Instance globale
gpu_optimizer = GPUMemoryOptimizer() 