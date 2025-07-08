"""
Tests pour la configuration
"""

import pytest
from pathlib import Path
import sys

# Ajouter le module eva2sport au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eva2sport.config import Config


def test_config_creation():
    """Test création d'une configuration"""
    config = Config("test_video")
    
    assert config.VIDEO_NAME == "test_video"
    assert config.FRAME_INTERVAL == 3
    assert config.SEGMENT_MODE == True
    assert config.SEGMENT_OFFSET_BEFORE_SECONDS == 2.0
    

def test_config_paths():
    """Test génération des chemins"""
    config = Config("test_video")
    
    assert config.video_path.name == "test_video.mp4"
    assert config.config_path.name == "test_video_config.json"
    assert "test_video" in str(config.output_dir)


def test_config_segment_offsets():
    """Test calcul des offsets de segmentation"""
    config = Config("test_video")
    
    # Mock FPS
    config.get_video_fps = lambda: 25.0
    
    offset_before, offset_after = config.get_segment_offsets_frames()
    
    # 2 secondes * 25 FPS = 50 frames
    assert offset_before == 50
    assert offset_after == 50


if __name__ == "__main__":
    # Tests manuels
    print("🧪 Tests manuels...")
    
    config = Config("SD_13_06_2025_cam1_PdB_S1_T959s_1")
    print(f"✅ Config créée: {config.VIDEO_NAME}")
    
    config.display_config()
    print("✅ Tests terminés")