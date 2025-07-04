import numpy as np
import matplotlib.pyplot as plt
import cv2
import torch
from smplx import SMPL
from pathlib import Path


def project_vertices(vertices_3d, K, R, t, k):
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


def visualize_poses_on_frame(frame_idx=0, 
                            camera_file=r'\\10.35.51.152\Biomeca\Projets\25_AIT_Challenge\extracted_files\cameras\ARG_CRO_220001.npz',
                            poses_file=r'\\10.35.51.152\Biomeca\Projets\25_AIT_Challenge\extracted_files\poses\ARG_CRO_220001.npz',
                            video_file=r'\\10.35.51.152\Biomeca\Projets\25_AIT_Challenge\extracted_files\videos\ARG_CRO_220001.mp4',
                            smpl_model_path=r'\\10.35.51.152\Biomeca\Projets\25_AIT_Challenge\models\smpl',
                            save_path=None):
    """
    Visualise les poses SMPL superposées sur une frame vidéo
    
    Args:
        frame_idx: Index de la frame à visualiser
        camera_file: Chemin vers le fichier caméra NPZ
        poses_file: Chemin vers le fichier poses NPZ
        video_file: Chemin vers le fichier vidéo
        smpl_model_path: Chemin vers le modèle SMPL
        save_path: Chemin pour sauvegarder l'image (optionnel)
    """
    
    # Charger les données caméra
    npz_file_camera = np.load(camera_file)
    
    # Charger les poses des corps
    npz_file = np.load(poses_file)
    
    # Préparer les données SMPL pour la frame choisie
    betas = torch.tensor(npz_file['betas'], dtype=torch.float32)  # (N, 10)
    global_orient = torch.tensor(npz_file['global_orient'][:, frame_idx], dtype=torch.float32)  # (N, 3)
    body_pose = torch.tensor(npz_file['body_pose'][:, frame_idx], dtype=torch.float32)  # (N, 69)
    transl = torch.tensor(npz_file['transl'][:, frame_idx], dtype=torch.float32)  # (N, 3)
    
    # Créer le modèle SMPL
    smpl = SMPL(
        model_path=smpl_model_path,
        gender='male',
        batch_size=1  # On va traiter les joueurs un par un
    )
    
    # Traiter chaque joueur individuellement
    all_vertices = []
    for i in range(22):
        vertices = smpl(
            betas=betas[i:i+1],
            global_orient=global_orient[i:i+1],
            body_pose=body_pose[i:i+1],
            transl=transl[i:i+1]
        ).vertices.detach().numpy()
        all_vertices.append(vertices)
    
    # Combiner tous les vertices
    vertices = np.concatenate(all_vertices, axis=0)  # (22, 6890, 3)
    
    # Charger les matrices intrinsèques et extrinsèques
    K = npz_file_camera['K'][frame_idx]   # (3, 3)
    R = npz_file_camera['R'][frame_idx]   # (3, 3)
    t = npz_file_camera['t'][frame_idx]   # (3,)
    k = npz_file_camera['k'][frame_idx]   # Coefficients de distorsion
    
    # Projeter les vertices 2D
    vertices_2d = project_vertices(vertices, K, R, t, k)
    
    # Charger l'image correspondante
    cap = cv2.VideoCapture(video_file)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print(f"Impossible de lire la frame {frame_idx}")
        return None
    
    # Convertir l'image BGR en RGB pour matplotlib
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Créer la visualisation
    plt.figure(figsize=(15, 10))
    plt.imshow(frame_rgb)
    
    # Dessiner les silhouettes des joueurs
    for i in range(11):  # Équipe 1
        plt.scatter(vertices_2d[i, :, 0], vertices_2d[i, :, 1], 
                   c='red', alpha=0.1, s=1, label='Équipe 1' if i == 0 else "")
    
    for i in range(11, 22):  # Équipe 2
        plt.scatter(vertices_2d[i, :, 0], vertices_2d[i, :, 1], 
                   c='blue', alpha=0.1, s=1, label='Équipe 2' if i == 11 else "")
    
    plt.title(f"Projection des modèles SMPL des joueurs (Frame {frame_idx})")
    plt.legend()
    plt.axis('off')
    
    # Sauvegarder si demandé
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"Image sauvegardée: {save_path}")
    
    plt.show()
    
    return frame_rgb, vertices_2d


if __name__ == "__main__":
    # Configuration par défaut
    FRAME_IDX = 0
    VIDEO_NAME = 'ARG_CRO_220001' 

    INPUT_PATH = Path(r'\\10.35.51.152\Biomeca\Projets\25_AIT_Challenge')
    CAMERAS_PATH = INPUT_PATH / f'extracted_files/cameras/{VIDEO_NAME}.npz'
    POSES_PATH = INPUT_PATH / f'extracted_files/poses/{VIDEO_NAME}.npz'
    VIDEOS_PATH = INPUT_PATH / f'extracted_files/videos/{VIDEO_NAME}.mp4'
    SMPL_PATH = INPUT_PATH / 'models/smpl'
    SAVE_PATH = f'./test_extraction/pose_visualization_frame_{FRAME_IDX}.png'
    
    # Vérifier que les fichiers existent
    print(f"Vérification des fichiers...")
    print(f"Caméra: {CAMERAS_PATH.exists()} - {CAMERAS_PATH}")
    print(f"Poses: {POSES_PATH.exists()} - {POSES_PATH}")
    print(f"Vidéo: {VIDEOS_PATH.exists()} - {VIDEOS_PATH}")
    print(f"SMPL: {SMPL_PATH.exists()} - {SMPL_PATH}")
    
    try:
        print("=== Exemple 1: Frame 0 ===")
        result = visualize_poses_on_frame(
                frame_idx=FRAME_IDX,
                camera_file=str(CAMERAS_PATH),
                poses_file=str(POSES_PATH),
                video_file=str(VIDEOS_PATH),
                smpl_model_path=str(SMPL_PATH),
                save_path=SAVE_PATH
        )
        
        if result is not None:
            print(f"Visualisation terminée avec succès pour la frame {FRAME_IDX}")
        else:
            print("Erreur lors de la visualisation")
            
    except Exception as e:
        print(f"Erreur détaillée: {e}")
        import traceback
        traceback.print_exc()
        print("Vérifiez que tous les fichiers existent et que les chemins sont corrects")




        # # Exemple 2: Visualisation d'une autre frame
        # print("\n=== Exemple 2: Frame 100 ===")
        # visualize_poses_on_frame(
        #     frame_idx=100,
        #     save_path='frame_100.png'
        # )
        
        # # Exemple 3: Visualisation sans sauvegarde
        # print("\n=== Exemple 3: Frame 50 (sans sauvegarde) ===")
        # visualize_poses_on_frame(
        #     frame_idx=50,
        #     save_path=None
        # )
        
        # # Exemple 4: Personnalisation des chemins
        # print("\n=== Exemple 4: Chemins personnalisés ===")
        # visualize_poses_on_frame(
        #     frame_idx=25,
        #     camera_file='./extracted_files/cameras/ARG_CRO_220001.npz',
        #     poses_file='./extracted_files/poses/ARG_CRO_220001.npz',
        #     video_file='./extracted_files/videos/ARG_CRO_220001.mp4',
        #     smpl_model_path=r'C:\Users\antoi\Documents\Work_Learn\Stage-Rennes\RepositoryFootballVision\FIFA\models\smpl',
        #     save_path='custom_frame_25.png'
        # )