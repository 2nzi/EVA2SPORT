"""
Système de logging centralisé pour EVA2SPORT
Remplace les print() statements par un logging structuré
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class EVA2SportLogger:
    """Logger centralisé avec formatage spécial pour EVA2SPORT"""
    
    def __init__(self, name: str = "EVA2SPORT", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Éviter les doublons de handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configure les handlers de logging"""
        
        # Formatter avec emojis
        formatter = logging.Formatter(
            '%(message)s'  # Format simple pour garder les emojis
        )
        
        # Handler console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def setup_file_logging(self, log_dir: Optional[Path] = None):
        """Active le logging vers fichier"""
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"eva2sport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s'
            ))
            self.logger.addHandler(file_handler)
    
    # Méthodes de logging avec formatage EVA2SPORT
    def step(self, step_num: int, total_steps: int, message: str):
        """Log d'étape de pipeline"""
        self.logger.info(f"🔄 Étape {step_num}/{total_steps}: {message}")
    
    def success(self, message: str):
        """Log de succès"""
        self.logger.info(f"✅ {message}")
    
    def error(self, message: str):
        """Log d'erreur"""
        self.logger.error(f"❌ {message}")
    
    def warning(self, message: str):
        """Log d'avertissement"""
        self.logger.warning(f"⚠️ {message}")
    
    def info(self, message: str):
        """Log d'information"""
        self.logger.info(f"🎯 {message}")
    
    def debug(self, message: str):
        """Log de debug"""
        self.logger.debug(f"🔍 {message}")
    
    def progress(self, message: str):
        """Log de progression"""
        self.logger.info(f"📊 {message}")
    
    def config(self, message: str):
        """Log de configuration"""
        self.logger.info(f"📋 {message}")
    
    def video(self, message: str):
        """Log vidéo"""
        self.logger.info(f"🎬 {message}")
    
    def tracking(self, message: str):  
        """Log tracking"""
        self.logger.info(f"🤖 {message}")
    
    def export(self, message: str):
        """Log export"""
        self.logger.info(f"💾 {message}")
    
    def memory(self, message: str):
        """Log mémoire GPU"""
        self.logger.info(f"💾 {message}")
    
    def pipeline_start(self, video_name: str):
        """Log de début de pipeline"""
        self.logger.info(f"🚀 PIPELINE EVA2SPORT DÉMARRÉE: {video_name}")
        self.logger.info("=" * 60)
    
    def pipeline_end(self, success: bool = True):
        """Log de fin de pipeline"""
        if success:
            self.logger.info("=" * 60)
            self.logger.info("🎉 PIPELINE TERMINÉE AVEC SUCCÈS!")
        else:
            self.logger.info("=" * 60)
            self.logger.error("💥 PIPELINE ÉCHOUÉE!")


# Instance globale
eva_logger = EVA2SportLogger() 