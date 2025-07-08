"""
Test de l'API EVA2SPORT simple
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import eva2sport

# Test ultra-simple (une fois que tout fonctionne)
def test_ultra_simple():
    video_name = "SD_13_06_2025_cam1_PdB_S1_T959s_1"
    
    # UNE SEULE LIGNE pour tout faire ! 🎉
    results = eva2sport.track_video(video_name)
    
    print(f"🎉 Terminé !")
    print(f"📄 JSON: {results['export_paths']['json']}")
    print(f"📊 {results['frames_annotated']} frames traitées")
    print(f"🎯 {results['objects_tracked']} objets suivis")

if __name__ == "__main__":
    test_ultra_simple()