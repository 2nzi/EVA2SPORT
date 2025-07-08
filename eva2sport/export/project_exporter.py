"""
Exporteur de projets EVA2SPORT - Version Simplifiée
"""

import json
from pathlib import Path
from typing import Dict, Any

from ..config import Config


class ProjectExporter:
    """Exporteur pour sauvegarder et visualiser les projets"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def save_project_json(self, project_data: Dict[str, Any], 
                         compact: bool = True) -> Path:
        """Sauvegarde le projet au format JSON"""
        
        print(f"💾 Sauvegarde du projet JSON...")
        
        # Sauvegarde principale (formatée)
        json_path = self.config.output_json_path
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarde compacte (optionnelle)
        if compact:
            compact_path = self.config.output_dir / f"{self.config.VIDEO_NAME}_project_compact.json"
            with open(compact_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, separators=(',', ':'), ensure_ascii=False)
        
        json_size = json_path.stat().st_size / 1024**2  # MB
        print(f"✅ JSON sauvé: {json_path} ({json_size:.1f}MB)")
        
        return json_path
    
    def create_visualizations(self, project_data: Dict[str, Any]) -> Dict[str, Path]:
        """Crée des visualisations du projet"""
        
        print("🎨 Création des visualisations...")
        
        viz_paths = {
            'summary_report': self.config.output_dir / f"{self.config.VIDEO_NAME}_summary.txt"
        }
        
        self._create_summary_report(project_data, viz_paths['summary_report'])
        
        print(f"✅ Visualisations créées: {len(viz_paths)} fichiers")
        return viz_paths
    
    def display_final_statistics(self, project_data: Dict[str, Any]) -> None:
        """Affiche les statistiques finales du projet"""
        
        total_annotations = sum(len(annotations) for annotations in project_data['annotations'].values())
        unique_frames = len(project_data['annotations'])
        
        json_size = 0
        if self.config.output_json_path.exists():
            json_size = self.config.output_json_path.stat().st_size / 1024**2
        
        print(f"\n📊 RÉSULTATS FINAUX:")
        print(f"   🎬 Frames originales: {project_data['metadata']['frame_count_original']:,}")
        print(f"   🎬 Frames traitées: {project_data['metadata']['frame_count_processed']:,}")
        print(f"   📍 Frames avec annotations: {unique_frames:,}")
        print(f"   📍 Annotations totales: {total_annotations:,}")
        print(f"   🎯 Objets suivis: {len(project_data['objects'])}")
        print(f"   ⏯️  Intervalle frames: {project_data['metadata']['frame_interval']}")
        print(f"   📄 Taille JSON: {json_size:.1f}MB")
        print(f"   📁 Dossier sortie: {self.config.output_dir}")
        
        # Types d'objets
        if project_data['objects']:
            type_counts = {}
            for obj_data in project_data['objects'].values():
                obj_type = obj_data.get('type', 'unknown')
                type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            print(f"   🏷️  Types d'objets: {dict(type_counts)}")
    
    def cleanup_temporary_files(self) -> None:
        """Nettoie les fichiers temporaires (optionnel)"""
        
        print("🧹 Informations de nettoyage...")
        
        frame_count = len(list(self.config.frames_dir.glob("*.jpg")))
        if frame_count > 0:
            frame_size = sum(f.stat().st_size for f in self.config.frames_dir.glob("*.jpg")) / 1024**2
            print(f"   🖼️  Frames extraites: {frame_count} fichiers ({frame_size:.1f}MB)")
            print(f"   💡 Pour libérer l'espace: rm -rf {self.config.frames_dir}")
            print(f"   💡 Ré-extraction possible avec FORCE_EXTRACTION=True")
    
    def _create_summary_report(self, project_data: Dict[str, Any], report_path: Path) -> None:
        """Crée un rapport de résumé texte"""
        
        total_annotations = sum(len(annotations) for annotations in project_data['annotations'].values())
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"EVA2SPORT - Rapport de Tracking\n")
            f.write(f"================================\n\n")
            f.write(f"Vidéo: {project_data['video']}\n")
            f.write(f"Date: {project_data['metadata']['created_at']}\n\n")
            f.write(f"Statistiques:\n")
            f.write(f"- Frames originales: {project_data['metadata']['frame_count_original']}\n")
            f.write(f"- Frames traitées: {project_data['metadata']['frame_count_processed']}\n")
            f.write(f"- Frames annotées: {len(project_data['annotations'])}\n")
            f.write(f"- Annotations totales: {total_annotations}\n")
            f.write(f"- Objets suivis: {len(project_data['objects'])}\n\n")
            
            f.write(f"Objets:\n")
            for obj_id, obj_data in project_data['objects'].items():
                f.write(f"- ID {obj_id}: {obj_data['type']}")
                if obj_data.get('team'):
                    f.write(f" (équipe: {obj_data['team']})")
                if obj_data.get('jersey_number'):
                    f.write(f" (n°{obj_data['jersey_number']})")
                f.write(f"\n")
        
        print(f"   📄 Rapport créé: {report_path}")