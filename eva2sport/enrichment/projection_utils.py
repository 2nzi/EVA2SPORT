"""
Utilitaires de projection et transformations géométriques
"""

import numpy as np
from typing import List, Tuple, Dict, Any


class ProjectionUtils:
    """Utilitaires pour les projections et transformations"""
    
    @staticmethod
    def world_to_image(world_point: List[float], cam_params: Dict) -> List[float]:
        """Projette un point 3D monde vers l'image 2D"""
        
        # Matrice intrinsèque
        K = np.array([
            [cam_params["cam_params"]["x_focal_length"], 0, cam_params["cam_params"]["principal_point"][0]],
            [0, cam_params["cam_params"]["y_focal_length"], cam_params["cam_params"]["principal_point"][1]],
            [0, 0, 1]
        ])
        
        # Matrice extrinsèque
        R = np.array(cam_params["cam_params"]["rotation_matrix"])
        t = -R @ np.array(cam_params["cam_params"]["position_meters"])
        
        # Point 3D monde (ajouter Z=0 si nécessaire)
        if len(world_point) == 2:
            world_point = [world_point[0], world_point[1], 0.0]
        
        world_point_h = np.array([world_point[0], world_point[1], world_point[2], 1])
        
        # Transformation
        P = K @ np.hstack((R, t.reshape(-1,1)))
        image_point_h = P @ world_point_h
        
        # Normalisation
        image_point = image_point_h[:2] / image_point_h[2]
        
        return image_point.tolist()
    
    @staticmethod
    def calculate_field_distance(point1: Dict, point2: Dict) -> float:
        """Calcule la distance entre deux points sur le terrain"""
        
        if not point1 or not point2:
            return 0.0
            
        p1 = point1.get("field", {}).get("CENTER_BOTTOM")
        p2 = point2.get("field", {}).get("CENTER_BOTTOM")
        
        if not p1 or not p2:
            return 0.0
            
        dx = p1["x"] - p2["x"]
        dy = p1["y"] - p2["y"]
        
        return float(np.sqrt(dx**2 + dy**2))
    
    @staticmethod
    def calculate_object_velocity(positions: List[Dict], fps: float, frame_interval: int) -> Dict:
        """Calcule la vélocité d'un objet sur plusieurs frames"""
        
        if len(positions) < 2:
            return {"speed": 0.0, "direction": None}
        
        # Prendre les deux dernières positions valides
        valid_positions = [p for p in positions if p.get("field", {}).get("CENTER_BOTTOM")]
        
        if len(valid_positions) < 2:
            return {"speed": 0.0, "direction": None}
        
        p1 = valid_positions[-2]["field"]["CENTER_BOTTOM"]
        p2 = valid_positions[-1]["field"]["CENTER_BOTTOM"]
        
        # Distance parcourue
        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        distance = np.sqrt(dx**2 + dy**2)
        
        # Temps écoulé
        time_delta = frame_interval / fps
        
        # Vitesse (m/s)
        speed = distance / time_delta if time_delta > 0 else 0.0
        
        # Direction (radians)
        direction = np.arctan2(dy, dx) if distance > 0 else None
        
        return {
            "speed": float(speed),
            "direction": float(direction) if direction is not None else None,
            "distance": float(distance),
            "time_delta": float(time_delta)
        }