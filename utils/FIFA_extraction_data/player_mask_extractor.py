import matplotlib
matplotlib.use('Agg')  # Utiliser le backend 'Agg' non-interactif
import matplotlib.pyplot as plt
import numpy as np
import cv2
import os
from pathlib import Path
import torch
from smplx import SMPL

class PlayerMaskExtractor:
    def __init__(self, camera_path, poses_path, video_path, output_dir, smpl_model_path, save_empty_masks=True):
        """
        Initialise l'extracteur de masques de joueurs.
        
        Args:
            camera_path: Chemin vers le fichier .npz des données caméra
            poses_path: Chemin vers le fichier .npz des poses
            video_path: Chemin vers la vidéo source
            output_dir: Dossier de sortie pour les masques
            smpl_model_path: Chemin vers le modèle SMPL
            save_empty_masks: Si True, sauvegarde un masque noir et l'image quand un joueur est ignoré
        """
        self.camera_data = np.load(camera_path)
        self.poses_data = np.load(poses_path)
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.video_name = Path(video_path).stem
        self.save_empty_masks = save_empty_masks
        
        # Créer les dossiers de sortie
        self._create_output_directories()
        
        # Initialiser le modèle SMPL
        self.smpl = SMPL(
            model_path=smpl_model_path,
            gender='male',
            batch_size=1
        )
        
        # Charger les dimensions et le FPS de la vidéo
        cap = cv2.VideoCapture(video_path)
        self.frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.video_fps = cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        # Configuration matplotlib
        self.dpi = 100
        self.width_inches = self.frame_width / self.dpi
        self.height_inches = self.frame_height / self.dpi

    def _create_output_directories(self):
        """Crée la structure de dossiers nécessaire."""
        # Créer les dossiers principaux
        binary_base = self.output_dir / "BinaryMasks"
        jpeg_base = self.output_dir / "JPEGImages"
        
        # Créer un dossier pour chaque joueur
        for i in range(22):
            player_dir = f"{self.video_name}_player{i}"
            (binary_base / player_dir).mkdir(parents=True, exist_ok=True)
            (jpeg_base / player_dir).mkdir(parents=True, exist_ok=True)

    def _calculate_player_distances(self, frame_idx):
        """Calcule et trie les distances des joueurs à la caméra."""
        positions = self.poses_data['transl'][:, frame_idx, :]
        t = self.camera_data['t'][frame_idx]
        
        player_distances = []
        for i in range(22):
            player_pos = positions[i]
            distance = np.sqrt((player_pos[0] + t[0])**2 + 
                             (player_pos[1] - (-t[2]))**2)
            player_distances.append((i, distance, player_pos))
        
        return sorted(player_distances, key=lambda x: x[1])

    def process_frame(self, frame_idx):
        """
        Traite une frame spécifique pour tous les joueurs.
        
        Args:
            frame_idx: Index de la frame à traiter
        """
        # Charger la frame vidéo
        cap = cv2.VideoCapture(self.video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise ValueError(f"Impossible de lire la frame {frame_idx}")
            
        # Calculer les distances des joueurs
        player_distances = self._calculate_player_distances(frame_idx)
        
        # Générer et sauvegarder les masques pour chaque joueur
        for rank, (player_idx, distance, pos) in enumerate(player_distances):
            self._process_player_mask(frame_idx, frame, player_idx, rank, player_distances)
            self._save_frame_image(frame_idx, frame, player_idx)

    def _process_player_mask(self, frame_idx, frame, player_idx, rank, player_distances):
        """
        Génère et sauvegarde le masque d'un joueur spécifique.
        
        Args:
            frame_idx: Index de la frame
            frame: Image de la frame
            player_idx: Index du joueur
            rank: Position du joueur dans l'ordre de profondeur
            player_distances: Liste triée des distances des joueurs
        """
        vertices_2d = self._get_vertices_2d(frame_idx)
        
        if np.isnan(vertices_2d[player_idx]).any():
            print(f"Joueur {player_idx} ignoré car coordonnées NaN")
            if self.save_empty_masks:
                # Créer un masque noir
                mask = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)
                
                # Sauvegarder le masque noir
                mask_path = (self.output_dir / "BinaryMasks" / 
                           f"{self.video_name}_player{player_idx}" / 
                           f"{frame_idx:05d}.png")
                cv2.imwrite(str(mask_path), mask)
                
                # Sauvegarder l'image correspondante
                self._save_frame_image(frame_idx, frame, player_idx)
            return
            
        # Créer une nouvelle figure
        fig, ax = plt.subplots(figsize=(self.width_inches, self.height_inches))
        
        # Configurer le fond en noir et les paramètres de la figure
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        ax.axis('off')
        ax.set_xlim(0, self.frame_width)
        ax.set_ylim(self.frame_height, 0)
        
        # Dessiner la silhouette du joueur en blanc
        ax.scatter(vertices_2d[player_idx, :, 0], vertices_2d[player_idx, :, 1], 
                  c='white', s=1)
        
        # Soustraire (en noir) les silhouettes des joueurs plus proches
        for closer_rank in range(rank):
            closer_idx = player_distances[closer_rank][0]
            if not np.isnan(vertices_2d[closer_idx]).any():
                ax.scatter(vertices_2d[closer_idx, :, 0], vertices_2d[closer_idx, :, 1],
                          c='black', s=1)
        
        # Sauvegarder le masque
        mask_path = (self.output_dir / "BinaryMasks" / 
                    f"{self.video_name}_player{player_idx}" / 
                    f"{frame_idx:05d}.png")
        
        plt.savefig(str(mask_path),
                    dpi=self.dpi,
                    bbox_inches=None,
                    pad_inches=0,
                    facecolor='black',
                    edgecolor='none')
        plt.close(fig)

    def _project_vertices(self, vertices_3d, K, R, t, k):
        """
        Projette les vertices 3D en prenant en compte la distorsion
        
        Args:
            vertices_3d: points 3D (N, V, 3)
            K: matrice intrinsèque (3, 3)
            R: matrice de rotation (3, 3)
            t: vecteur de translation (3,)
            k: coefficients de distorsion [k1, k2, p1, p2, k3]
        """
        # Reshape pour traiter tous les points en une fois
        vertices_flat = vertices_3d.reshape(-1, 3).T  # (3, N*V)
        
        # Transformation dans le repère caméra
        vertices_cam = (R @ vertices_flat + t[:, np.newaxis])  # (3, N*V)
        
        # Normalisation (projection sur le plan z=1)
        x = vertices_cam[0] / vertices_cam[2]
        y = vertices_cam[1] / vertices_cam[2]
        
        # Calcul de la distorsion
        r2 = x*x + y*y
        r4 = r2*r2
        r6 = r2*r4
        
        # Distorsion radiale
        radial = (1 + k[0]*r2 + k[1]*r4 + k[4]*r6)
        x_dist = x * radial
        y_dist = y * radial
        
        # Distorsion tangentielle
        x_dist = x_dist + (2*k[2]*x*y + k[3]*(r2 + 2*x*x))
        y_dist = y_dist + (k[2]*(r2 + 2*y*y) + 2*k[3]*x*y)
        
        # Application de la matrice intrinsèque
        points_2d = np.vstack([
            K[0,0]*x_dist + K[0,2],
            K[1,1]*y_dist + K[1,2]
        ])
        
        return points_2d.T.reshape(vertices_3d.shape[0], -1, 2)

    def _get_vertices_2d(self, frame_idx):
        """
        Calcule les vertices 2D pour tous les joueurs à une frame donnée.
        
        Args:
            frame_idx: Index de la frame
        
        Returns:
            np.ndarray: Tableau des vertices 2D pour tous les joueurs
        """
        # Récupérer les paramètres de la caméra
        K = self.camera_data['K'][frame_idx]
        R = self.camera_data['R'][frame_idx]
        t = self.camera_data['t'][frame_idx]
        k = self.camera_data['k'][frame_idx]
        
        # Récupérer les poses des joueurs
        betas = torch.tensor(self.poses_data['betas'], dtype=torch.float32)
        global_orient = torch.tensor(self.poses_data['global_orient'][:, frame_idx], dtype=torch.float32)
        body_pose = torch.tensor(self.poses_data['body_pose'][:, frame_idx], dtype=torch.float32)
        transl = torch.tensor(self.poses_data['transl'][:, frame_idx], dtype=torch.float32)
        
        # Traiter chaque joueur individuellement
        all_vertices = []
        for i in range(22):
            vertices = self.smpl(
                betas=betas[i:i+1],
                global_orient=global_orient[i:i+1],
                body_pose=body_pose[i:i+1],
                transl=transl[i:i+1]
            ).vertices.detach().numpy()
            all_vertices.append(vertices)
            
        # Combiner tous les vertices
        vertices = np.concatenate(all_vertices, axis=0)  # (22, 6890, 3)
        
        # Projeter les vertices 3D en 2D avec distorsion
        return self._project_vertices(vertices, K, R, t, k)

    def _save_frame_image(self, frame_idx, frame, player_idx):
        """Sauvegarde l'image originale correspondant au masque."""
        image_path = (self.output_dir / "JPEGImages" / 
                     f"{self.video_name}_player{player_idx}" / 
                     f"{frame_idx:05d}.jpg")
        cv2.imwrite(str(image_path), frame)

    def process_video(self, target_fps=None):
        """
        Traite la vidéo entière avec un FPS spécifique.
        
        Args:
            target_fps: FPS cible pour le traitement. Si None, traite toutes les frames.
        """
        # Calculer l'intervalle entre les frames
        if target_fps is None or target_fps >= self.video_fps:
            frame_interval = 1
        else:
            frame_interval = int(self.video_fps / target_fps)
        
        # Calculer les indices des frames à traiter
        frame_indices = range(0, self.total_frames, frame_interval)
        
        # Initialiser le compteur pour la numérotation séquentielle
        save_idx = 0
        
        print(f"Traitement de la vidéo avec {len(frame_indices)} frames...")
        for frame_idx in frame_indices:
            print(f"Traitement de la frame {frame_idx} (sauvegarde comme {save_idx:05d})")
            self._process_frame_with_save_idx(frame_idx, save_idx)
            save_idx += 1

    def _process_frame_with_save_idx(self, frame_idx, save_idx):
        """
        Traite une frame avec un index de sauvegarde spécifique.
        
        Args:
            frame_idx: Index réel de la frame dans la vidéo
            save_idx: Index à utiliser pour la sauvegarde des fichiers
        """
        # Charger la frame vidéo
        cap = cv2.VideoCapture(self.video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise ValueError(f"Impossible de lire la frame {frame_idx}")
            
        # Calculer les distances des joueurs
        player_distances = self._calculate_player_distances(frame_idx)
        
        # Générer et sauvegarder les masques pour chaque joueur
        for rank, (player_idx, distance, pos) in enumerate(player_distances):
            self._process_player_mask_with_save_idx(frame_idx, frame, player_idx, rank, player_distances, save_idx)

    def _process_player_mask_with_save_idx(self, frame_idx, frame, player_idx, rank, player_distances, save_idx):
        """Version modifiée de _process_player_mask qui utilise save_idx pour la sauvegarde"""
        vertices_2d = self._get_vertices_2d(frame_idx)
        
        if np.isnan(vertices_2d[player_idx]).any():
            print(f"Joueur {player_idx} ignoré car coordonnées NaN")
            if self.save_empty_masks:
                # Créer un masque noir
                mask = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)
                
                # Sauvegarder le masque noir avec save_idx
                mask_path = (self.output_dir / "BinaryMasks" / 
                           f"{self.video_name}_player{player_idx}" / 
                           f"{save_idx:05d}.png")
                cv2.imwrite(str(mask_path), mask)
                
                # Sauvegarder l'image correspondante avec save_idx
                image_path = (self.output_dir / "JPEGImages" / 
                            f"{self.video_name}_player{player_idx}" / 
                            f"{save_idx:05d}.jpg")
                cv2.imwrite(str(image_path), frame)
            return
            
        # Créer une nouvelle figure
        fig, ax = plt.subplots(figsize=(self.width_inches, self.height_inches))
        
        # Configurer le fond en noir et les paramètres de la figure
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        ax.axis('off')
        ax.set_xlim(0, self.frame_width)
        ax.set_ylim(self.frame_height, 0)
        
        # Dessiner la silhouette du joueur en blanc
        ax.scatter(vertices_2d[player_idx, :, 0], vertices_2d[player_idx, :, 1], 
                  c='white', s=1)
        
        # Soustraire (en noir) les silhouettes des joueurs plus proches
        for closer_rank in range(rank):
            closer_idx = player_distances[closer_rank][0]
            if not np.isnan(vertices_2d[closer_idx]).any():
                ax.scatter(vertices_2d[closer_idx, :, 0], vertices_2d[closer_idx, :, 1],
                          c='black', s=1)
        
        # Sauvegarder le masque avec save_idx
        mask_path = (self.output_dir / "BinaryMasks" / 
                    f"{self.video_name}_player{player_idx}" / 
                    f"{save_idx:05d}.png")
        
        plt.savefig(str(mask_path),
                    dpi=self.dpi,
                    bbox_inches=None,
                    pad_inches=0,
                    facecolor='black',
                    edgecolor='none')
        plt.close(fig)
        
        # Sauvegarder l'image correspondante avec save_idx
        image_path = (self.output_dir / "JPEGImages" / 
                     f"{self.video_name}_player{player_idx}" / 
                     f"{save_idx:05d}.jpg")
        cv2.imwrite(str(image_path), frame) 


def main():
    # Chemins des fichiers
    video_name = 'ARG_CRO_220001'
    camera_path = f'./extracted_files/cameras/{video_name}.npz'
    poses_path = f'./extracted_files/poses/{video_name}.npz'
    video_path = f'./extracted_files/videos/{video_name}.mp4'
    output_dir = './output'
    smpl_model_path = './models/smpl'
    
    # Créer l'extracteur
    extractor = PlayerMaskExtractor(
        camera_path=camera_path,
        poses_path=poses_path,
        video_path=video_path,
        output_dir=output_dir,
        smpl_model_path=smpl_model_path,
        save_empty_masks=True
    )
    
    # Traiter la vidéo entière à 5 FPS
    # target_fps = 50
    target_fps = 5
    extractor.process_video(target_fps=target_fps)

if __name__ == "__main__":
    main() 