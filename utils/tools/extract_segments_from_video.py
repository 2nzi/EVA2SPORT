import pandas as pd
import os
import subprocess
from pathlib import Path
from typing import List

def extract_video_segment_ffmpeg(video_path: str, start_time: float, duration: float, output_path: str) -> bool:
    """
    Extrait un segment vidéo avec FFmpeg
    
    Args:
        video_path: Chemin vers la vidéo source
        start_time: Temps de début en secondes
        duration: Durée du segment en secondes
        output_path: Chemin de sortie pour le segment
    
    Returns:
        True si l'extraction a réussi, False sinon
    """
    try:
        # Commande FFmpeg pour extraire le segment
        cmd = [
            'ffmpeg',
            '-i', video_path,  # Fichier d'entrée
            '-ss', str(start_time),  # Temps de début
            '-t', str(duration),  # Durée
            '-c', 'copy',  # Copie sans réencodage (plus rapide)
            '-avoid_negative_ts', 'make_zero',  # Éviter les timestamps négatifs
            '-y',  # Écraser le fichier de sortie s'il existe
            output_path
        ]
        
        # Exécuter la commande
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Segment extrait: {os.path.basename(output_path)} ({start_time:.1f}s, durée: {duration:.1f}s)")
            return True
        else:
            print(f"Erreur FFmpeg: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("Erreur: FFmpeg n'est pas installé ou n'est pas dans le PATH")
        print("Installez FFmpeg: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"Erreur lors de l'extraction du segment: {e}")
        return False

def get_video_duration_ffmpeg(video_path: str) -> float:
    """
    Obtient la durée d'une vidéo avec FFmpeg
    
    Args:
        video_path: Chemin vers la vidéo
        
    Returns:
        Durée en secondes
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            print(f"Erreur lors de l'obtention de la durée: {result.stderr}")
            return 0.0
            
    except Exception as e:
        print(f"Erreur: {e}")
        return 0.0

def extract_pdb_segments_from_csv(video_path: str, csv_file: str, output_dir: str, 
                                 offset_before: float = 10.0, offset_after: float = 15.0) -> None:
    """
    Extrait les segments vidéo pour les lignes contenant 'PdB' dans la colonne 'Row'
    
    Args:
        video_path: Chemin vers la vidéo source
        csv_file: Chemin vers le fichier CSV
        output_dir: Dossier de sortie pour les segments
        offset_before: Offset avant le timestamp (secondes)
        offset_after: Offset après le timestamp (secondes)
    """
    
    # Vérifier les fichiers d'entrée
    if not os.path.exists(video_path):
        print(f"Erreur: Fichier vidéo non trouvé: {video_path}")
        return
    
    if not os.path.exists(csv_file):
        print(f"Erreur: Fichier CSV non trouvé: {csv_file}")
        return
    
    # Créer le dossier de sortie
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Obtenir la durée de la vidéo
        video_duration = get_video_duration_ffmpeg(video_path)
        print(f"Durée de la vidéo: {video_duration:.1f}s")
        
        # Lire le fichier CSV
        print(f"Lecture du fichier CSV: {csv_file}...")
        df = pd.read_csv(csv_file)
        
        # Filtrer les lignes contenant 'PdB' dans la colonne 'Row'
        pdb_rows = df[df['Row'].str.contains('PdB', na=False)]
        
        if pdb_rows.empty:
            print("Aucune ligne contenant 'PdB' trouvée dans la colonne 'Row'")
            return
        
        print(f"Trouvé {len(pdb_rows)} segments contenant 'PdB'")
        
        # Récupérer le nom de la vidéo sans extension
        video_name = Path(video_path).stem
        
        successful_extractions = 0
        
        # Parcourir chaque ligne PdB
        for index, row in pdb_rows.iterrows():
            start_time = float(row['Start time'])
            duration = float(row['Duration'])
            row_value = row['Row']
            instance_number = int(row['Instance number'])
            
            # Calculer les temps avec offsets
            segment_start = max(0, start_time - offset_before)
            segment_duration = duration + offset_before + offset_after
            
            # Ajuster si on dépasse la durée de la vidéo
            if segment_start + segment_duration > video_duration:
                segment_duration = video_duration - segment_start
            
            # Créer le nom du fichier selon le format demandé
            # Format: nom_video_f[Row]_Tf[int(starttime)]s_f[Instance number].mp4
            output_filename = f"{video_name}_f{row_value}_Tf{int(start_time)}s_f{instance_number}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Extraction du segment {successful_extractions + 1}/{len(pdb_rows)}: {row_value} - {start_time:.1f}s...")
            
            if extract_video_segment_ffmpeg(video_path, segment_start, segment_duration, output_path):
                successful_extractions += 1
        
        print(f"\nExtraction terminée: {successful_extractions}/{len(pdb_rows)} segments PdB extraits")
        print(f"Segments sauvegardés dans: {output_dir}")
        
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier CSV: {e}")

def read_timestamps_from_excel(excel_file: str, sheet_name: str = None, timestamp_column: str = 'timestamp') -> List[float]:
    """
    Lit les timestamps depuis un fichier Excel
    
    Args:
        excel_file: Chemin vers le fichier Excel
        sheet_name: Nom de la feuille Excel (None pour la première feuille)
        timestamp_column: Nom de la colonne contenant les timestamps
    
    Returns:
        Liste des timestamps en secondes
    """
    try:
        # Lire le fichier Excel
        if sheet_name:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
        else:
            df = pd.read_excel(excel_file)
        
        # Vérifier si la colonne existe
        if timestamp_column not in df.columns:
            print(f"Colonnes disponibles: {list(df.columns)}")
            raise ValueError(f"Colonne '{timestamp_column}' non trouvée dans le fichier Excel")
        
        # Extraire les timestamps
        timestamps = df[timestamp_column].tolist()
        
        # Convertir en secondes si nécessaire
        timestamps_seconds = []
        for ts in timestamps:
            if pd.isna(ts):
                continue
            
            # Si c'est une chaîne au format "mm:ss" ou "hh:mm:ss"
            if isinstance(ts, str) and ':' in ts:
                time_parts = ts.split(':')
                if len(time_parts) == 2:  # mm:ss
                    minutes, seconds = map(float, time_parts)
                    timestamps_seconds.append(minutes * 60 + seconds)
                elif len(time_parts) == 3:  # hh:mm:ss
                    hours, minutes, seconds = map(float, time_parts)
                    timestamps_seconds.append(hours * 3600 + minutes * 60 + seconds)
            else:
                # Si c'est déjà un nombre (secondes)
                timestamps_seconds.append(float(ts))
        
        return timestamps_seconds
    
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Excel: {e}")
        return []

def extract_segments_from_video(video_path: str, excel_file: str, output_dir: str, 
                              offset_before: float = 10.0, offset_after: float = 15.0,
                              sheet_name: str = None, timestamp_column: str = 'timestamp') -> None:
    """
    Extrait plusieurs segments vidéo basés sur les timestamps Excel
    
    Args:
        video_path: Chemin vers la vidéo source
        excel_file: Chemin vers le fichier Excel avec les timestamps
        output_dir: Dossier de sortie pour les segments
        offset_before: Offset avant le timestamp (secondes)
        offset_after: Offset après le timestamp (secondes)
        sheet_name: Nom de la feuille Excel
        timestamp_column: Nom de la colonne des timestamps
    """
    
    # Vérifier les fichiers d'entrée
    if not os.path.exists(video_path):
        print(f"Erreur: Fichier vidéo non trouvé: {video_path}")
        return
    
    if not os.path.exists(excel_file):
        print(f"Erreur: Fichier Excel non trouvé: {excel_file}")
        return
    
    # Créer le dossier de sortie
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Lire les timestamps
    print(f"Lecture des timestamps depuis {excel_file}...")
    timestamps = read_timestamps_from_excel(excel_file, sheet_name, timestamp_column)
    
    if not timestamps:
        print("Aucun timestamp trouvé dans le fichier Excel")
        return
    
    print(f"Trouvé {len(timestamps)} timestamps")
    
    # Extraire les segments
    video_name = Path(video_path).stem
    successful_extractions = 0
    
    for i, timestamp in enumerate(timestamps, 1):
        start_time = timestamp - offset_before
        duration = offset_before + offset_after
        
        output_filename = f"{video_name}_segment_{i:03d}_{timestamp:.1f}s.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Extraction du segment {i}/{len(timestamps)}: {timestamp:.1f}s...")
        
        if extract_video_segment_ffmpeg(video_path, start_time, duration, output_path):
            successful_extractions += 1
    
    print(f"\nExtraction terminée: {successful_extractions}/{len(timestamps)} segments extraits")
    print(f"Segments sauvegardés dans: {output_dir}")

# Exemple d'utilisation
if __name__ == "__main__":
    # Définir les paramètres directement ici
    video_path = r"C:\Users\antoi\Documents\Work_Learn\Stage-Rennes\DATA\FFF\SD\SD_13_06_2025_cam1.mp4"
    csv_file = r"C:\Users\antoi\Documents\Work_Learn\Stage-Rennes\DATA\FFF\SD\Timeline_g_SD.csv"
    output_dir = r"C:\Users\antoi\Documents\Work_Learn\Stage-Rennes\DATA\FFF\SD\segments_pdb_extraits"
    
    # Appeler la nouvelle fonction pour extraire les segments PdB
    extract_pdb_segments_from_csv(
        video_path=video_path,
        csv_file=csv_file,
        output_dir=output_dir,
        offset_before=10.0,  # 10 secondes avant
        offset_after=15.0    # 15 secondes après
    )


#pandas pathlib2