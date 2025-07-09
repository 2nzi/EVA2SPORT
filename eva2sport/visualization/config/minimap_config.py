"""
Configuration de la minimap
"""

from dataclasses import dataclass
from typing import Literal, Dict, Any
from copy import deepcopy

@dataclass
class MinimapConfig:
    """Configuration pour la minimap du terrain"""
    
    # Transformation du terrain
    rotation: Literal[0, 90, 180, 270] = 0
    half_field: Literal['left', 'right', 'full'] = 'full'
    invert_x: bool = False
    invert_y: bool = True
    
    # Apparence
    transparency: float = 0.4
    size: str = "35%"
    position: Literal[
        'upper left', 'upper center', 'upper right',
        'center left', 'center', 'center right', 
        'lower left', 'lower center', 'lower right'
    ] = 'lower center'
    
    # Style du terrain
    line_color: str = 'white'
    background_color: str = 'black'
    
    # Objets sur le terrain
    point_size: int = 125
    show_object_ids: bool = True
    id_font_size: int = 7
    
    def __post_init__(self):
        """Validation des paramètres après initialisation"""
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Valide tous les paramètres de configuration"""
        
        # Validation rotation
        if self.rotation not in [0, 90, 180, 270]:
            raise ValueError(f"rotation doit être 0, 90, 180 ou 270, reçu: {self.rotation}")
        
        # Validation half_field
        if self.half_field not in ['left', 'right', 'full']:
            raise ValueError(f"half_field doit être 'left', 'right' ou 'full', reçu: {self.half_field}")
        
        # Validation transparency
        if not 0.0 <= self.transparency <= 1.0:
            raise ValueError(f"transparency doit être entre 0.0 et 1.0, reçu: {self.transparency}")
        
        # Validation size
        if not self.size.endswith('%'):
            raise ValueError(f"size doit se terminer par '%', reçu: {self.size}")
        
        try:
            size_value = float(self.size[:-1])
            if not 10 <= size_value <= 80:
                raise ValueError(f"size doit être entre 10% et 80%, reçu: {self.size}")
        except ValueError:
            raise ValueError(f"size doit être un pourcentage valide, reçu: {self.size}")
        
        # Validation position
        valid_positions = [
            'upper left', 'upper center', 'upper right',
            'center left', 'center', 'center right', 
            'lower left', 'lower center', 'lower right'
        ]
        if self.position not in valid_positions:
            raise ValueError(f"position invalide: {self.position}")
        

        # Validation point_size
        if self.point_size <= 0:
            raise ValueError(f"point_size doit être positif, reçu: {self.point_size}")
        
        # Validation id_font_size
        if self.id_font_size <= 0:
            raise ValueError(f"id_font_size doit être positif, reçu: {self.id_font_size}")
    
    def update(self, **kwargs) -> 'MinimapConfig':
        """Met à jour la configuration avec de nouveaux paramètres"""
        new_config = deepcopy(self)
        
        for key, value in kwargs.items():
            if not hasattr(new_config, key):
                raise ValueError(f"Paramètre inconnu: {key}")
            setattr(new_config, key, value)
        
        # Revalider après mise à jour
        new_config._validate_parameters()
        return new_config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la configuration en dictionnaire"""
        return {
            'rotation': self.rotation,
            'half_field': self.half_field,
            'invert_x': self.invert_x,
            'invert_y': self.invert_y,
            'transparency': self.transparency,
            'size': self.size,
            'position': self.position,
            'line_color': self.line_color,
            'background_color': self.background_color,
            'point_size': self.point_size,
            'show_object_ids': self.show_object_ids,
            'id_font_size': self.id_font_size
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'MinimapConfig':
        """Crée une configuration à partir d'un dictionnaire"""
        return cls(**config_dict)
    
    @classmethod
    def get_default(cls) -> 'MinimapConfig':
        """Retourne la configuration par défaut"""
        return cls()
    
    @classmethod
    def get_tactical_view(cls) -> 'MinimapConfig':
        """Configuration pour vue tactique (demi-terrain gauche)"""
        return cls(
            rotation=90,
            half_field='left',
            invert_y=True,
            transparency=0.5,
            position='upper left',
            size="35%"
        )
    
    @classmethod
    def get_analysis_view(cls) -> 'MinimapConfig':
        """Configuration pour vue d'analyse (terrain complet)"""
        return cls(
            rotation=0,
            half_field='full',
            transparency=0.4,
            position='upper right',
            size="45%"
        )
    
    @classmethod
    def get_broadcast_view(cls) -> 'MinimapConfig':
        """Configuration pour vue broadcast"""
        return cls(
            rotation=90,
            half_field='right',
            transparency=0.7,
            position='lower center',
            size="30%"
        )
    
    def __str__(self) -> str:
        """Représentation string de la configuration"""
        return f"MinimapConfig(rotation={self.rotation}, half_field={self.half_field}, size={self.size})"
    
    def __repr__(self) -> str:
        """Représentation détaillée de la configuration"""
        return (f"MinimapConfig(rotation={self.rotation}, half_field={self.half_field}, "
                f"invert_x={self.invert_x}, invert_y={self.invert_y}, "
                f"transparency={self.transparency}, size={self.size}, position={self.position})") 