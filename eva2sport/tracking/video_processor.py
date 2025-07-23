"""
Processeur vidéo pour extraction de frames - Version Simplifiée
"""

import cv2
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from ..config import Config


class VideoProcessor:
    """Processeur vidéo pour extraction frames avec support segmentation"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def extract_all_frames(self, force_extraction: bool = False) -> int:
        """Extrait toutes les frames de la vidéo selon l'intervalle"""
        
        print(f"🎬 Extraction des frames...")
        print(f"   📹 Source: {self.config.video_path}")
        print(f"   📁 Destination: {self.config.frames_dir}")
        print(f"   ⏯️  Intervalle: {self.config.FRAME_INTERVAL}")

        # Vérification existence du fichier vidéo
        if not self.config.video_path.exists():
            raise FileNotFoundError(f"❌ Vidéo non trouvée: {self.config.video_path}")

        # Vérification si extraction déjà faite
        existing_frames = list(self.config.frames_dir.glob("*.jpg"))
        if existing_frames and not force_extraction:
            print(f"📂 {len(existing_frames)} frames déjà extraites - SKIP")
            return len(existing_frames)
        elif existing_frames and force_extraction:
            print(f"🔄 {len(existing_frames)} frames existantes - SUPPRESSION et ré-extraction...")
            for frame_file in existing_frames:
                frame_file.unlink()

        # Utiliser la méthode centralisée pour obtenir les informations vidéo
        video_info = self.config.get_video_info()
        total_frames = video_info['total_frames']
        fps = video_info['fps']

        print(f"📊 Vidéo: {total_frames} frames, {fps:.1f} FPS")
        print(f"📊 Frames à extraire: ~{total_frames // self.config.FRAME_INTERVAL}")

        from ..utils import video_context
        
        with video_context.open_video(self.config.video_path) as cap:
            extracted_count = 0
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Extraire seulement selon l'intervalle
                if frame_idx % self.config.FRAME_INTERVAL == 0:
                    output_idx = frame_idx // self.config.FRAME_INTERVAL
                    filename = self.config.frames_dir / f"{output_idx:05d}.jpg"
                    cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    extracted_count += 1

                    if extracted_count % 50 == 0:
                        progress = (frame_idx / total_frames) * 100
                        print(f"📊 Progrès: {extracted_count} frames extraites ({progress:.1f}%)")

                frame_idx += 1

        print(f"✅ {extracted_count} frames extraites")
        return extracted_count
    
    def extract_segment_frames(self, reference_frame: int, 
                              force_extraction: bool = False) -> int:
        """
        Extrait les frames du segment
        
        Args:
            reference_frame: Frame d'annotation de référence
            force_extraction: Force la ré-extraction même si les frames existent
        """
        
        # Utiliser la méthode centralisée pour obtenir les informations vidéo
        video_info = self.config.get_video_info()
        total_frames = video_info['total_frames']
        
        if self.config.is_event_mode:
            # Mode event : extraire l'intervalle [event-before, event+after]
            interval = self.config.create_event_interval(reference_frame)
            start_frame = max(0, interval.start_frame)
            end_frame = min(total_frames - 1, interval.end_frame)
            
            print(f"🎯 EXTRACTION MODE EVENT:")
            print(f"   📍 Event frame: {interval.event_frame}")
            print(f"   📍 Frame annotation: {reference_frame}")
            print(f"   🎬 Intervalle: frames {start_frame} à {end_frame}")
            
        else:
            # Mode segment classique : centré sur l'annotation
            start_frame, end_frame = self.config.create_segment_bounds(reference_frame)
            start_frame = max(0, start_frame)
            end_frame = min(total_frames - 1, end_frame)
            
            print(f"🎯 EXTRACTION MODE SEGMENT:")
            print(f"   📍 Frame référence: {reference_frame}")
            print(f"   🎬 Segment: frames {start_frame} à {end_frame}")
        
        return self._extract_segment_frames(
            start_frame, end_frame, force_extraction
        )
    
    def count_existing_frames(self) -> int:
        """Compte les frames existantes dans le dossier"""
        existing_frames = list(self.config.frames_dir.glob("*.jpg"))
        return len(existing_frames)
    
    def get_segment_info(self, reference_frame: int) -> Dict[str, Any]:
        """Récupère les informations du segment pour la frame de référence"""
        
        # Utiliser la méthode centralisée pour obtenir les informations vidéo
        video_info = self.config.get_video_info()
        total_frames = video_info['total_frames']
        
        if self.config.is_event_mode:
            # Mode event
            interval = self.config.create_event_interval(reference_frame)
            start_frame = max(0, interval.start_frame)
            end_frame = min(total_frames - 1, interval.end_frame)
        else:
            # Mode segment classique
            start_frame, end_frame = self.config.create_segment_bounds(reference_frame)
            start_frame = max(0, start_frame)
            end_frame = min(total_frames - 1, end_frame)
        
        processed_start_idx = start_frame // self.config.FRAME_INTERVAL
        processed_end_idx = end_frame // self.config.FRAME_INTERVAL
        
        return {
            'start_frame': start_frame,
            'end_frame': end_frame,
            'processed_start_idx': processed_start_idx,
            'processed_end_idx': processed_end_idx
        }
    
    def _calculate_segment_bounds(self, reference_frame: int, offset_before: int, 
                                offset_after: int, total_frames: int) -> Tuple[int, int, int, int]:
        """Calcule les bornes du segment vidéo"""
        
        start_frame = max(0, reference_frame - offset_before)
        end_frame = min(total_frames - 1, reference_frame + offset_after)
        
        processed_start_idx = start_frame // self.config.FRAME_INTERVAL
        processed_end_idx = end_frame // self.config.FRAME_INTERVAL
        
        print(f"🎯 CALCUL DES BORNES DE SEGMENTATION:")
        print(f"   📍 Frame de référence: {reference_frame}")
        print(f"   📉 Offset avant: {offset_before} frames")
        print(f"   📈 Offset après: {offset_after} frames")
        print(f"   🎬 Segment original: frames {start_frame} à {end_frame}")
        print(f"   🎬 Segment traité: indices {processed_start_idx} à {processed_end_idx}")
        
        return start_frame, end_frame, processed_start_idx, processed_end_idx
        
    def _extract_segment_frames(self, start_frame: int, end_frame: int, 
                            force_extraction: bool) -> int:
        """Extrait les frames du segment avec nommage séquentiel"""
        
        print(f"🎬 EXTRACTION DU SEGMENT:")
        print(f"   🎯 Segment: frames {start_frame} à {end_frame}")
        print(f"   ⏯️  Intervalle: {self.config.FRAME_INTERVAL}")
        
        # Calculer les frames attendues
        expected_frames = []
        sequential_idx = 0
        
        for frame_idx in range(start_frame, end_frame + 1, self.config.FRAME_INTERVAL):
            expected_frames.append((frame_idx, sequential_idx))
            sequential_idx += 1
        
        # NOUVEAU : Nettoyer complètement le dossier en mode segment
        all_existing_frames = list(self.config.frames_dir.glob("*.jpg"))
        
        if not force_extraction:
            # Vérifier si exactement les bonnes frames existent
            expected_files = [self.config.frames_dir / f"{seq_idx:05d}.jpg" 
                            for _, seq_idx in expected_frames]
            
            if (len(all_existing_frames) == len(expected_files) and 
                all(f.exists() for f in expected_files)):
                print(f"📂 {len(expected_files)} frames du segment déjà extraites - SKIP")
                return len(expected_files)
        
        # Nettoyage complet du dossier
        if all_existing_frames:
            print(f"🧹 Nettoyage du dossier: suppression de {len(all_existing_frames)} frames")
            for frame_file in all_existing_frames:
                frame_file.unlink()
        
        # Extraction des frames du segment
        from ..utils import video_context
        
        with video_context.open_video(self.config.video_path) as cap:
            extracted_count = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            for frame_idx in range(start_frame, end_frame + 1):
                ret, frame = cap.read()
                if not ret:
                    break
                
                if (frame_idx - start_frame) % self.config.FRAME_INTERVAL == 0:
                    sequential_idx = (frame_idx - start_frame) // self.config.FRAME_INTERVAL
                    filename = self.config.frames_dir / f"{sequential_idx:05d}.jpg"
                    
                    cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    extracted_count += 1
            
            print(f"✅ {extracted_count} frames du segment extraites")
            return extracted_count