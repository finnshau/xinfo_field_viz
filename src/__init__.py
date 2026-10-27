"""
xinfo_field_viz.src

X-Info football field visualization package.

Phase 1: Offensive player positioning and visualization.
"""

from .mapper import OffensiveMapper, plot_offensive_formation
from .roles import (
    get_role_category,
    is_offensive_role,
    is_left_side,
    is_right_side,
)

__version__ = '0.1.0'
__all__ = [
    'OffensiveMapper',
    'plot_offensive_formation',
    'get_role_category',
    'is_offensive_role',
    'is_left_side',
    'is_right_side',
]
