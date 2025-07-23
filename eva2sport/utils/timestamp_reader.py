"""
Lecteur de timestamps pour EVA2SPORT
Supporte différentes sources : CSV, listes manuelles, etc.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from ..config import Config


class TimestampReader:
    """Lecteur de timestamps depuis différentes sources"""
    
    def __init__(self, config: Optional['Config'] = None):
        """
        Initialise le lecteur de timestamps
        
        Args:
            config: Configuration EVA2SPORT (optionnel)
        """
        self.config = config
        if config:
            self.working_dir = config.working_dir
            self.videos_dir = config.videos_dir
        else:
            # Fallback si pas de config
            self.working_dir = Path.cwd()
            self.videos_dir = self.working_dir / "data" / "videos"
    
    def read_from_csv(self, csv_file: Union[str, Path], 
                     timestamp_column: str = 'Start time',
                     filter_column: Optional[str] = None,
                     filter_value: Optional[str] = None,
                     sort_timestamps: bool = True) -> List[float]:
        """
        Extrait les timestamps depuis un fichier CSV
        
        Args:
            csv_file: Nom du fichier CSV (dans data/videos/) ou chemin complet
            timestamp_column: Nom de la colonne contenant les timestamps (en secondes)
            filter_column: Colonne à utiliser pour filtrer les lignes (optionnel)
            filter_value: Valeur à rechercher pour filtrer (optionnel)
            sort_timestamps: Trier les timestamps par ordre croissant
            
        Returns:
            Liste des timestamps (float)
        """
        # Utiliser la config pour résoudre le chemin si disponible
        if self.config:
            csv_path = self.config.resolve_data_file_path(csv_file)
        else:
            # Fallback si pas de config
            csv_path = Path(csv_file)
            if not csv_path.is_absolute() and csv_path.parent == Path('.'):
                csv_path = self.videos_dir / csv_path
            elif not csv_path.is_absolute():
                csv_path = self.working_dir / csv_path
        
        if not csv_path.exists():
            raise FileNotFoundError(f"❌ Fichier CSV non trouvé: {csv_path}")
        
        print(f"📊 Lecture des timestamps depuis: {csv_path.name}")
        print(f"   📁 Chemin: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            
            # Vérifier que la colonne timestamp existe
            if timestamp_column not in df.columns:
                raise ValueError(f"❌ Colonne '{timestamp_column}' non trouvée dans le CSV")
            
            # Filtrer les lignes si demandé
            if filter_column and filter_value:
                if filter_column not in df.columns:
                    print(f"   ⚠️ Colonne de filtrage '{filter_column}' non trouvée - pas de filtrage")
                else:
                    initial_count = len(df)
                    df = df[df[filter_column].astype(str).str.contains(filter_value, na=False)]
                    print(f"   🔍 Filtrage '{filter_column}' = '{filter_value}': {initial_count} → {len(df)} lignes")
            
            # Extraire les timestamps
            timestamps = df[timestamp_column].dropna().astype(float).tolist()
            
            if sort_timestamps:
                timestamps.sort()
            
            print(f"   ✅ {len(timestamps)} timestamps extraits")
            if timestamps:
                print(f"   📊 Plage: {min(timestamps):.1f}s → {max(timestamps):.1f}s")
            
            return timestamps
            
        except Exception as e:
            raise RuntimeError(f"❌ Erreur lors de la lecture du CSV: {e}")
    
    def read_from_json(self, json_file: Union[str, Path], 
                      timestamp_key: str = 'timestamps') -> List[float]:
        """
        Extrait les timestamps depuis un fichier JSON
        
        Args:
            json_file: Nom du fichier JSON (dans data/videos/) ou chemin complet
            timestamp_key: Clé contenant les timestamps
            
        Returns:
            Liste des timestamps (float)
        """
        # Utiliser la config pour résoudre le chemin si disponible
        if self.config:
            json_path = self.config.resolve_data_file_path(json_file)
        else:
            # Fallback si pas de config
            json_path = Path(json_file)
            if not json_path.is_absolute() and json_path.parent == Path('.'):
                json_path = self.videos_dir / json_path
            elif not json_path.is_absolute():
                json_path = self.working_dir / json_path
        
        if not json_path.exists():
            raise FileNotFoundError(f"❌ Fichier JSON non trouvé: {json_path}")
        
        print(f"📊 Lecture des timestamps depuis: {json_path.name}")
        print(f"   📁 Chemin: {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if timestamp_key not in data:
                raise ValueError(f"❌ Clé '{timestamp_key}' non trouvée dans le JSON")
            
            timestamps = [float(ts) for ts in data[timestamp_key]]
            timestamps.sort()
            
            print(f"   ✅ {len(timestamps)} timestamps extraits")
            if timestamps:
                print(f"   📊 Plage: {min(timestamps):.1f}s → {max(timestamps):.1f}s")
            
            return timestamps
            
        except Exception as e:
            raise RuntimeError(f"❌ Erreur lors de la lecture du JSON: {e}")
    
    def validate_timestamps(self, timestamps: List[float], 
                          video_name: str) -> List[float]:
        """
        Valide les timestamps par rapport à la durée de la vidéo
        
        Args:
            timestamps: Liste des timestamps
            video_name: Nom de la vidéo pour vérifier la durée
            
        Returns:
            Liste des timestamps valides
        """
        if not timestamps:
            return []
        
        # Récupérer la durée de la vidéo
        if self.config and self.config.VIDEO_NAME == video_name:
            video_path = self.config.video_path
        else:
            video_path = self.videos_dir / f"{video_name}.mp4"
        
        if not video_path.exists():
            print(f"   ⚠️ Impossible de valider les timestamps - vidéo non trouvée: {video_path}")
            return timestamps
        
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"   ⚠️ Impossible de valider les timestamps - vidéo non lisible")
            cap.release()
            return timestamps
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if fps > 0 and total_frames > 0:
            video_duration = total_frames / fps
            
            # Filtrer les timestamps valides
            valid_timestamps = [ts for ts in timestamps if 0 <= ts <= video_duration]
            invalid_count = len(timestamps) - len(valid_timestamps)
            
            if invalid_count > 0:
                print(f"   ⚠️ {invalid_count} timestamps invalides ignorés (durée vidéo: {video_duration:.1f}s)")
            
            print(f"   ✅ {len(valid_timestamps)} timestamps valides")
            return valid_timestamps
        
        return timestamps
    
    def get_csv_info(self, csv_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Récupère les informations sur un fichier CSV
        
        Args:
            csv_file: Nom du fichier CSV (dans data/videos/) ou chemin complet
            
        Returns:
            Dictionnaire avec les informations du CSV
        """
        # Utiliser la config pour résoudre le chemin si disponible
        if self.config:
            csv_path = self.config.resolve_data_file_path(csv_file)
        else:
            # Fallback si pas de config
            csv_path = Path(csv_file)
            if not csv_path.is_absolute() and csv_path.parent == Path('.'):
                csv_path = self.videos_dir / csv_path
            elif not csv_path.is_absolute():
                csv_path = self.working_dir / csv_path
        
        if not csv_path.exists():
            raise FileNotFoundError(f"❌ Fichier CSV non trouvé: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            
            return {
                'file_path': str(csv_path),
                'columns': list(df.columns),
                'rows_count': len(df),
                'sample_data': df.head().to_dict('records') if len(df) > 0 else []
            }
            
        except Exception as e:
            raise RuntimeError(f"❌ Erreur lors de la lecture du CSV: {e}")
    
    @staticmethod
    def create_sample_csv(output_path: Union[str, Path], 
                         sample_timestamps: List[float],
                         additional_columns: Optional[Dict[str, List]] = None):
        """
        Crée un fichier CSV d'exemple avec des timestamps
        
        Args:
            output_path: Chemin de sortie pour le CSV
            sample_timestamps: Liste des timestamps d'exemple
            additional_columns: Colonnes supplémentaires à ajouter
        """
        data = {'Start time': sample_timestamps}
        
        if additional_columns:
            for col_name, col_data in additional_columns.items():
                if len(col_data) == len(sample_timestamps):
                    data[col_name] = col_data
                else:
                    print(f"   ⚠️ Colonne '{col_name}' ignorée - taille incompatible")
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        print(f"   ✅ CSV d'exemple créé: {output_path}") 