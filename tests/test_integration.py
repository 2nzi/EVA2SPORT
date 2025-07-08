"""
Script de test pour l'extraction
"""

import sys
from pathlib import Path

# Ajouter le module eva2sport au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eva2sport.config import Config
from eva2sport.tracking.video_processor import VideoProcessor


def test_video_processor():
    """Test du processeur vidéo"""
    
    # Configuration
    config = Config("SD_13_06_2025_cam1_PdB_S1_T959s_1")
    config.EXTRACT_FRAMES = False  # Test sans extraction réelle
    
    # Processeur
    processor = VideoProcessor(config)
    
    print("🧪 Test du processeur vidéo...")
    print(f"✅ Processeur créé pour: {config.VIDEO_NAME}")
    
    # Test comptage frames existantes
    if config.frames_dir.exists():
        existing_count = processor.count_existing_frames()
        print(f"✅ Frames existantes: {existing_count}")
    
    print("✅ Tests processeur terminés")


if __name__ == "__main__":
    test_video_processor()