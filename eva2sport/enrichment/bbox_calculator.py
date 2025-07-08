"""
Calculateur de bounding boxes et points de projection
"""

from typing import Dict, Any, Optional
import numpy as np


class BBoxCalculator:
    """Calcule les bounding boxes et projections terrain"""
    
    def calculate_points_from_bbox(self, bbox: Dict[str, int], 
                                 cam_params: Dict = None) -> Optional[Dict]:
        """
        Calcule les points de sortie depuis une bounding box
        
        Args:
            bbox: Dict avec 'x', 'y', 'width', 'height'
            cam_params: Paramètres de calibration caméra
            
        Returns:
            Dict avec points image et terrain
        """
        if not bbox:
            return None

        # Point CENTER_BOTTOM dans le plan image
        center_bottom_x = bbox['x'] + bbox['width'] / 2
        center_bottom_y = bbox['y'] + bbox['height']  # Bas de la bbox

        # Structure de base
        points_output = {
            "image": {
                "CENTER_BOTTOM": {
                    "x": float(center_bottom_x),
                    "y": float(center_bottom_y)
                }
            },
            "field": {
                "CENTER_BOTTOM": None
            }
        }

        # Projection terrain si paramètres fournis
        if cam_params:
            try:
                image_point = [center_bottom_x, center_bottom_y]
                field_point = self._image_to_world(image_point, cam_params)

                points_output["field"]["CENTER_BOTTOM"] = {
                    "x": float(field_point[0]),
                    "y": float(field_point[1])
                }

            except Exception as e:
                print(f"⚠️ Erreur projection terrain: {e}")
                points_output["field"]["CENTER_BOTTOM"] = None

        return points_output
    
    def _image_to_world(self, point_2d, cam_params):
        """Projette un point 2D vers le plan terrain (Z=0)"""
        
        # Matrice de projection P
        K = np.array([
            [cam_params["cam_params"]["x_focal_length"], 0, cam_params["cam_params"]["principal_point"][0]],
            [0, cam_params["cam_params"]["y_focal_length"], cam_params["cam_params"]["principal_point"][1]],
            [0, 0, 1]
        ])
        R = np.array(cam_params["cam_params"]["rotation_matrix"])
        t = -R @ np.array(cam_params["cam_params"]["position_meters"])
        P = K @ np.hstack((R, t.reshape(-1,1)))

        # Point sur le plan image en coordonnées homogènes
        point_2d_h = np.array([point_2d[0], point_2d[1], 1])

        # Rétro-projection du rayon depuis la caméra
        ray = np.linalg.inv(K) @ point_2d_h
        ray = R.T @ ray

        # Intersection avec le plan Z=0
        camera_pos = np.array(cam_params["cam_params"]["position_meters"])
        t = -camera_pos[2] / ray[2]
        world_point = camera_pos + t * ray

        return world_point[:2]  # Retourner seulement X,Y puisque Z=0